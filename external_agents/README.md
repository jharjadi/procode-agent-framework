# External Agents

A collection of specialized A2A-compatible agents that extend the ProCode Agent Framework's capabilities through agent-to-agent communication.

## 🎯 Overview

External agents are independent, specialized agents that:
- Run as separate services
- Communicate via A2A protocol
- Have their own Principal and Task agents
- Can be deployed and scaled independently
- Extend ProCode's capabilities without modifying core code

## 📦 Available Agents

### Translation Agent (Port 9997)
**Capabilities**: `translation`, `language-detection`, `transliteration`

Specialized in language services:
- Translate text between 100+ languages
- Detect source language automatically
- Transliterate between scripts (e.g., Latin to Cyrillic)

### Analytics Agent (Port 9996)
**Capabilities**: `analytics`, `reporting`, `visualization`

Specialized in data analysis:
- Analyze datasets and generate insights
- Create statistical reports
- Generate data visualizations

### Compliance Agent (Port 9995)
**Capabilities**: `compliance`, `pii-detection`, `gdpr`, `audit`

Specialized in compliance and security:
- Detect and redact PII
- GDPR compliance checking
- Audit trail generation
- Data retention policy enforcement

## 🚀 Quick Start

### Run All External Agents

```bash
# Start all external agents
docker-compose -f external_agents/docker/docker-compose.external.yml up -d

# View logs
docker-compose -f external_agents/docker/docker-compose.external.yml logs -f

# Stop all agents
docker-compose -f external_agents/docker/docker-compose.external.yml down
```

### Run Individual Agent

```bash
# Translation Agent only
cd external_agents/translation_agent
python __main__.py

# Or with Docker
docker build -t translation-agent .
docker run -p 9997:9997 translation-agent
```

### Test Agent Communication

```bash
# Test A2A communication between ProCode and external agents
python external_agents/tests/test_agent_communication.py

# Test multi-agent orchestration
python external_agents/tests/test_orchestration.py
```

## 🔧 Using External Agents from ProCode

### Register External Agent

```python
from a2a_comm.agent_discovery import AgentDiscovery

discovery = AgentDiscovery()
discovery.register_agent(
    name="translation_agent",
    url="http://localhost:9997",
    capabilities=["translation", "language-detection"]
)
```

### Call External Agent

```python
from a2a_comm.agent_client import AgentClient

# Direct call
client = AgentClient("http://localhost:9997")
response = await client.send_text("Translate 'Hello' to Spanish")

# Via orchestrator
from a2a_comm.agent_orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(discovery)
result = await orchestrator.delegate_task(
    agent="translation_agent",
    task="Translate 'Hello World' to French"
)
```

### Multi-Agent Workflow

```python
# Orchestrate multiple agents
workflow = [
    {"agent": "translation_agent", "task": "Translate to Spanish"},
    {"agent": "analytics_agent", "task": "Analyze sentiment"},
    {"agent": "compliance_agent", "task": "Check for PII"}
]

result = await orchestrator.execute_workflow(workflow)
```

## 🏗️ Architecture

Each external agent follows the same structure:

```
external_agent/
├── principal.py          # Routes requests to task agents
├── tasks/               # Specialized task handlers
│   ├── task_*.py       # Individual task implementations
├── config.yaml         # Agent configuration
├── __main__.py         # Entry point
└── Dockerfile          # Docker configuration
```

**Flow:**
1. ProCode Agent → A2A Request → External Agent Principal
2. External Principal → Routes to appropriate Task Agent
3. Task Agent → Processes request
4. Task Agent → Returns result to Principal
5. External Principal → Returns to ProCode Agent

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture and design patterns
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - How to create new agents
- **Agent-specific READMEs** - In each agent's directory

## 🛠️ Creating a New Agent

Use the agent template generator:

```bash
# Generate new agent from template
python external_agents/templates/create_agent.py --name my_agent --port 9994

# This creates:
# external_agents/my_agent/
#   ├── README.md
#   ├── __init__.py
#   ├── __main__.py
#   ├── principal.py
#   ├── config.yaml
#   ├── Dockerfile
#   └── tasks/
#       └── task_example.py
```

Then customize the generated files for your use case.

## 🧪 Testing

```bash
# Run all external agent tests
pytest external_agents/tests/

# Test specific agent
pytest external_agents/translation_agent/tests/

# Integration tests
pytest external_agents/tests/test_agent_communication.py -v
```

## 🐳 Docker Deployment

### Build All Agents

```bash
# Build all external agent images
make docker-build-external-agents

# Or individually
docker build -t translation-agent external_agents/translation_agent/
docker build -t analytics-agent external_agents/analytics_agent/
docker build -t compliance-agent external_agents/compliance_agent/
```

### Production Deployment

```bash
# Deploy to production
docker-compose -f external_agents/docker/docker-compose.external.yml \
  -f external_agents/docker/docker-compose.prod.yml up -d

# Scale specific agent
docker-compose -f external_agents/docker/docker-compose.external.yml \
  scale translation-agent=3
```

## 🔐 Security

External agents support the same security features as ProCode:
- API key authentication (optional)
- Rate limiting
- CORS restrictions
- Audit logging
- PII detection

Configure in each agent's `config.yaml`.

## 📊 Monitoring

Each agent exposes:
- **Health check**: `GET /health`
- **Metrics**: `GET /metrics`
- **Agent info**: `GET /info`

## 🤝 Contributing

To add a new external agent:

1. Use the template generator
2. Implement your task agents
3. Write tests
4. Update documentation
5. Add to docker-compose.external.yml
6. Submit PR

## 📝 License

Same as ProCode Agent Framework - MIT License

## 🆘 Support

- Check agent-specific README for details
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for design patterns
- See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for examples
- Open an issue for bugs or questions

---

**Built with**: A2A Protocol, Python 3.11+, FastAPI, Docker
