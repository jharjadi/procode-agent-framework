#!/usr/bin/env python3
"""
Quick test for general conversation and greetings.
"""

from core.intent_classifier import IntentClassifier
from tasks.task_general import GeneralAgent
import asyncio


async def test_greetings():
    """Test greeting and general conversation functionality."""
    print("👋 Testing General Conversation Agent\n")
    
    # Test intent classification
    classifier = IntentClassifier(use_llm=False)  # Use deterministic for quick test
    general_agent = GeneralAgent()
    
    test_inputs = [
        "Hello",
        "Good morning",
        "Hi there",
        "How are you?",
        "What can you do?",
        "Thanks",
        "Goodbye",
        "What's up",
    ]
    
    for user_input in test_inputs:
        print(f"User: {user_input}")
        
        # Classify intent
        intent = classifier.classify_intent(user_input)
        print(f"  Intent: {intent}")
        
        # Get response from general agent
        if intent == "general":
            class SimpleContext:
                class Input:
                    def __init__(self, text):
                        self.text = text
                def __init__(self, text):
                    self.input = self.Input(text)
            
            context = SimpleContext(user_input)
            response = await general_agent.invoke(context)
            print(f"  Agent: {response}")
        
        print()
    
    print("✅ General conversation test complete!")


if __name__ == "__main__":
    asyncio.run(test_greetings())
