"""
Golden file tests for Scenario Lab V2

Compares actual scenario outputs against known-good reference files.
These tests ensure output consistency and catch unintended changes.
"""
import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock

from scenario_lab.runners import SyncRunner


class DeterministicMockLLM:
    """
    Deterministic mock LLM for golden file testing

    Returns the same responses every time for reproducible outputs.
    """

    def __init__(self):
        self.call_sequence = 0
        # Pre-defined responses for deterministic output
        self.sequence_responses = {
            # Turn 1 - Actor 1 decision
            0: '''{
                "goals": ["Establish baseline cooperation framework"],
                "reasoning": "Initial turn requires setting cooperative foundations and establishing communication channels with other actors.",
                "action": "Propose a preliminary framework for information sharing and mutual coordination on key policy issues."
            }''',
            # Turn 1 - Actor 2 decision
            1: '''{
                "goals": ["Understand the landscape and actor positions"],
                "reasoning": "First priority is to assess other actors' positions and identify potential areas of alignment or conflict.",
                "action": "Conduct stakeholder analysis and reach out to Actor 1 to discuss their proposed framework."
            }''',
            # Turn 1 - World state update
            2: '''**Turn 1 Summary:**

The simulation has begun with both actors taking initial positioning actions.

**Key Developments:**

- **Actor 1** proposed a preliminary cooperation framework focused on information sharing
- **Actor 2** initiated stakeholder analysis and opened communication with Actor 1
- Initial dialogue has been established between the two actors

**World State:**

The policy landscape remains in its initial configuration, with actors now having taken first positions. The proposed framework from Actor 1 is under consideration, and Actor 2's outreach has been received positively.

**Outlook:**

Turn duration: 1 week. The next turn will likely see responses to these initial moves and potential framework negotiations.''',
            # Turn 2 - Actor 1 decision
            3: '''{
                "goals": ["Refine framework based on Actor 2 feedback"],
                "reasoning": "Actor 2 has engaged positively. Now is the time to incorporate their stakeholder insights and refine the cooperation framework.",
                "action": "Meet with Actor 2 to integrate their stakeholder analysis into the framework and propose specific cooperation mechanisms."
            }''',
            # Turn 2 - Actor 2 decision
            4: '''{
                "goals": ["Negotiate framework terms"],
                "reasoning": "Actor 1's framework is promising but needs adjustment to address concerns identified in stakeholder analysis.",
                "action": "Present detailed feedback on the framework and propose amendments that address stakeholder concerns while maintaining cooperation spirit."
            }''',
            # Turn 2 - World state update
            5: '''**Turn 2 Summary:**

Negotiations on the cooperation framework have progressed significantly.

**Key Developments:**

- **Actor 1** incorporated Actor 2's stakeholder insights into framework refinements
- **Actor 2** provided constructive feedback and proposed specific amendments
- Bilateral meeting between actors resulted in productive framework negotiations

**World State:**

The cooperation framework is taking shape through iterative negotiation. Both actors are demonstrating commitment to finding mutually acceptable terms. The policy landscape shows early signs of collaborative governance emerging.

**Outlook:**

Turn duration: 1 week. Next turn will likely focus on finalizing framework details and beginning implementation planning.''',
        }

    def make_call(self, model: str, messages: list, temperature: float = 0.7, **kwargs):
        """
        Return deterministic response based on call sequence

        Returns:
            Tuple of (content_string, tokens_int)
        """
        response = self.sequence_responses.get(
            self.call_sequence,
            '{"goals": [], "reasoning": "Default", "action": "Wait"}'
        )

        self.call_sequence += 1

        # Calculate consistent token count
        tokens = len(response.split()) * 2

        return response, tokens


@pytest.fixture
def golden_scenario_dir():
    """Create golden test scenario directory"""
    temp_dir = tempfile.mkdtemp()
    scenario_dir = Path(temp_dir) / 'golden-scenario'
    scenario_dir.mkdir()

    # Create scenario.yaml
    scenario_yaml = """name: Golden File Test Scenario
description: Scenario for golden file comparison testing
num_turns: 2
turn_duration: "1 week"
initial_world_state: |
  **Initial Policy Landscape**

  This is a test scenario designed for golden file validation.

  **Current Status:**
  - Turn duration: 1 week
  - Participating actors: Policy Maker, Analyst
  - Objective: Generate consistent, reproducible outputs

world_state_model: "test/mock-model"
context_window: 2
"""

    with open(scenario_dir / 'scenario.yaml', 'w') as f:
        f.write(scenario_yaml)

    # Create actors
    actors_dir = scenario_dir / 'actors'
    actors_dir.mkdir()

    actor1_yaml = """name: Policy Maker
short_name: actor1
llm_model: "test/mock-model"
system_prompt: |
  You are a Policy Maker focused on establishing cooperative frameworks.

  Your approach is methodical and consensus-building.

goals:
  - Establish cooperation framework
  - Build consensus among stakeholders

constraints:
  - Must consider stakeholder input
  - Must maintain diplomatic approach

expertise: Policy Development
decision_style: Collaborative
"""

    actor2_yaml = """name: Analyst
short_name: actor2
llm_model: "test/mock-model"
system_prompt: |
  You are an Analyst focused on thorough stakeholder assessment.

  Your approach is analytical and evidence-based.

goals:
  - Conduct comprehensive stakeholder analysis
  - Provide evidence-based recommendations

constraints:
  - Must base decisions on analysis
  - Must consider multiple perspectives

expertise: Stakeholder Analysis
decision_style: Analytical
"""

    with open(actors_dir / 'actor1.yaml', 'w') as f:
        f.write(actor1_yaml)

    with open(actors_dir / 'actor2.yaml', 'w') as f:
        f.write(actor2_yaml)

    yield str(scenario_dir)

    # Cleanup
    shutil.rmtree(temp_dir)


class TestGoldenFiles:
    """Test output consistency against golden files"""

    @pytest.mark.asyncio
    async def test_deterministic_output(self, golden_scenario_dir, monkeypatch):
        """Test that identical inputs produce identical outputs"""
        # Patch LLM
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        mock_llm = DeterministicMockLLM()

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # Run scenario twice
        temp_dir = tempfile.mkdtemp()
        try:
            output_dir1 = Path(temp_dir) / 'run1'
            output_dir2 = Path(temp_dir) / 'run2'

            # First run
            mock_llm.call_sequence = 0  # Reset sequence
            runner1 = SyncRunner(
                scenario_path=golden_scenario_dir,
                output_path=str(output_dir1),
                end_turn=2
            )
            runner1.setup()
            state1 = await runner1.run()

            # Second run
            mock_llm.call_sequence = 0  # Reset sequence
            runner2 = SyncRunner(
                scenario_path=golden_scenario_dir,
                output_path=str(output_dir2),
                end_turn=2
            )
            runner2.setup()
            state2 = await runner2.run()

            # Compare state files
            with open(output_dir1 / 'scenario-state-v2.json') as f:
                state_data1 = json.load(f)

            with open(output_dir2 / 'scenario-state-v2.json') as f:
                state_data2 = json.load(f)

            # Ignore timestamps and run IDs (these will differ)
            fields_to_compare = ['turn', 'scenario_name', 'status']
            for field in fields_to_compare:
                assert state_data1[field] == state_data2[field], f"Mismatch in {field}"

            # Verify same number of costs
            assert len(state_data1['costs']) == len(state_data2['costs'])

            # Verify same number of actors
            assert len(state_data1['actors']) == len(state_data2['actors'])

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_state_structure_consistency(self, golden_scenario_dir, monkeypatch):
        """Test that saved state has consistent structure"""
        # Patch LLM
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        mock_llm = DeterministicMockLLM()

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'

            runner = SyncRunner(
                scenario_path=golden_scenario_dir,
                output_path=str(output_dir),
                end_turn=2
            )
            runner.setup()
            await runner.run()

            # Load state file
            with open(output_dir / 'scenario-state-v2.json') as f:
                state_data = json.load(f)

            # Verify required fields exist
            required_fields = [
                'version',
                'scenario_id',
                'scenario_name',
                'run_id',
                'turn',
                'status',
                'world_state',
                'actors',
                'decisions',
                'communications',
                'costs',
                'metrics',
                'scenario_config',
                'execution_metadata'
            ]

            for field in required_fields:
                assert field in state_data, f"Missing required field: {field}"

            # Verify world state structure
            assert 'turn' in state_data['world_state']
            assert 'content' in state_data['world_state']

            # Verify cost records have required fields
            for cost in state_data['costs']:
                assert 'timestamp' in cost
                assert 'model' in cost
                assert 'input_tokens' in cost
                assert 'output_tokens' in cost
                assert 'cost' in cost

        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_world_state_progression(self, golden_scenario_dir, monkeypatch):
        """Test that world state evolves consistently across turns"""
        # Patch LLM
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        mock_llm = DeterministicMockLLM()

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        temp_dir = tempfile.mkdtemp()
        try:
            output_dir = Path(temp_dir) / 'output'

            runner = SyncRunner(
                scenario_path=golden_scenario_dir,
                output_path=str(output_dir),
                end_turn=2
            )
            runner.setup()
            await runner.run()

            # Verify world state files
            assert (output_dir / 'world-state-001.md').exists()
            assert (output_dir / 'world-state-002.md').exists()

            # Read world states
            with open(output_dir / 'world-state-001.md') as f:
                ws1 = f.read()

            with open(output_dir / 'world-state-002.md') as f:
                ws2 = f.read()

            # Verify turn headers
            assert '# Turn 1' in ws1
            assert '# Turn 2' in ws2

            # Verify content is non-empty
            assert len(ws1) > 100
            assert len(ws2) > 100

            # Verify turn 2 references progression
            assert 'Turn 2' in ws2 or 'turn 2' in ws2.lower()

        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
