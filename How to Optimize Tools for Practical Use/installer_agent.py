"""
InstallerAgent for SB Toolsmith Pro

Handles dependency installation with backend detection (pip, poetry, uv).
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class InstallerAgent(Agent):
    """
    Installer Agent - Manages dependency installation.
    
    Responsibilities:
    - Detect available package managers (pip, poetry, uv)
    - Parse requirements files
    - Install dependencies
    - Validate installation
    - Handle installation failures
    - Repair broken environments
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize installer agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="installer",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute installer logic.
        
        Args:
            context: Execution context containing:
                - tool_key: Tool to install
                - requirements_file: Path to requirements
                - backend: Preferred backend (pip, poetry, uv, auto)
                
        Returns:
            Execution result with installation status
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            tool_key = context.get("tool_key")
            requirements_file = context.get("requirements_file")
            backend = context.get("backend", "auto")

            logger.info(
                f"InstallerAgent starting for {tool_key} with backend={backend}"
            )

            if not tool_key:
                decision = await self.record_decision(
                    AgentDecision.SKIP,
                    "No tool key provided",
                )
                result = self._create_result(
                    AgentStatus.COMPLETED,
                    result={"installed": False, "decisions": [decision]},
                )
                await self._record_execution(result)
                return result

            # Detect available backends
            available_backends = await self._detect_backends()
            logger.info(f"Available backends: {available_backends}")

            # Select backend
            selected_backend = await self._select_backend(backend, available_backends)
            if not selected_backend:
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    "No suitable package manager found",
                    confidence=0.5,
                )
                result = self._create_result(
                    AgentStatus.FAILED,
                    error="No package manager available",
                )
                await self._record_execution(result)
                return result

            logger.info(f"Selected backend: {selected_backend}")

            # Parse requirements
            requirements = await self._parse_requirements(requirements_file)
            logger.info(f"Parsed {len(requirements)} requirements")

            # Install dependencies
            success = await self._install_dependencies(
                tool_key,
                requirements,
                selected_backend,
            )

            if success:
                decision = await self.record_decision(
                    AgentDecision.PROCEED,
                    f"Successfully installed dependencies using {selected_backend}",
                    confidence=0.95,
                )
                status = AgentStatus.COMPLETED
            else:
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    f"Installation failed with {selected_backend}",
                    confidence=0.8,
                )
                status = AgentStatus.FAILED

            # Propose action
            action = AgentAction(
                action_type="validate_installation",
                description=f"Validate installation for {tool_key}",
                parameters={
                    "tool_key": tool_key,
                    "backend": selected_backend,
                },
                priority=1,
                reversible=True,
            )
            await self.propose_action(action)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=status,
                actions=[action],
                decisions=[decision],
                result={
                    "installed": success,
                    "backend": selected_backend,
                    "requirements_count": len(requirements),
                },
                duration_seconds=duration,
            )

            self.status = status
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"InstallerAgent failed: {e}", exc_info=True)
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

    async def _detect_backends(self) -> Dict[str, bool]:
        """
        Detect available package managers.
        
        Returns:
            Dict of backend availability
        """
        backends = {
            "pip": await self._check_command("pip", "--version"),
            "poetry": await self._check_command("poetry", "--version"),
            "uv": await self._check_command("uv", "--version"),
        }

        logger.info(f"Backend detection: {backends}")
        return backends

    async def _check_command(self, command: str, arg: str) -> bool:
        """Check if command is available."""
        try:
            process = await asyncio.create_subprocess_exec(
                command,
                arg,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.wait(), timeout=5)
            return process.returncode == 0
        except Exception:
            return False

    async def _select_backend(
        self,
        preferred: str,
        available: Dict[str, bool],
    ) -> Optional[str]:
        """
        Select package manager backend.
        
        Args:
            preferred: Preferred backend
            available: Available backends
            
        Returns:
            Selected backend or None
        """
        # If specific backend requested and available
        if preferred != "auto" and available.get(preferred):
            return preferred

        # Auto-detect: prefer uv > poetry > pip
        for backend in ["uv", "poetry", "pip"]:
            if available.get(backend):
                return backend

        return None

    async def _parse_requirements(
        self,
        requirements_file: Optional[str],
    ) -> List[str]:
        """
        Parse requirements from file.
        
        Args:
            requirements_file: Path to requirements file
            
        Returns:
            List of requirements
        """
        requirements = []

        if not requirements_file:
            return requirements

        try:
            path = Path(requirements_file)
            if path.exists():
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith("#"):
                            requirements.append(line)

                logger.info(f"Parsed {len(requirements)} requirements from {requirements_file}")

        except Exception as e:
            logger.warning(f"Failed to parse requirements: {e}")

        return requirements

    async def _install_dependencies(
        self,
        tool_key: str,
        requirements: List[str],
        backend: str,
    ) -> bool:
        """
        Install dependencies using selected backend.
        
        Args:
            tool_key: Tool identifier
            requirements: List of requirements
            backend: Package manager to use
            
        Returns:
            True if installation successful
        """
        if not requirements:
            logger.info("No requirements to install")
            return True

        try:
            if backend == "uv":
                return await self._install_with_uv(requirements)
            elif backend == "poetry":
                return await self._install_with_poetry(requirements)
            else:  # pip
                return await self._install_with_pip(requirements)

        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False

    async def _install_with_pip(self, requirements: List[str]) -> bool:
        """Install with pip."""
        try:
            process = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                *requirements,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            returncode = await asyncio.wait_for(process.wait(), timeout=300)
            return returncode == 0
        except Exception as e:
            logger.error(f"pip install failed: {e}")
            return False

    async def _install_with_poetry(self, requirements: List[str]) -> bool:
        """Install with poetry."""
        try:
            process = await asyncio.create_subprocess_exec(
                "poetry",
                "add",
                *requirements,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            returncode = await asyncio.wait_for(process.wait(), timeout=300)
            return returncode == 0
        except Exception as e:
            logger.error(f"poetry add failed: {e}")
            return False

    async def _install_with_uv(self, requirements: List[str]) -> bool:
        """Install with uv."""
        try:
            process = await asyncio.create_subprocess_exec(
                "uv",
                "pip",
                "install",
                *requirements,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            returncode = await asyncio.wait_for(process.wait(), timeout=300)
            return returncode == 0
        except Exception as e:
            logger.error(f"uv pip install failed: {e}")
            return False
