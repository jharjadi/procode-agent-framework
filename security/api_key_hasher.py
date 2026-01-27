"""
API Key Hasher

Provides secure hashing and verification of API keys using SHA-256.
Uses constant-time comparison to prevent timing attacks.

Security Features:
- SHA-256 hashing (one-way, irreversible)
- Constant-time comparison (timing attack resistant)
- No salt needed (keys are already high-entropy)
"""

import hashlib
import secrets
from typing import Optional


class APIKeyHasher:
    """Hash and verify API keys securely."""
    
    ALGORITHM = "sha256"
    
    @classmethod
    def hash_key(cls, key: str) -> str:
        """
        Hash an API key using SHA-256.
        
        Args:
            key: The plaintext API key
            
        Returns:
            Hexadecimal hash string (64 characters)
            
        Example:
            >>> APIKeyHasher.hash_key("pk_test_abc123")
            'a1b2c3d4e5f6...'
            
        Note:
            - Uses SHA-256 (not bcrypt/argon2) because API keys are already
              high-entropy random tokens, not user passwords
            - No salt needed for the same reason
            - Fast hashing is acceptable here (unlike passwords)
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        
        # Hash the key using SHA-256
        hash_obj = hashlib.sha256(key.encode('utf-8'))
        return hash_obj.hexdigest()
    
    @classmethod
    def verify_key(cls, key: str, key_hash: str) -> bool:
        """
        Verify an API key against its hash using constant-time comparison.
        
        Args:
            key: The plaintext API key to verify
            key_hash: The stored hash to compare against
            
        Returns:
            True if key matches hash, False otherwise
            
        Example:
            >>> key = "pk_test_abc123"
            >>> hash_val = APIKeyHasher.hash_key(key)
            >>> APIKeyHasher.verify_key(key, hash_val)
            True
            >>> APIKeyHasher.verify_key("wrong_key", hash_val)
            False
            
        Security:
            Uses secrets.compare_digest() for constant-time comparison
            to prevent timing attacks.
        """
        if not key or not key_hash:
            return False
        
        try:
            # Hash the provided key
            computed_hash = cls.hash_key(key)
            
            # Use constant-time comparison to prevent timing attacks
            # secrets.compare_digest() is designed to prevent timing analysis
            return secrets.compare_digest(computed_hash, key_hash)
        except Exception:
            # If any error occurs during hashing/comparison, fail closed
            return False
    
    @classmethod
    def hash_multiple(cls, keys: list[str]) -> dict[str, str]:
        """
        Hash multiple keys at once.
        
        Args:
            keys: List of plaintext API keys
            
        Returns:
            Dictionary mapping each key to its hash
            
        Example:
            >>> keys = ["pk_test_abc", "pk_live_xyz"]
            >>> hashes = APIKeyHasher.hash_multiple(keys)
            >>> len(hashes)
            2
        """
        return {key: cls.hash_key(key) for key in keys}
    
    @classmethod
    def is_valid_hash(cls, hash_value: str) -> bool:
        """
        Check if a string looks like a valid SHA-256 hash.
        
        Args:
            hash_value: The hash string to validate
            
        Returns:
            True if format is valid, False otherwise
            
        Example:
            >>> APIKeyHasher.is_valid_hash("a" * 64)
            True
            >>> APIKeyHasher.is_valid_hash("invalid")
            False
        """
        if not hash_value or not isinstance(hash_value, str):
            return False
        
        # SHA-256 produces 64 hexadecimal characters
        if len(hash_value) != 64:
            return False
        
        # Check if all characters are valid hex
        try:
            int(hash_value, 16)
            return True
        except ValueError:
            return False


# Convenience functions
def hash_api_key(key: str) -> str:
    """Hash an API key."""
    return APIKeyHasher.hash_key(key)


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    return APIKeyHasher.verify_key(key, key_hash)


# Example usage and testing
if __name__ == "__main__":
    # Example: Generate and verify a key
    test_key = "pk_test_AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-_A"
    
    # Hash the key
    key_hash = APIKeyHasher.hash_key(test_key)
    print(f"Key: {test_key}")
    print(f"Hash: {key_hash}")
    print(f"Hash length: {len(key_hash)}")
    
    # Verify correct key
    is_valid = APIKeyHasher.verify_key(test_key, key_hash)
    print(f"Verification (correct key): {is_valid}")
    
    # Verify wrong key
    wrong_key = "pk_test_WrongKeyWrongKeyWrongKeyWrongKeyWrongKey"
    is_valid = APIKeyHasher.verify_key(wrong_key, key_hash)
    print(f"Verification (wrong key): {is_valid}")
    
    # Test timing attack resistance
    import time
    
    def measure_verification_time(key: str, hash_val: str, iterations: int = 1000) -> float:
        start = time.perf_counter()
        for _ in range(iterations):
            APIKeyHasher.verify_key(key, hash_val)
        end = time.perf_counter()
        return (end - start) / iterations * 1000  # ms per verification
    
    correct_time = measure_verification_time(test_key, key_hash)
    wrong_time = measure_verification_time(wrong_key, key_hash)
    
    print(f"\nTiming attack resistance test:")
    print(f"Correct key avg time: {correct_time:.6f} ms")
    print(f"Wrong key avg time: {wrong_time:.6f} ms")
    print(f"Time difference: {abs(correct_time - wrong_time):.6f} ms")
    print(f"Timing attack resistant: {abs(correct_time - wrong_time) < 0.001}")
