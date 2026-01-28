"""
Observability Module for ProCode Agent Framework

This module provides comprehensive monitoring and observability:
- Prometheus metrics collection
- Health checks and readiness probes
- OpenTelemetry distributed tracing
- Sentry error tracking
- Alert configuration

Usage:
    from observability import metrics, health_checker, tracer
    
    # Track metrics
    metrics.track_http_request("POST", "/api/chat", 200, 0.5)
    
    # Check health
    health = await health_checker.check_health()
    
    # Create trace span
    with tracer.start_as_current_span("operation"):
        # Do work
        pass
"""

try:
    from observability.metrics import metrics, MetricsCollector
    from observability.health import health_checker, HealthChecker, HealthStatus
    from observability.tracing import tracer, trace_operation, trace_span
    
    __all__ = [
        # Metrics
        "metrics",
        "MetricsCollector",
        
        # Health
        "health_checker",
        "HealthChecker",
        "HealthStatus",
        
        # Tracing
        "tracer",
        "trace_operation",
        "trace_span",
    ]
except ImportError as e:
    print(f"Warning: Could not import observability components: {e}")
    # Provide dummy objects for graceful degradation
    metrics = None
    health_checker = None
    tracer = None
