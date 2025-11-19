"""
Unit tests for ScenarioOrchestrator

Tests the core execution coordination functionality.
"""
import pytest
import asyncio
from scenario_lab.core.orchestrator import ScenarioOrchestrator, PhaseService
from scenario_lab.core.events import EventBus, EventType
from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    PhaseType,
    CostRecord,
)
from datetime import datetime


class MockPhase:
    """Mock phase service for testing"""

    def __init__(self, name: str):
        self.name = name
        self.executed = False

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """Mock execution"""
        self.executed = True
        # Return state unchanged
        return state


class CostIncurringPhase:
    """Mock phase that adds costs"""

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """Add a cost record"""
        cost = CostRecord(
            timestamp=datetime.now(),
            actor="test",
            phase="decision",
            model="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            cost=0.50,
        )
        return state.with_cost(cost)


class TestScenarioOrchestrator:
    """Test ScenarioOrchestrator functionality"""

    def test_creation(self):
        """Test creating an orchestrator"""
        bus = EventBus()
        orchestrator = ScenarioOrchestrator(event_bus=bus, max_turns=10)

        assert orchestrator.event_bus is bus
        assert orchestrator.max_turns == 10
        assert len(orchestrator.phases) == 0

    def test_phase_registration(self):
        """Test registering phase services"""
        orchestrator = ScenarioOrchestrator()
        phase = MockPhase("test")

        orchestrator.register_phase(PhaseType.DECISION, phase)

        assert PhaseType.DECISION in orchestrator.phases
        assert orchestrator.phases[PhaseType.DECISION] is phase

    @pytest.mark.asyncio
    async def test_execute_turn_emits_events(self):
        """Test that executing a turn emits appropriate events"""
        bus = EventBus(keep_history=True)
        orchestrator = ScenarioOrchestrator(event_bus=bus)

        # Register a simple phase
        orchestrator.register_phase(PhaseType.DECISION, MockPhase("decision"))

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
            status=ScenarioStatus.RUNNING,
        )

        new_state = await orchestrator.execute_turn(state)

        # Check events were emitted
        history = bus.get_history()
        event_types = [e.type for e in history]

        assert EventType.TURN_STARTED in event_types
        assert EventType.PHASE_STARTED in event_types
        assert EventType.PHASE_COMPLETED in event_types
        assert EventType.TURN_COMPLETED in event_types

    @pytest.mark.asyncio
    async def test_max_turns_respected(self):
        """Test that max_turns stops execution"""
        orchestrator = ScenarioOrchestrator(max_turns=3)
        orchestrator.register_phase(PhaseType.DECISION, MockPhase("decision"))

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        final_state = await orchestrator.execute(state)

        # Should stop at turn 3
        assert final_state.turn == 3
        assert final_state.status == ScenarioStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_credit_limit_enforcement(self):
        """Test that credit limit stops execution"""
        bus = EventBus(keep_history=True)
        orchestrator = ScenarioOrchestrator(
            event_bus=bus,
            credit_limit=1.0,  # $1.00 limit
        )

        # Phase that costs $0.50 per turn
        orchestrator.register_phase(PhaseType.DECISION, CostIncurringPhase())

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        final_state = await orchestrator.execute(state)

        # Should stop at turn 2 (2 * $0.50 = $1.00)
        assert final_state.turn == 2
        assert final_state.total_cost() == 1.0
        assert final_state.status == ScenarioStatus.PAUSED

        # Should have emitted credit limit event
        events = bus.get_history(EventType.CREDIT_LIMIT_EXCEEDED)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_credit_limit_warning(self):
        """Test that credit limit warning is emitted at 80%"""
        bus = EventBus(keep_history=True)
        orchestrator = ScenarioOrchestrator(
            event_bus=bus,
            credit_limit=2.5,  # $2.50 limit
        )

        # Phase that costs $0.50 per turn
        orchestrator.register_phase(PhaseType.DECISION, CostIncurringPhase())

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        # Execute turns: $0.50, $1.00, $1.50, $2.00, $2.50
        # Warning should trigger at turn 4 when cost is $2.00 (80% of $2.50)
        final_state = await orchestrator.execute(state)

        # Should have emitted warning before hitting limit
        warnings = bus.get_history(EventType.CREDIT_LIMIT_WARNING)
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_pause_and_resume(self):
        """Test pause and resume functionality"""
        orchestrator = ScenarioOrchestrator()
        orchestrator.register_phase(PhaseType.DECISION, MockPhase("decision"))

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        # Start execution
        async def run_with_pause():
            state = ScenarioState(
                scenario_id="test",
                scenario_name="Test",
                run_id="run-001",
            )

            # Execute one turn
            state = await orchestrator.execute_turn(state)
            assert state.turn == 1

            # Pause
            orchestrator.pause()
            assert orchestrator.paused is True

            # Resume
            orchestrator.resume()
            assert orchestrator.paused is False

        await run_with_pause()

    @pytest.mark.asyncio
    async def test_phase_sequence(self):
        """Test that phases execute in correct order"""
        orchestrator = ScenarioOrchestrator()

        phase1 = MockPhase("communication")
        phase2 = MockPhase("decision")
        phase3 = MockPhase("world_update")

        orchestrator.register_phase(PhaseType.COMMUNICATION, phase1)
        orchestrator.register_phase(PhaseType.DECISION, phase2)
        orchestrator.register_phase(PhaseType.WORLD_UPDATE, phase3)

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
            status=ScenarioStatus.RUNNING,
        )

        await orchestrator.execute_turn(state)

        # All phases should have executed
        assert phase1.executed is True
        assert phase2.executed is True
        assert phase3.executed is True

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling during execution"""

        class FailingPhase:
            async def execute(self, state: ScenarioState) -> ScenarioState:
                raise ValueError("Intentional error")

        bus = EventBus(keep_history=True)
        orchestrator = ScenarioOrchestrator(event_bus=bus)
        orchestrator.register_phase(PhaseType.DECISION, FailingPhase())

        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test",
            run_id="run-001",
        )

        # Should handle error gracefully
        final_state = await orchestrator.execute(state)

        assert final_state.status == ScenarioStatus.FAILED
        assert final_state.error is not None

        # Should have emitted failure event
        failures = bus.get_history(EventType.SCENARIO_FAILED)
        assert len(failures) > 0


class TestPhaseService:
    """Test PhaseService protocol"""

    def test_mock_phase_implements_protocol(self):
        """Test that MockPhase implements PhaseService protocol"""
        phase = MockPhase("test")

        # Should have execute method
        assert hasattr(phase, "execute")
        assert callable(phase.execute)
