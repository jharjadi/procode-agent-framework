# Procode Agent Framework

**A production-minded reference implementation for A2A-style agent systems**

---

## What This Is

This repository is a **learning-first, production-minded reference implementation** of an agent system built using explicit contracts, deterministic routing, guardrails, and cost-aware LLM usage.

It exists to answer a simple but under-documented question:

> **What does a real, inspectable, production-style agent system actually look like?**

Rather than relying on opaque abstractions or "fully autonomous" claims, this project focuses on:

- **clear agent boundaries**
- **explicit intent routing**
- **deterministic fallbacks**
- **observable behavior**
- **realistic operational constraints**

It is **not a toy demo** — but it is also **not a finished product**.  
It's a system being built step by step, in public, with trade-offs documented along the way.

---

## What This Is Not

To set expectations clearly, this project does **not** attempt to solve:

- long-horizon autonomous planning
- unsupervised execution across critical systems
- regulatory approval or legal compliance
- trust between unknown or adversarial agents
- "AGI-style" general intelligence

Those are real problems — and **intentionally out of scope** here.

---

## Design Philosophy

This project is guided by a few core principles:

### Contracts over magic
Agents communicate via explicit schemas and agent cards.

### Determinism first, LLMs second
LLMs enhance the system, but never replace inspectable logic.

### Cost is a first-class constraint
Model choice, routing, and fallbacks are designed with real budgets in mind.

### Failure is observable
Every request is auditable. Every decision can be traced.

### Agents are deployable units
External agents run as independent services, not hidden classes.

---

## Quick Start (Docker – recommended)

You can run the entire system locally in about a minute.

```bash
git clone https://github.com/jharjadi/procode-agent-framework.git
cd procode-agent-framework
cp .env.example .env
docker-compose up -d
```

### Running services

- **Principal Agent API**: http://localhost:9998
- **Frontend UI (Next.js)**: http://localhost:3001
- **PostgreSQL**: localhost:5433
- **Weather Agent (external)**: http://localhost:9996
- **Insurance Agent (external)**: http://localhost:9997

The system works **out of the box** with deterministic routing.  
Adding an LLM API key enables enhanced intent classification.

---

## Why Agent Cards (A2A)

Each agent in this system is described using an **agent card** — a declarative contract that defines:

- agent identity
- capabilities
- supported intents
- routing expectations
- security and operational constraints

**Example:**

```yaml
agent:
  name: insurance_agent
  role: principal
  version: 1.0.0

capabilities:
  info:
    intents: ["get", "check", "quote", "coverage"]
  creation:
    intents: ["create", "update", "cancel"]
```

This allows agents to be:

- **independently deployable**
- **discoverable**
- **replaceable**
- **reasoned about** without reading implementation code

---

## Current State of the Project

This repository is being built **incrementally**.  
The system is currently at **Step 11 of 25** in a documented production roadmap.

### Implemented Capabilities

#### Core System

-  Principal agent with deterministic routing
-  LLM-assisted intent classification with fallback logic
-  Multi-turn conversation memory
-  Server-Sent Events (SSE) streaming
-  Tool integration with mocked / real execution modes

#### External Agents

-  **Weather Agent** (OpenWeatherMap API, caching, standalone service)
-  **Insurance Agent** (principal + task-agent pattern)

#### Persistence & Auditability

-  SQLAlchemy ORM with SQLite / PostgreSQL
-  Alembic migrations
-  Full audit trail (database + file logging)
-  Conversation history persistence

#### Security & Guardrails

-  Optional enterprise-style API key system
-  Rate limiting (per-IP / per-key)
-  PII detection and redaction
-  CORS restrictions
-  Circuit breaker patterns

---

## Cost-Aware LLM Routing

One of the goals of this project is to treat **LLM cost as a design constraint**, not an afterthought.

The system supports:

- multiple LLM providers (Anthropic, OpenAI, Google)
- lightweight models for simple intents
- higher-capability models only when needed
- deterministic routing when LLMs are unavailable

A detailed breakdown of the cost strategy is available here:  
📊 [Cost Optimization Summary](docs/COST_OPTIMIZATION_SUMMARY.md)

---

## Architecture Overview

```
Principal Agent
│
├─ Intent Classification (LLM + deterministic fallback)
├─ Task Routing
├─ Guardrails & Audit Logging
│
├─ Internal Task Agents
│   ├─ Tickets
│   ├─ Account
│   ├─ Payments
│   └─ General
│
└─ External Agents (A2A)
    ├─ Weather Agent (standalone service)
    └─ Insurance Agent (principal + task agents)
```

Each external agent runs as its own process, communicates over A2A, and can be replaced independently.

---

## Configuration

All behavior is driven via **environment variables**.  
LLM usage is **optional**.

```bash
# LLMs (optional)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Database
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@localhost:5433/procode

# Security (optional)
ENABLE_API_KEY_AUTH=false
ENABLE_API_SECURITY=false
RATE_LIMIT_PER_MINUTE=10

# External agents
OPENWEATHER_API_KEY=
EXTERNAL_AGENTS_CONFIG=config/external_agents.production.json
```

See [`.env.example`](.env.example) for the full list.

---

## Testing

```bash
make test-all
```

Includes:

- unit tests
- LLM integration tests
- streaming tests
- agent-to-agent communication tests
- database persistence tests

---

## Roadmap (High Level)

### Phase 1 – Core Infrastructure

-  Database persistence
-  API authentication
-  API security & rate limiting
-  External agents system
- ⏳ Redis caching (next)

### Phase 2 – Scalability

- ⏳ Horizontal scaling
- ⏳ Message queues
- ⏳ Observability

### Phase 3 – Advanced AI

- ⏳ Vector search
- ⏳ RAG
- ⏳ Model optimization

### Phase 4 – Business Capabilities

- ⏳ Multi-tenancy
- ⏳ Billing & usage tracking
- ⏳ Admin UI

### Phase 5 – Production Readiness

- ⏳ CI/CD
- ⏳ Deployment guides

**Full roadmap**: [Production Roadmap](docs/PRODUCTION_ROADMAP.md)

---

## Documentation

### Getting Started
- [Quick Start Guide](QUICKSTART.md)
- [Docker Deployment](docs/DOCKER_DEPLOYMENT.md)
- [Project Structure](docs/STRUCTURE.md)

### Core Features
- [Multi-LLM Strategy](docs/MULTI_LLM_STRATEGY.md)
- [Database Integration](docs/DATABASE_INTEGRATION.md)
- [API Security](docs/API_SECURITY.md)
- [A2A Communication](docs/A2A_COMMUNICATION.md)

### External Agents
- [External Agents Overview](external_agents/README.md)
- [Architecture](external_agents/ARCHITECTURE.md)
- [Development Guide](external_agents/DEVELOPMENT_GUIDE.md)
- [Quick Start](external_agents/QUICKSTART.md)

### Implementation
- [Cost Optimization Summary](docs/COST_OPTIMIZATION_SUMMARY.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Development History](docs/DEVELOPMENT_HISTORY.md)
- [Changelog](CHANGELOG.md)

---

## Contributing & Reuse

This project is evolving quickly, and some APIs are still in flux.

That said:

- **issues for discussion** are welcome
- **forks** are encouraged
- **patterns and ideas** are free to reuse elsewhere

Once the core architecture stabilises, contributions will open up more formally.

---

## License

[MIT License](LICENSE) — use freely, modify responsibly.

Copyright (c) 2026 Jimmy Harjadi

---

## Final Note

This repository is **not trying to predict the future of AI agents**.

It's trying to make the present less confusing by showing:

- what works
- what breaks
- what trade-offs exist
- and where human judgment is still required

If it helps you reason more clearly about agent systems, then it's done its job.

---

**Built with expertise in**: AI/ML Engineering, Solution Architecture, Production Systems, Cost Optimization, Security & Compliance

**Questions?** Check the [documentation](docs/) or review the [development history](docs/DEVELOPMENT_HISTORY.md) for context.
