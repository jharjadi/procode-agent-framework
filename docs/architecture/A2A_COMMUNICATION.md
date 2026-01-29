# Agent-to-Agent (A2A) Communication

This document describes the Agent-to-Agent communication features implemented in Step 8 of the procode framework.

## Overview

The A2A communication system enables the procode agent to:
- Discover and communicate with other agents
- Delegate tasks to specialized agents
- Orchestrate multi-agent workflows (sequential and parallel)
- Handle errors and implement fallback strategies

## Components

### 1. Agent Discovery (`agent_discovery.py`)

The `AgentRegistry` class manages agent discovery and registration.

**Features:**
- Register agents programmatically
- Load agents from JSON configuration files
- Load agents from environment variables
- Find agents by name or capability
- List all registered agents and capabilities

**Example Usage:**
```python
from agent_discovery import AgentRegistry, AgentCard

# Create registry
registry = AgentRegistry()

# Register an agent
agent_card = AgentCard(
    name="ticket_agent",
    url="http://localhost:9999",
    capabilities=["tickets", "support"],
    description="Ticket management agent"
)
registry.register_agent(agent_card)

# Find agent by capability
agent = registry.find_agent("tickets")
```

**Configuration File Format (`agents_config.json`):**
```json
{
  "agents": [
    {
      "name": "ticket_agent",
      "url": "http://localhost:9999",
      "capabilities": ["tickets", "support"],
      "description": "Agent for ticket management",
      "version": "1.0.0"
    }
  ]
}
```

**Environment Variables:**
```bash
# Define agent URL
export AGENT_TICKET_URL=http://localhost:9999

# Define agent capabilities
export AGENT_TICKET_CAPABILITIES=tickets,support,issue_tracking
```

### 2. Agent Client (`agent_client.py`)

The `AgentClient` class handles communication with remote agents via A2A protocol.

**Features:**
- Send messages to agents using JSON-RPC
- Delegate tasks with automatic retry logic
- Handle timeouts and errors gracefully
- Connection pooling for efficiency

**Example Usage:**
```python
from agent_client import AgentClient
from a2a.types import Message, TextPart

# Create client
async with AgentClient("http://localhost:9999") as client:
    # Send a simple text message
    response = await client.send_text("Create a support ticket")
    print(response)
    
    # Delegate a task
    result = await client.delegate_task(
        "Create ticket for login issue",
        task_id="task-123"
    )
```

**Client Pool:**
```python
from agent_client import AgentClientPool

# Create pool for managing multiple connections
pool = AgentClientPool()

# Get clients (automatically cached)
client1 = pool.get_client("http://localhost:9999")
client2 = pool.get_client("http://localhost:9998")

# Clean up
await pool.close_all()
```

### 3. Agent Orchestrator (`agent_orchestrator.py`)

The `AgentOrchestrator` class coordinates multi-agent workflows.

**Features:**
- Sequential workflow execution with dependencies
- Parallel task execution
- Fallback strategies for resilience
- Progress tracking and status monitoring

**Sequential Workflow Example:**
```python
from agent_orchestrator import AgentOrchestrator
from agent_discovery import AgentRegistry

registry = AgentRegistry()
orchestrator = AgentOrchestrator(registry)

# Define workflow steps
workflow = [
    {
        "agent": "ticket_agent",
        "task": "Create support ticket",
        "depends_on": []
    },
    {
        "agent": "notification_agent",
        "task": "Send notification to team",
        "depends_on": [0]  # Wait for step 0 to complete
    }
]

# Execute workflow
result = await orchestrator.execute_workflow(workflow)

print(f"Status: {result.status}")
print(f"Execution time: {result.execution_time}s")
for step in result.steps:
    print(f"  {step.agent}: {step.status} - {step.result}")
```

**Parallel Execution Example:**
```python
# Define parallel tasks
tasks = [
    {"agent": "analytics_agent", "task": "Analyze user data"},
    {"agent": "security_agent", "task": "Check security logs"},
    {"agent": "performance_agent", "task": "Review metrics"}
]

# Execute in parallel
result = await orchestrator.execute_parallel(tasks)
```

**Fallback Strategy Example:**
```python
# Try multiple agents in order until one succeeds
result = await orchestrator.execute_with_fallback(
    task="Process payment",
    agent_names=["primary_payment_agent", "backup_payment_agent", "fallback_agent"]
)
```

### 4. Agent Router Integration (`agent_router.py`)

The `ProcodeAgentRouter` now supports automatic delegation detection.

**Delegation Keywords:**
- "ask the [agent]"
- "check with [agent]"
- "consult [agent]"
- "delegate to [agent]"
- "get help from [agent]"
- "forward to [agent]"
- "send to [agent]"
- "talk to [agent]"

**Example:**
```python
# User input that triggers delegation
"ask the ticket_agent to create a support ticket"

# Router automatically:
# 1. Detects delegation intent
# 2. Extracts agent name (ticket_agent)
# 3. Extracts task (create a support ticket)
# 4. Delegates to the agent
# 5. Returns the result
```

## Testing

### Mock Agent Server

Use `test_mock_agent.py` to create mock agents for testing:

```bash
# Run a generic mock agent
python test_mock_agent.py

# Run a specialized mock agent
python test_mock_agent.py ticket 9999

# Run analytics mock agent on custom port
python test_mock_agent.py analytics 9997
```

### Running Tests

```bash
# Run all A2A communication tests
pytest test_agent_communication.py -v

# Run specific test class
pytest test_agent_communication.py::TestAgentRegistry -v

# Run with coverage
pytest test_agent_communication.py --cov=agent_discovery --cov=agent_client --cov=agent_orchestrator
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Procode Agent Router                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Delegation Detection & Routing                        │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Agent      │ │   Agent      │ │   Agent      │
│  Discovery   │ │   Client     │ │ Orchestrator │
│              │ │              │ │              │
│ - Registry   │ │ - JSON-RPC   │ │ - Workflows  │
│ - Config     │ │ - Retry      │ │ - Parallel   │
│ - Env Vars   │ │ - Pooling    │ │ - Fallback   │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │     Remote Agents (A2A)       │
        │                               │
        │  ┌─────────┐  ┌─────────┐   │
        │  │ Ticket  │  │Analytics│   │
        │  │ Agent   │  │ Agent   │   │
        │  └─────────┘  └─────────┘   │
        └───────────────────────────────┘
```

## Error Handling

The A2A system includes comprehensive error handling:

1. **Connection Errors**: Automatic retry with exponential backoff
2. **Timeouts**: Configurable timeout with fallback options
3. **Agent Not Found**: Clear error messages with suggestions
4. **Workflow Failures**: Partial results with error details
5. **Validation Errors**: Input/output validation with guardrails

## Best Practices

1. **Agent Registration**: Always register agents before use
2. **Timeouts**: Set appropriate timeouts based on task complexity
3. **Retries**: Use retry logic for transient failures
4. **Fallbacks**: Implement fallback agents for critical operations
5. **Monitoring**: Track workflow execution times and success rates
6. **Testing**: Use mock agents for development and testing

## Future Enhancements

- Circuit breaker pattern for failing agents
- Agent health monitoring and auto-discovery
- Message queues for async communication
- Agent versioning and compatibility checks
- Authentication and authorization between agents
- Distributed tracing and observability

## Related Files

- [`agent_discovery.py`](agent_discovery.py) - Agent registry and discovery
- [`agent_client.py`](agent_client.py) - A2A protocol client
- [`agent_orchestrator.py`](agent_orchestrator.py) - Workflow orchestration
- [`agent_router.py`](agent_router.py) - Router with delegation logic
- [`test_mock_agent.py`](test_mock_agent.py) - Mock agent server
- [`test_agent_communication.py`](test_agent_communication.py) - Integration tests
- [`agents_config.json`](agents_config.json) - Agent configuration

## See Also

- [Step 8 Specification](.roo/specs/step8-agent-to-agent-communication.md)
- [A2A Protocol Documentation](https://github.com/google/a2a)
