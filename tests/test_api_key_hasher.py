"""
Tests for API Key Hasher

Tests hashing, verification, and timing attack resistance.
"""

import pytest
import time
from security.api_key_hasher import (
    APIKeyHasher,
    hash_api_key,
    verify_api_key
)


class TestAPIKeyHasher:
    """Test suite for APIKeyHasher."""
    
    def test_hash_key(self):
        """Test basic key hashing."""
        key = "pk_test_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A"
        hash_value = APIKeyHasher.hash_key(key)
        
        # SHA-256 produces 64 hex characters
        assert len(hash_value) == 64
        assert isinstance(hash_value, str)
        
        # Should be valid hex
        int(hash_value, 16)  # Will raise if not valid hex
    
    def test_hash_consistency(self):
        """Test that same key produces same hash."""
        key = "pk_test_consistent_key_test_123456789012345"
        
        hash1 = APIKeyHasher.hash_key(key)
        hash2 = APIKeyHasher.hash_key(key)
        hash3 = APIKeyHasher.hash_key(key)
        
        assert hash1 == hash2 == hash3
    
    def test_hash_uniqueness(self):
        """Test that different keys produce different hashes."""
        key1 = "pk_test_key1_AbCdEfGhIjKlMnOpQrStUvWxYz012345"
        key2 = "pk_test_key2_AbCdEfGhIjKlMnOpQrStUvWxYz012345"
        
        hash1 = APIKeyHasher.hash_key(key1)
        hash2 = APIKeyHasher.hash_key(key2)
        
        assert hash1 != hash2
    
    def test_hash_empty_key(self):
        """Test that empty key raises error."""
        with pytest.raises(ValueError, match="Key must be a non-empty string"):
            APIKeyHasher.hash_key("")
    
    def test_hash_none_key(self):
        """Test that None key raises error."""
        with pytest.raises(ValueError, match="Key must be a non-empty string"):
            APIKeyHasher.hash_key(None)
    
    def test_hash_non_string_key(self):
        """Test that non-string key raises error."""
        with pytest.raises(ValueError, match="Key must be a non-empty string"):
            APIKeyHasher.hash_key(123)
    
    def test_verify_key_correct(self):
        """Test verification with correct key."""
        key = "pk_test_verify_correct_key_12345678901234567"
        hash_value = APIKeyHasher.hash_key(key)
        
        assert APIKeyHasher.verify_key(key, hash_value) is True
    
    def test_verify_key_incorrect(self):
        """Test verification with incorrect key."""
        correct_key = "pk_test_correct_key_1234567890123456789012"
        wrong_key = "pk_test_wrong_key_123456789012345678901234"
        
        hash_value = APIKeyHasher.hash_key(correct_key)
        
        assert APIKeyHasher.verify_key(wrong_key, hash_value) is False
    
    def test_verify_key_empty(self):
        """Test verification with empty key."""
        hash_value = APIKeyHasher.hash_key("pk_test_some_key_1234567890123456789012345")
        
        assert APIKeyHasher.verify_key("", hash_value) is False
    
    def test_verify_key_none(self):
        """Test verification with None key."""
        hash_value = APIKeyHasher.hash_key("pk_test_some_key_1234567890123456789012345")
        
        assert APIKeyHasher.verify_key(None, hash_value) is False
    
    def test_verify_key_invalid_hash(self):
        """Test verification with invalid hash."""
        key = "pk_test_some_key_1234567890123456789012345678"
        
        assert APIKeyHasher.verify_key(key, "invalid_hash") is False
        assert APIKeyHasher.verify_key(key, "") is False
        assert APIKeyHasher.verify_key(key, None) is False
    
    def test_hash_multiple(self):
        """Test hashing multiple keys at once."""
        keys = [
            "pk_test_key1_AbCdEfGhIjKlMnOpQrStUvWxYz01234",
            "pk_test_key2_AbCdEfGhIjKlMnOpQrStUvWxYz01234",
            "pk_live_key3_AbCdEfGhIjKlMnOpQrStUvWxYz01234"
        ]
        
        hashes = APIKeyHasher.hash_multiple(keys)
        
        assert len(hashes) == 3
        assert all(key in hashes for key in keys)
        assert all(len(hash_val) == 64 for hash_val in hashes.values())
        
        # Verify each hash
        for key, hash_val in hashes.items():
            assert APIKeyHasher.verify_key(key, hash_val)
    
    def test_is_valid_hash(self):
        """Test hash format validation."""
        # Valid hash (64 hex characters)
        valid_hash = "a" * 64
        assert APIKeyHasher.is_valid_hash(valid_hash)
        
        # Valid hash with mixed hex
        valid_hash2 = "1234567890abcdef" * 4
        assert APIKeyHasher.is_valid_hash(valid_hash2)
        
        # Invalid hashes
        assert not APIKeyHasher.is_valid_hash("")  # Empty
        assert not APIKeyHasher.is_valid_hash("a" * 63)  # Too short
        assert not APIKeyHasher.is_valid_hash("a" * 65)  # Too long
        assert not APIKeyHasher.is_valid_hash("g" * 64)  # Invalid hex char
        assert not APIKeyHasher.is_valid_hash(None)  # None
        assert not APIKeyHasher.is_valid_hash(123)  # Not string
    
    def test_timing_attack_resistance(self):
        """Test that verification is timing attack resistant."""
        key = "pk_test_timing_test_key_1234567890123456789"
        hash_value = APIKeyHasher.hash_key(key)
        
        # Test with correct key
        correct_times = []
        for _ in range(100):
            start = time.perf_counter()
            APIKeyHasher.verify_key(key, hash_value)
            end = time.perf_counter()
            correct_times.append(end - start)
        
        # Test with incorrect key (same length)
        wrong_key = "pk_test_wrong_key_here_1234567890123456789"
        wrong_times = []
        for _ in range(100):
            start = time.perf_counter()
            APIKeyHasher.verify_key(wrong_key, hash_value)
            end = time.perf_counter()
            wrong_times.append(end - start)
        
        # Calculate average times
        avg_correct = sum(correct_times) / len(correct_times)
        avg_wrong = sum(wrong_times) / len(wrong_times)
        
        # Time difference should be minimal (< 10% difference)
        # This indicates constant-time comparison
        time_diff_ratio = abs(avg_correct - avg_wrong) / max(avg_correct, avg_wrong)
        
        # Allow up to 20% difference due to system variance
        assert time_diff_ratio < 0.2, f"Timing difference too large: {time_diff_ratio:.2%}"
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        key = "pk_test_convenience_test_12345678901234567890"
        
        # Test hash_api_key
        hash_value = hash_api_key(key)
        assert len(hash_value) == 64
        
        # Test verify_api_key
        assert verify_api_key(key, hash_value) is True
        assert verify_api_key("wrong_key", hash_value) is False
    
    def test_hash_deterministic(self):
        """Test that hashing is deterministic (no random salt)."""
        key = "pk_test_deterministic_test_123456789012345678"
        
        # Hash the same key multiple times
        hashes = [APIKeyHasher.hash_key(key) for _ in range(10)]
        
        # All hashes should be identical
        assert len(set(hashes)) == 1
    
    def test_hash_avalanche_effect(self):
        """Test that small changes in key produce large changes in hash."""
        key1 = "pk_test_avalanche_test_1234567890123456789012"
        key2 = "pk_test_avalanche_test_1234567890123456789013"  # Last char different
        
        hash1 = APIKeyHasher.hash_key(key1)
        hash2 = APIKeyHasher.hash_key(key2)
        
        # Count different characters
        differences = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        
        # Should have significant differences (> 50% different)
        assert differences > 32  # More than half of 64 chars
    
    def test_verify_with_real_generated_key(self):
        """Test verification with a real generated key."""
        from security.api_key_generator import APIKeyGenerator
        
        result = APIKeyGenerator.generate_key("live")
        full_key = result["full_key"]
        stored_hash = result["key_hash"]
        
        # Verification should succeed
        assert APIKeyHasher.verify_key(full_key, stored_hash)
        
        # Verification with wrong key should fail
        wrong_result = APIKeyGenerator.generate_key("live")
        assert not APIKeyHasher.verify_key(wrong_result["full_key"], stored_hash)
    
    def test_hash_unicode_handling(self):
        """Test that hasher handles unicode correctly."""
        # Keys with unicode characters (though not recommended)
        unicode_key = "pk_test_unicode_测试_1234567890123456789"
        
        hash_value = APIKeyHasher.hash_key(unicode_key)
        assert len(hash_value) == 64
        assert APIKeyHasher.verify_key(unicode_key, hash_value)
    
    def test_verify_exception_handling(self):
        """Test that verify_key handles exceptions gracefully."""
        # Should return False instead of raising exceptions
        assert APIKeyHasher.verify_key("key", "invalid") is False
        assert APIKeyHasher.verify_key(None, None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
