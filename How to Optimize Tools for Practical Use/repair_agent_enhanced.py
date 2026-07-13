"""
Enhanced RepairAgent for SB Toolsmith Pro

Advanced failure analysis with AI-assisted diagnostics and recovery strategies.
"""

import asyncio
import ast
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class FailurePattern:
    """Represents a detected failure pattern."""
    
    def __init__(
        self,
        pattern_type: str,
        severity: str,
        confidence: float,
        indicators: List[str],
        root_cause: str,
        affected_components: List[str],
    ):
        self.pattern_type = pattern_type
        self.severity = severity  # critical, high, medium, low
        self.confidence = confidence
        self.indicators = indicators
        self.root_cause = root_cause
        self.affected_components = affected_components

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "root_cause": self.root_cause,
            "affected_components": self.affected_components,
        }


class RecoveryStrategy:
    """Represents a recovery strategy."""
    
    def __init__(
        self,
        strategy_id: str,
        strategy_type: str,
        description: str,
        steps: List[str],
        estimated_duration: float,
        reversible: bool,
        risk_level: str,  # low, medium, high
        success_probability: float,
        prerequisites: List[str] = None,
        rollback_steps: List[str] = None,
    ):
        self.strategy_id = strategy_id
        self.strategy_type = strategy_type
        self.description = description
        self.steps = steps
        self.estimated_duration = estimated_duration
        self.reversible = reversible
        self.risk_level = risk_level
        self.success_probability = success_probability
        self.prerequisites = prerequisites or []
        self.rollback_steps = rollback_steps or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type,
            "description": self.description,
            "steps": self.steps,
            "estimated_duration": self.estimated_duration,
            "reversible": self.reversible,
            "risk_level": self.risk_level,
            "success_probability": self.success_probability,
            "prerequisites": self.prerequisites,
            "rollback_steps": self.rollback_steps,
        }


class EnhancedRepairAgent(Agent):
    """
    Enhanced Repair Agent with advanced diagnostics.
    
    Responsibilities:
    - Deep error analysis with pattern matching
    - Multi-level diagnostics (system, environment, code)
    - Intelligent recovery strategy selection
    - Predictive failure prevention
    - Learning from repair outcomes
    - AI-assisted root cause analysis
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize enhanced repair agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="repair",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )
        self._repair_history: Dict[str, Dict[str, Any]] = {}
        self._pattern_cache: Dict[str, FailurePattern] = {}
        self._strategy_success_rates: Dict[str, float] = {}

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute enhanced repair logic.
        
        Args:
            context: Execution context containing:
                - error: Error message
                - stderr: Standard error output
                - stdout: Standard output
                - tool_key: Tool that failed
                - execution_history: Previous executions
                - environment: Runtime environment info
                - source_code: Tool source code
                
        Returns:
            Execution result with repair recommendations
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            error = context.get("error", "")
            stderr = context.get("stderr", "")
            stdout = context.get("stdout", "")
            tool_key = context.get("tool_key", "unknown")
            source_code = context.get("source_code", "")

            logger.info(f"EnhancedRepairAgent analyzing failure for {tool_key}")

            # Multi-level diagnostics
            diagnostics = await self._run_diagnostics(
                error,
                stderr,
                stdout,
                source_code,
                context,
            )

            # Detect failure pattern
            pattern = await self._detect_failure_pattern(diagnostics)
            logger.info(f"Detected pattern: {pattern.pattern_type} (confidence: {pattern.confidence})")

            # Generate recovery strategies
            strategies = await self._generate_recovery_strategies(pattern, tool_key, diagnostics)

            # Rank strategies by success probability
            ranked_strategies = sorted(
                strategies,
                key=lambda s: (s.success_probability, -s.risk_level == "low"),
                reverse=True,
            )

            if not ranked_strategies:
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    "Unable to determine recovery strategy",
                    confidence=0.3,
                )
                status = AgentStatus.FAILED
                result_data = {
                    "pattern": pattern.to_dict(),
                    "strategies": [],
                    "diagnostics": diagnostics,
                }
            else:
                decision = await self.record_decision(
                    AgentDecision.PROCEED,
                    f"Proposed {len(ranked_strategies)} recovery strategies",
                    confidence=min(0.95, pattern.confidence + 0.1),
                    alternatives=[s.strategy_type for s in ranked_strategies[:3]],
                )
                status = AgentStatus.COMPLETED
                result_data = {
                    "pattern": pattern.to_dict(),
                    "strategies": [s.to_dict() for s in ranked_strategies],
                    "diagnostics": diagnostics,
                    "recommended": ranked_strategies[0].to_dict() if ranked_strategies else None,
                }

            # Propose primary recovery action
            actions = []
            if ranked_strategies:
                primary_strategy = ranked_strategies[0]
                action = AgentAction(
                    action_type="apply_recovery",
                    description=f"Apply recovery: {primary_strategy.description}",
                    parameters={
                        "tool_key": tool_key,
                        "strategy_id": primary_strategy.strategy_id,
                        "steps": primary_strategy.steps,
                        "rollback_steps": primary_strategy.rollback_steps,
                    },
                    priority=2,
                    reversible=primary_strategy.reversible,
                    estimated_duration_seconds=primary_strategy.estimated_duration,
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
                result=result_data,
                duration_seconds=duration,
            )

            self.status = status
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"EnhancedRepairAgent failed: {e}", exc_info=True)
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

    async def _run_diagnostics(
        self,
        error: str,
        stderr: str,
        stdout: str,
        source_code: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run multi-level diagnostics.
        
        Args:
            error: Error message
            stderr: Standard error
            stdout: Standard output
            source_code: Tool source code
            context: Execution context
            
        Returns:
            Comprehensive diagnostics
        """
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_analysis": await self._analyze_error(error, stderr, stdout),
            "code_analysis": await self._analyze_code(source_code),
            "environment_analysis": await self._analyze_environment(context),
            "system_analysis": await self._analyze_system(),
        }

        return diagnostics

    async def _analyze_error(
        self,
        error: str,
        stderr: str,
        stdout: str,
    ) -> Dict[str, Any]:
        """Analyze error messages."""
        full_output = f"{error}\n{stderr}\n{stdout}".lower()

        analysis = {
            "error_type": self._classify_error(full_output),
            "error_categories": self._extract_error_categories(full_output),
            "stack_trace_present": "traceback" in full_output,
            "error_line_numbers": self._extract_line_numbers(error),
            "error_keywords": self._extract_keywords(full_output),
            "raw_error": error[:500],  # First 500 chars
            "raw_stderr": stderr[:500],
        }

        return analysis

    async def _analyze_code(self, source_code: str) -> Dict[str, Any]:
        """Analyze source code for issues."""
        analysis = {
            "has_syntax_errors": False,
            "has_import_errors": False,
            "imports": [],
            "functions": [],
            "classes": [],
            "potential_issues": [],
        }

        if not source_code:
            return analysis

        try:
            tree = ast.parse(source_code)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis["imports"].append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append(node.name)

        except SyntaxError as e:
            analysis["has_syntax_errors"] = True
            analysis["syntax_error"] = str(e)
        except Exception as e:
            logger.warning(f"Code analysis failed: {e}")

        return analysis

    async def _analyze_environment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze runtime environment."""
        analysis = {
            "python_version": context.get("python_version"),
            "virtual_env": context.get("virtual_env"),
            "installed_packages": context.get("installed_packages", []),
            "environment_variables": context.get("environment_variables", {}),
            "working_directory": context.get("working_directory"),
        }

        return analysis

    async def _analyze_system(self) -> Dict[str, Any]:
        """Analyze system state."""
        analysis = {
            "platform": self._get_platform(),
            "available_memory_mb": self._get_available_memory(),
            "disk_space_mb": self._get_disk_space(),
            "cpu_count": self._get_cpu_count(),
        }

        return analysis

    def _classify_error(self, output: str) -> str:
        """Classify error type."""
        if "importerror" in output or "modulenotfounderror" in output:
            return "import_error"
        elif "syntaxerror" in output:
            return "syntax_error"
        elif "typeerror" in output:
            return "type_error"
        elif "valueerror" in output:
            return "value_error"
        elif "keyerror" in output:
            return "key_error"
        elif "indexerror" in output:
            return "index_error"
        elif "attributeerror" in output:
            return "attribute_error"
        elif "runtimeerror" in output:
            return "runtime_error"
        elif "timeout" in output:
            return "timeout_error"
        elif "memoryerror" in output:
            return "memory_error"
        elif "permissionerror" in output:
            return "permission_error"
        elif "filenotfounderror" in output:
            return "file_not_found"
        elif "connectionerror" in output or "network" in output:
            return "network_error"
        else:
            return "unknown_error"

    def _extract_error_categories(self, output: str) -> List[str]:
        """Extract error categories."""
        categories = []

        if "import" in output:
            categories.append("import_issue")
        if "version" in output:
            categories.append("version_conflict")
        if "permission" in output:
            categories.append("permission_issue")
        if "timeout" in output:
            categories.append("timeout_issue")
        if "memory" in output:
            categories.append("memory_issue")
        if "network" in output or "connection" in output:
            categories.append("network_issue")
        if "file" in output or "path" in output:
            categories.append("file_system_issue")
        if "database" in output or "sql" in output:
            categories.append("database_issue")

        return categories

    def _extract_line_numbers(self, error: str) -> List[int]:
        """Extract line numbers from error."""
        lines = []
        for match in re.finditer(r"line (\d+)", error, re.IGNORECASE):
            lines.append(int(match.group(1)))
        return lines

    def _extract_keywords(self, output: str) -> List[str]:
        """Extract error keywords."""
        keywords = set()

        # Common error keywords
        error_keywords = [
            "error", "failed", "exception", "traceback", "warning",
            "critical", "fatal", "abort", "crash", "panic",
        ]

        for keyword in error_keywords:
            if keyword in output:
                keywords.add(keyword)

        return list(keywords)

    def _get_platform(self) -> str:
        """Get platform info."""
        import platform
        return platform.system()

    def _get_available_memory(self) -> float:
        """Get available memory in MB."""
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except:
            return 0

    def _get_disk_space(self) -> float:
        """Get available disk space in MB."""
        try:
            import shutil
            return shutil.disk_usage("/").free / 1024 / 1024
        except:
            return 0

    def _get_cpu_count(self) -> int:
        """Get CPU count."""
        try:
            import os
            return os.cpu_count() or 1
        except:
            return 1

    async def _detect_failure_pattern(
        self,
        diagnostics: Dict[str, Any],
    ) -> FailurePattern:
        """
        Detect failure pattern from diagnostics.
        
        Args:
            diagnostics: Comprehensive diagnostics
            
        Returns:
            Detected failure pattern
        """
        error_analysis = diagnostics.get("error_analysis", {})
        error_type = error_analysis.get("error_type", "unknown_error")
        categories = error_analysis.get("error_categories", [])

        # Map error types to patterns
        pattern_map = {
            "import_error": FailurePattern(
                pattern_type="missing_dependency",
                severity="high",
                confidence=0.95,
                indicators=["ImportError", "ModuleNotFoundError"],
                root_cause="Required package not installed or not in path",
                affected_components=["dependencies", "environment"],
            ),
            "syntax_error": FailurePattern(
                pattern_type="code_syntax_error",
                severity="critical",
                confidence=0.98,
                indicators=["SyntaxError"],
                root_cause="Invalid Python syntax in source code",
                affected_components=["source_code"],
            ),
            "timeout_error": FailurePattern(
                pattern_type="execution_timeout",
                severity="high",
                confidence=0.90,
                indicators=["timeout", "timed out"],
                root_cause="Execution exceeded time limit",
                affected_components=["execution", "performance"],
            ),
            "memory_error": FailurePattern(
                pattern_type="out_of_memory",
                severity="critical",
                confidence=0.95,
                indicators=["MemoryError", "out of memory"],
                root_cause="Insufficient memory for execution",
                affected_components=["system", "memory"],
            ),
            "permission_error": FailurePattern(
                pattern_type="permission_denied",
                severity="medium",
                confidence=0.92,
                indicators=["PermissionError", "permission denied"],
                root_cause="Insufficient permissions for operation",
                affected_components=["file_system", "permissions"],
            ),
            "file_not_found": FailurePattern(
                pattern_type="missing_file",
                severity="medium",
                confidence=0.93,
                indicators=["FileNotFoundError", "No such file"],
                root_cause="Required file not found",
                affected_components=["file_system", "paths"],
            ),
            "network_error": FailurePattern(
                pattern_type="network_failure",
                severity="medium",
                confidence=0.85,
                indicators=["ConnectionError", "network", "timeout"],
                root_cause="Network connectivity issue",
                affected_components=["network", "connectivity"],
            ),
        }

        pattern = pattern_map.get(
            error_type,
            FailurePattern(
                pattern_type="unknown_error",
                severity="low",
                confidence=0.5,
                indicators=categories,
                root_cause="Unable to determine root cause",
                affected_components=["unknown"],
            ),
        )

        return pattern

    async def _generate_recovery_strategies(
        self,
        pattern: FailurePattern,
        tool_key: str,
        diagnostics: Dict[str, Any],
    ) -> List[RecoveryStrategy]:
        """Generate recovery strategies."""
        strategies = []

        if pattern.pattern_type == "missing_dependency":
            strategies.extend([
                RecoveryStrategy(
                    strategy_id="reinstall_deps",
                    strategy_type="environment_reset",
                    description="Reinstall all dependencies",
                    steps=[
                        "Delete virtual environment",
                        "Create new virtual environment",
                        "Reinstall dependencies from requirements.txt",
                        "Verify installation",
                    ],
                    estimated_duration=120,
                    reversible=True,
                    risk_level="low",
                    success_probability=0.95,
                    rollback_steps=["Restore from snapshot"],
                ),
                RecoveryStrategy(
                    strategy_id="install_missing",
                    strategy_type="targeted_install",
                    description="Install missing package",
                    steps=[
                        "Extract package name from error",
                        "Install with pip",
                        "Verify installation",
                    ],
                    estimated_duration=30,
                    reversible=True,
                    risk_level="low",
                    success_probability=0.85,
                ),
            ])

        elif pattern.pattern_type == "code_syntax_error":
            strategies.append(
                RecoveryStrategy(
                    strategy_id="fix_syntax",
                    strategy_type="code_review",
                    description="Fix syntax errors in source code",
                    steps=[
                        "Identify syntax error location",
                        "Review code around error",
                        "Apply fix",
                        "Validate syntax",
                    ],
                    estimated_duration=60,
                    reversible=False,
                    risk_level="medium",
                    success_probability=0.70,
                )
            )

        elif pattern.pattern_type == "execution_timeout":
            strategies.extend([
                RecoveryStrategy(
                    strategy_id="increase_timeout",
                    strategy_type="parameter_adjustment",
                    description="Increase execution timeout",
                    steps=[
                        "Increase timeout threshold",
                        "Retry execution",
                    ],
                    estimated_duration=120,
                    reversible=True,
                    risk_level="low",
                    success_probability=0.60,
                ),
                RecoveryStrategy(
                    strategy_id="optimize_performance",
                    strategy_type="optimization",
                    description="Optimize tool performance",
                    steps=[
                        "Profile execution",
                        "Identify bottlenecks",
                        "Apply optimizations",
                    ],
                    estimated_duration=600,
                    reversible=False,
                    risk_level="medium",
                    success_probability=0.75,
                ),
            ])

        elif pattern.pattern_type == "out_of_memory":
            strategies.extend([
                RecoveryStrategy(
                    strategy_id="increase_memory",
                    strategy_type="resource_allocation",
                    description="Increase available memory",
                    steps=[
                        "Increase memory limit",
                        "Retry execution",
                    ],
                    estimated_duration=30,
                    reversible=True,
                    risk_level="low",
                    success_probability=0.70,
                ),
                RecoveryStrategy(
                    strategy_id="optimize_memory",
                    strategy_type="optimization",
                    description="Optimize memory usage",
                    steps=[
                        "Profile memory usage",
                        "Identify leaks",
                        "Optimize data structures",
                    ],
                    estimated_duration=300,
                    reversible=False,
                    risk_level="medium",
                    success_probability=0.65,
                ),
            ])

        return strategies
