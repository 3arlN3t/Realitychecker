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