# External Agents Implementation Plan

## Overview

This document outlines the complete implementation plan for the external agents system, including all files that need to be created and their contents.

**Demo Agents**:
- **Insurance Agent (Port 9997)** - Complex pattern with Principal + 2 Task Agents
- **Weather Agent (Port 9996)** - Simple pattern with Principal only

See [`DEMO_ARCHITECTURE.md`](DEMO_ARCHITECTURE.md) for detailed architecture and use cases.

## Phase 1: Foundation (Documentation Complete ✅)

### Completed Files
- ✅ `external_agents/README.md` - Quick start guide
- ✅ `external_agents/ARCHITECTURE.md` - Design patterns and principles
- ✅ `external_agents/DEVELOPMENT_GUIDE.md` - Development guide
- ✅ `external_agents/DEMO_ARCHITECTURE.md` - Demo architecture and scenarios
- ✅ `external_agents/IMPLEMENTATION_PLAN.md` - This file

## Phase 2: Shared Infrastructure

### Files to Create

#### 1. `external_agents/__init__.py`
```python
"""External Agents Package"""
__version__ = "1.0.0"

AVAILABLE_AGENTS = ["insurance_agent", "weather_agent"]
DEFAULT_PORTS = {
    "insurance_agent": 9997,
    "weather_agent": 9996
}
```

#### 2. `external_agents/shared/__init__.py`
```python
"""Shared utilities for all external agents"""
from .base_agent import BaseExternalAgent, BaseTaskAgent
from .agent_config import AgentConfig
from .agent_utils import extract_text, extract_location, format_error

__all__ = [
    'BaseExternalAgent',
    'BaseTaskAgent',
    'AgentConfig',
    'extract_text',
    'extract_location',
    'format_error'
]
```

#### 3. `external_agents/shared/base_agent.py`
**Purpose**: Base classes for all external agents

**Key Features**:
- Abstract base class for Principal Agents
- Abstract base class for Task Agents
- Common error handling
- Standard logging setup
- Health check implementation
- Metrics collection

**Methods**:
- `execute()` - Main execution method
- `cancel()` - Cancellation handler
- `_extract_text()` - Extract text from A2A message
- `_classify_intent()` - Intent classification (override in subclass)
- `health_check()` - Health check endpoint
- `get_metrics()` - Metrics endpoint

#### 4. `external_agents/shared/agent_config.py`
**Purpose**: Configuration management

**Key Features**:
- Load config from YAML
- Environment variable overrides
- Validation
- Type conversion
- Default values

**Methods**:
- `load_config()` - Load from file
- `get()` - Get config value by dot notation
- `validate()` - Validate configuration
- Properties for common config values

#### 5. `external_agents/shared/agent_utils.py`
**Purpose**: Common utility functions

**Functions**:
- `extract_text(message)` - Extract text from A2A message
- `extract_location(text)` - Extract location from text
- `extract_date(text)` - Extract date from text
- `format_error(error)` - Format error for response
- `create_response(text)` - Create A2A response message
- `validate_input(text, max_length)` - Input validation

#### 6. `external_agents/shared/middleware.py`
**Purpose**: Shared middleware components

**Components**:
- `AuthMiddleware` - API key authentication
- `RateLimitMiddleware` - Rate limiting
- `LoggingMiddleware` - Request/response logging
- `MetricsMiddleware` - Metrics collection
- `ErrorHandlerMiddleware` - Error handling

## Phase 3: Insurance Agent (Complex Pattern - Port 9997)

### Directory Structure
```
external_agents/insurance_agent/
├── README.md
├── __init__.py
├── __main__.py
├── principal.py
├── config.yaml
├── Dockerfile
├── requirements.txt
├── tasks/
│   ├── __init__.py
│   ├── task_insurance_info.py
│   └── task_insurance_creation.py
└── tests/
    ├── __init__.py
    ├── test_principal.py
    └── test_tasks.py
```

### Files to Create

#### 1. `external_agents/insurance_agent/README.md`
**Content**:
- Agent description: Insurance management system
- Capabilities: Policy information, policy creation/management
- Usage examples with curl commands
- API endpoints
- Configuration options
- Deployment instructions

#### 2. `external_agents/insurance_agent/__init__.py`
```python
"""Insurance Agent - Insurance policy management"""
from .principal import InsurancePrincipal

__version__ = "1.0.0"
__all__ = ['InsurancePrincipal']
```

#### 3. `external_agents/insurance_agent/__main__.py`
**Purpose**: Entry point for running the agent

**Key Features**:
- Load configuration
- Initialize principal agent with task routing
- Start A2A server on port 9997
- Setup logging
- Register with discovery service
- Health check endpoint

#### 4. `external_agents/insurance_agent/principal.py`
**Purpose**: Principal agent for insurance services (Router pattern)

**Inherits**: `BaseExternalAgent`

**Task Agents**:
- `InsuranceInfoTask` - Get policy details, check coverage, get quotes
- `InsuranceCreationTask` - Create, update, cancel policies

**Intent Classification**:
- Keywords: get, check, show, details, coverage, quote → InsuranceInfoTask
- Keywords: create, new, update, modify, cancel, delete → InsuranceCreationTask

**Example Code**:
```python
class InsurancePrincipal(BaseExternalAgent):
    def __init__(self):
        super().__init__()
        self.task_agents = {
            'info': InsuranceInfoTask(),
            'creation': InsuranceCreationTask()
        }
    
    async def execute(self, context, event_queue):
        intent = self._classify_intent(context.message)
        task_agent = self.task_agents.get(intent, self.task_agents['info'])
        result = await task_agent.execute(context, event_queue)
        return result
    
    def _classify_intent(self, message):
        text = self._extract_text(message).lower()
        creation_keywords = ['create', 'new', 'update', 'modify', 'cancel', 'delete']
        if any(keyword in text for keyword in creation_keywords):
            return 'creation'
        return 'info'
```

#### 5. `external_agents/insurance_agent/config.yaml`
```yaml
agent:
  name: insurance_agent
  version: 1.0.0
  port: 9997
  pattern: complex  # Principal + Task Agents

capabilities:
  - insurance-info
  - insurance-creation
  - policy-management

routing:
  default_task: info
  intent_keywords:
    info: ["get", "check", "show", "details", "coverage", "quote", "premium"]
    creation: ["create", "new", "update", "modify", "cancel", "delete"]

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
```

#### 6. `external_agents/insurance_agent/tasks/task_insurance_info.py`
**Purpose**: Handle insurance information queries

**Inherits**: `BaseTaskAgent`

**Features**:
- Get policy details by policy number
- Check coverage for specific scenarios
- Get premium quotes
- List available policies

**Methods**:
- `execute()` - Main execution logic
- `_get_policy_details()` - Fetch policy information
- `_check_coverage()` - Verify coverage
- `_get_quote()` - Calculate premium quote
- `_format_response()` - Format result

**Example Response**:
```json
{
  "policy_number": "POL-2024-001",
  "type": "Auto Insurance",
  "coverage": "$500,000",
  "premium": "$1,200/year",
  "status": "Active"
}
```

#### 7. `external_agents/insurance_agent/tasks/task_insurance_creation.py`
**Purpose**: Handle insurance policy creation and management

**Inherits**: `BaseTaskAgent`

**Features**:
- Create new insurance policy
- Update existing policy
- Cancel policy
- Validate policy data

**Methods**:
- `execute()` - Main execution logic
- `_create_policy()` - Create new policy
- `_update_policy()` - Update existing policy
- `_cancel_policy()` - Cancel policy
- `_validate_policy_data()` - Validate input
- `_format_response()` - Format result

**Example Response**:
```json
{
  "action": "created",
  "policy_number": "POL-2024-002",
  "message": "Policy created successfully",
  "next_steps": ["Review policy documents", "Set up payment"]
}
```

#### 8. `external_agents/insurance_agent/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 9997
HEALTHCHECK --interval=30s CMD python -c "import httpx; httpx.get('http://localhost:9997/health')"
CMD ["python", "__main__.py"]
```

#### 9. `external_agents/insurance_agent/requirements.txt`
```
# Core dependencies (inherited from main project)
a2a-sdk>=0.1.0
httpx>=0.24.0
pydantic>=2.0.0
pyyaml>=6.0

# Insurance-specific
# Add any insurance calculation libraries if needed
```

## Phase 4: Weather Agent (Simple Pattern - Port 9996)

### Directory Structure
```
external_agents/weather_agent/
├── README.md
├── __init__.py
├── __main__.py
├── principal.py
├── config.yaml
├── Dockerfile
├── requirements.txt
└── tests/
    ├── __init__.py
    └── test_principal.py
```

**Note**: No separate `tasks/` directory - all functionality in Principal Agent

### Files to Create

#### 1. `external_agents/weather_agent/README.md`
**Content**:
- Agent description: Weather information service
- Capabilities: Current weather, forecasts, alerts, historical data
- Usage examples with curl commands
- API endpoints
- Configuration options
- Deployment instructions

#### 2. `external_agents/weather_agent/__init__.py`
```python
"""Weather Agent - Weather information service"""
from .principal import WeatherPrincipal

__version__ = "1.0.0"
__all__ = ['WeatherPrincipal']
```

#### 3. `external_agents/weather_agent/__main__.py`
**Purpose**: Entry point for running the agent

**Key Features**:
- Load configuration
- Initialize principal agent (all-in-one)
- Start A2A server on port 9996
- Setup logging
- Register with discovery service
- Health check endpoint

#### 4. `external_agents/weather_agent/principal.py`
**Purpose**: Principal agent for weather services (All-in-one pattern)

**Inherits**: `BaseExternalAgent`

**Features** (all in Principal):
- Get current weather
- Get weather forecast
- Get weather alerts
- Get historical weather data

**Example Code**:
```python
class WeatherPrincipal(BaseExternalAgent):
    def __init__(self):
        super().__init__()
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
    
    async def execute(self, context, event_queue):
        text = self._extract_text(context.message)
        location = self._extract_location(text)
        
        # Determine what type of weather info is requested
        if 'forecast' in text.lower():
            result = await self._get_forecast(location)
        elif 'alert' in text.lower():
            result = await self._get_alerts(location)
        elif 'historical' in text.lower() or 'history' in text.lower():
            result = await self._get_historical(location)
        else:
            result = await self._get_current_weather(location)
        
        response = self._format_response(result)
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def _get_current_weather(self, location):
        # Fetch current weather from API
        pass
    
    async def _get_forecast(self, location):
        # Fetch forecast from API
        pass
    
    async def _get_alerts(self, location):
        # Fetch weather alerts from API
        pass
    
    async def _get_historical(self, location):
        # Fetch historical data from API
        pass
```

#### 5. `external_agents/weather_agent/config.yaml`
```yaml
agent:
  name: weather_agent
  version: 1.0.0
  port: 9996
  pattern: simple  # Principal only, no task agents

capabilities:
  - current-weather
  - weather-forecast
  - weather-alerts
  - historical-weather

resources:
  max_concurrent_requests: 200
  timeout_seconds: 15

security:
  enable_api_key_auth: false
  enable_rate_limiting: true
  rate_limit_per_minute: 120

logging:
  level: INFO
  format: json

weather_api:
  provider: openweathermap  # or weatherapi.com
  cache_ttl_seconds: 300  # Cache weather data for 5 minutes
```

#### 6. `external_agents/weather_agent/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 9996
HEALTHCHECK --interval=30s CMD python -c "import httpx; httpx.get('http://localhost:9996/health')"
CMD ["python", "__main__.py"]
```

#### 7. `external_agents/weather_agent/requirements.txt`
```
# Core dependencies (inherited from main project)
a2a-sdk>=0.1.0
httpx>=0.24.0
pydantic>=2.0.0
pyyaml>=6.0

# Weather-specific
# Weather API client library if needed
```

## Phase 5: Templates

### Directory Structure
```
external_agents/templates/
├── agent_template/
│   ├── README.md.template
│   ├── __init__.py.template
│   ├── __main__.py.template
│   ├── principal.py.template
│   ├── config.yaml.template
│   ├── Dockerfile.template
│   ├── requirements.txt.template
│   └── tasks/
│       └── task_example.py.template
└── create_agent.py
```

### create_agent.py
**Purpose**: Script to generate new agent from template

**Usage**:
```bash
python templates/create_agent.py \
  --name weather_agent \
  --port 9994 \
  --capabilities "weather,forecast,alerts"
```

**Features**:
- Generate complete agent structure
- Replace template variables
- Create initial files
- Setup git repository
- Generate README

## Phase 6: Docker Configuration

### Files to Create

#### 1. `external_agents/docker/docker-compose.external.yml`
```yaml
version: '3.8'

services:
  insurance-agent:
    build: ../insurance_agent
    container_name: insurance-agent
    ports:
      - "9997:9997"
    environment:
      - LOG_LEVEL=INFO
    networks:
      - procode-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:9997/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  weather-agent:
    build: ../weather_agent
    container_name: weather-agent
    ports:
      - "9996:9996"
    environment:
      - LOG_LEVEL=INFO
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    networks:
      - procode-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:9996/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  procode-network:
    external: true
```

#### 2. `external_agents/docker/Dockerfile.base`
**Purpose**: Base image for all external agents

**Features**:
- Python 3.11
- Common dependencies
- Security hardening
- Non-root user
- Health check utilities

#### 3. `external_agents/docker/.dockerignore`
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.env
.venv/
venv/
*.log
.DS_Store
```

## Phase 7: Integration Tests

### Directory Structure
```
external_agents/tests/
├── __init__.py
├── test_agent_communication.py
├── test_orchestration.py
├── test_discovery.py
├── test_load.py
└── conftest.py
```

### Test Files

#### 1. `test_agent_communication.py`
**Purpose**: Test A2A communication between agents

**Tests**:
- ProCode → Insurance Agent (Complex pattern)
- ProCode → Weather Agent (Simple pattern)
- Insurance Agent task routing
- Weather Agent direct handling
- Error handling
- Timeout handling

#### 2. `test_orchestration.py`
**Purpose**: Test multi-agent workflows

**Tests**:
- Sequential workflow (Weather → Insurance)
- Parallel workflow (Multiple weather queries)
- Conditional workflow (Check weather before insurance quote)
- Error recovery
- Fallback strategies

#### 3. `test_discovery.py`
**Purpose**: Test agent discovery

**Tests**:
- Register agent
- Find agent by name
- Find agent by capability
- Unregister agent
- Health checks

#### 4. `test_load.py`
**Purpose**: Load testing

**Tests**:
- Concurrent requests
- Sustained load
- Peak load
- Resource usage
- Response times

## Phase 8: Makefile Integration

### Add to Main Makefile

```makefile
# External Agents Commands
external-agents-build: ## Build all external agent images
	@echo "$(BLUE)Building external agent images...$(NC)"
	docker-compose -f external_agents/docker/docker-compose.external.yml build

external-agents-up: ## Start all external agents
	@echo "$(BLUE)Starting external agents...$(NC)"
	docker-compose -f external_agents/docker/docker-compose.external.yml up -d

external-agents-down: ## Stop all external agents
	@echo "$(BLUE)Stopping external agents...$(NC)"
	docker-compose -f external_agents/docker/docker-compose.external.yml down

external-agents-logs: ## Show external agent logs
	@echo "$(BLUE)Showing external agent logs...$(NC)"
	docker-compose -f external_agents/docker/docker-compose.external.yml logs -f

external-agents-test: ## Test external agents
	@echo "$(BLUE)Testing external agents...$(NC)"
	pytest external_agents/tests/ -v

external-agents-create: ## Create new external agent (use: make external-agents-create NAME=my_agent)
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: Please provide NAME$(NC)"; \
		echo "Usage: make external-agents-create NAME=my_agent"; \
		exit 1; \
	fi
	python external_agents/templates/create_agent.py --name $(NAME)
```

## Implementation Timeline

### Week 1: Foundation
- [x] Documentation (README, ARCHITECTURE, DEVELOPMENT_GUIDE, DEMO_ARCHITECTURE)
- [ ] Shared infrastructure (base classes, config, utils)
- [ ] Template generator

### Week 2: Insurance Agent (Complex Pattern)
- [ ] Principal agent with task routing
- [ ] Insurance Info Task Agent
- [ ] Insurance Creation Task Agent
- [ ] Unit tests
- [ ] Docker configuration

### Week 3: Weather Agent (Simple Pattern)
- [ ] Principal agent (all-in-one)
- [ ] Weather API integration
- [ ] Unit tests
- [ ] Docker configuration
- [ ] Integration tests

### Week 4: Polish & Demo
- [ ] Performance optimization
- [ ] Documentation review
- [ ] Demo scripts and workflows
- [ ] End-to-end testing
- [ ] Update main README

## Success Criteria

✅ **Functionality**
- All agents respond to A2A requests
- Multi-agent workflows work
- Error handling is robust
- Performance meets requirements

✅ **Quality**
- Test coverage > 80%
- All tests passing
- No critical security issues
- Documentation complete

✅ **Deployment**
- Docker images build successfully
- Agents start and register
- Health checks pass
- Monitoring works

✅ **Usability**
- Clear documentation
- Easy to create new agents
- Good developer experience
- Example code works

## Demo Use Cases

### Insurance Agent Demo
```bash
# Get policy information
curl -X POST http://localhost:9997/a2a \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me details for policy POL-2024-001"}'

# Create new policy
curl -X POST http://localhost:9997/a2a \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a new auto insurance policy for John Doe"}'
```

### Weather Agent Demo
```bash
# Get current weather
curl -X POST http://localhost:9996/a2a \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Melbourne?"}'

# Get forecast
curl -X POST http://localhost:9996/a2a \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the 7-day forecast for Sydney"}'
```

## Next Steps

1. **Switch to Code mode** to implement the shared infrastructure
2. **Create base classes** for external agents
3. **Implement Insurance Agent** (Complex pattern with task routing)
4. **Implement Weather Agent** (Simple pattern without task routing)
5. **Test integration** with ProCode Agent
6. **Create demo scripts** for both patterns
7. **Document learnings** and iterate

## Key Differences Between Patterns

### Complex Pattern (Insurance Agent)
- ✅ Principal Agent routes to Task Agents
- ✅ Demonstrates task delegation
- ✅ Shows intent classification
- ✅ Better for multi-domain functionality
- ✅ More scalable for adding new capabilities

### Simple Pattern (Weather Agent)
- ✅ Principal Agent handles everything
- ✅ Simpler architecture
- ✅ Lower latency (no routing overhead)
- ✅ Better for single-domain functionality
- ✅ Easier to maintain for simple use cases

## Notes

- Keep agents simple and focused
- Prioritize testability
- Document as you go
- Get feedback early
- Iterate based on usage
- Insurance Agent demonstrates complex routing
- Weather Agent demonstrates simple all-in-one pattern

---

**Status**: Phase 1 Complete (Documentation) ✅
**Next**: Phase 2 (Shared Infrastructure) - Switch to Code mode
