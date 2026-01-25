"""
Multi-LLM Intent Classifier with Cost Optimization

This module implements a tiered LLM approach for intent classification:
1. Fast deterministic matching with confidence scoring (free)
2. Small/cheap LLM for ambiguous cases (Claude Haiku, Gemini Flash-8B)
3. Local LLM option (Ollama) for zero-cost inference
4. Caching layer to avoid duplicate LLM calls

Cost savings: 85-99% compared to using Claude 3.5 Sonnet for all requests
"""

import os
import hashlib
from typing import Literal, Optional, Tuple, Dict
from datetime import datetime, timedelta

IntentType = Literal["tickets", "account", "payments", "general", "unknown"]


class IntentCache:
    """Simple in-memory cache for intent classifications."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self.cache: Dict[str, Tuple[IntentType, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def _hash_text(self, text: str) -> str:
        """Create hash of text for cache key."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
    
    def get(self, text: str) -> Optional[IntentType]:
        """Get cached intent if available and not expired."""
        key = self._hash_text(text)
        if key in self.cache:
            intent, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return intent
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None
    
    def set(self, text: str, intent: IntentType):
        """Cache an intent classification."""
        key = self._hash_text(text)
        self.cache[key] = (intent, datetime.now())
    
    def clear_expired(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


class MultiLLMClassifier:
    """
    Cost-optimized intent classifier using multiple strategies:
    1. Cache lookup (free)
    2. Deterministic matching with confidence (free)
    3. Small LLM for ambiguous cases (cheap)
    4. Local LLM option (free)
    """
    
    def __init__(
        self,
        use_llm: bool = True,
        provider: Optional[str] = None,
        confidence_threshold: float = 0.8,
        enable_cache: bool = True
    ):
        """
        Initialize the multi-LLM classifier.
        
        Args:
            use_llm: If True, use LLM for low-confidence cases
            provider: LLM provider ("anthropic", "openai", "google", "ollama")
            confidence_threshold: Minimum confidence to skip LLM (0.0-1.0)
            enable_cache: Enable caching of classifications
        """
        self.use_llm = use_llm
        self.confidence_threshold = confidence_threshold
        self.enable_cache = enable_cache
        
        # Initialize cache
        self.cache = IntentCache() if enable_cache else None
        
        # Initialize LLM (prefer small/cheap models)
        self.llm = None
        self.provider = None
        if self.use_llm:
            self.llm, self.provider = self._initialize_llm(provider)
        
        # Metrics tracking
        self.metrics = {
            "cache_hits": 0,
            "deterministic_high_confidence": 0,
            "deterministic_low_confidence": 0,
            "llm_calls": 0,
            "total_requests": 0
        }
    
    def _initialize_llm(self, provider: Optional[str] = None):
        """
        Initialize LLM, preferring small/cheap models.
        
        Priority order:
        1. Ollama (free, local)
        2. Claude 3 Haiku (12x cheaper than Sonnet)
        3. Gemini Flash-8B (2x cheaper than Flash)
        4. GPT-4o-mini (already cheap)
        """
        # Check environment variable for provider preference
        env_provider = provider or os.getenv("INTENT_LLM_PROVIDER", "").lower()
        
        # Try specified provider first
        if env_provider:
            result = self._try_provider(env_provider)
            if result[0]:
                return result
        
        # Auto-detect in order of cost-effectiveness
        # 1. Try Ollama first (free)
        if os.getenv("OLLAMA_BASE_URL") or self._is_ollama_available():
            result = self._try_provider("ollama")
            if result[0]:
                return result
        
        # 2. Try Claude Haiku (cheap)
        if os.getenv("ANTHROPIC_API_KEY"):
            result = self._try_provider("anthropic")
            if result[0]:
                return result
        
        # 3. Try Gemini Flash-8B (cheap)
        if os.getenv("GOOGLE_API_KEY"):
            result = self._try_provider("google")
            if result[0]:
                return result
        
        # 4. Try OpenAI (already using mini)
        if os.getenv("OPENAI_API_KEY"):
            result = self._try_provider("openai")
            if result[0]:
                return result
        
        return None, None
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama is available locally."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=1)
            return response.status_code == 200
        except:
            return False
    
    def _try_provider(self, provider: str):
        """Try to initialize a specific LLM provider with cost-optimized models."""
        try:
            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    return None, None
                
                # Use Claude 3 Haiku instead of Sonnet (12x cheaper!)
                llm = ChatAnthropic(
                    model="claude-3-haiku-20240307",  # Haiku, not Sonnet
                    temperature=0.0,
                    anthropic_api_key=api_key
                )
                print(f"✓ Using Claude 3 Haiku for intent classification (cost-optimized)")
                return llm, "anthropic"
            
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return None, None
                
                # GPT-4o-mini is already the cheapest OpenAI option
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.0,
                    openai_api_key=api_key
                )
                print(f"✓ Using GPT-4o-mini for intent classification")
                return llm, "openai"
            
            elif provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    return None, None
                
                # Use Flash-8B instead of Flash (2x cheaper!)
                model = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash-8b")
                llm = ChatGoogleGenerativeAI(
                    model=model,
                    temperature=0.0,
                    google_api_key=api_key
                )
                print(f"✓ Using {model} for intent classification (cost-optimized)")
                return llm, "google"
            
            elif provider == "ollama":
                from langchain_ollama import ChatOllama
                
                # Use small, fast model for classification
                model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                
                llm = ChatOllama(
                    model=model,
                    base_url=base_url,
                    temperature=0.0
                )
                print(f"✓ Using Ollama ({model}) for intent classification (FREE, local)")
                return llm, "ollama"
            
        except Exception as e:
            print(f"Warning: Failed to initialize {provider}: {e}")
            return None, None
        
        return None, None
    
    def classify_intent(self, text: str) -> IntentType:
        """
        Classify intent using tiered approach for cost optimization.
        
        Flow:
        1. Check cache (free)
        2. Try deterministic with confidence (free)
        3. Use LLM only if confidence is low (cheap)
        
        Args:
            text: User input text
            
        Returns:
            Classified intent
        """
        self.metrics["total_requests"] += 1
        
        if not text or not text.strip():
            return "unknown"
        
        # Step 1: Check cache
        if self.enable_cache and self.cache:
            cached_intent = self.cache.get(text)
            if cached_intent:
                self.metrics["cache_hits"] += 1
                return cached_intent
        
        # Step 2: Try deterministic with confidence scoring
        intent, confidence = self._classify_deterministic_with_confidence(text)
        
        if confidence >= self.confidence_threshold:
            # High confidence, use deterministic result (free!)
            self.metrics["deterministic_high_confidence"] += 1
            if self.enable_cache and self.cache:
                self.cache.set(text, intent)
            return intent
        
        # Step 3: Low confidence, use LLM if available
        self.metrics["deterministic_low_confidence"] += 1
        
        if self.use_llm and self.llm:
            try:
                self.metrics["llm_calls"] += 1
                llm_intent = self._classify_with_llm(text)
                if llm_intent in ["tickets", "account", "payments", "general", "unknown"]:
                    if self.enable_cache and self.cache:
                        self.cache.set(text, llm_intent)
                    return llm_intent
            except Exception as e:
                print(f"LLM classification failed: {e}. Using deterministic result.")
        
        # Fallback to deterministic result
        if self.enable_cache and self.cache:
            self.cache.set(text, intent)
        return intent
    
    def _classify_deterministic_with_confidence(
        self,
        text: str
    ) -> Tuple[IntentType, float]:
        """
        Deterministic classification with confidence scoring.
        
        Returns:
            Tuple of (intent, confidence_score)
            confidence_score: 0.0 (low) to 1.0 (high)
        """
        text_lower = text.strip().lower()
        
        # Strong indicators (high confidence)
        strong_patterns = {
            "tickets": [
                "create ticket", "new ticket", "open ticket", "support ticket",
                "report issue", "report bug", "file ticket"
            ],
            "account": [
                "my account", "account settings", "profile settings",
                "update profile", "change password", "account info"
            ],
            "payments": [
                "make payment", "process payment", "pay bill", "payment method",
                "billing info", "invoice"
            ],
            "general": [
                "hello", "hi there", "good morning", "good afternoon",
                "thank you", "thanks", "goodbye", "bye"
            ]
        }
        
        # Check strong patterns first (confidence: 0.95)
        for intent, patterns in strong_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent, 0.95
        
        # Weak indicators (medium confidence)
        weak_keywords = {
            "tickets": ["ticket", "issue", "problem", "bug", "error", "support"],
            "account": ["account", "profile", "user", "settings"],
            "payments": ["payment", "pay", "billing", "charge", "bill"],
            "general": ["help", "what can you do", "who are you"]
        }
        
        # Check weak keywords (confidence: 0.6)
        for intent, keywords in weak_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent, 0.6
        
        # No clear match (low confidence)
        return "unknown", 0.3
    
    def _classify_with_llm(self, text: str) -> IntentType:
        """Use LLM for classification (only called for ambiguous cases)."""
        # Optimized prompt for small models
        prompt = f"""Classify this message into ONE intent:
- tickets: support tickets, issues, bugs
- account: account info, profile, settings
- payments: payment requests, billing
- general: greetings, thanks, help
- unknown: anything else

Message: "{text}"
Intent:"""
        
        response = self.llm.invoke(prompt)
        intent_text = response.content.strip().lower()
        
        # Extract intent
        if "tickets" in intent_text:
            return "tickets"
        elif "account" in intent_text:
            return "account"
        elif "payments" in intent_text:
            return "payments"
        elif "general" in intent_text:
            return "general"
        else:
            return "unknown"
    
    def get_metrics(self) -> dict:
        """Get classification metrics for monitoring."""
        total = self.metrics["total_requests"]
        if total == 0:
            return self.metrics
        
        return {
            **self.metrics,
            "cache_hit_rate": self.metrics["cache_hits"] / total,
            "deterministic_rate": (
                self.metrics["deterministic_high_confidence"] / total
            ),
            "llm_call_rate": self.metrics["llm_calls"] / total,
            "cost_savings_estimate": (
                1 - (self.metrics["llm_calls"] / total)
            ) * 100  # % of requests that didn't need LLM
        }
    
    def print_metrics(self):
        """Print classification metrics."""
        metrics = self.get_metrics()
        print("\n📊 Intent Classification Metrics:")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Cache hits: {metrics['cache_hits']} ({metrics.get('cache_hit_rate', 0):.1%})")
        print(f"  Deterministic (high conf): {metrics['deterministic_high_confidence']} ({metrics.get('deterministic_rate', 0):.1%})")
        print(f"  LLM calls: {metrics['llm_calls']} ({metrics.get('llm_call_rate', 0):.1%})")
        print(f"  💰 Estimated cost savings: {metrics.get('cost_savings_estimate', 0):.1f}%")
