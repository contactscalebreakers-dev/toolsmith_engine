"""
Execution Monitor for SB Toolsmith Pro

Monitor and track execution sessions.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionMetrics:
    """Execution metrics."""

    start_time: float
    end_time: Optional[float] = None
    duration: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    output_lines: int = 0
    error_lines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "output_lines": self.output_lines,
            "error_lines": self.error_lines,
        }


@dataclass
class ExecutionSession:
    """Execution session."""

    session_id: str
    tool_name: str
    command: List[str]
    status: ExecutionStatus = ExecutionStatus.PENDING
    metrics: ExecutionMetrics = field(default_factory=lambda: ExecutionMetrics(
        start_time=time.time()
    ))
    returncode: Optional[int] = None
    error_message: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "command": self.command,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "returncode": self.returncode,
            "error_message": self.error_message,
            "created_at": self.created_at,
        }


class ExecutionMonitor:
    """Monitor execution sessions."""

    def __init__(self):
        """Initialize execution monitor."""
        self._sessions: Dict[str, ExecutionSession] = {}
        self._history: List[ExecutionSession] = []
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        session_id: str,
        tool_name: str,
        command: List[str],
    ) -> ExecutionSession:
        """
        Create execution session.
        
        Args:
            session_id: Unique session ID
            tool_name: Tool name
            command: Command to execute
            
        Returns:
            ExecutionSession
        """
        async with self._lock:
            session = ExecutionSession(
                session_id=session_id,
                tool_name=tool_name,
                command=command,
            )

            self._sessions[session_id] = session
            logger.info(f"Execution session created: {session_id}")

            return session

    async def start_session(self, session_id: str) -> bool:
        """Start execution session."""
        async with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]
            session.status = ExecutionStatus.RUNNING
            session.metrics.start_time = time.time()

            logger.info(f"Execution session started: {session_id}")
            return True

    async def end_session(
        self,
        session_id: str,
        returncode: int = 0,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        End execution session.
        
        Args:
            session_id: Session ID
            returncode: Process return code
            error_message: Error message if any
            
        Returns:
            True if successful
        """
        async with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]
            session.returncode = returncode
            session.error_message = error_message
            session.metrics.end_time = time.time()
            session.metrics.duration = (
                session.metrics.end_time - session.metrics.start_time
            )

            if returncode == 0:
                session.status = ExecutionStatus.SUCCESS
            else:
                session.status = ExecutionStatus.FAILED

            # Move to history
            self._history.append(session)
            del self._sessions[session_id]

            logger.info(f"Execution session ended: {session_id} (code: {returncode})")
            return True

    async def timeout_session(self, session_id: str) -> bool:
        """Mark session as timed out."""
        async with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]
            session.status = ExecutionStatus.TIMEOUT
            session.metrics.end_time = time.time()
            session.metrics.duration = (
                session.metrics.end_time - session.metrics.start_time
            )

            # Move to history
            self._history.append(session)
            del self._sessions[session_id]

            logger.warning(f"Execution session timed out: {session_id}")
            return True

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel execution session."""
        async with self._lock:
            if session_id not in self._sessions:
                return False

            session = self._sessions[session_id]
            session.status = ExecutionStatus.CANCELLED
            session.metrics.end_time = time.time()
            session.metrics.duration = (
                session.metrics.end_time - session.metrics.start_time
            )

            # Move to history
            self._history.append(session)
            del self._sessions[session_id]

            logger.info(f"Execution session cancelled: {session_id}")
            return True

    async def get_session(self, session_id: str) -> Optional[ExecutionSession]:
        """Get session."""
        async with self._lock:
            return self._sessions.get(session_id)

    async def get_active_sessions(self) -> List[ExecutionSession]:
        """Get all active sessions."""
        async with self._lock:
            return list(self._sessions.values())

    async def get_history(
        self,
        limit: int = 100,
        tool_name: Optional[str] = None,
    ) -> List[ExecutionSession]:
        """
        Get execution history.
        
        Args:
            limit: Maximum number of sessions
            tool_name: Filter by tool name
            
        Returns:
            List of sessions
        """
        async with self._lock:
            history = self._history

            if tool_name:
                history = [s for s in history if s.tool_name == tool_name]

            return history[-limit:]

    async def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        async with self._lock:
            total_sessions = len(self._sessions) + len(self._history)
            successful = sum(
                1 for s in self._history
                if s.status == ExecutionStatus.SUCCESS
            )
            failed = sum(
                1 for s in self._history
                if s.status == ExecutionStatus.FAILED
            )
            timeout = sum(
                1 for s in self._history
                if s.status == ExecutionStatus.TIMEOUT
            )

            avg_duration = 0.0
            if self._history:
                avg_duration = sum(s.metrics.duration for s in self._history) / len(
                    self._history
                )

            return {
                "active_sessions": len(self._sessions),
                "total_sessions": total_sessions,
                "successful": successful,
                "failed": failed,
                "timeout": timeout,
                "success_rate": successful / len(self._history)
                if self._history else 0.0,
                "average_duration": avg_duration,
                "history_size": len(self._history),
            }

    async def cleanup_history(self, keep_count: int = 1000) -> int:
        """
        Clean up old history.
        
        Args:
            keep_count: Number of sessions to keep
            
        Returns:
            Number of sessions removed
        """
        async with self._lock:
            if len(self._history) > keep_count:
                removed = len(self._history) - keep_count
                self._history = self._history[-keep_count:]
                logger.info(f"Cleaned up {removed} old sessions")
                return removed
            return 0
