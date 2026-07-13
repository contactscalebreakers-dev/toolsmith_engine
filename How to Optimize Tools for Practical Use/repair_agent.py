"""
RepairAgent for SB Toolsmith Pro

Analyzes failures and proposes recovery strategies.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class RepairAgent(Agent):
    """
    Repair Agent - Analyzes failures and proposes fixes.
    
    Responsibilities:
    - Analyze error logs
    - Detect common failure patterns
    - Propose recovery strategies
    - Suggest rollback points
    - Recommend environment repairs
    - Track repair success rates
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize repair agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="repair",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )
        self._repair_history: Dict[str, Dict[str, Any]] = {}

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute repair logic.
        
        Args:
            context: Execution context containing:
                - error: Error message or exception
                - stderr: Standard error output
                - tool_key: Tool that failed
                - execution_history: Previous execution results
                
        Returns:
            Execution result with repair recommendations
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            error = context.get("error", "")
            stderr = context.get("stderr", "")
            tool_key = context.get("tool_key", "unknown")

            logger.info(f"RepairAgent analyzing failure for {tool_key}")

            # Analyze error
            error_analysis = await self._analyze_error(error, stderr)
            logger.info(f"Error analysis: {error_analysis}")

            # Detect failure pattern
            pattern = await self._detect_failure_pattern(error_analysis)
            logger.info(f"Detected failure pattern: {pattern}")

            # Propose repairs
            repairs = await self._propose_repairs(pattern, tool_key, error_analysis)

            if not repairs:
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    "Unable to determine repair strategy",
                    confidence=0.3,
                )
                status = AgentStatus.FAILED
                result_data = {"repairs": [], "pattern": pattern}
            else:
                decision = await self.record_decision(
                    AgentDecision.PROCEED,
                    f"Proposed {len(repairs)} repair strategies",
                    confidence=0.8,
                    alternatives=[r["strategy"] for r in repairs],
                )
                status = AgentStatus.COMPLETED
                result_data = {
                    "repairs": repairs,
                    "pattern": pattern,
                    "recommended": repairs[0] if repairs else None,
                }

            # Propose repair action
            if repairs:
                action = AgentAction(
                    action_type="apply_repair",
                    description=f"Apply repair: {repairs[0]['strategy']}",
                    parameters={
                        "tool_key": tool_key,
                        "repair_strategy": repairs[0]["strategy"],
                        "steps": repairs[0].get("steps", []),
                    },
                    priority=2,
                    reversible=True,
                    estimated_duration_seconds=repairs[0].get("estimated_duration", 60),
                )
                await self.propose_action(action)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=status,
                actions=[action] if repairs else [],
                decisions=[decision],
                result=result_data,
                duration_seconds=duration,
            )

            self.status = status
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"RepairAgent failed: {e}", exc_info=True)
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

    async def _analyze_error(
        self,
        error: str,
        stderr: str,
    ) -> Dict[str, Any]:
        """
        Analyze error message.
        
        Args:
            error: Error message
            stderr: Standard error output
            
        Returns:
            Error analysis
        """
        full_output = f"{error}\n{stderr}".lower()

        analysis = {
            "has_import_error": "importerror" in full_output or "modulenotfounderror" in full_output,
            "has_syntax_error": "syntaxerror" in full_output,
            "has_permission_error": "permissionerror" in full_output,
            "has_timeout": "timeout" in full_output,
            "has_memory_error": "memoryerror" in full_output,
            "has_network_error": "connectionerror" in full_output or "timeout" in full_output,
            "has_file_error": "filenotfounderror" in full_output or "no such file" in full_output,
            "has_version_error": "version" in full_output and "incompatible" in full_output,
            "raw_error": error,
            "raw_stderr": stderr,
        }

        return analysis

    async def _detect_failure_pattern(
        self,
        analysis: Dict[str, Any],
    ) -> str:
        """
        Detect failure pattern.
        
        Args:
            analysis: Error analysis
            
        Returns:
            Failure pattern name
        """
        if analysis.get("has_import_error"):
            return "missing_dependency"
        elif analysis.get("has_syntax_error"):
            return "syntax_error"
        elif analysis.get("has_permission_error"):
            return "permission_denied"
        elif analysis.get("has_timeout"):
            return "execution_timeout"
        elif analysis.get("has_memory_error"):
            return "out_of_memory"
        elif analysis.get("has_network_error"):
            return "network_error"
        elif analysis.get("has_file_error"):
            return "file_not_found"
        elif analysis.get("has_version_error"):
            return "version_conflict"
        else:
            return "unknown_error"

    async def _propose_repairs(
        self,
        pattern: str,
        tool_key: str,
        analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Propose repair strategies.
        
        Args:
            pattern: Failure pattern
            tool_key: Tool identifier
            analysis: Error analysis
            
        Returns:
            List of repair strategies
        """
        repairs = []

        if pattern == "missing_dependency":
            repairs = [
                {
                    "strategy": "reinstall_dependencies",
                    "description": "Reinstall all dependencies",
                    "steps": [
                        "Delete virtual environment",
                        "Create new virtual environment",
                        "Reinstall all dependencies",
                    ],
                    "estimated_duration": 120,
                    "reversible": True,
                },
                {
                    "strategy": "install_missing_package",
                    "description": "Install missing package",
                    "steps": [
                        "Extract package name from error",
                        "Install package with pip",
                    ],
                    "estimated_duration": 30,
                    "reversible": True,
                },
            ]

        elif pattern == "syntax_error":
            repairs = [
                {
                    "strategy": "review_source_code",
                    "description": "Review source code for syntax errors",
                    "steps": [
                        "Check Python version compatibility",
                        "Validate syntax with ast.parse()",
                    ],
                    "estimated_duration": 10,
                    "reversible": False,
                },
            ]

        elif pattern == "permission_denied":
            repairs = [
                {
                    "strategy": "fix_permissions",
                    "description": "Fix file permissions",
                    "steps": [
                        "Check file permissions",
                        "Fix read/write permissions",
                    ],
                    "estimated_duration": 5,
                    "reversible": True,
                },
            ]

        elif pattern == "execution_timeout":
            repairs = [
                {
                    "strategy": "increase_timeout",
                    "description": "Increase execution timeout",
                    "steps": [
                        "Increase timeout threshold",
                        "Retry execution",
                    ],
                    "estimated_duration": 60,
                    "reversible": True,
                },
                {
                    "strategy": "optimize_execution",
                    "description": "Optimize tool execution",
                    "steps": [
                        "Profile execution",
                        "Identify bottlenecks",
                        "Optimize critical paths",
                    ],
                    "estimated_duration": 300,
                    "reversible": False,
                },
            ]

        elif pattern == "out_of_memory":
            repairs = [
                {
                    "strategy": "increase_memory",
                    "description": "Increase available memory",
                    "steps": [
                        "Increase memory limit",
                        "Retry execution",
                    ],
                    "estimated_duration": 30,
                    "reversible": True,
                },
                {
                    "strategy": "optimize_memory",
                    "description": "Optimize memory usage",
                    "steps": [
                        "Profile memory usage",
                        "Identify memory leaks",
                        "Optimize data structures",
                    ],
                    "estimated_duration": 600,
                    "reversible": False,
                },
            ]

        elif pattern == "network_error":
            repairs = [
                {
                    "strategy": "retry_with_backoff",
                    "description": "Retry with exponential backoff",
                    "steps": [
                        "Wait 5 seconds",
                        "Retry execution",
                    ],
                    "estimated_duration": 30,
                    "reversible": True,
                },
            ]

        elif pattern == "file_not_found":
            repairs = [
                {
                    "strategy": "check_file_paths",
                    "description": "Verify file paths and locations",
                    "steps": [
                        "Check working directory",
                        "Verify file existence",
                        "Update file paths if needed",
                    ],
                    "estimated_duration": 10,
                    "reversible": False,
                },
            ]

        elif pattern == "version_conflict":
            repairs = [
                {
                    "strategy": "resolve_version_conflict",
                    "description": "Resolve package version conflicts",
                    "steps": [
                        "Identify conflicting packages",
                        "Update to compatible versions",
                        "Reinstall dependencies",
                    ],
                    "estimated_duration": 120,
                    "reversible": True,
                },
            ]

        else:  # unknown_error
            repairs = [
                {
                    "strategy": "rollback_snapshot",
                    "description": "Rollback to last known good state",
                    "steps": [
                        "Restore from snapshot",
                        "Retry execution",
                    ],
                    "estimated_duration": 60,
                    "reversible": True,
                },
            ]

        return repairs

    async def record_repair_result(
        self,
        tool_key: str,
        strategy: str,
        success: bool,
        duration: float,
    ) -> None:
        """Record repair result for learning."""
        if tool_key not in self._repair_history:
            self._repair_history[tool_key] = {
                "total_repairs": 0,
                "successful_repairs": 0,
                "strategies": {},
            }

        history = self._repair_history[tool_key]
        history["total_repairs"] += 1
        if success:
            history["successful_repairs"] += 1

        if strategy not in history["strategies"]:
            history["strategies"][strategy] = {"count": 0, "success": 0}

        history["strategies"][strategy]["count"] += 1
        if success:
            history["strategies"][strategy]["success"] += 1

        logger.info(
            f"Recorded repair: {tool_key}/{strategy} - "
            f"success={success}, duration={duration}s"
        )
