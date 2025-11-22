"""
Tests for cost estimator functionality

Tests cost estimation with and without historical data.
"""
import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from scenario_lab.utils.cost_estimator import CostEstimator, CostEstimate, HistoricalCostData


class TestCostEstimatorBase(unittest.TestCase):
    """Base class for cost estimator tests"""

    def create_minimal_scenario(self, tmpdir: str) -> Path:
        """Create a minimal valid scenario for testing"""
        scenario_dir = Path(tmpdir) / 'test-scenario'
        scenario_dir.mkdir()

        # Create scenario.yaml
        (scenario_dir / 'scenario.yaml').write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: The world is in a test state.
turns: 5
turn_duration: 1 day
world_state_model: openai/gpt-4o-mini
enable_bilateral_communication: true
max_communications_per_turn: 2
actors:
  - test-actor
""")

        # Create actors directory and actor file
        actors_dir = scenario_dir / 'actors'
        actors_dir.mkdir()
        (actors_dir / 'test-actor.yaml').write_text("""
name: Test Actor
short_name: test-actor
llm_model: openai/gpt-4o-mini
system_prompt: You are a test actor.
goals:
  - Complete the test
""")

        return scenario_dir


class TestCommunicationCostEstimation(TestCostEstimatorBase):
    """Tests for communication cost estimation (should be 0 for stub phase)"""

    def test_communication_cost_is_zero(self):
        """Communication costs should be 0 since the phase is a stub"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            estimator = CostEstimator(scenario_dir)
            self.assertTrue(estimator.load_configs())

            estimate = estimator.estimate()

            # Communication cost should be 0 since the phase is a stub
            self.assertEqual(estimate.communication_cost, 0.0)

    def test_communication_cost_zero_even_when_enabled(self):
        """Communication costs should be 0 even when bilateral communication is enabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            estimator = CostEstimator(scenario_dir)
            self.assertTrue(estimator.load_configs())

            # Verify communication is enabled
            self.assertTrue(estimator.scenario_config.enable_bilateral_communication)

            estimate = estimator.estimate()

            # Still should be 0
            self.assertEqual(estimate.communication_cost, 0.0)


class TestHistoricalDataLoading(TestCostEstimatorBase):
    """Tests for historical data loading and usage"""

    def test_no_historical_data_when_no_runs(self):
        """Should have no historical data when no runs exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            estimator = CostEstimator(scenario_dir)
            estimator.load_configs()

            self.assertIsNone(estimator.historical_data)

    def test_loads_historical_data_from_runs(self):
        """Should load historical data from previous runs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            # Create a run with cost data
            runs_dir = scenario_dir / 'runs' / 'run-001'
            runs_dir.mkdir(parents=True)

            state_data = {
                "version": "2.0",
                "scenario_id": "test",
                "scenario_name": "Test",
                "run_id": "run-001",
                "turn": 3,
                "status": "completed",
                "world_state": {"turn": 3, "content": "Test"},
                "actors": {},
                "decisions": {},
                "communications": [],
                "costs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "actor": "test-actor",
                        "phase": "decision",
                        "model": "openai/gpt-4o-mini",
                        "input_tokens": 1000,
                        "output_tokens": 200,
                        "cost": 0.001
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "actor": "",
                        "phase": "world_update",
                        "model": "openai/gpt-4o-mini",
                        "input_tokens": 1500,
                        "output_tokens": 300,
                        "cost": 0.002
                    }
                ],
                "metrics": [],
                "metadata": {}
            }

            (runs_dir / 'scenario-state-v2.json').write_text(json.dumps(state_data))

            estimator = CostEstimator(scenario_dir)
            estimator.load_configs()

            self.assertIsNotNone(estimator.historical_data)
            self.assertEqual(estimator.historical_data.run_count, 1)
            self.assertIn("test-actor", estimator.historical_data.avg_tokens_per_decision)

    def test_historical_data_used_flag(self):
        """Estimate should indicate when historical data was used"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            # Create a run with cost data
            runs_dir = scenario_dir / 'runs' / 'run-001'
            runs_dir.mkdir(parents=True)

            state_data = {
                "version": "2.0",
                "scenario_id": "test",
                "scenario_name": "Test",
                "run_id": "run-001",
                "turn": 2,
                "status": "completed",
                "world_state": {"turn": 2, "content": "Test"},
                "actors": {},
                "decisions": {},
                "communications": [],
                "costs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "actor": "test-actor",
                        "phase": "decision",
                        "model": "openai/gpt-4o-mini",
                        "input_tokens": 800,
                        "output_tokens": 150,
                        "cost": 0.0005
                    }
                ],
                "metrics": [],
                "metadata": {}
            }

            (runs_dir / 'scenario-state-v2.json').write_text(json.dumps(state_data))

            estimator = CostEstimator(scenario_dir)
            estimator.load_configs()
            estimate = estimator.estimate()

            self.assertTrue(estimate.historical_data_used)

    def test_no_historical_data_flag_when_no_runs(self):
        """Estimate should indicate when no historical data was used"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            estimator = CostEstimator(scenario_dir)
            estimator.load_configs()
            estimate = estimator.estimate()

            self.assertFalse(estimate.historical_data_used)


class TestHistoricalCostDataClass(unittest.TestCase):
    """Tests for HistoricalCostData dataclass"""

    def test_default_values(self):
        """Test default values of HistoricalCostData"""
        data = HistoricalCostData()

        self.assertEqual(data.run_count, 0)
        self.assertEqual(data.avg_cost_per_turn, 0.0)
        self.assertEqual(data.avg_tokens_per_decision, {})
        self.assertEqual(data.avg_tokens_per_world_update, (0, 0))
        self.assertEqual(data.total_historical_cost, 0.0)


class TestCostEstimateDataclass(unittest.TestCase):
    """Tests for CostEstimate dataclass"""

    def test_historical_data_used_default(self):
        """Test that historical_data_used defaults to False"""
        estimate = CostEstimate(
            total_cost=1.0,
            per_turn_cost=0.1,
            actor_costs={},
            world_state_cost=0.5,
            communication_cost=0.0,
            metrics_cost=0.0,
            validation_cost=0.0,
            warnings=[]
        )

        self.assertFalse(estimate.historical_data_used)


if __name__ == '__main__':
    unittest.main()
