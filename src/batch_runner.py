"""
Batch Runner - Execute multiple scenario variations for statistical analysis
"""
import os
import yaml
import json
import shutil
import logging
import tempfile
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

from parameter_variator import ParameterVariator
from batch_cost_manager import BatchCostManager
from batch_progress_tracker import BatchProgressTracker
from batch_parallel_executor import BatchParallelExecutor, RateLimitManager
from run_scenario import run_scenario


class BatchRunner:
    """
    Orchestrates execution of multiple scenario variations with cost controls
    """

    def __init__(self, config_path: str, resume: bool = False, progress_display: bool = True, dry_run: bool = False):
        """
        Initialize batch runner

        Args:
            config_path: Path to batch configuration YAML file
            resume: If True, attempt to resume from previous batch execution
            progress_display: If True, show rich progress display (default: True)
            dry_run: If True, show preview without actually running
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.resume_mode = resume
        self.progress_display = progress_display
        self.dry_run = dry_run

        # Extract configuration
        self.experiment_name = self.config['experiment_name']
        self.base_scenario = self.config['base_scenario']
        self.runs_per_variation = self.config.get('runs_per_variation', 1)
        self.max_parallel = self.config.get('max_parallel', 1)
        self.timeout_per_run = self.config.get('timeout_per_run', 1800)

        # Output configuration
        self.output_dir = self.config.get('output_dir', 'experiments/batch-run')
        self.save_individual_runs = self.config.get('save_individual_runs', True)

        # Initialize components
        self.variator = ParameterVariator(
            self.base_scenario,
            self.config.get('variations', [])
        )

        self.cost_manager = BatchCostManager(
            budget_limit=self.config.get('budget_limit'),
            cost_per_run_limit=self.config.get('cost_per_run_limit')
        )

        # State tracking
        self.variations = []
        self.completed_runs = set()  # Set of run_ids that completed
        self.failed_runs = []  # List of {run_id, error}
        self.start_time = None
        self.end_time = None

        # Setup logging
        self.logger = logging.getLogger("batch_runner")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate batch configuration"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Batch config not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Validate required fields
        required = ['experiment_name', 'base_scenario']
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required field in batch config: {field}")

        return config

    def _setup_output_directory(self):
        """Create output directory structure"""
        os.makedirs(self.output_dir, exist_ok=True)

        # Create subdirectories
        self.runs_dir = os.path.join(self.output_dir, 'runs')
        os.makedirs(self.runs_dir, exist_ok=True)

        self.analysis_dir = os.path.join(self.output_dir, 'analysis')
        os.makedirs(self.analysis_dir, exist_ok=True)

        # Copy batch config to output for reference
        config_copy = os.path.join(self.output_dir, 'batch-config.yaml')
        if not os.path.exists(config_copy):
            shutil.copy(self.config_path, config_copy)

    def _generate_run_id(self, variation_id: int, run_number: int) -> str:
        """
        Generate unique run identifier

        Args:
            variation_id: Variation ID (1-based)
            run_number: Run number within variation (1-based)

        Returns:
            Run ID string (e.g., "var-001-run-003")
        """
        return f"var-{variation_id:03d}-run-{run_number:03d}"

    def _save_batch_state(self):
        """Save current batch state for resumption"""
        state = {
            'experiment_name': self.experiment_name,
            'config_path': self.config_path,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'completed_runs': list(self.completed_runs),
            'failed_runs': self.failed_runs,
            'variations': self.variations,
            'runs_per_variation': self.runs_per_variation
        }

        state_file = os.path.join(self.output_dir, 'batch-state.json')
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Save cost state
        cost_file = os.path.join(self.output_dir, 'batch-costs.json')
        self.cost_manager.save_to_file(cost_file)

    def _load_batch_state(self) -> bool:
        """
        Load batch state from previous execution

        Returns:
            True if state loaded successfully, False otherwise
        """
        state_file = os.path.join(self.output_dir, 'batch-state.json')
        cost_file = os.path.join(self.output_dir, 'batch-costs.json')

        if not os.path.exists(state_file):
            return False

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            self.completed_runs = set(state.get('completed_runs', []))
            self.failed_runs = state.get('failed_runs', [])
            self.variations = state.get('variations', [])

            if state.get('start_time'):
                self.start_time = datetime.fromisoformat(state['start_time'])

            # Load cost state
            if os.path.exists(cost_file):
                self.cost_manager.load_from_file(cost_file)

            self.logger.info(f"Resumed batch state: {len(self.completed_runs)} runs completed")
            return True

        except Exception as e:
            self.logger.warning(f"Could not load batch state: {e}")
            return False

    def _run_single_scenario(
        self,
        run_id: str,
        variation: Dict[str, Any],
        run_number: int
    ) -> Dict[str, Any]:
        """
        Execute a single scenario run

        Args:
            run_id: Unique run identifier
            variation: Variation configuration
            run_number: Run number within variation

        Returns:
            Result dictionary with status, cost, metrics
        """
        result = {
            'run_id': run_id,
            'variation_id': variation['variation_id'],
            'run_number': run_number,
            'status': 'failed',
            'cost': 0.0,
            'error': None,
            'output_path': None
        }

        try:
            # Create temporary scenario with variation applied
            temp_dir = tempfile.mkdtemp(prefix='batch_scenario_')
            modified_scenario_path = self.variator.apply_variation_to_scenario(
                variation,
                temp_dir
            )

            # Determine output path
            output_path = os.path.join(self.runs_dir, run_id)
            os.makedirs(output_path, exist_ok=True)

            # Check budget before starting
            can_start, reason = self.cost_manager.can_start_run()
            if not can_start:
                result['error'] = reason
                result['status'] = 'budget_exceeded'
                self.logger.warning(f"⚠️  {run_id}: {reason}")
                return result

            # Run scenario
            self.logger.info(f"▶️  Starting {run_id}: {variation['description']}")

            # Pass cost_per_run_limit as credit_limit to scenario
            run_scenario(
                scenario_path=modified_scenario_path,
                output_path=output_path,
                credit_limit=self.cost_manager.cost_per_run_limit,
                verbose=False
            )

            # Read cost from completed run
            cost_file = os.path.join(output_path, 'costs.json')
            if os.path.exists(cost_file):
                with open(cost_file, 'r') as f:
                    cost_data = json.load(f)
                    run_cost = cost_data.get('total_cost', 0.0)
            else:
                run_cost = 0.0

            # Check if run cost exceeded limit
            within_limit, limit_reason = self.cost_manager.check_run_cost(run_cost)
            if not within_limit:
                result['status'] = 'cost_limit_exceeded'
                result['error'] = limit_reason
                result['cost'] = run_cost
                self.logger.warning(f"⚠️  {run_id}: {limit_reason}")
            else:
                result['status'] = 'success'
                result['cost'] = run_cost
                result['output_path'] = output_path
                self.logger.info(f"✓ {run_id}: Completed (${run_cost:.3f})")

            # Record cost
            self.cost_manager.record_run_cost(
                run_id=run_id,
                variation_id=variation['variation_id'],
                cost=run_cost,
                success=(result['status'] == 'success')
            )

            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'failed'
            self.logger.error(f"❌ {run_id}: Failed - {str(e)}")

        return result

    def show_batch_preview(self):
        """Show detailed preview of batch execution without running"""
        print("=" * 70)
        print(f"{'BATCH PREVIEW':^70}")
        print("=" * 70)
        print()

        # Experiment info
        print(f"📊 Experiment: {self.experiment_name}")
        if self.config.get('description'):
            print(f"   {self.config['description']}")
        print(f"📁 Base scenario: {self.base_scenario}")
        print()

        # Generate variations
        self.variations = self.variator.generate_variations()

        # Calculate total runs
        total_runs = len(self.variations) * self.runs_per_variation

        print(f"🔢 Variations: {len(self.variations)}")
        print(f"🔢 Runs per variation: {self.runs_per_variation}")
        print(f"🔢 Total runs: {total_runs}")
        print()

        # Execution mode
        if self.max_parallel > 1:
            print(f"⚡ Execution mode: Parallel ({self.max_parallel} concurrent runs)")
        else:
            print(f"⚡ Execution mode: Sequential")
        print()

        # Budget and limits
        if self.cost_manager.budget_limit:
            print(f"💰 Budget limit: ${self.cost_manager.budget_limit:.2f}")
        else:
            print(f"💰 Budget limit: None (unlimited)")

        if self.cost_manager.cost_per_run_limit:
            print(f"💰 Per-run cost limit: ${self.cost_manager.cost_per_run_limit:.2f}")
        print()

        # Cost estimation
        print("💵 Cost Estimation:")
        try:
            # Load scenario to get actor models
            from cost_tracker import CostTracker
            import yaml as yaml_lib
            scenario_file = os.path.join(self.base_scenario, 'scenario.yaml')
            with open(scenario_file, 'r') as f:
                scenario_config = yaml_lib.safe_load(f)

            # Get actor models (will be overridden by variations)
            actor_models = {}
            actors_dir = os.path.join(self.base_scenario, 'actors')
            if os.path.exists(actors_dir):
                for actor_file in os.listdir(actors_dir):
                    if actor_file.endswith('.yaml'):
                        actor_path = os.path.join(actors_dir, actor_file)
                        with open(actor_path, 'r') as f:
                            actor_config = yaml_lib.safe_load(f)
                            short_name = actor_config.get('short_name', actor_config.get('name', ''))
                            model = actor_config.get('llm_model', 'openai/gpt-4o-mini')
                            actor_models[short_name] = model

            num_actors = len(actor_models)
            num_turns = scenario_config.get('turns', 3)
            world_model = scenario_config.get('world_state_model', 'openai/gpt-4o-mini')

            # Estimate cost for one run using CostTracker
            cost_tracker = CostTracker()
            estimate = cost_tracker.estimate_scenario_cost(
                num_actors=num_actors,
                num_turns=num_turns,
                actor_models=actor_models,
                world_state_model=world_model
            )

            cost_per_run = estimate['total']
            total_estimated_cost = cost_per_run * total_runs

            print(f"   Per run (estimated): ${cost_per_run:.2f}")
            print(f"   Total (estimated): ${total_estimated_cost:.2f}")

            if self.cost_manager.budget_limit:
                if total_estimated_cost > self.cost_manager.budget_limit:
                    affordable_runs = int(self.cost_manager.budget_limit / cost_per_run)
                    print(f"   ⚠️  Estimated cost exceeds budget!")
                    print(f"   ⚠️  Budget allows ~{affordable_runs} runs (not {total_runs})")
                else:
                    budget_pct = (total_estimated_cost / self.cost_manager.budget_limit) * 100
                    print(f"   ✓ Within budget ({budget_pct:.1f}% of limit)")

        except Exception as e:
            print(f"   (Unable to estimate: {str(e)})")

        print()

        # Time estimation
        print("⏱️  Time Estimation:")
        avg_time_per_run = 3 * 60  # 3 minutes default
        if self.max_parallel > 1:
            # Parallel execution is faster
            total_time = (total_runs / self.max_parallel) * avg_time_per_run
        else:
            total_time = total_runs * avg_time_per_run

        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)

        print(f"   Estimated time: ", end="")
        if hours > 0:
            print(f"{hours}h {minutes}m")
        else:
            print(f"{minutes}m")

        print()

        # List all variations
        print("📋 Variations to be executed:")
        print()
        for i, variation in enumerate(self.variations, 1):
            print(f"   {i}. {variation['description']}")
            print(f"      Runs: {self.runs_per_variation}")

            # Show modifications
            mods = variation.get('modifications', {})
            if 'actor_models' in mods:
                for actor, model in mods['actor_models'].items():
                    print(f"      • {actor}: {model}")
            print()

        # Output location
        print(f"📁 Output directory: {self.output_dir}")
        print()

        # Summary
        print("=" * 70)
        print("To execute this batch, run without --dry-run flag:")
        print(f"  python src/batch_runner.py {self.config_path}")
        print("=" * 70)

    def run(self):
        """Execute the batch experiment"""
        # If dry-run mode, show preview and exit
        if self.dry_run:
            self.show_batch_preview()
            return

        # Choose execution mode based on max_parallel
        if self.max_parallel > 1:
            # Use parallel execution
            asyncio.run(self.run_parallel())
        else:
            # Use sequential execution
            self.run_sequential()

    def run_sequential(self):
        """Execute the batch experiment sequentially"""
        # Setup
        self._setup_output_directory()

        # Resume or start fresh
        if self.resume_mode:
            loaded = self._load_batch_state()
            if not loaded:
                self.logger.warning("No previous state found, starting fresh")
                self.resume_mode = False

        # Generate variations if not resuming
        if not self.resume_mode:
            self.variations = self.variator.generate_variations()

        # Calculate total runs
        total_runs = len(self.variations) * self.runs_per_variation

        # Initialize progress tracker
        progress_tracker = None
        if self.progress_display:
            progress_tracker = BatchProgressTracker(
                total_runs=total_runs,
                experiment_name=self.experiment_name,
                budget_limit=self.cost_manager.budget_limit
            )
            progress_tracker.start()
        else:
            # Traditional logging output
            self.logger.info("=" * 60)
            self.logger.info(f"🔬 Batch Experiment: {self.experiment_name}")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 Variations: {len(self.variations)}")
            self.logger.info(f"📊 Runs per variation: {self.runs_per_variation}")
            self.logger.info(f"📊 Total runs: {total_runs}")

            if self.cost_manager.budget_limit:
                self.logger.info(f"💰 Budget limit: ${self.cost_manager.budget_limit:.2f}")
            if self.cost_manager.cost_per_run_limit:
                self.logger.info(f"💰 Cost per run limit: ${self.cost_manager.cost_per_run_limit:.2f}")

            self.logger.info("")

        # Start tracking
        if not self.start_time:
            self.start_time = datetime.now()
            self.cost_manager.start_batch()

        # Execute runs sequentially (TODO: add parallelization)
        runs_executed = 0
        runs_skipped = 0

        try:
            for variation in self.variations:
                if not self.progress_display:
                    self.logger.info(f"\n📍 Variation {variation['variation_id']}/{len(self.variations)}: {variation['description']}")

                for run_num in range(1, self.runs_per_variation + 1):
                    run_id = self._generate_run_id(variation['variation_id'], run_num)

                    # Skip if already completed
                    if run_id in self.completed_runs:
                        runs_skipped += 1
                        if not self.progress_display:
                            self.logger.info(f"⏭️  {run_id}: Already completed (skipping)")
                        if progress_tracker:
                            # Still need to advance progress for skipped runs
                            progress_tracker.update_run_completed(run_id, 0.0, success=True)
                        continue

                    # Check budget before each run
                    can_continue, reason = self.cost_manager.can_start_run()
                    if not can_continue:
                        if not self.progress_display:
                            self.logger.warning(f"\n⚠️  Stopping batch: {reason}")
                        self._save_batch_state()
                        if progress_tracker:
                            progress_tracker.stop()
                        self._generate_summary()
                        return

                    # Notify progress tracker
                    if progress_tracker:
                        progress_tracker.update_run_started(run_id, variation['description'])

                    # Execute run
                    result = self._run_single_scenario(run_id, variation, run_num)

                    # Track result
                    success = (result['status'] == 'success')
                    if success:
                        self.completed_runs.add(run_id)
                    else:
                        self.failed_runs.append({
                            'run_id': run_id,
                            'error': result['error'],
                            'status': result['status']
                        })

                    runs_executed += 1

                    # Update progress tracker
                    if progress_tracker:
                        progress_tracker.update_run_completed(
                            run_id,
                            result['cost'],
                            success=success
                        )

                    # Save state periodically
                    if runs_executed % 5 == 0:
                        self._save_batch_state()

        finally:
            # Stop progress tracker
            if progress_tracker:
                progress_tracker.stop()

        # Complete
        self.end_time = datetime.now()
        self.cost_manager.end_batch()
        self._save_batch_state()

        # Generate summary
        if not self.progress_display:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ Batch execution completed")
            self.logger.info("=" * 60)
        self._generate_summary()

    def _generate_summary(self):
        """Generate and save batch summary"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()

        summary = {
            'experiment_name': self.experiment_name,
            'base_scenario': self.base_scenario,
            'total_variations': len(self.variations),
            'runs_per_variation': self.runs_per_variation,
            'total_runs_planned': len(self.variations) * self.runs_per_variation,
            'runs_completed': len(self.completed_runs),
            'runs_failed': len(self.failed_runs),
            'duration_seconds': duration,
            'cost_summary': self.cost_manager.get_summary(),
            'failed_runs': self.failed_runs
        }

        # Save JSON summary
        summary_file = os.path.join(self.output_dir, 'batch-summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print summary
        self.logger.info(f"\n📊 Runs completed: {summary['runs_completed']}/{summary['total_runs_planned']}")
        self.logger.info(f"❌ Runs failed: {summary['runs_failed']}")
        self.logger.info(f"💰 Total cost: ${self.cost_manager.total_spent:.2f}")

        if self.cost_manager.budget_limit:
            pct = (self.cost_manager.total_spent / self.cost_manager.budget_limit) * 100
            self.logger.info(f"💰 Budget used: {pct:.1f}%")

        if summary.get('duration_seconds'):
            minutes = summary['duration_seconds'] / 60
            self.logger.info(f"⏱️  Duration: {minutes:.1f} minutes")

        if summary['runs_completed'] > 0:
            avg = self.cost_manager.get_average_cost_per_run()
            self.logger.info(f"💰 Average per run: ${avg:.3f}")

        self.logger.info(f"\n📁 Results saved to: {self.output_dir}")
        self.logger.info(f"📄 Summary: {summary_file}")

    async def run_parallel(self):
        """Execute the batch experiment in parallel"""
        # Setup
        self._setup_output_directory()

        # Resume or start fresh
        if self.resume_mode:
            loaded = self._load_batch_state()
            if not loaded:
                self.logger.warning("No previous state found, starting fresh")
                self.resume_mode = False

        # Generate variations if not resuming
        if not self.resume_mode:
            self.variations = self.variator.generate_variations()

        # Calculate total runs
        total_runs = len(self.variations) * self.runs_per_variation

        # Initialize progress tracker
        progress_tracker = None
        if self.progress_display:
            progress_tracker = BatchProgressTracker(
                total_runs=total_runs,
                experiment_name=self.experiment_name,
                budget_limit=self.cost_manager.budget_limit
            )
            progress_tracker.start()
        else:
            # Traditional logging output
            self.logger.info("=" * 60)
            self.logger.info(f"🔬 Batch Experiment: {self.experiment_name} (Parallel)")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 Variations: {len(self.variations)}")
            self.logger.info(f"📊 Runs per variation: {self.runs_per_variation}")
            self.logger.info(f"📊 Total runs: {total_runs}")
            self.logger.info(f"🔀 Max parallel: {self.max_parallel}")

            if self.cost_manager.budget_limit:
                self.logger.info(f"💰 Budget limit: ${self.cost_manager.budget_limit:.2f}")
            if self.cost_manager.cost_per_run_limit:
                self.logger.info(f"💰 Cost per run limit: ${self.cost_manager.cost_per_run_limit:.2f}")

            self.logger.info("")

        # Start tracking
        if not self.start_time:
            self.start_time = datetime.now()
            self.cost_manager.start_batch()

        # Create parallel executor
        rate_limit_manager = RateLimitManager()
        executor = BatchParallelExecutor(
            max_parallel=self.max_parallel,
            rate_limit_manager=rate_limit_manager
        )

        # Collect all tasks to run
        tasks = []
        for variation in self.variations:
            for run_num in range(1, self.runs_per_variation + 1):
                run_id = self._generate_run_id(variation['variation_id'], run_num)

                # Skip if already completed
                if run_id in self.completed_runs:
                    continue

                tasks.append({
                    'run_id': run_id,
                    'variation': variation,
                    'run_num': run_num
                })

        try:
            # Process tasks with asyncio.gather
            async def run_task(task):
                run_id = task['run_id']
                variation = task['variation']
                run_num = task['run_num']

                # Check budget before each run
                can_continue, reason = self.cost_manager.can_start_run()
                if not can_continue:
                    return {'status': 'budget_exceeded', 'run_id': run_id}

                # Notify progress tracker
                if progress_tracker:
                    progress_tracker.update_run_started(run_id, variation['description'])

                # Execute run (using executor's rate-limited execution)
                async def execute_scenario_wrapper():
                    return self._run_single_scenario(run_id, variation, run_num)

                try:
                    result = await executor.execute_scenario(execute_scenario_wrapper)
                except Exception as e:
                    result = {
                        'run_id': run_id,
                        'status': 'failed',
                        'error': str(e),
                        'cost': 0.0
                    }

                # Track result
                success = (result.get('status') == 'success')
                if success:
                    self.completed_runs.add(run_id)
                else:
                    self.failed_runs.append({
                        'run_id': run_id,
                        'error': result.get('error'),
                        'status': result.get('status')
                    })

                # Update progress tracker
                if progress_tracker:
                    progress_tracker.update_run_completed(
                        run_id,
                        result.get('cost', 0.0),
                        success=success
                    )

                return result

            # Run all tasks in parallel (limited by semaphore)
            results = await asyncio.gather(*[run_task(task) for task in tasks])

            # Save state after all runs complete
            self._save_batch_state()

        finally:
            # Stop progress tracker
            if progress_tracker:
                progress_tracker.stop()

        # Complete
        self.end_time = datetime.now()
        self.cost_manager.end_batch()
        self._save_batch_state()

        # Generate summary
        if not self.progress_display:
            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ Batch execution completed")
            self.logger.info("=" * 60)
        self._generate_summary()


def main():
    """Command-line interface for batch runner"""
    parser = argparse.ArgumentParser(
        description='Run batch scenario experiments for statistical analysis'
    )
    parser.add_argument(
        'config',
        help='Path to batch configuration YAML file'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume incomplete batch execution'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable rich progress display (use simple logging instead)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show preview of what will be executed without running'
    )

    args = parser.parse_args()

    # Create and run batch
    batch_runner = BatchRunner(
        args.config,
        resume=args.resume,
        progress_display=not args.no_progress,
        dry_run=args.dry_run
    )
    batch_runner.run()


if __name__ == '__main__':
    main()
