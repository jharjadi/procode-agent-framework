"""
Insurance Creation Task Agent - Handles insurance policy creation and management.

Provides functionality for:
- Creating new policies
- Updating existing policies
- Canceling policies
- Modifying policy details
"""

import sys
import os
from typing import Optional
from datetime import datetime, timedelta
import random

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from a2a.server.agent_execution import RequestContext
from external_agents.shared.base_agent import BaseTaskAgent
from external_agents.shared.agent_utils import extract_policy_number, parse_yes_no


class InsuranceCreationTask(BaseTaskAgent):
    """
    Task Agent for insurance policy creation and management.
    
    Handles requests like:
    - "Create a new auto insurance policy"
    - "Update policy POL-2024-001"
    - "Cancel my home insurance"
    """
    
    def __init__(self):
        """Initialize the Insurance Creation Task Agent."""
        super().__init__(task_name="insurance_creation")
        
        # Mock database (in production, this would be a real database)
        self.policies = {}
        self.next_policy_number = 1
        
        self.logger.info("Insurance Creation Task Agent initialized")
    
    async def execute(self, text: str, context: Optional[RequestContext] = None) -> str:
        """
        Execute insurance policy creation/management task.
        
        Args:
            text: User input text
            context: Optional request context
            
        Returns:
            Result of the operation as formatted string
        """
        try:
            text_lower = text.lower()
            
            # Check if user wants to create a new policy
            if any(keyword in text_lower for keyword in ["create", "new", "start", "begin"]):
                return self._create_policy(text)
            
            # Check if user wants to update a policy
            if any(keyword in text_lower for keyword in ["update", "modify", "change", "edit"]):
                return self._update_policy(text)
            
            # Check if user wants to cancel a policy
            if any(keyword in text_lower for keyword in ["cancel", "delete", "remove", "terminate"]):
                return self._cancel_policy(text)
            
            # Default: provide guidance
            return self._get_guidance()
            
        except Exception as e:
            self.logger.error(f"Error in insurance creation task: {e}", exc_info=True)
            return self._format_error(e)
    
    def _create_policy(self, text: str) -> str:
        """Create a new insurance policy."""
        text_lower = text.lower()
        
        # Determine insurance type
        if "auto" in text_lower or "car" in text_lower or "vehicle" in text_lower:
            insurance_type = "Auto Insurance"
            coverage = "$500,000"
            premium = "$1,200/year"
            deductible = "$1,000"
        elif "home" in text_lower or "house" in text_lower or "property" in text_lower:
            insurance_type = "Home Insurance"
            coverage = "$750,000"
            premium = "$1,800/year"
            deductible = "$2,500"
        elif "life" in text_lower:
            insurance_type = "Life Insurance"
            coverage = "$1,000,000"
            premium = "$2,400/year"
            deductible = "N/A"
        else:
            return """❌ Please specify the type of insurance you want to create:
• Auto Insurance
• Home Insurance
• Life Insurance

Example: "Create a new auto insurance policy" """
        
        # Generate policy number
        policy_number = f"POL-2024-{str(self.next_policy_number).zfill(3)}"
        self.next_policy_number += 1
        
        # Create policy
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        
        policy = {
            "policy_number": policy_number,
            "type": insurance_type,
            "holder": "New Customer",  # In production, get from user profile
            "coverage": coverage,
            "premium": premium,
            "status": "Pending",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "deductible": deductible,
            "created_at": datetime.now().isoformat()
        }
        
        self.policies[policy_number] = policy
        
        result = f"""✅ **Policy Created Successfully**

**Policy Number:** {policy_number}
**Type:** {insurance_type}
**Coverage:** {coverage}
**Annual Premium:** {premium}
**Deductible:** {deductible}
**Status:** Pending Activation

**Policy Period:**
• Start Date: {policy['start_date']}
• End Date: {policy['end_date']}

**Next Steps:**
1. Review the policy details
2. Complete payment setup
3. Provide required documentation
4. Policy will be activated within 24 hours

💡 Your policy number is **{policy_number}**. Save this for future reference.

📞 Questions? Contact our support team or ask me for more information."""
        
        self.logger.info(f"Created new policy: {policy_number}")
        return result
    
    def _update_policy(self, text: str) -> str:
        """Update an existing policy."""
        policy_number = extract_policy_number(text)
        
        if not policy_number:
            return """❌ Please provide a policy number to update.

Example: "Update policy POL-2024-001" """
        
        if policy_number not in self.policies:
            return f"""❌ Policy {policy_number} not found.

💡 Make sure you have the correct policy number. You can ask me to list your policies."""
        
        policy = self.policies[policy_number]
        
        # In production, this would parse the update request and modify specific fields
        # For demo, we'll show what can be updated
        
        result = f"""✅ **Policy Update Request Received**

**Policy Number:** {policy_number}
**Current Type:** {policy['type']}
**Current Status:** {policy['status']}

**What would you like to update?**
• Coverage amount
• Premium payment schedule
• Deductible amount
• Beneficiary information
• Contact details

**Example requests:**
• "Increase coverage to $1,000,000"
• "Change payment to monthly"
• "Update beneficiary information"

💡 Please specify what you'd like to change, and I'll process your request."""
        
        self.logger.info(f"Update requested for policy: {policy_number}")
        return result
    
    def _cancel_policy(self, text: str) -> str:
        """Cancel an existing policy."""
        policy_number = extract_policy_number(text)
        
        if not policy_number:
            return """❌ Please provide a policy number to cancel.

Example: "Cancel policy POL-2024-001" """
        
        if policy_number not in self.policies:
            return f"""❌ Policy {policy_number} not found.

💡 Make sure you have the correct policy number."""
        
        policy = self.policies[policy_number]
        
        # Update policy status
        policy['status'] = "Cancelled"
        policy['cancelled_at'] = datetime.now().isoformat()
        
        result = f"""✅ **Policy Cancellation Processed**

**Policy Number:** {policy_number}
**Type:** {policy['type']}
**Previous Status:** Active
**New Status:** Cancelled

**Cancellation Details:**
• Effective Date: {datetime.now().strftime("%Y-%m-%d")}
• Refund Processing: 5-7 business days
• Coverage Ends: Immediately

**Important Information:**
• You will receive a refund for any unused premium
• All active claims will be processed
• Coverage is no longer in effect

**Need to Reinstate?**
Contact our support team within 30 days to reinstate your policy without reapplication.

📧 A confirmation email has been sent to your registered email address."""
        
        self.logger.info(f"Cancelled policy: {policy_number}")
        return result
    
    def _get_guidance(self) -> str:
        """Provide guidance on policy creation and management."""
        return """🔧 **Policy Management**

I can help you with:

**Create New Policy:**
• "Create a new auto insurance policy"
• "Start a home insurance policy"
• "I need life insurance"

**Update Existing Policy:**
• "Update policy POL-2024-001"
• "Modify my coverage amount"
• "Change payment schedule"

**Cancel Policy:**
• "Cancel policy POL-2024-001"
• "Terminate my insurance"
• "Stop my policy"

💡 **Tips:**
• Have your policy number ready for updates/cancellations
• Specify the type of insurance when creating new policies
• Contact support for complex changes

How can I assist you with your policy today?"""
