#!/usr/bin/env python3
"""
Test V2 Batch Runner

Tests the batch orchestrator that integrates all batch components.
"""
import sys
import os
import asyncio
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.batch_runner import BatchRunner
from scenario_lab.models.state import ScenarioState, ScenarioStatus


def create_test_scenario(base_dir: str) -> str:
    """Create a minimal test scenario"""
    scenario_path = os.path.join(base_dir, 'test-scenario')
    os.makedirs(scenario_path, exist_ok=True)
    os.makedirs(os.path.join(scenario_path, 'actors'), exist_ok=True)

    # Create scenario.yaml
    scenario_config = {
        'name': 'Test Scenario',
        'description': 'Test scenario for batch runner',
        'turns': 3,
        'world_state_model': 'openai/gpt-4o-mini',
        'initial_world_state': 'Test world state',
        'system_prompt': 'Test system prompt'
    }
    with open(os.path.join(scenario_path, 'scenario.yaml'), 'w') as f:
        yaml.dump(scenario_config, f)

    # Create actor
    actor_config = {
        'name': 'Test Actor',
        'short_name': 'test',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'Test actor prompt',
        'goals': ['Test goal']
    }
    with open(os.path.join(scenario_path, 'actors', 'test-actor.yaml'), 'w') as f:
        yaml.dump(actor_config, f)

    return scenario_path


def create_batch_config(base_dir: str, scenario_path: str) -> str:
    """Create a test batch configuration"""
    config = {
        'experiment_name': 'Test Batch',
        'description': 'Test batch experiment',
        'base_scenario': scenario_path,
        'output_dir': os.path.join(base_dir, 'output'),
        'runs_per_variation': 2,
        'max_parallel': 1,
        'budget_limit': 10.0,
        'cost_per_run_limit': 5.0,
        'variations': {
            'actor_models': {
                'test': ['openai/gpt-4o-mini', 'openai/gpt-4o']
            }
        }
    }

    config_path = os.path.join(base_dir, 'batch-config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config_path


def test_config_loading():
    """Test configuration loading and validation"""
    print("=" * 70)
    print("TEST 1: Config loading and validation")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        # Create test scenario and config
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        # Load config
        runner = BatchRunner(config_path)

        assert runner.experiment_name == 'Test Batch'
        assert runner.base_scenario == scenario_path
        assert runner.runs_per_variation == 2
        assert runner.max_parallel == 1
        assert runner.cost_manager.budget_limit == 10.0
        assert runner.cost_manager.cost_per_run_limit == 5.0

        print(f"  ✓ Config loaded successfully")
        print(f"  ✓ Experiment name: {runner.experiment_name}")
        print(f"  ✓ Runs per variation: {runner.runs_per_variation}")
        print(f"  ✓ Budget limit: ${runner.cost_manager.budget_limit:.2f}")

        print()
        print("✅ Test 1 passed: Config loading works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_output_directory_setup():
    """Test output directory creation"""
    print("=" * 70)
    print("TEST 2: Output directory setup")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path)
        runner._setup_output_directory()

        # Check directories created
        assert os.path.exists(runner.output_dir)
        assert os.path.exists(runner.runs_dir)

        # Check config copy created
        config_copy = os.path.join(runner.output_dir, 'batch-config.yaml')
        assert os.path.exists(config_copy)

        print(f"  ✓ Output directory created: {runner.output_dir}")
        print(f"  ✓ Runs directory created: {runner.runs_dir}")
        print(f"  ✓ Config copied to output")

        print()
        print("✅ Test 2 passed: Output directory setup works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_run_id_generation():
    """Test run ID generation"""
    print("=" * 70)
    print("TEST 3: Run ID generation")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path)

        run_id_1 = runner._generate_run_id(1, 1)
        run_id_2 = runner._generate_run_id(1, 2)
        run_id_3 = runner._generate_run_id(2, 1)

        assert run_id_1 == "var-001-run-001"
        assert run_id_2 == "var-001-run-002"
        assert run_id_3 == "var-002-run-001"

        print(f"  ✓ Generated run IDs:")
        print(f"    {run_id_1}")
        print(f"    {run_id_2}")
        print(f"    {run_id_3}")

        print()
        print("✅ Test 3 passed: Run ID generation works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_state_persistence():
    """Test saving and loading batch state"""
    print("=" * 70)
    print("TEST 4: State persistence")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path)
        runner._setup_output_directory()

        # Add some completed runs
        runner.completed_runs.add("var-001-run-001")
        runner.completed_runs.add("var-001-run-002")
        runner.failed_runs.append({
            'run_id': 'var-002-run-001',
            'error': 'Test error',
            'status': 'failed'
        })
        runner.variations = [
            {'variation_id': 1, 'description': 'Test var 1'},
            {'variation_id': 2, 'description': 'Test var 2'}
        ]

        # Save state
        runner._save_batch_state()

        state_file = os.path.join(runner.output_dir, 'batch-state.json')
        assert os.path.exists(state_file)
        print(f"  ✓ State saved to: {state_file}")

        # Create new runner and load state
        runner2 = BatchRunner(config_path, resume=True)
        runner2._setup_output_directory()
        loaded = runner2._load_batch_state()

        assert loaded is True
        assert len(runner2.completed_runs) == 2
        assert "var-001-run-001" in runner2.completed_runs
        assert len(runner2.failed_runs) == 1
        assert len(runner2.variations) == 2

        print(f"  ✓ State loaded successfully")
        print(f"  ✓ Completed runs: {len(runner2.completed_runs)}")
        print(f"  ✓ Failed runs: {len(runner2.failed_runs)}")

        print()
        print("✅ Test 4 passed: State persistence works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_single_scenario_execution():
    """Test executing a single scenario"""
    print("=" * 70)
    print("TEST 5: Single scenario execution")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path)
        runner._setup_output_directory()

        # Mock the run_scenario_async function
        with patch('scenario_lab.batch.batch_runner.run_scenario_async') as mock_run:
            # Create mock final state
            mock_state = Mock(spec=ScenarioState)
            mock_state.total_cost.return_value = 1.5
            mock_state.status = ScenarioStatus.COMPLETED
            mock_run.return_value = mock_state

            variation = {
                'variation_id': 1,
                'description': 'Test variation',
                'modifications': {}
            }

            result = await runner._run_single_scenario('var-001-run-001', variation, 1)

            assert result['status'] == 'success'
            assert result['cost'] == 1.5
            assert result['run_id'] == 'var-001-run-001'

            print(f"  ✓ Scenario executed successfully")
            print(f"  ✓ Status: {result['status']}")
            print(f"  ✓ Cost: ${result['cost']:.2f}")

        print()
        print("✅ Test 5 passed: Single scenario execution works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_dry_run_preview():
    """Test dry-run preview mode"""
    print("=" * 70)
    print("TEST 6: Dry-run preview")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path, dry_run=True)

        # Should not create any directories yet
        assert not os.path.exists(runner.runs_dir)

        # Show preview (this should not execute anything)
        print("  ✓ Showing preview:")
        print()
        runner.show_batch_preview()
        print()

        # Check variations were generated
        assert len(runner.variations) > 0
        print(f"  ✓ Generated {len(runner.variations)} variations")

        # Still no execution directories
        assert not os.path.exists(runner.runs_dir)
        print(f"  ✓ No execution directories created")

        print()
        print("✅ Test 6 passed: Dry-run preview works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_sequential_execution():
    """Test sequential batch execution"""
    print("=" * 70)
    print("TEST 7: Sequential execution")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        # Create simple config with 1 variation, 2 runs
        simple_config = {
            'experiment_name': 'Simple Test',
            'base_scenario': scenario_path,
            'output_dir': os.path.join(temp_dir, 'output'),
            'runs_per_variation': 2,
            'max_parallel': 1,
            'variations': {
                'actor_models': {
                    'test': ['openai/gpt-4o-mini']
                }
            }
        }
        config_path = os.path.join(temp_dir, 'simple-config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(simple_config, f)

        runner = BatchRunner(config_path, progress_display=False)

        # Mock the run_scenario_async function
        with patch('scenario_lab.batch.batch_runner.run_scenario_async') as mock_run:
            mock_state = Mock(spec=ScenarioState)
            mock_state.total_cost.return_value = 0.5
            mock_state.status = ScenarioStatus.COMPLETED
            mock_run.return_value = mock_state

            await runner.run_sequential()

            # Check that runs completed
            assert len(runner.completed_runs) == 2
            assert runner.cost_manager.total_spent == 1.0  # 2 runs * 0.5

            print(f"  ✓ Sequential execution completed")
            print(f"  ✓ Runs completed: {len(runner.completed_runs)}")
            print(f"  ✓ Total cost: ${runner.cost_manager.total_spent:.2f}")

        print()
        print("✅ Test 7 passed: Sequential execution works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_parallel_execution():
    """Test parallel batch execution"""
    print("=" * 70)
    print("TEST 8: Parallel execution")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)

        # Create config with parallel execution
        parallel_config = {
            'experiment_name': 'Parallel Test',
            'base_scenario': scenario_path,
            'output_dir': os.path.join(temp_dir, 'output'),
            'runs_per_variation': 2,
            'max_parallel': 2,  # Parallel mode
            'variations': {
                'actor_models': {
                    'test': ['openai/gpt-4o-mini']
                }
            }
        }
        config_path = os.path.join(temp_dir, 'parallel-config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(parallel_config, f)

        runner = BatchRunner(config_path, progress_display=False)

        # Mock the run_scenario_async function
        with patch('scenario_lab.batch.batch_runner.run_scenario_async') as mock_run:
            mock_state = Mock(spec=ScenarioState)
            mock_state.total_cost.return_value = 0.5
            mock_state.status = ScenarioStatus.COMPLETED
            mock_run.return_value = mock_state

            await runner.run_parallel()

            # Check that runs completed
            assert len(runner.completed_runs) == 2
            assert runner.cost_manager.total_spent == 1.0

            print(f"  ✓ Parallel execution completed")
            print(f"  ✓ Runs completed: {len(runner.completed_runs)}")
            print(f"  ✓ Total cost: ${runner.cost_manager.total_spent:.2f}")
            print(f"  ✓ Max parallel: 2")

        print()
        print("✅ Test 8 passed: Parallel execution works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_summary_generation():
    """Test batch summary generation"""
    print("=" * 70)
    print("TEST 9: Summary generation")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)
        config_path = create_batch_config(temp_dir, scenario_path)

        runner = BatchRunner(config_path)
        runner._setup_output_directory()

        # Setup some state
        runner.variations = [
            {'variation_id': 1, 'description': 'Var 1'},
            {'variation_id': 2, 'description': 'Var 2'}
        ]
        runner.completed_runs.add('var-001-run-001')
        runner.completed_runs.add('var-001-run-002')
        runner.failed_runs.append({
            'run_id': 'var-002-run-001',
            'error': 'Test error',
            'status': 'failed'
        })
        runner.cost_manager.record_run_cost('var-001-run-001', 1, 1.5, True)
        runner.cost_manager.record_run_cost('var-001-run-002', 1, 2.0, True)

        # Generate summary
        runner._generate_summary()

        # Check summary file created
        summary_file = os.path.join(runner.output_dir, 'batch-summary.json')
        assert os.path.exists(summary_file)

        with open(summary_file, 'r') as f:
            summary = json.load(f)

        assert summary['experiment_name'] == 'Test Batch'
        assert summary['runs_completed'] == 2
        assert summary['runs_failed'] == 1
        assert summary['cost_summary']['total_spent'] == 3.5

        print(f"  ✓ Summary generated: {summary_file}")
        print(f"  ✓ Runs completed: {summary['runs_completed']}")
        print(f"  ✓ Runs failed: {summary['runs_failed']}")
        print(f"  ✓ Total cost: ${summary['cost_summary']['total_spent']:.2f}")

        print()
        print("✅ Test 9 passed: Summary generation works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_budget_enforcement():
    """Test budget limit enforcement"""
    print("=" * 70)
    print("TEST 10: Budget enforcement")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        scenario_path = create_test_scenario(temp_dir)

        # Create config with very low budget
        budget_config = {
            'experiment_name': 'Budget Test',
            'base_scenario': scenario_path,
            'output_dir': os.path.join(temp_dir, 'output'),
            'runs_per_variation': 5,
            'max_parallel': 1,
            'budget_limit': 1.0,  # Very low budget
            'variations': {
                'actor_models': {
                    'test': ['openai/gpt-4o-mini']
                }
            }
        }
        config_path = os.path.join(temp_dir, 'budget-config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(budget_config, f)

        runner = BatchRunner(config_path, progress_display=False)

        # Mock the run_scenario_async function
        with patch('scenario_lab.batch.batch_runner.run_scenario_async') as mock_run:
            mock_state = Mock(spec=ScenarioState)
            mock_state.total_cost.return_value = 0.6  # Each run costs 0.6
            mock_state.status = ScenarioStatus.COMPLETED
            mock_run.return_value = mock_state

            await runner.run_sequential()

            # Should stop after 2 runs due to budget
            # Run 1: $0.60 spent (< $1.00), continues
            # Run 2: Starts at $0.60 (< $1.00), completes at $1.20 (> $1.00), stops
            # Allow overage of one run's cost since budget check happens before run starts
            assert len(runner.completed_runs) <= 2  # Max 2 runs with budget 1.0
            assert runner.cost_manager.total_spent <= runner.cost_manager.budget_limit + 0.6  # Budget + one run

            print(f"  ✓ Budget enforcement worked")
            print(f"  ✓ Budget limit: ${runner.cost_manager.budget_limit:.2f}")
            print(f"  ✓ Total spent: ${runner.cost_manager.total_spent:.2f}")
            print(f"  ✓ Runs completed: {len(runner.completed_runs)}/5")
            print(f"  ✓ Stopped before completing all 5 runs")

        print()
        print("✅ Test 10 passed: Budget enforcement works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all batch runner tests"""
    print()
    print("=" * 70)
    print("V2 BATCH RUNNER TESTS")
    print("=" * 70)
    print()

    async def run_async_tests():
        tests = [
            (test_config_loading, False),
            (test_output_directory_setup, False),
            (test_run_id_generation, False),
            (test_state_persistence, False),
            (test_single_scenario_execution, True),
            (test_dry_run_preview, False),
            (test_sequential_execution, True),
            (test_parallel_execution, True),
            (test_summary_generation, False),
            (test_budget_enforcement, True),
        ]

        results = []
        for test_func, is_async in tests:
            try:
                if is_async:
                    result = await test_func()
                else:
                    result = test_func()
                results.append(result)
            except Exception as e:
                print(f"  ✗ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)

        return results

    results = asyncio.run(run_async_tests())

    print("=" * 70)
    print("BATCH RUNNER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL BATCH RUNNER TESTS PASSED")
        print()
        print("Phase 4.5 Complete: Batch Runner")
        print("  ✓ Configuration loading and validation")
        print("  ✓ Output directory setup")
        print("  ✓ Run ID generation")
        print("  ✓ State persistence (save/load)")
        print("  ✓ Single scenario execution")
        print("  ✓ Dry-run preview mode")
        print("  ✓ Sequential batch execution")
        print("  ✓ Parallel batch execution")
        print("  ✓ Summary generation with statistics")
        print("  ✓ Budget limit enforcement")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
