"""
Sandbox System for SB Toolsmith Pro

Process isolation and resource limiting.
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class SandboxConfig:
    """Sandbox configuration."""

    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_percent: float = 80.0,
        max_runtime_seconds: int = 300,
        max_processes: int = 10,
        network_enabled: bool = False,
        file_access_restricted: bool = True,
    ):
        """
        Initialize sandbox config.
        
        Args:
            max_memory_mb: Maximum memory in MB
            max_cpu_percent: Maximum CPU percentage
            max_runtime_seconds: Maximum runtime in seconds
            max_processes: Maximum number of processes
            network_enabled: Allow network access
            file_access_restricted: Restrict file system access
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.max_runtime_seconds = max_runtime_seconds
        self.max_processes = max_processes
        self.network_enabled = network_enabled
        self.file_access_restricted = file_access_restricted

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "max_runtime_seconds": self.max_runtime_seconds,
            "max_processes": self.max_processes,
            "network_enabled": self.network_enabled,
            "file_access_restricted": self.file_access_restricted,
        }


class Sandbox:
    """Isolated execution sandbox."""

    def __init__(
        self,
        sandbox_id: str,
        config: SandboxConfig,
        work_dir: Optional[Path] = None,
    ):
        """
        Initialize sandbox.
        
        Args:
            sandbox_id: Unique sandbox identifier
            config: Sandbox configuration
            work_dir: Working directory (created if None)
        """
        self.sandbox_id = sandbox_id
        self.config = config
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix=f"sandbox-{sandbox_id}-"))
        self._processes: Dict[int, asyncio.subprocess.Process] = {}
        self._resource_limits_applied = False

    async def initialize(self) -> bool:
        """
        Initialize sandbox.
        
        Returns:
            True if successful
        """
        try:
            # Create work directory
            self.work_dir.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            (self.work_dir / "tmp").mkdir(exist_ok=True)
            (self.work_dir / "output").mkdir(exist_ok=True)
            (self.work_dir / "cache").mkdir(exist_ok=True)

            # Apply resource limits
            if RESOURCE_AVAILABLE:
                self._apply_resource_limits()
                self._resource_limits_applied = True

            logger.info(f"Sandbox initialized: {self.sandbox_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sandbox: {e}")
            return False

    def _apply_resource_limits(self) -> None:
        """Apply resource limits using resource module."""
        try:
            # Memory limit
            memory_bytes = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_AS,
                (memory_bytes, memory_bytes),
            )

            # Process limit
            resource.setrlimit(
                resource.RLIMIT_NPROC,
                (self.config.max_processes, self.config.max_processes),
            )

            # File size limit (1GB)
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (1024 * 1024 * 1024, 1024 * 1024 * 1024),
            )

            logger.info(f"Resource limits applied for sandbox: {self.sandbox_id}")

        except Exception as e:
            logger.warning(f"Failed to apply resource limits: {e}")

    async def run_process(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
    ) -> Dict[str, Any]:
        """
        Run process in sandbox.
        
        Args:
            command: Command to run
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Capture stdout/stderr
            
        Returns:
            Process result
        """
        try:
            # Prepare environment
            sandbox_env = os.environ.copy()
            if env:
                sandbox_env.update(env)

            # Disable network if restricted
            if not self.config.network_enabled:
                sandbox_env["http_proxy"] = "127.0.0.1:1"
                sandbox_env["https_proxy"] = "127.0.0.1:1"

            # Use timeout from config if not specified
            timeout = timeout or self.config.max_runtime_seconds

            # Create process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=str(self.work_dir),
                env=sandbox_env,
            )

            self._processes[process.pid] = process

            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )

                result = {
                    "pid": process.pid,
                    "returncode": process.returncode,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "timeout": False,
                    "success": process.returncode == 0,
                }

                logger.info(f"Process {process.pid} completed: {process.returncode}")
                return result

            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()

                result = {
                    "pid": process.pid,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Process timeout after {timeout} seconds",
                    "timeout": True,
                    "success": False,
                }

                logger.warning(f"Process {process.pid} timed out")
                return result

            finally:
                # Remove from tracking
                if process.pid in self._processes:
                    del self._processes[process.pid]

        except Exception as e:
            logger.error(f"Process execution failed: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "timeout": False,
                "success": False,
            }

    async def run_process_streaming(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> asyncio.subprocess.Process:
        """
        Run process with streaming output.
        
        Args:
            command: Command to run
            env: Environment variables
            timeout: Timeout in seconds
            
        Returns:
            Process object for streaming
        """
        # Prepare environment
        sandbox_env = os.environ.copy()
        if env:
            sandbox_env.update(env)

        # Create process
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.work_dir),
            env=sandbox_env,
        )

        self._processes[process.pid] = process
        return process

    async def cleanup(self) -> None:
        """Clean up sandbox."""
        try:
            # Kill any remaining processes
            for pid, process in list(self._processes.items()):
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass

            # Remove work directory
            if self.work_dir.exists():
                shutil.rmtree(self.work_dir)

            logger.info(f"Sandbox cleaned up: {self.sandbox_id}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def get_work_dir(self) -> Path:
        """Get sandbox work directory."""
        return self.work_dir

    def get_output_dir(self) -> Path:
        """Get sandbox output directory."""
        return self.work_dir / "output"

    def get_temp_dir(self) -> Path:
        """Get sandbox temp directory."""
        return self.work_dir / "tmp"

    def get_cache_dir(self) -> Path:
        """Get sandbox cache directory."""
        return self.work_dir / "cache"

    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics."""
        return {
            "sandbox_id": self.sandbox_id,
            "work_dir": str(self.work_dir),
            "active_processes": len(self._processes),
            "config": self.config.to_dict(),
            "resource_limits_applied": self._resource_limits_applied,
        }


class SandboxManager:
    """Manage multiple sandboxes."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize sandbox manager.
        
        Args:
            base_dir: Base directory for sandboxes
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "sb-toolsmith-sandboxes"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._sandboxes: Dict[str, Sandbox] = {}

    async def create_sandbox(
        self,
        sandbox_id: str,
        config: Optional[SandboxConfig] = None,
    ) -> Sandbox:
        """
        Create a new sandbox.
        
        Args:
            sandbox_id: Unique sandbox identifier
            config: Sandbox configuration
            
        Returns:
            Sandbox instance
        """
        config = config or SandboxConfig()
        work_dir = self.base_dir / sandbox_id

        sandbox = Sandbox(sandbox_id, config, work_dir)
        await sandbox.initialize()

        self._sandboxes[sandbox_id] = sandbox
        logger.info(f"Sandbox created: {sandbox_id}")

        return sandbox

    async def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """Get existing sandbox."""
        return self._sandboxes.get(sandbox_id)

    async def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete sandbox."""
        if sandbox_id in self._sandboxes:
            sandbox = self._sandboxes[sandbox_id]
            await sandbox.cleanup()
            del self._sandboxes[sandbox_id]
            logger.info(f"Sandbox deleted: {sandbox_id}")
            return True
        return False

    async def cleanup_all(self) -> None:
        """Clean up all sandboxes."""
        for sandbox_id in list(self._sandboxes.keys()):
            await self.delete_sandbox(sandbox_id)

    def list_sandboxes(self) -> List[str]:
        """List all sandboxes."""
        return list(self._sandboxes.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "total_sandboxes": len(self._sandboxes),
            "base_dir": str(self.base_dir),
            "sandboxes": {
                sid: sandbox.get_stats()
                for sid, sandbox in self._sandboxes.items()
            },
        }
