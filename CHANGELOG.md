# Changelog

All notable changes to the ProCode Agent Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - External Agents System (2026-01-28)

#### Core Infrastructure
- **External Agents Architecture**: Plug-and-play system for integrating specialized external agents via A2A protocol
- **Agent Discovery**: Registry-based discovery system in [`config/external_agents.json`](config/external_agents.json)
- **Intent Routing**: Automatic routing of "insurance" and "weather" intents to external agents
- **Shared Infrastructure**: Base classes, configuration loader, and 15+ utility functions in [`external_agents/shared/`](external_agents/shared/)

#### Weather Agent (Port 9996)
- **OpenWeatherMap Integration**: Real-time weather data with 5-minute caching
- **Simple Pattern**: Principal-only architecture without separate task agents
- **Location Extraction**: Intelligent location parsing from natural language queries
- **Fallback Support**: Mock data when API key not provided
- **API Key**: Configured via `OPENWEATHER_API_KEY` environment variable

#### Insurance Agent (Port 9997)
- **Complex Pattern**: Principal + 2 Task Agents (Info, Creation)
- **Task Routing**: Intelligent delegation to specialized task agents
- **Policy Management**: Query policy information and create new policies
- **Demo Data**: Mock policy database for testing

#### ProCode Integration
- **Intent Classification**: Added "insurance" and "weather" to intent classifier ([`core/intent_classifier.py`](core/intent_classifier.py))
- **Agent Router**: New `_route_to_external_agent()` method in [`core/agent_router.py`](core/agent_router.py)
- **Capabilities Update**: External agents marked with "EXT:" prefix in general agent capabilities
- **Out-of-Scope Removal**: Weather queries no longer redirected to ChatGPT

#### Documentation
- [`external_agents/README.md`](external_agents/README.md) - Overview and quick start
- [`external_agents/ARCHITECTURE.md`](external_agents/ARCHITECTURE.md) - System architecture and patterns
- [`external_agents/DEMO_ARCHITECTURE.md`](external_agents/DEMO_ARCHITECTURE.md) - Demo agents specification
- [`external_agents/DEVELOPMENT_GUIDE.md`](external_agents/DEVELOPMENT_GUIDE.md) - Development guidelines
- [`external_agents/IMPLEMENTATION_PLAN.md`](external_agents/IMPLEMENTATION_PLAN.md) - Implementation phases
- [`external_agents/QUICKSTART.md`](external_agents/QUICKSTART.md) - Quick start guide
- [`external_agents/ROUTING_INTEGRATION.md`](external_agents/ROUTING_INTEGRATION.md) - ProCode integration details

### Fixed - External Agents System (2026-01-28)

#### Critical Bug Fixes
- **RequestContext Error**: Fixed `ExecutionContext` → `RequestContext` in [`a2a_comm/agent_client.py:181`](a2a_comm/agent_client.py)
- **Model Dump Error**: Removed invalid `model_dump()` call in [`a2a_comm/agent_client.py:102`](a2a_comm/agent_client.py)
- **Docker Networking**: Changed URLs from `localhost` to `host.docker.internal` in [`config/external_agents.json`](config/external_agents.json)
- **Location Extraction**: Fixed text corruption using regex with word boundaries in [`external_agents/weather_agent/principal.py:106`](external_agents/weather_agent/principal.py)
  - Before: "weather today" → "Wear Today" ❌
  - After: "weather today" → "today" ✅
- **A2A SDK Imports**: Updated [`external_agents/insurance_agent/__main__.py`](external_agents/insurance_agent/__main__.py) to use correct imports:
  - `A2AStarletteApplication` instead of deprecated `A2AServer`
  - Proper `AgentCard` with all required fields (capabilities, skills, version, etc.)

#### Configuration Updates
- **Development Mode**: Use `localhost` instead of `agent` hostname for browser testing
- **Frontend Build**: Configured `BACKEND_URL=http://localhost:9998` for development

### Changed - External Agents System (2026-01-28)

#### User Experience
- **Capabilities List**: Added external agents to general agent capabilities with "EXT:" prefix
- **Scope Management**: Removed weather/temperature/forecast from out-of-scope keywords

#### Technical Improvements
- **Error Handling**: Better error messages for external agent communication failures
- **Logging**: Comprehensive logging in all external agent components
- **Caching**: 5-minute TTL cache for weather data to reduce API calls

## [0.11.0] - 2026-01-27

### Added - API Key Authentication (Step 11)
- Enterprise-grade API key management system
- Organization-based multi-tenancy support
- Cryptographically secure key generation (SHA-256 hashing)
- Scope-based authorization (read, write, admin, billing)
- Per-key rate limiting and usage tracking
- Admin API endpoints for key management
- Optional (disabled by default for backward compatibility)

### Documentation
- [`docs/STEP11_API_KEY_AUTH_DESIGN.md`](docs/STEP11_API_KEY_AUTH_DESIGN.md)
- [`docs/STEP11_API_KEY_IMPLEMENTATION.md`](docs/STEP11_API_KEY_IMPLEMENTATION.md)
- [`docs/STEP11_API_KEY_SUMMARY.md`](docs/STEP11_API_KEY_SUMMARY.md)

## [0.10.0] - 2026-01-26

### Added - Database Integration (Step 10)
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations for schema management
- Repository pattern for data access
- Conversation and message persistence
- Audit logging to database
- Usage tracking and analytics

### Documentation
- [`docs/DATABASE_INTEGRATION.md`](docs/DATABASE_INTEGRATION.md)
- [`docs/POSTGRESQL_SETUP.md`](docs/POSTGRESQL_SETUP.md)
- [`docs/POSTGRESQL_MIGRATION_COMPLETE.md`](docs/POSTGRESQL_MIGRATION_COMPLETE.md)

## [0.9.0] - 2026-01-25

### Added - API Security (Step 12)
- Rate limiting (10 req/min, 100/hr, 1000/day per IP)
- CORS restriction to specific domains
- PII detection and redaction
- Comprehensive audit logging
- Circuit breaker pattern for failure recovery

### Documentation
- [`docs/API_SECURITY.md`](docs/API_SECURITY.md)
- [`docs/SECURITY_IMPLEMENTATION.md`](docs/SECURITY_IMPLEMENTATION.md)

## [0.8.0] - 2026-01-24

### Added - Multi-LLM Strategy
- Cost-optimized model routing
- Support for Anthropic Claude, OpenAI GPT, Google Gemini
- Complexity analysis for model selection
- 98% cost reduction compared to baseline

### Documentation
- [`docs/MULTI_LLM_STRATEGY.md`](docs/MULTI_LLM_STRATEGY.md)
- [`docs/COST_OPTIMIZATION_SUMMARY.md`](docs/COST_OPTIMIZATION_SUMMARY.md)

## [0.7.0] - 2026-01-23

### Added - Docker Deployment
- Multi-stage Docker builds
- Docker Compose orchestration
- PostgreSQL containerization
- Next.js frontend containerization
- Production-ready configuration

### Documentation
- [`docs/DOCKER_DEPLOYMENT.md`](docs/DOCKER_DEPLOYMENT.md)

## [0.6.0] - 2026-01-22

### Added - A2A Communication
- Agent-to-Agent protocol implementation
- JSON-RPC 2.0 support
- Streaming responses via SSE
- Multi-agent coordination

### Documentation
- [`docs/A2A_COMMUNICATION.md`](docs/A2A_COMMUNICATION.md)

## [0.5.0] - 2026-01-21

### Added - Core Features
- Intent classification with LLM and deterministic fallback
- Conversation memory with context awareness
- Task-specific agents (Tickets, Account, Payments)
- GitHub API integration
- Interactive console app
- Streamlit web interface
- Next.js frontend

### Documentation
- [`docs/CONSOLE_APP.md`](docs/CONSOLE_APP.md)
- [`docs/STRUCTURE.md`](docs/STRUCTURE.md)
- [`docs/IMPLEMENTATION_GUIDE.md`](docs/IMPLEMENTATION_GUIDE.md)

## [0.1.0] - 2026-01-20

### Added - Initial Release
- Basic agent framework
- A2A SDK integration
- Simple intent routing
- Mock tools for testing

---

## Testing Status

### External Agents (2026-01-28)
- ✅ Weather Agent: Successfully tested with OpenWeatherMap API
- ✅ Insurance Agent: Successfully tested with policy queries
- ✅ ProCode Integration: Intent routing working correctly
- ✅ Docker Networking: host.docker.internal configuration verified
- ✅ Location Extraction: Regex-based parsing working correctly
- ✅ Browser Testing: Frontend successfully communicating with backend

### Known Issues
- None currently

### Future Enhancements
- Add more external agents (e.g., translation, analytics)
- Implement agent health monitoring
- Add agent versioning and compatibility checks
- Create agent marketplace/registry
- Add agent authentication and authorization
- Implement agent-to-agent streaming

---

**For detailed development history, see [`docs/DEVELOPMENT_HISTORY.md`](docs/DEVELOPMENT_HISTORY.md)**
