"""
Agent Orchestrator Module

This module provides functionality for orchestrating multi-agent workflows,
including sequential and parallel task execution across multiple agents.
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
from dataclasses import dataclass, field
from enum import Enum
import uuid

from a2a_comm.agent_discovery import AgentRegistry, AgentCard
from a2a_comm.agent_client import AgentClient, AgentClientPool, AgentCommunicationError
from a2a.server.agent_execution import RequestContext


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    Attributes:
        agent: Name or capability of the agent to execute this step
        task: Task description to send to the agent
        depends_on: List of step indices this step depends on
        step_id: Unique identifier for this step
        status: Current status of the step
        result: Result from executing the step
        error: Error message if step failed
    """
    agent: str
    task: str
    depends_on: List[int] = field(default_factory=list)
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert step to dictionary."""
        return {
            "agent": self.agent,
            "task": self.task,
            "depends_on": self.depends_on,
            "step_id": self.step_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.
    
    Attributes:
        workflow_id: Unique identifier for the workflow
        status: Overall workflow status
        steps: List of workflow steps with results
        execution_time: Total execution time in seconds
        error: Error message if workflow failed
    """
    workflow_id: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    execution_time: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "execution_time": self.execution_time,
            "error": self.error
        }
    
    def get_step_results(self) -> List[str]:
        """Get list of successful step results."""
        return [step.result for step in self.steps if step.result]


class AgentOrchestrator:
    """
    Orchestrate multi-agent workflows.
    
    This orchestrator supports:
    - Sequential workflow execution with dependencies
    - Parallel task execution
    - Error handling and recovery
    - Progress tracking
    """
    
    def __init__(
        self,
        registry: AgentRegistry,
        client_pool: Optional[AgentClientPool] = None,
        timeout: int = 30
    ):
        """
        Initialize the orchestrator.
        
        Args:
            registry: Agent registry for discovering agents
            client_pool: Optional client pool for reusing connections
            timeout: Default timeout for agent communication
        """
        self.registry = registry
        self.client_pool = client_pool or AgentClientPool(timeout=timeout)
        self.timeout = timeout
        self._active_workflows: Dict[str, WorkflowResult] = {}
    
    async def execute_workflow(
        self,
        steps: List[Dict[str, Any]],
        context: Optional[RequestContext] = None,
        workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Execute a multi-step workflow with dependencies.
        
        Args:
            steps: List of workflow step definitions
            context: Optional execution context
            workflow_id: Optional workflow identifier
            
        Returns:
            WorkflowResult with execution details
            
        Example:
            steps = [
                {"agent": "ticket_agent", "task": "Create ticket", "depends_on": []},
                {"agent": "notify_agent", "task": "Send notification", "depends_on": [0]}
            ]
        """
        import time
        start_time = time.time()
        
        # Create workflow ID
        wf_id = workflow_id or str(uuid.uuid4())
        
        # Parse steps
        workflow_steps = [
            WorkflowStep(
                agent=step["agent"],
                task=step["task"],
                depends_on=step.get("depends_on", [])
            )
            for step in steps
        ]
        
        # Create result object
        result = WorkflowResult(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
            steps=workflow_steps
        )
        self._active_workflows[wf_id] = result
        
        try:
            # Execute steps in order, respecting dependencies
            for i, step in enumerate(workflow_steps):
                step.status = WorkflowStatus.RUNNING
                
                # Wait for dependencies
                if step.depends_on:
                    await self._wait_for_dependencies(step.depends_on, workflow_steps)
                    
                    # Check if any dependency failed
                    if any(workflow_steps[dep].status == WorkflowStatus.FAILED 
                           for dep in step.depends_on):
                        step.status = WorkflowStatus.FAILED
                        step.error = "Dependency failed"
                        continue
                
                # Find agent
                agent_card = self._find_agent(step.agent)
                if not agent_card:
                    step.status = WorkflowStatus.FAILED
                    step.error = f"Agent not found: {step.agent}"
                    continue
                
                # Execute step
                try:
                    client = self.client_pool.get_client(agent_card.url)
                    task_id = context.task_id if context else wf_id
                    step.result = await client.delegate_task(step.task, task_id)
                    step.status = WorkflowStatus.COMPLETED
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
            
            # Determine overall status
            if all(s.status == WorkflowStatus.COMPLETED for s in workflow_steps):
                result.status = WorkflowStatus.COMPLETED
            elif any(s.status == WorkflowStatus.FAILED for s in workflow_steps):
                result.status = WorkflowStatus.FAILED
                result.error = "One or more steps failed"
            
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = f"Workflow execution error: {e}"
        
        finally:
            result.execution_time = time.time() - start_time
            del self._active_workflows[wf_id]
        
        return result
    
    async def execute_parallel(
        self,
        tasks: List[Dict[str, str]],
        context: Optional[RequestContext] = None,
        workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Execute multiple tasks in parallel across different agents.
        
        Args:
            tasks: List of task definitions with 'agent' and 'task' keys
            context: Optional execution context
            workflow_id: Optional workflow identifier
            
        Returns:
            WorkflowResult with execution details
            
        Example:
            tasks = [
                {"agent": "analytics_agent", "task": "Analyze data"},
                {"agent": "security_agent", "task": "Check security"},
                {"agent": "performance_agent", "task": "Review metrics"}
            ]
        """
        import time
        start_time = time.time()
        
        # Create workflow ID
        wf_id = workflow_id or str(uuid.uuid4())
        
        # Create workflow steps
        workflow_steps = [
            WorkflowStep(agent=task["agent"], task=task["task"])
            for task in tasks
        ]
        
        # Create result object
        result = WorkflowResult(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
            steps=workflow_steps
        )
        self._active_workflows[wf_id] = result
        
        try:
            # Execute all tasks in parallel
            async def execute_task(step: WorkflowStep) -> None:
                """Execute a single task."""
                step.status = WorkflowStatus.RUNNING
                
                try:
                    # Find agent
                    agent_card = self._find_agent(step.agent)
                    if not agent_card:
                        step.status = WorkflowStatus.FAILED
                        step.error = f"Agent not found: {step.agent}"
                        return
                    
                    # Execute task
                    client = self.client_pool.get_client(agent_card.url)
                    task_id = context.task_id if context else wf_id
                    step.result = await client.delegate_task(step.task, task_id)
                    step.status = WorkflowStatus.COMPLETED
                
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
            
            # Run all tasks concurrently
            await asyncio.gather(
                *[execute_task(step) for step in workflow_steps],
                return_exceptions=True
            )
            
            # Determine overall status
            if all(s.status == WorkflowStatus.COMPLETED for s in workflow_steps):
                result.status = WorkflowStatus.COMPLETED
            elif any(s.status == WorkflowStatus.FAILED for s in workflow_steps):
                result.status = WorkflowStatus.FAILED
                result.error = "One or more tasks failed"
        
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = f"Parallel execution error: {e}"
        
        finally:
            result.execution_time = time.time() - start_time
            del self._active_workflows[wf_id]
        
        return result
    
    async def execute_with_fallback(
        self,
        task: str,
        agent_names: List[str],
        context: Optional[RequestContext] = None
    ) -> str:
        """
        Execute a task with fallback to alternative agents.
        
        Args:
            task: Task description
            agent_names: List of agent names to try in order
            context: Optional execution context
            
        Returns:
            Result from first successful agent
            
        Raises:
            AgentCommunicationError: If all agents fail
        """
        last_error = None
        
        for agent_name in agent_names:
            try:
                agent_card = self._find_agent(agent_name)
                if not agent_card:
                    continue
                
                client = self.client_pool.get_client(agent_card.url)
                task_id = context.task_id if context else str(uuid.uuid4())
                result = await client.delegate_task(task, task_id)
                return result
            
            except Exception as e:
                last_error = e
                continue
        
        # All agents failed
        raise AgentCommunicationError(
            f"All agents failed. Last error: {last_error}"
        )
    
    def _find_agent(self, agent_identifier: str) -> Optional[AgentCard]:
        """
        Find agent by name or capability.
        
        Args:
            agent_identifier: Agent name or capability
            
        Returns:
            AgentCard if found, None otherwise
        """
        # Try by name first
        agent = self.registry.get_agent(agent_identifier)
        if agent:
            return agent
        
        # Try by capability
        agent = self.registry.find_agent(agent_identifier)
        return agent
    
    async def _wait_for_dependencies(
        self,
        dependencies: List[int],
        steps: List[WorkflowStep],
        poll_interval: float = 0.1,
        timeout: float = 300.0
    ):
        """
        Wait for dependent steps to complete.
        
        Args:
            dependencies: List of step indices to wait for
            steps: List of all workflow steps
            poll_interval: How often to check status (seconds)
            timeout: Maximum time to wait (seconds)
            
        Raises:
            TimeoutError: If dependencies don't complete in time
        """
        import time
        start_time = time.time()
        
        while True:
            # Check if all dependencies are complete
            all_complete = all(
                steps[dep].status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
                for dep in dependencies
            )
            
            if all_complete:
                return
            
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Dependencies did not complete within {timeout} seconds"
                )
            
            # Wait before checking again
            await asyncio.sleep(poll_interval)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """
        Get status of an active workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            WorkflowResult if workflow is active, None otherwise
        """
        return self._active_workflows.get(workflow_id)
    
    def list_active_workflows(self) -> List[str]:
        """
        List IDs of all active workflows.
        
        Returns:
            List of workflow IDs
        """
        return list(self._active_workflows.keys())
    
    async def close(self):
        """Close all client connections."""
        await self.client_pool.close_all()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
