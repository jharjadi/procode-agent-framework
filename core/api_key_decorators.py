"""
API Key Decorators

Decorators for protecting FastAPI endpoints with API key authentication
and scope-based authorization.
"""

from functools import wraps
from typing import List, Callable
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from security.api_key_exceptions import MissingAPIKeyError, InsufficientScopeError
from core.api_key_middleware import get_auth_context


def require_api_key(func: Callable) -> Callable:
    """
    Decorator to require valid API key for endpoint.
    
    Checks that request has valid authentication context from middleware.
    
    Args:
        func: Endpoint function to protect
        
    Returns:
        Wrapped function
        
    Example:
        @app.get("/protected")
        @require_api_key
        async def protected_endpoint(request: Request):
            return {"message": "Access granted"}
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Check if auth context exists
        auth_context = get_auth_context(request)
        
        if not auth_context:
            error = MissingAPIKeyError()
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content=error.to_dict()
            )
        
        # Call original function
        return await func(request, *args, **kwargs)
    
    return wrapper


def require_scope(required_scope: str) -> Callable:
    """
    Decorator to require specific scope for endpoint.
    
    Args:
        required_scope: Required scope (e.g., "chat", "agents", "admin")
        
    Returns:
        Decorator function
        
    Example:
        @app.post("/admin/users")
        @require_scope("admin")
        async def admin_endpoint(request: Request):
            return {"message": "Admin access granted"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth context
            auth_context = get_auth_context(request)
            
            if not auth_context:
                error = MissingAPIKeyError()
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content=error.to_dict()
                )
            
            # Check scope
            scopes = auth_context.get("scopes", [])
            
            # Wildcard grants all access
            if "*" in scopes:
                return await func(request, *args, **kwargs)
            
            # Check if required scope is present
            if required_scope not in scopes:
                error = InsufficientScopeError(
                    required_scope=required_scope,
                    available_scopes=scopes
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content=error.to_dict()
                )
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_any_scope(*required_scopes: str) -> Callable:
    """
    Decorator to require any of the specified scopes.
    
    Args:
        *required_scopes: One or more required scopes
        
    Returns:
        Decorator function
        
    Example:
        @app.get("/data")
        @require_any_scope("read", "write", "admin")
        async def data_endpoint(request: Request):
            return {"message": "Access granted"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth context
            auth_context = get_auth_context(request)
            
            if not auth_context:
                error = MissingAPIKeyError()
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content=error.to_dict()
                )
            
            # Check scopes
            scopes = auth_context.get("scopes", [])
            
            # Wildcard grants all access
            if "*" in scopes:
                return await func(request, *args, **kwargs)
            
            # Check if any required scope is present
            if not any(scope in scopes for scope in required_scopes):
                error = InsufficientScopeError(
                    required_scope=f"any of: {', '.join(required_scopes)}",
                    available_scopes=scopes
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content=error.to_dict()
                )
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_all_scopes(*required_scopes: str) -> Callable:
    """
    Decorator to require all of the specified scopes.
    
    Args:
        *required_scopes: All required scopes
        
    Returns:
        Decorator function
        
    Example:
        @app.post("/admin/critical")
        @require_all_scopes("admin", "write", "critical")
        async def critical_endpoint(request: Request):
            return {"message": "Full access granted"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get auth context
            auth_context = get_auth_context(request)
            
            if not auth_context:
                error = MissingAPIKeyError()
                return JSONResponse(
                    status_code=HTTP_401_UNAUTHORIZED,
                    content=error.to_dict()
                )
            
            # Check scopes
            scopes = auth_context.get("scopes", [])
            
            # Wildcard grants all access
            if "*" in scopes:
                return await func(request, *args, **kwargs)
            
            # Check if all required scopes are present
            missing_scopes = [s for s in required_scopes if s not in scopes]
            
            if missing_scopes:
                error = InsufficientScopeError(
                    required_scope=f"all of: {', '.join(required_scopes)}",
                    available_scopes=scopes
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN,
                    content=error.to_dict()
                )
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Convenience decorator for admin-only endpoints
def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin scope.
    
    Shorthand for @require_scope("admin")
    
    Args:
        func: Endpoint function to protect
        
    Returns:
        Wrapped function
        
    Example:
        @app.delete("/users/{user_id}")
        @require_admin
        async def delete_user(request: Request, user_id: str):
            return {"message": "User deleted"}
    """
    return require_scope("admin")(func)
