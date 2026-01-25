
import os
from typing import AsyncGenerator, Optional
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Part, TextPart, Message
from a2a.utils import new_agent_text_message
from tasks.task_tickets import TicketsAgent
from tasks.task_account import AccountAgent
from tasks.task_payments import PaymentsAgent
from security.enhanced_guardrails import EnhancedGuardrails, get_global_enhanced_guardrails
from core.intent_classifier import IntentClassifier
from core.conversation_memory import get_conversation_memory
from streaming.streaming_handler import StreamingHandler
from a2a_comm.agent_discovery import AgentRegistry, get_global_registry
from a2a_comm.agent_client import AgentClient, AgentCommunicationError
from a2a_comm.agent_orchestrator import AgentOrchestrator

class ProcodeAgentRouter(AgentExecutor):
    """
    Principal agent router with LLM-based intent classification and A2A delegation.
    Falls back to deterministic routing if LLM is unavailable.
    Supports delegating tasks to other agents via A2A protocol.
    Enhanced with comprehensive security guardrails.
    """
    def __init__(self, use_llm: bool = None, enable_a2a: bool = True, use_enhanced_guardrails: bool = True):
        """
        Initialize the router.
        
        Args:
            use_llm: If True, use LLM for intent classification.
                    If False, use deterministic matching.
                    If None, check USE_LLM_INTENT environment variable (default: True)
            enable_a2a: If True, enable agent-to-agent communication
            use_enhanced_guardrails: If True, use enhanced guardrails with PII detection, rate limiting, etc.
        """
        self.tickets_agent = TicketsAgent()
        self.account_agent = AccountAgent()
        self.payments_agent = PaymentsAgent()
        
        # Determine whether to use LLM
        if use_llm is None:
            use_llm = os.getenv("USE_LLM_INTENT", "true").lower() == "true"
        
        self.intent_classifier = IntentClassifier(use_llm=use_llm)
        self.streaming_handler = StreamingHandler()
        
        # Enhanced guardrails
        self.use_enhanced_guardrails = use_enhanced_guardrails
        if use_enhanced_guardrails:
            self.guardrails = get_global_enhanced_guardrails()
        else:
            self.guardrails = None
        
        # A2A communication components
        self.enable_a2a = enable_a2a
        if enable_a2a:
            self.agent_registry = get_global_registry()
            self.orchestrator = AgentOrchestrator(self.agent_registry)
        else:
            self.agent_registry = None
            self.orchestrator = None

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Get conversation memory
        memory = get_conversation_memory()
        
        # Extract conversation ID (use task_id or message_id as conversation ID)
        conversation_id = None
        if hasattr(context, 'task_id') and context.task_id:
            conversation_id = context.task_id
        elif context.message and hasattr(context.message, 'message_id'):
            conversation_id = context.message.message_id
        else:
            conversation_id = "default"
        
        # Extract text from the message
        text = ""
        if context.message and context.message.parts:
            for part in context.message.parts:
                # The part is a Pydantic model with a root attribute
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    text += part.root.text
                elif hasattr(part, 'text') and part.text:
                    text += part.text
                elif isinstance(part, dict) and 'text' in part:
                    text += part['text']
        
        # Store user message in conversation history
        memory.add_message(conversation_id, "user", text)
        
        # Get conversation history for context
        history = memory.get_history(conversation_id, max_messages=5)  # Last 5 messages
        
        # Create a simple context object with conversation history
        class SimpleContext:
            class Input:
                def __init__(self, text, history):
                    self.text = text
                    self.history = history
            def __init__(self, text, history):
                self.input = self.Input(text, history)
                self.conversation_id = conversation_id
        
        simple_context = SimpleContext(text, history)
        
        # Input validation with enhanced guardrails
        if self.use_enhanced_guardrails:
            is_valid, error_msg = self.guardrails.validate_input(text, user_id=conversation_id)
            if not is_valid:
                result = f"❌ {error_msg}"
                # Store error in conversation history
                memory.add_message(conversation_id, "agent", result, metadata={"error": "validation_failed"})
                await event_queue.enqueue_event(new_agent_text_message(result))
                return
        else:
            # Fallback to basic validation
            from security.guardrails import validate_input
            if not validate_input(simple_context):
                result = "Invalid input"
                memory.add_message(conversation_id, "agent", result, metadata={"error": "validation_failed"})
                await event_queue.enqueue_event(new_agent_text_message(result))
                return
        
        # Process the request
        # Check if this should be delegated to another agent
        if self._should_delegate(text):
            result = await self._delegate_to_agent(text, context)
            intent = "delegation"
        else:
            # Classify intent using LLM or deterministic matching
            intent = self.intent_classifier.classify_intent(text)
            
            # Route to appropriate agent based on intent
            if intent == "tickets":
                result = await self.tickets_agent.invoke(simple_context)
            elif intent == "account":
                result = await self.account_agent.invoke(simple_context)
            elif intent == "payments":
                result = await self.payments_agent.invoke(simple_context)
            else:
                result = "Unknown intent"
        
        # Output validation with enhanced guardrails
        if self.use_enhanced_guardrails:
            # Sanitize output to remove PII
            result = self.guardrails.sanitize_output(result, redact_pii=True)
            is_valid, error_msg = self.guardrails.validate_output(result)
            if not is_valid:
                result = f"❌ Output validation failed: {error_msg}"
        else:
            # Fallback to basic validation
            from security.guardrails import validate_output
            if not validate_output(result):
                result = "Output validation failed"
        
        # Store agent response in conversation history
        memory.add_message(conversation_id, "agent", result, metadata={"intent": intent})
        
        # Send result as a message
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def execute_streaming(self, context: RequestContext) -> AsyncGenerator[Part, None]:
        """
        Execute with streaming responses for real-time feedback.
        
        Args:
            context: Request context
            
        Yields:
            Part objects containing streaming response chunks
        """
        # Get conversation memory
        memory = get_conversation_memory()
        
        # Extract conversation ID
        conversation_id = None
        if hasattr(context, 'task_id') and context.task_id:
            conversation_id = context.task_id
        elif context.message and hasattr(context.message, 'message_id'):
            conversation_id = context.message.message_id
        else:
            conversation_id = "default"
        
        # Extract text from the message
        text = ""
        if context.message and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    text += part.root.text
                elif hasattr(part, 'text') and part.text:
                    text += part.text
                elif isinstance(part, dict) and 'text' in part:
                    text += part['text']
        
        # Store user message
        memory.add_message(conversation_id, "user", text)
        
        # Get conversation history
        history = memory.get_history(conversation_id, max_messages=5)
        
        # Create simple context
        class SimpleContext:
            class Input:
                def __init__(self, text, history):
                    self.text = text
                    self.history = history
            def __init__(self, text, history):
                self.input = self.Input(text, history)
                self.conversation_id = conversation_id
        
        simple_context = SimpleContext(text, history)
        
        # Input validation with enhanced guardrails
        if self.use_enhanced_guardrails:
            is_valid, error_msg = self.guardrails.validate_input(text, user_id=conversation_id)
            if not is_valid:
                yield TextPart(text=f"❌ {error_msg}\n")
                return
        else:
            # Fallback to basic validation
            from security.guardrails import validate_input
            if not validate_input(simple_context):
                yield TextPart(text="❌ Invalid input\n")
                return
        
        # Stream intent classification
        intent = None
        async for progress_msg, classified_intent in self.intent_classifier.classify_intent_streaming(text):
            yield TextPart(text=progress_msg + "\n")
            if classified_intent:
                intent = classified_intent
        
        if not intent:
            yield TextPart(text="❌ Could not determine intent\n")
            return
        
        # Stream tool execution based on intent
        yield TextPart(text=f"\n🔧 Executing {intent} task...\n")
        
        # Route to appropriate agent and get result
        result = None
        if intent == "tickets":
            result = await self.tickets_agent.invoke(simple_context)
        elif intent == "account":
            result = await self.account_agent.invoke(simple_context)
        elif intent == "payments":
            result = await self.payments_agent.invoke(simple_context)
        else:
            result = "Unknown intent"
        
        # Validate and sanitize output with enhanced guardrails
        if self.use_enhanced_guardrails:
            # Sanitize output to remove PII
            result = self.guardrails.sanitize_output(result, redact_pii=True)
            is_valid, error_msg = self.guardrails.validate_output(result)
            if not is_valid:
                yield TextPart(text=f"❌ Output validation failed: {error_msg}\n")
                return
        else:
            # Fallback to basic validation
            from security.guardrails import validate_output
            if not validate_output(result):
                yield TextPart(text="❌ Output validation failed\n")
                return
        
        # Store agent response
        memory.add_message(conversation_id, "agent", result, metadata={"intent": intent})
        
        # Stream the final result
        yield TextPart(text="\n📋 Result:\n")
        async for part in self.streaming_handler.stream_text(result):
            yield part

    def _should_delegate(self, text: str) -> bool:
        """
        Determine if the task should be delegated to another agent.
        
        Args:
            text: User input text
            
        Returns:
            True if task should be delegated, False otherwise
        """
        if not self.enable_a2a:
            return False
        
        # Keywords that indicate delegation
        delegation_keywords = [
            "ask the", "check with", "consult", "delegate to",
            "get help from", "forward to", "send to", "talk to"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in delegation_keywords)
    
    def _extract_agent_name(self, text: str) -> Optional[str]:
        """
        Extract target agent name from delegation request.
        
        Args:
            text: User input text
            
        Returns:
            Agent name if found, None otherwise
        """
        # Simple extraction - look for agent names in registry
        text_lower = text.lower()
        
        for agent_name in self.agent_registry.agents.keys():
            if agent_name.lower() in text_lower:
                return agent_name
        
        return None
    
    def _extract_task_from_delegation(self, text: str, agent_name: str) -> str:
        """
        Extract the actual task from a delegation request.
        
        Args:
            text: User input text
            agent_name: Name of the target agent
            
        Returns:
            Extracted task description
        """
        # Remove delegation keywords and agent name
        task = text.lower()
        
        # Remove common delegation phrases
        delegation_phrases = [
            f"ask the {agent_name}", f"check with {agent_name}",
            f"consult {agent_name}", f"delegate to {agent_name}",
            f"get help from {agent_name}", f"forward to {agent_name}",
            f"send to {agent_name}", f"talk to {agent_name}",
            "to ", "about "
        ]
        
        for phrase in delegation_phrases:
            task = task.replace(phrase, "")
        
        return task.strip()
    
    async def _delegate_to_agent(
        self,
        text: str,
        context: RequestContext
    ) -> str:
        """
        Delegate task to another agent via A2A protocol.
        
        Args:
            text: User input text
            context: Request context
            
        Returns:
            Result from the delegated agent
        """
        # Extract agent name and task
        agent_name = self._extract_agent_name(text)
        
        if not agent_name:
            return "❌ Could not identify which agent to delegate to. Please specify the agent name."
        
        # Find agent in registry
        agent_card = self.agent_registry.get_agent(agent_name)
        if not agent_card:
            return f"❌ Agent '{agent_name}' not found in registry."
        
        # Extract the actual task
        task = self._extract_task_from_delegation(text, agent_name)
        if not task:
            task = text  # Use full text if extraction fails
        
        # Create client and delegate
        client = AgentClient(agent_card.url)
        try:
            task_id = context.task_id if hasattr(context, 'task_id') else None
            result = await client.delegate_task(task, task_id)
            return f"✅ Delegated to {agent_name}:\n{result}"
        except AgentCommunicationError as e:
            return f"❌ Failed to communicate with {agent_name}: {e}"
        except Exception as e:
            return f"❌ Unexpected error during delegation: {e}"
        finally:
            await client.close()
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Cancel not supported in v1
        await event_queue.enqueue_event(new_agent_text_message("Cancel not supported in this version."))
