"""Main FastAPI application for Reality Checker WhatsApp Bot."""

import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_config
from app.api.webhook import router as webhook_router
from app.utils.logging import setup_logging, get_logger, set_correlation_id, get_correlation_id
from app.utils.error_handling import handle_error, ErrorCategory

logger = get_logger(__name__)


async def startup_event():
    """Application startup event handler."""
    try:
        # Validate configuration on startup
        config = get_config()
        
        # Setup structured logging
        setup_logging(
            log_level=config.log_level,
            use_json=config.log_level.upper() == "DEBUG"  # Use JSON logging in debug mode
        )
        
        logger.info("Application started successfully")
        logger.info(f"Log level: {config.log_level}")
        logger.info(f"OpenAI model: {config.openai_model}")
        logger.info(f"Max PDF size: {config.max_pdf_size_mb}MB")
        logger.info(f"Webhook validation: {config.webhook_validation}")
        
    except Exception as exc:
        user_message, error_info = handle_error(exc, {"component": "startup"})
        logger.error(f"Failed to start application: {str(exc)}", exc_info=True)
        raise


async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
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
        # Get configuration to validate environment setup
        config = get_config()
        
        # Check if critical configuration is available
        services_status = {
            "openai": "connected" if config.openai_api_key else "not_configured",
            "twilio": "connected" if (config.twilio_account_sid and 
                                   config.twilio_auth_token and 
                                   config.twilio_phone_number) else "not_configured"
        }
        
        # Determine overall health status
        overall_status = "healthy" if all(
            status == "connected" for status in services_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": services_status,
            "version": "1.0.0"
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