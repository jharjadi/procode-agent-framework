# Procode Agent Framework - Development History & Context

## Project Overview

The Procode Agent Framework is a production-ready, multi-agent system built on the A2A (Agent-to-Agent) protocol. It demonstrates advanced agent capabilities including streaming responses, LLM-based intent classification, conversation memory, and agent-to-agent communication.

## Development Timeline

### Phase 1: Foundation (Steps 1-3)
- **Step 1-2**: Basic agent structure with A2A protocol
- **Step 3**: Principal agent router with task delegation
  - Created `agent_router.py` - main routing logic
  - Created task agents: `task_tickets.py`, `task_account.py`, `task_payments.py`
  - Implemented basic guardrails for input/output validation

### Phase 2: Intelligence (Steps 4-6)
- **Step 4**: LLM-based intent classification
  - Added `intent_classifier.py` with multi-provider support (Anthropic, OpenAI, Google)
  - Implemented deterministic fallback for when no API key is available
  - Natural language understanding for conversational inputs

- **Step 5**: Real tool integration
  - Created `tools.py` with GitHub Issues API integration
  - Hybrid approach: mocked tools for testing, real tools for production
  - Retry logic and error handling

- **Step 6**: Conversation memory
  - Added `conversation_memory.py` for multi-turn dialogues
  - Context window management (configurable message limit)
  - Automatic cleanup of old conversations

### Phase 3: Advanced Features (Steps 7-8)
- **Step 7**: Streaming responses
  - Created `streaming_handler.py` for Server-Sent Events (SSE)
  - Real-time progress indicators
  - Token-by-token streaming for better UX
  - Added `/stream` endpoint to `__main__.py`

- **Step 8**: Agent-to-Agent communication
  - Created `agent_discovery.py` - agent registry and discovery
  - Created `agent_client.py` - A2A protocol client
  - Created `agent_orchestrator.py` - multi-agent workflow orchestration
  - Delegation logic in `agent_router.py`

### Phase 4: Security & Organization (Step 9 + Reorganization)
- **Step 9**: Enhanced guardrails (partially implemented)
  - Created 5 security modules:
    - `rate_limiter.py` - Rate limiting for abuse prevention
    - `audit_logger.py` - Security audit logging
    - `circuit_breaker.py` - Circuit breaker pattern
    - `compliance.py` - GDPR and compliance features
    - `enhanced_guardrails.py` - PII detection, injection prevention
  - **Status**: Core modules created, integration pending

- **Folder Reorganization**: 
  - Reorganized 26 files into 9 logical directories
  - Fixed all import statements across the codebase
  - Renamed `a2a/` → `a2a_comm/` to avoid SDK package conflict
  - Created `docs/STRUCTURE.md` documenting the organization

### Phase 5: Developer Experience
- **Interactive Console App**:
  - Created `console_app.py` - beautiful CLI with rich UI
  - Created `demo_console.py` - non-interactive demo
  - Created `test_console.py` - quick test script
  - Created `docs/CONSOLE_APP.md` - complete documentation
  - Features: interactive chat, history tracking, health monitoring, built-in commands

## Current Project Structure

```
procode_framework/
├── __init__.py                    # Package initialization
├── __main__.py                    # Main entry point (Starlette app with /stream endpoint)
├── console_app.py                 # Interactive console (NEW)
├── demo_console.py                # Console demo (NEW)
├── test_console.py                # Quick test (NEW)
├── pyproject.toml                 # Dependencies
│
├── core/                          # Core agent functionality
│   ├── agent_router.py           # Main routing logic with A2A delegation
│   ├── intent_classifier.py      # LLM/deterministic intent classification
│   └── conversation_memory.py    # Multi-turn conversation support
│
├── tasks/                         # Task-specific handlers
│   ├── task_account.py           # Account management (mocked)
│   ├── task_payments.py          # Payment processing (stubbed/refused)
│   ├── task_tickets.py           # Ticket management with GitHub API
│   └── tools.py                  # Hybrid tools (mocked/real)
│
├── a2a_comm/                     # Agent-to-Agent communication
│   ├── agent_discovery.py        # Agent registry and discovery
│   ├── agent_client.py           # A2A protocol client
│   ├── agent_orchestrator.py     # Multi-agent workflow orchestration
│   └── test_mock_agent.py        # Mock agent for testing
│
├── security/                      # Security and guardrails
│   ├── guardrails.py             # Basic input/output validation
│   ├── enhanced_guardrails.py    # PII detection, injection prevention
│   ├── rate_limiter.py           # Rate limiting
│   ├── circuit_breaker.py        # Circuit breaker pattern
│   ├── audit_logger.py           # Security audit logging
│   └── compliance.py             # GDPR compliance
│
├── streaming/                     # Streaming responses
│   └── streaming_handler.py      # SSE streaming support
│
├── observability/                 # Monitoring (placeholder)
│   ├── metrics.py                # Metrics collection (TODO)
│   └── health.py                 # Health checks (TODO)
│
├── config/                        # Configuration
│   └── agents_config.json        # Agent registry configuration
│
├── tests/                         # Test suite
│   ├── tests.py                  # Main test suite
│   ├── test_llm.py               # LLM integration tests
│   ├── test_streaming.py         # Streaming tests
│   └── test_agent_communication.py  # A2A communication tests
│
└── docs/                          # Documentation
    ├── STRUCTURE.md              # Project structure documentation
    ├── CONSOLE_APP.md            # Console app documentation
    ├── A2A_COMMUNICATION.md      # A2A feature documentation
    └── DEVELOPMENT_HISTORY.md    # This file
```

## Key Technical Decisions

### 1. Folder Organization
- **Why**: Original flat structure with 26 files was becoming unmanageable
- **Solution**: Organized into 9 logical directories (core, tasks, a2a_comm, security, streaming, observability, config, tests, docs)
- **Challenge**: Had to fix all imports across 8+ files
- **Lesson**: Renamed `a2a/` to `a2a_comm/` to avoid conflict with installed A2A SDK package

### 2. Multi-Provider LLM Support
- **Why**: Different users have different API keys
- **Solution**: Auto-detect and use first available provider (Anthropic → OpenAI → Google)
- **Fallback**: Deterministic keyword matching when no API key available
- **Configuration**: `USE_LLM_INTENT` environment variable to control behavior

### 3. Hybrid Tools Approach
- **Why**: Need both safe testing and real production capabilities
- **Solution**: Tools support both mocked and real modes
- **Configuration**: `USE_REAL_TOOLS` environment variable
- **Example**: GitHub Issues API with mocked fallback

### 4. Streaming Architecture
- **Why**: Better UX for long-running operations
- **Solution**: Server-Sent Events (SSE) with progress indicators
- **Implementation**: Custom `/stream` endpoint added to Starlette app
- **Challenge**: Had to use Starlette routing (not FastAPI decorators) since A2A SDK uses Starlette

### 5. Console App Design
- **Why**: curl commands are tedious for testing
- **Solution**: Interactive CLI with rich UI library
- **Features**: Chat interface, history tracking, health monitoring, built-in commands
- **Note**: Health check shows false warning (no /health endpoint) but works fine when you continue

## Known Issues & Limitations

### 1. Health Check Warning
- **Issue**: Console app shows warning "Agent doesn't appear to be running"
- **Cause**: Checking for `/health` endpoint that doesn't exist
- **Workaround**: Type "y" to continue - agent works perfectly
- **Fix**: Could update health check to use JSON-RPC ping instead

### 2. Step 9 Integration Pending
- **Status**: Security modules created but not integrated into agent_router
- **TODO**: Add enhanced guardrails to the request/response pipeline
- **Files**: `security/enhanced_guardrails.py`, `security/rate_limiter.py`, etc.

### 3. Step 10 Not Started
- **Status**: Observability modules are placeholders
- **TODO**: Implement `observability/metrics.py` and `observability/health.py`
- **TODO**: Add monitoring endpoints to `__main__.py`

## Environment Variables

```bash
# LLM Configuration
ANTHROPIC_API_KEY=your-key          # For Claude
OPENAI_API_KEY=your-key             # For GPT
GOOGLE_API_KEY=your-key             # For Gemini
LLM_PROVIDER=anthropic              # Force specific provider
USE_LLM_INTENT=true                 # Enable/disable LLM classification

# Tool Configuration
USE_REAL_TOOLS=false                # Enable real GitHub API
GITHUB_TOKEN=your-token             # GitHub personal access token
GITHUB_REPO=owner/repo              # GitHub repository

# Testing
RUN_INTEGRATION_TESTS=false         # Enable integration tests

# Conversation Memory
CONVERSATION_WINDOW_SIZE=10         # Max messages to keep

# Agent URL (for console app)
AGENT_URL=http://localhost:9998     # Agent server URL
```

## Dependencies

Key dependencies (see `pyproject.toml` for full list):
- `a2a-sdk>=0.3.0` - A2A protocol implementation
- `fastapi>=0.115.0` - Web framework (for /stream endpoint)
- `starlette>=0.46.2` - ASGI framework (used by A2A SDK)
- `uvicorn>=0.34.2` - ASGI server
- `httpx>=0.28.1` - HTTP client for A2A communication
- `rich>=13.7.0` - Beautiful terminal UI (for console app)
- `langchain-anthropic>=0.3.0` - Claude integration
- `langchain-openai>=0.3.0` - GPT integration
- `langchain-google-genai>=2.1.4` - Gemini integration
- `sse-starlette>=2.3.5` - Server-Sent Events support

## Testing

### Unit Tests
```bash
python tests/tests.py              # Main test suite
python tests/test_llm.py           # LLM tests (requires API key)
python tests/test_streaming.py     # Streaming tests
python tests/test_agent_communication.py  # A2A tests
```

### Integration Tests
```bash
export RUN_INTEGRATION_TESTS=true
export GITHUB_TOKEN=your-token
export GITHUB_REPO=owner/repo
python tests/tests.py
```

### Quick Tests
```bash
python test_console.py             # Quick agent test
python demo_console.py             # Console demo
```

## Running the Agent

### Start Agent Server
```bash
cd procode_framework
source venv/bin/activate
python __main__.py
```

### Use Interactive Console
```bash
python console_app.py
```

### Use curl
```bash
curl -X POST http://localhost:9998/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"kind":"text","text":"create ticket"}],"messageId":"test"}},"id":1}'
```

### Phase 6: Cost Optimization (Multi-LLM Strategy)
- **Multi-LLM Classifier**:
  - Created `core/multi_llm_classifier.py` - intelligent model selection
  - 98% cost savings by routing simple queries to cheaper models
  - Complexity analysis: greeting/simple → Gemini Flash, complex → GPT-4
  - Created `docs/MULTI_LLM_STRATEGY.md` - complete strategy documentation
  - Created `docs/COST_OPTIMIZATION_SUMMARY.md` - cost analysis
  - Created `test_multi_llm.py` - comprehensive testing

### Phase 7: User Experience Enhancement
- **Streamlit Web UI**:
  - Created `streamlit_app.py` - simple, working web interface
  - Real-time streaming responses
  - Cost tracking per message
  - Conversation history display
  - Alternative to Next.js frontend (simpler, faster to deploy)

- **Next.js Frontend**:
  - Created `frontend/` directory with Next.js + TypeScript
  - CopilotKit integration for AI chat
  - Cost metrics dashboard
  - Agent status monitoring
  - Modern, production-ready UI

### Phase 8: Database Integration & Persistence (Step 10) ✅

**Completed**: January 25, 2026

Implemented comprehensive database layer for long-term data persistence:

#### Database Infrastructure
- **Dual Database Support**:
  - SQLite for development (file-based, zero config)
  - PostgreSQL for production (scalable, connection pooling)
  - Automatic detection from `DATABASE_URL`

- **SQLAlchemy Models** ([`database/models.py`](../database/models.py)):
  - `User`: Authentication and user management (ready for Step 11)
  - `Conversation`: Track conversation sessions with intent and status
  - `Message`: Store individual messages with cost tracking
  - `AuditLog`: Compliance and security audit trail
  - Strategic indexes for query optimization

- **Repository Pattern** ([`database/repositories/`](../database/repositories/)):
  - `ConversationRepository`: CRUD operations for conversations and messages
  - `AuditRepository`: Audit log creation and querying
  - `UserRepository`: User management (placeholder for Step 11)
  - `MessageRepository`: Message retrieval operations
  - Clean abstraction layer for data access

- **Database Migrations**:
  - Alembic integration for schema management
  - Initial migration with all tables and indexes
  - Auto-generation from model changes
  - Version control for database schema

#### Integration with Existing Components

- **ConversationMemory Enhancement** ([`core/conversation_memory.py`](../core/conversation_memory.py)):
  - Optional database persistence via `USE_DATABASE` env var
  - In-memory caching for fast access
  - Database fallback for loading history
  - Automatic conversation creation
  - Cost tracking per message
  - Backward compatible (works without database)

- **AuditLogger Enhancement** ([`security/audit_logger.py`](../security/audit_logger.py)):
  - Dual logging: JSON files + database
  - Automatic event categorization (security, compliance, access, system)
  - User ID conversion for database compatibility
  - Graceful fallback if database unavailable
  - Maintains existing file-based logging

#### Configuration & Testing

- **Environment Variables** (added to [`.env.example`](./.env.example)):
  ```bash
  DATABASE_URL=sqlite:///data/procode.db  # or PostgreSQL URL
  USE_DATABASE=false  # Enable database persistence
  DB_POOL_SIZE=5      # PostgreSQL connection pool
  DB_MAX_OVERFLOW=10  # Burst capacity
  SQL_ECHO=false      # SQL query logging
  ```

- **Testing**:
  - Created `test_database.py` - comprehensive integration tests
  - Verifies database initialization, table creation, CRUD operations
  - Tests repository layer functionality
  - All tests passing ✅

#### Documentation

- **Created** [`docs/DATABASE_INTEGRATION.md`](../docs/DATABASE_INTEGRATION.md):
  - Complete setup and configuration guide
  - Repository pattern usage examples
  - Migration management with Alembic
  - Production deployment guide (PostgreSQL)
  - Performance considerations and optimization
  - Troubleshooting common issues

#### Files Created/Modified

**New Files**:
- `database/__init__.py` - Package exports
- `database/connection.py` - Database connection management
- `database/models.py` - SQLAlchemy models
- `database/repositories/__init__.py`
- `database/repositories/conversation_repository.py`
- `database/repositories/user_repository.py`
- `database/repositories/message_repository.py`
- `database/repositories/audit_repository.py`
- `alembic/` - Migration framework
- `alembic.ini` - Alembic configuration
- `alembic/versions/5c6758e838d3_initial_migration.py`
- `test_database.py` - Integration tests
- `docs/DATABASE_INTEGRATION.md` - Complete documentation

**Modified Files**:
- `pyproject.toml` - Added SQLAlchemy, Alembic, psycopg2-binary
- `.env.example` - Added database configuration
- `core/conversation_memory.py` - Added database persistence
- `security/audit_logger.py` - Added database persistence

#### Key Features

✅ **Dual Database Support**: SQLite (dev) + PostgreSQL (prod)
✅ **Repository Pattern**: Clean data access layer
✅ **Migration System**: Alembic for schema management
✅ **Backward Compatible**: Works with or without database
✅ **Performance Optimized**: Strategic indexes, connection pooling
✅ **Production Ready**: PostgreSQL support with pooling
✅ **Comprehensive Testing**: Full integration test suite
✅ **Complete Documentation**: Setup, usage, and troubleshooting

#### Next: Step 11 - Authentication & Authorization

The database foundation is now ready for:
- User registration and login
- Password hashing (bcrypt)
- API key generation
- Role-based access control (RBAC)
- Session management

## Next Steps (Roadmap)

### Immediate (Step 11)
1. **Authentication & Authorization**
   - User registration and login endpoints
   - Password hashing with bcrypt
   - JWT token generation and validation
   - API key authentication
   - Role-based access control (RBAC)
   - Session management

### Future Enhancements (Steps 12-25)
See [`docs/PRODUCTION_ROADMAP.md`](../docs/PRODUCTION_ROADMAP.md) for complete roadmap.

1. **Persistent Storage** ✅ (Step 10 - Completed)
   - Database for conversation history ✅
   - Agent registry persistence (pending)

2. **Advanced A2A Features**
   - Agent discovery via broadcast
   - Load balancing across agents
   - Fault tolerance and retries

3. **UI Improvements**
   - Web-based console (FastAPI + React)
   - Real-time streaming in web UI
   - Conversation visualization

4. **Production Features**
   - Docker containerization
   - Kubernetes deployment
   - CI/CD pipeline
   - Monitoring and alerting

## Important Notes for Future Development

1. **Import Paths**: Always use relative imports from package root (e.g., `from core.agent_router import ...`)

2. **A2A SDK Compatibility**: The A2A SDK uses Starlette, not FastAPI. Use Starlette routing for custom endpoints.

3. **Package Naming**: The local `a2a_comm/` folder was renamed from `a2a/` to avoid shadowing the installed `a2a` SDK package.

4. **Testing**: Always test with both mocked and real tools. Set `USE_REAL_TOOLS=false` for safe testing.

5. **LLM Fallback**: The agent works without any API keys using deterministic matching. This is intentional for accessibility.

6. **Console App**: The health check warning is cosmetic - the app works fine when you continue.

## Contact & Contribution

When working on this project in a new repo, refer to this document for context. Key files to understand:
- `core/agent_router.py` - Main routing logic
- `__main__.py` - Entry point and server setup
- `docs/STRUCTURE.md` - Current project organization
- `docs/CONSOLE_APP.md` - Console app usage

For questions about specific features, check the corresponding spec files in `.roo/specs/` (if copied from original repo).
