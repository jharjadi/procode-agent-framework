#!/usr/bin/env python3
"""
Quick test script to verify LLM intent classification works.
Run this to test your API keys and see LLM in action!
"""

import os
from core.intent_classifier import IntentClassifier

def test_llm_classification():
    """Test LLM-based intent classification with various inputs."""
    
    print("=" * 60)
    print("LLM Intent Classification Test")
    print("=" * 60)
    
    # Check which API keys are available
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    
    print("\n📋 API Key Status:")
    print(f"  Anthropic (Claude): {'✅ Available' if has_anthropic else '❌ Not set'}")
    print(f"  OpenAI (GPT):       {'✅ Available' if has_openai else '❌ Not set'}")
    print(f"  Google (Gemini):    {'✅ Available' if has_google else '❌ Not set'}")
    
    if not (has_anthropic or has_openai or has_google):
        print("\n⚠️  No API keys found!")
        print("\nTo test LLM classification, set one of these:")
        print("  export ANTHROPIC_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export GOOGLE_API_KEY='your-key'")
        return
    
    print("\n" + "=" * 60)
    print("Initializing LLM Classifier...")
    print("=" * 60)
    
    # Initialize classifier with LLM enabled
    classifier = IntentClassifier(use_llm=True)
    
    if not classifier.llm:
        print("\n❌ LLM initialization failed!")
        print("   Falling back to deterministic matching")
        return
    
    print(f"\n✅ Using: {classifier.provider.upper()}")
    
    # Test cases with natural language
    test_cases = [
        # Ticket-related
        ("I'm having trouble with my order", "tickets"),
        ("Something went wrong and I need help", "tickets"),
        ("Can you help me fix this bug?", "tickets"),
        ("I need to report a problem", "tickets"),
        
        # Account-related
        ("What's my account status?", "account"),
        ("Can you show me my profile?", "account"),
        ("I want to update my user information", "account"),
        ("How do I change my settings?", "account"),
        
        # Payment-related
        ("I want to make a payment", "payments"),
        ("How do I pay my bill?", "payments"),
        ("What's my billing information?", "payments"),
        ("I need to update my payment method", "payments"),
        
        # Unknown/ambiguous
        ("What's the weather today?", "unknown"),
        ("Hello, how are you?", "unknown"),
    ]
    
    print("\n" + "=" * 60)
    print("Testing Natural Language Inputs")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        result = classifier.classify_intent(text)
        is_correct = result == expected
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"\n{status} Input: \"{text}\"")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
    
    print("\n" + "=" * 60)
    print(f"Results: {correct}/{total} correct ({100*correct//total}%)")
    print("=" * 60)
    
    if correct == total:
        print("\n🎉 Perfect! LLM classification is working great!")
    elif correct >= total * 0.8:
        print("\n👍 Good! LLM classification is working well.")
    else:
        print("\n⚠️  Some misclassifications detected. This might be expected for ambiguous inputs.")
    
    # Show comparison with deterministic
    print("\n" + "=" * 60)
    print("Comparison: LLM vs Deterministic")
    print("=" * 60)
    
    deterministic = IntentClassifier(use_llm=False)
    
    comparison_cases = [
        "I'm having trouble with my order",
        "Can you show me my profile?",
        "I want to make a payment",
    ]
    
    for text in comparison_cases:
        llm_result = classifier.classify_intent(text)
        det_result = deterministic.classify_intent(text)
        
        print(f"\nInput: \"{text}\"")
        print(f"  LLM:           {llm_result}")
        print(f"  Deterministic: {det_result}")
        if llm_result != det_result:
            print(f"  → Different! LLM is more accurate for natural language")

if __name__ == "__main__":
    test_llm_classification()
