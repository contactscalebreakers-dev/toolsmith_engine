"""
Terminal Bridge for SB Toolsmith Pro

Bridge between process output and terminal UI.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Callable, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class OutputType(Enum):
    """Output line type."""

    STDOUT = "stdout"
    STDERR = "stderr"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class OutputLine:
    """Single output line."""

    text: str
    output_type: OutputType
    timestamp: float
    line_number: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "type": self.output_type.value,
            "timestamp": self.timestamp,
            "line_number": self.line_number,
        }


class TerminalBridge:
    """Bridge between process and terminal UI."""

    def __init__(self, max_lines: int = 10000):
        """
        Initialize terminal bridge.
        
        Args:
            max_lines: Maximum lines to keep in buffer
        """
        self.max_lines = max_lines
        self._lines: List[OutputLine] = []
        self._line_number = 0
        self._callbacks: List[Callable[[OutputLine], None]] = []
        self._lock = asyncio.Lock()

    def add_callback(self, callback: Callable[[OutputLine], None]) -> None:
        """Add output callback."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[OutputLine], None]) -> None:
        """Remove output callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def write_stdout(self, text: str) -> None:
        """Write stdout line."""
        await self._write(text, OutputType.STDOUT)

    async def write_stderr(self, text: str) -> None:
        """Write stderr line."""
        await self._write(text, OutputType.STDERR)

    async def write_info(self, text: str) -> None:
        """Write info message."""
        await self._write(text, OutputType.INFO)

    async def write_warning(self, text: str) -> None:
        """Write warning message."""
        await self._write(text, OutputType.WARNING)

    async def write_error(self, text: str) -> None:
        """Write error message."""
        await self._write(text, OutputType.ERROR)

    async def write_success(self, text: str) -> None:
        """Write success message."""
        await self._write(text, OutputType.SUCCESS)

    async def _write(self, text: str, output_type: OutputType) -> None:
        """Write line to terminal."""
        import time

        async with self._lock:
            line = OutputLine(
                text=text,
                output_type=output_type,
                timestamp=time.time(),
                line_number=self._line_number,
            )

            self._line_number += 1
            self._lines.append(line)

            # Trim buffer
            if len(self._lines) > self.max_lines:
                self._lines = self._lines[-self.max_lines :]

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(line)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    async def clear(self) -> None:
        """Clear terminal."""
        async with self._lock:
            self._lines.clear()
            self._line_number = 0

    async def get_lines(
        self,
        start: int = 0,
        end: Optional[int] = None,
    ) -> List[OutputLine]:
        """Get lines from buffer."""
        async with self._lock:
            end = end or len(self._lines)
            return self._lines[start:end]

    async def get_all_lines(self) -> List[OutputLine]:
        """Get all lines."""
        async with self._lock:
            return self._lines.copy()

    async def get_lines_as_text(self) -> str:
        """Get all lines as text."""
        async with self._lock:
            return "\n".join(line.text for line in self._lines)

    async def get_stats(self) -> Dict[str, Any]:
        """Get terminal statistics."""
        async with self._lock:
            return {
                "total_lines": len(self._lines),
                "line_number": self._line_number,
                "callbacks": len(self._callbacks),
                "stdout_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.STDOUT
                ),
                "stderr_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.STDERR
                ),
                "info_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.INFO
                ),
                "warning_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.WARNING
                ),
                "error_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.ERROR
                ),
                "success_lines": sum(
                    1 for line in self._lines
                    if line.output_type == OutputType.SUCCESS
                ),
            }


class ExecutionTerminal:
    """Terminal for execution session."""

    def __init__(self, session_id: str):
        """
        Initialize execution terminal.
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.bridge = TerminalBridge()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._is_running = False

    async def start(self) -> None:
        """Start execution session."""
        import time

        self.start_time = time.time()
        self._is_running = True
        await self.bridge.write_info(f"=== Execution started: {self.session_id} ===")

    async def end(self, returncode: int = 0) -> None:
        """End execution session."""
        import time

        self.end_time = time.time()
        self._is_running = False

        duration = self.end_time - self.start_time if self.start_time else 0

        if returncode == 0:
            await self.bridge.write_success(
                f"=== Execution completed successfully ({duration:.2f}s) ==="
            )
        else:
            await self.bridge.write_error(
                f"=== Execution failed with code {returncode} ({duration:.2f}s) ==="
            )

    def is_running(self) -> bool:
        """Check if execution is running."""
        return self._is_running

    def get_duration(self) -> Optional[float]:
        """Get execution duration."""
        if not self.start_time:
            return None

        end = self.end_time or __import__("time").time()
        return end - self.start_time

    async def get_output(self) -> str:
        """Get all output."""
        return await self.bridge.get_lines_as_text()

    async def get_stats(self) -> Dict[str, Any]:
        """Get terminal statistics."""
        stats = await self.bridge.get_stats()
        stats.update({
            "session_id": self.session_id,
            "is_running": self._is_running,
            "duration": self.get_duration(),
            "start_time": self.start_time,
            "end_time": self.end_time,
        })
        return stats
