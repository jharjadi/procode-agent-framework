#!/usr/bin/env python3
"""
Test script to verify agent name prefixes are working correctly.
"""
import asyncio
import httpx

AGENT_URL = "http://localhost:9998"

async def test_agent_response(message: str, expected_agent: str):
    """Test a single message and check for agent prefix."""
    print(f"\n{'='*60}")
    print(f"Testing: {message}")
    print(f"Expected Agent: {expected_agent}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": message}],
                    "messageId": f"test-{hash(message)}"
                }
            },
            "id": 1
        }
        
        try:
            response = await client.post(AGENT_URL, json=payload)
            result = response.json()
            
            if "result" in result:
                message_data = result["result"]
                if "parts" in message_data:
                    response_text = message_data["parts"][0].get("text", "")
                    print(f"\n✅ Response received:")
                    print(f"{response_text[:200]}...")
                    
                    # Check if agent prefix is present
                    if expected_agent in response_text:
                        print(f"\n✅ SUCCESS: Found '{expected_agent}' prefix in response!")
                        return True
                    else:
                        print(f"\n❌ FAILED: Expected '{expected_agent}' prefix not found!")
                        return False
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return False

async def main():
    """Run all tests."""
    print("\n🧪 Testing Agent Name Prefixes")
    print("="*60)
    
    tests = [
        ("Hello!", "💬 **General Agent**"),
        ("Create a support ticket for login issues", "🎫 **Tickets Agent**"),
        ("Show my account information", "👤 **Account Agent**"),
        ("What are my payment options?", "💳 **Payments Agent**"),
    ]
    
    results = []
    for message, expected_agent in tests:
        result = await test_agent_response(message, expected_agent)
        results.append(result)
        await asyncio.sleep(1)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
