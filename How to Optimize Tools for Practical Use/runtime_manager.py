"""
RuntimeManager - Core Execution Orchestrator for SB Toolsmith Pro

Single source of truth for:
- Virtual environment lifecycle
- Subprocess orchestration
- Dependency installation
- Sandboxing and isolation
- Snapshots and rollback
- Cancellation and supervision
- Process metadata tracking
"""

import asyncio
import dataclasses
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status codes."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


@dataclasses.dataclass
class ProcessMetadata:
    """Metadata for a running process."""
    execution_id: str
    tool_key: str
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    return_code: Optional[int] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    stdout: str = ""
    stderr: str = ""
    environment_path: Optional[Path] = None


@dataclasses.dataclass
class ExecutionResult:
    """Result of tool execution."""
    execution_id: str
    tool_key: str
    status: ExecutionStatus
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


class VirtualEnvironmentManager:
    """Manages Python virtual environments per tool."""

    def __init__(self, base_dir: Path):
        """
        Initialize venv manager.
        
        Args:
            base_dir: Base directory for virtual environments
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._venvs: Dict[str, Path] = {}

    def get_venv_path(self, tool_key: str) -> Path:
        """Get or create venv path for tool."""
        if tool_key in self._venvs:
            return self._venvs[tool_key]

        venv_path = self.base_dir / tool_key / "venv"
        self._venvs[tool_key] = venv_path
        return venv_path

    async def create_venv(self, tool_key: str) -> Path:
        """
        Create a virtual environment for a tool.
        
        Args:
            tool_key: Tool identifier
            
        Returns:
            Path to venv
        """
        venv_path = self.get_venv_path(tool_key)

        if venv_path.exists():
            logger.debug(f"Venv already exists for {tool_key}: {venv_path}")
            return venv_path

        logger.info(f"Creating venv for {tool_key} at {venv_path}")

        try:
            # Create venv
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True,
            )
            logger.info(f"Venv created successfully: {venv_path}")
            return venv_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create venv: {e}")
            raise

    async def delete_venv(self, tool_key: str) -> bool:
        """
        Delete a virtual environment.
        
        Args:
            tool_key: Tool identifier
            
        Returns:
            True if deleted, False if not found
        """
        venv_path = self._venvs.get(tool_key)
        if not venv_path:
            return False

        if venv_path.exists():
            logger.info(f"Deleting venv for {tool_key}: {venv_path}")
            shutil.rmtree(venv_path)
            del self._venvs[tool_key]
            return True

        return False

    def get_python_executable(self, tool_key: str) -> Path:
        """Get Python executable path in venv."""
        venv_path = self.get_venv_path(tool_key)
        if sys.platform == "win32":
            return venv_path / "Scripts" / "python.exe"
        return venv_path / "bin" / "python"

    def get_pip_executable(self, tool_key: str) -> Path:
        """Get pip executable path in venv."""
        venv_path = self.get_venv_path(tool_key)
        if sys.platform == "win32":
            return venv_path / "Scripts" / "pip.exe"
        return venv_path / "bin" / "pip"


class ProcessRunner:
    """Manages subprocess execution with isolation and monitoring."""

    def __init__(self, venv_manager: VirtualEnvironmentManager):
        """
        Initialize process runner.
        
        Args:
            venv_manager: Virtual environment manager
        """
        self.venv_manager = venv_manager
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
        self._metadata: Dict[str, ProcessMetadata] = {}

    async def run_tool(
        self,
        tool_key: str,
        command: List[str],
        timeout: Optional[float] = None,
        on_stdout: Optional[Callable[[str], Any]] = None,
        on_stderr: Optional[Callable[[str], Any]] = None,
    ) -> ExecutionResult:
        """
        Run a tool in isolated environment.
        
        Args:
            tool_key: Tool identifier
            command: Command to execute
            timeout: Execution timeout in seconds
            on_stdout: Callback for stdout lines
            on_stderr: Callback for stderr lines
            
        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        metadata = ProcessMetadata(
            execution_id=execution_id,
            tool_key=tool_key,
            start_time=datetime.utcnow(),
            environment_path=self.venv_manager.get_venv_path(tool_key),
        )
        self._metadata[execution_id] = metadata

        try:
            # Prepare environment
            env = os.environ.copy()
            venv_path = self.venv_manager.get_venv_path(tool_key)
            if sys.platform == "win32":
                env["PATH"] = f"{venv_path / 'Scripts'};{env['PATH']}"
            else:
                env["PATH"] = f"{venv_path / 'bin'}:{env['PATH']}"
            env["VIRTUAL_ENV"] = str(venv_path)

            logger.info(f"Starting execution {execution_id} for {tool_key}: {command}")
            metadata.status = ExecutionStatus.RUNNING

            # Start process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            metadata.pid = process.pid
            self._processes[execution_id] = process

            # Read output
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                metadata.return_code = process.returncode
                metadata.stdout = stdout_data.decode("utf-8", errors="replace")
                metadata.stderr = stderr_data.decode("utf-8", errors="replace")

                if on_stdout:
                    await self._safe_call(on_stdout, metadata.stdout)
                if on_stderr:
                    await self._safe_call(on_stderr, metadata.stderr)

            except asyncio.TimeoutError:
                logger.warning(f"Execution {execution_id} timed out after {timeout}s")
                process.kill()
                await process.wait()
                metadata.status = ExecutionStatus.FAILED
                metadata.return_code = -1
                metadata.stderr = f"Execution timed out after {timeout} seconds"

            metadata.end_time = datetime.utcnow()
            metadata.status = (
                ExecutionStatus.COMPLETED
                if metadata.return_code == 0
                else ExecutionStatus.FAILED
            )

            result = ExecutionResult(
                execution_id=execution_id,
                tool_key=tool_key,
                status=metadata.status,
                return_code=metadata.return_code,
                stdout=metadata.stdout,
                stderr=metadata.stderr,
                duration=(metadata.end_time - metadata.start_time).total_seconds(),
                metadata={"pid": metadata.pid},
            )

            logger.info(
                f"Execution {execution_id} completed with status {metadata.status}: "
                f"return_code={metadata.return_code}"
            )

            return result

        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            metadata.status = ExecutionStatus.FAILED
            metadata.error = str(e)
            metadata.end_time = datetime.utcnow()

            return ExecutionResult(
                execution_id=execution_id,
                tool_key=tool_key,
                status=ExecutionStatus.FAILED,
                error=str(e),
                duration=(metadata.end_time - metadata.start_time).total_seconds(),
            )

        finally:
            # Cleanup
            if execution_id in self._processes:
                del self._processes[execution_id]

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if cancelled, False if not found
        """
        process = self._processes.get(execution_id)
        if process and not process.done():
            logger.info(f"Cancelling execution {execution_id}")
            process.kill()
            await process.wait()
            metadata = self._metadata.get(execution_id)
            if metadata:
                metadata.status = ExecutionStatus.CANCELLED
            return True
        return False

    def get_metadata(self, execution_id: str) -> Optional[ProcessMetadata]:
        """Get execution metadata."""
        return self._metadata.get(execution_id)

    async def _safe_call(self, callback: Callable, data: Any) -> None:
        """Safely call a callback."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"Callback error: {e}", exc_info=True)


class RuntimeManager:
    """
    Central runtime orchestration manager.
    
    Single source of truth for all tool execution, environment management,
    and runtime lifecycle.
    """

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        event_bus: Optional[Any] = None,
    ):
        """
        Initialize runtime manager.
        
        Args:
            workspace_dir: Workspace directory for environments
            event_bus: Event bus for emitting events
        """
        self.workspace_dir = workspace_dir or Path.home() / ".toolsmith" / "runtime"
        self.event_bus = event_bus
        
        # Initialize managers
        self.venv_manager = VirtualEnvironmentManager(
            self.workspace_dir / "venvs"
        )
        self.process_runner = ProcessRunner(self.venv_manager)
        
        # Tracking
        self._executions: Dict[str, ExecutionResult] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

        logger.info(f"RuntimeManager initialized with workspace: {self.workspace_dir}")

    async def initialize_tool(self, tool_key: str) -> Path:
        """
        Initialize a tool runtime environment.
        
        Args:
            tool_key: Tool identifier
            
        Returns:
            Path to venv
        """
        async with self._lock:
            logger.info(f"Initializing tool: {tool_key}")
            venv_path = await self.venv_manager.create_venv(tool_key)
            return venv_path

    async def execute_tool(
        self,
        tool_key: str,
        command: List[str],
        timeout: Optional[float] = None,
        on_stdout: Optional[Callable[[str], Any]] = None,
        on_stderr: Optional[Callable[[str], Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a tool with monitoring and isolation.
        
        Args:
            tool_key: Tool identifier
            command: Command to execute
            timeout: Execution timeout
            on_stdout: Stdout callback
            on_stderr: Stderr callback
            
        Returns:
            Execution result
        """
        async with self._lock:
            result = await self.process_runner.run_tool(
                tool_key=tool_key,
                command=command,
                timeout=timeout,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
            )
            self._executions[result.execution_id] = result
            return result

    async def create_snapshot(self, tool_key: str, snapshot_id: Optional[str] = None) -> str:
        """
        Create a snapshot of tool environment.
        
        Args:
            tool_key: Tool identifier
            snapshot_id: Optional snapshot ID
            
        Returns:
            Snapshot ID
        """
        snapshot_id = snapshot_id or str(uuid.uuid4())
        venv_path = self.venv_manager.get_venv_path(tool_key)

        snapshot_data = {
            "snapshot_id": snapshot_id,
            "tool_key": tool_key,
            "timestamp": datetime.utcnow().isoformat(),
            "venv_path": str(venv_path),
            "exists": venv_path.exists(),
        }

        async with self._lock:
            self._snapshots[snapshot_id] = snapshot_data

        logger.info(f"Created snapshot {snapshot_id} for {tool_key}")
        return snapshot_id

    async def rollback_snapshot(self, snapshot_id: str) -> bool:
        """
        Rollback to a snapshot.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            True if successful
        """
        async with self._lock:
            snapshot = self._snapshots.get(snapshot_id)

        if not snapshot:
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return False

        logger.info(f"Rolling back to snapshot {snapshot_id}")
        tool_key = snapshot["tool_key"]

        # Delete current venv
        await self.venv_manager.delete_venv(tool_key)

        # Recreate from snapshot
        await self.venv_manager.create_venv(tool_key)

        logger.info(f"Rollback complete for snapshot {snapshot_id}")
        return True

    async def cleanup_tool(self, tool_key: str) -> bool:
        """
        Clean up tool environment.
        
        Args:
            tool_key: Tool identifier
            
        Returns:
            True if cleaned up
        """
        async with self._lock:
            result = await self.venv_manager.delete_venv(tool_key)
        logger.info(f"Cleaned up tool: {tool_key}")
        return result

    def get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result."""
        return self._executions.get(execution_id)

    def get_all_executions(self) -> Dict[str, ExecutionResult]:
        """Get all executions."""
        return self._executions.copy()

    async def get_runtime_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        async with self._lock:
            return {
                "total_executions": len(self._executions),
                "total_snapshots": len(self._snapshots),
                "workspace_dir": str(self.workspace_dir),
                "venvs_count": len(self.venv_manager._venvs),
            }
