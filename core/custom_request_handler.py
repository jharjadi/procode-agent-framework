"""
Custom request handler that adds classification metadata to responses.
"""
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from typing import Any, Dict
import json


class MetadataTrackingRequestHandler(DefaultRequestHandler):
    """
    Custom request handler that tracks and returns classification metadata.
    Extends the default handler to add LLM usage tracking to responses.
    """
    
    def __init__(self, agent_executor, task_store):
        super().__init__(agent_executor, task_store)
        self.last_classification_metadata = {}
    
    async def handle_message_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle message/send requests and add classification metadata to response.
        """
        # Call parent handler
        result = await super().handle_message_send(params)
        
        # Try to get classification metadata from the agent executor
        if hasattr(self.agent_executor, 'intent_classifier'):
            metadata = self.agent_executor.intent_classifier.get_classification_metadata()
            self.last_classification_metadata = metadata
            
            # Add metadata to the result
            if result and isinstance(result, dict):
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata'].update(metadata)
        
        return result
