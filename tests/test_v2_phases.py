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
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

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

            # Check content
            with open(world_state_file) as f:
                content = f.read()

            assert '# Turn 1' in content
            assert 'This is the world state at turn 1' in content

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

            # Check actor decision files exist
            actor1_file = output_dir / 'actor1-001.md'
            actor2_file = output_dir / 'actor2-001.md'

            assert actor1_file.exists()
            assert actor2_file.exists()

            # Check actor1 content
            with open(actor1_file) as f:
                content = f.read()

            assert 'Test Actor 1' in content
            assert 'Test reasoning for actor 1' in content
            assert 'Test action for actor 1' in content

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_persistence_appends_to_costs_file(self, sample_state):
        """Test that persistence phase appends costs to costs.jsonl"""
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'
            output_dir.mkdir()

            phase = PersistencePhase(output_dir=str(output_dir))

            # Execute twice to test appending
            state1 = sample_state
            state2 = sample_state.with_turn(2)

            await phase.execute(state1)
            await phase.execute(state2)

            # Check costs file
            costs_file = output_dir / 'costs.jsonl'
            assert costs_file.exists()

            # Read and verify costs
            import json
            with open(costs_file) as f:
                lines = f.readlines()

            # Should have entries from both turns
            assert len(lines) >= 2

            # Verify JSON format
            for line in lines:
                cost_data = json.loads(line)
                assert 'actor' in cost_data
                assert 'cost' in cost_data
                assert 'model' in cost_data

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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
