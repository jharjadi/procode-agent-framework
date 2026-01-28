# Public Reference Release (v0.1.0)

I'm sharing this project publicly as a **learning-first, production-minded reference implementation** of an A2A-style agent system.

This repository exists to explore a simple question:

> What does a *real*, inspectable, production-style agent system look like — without hype or hidden magic?

## What this project focuses on

- explicit agent contracts (agent cards)
- deterministic routing with LLM assistance (not replacement)
- cost-aware model selection
- observable behavior (audit logs, persistence)
- independently deployable external agents

## What this project does *not* try to do

- long-horizon autonomy
- unsupervised execution
- "AGI-style" claims
- black-box abstractions

The system is being built incrementally, with trade-offs documented as the design evolves.  
It is not a finished product — and that's intentional.

If this helps you reason more clearly about agent architectures, feel free to explore, fork, or reuse patterns.

Questions and discussion are welcome.

---

## Quick Links

- [README](README.md) - Project overview and philosophy
- [QUICKSTART](QUICKSTART.md) - Get started in 5 minutes
- [External Agents](external_agents/README.md) - Learn about the A2A integration pattern
- [Architecture](external_agents/ARCHITECTURE.md) - System design and trade-offs

## What's Included in v0.1.0

### Core Framework
- Multi-agent orchestration with deterministic routing
- Intent classification with LLM assistance
- Cost-aware model selection (GPT-4.1, Claude Sonnet 4.5, Gemini 2.0 Flash)
- Conversation memory and context management
- PostgreSQL persistence layer

### External Agents (A2A Protocol)
- **Weather Agent** - Simple pattern with OpenWeatherMap API integration
- **Insurance Agent** - Complex pattern with principal + task agent routing
- Shared infrastructure for building new external agents

### Security & Observability
- API key authentication with rate limiting
- Structured audit logging
- Circuit breaker pattern for external services
- Content guardrails and compliance checks

### Deployment
- Docker Compose for local development
- Production-ready Portainer configuration
- Health checks and monitoring

## Known Limitations

This is an early reference release. Known areas for improvement:

- Frontend UX needs enhancement
- Test coverage is incomplete
- Some edge cases in external agent routing
- Documentation could be more comprehensive

These are documented intentionally to show real-world trade-offs in building agent systems.

## Contributing

This project is primarily a reference implementation, but thoughtful contributions are welcome. Please open an issue first to discuss significant changes.
