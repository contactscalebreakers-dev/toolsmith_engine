"""
Async Task Scheduler for SB Toolsmith Pro

Manages coroutine scheduling, retries, task dependencies, and cancellation.
"""

import asyncio
import dataclasses
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclasses.dataclass
class RetryPolicy:
    """Retry policy for failed tasks."""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0


@dataclasses.dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempts: int = 0
    duration: Optional[float] = None

    @property
    def is_success(self) -> bool:
        """Check if task succeeded."""
        return self.status == TaskStatus.COMPLETED

    @property
    def is_failure(self) -> bool:
        """Check if task failed."""
        return self.status == TaskStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self.status == TaskStatus.CANCELLED


class Task:
    """Represents a scheduled task."""

    def __init__(
        self,
        coro: Any,
        task_id: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        dependencies: Optional[Set[str]] = None,
        timeout: Optional[float] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        Initialize task.
        
        Args:
            coro: Coroutine to execute
            task_id: Unique task identifier
            retry_policy: Retry configuration
            dependencies: Set of task IDs this task depends on
            timeout: Task timeout in seconds
            on_complete: Callback on completion
            on_error: Callback on error
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.coro = coro
        self.retry_policy = retry_policy or RetryPolicy()
        self.dependencies = dependencies or set()
        self.timeout = timeout
        self.on_complete = on_complete
        self.on_error = on_error
        
        self.status = TaskStatus.PENDING
        self.result: Optional[TaskResult] = None
        self.handle: Optional[asyncio.Task] = None
        self.attempts = 0

    async def execute(self) -> TaskResult:
        """Execute the task with retry logic."""
        self.status = TaskStatus.RUNNING
        start_time = datetime.utcnow()
        
        while self.attempts < self.retry_policy.max_retries + 1:
            self.attempts += 1
            
            try:
                logger.debug(f"Executing task {self.task_id} (attempt {self.attempts})")
                
                # Execute with timeout
                if self.timeout:
                    result = await asyncio.wait_for(self.coro, timeout=self.timeout)
                else:
                    result = await self.coro
                
                # Success
                self.status = TaskStatus.COMPLETED
                self.result = TaskResult(
                    task_id=self.task_id,
                    status=self.status,
                    result=result,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    attempts=self.attempts,
                    duration=(datetime.utcnow() - start_time).total_seconds()
                )
                
                if self.on_complete:
                    await self._safe_call(self.on_complete, self.result)
                
                logger.info(f"Task {self.task_id} completed successfully")
                return self.result
                
            except asyncio.CancelledError:
                self.status = TaskStatus.CANCELLED
                self.result = TaskResult(
                    task_id=self.task_id,
                    status=self.status,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    attempts=self.attempts,
                    duration=(datetime.utcnow() - start_time).total_seconds()
                )
                logger.info(f"Task {self.task_id} cancelled")
                raise
                
            except Exception as e:
                self.attempts += 1
                
                if self.attempts <= self.retry_policy.max_retries:
                    # Calculate backoff delay
                    delay = min(
                        self.retry_policy.initial_delay * (
                            self.retry_policy.exponential_base ** (self.attempts - 1)
                        ),
                        self.retry_policy.max_delay
                    )
                    
                    logger.warning(
                        f"Task {self.task_id} failed (attempt {self.attempts}), "
                        f"retrying in {delay}s: {e}"
                    )
                    
                    self.status = TaskStatus.RETRYING
                    await asyncio.sleep(delay)
                else:
                    # Final failure
                    self.status = TaskStatus.FAILED
                    self.result = TaskResult(
                        task_id=self.task_id,
                        status=self.status,
                        error=e,
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        attempts=self.attempts,
                        duration=(datetime.utcnow() - start_time).total_seconds()
                    )
                    
                    if self.on_error:
                        await self._safe_call(self.on_error, self.result)
                    
                    logger.error(
                        f"Task {self.task_id} failed after {self.attempts} attempts: {e}",
                        exc_info=True
                    )
                    return self.result
        
        # Should not reach here
        raise RuntimeError(f"Task {self.task_id} execution logic error")

    async def _safe_call(self, callback: Callable, result: TaskResult) -> None:
        """Safely call a callback."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(result)
            else:
                callback(result)
        except Exception as e:
            logger.error(f"Callback error: {e}", exc_info=True)

    def cancel(self) -> bool:
        """Cancel the task."""
        if self.handle and not self.handle.done():
            self.handle.cancel()
            return True
        return False


class Scheduler:
    """
    Async task scheduler with dependency management and retry support.
    """

    def __init__(self):
        """Initialize scheduler."""
        self._tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, TaskResult] = {}
        self._lock = asyncio.Lock()

    async def schedule(
        self,
        coro: Any,
        task_id: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        dependencies: Optional[Set[str]] = None,
        timeout: Optional[float] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> str:
        """
        Schedule a coroutine for execution.
        
        Args:
            coro: Coroutine to execute
            task_id: Unique task identifier
            retry_policy: Retry configuration
            dependencies: Set of task IDs this task depends on
            timeout: Task timeout in seconds
            on_complete: Callback on completion
            on_error: Callback on error
            
        Returns:
            Task ID
        """
        task = Task(
            coro=coro,
            task_id=task_id,
            retry_policy=retry_policy,
            dependencies=dependencies,
            timeout=timeout,
            on_complete=on_complete,
            on_error=on_error,
        )
        
        async with self._lock:
            self._tasks[task.task_id] = task
        
        logger.debug(f"Scheduled task {task.task_id}")
        return task.task_id

    async def execute_task(self, task_id: str) -> TaskResult:
        """
        Execute a task and wait for completion.
        
        Args:
            task_id: Task ID to execute
            
        Returns:
            Task result
        """
        async with self._lock:
            task = self._tasks.get(task_id)
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Wait for dependencies
        if task.dependencies:
            logger.debug(f"Task {task_id} waiting for dependencies: {task.dependencies}")
            while True:
                async with self._lock:
                    completed = all(
                        dep_id in self._completed_tasks
                        for dep_id in task.dependencies
                    )
                if completed:
                    break
                await asyncio.sleep(0.1)
        
        # Execute task
        result = await task.execute()
        
        async with self._lock:
            self._completed_tasks[task_id] = result
        
        return result

    async def execute_all(self) -> Dict[str, TaskResult]:
        """
        Execute all scheduled tasks.
        
        Returns:
            Dictionary of task results
        """
        async with self._lock:
            task_ids = list(self._tasks.keys())
        
        results = {}
        for task_id in task_ids:
            try:
                result = await self.execute_task(task_id)
                results[task_id] = result
            except Exception as e:
                logger.error(f"Failed to execute task {task_id}: {e}")
                results[task_id] = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=e
                )
        
        return results

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        async with self._lock:
            task = self._tasks.get(task_id)
        
        if task:
            return task.cancel()
        return False

    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result of a completed task."""
        async with self._lock:
            return self._completed_tasks.get(task_id)

    async def get_all_results(self) -> Dict[str, TaskResult]:
        """Get all completed task results."""
        async with self._lock:
            return self._completed_tasks.copy()

    async def clear(self) -> None:
        """Clear all tasks."""
        async with self._lock:
            self._tasks.clear()
            self._completed_tasks.clear()

    def get_task_count(self) -> int:
        """Get number of scheduled tasks."""
        return len(self._tasks)

    def get_completed_count(self) -> int:
        """Get number of completed tasks."""
        return len(self._completed_tasks)
