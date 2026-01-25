"""
Mock Agent Server for Testing A2A Communication

This module provides a simple mock agent that can be used for testing
agent-to-agent communication without requiring real external agents.
"""

import asyncio
from typing import Optional
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, TextPart
from a2a.utils import new_agent_text_message
from a2a.server.apps.jsonrpc.fastapi_app import create_jsonrpc_app
import uvicorn


class MockAgent(AgentExecutor):
    """
    Mock agent for testing A2A communication.
    
    This agent simply echoes back the received message with a prefix
    to demonstrate successful communication.
    """
    
    def __init__(self, agent_name: str = "mock_agent", response_prefix: str = "Mock response"):
        """
        Initialize the mock agent.
        
        Args:
            agent_name: Name of the mock agent
            response_prefix: Prefix to add to responses
        """
        self.agent_name = agent_name
        self.response_prefix = response_prefix
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the mock agent logic.
        
        Args:
            context: Request context containing the message
            event_queue: Event queue for sending responses
        """
        # Extract text from message
        text = self._extract_text(context.message)
        
        # Create response
        response = f"{self.response_prefix} from {self.agent_name}: {text}"
        
        # Send response
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation (not implemented)."""
        await event_queue.enqueue_event(
            new_agent_text_message(f"{self.agent_name}: Cancel not supported")
        )
    
    def _extract_text(self, message: Message) -> str:
        """
        Extract text from message parts.
        
        Args:
            message: Message to extract text from
            
        Returns:
            Concatenated text from all parts
        """
        texts = []
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    texts.append(part.root.text)
                elif hasattr(part, 'text'):
                    texts.append(part.text)
                elif isinstance(part, dict) and 'text' in part:
                    texts.append(part['text'])
        return " ".join(texts) if texts else ""


class TicketMockAgent(AgentExecutor):
    """Mock agent specialized for ticket operations."""
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = self._extract_text(context.message)
        
        if "create" in text.lower():
            response = "✅ Mock ticket created: TICKET-12345"
        elif "list" in text.lower():
            response = "📋 Mock tickets: TICKET-001, TICKET-002, TICKET-003"
        elif "get" in text.lower() or "show" in text.lower():
            response = "📄 Mock ticket details: TICKET-001 - Test Issue (Status: Open)"
        else:
            response = f"🎫 Ticket agent received: {text}"
        
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Cancel not supported"))
    
    def _extract_text(self, message: Message) -> str:
        texts = []
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    texts.append(part.root.text)
                elif hasattr(part, 'text'):
                    texts.append(part.text)
                elif isinstance(part, dict) and 'text' in part:
                    texts.append(part['text'])
        return " ".join(texts) if texts else ""


class AnalyticsMockAgent(AgentExecutor):
    """Mock agent specialized for analytics operations."""
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = self._extract_text(context.message)
        response = f"📊 Analytics result: Analyzed '{text}' - 95% confidence, 1000 data points processed"
        await event_queue.enqueue_event(new_agent_text_message(response))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(new_agent_text_message("Cancel not supported"))
    
    def _extract_text(self, message: Message) -> str:
        texts = []
        if message and message.parts:
            for part in message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    texts.append(part.root.text)
                elif hasattr(part, 'text'):
                    texts.append(part.text)
                elif isinstance(part, dict) and 'text' in part:
                    texts.append(part['text'])
        return " ".join(texts) if texts else ""


def create_mock_agent_app(agent_type: str = "generic"):
    """
    Create a FastAPI app with a mock agent.
    
    Args:
        agent_type: Type of mock agent ('generic', 'ticket', 'analytics')
        
    Returns:
        FastAPI application
    """
    if agent_type == "ticket":
        agent = TicketMockAgent()
    elif agent_type == "analytics":
        agent = AnalyticsMockAgent()
    else:
        agent = MockAgent(agent_name=f"{agent_type}_agent")
    
    return create_jsonrpc_app(agent)


def run_mock_agent(port: int = 9999, agent_type: str = "generic"):
    """
    Run a mock agent server.
    
    Args:
        port: Port to run the server on
        agent_type: Type of mock agent to run
    """
    app = create_mock_agent_app(agent_type)
    
    print(f"🚀 Starting {agent_type} mock agent on port {port}")
    print(f"   Agent URL: http://localhost:{port}")
    print(f"   Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


async def test_mock_agent_locally():
    """
    Test the mock agent locally without starting a server.
    Useful for unit testing.
    """
    from a2a.types import Message, TextPart
    
    # Create mock agent
    agent = MockAgent()
    
    # Create test message
    message = Message(
        role="user",
        parts=[TextPart(text="Hello, mock agent!")],
        messageId="test-123"
    )
    
    # Create context
    class TestContext:
        def __init__(self, message):
            self.message = message
            self.task_id = "test-task"
    
    context = TestContext(message)
    
    # Create event queue
    class TestEventQueue:
        def __init__(self):
            self.events = []
        
        async def enqueue_event(self, event):
            self.events.append(event)
    
    event_queue = TestEventQueue()
    
    # Execute
    await agent.execute(context, event_queue)
    
    # Check result
    print("Test Results:")
    print(f"  Events received: {len(event_queue.events)}")
    for i, event in enumerate(event_queue.events):
        print(f"  Event {i+1}: {event}")
    
    return event_queue.events


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    port = 9999
    agent_type = "generic"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run local test
            print("Running local test...")
            asyncio.run(test_mock_agent_locally())
        else:
            # First arg is agent type
            agent_type = sys.argv[1]
            
            # Second arg is port (optional)
            if len(sys.argv) > 2:
                port = int(sys.argv[2])
            
            # Run server
            run_mock_agent(port, agent_type)
    else:
        # Default: run generic mock agent
        run_mock_agent(port, agent_type)
