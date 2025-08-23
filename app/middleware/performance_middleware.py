"""
Performance monitoring middleware for FastAPI.

This middleware integrates with the performance monitoring service to track
request metrics, response times, and system performance in real-time.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging import get_logger
from app.services.performance_monitor import get_performance_monitor

logger = get_logger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking request performance metrics.
    """
    
    def __init__(self, app, exclude_paths: list = None):
        """
        Initialize performance middleware.
        
        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from monitoring
        """
        super().__init__(app)
        self.performance_monitor = get_performance_monitor()
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/static/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with performance monitoring.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with performance headers
        """
        # Check if path should be excluded from monitoring
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Record request start
        request_id = self.performance_monitor.record_request_start()
        start_time = time.time()
        
        # Add request ID to request state for tracking
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Determine if request was successful
            success = 200 <= response.status_code < 400
            
            # Record request end
            self.performance_monitor.record_request_end(
                request_id, 
                response_time, 
                success
            )
            
            # Add performance headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}"
            response.headers["X-Performance-Monitored"] = "true"
            
            # Log performance metrics for slow requests
            if response_time > 1.0:  # Log requests slower than 1 second
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {response_time:.3f}s (status: {response.status_code})",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                )
            
            return response
            
        except Exception as e:
            # Calculate response time for failed requests
            response_time = time.time() - start_time
            
            # Record failed request
            self.performance_monitor.record_request_end(
                request_id, 
                response_time, 
                success=False
            )
            
            # Log error with performance context
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {response_time:.3f}s - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "response_time": response_time,
                    "error": str(e)
                }
            )
            
            # Re-raise the exception
            raise


def create_performance_middleware(exclude_paths: list = None) -> type:
    """
    Create performance middleware with custom configuration.
    
    Args:
        exclude_paths: List of paths to exclude from monitoring
        
    Returns:
        Configured middleware class
    """
    class ConfiguredPerformanceMiddleware(PerformanceMiddleware):
        def __init__(self, app):
            super().__init__(app, exclude_paths)
    
    return ConfiguredPerformanceMiddleware