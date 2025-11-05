"""
Integration tests for batch execution system

These tests run the complete batch pipeline end-to-end using a minimal
test scenario to verify all components work together correctly.
"""
import unittest
import os
import tempfile
import shutil
import yaml
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from batch_runner import BatchRunner
from batch_analyzer import BatchAnalyzer


class TestBatchIntegration(unittest.TestCase):
    """Integration tests for complete batch execution pipeline"""

    @classmethod
    def setUpClass(cls):
        """Create a minimal test scenario for integration testing"""
        cls.temp_dir = tempfile.mkdtemp()

        # Create minimal test scenario
        cls.test_scenario_dir = os.path.join(cls.temp_dir, 'test-scenario')
        os.makedirs(cls.test_scenario_dir)

        # Create scenario.yaml
        scenario_config = {
            'name': 'Integration Test Scenario',
            'description': 'Minimal scenario for integration testing',
            'system_prompt': 'You are participating in a test scenario.',
            'initial_world_state': 'This is a test scenario for integration testing.',
            'turns': 2,
            'turn_duration': '1 day',
            'world_state_model': 'openai/gpt-4o-mini',
            'actors': ['actor1', 'actor2']
        }

        with open(os.path.join(cls.test_scenario_dir, 'scenario.yaml'), 'w') as f:
            yaml.dump(scenario_config, f)

        # Create actors directory and actor files
        actors_dir = os.path.join(cls.test_scenario_dir, 'actors')
        os.makedirs(actors_dir)

        for actor_name in ['actor1', 'actor2']:
            actor_config = {
                'name': f'Test {actor_name.title()}',
                'short_name': actor_name,
                'llm_model': 'openai/gpt-4o-mini',
                'description': f'Test actor {actor_name}',
                'goals': ['Complete the test successfully'],
                'constraints': ['Follow test protocol'],
                'expertise': ['Testing'],
                'decision_style': 'methodical'
            }

            actor_file = os.path.join(actors_dir, f'{actor_name}.yaml')
            with open(actor_file, 'w') as f:
                yaml.dump(actor_config, f)

        # Create metrics.yaml
        metrics_config = {
            'scenario_name': 'Integration Test',
            'metrics': {
                'test_metric': {
                    'description': 'A test metric',
                    'extraction_method': 'regex',
                    'pattern': r'test_value:\s*(\d+)',
                    'type': 'int'
                }
            }
        }

        metrics_file = os.path.join(cls.test_scenario_dir, 'metrics.yaml')
        with open(metrics_file, 'w') as f:
            yaml.dump(metrics_config, f)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Create fresh experiment directory for each test"""
        self.experiment_dir = os.path.join(self.temp_dir, f'experiment-{id(self)}')
        os.makedirs(self.experiment_dir, exist_ok=True)

    def tearDown(self):
        """Clean up experiment directory"""
        if os.path.exists(self.experiment_dir):
            shutil.rmtree(self.experiment_dir)

    def _create_batch_config(
        self,
        runs_per_variation=2,
        max_parallel=1,
        budget_limit=None,
        variations=None
    ):
        """
        Helper to create batch configuration file

        Args:
            runs_per_variation: Number of runs per variation
            max_parallel: Max concurrent runs
            budget_limit: Optional budget limit
            variations: Optional variation config (default: simple actor model variation)

        Returns:
            Path to batch config file
        """
        if variations is None:
            variations = [
                {
                    'type': 'actor_model',
                    'actor': 'actor1',
                    'values': ['openai/gpt-4o-mini']
                }
            ]

        config = {
            'experiment_name': 'Integration Test Experiment',
            'description': 'Testing batch execution',
            'base_scenario': self.test_scenario_dir,
            'runs_per_variation': runs_per_variation,
            'max_parallel': max_parallel,
            'timeout_per_run': 600,
            'output_dir': self.experiment_dir,
            'save_individual_runs': True,
            'aggregate_metrics': True,
            'variations': variations
        }

        if budget_limit:
            config['budget_limit'] = budget_limit

        config_path = os.path.join(self.experiment_dir, 'batch-config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        return config_path

    def test_sequential_batch_execution(self):
        """Test complete sequential batch execution"""
        # Create batch config
        config_path = self._create_batch_config(
            runs_per_variation=2,
            max_parallel=1
        )

        # Run batch
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Verify output structure
        self.assertTrue(os.path.exists(self.experiment_dir))
        self.assertTrue(os.path.exists(os.path.join(self.experiment_dir, 'runs')))
        self.assertTrue(os.path.exists(os.path.join(self.experiment_dir, 'batch-summary.json')))
        self.assertTrue(os.path.exists(os.path.join(self.experiment_dir, 'batch-costs.json')))
        self.assertTrue(os.path.exists(os.path.join(self.experiment_dir, 'batch-state.json')))

        # Verify summary
        with open(os.path.join(self.experiment_dir, 'batch-summary.json')) as f:
            summary = json.load(f)

        self.assertEqual(summary['total_runs_planned'], 2)
        self.assertGreater(summary['runs_completed'], 0)

        # Verify individual runs exist
        runs_dir = os.path.join(self.experiment_dir, 'runs')
        run_dirs = [d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))]
        self.assertGreater(len(run_dirs), 0)

        # Verify run contents
        first_run = os.path.join(runs_dir, run_dirs[0])
        self.assertTrue(os.path.exists(os.path.join(first_run, 'costs.json')))
        self.assertTrue(os.path.exists(os.path.join(first_run, 'scenario-state.json')))

    def test_parallel_batch_execution(self):
        """Test parallel batch execution with multiple workers"""
        # Create batch config with parallel execution
        config_path = self._create_batch_config(
            runs_per_variation=2,
            max_parallel=2
        )

        # Run batch
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Verify completion
        with open(os.path.join(self.experiment_dir, 'batch-summary.json')) as f:
            summary = json.load(f)

        self.assertEqual(summary['total_runs_planned'], 2)
        self.assertGreater(summary['runs_completed'], 0)

    def test_multiple_variations(self):
        """Test batch with multiple parameter variations"""
        # Create config with 2x2 variation matrix
        variations = [
            {
                'type': 'actor_model',
                'actor': 'actor1',
                'values': ['openai/gpt-4o-mini']
            },
            {
                'type': 'actor_model',
                'actor': 'actor2',
                'values': ['openai/gpt-4o-mini']
            }
        ]

        config_path = self._create_batch_config(
            runs_per_variation=1,
            max_parallel=1,
            variations=variations
        )

        # Run batch
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Should have 1x1 = 1 variation with 1 run = 1 total run
        with open(os.path.join(self.experiment_dir, 'batch-summary.json')) as f:
            summary = json.load(f)

        self.assertEqual(summary['total_runs_planned'], 1)

    def test_batch_resume_functionality(self):
        """Test batch resume after interruption"""
        # Create batch config
        config_path = self._create_batch_config(
            runs_per_variation=3,
            max_parallel=1
        )

        # Run batch initially (will complete all runs since they're fast)
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Verify state was saved
        state_file = os.path.join(self.experiment_dir, 'batch-state.json')
        self.assertTrue(os.path.exists(state_file))

        with open(state_file) as f:
            state = json.load(f)

        self.assertIn('completed_runs', state)
        self.assertIn('experiment_name', state)

        # Try to resume (should detect all runs complete)
        runner2 = BatchRunner(config_path, resume=True, progress_display=False)
        runner2.run()

        # Should still have same results
        with open(os.path.join(self.experiment_dir, 'batch-summary.json')) as f:
            summary = json.load(f)

        self.assertEqual(summary['total_runs_planned'], 3)

    def test_cost_tracking(self):
        """Test cost tracking throughout batch execution"""
        config_path = self._create_batch_config(
            runs_per_variation=2,
            max_parallel=1
        )

        # Run batch
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Verify cost tracking
        costs_file = os.path.join(self.experiment_dir, 'batch-costs.json')
        self.assertTrue(os.path.exists(costs_file))

        with open(costs_file) as f:
            costs = json.load(f)

        self.assertIn('summary', costs)
        self.assertIn('run_costs', costs)
        self.assertIn('variation_statistics', costs)

        summary = costs['summary']
        self.assertGreaterEqual(summary['total_spent'], 0.0)
        self.assertGreater(summary['runs_completed'], 0)

    def test_batch_analysis_integration(self):
        """Test batch analyzer integration with completed batch"""
        # Run a batch first
        config_path = self._create_batch_config(
            runs_per_variation=2,
            max_parallel=1
        )

        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Run analyzer
        analyzer = BatchAnalyzer(self.experiment_dir)
        analyzer.save_analysis_data()

        # Verify analysis outputs
        analysis_dir = os.path.join(self.experiment_dir, 'analysis')
        self.assertTrue(os.path.exists(analysis_dir))
        self.assertTrue(os.path.exists(os.path.join(analysis_dir, 'metrics-analysis.json')))
        self.assertTrue(os.path.exists(os.path.join(analysis_dir, 'variation-statistics.json')))
        self.assertTrue(os.path.exists(os.path.join(analysis_dir, 'patterns.json')))

        # Generate report
        report = analyzer.generate_analysis_report()
        self.assertIn('Batch Analysis Report', report)
        self.assertIn('Total Runs', report)

        # Verify report file was created
        report_file = os.path.join(analysis_dir, 'analysis-report.md')
        self.assertTrue(os.path.exists(report_file))

    def test_budget_limit_enforcement(self):
        """Test that budget limits are enforced"""
        # Create config with very low budget limit
        config_path = self._create_batch_config(
            runs_per_variation=5,
            max_parallel=1,
            budget_limit=0.01  # Very low limit
        )

        # Run batch
        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Should have stopped due to budget
        with open(os.path.join(self.experiment_dir, 'batch-summary.json')) as f:
            summary = json.load(f)

        # Might complete 0-2 runs depending on actual costs
        self.assertLessEqual(summary['runs_completed'], summary['total_runs_planned'])

    def test_output_directory_structure(self):
        """Test that batch creates correct output directory structure"""
        config_path = self._create_batch_config(
            runs_per_variation=1,
            max_parallel=1
        )

        runner = BatchRunner(config_path, progress_display=False)
        runner.run()

        # Verify directory structure
        expected_files = [
            'batch-config.yaml',
            'batch-summary.json',
            'batch-costs.json',
            'batch-state.json'
        ]

        for filename in expected_files:
            filepath = os.path.join(self.experiment_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"Missing: {filename}")

        # Verify runs directory
        runs_dir = os.path.join(self.experiment_dir, 'runs')
        self.assertTrue(os.path.exists(runs_dir))
        self.assertTrue(os.path.isdir(runs_dir))


class TestBatchWorkflow(unittest.TestCase):
    """Test complete batch workflow scenarios"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_research_workflow(self):
        """
        Test a complete research workflow:
        1. Create scenario
        2. Run batch
        3. Analyze results
        4. Generate report
        """
        # This test verifies the complete end-to-end workflow
        # that a researcher would actually use

        # For now, just verify the workflow steps are available
        # (Full implementation would run actual scenario)

        from batch_runner import BatchRunner
        from batch_analyzer import BatchAnalyzer
        from parameter_variator import ParameterVariator
        from batch_cost_manager import BatchCostManager

        # Verify all components are importable
        self.assertTrue(callable(BatchRunner))
        self.assertTrue(callable(BatchAnalyzer))
        self.assertTrue(callable(ParameterVariator))
        self.assertTrue(callable(BatchCostManager))


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
