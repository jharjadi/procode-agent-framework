# External Agents Quick Start Guide

## 🚀 Quick Start

This guide will help you get the external agents (Insurance and Weather) running with ProCode in under 5 minutes.

## Prerequisites

- Python 3.11+
- ProCode Agent Framework installed
- Terminal access

## Step 1: Get Weather API Key (Optional but Recommended)

The Weather Agent works with mock data by default, but for real weather information:

1. Sign up for free at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your API key (free tier: 1000 calls/day)
3. Set environment variable:

```bash
export OPENWEATHER_API_KEY=your_api_key_here
```

## Step 2: Start the External Agents

### Terminal 1: Start Insurance Agent (Port 9997)

```bash
cd external_agents/insurance_agent
python -m external_agents.insurance_agent
```

You should see:
```
============================================================
🏥 Insurance Agent Starting
============================================================
Agent Name: insurance_agent
Version: 1.0.0
Port: 9997
Pattern: complex
Capabilities: insurance-info, insurance-creation, policy-management
============================================================
Server running on http://0.0.0.0:9997
Press Ctrl+C to stop
============================================================
```

### Terminal 2: Start Weather Agent (Port 9996)

```bash
cd external_agents/weather_agent
python -m external_agents.weather_agent
```

You should see:
```
============================================================
🌤️  Weather Agent Starting
============================================================
Agent Name: weather_agent
Version: 1.0.0
Port: 9996
Pattern: simple
Capabilities: current-weather, weather-forecast, weather-alerts, historical-weather
API Key: ✓ Configured  (or ⚠️  Not configured)
============================================================
Server running on http://0.0.0.0:9996
Press Ctrl+C to stop
============================================================
```

### Terminal 3: Start ProCode Agent (Port 9998)

```bash
# From project root
python __main__.py
```

You should see:
```
✓ Loaded external agents configuration from config/external_agents.json
```

## Step 3: Test the System

### Test Insurance Agent

Open Terminal 4 and test with curl:

```bash
# Test 1: Get policy information
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "Show me policy POL-2024-001"}]
    }
  }'

# Test 2: Get insurance quote
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "Get me a quote for auto insurance"}]
    }
  }'

# Test 3: Create new policy
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "Create a new home insurance policy"}]
    }
  }'
```

### Test Weather Agent

```bash
# Test 1: Current weather
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "What is the weather in Melbourne?"}]
    }
  }'

# Test 2: Weather forecast
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "Show me the forecast for Sydney"}]
    }
  }'

# Test 3: Different location
curl -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "parts": [{"text": "Weather in Tokyo"}]
    }
  }'
```

## Expected Results

### Insurance Agent Response Example

```json
{
  "result": {
    "parts": [
      {
        "text": "🏥 **Insurance Agent**: 📋 **Policy Details**\n\npolicy_number: POL-2024-001\ntype: Auto Insurance\nholder: John Doe\ncoverage: $500,000\npremium: $1,200/year\nstatus: Active\n..."
      }
    ]
  }
}
```

### Weather Agent Response Example

```json
{
  "result": {
    "parts": [
      {
        "text": "🌤️ **Weather Agent**: ☀️ **Current Weather in Melbourne, AU**\n\n**Conditions:** Clear Sky\n**Temperature:** 22°C (feels like 21°C)\n**Humidity:** 65%\n..."
      }
    ]
  }
}
```

## Verification Checklist

✅ **Insurance Agent**:
- [ ] Agent starts on port 9997
- [ ] Can view policy details
- [ ] Can get insurance quotes
- [ ] Can create new policies
- [ ] ProCode routes insurance queries correctly

✅ **Weather Agent**:
- [ ] Agent starts on port 9996
- [ ] Can get current weather
- [ ] Can get forecasts
- [ ] Real API data (if key configured)
- [ ] ProCode routes weather queries correctly

✅ **ProCode Integration**:
- [ ] Loads external agents config
- [ ] Intent classifier recognizes "insurance" and "weather"
- [ ] Router delegates to external agents
- [ ] Responses include agent emoji prefixes

## Troubleshooting

### Issue: "Agent not found in registry"

**Solution**: Make sure the external agent is running before starting ProCode.

```bash
# Check if agents are running
curl http://localhost:9997/health  # Insurance
curl http://localhost:9996/health  # Weather
```

### Issue: "Connection refused"

**Solution**: Verify the agent is listening on the correct port.

```bash
# Check what's running on ports
lsof -i :9997  # Insurance
lsof -i :9996  # Weather
lsof -i :9998  # ProCode
```

### Issue: Weather shows mock data

**Solution**: Set the OPENWEATHER_API_KEY environment variable and restart the Weather Agent.

```bash
export OPENWEATHER_API_KEY=your_key
cd external_agents/weather_agent
python -m external_agents.weather_agent
```

### Issue: "Module not found"

**Solution**: Make sure you're running from the correct directory and Python path is set.

```bash
# From project root
export PYTHONPATH=$PWD:$PYTHONPATH
cd external_agents/insurance_agent
python -m external_agents.insurance_agent
```

## Architecture Overview

```
User Query
    ↓
ProCode Agent (9998)
    ↓
Intent Classifier
    ↓
    ├─→ "insurance" → Insurance Agent (9997)
    │                      ↓
    │                 Principal Agent
    │                      ↓
    │         ┌────────────┴────────────┐
    │         ↓                         ↓
    │   Insurance Info Task    Insurance Creation Task
    │
    └─→ "weather" → Weather Agent (9996)
                         ↓
                    Principal Agent
                    (handles all queries)
```

## Next Steps

1. **Try More Queries**: Experiment with different insurance and weather queries
2. **Check Logs**: Monitor the terminal outputs for debugging
3. **Modify Agents**: Customize the agents for your use case
4. **Add More Agents**: Use the template to create new external agents

## Example Queries

### Insurance Queries
- "What's my insurance coverage?"
- "Show me policy POL-2024-002"
- "Get me a quote for life insurance"
- "Create a new auto insurance policy"
- "Update policy POL-2024-001"
- "Cancel my insurance"
- "List all my policies"

### Weather Queries
- "What's the weather in London?"
- "Show me the forecast for New York"
- "Is it raining in Paris?"
- "Weather in Singapore"
- "Temperature in Berlin"
- "Forecast for Los Angeles"

## Performance Tips

1. **Caching**: Weather data is cached for 5 minutes
2. **Rate Limiting**: Both agents have rate limiting enabled
3. **Concurrent Requests**: Insurance (100), Weather (200)
4. **Timeouts**: Insurance (30s), Weather (15s)

## API Keys and Configuration

### Weather API Key
- **Provider**: OpenWeatherMap
- **Free Tier**: 1,000 calls/day, 60 calls/minute
- **Sign Up**: https://openweathermap.org/api
- **Environment Variable**: `OPENWEATHER_API_KEY`

### Configuration Files
- **Insurance**: [`external_agents/insurance_agent/config.yaml`](insurance_agent/config.yaml)
- **Weather**: [`external_agents/weather_agent/config.yaml`](weather_agent/config.yaml)
- **Registry**: [`config/external_agents.json`](../config/external_agents.json)

## Support

For issues or questions:
1. Check the logs in each terminal
2. Review [`ARCHITECTURE.md`](ARCHITECTURE.md) for design details
3. See [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) for implementation details
4. Check [`ROUTING_INTEGRATION.md`](ROUTING_INTEGRATION.md) for ProCode integration

---

**Status**: ✅ Ready to Use
**Last Updated**: 2026-01-28
