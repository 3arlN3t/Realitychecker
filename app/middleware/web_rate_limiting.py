"""
Hybrid web rate limiting middleware with session, IP, and fingerprinting.

This module provides sophisticated rate limiting for web users using multiple
identification methods with progressive tiers and abuse detection.
"""

import asyncio
import time
import hashlib
import json
import uuid
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis

from app.utils.logging import get_logger, get_correlation_id

logger = get_logger(__name__)


@dataclass
class WebRateLimitConfig:
    """Configuration for web-based rate limiting with progressive tiers."""
    
    # Anonymous user limits (most restrictive)
    anonymous_requests_per_minute: int = 3
    anonymous_requests_per_hour: int = 20  
    anonymous_requests_per_day: int = 50
    anonymous_burst_limit: int = 2
    
    # Session-based user limits (moderate)
    session_requests_per_minute: int = 6
    session_requests_per_hour: int = 40
    session_requests_per_day: int = 150
    session_burst_limit: int = 4
    
    # Established user limits (most generous)
    established_requests_per_minute: int = 10
    established_requests_per_hour: int = 80
    established_requests_per_day: int = 300
    established_burst_limit: int = 6
    
    # Progression thresholds
    session_establishment_requests: int = 5  # Requests to become established
    suspicious_behavior_threshold: int = 20  # Requests that trigger suspicion
    
    # Fingerprinting and abuse detection
    enable_fingerprinting: bool = True
    max_sessions_per_ip: int = 10  # Max sessions allowed per IP
    suspicious_pattern_penalty_minutes: int = 30
    
    # Session management
    session_cookie_name: str = "reality_checker_session"
    session_ttl: int = 86400  # 24 hours
    
    # Redis configuration
    redis_key_prefix: str = "web_rate_limit:"
    redis_ttl: int = 86400


class BrowserFingerprinter:
    """Generate browser fingerprints for abuse detection."""
    
    @staticmethod
    def generate_fingerprint(request: Request) -> str:
        """
        Generate browser fingerprint from request headers and characteristics.
        
        Args:
            request: HTTP request object
            
        Returns:
            Browser fingerprint hash
        """
        fingerprint_data = {
            "user_agent": request.headers.get("user-agent", ""),
            "accept": request.headers.get("accept", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
            "connection": request.headers.get("connection", ""),
            "upgrade_insecure_requests": request.headers.get("upgrade-insecure-requests", ""),
            "sec_fetch_dest": request.headers.get("sec-fetch-dest", ""),
            "sec_fetch_mode": request.headers.get("sec-fetch-mode", ""),
            "sec_fetch_site": request.headers.get("sec-fetch-site", ""),
            # Include some derived characteristics
            "has_cookie": bool(request.headers.get("cookie")),
            "has_referer": bool(request.headers.get("referer")),
        }
        
        # Create a stable hash
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
    
    @staticmethod
    def detect_suspicious_patterns(request: Request) -> List[str]:
        """
        Detect suspicious patterns in the request.
        
        Args:
            request: HTTP request object
            
        Returns:
            List of detected suspicious patterns
        """
        suspicious_patterns = []
        
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Check for bot-like user agents
        bot_indicators = ["bot", "crawler", "spider", "scraper", "automated"]
        if any(indicator in user_agent for indicator in bot_indicators):
            suspicious_patterns.append("bot_user_agent")
        
        # Check for missing common headers
        if not request.headers.get("accept"):
            suspicious_patterns.append("missing_accept_header")
            
        if not request.headers.get("accept-language"):
            suspicious_patterns.append("missing_accept_language")
        
        # Check for unusual referrer patterns
        referer = request.headers.get("referer", "")
        if referer and not any(domain in referer for domain in ["localhost", "127.0.0.1"] + [request.url.hostname]):
            suspicious_patterns.append("external_referer")
        
        # Check for rapid requests (if we had timing data)
        # This would be enhanced with request history
        
        return suspicious_patterns


class WebRateLimiter:
    """Redis-based hybrid rate limiter for web users."""
    
    def __init__(self, config: WebRateLimitConfig, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the web rate limiter.
        
        Args:
            config: Rate limiting configuration
            redis_client: Optional Redis client
        """
        self.config = config
        self.redis_client = redis_client
        self.fingerprinter = BrowserFingerprinter()
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection if needed."""
        if self._initialized:
            return
        
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                await self.redis_client.ping()
                logger.info("✅ Connected to Redis for web rate limiting")
            except Exception as e:
                logger.warning(f"❌ Redis not available for web rate limiting: {e}")
                self.redis_client = None
        
        self._initialized = True
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address, handling proxies."""
        # Check for forwarded headers (common in production)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client IP
        return request.client.host if request.client else "unknown"
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from cookie."""
        return request.cookies.get(self.config.session_cookie_name)
    
    async def _create_session(self, request: Request, response: Response) -> str:
        """
        Create a new session for the user.
        
        Args:
            request: HTTP request
            response: HTTP response to set cookie
            
        Returns:
            New session ID
        """
        session_id = str(uuid.uuid4())
        
        # Set secure session cookie
        response.set_cookie(
            key=self.config.session_cookie_name,
            value=session_id,
            max_age=self.config.session_ttl,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax"
        )
        
        if self.redis_client:
            # Initialize session data
            session_key = f"{self.config.redis_key_prefix}session:{session_id}"
            session_data = {
                "created_at": time.time(),
                "ip_address": self._get_client_ip(request),
                "fingerprint": self.fingerprinter.generate_fingerprint(request),
                "total_requests": 0,
                "suspicious_score": 0
            }
            
            await self.redis_client.hset(session_key, mapping=session_data)
            await self.redis_client.expire(session_key, self.config.redis_ttl)
        
        return session_id
    
    def _determine_user_tier(self, session_data: Dict[str, Any], has_session: bool) -> Tuple[str, Dict[str, int]]:
        """
        Determine user tier and applicable limits.
        
        Args:
            session_data: Session information from Redis
            has_session: Whether user has a valid session
            
        Returns:
            Tuple of (tier_name, limits_dict)
        """
        if not has_session:
            return "anonymous", {
                "minute": self.config.anonymous_requests_per_minute,
                "hour": self.config.anonymous_requests_per_hour,
                "day": self.config.anonymous_requests_per_day,
                "burst": self.config.anonymous_burst_limit
            }
        
        total_requests = int(session_data.get("total_requests", 0))
        suspicious_score = int(session_data.get("suspicious_score", 0))
        
        # Check if user is suspicious
        if suspicious_score >= self.config.suspicious_behavior_threshold:
            # Apply anonymous limits as penalty
            return "suspicious", {
                "minute": self.config.anonymous_requests_per_minute,
                "hour": self.config.anonymous_requests_per_hour,
                "day": self.config.anonymous_requests_per_day,
                "burst": self.config.anonymous_burst_limit
            }
        
        # Check if user is established
        if total_requests >= self.config.session_establishment_requests:
            return "established", {
                "minute": self.config.established_requests_per_minute,
                "hour": self.config.established_requests_per_hour,
                "day": self.config.established_requests_per_day,
                "burst": self.config.established_burst_limit
            }
        
        # Default to session user
        return "session", {
            "minute": self.config.session_requests_per_minute,
            "hour": self.config.session_requests_per_hour,
            "day": self.config.session_requests_per_day,
            "burst": self.config.session_burst_limit
        }
    
    async def is_allowed(self, request: Request) -> Tuple[bool, Optional[str], Dict[str, Any], Optional[str]]:
        """
        Check if web request is allowed based on hybrid rate limiting.
        
        Args:
            request: HTTP request object
            
        Returns:
            Tuple of (is_allowed, reason_if_blocked, stats, session_id_if_created)
        """
        await self.initialize()
        
        if self.redis_client is None:
            # If Redis unavailable, allow but log warning
            logger.warning("Web rate limiting unavailable (no Redis), allowing request")
            return True, None, {}, None
        
        current_time = time.time()
        correlation_id = get_correlation_id()
        
        # Extract identifiers
        client_ip = self._get_client_ip(request)
        session_id = self._get_session_id(request)
        fingerprint = self.fingerprinter.generate_fingerprint(request) if self.config.enable_fingerprinting else None
        
        # Check for suspicious patterns
        suspicious_patterns = self.fingerprinter.detect_suspicious_patterns(request)
        
        try:
            # Get session data if session exists
            session_data = {}
            if session_id:
                session_key = f"{self.config.redis_key_prefix}session:{session_id}"
                session_data = await self.redis_client.hgetall(session_key) or {}
            
            # Determine user tier and limits
            user_tier, limits = self._determine_user_tier(session_data, bool(session_id and session_data))
            
            # Create identifier for rate limiting
            if session_id and session_data:
                rate_limit_key = f"session:{session_id}"
            else:
                rate_limit_key = f"ip:{client_ip}"
            
            # Check rate limits using sliding window
            window_keys = {
                "burst": f"{self.config.redis_key_prefix}{rate_limit_key}:burst",
                "minute": f"{self.config.redis_key_prefix}{rate_limit_key}:minute",
                "hour": f"{self.config.redis_key_prefix}{rate_limit_key}:hour",
                "day": f"{self.config.redis_key_prefix}{rate_limit_key}:day"
            }
            
            # Get current counts
            pipe = self.redis_client.pipeline()
            pipe.zcount(window_keys["burst"], current_time - 10, current_time)  # 10-second burst window
            pipe.zcount(window_keys["minute"], current_time - 60, current_time)
            pipe.zcount(window_keys["hour"], current_time - 3600, current_time)
            pipe.zcount(window_keys["day"], current_time - 86400, current_time)
            
            counts = await pipe.execute()
            burst_count, minute_count, hour_count, day_count = counts
            
            # Apply suspicious pattern penalties
            if suspicious_patterns:
                penalty_multiplier = len(suspicious_patterns) * 0.5  # Reduce limits by 50% per pattern
                for limit_type in limits:
                    limits[limit_type] = max(1, int(limits[limit_type] * (1 - penalty_multiplier)))
            
            # Check limits in order of severity
            if burst_count >= limits["burst"]:
                return False, f"Burst limit exceeded ({limits['burst']} per 10s)", {
                    "user_tier": user_tier,
                    "limits": limits,
                    "counts": {"burst": burst_count, "minute": minute_count, "hour": hour_count, "day": day_count},
                    "suspicious_patterns": suspicious_patterns
                }, None
            
            if minute_count >= limits["minute"]:
                return False, f"Per-minute limit exceeded ({limits['minute']} per minute)", {
                    "user_tier": user_tier,
                    "limits": limits,
                    "counts": {"burst": burst_count, "minute": minute_count, "hour": hour_count, "day": day_count},
                    "suspicious_patterns": suspicious_patterns
                }, None
            
            if hour_count >= limits["hour"]:
                return False, f"Hourly limit exceeded ({limits['hour']} per hour)", {
                    "user_tier": user_tier,
                    "limits": limits,
                    "counts": {"burst": burst_count, "minute": minute_count, "hour": hour_count, "day": day_count},
                    "suspicious_patterns": suspicious_patterns
                }, None
            
            if day_count >= limits["day"]:
                return False, f"Daily limit exceeded ({limits['day']} per day)", {
                    "user_tier": user_tier,
                    "limits": limits,
                    "counts": {"burst": burst_count, "minute": minute_count, "hour": hour_count, "day": day_count},
                    "suspicious_patterns": suspicious_patterns
                }, None
            
            # All checks passed - record the request
            await self._record_request(window_keys, session_id, session_data, suspicious_patterns, current_time)
            
            return True, None, {
                "user_tier": user_tier,
                "limits": limits,
                "counts": {"burst": burst_count + 1, "minute": minute_count + 1, "hour": hour_count + 1, "day": day_count + 1},
                "suspicious_patterns": suspicious_patterns
            }, None
            
        except Exception as e:
            logger.error(f"Web rate limit check failed: {e}", extra={"correlation_id": correlation_id})
            # On error, allow request but log issue
            return True, None, {}, None
    
    async def _record_request(self, window_keys: Dict[str, str], session_id: Optional[str], 
                            session_data: Dict[str, Any], suspicious_patterns: List[str], current_time: float):
        """Record a request in all time windows and update session data."""
        pipe = self.redis_client.pipeline()
        
        # Add to sliding windows
        for window, key in window_keys.items():
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, self.config.redis_ttl)
            
            # Clean up old entries
            if window == "burst":
                cutoff = current_time - 10
            elif window == "minute":
                cutoff = current_time - 60
            elif window == "hour":
                cutoff = current_time - 3600
            else:  # day
                cutoff = current_time - 86400
            
            pipe.zremrangebyscore(key, 0, cutoff)
        
        # Update session data if session exists
        if session_id and session_data:
            session_key = f"{self.config.redis_key_prefix}session:{session_id}"
            total_requests = int(session_data.get("total_requests", 0)) + 1
            suspicious_score = int(session_data.get("suspicious_score", 0)) + len(suspicious_patterns)
            
            pipe.hset(session_key, mapping={
                "total_requests": total_requests,
                "suspicious_score": suspicious_score,
                "last_request": current_time
            })
        
        await pipe.execute()


class WebRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for hybrid web rate limiting."""
    
    def __init__(self, app, config: WebRateLimitConfig):
        """Initialize the middleware."""
        super().__init__(app)
        self.rate_limiter = WebRateLimiter(config)
        self.config = config
    
    def _should_apply_rate_limiting(self, path: str) -> bool:
        """Determine if rate limiting should apply to this path."""
        # Apply to API endpoints but not static files, health checks, etc.
        api_paths = ["/api/", "/analyze", "/upload"]
        excluded_paths = ["/health", "/static/", "/favicon.ico", "/metrics", "/dashboard", "/webhook/whatsapp"]
        
        # Don't apply to excluded paths
        if any(excluded in path for excluded in excluded_paths):
            return False
        
        # Apply to API paths
        if any(api_path in path for api_path in api_paths):
            return True
        
        # Apply to root paths that might be API endpoints
        if path in ["/", "/simple", "/direct", "/upload"]:
            return True
        
        return False
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with hybrid web rate limiting."""
        
        # Check if we should apply rate limiting to this path
        if not self._should_apply_rate_limiting(request.url.path):
            return await call_next(request)
        
        # Check rate limits
        allowed, reason, stats, new_session_id = await self.rate_limiter.is_allowed(request)
        
        if not allowed:
            logger.warning(
                f"Web rate limit exceeded",
                extra={
                    "ip": self.rate_limiter._get_client_ip(request),
                    "path": request.url.path,
                    "reason": reason,
                    "user_tier": stats.get("user_tier", "unknown"),
                    "suspicious_patterns": stats.get("suspicious_patterns", []),
                    "correlation_id": get_correlation_id()
                }
            )
            
            limits = stats.get("limits", {})
            counts = stats.get("counts", {})
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": reason,
                    "user_tier": stats.get("user_tier", "unknown"),
                    "limits": limits,
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(limits.get("minute", 0)),
                    "X-RateLimit-Remaining": str(max(0, limits.get("minute", 0) - counts.get("minute", 0))),
                    "X-RateLimit-Reset": str(int(time.time() + 60)),
                    "X-RateLimit-Tier": stats.get("user_tier", "unknown"),
                    "Retry-After": "60"
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Create session for new users if none exists
        if new_session_id is None and not self.rate_limiter._get_session_id(request):
            try:
                new_session_id = await self.rate_limiter._create_session(request, response)
                logger.debug(f"Created new web session: {new_session_id[:8]}...")
            except Exception as e:
                logger.warning(f"Failed to create web session: {e}")
        
        # Add rate limit headers to response
        if stats:
            limits = stats.get("limits", {})
            counts = stats.get("counts", {})
            
            response.headers["X-RateLimit-Limit"] = str(limits.get("minute", 0))
            response.headers["X-RateLimit-Remaining"] = str(max(0, limits.get("minute", 0) - counts.get("minute", 0)))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            response.headers["X-RateLimit-Tier"] = stats.get("user_tier", "unknown")
            
            suspicious_patterns = stats.get("suspicious_patterns", [])
            if suspicious_patterns:
                response.headers["X-RateLimit-Suspicious"] = ",".join(suspicious_patterns)
        
        return response


def create_web_rate_limit_middleware(
    anonymous_per_minute: int = 3,
    session_per_minute: int = 6,
    established_per_minute: int = 10,
    enable_fingerprinting: bool = True
) -> type:
    """
    Create web rate limiting middleware with specified configuration.
    
    Args:
        anonymous_per_minute: Rate limit for anonymous users
        session_per_minute: Rate limit for session users
        established_per_minute: Rate limit for established users
        enable_fingerprinting: Enable browser fingerprinting
        
    Returns:
        Configured middleware class
    """
    config = WebRateLimitConfig(
        anonymous_requests_per_minute=anonymous_per_minute,
        session_requests_per_minute=session_per_minute,
        established_requests_per_minute=established_per_minute,
        enable_fingerprinting=enable_fingerprinting
    )
    
    class ConfiguredWebRateLimitMiddleware(WebRateLimitMiddleware):
        def __init__(self, app):
            super().__init__(app, config)
    
    return ConfiguredWebRateLimitMiddleware