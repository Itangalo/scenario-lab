"""
Unit tests for Event system

Tests the event bus and event handling functionality.
"""
import pytest
import asyncio
from scenario_lab.core.events import EventBus, Event, EventType


class TestEventBus:
    """Test EventBus functionality"""

    def test_event_creation(self):
        """Test creating an event"""
        event = Event(type="test", data={"key": "value"})
        assert event.type == "test"
        assert event.data["key"] == "value"
        assert event.timestamp > 0

    def test_event_immutability(self):
        """Test that events are immutable"""
        event = Event(type="test", data={"key": "value"})

        with pytest.raises(AttributeError):
            event.type = "modified"  # Should raise error

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test emitting events"""
        bus = EventBus()
        received_events = []

        async def handler(event: Event):
            received_events.append(event)

        bus.on("test_event", handler)
        await bus.emit("test_event", data={"test": "data"})

        assert len(received_events) == 1
        assert received_events[0].type == "test_event"
        assert received_events[0].data["test"] == "data"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        """Test multiple handlers for the same event"""
        bus = EventBus()
        calls = []

        async def handler1(event: Event):
            calls.append("handler1")

        async def handler2(event: Event):
            calls.append("handler2")

        bus.on("test", handler1)
        bus.on("test", handler2)
        await bus.emit("test")

        assert len(calls) == 2
        assert "handler1" in calls
        assert "handler2" in calls

    @pytest.mark.asyncio
    async def test_wildcard_handler(self):
        """Test wildcard handler receives all events"""
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event.type)

        bus.on("*", handler)
        await bus.emit("event1")
        await bus.emit("event2")
        await bus.emit("event3")

        assert len(received) == 3
        assert "event1" in received
        assert "event2" in received
        assert "event3" in received

    @pytest.mark.asyncio
    async def test_event_history(self):
        """Test event history tracking"""
        bus = EventBus(keep_history=True)

        await bus.emit("event1", data={"n": 1})
        await bus.emit("event2", data={"n": 2})
        await bus.emit("event3", data={"n": 3})

        history = bus.get_history()
        assert len(history) == 3
        assert history[0].type == "event1"
        assert history[1].type == "event2"
        assert history[2].type == "event3"

    @pytest.mark.asyncio
    async def test_event_type_filter(self):
        """Test filtering history by event type"""
        bus = EventBus(keep_history=True)

        await bus.emit("type_a", data={"n": 1})
        await bus.emit("type_b", data={"n": 2})
        await bus.emit("type_a", data={"n": 3})

        type_a_events = bus.get_history("type_a")
        assert len(type_a_events) == 2
        assert all(e.type == "type_a" for e in type_a_events)

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """Test that one handler error doesn't break others"""
        bus = EventBus()
        successful_calls = []

        async def failing_handler(event: Event):
            raise ValueError("Intentional error")

        async def successful_handler(event: Event):
            successful_calls.append(event)

        bus.on("test", failing_handler)
        bus.on("test", successful_handler)
        await bus.emit("test")

        # Successful handler should have run despite failing handler
        assert len(successful_calls) == 1

        # Error should be tracked
        errors = bus.get_errors()
        assert len(errors) == 1
        assert isinstance(errors[0][1], ValueError)

    def test_handler_removal(self):
        """Test removing event handlers"""
        bus = EventBus()

        async def handler(event: Event):
            pass

        bus.on("test", handler)
        assert "test" in bus.handlers
        assert handler in bus.handlers["test"]

        bus.off("test", handler)
        assert handler not in bus.handlers.get("test", [])

    def test_clear_handlers(self):
        """Test clearing all handlers"""
        bus = EventBus()

        async def handler1(event: Event):
            pass

        async def handler2(event: Event):
            pass

        bus.on("event1", handler1)
        bus.on("event2", handler2)

        assert len(bus.handlers) == 2

        bus.clear_handlers()
        assert len(bus.handlers) == 0

    def test_max_history(self):
        """Test history size limit"""
        bus = EventBus(keep_history=True, max_history=3)

        async def emit_events():
            for i in range(5):
                await bus.emit(f"event{i}")

        asyncio.run(emit_events())

        history = bus.get_history()
        assert len(history) == 3  # Should keep only last 3
        assert history[0].type == "event2"
        assert history[2].type == "event4"


class TestEventTypes:
    """Test predefined event types"""

    def test_event_types_exist(self):
        """Test that all expected event types are defined"""
        expected_types = [
            EventType.SCENARIO_STARTED,
            EventType.SCENARIO_COMPLETED,
            EventType.TURN_STARTED,
            EventType.TURN_COMPLETED,
            EventType.PHASE_STARTED,
            EventType.PHASE_COMPLETED,
            EventType.COST_INCURRED,
            EventType.CREDIT_LIMIT_WARNING,
        ]

        for event_type in expected_types:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0
