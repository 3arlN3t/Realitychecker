"""
Performance monitoring API endpoints.

This module provides API endpoints for accessing performance metrics,
system health, and monitoring data.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta

from app.dependencies import require_admin_user, get_current_active_user
from app.models.data_models import User
from app.services.performance_monitor import get_performance_monitor
from app.services.caching_service import get_caching_service
from app.database.connection_pool import get_pool_manager
from app.database.query_optimizer import get_query_optimizer
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current performance metrics.
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        performance_monitor = get_performance_monitor()
        metrics = await performance_monitor.get_performance_summary()
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/system")
async def get_system_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current system resource metrics.
    
    Returns:
        Dictionary with system metrics
    """
    try:
        performance_monitor = get_performance_monitor()
        system_metrics = await performance_monitor.get_system_metrics()
        
        return {
            "status": "success",
            "data": system_metrics.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.get("/application")
async def get_application_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current application metrics.
    
    Returns:
        Dictionary with application metrics
    """
    try:
        performance_monitor = get_performance_monitor()
        app_metrics = await performance_monitor.get_application_metrics()
        
        return {
            "status": "success",
            "data": app_metrics.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve application metrics")


@router.get("/cache")
async def get_cache_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get cache performance metrics.
    
    Returns:
        Dictionary with cache metrics
    """
    try:
        caching_service = get_caching_service()
        cache_stats = await caching_service.get_cache_stats()
        
        return {
            "status": "success",
            "data": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache metrics")


@router.get("/database")
async def get_database_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get database performance metrics.
    
    Returns:
        Dictionary with database metrics
    """
    try:
        pool_manager = get_pool_manager()
        pool_stats = await pool_manager.get_pool_stats()
        health_check = await pool_manager.health_check()
        
        return {
            "status": "success",
            "data": {
                "pool_stats": pool_stats,
                "health_check": health_check
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database metrics")


@router.get("/queries")
async def get_query_performance(
    current_user: User = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Get query performance statistics (admin only).
    
    Returns:
        Dictionary with query performance data
    """
    try:
        query_optimizer = get_query_optimizer()
        query_stats = query_optimizer.get_query_statistics()
        
        return {
            "status": "success",
            "data": query_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get query performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve query performance")


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(..., description="Cache key pattern to invalidate"),
    current_user: User = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Invalidate cache entries matching pattern (admin only).
    
    Args:
        pattern: Cache key pattern (e.g., "user:*")
        
    Returns:
        Success message
    """
    try:
        caching_service = get_caching_service()
        success = await caching_service.invalidate_pattern(pattern)
        
        if success:
            logger.info(f"Cache invalidated by admin {current_user.username}: {pattern}")
            return {
                "status": "success",
                "message": f"Cache pattern '{pattern}' invalidated successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to invalidate cache")
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.post("/cache/warm")
async def warm_cache(
    current_user: User = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Warm up cache with frequently accessed data (admin only).
    
    Returns:
        Success message
    """
    try:
        caching_service = get_caching_service()
        await caching_service.warm_cache()
        
        logger.info(f"Cache warmed by admin {current_user.username}")
        return {
            "status": "success",
            "message": "Cache warmed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to warm cache")


@router.get("/thresholds")
async def get_performance_thresholds(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get performance monitoring thresholds.
    
    Returns:
        Dictionary with performance thresholds
    """
    try:
        performance_monitor = get_performance_monitor()
        
        return {
            "status": "success",
            "data": performance_monitor.thresholds,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance thresholds")


@router.put("/thresholds")
async def update_performance_thresholds(
    thresholds: Dict[str, float],
    current_user: User = Depends(require_admin_user)
) -> Dict[str, Any]:
    """
    Update performance monitoring thresholds (admin only).
    
    Args:
        thresholds: Dictionary of threshold values to update
        
    Returns:
        Success message with updated thresholds
    """
    try:
        performance_monitor = get_performance_monitor()
        
        # Validate and update thresholds
        valid_threshold_keys = {
            "response_time_warning", "response_time_critical",
            "cpu_warning", "cpu_critical",
            "memory_warning", "memory_critical",
            "error_rate_warning", "error_rate_critical"
        }
        
        updated_thresholds = {}
        for key, value in thresholds.items():
            if key in valid_threshold_keys and isinstance(value, (int, float)) and value > 0:
                performance_monitor.thresholds[key] = float(value)
                updated_thresholds[key] = float(value)
        
        if updated_thresholds:
            logger.info(f"Performance thresholds updated by admin {current_user.username}: {updated_thresholds}")
            return {
                "status": "success",
                "message": "Performance thresholds updated successfully",
                "updated_thresholds": updated_thresholds,
                "current_thresholds": performance_monitor.thresholds,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="No valid thresholds provided")
        
    except Exception as e:
        logger.error(f"Failed to update performance thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to update performance thresholds")


@router.get("/alerts")
async def get_performance_alerts(
    hours: int = Query(24, description="Number of hours to look back for alerts"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get recent performance alerts.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        List of recent performance alerts
    """
    try:
        # TODO: Implement alert storage and retrieval
        # For now, return placeholder data
        
        return {
            "status": "success",
            "data": {
                "alerts": [],
                "total_count": 0,
                "time_range_hours": hours
            },
            "message": "Alert history feature coming soon",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance alerts")