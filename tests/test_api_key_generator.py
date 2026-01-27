"""
Tests for API Key Generator

Tests key generation, format validation, and security properties.
"""

import pytest
import re
from security.api_key_generator import (
    APIKeyGenerator,
    generate_live_key,
    generate_test_key,
    is_valid_key_format
)


class TestAPIKeyGenerator:
    """Test suite for APIKeyGenerator."""
    
    def test_generate_live_key(self):
        """Test generating a live environment key."""
        result = APIKeyGenerator.generate_key("live")
        
        assert "full_key" in result
        assert "key_hash" in result
        assert "key_hint" in result
        assert "key_prefix" in result
        
        # Check prefix
        assert result["full_key"].startswith("pk_live_")
        assert result["key_prefix"] == "pk_live_"
        
        # Check key format
        assert APIKeyGenerator.validate_key_format(result["full_key"])
        
        # Check hint is last 4 chars
        token = result["full_key"].split("_")[2]
        assert result["key_hint"] == token[-4:]
        
        # Check hash length (SHA-256 = 64 hex chars)
        assert len(result["key_hash"]) == 64
    
    def test_generate_test_key(self):
        """Test generating a test environment key."""
        result = APIKeyGenerator.generate_key("test")
        
        assert result["full_key"].startswith("pk_test_")
        assert result["key_prefix"] == "pk_test_"
        assert APIKeyGenerator.validate_key_format(result["full_key"])
    
    def test_generate_key_uniqueness(self):
        """Test that generated keys are unique."""
        keys = [APIKeyGenerator.generate_key("live")["full_key"] for _ in range(100)]
        
        # All keys should be unique
        assert len(keys) == len(set(keys))
    
    def test_generate_key_invalid_environment(self):
        """Test that invalid environment raises error."""
        with pytest.raises(ValueError, match="Environment must be one of"):
            APIKeyGenerator.generate_key("invalid")
    
    def test_validate_key_format_valid(self):
        """Test validation of valid key formats."""
        # Generate a real key
        key = APIKeyGenerator.generate_key("live")["full_key"]
        assert APIKeyGenerator.validate_key_format(key)
        
        # Test both environments
        live_key = "pk_live_" + "A" * 43
        test_key = "pk_test_" + "B" * 43
        
        assert APIKeyGenerator.validate_key_format(live_key)
        assert APIKeyGenerator.validate_key_format(test_key)
    
    def test_validate_key_format_invalid(self):
        """Test validation rejects invalid formats."""
        invalid_keys = [
            "",  # Empty
            "invalid_key",  # Wrong format
            "pk_live_",  # Missing token
            "pk_live_short",  # Token too short
            "pk_prod_" + "A" * 43,  # Wrong environment
            "sk_live_" + "A" * 43,  # Wrong prefix
            "pk_live_" + "!" * 43,  # Invalid characters
            None,  # None
            123,  # Not a string
        ]
        
        for key in invalid_keys:
            assert not APIKeyGenerator.validate_key_format(key)
    
    def test_extract_environment(self):
        """Test extracting environment from key."""
        live_key = APIKeyGenerator.generate_key("live")["full_key"]
        test_key = APIKeyGenerator.generate_key("test")["full_key"]
        
        assert APIKeyGenerator.extract_environment(live_key) == "live"
        assert APIKeyGenerator.extract_environment(test_key) == "test"
        assert APIKeyGenerator.extract_environment("invalid") is None
    
    def test_extract_prefix(self):
        """Test extracting prefix from key."""
        live_key = APIKeyGenerator.generate_key("live")["full_key"]
        test_key = APIKeyGenerator.generate_key("test")["full_key"]
        
        assert APIKeyGenerator.extract_prefix(live_key) == "pk_live_"
        assert APIKeyGenerator.extract_prefix(test_key) == "pk_test_"
        assert APIKeyGenerator.extract_prefix("invalid") is None
    
    def test_key_length(self):
        """Test that generated keys have correct length."""
        key = APIKeyGenerator.generate_key("live")["full_key"]
        
        # pk_live_ (8 chars) + 43 chars token = 51 total
        assert len(key) == 51
    
    def test_key_character_set(self):
        """Test that keys use URL-safe base64 characters."""
        key = APIKeyGenerator.generate_key("live")["full_key"]
        token = key.split("_")[2]
        
        # URL-safe base64: A-Z, a-z, 0-9, -, _
        pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        assert pattern.match(token)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        live_key = generate_live_key()
        test_key = generate_test_key()
        
        assert live_key["full_key"].startswith("pk_live_")
        assert test_key["full_key"].startswith("pk_test_")
        
        assert is_valid_key_format(live_key["full_key"])
        assert is_valid_key_format(test_key["full_key"])
    
    def test_key_hint_accuracy(self):
        """Test that key hint matches actual last 4 chars."""
        result = APIKeyGenerator.generate_key("live")
        full_key = result["full_key"]
        hint = result["key_hint"]
        
        # Extract token (everything after pk_live_)
        token = full_key.split("_", 2)[2]
        
        # Hint should be last 4 chars of token
        assert hint == token[-4:]
        assert len(hint) == 4
    
    def test_hash_consistency(self):
        """Test that same key produces same hash."""
        from security.api_key_hasher import APIKeyHasher
        
        result1 = APIKeyGenerator.generate_key("live")
        key = result1["full_key"]
        hash1 = result1["key_hash"]
        
        # Hash the same key again
        hash2 = APIKeyHasher.hash_key(key)
        
        assert hash1 == hash2
    
    def test_multiple_generations_different_hashes(self):
        """Test that different keys produce different hashes."""
        result1 = APIKeyGenerator.generate_key("live")
        result2 = APIKeyGenerator.generate_key("live")
        
        assert result1["full_key"] != result2["full_key"]
        assert result1["key_hash"] != result2["key_hash"]
    
    def test_key_entropy(self):
        """Test that keys have high entropy (randomness)."""
        keys = [APIKeyGenerator.generate_key("live")["full_key"] for _ in range(10)]
        
        # Check that keys don't have obvious patterns
        for i in range(len(keys) - 1):
            # Keys should be completely different
            assert keys[i] != keys[i + 1]
            
            # Extract tokens
            token1 = keys[i].split("_")[2]
            token2 = keys[i + 1].split("_")[2]
            
            # Tokens should have low similarity
            # (simple check: count matching characters at same positions)
            matches = sum(c1 == c2 for c1, c2 in zip(token1, token2))
            similarity = matches / len(token1)
            
            # Should have less than 20% similarity (random chance ~1.5%)
            assert similarity < 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
