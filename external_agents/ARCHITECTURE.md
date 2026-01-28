# External Agents Architecture

## Table of Contents
- [Overview](#overview)
- [Design Principles](#design-principles)
- [Agent Anatomy](#agent-anatomy)
- [Communication Patterns](#communication-patterns)
- [Routing Strategies](#routing-strategies)
- [State Management](#state-management)
- [Error Handling](#error-handling)
- [Scaling Considerations](#scaling-considerations)
- [Security](#security)

## Overview

External agents are independent, specialized services that extend the ProCode Agent Framework through the A2A (Agent-to-Agent) protocol. Each external agent is a complete agent system with its own Principal Agent and Task Agents.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ProCode Agent (Main)                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Principal Agent                                    │    │
│  │  - Intent Classification                            │    │
│  │  - Routing Logic                                    │    │
│  └────────────────────────────────────────────────────┘    │
│         │                                                    │
│         ├─► Tickets Agent (Internal)                        │
│         ├─► Account Agent (Internal)                        │
│         ├─► Payments Agent (Internal)                       │
│         │                                                    │
│         └─► A2A Client ──────────────────────────────────┐  │
└─────────────────────────────────────────────────────────│──┘
                                                          │
                    ┌─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┬─────────────────────┐
    │               │               │                     │
    ▼               ▼               ▼                     ▼
┌─────────┐   ┌─────────┐   ┌─────────┐         ┌─────────┐
│Translation│   │Analytics│   │Compliance│   ...   │Custom  │
│  Agent   │   │  Agent  │   │  Agent  │         │ Agent  │
└─────────┘   └─────────┘   └─────────┘         └─────────┘
     │             │             │                     │
     ▼             ▼             ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│  External Agent Structure (Each)                         │
│  ┌────────────────────────────────────────────────┐    │
│  │  Principal Agent                                │    │
│  │  - Receives A2A requests                        │    │
│  │  - Routes to task agents                        │    │
│  │  - Aggregates responses                         │    │
│  └────────────────────────────────────────────────┘    │
│         │                                                │
│         ├─► Task Agent 1 (Specialized)                  │
│         ├─► Task Agent 2 (Specialized)                  │
│         └─► Task Agent 3 (Specialized)                  │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Single Responsibility
Each external agent focuses on ONE domain:
- **Translation Agent**: Language services only
- **Analytics Agent**: Data analysis only
- **Compliance Agent**: Security and compliance only

### 2. Loose Coupling
- Agents communicate only via A2A protocol
- No shared database or state
- Independent deployment and scaling
- Version independence

### 3. High Cohesion
- Related tasks grouped in same agent
- Shared utilities within agent
- Consistent error handling
- Unified configuration

### 4. Fail-Safe
- Graceful degradation
- Circuit breakers
- Retry logic
- Fallback strategies

### 5. Observable
- Health checks
- Metrics endpoints
- Structured logging
- Distributed tracing

## Agent Anatomy

### Principal Agent

The Principal Agent is the entry point and orchestrator for each external agent.

**Responsibilities:**
1. **Request Reception**: Receive A2A requests from ProCode
2. **Intent Classification**: Determine which task agent to use
3. **Task Routing**: Delegate to appropriate task agent
4. **Response Aggregation**: Combine results from multiple tasks
5. **Error Handling**: Manage failures and retries

**Example Structure:**
```python
class TranslationPrincipal(AgentExecutor):
    def __init__(self):
        self.task_agents = {
            'translate': TranslateTask(),
            'detect': DetectLanguageTask(),
            'transliterate': TransliterateTask()
        }
    
    async def execute(self, context, event_queue):
        # 1. Parse request
        intent = self.classify_intent(context.message)
        
        # 2. Route to task agent
        task_agent = self.task_agents.get(intent)
        
        # 3. Execute task
        result = await task_agent.execute(context, event_queue)
        
        # 4. Return response
        return result
```

### Task Agents

Task Agents are specialized handlers for specific operations.

**Characteristics:**
- **Focused**: One task, one responsibility
- **Stateless**: No persistent state between requests
- **Reusable**: Can be called multiple times
- **Testable**: Easy to unit test in isolation

**Example Structure:**
```python
class TranslateTask(AgentExecutor):
    async def execute(self, context, event_queue):
        # 1. Extract parameters
        text = self.extract_text(context.message)
        target_lang = self.extract_language(context.message)
        
        # 2. Perform translation
        translated = await self.translate(text, target_lang)
        
        # 3. Send response
        await event_queue.enqueue_event(
            new_agent_text_message(translated)
        )
```

### Configuration

Each agent has a `config.yaml` file:

```yaml
agent:
  name: translation_agent
  version: 1.0.0
  port: 9997
  
capabilities:
  - translation
  - language-detection
  - transliteration

routing:
  default_task: translate
  intent_keywords:
    translate: ["translate", "translation", "convert"]
    detect: ["detect", "identify", "language"]
    transliterate: ["transliterate", "romanize"]

resources:
  max_concurrent_requests: 100
  timeout_seconds: 30
  
security:
  enable_api_key_auth: false
  enable_rate_limiting: true
  rate_limit_per_minute: 60

logging:
  level: INFO
  format: json
  output: stdout
```

## Communication Patterns

### 1. Request-Response (Synchronous)

**Use Case**: Simple, immediate operations

```
ProCode Agent → Translation Agent
    Request: "Translate 'Hello' to Spanish"
    ↓
Translation Agent processes
    ↓
Translation Agent → ProCode Agent
    Response: "Hola"
```

**Implementation:**
```python
# ProCode side
client = AgentClient("http://translation-agent:9997")
response = await client.send_text("Translate 'Hello' to Spanish")
```

### 2. Fire-and-Forget (Asynchronous)

**Use Case**: Long-running operations, logging, analytics

```
ProCode Agent → Analytics Agent
    Request: "Analyze this dataset"
    ↓
ProCode continues processing
    ↓
Analytics Agent processes in background
    ↓
Analytics Agent → Callback URL (optional)
    Result: Analysis complete
```

### 3. Streaming (Real-time)

**Use Case**: Progressive results, large data

```
ProCode Agent → Translation Agent
    Request: "Translate this document"
    ↓
Translation Agent → ProCode Agent
    Chunk 1: "First paragraph..."
    Chunk 2: "Second paragraph..."
    Chunk 3: "Third paragraph..."
    Complete: Done
```

### 4. Multi-Agent Orchestration

**Use Case**: Complex workflows requiring multiple agents

```
ProCode Principal
    ↓
    ├─► Translation Agent (parallel)
    ├─► Analytics Agent (parallel)
    └─► Compliance Agent (parallel)
    ↓
Aggregate results
    ↓
Return to user
```

**Implementation:**
```python
orchestrator = AgentOrchestrator(registry)
result = await orchestrator.execute_parallel([
    {"agent": "translation_agent", "task": "Translate"},
    {"agent": "analytics_agent", "task": "Analyze"},
    {"agent": "compliance_agent", "task": "Check PII"}
])
```

## Routing Strategies

### 1. Keyword-Based Routing

**Simple and fast** - Match keywords in request

```python
def classify_intent(self, message):
    text = message.text.lower()
    
    if any(kw in text for kw in ['translate', 'translation']):
        return 'translate'
    elif any(kw in text for kw in ['detect', 'identify']):
        return 'detect'
    else:
        return 'default'
```

### 2. LLM-Based Routing

**Intelligent but slower** - Use LLM for classification

```python
async def classify_intent(self, message):
    prompt = f"""
    Classify this request into one of: translate, detect, transliterate
    Request: {message.text}
    Classification:
    """
    
    classification = await self.llm.complete(prompt)
    return classification.strip().lower()
```

### 3. Capability-Based Routing

**Flexible** - Route based on agent capabilities

```python
def find_capable_agent(self, required_capability):
    for agent in self.registry.agents:
        if required_capability in agent.capabilities:
            return agent
    return None
```

### 4. Load-Based Routing

**Scalable** - Route to least busy agent

```python
async def route_to_least_busy(self, agents):
    loads = await asyncio.gather(*[
        agent.get_current_load() for agent in agents
    ])
    
    min_load_idx = loads.index(min(loads))
    return agents[min_load_idx]
```

## State Management

### Stateless Design (Recommended)

External agents should be **stateless** for scalability:

```python
class TranslateTask:
    async def execute(self, context, event_queue):
        # All state comes from context
        text = context.message.text
        target_lang = context.metadata.get('target_language')
        
        # No instance variables
        # No shared state
        # Pure function
        
        result = await translate(text, target_lang)
        return result
```

### When State is Needed

If state is required, use external storage:

**Option 1: Redis**
```python
class StatefulTask:
    def __init__(self):
        self.redis = Redis()
    
    async def execute(self, context, event_queue):
        # Get state from Redis
        state = await self.redis.get(f"task:{context.task_id}")
        
        # Process
        result = await self.process(state)
        
        # Update state
        await self.redis.set(f"task:{context.task_id}", new_state)
```

**Option 2: Database**
```python
class StatefulTask:
    async def execute(self, context, event_queue):
        # Get state from database
        state = await db.get_task_state(context.task_id)
        
        # Process
        result = await self.process(state)
        
        # Update state
        await db.update_task_state(context.task_id, new_state)
```

## Error Handling

### Error Hierarchy

```python
class ExternalAgentError(Exception):
    """Base exception for external agents"""
    pass

class TaskExecutionError(ExternalAgentError):
    """Task execution failed"""
    pass

class InvalidRequestError(ExternalAgentError):
    """Invalid request format"""
    pass

class ResourceExhaustedError(ExternalAgentError):
    """Resource limits exceeded"""
    pass

class DependencyError(ExternalAgentError):
    """External dependency failed"""
    pass
```

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Task execution failed",
    "data": {
      "error_type": "TaskExecutionError",
      "details": "Translation service unavailable",
      "retry_after": 60,
      "request_id": "req-123"
    }
  },
  "id": 1
}
```

### Retry Strategy

```python
class RetryableTask:
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    async def execute_with_retry(self, context, event_queue):
        for attempt in range(self.MAX_RETRIES):
            try:
                return await self.execute(context, event_queue)
            except RetryableError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(self.RETRY_DELAY * (2 ** attempt))
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

## Scaling Considerations

### Horizontal Scaling

Run multiple instances of the same agent:

```yaml
# docker-compose.yml
services:
  translation-agent:
    image: translation-agent:latest
    deploy:
      replicas: 3
    ports:
      - "9997-9999:9997"
```

### Load Balancing

Use a load balancer (nginx, HAProxy, or cloud LB):

```nginx
upstream translation_agents {
    least_conn;
    server translation-agent-1:9997;
    server translation-agent-2:9997;
    server translation-agent-3:9997;
}

server {
    listen 9997;
    location / {
        proxy_pass http://translation_agents;
    }
}
```

### Resource Limits

Set appropriate limits:

```yaml
# docker-compose.yml
services:
  translation-agent:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Caching

Cache expensive operations:

```python
from functools import lru_cache

class TranslateTask:
    @lru_cache(maxsize=1000)
    async def translate(self, text, target_lang):
        # Expensive translation operation
        return result
```

## Security

### Authentication

Support API key authentication:

```python
class SecureAgent:
    async def authenticate(self, request):
        api_key = request.headers.get('Authorization')
        if not api_key:
            raise UnauthorizedError()
        
        # Validate API key
        if not await self.validate_api_key(api_key):
            raise UnauthorizedError()
```

### Rate Limiting

Prevent abuse:

```python
class RateLimitedAgent:
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=60
        )
    
    async def execute(self, context, event_queue):
        if not await self.rate_limiter.allow(context.client_id):
            raise RateLimitExceededError()
        
        return await self.process(context, event_queue)
```

### Input Validation

Validate all inputs:

```python
class ValidatedTask:
    def validate_input(self, message):
        if not message.text:
            raise InvalidRequestError("Text is required")
        
        if len(message.text) > 10000:
            raise InvalidRequestError("Text too long")
        
        # Sanitize input
        return self.sanitize(message.text)
```

## Best Practices

1. **Keep agents focused** - One domain per agent
2. **Design for failure** - Assume dependencies will fail
3. **Make agents stateless** - Use external storage for state
4. **Implement health checks** - Monitor agent health
5. **Log everything** - Structured logging for debugging
6. **Version your APIs** - Support backward compatibility
7. **Document thoroughly** - Clear API documentation
8. **Test extensively** - Unit, integration, and load tests
9. **Monitor performance** - Track latency and throughput
10. **Plan for scale** - Design for horizontal scaling

## Next Steps

- Review [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for implementation details
- Check agent-specific READMEs for examples
- See [../docs/A2A_COMMUNICATION.md](../docs/A2A_COMMUNICATION.md) for A2A protocol details
