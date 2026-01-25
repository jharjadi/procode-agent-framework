"""
Agent Discovery and Registry Module

This module provides functionality for discovering and managing available agents
in the A2A ecosystem. It supports agent registration, capability-based discovery,
and configuration-based agent loading.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import os
import json
from pathlib import Path


@dataclass
class AgentCard:
    """
    Represents an agent's metadata and capabilities.
    
    Attributes:
        name: Unique identifier for the agent
        url: Base URL where the agent is accessible
        capabilities: List of capabilities the agent provides
        description: Human-readable description of the agent
        version: Agent version string
        metadata: Additional metadata about the agent
    """
    name: str
    url: str
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert agent card to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "capabilities": self.capabilities,
            "description": self.description,
            "version": self.version,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentCard":
        """Create agent card from dictionary."""
        return cls(
            name=data["name"],
            url=data["url"],
            capabilities=data.get("capabilities", []),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {})
        )


class AgentRegistry:
    """
    Registry for discovering and managing available agents.
    
    The registry supports multiple sources for agent discovery:
    - Environment variables
    - Configuration files
    - Programmatic registration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent registry.
        
        Args:
            config_path: Optional path to agent configuration file
        """
        self.agents: Dict[str, AgentCard] = {}
        self._load_agents(config_path)
    
    def _load_agents(self, config_path: Optional[str] = None):
        """
        Load agents from configuration sources.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load from environment variables
        self._load_from_env()
        
        # Load from configuration file
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            # Try default config locations
            default_paths = [
                "agents_config.json",
                "config/agents.json",
                ".agents.json"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    self._load_from_file(path)
                    break
    
    def _load_from_env(self):
        """Load agents from environment variables."""
        # Format: AGENT_<NAME>_URL=http://localhost:9999
        # Format: AGENT_<NAME>_CAPABILITIES=cap1,cap2,cap3
        env_agents = {}
        
        for key, value in os.environ.items():
            if key.startswith("AGENT_") and "_URL" in key:
                agent_name = key.replace("AGENT_", "").replace("_URL", "").lower()
                if agent_name not in env_agents:
                    env_agents[agent_name] = {"url": value}
                else:
                    env_agents[agent_name]["url"] = value
            
            elif key.startswith("AGENT_") and "_CAPABILITIES" in key:
                agent_name = key.replace("AGENT_", "").replace("_CAPABILITIES", "").lower()
                capabilities = [cap.strip() for cap in value.split(",")]
                if agent_name not in env_agents:
                    env_agents[agent_name] = {"capabilities": capabilities}
                else:
                    env_agents[agent_name]["capabilities"] = capabilities
        
        # Register agents from environment
        for name, config in env_agents.items():
            if "url" in config:
                agent_card = AgentCard(
                    name=name,
                    url=config["url"],
                    capabilities=config.get("capabilities", []),
                    description=f"Agent loaded from environment: {name}"
                )
                self.agents[name] = agent_card
    
    def _load_from_file(self, config_path: str):
        """
        Load agents from JSON configuration file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            agents_config = config.get("agents", [])
            for agent_data in agents_config:
                agent_card = AgentCard.from_dict(agent_data)
                self.agents[agent_card.name] = agent_card
        
        except Exception as e:
            print(f"Warning: Failed to load agents from {config_path}: {e}")
    
    def register_agent(self, agent_card: AgentCard):
        """
        Register a new agent in the registry.
        
        Args:
            agent_card: Agent card to register
        """
        self.agents[agent_card.name] = agent_card
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            return True
        return False
    
    def get_agent(self, agent_name: str) -> Optional[AgentCard]:
        """
        Get agent by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            AgentCard if found, None otherwise
        """
        return self.agents.get(agent_name)
    
    def find_agent(self, capability: str) -> Optional[AgentCard]:
        """
        Find first agent with specified capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            First matching AgentCard, or None if not found
        """
        for agent in self.agents.values():
            if capability in agent.capabilities:
                return agent
        return None
    
    def find_agents(self, capability: str) -> List[AgentCard]:
        """
        Find all agents with specified capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of matching AgentCards
        """
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]
    
    def list_agents(self) -> List[AgentCard]:
        """
        List all registered agents.
        
        Returns:
            List of all AgentCards
        """
        return list(self.agents.values())
    
    def list_capabilities(self) -> List[str]:
        """
        List all unique capabilities across all agents.
        
        Returns:
            List of unique capability strings
        """
        capabilities = set()
        for agent in self.agents.values():
            capabilities.update(agent.capabilities)
        return sorted(list(capabilities))
    
    def save_to_file(self, config_path: str):
        """
        Save current registry to configuration file.
        
        Args:
            config_path: Path to save configuration
        """
        config = {
            "agents": [agent.to_dict() for agent in self.agents.values()]
        }
        
        # Create directory if it doesn't exist
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self.agents)
    
    def __contains__(self, agent_name: str) -> bool:
        """Check if agent is registered."""
        return agent_name in self.agents
    
    def __repr__(self) -> str:
        """String representation of registry."""
        return f"AgentRegistry(agents={len(self.agents)})"


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_global_registry() -> AgentRegistry:
    """
    Get or create the global agent registry instance.
    
    Returns:
        Global AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def reset_global_registry():
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
