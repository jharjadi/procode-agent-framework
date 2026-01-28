# External Agent Routing Integration

## Overview

This document explains how to integrate external agent routing into the ProCode Principal Agent ([`core/agent_router.py`](../core/agent_router.py:20)) so it can intelligently route requests to external agents (Insurance Agent, Weather Agent) based on topic/intent.

## Current Architecture

### ProCode Principal Agent (Port 9998)
The ProCode system currently has:
- **Principal Agent**: [`ProcodeAgentRouter`](../core/agent_router.py:20) - Routes to internal task agents
- **Internal Task Agents**:
  - [`TicketsAgent`](../tasks/task_tickets.py) - Support tickets
  - [`AccountAgent`](../tasks/task_account.py) - Account management
  - [`PaymentsAgent`](../tasks/task_payments.py) - Payment processing
  - [`GeneralAgent`](../tasks/task_general.py) - General queries

### Current Routing Mechanism

The [`ProcodeAgentRouter`](../core/agent_router.py:20) uses:

1. **Intent Classification** ([`IntentClassifier`](../core/intent_classifier.py:8)):
   - LLM-based classification (Claude, GPT, Gemini)
   - Deterministic keyword matching (fallback)
   - Classifies into: `tickets`, `account`, `payments`, `general`, `unknown`

2. **A2A Delegation** (Already Implemented):
   - [`_should_delegate()`](../core/agent_router.py:306) - Detects delegation keywords
   - [`_extract_agent_name()`](../core/agent_router.py:328) - Extracts target agent name
   - [`_delegate_to_agent()`](../core/agent_router.py:375) - Delegates via A2A protocol
   - Uses [`AgentRegistry`](../a2a_comm/agent_discovery.py:60) for agent discovery

## Integration Strategy

### Option 1: Topic-Based Routing (Recommended)

Extend the intent classifier to recognize external agent topics and route automatically.

#### Architecture Flow

```
User Request
    ↓
ProCode Principal Agent (9998)
    ↓
Intent Classifier (Enhanced)
    ↓
    ├─→ Internal Topics → Internal Task Agents
    │   ├─→ "tickets" → TicketsAgent
    │   ├─→ "account" → AccountAgent
    │   ├─→ "payments" → PaymentsAgent
    │   └─→ "general" → GeneralAgent
    │
    └─→ External Topics → External Agents (via A2A)
        ├─→ "insurance" → Insurance Agent (9997)
        └─→ "weather" → Weather Agent (9996)
```

#### Implementation Steps

##### Step 1: Extend Intent Types

Update [`core/intent_classifier.py`](../core/intent_classifier.py:8):

```python
# Add new intent types
IntentType = Literal[
    "tickets", 
    "account", 
    "payments", 
    "general", 
    "insurance",  # NEW: External agent
    "weather",    # NEW: External agent
    "unknown"
]
```

##### Step 2: Update Deterministic Patterns

Add keyword patterns for external agents:

```python
def _classify_deterministic(self, text: str) -> IntentType:
    text_lower = text.lower()
    
    # External agent patterns (check first for priority)
    insurance_keywords = [
        "insurance", "policy", "coverage", "premium", 
        "claim", "insure", "insured"
    ]
    if any(keyword in text_lower for keyword in insurance_keywords):
        return "insurance"
    
    weather_keywords = [
        "weather", "forecast", "temperature", "rain", 
        "sunny", "cloudy", "climate", "meteorology"
    ]
    if any(keyword in text_lower for keyword in weather_keywords):
        return "weather"
    
    # Existing internal patterns...
    # (tickets, account, payments, general)
```

##### Step 3: Update LLM Classification Prompt

Enhance the LLM prompt to include external topics:

```python
def _classify_with_llm(self, text: str) -> IntentType:
    prompt = f"""You are an intent classifier for a multi-agent system.

Classify the following user message into ONE of these intents:

INTERNAL AGENTS:
- tickets: Support tickets, issues, bugs
- account: Account info, profile, settings
- payments: Payment requests, billing
- general: Greetings, thanks, help, capabilities

EXTERNAL AGENTS:
- insurance: Insurance policies, coverage, claims, premiums
- weather: Weather information, forecasts, temperature, climate

- unknown: Anything that doesn't fit above categories

Message: "{text}"
Intent:"""
    
    response = self.llm.invoke(prompt)
    intent_text = response.content.strip().lower()
    
    # Parse response
    if "insurance" in intent_text:
        return "insurance"
    elif "weather" in intent_text:
        return "weather"
    elif "tickets" in intent_text:
        return "tickets"
    # ... rest of parsing
```

##### Step 4: Update Agent Router

Modify [`core/agent_router.py`](../core/agent_router.py:20) to handle external intents:

```python
async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    # ... existing validation code ...
    
    # Classify intent
    intent = self.intent_classifier.classify_intent(text)
    classification_metadata = self.intent_classifier.get_classification_metadata()
    
    # Route based on intent
    if intent in ["insurance", "weather"]:
        # Route to external agent
        result = await self._route_to_external_agent(intent, text, context)
    elif intent == "tickets":
        result = await self.tickets_agent.invoke(simple_context)
        result = f"🎫 **Tickets Agent**: {result}"
    elif intent == "account":
        result = await self.account_agent.invoke(simple_context)
        result = f"👤 **Account Agent**: {result}"
    # ... rest of routing logic
```

##### Step 5: Implement External Agent Routing

Add new method to [`ProcodeAgentRouter`](../core/agent_router.py:20):

```python
async def _route_to_external_agent(
    self,
    intent: str,
    text: str,
    context: RequestContext
) -> str:
    """
    Route request to external agent based on intent.
    
    Args:
        intent: Classified intent (e.g., "insurance", "weather")
        text: User input text
        context: Request context
        
    Returns:
        Result from external agent
    """
    # Map intent to agent name
    intent_to_agent = {
        "insurance": "insurance_agent",
        "weather": "weather_agent"
    }
    
    agent_name = intent_to_agent.get(intent)
    if not agent_name:
        return f"❌ No external agent configured for intent: {intent}"
    
    # Find agent in registry
    agent_card = self.agent_registry.get_agent(agent_name)
    if not agent_card:
        return f"❌ External agent '{agent_name}' not found. Is it running?"
    
    # Create client and delegate
    from a2a_comm.agent_client import AgentClient, AgentCommunicationError
    
    client = AgentClient(agent_card.url)
    try:
        task_id = context.task_id if hasattr(context, 'task_id') else None
        result = await client.delegate_task(text, task_id)
        
        # Add emoji prefix based on agent
        emoji_map = {
            "insurance": "🏥",
            "weather": "🌤️"
        }
        emoji = emoji_map.get(intent, "🔗")
        
        return f"{emoji} **{agent_card.name.title()}**: {result}"
    except AgentCommunicationError as e:
        return f"❌ Failed to communicate with {agent_name}: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"
    finally:
        await client.close()
```

##### Step 6: Register External Agents

Create configuration file [`config/external_agents.json`](../config/external_agents.json):

```json
{
  "agents": [
    {
      "name": "insurance_agent",
      "url": "http://localhost:9997",
      "capabilities": [
        "insurance-info",
        "insurance-creation",
        "policy-management"
      ],
      "description": "Insurance policy management system",
      "version": "1.0.0",
      "metadata": {
        "pattern": "complex",
        "task_agents": ["insurance_info", "insurance_creation"]
      }
    },
    {
      "name": "weather_agent",
      "url": "http://localhost:9996",
      "capabilities": [
        "current-weather",
        "weather-forecast",
        "weather-alerts",
        "historical-weather"
      ],
      "description": "Weather information service",
      "version": "1.0.0",
      "metadata": {
        "pattern": "simple",
        "task_agents": []
      }
    }
  ]
}
```

Update [`AgentRegistry`](../a2a_comm/agent_discovery.py:60) initialization:

```python
# In core/agent_router.py __init__
if enable_a2a:
    self.agent_registry = get_global_registry()
    
    # Load external agents configuration
    external_config = "config/external_agents.json"
    if os.path.exists(external_config):
        self.agent_registry._load_from_file(external_config)
    
    self.orchestrator = AgentOrchestrator(self.agent_registry)
```

### Option 2: Capability-Based Routing

Route based on agent capabilities rather than fixed intents.

#### Implementation

```python
async def _route_by_capability(
    self,
    text: str,
    context: RequestContext
) -> Optional[str]:
    """
    Route to external agent based on capability matching.
    
    Args:
        text: User input text
        context: Request context
        
    Returns:
        Result from agent if capability matched, None otherwise
    """
    # Extract potential capabilities from text
    text_lower = text.lower()
    
    # Check all registered agents for capability match
    for agent_card in self.agent_registry.list_agents():
        for capability in agent_card.capabilities:
            # Simple keyword matching
            capability_keywords = capability.replace("-", " ").split()
            if any(keyword in text_lower for keyword in capability_keywords):
                # Found matching capability
                client = AgentClient(agent_card.url)
                try:
                    task_id = context.task_id if hasattr(context, 'task_id') else None
                    result = await client.delegate_task(text, task_id)
                    return f"🔗 **{agent_card.name.title()}**: {result}"
                except Exception as e:
                    return f"❌ Error communicating with {agent_card.name}: {e}"
                finally:
                    await client.close()
    
    return None  # No capability match found
```

### Option 3: Hybrid Approach (Best for Production)

Combine topic-based and capability-based routing with fallback.

#### Routing Priority

1. **Explicit Delegation** - User says "ask the insurance agent"
2. **Topic Classification** - LLM/deterministic classifies as "insurance" or "weather"
3. **Capability Matching** - Check if any external agent has matching capability
4. **Internal Routing** - Route to internal task agents
5. **Unknown** - Return helpful error message

#### Implementation

```python
async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    # ... validation code ...
    
    # Priority 1: Explicit delegation
    if self._should_delegate(text):
        result = await self._delegate_to_agent(text, context)
        intent = "delegation"
    
    # Priority 2: Topic classification
    else:
        intent = self.intent_classifier.classify_intent(text)
        
        if intent in ["insurance", "weather"]:
            # Route to external agent by topic
            result = await self._route_to_external_agent(intent, text, context)
        
        elif intent == "unknown" and self.enable_a2a:
            # Priority 3: Try capability-based routing
            result = await self._route_by_capability(text, context)
            if result is None:
                # No external agent matched, return unknown
                result = "I'm not sure how to help with that."
        
        else:
            # Priority 4: Internal routing
            if intent == "tickets":
                result = await self.tickets_agent.invoke(simple_context)
                result = f"🎫 **Tickets Agent**: {result}"
            # ... rest of internal routing
    
    # ... validation and response code ...
```

## Configuration Management

### Environment Variables

Support environment-based configuration for external agents:

```bash
# .env file
AGENT_INSURANCE_URL=http://localhost:9997
AGENT_INSURANCE_CAPABILITIES=insurance-info,insurance-creation,policy-management

AGENT_WEATHER_URL=http://localhost:9996
AGENT_WEATHER_CAPABILITIES=current-weather,weather-forecast,weather-alerts
```

The [`AgentRegistry`](../a2a_comm/agent_discovery.py:60) already supports this via [`_load_from_env()`](../a2a_comm/agent_discovery.py:105).

### Docker Compose Integration

Update [`docker-compose.yml`](../docker-compose.yml) to include external agents:

```yaml
services:
  procode-agent:
    # ... existing config ...
    environment:
      - AGENT_INSURANCE_URL=http://insurance-agent:9997
      - AGENT_WEATHER_URL=http://weather-agent:9996
    depends_on:
      - insurance-agent
      - weather-agent
    networks:
      - procode-network

  insurance-agent:
    build: ./external_agents/insurance_agent
    container_name: insurance-agent
    ports:
      - "9997:9997"
    networks:
      - procode-network

  weather-agent:
    build: ./external_agents/weather_agent
    container_name: weather-agent
    ports:
      - "9996:9996"
    environment:
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    networks:
      - procode-network

networks:
  procode-network:
    driver: bridge
```

## Testing Strategy

### Unit Tests

Test intent classification for external topics:

```python
# tests/test_external_routing.py
import pytest
from core.intent_classifier import IntentClassifier

def test_insurance_intent_classification():
    classifier = IntentClassifier(use_llm=False)
    
    # Test insurance keywords
    assert classifier.classify_intent("I need insurance") == "insurance"
    assert classifier.classify_intent("What's my policy coverage?") == "insurance"
    assert classifier.classify_intent("File a claim") == "insurance"

def test_weather_intent_classification():
    classifier = IntentClassifier(use_llm=False)
    
    # Test weather keywords
    assert classifier.classify_intent("What's the weather?") == "weather"
    assert classifier.classify_intent("Show me the forecast") == "weather"
    assert classifier.classify_intent("Is it going to rain?") == "weather"
```

### Integration Tests

Test end-to-end routing to external agents:

```python
# tests/test_external_agent_integration.py
import pytest
from core.agent_router import ProcodeAgentRouter
from a2a_comm.agent_discovery import AgentCard, get_global_registry

@pytest.mark.asyncio
async def test_route_to_insurance_agent():
    # Register mock insurance agent
    registry = get_global_registry()
    registry.register_agent(AgentCard(
        name="insurance_agent",
        url="http://localhost:9997",
        capabilities=["insurance-info"]
    ))
    
    # Create router
    router = ProcodeAgentRouter(use_llm=False, enable_a2a=True)
    
    # Test routing
    # ... create mock context and event queue ...
    # ... assert correct routing ...

@pytest.mark.asyncio
async def test_route_to_weather_agent():
    # Similar test for weather agent
    pass
```

## Monitoring and Observability

### Metrics to Track

1. **Routing Metrics**:
   - Internal vs External routing ratio
   - Per-agent request count
   - External agent response times
   - External agent error rates

2. **Classification Metrics**:
   - Intent distribution (tickets, account, insurance, weather, etc.)
   - LLM vs deterministic classification ratio
   - Classification confidence scores

### Logging

Add structured logging for external routing:

```python
async def _route_to_external_agent(self, intent: str, text: str, context: RequestContext) -> str:
    logger.info(
        "Routing to external agent",
        extra={
            "intent": intent,
            "agent_name": agent_name,
            "user_query": text[:100],  # Truncate for privacy
            "conversation_id": conversation_id
        }
    )
    
    # ... routing logic ...
    
    logger.info(
        "External agent response received",
        extra={
            "intent": intent,
            "agent_name": agent_name,
            "response_length": len(result),
            "duration_ms": duration
        }
    )
```

## Error Handling

### Fallback Strategy

When external agent is unavailable:

```python
async def _route_to_external_agent(self, intent: str, text: str, context: RequestContext) -> str:
    try:
        # Try external agent
        result = await client.delegate_task(text, task_id)
        return result
    
    except AgentCommunicationError as e:
        # Log error
        logger.error(f"External agent communication failed: {e}")
        
        # Fallback to helpful message
        fallback_messages = {
            "insurance": "The insurance service is currently unavailable. Please try again later or contact support.",
            "weather": "The weather service is currently unavailable. You can check weather.com for current conditions."
        }
        
        return f"⚠️ {fallback_messages.get(intent, 'External service unavailable')}"
```

### Circuit Breaker Pattern

Implement circuit breaker to prevent cascading failures:

```python
from security.circuit_breaker import CircuitBreaker

class ProcodeAgentRouter(AgentExecutor):
    def __init__(self, ...):
        # ... existing init ...
        
        # Circuit breakers for external agents
        self.circuit_breakers = {
            "insurance_agent": CircuitBreaker(failure_threshold=5, timeout=60),
            "weather_agent": CircuitBreaker(failure_threshold=5, timeout=60)
        }
    
    async def _route_to_external_agent(self, intent: str, text: str, context: RequestContext) -> str:
        agent_name = intent_to_agent.get(intent)
        circuit_breaker = self.circuit_breakers.get(agent_name)
        
        if circuit_breaker and circuit_breaker.is_open():
            return f"⚠️ {agent_name} is temporarily unavailable (circuit breaker open)"
        
        try:
            result = await client.delegate_task(text, task_id)
            if circuit_breaker:
                circuit_breaker.record_success()
            return result
        
        except Exception as e:
            if circuit_breaker:
                circuit_breaker.record_failure()
            raise
```

## Migration Path

### Phase 1: Add Intent Types (Week 1)
- [ ] Update [`IntentClassifier`](../core/intent_classifier.py:8) with new intent types
- [ ] Add deterministic patterns for insurance and weather
- [ ] Update LLM prompts
- [ ] Add unit tests

### Phase 2: Implement Routing (Week 1)
- [ ] Add [`_route_to_external_agent()`](../core/agent_router.py:20) method
- [ ] Update [`execute()`](../core/agent_router.py:66) to handle external intents
- [ ] Add configuration file support
- [ ] Add integration tests

### Phase 3: Deploy External Agents (Week 2)
- [ ] Build Insurance Agent (see [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md))
- [ ] Build Weather Agent
- [ ] Create Docker images
- [ ] Update docker-compose.yml

### Phase 4: Testing & Monitoring (Week 2)
- [ ] End-to-end testing
- [ ] Load testing
- [ ] Add monitoring dashboards
- [ ] Document usage

## Example Usage

### User Queries

```bash
# Insurance queries (routed to Insurance Agent on 9997)
"I need to check my insurance policy"
"What's my coverage for auto insurance?"
"Create a new life insurance policy"

# Weather queries (routed to Weather Agent on 9996)
"What's the weather in Melbourne?"
"Show me the 7-day forecast for Sydney"
"Are there any weather alerts?"

# Internal queries (routed to internal agents)
"Create a support ticket"
"What's my account balance?"
"I want to make a payment"
```

### API Examples

```bash
# Test insurance routing
curl -X POST http://localhost:9998/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my insurance coverage?",
    "task_id": "test-123"
  }'

# Test weather routing
curl -X POST http://localhost:9998/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather in Melbourne?",
    "task_id": "test-456"
  }'
```

## Summary

The integration strategy leverages existing A2A infrastructure in ProCode:
- ✅ [`AgentRegistry`](../a2a_comm/agent_discovery.py:60) - Already supports agent discovery
- ✅ [`AgentClient`](../a2a_comm/agent_client.py) - Already supports A2A communication
- ✅ [`_delegate_to_agent()`](../core/agent_router.py:375) - Already implements delegation

**Key Changes Needed**:
1. Extend [`IntentClassifier`](../core/intent_classifier.py:8) with external topics
2. Add [`_route_to_external_agent()`](../core/agent_router.py:20) method
3. Update routing logic in [`execute()`](../core/agent_router.py:66)
4. Create external agent configuration file
5. Update Docker Compose for deployment

This approach provides:
- 🎯 **Automatic routing** based on topic/intent
- 🔄 **Fallback strategies** for resilience
- 📊 **Monitoring** for observability
- 🧪 **Testability** at all levels
- 🚀 **Scalability** to add more external agents
