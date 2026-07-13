"""
Event Bus System for SB Toolsmith Pro

Provides typed event dispatch, subscription management, and event history.
All inter-component communication flows through this system.
"""

import asyncio
import dataclasses
import logging
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for execution order."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclasses.dataclass
class Event:
    """Base event class for all system events."""
    event_type: str
    timestamp: datetime = dataclasses.field(default_factory=datetime.utcnow)
    event_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Validate event after initialization."""
        if not self.event_type:
            raise ValueError("event_type cannot be empty")


# Specific Event Types
@dataclasses.dataclass
class ToolRegisteredEvent(Event):
    """Emitted when a tool is registered."""
    tool_key: str = ""
    tool_name: str = ""
    source_path: str = ""

    def __post_init__(self):
        self.event_type = "tool.registered"
        super().__post_init__()


@dataclasses.dataclass
class ToolExecutionStartedEvent(Event):
    """Emitted when tool execution begins."""
    tool_key: str = ""
    execution_id: str = ""
    args: List[str] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        self.event_type = "tool.execution.started"
        super().__post_init__()


@dataclasses.dataclass
class ToolExecutionCompletedEvent(Event):
    """Emitted when tool execution completes."""
    tool_key: str = ""
    execution_id: str = ""
    return_code: int = 0
    output: str = ""

    def __post_init__(self):
        self.event_type = "tool.execution.completed"
        super().__post_init__()


@dataclasses.dataclass
class ToolExecutionFailedEvent(Event):
    """Emitted when tool execution fails."""
    tool_key: str = ""
    execution_id: str = ""
    error: str = ""
    traceback: str = ""

    def __post_init__(self):
        self.event_type = "tool.execution.failed"
        super().__post_init__()


@dataclasses.dataclass
class AgentActionEvent(Event):
    """Emitted when an agent takes action."""
    agent_name: str = ""
    action: str = ""
    details: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self.event_type = "agent.action"
        super().__post_init__()


@dataclasses.dataclass
class RuntimeErrorEvent(Event):
    """Emitted when runtime error occurs."""
    error_type: str = ""
    error_message: str = ""
    recoverable: bool = False

    def __post_init__(self):
        self.event_type = "runtime.error"
        super().__post_init__()


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""
        pass


class EventBus:
    """
    Central event dispatch system for inter-component communication.
    
    Features:
    - Typed event dispatch with validation
    - Async event handling
    - Subscription management
    - Event history and replay
    - Priority-based event queuing
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize event bus.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        self._subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
        priority: int = 0
    ) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to (e.g., "tool.registered")
            handler: Async callable that handles the event
            priority: Handler priority (lower = earlier execution)
            
        Returns:
            Subscription ID for later unsubscription
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"Handler must be async callable, got {type(handler)}")

        subscription_id = str(uuid.uuid4())
        
        # Wrap handler with metadata
        wrapped_handler = (handler, priority, subscription_id)
        self._subscribers[event_type].add(wrapped_handler)
        
        logger.debug(f"Subscribed to '{event_type}' with handler {handler.__name__}")
        return subscription_id

    async def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            event_type: Type of event
            subscription_id: Subscription ID from subscribe()
            
        Returns:
            True if unsubscribed, False if subscription not found
        """
        async with self._lock:
            handlers = self._subscribers.get(event_type, set())
            for handler, _, sub_id in list(handlers):
                if sub_id == subscription_id:
                    handlers.discard((handler, _, sub_id))
                    logger.debug(f"Unsubscribed from '{event_type}'")
                    return True
        return False

    async def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event: Event to emit
        """
        if not isinstance(event, Event):
            raise TypeError(f"Event must be Event instance, got {type(event)}")

        # Add to history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # Queue for dispatch
        await self._event_queue.put(event)
        logger.debug(f"Emitted event: {event.event_type} (ID: {event.event_id})")

    async def _dispatch_events(self) -> None:
        """Internal coroutine for event dispatch loop."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1
                )
                
                # Get handlers for this event type
                handlers = self._subscribers.get(event.event_type, set())
                
                # Sort by priority
                sorted_handlers = sorted(handlers, key=lambda x: x[1])
                
                # Dispatch to all handlers
                tasks = []
                for handler, _, _ in sorted_handlers:
                    tasks.append(self._safe_call_handler(handler, event))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event dispatch: {e}", exc_info=True)

    async def _safe_call_handler(self, handler: Callable, event: Event) -> None:
        """Safely call a handler with exception handling."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Handler {handler.__name__} failed for event {event.event_type}: {e}",
                exc_info=True
            )

    async def start(self) -> None:
        """Start the event bus dispatch loop."""
        if self._running:
            logger.warning("Event bus already running")
            return

        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_events())
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus dispatch loop."""
        if not self._running:
            return

        self._running = False
        if self._dispatch_task:
            await self._dispatch_task
        logger.info("Event bus stopped")

    async def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (None = all)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        async with self._lock:
            if event_type:
                events = [e for e in self._event_history if e.event_type == event_type]
            else:
                events = self._event_history[:]
            
            return events[-limit:]

    async def clear_history(self) -> None:
        """Clear event history."""
        async with self._lock:
            self._event_history.clear()

    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get number of subscribers for event type."""
        if event_type:
            return len(self._subscribers.get(event_type, set()))
        return sum(len(handlers) for handlers in self._subscribers.values())

    def get_event_types(self) -> List[str]:
        """Get all registered event types."""
        return list(self._subscribers.keys())


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def initialize_event_bus() -> EventBus:
    """Initialize and start the global event bus."""
    bus = get_event_bus()
    await bus.start()
    return bus


async def shutdown_event_bus() -> None:
    """Shutdown the global event bus."""
    global _event_bus
    if _event_bus:
        await _event_bus.stop()
        _event_bus = None
