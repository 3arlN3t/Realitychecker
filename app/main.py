"""Main FastAPI application for Reality Checker WhatsApp Bot."""

import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_config
from app.dependencies import get_service_container, reset_service_container
from app.api.webhook import router as webhook_router
from app.utils.logging import setup_logging, get_logger, set_correlation_id, get_correlation_id
from app.utils.error_handling import handle_error, ErrorCategory
from app.middleware.rate_limiting import create_rate_limit_middleware
from app.middleware.security_headers import create_security_headers_middleware

logger = get_logger(__name__)


async def startup_event():
    """Application startup event handler with service initialization and health checks."""
    try:
        logger.info("Starting Reality Checker WhatsApp Bot application...")
        
        # Validate configuration on startup
        config = get_config()
        
        # Setup structured logging
        setup_logging(
            log_level=config.log_level,
            use_json=config.log_level.upper() == "DEBUG"  # Use JSON logging in debug mode
        )
        
        logger.info("Configuration loaded successfully")
        logger.info(f"Log level: {config.log_level}")
        logger.info(f"OpenAI model: {config.openai_model}")
        logger.info(f"Max PDF size: {config.max_pdf_size_mb}MB")
        logger.info(f"Webhook validation: {config.webhook_validation}")
        
        # Initialize service container and perform health checks
        logger.info("Initializing services and performing health checks...")
        service_container = get_service_container()
        
        # Perform startup health checks
        health_status = await service_container.perform_health_checks()
        
        # Log health check results
        for service_name, status in health_status.items():
            if status == 'connected' or status == 'ready':
                logger.info(f"✅ {service_name}: {status}")
            elif status == 'not_configured':
                logger.warning(f"⚠️ {service_name}: {status}")
            else:
                logger.error(f"❌ {service_name}: {status}")
        
        # Check if critical services are available
        critical_services = ['openai', 'twilio']
        failed_services = [
            service for service in critical_services 
            if health_status.get(service) not in ['connected', 'ready']
        ]
        
        if failed_services:
            error_msg = f"Critical services failed health checks: {failed_services}"
            logger.error(error_msg)
            logger.error("Application startup failed due to service configuration issues")
            raise RuntimeError(error_msg)
        
        # Pre-initialize core services to catch any initialization errors early
        logger.info("Pre-initializing core services...")
        try:
            _ = service_container.get_pdf_service()
            logger.info("✅ PDF processing service initialized")
            
            _ = service_container.get_openai_service()
            logger.info("✅ OpenAI analysis service initialized")
            
            _ = service_container.get_twilio_service()
            logger.info("✅ Twilio response service initialized")
            
            _ = service_container.get_message_handler()
            logger.info("✅ Message handler service initialized")
            
        except Exception as service_error:
            logger.error(f"Failed to initialize services: {service_error}")
            raise RuntimeError(f"Service initialization failed: {service_error}")
        
        logger.info("🚀 Application startup completed successfully")
        
    except Exception as exc:
        _, error_info = handle_error(exc, {"component": "startup"})
        logger.error(f"💥 Failed to start application: {str(exc)}", exc_info=True)
        
        # Exit the application if startup fails
        logger.critical("Application startup failed. Exiting...")
        sys.exit(1)


async def shutdown_event():
    """Application shutdown event handler with graceful cleanup."""
    logger.info("🛑 Application shutdown initiated...")
    
    try:
        # Get service container and perform cleanup
        service_container = get_service_container()
        await service_container.cleanup()
        
        # Reset the global service container
        reset_service_container()
        
        logger.info("✅ Graceful shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    logger.info("👋 Application shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with startup and shutdown handling."""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


# Create FastAPI application
app = FastAPI(
    title="Reality Checker WhatsApp Bot",
    description="AI-powered job advertisement scam detection via WhatsApp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Include routers
app.include_router(webhook_router)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Add security headers middleware
security_headers_middleware = create_security_headers_middleware(
    enforce_https=True  # Set to False for local development
)
app.add_middleware(security_headers_middleware)

# Add rate limiting middleware
rate_limit_middleware = create_rate_limit_middleware(
    requests_per_minute=10,
    requests_per_hour=100,
    burst_limit=5,
    burst_window=10
)
app.add_middleware(rate_limit_middleware)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_and_error_middleware(request: Request, call_next):
    """Middleware for correlation ID tracking and error handling."""
    # Set correlation ID for this request
    correlation_id = set_correlation_id()
    
    try:
        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
        
    except Exception as exc:
        # Handle the error using our centralized error handler
        user_message, error_info = handle_error(
            exc, 
            {
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type")
            },
            correlation_id
        )
        
        # Return appropriate error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            headers={"X-Correlation-ID": correlation_id}
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error in {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception in {request.method} {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "HTTP 404",
            "message": "Not Found",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: HTTPException):
    """Handle 405 Method Not Allowed errors."""
    return JSONResponse(
        status_code=405,
        content={
            "error": "HTTP 405",
            "message": "Method Not Allowed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint that validates system status and critical dependencies.
    
    Returns:
        Dict containing system status, timestamp, and service availability
    """
    try:
        # Get service container and perform health checks
        service_container = get_service_container()
        services_status = await service_container.perform_health_checks()
        
        # Determine overall health status
        critical_services = ['openai', 'twilio']
        healthy_services = [
            service for service in critical_services 
            if services_status.get(service) in ['connected', 'ready']
        ]
        
        if len(healthy_services) == len(critical_services):
            overall_status = "healthy"
        elif len(healthy_services) > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services_status,
            "version": "1.0.0",
            "uptime": "running"
        }
        
    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Health check failed",
                "message": "Unable to verify system status"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)