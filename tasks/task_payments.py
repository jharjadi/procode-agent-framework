class PaymentsAgent:
    """Handles payment-related tasks (informational only, no actual processing)."""
    
    async def invoke(self, context=None):
        """
        Handle payment-related inquiries.
        
        Note: This agent provides information only. Actual payment processing
        is not available for security reasons.
        """
        user_input = context.input.text.lower() if context and hasattr(context, 'input') else ""
        
        # Check what they're asking about
        if any(word in user_input for word in ["history", "past", "previous", "old"]):
            return """📋 **Payment History**

I can help you view your payment history, but I cannot access actual payment records in this demo.

In a production system, I would show you:
• Recent transactions
• Payment dates and amounts
• Payment methods used
• Invoice numbers

For actual payment history, please log into your account portal or contact support."""

        elif any(word in user_input for word in ["method", "how to pay", "how do i pay"]):
            return """💳 **Payment Methods**

I can provide information about payment methods:

**Supported payment methods typically include:**
• Credit/Debit cards (Visa, Mastercard, Amex)
• Bank transfers
• Digital wallets (PayPal, Apple Pay, Google Pay)
• Direct debit

**Important**: I cannot process actual payments. To make a payment, please use your account portal or contact your payment provider."""

        elif any(word in user_input for word in ["invoice", "bill", "statement"]):
            return """📄 **Invoices & Billing**

I can help you understand invoices and billing:

• **View invoices**: Check your account portal
• **Billing cycle**: Typically monthly
• **Payment due dates**: Usually 30 days from invoice date
• **Billing questions**: I can explain charges

For specific invoice details or to download invoices, please access your account portal."""

        elif any(word in user_input for word in ["process", "make", "send", "transfer", "execute"]):
            return """⚠️ **Payment Processing Not Available**

For security reasons, I cannot process actual payments or transactions.

**To make a payment:**
1. Log into your account portal
2. Navigate to the payments section
3. Follow the secure payment process

**Need help?** I can:
• Explain payment options
• Answer billing questions
• Help you understand invoices
• Direct you to the right resources"""

        else:
            # General payment inquiry
            return """💳 **Payment Information**

I can help you with payment-related questions:

**What I can do:**
• Explain payment methods and options
• Answer questions about billing and invoices
• Provide information about payment history
• Help you understand charges

**What I cannot do:**
• Process actual payments (for security)
• Access your payment details
• Modify payment information

**To make a payment**, please use your secure account portal.

What specific payment question can I help you with?"""
