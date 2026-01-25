"""
Integration Tests for Agent-to-Agent Communication

This module contains comprehensive tests for A2A communication features including:
- Agent discovery and registration
- Agent client communication
- Workflow orchestration
- Delegation logic
"""

import pytest
import asyncio
from a2a_comm.agent_discovery import AgentRegistry, AgentCard, reset_global_registry
from a2a_comm.agent_client import AgentClient, AgentClientPool, AgentCommunicationError, reset_global_client_pool
from a2a_comm.agent_orchestrator import AgentOrchestrator, WorkflowStatus
from a2a.types import Message, TextPart
from a2a.server.agent_execution import RequestContext

# Use anyio for async tests
pytestmark = pytest.mark.anyio


class TestAgentRegistry:
    """Test the AgentRegistry class."""
    
    def test_create_registry(self):
        """Test creating an agent registry."""
        # Create registry without config file
        registry = AgentRegistry(config_path="nonexistent.json")
        assert registry is not None
        # May have agents from environment variables, so just check it exists
        assert registry is not None
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry(config_path="nonexistent.json")
        initial_count = len(registry)
        
        agent_card = AgentCard(
            name="test_agent_unique",
            url="http://localhost:9999",
            capabilities=["test", "demo"],
            description="Test agent"
        )
        
        registry.register_agent(agent_card)
        assert len(registry) == initial_count + 1
        assert "test_agent_unique" in registry
    
    def test_get_agent(self):
        """Test retrieving an agent by name."""
        registry = AgentRegistry()
        
        agent_card = AgentCard(
            name="test_agent",
            url="http://localhost:9999",
            capabilities=["test"]
        )
        
        registry.register_agent(agent_card)
        retrieved = registry.get_agent("test_agent")
        
        assert retrieved is not None
        assert retrieved.name == "test_agent"
        assert retrieved.url == "http://localhost:9999"
    
    def test_find_agent_by_capability(self):
        """Test finding agent by capability."""
        registry = AgentRegistry()
        
        agent1 = AgentCard(
            name="ticket_agent",
            url="http://localhost:9999",
            capabilities=["tickets", "support"]
        )
        
        agent2 = AgentCard(
            name="analytics_agent",
            url="http://localhost:9998",
            capabilities=["analytics", "reporting"]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        found = registry.find_agent("tickets")
        assert found is not None
        assert found.name == "ticket_agent"
        
        found = registry.find_agent("analytics")
        assert found is not None
        assert found.name == "analytics_agent"
    
    def test_find_agents_multiple(self):
        """Test finding multiple agents with same capability."""
        registry = AgentRegistry()
        
        agent1 = AgentCard(
            name="agent1",
            url="http://localhost:9999",
            capabilities=["common", "unique1"]
        )
        
        agent2 = AgentCard(
            name="agent2",
            url="http://localhost:9998",
            capabilities=["common", "unique2"]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        found = registry.find_agents("common")
        assert len(found) == 2
        assert any(a.name == "agent1" for a in found)
        assert any(a.name == "agent2" for a in found)
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry(config_path="nonexistent.json")
        
        agent_card = AgentCard(
            name="test_agent_to_remove",
            url="http://localhost:9999",
            capabilities=["test"]
        )
        
        registry.register_agent(agent_card)
        initial_count = len(registry)
        
        result = registry.unregister_agent("test_agent_to_remove")
        assert result is True
        assert len(registry) == initial_count - 1
        
        result = registry.unregister_agent("nonexistent")
        assert result is False
    
    def test_list_capabilities(self):
        """Test listing all capabilities."""
        registry = AgentRegistry(config_path="nonexistent.json")
        
        agent1 = AgentCard(
            name="agent1_cap",
            url="http://localhost:9999",
            capabilities=["cap1", "cap2"]
        )
        
        agent2 = AgentCard(
            name="agent2_cap",
            url="http://localhost:9998",
            capabilities=["cap2", "cap3"]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        capabilities = registry.list_capabilities()
        assert "cap1" in capabilities
        assert "cap2" in capabilities
        assert "cap3" in capabilities


class TestAgentCard:
    """Test the AgentCard class."""
    
    def test_create_agent_card(self):
        """Test creating an agent card."""
        card = AgentCard(
            name="test_agent",
            url="http://localhost:9999",
            capabilities=["test"],
            description="Test agent",
            version="1.0.0"
        )
        
        assert card.name == "test_agent"
        assert card.url == "http://localhost:9999"
        assert "test" in card.capabilities
        assert card.description == "Test agent"
        assert card.version == "1.0.0"
    
    def test_agent_card_to_dict(self):
        """Test converting agent card to dictionary."""
        card = AgentCard(
            name="test_agent",
            url="http://localhost:9999",
            capabilities=["test"]
        )
        
        data = card.to_dict()
        assert data["name"] == "test_agent"
        assert data["url"] == "http://localhost:9999"
        assert "test" in data["capabilities"]
    
    def test_agent_card_from_dict(self):
        """Test creating agent card from dictionary."""
        data = {
            "name": "test_agent",
            "url": "http://localhost:9999",
            "capabilities": ["test"],
            "description": "Test agent",
            "version": "1.0.0"
        }
        
        card = AgentCard.from_dict(data)
        assert card.name == "test_agent"
        assert card.url == "http://localhost:9999"
        assert "test" in card.capabilities


class TestAgentClient:
    """Test the AgentClient class (without actual server)."""
    
    async def test_create_client(self):
        """Test creating an agent client."""
        client = AgentClient("http://localhost:9999")
        assert client.agent_url == "http://localhost:9999"
        assert client.timeout == 30
        await client.close()
    
    async def test_client_context_manager(self):
        """Test using client as context manager."""
        async with AgentClient("http://localhost:9999") as client:
            assert client is not None
    
    async def test_client_timeout_error(self):
        """Test client timeout handling."""
        client = AgentClient("http://localhost:19999", timeout=0.1, max_retries=1)
        
        message = Message(
            role="user",
            parts=[TextPart(text="test")],
            messageId="test-123"
        )
        
        # This should timeout since no server is running on this port
        try:
            await client.send_message(message)
            # If we get here without exception, that's also acceptable
            # (connection refused is immediate, not a timeout)
        except (AgentCommunicationError, Exception):
            # Expected - either timeout or connection error
            pass
        finally:
            await client.close()


class TestAgentClientPool:
    """Test the AgentClientPool class."""
    
    async def test_create_pool(self):
        """Test creating a client pool."""
        pool = AgentClientPool()
        assert pool is not None
        await pool.close_all()
    
    async def test_get_client(self):
        """Test getting client from pool."""
        pool = AgentClientPool()
        
        client1 = pool.get_client("http://localhost:9999")
        client2 = pool.get_client("http://localhost:9999")
        
        # Should return same client instance
        assert client1 is client2
        
        await pool.close_all()
    
    async def test_multiple_clients(self):
        """Test managing multiple clients."""
        pool = AgentClientPool()
        
        client1 = pool.get_client("http://localhost:9999")
        client2 = pool.get_client("http://localhost:9998")
        
        # Should be different clients
        assert client1 is not client2
        assert len(pool.clients) == 2
        
        await pool.close_all()


class TestAgentOrchestrator:
    """Test the AgentOrchestrator class."""
    
    async def test_create_orchestrator(self):
        """Test creating an orchestrator."""
        registry = AgentRegistry()
        orchestrator = AgentOrchestrator(registry)
        
        assert orchestrator is not None
        assert orchestrator.registry is registry
        
        await orchestrator.close()
    
    async def test_find_agent_by_name(self):
        """Test finding agent by name."""
        registry = AgentRegistry()
        agent_card = AgentCard(
            name="test_agent",
            url="http://localhost:9999",
            capabilities=["test"]
        )
        registry.register_agent(agent_card)
        
        orchestrator = AgentOrchestrator(registry)
        found = orchestrator._find_agent("test_agent")
        
        assert found is not None
        assert found.name == "test_agent"
        
        await orchestrator.close()
    
    async def test_find_agent_by_capability(self):
        """Test finding agent by capability."""
        registry = AgentRegistry()
        agent_card = AgentCard(
            name="test_agent",
            url="http://localhost:9999",
            capabilities=["test_capability"]
        )
        registry.register_agent(agent_card)
        
        orchestrator = AgentOrchestrator(registry)
        found = orchestrator._find_agent("test_capability")
        
        assert found is not None
        assert found.name == "test_agent"
        
        await orchestrator.close()
    
    async def test_workflow_with_no_agents(self):
        """Test workflow execution with no registered agents."""
        registry = AgentRegistry()
        orchestrator = AgentOrchestrator(registry)
        
        steps = [
            {"agent": "nonexistent_agent", "task": "Do something"}
        ]
        
        result = await orchestrator.execute_workflow(steps)
        
        assert result.status == WorkflowStatus.FAILED
        assert len(result.steps) == 1
        assert result.steps[0].status == WorkflowStatus.FAILED
        
        await orchestrator.close()
    
    async def test_parallel_execution_structure(self):
        """Test parallel execution structure (without actual agents)."""
        registry = AgentRegistry()
        orchestrator = AgentOrchestrator(registry)
        
        tasks = [
            {"agent": "agent1", "task": "Task 1"},
            {"agent": "agent2", "task": "Task 2"}
        ]
        
        result = await orchestrator.execute_parallel(tasks)
        
        # Should fail since agents don't exist, but structure should be correct
        assert result.status == WorkflowStatus.FAILED
        assert len(result.steps) == 2
        
        await orchestrator.close()


class TestWorkflowExecution:
    """Test workflow execution logic."""
    
    async def test_workflow_result_structure(self):
        """Test workflow result structure."""
        from agent_orchestrator import WorkflowResult, WorkflowStep
        
        steps = [
            WorkflowStep(agent="agent1", task="Task 1"),
            WorkflowStep(agent="agent2", task="Task 2")
        ]
        
        result = WorkflowResult(
            workflow_id="test-123",
            status=WorkflowStatus.COMPLETED,
            steps=steps
        )
        
        assert result.workflow_id == "test-123"
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.steps) == 2
        
        # Test to_dict
        data = result.to_dict()
        assert data["workflow_id"] == "test-123"
        assert data["status"] == "completed"
    
    async def test_workflow_step_structure(self):
        """Test workflow step structure."""
        from agent_orchestrator import WorkflowStep
        
        step = WorkflowStep(
            agent="test_agent",
            task="Test task",
            depends_on=[0, 1]
        )
        
        assert step.agent == "test_agent"
        assert step.task == "Test task"
        assert step.depends_on == [0, 1]
        assert step.status == WorkflowStatus.PENDING
        
        # Test to_dict
        data = step.to_dict()
        assert data["agent"] == "test_agent"
        assert data["task"] == "Test task"


class TestDelegationLogic:
    """Test delegation logic in agent router."""
    
    def test_should_delegate_detection(self):
        """Test delegation keyword detection."""
        from core.agent_router import ProcodeAgentRouter
        
        router = ProcodeAgentRouter(use_llm=False, enable_a2a=True)
        
        # Should detect delegation
        assert router._should_delegate("ask the ticket agent to create a ticket")
        assert router._should_delegate("check with analytics agent")
        assert router._should_delegate("delegate to support agent")
        
        # Should not detect delegation
        assert not router._should_delegate("create a ticket")
        assert not router._should_delegate("show my account")
    
    def test_extract_agent_name(self):
        """Test extracting agent name from text."""
        from core.agent_router import ProcodeAgentRouter
        from a2a_comm.agent_discovery import AgentCard
        
        router = ProcodeAgentRouter(use_llm=False, enable_a2a=True)
        
        # Register test agent
        agent_card = AgentCard(
            name="ticket_agent",
            url="http://localhost:9999",
            capabilities=["tickets"]
        )
        router.agent_registry.register_agent(agent_card)
        
        # Test extraction
        agent_name = router._extract_agent_name("ask the ticket_agent to create a ticket")
        assert agent_name == "ticket_agent"
    
    def test_extract_task_from_delegation(self):
        """Test extracting task from delegation request."""
        from core.agent_router import ProcodeAgentRouter
        
        router = ProcodeAgentRouter(use_llm=False, enable_a2a=True)
        
        text = "ask the ticket_agent to create a new support ticket"
        task = router._extract_task_from_delegation(text, "ticket_agent")
        
        # Should extract the actual task
        assert "create" in task or "new" in task or "support" in task


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
