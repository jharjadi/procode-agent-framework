"""
Insurance Agent Entry Point

Starts the Insurance Agent A2A server on port 9997.
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
from external_agents.insurance_agent.principal import InsurancePrincipal
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
    
    # Print startup information
    print("=" * 60)
    print(f"🏥 Insurance Agent Starting")
    print("=" * 60)
    print(f"Agent Name: {config.agent_name}")
    print(f"Version: {config.agent_version}")
    print(f"Port: {config.agent_port}")
    print(f"Pattern: {config.agent_pattern}")
    print(f"Capabilities: {', '.join(config.capabilities)}")
    print("=" * 60)
    print(f"Server running on http://0.0.0.0:{config.agent_port}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Define skills
    insurance_skill = AgentSkill(
        id="insurance",
        name="Insurance Management",
        description="Manage insurance policies, get policy information, and create new policies",
        tags=["insurance", "policy", "coverage"],
        examples=["Tell me about policy POL-2024-001", "I need to create a new insurance policy"],
    )
    
    # Create agent card
    agent_card = AgentCard(
        name="Insurance Agent",
        description="Insurance policy management system with complex routing pattern",
        url=f"http://localhost:{config.agent_port}/",
        version=config.agent_version,
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[insurance_skill],
        supports_authenticated_extended_card=False,
    )
    
    # Create principal agent
    principal = InsurancePrincipal(config_path)
    
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
