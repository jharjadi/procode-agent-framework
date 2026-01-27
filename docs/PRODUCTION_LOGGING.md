# Production Logging Guide

## Overview

This guide explains how to utilize the centralized logging infrastructure in production environments for monitoring, debugging, and performance optimization.

## Production Setup

### 1. Docker Volume for Logs

Update [`docker-compose.yml`](../docker-compose.yml) to persist logs:

```yaml
services:
  agent:
    volumes:
      - ./logs:/app/logs  # Persist logs on host
      - ./data:/app/data
```

This ensures logs survive container restarts and are accessible from the host.

### 2. Log Rotation Configuration

The logging system automatically rotates logs:
- **Max Size**: 10MB per file
- **Backup Count**: 5 files
- **Total per logger**: ~50MB

For production, you may want to adjust these in [`observability/centralized_logger.py`](../observability/centralized_logger.py):

```python
StructuredLogger(
    name="app",
    max_bytes=50 * 1024 * 1024,  # 50MB per file
    backup_count=10               # Keep 10 backups
)
```

### 3. Log Retention Policy

Set up automated cleanup:

```bash
# Add to crontab on production server
0 2 * * * cd /path/to/app && make logs-clean  # Daily at 2 AM
```

Or use Docker volume cleanup:

```bash
# Clean logs older than 30 days
find /var/lib/docker/volumes/*/logs -name "*.jsonl*" -mtime +30 -delete
```

## Production Monitoring

### SSH into Production Server

```bash
# SSH to production
ssh user@apiproagent.harjadi.com

# Navigate to app directory
cd /path/to/procode-agent-framework
```

### Real-Time Monitoring

#### 1. Tail Recent Logs
```bash
# Show last 50 logs
make logs-tail

# Or use compact format for continuous monitoring
python3 scripts/search-logs.py --tail --limit 100 --format compact
```

#### 2. Monitor Errors
```bash
# Check for errors in last hour
make logs-since TIME="1h" | grep ERROR

# Or use the error filter
make logs-errors
```

#### 3. Monitor Agent Performance
```bash
# Show agent executions with performance metrics
make logs-agent

# Filter by specific agent
python3 scripts/search-logs.py --event-type agent_execution --query "tickets"
```

#### 4. Monitor HTTP Requests
```bash
# Show recent API requests
make logs-requests

# Filter by status code
python3 scripts/search-logs.py --event-type http_request --query "500"
```

### Performance Analysis

#### Find Slow Operations
```bash
# Search for operations taking >1000ms
python3 scripts/search-logs.py --format json | \
  jq 'select(.duration_ms > 1000) | {message, duration_ms, timestamp}'
```

#### Agent Performance Report
```bash
# Get average duration by agent
python3 scripts/search-logs.py --event-type agent_execution --format json | \
  jq -r '[.[] | {agent: .agent_name, duration: .duration_ms}] | 
         group_by(.agent) | 
         map({agent: .[0].agent, avg_duration: (map(.duration) | add / length)})'
```

#### Error Rate Analysis
```bash
# Count errors per hour
python3 scripts/search-logs.py --level error --since 24h --format json | \
  jq -r '.[] | .timestamp[:13]' | sort | uniq -c
```

## Production Debugging

### Scenario 1: User Reports Issue

```bash
# 1. Find user's recent activity
python3 scripts/search-logs.py --query "user_id:USER123" --since 1h

# 2. Check for errors related to user
python3 scripts/search-logs.py --level error --query "USER123"

# 3. Check agent executions for user
python3 scripts/search-logs.py --event-type agent_execution --query "USER123"
```

### Scenario 2: Performance Degradation

```bash
# 1. Check recent slow operations
python3 scripts/search-logs.py --since 1h --format json | \
  jq 'select(.duration_ms > 500) | {message, duration_ms}'

# 2. Check error rate
make logs-errors

# 3. Check system resources
docker stats procode-agent
```

### Scenario 3: Specific Feature Not Working

```bash
# 1. Search for feature-related logs
make logs-search QUERY="ticket creation"

# 2. Check agent execution success rate
python3 scripts/search-logs.py --event-type agent_execution --query "tickets" | \
  grep -c "success.*true"

# 3. Check for related errors
python3 scripts/search-logs.py --level error --query "ticket"
```

## Log Aggregation (Advanced)

### Option 1: Ship Logs to External Service

#### Using Filebeat (ELK Stack)
```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /app/logs/structured/*.jsonl
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

#### Using Fluentd
```conf
# fluent.conf
<source>
  @type tail
  path /app/logs/structured/*.jsonl
  pos_file /var/log/fluentd/app.pos
  tag app.logs
  <parse>
    @type json
  </parse>
</source>

<match app.logs>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name app-logs
</match>
```

### Option 2: Centralized Log Server

Set up a dedicated log server:

```bash
# On log server
mkdir -p /var/log/procode-agent
chmod 755 /var/log/procode-agent

# On production server, sync logs
rsync -avz logs/structured/ logserver:/var/log/procode-agent/
```

### Option 3: Cloud Logging

#### AWS CloudWatch
```python
# Add to centralized_logger.py
import watchtower

cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='procode-agent',
    stream_name='production'
)
logger.addHandler(cloudwatch_handler)
```

#### Google Cloud Logging
```python
from google.cloud import logging as gcp_logging

client = gcp_logging.Client()
handler = client.get_default_handler()
logger.addHandler(handler)
```

## Alerting

### Set Up Alerts for Critical Events

#### Email Alerts on Errors
```bash
# Create alert script
cat > /usr/local/bin/check-errors.sh << 'EOF'
#!/bin/bash
ERROR_COUNT=$(python3 /app/scripts/search-logs.py --level error --since 5m --format json | jq length)

if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "High error rate: $ERROR_COUNT errors in last 5 minutes" | \
    mail -s "Production Alert: High Error Rate" admin@example.com
fi
EOF

chmod +x /usr/local/bin/check-errors.sh

# Add to crontab (every 5 minutes)
*/5 * * * * /usr/local/bin/check-errors.sh
```

#### Slack Alerts
```python
# Add to observability/alerts.py
import requests

def send_slack_alert(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    requests.post(webhook_url, json={"text": message})

# Use in critical error logging
logger.critical("System failure", error=str(e))
send_slack_alert(f"🚨 Critical Error: {str(e)}")
```

## Production Dashboards

### Simple Dashboard with Grafana

```yaml
# docker-compose.yml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./logs:/logs:ro
```

### Metrics to Track

1. **Request Rate**: HTTP requests per minute
2. **Error Rate**: Errors per hour
3. **Agent Performance**: Average duration by agent
4. **Success Rate**: Successful operations percentage
5. **Response Time**: P50, P95, P99 latencies

## Best Practices for Production

### 1. Log Levels
- **DEBUG**: Disabled in production (too verbose)
- **INFO**: Normal operations, requests, agent executions
- **WARNING**: Potential issues, degraded performance
- **ERROR**: Failures that need attention
- **CRITICAL**: System-wide failures requiring immediate action

### 2. Sensitive Data
```python
# Never log sensitive data
logger.info("User login", user_id="123")  # ✅ Good

# Don't log passwords, tokens, PII
logger.info("Login", password="secret")   # ❌ Bad
```

### 3. Performance Impact
- Structured logging is fast (~1ms overhead)
- JSON serialization is efficient
- Log rotation prevents disk issues
- Async logging for high-throughput (future enhancement)

### 4. Disk Space Management
```bash
# Monitor disk usage
df -h /var/lib/docker/volumes

# Set up alerts for disk space
if [ $(df -h | grep '/var/lib/docker' | awk '{print $5}' | sed 's/%//') -gt 80 ]; then
    echo "Disk space warning" | mail -s "Disk Alert" admin@example.com
fi
```

## Quick Reference Commands

```bash
# Real-time monitoring
make logs-tail                    # Last 50 logs
make logs-errors                  # Recent errors
make logs-agent                   # Agent performance
make logs-requests                # HTTP requests

# Time-based queries
make logs-since TIME="1h"         # Last hour
make logs-since TIME="30m"        # Last 30 minutes
make logs-since TIME="1d"         # Last day

# Search queries
make logs-search QUERY="error"    # Search text
make logs-search QUERY="user_123" # Find user activity

# System health
make logs-stats                   # Log statistics
docker stats procode-agent        # Container stats
df -h                            # Disk usage

# Maintenance
make logs-clean                   # Clean old logs
docker system prune              # Clean Docker
```

## Troubleshooting

### Logs Not Appearing
```bash
# Check log directory permissions
ls -la logs/structured/

# Check if logger is initialized
grep "StructuredLogger" logs/structured/*.jsonl

# Check Docker volume mounts
docker inspect procode-agent | grep Mounts -A 10
```

### High Disk Usage
```bash
# Check log sizes
du -sh logs/structured/*

# Force rotation
make logs-clean

# Adjust retention policy
# Edit DEVELOPMENT_RULES.md log retention settings
```

### Search Performance Slow
```bash
# Limit search scope
python3 scripts/search-logs.py --since 1h  # Only recent logs

# Use specific filters
python3 scripts/search-logs.py --logger core.agent_router --level error

# Consider log aggregation for large volumes
```

## Related Documentation

- [Logging Infrastructure](./LOGGING_INFRASTRUCTURE.md)
- [Development Rules](../DEVELOPMENT_RULES.md)
- [Docker Deployment](./DOCKER_DEPLOYMENT.md)
