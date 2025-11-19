"""
Event-driven architecture for Scenario Lab V2

This module provides the event system that enables:
- Decoupling of components
- Observability into execution
- WebSocket integration
- Metrics tracking
- Logging

Based on ROADMAP_V2.md Phase 2.1 architecture design.
"""
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types in scenario execution"""

    # Scenario lifecycle
    SCENARIO_STARTED = "scenario_started"
    SCENARIO_COMPLETED = "scenario_completed"
    SCENARIO_HALTED = "scenario_halted"  # Stopped early (credit limit, manual stop)
    SCENARIO_FAILED = "scenario_failed"
    SCENARIO_PAUSED = "scenario_paused"
    SCENARIO_RESUMED = "scenario_resumed"

    # Turn lifecycle
    TURN_STARTED = "turn_started"
    TURN_COMPLETED = "turn_completed"
    TURN_FAILED = "turn_failed"

    # Phase lifecycle
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"

    # Actor events
    ACTOR_DECISION_STARTED = "actor_decision_started"
    ACTOR_DECISION_COMPLETED = "actor_decision_completed"
    ACTOR_DECISION_FAILED = "actor_decision_failed"

    # World state events
    WORLD_STATE_UPDATED = "world_state_updated"

    # Communication events
    COMMUNICATION_SENT = "communication_sent"
    COMMUNICATION_RECEIVED = "communication_received"

    # Cost events
    COST_INCURRED = "cost_incurred"
    CREDIT_LIMIT_WARNING = "credit_limit_warning"
    CREDIT_LIMIT_EXCEEDED = "credit_limit_exceeded"

    # Metrics events
    METRIC_RECORDED = "metric_recorded"

    # Validation events
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_FAILED = "validation_failed"

    # Persistence events
    STATE_SAVED = "state_saved"
    STATE_LOADED = "state_loaded"


@dataclass(frozen=True)
class Event:
    """
    Immutable event object

    Events are the primary way components communicate in V2.
    They enable observability, testing, and decoupling.
    """

    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    correlation_id: Optional[str] = None

    def __str__(self) -> str:
        return f"Event({self.type}, source={self.source}, data_keys={list(self.data.keys())})"


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus for publish-subscribe pattern

    Features:
    - Async event handlers
    - Multiple handlers per event type
    - Error isolation (one handler failure doesn't break others)
    - Handler removal support
    - Event history for debugging
    """

    def __init__(self, keep_history: bool = False, max_history: int = 1000):
        """
        Initialize event bus

        Args:
            keep_history: Whether to store event history
            max_history: Maximum number of events to keep in history
        """
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.keep_history = keep_history
        self.max_history = max_history
        self.history: List[Event] = []
        self._handler_errors: List[tuple[Event, Exception]] = []

    def on(self, event_type: str, handler: EventHandler) -> None:
        """
        Register an event handler

        Args:
            event_type: The event type to listen for
            handler: Async function that takes Event as parameter
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    def off(self, event_type: str, handler: EventHandler) -> None:
        """
        Unregister an event handler

        Args:
            event_type: The event type
            handler: The handler to remove
        """
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type}")

    async def emit(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Emit an event to all registered handlers

        Args:
            event_type: The type of event
            data: Event data dictionary
            source: Source component that emitted the event
            correlation_id: ID to correlate related events

        Returns:
            The emitted Event object
        """
        event = Event(
            type=event_type,
            data=data or {},
            timestamp=time.time(),
            source=source,
            correlation_id=correlation_id,
        )

        # Store in history if enabled
        if self.keep_history:
            self.history.append(event)
            # Trim history if needed
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history :]

        # Get handlers for this event type
        handlers = self.handlers.get(event_type, [])

        # Also get wildcard handlers (listening to all events)
        handlers.extend(self.handlers.get("*", []))

        if not handlers:
            logger.debug(f"No handlers for {event_type}")
            return event

        # Execute all handlers concurrently
        # Use gather with return_exceptions to prevent one failure from breaking others
        results = await asyncio.gather(
            *[self._safe_execute_handler(handler, event) for handler in handlers],
            return_exceptions=True,
        )

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {i} for {event_type} failed: {result}", exc_info=result
                )
                self._handler_errors.append((event, result))

        return event

    async def _safe_execute_handler(self, handler: EventHandler, event: Event) -> None:
        """
        Execute a handler with error handling

        Args:
            handler: The handler function
            event: The event to pass to handler
        """
        try:
            await handler(event)
        except Exception as e:
            # Re-raise to be caught by gather
            raise e

    def clear_handlers(self, event_type: Optional[str] = None) -> None:
        """
        Clear event handlers

        Args:
            event_type: If specified, clear only handlers for this type.
                       If None, clear all handlers.
        """
        if event_type is None:
            self.handlers.clear()
            logger.info("Cleared all event handlers")
        elif event_type in self.handlers:
            del self.handlers[event_type]
            logger.info(f"Cleared handlers for {event_type}")

    def get_history(self, event_type: Optional[str] = None) -> List[Event]:
        """
        Get event history

        Args:
            event_type: If specified, filter by this event type

        Returns:
            List of events
        """
        if not self.keep_history:
            logger.warning("Event history is disabled")
            return []

        if event_type is None:
            return self.history.copy()
        else:
            return [e for e in self.history if e.type == event_type]

    def get_errors(self) -> List[tuple[Event, Exception]]:
        """
        Get handler errors

        Returns:
            List of (event, exception) tuples
        """
        return self._handler_errors.copy()

    def clear_errors(self) -> None:
        """Clear handler error log"""
        self._handler_errors.clear()


# Global event bus instance (can be overridden for testing)
_global_bus: Optional[EventBus] = None


def get_event_bus(create_if_missing: bool = True) -> EventBus:
    """
    Get the global event bus instance

    Args:
        create_if_missing: Create a new bus if one doesn't exist

    Returns:
        EventBus instance
    """
    global _global_bus
    if _global_bus is None and create_if_missing:
        _global_bus = EventBus(keep_history=False)
    return _global_bus


def set_event_bus(bus: EventBus) -> None:
    """
    Set the global event bus instance

    Useful for testing or custom configurations.

    Args:
        bus: EventBus instance to use globally
    """
    global _global_bus
    _global_bus = bus
