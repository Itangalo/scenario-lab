"""
Unit tests for State models

Tests immutable state models and transformations.
"""
import pytest
from datetime import datetime
from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    PhaseType,
    WorldState,
    ActorState,
    Decision,
    Communication,
    CostRecord,
    MetricRecord,
)


class TestWorldState:
    """Test WorldState model"""

    def test_creation(self):
        """Test creating a world state"""
        ws = WorldState(turn=1, content="Test world")
        assert ws.turn == 1
        assert ws.content == "Test world"
        assert isinstance(ws.timestamp, datetime)

    def test_immutability(self):
        """Test that WorldState is immutable"""
        ws = WorldState(turn=1, content="Test")

        with pytest.raises(AttributeError):
            ws.turn = 2  # Should raise error

    def test_with_content(self):
        """Test creating new state with updated content"""
        ws1 = WorldState(turn=1, content="Old content")
        ws2 = ws1.with_content("New content")

        # Original unchanged
        assert ws1.content == "Old content"
        # New state has new content
        assert ws2.content == "New content"
        # Turn is preserved
        assert ws2.turn == ws1.turn


class TestActorState:
    """Test ActorState model"""

    def test_creation(self):
        """Test creating an actor state"""
        actor = ActorState(
            name="Test Actor",
            short_name="test",
            model="gpt-4o-mini",
            current_goals=["Goal 1"],
        )
        assert actor.name == "Test Actor"
        assert actor.short_name == "test"
        assert actor.model == "gpt-4o-mini"
        assert len(actor.current_goals) == 1

    def test_with_decision(self):
        """Test adding a decision to actor state"""
        actor = ActorState(name="Test", short_name="test", model="gpt-4o-mini")
        decision = Decision(
            actor="test",
            turn=1,
            goals=["New goal"],
            reasoning="Test reasoning",
            action="Test action",
        )

        new_actor = actor.with_decision(decision)

        # Original unchanged
        assert len(actor.recent_decisions) == 0
        # New state has decision
        assert len(new_actor.recent_decisions) == 1
        assert new_actor.current_goals == ["New goal"]

    def test_decision_limit(self):
        """Test that recent decisions are limited to 5"""
        actor = ActorState(name="Test", short_name="test", model="gpt-4o-mini")

        # Add 10 decisions
        for i in range(10):
            decision = Decision(
                actor="test",
                turn=i,
                goals=[f"Goal {i}"],
                reasoning="Test",
                action="Test",
            )
            actor = actor.with_decision(decision)

        # Should keep only last 5
        assert len(actor.recent_decisions) == 5
        assert actor.recent_decisions[0].turn == 5
        assert actor.recent_decisions[-1].turn == 9


class TestScenarioState:
    """Test ScenarioState model"""

    def test_creation(self):
        """Test creating a scenario state"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test Scenario",
            run_id="run-001",
        )
        assert state.scenario_id == "test"
        assert state.status == ScenarioStatus.CREATED
        assert state.turn == 0
        assert isinstance(state.world_state, WorldState)

    def test_immutability(self):
        """Test that ScenarioState is immutable"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        with pytest.raises(AttributeError):
            state.turn = 1  # Should raise error

    def test_with_turn(self):
        """Test advancing turns"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )
        new_state = state.with_turn(1)

        assert state.turn == 0  # Original unchanged
        assert new_state.turn == 1  # New state advanced
        assert len(new_state.decisions) == 0  # Decisions reset

    def test_with_status(self):
        """Test updating status"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )
        new_state = state.with_status(ScenarioStatus.RUNNING)

        assert state.status == ScenarioStatus.CREATED
        assert new_state.status == ScenarioStatus.RUNNING

    def test_with_decision(self):
        """Test adding a decision"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        # Add actor first
        actor = ActorState(name="Test", short_name="test", model="gpt-4o-mini")
        state = state.with_actor("test", actor)

        # Add decision
        decision = Decision(
            actor="test",
            turn=1,
            goals=["Goal"],
            reasoning="Reasoning",
            action="Action",
        )
        new_state = state.with_decision("test", decision)

        assert "test" not in state.decisions
        assert "test" in new_state.decisions
        assert new_state.decisions["test"] == decision

    def test_total_cost(self):
        """Test calculating total cost"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        cost1 = CostRecord(
            timestamp=datetime.now(),
            actor="actor1",
            phase="decision",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost=0.10,
        )
        cost2 = CostRecord(
            timestamp=datetime.now(),
            actor="actor2",
            phase="decision",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost=0.15,
        )

        state = state.with_cost(cost1).with_cost(cost2)

        assert state.total_cost() == 0.25

    def test_actor_cost(self):
        """Test calculating cost for specific actor"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        cost1 = CostRecord(
            timestamp=datetime.now(),
            actor="actor1",
            phase="decision",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost=0.10,
        )
        cost2 = CostRecord(
            timestamp=datetime.now(),
            actor="actor2",
            phase="decision",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost=0.15,
        )

        state = state.with_cost(cost1).with_cost(cost2)

        assert state.actor_cost("actor1") == 0.10
        assert state.actor_cost("actor2") == 0.15
        assert state.actor_cost("actor3") == 0.0  # Non-existent actor

    def test_chaining_transformations(self):
        """Test chaining multiple state transformations"""
        state = (
            ScenarioState(
                scenario_id="test",
                scenario_name="Test",
                run_id="run-001",
            )
            .with_started()
            .with_turn(1)
            .with_status(ScenarioStatus.RUNNING)
        )

        assert state.turn == 1
        assert state.status == ScenarioStatus.RUNNING
        assert state.started_at is not None

    def test_to_dict(self):
        """Test serializing to dictionary"""
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test Scenario",
            run_id="run-001",
        )

        data = state.to_dict()

        assert data["scenario_id"] == "test"
        assert data["scenario_name"] == "Test Scenario"
        assert data["run_id"] == "run-001"
        assert data["status"] == "created"
        assert data["turn"] == 0
        assert "world_state" in data
        assert "actors" in data
        assert isinstance(data, dict)


class TestCommunication:
    """Test Communication model"""

    def test_creation(self):
        """Test creating a communication"""
        comm = Communication(
            id="comm-1",
            turn=1,
            type="bilateral",
            sender="actor1",
            recipients=["actor2"],
            content="Hello",
        )
        assert comm.id == "comm-1"
        assert comm.sender == "actor1"
        assert len(comm.recipients) == 1


class TestDecision:
    """Test Decision model"""

    def test_creation(self):
        """Test creating a decision"""
        decision = Decision(
            actor="test",
            turn=1,
            goals=["Goal 1", "Goal 2"],
            reasoning="Because...",
            action="Do something",
        )
        assert decision.actor == "test"
        assert len(decision.goals) == 2
        assert decision.reasoning == "Because..."
