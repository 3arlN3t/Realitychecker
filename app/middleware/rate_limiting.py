"""Rate limiting middleware for API endpoints."""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.logging import get_logger, sanitize_phone_number

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    burst_limit: int = 5  # Maximum requests in a 10-second window
    burst_window: int = 10  # Burst window in seconds


class RateLimiter:
    """Thread-safe rate limiter with multiple time windows."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._lock = Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed based on rate limiting rules.
        
        Args:
            identifier: Unique identifier for the client (IP, phone number, etc.)
            
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        current_time = time.time()
        
        with self._lock:
            # Get or create request history for this identifier
            requests = self._requests[identifier]
            
            # Clean up old requests outside all windows
            cutoff_time = current_time - 3600  # Keep 1 hour of history
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Check burst limit (requests in last 10 seconds)
            burst_cutoff = current_time - self.config.burst_window
            burst_count = sum(1 for req_time in requests if req_time > burst_cutoff)
            
            if burst_count >= self.config.burst_limit:
                return False, f"Burst limit exceeded ({self.config.burst_limit} requests per {self.config.burst_window}s)"
            
            # Check per-minute limit
            minute_cutoff = current_time - 60
            minute_count = sum(1 for req_time in requests if req_time > minute_cutoff)
            
            if minute_count >= self.config.requests_per_minute:
                return False, f"Rate limit exceeded ({self.config.requests_per_minute} requests per minute)"
            
            # Check per-hour limit
            hour_cutoff = current_time - 3600
            hour_count = sum(1 for req_time in requests if req_time > hour_cutoff)
            
            if hour_count >= self.config.requests_per_hour:
                return False, f"Rate limit exceeded ({self.config.requests_per_hour} requests per hour)"
            
            # Record this request
            requests.append(current_time)
            
            return True, None
    
    def get_stats(self, identifier: str) -> Dict[str, int]:
        """
        Get current usage statistics for an identifier.
        
        Args:
            identifier: Client identifier
            
        Returns:
            Dictionary with current usage counts
        """
        current_time = time.time()
        
        with self._lock:
            requests = self._requests.get(identifier, deque())
            
            # Count requests in different time windows
            burst_count = sum(1 for req_time in requests if req_time > current_time - self.config.burst_window)
            minute_count = sum(1 for req_time in requests if req_time > current_time - 60)
            hour_count = sum(1 for req_time in requests if req_time > current_time - 3600)
            
            return {
                "burst_count": burst_count,
                "minute_count": minute_count,
                "hour_count": hour_count,
                "burst_limit": self.config.burst_limit,
                "minute_limit": self.config.requests_per_minute,
                "hour_limit": self.config.requests_per_hour
            }
    
    def cleanup_old_entries(self):
        """Clean up old entries to prevent memory leaks."""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep 1 hour of history
        
        with self._lock:
            # Clean up old requests for all identifiers
            identifiers_to_remove = []
            
            for identifier, requests in self._requests.items():
                # Remove old requests
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # If no recent requests, remove the identifier entirely
                if not requests:
                    identifiers_to_remove.append(identifier)
            
            # Remove empty identifiers
            for identifier in identifiers_to_remove:
                del self._requests[identifier]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.rate_limiter = RateLimiter(self.config)
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks and non-webhook endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (prefer phone number from webhook, fallback to IP)
        identifier = self._get_client_identifier(request)
        
        # Check rate limits
        allowed, reason = self.rate_limiter.is_allowed(identifier)
        
        if not allowed:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for client {sanitize_phone_number(identifier)}: {reason}",
                extra={
                    "client_identifier": sanitize_phone_number(identifier),
                    "endpoint": request.url.path,
                    "method": request.method,
                    "reason": reason
                }
            )
            
            # Get current stats for response headers
            stats = self.rate_limiter.get_stats(identifier)
            
            # Return rate limit error
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "retry_after": 60,  # Suggest retry after 1 minute
                    "limits": {
                        "burst": f"{stats['burst_count']}/{stats['burst_limit']} per {self.config.burst_window}s",
                        "minute": f"{stats['minute_count']}/{stats['minute_limit']} per minute",
                        "hour": f"{stats['hour_count']}/{stats['hour_limit']} per hour"
                    }
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit-Minute": str(self.config.requests_per_minute),
                    "X-RateLimit-Limit-Hour": str(self.config.requests_per_hour),
                    "X-RateLimit-Remaining-Minute": str(max(0, self.config.requests_per_minute - stats['minute_count'])),
                    "X-RateLimit-Remaining-Hour": str(max(0, self.config.requests_per_hour - stats['hour_count']))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        stats = self.rate_limiter.get_stats(identifier)
        response.headers["X-RateLimit-Limit-Minute"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.config.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.config.requests_per_minute - stats['minute_count']))
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, self.config.requests_per_hour - stats['hour_count']))
        
        # Periodic cleanup to prevent memory leaks
        current_time = time.time()
        if current_time - self.last_cleanup > 300:  # Cleanup every 5 minutes
            self.rate_limiter.cleanup_old_entries()
            self.last_cleanup = current_time
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client making the request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Unique identifier string
        """
        # For webhook requests, try to get the phone number from form data
        if request.url.path.startswith("/webhook") and request.method == "POST":
            # Try to get phone number from form data (this requires reading the body)
            # For now, we'll use a combination of IP and User-Agent
            # In a real implementation, you might want to parse the form data
            pass
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Consider X-Forwarded-For header for reverse proxy setups
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Consider X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip.strip()
        
        return client_ip


def create_rate_limit_middleware(
    requests_per_minute: int = 10,
    requests_per_hour: int = 100,
    burst_limit: int = 5,
    burst_window: int = 10
) -> RateLimitMiddleware:
    """
    Create a rate limiting middleware with custom configuration.
    
    Args:
        requests_per_minute: Maximum requests per minute
        requests_per_hour: Maximum requests per hour
        burst_limit: Maximum requests in burst window
        burst_window: Burst window duration in seconds
        
    Returns:
        Configured RateLimitMiddleware instance
    """
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        burst_limit=burst_limit,
        burst_window=burst_window
    )
    
    return lambda app: RateLimitMiddleware(app, config)