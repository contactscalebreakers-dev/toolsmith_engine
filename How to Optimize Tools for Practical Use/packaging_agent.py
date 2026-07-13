"""
PackagingAgent for SB Toolsmith Pro

Bundles tools into portable packages.
"""

import asyncio
import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_agent import Agent, AgentAction, AgentDecision, AgentExecutionResult, AgentStatus

logger = logging.getLogger(__name__)


class PackagingAgent(Agent):
    """
    Packaging Agent - Packages tools for distribution.
    
    Responsibilities:
    - Create tool packages
    - Generate manifests
    - Bundle dependencies
    - Create portable runtimes
    - Generate installation scripts
    - Validate packages
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: Optional[Any] = None,
        runtime_manager: Optional[Any] = None,
    ):
        """Initialize packaging agent."""
        super().__init__(
            agent_id=agent_id,
            agent_type="packaging",
            event_bus=event_bus,
            runtime_manager=runtime_manager,
        )

    async def execute(self, context: Dict[str, Any]) -> AgentExecutionResult:
        """
        Execute packaging logic.
        
        Args:
            context: Execution context containing:
                - tool_key: Tool to package
                - source_path: Tool source path
                - output_dir: Output directory
                - include_dependencies: Include deps in package
                
        Returns:
            Execution result with package info
        """
        start_time = datetime.utcnow()
        execution_id = context.get("execution_id", "unknown")

        try:
            self.status = AgentStatus.RUNNING

            tool_key = context.get("tool_key")
            source_path = context.get("source_path")
            output_dir = context.get("output_dir", ".")
            include_deps = context.get("include_dependencies", False)

            logger.info(f"PackagingAgent packaging {tool_key}")

            if not tool_key or not source_path:
                decision = await self.record_decision(
                    AgentDecision.SKIP,
                    "Missing tool_key or source_path",
                )
                result = self._create_result(
                    AgentStatus.COMPLETED,
                    result={"packaged": False},
                )
                await self._record_execution(result)
                return result

            # Create package
            package_path = await self._create_package(
                tool_key,
                source_path,
                output_dir,
                include_deps,
            )

            if not package_path:
                decision = await self.record_decision(
                    AgentDecision.ESCALATE,
                    "Failed to create package",
                    confidence=0.5,
                )
                result = self._create_result(
                    AgentStatus.FAILED,
                    error="Package creation failed",
                )
                await self._record_execution(result)
                return result

            # Generate manifest
            manifest = await self._generate_manifest(tool_key, source_path)

            # Save manifest
            manifest_path = Path(output_dir) / f"{tool_key}-manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"Package created: {package_path}")
            logger.info(f"Manifest saved: {manifest_path}")

            decision = await self.record_decision(
                AgentDecision.PROCEED,
                f"Successfully packaged {tool_key}",
                confidence=0.95,
            )

            # Propose action
            action = AgentAction(
                action_type="distribute_package",
                description=f"Distribute package: {tool_key}",
                parameters={
                    "package_path": str(package_path),
                    "manifest_path": str(manifest_path),
                },
                priority=1,
                reversible=False,
            )
            await self.propose_action(action)

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = AgentExecutionResult(
                agent_id=self.agent_id,
                execution_id=execution_id,
                status=AgentStatus.COMPLETED,
                actions=[action],
                decisions=[decision],
                result={
                    "packaged": True,
                    "package_path": str(package_path),
                    "manifest_path": str(manifest_path),
                    "manifest": manifest,
                },
                duration_seconds=duration,
            )

            self.status = AgentStatus.COMPLETED
            await self._record_execution(result)

            return result

        except Exception as e:
            logger.error(f"PackagingAgent failed: {e}", exc_info=True)
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

    async def _create_package(
        self,
        tool_key: str,
        source_path: str,
        output_dir: str,
        include_deps: bool,
    ) -> Optional[Path]:
        """
        Create tool package.
        
        Args:
            tool_key: Tool identifier
            source_path: Source path
            output_dir: Output directory
            include_deps: Include dependencies
            
        Returns:
            Path to package or None
        """
        try:
            source = Path(source_path)
            output = Path(output_dir)
            output.mkdir(parents=True, exist_ok=True)

            package_path = output / f"{tool_key}.zip"

            logger.info(f"Creating package: {package_path}")

            with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add source files
                if source.is_file():
                    zf.write(source, arcname=source.name)
                elif source.is_dir():
                    for item in source.rglob("*"):
                        if item.is_file():
                            arcname = item.relative_to(source.parent)
                            zf.write(item, arcname=arcname)

                # Add dependencies if requested
                if include_deps:
                    req_file = source / "requirements.txt"
                    if req_file.exists():
                        zf.write(req_file, arcname="requirements.txt")

            logger.info(f"Package created: {package_path}")
            return package_path

        except Exception as e:
            logger.error(f"Failed to create package: {e}", exc_info=True)
            return None

    async def _generate_manifest(
        self,
        tool_key: str,
        source_path: str,
    ) -> Dict[str, Any]:
        """
        Generate package manifest.
        
        Args:
            tool_key: Tool identifier
            source_path: Source path
            
        Returns:
            Manifest dictionary
        """
        source = Path(source_path)

        # Count files
        file_count = 0
        total_size = 0
        if source.is_file():
            file_count = 1
            total_size = source.stat().st_size
        elif source.is_dir():
            for item in source.rglob("*"):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size

        manifest = {
            "id": tool_key,
            "name": tool_key,
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "source_path": str(source_path),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "capabilities": [
                "runtime.execute",
                "graph.node",
                "terminal.stream",
            ],
            "permissions": {
                "filesystem": ["workspace"],
                "network": False,
                "subprocess": True,
            },
            "dependencies": [],
        }

        return manifest
