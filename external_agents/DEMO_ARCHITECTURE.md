# External Agents Demo Architecture

## Overview

This document outlines the demo architecture for external agents, showcasing two different patterns:
1. **Complex Agent** with Principal + Multiple Task Agents
2. **Simple Agent** with Principal only (handles all tasks)

## Demo Scenario

### ProCode Agent (Port 9998) - Main System
```
Port 9998: ProCode Agent System
├── Principal Agent (Router)
│   ├── Intent Classification
│   └── Routes to:
│       ├── Tickets Task Agent
│       ├── Account Task Agent
│       ├── Payments Task Agent
│       └── External Agents (via A2A)
```

### Insurance Agent (Port 9997) - Complex Pattern
```
Port 9997: Insurance Agent System
├── Insurance Principal Agent (Router)
│   ├── Intent Classification
│   │   - "get insurance info" → Insurance Info Agent
│   │   - "create insurance" → Insurance Creation Agent
│   └── Routes to:
│       ├── Insurance Info Task Agent
│       │   - Get policy details
│       │   - Check coverage
│       │   - Get premium quotes
│       └── Insurance Creation Task Agent
│           - Create new policy
│           - Update policy
│           - Cancel policy
```

**Demonstrates**: Principal + Multiple Task Agents pattern

### Weather Agent (Port 9996) - Simple Pattern
```
Port 9996: Weather Agent System
├── Weather Principal Agent (All-in-One)
    ├── Get current weather
    ├── Get forecast
    ├── Get weather alerts
    └── Get historical data
```

**Demonstrates**: Principal-only pattern (no separate task agents)

## Communication Flow Examples

### Example 1: Complex Agent (Insurance)

```
User: "What's my insurance coverage?"
    ↓
ProCode Principal (9998)
    ↓
Classifies: "insurance query"
    ↓
A2A Call → Insurance Principal (9997)
    ↓
Insurance Principal classifies: "info request"
    ↓
Routes to → Insurance Info Task Agent
    ↓
Fetches policy details
    ↓
Returns to Insurance Principal
    ↓
Returns to ProCode Principal
    ↓
Response to User: "Your policy covers..."
```

### Example 2: Simple Agent (Weather)

```
User: "What's the weather in San Francisco?"
    ↓
ProCode Principal (9998)
    ↓
Classifies: "weather query"
    ↓
A2A Call → Weather Principal (9996)
    ↓
Weather Principal handles directly (no routing)
    ↓
Fetches weather data
    ↓
Returns to ProCode Principal
    ↓
Response to User: "Currently 72°F, sunny..."
```

### Example 3: Multi-Agent Workflow

```
User: "Create insurance for my trip to Hawaii"
    ↓
ProCode Principal (9998)
    ↓
Orchestrates:
    ├─► Weather Agent (9996): "Get Hawaii weather forecast"
    └─► Insurance Agent (9997): "Create travel insurance"
    ↓
Aggregates results
    ↓
Response: "Created travel insurance. Weather looks good!"
```

## Architecture Diagrams

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                ProCode Agent (9998)                      │
│  ┌────────────────────────────────────────────────┐    │
│  │  Principal Agent                                │    │
│  │  - Routes internal tasks                        │    │
│  │  - Delegates to external agents                 │    │
│  └────────────────────────────────────────────────┘    │
│         │                                                │
│         ├─► Tickets Agent (Internal)                    │
│         ├─► Account Agent (Internal)                    │
│         ├─► Payments Agent (Internal)                   │
│         │                                                │
│         └─► A2A Client ──────────────────────────────┐  │
└─────────────────────────────────────────────────────│──┘
                                                      │
                    ┌─────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Insurance│   │ Weather │   │ Future  │
│  Agent  │   │  Agent  │   │ Agents  │
│  9997   │   │  9996   │   │  ...    │
└─────────┘   └─────────┘   └─────────┘
```

### Insurance Agent (Complex Pattern)

```
┌─────────────────────────────────────────────────────────┐
│         Insurance Agent System (Port 9997)               │
│  ┌────────────────────────────────────────────────┐    │
│  │  Insurance Principal Agent                      │    │
│  │  - Receives A2A requests                        │    │
│  │  - Classifies intent (info vs creation)        │    │
│  │  - Routes to appropriate task agent             │    │
│  └────────────────────────────────────────────────┘    │
│         │                                                │
│         ├─► Insurance Info Task Agent                   │
│         │   - Get policy details                        │
│         │   - Check coverage                            │
│         │   - Get premium quotes                        │
│         │                                                │
│         └─► Insurance Creation Task Agent               │
│             - Create new policy                         │
│             - Update existing policy                    │
│             - Cancel policy                             │
└─────────────────────────────────────────────────────────┘
```

### Weather Agent (Simple Pattern)

```
┌─────────────────────────────────────────────────────────┐
│          Weather Agent System (Port 9996)                │
│  ┌────────────────────────────────────────────────┐    │
│  │  Weather Principal Agent (All-in-One)           │    │
│  │  - Receives A2A requests                        │    │
│  │  - Handles all weather queries directly         │    │
│  │  - No routing to task agents                    │    │
│  │                                                  │    │
│  │  Capabilities:                                   │    │
│  │  - Get current weather                          │    │
│  │  - Get forecast                                 │    │
│  │  - Get weather alerts                           │    │
│  │  - Get historical data                          │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Demo Use Cases

### Use Case 1: Insurance Information Query
**User**: "What does my insurance cover?"

**Flow**:
1. ProCode Principal → Insurance Agent (9997)
2. Insurance Principal → Insurance Info Task Agent
3. Returns policy coverage details

**Demonstrates**: Complex agent with task routing

### Use Case 2: Weather Query
**User**: "What's the weather like?"

**Flow**:
1. ProCode Principal → Weather Agent (9996)
2. Weather Principal handles directly
3. Returns weather information

**Demonstrates**: Simple agent without task routing

### Use Case 3: Insurance Creation
**User**: "I need travel insurance for my trip"

**Flow**:
1. ProCode Principal → Insurance Agent (9997)
2. Insurance Principal → Insurance Creation Task Agent
3. Creates new policy
4. Returns policy confirmation

**Demonstrates**: Complex agent with different task routing

### Use Case 4: Multi-Agent Orchestration
**User**: "Plan my trip to Hawaii - check weather and get travel insurance"

**Flow**:
1. ProCode Principal orchestrates:
   - Weather Agent (9996): Get Hawaii forecast
   - Insurance Agent (9997): Create travel insurance
2. Aggregates results
3. Returns comprehensive response

**Demonstrates**: Multi-agent collaboration

## Implementation Priorities

### Phase 1: Insurance Agent (Complex Pattern)
**Priority**: High - Demonstrates full pattern

**Components**:
- Insurance Principal Agent
- Insurance Info Task Agent
- Insurance Creation Task Agent
- Configuration
- Tests

**Estimated Effort**: 3-4 days

### Phase 2: Weather Agent (Simple Pattern)
**Priority**: High - Demonstrates simple pattern

**Components**:
- Weather Principal Agent (all-in-one)
- Configuration
- Tests

**Estimated Effort**: 1-2 days

### Phase 3: Integration & Demo
**Priority**: High - Show it working

**Components**:
- Multi-agent workflows
- Demo scripts
- Documentation
- Video/screenshots

**Estimated Effort**: 1-2 days

## Key Differences Between Patterns

### Complex Pattern (Insurance Agent)
**When to use**:
- Multiple distinct operations
- Different data sources per operation
- Complex business logic
- Need for specialized handling

**Pros**:
- Clear separation of concerns
- Easy to test individual tasks
- Can optimize each task independently
- Easier to maintain

**Cons**:
- More code
- More files
- Slightly more complex

### Simple Pattern (Weather Agent)
**When to use**:
- Simple, related operations
- Single data source
- Straightforward logic
- Quick responses

**Pros**:
- Less code
- Faster to implement
- Easier to understand
- Lower latency (no internal routing)

**Cons**:
- Can become messy if grows
- Harder to test individual operations
- Less flexible for future changes

## Demo Script

### Setup
```bash
# Start ProCode Agent
make start

# Start Insurance Agent
cd external_agents/insurance_agent
python __main__.py

# Start Weather Agent
cd external_agents/weather_agent
python __main__.py
```

### Demo 1: Simple Weather Query
```bash
curl -X POST http://localhost:9998/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What'\''s the weather in Tokyo?"}]
      }
    },
    "id": 1
  }'
```

### Demo 2: Insurance Info Query
```bash
curl -X POST http://localhost:9998/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What does my insurance cover?"}]
      }
    },
    "id": 2
  }'
```

### Demo 3: Create Insurance
```bash
curl -X POST http://localhost:9998/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Create travel insurance for my Hawaii trip"}]
      }
    },
    "id": 3
  }'
```

### Demo 4: Multi-Agent Workflow
```python
from a2a_comm.agent_orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(registry)
result = await orchestrator.execute_parallel([
    {"agent": "weather_agent", "task": "Get Hawaii weather"},
    {"agent": "insurance_agent", "task": "Create travel insurance"}
])
```

## Success Metrics

✅ **Functionality**
- Insurance agent routes to correct task agent
- Weather agent responds directly
- Multi-agent workflows work
- Error handling is robust

✅ **Demo Quality**
- Clear difference between patterns
- Easy to understand
- Impressive to watch
- Good documentation

✅ **Code Quality**
- Clean, readable code
- Well-tested
- Good comments
- Follows patterns

## Next Steps

1. **Review this architecture** - Confirm it matches your vision
2. **Switch to Code mode** - Start implementation
3. **Implement Insurance Agent** - Complex pattern first
4. **Implement Weather Agent** - Simple pattern second
5. **Create demo scripts** - Show it working
6. **Document learnings** - Update guides

---

**This architecture demonstrates**:
- ✅ Two different agent patterns
- ✅ Real-world use cases (insurance, weather)
- ✅ Multi-agent collaboration
- ✅ A2A protocol in action
- ✅ Scalability and flexibility

**Ready to implement!** 🚀
