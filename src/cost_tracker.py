"""
Cost Tracker - Estimates and tracks LLM API costs during scenario execution
"""
import json
from typing import Dict, Any, List
from datetime import datetime


class CostTracker:
    """
    Tracks LLM API usage and costs throughout scenario execution
    """

    # Rough cost estimates (USD per 1M tokens) for common models
    # These are approximate - actual costs may vary
    MODEL_COSTS = {
        # Free models
        "alibaba/tongyi-deepresearch-30b-a3b:free": {"input": 0.0, "output": 0.0},

        # OpenAI models (approximate)
        "openai/gpt-4o": {"input": 2.50, "output": 10.00},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "openai/gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "openai/gpt-3.5-turbo": {"input": 0.50, "output": 1.50},

        # Anthropic models (approximate)
        "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
        "anthropic/claude-3-opus": {"input": 15.00, "output": 75.00},
        "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},

        # Default for unknown models
        "default": {"input": 1.00, "output": 5.00}
    }

    def __init__(self):
        """Initialize the cost tracker"""
        self.costs_by_actor = {}  # {actor_name: {turns: [], total_cost: 0, total_tokens: 0}}
        self.costs_by_turn = {}  # {turn: {actor_costs: {}, world_state_cost: 0, total: 0}}
        self.world_state_costs = []  # List of {turn, tokens, cost}
        self.total_tokens = 0
        self.total_cost = 0.0
        self.start_time = None
        self.end_time = None

    def estimate_scenario_cost(
        self,
        num_actors: int,
        num_turns: int,
        actor_models: Dict[str, str],
        world_state_model: str,
        avg_tokens_per_decision: int = 1000,
        avg_tokens_per_world_update: int = 1500
    ) -> Dict[str, Any]:
        """
        Estimate total cost before running scenario

        Args:
            num_actors: Number of actors in scenario
            num_turns: Number of turns to run
            actor_models: Dict of {actor_name: model}
            world_state_model: Model used for world state updates
            avg_tokens_per_decision: Estimated tokens per actor decision
            avg_tokens_per_world_update: Estimated tokens per world state update

        Returns:
            Dict with cost breakdown and total estimate
        """
        estimate = {
            "actors": {},
            "world_state": 0.0,
            "total": 0.0,
            "total_tokens_estimated": 0,
            "assumptions": {
                "tokens_per_decision": avg_tokens_per_decision,
                "tokens_per_world_update": avg_tokens_per_world_update,
                "num_turns": num_turns
            }
        }

        # Estimate actor costs
        for actor_name, model in actor_models.items():
            cost_per_1m = self._get_model_cost(model)
            # Assume 50/50 split between input and output tokens
            input_tokens = (avg_tokens_per_decision * 0.5) * num_turns
            output_tokens = (avg_tokens_per_decision * 0.5) * num_turns

            cost = (input_tokens / 1_000_000 * cost_per_1m['input'] +
                   output_tokens / 1_000_000 * cost_per_1m['output'])

            estimate["actors"][actor_name] = {
                "model": model,
                "estimated_tokens": avg_tokens_per_decision * num_turns,
                "estimated_cost_usd": round(cost, 4)
            }
            estimate["total"] += cost
            estimate["total_tokens_estimated"] += avg_tokens_per_decision * num_turns

        # Estimate world state costs
        ws_cost_per_1m = self._get_model_cost(world_state_model)
        ws_input_tokens = (avg_tokens_per_world_update * 0.6) * num_turns  # More input for context
        ws_output_tokens = (avg_tokens_per_world_update * 0.4) * num_turns

        ws_cost = (ws_input_tokens / 1_000_000 * ws_cost_per_1m['input'] +
                  ws_output_tokens / 1_000_000 * ws_cost_per_1m['output'])

        estimate["world_state"] = round(ws_cost, 4)
        estimate["total"] += ws_cost
        estimate["total_tokens_estimated"] += avg_tokens_per_world_update * num_turns

        estimate["total"] = round(estimate["total"], 4)

        return estimate

    def record_actor_decision(
        self,
        actor_name: str,
        turn: int,
        model: str,
        tokens_used: int
    ):
        """Record cost for an actor's decision"""
        cost = self._calculate_cost(model, tokens_used)

        # Initialize actor tracking if needed
        if actor_name not in self.costs_by_actor:
            self.costs_by_actor[actor_name] = {
                "model": model,
                "turns": [],
                "total_tokens": 0,
                "total_cost": 0.0
            }

        # Record turn data
        self.costs_by_actor[actor_name]["turns"].append({
            "turn": turn,
            "tokens": tokens_used,
            "cost": cost
        })
        self.costs_by_actor[actor_name]["total_tokens"] += tokens_used
        self.costs_by_actor[actor_name]["total_cost"] += cost

        # Update turn tracking
        if turn not in self.costs_by_turn:
            self.costs_by_turn[turn] = {
                "actor_costs": {},
                "world_state_cost": 0.0,
                "total": 0.0
            }

        self.costs_by_turn[turn]["actor_costs"][actor_name] = cost
        self.costs_by_turn[turn]["total"] += cost

        # Update totals
        self.total_tokens += tokens_used
        self.total_cost += cost

    def record_world_state_update(
        self,
        turn: int,
        model: str,
        tokens_used: int
    ):
        """Record cost for world state update"""
        cost = self._calculate_cost(model, tokens_used)

        self.world_state_costs.append({
            "turn": turn,
            "tokens": tokens_used,
            "cost": cost
        })

        # Update turn tracking
        if turn not in self.costs_by_turn:
            self.costs_by_turn[turn] = {
                "actor_costs": {},
                "world_state_cost": 0.0,
                "total": 0.0
            }

        self.costs_by_turn[turn]["world_state_cost"] = cost
        self.costs_by_turn[turn]["total"] += cost

        # Update totals
        self.total_tokens += tokens_used
        self.total_cost += cost

    def start_tracking(self):
        """Mark start time for tracking"""
        self.start_time = datetime.now()

    def end_tracking(self):
        """Mark end time for tracking"""
        self.end_time = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """Get complete cost summary"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "scenario_execution": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": duration
            },
            "costs_by_actor": self.costs_by_actor,
            "costs_by_turn": self.costs_by_turn,
            "world_state_costs": self.world_state_costs,
            "totals": {
                "total_tokens": self.total_tokens,
                "total_cost_usd": round(self.total_cost, 4)
            }
        }

    def save_to_file(self, filepath: str):
        """Save cost data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)

    def _get_model_cost(self, model: str) -> Dict[str, float]:
        """Get cost per 1M tokens for a model"""
        if model in self.MODEL_COSTS:
            return self.MODEL_COSTS[model]
        return self.MODEL_COSTS["default"]

    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for token usage"""
        cost_per_1m = self._get_model_cost(model)
        # Assume 60% input, 40% output tokens as rough estimate
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4

        cost = (input_tokens / 1_000_000 * cost_per_1m['input'] +
               output_tokens / 1_000_000 * cost_per_1m['output'])

        return round(cost, 6)

    def print_summary(self):
        """Print a formatted cost summary"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("COST SUMMARY")
        print("="*60)

        print("\nBy Actor:")
        for actor_name, data in summary["costs_by_actor"].items():
            print(f"  {actor_name}:")
            print(f"    Model: {data['model']}")
            print(f"    Tokens: {data['total_tokens']:,}")
            print(f"    Cost: ${data['total_cost']:.4f}")

        print("\nWorld State Updates:")
        total_ws_tokens = sum(item['tokens'] for item in summary["world_state_costs"])
        total_ws_cost = sum(item['cost'] for item in summary["world_state_costs"])
        print(f"  Tokens: {total_ws_tokens:,}")
        print(f"  Cost: ${total_ws_cost:.4f}")

        print("\nTotal:")
        print(f"  Tokens: {summary['totals']['total_tokens']:,}")
        print(f"  Cost: ${summary['totals']['total_cost_usd']:.4f}")

        if summary['scenario_execution']['duration_seconds']:
            print(f"  Duration: {summary['scenario_execution']['duration_seconds']:.1f} seconds")

        print("="*60 + "\n")
