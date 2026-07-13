"""
PlannerAgent for SB Toolsmith Pro

Analyzes tool dependencies and generates optimized execution DAGs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from core.dag_engine import DAGGraph, Edge, NodeDefinition, Port, PortType
from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class PlannerAgent(Agent):
    """
    Planner Agent - Generates execution plans and DAGs.
    
    Responsibilities:
    - Analyze tool dependencies
    - Build execution DAGs
    - Validate graph topology
    - Optimize execution order
    - Detect circular dependencies
    - Propose parallel execution paths
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize planner agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="planner",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute planner logic.
        
        Args:
            context: Execution context containing:
                - tools: List of tools to plan
                - dependencies: Tool dependency graph
                - constraints: Execution constraints
                
        Returns:
            Execution result with generated DAG
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            tools = context.get("tools", [])
            dependencies = context.get("dependencies", {})
            constraints = context.get("constraints", {})

            logger.info(
                f"PlannerAgent starting execution for {len(tools)} tools"
            )

            # Validate input
            if not tools:
                logger.warning("No tools provided for planning")
                decision = await self.record_decision(
                    AgentDecision.SKIP,
                    "No tools to plan",
                )
                result = self._create_result(
                    AgentStatus.COMPLETED,
                    result={"graph": None, "decisions": [decision]},
                )
                await self._record_execution(result)
                return result

            # Build DAG
            graph = await self._build_dag(tools, dependencies, constraints)

            # Validate graph
            is_valid, error = graph.validate()
            if not is_valid:
                logger.error(f"Generated invalid graph: {error}")
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    f"Invalid graph generated: {error}",
                    confidence=0.5,
                )
                result = self._create_result(
                    AgentStatus.FAILED,
                    error=error,
                )
                await self._record_execution(result)
                return result

            # Analyze execution order
            execution_order = graph.get_execution_order()
            logger.info(f"Generated execution order: {execution_order}")

            # Detect parallelizable nodes
            parallelizable = await self._detect_parallelizable_nodes(graph)

            # Record decision
            decision = await self.record_decision(
                AgentDecision.PROCEED,
                f"Generated DAG with {len(graph.nodes)} nodes, "
                f"{len(parallelizable)} parallelizable",
                confidence=0.95,
            )

            # Propose action
            action = AgentAction(
                action_type="execute_dag",
                description=f"Execute DAG with {len(graph.nodes)} nodes",
                parameters={
                    "graph_id": graph.graph_id,
                    "execution_order": execution_order,
                    "parallelizable_groups": parallelizable,
                },
                priority=1,
                reversible=False,
            )
            await self.propose_action(action)

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=AgentStatus.COMPLETED,
                actions=[action],
                decisions=[decision],
                result={
                    "graph": graph.to_dict(),
                    "execution_order": execution_order,
                    "parallelizable": parallelizable,
                },
                duration_seconds=duration,
            )

            self.status = AgentStatus.COMPLETED
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"PlannerAgent failed: {e}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=AgentStatus.FAILED,
                error=str(e),
                duration_seconds=duration,
            )

            self.status = AgentStatus.FAILED
            await self._record_execution(result)

            return result

    async def _build_dag(
        self,
        tools: List[Dict[str, Any]],
        dependencies: Dict[str, List[str]],
        constraints: Dict[str, Any],
    ) -> DAGGraph:
        """
        Build execution DAG from tools and dependencies.
        
        Args:
            tools: List of tool definitions
            dependencies: Dependency map
            constraints: Execution constraints
            
        Returns:
            Generated DAG
        """
        graph = DAGGraph(graph_id=f"plan_{id(tools)}")

        # Add nodes for each tool
        for tool in tools:
            tool_key = tool.get("key", tool.get("id"))
            node = NodeDefinition(
                node_id=tool_key,
                node_type="tool_execution",
                inputs=[
                    Port(
                        name="input",
                        port_type=PortType.ANY,
                        required=False,
                    )
                ],
                outputs=[
                    Port(
                        name="output",
                        port_type=PortType.ANY,
                        required=False,
                    )
                ],
                config={
                    "tool_key": tool_key,
                    "name": tool.get("name", tool_key),
                    "command": tool.get("command"),
                },
            )
            graph.add_node(node)

        # Add edges based on dependencies
        for tool_key, deps in dependencies.items():
            for dep in deps:
                if dep in [t.get("key", t.get("id")) for t in tools]:
                    edge = Edge(
                        from_node=dep,
                        from_port="output",
                        to_node=tool_key,
                        to_port="input",
                    )
                    graph.add_edge(edge)

        logger.info(f"Built DAG with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        return graph

    async def _detect_parallelizable_nodes(
        self,
        graph: DAGGraph,
    ) -> List[List[str]]:
        """
        Detect groups of nodes that can execute in parallel.
        
        Args:
            graph: DAG to analyze
            
        Returns:
            List of parallelizable node groups
        """
        groups = []
        processed = set()

        for node_id in graph.nodes:
            if node_id in processed:
                continue

            # Find all nodes with same dependencies
            deps = graph.get_dependencies(node_id)
            group = [node_id]

            for other_id in graph.nodes:
                if other_id != node_id and other_id not in processed:
                    other_deps = graph.get_dependencies(other_id)
                    if deps == other_deps:
                        group.append(other_id)

            if len(group) > 1:
                groups.append(group)
                processed.update(group)

        logger.info(f"Detected {len(groups)} parallelizable groups")

        return groups

    async def optimize_execution_order(
        self,
        graph: DAGGraph,
        constraints: Dict[str, Any],
    ) -> List[str]:
        """
        Optimize execution order based on constraints.
        
        Args:
            graph: DAG to optimize
            constraints: Execution constraints
            
        Returns:
            Optimized execution order
        """
        execution_order = graph.get_execution_order()

        # Apply constraints
        max_parallel = constraints.get("max_parallel", 4)
        priority_nodes = constraints.get("priority_nodes", [])

        # Reorder to prioritize high-priority nodes
        if priority_nodes:
            execution_order = sorted(
                execution_order,
                key=lambda n: (
                    0 if n in priority_nodes else 1,
                    execution_order.index(n),
                ),
            )

        logger.info(f"Optimized execution order: {execution_order}")

        return execution_order
