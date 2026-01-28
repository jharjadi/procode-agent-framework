"""
Sentry Error Tracking Integration for ProCode Agent Framework

This module provides Sentry integration for error tracking and monitoring:
- Automatic error capture
- Custom error context
- Performance monitoring
- Release tracking
- User context

Usage:
    from observability.sentry_integration import init_sentry, capture_exception
    
    # Initialize Sentry
    init_sentry()
    
    # Capture exception with context
    try:
        # Do something
        pass
    except Exception as e:
        capture_exception(e, {"user_id": "123"})
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from typing import Optional, Dict, Any, Callable


# ============================================================================
# CONFIGURATION
# ============================================================================

class SentryConfig:
    """Configuration for Sentry error tracking."""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_SENTRY", "false").lower() == "true"
        self.dsn = os.getenv("SENTRY_DSN", "")
        self.environment = os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
        self.release = os.getenv("SENTRY_RELEASE", "procode-agent-framework@0.1.0")
        self.traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
        self.profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))
        self.send_default_pii = os.getenv("SENTRY_SEND_DEFAULT_PII", "false").lower() == "true"
        
    def is_valid(self) -> bool:
        """Check if Sentry configuration is valid."""
        return self.enabled and bool(self.dsn)
    
    def __repr__(self):
        return (
            f"SentryConfig(enabled={self.enabled}, "
            f"environment={self.environment}, "
            f"release={self.release}, "
            f"traces_sample_rate={self.traces_sample_rate})"
        )


config = SentryConfig()


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_sentry() -> bool:
    """
    Initialize Sentry SDK with FastAPI integration.
    
    Returns:
        True if Sentry was initialized successfully, False otherwise.
    """
    if not config.is_valid():
        if config.enabled and not config.dsn:
            print("⚠️  Sentry is enabled but SENTRY_DSN is not set")
        else:
            print("⚠️  Sentry error tracking is disabled")
        return False
    
    try:
        sentry_sdk.init(
            dsn=config.dsn,
            environment=config.environment,
            release=config.release,
            traces_sample_rate=config.traces_sample_rate,
            profiles_sample_rate=config.profiles_sample_rate,
            send_default_pii=config.send_default_pii,
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",
                    failed_request_status_codes=[500, 599],
                ),
                SqlalchemyIntegration(),
                HttpxIntegration(),
            ],
            before_send=before_send_filter,
            before_breadcrumb=before_breadcrumb_filter,
        )
        
        print(f"✅ Sentry error tracking initialized: {config}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize Sentry: {e}")
        return False


# ============================================================================
# FILTERS
# ============================================================================

def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter events before sending to Sentry.
    
    This function can be used to:
    - Scrub sensitive data
    - Filter out certain errors
    - Add additional context
    
    Args:
        event: Sentry event dictionary
        hint: Additional context about the event
    
    Returns:
        Modified event or None to drop the event
    """
    # Scrub sensitive data from request headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"
    
    # Filter out health check errors
    if "request" in event and "url" in event["request"]:
        url = event["request"]["url"]
        if "/health" in url or "/metrics" in url:
            return None  # Don't send health check errors
    
    return event


def before_breadcrumb_filter(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter breadcrumbs before adding to Sentry.
    
    Args:
        crumb: Breadcrumb dictionary
        hint: Additional context
    
    Returns:
        Modified breadcrumb or None to drop it
    """
    # Filter out noisy breadcrumbs
    if crumb.get("category") == "httplib":
        # Don't log every HTTP request as breadcrumb
        return None
    
    return crumb


# ============================================================================
# CONTEXT MANAGEMENT
# ============================================================================

def set_user_context(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    organization: Optional[str] = None,
    **kwargs
):
    """
    Set user context for error tracking.
    
    Args:
        user_id: User ID
        email: User email
        username: Username
        organization: Organization name
        **kwargs: Additional user attributes
    """
    if not config.is_valid():
        return
    
    user_data = {}
    if user_id:
        user_data["id"] = user_id
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    if organization:
        user_data["organization"] = organization
    
    user_data.update(kwargs)
    sentry_sdk.set_user(user_data)


def set_request_context(
    method: Optional[str] = None,
    url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
):
    """
    Set request context for error tracking.
    
    Args:
        method: HTTP method
        url: Request URL
        headers: Request headers (will be sanitized)
        **kwargs: Additional request attributes
    """
    if not config.is_valid():
        return
    
    request_data = {}
    if method:
        request_data["method"] = method
    if url:
        request_data["url"] = url
    if headers:
        # Sanitize sensitive headers
        sanitized_headers = {
            k: v if k.lower() not in ["authorization", "cookie", "x-api-key"] else "[Filtered]"
            for k, v in headers.items()
        }
        request_data["headers"] = sanitized_headers
    
    request_data.update(kwargs)
    sentry_sdk.set_context("request", request_data)


def set_llm_context(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    tokens: Optional[int] = None,
    cost: Optional[float] = None,
    **kwargs
):
    """
    Set LLM context for error tracking.
    
    Args:
        provider: LLM provider
        model: Model name
        tokens: Token count
        cost: Cost in USD
        **kwargs: Additional LLM attributes
    """
    if not config.is_valid():
        return
    
    llm_data = {}
    if provider:
        llm_data["provider"] = provider
    if model:
        llm_data["model"] = model
    if tokens:
        llm_data["tokens"] = tokens
    if cost:
        llm_data["cost_usd"] = cost
    
    llm_data.update(kwargs)
    sentry_sdk.set_context("llm", llm_data)


def set_agent_context(
    agent_type: Optional[str] = None,
    intent: Optional[str] = None,
    **kwargs
):
    """
    Set agent context for error tracking.
    
    Args:
        agent_type: Type of agent
        intent: User intent
        **kwargs: Additional agent attributes
    """
    if not config.is_valid():
        return
    
    agent_data = {}
    if agent_type:
        agent_data["type"] = agent_type
    if intent:
        agent_data["intent"] = intent
    
    agent_data.update(kwargs)
    sentry_sdk.set_context("agent", agent_data)


def clear_context():
    """Clear all Sentry context."""
    if not config.is_valid():
        return
    
    sentry_sdk.set_user(None)
    sentry_sdk.clear_breadcrumbs()


# ============================================================================
# ERROR CAPTURE
# ============================================================================

def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.
    
    Args:
        error: Exception to capture
        context: Additional context dictionary
        level: Error level (debug, info, warning, error, fatal)
    
    Returns:
        Event ID if sent to Sentry, None otherwise
    """
    if not config.is_valid():
        return None
    
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        event_id = sentry_sdk.capture_exception(error)
        return event_id


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Capture a message and send to Sentry.
    
    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error, fatal)
        context: Additional context dictionary
    
    Returns:
        Event ID if sent to Sentry, None otherwise
    """
    if not config.is_valid():
        return None
    
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        event_id = sentry_sdk.capture_message(message)
        return event_id


# ============================================================================
# BREADCRUMBS
# ============================================================================

def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
):
    """
    Add a breadcrumb for debugging context.
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level
        data: Additional data
    """
    if not config.is_valid():
        return
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

def start_transaction(
    name: str,
    op: str = "function"
) -> Optional[Any]:
    """
    Start a Sentry transaction for performance monitoring.
    
    Args:
        name: Transaction name
        op: Operation type
    
    Returns:
        Transaction object or None
    """
    if not config.is_valid():
        return None
    
    return sentry_sdk.start_transaction(name=name, op=op)


# ============================================================================
# DECORATOR
# ============================================================================

def capture_errors(
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
):
    """
    Decorator to automatically capture errors from a function.
    
    Args:
        context: Additional context to include
        level: Error level
    
    Usage:
        @capture_errors({"service": "payment"})
        def process_payment():
            # Errors are automatically captured
            pass
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_exception(e, context, level)
                raise
        return wrapper
    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def flush(timeout: float = 2.0) -> bool:
    """
    Flush pending Sentry events.
    
    Args:
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if all events were sent, False otherwise
    """
    if not config.is_valid():
        return True
    
    return sentry_sdk.flush(timeout=timeout)


def is_enabled() -> bool:
    """Check if Sentry is enabled and configured."""
    return config.is_valid()


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("ProCode Agent Framework - Sentry Integration")
    print("=" * 60)
    print(f"Configuration: {config}")
    
    if init_sentry():
        # Set user context
        set_user_context(user_id="test_user", organization="test_org")
        
        # Add breadcrumb
        add_breadcrumb("Test breadcrumb", category="test")
        
        # Capture message
        event_id = capture_message("Test message", level="info")
        print(f"Message captured: {event_id}")
        
        # Capture exception
        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = capture_exception(e, {"test": "context"})
            print(f"Exception captured: {event_id}")
        
        # Flush events
        flush()
        print("\n✅ Sentry integration test completed")
    else:
        print("\n⚠️  Sentry not configured")
