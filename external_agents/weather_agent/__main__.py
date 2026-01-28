"""
Weather Agent Entry Point

Starts the Weather Agent A2A server on port 9996.
"""

import sys
import os
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from external_agents.weather_agent.principal import WeatherPrincipal
from external_agents.shared.agent_config import AgentConfig


if __name__ == "__main__":
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = AgentConfig(config_path)
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Check for API key
    api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
    api_status = "✓ Configured" if api_key else "⚠️  Not configured (using mock data)"
    
    # Print startup information
    print("=" * 60)
    print(f"🌤️  Weather Agent Starting")
    print("=" * 60)
    print(f"Agent Name: {config.agent_name}")
    print(f"Version: {config.agent_version}")
    print(f"Port: {config.agent_port}")
    print(f"Pattern: {config.agent_pattern}")
    print(f"Capabilities: {', '.join(config.capabilities)}")
    print(f"API Key: {api_status}")
    print("=" * 60)
    if not api_key:
        print("💡 To use real weather data:")
        print("   1. Get free API key: https://openweathermap.org/api")
        print("   2. Set environment variable: OPENWEATHER_API_KEY=your_key")
        print("   3. Restart the agent")
        print("=" * 60)
    print(f"Server running on http://0.0.0.0:{config.agent_port}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Define skills
    weather_skill = AgentSkill(
        id="weather",
        name="Weather Information",
        description="Get current weather and forecasts for any location",
        tags=["weather", "forecast", "temperature"],
        examples=["What's the weather in Melbourne?", "Show me the forecast for Sydney"],
    )
    
    # Create agent card
    agent_card = AgentCard(
        name="Weather Agent",
        description="Provides real-time weather information and forecasts using OpenWeatherMap API",
        url=f"http://localhost:{config.agent_port}/",
        version=config.agent_version,
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[weather_skill],
        supports_authenticated_extended_card=False,
    )
    
    # Create principal agent
    principal = WeatherPrincipal(config_path)
    
    # Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=principal,
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    # Build and run
    app = server.build()
    uvicorn.run(app, host="0.0.0.0", port=config.agent_port)
