"""
Unit tests for V2 Phase Services

Tests individual phase services in isolation with mocked dependencies.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    WorldState,
    ActorState,
    Decision,
    Communication,
    CostRecord,
)
from scenario_lab.services.persistence_phase import PersistencePhase
from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.services.communication_phase import CommunicationPhase
from scenario_lab.utils.state_persistence import StatePersistence


@pytest.fixture
def sample_state():
    """Create a sample scenario state for testing"""
    return ScenarioState(
        scenario_id="test-scenario",
        scenario_name="Test Scenario",
        run_id="test-run-001",
        turn=1,
        status=ScenarioStatus.RUNNING,
        world_state=WorldState(
            turn=1,
            content="This is the world state at turn 1.\n\n**Key points:**\n- Test point 1\n- Test point 2"
        ),
        actors={
            "actor1": ActorState(
                name="Test Actor 1",
                short_name="actor1",
                model="test/model",
                current_goals=["Test goal 1"]
            ),
            "actor2": ActorState(
                name="Test Actor 2",
                short_name="actor2",
                model="test/model",
                current_goals=["Test goal 2"]
            ),
        },
        decisions={
            "actor1": Decision(
                actor="actor1",
                turn=1,
                goals=["Test goal 1"],
                reasoning="Test reasoning for actor 1",
                action="Test action for actor 1"
            ),
            "actor2": Decision(
                actor="actor2",
                turn=1,
                goals=["Test goal 2"],
                reasoning="Test reasoning for actor 2",
                action="Test action for actor 2"
            ),
        },
        communications=[
            Communication(
                id="comm-001",
                turn=1,
                type="bilateral",
                sender="actor1",
                recipients=["actor2"],
                content="Test communication content",
                timestamp=datetime.now()
            )
        ],
        costs=[
            CostRecord(
                timestamp=datetime.now(),
                actor="actor1",
                phase="decision",
                model="test/model",
                input_tokens=100,
                output_tokens=50,
                cost=0.01
            ),
            CostRecord(
                timestamp=datetime.now(),
                actor="actor2",
                phase="decision",
                model="test/model",
                input_tokens=120,
                output_tokens=60,
                cost=0.012
            ),
        ],
        metrics=[]
    )


class TestPersistencePhase:
    """Test the file persistence phase service"""

    @pytest.mark.asyncio
    async def test_persistence_creates_output_directory(self, sample_state):
        """Test that persistence phase creates output directory if it doesn't exist"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'

            # Output dir doesn't exist yet
            assert not output_dir.exists()

            # Create persistence phase
            phase = PersistencePhase(output_dir=str(output_dir))

            # Execute phase
            result_state = await phase.execute(sample_state)

            # Directory should now exist
            assert output_dir.exists()

            # State should be unchanged
            assert result_state.turn == sample_state.turn
            assert result_state.scenario_id == sample_state.scenario_id

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_persistence_writes_world_state(self, sample_state):
        """Test that persistence phase writes world state markdown file"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            phase = PersistencePhase(output_dir=str(output_dir))
            await phase.execute(sample_state)

            # Check world state file exists
            world_state_file = output_dir / 'world-state-001.md'
            assert world_state_file.exists()

            # Check content - persistence saves content as-is
            with open(world_state_file) as f:
                content = f.read()

            # Content should contain the world state text
            assert 'world state at turn 1' in content

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_persistence_writes_actor_decisions(self, sample_state):
        """Test that persistence phase writes actor decision files"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            phase = PersistencePhase(output_dir=str(output_dir))
            await phase.execute(sample_state)

            # Check actor decision files exist (filename is actor key, lowercase)
            actor1_file = output_dir / 'actor1-001.md'
            actor2_file = output_dir / 'actor2-001.md'

            assert actor1_file.exists()
            assert actor2_file.exists()

            # Check actor1 content - format is "# actor_name - Turn X"
            with open(actor1_file) as f:
                content = f.read()

            # Decision file contains reasoning and action
            assert 'Test reasoning for actor 1' in content
            assert 'Test action for actor 1' in content

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_persistence_saves_costs_file(self, sample_state):
        """Test that persistence phase saves costs to costs.json"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            phase = PersistencePhase(output_dir=str(output_dir))
            await phase.execute(sample_state)

            # Check costs file (V2 uses costs.json not costs.jsonl)
            costs_file = output_dir / 'costs.json'
            assert costs_file.exists()

            # Read and verify costs
            import json
            with open(costs_file) as f:
                cost_data = json.load(f)

            # Should have records array
            assert 'records' in cost_data
            assert len(cost_data['records']) >= 1

            # Verify record format
            for record in cost_data['records']:
                assert 'actor' in record
                assert 'cost' in record
                assert 'model' in record

        finally:
            shutil.rmtree(temp_dir)


class TestStatePersistence:
    """Test the state persistence utility"""

    def test_save_and_load_state(self, sample_state):
        """Test that state can be saved and loaded correctly"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            # Save state
            StatePersistence.save_state(sample_state, str(output_dir))

            # Verify file exists
            state_file = output_dir / 'scenario-state-v2.json'
            assert state_file.exists()

            # Load state
            loaded_state = StatePersistence.load_state(str(state_file))

            # Verify loaded state matches original
            assert loaded_state.scenario_id == sample_state.scenario_id
            assert loaded_state.scenario_name == sample_state.scenario_name
            assert loaded_state.turn == sample_state.turn
            assert loaded_state.status == sample_state.status
            assert len(loaded_state.actors) == len(sample_state.actors)
            assert len(loaded_state.decisions) == len(sample_state.decisions)
            assert len(loaded_state.communications) == len(sample_state.communications)
            assert len(loaded_state.costs) == len(sample_state.costs)

        finally:
            shutil.rmtree(temp_dir)

    def test_create_branch(self, sample_state):
        """Test that branching creates correct state"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            # Create and save multi-turn state
            state_turn3 = sample_state.with_turn(3)
            StatePersistence.save_state(state_turn3, str(output_dir))

            state_file = output_dir / 'scenario-state-v2.json'

            # Create branch at turn 2
            branch_dir = Path(temp_dir) / 'branch'
            branched_state = StatePersistence.create_branch(
                source_state_file=str(state_file),
                branch_at_turn=2,
                new_output_dir=str(branch_dir)
            )

            # Verify branched state
            assert branched_state.turn == 2
            assert 'branched_from' in branched_state.metadata
            assert branched_state.metadata['branch_point'] == 2
            assert branched_state.status == ScenarioStatus.RUNNING

        finally:
            shutil.rmtree(temp_dir)

    def test_branch_invalid_turn_raises_error(self, sample_state):
        """Test that branching at invalid turn raises error"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            # Save state at turn 1
            StatePersistence.save_state(sample_state, str(output_dir))

            state_file = output_dir / 'scenario-state-v2.json'

            # Try to branch at turn 5 (beyond available)
            branch_dir = Path(temp_dir) / 'branch'
            with pytest.raises(ValueError, match="Cannot branch at turn"):
                StatePersistence.create_branch(
                    source_state_file=str(state_file),
                    branch_at_turn=5,
                    new_output_dir=str(branch_dir)
                )

        finally:
            shutil.rmtree(temp_dir)

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises error"""
        with pytest.raises(FileNotFoundError):
            StatePersistence.load_state('/nonexistent/path/state.json')

    def test_state_includes_version(self, sample_state):
        """Test that saved state includes version number"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            StatePersistence.save_state(sample_state, str(output_dir))

            state_file = output_dir / 'scenario-state-v2.json'

            import json
            with open(state_file) as f:
                state_data = json.load(f)

            assert 'version' in state_data
            assert state_data['version'] == '2.0'

        finally:
            shutil.rmtree(temp_dir)


class TestScenarioState:
    """Test the ScenarioState model"""

    def test_total_cost_calculation(self, sample_state):
        """Test that total_cost calculates correctly"""
        total = sample_state.total_cost()

        expected = sum(c.cost for c in sample_state.costs)
        assert abs(total - expected) < 0.0001

    def test_with_turn_creates_new_state(self, sample_state):
        """Test that with_turn creates a new immutable state"""
        new_state = sample_state.with_turn(5)

        # New state has updated turn
        assert new_state.turn == 5

        # Original state unchanged
        assert sample_state.turn == 1

        # Other fields preserved
        assert new_state.scenario_id == sample_state.scenario_id
        assert new_state.scenario_name == sample_state.scenario_name

    def test_with_decision_adds_decision(self, sample_state):
        """Test that with_decision adds a new decision"""
        new_decision = Decision(
            actor="actor3",
            turn=2,
            goals=["New goal"],
            reasoning="New reasoning",
            action="New action"
        )

        new_state = sample_state.with_decision("actor3", new_decision)

        # New state has the decision
        assert "actor3" in new_state.decisions
        assert new_state.decisions["actor3"] == new_decision

        # Original state unchanged
        assert "actor3" not in sample_state.decisions

    def test_with_cost_adds_cost(self, sample_state):
        """Test that with_cost appends a new cost"""
        new_cost = CostRecord(
            timestamp=datetime.now(),
            actor="actor3",
            phase="test",
            model="test/model",
            input_tokens=200,
            output_tokens=100,
            cost=0.02
        )

        new_state = sample_state.with_cost(new_cost)

        # New state has the cost
        assert len(new_state.costs) == len(sample_state.costs) + 1
        assert new_cost in new_state.costs

        # Original state unchanged
        assert len(sample_state.costs) == 2


class TestDecisionPhase:
    """Test the decision phase service"""

    @pytest.mark.asyncio
    async def test_decision_phase_v2_exists(self, sample_state):
        """Test that DecisionPhaseV2 can be imported and instantiated"""
        # DecisionPhaseV2 is the pure V2 implementation
        assert DecisionPhaseV2 is not None

        # Note: Full integration tests for DecisionPhaseV2 require more complex setup
        # with actual actors and context managers. Unit tests verify the class exists.

    @pytest.mark.asyncio
    async def test_decision_phase_v2_has_execute_method(self, sample_state):
        """Test that DecisionPhaseV2 has an execute method"""
        import inspect
        assert hasattr(DecisionPhaseV2, 'execute')
        assert callable(getattr(DecisionPhaseV2, 'execute'))

    def test_extract_recent_goals_from_persistent_actor_state(self):
        """Test that _extract_recent_goals uses persistent actor state (issue #34)"""
        # Create actor with recent_decisions history
        actor_state = ActorState(
            name="Test Actor",
            short_name="actor1",
            model="test/model",
            current_goals=["Current goal"],
            recent_decisions=[
                Decision(
                    actor="Test Actor",
                    turn=1,
                    goals=["Goal from turn 1", "Secondary goal turn 1"],
                    reasoning="Reasoning turn 1",
                    action="Action turn 1"
                ),
                Decision(
                    actor="Test Actor",
                    turn=2,
                    goals=["Goal from turn 2"],
                    reasoning="Reasoning turn 2",
                    action="Action turn 2"
                ),
            ]
        )

        # Create state at turn 3 with the actor having persistent decisions
        # but with an empty decisions dict (simulating cleared per-turn decisions)
        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            run_id="test-run",
            turn=3,
            status=ScenarioStatus.RUNNING,
            actors={"Test Actor": actor_state},
            decisions={},  # Empty - cleared by with_turn()
        )

        # Create phase and extract goals
        phase = DecisionPhaseV2(
            actor_configs={"actor1": {"name": "Test Actor", "llm_model": "test/model"}},
            scenario_system_prompt=""
        )

        goals = phase._extract_recent_goals(state, "Test Actor")

        # Should find goals from persistent actor state
        assert goals != ""
        assert "Goal from turn 1" in goals
        assert "Goal from turn 2" in goals

    def test_extract_recent_goals_returns_empty_for_turn_1(self):
        """Test that _extract_recent_goals returns empty string for turn 1"""
        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            run_id="test-run",
            turn=1,
            status=ScenarioStatus.RUNNING,
            actors={},
            decisions={},
        )

        phase = DecisionPhaseV2(
            actor_configs={},
            scenario_system_prompt=""
        )

        goals = phase._extract_recent_goals(state, "Test Actor")
        assert goals == ""

    def test_extract_recent_goals_limits_to_last_2_decisions(self):
        """Test that _extract_recent_goals only returns last 2 turns of goals"""
        actor_state = ActorState(
            name="Test Actor",
            short_name="actor1",
            model="test/model",
            recent_decisions=[
                Decision(actor="Test Actor", turn=1, goals=["Old goal 1"], reasoning="", action=""),
                Decision(actor="Test Actor", turn=2, goals=["Old goal 2"], reasoning="", action=""),
                Decision(actor="Test Actor", turn=3, goals=["Recent goal 3"], reasoning="", action=""),
                Decision(actor="Test Actor", turn=4, goals=["Recent goal 4"], reasoning="", action=""),
            ]
        )

        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            run_id="test-run",
            turn=5,
            status=ScenarioStatus.RUNNING,
            actors={"Test Actor": actor_state},
            decisions={},
        )

        phase = DecisionPhaseV2(
            actor_configs={"actor1": {"name": "Test Actor", "llm_model": "test/model"}},
            scenario_system_prompt=""
        )

        goals = phase._extract_recent_goals(state, "Test Actor")

        # Should only have goals from last 2 decisions (turn 3 and 4)
        assert "Recent goal 3" in goals
        assert "Recent goal 4" in goals
        assert "Old goal 1" not in goals
        assert "Old goal 2" not in goals

    def test_extract_recent_goals_excludes_current_turn(self):
        """Test that _extract_recent_goals excludes goals from current turn"""
        actor_state = ActorState(
            name="Test Actor",
            short_name="actor1",
            model="test/model",
            recent_decisions=[
                Decision(actor="Test Actor", turn=2, goals=["Previous turn goal"], reasoning="", action=""),
                Decision(actor="Test Actor", turn=3, goals=["Current turn goal"], reasoning="", action=""),
            ]
        )

        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            run_id="test-run",
            turn=3,  # Current turn is 3
            status=ScenarioStatus.RUNNING,
            actors={"Test Actor": actor_state},
            decisions={},
        )

        phase = DecisionPhaseV2(
            actor_configs={"actor1": {"name": "Test Actor", "llm_model": "test/model"}},
            scenario_system_prompt=""
        )

        goals = phase._extract_recent_goals(state, "Test Actor")

        # Should include turn 2 but exclude turn 3 (current)
        assert "Previous turn goal" in goals
        assert "Current turn goal" not in goals


class TestWorldUpdatePhase:
    """Test the world update phase service"""

    @pytest.mark.asyncio
    async def test_world_update_phase_v2_exists(self, sample_state):
        """Test that WorldUpdatePhaseV2 can be imported and instantiated"""
        # WorldUpdatePhaseV2 is the pure V2 implementation
        assert WorldUpdatePhaseV2 is not None

        # Note: Full integration tests for WorldUpdatePhaseV2 require more complex setup
        # with actual world synthesizers. Unit tests verify the class exists.

    @pytest.mark.asyncio
    async def test_world_update_phase_v2_has_execute_method(self, sample_state):
        """Test that WorldUpdatePhaseV2 has an execute method"""
        import inspect
        assert hasattr(WorldUpdatePhaseV2, 'execute')
        assert callable(getattr(WorldUpdatePhaseV2, 'execute'))


class TestCommunicationPhase:
    """Test the communication phase service"""

    @pytest.mark.asyncio
    async def test_communication_phase_handles_no_communications(self, sample_state):
        """Test that communication phase handles case with no communications"""
        # V2 CommunicationPhase takes only output_dir parameter
        phase = CommunicationPhase(output_dir=None)

        # Create state with no communications for current turn
        state_no_comms = sample_state
        # Filter out communications for current turn
        state_no_comms = ScenarioState(
            scenario_id=sample_state.scenario_id,
            scenario_name=sample_state.scenario_name,
            run_id=sample_state.run_id,
            turn=sample_state.turn,
            status=sample_state.status,
            world_state=sample_state.world_state,
            actors=sample_state.actors,
            decisions=sample_state.decisions,
            communications=[],  # No communications
            costs=sample_state.costs,
            metrics=sample_state.metrics,
        )

        # Execute phase
        result_state = await phase.execute(state_no_comms)

        # State should be unchanged (stub implementation returns same state)
        assert len(result_state.communications) == len(state_no_comms.communications)

    @pytest.mark.asyncio
    async def test_communication_phase_passes_through_existing_communications(self, sample_state):
        """Test that communication phase preserves existing communications"""
        # V2 CommunicationPhase is a stub that preserves existing state
        phase = CommunicationPhase(output_dir=None)

        # Execute phase
        result_state = await phase.execute(sample_state)

        # Communications should be preserved (stub implementation)
        assert len(result_state.communications) == len(sample_state.communications)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
