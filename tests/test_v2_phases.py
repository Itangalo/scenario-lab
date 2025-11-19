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
from scenario_lab.services.decision_phase import DecisionPhase
from scenario_lab.services.world_update_phase import WorldUpdatePhase
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


class TestDecisionPhase:
    """Test the decision phase service"""

    @pytest.mark.asyncio
    async def test_decision_phase_processes_all_actors(self, sample_state):
        """Test that decision phase gets decisions from all actors"""
        # Create mock actors
        mock_actor1 = MagicMock()
        mock_actor1.name = "Test Actor 1"
        mock_actor1.llm_model = "test/model"
        mock_actor1.make_decision = MagicMock(return_value={
            'goals': 'Test goals 1',
            'reasoning': 'Test reasoning 1',
            'action': 'Test action 1',
            'tokens_used': 100
        })

        mock_actor2 = MagicMock()
        mock_actor2.name = "Test Actor 2"
        mock_actor2.llm_model = "test/model"
        mock_actor2.make_decision = MagicMock(return_value={
            'goals': 'Test goals 2',
            'reasoning': 'Test reasoning 2',
            'action': 'Test action 2',
            'tokens_used': 120
        })

        actors = {
            'actor1': mock_actor1,
            'actor2': mock_actor2
        }

        # Create mock dependencies
        mock_context_manager = MagicMock()
        mock_context_manager.get_context_for_actor = MagicMock(
            return_value="Mocked context for actor"
        )

        mock_v1_world_state = MagicMock()
        mock_communication_manager = MagicMock()

        # Create decision phase
        phase = DecisionPhase(
            actors=actors,
            context_manager=mock_context_manager,
            v1_world_state=mock_v1_world_state,
            communication_manager=mock_communication_manager,
            output_dir=None  # Skip file writing for unit test
        )

        # Execute phase
        result_state = await phase.execute(sample_state)

        # Verify both actors made decisions
        assert mock_actor1.make_decision.called
        assert mock_actor2.make_decision.called

        # Verify state has decisions
        assert 'Test Actor 1' in result_state.decisions
        assert 'Test Actor 2' in result_state.decisions

        # Verify costs were tracked
        initial_cost_count = len(sample_state.costs)
        assert len(result_state.costs) == initial_cost_count + 2

    @pytest.mark.asyncio
    async def test_decision_phase_tracks_costs(self, sample_state):
        """Test that decision phase tracks LLM costs correctly"""
        mock_actor = MagicMock()
        mock_actor.name = "Test Actor"
        mock_actor.llm_model = "test/model"
        mock_actor.make_decision = MagicMock(return_value={
            'goals': 'Test goals',
            'reasoning': 'Test reasoning',
            'action': 'Test action',
            'tokens_used': 500
        })

        actors = {'actor1': mock_actor}

        mock_context_manager = MagicMock()
        mock_context_manager.get_context_for_actor = MagicMock(return_value="Context")
        mock_v1_world_state = MagicMock()
        mock_communication_manager = MagicMock()

        phase = DecisionPhase(
            actors=actors,
            context_manager=mock_context_manager,
            v1_world_state=mock_v1_world_state,
            communication_manager=mock_communication_manager
        )

        result_state = await phase.execute(sample_state)

        # Find the cost record for this phase
        new_costs = [c for c in result_state.costs if c not in sample_state.costs]
        assert len(new_costs) == 1

        cost_record = new_costs[0]
        assert cost_record.actor == "Test Actor"
        assert cost_record.phase == "decision"
        assert cost_record.model == "test/model"
        assert cost_record.input_tokens + cost_record.output_tokens == 500


class TestWorldUpdatePhase:
    """Test the world update phase service"""

    @pytest.mark.asyncio
    async def test_world_update_phase_synthesizes_new_state(self, sample_state):
        """Test that world update phase creates new world state"""
        # Create mock world state updater
        mock_updater = MagicMock()
        mock_updater.update_world_state = MagicMock(return_value={
            'updated_state': 'This is the new world state for turn 1. Things have changed.',
            'metadata': {'tokens_used': 300}
        })

        mock_v1_world_state = MagicMock()
        mock_v1_world_state.to_markdown = MagicMock(
            return_value="# Turn 1\n\nThis is the new world state for turn 1. Things have changed."
        )

        # Create phase
        phase = WorldUpdatePhase(
            world_state_updater=mock_updater,
            v1_world_state=mock_v1_world_state,
            scenario_name="Test Scenario",
            world_state_model="test/model",
            output_dir=None  # Skip file writing
        )

        # Execute phase
        result_state = await phase.execute(sample_state)

        # Verify world state was updated
        assert mock_updater.update_world_state.called
        assert result_state.world_state.content == 'This is the new world state for turn 1. Things have changed.'
        assert result_state.world_state.turn == sample_state.turn

        # Verify cost was tracked
        new_costs = [c for c in result_state.costs if c not in sample_state.costs]
        assert len(new_costs) == 1
        assert new_costs[0].phase == "world_update"
        assert new_costs[0].model == "test/model"

    @pytest.mark.asyncio
    async def test_world_update_phase_includes_actor_decisions(self, sample_state):
        """Test that world update receives actor decisions"""
        mock_updater = MagicMock()
        mock_updater.update_world_state = MagicMock(return_value={
            'updated_state': 'New world state',
            'metadata': {'tokens_used': 200}
        })

        mock_v1_world_state = MagicMock()

        phase = WorldUpdatePhase(
            world_state_updater=mock_updater,
            v1_world_state=mock_v1_world_state,
            scenario_name="Test",
            world_state_model="test/model"
        )

        await phase.execute(sample_state)

        # Verify update_world_state was called with actor decisions
        call_args = mock_updater.update_world_state.call_args
        assert 'actor_decisions' in call_args.kwargs

        # Should have decisions from both actors in sample_state
        actor_decisions = call_args.kwargs['actor_decisions']
        assert len(actor_decisions) == 2


class TestCommunicationPhase:
    """Test the communication phase service"""

    @pytest.mark.asyncio
    async def test_communication_phase_handles_no_communications(self, sample_state):
        """Test that communication phase handles case with no communications"""
        # Create mock dependencies
        mock_comm_manager = MagicMock()
        mock_comm_manager.has_pending_communications = MagicMock(return_value=False)

        mock_v1_world_state = MagicMock()

        # Create mock actors that don't want to communicate
        mock_actor = MagicMock()
        mock_actor.name = "Test Actor"
        mock_actor.decide_communication = MagicMock(return_value={
            'initiate_bilateral': False,
            'target_actor': None,
            'message': ''
        })

        actors = {'actor1': mock_actor}

        phase = CommunicationPhase(
            actors=actors,
            v1_world_state=mock_v1_world_state,
            communication_manager=mock_comm_manager
        )

        # Execute phase
        result_state = await phase.execute(sample_state)

        # State should be unchanged (no new communications)
        assert len(result_state.communications) == len(sample_state.communications)

    @pytest.mark.asyncio
    async def test_communication_phase_processes_bilateral_communications(self, sample_state):
        """Test that communication phase handles bilateral communications"""
        mock_comm_manager = MagicMock()
        mock_comm_manager.has_pending_communications = MagicMock(return_value=False)
        mock_comm_manager.get_bilateral_communications_for_turn = MagicMock(return_value=[])

        mock_v1_world_state = MagicMock()

        # Actor 1 wants to communicate with Actor 2
        mock_actor1 = MagicMock()
        mock_actor1.name = "Actor 1"
        mock_actor1.decide_communication = MagicMock(return_value={
            'initiate_bilateral': True,
            'target_actor': 'Actor 2',
            'message': 'Let us cooperate',
            'tokens_used': 50
        })

        # Actor 2 doesn't want to initiate
        mock_actor2 = MagicMock()
        mock_actor2.name = "Actor 2"
        mock_actor2.decide_communication = MagicMock(return_value={
            'initiate_bilateral': False,
            'target_actor': None,
            'message': ''
        })
        mock_actor2.respond_to_bilateral = MagicMock(return_value={
            'response': 'accept',
            'message': 'I agree',
            'internal_notes': 'This seems good',
            'tokens_used': 40
        })

        actors = {
            'actor1': mock_actor1,
            'actor2': mock_actor2
        }

        phase = CommunicationPhase(
            actors=actors,
            v1_world_state=mock_v1_world_state,
            communication_manager=mock_comm_manager
        )

        result_state = await phase.execute(sample_state)

        # Verify actors were asked about communication
        assert mock_actor1.decide_communication.called
        assert mock_actor2.decide_communication.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
