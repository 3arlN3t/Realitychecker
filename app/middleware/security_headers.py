"""Security headers middleware for enhanced security."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, RedirectResponse
from typing import Dict, Any

from app.utils.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers and enforce HTTPS."""
    
    def __init__(self, app, enforce_https: bool = True):
        super().__init__(app)
        self.enforce_https = enforce_https
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to all responses."""
        
        # Enforce HTTPS in production
        if self.enforce_https and request.url.scheme == "http":
            # Skip HTTPS enforcement for health checks and local development
            if request.url.hostname not in ["localhost", "127.0.0.1", "0.0.0.0"]:
                https_url = request.url.replace(scheme="https")
                logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")
                return RedirectResponse(url=str(https_url), status_code=301)
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        security_headers = self._get_security_headers()
        
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        return response
    
    def _get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers to add to responses.
        
        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Strict Transport Security (HSTS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Permissions Policy (formerly Feature Policy)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Server header (hide server information)
            "Server": "Reality-Checker-Bot/1.0"
        }


def create_security_headers_middleware(enforce_https: bool = True):
    """
    Create security headers middleware with configuration.
    
    Args:
        enforce_https: Whether to enforce HTTPS redirects
        
    Returns:
        Configured SecurityHeadersMiddleware
    """
    return lambda app: SecurityHeadersMiddleware(app, enforce_https=enforce_https)