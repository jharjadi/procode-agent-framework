# Step 12: Production Monitoring & Observability - Design Document

## Overview

This document outlines the complete design for implementing production-grade monitoring and observability for the ProCode Agent Framework. This is a **CRITICAL** step for production readiness.

**Goal**: Full visibility into system health, performance, and errors

**Estimated Time**: 2-3 days

---

## 📊 Architecture Overview

### The Three Pillars of Observability

1. **Metrics** (Prometheus) - What is happening?
2. **Logs** (Centralized Logger) - Why is it happening?
3. **Traces** (OpenTelemetry) - Where is it happening?

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    ProCode Agent Framework                   │
├─────────────────────────────────────────────────────────────┤
│  Instrumentation Layer                                       │
│  ├─ Prometheus Metrics (Counter, Gauge, Histogram, Summary) │
│  ├─ OpenTelemetry Tracing (Spans, Context Propagation)     │
│  ├─ Sentry Error Tracking (Exception Capture)              │
│  └─ Health Checks (Liveness, Readiness)                    │
├─────────────────────────────────────────────────────────────┤
│  Export Layer                                                │
│  ├─ /metrics endpoint (Prometheus format)                   │
│  ├─ /health endpoint (JSON status)                          │
│  ├─ /ready endpoint (JSON readiness)                        │
│  └─ Sentry DSN (async error reporting)                      │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   Prometheus      Grafana        Sentry      AlertManager
   (Metrics)     (Dashboards)    (Errors)      (Alerts)
```

---

## 🎯 Success Criteria

- ✅ Prometheus metrics exported at `/metrics`
- ✅ Health check endpoint at `/health`
- ✅ Readiness probe at `/ready`
- ✅ OpenTelemetry tracing enabled
- ✅ Sentry error tracking configured
- ✅ Grafana dashboards created
- ✅ Alert rules configured
- ✅ <10ms overhead per request
- ✅ Zero data loss on metrics

---

## 📈 Metrics Design

### Metric Categories

#### 1. HTTP Metrics
```python
# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Request size
http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

# Response size
http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Active requests
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)
```

#### 2. LLM Metrics
```python
# LLM requests
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status']
)

# LLM latency
llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Token usage
llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens used',
    ['provider', 'model', 'type']  # type: prompt, completion
)

# LLM cost
llm_cost_usd_total = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model']
)

# LLM errors
llm_errors_total = Counter(
    'llm_errors_total',
    'Total LLM errors',
    ['provider', 'model', 'error_type']
)
```

#### 3. Agent Metrics
```python
# Agent executions
agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type', 'status']
)

# Agent duration
agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Active agents
agent_executions_in_progress = Gauge(
    'agent_executions_in_progress',
    'Number of agent executions in progress',
    ['agent_type']
)
```

#### 4. Database Metrics
```python
# Database connections
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

# Database pool size
db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size'
)

# Query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Query errors
db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['operation', 'error_type']
)
```

#### 5. Cache Metrics (for future Step 13)
```python
# Cache hits/misses
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # result: hit, miss
)

# Cache size
cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_name']
)
```

#### 6. API Key Metrics
```python
# API key requests
api_key_requests_total = Counter(
    'api_key_requests_total',
    'Total API key requests',
    ['organization', 'key_id', 'status']
)

# Rate limit hits
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['organization', 'limit_type']  # limit_type: per_minute, monthly
)

# Quota usage
quota_usage_percent = Gauge(
    'quota_usage_percent',
    'Quota usage percentage',
    ['organization']
)
```

#### 7. System Metrics
```python
# Python info
python_info = Info(
    'python_info',
    'Python version info'
)

# Application info
app_info = Info(
    'app_info',
    'Application version and build info'
)

# Process metrics (auto-collected by prometheus_client)
# - process_cpu_seconds_total
# - process_resident_memory_bytes
# - process_virtual_memory_bytes
# - process_open_fds
```

---

## 🏥 Health Checks Design

### Health Check Endpoint: `GET /health`

**Purpose**: Liveness probe - Is the application running?

**Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T09:00:00Z",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5.2,
      "message": "Connected to PostgreSQL"
    },
    "llm_provider": {
      "status": "healthy",
      "latency_ms": 150.3,
      "message": "OpenAI API accessible"
    },
    "external_agents": {
      "status": "degraded",
      "available": 2,
      "total": 3,
      "message": "1 agent unreachable"
    }
  }
}
```

**Status Codes**:
- `200 OK` - All checks passed (healthy)
- `503 Service Unavailable` - One or more critical checks failed (unhealthy)

**Health Check Components**:
1. **Database Check** - Can we connect and query?
2. **LLM Provider Check** - Can we reach OpenAI/Anthropic?
3. **External Agents Check** - Are registered agents responding?
4. **Disk Space Check** - Do we have enough disk space?
5. **Memory Check** - Is memory usage within limits?

### Readiness Endpoint: `GET /ready`

**Purpose**: Readiness probe - Is the application ready to serve traffic?

**Response Format**:
```json
{
  "ready": true,
  "timestamp": "2026-01-28T09:00:00Z",
  "checks": {
    "database_migrations": {
      "ready": true,
      "message": "All migrations applied"
    },
    "dependencies": {
      "ready": true,
      "message": "All dependencies loaded"
    },
    "warmup": {
      "ready": true,
      "message": "Application warmed up"
    }
  }
}
```

**Status Codes**:
- `200 OK` - Application is ready
- `503 Service Unavailable` - Application is not ready

---

## 🔍 Distributed Tracing Design

### OpenTelemetry Integration

**Trace Structure**:
```
Span: HTTP Request (POST /api/chat)
├─ Span: Intent Classification
│  └─ Span: LLM Call (OpenAI GPT-4)
├─ Span: Agent Routing
│  └─ Span: Agent Execution (PaymentAgent)
│     ├─ Span: Database Query (get_user_payments)
│     └─ Span: External API Call (payment_gateway)
└─ Span: Response Generation
   └─ Span: LLM Call (OpenAI GPT-4)
```

**Span Attributes**:
```python
# HTTP span attributes
span.set_attribute("http.method", "POST")
span.set_attribute("http.url", "/api/chat")
span.set_attribute("http.status_code", 200)
span.set_attribute("http.user_agent", "...")

# LLM span attributes
span.set_attribute("llm.provider", "openai")
span.set_attribute("llm.model", "gpt-4")
span.set_attribute("llm.tokens.prompt", 150)
span.set_attribute("llm.tokens.completion", 75)
span.set_attribute("llm.cost_usd", 0.0045)

# Agent span attributes
span.set_attribute("agent.type", "payment")
span.set_attribute("agent.intent", "check_balance")
span.set_attribute("agent.user_id", "user_123")

# Database span attributes
span.set_attribute("db.system", "postgresql")
span.set_attribute("db.operation", "SELECT")
span.set_attribute("db.table", "payments")
```

**Trace Context Propagation**:
- W3C Trace Context headers
- Propagate across microservices
- Correlate logs with traces

---

## 🚨 Error Tracking Design

### Sentry Integration

**Error Categories**:
1. **Application Errors** - Unhandled exceptions
2. **LLM Errors** - API failures, rate limits
3. **Database Errors** - Connection issues, query failures
4. **Agent Errors** - Agent execution failures
5. **Validation Errors** - Input validation failures

**Error Context**:
```python
sentry_sdk.set_context("user", {
    "id": user_id,
    "organization": org_id,
    "api_key": key_id
})

sentry_sdk.set_context("request", {
    "method": request.method,
    "url": request.url,
    "headers": sanitized_headers
})

sentry_sdk.set_context("llm", {
    "provider": "openai",
    "model": "gpt-4",
    "tokens": 150
})
```

**Error Fingerprinting**:
- Group similar errors together
- Custom fingerprinting rules
- Ignore known issues

**Error Sampling**:
- 100% for critical errors
- 50% for warnings
- 10% for info

---

## 📊 Alert Rules

### Critical Alerts (PagerDuty)

1. **Service Down**
   - Condition: `up == 0`
   - Duration: 1 minute
   - Action: Page on-call engineer

2. **High Error Rate**
   - Condition: `rate(http_requests_total{status=~"5.."}[5m]) > 0.05`
   - Duration: 5 minutes
   - Action: Page on-call engineer

3. **Database Connection Failure**
   - Condition: `db_connections_active == 0`
   - Duration: 2 minutes
   - Action: Page on-call engineer

4. **LLM Provider Down**
   - Condition: `rate(llm_errors_total[5m]) > 0.5`
   - Duration: 5 minutes
   - Action: Page on-call engineer

### Warning Alerts (Slack)

1. **High Response Time**
   - Condition: `http_request_duration_seconds{quantile="0.95"} > 2.0`
   - Duration: 10 minutes
   - Action: Notify team channel

2. **High Memory Usage**
   - Condition: `process_resident_memory_bytes > 2GB`
   - Duration: 15 minutes
   - Action: Notify team channel

3. **Rate Limit Approaching**
   - Condition: `rate_limit_exceeded_total > 100`
   - Duration: 5 minutes
   - Action: Notify team channel

4. **Disk Space Low**
   - Condition: `disk_free_percent < 20`
   - Duration: 30 minutes
   - Action: Notify team channel

---

## 🏗️ Implementation Plan

### Phase 1: Core Metrics (Day 1)
- ✅ Create `observability/metrics.py`
- ✅ Implement Prometheus metrics
- ✅ Add metrics middleware
- ✅ Create `/metrics` endpoint
- ✅ Test metrics collection

### Phase 2: Health Checks (Day 1)
- ✅ Create `observability/health.py`
- ✅ Implement health check logic
- ✅ Create `/health` endpoint
- ✅ Create `/ready` endpoint
- ✅ Test health checks

### Phase 3: Tracing (Day 2)
- ✅ Create `observability/tracing.py`
- ✅ Configure OpenTelemetry
- ✅ Add tracing middleware
- ✅ Instrument key functions
- ✅ Test trace collection

### Phase 4: Error Tracking (Day 2)
- ✅ Configure Sentry SDK
- ✅ Add error context
- ✅ Test error capture
- ✅ Configure error filtering

### Phase 5: Alerts (Day 2)
- ✅ Create `observability/alerts.py`
- ✅ Define alert rules
- ✅ Configure AlertManager
- ✅ Test alert delivery

### Phase 6: Infrastructure (Day 3)
- ✅ Update `docker-compose.yml`
- ✅ Add Prometheus container
- ✅ Add Grafana container
- ✅ Add AlertManager container
- ✅ Configure service discovery

### Phase 7: Dashboards (Day 3)
- ✅ Create Grafana dashboards
- ✅ Configure data sources
- ✅ Import dashboards
- ✅ Test visualizations

### Phase 8: Documentation (Day 3)
- ✅ Write monitoring guide
- ✅ Document alert runbooks
- ✅ Create troubleshooting guide

---

## 📁 File Structure

```
procode-agent-framework/
├── observability/
│   ├── __init__.py
│   ├── metrics.py              # Prometheus metrics
│   ├── health.py               # Health checks
│   ├── tracing.py              # OpenTelemetry tracing
│   ├── alerts.py               # Alert rules
│   └── middleware.py           # Monitoring middleware
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml      # Prometheus config
│   │   └── alerts.yml          # Alert rules
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── overview.json
│   │   │   ├── llm.json
│   │   │   ├── agents.json
│   │   │   └── database.json
│   │   └── datasources/
│   │       └── prometheus.yml
│   └── alertmanager/
│       └── alertmanager.yml    # AlertManager config
├── docker-compose.monitoring.yml
└── docs/
    ├── STEP12_MONITORING_DESIGN.md
    ├── STEP12_MONITORING_GUIDE.md
    └── STEP12_ALERT_RUNBOOK.md
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
ENABLE_HEALTH_CHECKS=true

# Prometheus
PROMETHEUS_PORT=9090
METRICS_ENDPOINT=/metrics

# OpenTelemetry
OTEL_SERVICE_NAME=procode-agent-framework
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling

# Sentry
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

# Health Checks
HEALTH_CHECK_TIMEOUT_SECONDS=5
HEALTH_CHECK_DATABASE=true
HEALTH_CHECK_LLM=true
HEALTH_CHECK_AGENTS=true

# Grafana
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<secure-password>

# AlertManager
ALERTMANAGER_PORT=9093
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/...
ALERT_PAGERDUTY_KEY=<pagerduty-key>
```

---

## 📊 Grafana Dashboards

### 1. Overview Dashboard
- Request rate (req/s)
- Error rate (%)
- Response time (p50, p95, p99)
- Active requests
- System resources (CPU, memory)

### 2. LLM Dashboard
- LLM requests by provider
- Token usage by model
- LLM cost over time
- LLM latency distribution
- Error rate by provider

### 3. Agent Dashboard
- Agent executions by type
- Agent success rate
- Agent execution time
- Active agent executions
- Agent errors

### 4. Database Dashboard
- Active connections
- Query duration
- Query rate
- Connection pool usage
- Database errors

### 5. API Key Dashboard
- Requests by organization
- Rate limit hits
- Quota usage
- Top consumers
- API key errors

---

## 🧪 Testing Strategy

### Unit Tests
- Test metric collection
- Test health check logic
- Test alert rule evaluation

### Integration Tests
- Test `/metrics` endpoint
- Test `/health` endpoint
- Test `/ready` endpoint
- Test trace propagation
- Test error capture

### Load Tests
- Verify metrics under load
- Verify tracing overhead
- Verify health check performance

### Chaos Tests
- Simulate database failure
- Simulate LLM provider failure
- Verify alert delivery

---

## 📈 Performance Targets

- **Metrics Collection**: <5ms overhead per request
- **Health Check**: <100ms response time
- **Tracing**: <10ms overhead per request
- **Error Capture**: <1ms overhead per error
- **Metrics Endpoint**: <500ms response time

---

## 🔒 Security Considerations

1. **Metrics Endpoint**:
   - Expose only on internal network
   - Or require authentication
   - Don't expose sensitive data in labels

2. **Health Endpoint**:
   - Don't expose internal details publicly
   - Sanitize error messages
   - Rate limit to prevent abuse

3. **Sentry**:
   - Scrub sensitive data (passwords, API keys)
   - Use data scrubbing rules
   - Configure IP anonymization

4. **Tracing**:
   - Don't include sensitive data in spans
   - Sanitize span attributes
   - Use sampling to reduce data volume

---

## 📚 References

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)

---

## ✅ Ready for Implementation

This design document provides a complete blueprint for implementing production monitoring and observability. Implementation can begin immediately following this plan.

**Next Step**: Install dependencies and start Phase 1 (Core Metrics)

---

**Document Version**: 1.0  
**Created**: 2026-01-28  
**Status**: Ready for Implementation  
**Estimated Completion**: 2-3 days
