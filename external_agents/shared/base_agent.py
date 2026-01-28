"""
Base classes for external agents.

Provides abstract base classes for Principal Agents and Task Agents
with common functionality like error handling, logging, and metrics.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message


class BaseExternalAgent(AgentExecutor, ABC):
    """
    Abstract base class for Principal Agents in external agent systems.
    
    Principal Agents are responsible for:
    - Receiving A2A requests
    - Classifying intent (for complex patterns)
    - Routing to appropriate task agents (for complex patterns)
    - Handling requests directly (for simple patterns)
    - Error handling and logging
    - Metrics collection
    """
    
    def __init__(self, agent_name: str = "external_agent"):
        """
        Initialize the base external agent.
        
        Args:
            agent_name: Name of the agent for logging
        """
        self.agent_name = agent_name
        self.logger = self._setup_logger()
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time_ms": 0
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger for the agent."""
        logger = logging.getLogger(f"external_agent.{self.agent_name}")
        logger.setLevel(logging.INFO)
        
        # Create console handler if not already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _extract_text(self, message) -> str:
        """
        Extract text content from A2A message.
        
        Args:
            message: A2A message object
            
        Returns:
            Extracted text string
        """
        text = ""
        if message and hasattr(message, 'parts') and message.parts:
            for part in message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    text += part.root.text
                elif hasattr(part, 'text') and part.text:
                    text += part.text
                elif isinstance(part, dict) and 'text' in part:
                    text += part['text']
        return text.strip()
    
    def _classify_intent(self, text: str) -> str:
        """
        Classify intent from text (override in subclass for complex patterns).
        
        Args:
            text: User input text
            
        Returns:
            Intent string (e.g., "info", "creation")
        """
        # Default implementation - override in subclass
        return "default"
    
    def _format_error(self, error: Exception) -> str:
        """
        Format error message for user-friendly response.
        
        Args:
            error: Exception object
            
        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_msg = str(error)
        return f"❌ Error ({error_type}): {error_msg}"
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the agent request (must be implemented by subclass).
        
        Args:
            context: Request context from A2A
            event_queue: Event queue for sending responses
        """
        start_time = datetime.now()
        self.metrics["total_requests"] += 1
        
        try:
            # Extract text from message
            text = self._extract_text(context.message)
            
            if not text:
                await event_queue.enqueue_event(
                    new_agent_text_message("❌ No text content in request")
                )
                self.metrics["failed_requests"] += 1
                return
            
            self.logger.info(f"Processing request: {text[:100]}...")
            
            # Process request (implemented by subclass)
            result = await self._process_request(text, context, event_queue)
            
            # Send response
            if result:
                await event_queue.enqueue_event(new_agent_text_message(result))
                self.metrics["successful_requests"] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            error_msg = self._format_error(e)
            await event_queue.enqueue_event(new_agent_text_message(error_msg))
            self.metrics["failed_requests"] += 1
        
        finally:
            # Track response time
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["total_response_time_ms"] += duration
            self.logger.info(f"Request completed in {duration:.2f}ms")
    
    @abstractmethod
    async def _process_request(
        self,
        text: str,
        context: RequestContext,
        event_queue: EventQueue
    ) -> Optional[str]:
        """
        Process the request (must be implemented by subclass).
        
        Args:
            text: Extracted text from message
            context: Request context
            event_queue: Event queue for streaming responses
            
        Returns:
            Response text or None if response already sent via event_queue
        """
        pass
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation requests."""
        await event_queue.enqueue_event(
            new_agent_text_message("⚠️ Cancellation not supported")
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent metrics.
        
        Returns:
            Dictionary of metrics
        """
        avg_response_time = 0
        if self.metrics["total_requests"] > 0:
            avg_response_time = (
                self.metrics["total_response_time_ms"] / 
                self.metrics["total_requests"]
            )
        
        return {
            **self.metrics,
            "avg_response_time_ms": round(avg_response_time, 2),
            "success_rate": (
                self.metrics["successful_requests"] / 
                self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0 else 0
            )
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "agent_name": self.agent_name,
            "timestamp": datetime.now().isoformat(),
            "metrics": self.get_metrics()
        }


class BaseTaskAgent(ABC):
    """
    Abstract base class for Task Agents in complex external agent systems.
    
    Task Agents are responsible for:
    - Handling specific tasks delegated by Principal Agent
    - Implementing domain-specific logic
    - Returning results to Principal Agent
    """
    
    def __init__(self, task_name: str = "task"):
        """
        Initialize the base task agent.
        
        Args:
            task_name: Name of the task for logging
        """
        self.task_name = task_name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger for the task agent."""
        logger = logging.getLogger(f"task_agent.{self.task_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def execute(self, text: str, context: Optional[RequestContext] = None) -> str:
        """
        Execute the task (must be implemented by subclass).
        
        Args:
            text: User input text
            context: Optional request context
            
        Returns:
            Task result as string
        """
        pass
    
    def _format_error(self, error: Exception) -> str:
        """
        Format error message for user-friendly response.
        
        Args:
            error: Exception object
            
        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_msg = str(error)
        return f"❌ Task Error ({error_type}): {error_msg}"
