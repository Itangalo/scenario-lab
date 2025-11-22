"""
Batch Executor - Execution logic for batch scenario runs

Handles sequential and parallel execution of scenario variations,
including single scenario runs, state persistence, and error handling.
"""
import os
import json
import asyncio
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from scenario_lab.batch.batch_config import BatchConfig
from scenario_lab.batch.parameter_variator import ParameterVariator
from scenario_lab.batch.batch_cost_manager import BatchCostManager
from scenario_lab.batch.batch_progress_tracker import BatchProgressTracker
from scenario_lab.runners.async_executor import run_scenario_async
from scenario_lab.utils.error_handler import (
    ErrorHandler,
    classify_error,
    ErrorSeverity
)
from scenario_lab.utils.memory_optimizer import get_memory_monitor, optimize_memory


class BatchExecutor:
    """
    Executes batch scenario runs

    Handles both sequential and parallel execution modes with:
    - State persistence for resumption
    - Cost tracking and budget enforcement
    - Progress tracking
    - Error handling with fallback strategies
    """

    def __init__(
        self,
        config: BatchConfig,
        variator: ParameterVariator,
        cost_manager: BatchCostManager,
        error_handler: ErrorHandler,
        progress_display: bool = True
    ):
        """
        Initialize batch executor

        Args:
            config: Batch configuration
            variator: Parameter variator for generating scenario variants
            cost_manager: Cost tracking and budget management
            error_handler: Error handling with user-friendly messages
            progress_display: Whether to show rich progress display
        """
        self.config = config
        self.variator = variator
        self.cost_manager = cost_manager
        self.error_handler = error_handler
        self.progress_display = progress_display

        # Logger
        self.logger = logging.getLogger("batch_executor")

        # Execution state
        self.variations: List[Dict[str, Any]] = []
        self.completed_runs: Set[str] = set()
        self.failed_runs: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def generate_run_id(self, variation_id: int, run_number: int) -> str:
        """
        Generate unique run identifier

        Args:
            variation_id: Variation number
            run_number: Run number within variation

        Returns:
            Run ID string (e.g., "var-001-run-003")
        """
        return f"var-{variation_id:03d}-run-{run_number:03d}"

    def save_state(self) -> None:
        """Save batch execution state for resumption"""
        state_file = os.path.join(self.config.output_dir, 'batch-state.json')
        cost_file = os.path.join(self.config.output_dir, 'batch-costs.json')

        state = {
            'experiment_name': self.config.experiment_name,
            'completed_runs': list(self.completed_runs),
            'failed_runs': self.failed_runs,
            'variations': self.variations,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Save cost state
        self.cost_manager.save_to_file(cost_file)

        self.logger.debug(f"Saved batch state: {len(self.completed_runs)} runs completed")

    def load_state(self) -> bool:
        """
        Load batch execution state from previous run

        Returns:
            True if state loaded successfully, False otherwise
        """
        state_file = os.path.join(self.config.output_dir, 'batch-state.json')
        cost_file = os.path.join(self.config.output_dir, 'batch-costs.json')

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

    async def run_single_scenario(
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
            output_path = os.path.join(self.config.runs_dir, run_id)
            os.makedirs(output_path, exist_ok=True)

            # Check budget before starting
            can_start, reason = self.cost_manager.can_start_run()
            if not can_start:
                result['error'] = reason
                result['status'] = 'budget_exceeded'
                self.logger.warning(f"  {run_id}: {reason}")
                return result

            # Run scenario using V2 async executor
            self.logger.info(f"  Starting {run_id}: {variation['description']}")

            final_state = await run_scenario_async(
                scenario_path=modified_scenario_path,
                output_path=output_path,
                credit_limit=self.cost_manager.cost_per_run_limit
            )

            # Get cost from final state
            run_cost = final_state.total_cost()

            # Check if run cost exceeded limit
            within_limit, limit_reason = self.cost_manager.check_run_cost(run_cost)
            if not within_limit:
                result['status'] = 'cost_limit_exceeded'
                result['error'] = limit_reason
                result['cost'] = run_cost
                self.logger.warning(f"  {run_id}: {limit_reason}")
            else:
                result['status'] = 'success'
                result['cost'] = run_cost
                result['output_path'] = output_path
                self.logger.info(f"  {run_id}: Completed (${run_cost:.3f})")

            # Record cost
            self.cost_manager.record_run_cost(
                run_id=run_id,
                variation_id=variation['variation_id'],
                cost=run_cost,
                success=(result['status'] == 'success')
            )

            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            # Memory optimization: periodic garbage collection every 10 runs
            if run_number % 10 == 0:
                optimize_memory()
                memory_monitor = get_memory_monitor()
                memory_monitor.check_memory(f"After run {run_number}")

        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'failed'

            # Create error context with full details
            error_context = classify_error(
                e,
                operation=f"Running scenario variation {variation['variation_id']}",
                scenario_name=self.config.base_scenario,
                run_number=run_number,
                cost_so_far=self.cost_manager.total_spent,
                additional_context={
                    'run_id': run_id,
                    'variation_description': variation.get('description', 'N/A'),
                    'completed_runs': len(self.completed_runs),
                    'total_runs': len(self.variations) * self.config.runs_per_variation
                }
            )

            # Handle error with user-friendly message (only for HIGH/FATAL severity)
            if error_context.severity in [ErrorSeverity.HIGH, ErrorSeverity.FATAL]:
                should_continue, recovery_actions = self.error_handler.handle_error(error_context)

                # For batch runs, we typically continue even on high severity
                # (single run failure shouldn't stop entire batch)
                if not should_continue and error_context.severity == ErrorSeverity.FATAL:
                    # FATAL errors should halt the entire batch
                    self.logger.error(f"  {run_id}: FATAL error - halting batch")
                    raise
            else:
                # Low/medium severity - just log
                self.logger.error(f"  {run_id}: Failed - {str(e)[:200]}")

        return result

    async def run_sequential(self, resume_mode: bool = False) -> None:
        """
        Execute the batch experiment sequentially

        Args:
            resume_mode: Whether to resume from previous state
        """
        # Resume or start fresh
        if resume_mode:
            loaded = self.load_state()
            if not loaded:
                self.logger.warning("No previous state found, starting fresh")

        # Generate variations if not resuming with existing variations
        if not self.variations:
            self.variations = self.variator.generate_variations()

        # Calculate total runs
        total_runs = len(self.variations) * self.config.runs_per_variation

        # Initialize progress tracker
        progress_tracker = None
        if self.progress_display:
            progress_tracker = BatchProgressTracker(
                total_runs=total_runs,
                experiment_name=self.config.experiment_name,
                budget_limit=self.cost_manager.budget_limit
            )
            progress_tracker.start()
        else:
            # Traditional logging output
            self.logger.info("=" * 60)
            self.logger.info(f"Batch Experiment: {self.config.experiment_name}")
            self.logger.info("=" * 60)
            self.logger.info(f"Variations: {len(self.variations)}")
            self.logger.info(f"Runs per variation: {self.config.runs_per_variation}")
            self.logger.info(f"Total runs: {total_runs}")

            if self.cost_manager.budget_limit:
                self.logger.info(f"Budget limit: ${self.cost_manager.budget_limit:.2f}")
            if self.cost_manager.cost_per_run_limit:
                self.logger.info(f"Cost per run limit: ${self.cost_manager.cost_per_run_limit:.2f}")

            self.logger.info("")

        # Start tracking
        if not self.start_time:
            self.start_time = datetime.now()
            self.cost_manager.start_batch()

        # Execute runs sequentially
        runs_executed = 0

        try:
            for variation in self.variations:
                if not self.progress_display:
                    self.logger.info(f"\nVariation {variation['variation_id']}/{len(self.variations)}: {variation['description']}")

                for run_num in range(1, self.config.runs_per_variation + 1):
                    run_id = self.generate_run_id(variation['variation_id'], run_num)

                    # Skip if already completed
                    if run_id in self.completed_runs:
                        if not self.progress_display:
                            self.logger.info(f"  {run_id}: Already completed (skipping)")
                        if progress_tracker:
                            # Still need to advance progress for skipped runs
                            progress_tracker.update_run_completed(run_id, 0.0, success=True)
                        continue

                    # Check budget before each run
                    can_continue, reason = self.cost_manager.can_start_run()
                    if not can_continue:
                        if not self.progress_display:
                            self.logger.warning(f"\nStopping batch: {reason}")
                        self.save_state()
                        if progress_tracker:
                            progress_tracker.stop()
                        return

                    # Notify progress tracker
                    if progress_tracker:
                        progress_tracker.update_run_started(run_id, variation['description'])

                    # Execute run
                    result = await self.run_single_scenario(run_id, variation, run_num)

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
                        self.save_state()

        finally:
            # Stop progress tracker
            if progress_tracker:
                progress_tracker.stop()

        # Complete
        self.end_time = datetime.now()
        self.cost_manager.end_batch()
        self.save_state()

    async def run_parallel(self, resume_mode: bool = False) -> None:
        """
        Execute the batch experiment in parallel

        Args:
            resume_mode: Whether to resume from previous state
        """
        # Resume or start fresh
        if resume_mode:
            loaded = self.load_state()
            if not loaded:
                self.logger.warning("No previous state found, starting fresh")

        # Generate variations if not resuming
        if not self.variations:
            self.variations = self.variator.generate_variations()

        # Calculate total runs
        total_runs = len(self.variations) * self.config.runs_per_variation

        # Initialize progress tracker
        progress_tracker = None
        if self.progress_display:
            progress_tracker = BatchProgressTracker(
                total_runs=total_runs,
                experiment_name=self.config.experiment_name,
                budget_limit=self.cost_manager.budget_limit
            )
            progress_tracker.start()
        else:
            # Traditional logging output
            self.logger.info("=" * 60)
            self.logger.info(f"Batch Experiment: {self.config.experiment_name} (Parallel)")
            self.logger.info("=" * 60)
            self.logger.info(f"Variations: {len(self.variations)}")
            self.logger.info(f"Runs per variation: {self.config.runs_per_variation}")
            self.logger.info(f"Total runs: {total_runs}")
            self.logger.info(f"Max parallel: {self.config.max_parallel}")

            if self.cost_manager.budget_limit:
                self.logger.info(f"Budget limit: ${self.cost_manager.budget_limit:.2f}")
            if self.cost_manager.cost_per_run_limit:
                self.logger.info(f"Cost per run limit: ${self.cost_manager.cost_per_run_limit:.2f}")

            self.logger.info("")

        # Start tracking
        if not self.start_time:
            self.start_time = datetime.now()
            self.cost_manager.start_batch()

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.config.max_parallel)

        # Collect all tasks to run
        tasks = []
        for variation in self.variations:
            for run_num in range(1, self.config.runs_per_variation + 1):
                run_id = self.generate_run_id(variation['variation_id'], run_num)

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
                # Use semaphore to limit concurrency
                async with semaphore:
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

                    # Execute run directly (already async)
                    try:
                        result = await self.run_single_scenario(run_id, variation, run_num)
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
            await asyncio.gather(*[run_task(task) for task in tasks])

            # Save state after all runs complete
            self.save_state()

        finally:
            # Stop progress tracker
            if progress_tracker:
                progress_tracker.stop()

        # Complete
        self.end_time = datetime.now()
        self.cost_manager.end_batch()
        self.save_state()
