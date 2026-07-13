"""
ExecutionAgent for SB Toolsmith Pro

Supervises DAG execution and monitors runtime health.
"""

import asyncio
import logging
import psutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class ExecutionAgent(Agent):
    """
    Execution Agent - Supervises tool execution.
    
    Responsibilities:
    - Monitor DAG execution
    - Track resource usage
    - Detect execution anomalies
    - Handle timeouts
    - Recover failed nodes
    - Manage execution state
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize execution agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="execution",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )
        self._execution_monitors: Dict[str, Dict[str, Any]] = {}

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute supervision logic.
        
        Args:
            context: Execution context containing:
                - execution_id: Execution ID to monitor
                - dag: DAG being executed
                - resource_limits: Resource limits
                
        Returns:
            Execution result with monitoring data
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            dag = context.get("dag")
            resource_limits = context.get("resource_limits", {})

            logger.info(f"ExecutionAgent monitoring execution {execution_id}")

            # Initialize monitoring
            monitor = {
                "execution_id": execution_id,
                "start_time": start_time,
                "resource_usage": [],
                "anomalies": [],
                "status": "running",
            }
            self._execution_monitors[execution_id] = monitor

            # Monitor execution
            await self._monitor_execution(
                execution_id,
                dag,
                resource_limits,
                monitor,
            )

            # Analyze results
            anomalies = monitor.get("anomalies", [])

            if anomalies:
                decision = await self.record_decision(
                    AgentDecision.PROCEED,
                    f"Detected {len(anomalies)} runtime anomalies",
                    confidence=0.8,
                )
                status = AgentStatus.COMPLETED
            else:
                decision = await self.record_decision(
                    AgentDecision.SKIP,
                    "Execution completed normally",
                    confidence=0.95,
                )
                status = AgentStatus.COMPLETED

            # Propose action if needed
            actions = []
            if anomalies:
                action = AgentAction(
                    action_type="handle_anomaly",
                    description="Handle detected anomalies",
                    parameters={
                        "execution_id": execution_id,
                        "anomalies": anomalies,
                    },
                    priority=2,
                    reversible=True,
                )
                actions.append(action)
                await self.propose_action(action)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=status,
                actions=actions,
                decisions=[decision],
                result={
                    "anomalies": anomalies,
                    "resource_usage": monitor.get("resource_usage", []),
                },
                duration_seconds=duration,
            )

            self.status = status
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"ExecutionAgent failed: {e}", exc_info=True)
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

    async def _monitor_execution(
        self,
        execution_id: str,
        dag: Any,
        resource_limits: Dict[str, Any],
        monitor: Dict[str, Any],
    ) -> None:
        """Monitor execution in real-time."""
        try:
            # Get process
            process = psutil.Process()

            # Monitor loop
            while monitor.get("status") == "running":
                # Collect metrics
                try:
                    metrics = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "cpu_percent": process.cpu_percent(interval=0.1),
                        "num_threads": process.num_threads(),
                    }
                    monitor["resource_usage"].append(metrics)

                    # Check limits
                    max_memory = resource_limits.get("max_memory_mb", 1024)
                    max_cpu = resource_limits.get("max_cpu_percent", 100)

                    if metrics["memory_mb"] > max_memory:
                        monitor["anomalies"].append({
                            "type": "memory_exceeded",
                            "value": metrics["memory_mb"],
                            "limit": max_memory,
                            "timestamp": metrics["timestamp"],
                        })
                        logger.warning(
                            f"Memory limit exceeded: {metrics['memory_mb']}MB > {max_memory}MB"
                        )

                    if metrics["cpu_percent"] > max_cpu:
                        monitor["anomalies"].append({
                            "type": "cpu_exceeded",
                            "value": metrics["cpu_percent"],
                            "limit": max_cpu,
                            "timestamp": metrics["timestamp"],
                        })

                except Exception as e:
                    logger.warning(f"Failed to collect metrics: {e}")

                # Check execution status
                # This would be updated by external execution engine
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Monitoring failed: {e}", exc_info=True)

    async def get_execution_metrics(
        self,
        execution_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get execution metrics."""
        return self._execution_monitors.get(execution_id)

    async def stop_monitoring(self, execution_id: str) -> None:
        """Stop monitoring execution."""
        monitor = self._execution_monitors.get(execution_id)
        if monitor:
            monitor["status"] = "stopped"
            monitor["end_time"] = datetime.utcnow()
            logger.info(f"Stopped monitoring execution {execution_id}")
