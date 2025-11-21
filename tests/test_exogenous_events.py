"""
Tests for exogenous events functionality

Tests cover:
- Event schema validation
- Event manager evaluation logic
- Event loader
- Integration with orchestrator
"""
import pytest
from pathlib import Path
from typing import Set

from scenario_lab.schemas.exogenous_events import (
    TrendEvent,
    RandomEvent,
    ConditionalEvent,
    ScheduledEvent,
    ExogenousEventsConfig,
)
from scenario_lab.services.exogenous_events_manager import (
    ExogenousEventManager,
    TriggeredEvent,
)
from scenario_lab.loaders.exogenous_events_loader import load_exogenous_events


class TestEventSchemas:
    """Test Pydantic schemas for event validation"""

    def test_trend_event_valid(self):
        """Test valid trend event creation"""
        event = TrendEvent(
            name="Test Trend",
            description="A test trend event",
            turn_range=[1, 10],
            frequency=3,
        )
        assert event.type == "trend"
        assert event.frequency == 3
        assert event.turn_range == [1, 10]

    def test_trend_event_requires_turn_range(self):
        """Test that trend events require turn_range"""
        with pytest.raises(ValueError, match="turn_range is required"):
            TrendEvent(
                name="Test Trend",
                description="A test trend event",
                frequency=3,
            )

    def test_random_event_valid(self):
        """Test valid random event creation"""
        event = RandomEvent(
            name="Test Random",
            description="A test random event",
            probability=0.1,
            turn_range=[5, 20],
        )
        assert event.type == "random"
        assert event.probability == 0.1

    def test_random_event_probability_validation(self):
        """Test that probability must be 0.0-1.0"""
        with pytest.raises(ValueError):
            RandomEvent(
                name="Test Random",
                description="A test random event",
                probability=1.5,  # Invalid
            )

    def test_conditional_event_valid(self):
        """Test valid conditional event creation"""
        event = ConditionalEvent(
            name="Test Conditional",
            description="A test conditional event",
            conditions={"metric1": ">= 7", "metric2": "< 5"},
        )
        assert event.type == "conditional"
        assert len(event.conditions) == 2

    def test_conditional_event_requires_conditions(self):
        """Test that conditional events require at least one condition"""
        with pytest.raises(ValueError, match="At least one condition is required"):
            ConditionalEvent(
                name="Test Conditional",
                description="A test conditional event",
                conditions={},
            )

    def test_conditional_event_validates_operators(self):
        """Test that invalid operators are rejected"""
        with pytest.raises(ValueError, match="must use one of"):
            ConditionalEvent(
                name="Test Conditional",
                description="A test conditional event",
                conditions={"metric1": "invalid 7"},
            )

    def test_scheduled_event_valid(self):
        """Test valid scheduled event creation"""
        event = ScheduledEvent(
            name="Test Scheduled",
            description="A test scheduled event",
            turn=15,
        )
        assert event.type == "scheduled"
        assert event.turn == 15
        assert event.once is True  # Always true for scheduled events

    def test_exogenous_events_config_parsing(self):
        """Test parsing mixed event types"""
        config_data = {
            "exogenous_events": [
                {
                    "type": "trend",
                    "name": "Trend 1",
                    "description": "Test trend",
                    "turn_range": [1, 10],
                    "frequency": 2,
                },
                {
                    "type": "random",
                    "name": "Random 1",
                    "description": "Test random",
                    "probability": 0.1,
                },
                {
                    "type": "conditional",
                    "name": "Conditional 1",
                    "description": "Test conditional",
                    "conditions": {"metric1": ">= 5"},
                },
                {
                    "type": "scheduled",
                    "name": "Scheduled 1",
                    "description": "Test scheduled",
                    "turn": 10,
                },
            ]
        }

        config = ExogenousEventsConfig(**config_data)
        assert len(config.exogenous_events) == 4
        assert isinstance(config.exogenous_events[0], TrendEvent)
        assert isinstance(config.exogenous_events[1], RandomEvent)
        assert isinstance(config.exogenous_events[2], ConditionalEvent)
        assert isinstance(config.exogenous_events[3], ScheduledEvent)


class TestExogenousEventManager:
    """Test event manager evaluation logic"""

    def test_trend_event_evaluation(self):
        """Test trend event triggers at correct intervals"""
        events = [
            TrendEvent(
                name="Test Trend",
                description="Occurs every 3 turns",
                turn_range=[1, 10],
                frequency=3,
            )
        ]
        manager = ExogenousEventManager(events)

        # Should trigger on turns 1, 4, 7, 10
        assert len(manager.get_events_for_turn(1, {})) == 1
        assert len(manager.get_events_for_turn(2, {})) == 0
        assert len(manager.get_events_for_turn(3, {})) == 0
        assert len(manager.get_events_for_turn(4, {})) == 1
        assert len(manager.get_events_for_turn(5, {})) == 0
        assert len(manager.get_events_for_turn(7, {})) == 1
        assert len(manager.get_events_for_turn(10, {})) == 1
        assert len(manager.get_events_for_turn(11, {})) == 0  # Outside range

    def test_random_event_with_seed(self):
        """Test random event with deterministic seed"""
        events = [
            RandomEvent(
                name="Test Random",
                description="50% probability",
                probability=0.5,
                turn_range=[1, 100],
                once=False,  # Can repeat
            )
        ]

        # With seed, results should be deterministic
        manager1 = ExogenousEventManager(events, random_seed=42)
        manager2 = ExogenousEventManager(events, random_seed=42)

        results1 = [len(manager1.get_events_for_turn(i, {})) for i in range(1, 11)]
        results2 = [len(manager2.get_events_for_turn(i, {})) for i in range(1, 11)]

        assert results1 == results2

    def test_random_event_once_only_triggers_once(self):
        """Test that one-time random events only trigger once"""
        events = [
            RandomEvent(
                name="Test Random",
                description="100% probability",
                probability=1.0,
                turn_range=[1, 100],
                once=True,
            )
        ]

        manager = ExogenousEventManager(events)

        # First turn should trigger
        triggered_turn_1 = manager.get_events_for_turn(1, {})
        assert len(triggered_turn_1) == 1

        # Subsequent turns should not trigger
        assert len(manager.get_events_for_turn(2, {})) == 0
        assert len(manager.get_events_for_turn(3, {})) == 0

    def test_conditional_event_evaluation(self):
        """Test conditional event triggers when conditions met"""
        events = [
            ConditionalEvent(
                name="High Risk Alert",
                description="Triggers when risk >= 7",
                conditions={"risk_level": ">= 7"},
                turn_range=[1, 100],
            )
        ]

        manager = ExogenousEventManager(events)

        # Should not trigger when condition not met
        assert len(manager.get_events_for_turn(1, {"risk_level": 5.0})) == 0
        assert len(manager.get_events_for_turn(2, {"risk_level": 6.9})) == 0

        # Should trigger when condition met
        triggered = manager.get_events_for_turn(3, {"risk_level": 7.0})
        assert len(triggered) == 1
        assert triggered[0].name == "High Risk Alert"

        # Should not trigger again (once=True by default)
        assert len(manager.get_events_for_turn(4, {"risk_level": 8.0})) == 0

    def test_conditional_event_multiple_conditions(self):
        """Test conditional event with multiple conditions (all must be met)"""
        events = [
            ConditionalEvent(
                name="Crisis",
                description="High capability + low alignment",
                conditions={
                    "capability": ">= 8",
                    "alignment": "< 4",
                },
                turn_range=[1, 100],
            )
        ]

        manager = ExogenousEventManager(events)

        # Only one condition met
        assert len(manager.get_events_for_turn(1, {"capability": 9.0, "alignment": 5.0})) == 0
        assert len(manager.get_events_for_turn(2, {"capability": 7.0, "alignment": 3.0})) == 0

        # Both conditions met
        triggered = manager.get_events_for_turn(3, {"capability": 9.0, "alignment": 3.0})
        assert len(triggered) == 1

    def test_conditional_event_all_operators(self):
        """Test all supported comparison operators"""
        events = [
            ConditionalEvent(
                name="Greater Than",
                description="Test >",
                conditions={"metric": "> 5"},
            ),
            ConditionalEvent(
                name="Greater Equal",
                description="Test >=",
                conditions={"metric": ">= 5"},
            ),
            ConditionalEvent(
                name="Less Than",
                description="Test <",
                conditions={"metric": "< 5"},
            ),
            ConditionalEvent(
                name="Less Equal",
                description="Test <=",
                conditions={"metric": "<= 5"},
            ),
            ConditionalEvent(
                name="Equal",
                description="Test ==",
                conditions={"metric": "== 5"},
            ),
            ConditionalEvent(
                name="Not Equal",
                description="Test !=",
                conditions={"metric": "!= 5"},
            ),
        ]

        manager = ExogenousEventManager(events)
        metrics = {"metric": 5.0}
        triggered = manager.get_events_for_turn(1, metrics)
        triggered_names = {t.name for t in triggered}

        # >= 5, <= 5, == 5 should trigger
        assert "Greater Equal" in triggered_names
        assert "Less Equal" in triggered_names
        assert "Equal" in triggered_names

        # > 5, < 5, != 5 should not trigger
        assert "Greater Than" not in triggered_names
        assert "Less Than" not in triggered_names
        assert "Not Equal" not in triggered_names

    def test_scheduled_event_evaluation(self):
        """Test scheduled event triggers at exact turn"""
        events = [
            ScheduledEvent(
                name="Conference",
                description="Major event at turn 15",
                turn=15,
            )
        ]

        manager = ExogenousEventManager(events)

        # Should not trigger before turn 15
        assert len(manager.get_events_for_turn(14, {})) == 0

        # Should trigger at turn 15
        triggered = manager.get_events_for_turn(15, {})
        assert len(triggered) == 1
        assert triggered[0].name == "Conference"

        # Should not trigger again
        assert len(manager.get_events_for_turn(16, {})) == 0

    def test_turn_range_filtering(self):
        """Test that events respect turn_range"""
        events = [
            RandomEvent(
                name="Limited Event",
                description="Only active turns 10-20",
                probability=1.0,
                turn_range=[10, 20],
                once=False,
            )
        ]

        manager = ExogenousEventManager(events)

        # Before range
        assert len(manager.get_events_for_turn(5, {})) == 0
        assert len(manager.get_events_for_turn(9, {})) == 0

        # Within range
        assert len(manager.get_events_for_turn(10, {})) == 1
        assert len(manager.get_events_for_turn(15, {})) == 1
        assert len(manager.get_events_for_turn(20, {})) == 1

        # After range
        assert len(manager.get_events_for_turn(21, {})) == 0

    def test_triggered_event_ids_tracking(self):
        """Test that triggered event IDs are tracked correctly"""
        events = [
            RandomEvent(
                name="Event 1",
                description="Test",
                probability=1.0,
                once=True,
            ),
            RandomEvent(
                name="Event 2",
                description="Test",
                probability=1.0,
                once=True,
            ),
        ]

        manager = ExogenousEventManager(events)

        # Trigger events
        manager.get_events_for_turn(1, {})

        # Check tracked IDs
        triggered_ids = manager.get_triggered_event_ids()
        assert "random:Event 1" in triggered_ids
        assert "random:Event 2" in triggered_ids

    def test_resume_with_triggered_events(self):
        """Test resuming with already-triggered events"""
        events = [
            RandomEvent(
                name="Event 1",
                description="Test",
                probability=1.0,
                once=True,
            )
        ]

        # First run - event triggers
        manager1 = ExogenousEventManager(events)
        triggered = manager1.get_events_for_turn(1, {})
        assert len(triggered) == 1

        # Resume - event should not trigger again
        triggered_ids = manager1.get_triggered_event_ids()
        manager2 = ExogenousEventManager(events, triggered_event_ids=triggered_ids)
        triggered_resume = manager2.get_events_for_turn(1, {})
        assert len(triggered_resume) == 0

    def test_multiple_events_same_turn(self):
        """Test that multiple events can trigger on same turn"""
        events = [
            TrendEvent(
                name="Trend",
                description="Test trend",
                turn_range=[1, 10],
                frequency=5,
            ),
            RandomEvent(
                name="Random",
                description="Test random",
                probability=1.0,
            ),
            ScheduledEvent(
                name="Scheduled",
                description="Test scheduled",
                turn=1,
            ),
        ]

        manager = ExogenousEventManager(events, random_seed=42)
        triggered = manager.get_events_for_turn(1, {})

        # All three should trigger on turn 1
        assert len(triggered) == 3
        names = {t.name for t in triggered}
        assert names == {"Trend", "Random", "Scheduled"}


class TestExogenousEventsLoader:
    """Test event loader functionality"""

    def test_load_nonexistent_scenario_raises_error(self):
        """Test that loading from nonexistent path raises error"""
        with pytest.raises(FileNotFoundError):
            load_exogenous_events(Path("/nonexistent/path"))

    def test_load_scenario_without_events_returns_none(self, tmp_path):
        """Test that scenario without events file returns None"""
        # Create scenario directory without exogenous-events.yaml
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        (scenario_dir / "definition").mkdir()

        result = load_exogenous_events(scenario_dir)
        assert result is None

    def test_load_valid_events_file(self, tmp_path):
        """Test loading valid events file"""
        scenario_dir = tmp_path / "test-scenario"
        definition_dir = scenario_dir / "definition"
        definition_dir.mkdir(parents=True)

        # Create events file
        events_file = definition_dir / "exogenous-events.yaml"
        events_file.write_text("""
exogenous_events:
  - type: trend
    name: "Test Trend"
    description: "A test trend"
    turn_range: [1, 10]
    frequency: 3
  - type: random
    name: "Test Random"
    description: "A test random event"
    probability: 0.1
""")

        manager = load_exogenous_events(scenario_dir)
        assert manager is not None
        assert len(manager.events) == 2

    def test_load_with_triggered_events(self, tmp_path):
        """Test loading with pre-existing triggered events"""
        scenario_dir = tmp_path / "test-scenario"
        definition_dir = scenario_dir / "definition"
        definition_dir.mkdir(parents=True)

        events_file = definition_dir / "exogenous-events.yaml"
        events_file.write_text("""
exogenous_events:
  - type: random
    name: "Event 1"
    description: "Test"
    probability: 1.0
    once: true
""")

        # Load with triggered event
        triggered_ids = {"random:Event 1"}
        manager = load_exogenous_events(scenario_dir, triggered_event_ids=triggered_ids)

        # Event should not trigger (already triggered)
        assert len(manager.get_events_for_turn(1, {})) == 0

    def test_load_invalid_yaml_raises_error(self, tmp_path):
        """Test that invalid YAML raises error"""
        scenario_dir = tmp_path / "test-scenario"
        definition_dir = scenario_dir / "definition"
        definition_dir.mkdir(parents=True)

        events_file = definition_dir / "exogenous-events.yaml"
        events_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_exogenous_events(scenario_dir)

    def test_load_invalid_schema_raises_error(self, tmp_path):
        """Test that invalid event schema raises error"""
        scenario_dir = tmp_path / "test-scenario"
        definition_dir = scenario_dir / "definition"
        definition_dir.mkdir(parents=True)

        events_file = definition_dir / "exogenous-events.yaml"
        events_file.write_text("""
exogenous_events:
  - type: trend
    name: "Missing Frequency"
    description: "This should fail"
    turn_range: [1, 10]
    # Missing required 'frequency' field
""")

        with pytest.raises(ValueError, match="Invalid exogenous events configuration"):
            load_exogenous_events(scenario_dir)
