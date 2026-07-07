"""Cost estimation for simulations before running."""

from .models import Scenario
from .prompts import PromptBuilder
from .cost import CostCalculator, estimate_tokens


class CostEstimator:
    """Estimate costs for a simulation run before executing."""

    def __init__(self, scenario: Scenario):
        """Initialize cost estimator.

        Args:
            scenario: Loaded scenario to estimate costs for
        """
        self.scenario = scenario
        self.prompt_builder = PromptBuilder(scenario)

    def estimate_costs(self, num_turns: int) -> dict:
        """Estimate total costs for a simulation run.

        Args:
            num_turns: Number of turns to simulate

        Returns:
            Dict with cost estimates:
            {
                "total_cost_usd": float,
                "total_tokens": int,
                "per_turn_cost_usd": float,
                "per_turn_tokens": int,
                "by_task": {
                    "events": {"tokens": int, "cost_usd": float},
                    "actors": {"tokens": int, "cost_usd": float},
                    ...
                },
                "warning": str
            }
        """
        # Estimate tokens for each task type
        events_tokens = self._estimate_events_tokens()
        actors_tokens = self._estimate_actors_tokens()
        rules_tokens = self._estimate_rules_tokens()
        metrics_tokens = self._estimate_metrics_tokens()
        summary_tokens = self._estimate_summary_tokens()

        # Total per turn
        per_turn_tokens = (
            events_tokens
            + actors_tokens
            + rules_tokens
            + metrics_tokens
            + summary_tokens
        )

        # Calculate costs using configured models
        events_cost = self._calculate_task_cost(events_tokens, "events")
        actors_cost = self._calculate_task_cost(actors_tokens, "actors")
        rules_cost = self._calculate_task_cost(rules_tokens, "rules")
        metrics_cost = self._calculate_task_cost(metrics_tokens, "metrics")
        summary_cost = self._calculate_task_cost(summary_tokens, "summary")

        per_turn_cost = (
            events_cost + actors_cost + rules_cost + metrics_cost + summary_cost
        )

        return {
            "total_cost_usd": per_turn_cost * num_turns,
            "total_tokens": per_turn_tokens * num_turns,
            "per_turn_cost_usd": per_turn_cost,
            "per_turn_tokens": per_turn_tokens,
            "by_task": {
                "events": {"tokens": events_tokens, "cost_usd": events_cost},
                "actors": {
                    "tokens": actors_tokens,
                    "cost_usd": actors_cost,
                    "num_actors": len(self.scenario.config.actor_ids),
                },
                "rules": {"tokens": rules_tokens, "cost_usd": rules_cost},
                "metrics": {"tokens": metrics_tokens, "cost_usd": metrics_cost},
                "summary": {"tokens": summary_tokens, "cost_usd": summary_cost},
            },
            "warning": "Estimates may vary ±30% based on actual LLM response length",
        }

    def _estimate_events_tokens(self) -> int:
        """Estimate tokens for events step."""
        # Build a sample events prompt
        system, user = self.prompt_builder.build_events_prompt(turn=1)

        # Estimate input tokens (system + user prompt)
        input_tokens = estimate_tokens(system) + estimate_tokens(user)

        # Estimate output tokens (conservative: JSON array with a few events)
        # Example: [{"id": "event1", "probability": 0.15}, {...}]
        # Average ~50 chars per event, assume ~2 events triggered
        output_tokens = estimate_tokens('[{"id": "event_example", "probability": 0.15}]')

        # Probability sampling repeats the full events call per sample.
        samples = self.scenario.config.llm.probability_samples
        return (input_tokens + output_tokens) * samples

    def _estimate_actors_tokens(self) -> int:
        """Estimate tokens for all actors combined."""
        num_actors = len(self.scenario.config.actor_ids)

        if num_actors == 0:
            return 0

        # Sample one actor to estimate
        sample_actor_id = self.scenario.config.actor_ids[0]
        system, user = self.prompt_builder.build_actor_prompt(
            sample_actor_id, turn=1, triggered_events=[]
        )

        # Estimate input tokens per actor
        input_tokens = estimate_tokens(system) + estimate_tokens(user)

        # Estimate output tokens (markdown output with goals and actions)
        # Conservative estimate: ~200-400 words = ~800-1600 chars
        output_tokens = estimate_tokens("## Goals\n" + "Goal description. " * 30 + "\n## Actions\n" + "Action description. " * 40)

        # Multiply by number of actors
        return (input_tokens + output_tokens) * num_actors

    def _estimate_rules_tokens(self) -> int:
        """Estimate tokens for metric rules update."""
        # Build sample rules prompt
        actor_actions = {
            actor_id: "Sample actor output"
            for actor_id in self.scenario.config.actor_ids
        }
        system, user = self.prompt_builder.build_rules_prompt(
            turn=1, actor_actions=actor_actions, triggered_events=[]
        )

        input_tokens = estimate_tokens(system) + estimate_tokens(user)

        # Output is the updated rules markdown (roughly same size as input rules)
        # Use current metric rules as proxy
        output_tokens = estimate_tokens(self.scenario.metric_rules)

        return input_tokens + output_tokens

    def _estimate_metrics_tokens(self) -> int:
        """Estimate tokens for metrics and narrative update."""
        # Build sample metrics prompt
        actor_actions = {
            actor_id: "Sample actor output"
            for actor_id in self.scenario.config.actor_ids
        }
        system, user = self.prompt_builder.build_metrics_prompt(
            turn=1, actor_actions=actor_actions, triggered_events=[]
        )

        input_tokens = estimate_tokens(system) + estimate_tokens(user)

        # Output: metrics JSON + narrative + notepad
        # Metrics: ~20 chars per metric
        num_metrics = len(self.scenario.metrics.metrics)
        metrics_output = estimate_tokens('{"metric1": 50, "metric2": 75}' * (num_metrics // 2))

        # Narrative: ~300-500 words = ~1200-2000 chars
        narrative_output = estimate_tokens("This is a narrative description. " * 50)

        # Notepad: ~50-100 words = ~200-400 chars
        notepad_output = estimate_tokens("Notepad entry. " * 15)

        output_tokens = metrics_output + narrative_output + notepad_output

        return input_tokens + output_tokens

    def _estimate_summary_tokens(self) -> int:
        """Estimate tokens for historical summary update."""
        # Build sample summary prompt
        current_summary = self.scenario.world_state.historical_summary
        current_narrative = "Sample narrative from the turn."

        system, user = self.prompt_builder.build_summary_prompt(
            current_summary, current_narrative
        )

        input_tokens = estimate_tokens(system) + estimate_tokens(user)

        # Output: Updated summary (grows over time, but for estimation use current size)
        # Conservative: assume summary doubles after a few turns
        output_tokens = estimate_tokens(current_summary) + 200  # + growth

        return input_tokens + output_tokens

    def _calculate_task_cost(self, tokens: int, task_name: str) -> float:
        """Calculate cost for a task based on configured model.

        Args:
            tokens: Estimated token count
            task_name: Task identifier (events, actors, rules, metrics, summary)

        Returns:
            Estimated cost in USD
        """
        # Get model for this task
        config = self.scenario.config.llm

        if task_name == "events":
            model = config.events
        elif task_name == "actors":
            # Use first actor's model or default
            model = config.get_actor_models(self.scenario.config.actor_ids[0]) if self.scenario.config.actor_ids else config.events
        elif task_name == "rules":
            model = config.rules
        elif task_name == "metrics":
            model = config.metrics
        elif task_name == "summary":
            model = config.summary
        else:
            model = config.events  # fallback

        # Handle fallback lists (use first model)
        if isinstance(model, list):
            model = model[0]

        # Get pricing for the route, falling back to the default estimate for
        # models missing from the cache.
        from .pricing import DEFAULT_PRICING, get_pricing_for

        pricing = get_pricing_for(model) or DEFAULT_PRICING

        # Assume 60/40 split between prompt and completion tokens
        prompt_tokens = int(tokens * 0.6)
        completion_tokens = int(tokens * 0.4)

        # Calculate cost
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]

        return prompt_cost + completion_cost


def format_estimate_report(estimate: dict, scenario_name: str, num_turns: int) -> str:
    """Format cost estimate for CLI display.

    Args:
        estimate: Cost estimate dict from CostEstimator
        scenario_name: Name of the scenario
        num_turns: Number of turns

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("COST ESTIMATE")
    lines.append("=" * 60)
    lines.append(f"Scenario: {scenario_name}")
    lines.append(f"Turns: {num_turns}")
    lines.append("")

    # Per-turn breakdown
    lines.append("Estimated per turn:")
    for task_name, task_data in estimate["by_task"].items():
        tokens = task_data["tokens"]
        cost = task_data["cost_usd"]

        if task_name == "actors" and "num_actors" in task_data:
            lines.append(
                f"  {task_name.capitalize():10s}: ~{tokens:,} tokens "
                f"({task_data['num_actors']} actors) → ${cost:.4f}"
            )
        else:
            lines.append(
                f"  {task_name.capitalize():10s}: ~{tokens:,} tokens → ${cost:.4f}"
            )

    lines.append(
        f"  {'Total':10s}: ~{estimate['per_turn_tokens']:,} tokens → "
        f"${estimate['per_turn_cost_usd']:.4f}"
    )

    lines.append("")
    lines.append("Total simulation estimate:")
    lines.append(f"  Tokens: ~{estimate['total_tokens']:,}")
    lines.append(f"  Cost: ${estimate['total_cost_usd']:.2f} USD")

    lines.append("")
    lines.append(f"⚠️  {estimate['warning']}")
    lines.append("=" * 60)

    return "\n".join(lines)
