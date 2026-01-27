"""
Centralized Logging Infrastructure for Hypervelocity Development

Provides structured, searchable logging with JSON output for easy parsing.
Implements total machine observability principle.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


class StructuredLogger:
    """
    Structured logger that outputs JSON for easy searching and parsing.
    """
    
    def __init__(
        self,
        name: str,
        log_dir: str = "logs/structured",
        level: int = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
            log_dir: Directory for log files
            level: Logging level
            max_bytes: Max size per log file
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # JSON file handler
        json_log_file = self.log_dir / f"{name}.jsonl"
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
        
        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(HumanReadableFormatter())
        self.logger.addHandler(console_handler)
    
    def _log(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ) -> None:
        """
        Internal log method with structured data.
        
        Args:
            level: Log level (info, warning, error, etc.)
            message: Log message
            **kwargs: Additional structured data
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "logger": self.name,
            "message": message,
            **kwargs
        }
        
        # Log with appropriate level
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with structured data."""
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with structured data."""
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with structured data."""
        self._log("error", message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with structured data."""
        self._log("debug", message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with structured data."""
        self._log("critical", message, **kwargs)
    
    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """Log HTTP request with structured data."""
        self._log(
            "info",
            f"{method} {path} {status_code}",
            event_type="http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_agent_execution(
        self,
        agent_name: str,
        intent: str,
        success: bool,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """Log agent execution with structured data."""
        self._log(
            "info",
            f"Agent {agent_name} executed {intent}",
            event_type="agent_execution",
            agent_name=agent_name,
            intent=intent,
            success=success,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_test_result(
        self,
        test_name: str,
        passed: bool,
        duration_ms: float,
        **kwargs: Any
    ) -> None:
        """Log test result with structured data."""
        self._log(
            "info" if passed else "error",
            f"Test {test_name} {'passed' if passed else 'failed'}",
            event_type="test_result",
            test_name=test_name,
            passed=passed,
            duration_ms=duration_ms,
            **kwargs
        )


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON for machine parsing."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # The message is already JSON from StructuredLogger
        return record.getMessage()


class HumanReadableFormatter(logging.Formatter):
    """Formatter that outputs human-readable logs to console."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human reading."""
        try:
            log_data = json.loads(record.getMessage())
            timestamp = log_data.get("timestamp", "")
            level = log_data.get("level", "INFO")
            message = log_data.get("message", "")
            
            # Color codes
            colors = {
                "DEBUG": "\033[0;36m",    # Cyan
                "INFO": "\033[0;32m",     # Green
                "WARNING": "\033[0;33m",  # Yellow
                "ERROR": "\033[0;31m",    # Red
                "CRITICAL": "\033[0;35m", # Magenta
            }
            reset = "\033[0m"
            
            color = colors.get(level, "")
            return f"{color}[{timestamp}] {level:8s} {message}{reset}"
        except (json.JSONDecodeError, KeyError):
            return record.getMessage()


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


# Convenience function for quick logging
def log_event(
    event_type: str,
    message: str,
    level: str = "info",
    **kwargs: Any
) -> None:
    """
    Quick logging function for events.
    
    Args:
        event_type: Type of event (e.g., "agent_execution", "http_request")
        message: Log message
        level: Log level
        **kwargs: Additional structured data
    """
    logger = get_logger("app")
    log_method = getattr(logger, level.lower())
    log_method(message, event_type=event_type, **kwargs)
