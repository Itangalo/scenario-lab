"""
Cost estimation for Scenario Lab

Estimates costs before running scenarios based on configuration.
"""
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

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


class CostEstimator:
    """
    Estimates scenario execution costs

    Uses conservative estimates based on:
    - Scenario configuration (turns, actors, settings)
    - Model pricing
    - Estimated token counts
    """

    # Token estimation constants (conservative estimates)
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

        return True

    def estimate(self, max_turns: Optional[int] = None) -> CostEstimate:
        """
        Estimate costs for scenario execution

        Args:
            max_turns: Override number of turns (uses scenario default if None)

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
        turns = max_turns or self.scenario_config.turns or 10

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

        return CostEstimate(
            total_cost=total_cost,
            per_turn_cost=per_turn_cost,
            actor_costs=actor_costs,
            world_state_cost=world_state_cost,
            communication_cost=communication_cost,
            metrics_cost=metrics_cost,
            validation_cost=validation_cost,
            warnings=self.warnings,
        )

    def _estimate_actor_cost(self, actor: ActorConfig, turns: int) -> float:
        """Estimate cost for a single actor across all turns"""
        model = actor.llm_model or "openai/gpt-4o-mini"

        # Estimate input tokens per turn
        # System prompt + world state + context + goals
        input_tokens = (
            self.BASE_SYSTEM_PROMPT_TOKENS +
            self.BASE_WORLD_STATE_TOKENS +
            (self.CONTEXT_TOKENS_PER_TURN * min(turns, self.scenario_config.context_window_size or 3))
        )

        # Output tokens per turn (decision)
        output_tokens = self.DECISION_OUTPUT_TOKENS

        # Calculate cost per turn
        cost_per_turn = estimate_cost(input_tokens, output_tokens, model)

        # Total cost
        return cost_per_turn * turns

    def _estimate_world_state_cost(self, turns: int) -> float:
        """Estimate cost for world state updates"""
        model = self.scenario_config.world_state_model or "openai/gpt-4o-mini"

        # Input: current state + all actor decisions + context
        num_actors = len(self.actor_configs)
        input_tokens = (
            self.BASE_WORLD_STATE_TOKENS +
            (num_actors * self.DECISION_OUTPUT_TOKENS) +
            (self.CONTEXT_TOKENS_PER_TURN * 2)
        )

        # Output: updated world state
        output_tokens = self.WORLD_STATE_OUTPUT_TOKENS

        cost_per_turn = estimate_cost(input_tokens, output_tokens, model)
        return cost_per_turn * turns

    def _estimate_communication_cost(self, turns: int) -> float:
        """Estimate cost for communications (if enabled)"""
        if not self.scenario_config.enable_bilateral_communication:
            return 0.0

        # Conservative estimate: 1 communication per actor per turn
        num_actors = len(self.actor_configs)
        comms_per_turn = num_actors * (self.scenario_config.max_communications_per_turn or 1)

        # Each communication involves LLM calls
        # Assume actors use their own models for communication decisions
        total_cost = 0.0
        for actor_config in self.actor_configs.values():
            model = actor_config.llm_model or "openai/gpt-4o-mini"
            cost_per_comm = estimate_cost(
                self.COMMUNICATION_INPUT_TOKENS,
                self.COMMUNICATION_OUTPUT_TOKENS,
                model
            )
            total_cost += cost_per_comm * (comms_per_turn / num_actors) * turns

        return total_cost

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
