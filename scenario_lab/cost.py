"""Cost tracking and reporting for LLM API calls."""

from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

from .pricing import DEFAULT_PRICING, get_pricing_cache


@dataclass
class TokenUsage:
    """Token usage from a single LLM call."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str

    @property
    def tokens(self) -> int:
        """Convenience property for total tokens."""
        return self.total_tokens


@dataclass
class CostDetails:
    """Cost calculation for a single LLM call."""

    usage: TokenUsage
    prompt_cost_usd: float
    completion_cost_usd: float
    total_cost_usd: float

    @property
    def cost_usd(self) -> float:
        """Convenience property for total cost."""
        return self.total_cost_usd


@dataclass
class TaskCosts:
    """Aggregated costs for a task (events, actor:X, rules, metrics, summary)."""

    task_name: str
    calls: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost_usd: float = 0.0
    by_model: dict = field(default_factory=dict)

    def add_call(self, cost: CostDetails):
        """Add a call's costs to this task."""
        self.calls += 1
        self.total_tokens += cost.usage.total_tokens
        self.prompt_tokens += cost.usage.prompt_tokens
        self.completion_tokens += cost.usage.completion_tokens
        self.total_cost_usd += cost.total_cost_usd

        # Track by model
        model = cost.usage.model
        if model not in self.by_model:
            self.by_model[model] = {
                "calls": 0,
                "tokens": 0,
                "cost_usd": 0.0,
            }
        self.by_model[model]["calls"] += 1
        self.by_model[model]["tokens"] += cost.usage.total_tokens
        self.by_model[model]["cost_usd"] += cost.total_cost_usd


@dataclass
class TurnCosts:
    """Aggregated costs for a single turn."""

    turn: int
    by_task: dict = field(default_factory=dict)  # task_name -> TaskCosts
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def add_call(self, task_name: str, cost: CostDetails):
        """Add a call to this turn."""
        if task_name not in self.by_task:
            self.by_task[task_name] = TaskCosts(task_name=task_name)

        self.by_task[task_name].add_call(cost)
        self.total_tokens += cost.usage.total_tokens
        self.total_cost_usd += cost.total_cost_usd


@dataclass
class RunCosts:
    """Complete cost summary for a run."""

    by_turn: dict = field(default_factory=dict)  # turn -> TurnCosts
    by_task_aggregated: dict = field(default_factory=dict)  # task -> TaskCosts (across all turns)
    by_model: dict = field(default_factory=dict)  # model -> {calls, tokens, cost}
    total_tokens: int = 0
    total_cost_usd: float = 0.0


class CostCalculator:
    """Calculate costs from token usage."""

    _unknown_models_warned = set()  # Track which unknown models we've warned about
    _pricing_cache = get_pricing_cache()

    @staticmethod
    def normalize_model_name(model: str) -> str:
        """Normalize model name for pricing lookup.

        Handles cases where model might have variants or suffixes.

        Args:
            model: Model name from API response

        Returns:
            Normalized model name
        """
        # Remove :free suffix and other variations
        if ":" in model:
            base_model = model.split(":")[0]
            # Keep the full model id when the cache knows that exact variant.
            if CostCalculator._pricing_cache.get_model_pricing(model) is not None:
                return model
            return base_model

        return model

    @staticmethod
    def get_model_pricing(model: str) -> dict:
        """Get pricing for a model.

        Args:
            model: Model name

        Returns:
            Dict with "prompt" and "completion" pricing per million tokens
        """
        normalized = CostCalculator.normalize_model_name(model)
        pricing = CostCalculator._pricing_cache.get_model_pricing(normalized)
        if pricing is not None:
            return pricing

        # Fall back to default and warn once
        if normalized not in CostCalculator._unknown_models_warned:
            print(
                f"  ⚠️  Could not load OpenRouter pricing for '{normalized}' "
                f"- using default (${DEFAULT_PRICING['prompt']}/{DEFAULT_PRICING['completion']} per 1M tokens)"
            )
            CostCalculator._unknown_models_warned.add(normalized)

        return dict(DEFAULT_PRICING)

    @staticmethod
    def calculate_cost(usage: TokenUsage) -> CostDetails:
        """Calculate cost from token usage.

        Args:
            usage: Token usage from LLM call

        Returns:
            CostDetails with calculated costs
        """
        pricing = CostCalculator.get_model_pricing(usage.model)

        # Convert to cost (pricing is per million tokens)
        prompt_cost = (usage.prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1_000_000) * pricing["completion"]

        return CostDetails(
            usage=usage,
            prompt_cost_usd=prompt_cost,
            completion_cost_usd=completion_cost,
            total_cost_usd=prompt_cost + completion_cost,
        )


class CostTracker:
    """Track and aggregate costs across turns and tasks."""

    def __init__(self):
        """Initialize cost tracker."""
        self.turns: dict[int, TurnCosts] = {}

    def record_call(self, turn: int, task_name: str, cost: CostDetails):
        """Record a single LLM call.

        Args:
            turn: Turn number
            task_name: Task identifier (e.g., "events", "actor:government", "rules")
            cost: Cost details for the call
        """
        # Create turn if doesn't exist
        if turn not in self.turns:
            self.turns[turn] = TurnCosts(turn=turn)

        # Add to turn
        self.turns[turn].add_call(task_name, cost)

    def get_turn_costs(self, turn: int) -> Optional[TurnCosts]:
        """Get costs for a specific turn.

        Args:
            turn: Turn number

        Returns:
            TurnCosts or None if turn not found
        """
        return self.turns.get(turn)

    def get_run_costs(self) -> RunCosts:
        """Get complete run cost summary.

        Returns:
            RunCosts with all aggregations
        """
        run_costs = RunCosts()

        # Copy turn data
        run_costs.by_turn = self.turns.copy()

        # Aggregate by task across all turns
        task_aggregates = defaultdict(lambda: TaskCosts(task_name=""))
        model_aggregates = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})

        for turn_costs in self.turns.values():
            run_costs.total_tokens += turn_costs.total_tokens
            run_costs.total_cost_usd += turn_costs.total_cost_usd

            for task_name, task_costs in turn_costs.by_task.items():
                # Aggregate by task
                if not task_aggregates[task_name].task_name:
                    task_aggregates[task_name].task_name = task_name

                task_aggregates[task_name].calls += task_costs.calls
                task_aggregates[task_name].total_tokens += task_costs.total_tokens
                task_aggregates[task_name].prompt_tokens += task_costs.prompt_tokens
                task_aggregates[task_name].completion_tokens += task_costs.completion_tokens
                task_aggregates[task_name].total_cost_usd += task_costs.total_cost_usd

                # Aggregate by model
                for model, model_data in task_costs.by_model.items():
                    model_aggregates[model]["calls"] += model_data["calls"]
                    model_aggregates[model]["tokens"] += model_data["tokens"]
                    model_aggregates[model]["cost_usd"] += model_data["cost_usd"]

        run_costs.by_task_aggregated = dict(task_aggregates)
        run_costs.by_model = dict(model_aggregates)

        return run_costs


def format_cost_report(run_costs: RunCosts, detailed: bool = False) -> str:
    """Format cost summary for CLI display.

    Args:
        run_costs: RunCosts to format
        detailed: Include detailed breakdown

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("COST REPORT")
    lines.append("=" * 60)

    # Overall summary
    lines.append(f"Total cost: ${run_costs.total_cost_usd:.4f}")
    lines.append(f"Total tokens: {run_costs.total_tokens:,}")

    if run_costs.by_turn:
        avg_cost = run_costs.total_cost_usd / len(run_costs.by_turn)
        avg_tokens = run_costs.total_tokens / len(run_costs.by_turn)
        lines.append(f"Average per turn: ${avg_cost:.4f} ({avg_tokens:,.0f} tokens)")

    # By task summary
    if run_costs.by_task_aggregated:
        lines.append("")
        lines.append("By Task (Total):")
        # Sort by cost descending
        sorted_tasks = sorted(
            run_costs.by_task_aggregated.items(),
            key=lambda x: x[1].total_cost_usd,
            reverse=True
        )
        for task_name, task_costs in sorted_tasks:
            lines.append(
                f"  {task_name:20s}: ${task_costs.total_cost_usd:.4f} "
                f"({task_costs.total_tokens:,} tokens, {task_costs.calls} calls)"
            )

    # By model summary
    if run_costs.by_model:
        lines.append("")
        lines.append("By Model:")
        sorted_models = sorted(
            run_costs.by_model.items(),
            key=lambda x: x[1]["cost_usd"],
            reverse=True
        )
        for model, data in sorted_models:
            lines.append(
                f"  {model:40s}: ${data['cost_usd']:.4f} "
                f"({data['tokens']:,} tokens, {data['calls']} calls)"
            )

    # Detailed: by turn
    if detailed and run_costs.by_turn:
        lines.append("")
        lines.append("By Turn:")
        for turn in sorted(run_costs.by_turn.keys()):
            turn_costs = run_costs.by_turn[turn]
            lines.append(
                f"  Turn {turn:2d}: ${turn_costs.total_cost_usd:.4f} "
                f"({turn_costs.total_tokens:,} tokens)"
            )

            # Task breakdown for this turn
            if detailed and turn_costs.by_task:
                for task_name, task_costs in sorted(turn_costs.by_task.items()):
                    lines.append(
                        f"    {task_name:18s}: ${task_costs.total_cost_usd:.4f} "
                        f"({task_costs.total_tokens:,} tokens)"
                    )

    lines.append("=" * 60)

    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using character-based heuristic.

    Uses conservative estimate of 1 token per 4 characters.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4
