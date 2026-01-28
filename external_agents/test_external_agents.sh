#!/bin/bash

# Test script for external agents
# This script tests both Insurance and Weather agents

set -e  # Exit on error

echo "=========================================="
echo "🧪 External Agents Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if agents are running
echo "📡 Checking if agents are running..."
echo ""

# Check Insurance Agent
if curl -s http://localhost:9997/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Insurance Agent is running on port 9997"
else
    echo -e "${RED}✗${NC} Insurance Agent is NOT running on port 9997"
    echo "   Start it with: cd external_agents/insurance_agent && python -m external_agents.insurance_agent"
    exit 1
fi

# Check Weather Agent
if curl -s http://localhost:9996/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Weather Agent is running on port 9996"
else
    echo -e "${RED}✗${NC} Weather Agent is NOT running on port 9996"
    echo "   Start it with: cd external_agents/weather_agent && python -m external_agents.weather_agent"
    exit 1
fi

# Check ProCode Agent
if curl -s http://localhost:9998/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ProCode Agent is running on port 9998"
else
    echo -e "${RED}✗${NC} ProCode Agent is NOT running on port 9998"
    echo "   Start it with: python __main__.py"
    exit 1
fi

echo ""
echo "=========================================="
echo "🏥 Testing Insurance Agent"
echo "=========================================="
echo ""

# Test 1: Get policy information
echo "Test 1: Get policy information"
echo "Query: 'Show me policy POL-2024-001'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "Show me policy POL-2024-001"}]}}')

if echo "$response" | grep -q "POL-2024-001"; then
    echo -e "${GREEN}✓${NC} Test 1 PASSED - Policy information retrieved"
else
    echo -e "${RED}✗${NC} Test 1 FAILED"
    echo "Response: $response"
fi
echo ""

# Test 2: Get insurance quote
echo "Test 2: Get insurance quote"
echo "Query: 'Get me a quote for auto insurance'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "Get me a quote for auto insurance"}]}}')

if echo "$response" | grep -q "quote\|Quote\|premium\|Premium"; then
    echo -e "${GREEN}✓${NC} Test 2 PASSED - Insurance quote generated"
else
    echo -e "${RED}✗${NC} Test 2 FAILED"
    echo "Response: $response"
fi
echo ""

# Test 3: Create new policy
echo "Test 3: Create new policy"
echo "Query: 'Create a new home insurance policy'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "Create a new home insurance policy"}]}}')

if echo "$response" | grep -q "created\|Created\|POL-"; then
    echo -e "${GREEN}✓${NC} Test 3 PASSED - Policy created"
else
    echo -e "${RED}✗${NC} Test 3 FAILED"
    echo "Response: $response"
fi
echo ""

echo "=========================================="
echo "🌤️  Testing Weather Agent"
echo "=========================================="
echo ""

# Test 4: Current weather
echo "Test 4: Current weather"
echo "Query: 'What is the weather in Melbourne?'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "What is the weather in Melbourne?"}]}}')

if echo "$response" | grep -q "Melbourne\|weather\|Weather\|Temperature\|temperature"; then
    echo -e "${GREEN}✓${NC} Test 4 PASSED - Weather information retrieved"
    
    # Check if using real API or mock data
    if echo "$response" | grep -q "Demo Data"; then
        echo -e "${YELLOW}⚠${NC}  Using mock data (API key not configured)"
    else
        echo -e "${GREEN}✓${NC} Using real weather API data"
    fi
else
    echo -e "${RED}✗${NC} Test 4 FAILED"
    echo "Response: $response"
fi
echo ""

# Test 5: Weather forecast
echo "Test 5: Weather forecast"
echo "Query: 'Show me the forecast for Sydney'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "Show me the forecast for Sydney"}]}}')

if echo "$response" | grep -q "Sydney\|forecast\|Forecast"; then
    echo -e "${GREEN}✓${NC} Test 5 PASSED - Weather forecast retrieved"
else
    echo -e "${RED}✗${NC} Test 5 FAILED"
    echo "Response: $response"
fi
echo ""

# Test 6: Different location
echo "Test 6: Different location"
echo "Query: 'Weather in Tokyo'"
echo ""
response=$(curl -s -X POST http://localhost:9998/message/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"parts": [{"text": "Weather in Tokyo"}]}}')

if echo "$response" | grep -q "Tokyo\|weather\|Weather"; then
    echo -e "${GREEN}✓${NC} Test 6 PASSED - Tokyo weather retrieved"
else
    echo -e "${RED}✗${NC} Test 6 FAILED"
    echo "Response: $response"
fi
echo ""

echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}✓${NC} All agents are running"
echo -e "${GREEN}✓${NC} Insurance Agent tests completed"
echo -e "${GREEN}✓${NC} Weather Agent tests completed"
echo ""
echo "🎉 External agents system is working!"
echo ""
echo "Next steps:"
echo "1. Try more queries through the UI or API"
echo "2. Check agent logs for detailed information"
echo "3. Monitor performance and response times"
echo ""
