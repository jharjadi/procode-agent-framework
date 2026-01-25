"""
General Conversation Agent

Handles greetings, casual conversation, and general inquiries.
Provides friendly responses and helps users understand what the system can do.
"""

import random
from datetime import datetime


class GeneralAgent:
    """
    Agent for handling general conversation, greetings, and help requests.
    """
    
    def __init__(self):
        """Initialize the general conversation agent."""
        self.greetings = [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Greetings! I'm here to help.",
            "Hello! Nice to meet you. How may I help?",
        ]
        
        self.capabilities = """I can help you with:
• 🎫 **Support Tickets** - Create and manage support tickets for issues
• 👤 **Account Management** - View and update your account information
• 💳 **Payment Inquiries** - Answer questions about payments (note: actual payment processing is not available)

Just let me know what you need, and I'll be happy to assist!"""
    
    async def invoke(self, context) -> str:
        """
        Handle general conversation requests.
        
        Args:
            context: Request context with user input
            
        Returns:
            Friendly response string
        """
        user_input = context.input.text.lower().strip()
        
        # Handle greetings
        if any(greeting in user_input for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            time_greeting = self._get_time_based_greeting()
            return f"{time_greeting} {random.choice(self.greetings)}"
        
        # Handle "how are you"
        if "how are you" in user_input or "how r u" in user_input:
            return "I'm doing great, thank you for asking! I'm here and ready to help you. How can I assist you today?"
        
        # Handle thanks
        if any(thanks in user_input for thanks in ["thank", "thanks", "thx"]):
            return "You're very welcome! Is there anything else I can help you with?"
        
        # Handle goodbye
        if any(bye in user_input for bye in ["bye", "goodbye", "see you", "later"]):
            return "Goodbye! Feel free to come back anytime you need assistance. Have a great day!"
        
        # Handle "what can you do" / "help"
        if any(phrase in user_input for phrase in ["what can you do", "what can you help", "capabilities", "features", "help me understand", "who are you"]):
            return f"I'm your AI assistant! {self.capabilities}"
        
        # Handle "what's up"
        if "what's up" in user_input or "whats up" in user_input or "wassup" in user_input:
            return "Not much! Just here to help you out. What can I do for you today?"
        
        # Default friendly response
        return f"I'm here to help! {self.capabilities}"
    
    def _get_time_based_greeting(self) -> str:
        """Get a greeting based on current time."""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Good morning!"
        elif 12 <= hour < 17:
            return "Good afternoon!"
        elif 17 <= hour < 22:
            return "Good evening!"
        else:
            return "Hello!"
