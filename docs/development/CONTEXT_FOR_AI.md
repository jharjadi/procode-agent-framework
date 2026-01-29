# Context for AI Assistant - Procode Agent Framework

## Quick Reference for AI Assistants

When helping with this project, read this file first to understand the current state and context.

## Project Status Summary

### ✅ Completed Features
1. **Core Agent System** - Principal agent router with task delegation
2. **LLM Intent Classification** - Multi-provider support (Anthropic, OpenAI, Google) with deterministic fallback
3. **Real Tool Integration** - GitHub Issues API with mocked fallback
4. **Conversation Memory** - Multi-turn dialogues with context awareness
5. **Streaming Responses** - Server-Sent Events (SSE) for real-time feedback
6. **Agent-to-Agent Communication** - Full A2A protocol support with discovery, client, and orchestrator
7. **Interactive Console App** - Beautiful CLI with rich UI for easy testing
8. **Folder Organization** - Clean structure with 9 logical directories
9. **Comprehensive Tests** - Unit tests, integration tests, and demos

### 🚧 Partially Complete
1. **Enhanced Guardrails (Step 9)** - Security modules created but NOT integrated into agent_router
   - Files exist: `security/enhanced_guardrails.py`, `security/rate_limiter.py`, etc.
   - TODO: Integrate into request/response pipeline

### ❌ Not Started
1. **Observability (Step 10)** - Placeholder files only
   - TODO: Implement `observability/metrics.py`
   - TODO: Implement `observability/health.py`
   - TODO: Add `/metrics` and `/health` endpoints

## Critical Information

### Import Structure
- **Package root**: All imports are relative to `procode_framework/`
- **Example**: `from core.agent_router import ProcodeAgentRouter`
- **Important**: `a2a_comm/` (NOT `a2a/`) - renamed to avoid SDK conflict

### Key Files to Understand
1. **`__main__.py`** - Entry point, Starlette app with custom `/stream` endpoint
2. **`core/agent_router.py`** - Main routing logic, LLM classification, A2A delegation
3. **`console_app.py`** - Interactive console for testing
4. **`pyproject.toml`** - All dependencies

### Known Issues
1. **Console App Health Check** - Shows false warning about agent not running
   - **Cause**: No `/health` endpoint exists
   - **Solution**: User types "y" to continue, works perfectly
   - **Fix Needed**: Update health check to use JSON-RPC ping

2. **Starlette vs FastAPI** - A2A SDK uses Starlette, not FastAPI
   - **Impact**: Custom endpoints must use Starlette routing
   - **Example**: See `/stream` endpoint in `__main__.py`

3. **Step 9 Integration** - Security modules exist but not integrated
   - **Files**: `security/*.py`
   - **TODO**: Add to `agent_router.py` pipeline

## Architecture Overview

```
User Request
    ↓
agent_router.py (ProcodeAgentRouter)
    ↓
intent_classifier.py (LLM or deterministic)
    ↓
Task Agent (tickets/account/payments)
    ↓
tools.py (mocked or real GitHub API)
    ↓
Response (with conversation memory)
```

### A2A Communication Flow
```
User → agent_router → _should_delegate?
    ↓ Yes
agent_discovery → find agent
    ↓
agent_client → send message
    ↓
Remote Agent → response
```

### Streaming Flow
```
User → /stream endpoint
    ↓
agent_router.execute_streaming()
    ↓
Yields progress messages
    ↓
SSE stream to client
```

## Environment Variables

```bash
# LLM (optional - falls back to deterministic)
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
USE_LLM_INTENT=true

# Tools (optional - uses mocked by default)
USE_REAL_TOOLS=false
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo

# Testing
RUN_INTEGRATION_TESTS=false

# Console
AGENT_URL=http://localhost:9998
```

## Common Tasks

### Adding a New Task Agent
1. Create `tasks/task_newfeature.py`
2. Add to `agent_router.py` imports
3. Add intent to `intent_classifier.py`
4. Add skill to `__main__.py` agent card
5. Add tests to `tests/tests.py`

### Adding a New Security Module
1. Create `security/new_module.py`
2. Import in `agent_router.py`
3. Add to request/response pipeline
4. Add tests

### Adding a New A2A Agent
1. Register in `config/agents_config.json`
2. Or use `agent_registry.register_agent()`
3. Test with `agent_client.delegate_task()`

## Testing Commands

```bash
# Quick test
python test_console.py

# Full test suite
python tests/tests.py

# Specific tests
python tests/test_llm.py
python tests/test_streaming.py
python tests/test_agent_communication.py

# Demo
python demo_console.py

# Interactive
python console_app.py
```

## File Locations

### Core Logic
- `core/agent_router.py` - Main router (338 lines)
- `core/intent_classifier.py` - LLM classification (200+ lines)
- `core/conversation_memory.py` - Memory management (150+ lines)

### Task Handlers
- `tasks/task_tickets.py` - Ticket operations with GitHub API
- `tasks/task_account.py` - Account operations (mocked)
- `tasks/task_payments.py` - Payment operations (stubbed)
- `tasks/tools.py` - Tool implementations (300+ lines)

### A2A Communication
- `a2a_comm/agent_discovery.py` - Registry (200+ lines)
- `a2a_comm/agent_client.py` - Client (350+ lines)
- `a2a_comm/agent_orchestrator.py` - Orchestrator (450+ lines)

### Security (NOT INTEGRATED)
- `security/guardrails.py` - Basic validation
- `security/enhanced_guardrails.py` - PII, injection detection
- `security/rate_limiter.py` - Rate limiting
- `security/circuit_breaker.py` - Circuit breaker
- `security/audit_logger.py` - Audit logging
- `security/compliance.py` - GDPR compliance

### Streaming
- `streaming/streaming_handler.py` - SSE implementation

### Tests
- `tests/tests.py` - Main suite (486 lines)
- `tests/test_llm.py` - LLM tests (126 lines)
- `tests/test_streaming.py` - Streaming tests (299 lines)
- `tests/test_agent_communication.py` - A2A tests (468 lines)

## Dependencies

Key packages:
- `a2a-sdk>=0.3.0` - A2A protocol
- `fastapi>=0.115.0` - Web framework
- `starlette>=0.46.2` - ASGI (used by A2A SDK)
- `uvicorn>=0.34.2` - Server
- `httpx>=0.28.1` - HTTP client
- `rich>=13.7.0` - Console UI
- `langchain-*` - LLM providers

## Next Steps (Priority Order)

1. **Fix Console Health Check** (Quick win)
   - Update `console_app.py` health_check() to use JSON-RPC
   - Remove false warning

2. **Integrate Step 9 Security** (Important)
   - Add enhanced_guardrails to agent_router pipeline
   - Test PII detection and injection prevention
   - Configure rate limiting

3. **Implement Step 10 Observability** (Important)
   - Create metrics.py with Prometheus metrics
   - Create health.py with proper health checks
   - Add /metrics and /health endpoints

4. **Documentation** (Ongoing)
   - Update README for standalone repo
   - Add API documentation
   - Add architecture diagrams

5. **Production Readiness** (Future)
   - Docker containerization
   - CI/CD pipeline
   - Monitoring and alerting

## Questions to Ask User

When starting work in the new repo, ask:
1. "What feature would you like to work on?"
2. "Should I continue with Step 9 (security) or Step 10 (observability)?"
3. "Do you want to fix the console health check first?"
4. "Any specific issues or improvements needed?"

## Important Notes

- **Always check this file first** when helping with the project
- **Read DEVELOPMENT_HISTORY.md** for detailed context
- **Check STRUCTURE.md** for current file organization
- **Test changes** with `python test_console.py` before committing
- **Update documentation** when adding features

## Contact Points

- Main entry: `__main__.py`
- Core logic: `core/agent_router.py`
- Testing: `test_console.py` or `demo_console.py`
- Documentation: `docs/` directory
