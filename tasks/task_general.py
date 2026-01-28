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
• 🌤️ **EXT: Weather Information** - Get current weather and forecasts for any location worldwide
• 🏥 **EXT: Insurance Services** - Manage insurance policies, get policy information, and create new policies

Just let me know what you need, and I'll be happy to assist!"""
        
        self.payment_info = """Regarding payments, I can help you with:
• View payment history and invoices
• Answer questions about billing cycles
• Explain payment methods
• Provide information about charges

**Important**: I cannot process actual payments or transactions. For payment processing, please contact your payment provider directly."""

        self.ticket_info = """For support tickets, I can help you:
• Create new support tickets for any issues
• View existing ticket status
• Update ticket information
• Track ticket resolution

Just describe your issue and I'll help you create a ticket!"""

        self.account_info = """For account management, I can assist with:
• Viewing your account information
• Updating profile details
• Checking account status
• Managing account settings

What would you like to know about your account?"""
    
    async def invoke(self, context) -> str:
        """
        Handle general conversation requests.
        
        Args:
            context: Request context with user input
            
        Returns:
            Friendly response string
        """
        user_input = context.input.text.lower().strip()
        
        # Handle specific domain questions FIRST
        if any(word in user_input for word in ["payment", "pay", "billing", "invoice", "charge"]):
            if any(q in user_input for q in ["what", "how", "can you", "do you", "tell me", "explain"]):
                return self.payment_info
        
        if any(word in user_input for word in ["ticket", "support", "issue", "problem"]):
            if any(q in user_input for q in ["what", "how", "can you", "do you", "tell me", "explain"]):
                return self.ticket_info
        
        if any(word in user_input for word in ["account", "profile", "user", "settings"]):
            if any(q in user_input for q in ["what", "how", "can you", "do you", "tell me", "explain"]):
                return self.account_info
        
        # Handle general "what can you do" / "help" / "supported" questions
        help_keywords = [
            "what can you do", "what can you help", "capabilities", "features",
            "help me understand", "who are you", "what are supported", "what is supported",
            "what do you support", "what are you", "what can i", "what features",
            "what version", "what's supported", "whats supported"
        ]
        if any(phrase in user_input for phrase in help_keywords):
            # Check if it's asking about a specific domain
            if "payment" in user_input or "pay" in user_input:
                return self.payment_info
            elif "ticket" in user_input or "support" in user_input:
                return self.ticket_info
            elif "account" in user_input or "profile" in user_input:
                return self.account_info
            else:
                return f"I'm your AI assistant! {self.capabilities}"
        
        # Handle greetings (but only if not asking for help)
        if any(greeting in user_input for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            # Check if it's JUST a greeting (not a question)
            if "?" not in user_input and not any(q in user_input for q in ["what", "how", "can you", "do you"]):
                time_greeting = self._get_time_based_greeting()
                return f"{time_greeting} {random.choice(self.greetings)}"
            else:
                # It's a greeting + question, show capabilities
                return f"Hello! {self.capabilities}"
        
        # Handle "how are you"
        if "how are you" in user_input or "how r u" in user_input:
            return "I'm doing great, thank you for asking! I'm here and ready to help you. How can I assist you today?"
        
        # Handle thanks
        if any(thanks in user_input for thanks in ["thank", "thanks", "thx"]):
            return "You're very welcome! Is there anything else I can help you with?"
        
        # Handle goodbye
        if any(bye in user_input for bye in ["bye", "goodbye", "see you", "later"]):
            return "Goodbye! Feel free to come back anytime you need assistance. Have a great day!"
        
        # Handle "what's up"
        if "what's up" in user_input or "whats up" in user_input or "wassup" in user_input:
            return "Not much! Just here to help you out. What can I do for you today?"
        
        # Check for out-of-scope questions (religion, philosophy, calculations, etc.)
        # Note: weather and insurance are now handled by external agents
        out_of_scope_keywords = [
            "religion", "buddhism", "christianity", "islam", "hinduism", "god",
            "calculate", "math", "equation", "solve", "compute",
            "write code", "program", "script", "function",
            "meaning of life", "philosophy", "existence",
            "recipe", "cook", "food", "restaurant",
            "movie", "film", "tv show", "entertainment",
            "sports", "game", "score", "team",
            "news", "politics", "election", "government"
        ]
        
        if any(keyword in user_input for keyword in out_of_scope_keywords):
            return f"""I appreciate your question, but I'm specifically designed to help with customer service tasks.

{self.capabilities}

For questions about weather, calculations, general knowledge, or other topics, you might want to use a general-purpose AI assistant like ChatGPT or Google.

Is there anything related to tickets, accounts, or payments I can help you with?"""
        
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
