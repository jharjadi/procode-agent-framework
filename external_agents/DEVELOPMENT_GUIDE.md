# External Agents Development Guide

Complete guide for creating, testing, and deploying external agents for the ProCode Agent Framework.

## Table of Contents
- [Getting Started](#getting-started)
- [Creating a New Agent](#creating-a-new-agent)
- [Agent Structure](#agent-structure)
- [Implementing Task Agents](#implementing-task-agents)
- [Configuration](#configuration)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- ProCode Agent Framework installed
- Basic understanding of A2A protocol

### Development Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/procode-agent-framework.git
cd procode-agent-framework

# 2. Install dependencies
pip install -e .

# 3. Start ProCode Agent
make start

# 4. In another terminal, navigate to external agents
cd external_agents
```

## Creating a New Agent

### Option 1: Use the Template Generator (Recommended)

```bash
# Generate a new agent from template
python templates/create_agent.py \
  --name weather_agent \
  --port 9994 \
  --capabilities "weather,forecast,alerts"

# This creates:
# external_agents/weather_agent/
#   ├── README.md
#   ├── __init__.py
#   ├── __main__.py
#   ├── principal.py
#   ├── config.yaml
#   ├── Dockerfile
#   ├── requirements.txt
#   └── tasks/
#       ├── __init__.py
#       └── task_example.py
```

### Option 2: Manual Creation

```bash
# Create directory structure
mkdir -p external_agents/weather_agent/tasks
cd external_agents/weather_agent

# Create files
touch __init__.py __main__.py principal.py config.yaml Dockerfile
touch tasks/__init__.py tasks/task_get_weather.py
```

## Agent Structure

### Minimal Agent Structure

```
weather_agent/
├── __init__.py              # Package initialization
├── __main__.py             # Entry point
├── principal.py            # Principal agent (routing)
├── config.yaml            # Configuration
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── README.md             # Agent documentation
└── tasks/                # Task agents
    ├── __init__.py
    ├── task_get_weather.py
    ├── task_get_forecast.py
    └── task_get_alerts.py
```

### Complete Agent Structure (Production)

```
weather_agent/
├── __init__.py
├── __main__.py
├── principal.py
├── config.yaml
├── Dockerfile
├── requirements.txt
├── README.md
├── tasks/                 # Task implementations
│   ├── __init__.py
│   ├── task_get_weather.py
│   ├── task_get_forecast.py
│   └── task_get_alerts.py
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── api_client.py
│   └── formatters.py
├── models/                # Data models
│   ├── __init__.py
│   └── weather_models.py
├── tests/                 # Tests
│   ├── __init__.py
│   ├── test_principal.py
│   ├── test_tasks.py
│   └── test_integration.py
└── docs/                  # Additional docs
    └── API.md
```

## Implementing the Principal Agent

### Basic Principal Agent

```python
# principal.py
from a2a.server.agent_execution import AgentExecutor, RequestContext, EventQueue
from a2a.types import new_agent_text_message
from typing import Dict
import re

class WeatherPrincipal(AgentExecutor):
    """
    Principal agent for weather services.
    Routes requests to appropriate task agents.
    """
    
    def __init__(self):
        # Import task agents
        from tasks.task_get_weather import GetWeatherTask
        from tasks.task_get_forecast import GetForecastTask
        from tasks.task_get_alerts import GetAlertsTask
        
        # Register task agents
        self.task_agents: Dict[str, AgentExecutor] = {
            'weather': GetWeatherTask(),
            'forecast': GetForecastTask(),
            'alerts': GetAlertsTask()
        }
        
        # Default task
        self.default_task = 'weather'
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the principal agent logic.
        
        Args:
            context: Request context containing the message
            event_queue: Event queue for sending responses
        """
        try:
            # 1. Extract text from message
            text = self._extract_text(context.message)
            
            # 2. Classify intent
            intent = self._classify_intent(text)
            
            # 3. Get appropriate task agent
            task_agent = self.task_agents.get(intent, self.task_agents[self.default_task])
            
            # 4. Delegate to task agent
            await task_agent.execute(context, event_queue)
            
        except Exception as e:
            # Send error response
            error_msg = f"Error processing request: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_msg))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation requests."""
        await event_queue.enqueue_event(
            new_agent_text_message("Operation cancelled")
        )
    
    def _extract_text(self, message) -> str:
        """Extract text from message parts."""
        texts = []
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    texts.append(part.root.text)
                elif hasattr(part, 'text'):
                    texts.append(part.text)
                elif isinstance(part, dict) and 'text' in part:
                    texts.append(part['text'])
        return " ".join(texts) if texts else ""
    
    def _classify_intent(self, text: str) -> str:
        """
        Classify user intent from text.
        
        Simple keyword-based classification.
        For production, consider using LLM-based classification.
        """
        text_lower = text.lower()
        
        # Check for forecast keywords
        if any(kw in text_lower for kw in ['forecast', 'tomorrow', 'next week', 'upcoming']):
            return 'forecast'
        
        # Check for alerts keywords
        if any(kw in text_lower for kw in ['alert', 'warning', 'severe', 'storm']):
            return 'alerts'
        
        # Default to current weather
        return 'weather'
```

### Advanced Principal with LLM Classification

```python
# principal.py (advanced)
from core.multi_llm_classifier import MultiLLMClassifier

class WeatherPrincipal(AgentExecutor):
    def __init__(self):
        self.task_agents = {...}
        self.classifier = MultiLLMClassifier()
    
    async def _classify_intent(self, text: str) -> str:
        """Use LLM for intelligent intent classification."""
        prompt = f"""
        Classify this weather-related request into one of:
        - weather: Current weather conditions
        - forecast: Future weather predictions
        - alerts: Weather warnings and alerts
        
        Request: {text}
        
        Classification (one word):
        """
        
        result = await self.classifier.classify(prompt)
        intent = result.strip().lower()
        
        # Validate intent
        if intent in self.task_agents:
            return intent
        return 'weather'  # default
```

## Implementing Task Agents

### Basic Task Agent

```python
# tasks/task_get_weather.py
from a2a.server.agent_execution import AgentExecutor, RequestContext, EventQueue
from a2a.types import new_agent_text_message
import httpx
import json

class GetWeatherTask(AgentExecutor):
    """
    Task agent for getting current weather.
    """
    
    def __init__(self):
        self.api_url = "https://api.weather.com/v1/current"
        self.api_key = os.getenv("WEATHER_API_KEY")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Get current weather for a location.
        
        Expected message format:
        "What's the weather in San Francisco?"
        """
        try:
            # 1. Extract location from message
            text = self._extract_text(context.message)
            location = self._extract_location(text)
            
            if not location:
                await event_queue.enqueue_event(
                    new_agent_text_message("Please specify a location")
                )
                return
            
            # 2. Fetch weather data
            weather_data = await self._fetch_weather(location)
            
            # 3. Format response
            response = self._format_response(weather_data)
            
            # 4. Send response
            await event_queue.enqueue_event(
                new_agent_text_message(response)
            )
            
        except Exception as e:
            error_msg = f"Failed to get weather: {str(e)}"
            await event_queue.enqueue_event(
                new_agent_text_message(error_msg)
            )
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation."""
        await event_queue.enqueue_event(
            new_agent_text_message("Weather request cancelled")
        )
    
    def _extract_text(self, message) -> str:
        """Extract text from message."""
        texts = []
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'text'):
                    texts.append(part.text)
                elif hasattr(part, 'root') and hasattr(part.root, 'text'):
                    texts.append(part.root.text)
        return " ".join(texts)
    
    def _extract_location(self, text: str) -> str:
        """
        Extract location from text.
        Simple implementation - for production, use NER or LLM.
        """
        # Look for common patterns
        import re
        
        # Pattern: "weather in LOCATION"
        match = re.search(r'(?:in|for|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if match:
            return match.group(1)
        
        # Pattern: "LOCATION weather"
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+weather', text)
        if match:
            return match.group(1)
        
        return None
    
    async def _fetch_weather(self, location: str) -> dict:
        """Fetch weather data from API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.api_url,
                params={
                    'location': location,
                    'apikey': self.api_key
                }
            )
            response.raise_for_status()
            return response.json()
    
    def _format_response(self, data: dict) -> str:
        """Format weather data into human-readable text."""
        temp = data.get('temperature', 'N/A')
        condition = data.get('condition', 'N/A')
        humidity = data.get('humidity', 'N/A')
        
        return f"""
Current Weather:
🌡️ Temperature: {temp}°F
☁️ Condition: {condition}
💧 Humidity: {humidity}%
        """.strip()
```

### Task Agent with Streaming

```python
# tasks/task_get_forecast.py
class GetForecastTask(AgentExecutor):
    """Task agent that streams forecast data."""
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Stream forecast data day by day."""
        location = self._extract_location(context.message)
        forecast_data = await self._fetch_forecast(location)
        
        # Stream each day's forecast
        for day in forecast_data['days']:
            message = f"""
📅 {day['date']}
🌡️ High: {day['high']}°F, Low: {day['low']}°F
☁️ {day['condition']}
            """.strip()
            
            await event_queue.enqueue_event(
                new_agent_text_message(message)
            )
            
            # Small delay between messages
            await asyncio.sleep(0.5)
```

## Configuration

### config.yaml Structure

```yaml
# config.yaml
agent:
  name: weather_agent
  version: 1.0.0
  description: "Weather information and forecasts"
  port: 9994
  host: "0.0.0.0"

capabilities:
  - weather
  - forecast
  - alerts

routing:
  default_task: weather
  intent_keywords:
    weather: ["weather", "temperature", "current", "now"]
    forecast: ["forecast", "tomorrow", "next week", "upcoming"]
    alerts: ["alert", "warning", "severe", "storm"]

external_apis:
  weather_api:
    url: "https://api.weather.com/v1"
    timeout: 10
    retry_attempts: 3

resources:
  max_concurrent_requests: 100
  request_timeout_seconds: 30
  memory_limit_mb: 512

security:
  enable_api_key_auth: false
  enable_rate_limiting: true
  rate_limit_per_minute: 60
  allowed_origins:
    - "http://localhost:9998"
    - "https://procode-agent.example.com"

logging:
  level: INFO
  format: json
  output: stdout
  include_request_id: true

monitoring:
  enable_metrics: true
  metrics_port: 9095
  health_check_interval: 30
```

### Loading Configuration

```python
# utils/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

class AgentConfig:
    """Configuration manager for external agents."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    @property
    def agent_name(self) -> str:
        return self.get('agent.name', 'unknown_agent')
    
    @property
    def port(self) -> int:
        return self.get('agent.port', 9999)
    
    @property
    def capabilities(self) -> list:
        return self.get('capabilities', [])
```

## Testing

### Unit Tests

```python
# tests/test_tasks.py
import pytest
from tasks.task_get_weather import GetWeatherTask
from a2a.types import Message, TextPart

@pytest.mark.asyncio
async def test_get_weather_task():
    """Test weather task execution."""
    # Create task
    task = GetWeatherTask()
    
    # Create mock context
    message = Message(
        role="user",
        parts=[TextPart(text="What's the weather in San Francisco?")],
        messageId="test-123"
    )
    
    class MockContext:
        def __init__(self, message):
            self.message = message
            self.task_id = "test-task"
    
    class MockEventQueue:
        def __init__(self):
            self.events = []
        
        async def enqueue_event(self, event):
            self.events.append(event)
    
    context = MockContext(message)
    event_queue = MockEventQueue()
    
    # Execute task
    await task.execute(context, event_queue)
    
    # Verify response
    assert len(event_queue.events) > 0
    assert "temperature" in str(event_queue.events[0]).lower()
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from a2a_comm.agent_client import AgentClient

@pytest.mark.asyncio
async def test_weather_agent_integration():
    """Test full integration with weather agent."""
    # Create client
    client = AgentClient("http://localhost:9994")
    
    # Send request
    response = await client.send_text("What's the weather in New York?")
    
    # Verify response
    assert response is not None
    assert "temperature" in response.lower()

@pytest.mark.asyncio
async def test_multi_agent_workflow():
    """Test workflow involving multiple agents."""
    from a2a_comm.agent_orchestrator import AgentOrchestrator
    from a2a_comm.agent_discovery import AgentRegistry
    
    # Setup
    registry = AgentRegistry()
    orchestrator = AgentOrchestrator(registry)
    
    # Execute workflow
    result = await orchestrator.execute_parallel([
        {"agent": "weather_agent", "task": "Get weather for NYC"},
        {"agent": "translation_agent", "task": "Translate to Spanish"}
    ])
    
    # Verify
    assert len(result.steps) == 2
    assert all(step.status == "completed" for step in result.steps)
```

### Load Tests

```python
# tests/test_load.py
import asyncio
import pytest
from a2a_comm.agent_client import AgentClient

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test agent under load."""
    client = AgentClient("http://localhost:9994")
    
    # Send 100 concurrent requests
    tasks = [
        client.send_text(f"Weather request {i}")
        for i in range(100)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) >= 95  # 95% success rate
```

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Expose port
EXPOSE 9994

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:9994/health')"

# Run agent
CMD ["python", "__main__.py"]
```

### docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  weather-agent:
    build: .
    container_name: weather-agent
    ports:
      - "9994:9994"
    environment:
      - WEATHER_API_KEY=${WEATHER_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - procode-network

networks:
  procode-network:
    external: true
```

## Best Practices

### 1. Error Handling

```python
# Always handle errors gracefully
try:
    result = await self.process(data)
except ExternalAPIError as e:
    # Log error
    logger.error(f"API error: {e}")
    # Return user-friendly message
    return "Service temporarily unavailable"
except ValidationError as e:
    # Return specific error
    return f"Invalid input: {e}"
```

### 2. Logging

```python
# Use structured logging
import logging
import json

logger = logging.getLogger(__name__)

logger.info("Processing request", extra={
    "request_id": context.task_id,
    "agent": "weather_agent",
    "task": "get_weather",
    "location": location
})
```

### 3. Metrics

```python
# Track metrics
from prometheus_client import Counter, Histogram

request_counter = Counter('weather_requests_total', 'Total requests')
request_duration = Histogram('weather_request_duration_seconds', 'Request duration')

@request_duration.time()
async def execute(self, context, event_queue):
    request_counter.inc()
    # ... process request
```

### 4. Validation

```python
# Validate all inputs
def validate_location(self, location: str) -> bool:
    if not location:
        return False
    if len(location) > 100:
        return False
    if not re.match(r'^[a-zA-Z\s]+$', location):
        return False
    return True
```

### 5. Documentation

```python
# Document everything
class GetWeatherTask(AgentExecutor):
    """
    Get current weather for a location.
    
    Capabilities:
        - Current temperature
        - Weather conditions
        - Humidity levels
    
    Input Format:
        "What's the weather in [LOCATION]?"
        "Weather for [LOCATION]"
        "[LOCATION] weather"
    
    Output Format:
        Temperature: XX°F
        Condition: [sunny/cloudy/rainy/etc]
        Humidity: XX%
    
    Errors:
        - InvalidLocationError: Location not found
        - APIError: Weather service unavailable
    """
```

## Troubleshooting

### Common Issues

**Issue: Agent not responding**
```bash
# Check if agent is running
docker ps | grep weather-agent

# Check logs
docker logs weather-agent

# Check health endpoint
curl http://localhost:9994/health
```

**Issue: A2A communication failing**
```bash
# Test connectivity
curl -X POST http://localhost:9994/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"kind":"text","text":"test"}]}},"id":1}'

# Check network
docker network inspect procode-network
```

**Issue: High latency**
```python
# Add timing logs
import time

start = time.time()
result = await self.process(data)
duration = time.time() - start
logger.info(f"Processing took {duration:.2f}s")
```

## Next Steps

1. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design patterns
2. Check example agents in this directory
3. Run the test suite
4. Deploy your first agent
5. Monitor and iterate

## Resources

- [A2A Protocol Specification](../docs/A2A_COMMUNICATION.md)
- [ProCode Agent Documentation](../docs/)
- [Python AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
