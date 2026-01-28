"""
Alert Configuration for ProCode Agent Framework

This module defines alert rules for Prometheus AlertManager.
Alerts are categorized by severity:
- CRITICAL: Requires immediate attention (page on-call)
- WARNING: Requires attention soon (notify team)
- INFO: Informational only

Usage:
    This file is used to generate Prometheus alert rules.
    The alert rules are exported to monitoring/prometheus/alerts.yml
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class AlertRule:
    """Definition of a Prometheus alert rule."""
    name: str
    severity: AlertSeverity
    expr: str  # PromQL expression
    duration: str  # How long condition must be true
    summary: str
    description: str
    runbook_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Prometheus alert rule format."""
        rule = {
            "alert": self.name,
            "expr": self.expr,
            "for": self.duration,
            "labels": {
                "severity": self.severity.value
            },
            "annotations": {
                "summary": self.summary,
                "description": self.description
            }
        }
        if self.runbook_url:
            rule["annotations"]["runbook_url"] = self.runbook_url
        return rule


# ============================================================================
# CRITICAL ALERTS (Page On-Call)
# ============================================================================

CRITICAL_ALERTS = [
    AlertRule(
        name="ServiceDown",
        severity=AlertSeverity.CRITICAL,
        expr='up{job="procode-agent"} == 0',
        duration="1m",
        summary="ProCode Agent service is down",
        description="The ProCode Agent service has been down for more than 1 minute.",
        runbook_url="https://docs.procode.io/runbooks/service-down"
    ),
    
    AlertRule(
        name="HighErrorRate",
        severity=AlertSeverity.CRITICAL,
        expr='rate(http_requests_total{status=~"5.."}[5m]) > 0.05',
        duration="5m",
        summary="High error rate detected",
        description="Error rate is above 5% for the last 5 minutes ({{ $value | humanizePercentage }}).",
        runbook_url="https://docs.procode.io/runbooks/high-error-rate"
    ),
    
    AlertRule(
        name="DatabaseConnectionFailure",
        severity=AlertSeverity.CRITICAL,
        expr='db_connections_active == 0',
        duration="2m",
        summary="Database connection failure",
        description="No active database connections for more than 2 minutes.",
        runbook_url="https://docs.procode.io/runbooks/database-failure"
    ),
    
    AlertRule(
        name="LLMProviderDown",
        severity=AlertSeverity.CRITICAL,
        expr='rate(llm_errors_total[5m]) > 0.5',
        duration="5m",
        summary="LLM provider experiencing high error rate",
        description="LLM provider error rate is above 50% for the last 5 minutes.",
        runbook_url="https://docs.procode.io/runbooks/llm-provider-down"
    ),
    
    AlertRule(
        name="DiskSpaceCritical",
        severity=AlertSeverity.CRITICAL,
        expr='(node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10',
        duration="5m",
        summary="Disk space critically low",
        description="Disk space is below 10% ({{ $value | humanize }}% remaining).",
        runbook_url="https://docs.procode.io/runbooks/disk-space-critical"
    ),
    
    AlertRule(
        name="MemoryCritical",
        severity=AlertSeverity.CRITICAL,
        expr='(process_resident_memory_bytes / node_memory_MemTotal_bytes) * 100 > 90',
        duration="10m",
        summary="Memory usage critically high",
        description="Memory usage is above 90% for more than 10 minutes ({{ $value | humanize }}%).",
        runbook_url="https://docs.procode.io/runbooks/memory-critical"
    ),
]


# ============================================================================
# WARNING ALERTS (Notify Team)
# ============================================================================

WARNING_ALERTS = [
    AlertRule(
        name="HighResponseTime",
        severity=AlertSeverity.WARNING,
        expr='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2.0',
        duration="10m",
        summary="High response time detected",
        description="95th percentile response time is above 2 seconds for the last 10 minutes ({{ $value | humanizeDuration }}).",
        runbook_url="https://docs.procode.io/runbooks/high-response-time"
    ),
    
    AlertRule(
        name="HighMemoryUsage",
        severity=AlertSeverity.WARNING,
        expr='(process_resident_memory_bytes / node_memory_MemTotal_bytes) * 100 > 80',
        duration="15m",
        summary="High memory usage",
        description="Memory usage is above 80% for more than 15 minutes ({{ $value | humanize }}%).",
        runbook_url="https://docs.procode.io/runbooks/high-memory"
    ),
    
    AlertRule(
        name="RateLimitApproaching",
        severity=AlertSeverity.WARNING,
        expr='rate(rate_limit_exceeded_total[5m]) > 100',
        duration="5m",
        summary="Rate limit frequently exceeded",
        description="Rate limit exceeded more than 100 times in the last 5 minutes.",
        runbook_url="https://docs.procode.io/runbooks/rate-limit"
    ),
    
    AlertRule(
        name="DiskSpaceLow",
        severity=AlertSeverity.WARNING,
        expr='(node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 20',
        duration="30m",
        summary="Disk space running low",
        description="Disk space is below 20% ({{ $value | humanize }}% remaining).",
        runbook_url="https://docs.procode.io/runbooks/disk-space-low"
    ),
    
    AlertRule(
        name="LLMCostSpike",
        severity=AlertSeverity.WARNING,
        expr='rate(llm_cost_usd_total[1h]) > 10',
        duration="1h",
        summary="LLM cost spike detected",
        description="LLM costs are above $10/hour for the last hour ({{ $value | humanize }}).",
        runbook_url="https://docs.procode.io/runbooks/llm-cost-spike"
    ),
    
    AlertRule(
        name="AgentExecutionFailures",
        severity=AlertSeverity.WARNING,
        expr='rate(agent_executions_total{status="error"}[10m]) > 0.1',
        duration="10m",
        summary="High agent execution failure rate",
        description="Agent execution failure rate is above 10% for the last 10 minutes.",
        runbook_url="https://docs.procode.io/runbooks/agent-failures"
    ),
    
    AlertRule(
        name="DatabaseSlowQueries",
        severity=AlertSeverity.WARNING,
        expr='histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 0.5',
        duration="10m",
        summary="Slow database queries detected",
        description="95th percentile database query time is above 500ms for the last 10 minutes.",
        runbook_url="https://docs.procode.io/runbooks/slow-queries"
    ),
    
    AlertRule(
        name="ExternalAgentUnreachable",
        severity=AlertSeverity.WARNING,
        expr='up{job="external-agent"} == 0',
        duration="5m",
        summary="External agent unreachable",
        description="External agent {{ $labels.instance }} has been unreachable for more than 5 minutes.",
        runbook_url="https://docs.procode.io/runbooks/agent-unreachable"
    ),
]


# ============================================================================
# INFO ALERTS (Informational)
# ============================================================================

INFO_ALERTS = [
    AlertRule(
        name="HighRequestVolume",
        severity=AlertSeverity.INFO,
        expr='rate(http_requests_total[5m]) > 100',
        duration="10m",
        summary="High request volume",
        description="Request rate is above 100 req/s for the last 10 minutes ({{ $value | humanize }} req/s).",
        runbook_url=""
    ),
    
    AlertRule(
        name="NewUserRegistration",
        severity=AlertSeverity.INFO,
        expr='increase(api_key_requests_total{status="created"}[1h]) > 10',
        duration="1h",
        summary="High new user registration rate",
        description="More than 10 new users registered in the last hour.",
        runbook_url=""
    ),
]


# ============================================================================
# ALERT GROUPS
# ============================================================================

def get_all_alerts() -> List[AlertRule]:
    """Get all alert rules."""
    return CRITICAL_ALERTS + WARNING_ALERTS + INFO_ALERTS


def get_alerts_by_severity(severity: AlertSeverity) -> List[AlertRule]:
    """Get alerts filtered by severity."""
    all_alerts = get_all_alerts()
    return [alert for alert in all_alerts if alert.severity == severity]


def generate_prometheus_rules() -> Dict[str, Any]:
    """
    Generate Prometheus alert rules in YAML format.
    
    Returns:
        Dictionary that can be serialized to YAML for Prometheus.
    """
    groups = []
    
    # Group by severity
    for severity in AlertSeverity:
        alerts = get_alerts_by_severity(severity)
        if alerts:
            groups.append({
                "name": f"{severity.value}_alerts",
                "rules": [alert.to_dict() for alert in alerts]
            })
    
    return {
        "groups": groups
    }


# ============================================================================
# ALERT MANAGER CONFIGURATION
# ============================================================================

ALERTMANAGER_CONFIG = """
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    
    # Warning alerts go to Slack
    - match:
        severity: warning
      receiver: 'slack'
    
    # Info alerts go to Slack (low priority)
    - match:
        severity: info
      receiver: 'slack-info'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'ProCode Agent Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
  
  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        title: '⚠️ {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'warning'
  
  - name: 'slack-info'
    slack_configs:
      - channel: '#monitoring'
        title: 'ℹ️ {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        color: 'good'

inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
"""


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_prometheus_rules(output_file: str = "monitoring/prometheus/alerts.yml"):
    """
    Export Prometheus alert rules to YAML file.
    
    Args:
        output_file: Path to output file
    """
    import yaml
    import os
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Generate rules
    rules = generate_prometheus_rules()
    
    # Write to file
    with open(output_file, 'w') as f:
        yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Prometheus alert rules exported to {output_file}")


def export_alertmanager_config(output_file: str = "monitoring/alertmanager/alertmanager.yml"):
    """
    Export AlertManager configuration to YAML file.
    
    Args:
        output_file: Path to output file
    """
    import os
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(ALERTMANAGER_CONFIG)
    
    print(f"✅ AlertManager configuration exported to {output_file}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("ProCode Agent Framework - Alert Configuration")
    print("=" * 60)
    
    # Print alert summary
    print(f"\nTotal alerts: {len(get_all_alerts())}")
    print(f"  - Critical: {len(get_alerts_by_severity(AlertSeverity.CRITICAL))}")
    print(f"  - Warning: {len(get_alerts_by_severity(AlertSeverity.WARNING))}")
    print(f"  - Info: {len(get_alerts_by_severity(AlertSeverity.INFO))}")
    
    # Export rules
    print("\nExporting alert rules...")
    try:
        export_prometheus_rules()
        export_alertmanager_config()
        print("\n✅ Alert configuration exported successfully")
    except Exception as e:
        print(f"\n❌ Failed to export configuration: {e}")
