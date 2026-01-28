"""
Insurance Info Task Agent - Handles insurance information queries.

Provides information about:
- Policy details
- Coverage information
- Premium quotes
- Policy status
"""

import sys
import os
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from a2a.server.agent_execution import RequestContext
from external_agents.shared.base_agent import BaseTaskAgent
from external_agents.shared.agent_utils import extract_policy_number, extract_amount, format_dict


class InsuranceInfoTask(BaseTaskAgent):
    """
    Task Agent for insurance information queries.
    
    Handles requests like:
    - "Show me policy POL-2024-001"
    - "What's my coverage?"
    - "Get me a quote for auto insurance"
    """
    
    def __init__(self):
        """Initialize the Insurance Info Task Agent."""
        super().__init__(task_name="insurance_info")
        
        # Mock database of policies (in production, this would be a real database)
        self.policies = {
            "POL-2024-001": {
                "policy_number": "POL-2024-001",
                "type": "Auto Insurance",
                "holder": "John Doe",
                "coverage": "$500,000",
                "premium": "$1,200/year",
                "status": "Active",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
                "deductible": "$1,000"
            },
            "POL-2024-002": {
                "policy_number": "POL-2024-002",
                "type": "Home Insurance",
                "holder": "Jane Smith",
                "coverage": "$750,000",
                "premium": "$1,800/year",
                "status": "Active",
                "start_date": "2024-02-15",
                "end_date": "2025-02-15",
                "deductible": "$2,500"
            },
            "POL-2024-003": {
                "policy_number": "POL-2024-003",
                "type": "Life Insurance",
                "holder": "Bob Johnson",
                "coverage": "$1,000,000",
                "premium": "$2,400/year",
                "status": "Active",
                "start_date": "2024-03-01",
                "end_date": "2044-03-01",
                "deductible": "N/A"
            }
        }
        
        self.logger.info("Insurance Info Task Agent initialized")
    
    async def execute(self, text: str, context: Optional[RequestContext] = None) -> str:
        """
        Execute insurance information query.
        
        Args:
            text: User input text
            context: Optional request context
            
        Returns:
            Insurance information as formatted string
        """
        try:
            text_lower = text.lower()
            
            # Check if user is asking for a specific policy
            policy_number = extract_policy_number(text)
            if policy_number:
                return self._get_policy_details(policy_number)
            
            # Check if user is asking for coverage information
            if any(keyword in text_lower for keyword in ["coverage", "covered", "cover"]):
                return self._get_coverage_info(text)
            
            # Check if user is asking for a quote
            if any(keyword in text_lower for keyword in ["quote", "price", "cost", "premium"]):
                return self._get_quote(text)
            
            # Check if user is asking to list policies
            if any(keyword in text_lower for keyword in ["list", "show all", "my policies"]):
                return self._list_policies()
            
            # Default: provide general information
            return self._get_general_info()
            
        except Exception as e:
            self.logger.error(f"Error in insurance info task: {e}", exc_info=True)
            return self._format_error(e)
    
    def _get_policy_details(self, policy_number: str) -> str:
        """Get details for a specific policy."""
        policy = self.policies.get(policy_number)
        
        if not policy:
            return f"❌ Policy {policy_number} not found.\n\n💡 Available policies: {', '.join(self.policies.keys())}"
        
        details = f"""📋 **Policy Details**

{format_dict(policy)}

✅ This policy is currently {policy['status'].lower()}.

💡 Need to make changes? Ask me to update or cancel this policy."""
        
        return details
    
    def _get_coverage_info(self, text: str) -> str:
        """Get coverage information."""
        # In production, this would analyze the text to determine specific coverage questions
        return """🛡️ **Coverage Information**

Our insurance policies provide comprehensive coverage:

**Auto Insurance:**
• Liability coverage up to $500,000
• Collision and comprehensive coverage
• Uninsured motorist protection
• Roadside assistance

**Home Insurance:**
• Dwelling coverage up to $750,000
• Personal property protection
• Liability coverage
• Additional living expenses

**Life Insurance:**
• Term and whole life options
• Coverage from $100,000 to $5,000,000
• Accidental death benefit
• Optional riders available

💡 For specific coverage details, please provide your policy number."""
    
    def _get_quote(self, text: str) -> str:
        """Generate an insurance quote."""
        text_lower = text.lower()
        
        # Determine insurance type from text
        if "auto" in text_lower or "car" in text_lower or "vehicle" in text_lower:
            insurance_type = "Auto Insurance"
            base_premium = 1200
        elif "home" in text_lower or "house" in text_lower or "property" in text_lower:
            insurance_type = "Home Insurance"
            base_premium = 1800
        elif "life" in text_lower:
            insurance_type = "Life Insurance"
            base_premium = 2400
        else:
            insurance_type = "General Insurance"
            base_premium = 1500
        
        quote = f"""💰 **Insurance Quote**

**Type:** {insurance_type}
**Estimated Annual Premium:** ${base_premium:,}/year
**Monthly Payment:** ${base_premium // 12:,}/month

**Coverage Includes:**
• Comprehensive protection
• 24/7 customer support
• Easy claims process
• Flexible payment options

**Next Steps:**
1. Review the quote details
2. Ask me to create a new policy
3. Provide additional information if needed

💡 This is an estimated quote. Final premium may vary based on your specific circumstances."""
        
        return quote
    
    def _list_policies(self) -> str:
        """List all available policies."""
        if not self.policies:
            return "❌ No policies found."
        
        policy_list = ["📋 **Available Policies**\n"]
        
        for policy_number, policy in self.policies.items():
            policy_list.append(
                f"• **{policy_number}** - {policy['type']} "
                f"({policy['holder']}) - {policy['status']}"
            )
        
        policy_list.append("\n💡 Ask me about a specific policy number for more details.")
        
        return "\n".join(policy_list)
    
    def _get_general_info(self) -> str:
        """Provide general insurance information."""
        return """🏥 **Insurance Information**

I can help you with:

**Policy Information:**
• View policy details (provide policy number)
• Check coverage information
• Review policy status

**Quotes:**
• Get premium quotes
• Compare coverage options
• Estimate costs

**Available Policies:**
• Auto Insurance
• Home Insurance
• Life Insurance

💡 **Examples:**
• "Show me policy POL-2024-001"
• "What's covered in my auto insurance?"
• "Get me a quote for home insurance"
• "List all my policies"

How can I assist you today?"""
