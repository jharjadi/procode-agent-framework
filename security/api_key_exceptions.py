"""
API Key Exceptions

Custom exception hierarchy for API key authentication errors.
Provides clear, user-friendly error messages and appropriate HTTP status codes.
"""

from typing import Optional


class APIKeyError(Exception):
    """Base exception for all API key related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None
    ):
        """
        Initialize API key error.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            error_code: Machine-readable error code
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code
        }


class InvalidAPIKeyError(APIKeyError):
    """Raised when API key format is invalid or key not found."""
    
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="invalid_api_key"
        )


class MissingAPIKeyError(APIKeyError):
    """Raised when API key is missing from request."""
    
    def __init__(self, message: str = "API key is required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="missing_api_key"
        )


class ExpiredAPIKeyError(APIKeyError):
    """Raised when API key has expired."""
    
    def __init__(self, message: str = "API key has expired", expires_at: Optional[str] = None):
        if expires_at:
            message = f"{message}. Expired at: {expires_at}"
        super().__init__(
            message=message,
            status_code=401,
            error_code="expired_api_key"
        )


class RevokedAPIKeyError(APIKeyError):
    """Raised when API key has been revoked."""
    
    def __init__(
        self,
        message: str = "API key has been revoked",
        revoked_at: Optional[str] = None,
        reason: Optional[str] = None
    ):
        if revoked_at:
            message = f"{message}. Revoked at: {revoked_at}"
        if reason:
            message = f"{message}. Reason: {reason}"
        super().__init__(
            message=message,
            status_code=401,
            error_code="revoked_api_key"
        )


class RateLimitExceededError(APIKeyError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        reset_at: Optional[str] = None
    ):
        if limit:
            message = f"{message}. Limit: {limit} requests per minute"
        if reset_at:
            message = f"{message}. Resets at: {reset_at}"
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limit_exceeded"
        )


class InsufficientScopeError(APIKeyError):
    """Raised when API key lacks required scope."""
    
    def __init__(
        self,
        message: str = "Insufficient scope",
        required_scope: Optional[str] = None,
        available_scopes: Optional[list] = None
    ):
        if required_scope:
            message = f"{message}. Required scope: {required_scope}"
        if available_scopes:
            message = f"{message}. Available scopes: {', '.join(available_scopes)}"
        super().__init__(
            message=message,
            status_code=403,
            error_code="insufficient_scope"
        )


class OrganizationInactiveError(APIKeyError):
    """Raised when organization is inactive."""
    
    def __init__(self, message: str = "Organization is inactive"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="organization_inactive"
        )


class APIKeyLimitExceededError(APIKeyError):
    """Raised when organization has reached API key limit."""
    
    def __init__(
        self,
        message: str = "API key limit exceeded",
        current_count: Optional[int] = None,
        max_keys: Optional[int] = None
    ):
        if current_count and max_keys:
            message = f"{message}. Current: {current_count}, Maximum: {max_keys}"
        super().__init__(
            message=message,
            status_code=403,
            error_code="api_key_limit_exceeded"
        )


class MonthlyQuotaExceededError(APIKeyError):
    """Raised when monthly request quota is exceeded."""
    
    def __init__(
        self,
        message: str = "Monthly quota exceeded",
        current_usage: Optional[int] = None,
        quota: Optional[int] = None
    ):
        if current_usage and quota:
            message = f"{message}. Usage: {current_usage}/{quota} requests"
        super().__init__(
            message=message,
            status_code=429,
            error_code="monthly_quota_exceeded"
        )


class APIKeyGenerationError(APIKeyError):
    """Raised when API key generation fails."""
    
    def __init__(self, message: str = "Failed to generate API key"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="api_key_generation_error"
        )


class APIKeyStorageError(APIKeyError):
    """Raised when API key storage fails."""
    
    def __init__(self, message: str = "Failed to store API key"):
        super().__init__(
            message=message,
            status_code=500,
            error_code="api_key_storage_error"
        )


# Convenience function to create appropriate exception from error type
def create_api_key_exception(
    error_type: str,
    message: Optional[str] = None,
    **kwargs
) -> APIKeyError:
    """
    Create appropriate API key exception based on error type.
    
    Args:
        error_type: Type of error (invalid, expired, revoked, etc.)
        message: Optional custom message
        **kwargs: Additional parameters for specific exceptions
        
    Returns:
        Appropriate APIKeyError subclass instance
        
    Example:
        >>> exc = create_api_key_exception("invalid", "Key not found")
        >>> exc.status_code
        401
    """
    exception_map = {
        "invalid": InvalidAPIKeyError,
        "missing": MissingAPIKeyError,
        "expired": ExpiredAPIKeyError,
        "revoked": RevokedAPIKeyError,
        "rate_limit": RateLimitExceededError,
        "insufficient_scope": InsufficientScopeError,
        "organization_inactive": OrganizationInactiveError,
        "key_limit": APIKeyLimitExceededError,
        "quota_exceeded": MonthlyQuotaExceededError,
        "generation_error": APIKeyGenerationError,
        "storage_error": APIKeyStorageError,
    }
    
    exception_class = exception_map.get(error_type, APIKeyError)
    
    if message:
        return exception_class(message, **kwargs)
    else:
        return exception_class(**kwargs)
