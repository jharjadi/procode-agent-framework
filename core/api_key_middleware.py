"""
API Key Middleware

FastAPI/Starlette middleware for API key authentication.
Validates API keys, checks rate limits, and injects auth context into requests.
"""

from typing import Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR
)

from security.api_key_service import APIKeyService
from security.api_key_exceptions import (
    APIKeyError,
    MissingAPIKeyError,
    RateLimitExceededError
)
from security.rate_limiter import get_global_api_key_rate_limiter
from security.audit_logger import AuditLogger
from database.connection import get_db_session


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication and rate limiting.
    
    Features:
    - Extracts API key from Authorization header
    - Validates API key using APIKeyService
    - Checks rate limits
    - Injects auth context into request.state
    - Adds rate limit headers to response
    - Tracks usage asynchronously
    - Handles authentication errors
    """
    
    def __init__(
        self,
        app,
        public_paths: Optional[List[str]] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize API key middleware.
        
        Args:
            app: Starlette/FastAPI application
            public_paths: List of paths that don't require authentication
            audit_logger: Optional audit logger for security events
        """
        super().__init__(app)
        
        # Default public paths (health checks, docs, etc.)
        self.public_paths = public_paths or [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        
        self.audit_logger = audit_logger
        self.rate_limiter = get_global_api_key_rate_limiter()
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request through authentication pipeline.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Check if path is public (skip authentication)
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        try:
            # Extract API key from request
            api_key = self._extract_api_key(request)
            
            if not api_key:
                raise MissingAPIKeyError()
            
            # Get database session
            db_session = next(get_db_session())
            
            try:
                # Create API key service
                api_key_service = APIKeyService(
                    session=db_session,
                    audit_logger=self.audit_logger
                )
                
                # Validate API key
                auth_context = api_key_service.validate_key(api_key)
                
                # Check rate limit
                allowed, rate_info = self.rate_limiter.check_rate_limit(
                    key_id=auth_context["key_id"],
                    limit=auth_context["rate_limit"]
                )
                
                if not allowed:
                    raise RateLimitExceededError(
                        limit=rate_info["limit"],
                        reset_at=rate_info["reset_at"]
                    )
                
                # Check monthly quota
                quota_info = api_key_service.check_monthly_quota(
                    auth_context["organization_id"]
                )
                
                # Inject auth context into request state
                request.state.auth = auth_context
                request.state.rate_info = rate_info
                request.state.quota_info = quota_info
                
                # Process request
                response = await call_next(request)
                
                # Add rate limit headers
                response.headers.update(
                    self._get_rate_limit_headers(rate_info)
                )
                
                # Track usage (async - don't wait)
                self._track_usage_async(
                    api_key_service=api_key_service,
                    auth_context=auth_context,
                    request=request,
                    response=response
                )
                
                return response
                
            finally:
                db_session.close()
        
        except APIKeyError as e:
            # Handle API key authentication errors
            return self._create_error_response(e)
        
        except Exception as e:
            # Handle unexpected errors
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "api_key_middleware_error",
                    f"Unexpected error: {str(e)}",
                    severity="error"
                )
            
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred"
                }
            )
    
    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public (doesn't require authentication).
        
        Args:
            path: Request path
            
        Returns:
            True if public, False otherwise
        """
        return any(path.startswith(public_path) for public_path in self.public_paths)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key from Authorization header.
        
        Supports formats:
        - Authorization: Bearer pk_live_...
        - Authorization: pk_live_...
        
        Args:
            request: HTTP request
            
        Returns:
            API key or None
        """
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return None
        
        # Remove "Bearer " prefix if present
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        
        return auth_header.strip()
    
    def _get_rate_limit_headers(self, rate_info: dict) -> dict:
        """
        Get rate limit headers for response.
        
        Args:
            rate_info: Rate limit information
            
        Returns:
            Dictionary of headers
        """
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
        }
        
        if rate_info.get("reset_at"):
            headers["X-RateLimit-Reset"] = rate_info["reset_at"]
        
        return headers
    
    def _track_usage_async(
        self,
        api_key_service: APIKeyService,
        auth_context: dict,
        request: Request,
        response: Response
    ):
        """
        Track API usage asynchronously (fire and forget).
        
        Args:
            api_key_service: API key service instance
            auth_context: Authentication context
            request: HTTP request
            response: HTTP response
        """
        try:
            # Extract request details
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code
            
            # Get client info
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("User-Agent")
            
            # Track usage
            api_key_service.track_usage(
                key_id=auth_context["key_id"],
                org_id=auth_context["organization_id"],
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            # Log error but don't fail the request
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    "usage_tracking_error",
                    f"Failed to track usage: {str(e)}",
                    severity="warning"
                )
    
    def _create_error_response(self, error: APIKeyError) -> JSONResponse:
        """
        Create JSON error response from APIKeyError.
        
        Args:
            error: API key error
            
        Returns:
            JSON response
        """
        return JSONResponse(
            status_code=error.status_code,
            content=error.to_dict()
        )


# Helper function to get auth context from request
def get_auth_context(request: Request) -> Optional[dict]:
    """
    Get authentication context from request state.
    
    Args:
        request: HTTP request
        
    Returns:
        Auth context dictionary or None
        
    Example:
        >>> context = get_auth_context(request)
        >>> org_id = context["organization_id"]
    """
    return getattr(request.state, "auth", None)


# Helper function to get rate info from request
def get_rate_info(request: Request) -> Optional[dict]:
    """
    Get rate limit info from request state.
    
    Args:
        request: HTTP request
        
    Returns:
        Rate info dictionary or None
    """
    return getattr(request.state, "rate_info", None)


# Helper function to get quota info from request
def get_quota_info(request: Request) -> Optional[dict]:
    """
    Get quota info from request state.
    
    Args:
        request: HTTP request
        
    Returns:
        Quota info dictionary or None
    """
    return getattr(request.state, "quota_info", None)
