"""
Configuration management for external agents.

Provides a unified way to load and access agent configuration from
YAML files with environment variable overrides.
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class AgentConfig:
    """
    Configuration manager for external agents.
    
    Loads configuration from YAML files and supports environment
    variable overrides for deployment flexibility.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file.
                        If None, looks for config.yaml in current directory.
        """
        self.config_path = config_path or "config.yaml"
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )
        
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Agent name override
        if env_name := os.getenv("AGENT_NAME"):
            self.set("agent.name", env_name)
        
        # Port override
        if env_port := os.getenv("AGENT_PORT"):
            self.set("agent.port", int(env_port))
        
        # Log level override
        if env_log_level := os.getenv("LOG_LEVEL"):
            self.set("logging.level", env_log_level)
        
        # API key override (for external services)
        if env_api_key := os.getenv("EXTERNAL_API_KEY"):
            self.set("api.key", env_api_key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., "agent.name")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Examples:
            >>> config.get("agent.name")
            "insurance_agent"
            >>> config.get("agent.port", 9997)
            9997
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot notation key.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
            
        Examples:
            >>> config.set("agent.port", 9998)
        """
        keys = key.split(".")
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        Validate required configuration fields.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "agent.name",
            "agent.version",
            "agent.port"
        ]
        
        missing_fields = []
        for field in required_fields:
            if self.get(field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )
        
        return True
    
    # Convenience properties for common config values
    
    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self.get("agent.name", "unknown_agent")
    
    @property
    def agent_version(self) -> str:
        """Get agent version."""
        return self.get("agent.version", "1.0.0")
    
    @property
    def agent_port(self) -> int:
        """Get agent port."""
        return self.get("agent.port", 9999)
    
    @property
    def agent_pattern(self) -> str:
        """Get agent pattern (complex or simple)."""
        return self.get("agent.pattern", "simple")
    
    @property
    def capabilities(self) -> list:
        """Get agent capabilities."""
        return self.get("capabilities", [])
    
    @property
    def max_concurrent_requests(self) -> int:
        """Get max concurrent requests."""
        return self.get("resources.max_concurrent_requests", 100)
    
    @property
    def timeout_seconds(self) -> int:
        """Get request timeout in seconds."""
        return self.get("resources.timeout_seconds", 30)
    
    @property
    def enable_rate_limiting(self) -> bool:
        """Check if rate limiting is enabled."""
        return self.get("security.enable_rate_limiting", True)
    
    @property
    def rate_limit_per_minute(self) -> int:
        """Get rate limit per minute."""
        return self.get("security.rate_limit_per_minute", 60)
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get("logging.level", "INFO")
    
    @property
    def log_format(self) -> str:
        """Get logging format."""
        return self.get("logging.format", "json")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return self.config.copy()
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"AgentConfig(name='{self.agent_name}', port={self.agent_port})"
