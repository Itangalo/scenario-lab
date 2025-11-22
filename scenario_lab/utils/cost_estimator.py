"""
Cost estimation for Scenario Lab

Estimates costs before running scenarios based on configuration.
Supports historical data analysis for more accurate projections.
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field
import json
import logging

from scenario_lab.schemas import (
    ScenarioConfig,
    ActorConfig,
    MetricsConfig,
    ValidationConfig,
    load_and_validate_scenario,
    load_and_validate_actor,
    load_and_validate_metrics,
    load_and_validate_validation_rules,
)
from scenario_lab.utils.model_pricing import estimate_cost, is_free_model, is_expensive_model

logger = logging.getLogger(__name__)


@dataclass
class HistoricalCostData:
    """Aggregated historical cost data from previous runs"""
    run_count: int = 0
    avg_cost_per_turn: float = 0.0
    avg_tokens_per_decision: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # actor -> (input, output)
    avg_tokens_per_world_update: Tuple[int, int] = (0, 0)  # (input, output)
    total_historical_cost: float = 0.0


@dataclass
class CostEstimate:
    """Cost estimate for a scenario run"""
    total_cost: float
    per_turn_cost: float
    actor_costs: Dict[str, float]
    world_state_cost: float
    communication_cost: float
    metrics_cost: float
    validation_cost: float
    warnings: List[str]
    historical_data_used: bool = False


class CostEstimator:
    """
    Estimates scenario execution costs

    Uses conservative estimates based on:
    - Scenario configuration (turns, actors, settings)
    - Model pricing
    - Estimated token counts
    - Historical data from previous runs (when available)
    """

    # Token estimation constants (conservative estimates, used as fallback)
    BASE_SYSTEM_PROMPT_TOKENS = 500
    BASE_WORLD_STATE_TOKENS = 1000
    CONTEXT_TOKENS_PER_TURN = 300
    DECISION_OUTPUT_TOKENS = 400
    WORLD_STATE_OUTPUT_TOKENS = 600
    COMMUNICATION_INPUT_TOKENS = 800
    COMMUNICATION_OUTPUT_TOKENS = 300
    METRIC_LLM_INPUT_TOKENS = 500
    METRIC_LLM_OUTPUT_TOKENS = 50
    VALIDATION_INPUT_TOKENS = 1500
    VALIDATION_OUTPUT_TOKENS = 200

    def __init__(self, scenario_path: Path):
        """
        Initialize cost estimator

        Args:
            scenario_path: Path to scenario directory
        """
        self.scenario_path = scenario_path
        self.scenario_config: Optional[ScenarioConfig] = None
        self.actor_configs: Dict[str, ActorConfig] = {}
        self.metrics_config: Optional[MetricsConfig] = None
        self.validation_config: Optional[ValidationConfig] = None
        self.warnings: List[str] = []
        self.historical_data: Optional[HistoricalCostData] = None

    def load_configs(self) -> bool:
        """
        Load scenario configurations

        Returns:
            True if all required configs loaded successfully
        """
        # Load scenario.yaml
        scenario_file = self.scenario_path / "scenario.yaml"
        config, result = load_and_validate_scenario(scenario_file)
        if not result.success:
            self.warnings.append("Failed to load scenario.yaml")
            return False

        self.scenario_config = config

        # Load actors
        actors_dir = self.scenario_path / "actors"
        if actors_dir.exists():
            for actor_name in self.scenario_config.actors:
                actor_file = actors_dir / f"{actor_name}.yaml"
                if actor_file.exists():
                    actor_config, result = load_and_validate_actor(actor_file)
                    if result.success:
                        self.actor_configs[actor_name] = actor_config
                    else:
                        self.warnings.append(f"Failed to load {actor_name}.yaml")

        # Load optional configs
        metrics_file = self.scenario_path / "metrics.yaml"
        if metrics_file.exists():
            config, result = load_and_validate_metrics(metrics_file)
            if result.success:
                self.metrics_config = config

        validation_file = self.scenario_path / "validation-rules.yaml"
        if validation_file.exists():
            config, result = load_and_validate_validation_rules(validation_file)
            if result.success:
                self.validation_config = config

        # Load historical data from previous runs
        self.historical_data = self._load_historical_data()

        return True

    def _load_historical_data(self) -> Optional[HistoricalCostData]:
        """
        Load and aggregate historical cost data from previous runs

        Scans the runs/ directory for scenario-state-v2.json files
        and extracts cost information to improve estimates.

        Returns:
            HistoricalCostData if runs exist, None otherwise
        """
        runs_dir = self.scenario_path / "runs"
        if not runs_dir.exists():
            return None

        # Find all state files
        state_files = list(runs_dir.glob("*/scenario-state-v2.json"))
        if not state_files:
            return None

        historical = HistoricalCostData()
        all_costs_by_actor: Dict[str, List[Tuple[int, int]]] = {}  # actor -> list of (input, output)
        all_world_update_tokens: List[Tuple[int, int]] = []
        total_turns = 0

        for state_file in state_files:
            try:
                with open(state_file, "r") as f:
                    state_dict = json.load(f)

                # Skip if version doesn't match
                version = state_dict.get("version", "1.0")
                if not version.startswith("2."):
                    continue

                historical.run_count += 1
                run_turns = state_dict.get("turn", 0)
                total_turns += run_turns

                # Extract cost records
                costs = state_dict.get("costs", [])
                run_cost = 0.0

                for cost in costs:
                    run_cost += cost.get("cost", 0.0)
                    phase = cost.get("phase", "")
                    actor = cost.get("actor", "")
                    input_tokens = cost.get("input_tokens", 0)
                    output_tokens = cost.get("output_tokens", 0)

                    if phase == "decision" and actor:
                        if actor not in all_costs_by_actor:
                            all_costs_by_actor[actor] = []
                        all_costs_by_actor[actor].append((input_tokens, output_tokens))
                    elif phase == "world_update":
                        all_world_update_tokens.append((input_tokens, output_tokens))

                historical.total_historical_cost += run_cost

            except (json.JSONDecodeError, KeyError, IOError) as e:
                logger.debug(f"Failed to load state file {state_file}: {e}")
                continue

        if historical.run_count == 0:
            return None

        # Calculate averages
        if total_turns > 0:
            historical.avg_cost_per_turn = historical.total_historical_cost / total_turns

        # Average tokens per actor decision
        for actor, token_list in all_costs_by_actor.items():
            if token_list:
                avg_input = sum(t[0] for t in token_list) // len(token_list)
                avg_output = sum(t[1] for t in token_list) // len(token_list)
                historical.avg_tokens_per_decision[actor] = (avg_input, avg_output)

        # Average tokens per world update
        if all_world_update_tokens:
            avg_input = sum(t[0] for t in all_world_update_tokens) // len(all_world_update_tokens)
            avg_output = sum(t[1] for t in all_world_update_tokens) // len(all_world_update_tokens)
            historical.avg_tokens_per_world_update = (avg_input, avg_output)

        logger.info(
            f"Loaded historical data from {historical.run_count} runs "
            f"(avg ${historical.avg_cost_per_turn:.4f}/turn)"
        )

        return historical

    def estimate(self, end_turn: Optional[int] = None) -> CostEstimate:
        """
        Estimate costs for scenario execution

        Args:
            end_turn: Override number of turns to execute (uses scenario default if None)

        Returns:
            CostEstimate with detailed breakdown
        """
        if not self.scenario_config:
            if not self.load_configs():
                return CostEstimate(
                    total_cost=0.0,
                    per_turn_cost=0.0,
                    actor_costs={},
                    world_state_cost=0.0,
                    communication_cost=0.0,
                    metrics_cost=0.0,
                    validation_cost=0.0,
                    warnings=self.warnings,
                )

        # Determine number of turns
        turns = end_turn or self.scenario_config.turns or 10

        # Estimate per-actor costs
        actor_costs = {}
        for actor_name, actor_config in self.actor_configs.items():
            cost = self._estimate_actor_cost(actor_config, turns)
            actor_costs[actor_name] = cost

        # Estimate world state cost
        world_state_cost = self._estimate_world_state_cost(turns)

        # Estimate communication cost
        communication_cost = self._estimate_communication_cost(turns)

        # Estimate metrics cost
        metrics_cost = self._estimate_metrics_cost(turns)

        # Estimate validation cost
        validation_cost = self._estimate_validation_cost(turns)

        # Calculate totals
        total_cost = (
            sum(actor_costs.values())
            + world_state_cost
            + communication_cost
            + metrics_cost
            + validation_cost
        )
        per_turn_cost = total_cost / turns if turns > 0 else 0.0

        # Add warnings
        self._add_cost_warnings(total_cost, actor_costs)

        # Note if historical data was used
        historical_used = self.historical_data is not None
        if historical_used:
            self.warnings.append(
                f"Estimate improved using historical data from {self.historical_data.run_count} previous runs"
            )

        return CostEstimate(
            total_cost=total_cost,
            per_turn_cost=per_turn_cost,
            actor_costs=actor_costs,
            world_state_cost=world_state_cost,
            communication_cost=communication_cost,
            metrics_cost=metrics_cost,
            validation_cost=validation_cost,
            warnings=self.warnings,
            historical_data_used=historical_used,
        )

    def _estimate_actor_cost(self, actor: ActorConfig, turns: int) -> float:
        """Estimate cost for a single actor across all turns

        Uses historical data when available, falls back to conservative estimates.
        """
        model = actor.llm_model or "openai/gpt-4o-mini"
        actor_name = actor.name

        # Check if we have historical data for this actor
        if (
            self.historical_data is not None
            and actor_name in self.historical_data.avg_tokens_per_decision
        ):
            # Use historical averages
            hist_input, hist_output = self.historical_data.avg_tokens_per_decision[actor_name]
            input_tokens = hist_input
            output_tokens = hist_output
        else:
            # Fall back to conservative estimates
            # System prompt + world state + context + goals
            input_tokens = (
                self.BASE_SYSTEM_PROMPT_TOKENS +
                self.BASE_WORLD_STATE_TOKENS +
                (self.CONTEXT_TOKENS_PER_TURN * min(turns, self.scenario_config.context_window_size or 3))
            )
            output_tokens = self.DECISION_OUTPUT_TOKENS

        # Calculate cost per turn
        cost_per_turn = estimate_cost(input_tokens, output_tokens, model)

        # Total cost
        return cost_per_turn * turns

    def _estimate_world_state_cost(self, turns: int) -> float:
        """Estimate cost for world state updates

        Uses historical data when available, falls back to conservative estimates.
        """
        model = self.scenario_config.world_state_model or "openai/gpt-4o-mini"

        # Check if we have historical data for world updates
        if (
            self.historical_data is not None
            and self.historical_data.avg_tokens_per_world_update[0] > 0
        ):
            # Use historical averages
            input_tokens, output_tokens = self.historical_data.avg_tokens_per_world_update
        else:
            # Fall back to conservative estimates
            # Input: current state + all actor decisions + context
            num_actors = len(self.actor_configs)
            input_tokens = (
                self.BASE_WORLD_STATE_TOKENS +
                (num_actors * self.DECISION_OUTPUT_TOKENS) +
                (self.CONTEXT_TOKENS_PER_TURN * 2)
            )
            output_tokens = self.WORLD_STATE_OUTPUT_TOKENS

        cost_per_turn = estimate_cost(input_tokens, output_tokens, model)
        return cost_per_turn * turns

    def _estimate_communication_cost(self, turns: int) -> float:
        """Estimate cost for communications

        Note: The communication phase is currently a stub implementation (Phase 2.2)
        that does NOT make LLM calls. It only logs and exports existing communications.
        Therefore, communication cost is always 0 until the full implementation is added.

        When the communication phase is fully implemented (prompting actors to
        initiate communications, handling negotiations, etc.), this method should
        be updated to estimate those costs.
        """
        # Communication phase is a stub - no LLM calls are made
        # See scenario_lab/services/communication_phase.py
        #
        # The phase currently only:
        # - Logs existing communications
        # - Exports them to files
        #
        # It does NOT prompt actors to create communications (no LLM calls)
        return 0.0

    def _estimate_metrics_cost(self, turns: int) -> float:
        """Estimate cost for metrics extraction"""
        if not self.metrics_config:
            return 0.0

        # Count LLM-extracted metrics
        llm_metrics = [
            m for m in self.metrics_config.metrics
            if m.extraction.type == "llm"
        ]

        if not llm_metrics:
            return 0.0

        # Use default metrics extraction model
        model = "openai/gpt-4o-mini"

        cost_per_metric = estimate_cost(
            self.METRIC_LLM_INPUT_TOKENS,
            self.METRIC_LLM_OUTPUT_TOKENS,
            model
        )

        return cost_per_metric * len(llm_metrics) * turns

    def _estimate_validation_cost(self, turns: int) -> float:
        """Estimate cost for QA validation"""
        if not self.validation_config or not self.validation_config.run_after_each_turn:
            return 0.0

        # Count enabled validation checks
        enabled_checks = sum(
            1 for check in self.validation_config.checks.values()
            if check.enabled
        )

        if enabled_checks == 0:
            return 0.0

        model = self.validation_config.validation_model or "openai/gpt-4o-mini"

        cost_per_check = estimate_cost(
            self.VALIDATION_INPUT_TOKENS,
            self.VALIDATION_OUTPUT_TOKENS,
            model
        )

        return cost_per_check * enabled_checks * turns

    def _add_cost_warnings(self, total_cost: float, actor_costs: Dict[str, float]):
        """Add warnings based on costs"""
        # Warn if total cost is high
        if total_cost > 50.0:
            self.warnings.append(
                f"High estimated cost (${total_cost:.2f}) - consider reducing turns or using cheaper models"
            )
        elif total_cost > 10.0:
            self.warnings.append(
                f"Moderate estimated cost (${total_cost:.2f}) - monitor spending during execution"
            )

        # Warn about expensive models
        for actor_name, actor_config in self.actor_configs.items():
            model = actor_config.llm_model or "openai/gpt-4o-mini"
            if is_expensive_model(model):
                cost = actor_costs.get(actor_name, 0.0)
                self.warnings.append(
                    f"Actor '{actor_name}' uses expensive model ({model}) - estimated ${cost:.2f}"
                )

        # Note if using free models
        free_models = [
            actor_name for actor_name, actor_config in self.actor_configs.items()
            if is_free_model(actor_config.llm_model or "")
        ]
        if free_models:
            self.warnings.append(
                f"Actors using free/local models: {', '.join(free_models)} (zero cost)"
            )
