"""
API Security Middleware

This module provides security middleware for the public API including:
- API key authentication
- Rate limiting per IP address
- CORS restriction to specific domains
"""

import os
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class APISecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API security including rate limiting and API key validation.
    """
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize security middleware.
        
        Args:
            app: Starlette application
            rate_limiter: Optional RateLimiter instance (creates default if None)
        """
        super().__init__(app)
        
        # Get configuration from environment
        self.enabled = os.getenv("ENABLE_API_SECURITY", "false").lower() == "true"
        self.api_key = os.getenv("DEMO_API_KEY", "")
        self.require_api_key = bool(self.api_key)
        
        # Log security configuration (using print for immediate visibility)
        print("=" * 60)
        print("API Security Middleware Initialized")
        print(f"  Enabled: {self.enabled}")
        print(f"  API Key Required: {self.require_api_key}")
        print(f"  API Key Set: {'Yes' if self.api_key else 'No'}")
        if self.api_key:
            print(f"  API Key (first 8 chars): {self.api_key[:8]}...")
        print(f"  ENABLE_API_SECURITY env: {os.getenv('ENABLE_API_SECURITY', 'NOT SET')}")
        print(f"  DEMO_API_KEY env: {'SET' if os.getenv('DEMO_API_KEY') else 'NOT SET'}")
        print("=" * 60)
        
        # Initialize rate limiter
        if rate_limiter is None:
            requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
            requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
            requests_per_day = int(os.getenv("RATE_LIMIT_PER_DAY", "1000"))
            
            self.rate_limiter = RateLimiter(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                requests_per_day=requests_per_day
            )
            
            print(f"Rate Limiter: {requests_per_minute}/min, {requests_per_hour}/hr, {requests_per_day}/day")
        else:
            self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through security checks.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or error response
        """
        # Skip security for CORS preflight requests (OPTIONS method)
        # This allows the CORS middleware to handle preflight requests properly
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip security for health check and agent card endpoints
        if request.url.path in ["/health", "/.well-known/agent.json", "/favicon.ico"]:
            return await call_next(request)
        
        # Skip if security is disabled
        if not self.enabled:
            return await call_next(request)
        
        # 1. Check API Key (if required)
        if self.require_api_key:
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            
            if not api_key:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "API key required",
                        "message": "Please provide an API key via X-API-Key header or api_key query parameter"
                    }
                )
            
            if api_key != self.api_key:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Invalid API key",
                        "message": "The provided API key is invalid"
                    }
                )
        
        # 2. Check Rate Limit (by IP address)
        client_ip = self._get_client_ip(request)
        
        if not self.rate_limiter.check_rate(client_ip):
            # Get quota information for helpful error message
            quota = self.rate_limiter.get_remaining_quota(client_ip)
            reset_times = self.rate_limiter.get_reset_time(client_ip)
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "quota": quota,
                    "reset_time": {
                        "minute": reset_times["minute"].isoformat() if reset_times["minute"] else None,
                        "hour": reset_times["hour"].isoformat() if reset_times["hour"] else None,
                        "day": reset_times["day"].isoformat() if reset_times["day"] else None,
                    }
                },
                headers={
                    "Retry-After": "60"  # Suggest retry after 60 seconds
                }
            )
        
        # All checks passed, proceed with request
        response = await call_next(request)
        
        # Add rate limit headers to response
        quota = self.rate_limiter.get_remaining_quota(client_ip)
        response.headers["X-RateLimit-Remaining-Minute"] = str(quota["minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(quota["hour"])
        response.headers["X-RateLimit-Remaining-Day"] = str(quota["day"])
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Checks X-Forwarded-For header first (for proxied requests),
        then falls back to direct client IP.
        
        Args:
            request: Incoming request
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (set by proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header (alternative proxy header)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


def get_allowed_origins() -> list:
    """
    Get list of allowed CORS origins from environment.
    
    Returns:
        List of allowed origin URLs
    """
    # Get from environment variable (comma-separated)
    origins_env = os.getenv("ALLOWED_ORIGINS", "")
    
    if origins_env:
        # Parse comma-separated list
        origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
        return origins
    
    # Default to localhost for development
    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8501"
    ]
