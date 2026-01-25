"""
Audit Logger Module

This module provides comprehensive audit logging for security, compliance,
and operational monitoring. It logs all significant events with appropriate
severity levels and supports daily log rotation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading


class AuditLogger:
    """
    Audit logging for security and compliance.
    
    Logs events to daily JSON Lines files with structured data including
    timestamps, event types, user IDs, severity levels, and event details.
    """
    
    def __init__(self, log_dir: str = "logs/audit"):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        severity: str = "info"
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'blocked_content', 'tool_execution')
            details: Dictionary with event-specific details
            user_id: Optional user identifier
            severity: Event severity ('info', 'warning', 'error', 'critical')
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "severity": severity,
            "details": details
        }
        
        # Write to daily log file
        with self._lock:
            log_file = self._get_log_file()
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                # Fallback to stderr if file writing fails
                print(f"Failed to write audit log: {e}", file=__import__('sys').stderr)
    
    def _get_log_file(self) -> Path:
        """
        Get the current day's log file path.
        
        Returns:
            Path to the current log file
        """
        date_str = datetime.now().strftime('%Y%m%d')
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    def log_blocked_content(self, content: str, user_id: Optional[str] = None):
        """
        Log blocked content attempt.
        
        Args:
            content: The blocked content (truncated for logging)
            user_id: Optional user identifier
        """
        self.log_event(
            "blocked_content",
            {
                "content_preview": content[:100],
                "content_length": len(content)
            },
            user_id,
            "warning"
        )
    
    def log_pii_detection(self, pii_types: List[str], user_id: Optional[str] = None):
        """
        Log PII detection.
        
        Args:
            pii_types: List of detected PII types
            user_id: Optional user identifier
        """
        self.log_event(
            "pii_detected",
            {"pii_types": pii_types},
            user_id,
            "info"
        )
    
    def log_security_event(
        self,
        event_type: str,
        content: str,
        user_id: Optional[str] = None
    ):
        """
        Log security event.
        
        Args:
            event_type: Type of security event
            content: Content that triggered the event (truncated)
            user_id: Optional user identifier
        """
        self.log_event(
            f"security_{event_type}",
            {
                "content_preview": content[:100],
                "content_length": len(content)
            },
            user_id,
            "critical"
        )
    
    def log_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: str,
        user_id: Optional[str] = None,
        success: bool = True
    ):
        """
        Log tool execution for audit trail.
        
        Args:
            tool_name: Name of the tool executed
            parameters: Tool parameters
            result: Execution result (truncated)
            user_id: Optional user identifier
            success: Whether execution was successful
        """
        self.log_event(
            "tool_execution",
            {
                "tool": tool_name,
                "parameters": parameters,
                "result_preview": result[:100],
                "success": success
            },
            user_id,
            "info" if success else "error"
        )
    
    def log_rate_limit_exceeded(self, user_id: str, limit_type: str):
        """
        Log rate limit exceeded event.
        
        Args:
            user_id: User who exceeded the limit
            limit_type: Type of limit exceeded (minute/hour/day)
        """
        self.log_event(
            "rate_limit_exceeded",
            {"limit_type": limit_type},
            user_id,
            "warning"
        )
    
    def log_authentication(
        self,
        user_id: str,
        success: bool,
        method: str = "unknown"
    ):
        """
        Log authentication attempt.
        
        Args:
            user_id: User attempting authentication
            success: Whether authentication succeeded
            method: Authentication method used
        """
        self.log_event(
            "authentication",
            {
                "success": success,
                "method": method
            },
            user_id,
            "info" if success else "warning"
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool = True
    ):
        """
        Log data access for compliance.
        
        Args:
            user_id: User accessing data
            resource: Resource being accessed
            action: Action performed (read/write/delete)
            success: Whether access was successful
        """
        self.log_event(
            "data_access",
            {
                "resource": resource,
                "action": action,
                "success": success
            },
            user_id,
            "info"
        )
    
    def log_circuit_breaker_event(
        self,
        service: str,
        state: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log circuit breaker state change.
        
        Args:
            service: Service name
            state: New circuit breaker state
            details: Optional additional details
        """
        self.log_event(
            "circuit_breaker",
            {
                "service": service,
                "state": state,
                **(details or {})
            },
            None,
            "warning" if state == "open" else "info"
        )
    
    def log_compliance_event(
        self,
        event_type: str,
        user_id: str,
        details: Dict[str, Any]
    ):
        """
        Log compliance-related event (GDPR, data retention, etc.).
        
        Args:
            event_type: Type of compliance event
            user_id: User associated with the event
            details: Event details
        """
        self.log_event(
            f"compliance_{event_type}",
            details,
            user_id,
            "info"
        )
    
    def get_recent_events(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent audit events (from today's log).
        
        Args:
            limit: Maximum number of events to return
            severity: Filter by severity level
            event_type: Filter by event type
            
        Returns:
            List of audit events
        """
        events = []
        log_file = self._get_log_file()
        
        if not log_file.exists():
            return events
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if severity and event.get("severity") != severity:
                            continue
                        if event_type and event.get("event_type") != event_type:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return events[-limit:]  # Return most recent
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about audit logs.
        
        Returns:
            Dictionary with log statistics
        """
        log_file = self._get_log_file()
        
        if not log_file.exists():
            return {
                "total_events": 0,
                "log_file": str(log_file),
                "exists": False
            }
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            severity_counts = {}
            event_type_counts = {}
            
            for line in lines:
                try:
                    event = json.loads(line.strip())
                    severity = event.get("severity", "unknown")
                    event_type = event.get("event_type", "unknown")
                    
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            return {
                "total_events": len(lines),
                "log_file": str(log_file),
                "exists": True,
                "severity_counts": severity_counts,
                "event_type_counts": event_type_counts
            }
        except Exception as e:
            return {
                "total_events": 0,
                "log_file": str(log_file),
                "exists": True,
                "error": str(e)
            }


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_global_audit_logger() -> AuditLogger:
    """
    Get or create the global audit logger instance.
    
    Returns:
        Global AuditLogger instance
    """
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


def reset_global_audit_logger():
    """Reset the global audit logger (useful for testing)."""
    global _global_audit_logger
    _global_audit_logger = None
