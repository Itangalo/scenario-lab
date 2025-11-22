"""
Batch Dry Run - Preview mode for batch execution

Displays detailed preview of what will be executed without actually running,
including cost and time estimations.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from scenario_lab.batch.batch_config import BatchConfig
from scenario_lab.batch.parameter_variator import ParameterVariator
from scenario_lab.batch.batch_cost_manager import BatchCostManager
from scenario_lab.utils.cost_estimator import CostEstimator


class BatchDryRun:
    """
    Dry-run preview for batch execution

    Shows detailed preview of what will be executed including:
    - Experiment and scenario information
    - Variation listing
    - Cost and time estimations
    - Budget analysis
    """

    def __init__(
        self,
        config: BatchConfig,
        variator: ParameterVariator,
        cost_manager: BatchCostManager
    ):
        """
        Initialize dry-run preview

        Args:
            config: Batch configuration
            variator: Parameter variator for generating variations
            cost_manager: Cost manager for budget information
        """
        self.config = config
        self.variator = variator
        self.cost_manager = cost_manager

    def show_preview(self) -> None:
        """Display detailed preview of batch execution"""
        print("=" * 70)
        print(f"{'BATCH PREVIEW':^70}")
        print("=" * 70)
        print()

        # Experiment info
        self._show_experiment_info()

        # Generate and show variations
        variations = self.variator.generate_variations()
        total_runs = len(variations) * self.config.runs_per_variation

        self._show_run_summary(variations, total_runs)
        self._show_execution_mode()
        self._show_budget_limits()
        self._show_cost_estimation(variations, total_runs)
        self._show_time_estimation(total_runs)
        self._show_variations_list(variations)
        self._show_output_info()
        self._show_execution_instructions()

    def _show_experiment_info(self) -> None:
        """Display experiment information"""
        print(f"Experiment: {self.config.experiment_name}")
        if self.config.description:
            print(f"   {self.config.description}")
        print(f"Base scenario: {self.config.base_scenario}")
        print()

    def _show_run_summary(self, variations: List[Dict[str, Any]], total_runs: int) -> None:
        """Display run count summary"""
        print(f"Variations: {len(variations)}")
        print(f"Runs per variation: {self.config.runs_per_variation}")
        print(f"Total runs: {total_runs}")
        print()

    def _show_execution_mode(self) -> None:
        """Display execution mode"""
        if self.config.max_parallel > 1:
            print(f"Execution mode: Parallel ({self.config.max_parallel} concurrent runs)")
        else:
            print(f"Execution mode: Sequential")
        print()

    def _show_budget_limits(self) -> None:
        """Display budget limits"""
        if self.cost_manager.budget_limit:
            print(f"Budget limit: ${self.cost_manager.budget_limit:.2f}")
        else:
            print(f"Budget limit: None (unlimited)")

        if self.cost_manager.cost_per_run_limit:
            print(f"Per-run cost limit: ${self.cost_manager.cost_per_run_limit:.2f}")
        print()

    def _show_cost_estimation(self, variations: List[Dict[str, Any]], total_runs: int) -> None:
        """Display cost estimation"""
        print("Cost Estimation:")
        try:
            cost_per_run, total_estimated_cost = self._estimate_costs(total_runs)

            print(f"   Per run (estimated): ${cost_per_run:.2f}")
            print(f"   Total (estimated): ${total_estimated_cost:.2f}")

            if self.cost_manager.budget_limit:
                self._show_budget_analysis(cost_per_run, total_estimated_cost, total_runs)

        except Exception as e:
            print(f"   (Unable to estimate: {str(e)})")

        print()

    def _estimate_costs(self, total_runs: int) -> tuple:
        """
        Estimate costs for the batch

        Returns:
            Tuple of (cost_per_run, total_estimated_cost)
        """
        estimator = CostEstimator(Path(self.config.base_scenario))
        scenario_file = os.path.join(self.config.base_scenario, 'scenario.yaml')

        with open(scenario_file, 'r') as f:
            scenario_config = yaml.safe_load(f)

        # Get actor models
        actor_models = self._get_actor_models()

        num_actors = len(actor_models)
        num_turns = scenario_config.get('turns', 3)
        world_model = scenario_config.get('world_state_model', 'openai/gpt-4o-mini')

        # Estimate cost using CostEstimator
        estimate = estimator.estimate_scenario_cost(
            num_actors=num_actors,
            num_turns=num_turns,
            actor_models=list(actor_models.values()),
            world_state_model=world_model
        )

        cost_per_run = estimate['total']
        total_estimated_cost = cost_per_run * total_runs

        return cost_per_run, total_estimated_cost

    def _get_actor_models(self) -> Dict[str, str]:
        """Get actor models from scenario configuration"""
        actor_models = {}
        actors_dir = os.path.join(self.config.base_scenario, 'actors')

        if os.path.exists(actors_dir):
            for actor_file in os.listdir(actors_dir):
                if actor_file.endswith('.yaml'):
                    actor_path = os.path.join(actors_dir, actor_file)
                    with open(actor_path, 'r') as f:
                        actor_config = yaml.safe_load(f)
                        short_name = actor_config.get('short_name', actor_config.get('name', ''))
                        model = actor_config.get('llm_model', 'openai/gpt-4o-mini')
                        actor_models[short_name] = model

        return actor_models

    def _show_budget_analysis(
        self,
        cost_per_run: float,
        total_estimated_cost: float,
        total_runs: int
    ) -> None:
        """Display budget analysis based on estimates"""
        if total_estimated_cost > self.cost_manager.budget_limit:
            affordable_runs = int(self.cost_manager.budget_limit / cost_per_run)
            print(f"   WARNING: Estimated cost exceeds budget!")
            print(f"   WARNING: Budget allows ~{affordable_runs} runs (not {total_runs})")
        else:
            budget_pct = (total_estimated_cost / self.cost_manager.budget_limit) * 100
            print(f"   Within budget ({budget_pct:.1f}% of limit)")

    def _show_time_estimation(self, total_runs: int) -> None:
        """Display time estimation"""
        print("Time Estimation:")
        avg_time_per_run = 3 * 60  # 3 minutes default

        if self.config.max_parallel > 1:
            # Parallel execution is faster
            total_time = (total_runs / self.config.max_parallel) * avg_time_per_run
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

    def _show_variations_list(self, variations: List[Dict[str, Any]]) -> None:
        """Display list of variations to be executed"""
        print("Variations to be executed:")
        print()

        for i, variation in enumerate(variations, 1):
            print(f"   {i}. {variation['description']}")
            print(f"      Runs: {self.config.runs_per_variation}")

            # Show modifications
            mods = variation.get('modifications', {})
            if 'actor_models' in mods:
                for actor, model in mods['actor_models'].items():
                    print(f"      - {actor}: {model}")
            print()

    def _show_output_info(self) -> None:
        """Display output location"""
        print(f"Output directory: {self.config.output_dir}")
        print()

    def _show_execution_instructions(self) -> None:
        """Display instructions for running the batch"""
        print("=" * 70)
        print("To execute this batch, run without --dry-run flag:")
        print(f"  scenario-lab run-batch <config-file>")
        print("=" * 70)


def show_batch_preview(
    config: BatchConfig,
    variator: ParameterVariator,
    cost_manager: BatchCostManager
) -> None:
    """
    Convenience function to show batch preview

    Args:
        config: Batch configuration
        variator: Parameter variator
        cost_manager: Cost manager
    """
    dry_run = BatchDryRun(config, variator, cost_manager)
    dry_run.show_preview()
