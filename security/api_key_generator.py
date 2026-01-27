"""
API Key Generator

Generates cryptographically secure API keys with prefixes and validates key formats.
Follows OpenAI/Anthropic/Stripe API key patterns.

Key Format: pk_{environment}_{token}
- pk = "ProCode Key"
- environment = "live" or "test"
- token = 43 URL-safe base64 characters (32 bytes)

Example: pk_live_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A
"""

import secrets
import re
from typing import Dict, Literal

Environment = Literal["live", "test"]


class APIKeyGenerator:
    """Generate and validate API keys."""
    
    # Key format constants
    PREFIX = "pk"
    ENVIRONMENTS = ["live", "test"]
    TOKEN_BYTES = 32  # 32 bytes = 43 base64 characters
    
    # Regex pattern for validation
    # Format: pk_(live|test)_[A-Za-z0-9_-]{43}
    KEY_PATTERN = re.compile(r'^pk_(live|test)_[A-Za-z0-9_-]{43}$')
    
    @classmethod
    def generate_key(cls, environment: Environment = "live") -> Dict[str, str]:
        """
        Generate a new API key.
        
        Args:
            environment: Either "live" or "test"
            
        Returns:
            Dictionary containing:
            - full_key: The complete API key (show once, never store)
            - key_hash: SHA-256 hash of the key (store in database)
            - key_hint: Last 4 characters (for display)
            - key_prefix: The prefix part (pk_live_ or pk_test_)
            
        Example:
            >>> result = APIKeyGenerator.generate_key("test")
            >>> result['full_key']
            'pk_test_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A'
            >>> result['key_hint']
            '9-_A'
        """
        if environment not in cls.ENVIRONMENTS:
            raise ValueError(f"Environment must be one of {cls.ENVIRONMENTS}")
        
        # Generate cryptographically secure random token
        # token_urlsafe(32) generates 43 URL-safe base64 characters
        token = secrets.token_urlsafe(cls.TOKEN_BYTES)
        
        # Construct full key
        key_prefix = f"{cls.PREFIX}_{environment}_"
        full_key = f"{key_prefix}{token}"
        
        # Extract hint (last 4 characters of token)
        key_hint = token[-4:]
        
        # Import here to avoid circular dependency
        from security.api_key_hasher import APIKeyHasher
        key_hash = APIKeyHasher.hash_key(full_key)
        
        return {
            "full_key": full_key,
            "key_hash": key_hash,
            "key_hint": key_hint,
            "key_prefix": key_prefix,
        }
    
    @classmethod
    def validate_key_format(cls, key: str) -> bool:
        """
        Validate API key format without checking database.
        
        Args:
            key: The API key to validate
            
        Returns:
            True if format is valid, False otherwise
            
        Example:
            >>> APIKeyGenerator.validate_key_format("pk_live_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A")
            True
            >>> APIKeyGenerator.validate_key_format("invalid_key")
            False
        """
        if not key or not isinstance(key, str):
            return False
        
        return bool(cls.KEY_PATTERN.match(key))
    
    @classmethod
    def extract_environment(cls, key: str) -> str | None:
        """
        Extract environment from API key.
        
        Args:
            key: The API key
            
        Returns:
            "live" or "test" if valid, None otherwise
            
        Example:
            >>> APIKeyGenerator.extract_environment("pk_live_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A")
            'live'
        """
        if not cls.validate_key_format(key):
            return None
        
        # Extract environment from key (between first and second underscore)
        parts = key.split("_")
        if len(parts) >= 3:
            return parts[1]
        
        return None
    
    @classmethod
    def extract_prefix(cls, key: str) -> str | None:
        """
        Extract prefix from API key.
        
        Args:
            key: The API key
            
        Returns:
            Prefix (e.g., "pk_live_") if valid, None otherwise
            
        Example:
            >>> APIKeyGenerator.extract_prefix("pk_live_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A")
            'pk_live_'
        """
        if not cls.validate_key_format(key):
            return None
        
        # Extract prefix (everything before the token)
        parts = key.split("_")
        if len(parts) >= 3:
            return f"{parts[0]}_{parts[1]}_"
        
        return None


# Convenience functions
def generate_live_key() -> Dict[str, str]:
    """Generate a live environment API key."""
    return APIKeyGenerator.generate_key("live")


def generate_test_key() -> Dict[str, str]:
    """Generate a test environment API key."""
    return APIKeyGenerator.generate_key("test")


def is_valid_key_format(key: str) -> bool:
    """Check if key format is valid."""
    return APIKeyGenerator.validate_key_format(key)
