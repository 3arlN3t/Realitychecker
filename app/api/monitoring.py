"""
Real-time monitoring endpoints for WebSocket connections and metrics.

This module provides WebSocket endpoints for real-time monitoring and
metrics broadcasting to dashboard clients.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.websocket import get_websocket_manager
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker
from app.utils.logging import get_logger
from app.services.authentication import AuthenticationService
from app.dependencies import get_auth_service
from app.database.connection_pool import get_pool_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])
security = HTTPBearer()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    WebSocket endpoint for real-time monitoring updates.
    
    Args:
        websocket: The WebSocket connection
        token: Authentication token (optional)
        auth_service: Authentication service
    """
    # Validate token if provided
    user_id = "anonymous"
    
    if token:
        try:
            validation = await auth_service.validate_jwt_token(token)
            if validation.valid:
                user_id = validation.user_id
            else:
                await websocket.close(code=1008, reason="Invalid authentication token")
                return
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    
    # Accept connection
    manager = get_websocket_manager()
    
    try:
        await manager.connect(websocket, user_id)
        
        # Send initial metrics
        metrics_collector = get_metrics_collector()
        current_metrics = metrics_collector.get_current_metrics()
        
        await websocket.send_json({
            "type": "metrics_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": current_metrics
        })
        
        # Send active alerts
        error_tracker = get_error_tracker()
        active_alerts = error_tracker.get_active_alerts()
        
        if active_alerts:
            alerts_data = []
            for alert in active_alerts:
                alerts_data.append({
                    "id": alert.id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "context": alert.context
                })
            
            await websocket.send_json({
                "type": "active_alerts",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": alerts_data
            })
        
        # Keep connection alive until client disconnects
        while True:
            data = await websocket.receive_text()
            try:
                # Handle client messages (e.g., ping/pong)
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


@router.get("/active-requests")
async def get_active_requests(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Get currently active requests being processed by the system.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service
        
    Returns:
        Dict containing active requests information
    """
    # Validate token
    validation = await auth_service.validate_jwt_token(credentials.credentials)
    if not validation.valid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Get active requests from metrics collector
    metrics_collector = get_metrics_collector()
    current_metrics = metrics_collector.get_current_metrics()
    
    # In a real implementation, you would track active requests
    # Here we're returning sample data based on metrics
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_requests": [
            {
                "id": "req-1",
                "type": "text_analysis",
                "status": "processing",
                "started_at": (datetime.now(timezone.utc)).isoformat(),
                "duration_ms": 1200,
                "user": "+1234567890"
            },
            {
                "id": "req-2",
                "type": "pdf_processing",
                "status": "downloading",
                "started_at": (datetime.now(timezone.utc)).isoformat(),
                "duration_ms": 800,
                "user": "+0987654321"
            }
        ],
        "queue_depth": 0,
        "processing_capacity": {
            "used": 2,
            "total": 10,
            "percent": 20.0
        }
    }


@router.get("/error-rates")
async def get_error_rates(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
    period: str = "hour"  # hour, day, week
) -> Dict[str, Any]:
    """
    Get error rates over time.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service
        period: Time period for error rates
        
    Returns:
        Dict containing error rate data
    """
    # Validate token
    validation = await auth_service.validate_jwt_token(credentials.credentials)
    if not validation.valid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Get error tracker
    error_tracker = get_error_tracker()
    error_summary = error_tracker.get_error_summary(hours=24 if period == "day" else 1)
    
    # In a real implementation, you would aggregate error data by time
    # Here we're returning sample data based on error summary
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period": period,
        "error_rates": [
            {
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "error_rate": 2.5,
                "total_requests": 120,
                "error_count": 3
            },
            {
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "error_rate": 1.8,
                "total_requests": 110,
                "error_count": 2
            }
        ],
        "components": error_summary.get("components", {}),
        "total_errors": sum(
            comp.get("total_errors", 0) 
            for comp in error_summary.get("components", {}).values()
        )
    }


@router.get("/response-times")
async def get_response_times(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
    period: str = "hour"  # hour, day, week
) -> Dict[str, Any]:
    """
    Get response times over time.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service
        period: Time period for response times
        
    Returns:
        Dict containing response time data
    """
    # Validate token
    validation = await auth_service.validate_jwt_token(credentials.credentials)
    if not validation.valid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Get metrics collector
    metrics_collector = get_metrics_collector()
    current_metrics = metrics_collector.get_current_metrics()
    
    # In a real implementation, you would aggregate response time data by time
    # Here we're returning sample data based on current metrics
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period": period,
        "response_times": [
            {
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "avg_response_time": 1.2,
                "p50": 0.9,
                "p95": 2.1,
                "p99": 3.5,
                "total_requests": 120
            },
            {
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "avg_response_time": 1.0,
                "p50": 0.8,
                "p95": 1.9,
                "p99": 3.2,
                "total_requests": 110
            }
        ],
        "services": current_metrics.get("services", {}),
        "current": {
            "avg_response_time": current_metrics.get("requests", {}).get("avg_response_time_seconds", 0),
            "total_requests": current_metrics.get("requests", {}).get("total", 0)
        }
    }


@router.get("/connection-pool")
async def get_connection_pool_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Get comprehensive connection pool status and metrics.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service
        
    Returns:
        Dict containing connection pool status and metrics
    """
    # Validate token
    validation = await auth_service.validate_jwt_token(credentials.credentials)
    if not validation.valid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    try:
        # Get pool manager and stats
        pool_manager = get_pool_manager()
        pool_stats = await pool_manager.get_pool_stats()
        health_status = await pool_manager.health_check()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy" if health_status["database"]["status"] == "healthy" else "degraded",
            "pool_stats": pool_stats,
            "health_check": health_status,
            "recommendations": _generate_pool_recommendations(pool_stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting connection pool status: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": str(e),
            "pool_stats": {},
            "health_check": {},
            "recommendations": []
        }


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Get status of all circuit breakers in the system.
    
    Args:
        credentials: HTTP Authorization credentials
        auth_service: Authentication service
        
    Returns:
        Dict containing circuit breaker statuses
    """
    # Validate token
    validation = await auth_service.validate_jwt_token(credentials.credentials)
    if not validation.valid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    try:
        from app.utils.circuit_breaker import get_circuit_breaker_manager
        
        # Get all circuit breaker statuses
        cb_manager = get_circuit_breaker_manager()
        all_statuses = cb_manager.get_all_status()
        
        # Add database circuit breaker from pool manager
        pool_manager = get_pool_manager()
        db_cb_status = pool_manager.get_circuit_breaker_status()
        if db_cb_status.get("name"):
            all_statuses[db_cb_status["name"]] = db_cb_status
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "circuit_breakers": all_statuses,
            "summary": {
                "total": len(all_statuses),
                "open": sum(1 for cb in all_statuses.values() if cb.get("state") == "open"),
                "half_open": sum(1 for cb in all_statuses.values() if cb.get("state") == "half_open"),
                "closed": sum(1 for cb in all_statuses.values() if cb.get("state") == "closed")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "circuit_breakers": {},
            "summary": {"total": 0, "open": 0, "half_open": 0, "closed": 0}
        }


def _generate_pool_recommendations(pool_stats: Dict[str, Any]) -> list:
    """Generate recommendations based on pool statistics."""
    recommendations = []
    
    utilization = pool_stats.get("utilization", 0)
    pool_config = pool_stats.get("pool_config", {})
    
    # High utilization warnings
    if utilization >= 0.95:
        recommendations.append({
            "type": "critical",
            "message": f"Connection pool utilization is critically high ({utilization:.1%}). Consider increasing pool size immediately.",
            "action": "Increase DB_POOL_SIZE and DB_MAX_OVERFLOW environment variables"
        })
    elif utilization >= 0.8:
        recommendations.append({
            "type": "warning",
            "message": f"Connection pool utilization is high ({utilization:.1%}). Monitor for scaling needs.",
            "action": "Consider increasing pool size if utilization remains high"
        })
    
    # Circuit breaker recommendations
    circuit_breaker = pool_stats.get("circuit_breaker", {})
    if circuit_breaker.get("state") == "open":
        recommendations.append({
            "type": "critical",
            "message": "Database circuit breaker is OPEN. Database connections are failing.",
            "action": "Check database connectivity and health. Review error logs."
        })
    elif circuit_breaker.get("state") == "half_open":
        recommendations.append({
            "type": "warning",
            "message": "Database circuit breaker is HALF_OPEN. System is testing database recovery.",
            "action": "Monitor circuit breaker status. It should close automatically if database is healthy."
        })
    
    # Health check recommendations
    failed_health_checks = pool_stats.get("failed_health_checks", 0)
    total_health_checks = pool_stats.get("health_checks", 0)
    if total_health_checks > 0 and failed_health_checks / total_health_checks > 0.1:
        recommendations.append({
            "type": "warning",
            "message": f"High health check failure rate ({failed_health_checks}/{total_health_checks})",
            "action": "Investigate database connectivity issues"
        })
    
    # Redis recommendations
    redis_stats = pool_stats.get("redis", {})
    if redis_stats.get("status") == "unavailable":
        recommendations.append({
            "type": "warning",
            "message": "Redis cache is unavailable. Performance may be degraded.",
            "action": "Check Redis connectivity and configuration"
        })
    elif redis_stats.get("hit_rate", 0) < 0.5:
        recommendations.append({
            "type": "info",
            "message": f"Redis cache hit rate is low ({redis_stats.get('hit_rate', 0):.1%})",
            "action": "Consider adjusting cache TTL settings or cache key strategies"
        })
    
    return recommendations