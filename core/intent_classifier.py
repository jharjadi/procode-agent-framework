import os
from typing import Literal, Optional, AsyncGenerator, Tuple
import asyncio

IntentType = Literal["tickets", "account", "payments", "general", "unknown"]

class IntentClassifier:
    """
    LLM-based intent classifier with fallback to deterministic matching.
    Supports multiple LLM providers: Anthropic (Claude), OpenAI (GPT), and Google (Gemini).
    """
    
    def __init__(self, use_llm: bool = True, provider: Optional[str] = None):
        """
        Initialize the intent classifier.
        
        Args:
            use_llm: If True, use LLM for classification. If False, use deterministic matching.
            provider: LLM provider to use ("anthropic", "openai", "google").
                     If None, auto-detect based on available API keys.
        """
        self.use_llm = use_llm
        self.llm = None
        self.provider = None
        self.last_used_llm = False  # Track if last classification used LLM
        
        if self.use_llm:
            self.llm, self.provider = self._initialize_llm(provider)
            if not self.llm:
                print("Warning: No LLM provider available. Falling back to deterministic matching.")
    
    def _initialize_llm(self, provider: Optional[str] = None):
        """
        Initialize LLM based on available API keys and provider preference.
        
        Returns:
            Tuple of (llm_instance, provider_name) or (None, None) if initialization fails
        """
        # If provider is specified, try only that provider
        if provider:
            return self._try_provider(provider)
        
        # Auto-detect: try providers in order of preference
        # Check environment variable for provider preference
        env_provider = os.getenv("LLM_PROVIDER", "").lower()
        if env_provider:
            result = self._try_provider(env_provider)
            if result[0]:
                return result
        
        # Try Anthropic first (Claude)
        if os.getenv("ANTHROPIC_API_KEY"):
            result = self._try_provider("anthropic")
            if result[0]:
                return result
        
        # Try OpenAI second
        if os.getenv("OPENAI_API_KEY"):
            result = self._try_provider("openai")
            if result[0]:
                return result
        
        # Try Google last
        if os.getenv("GOOGLE_API_KEY"):
            result = self._try_provider("google")
            if result[0]:
                return result
        
        return None, None
    
    def _try_provider(self, provider: str):
        """Try to initialize a specific LLM provider."""
        try:
            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    return None, None
                llm = ChatAnthropic(
                    model="claude-3-haiku-20240307",
                    temperature=0.0,
                    anthropic_api_key=api_key
                )
                print(f"✓ Using Anthropic (Claude) for intent classification")
                return llm, "anthropic"
            
            elif provider == "openai":
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return None, None
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.0,
                    openai_api_key=api_key
                )
                print(f"✓ Using OpenAI (GPT) for intent classification")
                return llm, "openai"
            
            elif provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    return None, None
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    temperature=0.0,
                    google_api_key=api_key
                )
                print(f"✓ Using Google (Gemini) for intent classification")
                return llm, "google"
            
        except Exception as e:
            print(f"Warning: Failed to initialize {provider}: {e}")
            return None, None
        
        return None, None
    
    def classify_intent(self, text: str) -> IntentType:
        """
        Classify user intent from text.
        
        Args:
            text: User input text
            
        Returns:
            One of: "tickets", "account", "payments", "general", "unknown"
        """
        if not text or not text.strip():
            self.last_used_llm = False
            return "unknown"
        
        # Try LLM classification first if enabled and available
        if self.use_llm and self.llm:
            try:
                intent = self._classify_with_llm(text)
                if intent in ["tickets", "account", "payments", "general", "unknown"]:
                    self.last_used_llm = True
                    print(f"✓ LLM classified intent as: {intent}")
                    return intent
            except Exception as e:
                print(f"LLM classification failed: {e}. Falling back to deterministic matching.")
        
        # Fallback to deterministic matching
        self.last_used_llm = False
        print(f"✓ Deterministic classification used")
        return self._classify_deterministic(text)
    
    def get_classification_metadata(self) -> dict:
        """
        Get metadata about the last classification.
        
        Returns:
            Dictionary with classification metadata
        """
        return {
            "used_llm": self.last_used_llm,
            "provider": self.provider if self.last_used_llm else "deterministic",
            "llm_enabled": self.use_llm and self.llm is not None
        }
    
    def _classify_with_llm(self, text: str) -> IntentType:
        """
        Use LLM to classify intent.
        """
        prompt = f"""You are an intent classifier for a customer service system.

Classify the following user message into ONE of these intents:
- tickets: For creating, viewing, or managing support tickets
- account: For account information, profile changes, or account-related queries
- payments: For payment-related requests (note: payment actions are not supported)
- general: For greetings, casual conversation, general questions, or friendly chat
- unknown: For anything that doesn't fit the above categories

Examples:
User: "I need to create a support ticket"
Intent: tickets

User: "What's my account status?"
Intent: account

User: "I want to make a payment"
Intent: payments

User: "Hello"
Intent: general

User: "Good morning!"
Intent: general

User: "How are you?"
Intent: general

User: "What can you help me with?"
Intent: general

User: "What's the weather today?"
Intent: unknown

User: "Can you help me with my profile?"
Intent: account

User: "I have a problem with my order"
Intent: tickets

Now classify this message:
User: "{text}"
Intent:"""

        response = self.llm.invoke(prompt)
        intent_text = response.content.strip().lower()
        
        # Extract intent from response
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
    
    def _classify_deterministic(self, text: str) -> IntentType:
        """
        Fallback deterministic classification using keyword matching.
        Check more specific keywords first to avoid ambiguity.
        """
        text_lower = text.strip().lower()
        
        # Greeting and general conversation keywords (check first)
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon",
                            "good evening", "greetings", "how are you", "what's up",
                            "thanks", "thank you", "bye", "goodbye", "what can you do",
                            "who are you", "help me understand"]
        if any(keyword in text_lower for keyword in greeting_keywords):
            return "general"
        
        # Payment-related keywords (check first as they're more specific)
        payment_keywords = ["payment", "pay", "billing", "invoice", "charge", "bill"]
        if any(keyword in text_lower for keyword in payment_keywords):
            return "payments"
        
        # Account-related keywords
        account_keywords = ["account", "profile", "user", "settings"]
        if any(keyword in text_lower for keyword in account_keywords):
            return "account"
        
        # Ticket-related keywords (more general, check last)
        ticket_keywords = ["ticket", "support", "issue", "problem", "bug", "error"]
        if any(keyword in text_lower for keyword in ticket_keywords):
            return "tickets"
        
        return "unknown"
    
    async def classify_intent_streaming(
        self,
        text: str
    ) -> AsyncGenerator[tuple[str, Optional[IntentType]], None]:
        """
        Classify intent with streaming progress updates.
        
        Args:
            text: User input text
            
        Yields:
            Tuples of (progress_message, intent). Final yield contains the intent.
        """
        if not text or not text.strip():
            yield ("Classification complete", "unknown")
            return
        
        # Stream progress
        yield ("🤔 Analyzing your request...", None)
        await asyncio.sleep(0.1)
        
        # Try LLM classification if enabled
        if self.use_llm and self.llm:
            try:
                yield (f"🧠 Using {self.provider.upper()} for classification...", None)
                await asyncio.sleep(0.1)
                
                intent = await self._classify_with_llm_async(text)
                
                if intent in ["tickets", "account", "payments", "unknown"]:
                    yield (f"✓ Intent identified: {intent}", intent)
                    return
            except Exception as e:
                yield (f"⚠️ LLM classification failed, using fallback...", None)
                await asyncio.sleep(0.1)
        
        # Fallback to deterministic
        yield ("📋 Using keyword matching...", None)
        await asyncio.sleep(0.1)
        
        intent = self._classify_deterministic(text)
        yield (f"✓ Intent identified: {intent}", intent)
    
    async def _classify_with_llm_async(self, text: str) -> IntentType:
        """
        Async wrapper for LLM classification.
        """
        # Run synchronous LLM call in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._classify_with_llm, text)
