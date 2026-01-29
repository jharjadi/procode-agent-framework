# Centralized Logging Infrastructure

## Overview

This project implements a centralized, structured logging system that provides total machine observability for hypervelocity development. All logs are stored in JSON format for easy searching, parsing, and analysis.

## Architecture

### Components

1. **StructuredLogger** ([`observability/centralized_logger.py`](../observability/centralized_logger.py))
   - Outputs JSON logs for machine parsing
   - Provides human-readable console output
   - Supports log rotation and retention
   - Includes specialized logging methods for different event types

2. **Log Search CLI** ([`scripts/search-logs.py`](../scripts/search-logs.py))
   - Powerful search and filtering capabilities
   - Multiple output formats (pretty, JSON, compact)
   - Time-based filtering (relative and absolute)
   - Event type filtering

3. **Makefile Commands** ([`Makefile`](../Makefile))
   - Quick access to common log operations
   - Pre-configured searches for common scenarios
   - Log maintenance and statistics

## Usage

### Basic Logging

```python
from observability.centralized_logger import get_logger

# Get a logger
logger = get_logger(__name__)

# Log messages with structured data
logger.info("User logged in", user_id="123", ip_address="192.168.1.1")
logger.error("Database connection failed", error="timeout", retry_count=3)

# Specialized logging methods
logger.log_request(
    method="POST",
    path="/api/message",
    status_code=200,
    duration_ms=45.2
)

logger.log_agent_execution(
    agent_name="tickets",
    intent="create_ticket",
    success=True,
    duration_ms=123.4
)

logger.log_test_result(
    test_name="test_greetings",
    passed=True,
    duration_ms=56.7
)
```

### Searching Logs

#### Using Make Commands (Recommended)

```bash
# Show last 50 logs
make logs-tail

# Show recent errors
make logs-errors

# Show agent execution logs
make logs-agent

# Show HTTP request logs
make logs-requests

# Show logs from last hour
make logs-since TIME="1h"

# Search for specific text
make logs-search QUERY="ticket created"

# Show log statistics
make logs-stats

# Clean old logs (>7 days)
make logs-clean
```

#### Using CLI Directly

```bash
# Search for errors in the last hour
python3 scripts/search-logs.py --level error --since 1h

# Search for agent executions
python3 scripts/search-logs.py --event-type agent_execution

# Search for specific text
python3 scripts/search-logs.py --query "ticket created"

# Show last 50 logs
python3 scripts/search-logs.py --tail --limit 50

# Combine filters
python3 scripts/search-logs.py --level error --logger core.agent_router --since 30m

# Output as JSON
python3 scripts/search-logs.py --format json --limit 10

# Compact format
python3 scripts/search-logs.py --format compact --tail --limit 20
```

## Log Structure

### Standard Fields

Every log entry includes:

```json
{
  "timestamp": "2024-01-26T12:34:56.789012",
  "level": "INFO",
  "logger": "core.agent_router",
  "message": "Agent executed successfully"
}
```

### Event-Specific Fields

#### HTTP Request
```json
{
  "event_type": "http_request",
  "method": "POST",
  "path": "/api/message",
  "status_code": 200,
  "duration_ms": 45.2
}
```

#### Agent Execution
```json
{
  "event_type": "agent_execution",
  "agent_name": "tickets",
  "intent": "create_ticket",
  "success": true,
  "duration_ms": 123.4
}
```

#### Test Result
```json
{
  "event_type": "test_result",
  "test_name": "test_greetings",
  "passed": true,
  "duration_ms": 56.7
}
```

## Log Locations

- **Structured Logs**: `logs/structured/*.jsonl`
- **Audit Logs**: `logs/audit/*.jsonl`
- **Test Reports**: `test-reports/*.txt`

## Log Rotation

- Logs automatically rotate at 10MB per file
- Keeps 5 backup files per logger
- Old logs (>7 days) can be cleaned with `make logs-clean`

## Integration with Components

### Agent Router

```python
from observability.centralized_logger import get_logger

logger = get_logger(__name__)

# Log agent execution
start_time = time.time()
result = await agent.invoke(context)
duration_ms = (time.time() - start_time) * 1000

logger.log_agent_execution(
    agent_name="tickets",
    intent=intent,
    success=True,
    duration_ms=duration_ms,
    user_id=user_id
)
```

### API Endpoints

```python
from observability.centralized_logger import get_logger

logger = get_logger(__name__)

# Log HTTP requests
@app.post("/api/message")
async def handle_message(request: Request):
    start_time = time.time()
    
    # Process request...
    
    duration_ms = (time.time() - start_time) * 1000
    logger.log_request(
        method="POST",
        path="/api/message",
        status_code=200,
        duration_ms=duration_ms
    )
```

### Test Suite

```python
from observability.centralized_logger import get_logger

logger = get_logger(__name__)

# Log test results
def test_something():
    start_time = time.time()
    
    # Run test...
    passed = True
    
    duration_ms = (time.time() - start_time) * 1000
    logger.log_test_result(
        test_name="test_something",
        passed=passed,
        duration_ms=duration_ms
    )
```

## Best Practices

### 1. Use Structured Data

```python
# Good - structured data
logger.info("User action", action="login", user_id="123", success=True)

# Bad - unstructured string
logger.info(f"User 123 logged in successfully")
```

### 2. Include Context

```python
# Include relevant context for debugging
logger.error(
    "Database query failed",
    query="SELECT * FROM users",
    error=str(e),
    retry_count=3,
    user_id=user_id
)
```

### 3. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical messages for severe failures

### 4. Log Performance Metrics

```python
# Always log duration for performance tracking
logger.log_agent_execution(
    agent_name="tickets",
    intent="create_ticket",
    success=True,
    duration_ms=duration_ms  # Important!
)
```

## Hypervelocity Benefits

1. **Immediate Feedback**: Search logs instantly to understand system behavior
2. **Closed-Loop Debugging**: Logs provide immediate feedback for debugging
3. **Performance Tracking**: Track execution times and identify bottlenecks
4. **Audit Trail**: Complete history of all system events
5. **Machine-Readable**: JSON format enables automated analysis and alerting

## Future Enhancements

- [ ] Real-time log streaming dashboard
- [ ] Integration with OpenSearch/Elasticsearch
- [ ] Automated alerting on error patterns
- [ ] Log aggregation across distributed systems
- [ ] Performance metrics visualization
- [ ] Log-based testing and verification

## Related Documentation

- [Hypervelocity Manifesto](../DEVELOPMENT_RULES.md#hypervelocity-principles)
- [Test Automation](../DEVELOPMENT_RULES.md#hypervelocity-test-automation)
- [Audit Logging](./SECURITY_IMPLEMENTATION.md)
