"""
Base Agent Class for SB Toolsmith Pro

Defines the interface and common behavior for all capability-based agents.
Agents are deterministic orchestrators, not LLM wrappers.
"""

import asyncio
import dataclasses
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentDecision(Enum):
    """Agent decision types."""
    PROCEED = "proceed"
    SKIP = "skip"
    RETRY = "retry"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"


@dataclasses.dataclass
class AgentAction:
    """Action proposed by an agent."""
    action_type: str
    description: str
    parameters: Dict[str, Any] = dataclasses.field(default_factory=dict)
    priority: int = 0
    reversible: bool = False
    estimated_duration_seconds: Optional[float] = None


@dataclasses.dataclass
class AgentDecisionRecord:
    """Record of an agent decision."""
    decision: AgentDecision
    reasoning: str
    timestamp: datetime = dataclasses.field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    alternatives: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class AgentExecutionResult:
    """Result of agent execution."""
    agent_id: str
    execution_id: str
    status: AgentStatus
    actions: List[AgentAction] = dataclasses.field(default_factory=list)
    decisions: List[AgentDecisionRecord] = dataclasses.field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


class Agent(ABC):
    """
    Base class for all agents.
    
    Agents are deterministic orchestrators that:
    - Consume structured events
    - Produce deterministic plans
    - Request validated runtime actions
    - Analyze failures and propose repairs
    - Never recursively self-prompt
    - Never spawn other agents autonomously
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """
        Initialize agent.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (planner, installer, etc.)
            event_bus: Event bus for communication
            runtime_manager: Runtime manager reference
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.event_bus = event_bus
        self.runtime_manager = runtime_manager
        self.status = AgentStatus.IDLE
        self._execution_history: List[AgentExecutionResult] = []
        self._lock = asyncio.Lock()

        logger.info(f"Initialized {agent_type} agent: {agent_id}")

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute agent logic.
        
        Args:
            context: Execution context with input data
            
        Returns:
            Execution result with actions and decisions
        """
        pass

    async def propose_action(self, action: AgentAction) -> bool:
        """
        Propose an action for execution.
        
        Args:
            action: Action to propose
            
        Returns:
            True if action was accepted
        """
        logger.info(
            f"Agent {self.agent_id} proposing action: {action.action_type}"
        )

        if self.event_bus:
            await self.event_bus.emit(
                "agent.action_proposed",
                {
                    "agent_id": self.agent_id,
                    "action": action,
                },
            )

        return True

    async def record_decision(
        self,
        decision: AgentDecision,
        reasoning: str,
        confidence: float = 1.0,
        alternatives: Optional[List[str]] = None,
    ) -> AgentDecisionRecord:
        """
        Record a decision made by the agent.
        
        Args:
            decision: Decision type
            reasoning: Reasoning for decision
            confidence: Confidence level (0-1)
            alternatives: Alternative options considered
            
        Returns:
            Decision record
        """
        record = AgentDecisionRecord(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            alternatives=alternatives or [],
        )

        logger.info(
            f"Agent {self.agent_id} decision: {decision.value} "
            f"(confidence: {confidence})"
        )

        if self.event_bus:
            await self.event_bus.emit(
                "agent.decision_made",
                {
                    "agent_id": self.agent_id,
                    "decision": record,
                },
            )

        return record

    async def get_execution_history(self) -> List[AgentExecutionResult]:
        """Get agent execution history."""
        async with self._lock:
            return self._execution_history.copy()

    async def get_last_execution(self) -> Optional[AgentExecutionResult]:
        """Get last execution result."""
        async with self._lock:
            if self._execution_history:
                return self._execution_history[-1]
        return None

    async def clear_history(self) -> None:
        """Clear execution history."""
        async with self._lock:
            self._execution_history.clear()

    def _create_result(
        self,
        status: AgentStatus,
        result: Any = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> AgentExecutionResult:
        """Create execution result."""
        return AgentExecutionResult(
            agent_id=self.agent_id,
            execution_id=str(uuid.uuid4()),
            status=status,
            result=result,
            error=error,
            duration_seconds=duration_seconds,
        )

    async def _record_execution(self, result: AgentExecutionResult) -> None:
        """Record execution result."""
        async with self._lock:
            self._execution_history.append(result)

        if self.event_bus:
            await self.event_bus.emit(
                "agent.execution_complete",
                {
                    "agent_id": self.agent_id,
                    "result": result,
                },
            )


class AgentOrchestrator:
    """
    Orchestrates multiple agents without creating recursive loops.
    
    Ensures:
    - Sequential or parallel agent execution
    - No recursive agent spawning
    - Structured communication
    - Decision validation
    """

    def __init__(self, event_bus: Optional[Any] = None):
        """
        Initialize orchestrator.
        
        Args:
            event_bus: Event bus for agent communication
        """
        self.event_bus = event_bus
        self._agents: Dict[str, Agent] = {}
        self._lock = asyncio.Lock()

    async def register_agent(self, agent: Agent) -> None:
        """Register an agent."""
        async with self._lock:
            self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")
                return True
        return False

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        async with self._lock:
            return self._agents.get(agent_id)

    async def execute_sequential(
        self,
        agent_ids: List[str],
        context: Dict[str, Any],
    ) -> List[AgentExecutionResult]:
        """
        Execute agents sequentially.
        
        Args:
            agent_ids: List of agent IDs to execute
            context: Shared execution context
            
        Returns:
            List of execution results
        """
        results = []

        for agent_id in agent_ids:
            agent = await self.get_agent(agent_id)
            if not agent:
                logger.warning(f"Agent not found: {agent_id}")
                continue

            try:
                logger.info(f"Executing agent: {agent_id}")
                result = await agent.execute(context)
                results.append(result)

                # Update context with result for next agent
                context[f"{agent_id}_result"] = result

            except Exception as e:
                logger.error(f"Agent {agent_id} failed: {e}", exc_info=True)
                results.append(
                    AgentExecutionResult(
                        agent_id=agent_id,
                        execution_id=str(uuid.uuid4()),
                        status=AgentStatus.FAILED,
                        error=str(e),
                    )
                )

        return results

    async def execute_parallel(
        self,
        agent_ids: List[str],
        context: Dict[str, Any],
    ) -> List[AgentExecutionResult]:
        """
        Execute agents in parallel.
        
        Args:
            agent_ids: List of agent IDs to execute
            context: Shared execution context
            
        Returns:
            List of execution results
        """
        tasks = []

        for agent_id in agent_ids:
            agent = await self.get_agent(agent_id)
            if agent:
                tasks.append(agent.execute(context))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    AgentExecutionResult(
                        agent_id=agent_ids[i],
                        execution_id=str(uuid.uuid4()),
                        status=AgentStatus.FAILED,
                        error=str(result),
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        async with self._lock:
            return {
                agent_id: {
                    "type": agent.agent_type,
                    "status": agent.status.value,
                }
                for agent_id, agent in self._agents.items()
            }
