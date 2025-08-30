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
from app.utils.error_tracking import get_error_tracker

logger = get_logger(__name__)

# Create router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])


async def check_database_health() -> Dict[str, Any]:
    """
    Check database health and connection pool status.
    
    This function creates a temporary database connection to avoid circular imports
    with the main database layer. It tests basic connectivity and measures response time.
    
    Returns:
        Dict containing database health status and details
    """
    try:
        # Use a simple database connection test to avoid circular imports
        import os
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        start_time = time.time()
        
        # Get database URL directly to avoid circular import
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Check for PostgreSQL configuration
            if all(env_var in os.environ for env_var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']):
                host = os.getenv('DB_HOST', 'localhost')
                port = os.getenv('DB_PORT', '5432')
                name = os.getenv('DB_NAME')
                user = os.getenv('DB_USER')
                password = os.getenv('DB_PASSWORD')
                database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
            else:
                # Default to SQLite
                db_path = os.getenv('DATABASE_PATH', 'data/reality_checker.db')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                database_url = f"sqlite+aiosqlite:///{db_path}"
        
        # Validate database URL format
        if not database_url or '://' not in database_url:
            raise ValueError("Invalid database URL format")
        
        # Create a temporary engine for health check
        # Use different parameters based on database type
        if database_url.startswith(("sqlite", "sqlite+aiosqlite")):
            # SQLite-specific configuration
            engine = create_async_engine(
                database_url,
                echo=False,
                connect_args={"check_same_thread": False}
            )
        else:
            # PostgreSQL and other database-specific configuration
            engine = create_async_engine(
                database_url,
                echo=False,
                pool_timeout=5,  # 5 second timeout for getting connection from pool
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True  # Validate connections before use
            )
        
        try:
            # Test database connection with timeout
            async with engine.begin() as conn:
                # Use a simple query that works on both PostgreSQL and SQLite
                await conn.execute(text("SELECT 1"))
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine database type more safely
            db_type = "postgresql" if "postgresql" in database_url.lower() else "sqlite"
            
            return {
                "status": "healthy",
                "message": "Database is accessible and functioning",
                "response_time_ms": round(response_time, 2),
                "database_type": db_type,
                "connection_pool": {"status": "available"},
                "circuit_breaker": {"state": "closed"}
            }
            
        finally:
            # Ensure engine is properly disposed
            await engine.dispose()
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        
        # Provide more specific error context
        error_type = type(e).__name__
        is_connection_error = any(keyword in str(e).lower() for keyword in 
                                ['connection', 'timeout', 'refused', 'unreachable'])
        
        return {
            "status": "unhealthy",
            "message": f"Database health check error: {str(e)[:100]}",
            "response_time_ms": 0,
            "database_type": "unknown",
            "connection_pool": {"status": "unavailable"},
            "circuit_breaker": {"state": "error"},
            "error_type": error_type,
            "is_connection_issue": is_connection_error
        }


async def check_redis_health() -> Dict[str, Any]:
    """
    Check Redis health and connection status.
    
    Returns:
        Dict containing Redis health status and details
    """
    try:
        # Use direct Redis connection to avoid circular imports
        import os
        import redis.asyncio as redis
        
        start_time = time.time()
        
        # Get Redis URL from environment
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Create Redis client
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        try:
            # Test Redis operations
            test_key = "health_check_test"
            test_value = "test"
            
            # Test set and get operations
            await redis_client.set(test_key, test_value, ex=10)  # 10 second expiry
            retrieved_value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            if retrieved_value == test_value:
                return {
                    "status": "healthy",
                    "message": "Redis is accessible and functioning",
                    "response_time_ms": round(response_time, 2),
                    "operations_tested": ["set", "get", "delete"]
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Redis operations not working correctly",
                    "response_time_ms": round(response_time, 2),
                    "operations_tested": ["set", "get", "delete"]
                }
                
        finally:
            await redis_client.close()
            
    except ImportError:
        return {
            "status": "not_available",
            "message": "Redis client not available (redis package not installed)",
            "response_time_ms": 0,
            "operations_tested": []
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis health check error: {str(e)[:100]}",
            "response_time_ms": 0,
            "operations_tested": []
        }


async def check_ngrok_status() -> Dict[str, Any]:
    """
    Check ngrok tunnel status (optional for development).
    
    Returns:
        Dict containing ngrok status and tunnel information
    """
    try:
        import httpx
        
        start_time = time.time()
        
        # Try to connect to ngrok API
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get("http://localhost:4040/api/tunnels")
            
            if response.status_code == 200:
                tunnels_data = response.json()
                tunnels = tunnels_data.get("tunnels", [])
                response_time = (time.time() - start_time) * 1000
                
                # Find tunnel for port 8000 (our API)
                api_tunnel = None
                for tunnel in tunnels:
                    if "8000" in tunnel.get("config", {}).get("addr", ""):
                        api_tunnel = tunnel
                        break
                
                if api_tunnel:
                    return {
                        "status": "healthy",
                        "message": "ngrok tunnel is active",
                        "response_time_ms": round(response_time, 2),
                        "public_url": api_tunnel.get("public_url"),
                        "tunnel_name": api_tunnel.get("name"),
                        "total_tunnels": len(tunnels)
                    }
                else:
                    return {
                        "status": "degraded",
                        "message": "ngrok is running but no tunnel found for port 8000",
                        "response_time_ms": round(response_time, 2),
                        "public_url": None,
                        "total_tunnels": len(tunnels)
                    }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"ngrok API returned status {response.status_code}",
                    "response_time_ms": 0,
                    "public_url": None
                }
                
    except Exception as e:
        # ngrok not running is not critical for production
        return {
            "status": "not_available",
            "message": "ngrok is not running (normal for production)",
            "response_time_ms": 0,
            "public_url": None
        }


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
        health_check_tasks = {
            "openai": check_openai_health(config),
            "twilio": check_twilio_health(config),
            "database": check_database_health(),
            "redis": check_redis_health(),
            "ngrok": check_ngrok_status()
        }
        
        health_results = await asyncio.gather(
            *health_check_tasks.values(),
            return_exceptions=True
        )
        
        # Process results with proper error handling
        def process_health_result(result, service_name):
            if isinstance(result, Exception):
                logger.error(f"{service_name} health check failed: {result}")
                return {
                    "status": "error",
                    "message": f"Health check failed: {str(result)[:100]}",
                    "response_time_ms": 0
                }
            return result
        
        # Map results back to named services
        service_names = list(health_check_tasks.keys())
        openai_health = process_health_result(health_results[0], "OpenAI")
        twilio_health = process_health_result(health_results[1], "Twilio")
        database_health = process_health_result(health_results[2], "Database")
        redis_health = process_health_result(health_results[3], "Redis")
        ngrok_health = process_health_result(health_results[4], "Ngrok")
        
        # Get metrics
        metrics_collector = get_metrics_collector()
        current_metrics = metrics_collector.get_current_metrics()
        
        # Determine overall health status
        # Critical services: OpenAI, Twilio, Database
        critical_statuses = [openai_health["status"], twilio_health["status"], database_health["status"]]
        # Optional services: Redis, ngrok
        optional_statuses = [redis_health["status"], ngrok_health["status"]]
        
        # Count healthy critical services
        healthy_critical = sum(1 for status in critical_statuses if status in ["healthy", "not_configured"])
        # Count healthy optional services (not_available is OK for ngrok)
        healthy_optional = sum(1 for status in optional_statuses if status in ["healthy", "not_configured", "not_available"])
        
        if healthy_critical == len(critical_statuses) and healthy_optional >= len(optional_statuses) - 1:
            overall_status = "healthy"
        elif healthy_critical >= len(critical_statuses) - 1:  # Allow one critical service to be degraded
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
                "database": database_health,
                "redis": redis_health,
                "ngrok": ngrok_health,
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


@router.get("/openai")
async def openai_health_endpoint(
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Individual health check endpoint for OpenAI service.
    
    Returns:
        Dict containing OpenAI service health status
    """
    try:
        health_result = await check_openai_health(config)
        
        if health_result["status"] in ["unhealthy", "circuit_open"]:
            return JSONResponse(
                status_code=503,
                content={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "openai",
                    **health_result
                }
            )
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "openai",
            **health_result
        }
        
    except Exception as e:
        logger.error(f"OpenAI health endpoint failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "openai",
                "status": "error",
                "message": f"Health check failed: {str(e)[:100]}"
            }
        )


@router.get("/twilio")
async def twilio_health_endpoint(
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Individual health check endpoint for Twilio service.
    
    Returns:
        Dict containing Twilio service health status
    """
    try:
        health_result = await check_twilio_health(config)
        
        if health_result["status"] in ["unhealthy", "circuit_open"]:
            return JSONResponse(
                status_code=503,
                content={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "twilio",
                    **health_result
                }
            )
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "twilio",
            **health_result
        }
        
    except Exception as e:
        logger.error(f"Twilio health endpoint failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "twilio",
                "status": "error",
                "message": f"Health check failed: {str(e)[:100]}"
            }
        )


@router.get("/database")
async def database_health_endpoint() -> Dict[str, Any]:
    """
    Individual health check endpoint for database service.
    
    Returns:
        Dict containing database service health status
    """
    try:
        health_result = await check_database_health()
        
        if health_result["status"] == "unhealthy":
            return JSONResponse(
                status_code=503,
                content={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "database",
                    **health_result
                }
            )
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "database",
            **health_result
        }
        
    except Exception as e:
        logger.error(f"Database health endpoint failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "database",
                "status": "error",
                "message": f"Health check failed: {str(e)[:100]}"
            }
        )


@router.get("/redis")
async def redis_health_endpoint() -> Dict[str, Any]:
    """
    Individual health check endpoint for Redis service.
    
    Returns:
        Dict containing Redis service health status
    """
    try:
        health_result = await check_redis_health()
        
        if health_result["status"] == "unhealthy":
            return JSONResponse(
                status_code=503,
                content={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "redis",
                    **health_result
                }
            )
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "redis",
            **health_result
        }
        
    except Exception as e:
        logger.error(f"Redis health endpoint failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "redis",
                "status": "error",
                "message": f"Health check failed: {str(e)[:100]}"
            }
        )


@router.get("/ngrok")
async def ngrok_health_endpoint() -> Dict[str, Any]:
    """
    Individual health check endpoint for ngrok service.
    
    Returns:
        Dict containing ngrok service health status
    """
    try:
        health_result = await check_ngrok_status()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "ngrok",
            **health_result
        }
        
    except Exception as e:
        logger.error(f"Ngrok health endpoint failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,  # ngrok is optional, so don't return 503
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "ngrok",
                "status": "error",
                "message": f"Health check failed: {str(e)[:100]}"
            }
        )


@router.get("/external")
async def external_services_health(
    config: AppConfig = Depends(get_app_config)
) -> Dict[str, Any]:
    """
    Combined health check for all external services.
    
    Returns:
        Dict containing health status of all external services
    """
    try:
        # Check all external services
        health_checks = await asyncio.gather(
            check_openai_health(config),
            check_twilio_health(config),
            check_ngrok_status(),
            return_exceptions=True
        )
        
        openai_health = health_checks[0] if not isinstance(health_checks[0], Exception) else {
            "status": "error", "message": f"Health check failed: {health_checks[0]}"
        }
        
        twilio_health = health_checks[1] if not isinstance(health_checks[1], Exception) else {
            "status": "error", "message": f"Health check failed: {health_checks[1]}"
        }
        
        ngrok_health = health_checks[2] if not isinstance(health_checks[2], Exception) else {
            "status": "error", "message": f"Health check failed: {health_checks[2]}"
        }
        
        # Determine overall external services status
        external_statuses = [openai_health["status"], twilio_health["status"]]
        
        if all(status in ["healthy", "not_configured"] for status in external_statuses):
            overall_status = "healthy"
        elif any(status == "healthy" for status in external_statuses):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        response = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": overall_status,
            "services": {
                "openai": openai_health,
                "twilio": twilio_health,
                "ngrok": ngrok_health
            }
        }
        
        if overall_status == "unhealthy":
            return JSONResponse(status_code=503, content=response)
        elif overall_status == "degraded":
            return JSONResponse(status_code=200, content=response, headers={"X-Health-Status": "degraded"})
        else:
            return response
            
    except Exception as e:
        logger.error(f"External services health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "message": f"External services health check failed: {str(e)[:100]}"
            }
        )