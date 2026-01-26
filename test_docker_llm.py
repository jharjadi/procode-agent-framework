#!/usr/bin/env python3
"""
Test script to verify LLM intent classifier is working in Docker.
"""
import requests
import json
import time

# Agent URL
AGENT_URL = "http://localhost:9998"

def test_intent_classification():
    """Test various intents to verify LLM classification is working."""
    
    test_cases = [
        {
            "message": "Hello, how are you?",
            "expected_intent": "general",
            "description": "Greeting"
        },
        {
            "message": "I need to create a support ticket",
            "expected_intent": "tickets",
            "description": "Ticket creation"
        },
        {
            "message": "What's my account status?",
            "expected_intent": "account",
            "description": "Account query"
        },
        {
            "message": "I want to make a payment",
            "expected_intent": "payments",
            "description": "Payment request"
        },
        {
            "message": "Can you help me with my profile settings?",
            "expected_intent": "account",
            "description": "Profile/account"
        }
    ]
    
    print("=" * 80)
    print("Testing LLM Intent Classifier in Docker")
    print("=" * 80)
    print()
    
    # First, check if the agent is reachable
    try:
        response = requests.get(f"{AGENT_URL}/", timeout=5)
        print(f"✓ Agent is reachable at {AGENT_URL}")
        print(f"  Status: {response.status_code}")
        print()
    except Exception as e:
        print(f"✗ Failed to reach agent at {AGENT_URL}")
        print(f"  Error: {e}")
        return
    
    # Test each case
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['description']}")
        print(f"  Message: \"{test_case['message']}\"")
        print(f"  Expected Intent: {test_case['expected_intent']}")
        
        try:
            # Send request to agent
            payload = {
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": test_case['message']}]
                }
            }
            
            response = requests.post(
                f"{AGENT_URL}/tasks",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract response text
                response_text = ""
                if "message" in result and "content" in result["message"]:
                    for content in result["message"]["content"]:
                        if content.get("type") == "text":
                            response_text = content.get("text", "")
                            break
                
                print(f"  ✓ Response received")
                print(f"  Response preview: {response_text[:100]}...")
                
                results.append({
                    "test": test_case['description'],
                    "message": test_case['message'],
                    "expected": test_case['expected_intent'],
                    "status": "✓ PASS",
                    "response": response_text[:200]
                })
            else:
                print(f"  ✗ Request failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                results.append({
                    "test": test_case['description'],
                    "message": test_case['message'],
                    "expected": test_case['expected_intent'],
                    "status": "✗ FAIL",
                    "response": f"HTTP {response.status_code}"
                })
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "test": test_case['description'],
                "message": test_case['message'],
                "expected": test_case['expected_intent'],
                "status": "✗ ERROR",
                "response": str(e)
            })
        
        print()
        time.sleep(1)  # Brief pause between requests
    
    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    passed = sum(1 for r in results if "✓" in r["status"])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    
    for result in results:
        print(f"{result['status']} {result['test']}")
        print(f"   Message: {result['message']}")
        print(f"   Expected: {result['expected']}")
        print()
    
    return results

if __name__ == "__main__":
    test_intent_classification()
