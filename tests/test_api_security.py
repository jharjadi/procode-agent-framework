"""
Test API Security Features

This script tests the API security middleware including:
- Rate limiting
- API key authentication
- CORS restrictions
"""

import os
import time
import requests
from typing import Dict, Any

# Test configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:9998")
API_KEY = os.getenv("DEMO_API_KEY", "test-key-123")


def test_health_check():
    """Test that health check endpoint bypasses security"""
    print("\n=== Testing Health Check (No Security) ===")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("✓ Health check endpoint not implemented (expected)")
    else:
        print(f"Response: {response.text}")


def test_without_api_key():
    """Test that requests without API key are rejected"""
    print("\n=== Testing Without API Key ===")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "test-001"
            }
        },
        "id": 1
    }
    
    response = requests.post(BASE_URL, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 401:
        print("✓ Request correctly rejected without API key")
    else:
        print("✗ Security might be disabled (ENABLE_API_SECURITY=false)")


def test_with_invalid_api_key():
    """Test that requests with invalid API key are rejected"""
    print("\n=== Testing With Invalid API Key ===")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "test-002"
            }
        },
        "id": 2
    }
    
    headers = {"X-API-Key": "wrong-key"}
    response = requests.post(BASE_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 403:
        print("✓ Request correctly rejected with invalid API key")
    else:
        print("✗ Invalid API key not properly validated")


def test_with_valid_api_key():
    """Test that requests with valid API key are accepted"""
    print("\n=== Testing With Valid API Key ===")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "test-003"
            }
        },
        "id": 3
    }
    
    headers = {"X-API-Key": API_KEY}
    response = requests.post(BASE_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Request accepted with valid API key")
        print(f"Response: {response.json()}")
        
        # Check rate limit headers
        if "X-RateLimit-Remaining-Minute" in response.headers:
            print(f"\nRate Limit Headers:")
            print(f"  Remaining (minute): {response.headers.get('X-RateLimit-Remaining-Minute')}")
            print(f"  Remaining (hour): {response.headers.get('X-RateLimit-Remaining-Hour')}")
            print(f"  Remaining (day): {response.headers.get('X-RateLimit-Remaining-Day')}")
    else:
        print(f"✗ Request failed: {response.text}")


def test_rate_limiting():
    """Test that rate limiting works"""
    print("\n=== Testing Rate Limiting ===")
    print("Making 12 rapid requests (limit is 10/minute)...")
    
    headers = {"X-API-Key": API_KEY}
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Test"}],
                "messageId": f"test-rate-{time.time()}"
            }
        },
        "id": 1
    }
    
    success_count = 0
    rate_limited = False
    
    for i in range(12):
        response = requests.post(BASE_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            success_count += 1
            remaining = response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')
            print(f"  Request {i+1}: ✓ Success (remaining: {remaining})")
        elif response.status_code == 429:
            rate_limited = True
            print(f"  Request {i+1}: ✗ Rate limited (expected)")
            print(f"    Response: {response.json()}")
            break
        else:
            print(f"  Request {i+1}: ? Unexpected status {response.status_code}")
        
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\nResults:")
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited: {rate_limited}")
    
    if rate_limited and success_count <= 10:
        print("✓ Rate limiting working correctly")
    elif not rate_limited:
        print("✗ Rate limiting might be disabled or limit is too high")
    else:
        print("? Unexpected behavior")


def test_api_key_via_query_param():
    """Test API key authentication via query parameter"""
    print("\n=== Testing API Key via Query Parameter ===")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Hello"}],
                "messageId": "test-query-001"
            }
        },
        "id": 1
    }
    
    url = f"{BASE_URL}?api_key={API_KEY}"
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ API key via query parameter works")
    else:
        print(f"✗ Failed: {response.text}")


def main():
    """Run all security tests"""
    print("=" * 60)
    print("API Security Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    # Check if security is enabled
    security_enabled = os.getenv("ENABLE_API_SECURITY", "false").lower() == "true"
    print(f"Security Enabled: {security_enabled}")
    
    if not security_enabled:
        print("\n⚠️  WARNING: Security is disabled (ENABLE_API_SECURITY=false)")
        print("Set ENABLE_API_SECURITY=true to test security features")
        print("\nRunning basic connectivity test only...")
        test_health_check()
        return
    
    try:
        # Run all tests
        test_health_check()
        test_without_api_key()
        test_with_invalid_api_key()
        test_with_valid_api_key()
        test_api_key_via_query_param()
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("Test Suite Complete")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to backend")
        print(f"Make sure the backend is running at {BASE_URL}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")


if __name__ == "__main__":
    main()
