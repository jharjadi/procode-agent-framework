"""
Insurance Principal Agent - Routes insurance requests to appropriate task agents.

This is a complex pattern agent that demonstrates task routing.
"""

import sys
import os
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from external_agents.shared.base_agent import BaseExternalAgent
from external_agents.shared.agent_config import AgentConfig
from external_agents.insurance_agent.tasks.task_insurance_info import InsuranceInfoTask
from external_agents.insurance_agent.tasks.task_insurance_creation import InsuranceCreationTask


class InsurancePrincipal(BaseExternalAgent):
    """
    Principal Agent for Insurance services.
    
    Routes requests to appropriate task agents based on intent:
    - InsuranceInfoTask: Get policy details, check coverage, get quotes
    - InsuranceCreationTask: Create, update, cancel policies
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Insurance Principal Agent.
        
        Args:
            config_path: Path to configuration file
        """
        super().__init__(agent_name="insurance_principal")
        
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = AgentConfig(config_path)
        
        # Initialize task agents
        self.task_agents = {
            'info': InsuranceInfoTask(),
            'creation': InsuranceCreationTask()
        }
        
        self.logger.info(f"Insurance Principal Agent initialized with {len(self.task_agents)} task agents")
    
    def _classify_intent(self, text: str) -> str:
        """
        Classify intent to determine which task agent to use.
        
        Args:
            text: User input text
            
        Returns:
            Intent string: 'info' or 'creation'
        """
        text_lower = text.lower()
        
        # Get keywords from config
        creation_keywords = self.config.get("routing.intent_keywords.creation", [])
        info_keywords = self.config.get("routing.intent_keywords.info", [])
        
        # Check creation keywords first (more specific)
        if any(keyword in text_lower for keyword in creation_keywords):
            return 'creation'
        
        # Check info keywords
        if any(keyword in text_lower for keyword in info_keywords):
            return 'info'
        
        # Default to info
        return self.config.get("routing.default_task", "info")
    
    async def _process_request(
        self,
        text: str,
        context: RequestContext,
        event_queue: EventQueue
    ) -> Optional[str]:
        """
        Process insurance request by routing to appropriate task agent.
        
        Args:
            text: User input text
            context: Request context
            event_queue: Event queue for responses
            
        Returns:
            Response text from task agent
        """
        # Classify intent
        intent = self._classify_intent(text)
        self.logger.info(f"Classified intent as: {intent}")
        
        # Get appropriate task agent
        task_agent = self.task_agents.get(intent)
        if not task_agent:
            return f"❌ Unknown task type: {intent}"
        
        # Execute task agent
        try:
            result = await task_agent.execute(text, context)
            self.logger.info(f"Task agent '{intent}' completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Task agent '{intent}' failed: {e}", exc_info=True)
            return self._format_error(e)
