"""
Health check endpoints for monitoring application and service health.

This module provides comprehensive health check endpoints that validate
the application status and external service dependencies.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.config import AppConfig
from app.dependencies import get_service_container, get_app_config
from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_collector

logger = get_logger(__name__)

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])


async def check_openai_health(config: AppConfig) -> Dict[str, Any]:
    """
    Check OpenAI service health with circuit breaker protection.
    
    Args:
        config: Application configuration
        
    Returns:
        Dict containing health status and details
    """
    from app.utils.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig, CircuitBreakerError
    
    try:
        if not config.openai_api_key or not config.openai_api_key.startswith('sk-'):
            return {
                "status": "not_configured",
                "message": "OpenAI API key not configured",
                "response_time_ms": 0,
                "circuit_breaker": "disabled"
            }
        
        # Get circuit breaker for OpenAI health checks
        circuit_breaker = get_circuit_breaker(
            "openai_health_check",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                timeout=10.0
            )
        )
        
        async def _check_openai_api():
            """Internal function to check OpenAI API."""
            # Import here to avoid circular imports
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=config.openai_api_key)
            
            try:
                # Use a minimal completion request to test the connection
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use cheaper model for health check
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                    timeout=5.0
                )
                return response
            finally:
                await client.close()
        
        # Test OpenAI connection through circuit breaker
        start_time = time.time()
        
        try:
            await circuit_breaker.call(_check_openai_api)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "message": "OpenAI API accessible",
                "response_time_ms": round(response_time, 2),
                "model": config.openai_model,
                "circuit_breaker": circuit_breaker.get_status()
            }
            
        except CircuitBreakerError:
            return {
                "status": "circuit_open",
                "message": "OpenAI service circuit breaker is open",
                "response_time_ms": 0,
                "circuit_breaker": circuit_breaker.get_status()
            }
            
        except Exception as api_error:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"OpenAI health check API call failed: {api_error}")
            
            return {
                "status": "degraded",
                "message": f"OpenAI API error: {str(api_error)[:100]}",
                "response_time_ms": round(response_time, 2),
                "circuit_breaker": circuit_breaker.get_status()
            }
            
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"OpenAI health check error: {str(e)[:100]}",
            "response_time_ms": 0,
            "circuit_breaker": "error"
        }


async def check_twilio_health(config: AppConfig) -> Dict[str, Any]:
    """
    Check Twilio service health with circuit breaker protection.
    
    Args:
        config: Application configuration
        
    Returns:
        Dict containing health status and details
    """
    from app.utils.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig, CircuitBreakerError
    
    try:
        if not all([config.twilio_account_sid, config.twilio_auth_token, config.twilio_phone_number]):
            return {
                "status": "not_configured",
                "message": "Twilio credentials not configured",
                "response_time_ms": 0,
                "circuit_breaker": "disabled"
            }
        
        # Get circuit breaker for Twilio health checks
        circuit_breaker = get_circuit_breaker(
            "twilio_health_check",
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                timeout=10.0
            )
        )
        
        async def _check_twilio_api():
            """Internal function to check Twilio API."""
            # Import here to avoid circular imports
            from twilio.rest import Client
            
            client = Client(config.twilio_account_sid, config.twilio_auth_token)
            
            # Test Twilio connection by fetching account info
            account = client.api.accounts(config.twilio_account_sid).fetch()
            return account
        
        start_time = time.time()
        
        try:
            account = await circuit_breaker.call(_check_twilio_api)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "message": "Twilio API accessible",
                "response_time_ms": round(response_time, 2),
                "account_status": account.status,
                "phone_number": config.twilio_phone_number,
                "circuit_breaker": circuit_breaker.get_status()
            }
            
        except CircuitBreakerError:
            return {
                "status": "circuit_open",
                "message": "Twilio service circuit breaker is open",
                "response_time_ms": 0,
                "circuit_breaker": circuit_breaker.get_status()
            }
            
        except Exception as api_error:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"Twilio health check API call failed: {api_error}")
            
            return {
                "status": "degraded",
                "message": f"Twilio API error: {str(api_error)[:100]}",
                "response_time_ms": round(response_time, 2),
                "circuit_breaker": circuit_breaker.get_status()
            }
            
    except Exception as e:
        logger.error(f"Twilio health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Twilio health check error: {str(e)[:100]}",
            "response_time_ms": 0,
            "circuit_breaker": "error"
        }


@router.get("/")
async def basic_health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancers and simple monitoring.
    
    Returns:
        Dict containing basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "reality-checker-whatsapp-bot",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Detailed health check endpoint that validates all external dependencies.
    
    Args:
        config: Application configuration
        
    Returns:
        Dict containing comprehensive health status
    """
    start_time = time.time()
    
    try:
        # Get service container for basic health checks
        service_container = get_service_container()
        basic_health = await service_container.perform_health_checks()
        
        # Perform detailed external service health checks
        health_checks = await asyncio.gather(
            check_openai_health(config),
            check_twilio_health(config),
            return_exceptions=True
        )
        
        openai_health = health_checks[0] if not isinstance(health_checks[0], Exception) else {
            "status": "error",
            "message": f"Health check failed: {health_checks[0]}",
            "response_time_ms": 0
        }
        
        twilio_health = health_checks[1] if not isinstance(health_checks[1], Exception) else {
            "status": "error", 
            "message": f"Health check failed: {health_checks[1]}",
            "response_time_ms": 0
        }
        
        # Get metrics
        metrics_collector = get_metrics_collector()
        current_metrics = metrics_collector.get_current_metrics()
        
        # Determine overall health status
        service_statuses = [openai_health["status"], twilio_health["status"]]
        
        if all(status in ["healthy", "not_configured"] for status in service_statuses):
            overall_status = "healthy"
        elif any(status == "healthy" for status in service_statuses):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        total_time = (time.time() - start_time) * 1000
        
        response = {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "reality-checker-whatsapp-bot",
            "version": "1.0.0",
            "health_check_duration_ms": round(total_time, 2),
            "services": {
                "openai": openai_health,
                "twilio": twilio_health,
                "pdf_processing": {
                    "status": basic_health.get("pdf_processing", "unknown"),
                    "message": "PDF processing service status"
                }
            },
            "metrics": {
                "requests": current_metrics.get("requests", {}),
                "services": current_metrics.get("services", {})
            },
            "configuration": {
                "openai_model": config.openai_model,
                "max_pdf_size_mb": config.max_pdf_size_mb,
                "log_level": config.log_level,
                "webhook_validation": config.webhook_validation
            }
        }
        
        # Return appropriate HTTP status based on health
        if overall_status == "unhealthy":
            return JSONResponse(
                status_code=503,
                content=response
            )
        elif overall_status == "degraded":
            return JSONResponse(
                status_code=200,
                content=response,
                headers={"X-Health-Status": "degraded"}
            )
        else:
            return response
            
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Health check failed",
                "message": f"Unable to perform health check: {str(e)[:100]}"
            }
        )


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    Metrics endpoint for monitoring and observability.
    
    Returns:
        Dict containing application metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_current_metrics()
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve metrics"
        )


@router.get("/readiness")
async def readiness_check(
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes-style deployments.
    
    This endpoint checks if the application is ready to serve traffic.
    
    Args:
        config: Application configuration
        
    Returns:
        Dict containing readiness status
    """
    try:
        # Check critical configuration
        if not config.openai_api_key or not config.twilio_account_sid:
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Critical configuration missing"
                }
            )
        
        # Check if services can be initialized
        service_container = get_service_container()
        
        try:
            # Try to get core services
            _ = service_container.get_pdf_service()
            _ = service_container.get_openai_service()
            _ = service_container.get_twilio_service()
            _ = service_container.get_message_handler()
            
            return {
                "ready": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Application ready to serve traffic"
            }
            
        except Exception as service_error:
            logger.error(f"Service initialization failed in readiness check: {service_error}")
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": f"Service initialization failed: {str(service_error)[:100]}"
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Readiness check error: {str(e)[:100]}"
            }
        )


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes-style deployments.
    
    This endpoint checks if the application is alive and should not be restarted.
    
    Returns:
        Dict containing liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Application is alive"
    }


@router.get("/circuit-breakers")
async def circuit_breakers_status() -> Dict[str, Any]:
    """
    Get status of all circuit breakers.
    
    Returns:
        Dict containing circuit breaker statuses
    """
    try:
        from app.utils.circuit_breaker import get_circuit_breaker_manager
        
        manager = get_circuit_breaker_manager()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "circuit_breakers": manager.get_all_status()
        }
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve circuit breaker status"
        )


@router.get("/alerts")
async def active_alerts() -> Dict[str, Any]:
    """
    Get active alerts from the error tracking system.
    
    Returns:
        Dict containing active alerts
    """
    try:
        error_tracker = get_error_tracker()
        active_alerts = error_tracker.get_active_alerts()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_alerts": [
                {
                    "id": alert.id,
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "context": alert.context
                }
                for alert in active_alerts
            ],
            "alert_count": len(active_alerts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve active alerts"
        )