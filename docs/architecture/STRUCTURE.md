# Procode Framework - Project Structure

This document describes the organized structure of the procode framework.

## Directory Structure

```
procode_framework/
├── __init__.py                    # Package initialization
├── __main__.py                    # Main entry point
├── pyproject.toml                 # Project configuration
├── README.md                      # Project documentation
│
├── core/                          # Core agent functionality
│   ├── __init__.py
│   ├── agent_router.py           # Main routing logic
│   ├── intent_classifier.py      # Intent classification (LLM/deterministic)
│   └── conversation_memory.py    # Conversation history management
│
├── tasks/                         # Task-specific handlers
│   ├── __init__.py
│   ├── task_account.py           # Account management tasks
│   ├── task_payments.py          # Payment processing tasks
│   ├── task_tickets.py           # Ticket management tasks
│   └── tools.py                  # Shared tool implementations
│
├── a2a_comm/                     # Agent-to-Agent communication (renamed to avoid SDK conflict)
│   ├── __init__.py
│   ├── agent_discovery.py        # Agent registry and discovery
│   ├── agent_client.py           # A2A protocol client
│   ├── agent_orchestrator.py     # Multi-agent workflow orchestration
│   └── test_mock_agent.py        # Mock agent for testing
│
├── security/                      # Security and guardrails
│   ├── __init__.py
│   ├── guardrails.py             # Basic input/output validation
│   ├── enhanced_guardrails.py    # Advanced security checks
│   ├── rate_limiter.py           # Rate limiting (abuse prevention)
│   ├── circuit_breaker.py        # Circuit breaker pattern
│   ├── audit_logger.py           # Security audit logging
│   └── compliance.py             # GDPR and compliance features
│
├── streaming/                     # Streaming responses
│   ├── __init__.py
│   └── streaming_handler.py      # Real-time streaming support
│
├── observability/                 # Monitoring and observability
│   ├── __init__.py
│   ├── metrics.py                # Metrics collection (future)
│   ├── health.py                 # Health checks (future)
│   └── tracing.py                # Distributed tracing (future)
│
├── config/                        # Configuration files
│   ├── __init__.py
│   └── agents_config.json        # Agent registry configuration
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_streaming.py         # Streaming tests
│   ├── test_agent_communication.py  # A2A communication tests
│   ├── test_llm.py               # LLM integration tests
│   └── tests.py                  # General tests
│
└── docs/                          # Documentation
    ├── A2A_COMMUNICATION.md      # A2A feature documentation
    └── STRUCTURE.md              # This file
```

## Module Organization

### Core (`core/`)
Contains the fundamental agent logic:
- **agent_router.py**: Routes requests to appropriate task handlers
- **intent_classifier.py**: Classifies user intent using LLM or patterns
- **conversation_memory.py**: Manages conversation history and context

### Tasks (`tasks/`)
Task-specific implementations:
- **task_*.py**: Individual task handlers (account, payments, tickets)
- **tools.py**: Shared utilities and tool implementations

### A2A (`a2a/`)
Agent-to-Agent communication:
- **agent_discovery.py**: Service discovery and agent registry
- **agent_client.py**: Client for communicating with other agents
- **agent_orchestrator.py**: Workflow coordination across agents
- **test_mock_agent.py**: Mock agent server for testing

### Security (`security/`)
Security and compliance features:
- **guardrails.py**: Basic validation
- **enhanced_guardrails.py**: Advanced security (PII detection, injection prevention)
- **rate_limiter.py**: Request rate limiting
- **circuit_breaker.py**: Failure protection
- **audit_logger.py**: Security event logging
- **compliance.py**: GDPR and data compliance

### Streaming (`streaming/`)
Real-time response streaming:
- **streaming_handler.py**: Token-by-token streaming and progress tracking

### Observability (`observability/`)
Monitoring and observability (future):
- **metrics.py**: Metrics collection
- **health.py**: Health check system
- **tracing.py**: Distributed tracing

## Import Examples

### Old (Flat Structure)
```python
from agent_router import ProcodeAgentRouter
from intent_classifier import IntentClassifier
from rate_limiter import RateLimiter
```

### New (Organized Structure)
```python
from core.agent_router import ProcodeAgentRouter
from core.intent_classifier import IntentClassifier
from security.rate_limiter import RateLimiter
```

### Using Package Imports
```python
# After updating __init__.py files
from procode_framework.core import ProcodeAgentRouter, IntentClassifier
from procode_framework.security import RateLimiter, EnhancedGuardrails
from procode_framework.a2a import AgentRegistry, AgentClient
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each directory has a specific purpose
2. **Easier Navigation**: Find files by category, not alphabetically
3. **Better Scalability**: Easy to add new modules in appropriate folders
4. **Cleaner Imports**: Imports reflect the module's purpose
5. **Testing Organization**: All tests in one place
6. **Documentation**: Separate docs folder for guides
7. **Professional Structure**: Follows Python best practices

## Migration Notes

### Files Moved
- Core files → `core/`
- Task handlers → `tasks/`
- A2A modules → `a2a/`
- Security modules → `security/`
- Streaming → `streaming/`
- Tests → `tests/`
- Config → `config/`
- Docs → `docs/`

### Import Updates Required
After reorganization, imports in the following files need updating:
- `__main__.py` - Update all imports to use new paths
- `core/agent_router.py` - Update task and security imports
- `tests/*.py` - Update all test imports
- Any other files that import from moved modules

### Next Steps
1. Update imports in all affected files
2. Update `__init__.py` files to expose public APIs
3. Run tests to verify everything works
4. Update documentation with new import paths

## Future Additions

As the framework grows, consider adding:
- `middleware/` - Request/response middleware
- `plugins/` - Plugin system for extensions
- `utils/` - Shared utilities
- `models/` - Data models and schemas
- `api/` - API-specific code (if separated from __main__.py)
