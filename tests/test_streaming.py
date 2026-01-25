"""
Tests for streaming functionality.
"""

import asyncio
import pytest
from streaming.streaming_handler import StreamingHandler, ProgressTracker
from core.intent_classifier import IntentClassifier
from tasks.tools import TicketTool
from core.agent_router import ProcodeAgentRouter
from a2a.types import Message, TextPart

# Use anyio for async tests
pytestmark = pytest.mark.anyio


class TestStreamingHandler:
    """Test the StreamingHandler class."""
    
    async def test_stream_text_basic(self):
        """Test basic text streaming."""
        handler = StreamingHandler(chunk_size=2, delay=0.001)
        text = "Hello world from streaming"
        
        chunks = []
        async for part in handler.stream_text(text):
            chunks.append(part.text)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Reassembled text should match original
        reassembled = "".join(chunks)
        assert reassembled == text
    
    async def test_stream_text_empty(self):
        """Test streaming empty text."""
        handler = StreamingHandler()
        
        chunks = []
        async for part in handler.stream_text(""):
            chunks.append(part)
        
        assert len(chunks) == 0
    
    async def test_stream_progress(self):
        """Test progress message streaming."""
        handler = StreamingHandler(delay=0.001)
        messages = ["Step 1", "Step 2", "Step 3"]
        
        chunks = []
        async for part in handler.stream_progress(messages):
            chunks.append(part.text)
        
        assert len(chunks) == 3
        assert "Step 1\n" in chunks
        assert "Step 2\n" in chunks
        assert "Step 3\n" in chunks
    
    async def test_stream_with_progress(self):
        """Test streaming with progress followed by final text."""
        handler = StreamingHandler(chunk_size=3, delay=0.001)
        progress = ["Starting...", "Processing..."]
        final_text = "Task completed successfully"
        
        chunks = []
        async for part in handler.stream_with_progress(progress, final_text):
            chunks.append(part.text)
        
        # Should have progress messages + text chunks
        assert len(chunks) > 2
        assert "Starting...\n" in chunks
        assert "Processing...\n" in chunks


class TestProgressTracker:
    """Test the ProgressTracker class."""
    
    async def test_add_and_stream_steps(self):
        """Test adding and streaming progress steps."""
        tracker = ProgressTracker()
        tracker.add_step("Initialize")
        tracker.add_step("Process")
        tracker.add_step("Complete")
        
        chunks = []
        async for part in tracker.stream_all_steps():
            chunks.append(part.text)
        
        assert len(chunks) == 3
        assert "[1/3]" in chunks[0]
        assert "[2/3]" in chunks[1]
        assert "[3/3]" in chunks[2]
    
    async def test_stream_single_step(self):
        """Test streaming a single step."""
        tracker = ProgressTracker()
        tracker.add_step("Test step")
        
        chunks = []
        async for part in tracker.stream_step(0):
            chunks.append(part.text)
        
        assert len(chunks) == 1
        assert "Test step" in chunks[0]


class TestIntentClassifierStreaming:
    """Test streaming intent classification."""
    
    async def test_classify_intent_streaming_deterministic(self):
        """Test streaming classification with deterministic matching."""
        classifier = IntentClassifier(use_llm=False)
        
        results = []
        final_intent = None
        async for progress_msg, intent in classifier.classify_intent_streaming("create a ticket"):
            results.append(progress_msg)
            if intent:
                final_intent = intent
        
        # Should have progress messages
        assert len(results) > 0
        
        # Final intent should be tickets
        assert final_intent == "tickets"
    
    async def test_classify_intent_streaming_empty(self):
        """Test streaming classification with empty text."""
        classifier = IntentClassifier(use_llm=False)
        
        results = []
        final_intent = None
        async for progress_msg, intent in classifier.classify_intent_streaming(""):
            results.append(progress_msg)
            if intent:
                final_intent = intent
        
        assert final_intent == "unknown"
    
    async def test_classify_intent_streaming_account(self):
        """Test streaming classification for account intent."""
        classifier = IntentClassifier(use_llm=False)
        
        final_intent = None
        async for progress_msg, intent in classifier.classify_intent_streaming("show my account"):
            if intent:
                final_intent = intent
        
        assert final_intent == "account"
    
    async def test_classify_intent_streaming_payments(self):
        """Test streaming classification for payments intent."""
        classifier = IntentClassifier(use_llm=False)
        
        final_intent = None
        async for progress_msg, intent in classifier.classify_intent_streaming("make a payment"):
            if intent:
                final_intent = intent
        
        assert final_intent == "payments"


class TestTicketToolStreaming:
    """Test streaming ticket tool operations."""
    
    async def test_create_ticket_streaming_mocked(self):
        """Test streaming ticket creation with mocked tool."""
        tool = TicketTool(use_real=False)
        
        progress_messages = []
        final_result = None
        async for progress_msg, result in tool.create_ticket_streaming(
            "Test ticket", 
            "Test description"
        ):
            progress_messages.append(progress_msg)
            if result:
                final_result = result
        
        # Should have progress messages
        assert len(progress_messages) > 0
        
        # Should have final result
        assert final_result is not None
        assert final_result["title"] == "Test ticket"
        assert final_result["mocked"] is True
    
    async def test_get_ticket_streaming_mocked(self):
        """Test streaming ticket retrieval with mocked tool."""
        tool = TicketTool(use_real=False)
        
        progress_messages = []
        final_result = None
        async for progress_msg, result in tool.get_ticket_streaming("MOCK-001"):
            progress_messages.append(progress_msg)
            if result:
                final_result = result
        
        assert len(progress_messages) > 0
        assert final_result is not None
        assert final_result["id"] == "MOCK-001"
    
    async def test_list_tickets_streaming_mocked(self):
        """Test streaming ticket listing with mocked tool."""
        tool = TicketTool(use_real=False)
        
        progress_messages = []
        final_result = None
        async for progress_msg, result in tool.list_tickets_streaming("open"):
            progress_messages.append(progress_msg)
            if result:
                final_result = result
        
        assert len(progress_messages) > 0
        assert final_result is not None
        assert isinstance(final_result, list)
        assert len(final_result) > 0


class TestAgentRouterStreaming:
    """Test streaming agent router execution."""
    
    async def test_execute_streaming_basic(self):
        """Test basic streaming execution."""
        router = ProcodeAgentRouter(use_llm=False)
        
        # Create a mock context
        class MockContext:
            def __init__(self):
                self.message = Message(
                    role="user",
                    parts=[TextPart(text="create a support ticket")],
                    messageId="test-msg-1"
                )
                self.task_id = "test-task"
        
        context = MockContext()
        
        chunks = []
        async for part in router.execute_streaming(context):
            chunks.append(part.text)
        
        # Should have multiple chunks
        assert len(chunks) > 0
        
        # Should contain progress indicators
        full_response = "".join(chunks)
        assert "🤔" in full_response or "🔧" in full_response or "📋" in full_response
    
    async def test_execute_streaming_account(self):
        """Test streaming execution for account intent."""
        router = ProcodeAgentRouter(use_llm=False)
        
        class MockContext:
            def __init__(self):
                self.message = Message(
                    role="user",
                    parts=[TextPart(text="show my account info")],
                    messageId="test-msg-2"
                )
                self.task_id = "test-task-2"
        
        context = MockContext()
        
        chunks = []
        async for part in router.execute_streaming(context):
            chunks.append(part.text)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "account" in full_response.lower()
    
    async def test_execute_streaming_invalid_input(self):
        """Test streaming execution with invalid input."""
        router = ProcodeAgentRouter(use_llm=False)
        
        class MockContext:
            def __init__(self):
                self.message = Message(
                    role="user",
                    parts=[TextPart(text="")],
                    messageId="test-msg-3"
                )
                self.task_id = "test-task-3"
        
        context = MockContext()
        
        chunks = []
        async for part in router.execute_streaming(context):
            chunks.append(part.text)
        
        # Should handle invalid input gracefully
        assert len(chunks) > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
