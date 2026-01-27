#!/usr/bin/env python3
"""
Demo script to showcase hypervelocity logging and test automation.
"""

import time
from observability.centralized_logger import get_logger

# Get logger
logger = get_logger("demo")

print("🚀 Hypervelocity Demo - Generating Sample Logs\n")

# Demo 1: Basic logging
print("1. Basic Logging:")
logger.info("Application started", version="1.0.0", environment="demo")
logger.debug("Debug information", module="demo", details="sample data")
logger.warning("This is a warning", reason="demo purposes")
print("   ✓ Generated info, debug, and warning logs\n")

# Demo 2: HTTP Request logging
print("2. HTTP Request Logging:")
logger.log_request(
    method="POST",
    path="/api/message",
    status_code=200,
    duration_ms=45.2,
    user_id="demo_user"
)
logger.log_request(
    method="GET",
    path="/api/status",
    status_code=200,
    duration_ms=12.5
)
print("   ✓ Generated HTTP request logs\n")

# Demo 3: Agent execution logging
print("3. Agent Execution Logging:")
logger.log_agent_execution(
    agent_name="tickets",
    intent="create_ticket",
    success=True,
    duration_ms=123.4,
    ticket_id="DEMO-001"
)
logger.log_agent_execution(
    agent_name="general",
    intent="greeting",
    success=True,
    duration_ms=45.6
)
logger.log_agent_execution(
    agent_name="payments",
    intent="check_balance",
    success=False,
    duration_ms=234.5,
    error="insufficient_permissions"
)
print("   ✓ Generated agent execution logs\n")

# Demo 4: Test result logging
print("4. Test Result Logging:")
logger.log_test_result(
    test_name="test_greetings",
    passed=True,
    duration_ms=56.7
)
logger.log_test_result(
    test_name="test_tickets",
    passed=True,
    duration_ms=123.4
)
logger.log_test_result(
    test_name="test_payments",
    passed=False,
    duration_ms=89.2,
    error="assertion_failed"
)
print("   ✓ Generated test result logs\n")

# Demo 5: Error logging
print("5. Error Logging:")
logger.error(
    "Database connection failed",
    error="timeout",
    retry_count=3,
    database="postgres"
)
logger.critical(
    "System critical error",
    error="out_of_memory",
    available_mb=128
)
print("   ✓ Generated error and critical logs\n")

print("=" * 60)
print("✅ Demo Complete! Logs saved to logs/structured/demo.jsonl")
print("=" * 60)
print("\n📊 Try these commands to search the logs:\n")
print("  make logs-tail              # Show last 50 logs")
print("  make logs-errors            # Show recent errors")
print("  make logs-agent             # Show agent executions")
print("  make logs-requests          # Show HTTP requests")
print("  make logs-search QUERY=\"ticket\"  # Search for 'ticket'")
print("  make logs-stats             # Show log statistics")
print("\nOr use the CLI directly:")
print("  python3 scripts/search-logs.py --event-type agent_execution")
print("  python3 scripts/search-logs.py --level error")
print("  python3 scripts/search-logs.py --query \"demo\" --format json")
