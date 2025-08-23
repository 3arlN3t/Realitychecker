"""
Enhanced per-user rate limiting with Redis-based sliding window.

This module provides sophisticated rate limiting on a per-user basis using
Redis for distributed rate limiting with sliding window algorithm.
"""

import asyncio
import time
import hashlib
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis

from app.utils.logging import get_logger, sanitize_phone_number, get_correlation_id

logger = get_logger(__name__)


@dataclass
class UserRateLimitConfig:
    """Configuration for per-user rate limiting."""
    # Basic user limits
    requests_per_minute: int = 5      # Reduced from global limit
    requests_per_hour: int = 50       # Reduced from global limit
    requests_per_day: int = 200       # Daily limit for abuse prevention
    
    # Burst protection
    burst_limit: int = 3              # Maximum requests in burst window
    burst_window: int = 10            # Burst window in seconds
    
    # Progressive limits for established users
    trusted_user_multiplier: float = 2.0  # 2x limits for trusted users
    trusted_user_threshold: int = 20      # Requests needed to become trusted
    
    # Redis configuration
    redis_key_prefix: str = "rate_limit:user:"
    redis_ttl: int = 86400            # 24 hours TTL for cleanup


class RedisUserRateLimiter:
    """Redis-based per-user rate limiter with sliding window algorithm."""
    
    def __init__(self, config: UserRateLimitConfig, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the rate limiter.
        
        Args:
            config: Rate limiting configuration
            redis_client: Optional Redis client (will create if None)
        """
        self.config = config
        self.redis_client = redis_client
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection if needed."""
        if self._initialized:
            return
        
        if self.redis_client is None:
            try:
                # Try to connect to Redis
                self.redis_client = redis.from_url(
                    "redis://localhost:6379",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("✅ Connected to Redis for user rate limiting")
            except Exception as e:
                logger.warning(f"❌ Redis not available, falling back to in-memory rate limiting: {e}")
                self.redis_client = None
        
        self._initialized = True
    
    def _get_user_key(self, phone_number: str) -> str:
        """
        Generate Redis key for user rate limiting data.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Redis key for this user
        """
        # Hash phone number for privacy
        phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()[:16]
        return f"{self.config.redis_key_prefix}{phone_hash}"
    
    def _get_window_keys(self, user_key: str) -> Dict[str, str]:
        """Get Redis keys for different time windows."""
        return {
            "minute": f"{user_key}:minute",
            "hour": f"{user_key}:hour", 
            "day": f"{user_key}:day",
            "burst": f"{user_key}:burst",
            "total": f"{user_key}:total"  # For trusted user calculation
        }
    
    async def is_allowed(self, phone_number: str) -> Tuple[bool, Optional[str], Dict[str, int]]:
        """
        Check if request is allowed for this user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Tuple of (is_allowed, reason_if_blocked, current_stats)
        """
        await self.initialize()
        
        if self.redis_client is None:
            # Fallback to allowing all requests if Redis unavailable
            logger.warning("Redis unavailable, allowing request")
            return True, None, {}
        
        correlation_id = get_correlation_id()
        current_time = time.time()
        user_key = self._get_user_key(phone_number)
        window_keys = self._get_window_keys(user_key)
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Get current counts for all windows
            pipe.zcount(window_keys["burst"], current_time - self.config.burst_window, current_time)
            pipe.zcount(window_keys["minute"], current_time - 60, current_time)
            pipe.zcount(window_keys["hour"], current_time - 3600, current_time)
            pipe.zcount(window_keys["day"], current_time - 86400, current_time)
            pipe.zcard(window_keys["total"])  # Total requests for trusted user check
            
            counts = await pipe.execute()
            burst_count, minute_count, hour_count, day_count, total_count = counts
            
            # Check if user is trusted (gets higher limits)
            is_trusted = total_count >= self.config.trusted_user_threshold
            multiplier = self.config.trusted_user_multiplier if is_trusted else 1.0
            
            # Calculate effective limits
            effective_limits = {
                "burst": int(self.config.burst_limit * multiplier),
                "minute": int(self.config.requests_per_minute * multiplier),
                "hour": int(self.config.requests_per_hour * multiplier),
                "day": int(self.config.requests_per_day * multiplier)
            }
            
            # Check limits in order of severity
            if burst_count >= effective_limits["burst"]:
                return False, f"Burst limit exceeded ({effective_limits['burst']} per {self.config.burst_window}s)", {
                    "burst_count": burst_count,
                    "minute_count": minute_count,
                    "hour_count": hour_count,
                    "day_count": day_count,
                    "is_trusted": is_trusted,
                    "limits": effective_limits
                }
            
            if minute_count >= effective_limits["minute"]:
                return False, f"Per-minute limit exceeded ({effective_limits['minute']} per minute)", {
                    "burst_count": burst_count,
                    "minute_count": minute_count,
                    "hour_count": hour_count,
                    "day_count": day_count,
                    "is_trusted": is_trusted,
                    "limits": effective_limits
                }
            
            if hour_count >= effective_limits["hour"]:
                return False, f"Hourly limit exceeded ({effective_limits['hour']} per hour)", {
                    "burst_count": burst_count,
                    "minute_count": minute_count,
                    "hour_count": hour_count,
                    "day_count": day_count,
                    "is_trusted": is_trusted,
                    "limits": effective_limits
                }
            
            if day_count >= effective_limits["day"]:
                return False, f"Daily limit exceeded ({effective_limits['day']} per day)", {
                    "burst_count": burst_count,
                    "minute_count": minute_count,
                    "hour_count": hour_count,
                    "day_count": day_count,
                    "is_trusted": is_trusted,
                    "limits": effective_limits
                }
            
            # All checks passed - record the request
            await self._record_request(window_keys, current_time)
            
            logger.debug(
                f"User rate limit check passed",
                extra={
                    "phone": sanitize_phone_number(phone_number),
                    "burst_count": burst_count,
                    "minute_count": minute_count,
                    "hour_count": hour_count,
                    "day_count": day_count,
                    "is_trusted": is_trusted,
                    "correlation_id": correlation_id
                }
            )
            
            return True, None, {
                "burst_count": burst_count + 1,  # Include current request
                "minute_count": minute_count + 1,
                "hour_count": hour_count + 1,
                "day_count": day_count + 1,
                "is_trusted": is_trusted,
                "limits": effective_limits
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}", extra={"correlation_id": correlation_id})
            # On error, allow the request but log the issue
            return True, None, {}
    
    async def _record_request(self, window_keys: Dict[str, str], current_time: float):
        """
        Record a request in all time windows using Redis sorted sets.
        
        Args:
            window_keys: Redis keys for different time windows
            current_time: Current timestamp
        """
        pipe = self.redis_client.pipeline()
        
        # Add current request to all windows with cleanup
        for window, key in window_keys.items():
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set TTL for cleanup
            pipe.expire(key, self.config.redis_ttl)
            
            # Clean up old entries based on window
            if window == "burst":
                cutoff = current_time - self.config.burst_window
            elif window == "minute":
                cutoff = current_time - 60
            elif window == "hour":
                cutoff = current_time - 3600
            elif window == "day":
                cutoff = current_time - 86400
            else:  # total
                cutoff = current_time - (86400 * 30)  # Keep 30 days for trusted user calculation
            
            pipe.zremrangebyscore(key, 0, cutoff)
        
        await pipe.execute()
    
    async def get_user_stats(self, phone_number: str) -> Dict[str, int]:
        """
        Get current usage statistics for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Dictionary with current usage counts and limits
        """
        await self.initialize()
        
        if self.redis_client is None:
            return {}
        
        current_time = time.time()
        user_key = self._get_user_key(phone_number)
        window_keys = self._get_window_keys(user_key)
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Get counts for all windows
            pipe.zcount(window_keys["burst"], current_time - self.config.burst_window, current_time)
            pipe.zcount(window_keys["minute"], current_time - 60, current_time)
            pipe.zcount(window_keys["hour"], current_time - 3600, current_time)
            pipe.zcount(window_keys["day"], current_time - 86400, current_time)
            pipe.zcard(window_keys["total"])
            
            counts = await pipe.execute()
            burst_count, minute_count, hour_count, day_count, total_count = counts
            
            # Check if user is trusted
            is_trusted = total_count >= self.config.trusted_user_threshold
            multiplier = self.config.trusted_user_multiplier if is_trusted else 1.0
            
            return {
                "burst_count": burst_count,
                "minute_count": minute_count,
                "hour_count": hour_count,
                "day_count": day_count,
                "total_requests": total_count,
                "is_trusted": is_trusted,
                "burst_limit": int(self.config.burst_limit * multiplier),
                "minute_limit": int(self.config.requests_per_minute * multiplier),
                "hour_limit": int(self.config.requests_per_hour * multiplier),
                "day_limit": int(self.config.requests_per_day * multiplier)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for per-user rate limiting on WhatsApp endpoints."""
    
    def __init__(self, app, config: UserRateLimitConfig):
        """
        Initialize the middleware.
        
        Args:
            app: FastAPI application
            config: Rate limiting configuration
        """
        super().__init__(app)
        self.rate_limiter = RedisUserRateLimiter(config)
        self.config = config
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with user-based rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
        """
        # Only apply rate limiting to WhatsApp webhook endpoints
        if not request.url.path.startswith('/webhook/whatsapp'):
            return await call_next(request)
        
        # Extract phone number from request
        phone_number = await self._extract_phone_number(request)
        if not phone_number:
            # If no phone number, let global rate limiting handle it
            return await call_next(request)
        
        # Check rate limits
        allowed, reason, stats = await self.rate_limiter.is_allowed(phone_number)
        
        if not allowed:
            logger.warning(
                f"User rate limit exceeded",
                extra={
                    "phone": sanitize_phone_number(phone_number),
                    "reason": reason,
                    "stats": stats,
                    "correlation_id": get_correlation_id()
                }
            )
            
            return Response(
                content=f"Rate limit exceeded: {reason}",
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(stats.get("limits", {}).get("minute", 0)),
                    "X-RateLimit-Remaining": str(max(0, 
                        stats.get("limits", {}).get("minute", 0) - stats.get("minute_count", 0)
                    )),
                    "X-RateLimit-Reset": str(int(time.time() + 60)),
                    "Retry-After": "60"
                }
            )
        
        # Add rate limit headers to successful responses
        response = await call_next(request)
        
        if stats:
            limits = stats.get("limits", {})
            response.headers["X-RateLimit-Limit"] = str(limits.get("minute", 0))
            response.headers["X-RateLimit-Remaining"] = str(max(0, 
                limits.get("minute", 0) - stats.get("minute_count", 0)
            ))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            if stats.get("is_trusted"):
                response.headers["X-RateLimit-Trusted-User"] = "true"
        
        return response
    
    async def _extract_phone_number(self, request: Request) -> Optional[str]:
        """
        Extract phone number from WhatsApp webhook request.
        
        Args:
            request: HTTP request
            
        Returns:
            Phone number if found, None otherwise
        """
        try:
            if request.method == "POST":
                # Get form data from webhook
                form = await request.form()
                from_number = form.get("From", "")
                
                # Clean up WhatsApp format (whatsapp:+1234567890 -> +1234567890)
                if from_number.startswith("whatsapp:"):
                    from_number = from_number[9:]
                
                return from_number if from_number.startswith("+") else None
        
        except Exception as e:
            logger.warning(f"Could not extract phone number from request: {e}")
            return None


def create_user_rate_limit_middleware(
    requests_per_minute: int = 5,
    requests_per_hour: int = 50,
    requests_per_day: int = 200,
    burst_limit: int = 3,
    trusted_user_multiplier: float = 2.0
) -> type:
    """
    Create user rate limiting middleware with specified configuration.
    
    Args:
        requests_per_minute: Base requests per minute limit
        requests_per_hour: Base requests per hour limit  
        requests_per_day: Base requests per day limit
        burst_limit: Maximum burst requests
        trusted_user_multiplier: Multiplier for trusted users
        
    Returns:
        Configured middleware class
    """
    config = UserRateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        requests_per_day=requests_per_day,
        burst_limit=burst_limit,
        trusted_user_multiplier=trusted_user_multiplier
    )
    
    class ConfiguredUserRateLimitMiddleware(UserRateLimitMiddleware):
        def __init__(self, app):
            super().__init__(app, config)
    
    return ConfiguredUserRateLimitMiddleware