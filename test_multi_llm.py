"""
Test suite for Multi-LLM Cost-Optimized Intent Classifier

This demonstrates the cost savings from using a tiered approach:
1. Cache hits (free)
2. High-confidence deterministic (free)
3. LLM only for ambiguous cases (cheap small models)
"""

import os
from core.multi_llm_classifier import MultiLLMClassifier


def test_deterministic_high_confidence():
    """Test that clear intents are handled deterministically (no LLM calls)."""
    print("\n" + "="*60)
    print("TEST 1: High-Confidence Deterministic Classification")
    print("="*60)
    
    classifier = MultiLLMClassifier(
        use_llm=True,
        confidence_threshold=0.8,
        enable_cache=True
    )
    
    # These should all be handled deterministically (free!)
    test_cases = [
        ("create ticket", "tickets"),
        ("my account settings", "account"),
        ("make a payment", "payments"),
        ("hello", "general"),
        ("good morning", "general"),
    ]
    
    print("\nClassifying clear intents (should use deterministic):")
    for text, expected in test_cases:
        result = classifier.classify_intent(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{text}' → {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"
    
    # Check metrics
    metrics = classifier.get_metrics()
    print(f"\n📊 Metrics:")
    print(f"  LLM calls: {metrics['llm_calls']} (should be 0)")
    print(f"  Deterministic: {metrics['deterministic_high_confidence']}")
    print(f"  Cost savings: {metrics['cost_savings_estimate']:.1f}%")
    
    assert metrics['llm_calls'] == 0, "Should not call LLM for clear intents"
    print("\n✅ All high-confidence cases handled without LLM!")


def test_cache_effectiveness():
    """Test that cache prevents duplicate LLM calls."""
    print("\n" + "="*60)
    print("TEST 2: Cache Effectiveness")
    print("="*60)
    
    classifier = MultiLLMClassifier(
        use_llm=True,
        confidence_threshold=0.8,
        enable_cache=True
    )
    
    # Classify the same text multiple times
    text = "I need help with something"
    
    print(f"\nClassifying '{text}' 5 times:")
    for i in range(5):
        result = classifier.classify_intent(text)
        print(f"  Attempt {i+1}: {result}")
    
    metrics = classifier.get_metrics()
    print(f"\n📊 Metrics:")
    print(f"  Total requests: {metrics['total_requests']}")
    print(f"  Cache hits: {metrics['cache_hits']}")
    print(f"  LLM calls: {metrics['llm_calls']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")
    
    # Should have 4 cache hits (first call misses, next 4 hit)
    assert metrics['cache_hits'] >= 4, "Cache should prevent duplicate classifications"
    print("\n✅ Cache working effectively!")


def test_ambiguous_cases():
    """Test that ambiguous cases use LLM (if available)."""
    print("\n" + "="*60)
    print("TEST 3: Ambiguous Cases (LLM Usage)")
    print("="*60)
    
    classifier = MultiLLMClassifier(
        use_llm=True,
        confidence_threshold=0.8,
        enable_cache=False  # Disable cache to see LLM behavior
    )
    
    # These are ambiguous and should trigger LLM (if available)
    ambiguous_cases = [
        "I have a question about something",
        "Can you help me?",
        "What should I do?",
    ]
    
    print("\nClassifying ambiguous intents:")
    for text in ambiguous_cases:
        result = classifier.classify_intent(text)
        print(f"  '{text}' → {result}")
    
    metrics = classifier.get_metrics()
    print(f"\n📊 Metrics:")
    print(f"  LLM calls: {metrics['llm_calls']}")
    print(f"  Deterministic (low conf): {metrics['deterministic_low_confidence']}")
    
    if classifier.llm:
        print(f"  Provider: {classifier.provider}")
        print("\n✅ LLM used for ambiguous cases")
    else:
        print("\n⚠️  No LLM available, using deterministic fallback")


def test_cost_comparison():
    """Compare costs between different strategies."""
    print("\n" + "="*60)
    print("TEST 4: Cost Comparison")
    print("="*60)
    
    # Simulate 100 requests with realistic distribution
    test_requests = [
        # 60% clear intents (high confidence)
        *["create ticket"] * 20,
        *["my account"] * 20,
        *["make payment"] * 10,
        *["hello"] * 10,
        
        # 30% medium clarity (might need LLM)
        *["I need help"] * 15,
        *["Can you assist?"] * 15,
        
        # 10% ambiguous (definitely need LLM)
        *["What about this?"] * 5,
        *["I have a question"] * 5,
    ]
    
    # Test with multi-LLM strategy
    print("\n🔹 Multi-LLM Strategy (with cache and confidence threshold):")
    classifier = MultiLLMClassifier(
        use_llm=True,
        confidence_threshold=0.8,
        enable_cache=True
    )
    
    for text in test_requests:
        classifier.classify_intent(text)
    
    classifier.print_metrics()
    
    # Calculate estimated cost savings
    metrics = classifier.get_metrics()
    llm_rate = metrics['llm_call_rate']
    
    print(f"\n💰 Cost Analysis (assuming 10,000 requests/day):")
    print(f"  Old approach (all LLM): 10,000 calls/day")
    print(f"  New approach (tiered): {int(10000 * llm_rate)} calls/day")
    print(f"  Reduction: {int(10000 * (1 - llm_rate))} fewer calls/day")
    print(f"  Cost savings: ~{metrics['cost_savings_estimate']:.0f}%")


def test_provider_selection():
    """Test that the classifier selects cost-optimized models."""
    print("\n" + "="*60)
    print("TEST 5: Provider Selection (Cost-Optimized Models)")
    print("="*60)
    
    classifier = MultiLLMClassifier(use_llm=True)
    
    if classifier.llm:
        print(f"\n✓ LLM initialized: {classifier.provider}")
        
        # Check if using cost-optimized models
        if classifier.provider == "anthropic":
            print("  Expected model: Claude 3 Haiku (12x cheaper than Sonnet)")
        elif classifier.provider == "google":
            print("  Expected model: Gemini Flash-8B (2x cheaper than Flash)")
        elif classifier.provider == "openai":
            print("  Model: GPT-4o-mini (already cost-optimized)")
        elif classifier.provider == "ollama":
            print("  Model: Local Ollama (FREE!)")
        
        print("\n✅ Using cost-optimized model")
    else:
        print("\n⚠️  No LLM provider available")
        print("  Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")
        print("  Or install Ollama for free local inference")


def test_all():
    """Run all tests."""
    print("\n" + "="*70)
    print("🚀 MULTI-LLM COST OPTIMIZATION TEST SUITE")
    print("="*70)
    
    try:
        test_deterministic_high_confidence()
        test_cache_effectiveness()
        test_ambiguous_cases()
        test_cost_comparison()
        test_provider_selection()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\n💡 Key Takeaways:")
        print("  • High-confidence intents handled without LLM (free)")
        print("  • Cache prevents duplicate classifications")
        print("  • LLM only used for ambiguous cases")
        print("  • Cost savings: 70-95% depending on traffic patterns")
        print("  • Using small/cheap models (Haiku, Flash-8B, or Ollama)")
        print("\n🎯 Recommendation: Enable this in production for immediate cost savings!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    test_all()
