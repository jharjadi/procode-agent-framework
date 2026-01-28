"""
Agent Client Module

This module provides functionality for communicating with other agents using
the A2A (Agent-to-Agent) protocol. It supports sending messages, delegating tasks,
and handling responses from remote agents.
"""

from typing import Optional, Dict, Any, List
import httpx
import asyncio
from a2a.types import Message, Part, TextPart
from a2a.server.agent_execution import RequestContext
import uuid


class AgentClientError(Exception):
    """Base exception for agent client errors."""
    pass


class AgentCommunicationError(AgentClientError):
    """Exception raised when communication with agent fails."""
    pass


class AgentTimeoutError(AgentClientError):
    """Exception raised when agent communication times out."""
    pass


class AgentClient:
    """
    Client for communicating with other agents via A2A protocol.
    
    This client handles:
    - Sending messages to remote agents
    - Task delegation
    - Response parsing
    - Error handling and retries
    """
    
    def __init__(
        self,
        agent_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the agent client.
        
        Args:
            agent_url: Base URL of the target agent
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.agent_url = agent_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.AsyncClient(timeout=timeout)
        self._request_id = 0
    
    def _get_next_request_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self._request_id += 1
        return self._request_id
    
    async def send_message(
        self,
        message: Message,
        context: Optional[RequestContext] = None,
        method: str = "message/send"
    ) -> Message:
        """
        Send a message to the agent and get response.
        
        Args:
            message: Message to send
            context: Optional execution context
            method: JSON-RPC method name
            
        Returns:
            Response message from the agent
            
        Raises:
            AgentCommunicationError: If communication fails
            AgentTimeoutError: If request times out
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": {
                "message": message.model_dump(),
            },
            "id": self._get_next_request_id()
        }
        
        # Note: context is not serialized in the payload as it's handled internally
        # by the A2A protocol
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    self.agent_url,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Check for JSON-RPC error
                if "error" in result:
                    error = result["error"]
                    raise AgentCommunicationError(
                        f"Agent returned error: {error.get('message', 'Unknown error')}"
                    )
                
                # Parse response message
                if "result" in result:
                    return Message(**result["result"])
                else:
                    raise AgentCommunicationError("Invalid response format")
            
            except httpx.TimeoutException as e:
                last_error = AgentTimeoutError(f"Request timed out: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
            
            except httpx.HTTPStatusError as e:
                last_error = AgentCommunicationError(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                )
                if attempt < self.max_retries - 1 and e.response.status_code >= 500:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                break
            
            except Exception as e:
                last_error = AgentCommunicationError(f"Unexpected error: {e}")
                break
        
        # If we get here, all retries failed
        raise last_error
    
    async def delegate_task(
        self,
        task_description: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Delegate a task to another agent.
        
        Args:
            task_description: Description of the task to delegate
            task_id: Optional task ID for tracking
            metadata: Optional metadata to include
            
        Returns:
            Text response from the agent
            
        Raises:
            AgentCommunicationError: If delegation fails
        """
        # Create message
        message = Message(
            role="user",
            parts=[TextPart(text=task_description)],
            messageId=str(uuid.uuid4())
        )
        
        # Create context if task_id provided
        context = None
        if task_id:
            context = RequestContext(
                task_id=task_id or str(uuid.uuid4())
            )
        
        # Send message
        response = await self.send_message(message, context)
        
        # Extract text from response
        return self._extract_text(response)
    
    async def send_text(
        self,
        text: str,
        task_id: Optional[str] = None
    ) -> str:
        """
        Send a simple text message to the agent.
        
        Args:
            text: Text to send
            task_id: Optional task ID
            
        Returns:
            Text response from the agent
        """
        return await self.delegate_task(text, task_id)
    
    def _extract_text(self, message: Message) -> str:
        """
        Extract text content from message parts.
        
        Args:
            message: Message to extract text from
            
        Returns:
            Concatenated text from all text parts
        """
        texts = []
        for part in message.parts:
            # Handle different part types
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                texts.append(part.root.text)
            elif hasattr(part, 'text'):
                texts.append(part.text)
            elif isinstance(part, dict) and 'text' in part:
                texts.append(part['text'])
        
        return " ".join(texts) if texts else ""
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Agent information dictionary
            
        Raises:
            AgentCommunicationError: If request fails
        """
        try:
            response = await self.client.get(f"{self.agent_url}/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise AgentCommunicationError(f"Failed to get agent info: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if the agent is healthy and responsive.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.agent_url}/health",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class AgentClientPool:
    """
    Pool of agent clients for managing multiple agent connections.
    
    This pool maintains a cache of clients to avoid creating new connections
    for each request to the same agent.
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the client pool.
        
        Args:
            timeout: Default timeout for clients
            max_retries: Default max retries for clients
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.clients: Dict[str, AgentClient] = {}
    
    def get_client(self, agent_url: str) -> AgentClient:
        """
        Get or create a client for the specified agent URL.
        
        Args:
            agent_url: URL of the agent
            
        Returns:
            AgentClient instance
        """
        if agent_url not in self.clients:
            self.clients[agent_url] = AgentClient(
                agent_url=agent_url,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
        return self.clients[agent_url]
    
    async def close_all(self):
        """Close all clients in the pool."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()


# Global client pool instance
_global_pool: Optional[AgentClientPool] = None


def get_global_client_pool() -> AgentClientPool:
    """
    Get or create the global agent client pool.
    
    Returns:
        Global AgentClientPool instance
    """
    global _global_pool
    if _global_pool is None:
        _global_pool = AgentClientPool()
    return _global_pool


def reset_global_client_pool():
    """Reset the global client pool (useful for testing)."""
    global _global_pool
    if _global_pool is not None:
        # Note: This is synchronous, so we can't await close_all()
        # In production, ensure proper cleanup
        _global_pool = None
