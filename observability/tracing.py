"""
OpenTelemetry Distributed Tracing for ProCode Agent Framework

This module provides distributed tracing capabilities using OpenTelemetry:
- Automatic instrumentation for FastAPI, HTTPX, SQLAlchemy
- Manual span creation for custom operations
- Context propagation across services
- Trace export to OTLP collectors

Usage:
    from observability.tracing import tracer, trace_operation
    
    # Manual span creation
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        # Do work
    
    # Decorator for automatic tracing
    @trace_operation("process_payment")
    async def process_payment(amount):
        # Function is automatically traced
        pass
"""

import os
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import Status, StatusCode, Span


# ============================================================================
# CONFIGURATION
# ============================================================================

class TracingConfig:
    """Configuration for OpenTelemetry tracing."""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_TRACING", "false").lower() == "true"
        self.service_name = os.getenv("OTEL_SERVICE_NAME", "procode-agent-framework")
        self.service_version = os.getenv("SERVICE_VERSION", "0.1.0")
        self.otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        self.sample_rate = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "0.1"))  # 10% sampling
        
    def __repr__(self):
        return (
            f"TracingConfig(enabled={self.enabled}, "
            f"service={self.service_name}, "
            f"endpoint={self.otlp_endpoint}, "
            f"sample_rate={self.sample_rate})"
        )


config = TracingConfig()


# ============================================================================
# TRACER SETUP
# ============================================================================

def setup_tracing() -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry tracing.
    
    Returns:
        Tracer instance if tracing is enabled, None otherwise.
    """
    if not config.enabled:
        print("⚠️  OpenTelemetry tracing is disabled")
        return trace.get_tracer(__name__)  # Return no-op tracer
    
    try:
        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: config.service_name,
            SERVICE_VERSION: config.service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=config.otlp_endpoint,
            insecure=True  # Use insecure for local development
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        print(f"✅ OpenTelemetry tracing initialized: {config}")
        
        # Return tracer
        return trace.get_tracer(__name__)
        
    except Exception as e:
        print(f"❌ Failed to initialize OpenTelemetry tracing: {e}")
        return trace.get_tracer(__name__)  # Return no-op tracer


# Create global tracer
tracer = setup_tracing()


# ============================================================================
# INSTRUMENTATION
# ============================================================================

def instrument_fastapi(app):
    """
    Instrument FastAPI application for automatic tracing.
    
    Args:
        app: FastAPI application instance
    """
    if not config.enabled:
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        print("✅ FastAPI instrumented for tracing")
    except Exception as e:
        print(f"❌ Failed to instrument FastAPI: {e}")


def instrument_httpx():
    """Instrument HTTPX client for automatic tracing."""
    if not config.enabled:
        return
    
    try:
        HTTPXClientInstrumentor().instrument()
        print("✅ HTTPX instrumented for tracing")
    except Exception as e:
        print(f"❌ Failed to instrument HTTPX: {e}")


def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy engine for automatic tracing.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    if not config.enabled:
        return
    
    try:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            service=config.service_name
        )
        print("✅ SQLAlchemy instrumented for tracing")
    except Exception as e:
        print(f"❌ Failed to instrument SQLAlchemy: {e}")


# ============================================================================
# SPAN HELPERS
# ============================================================================

def set_span_attributes(span: Span, attributes: Dict[str, Any]):
    """
    Set multiple attributes on a span.
    
    Args:
        span: OpenTelemetry span
        attributes: Dictionary of attributes to set
    """
    if not span or not span.is_recording():
        return
    
    for key, value in attributes.items():
        if value is not None:
            # Convert value to string if it's not a primitive type
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)
            else:
                span.set_attribute(key, str(value))


def set_span_error(span: Span, error: Exception):
    """
    Record an error on a span.
    
    Args:
        span: OpenTelemetry span
        error: Exception that occurred
    """
    if not span or not span.is_recording():
        return
    
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)


def set_span_success(span: Span, message: Optional[str] = None):
    """
    Mark a span as successful.
    
    Args:
        span: OpenTelemetry span
        message: Optional success message
    """
    if not span or not span.is_recording():
        return
    
    span.set_status(Status(StatusCode.OK, message or "Success"))


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Context manager for creating a traced span.
    
    Args:
        name: Name of the span
        attributes: Optional attributes to set on the span
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
    
    Usage:
        with trace_span("my_operation", {"user_id": "123"}):
            # Do work
            pass
    """
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            set_span_attributes(span, attributes)
        try:
            yield span
            set_span_success(span)
        except Exception as e:
            set_span_error(span, e)
            raise


# ============================================================================
# DECORATORS
# ============================================================================

def trace_operation(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    Decorator to automatically trace a function or method.
    
    Args:
        operation_name: Name for the span (defaults to function name)
        attributes: Optional attributes to set on the span
        kind: Span kind
    
    Usage:
        @trace_operation("process_payment", {"service": "payment"})
        async def process_payment(amount):
            # Function is automatically traced
            pass
    """
    def decorator(func: Callable):
        span_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with trace_span(span_name, attributes, kind) as span:
                    # Add function arguments as attributes
                    if args:
                        span.set_attribute("args.count", len(args))
                    if kwargs:
                        for key, value in kwargs.items():
                            if isinstance(value, (str, int, float, bool)):
                                span.set_attribute(f"arg.{key}", value)
                    
                    result = await func(*args, **kwargs)
                    return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with trace_span(span_name, attributes, kind) as span:
                    # Add function arguments as attributes
                    if args:
                        span.set_attribute("args.count", len(args))
                    if kwargs:
                        for key, value in kwargs.items():
                            if isinstance(value, (str, int, float, bool)):
                                span.set_attribute(f"arg.{key}", value)
                    
                    result = func(*args, **kwargs)
                    return result
            return sync_wrapper
    
    return decorator


# ============================================================================
# SPECIALIZED TRACING FUNCTIONS
# ============================================================================

def trace_http_request(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    user_agent: Optional[str] = None
) -> Span:
    """
    Create a span for an HTTP request.
    
    Args:
        method: HTTP method
        url: Request URL
        status_code: Response status code
        user_agent: User agent string
    
    Returns:
        Span instance
    """
    span = tracer.start_span(
        f"HTTP {method}",
        kind=trace.SpanKind.SERVER
    )
    
    attributes = {
        "http.method": method,
        "http.url": url,
    }
    
    if status_code:
        attributes["http.status_code"] = status_code
    if user_agent:
        attributes["http.user_agent"] = user_agent
    
    set_span_attributes(span, attributes)
    return span


def trace_llm_request(
    provider: str,
    model: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    cost: Optional[float] = None
) -> Span:
    """
    Create a span for an LLM API request.
    
    Args:
        provider: LLM provider (openai, anthropic, etc.)
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        cost: Cost in USD
    
    Returns:
        Span instance
    """
    span = tracer.start_span(
        f"LLM {provider}/{model}",
        kind=trace.SpanKind.CLIENT
    )
    
    attributes = {
        "llm.provider": provider,
        "llm.model": model,
    }
    
    if prompt_tokens:
        attributes["llm.tokens.prompt"] = prompt_tokens
    if completion_tokens:
        attributes["llm.tokens.completion"] = completion_tokens
    if cost:
        attributes["llm.cost_usd"] = cost
    
    set_span_attributes(span, attributes)
    return span


def trace_agent_execution(
    agent_type: str,
    intent: Optional[str] = None,
    user_id: Optional[str] = None
) -> Span:
    """
    Create a span for an agent execution.
    
    Args:
        agent_type: Type of agent
        intent: User intent
        user_id: User ID
    
    Returns:
        Span instance
    """
    span = tracer.start_span(
        f"Agent {agent_type}",
        kind=trace.SpanKind.INTERNAL
    )
    
    attributes = {
        "agent.type": agent_type,
    }
    
    if intent:
        attributes["agent.intent"] = intent
    if user_id:
        attributes["agent.user_id"] = user_id
    
    set_span_attributes(span, attributes)
    return span


def trace_database_query(
    operation: str,
    table: Optional[str] = None
) -> Span:
    """
    Create a span for a database query.
    
    Args:
        operation: SQL operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
    
    Returns:
        Span instance
    """
    span = tracer.start_span(
        f"DB {operation}",
        kind=trace.SpanKind.CLIENT
    )
    
    attributes = {
        "db.system": "postgresql",
        "db.operation": operation,
    }
    
    if table:
        attributes["db.table"] = table
    
    set_span_attributes(span, attributes)
    return span


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_span() -> Optional[Span]:
    """Get the current active span."""
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """Get the current trace ID as a hex string."""
    span = get_current_span()
    if span and span.is_recording():
        trace_id = span.get_span_context().trace_id
        return format(trace_id, '032x')
    return None


def get_span_id() -> Optional[str]:
    """Get the current span ID as a hex string."""
    span = get_current_span()
    if span and span.is_recording():
        span_id = span.get_span_context().span_id
        return format(span_id, '016x')
    return None


# Need to import asyncio for the decorator
import asyncio


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("ProCode Agent Framework - OpenTelemetry Tracing")
    print("=" * 60)
    print(f"Configuration: {config}")
    
    # Example: Manual span creation
    with tracer.start_as_current_span("example_operation") as span:
        span.set_attribute("example.key", "example_value")
        print(f"Trace ID: {get_trace_id()}")
        print(f"Span ID: {get_span_id()}")
    
    # Example: Using context manager
    with trace_span("another_operation", {"user_id": "123"}):
        print("Doing work...")
    
    print("\n✅ Tracing examples completed")
