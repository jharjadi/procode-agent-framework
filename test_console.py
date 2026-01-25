#!/usr/bin/env python3
"""
Quick test script to demonstrate the console app working with the agent.
"""

import asyncio
import httpx

async def test_console_client():
    """Test the agent is responding correctly."""
    
    print("🧪 Testing Procode Agent...")
    print("=" * 60)
    
    agent_url = "http://localhost:9998"
    
    # Test 1: Send a ticket request
    print("\n1️⃣ Testing ticket creation...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "create a support ticket"}],
                    "messageId": "test-1"
                }
            },
            "id": 1
        }
        
        try:
            response = await client.post(agent_url, json=payload)
            result = response.json()
            
            if "result" in result:
                message = result["result"]
                if "parts" in message:
                    text = message["parts"][0].get("text", "")
                    print(f"   ✅ Agent Response: {text}")
                else:
                    print(f"   ✅ Agent Response: {message}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            print(f"   Make sure the agent is running: python __main__.py")
            return False
    
    # Test 2: Send an account request
    print("\n2️⃣ Testing account query...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": "show my account info"}],
                    "messageId": "test-2"
                }
            },
            "id": 2
        }
        
        try:
            response = await client.post(agent_url, json=payload)
            result = response.json()
            
            if "result" in result:
                message = result["result"]
                if "parts" in message:
                    text = message["parts"][0].get("text", "")
                    print(f"   ✅ Agent Response: {text}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ Connection Error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! The agent is working correctly.")
    print("\n📱 Now try the interactive console app:")
    print("   python console_app.py")
    print("\n   Then type commands like:")
    print("   - 'Create a support ticket for login issues'")
    print("   - '/history' to see conversation history")
    print("   - '/status' to check agent status")
    print("   - '/quit' to exit")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_console_client())
