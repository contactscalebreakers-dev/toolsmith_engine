"""
Process Runner for SB Toolsmith Pro

Execute and monitor processes with real-time output.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of process execution."""

    pid: int
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timeout: bool
    success: bool
    start_time: float = field(default_factory=time.time)
    end_time: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pid": self.pid,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "timeout": self.timeout,
            "success": self.success,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class ProcessMonitor:
    """Monitor process execution."""

    def __init__(self, process: asyncio.subprocess.Process):
        """
        Initialize process monitor.
        
        Args:
            process: Subprocess to monitor
        """
        self.process = process
        self.start_time = time.time()
        self.stdout_lines: List[str] = []
        self.stderr_lines: List[str] = []
        self._running = True

    async def stream_output(
        self,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Stream process output.
        
        Args:
            on_stdout: Callback for stdout lines
            on_stderr: Callback for stderr lines
        """
        tasks = []

        if self.process.stdout:
            tasks.append(self._read_stream(
                self.process.stdout,
                self.stdout_lines,
                on_stdout,
            ))

        if self.process.stderr:
            tasks.append(self._read_stream(
                self.process.stderr,
                self.stderr_lines,
                on_stderr,
            ))

        if tasks:
            await asyncio.gather(*tasks)

    async def _read_stream(
        self,
        stream: asyncio.StreamReader,
        lines: List[str],
        callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Read from stream."""
        try:
            while self._running:
                line = await stream.readline()
                if not line:
                    break

                decoded = line.decode().rstrip()
                lines.append(decoded)

                if callback:
                    callback(decoded)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Stream reading error: {e}")

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

    def get_duration(self) -> float:
        """Get elapsed time."""
        return time.time() - self.start_time

    def get_output(self) -> tuple[str, str]:
        """Get accumulated output."""
        return "\n".join(self.stdout_lines), "\n".join(self.stderr_lines)


class ProcessRunner:
    """Execute and manage processes."""

    def __init__(self):
        """Initialize process runner."""
        self._processes: Dict[int, asyncio.subprocess.Process] = {}

    async def run(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
    ) -> ProcessResult:
        """
        Run process and wait for completion.
        
        Args:
            command: Command to run
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            capture_output: Capture stdout/stderr
            
        Returns:
            ProcessResult
        """
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                cwd=cwd,
                env=env,
            )

            self._processes[process.pid] = process

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )

                duration = time.time() - start_time

                result = ProcessResult(
                    pid=process.pid,
                    returncode=process.returncode,
                    stdout=stdout.decode() if stdout else "",
                    stderr=stderr.decode() if stderr else "",
                    duration=duration,
                    timeout=False,
                    success=process.returncode == 0,
                    start_time=start_time,
                    end_time=time.time(),
                )

                logger.info(f"Process {process.pid} completed: {process.returncode}")
                return result

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

                duration = time.time() - start_time

                result = ProcessResult(
                    pid=process.pid,
                    returncode=-1,
                    stdout="",
                    stderr=f"Process timeout after {timeout} seconds",
                    duration=duration,
                    timeout=True,
                    success=False,
                    start_time=start_time,
                    end_time=time.time(),
                )

                logger.warning(f"Process {process.pid} timed out")
                return result

            finally:
                if process.pid in self._processes:
                    del self._processes[process.pid]

        except Exception as e:
            duration = time.time() - start_time

            result = ProcessResult(
                pid=-1,
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                timeout=False,
                success=False,
                start_time=start_time,
                end_time=time.time(),
            )

            logger.error(f"Process execution failed: {e}")
            return result

    async def run_streaming(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ) -> ProcessResult:
        """
        Run process with streaming output.
        
        Args:
            command: Command to run
            cwd: Working directory
            env: Environment variables
            timeout: Timeout in seconds
            on_stdout: Callback for stdout lines
            on_stderr: Callback for stderr lines
            
        Returns:
            ProcessResult
        """
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            self._processes[process.pid] = process
            monitor = ProcessMonitor(process)

            try:
                # Stream output and wait for completion
                stream_task = asyncio.create_task(
                    monitor.stream_output(on_stdout, on_stderr)
                )

                returncode = await asyncio.wait_for(
                    process.wait(),
                    timeout=timeout,
                )

                # Wait for stream to finish
                monitor.stop()
                await asyncio.wait_for(stream_task, timeout=5)

                stdout, stderr = monitor.get_output()
                duration = time.time() - start_time

                result = ProcessResult(
                    pid=process.pid,
                    returncode=returncode,
                    stdout=stdout,
                    stderr=stderr,
                    duration=duration,
                    timeout=False,
                    success=returncode == 0,
                    start_time=start_time,
                    end_time=time.time(),
                )

                logger.info(f"Process {process.pid} completed: {returncode}")
                return result

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                monitor.stop()

                stdout, stderr = monitor.get_output()
                duration = time.time() - start_time

                result = ProcessResult(
                    pid=process.pid,
                    returncode=-1,
                    stdout=stdout,
                    stderr=stderr + f"\nProcess timeout after {timeout} seconds",
                    duration=duration,
                    timeout=True,
                    success=False,
                    start_time=start_time,
                    end_time=time.time(),
                )

                logger.warning(f"Process {process.pid} timed out")
                return result

            finally:
                if process.pid in self._processes:
                    del self._processes[process.pid]

        except Exception as e:
            duration = time.time() - start_time

            result = ProcessResult(
                pid=-1,
                returncode=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                timeout=False,
                success=False,
                start_time=start_time,
                end_time=time.time(),
            )

            logger.error(f"Process streaming failed: {e}")
            return result

    def get_active_processes(self) -> List[int]:
        """Get list of active process IDs."""
        return list(self._processes.keys())

    async def terminate_process(self, pid: int) -> bool:
        """Terminate a process."""
        if pid in self._processes:
            try:
                self._processes[pid].terminate()
                await self._processes[pid].wait()
                del self._processes[pid]
                return True
            except:
                return False
        return False

    async def kill_process(self, pid: int) -> bool:
        """Kill a process."""
        if pid in self._processes:
            try:
                self._processes[pid].kill()
                await self._processes[pid].wait()
                del self._processes[pid]
                return True
            except:
                return False
        return False

    async def cleanup(self) -> None:
        """Clean up all processes."""
        for pid in list(self._processes.keys()):
            await self.kill_process(pid)
