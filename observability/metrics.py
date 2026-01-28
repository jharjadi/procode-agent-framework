"""
Prometheus Metrics Collection for ProCode Agent Framework

This module provides comprehensive metrics collection for monitoring:
- HTTP requests and responses
- LLM API calls and costs
- Agent executions
- Database operations
- API key usage
- System resources

Usage:
    from observability.metrics import metrics
    
    # Track HTTP request
    metrics.track_http_request(method="POST", endpoint="/api/chat", status=200, duration=0.5)
    
    # Track LLM call
    metrics.track_llm_request(provider="openai", model="gpt-4", tokens=150, cost=0.0045)
"""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Create a custom registry (optional - can use default)
registry = CollectorRegistry()

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=registry
)

http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=registry
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# ============================================================================
# LLM METRICS
# ============================================================================

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status'],
    registry=registry
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=registry
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens used',
    ['provider', 'model', 'type'],  # type: prompt, completion
    registry=registry
)

llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model'],
    registry=registry
)

llm_errors_total = Counter(
    'llm_errors_total',
    'Total LLM errors',
    ['provider', 'model', 'error_type'],
    registry=registry
)

# ============================================================================
# AGENT METRICS
# ============================================================================

agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type', 'status'],
    registry=registry
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry
)

agent_executions_in_progress = Gauge(
    'agent_executions_in_progress',
    'Number of agent executions in progress',
    ['agent_type'],
    registry=registry
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=registry
)

db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['operation', 'error_type'],
    registry=registry
)

# ============================================================================
# CACHE METRICS (for future Step 13)
# ============================================================================

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],  # result: hit, miss
    registry=registry
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_name'],
    registry=registry
)

# ============================================================================
# API KEY METRICS
# ============================================================================

api_key_requests_total = Counter(
    'api_key_requests_total',
    'Total API key requests',
    ['organization', 'key_id', 'status'],
    registry=registry
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['organization', 'limit_type'],  # limit_type: per_minute, monthly
    registry=registry
)

quota_usage_percent = Gauge(
    'quota_usage_percent',
    'Quota usage percentage',
    ['organization'],
    registry=registry
)

# ============================================================================
# SYSTEM METRICS
# ============================================================================

app_info = Info(
    'app_info',
    'Application version and build info',
    registry=registry
)

# Set application info
app_info.info({
    'version': '0.1.0',
    'name': 'procode-agent-framework',
    'python_version': '3.10+'
})


# ============================================================================
# METRICS COLLECTOR CLASS
# ============================================================================

class MetricsCollector:
    """
    Central metrics collector for the ProCode Agent Framework.
    
    Provides convenient methods for tracking various metrics throughout
    the application lifecycle.
    """
    
    def __init__(self):
        self.registry = registry
    
    # ------------------------------------------------------------------------
    # HTTP Metrics
    # ------------------------------------------------------------------------
    
    def track_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Track an HTTP request with all relevant metrics."""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size is not None:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size is not None:
            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    @contextmanager
    def track_http_in_progress(self, method: str, endpoint: str):
        """Context manager to track requests in progress."""
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()
        try:
            yield
        finally:
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
    
    # ------------------------------------------------------------------------
    # LLM Metrics
    # ------------------------------------------------------------------------
    
    def track_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        error_type: Optional[str] = None
    ):
        """Track an LLM API request with all relevant metrics."""
        llm_requests_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        llm_request_duration_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration)
        
        if prompt_tokens > 0:
            llm_tokens_total.labels(
                provider=provider,
                model=model,
                type='prompt'
            ).inc(prompt_tokens)
        
        if completion_tokens > 0:
            llm_tokens_total.labels(
                provider=provider,
                model=model,
                type='completion'
            ).inc(completion_tokens)
        
        if cost > 0:
            llm_cost_usd_total.labels(
                provider=provider,
                model=model
            ).inc(cost)
        
        if error_type:
            llm_errors_total.labels(
                provider=provider,
                model=model,
                error_type=error_type
            ).inc()
    
    # ------------------------------------------------------------------------
    # Agent Metrics
    # ------------------------------------------------------------------------
    
    def track_agent_execution(
        self,
        agent_type: str,
        status: str,
        duration: float
    ):
        """Track an agent execution."""
        agent_executions_total.labels(
            agent_type=agent_type,
            status=status
        ).inc()
        
        agent_execution_duration_seconds.labels(
            agent_type=agent_type
        ).observe(duration)
    
    @contextmanager
    def track_agent_in_progress(self, agent_type: str):
        """Context manager to track agent executions in progress."""
        agent_executions_in_progress.labels(
            agent_type=agent_type
        ).inc()
        try:
            yield
        finally:
            agent_executions_in_progress.labels(
                agent_type=agent_type
            ).dec()
    
    # ------------------------------------------------------------------------
    # Database Metrics
    # ------------------------------------------------------------------------
    
    def track_db_query(
        self,
        operation: str,
        duration: float,
        error_type: Optional[str] = None
    ):
        """Track a database query."""
        db_query_duration_seconds.labels(
            operation=operation
        ).observe(duration)
        
        if error_type:
            db_errors_total.labels(
                operation=operation,
                error_type=error_type
            ).inc()
    
    def update_db_connections(self, active: int, pool_size: int):
        """Update database connection metrics."""
        db_connections_active.set(active)
        db_pool_size.set(pool_size)
    
    # ------------------------------------------------------------------------
    # Cache Metrics
    # ------------------------------------------------------------------------
    
    def track_cache_operation(
        self,
        operation: str,
        result: str,  # 'hit' or 'miss'
        cache_name: str = 'default'
    ):
        """Track a cache operation."""
        cache_operations_total.labels(
            operation=operation,
            result=result
        ).inc()
    
    def update_cache_size(self, cache_name: str, size_bytes: int):
        """Update cache size metric."""
        cache_size_bytes.labels(
            cache_name=cache_name
        ).set(size_bytes)
    
    # ------------------------------------------------------------------------
    # API Key Metrics
    # ------------------------------------------------------------------------
    
    def track_api_key_request(
        self,
        organization: str,
        key_id: str,
        status: str
    ):
        """Track an API key request."""
        api_key_requests_total.labels(
            organization=organization,
            key_id=key_id,
            status=status
        ).inc()
    
    def track_rate_limit_exceeded(
        self,
        organization: str,
        limit_type: str
    ):
        """Track a rate limit exceeded event."""
        rate_limit_exceeded_total.labels(
            organization=organization,
            limit_type=limit_type
        ).inc()
    
    def update_quota_usage(
        self,
        organization: str,
        usage_percent: float
    ):
        """Update quota usage percentage."""
        quota_usage_percent.labels(
            organization=organization
        ).set(usage_percent)
    
    # ------------------------------------------------------------------------
    # Export Metrics
    # ------------------------------------------------------------------------
    
    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get the content type for Prometheus metrics."""
        return CONTENT_TYPE_LATEST


# ============================================================================
# GLOBAL METRICS INSTANCE
# ============================================================================

# Create a global metrics collector instance
metrics = MetricsCollector()


# ============================================================================
# CONVENIENCE DECORATORS
# ============================================================================

def track_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track execution time of a function.
    
    Usage:
        @track_time('my_function_duration', {'function': 'my_func'})
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # This is a simplified version - in production you'd want
                # to use the appropriate metric based on metric_name
                pass
        return wrapper
    return decorator


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of current metrics (for debugging/monitoring).
    
    Returns a dictionary with current metric values.
    """
    # This is a placeholder - in production you'd extract actual values
    # from the registry
    return {
        "http_requests": "See /metrics endpoint",
        "llm_requests": "See /metrics endpoint",
        "agent_executions": "See /metrics endpoint",
        "db_queries": "See /metrics endpoint",
    }


if __name__ == "__main__":
    # Example usage
    print("ProCode Agent Framework - Metrics Collector")
    print("=" * 60)
    
    # Simulate some metrics
    metrics.track_http_request("POST", "/api/chat", 200, 0.5, 1024, 2048)
    metrics.track_llm_request("openai", "gpt-4", "success", 2.5, 150, 75, 0.0045)
    metrics.track_agent_execution("payment", "success", 1.2)
    
    # Generate metrics
    print("\nGenerated Metrics:")
    print(metrics.generate_metrics().decode('utf-8'))
