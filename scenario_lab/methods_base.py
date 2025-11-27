"""
Base class for scenario-specific action methods.

Each scenario defines its own methods.py that inherits from ScenarioMethods.
Action functions modify world state and return interpretations for the Director.
"""

import logging
from typing import Dict, List, Any, Callable
from abc import ABC, abstractmethod

from .models import WorldState, FunctionCall


logger = logging.getLogger(__name__)


class ScenarioMethods(ABC):
    """
    Base class for scenario-specific action validation and execution.

    Subclasses define action functions that:
    1. Validate actor actions
    2. Modify world state (metrics, outcome_flags, etc.)
    3. Return interpretation strings for the Director

    Standard action signature:
        def action_name(self, actor: str, args: dict, state: WorldState) -> List[str]
    """

    def __init__(self):
        """Initialize the scenario methods handler."""
        self.action_registry: Dict[str, Callable] = {}
        self._register_actions()

    @abstractmethod
    def _register_actions(self) -> None:
        """
        Register all available actions for this scenario.

        Subclasses should implement this to register their action functions.

        Example:
            def _register_actions(self):
                self.register_action("declare_war", self.declare_war)
                self.register_action("sign_treaty", self.sign_treaty)
        """
        pass

    def register_action(self, name: str, func: Callable) -> None:
        """
        Register an action function.

        Args:
            name: Name of the action (matches function_call.name from LLM)
            func: Function to handle this action
        """
        self.action_registry[name] = func
        logger.debug(f"Registered action: {name}")

    def execute_action(
        self,
        actor: str,
        action: dict,
        state: WorldState
    ) -> List[str]:
        """
        Execute a function call and return interpretations.

        Args:
            actor: Name of the actor performing the action
            action: The action dictionary with "name" and "args"
            state: Current world state (will be modified in place)

        Returns:
            List of interpretation strings for the Director

        Raises:
            ValueError: If action is not registered
        """
        action_name = action["name"]

        if action_name not in self.action_registry:
            logger.error(f"Unknown action: {action_name}")
            raise ValueError(f"Action not registered: {action_name}")

        logger.info(f"Executing action: {actor}.{action_name}")

        # Execute the action function
        action_func = self.action_registry[action_name]
        interpretations = action_func(actor, action["args"], state)

        return interpretations

    def validate_action(
        self,
        actor: str,
        action: dict,
        state: WorldState
    ) -> bool:
        """
        Check if an action is allowed.
        
        Default: max 2 actions per actor per turn.
        """
        # This is a simplification. A real implementation would need to track
        # actions per actor per turn.
        return True

    # === Utility Methods for Subclasses ===

    def add_fact(
        self,
        state: WorldState,
        turn: int,
        fact: str,
        source: str
    ) -> None:
        """
        Add a fact to the fact ledger.

        Args:
            state: World state to modify
            turn: Current turn number
            fact: The fact to record
            source: Source of the fact (e.g., "action:declare_war")
        """
        from .models import FactLedgerEntry

        entry = FactLedgerEntry(
            timestamp=f"Turn {turn}",
            fact=fact,
            source=source
        )
        state.fact_ledger.append(entry)
        logger.info(f"Added fact: {fact}")

    def update_metric(
        self,
        state: WorldState,
        path: str,
        value: Any
    ) -> None:
        """
        Update a metric in the world state.

        Args:
            state: World state to modify
            path: Dot-separated path to metric (e.g., "world.temperature" or "actors.USA.public.gdp")
            value: New value for the metric

        Example:
            update_metric(state, "world.global_temperature", 1.3)
            update_metric(state, "actors.USA.private.military_capacity", 90)
        """
        from .models import ActorMetricsData

        parts = path.split(".")

        if parts[0] == "world":
            # World metric: world.metric_name
            metric_name = ".".join(parts[1:])
            state.metrics.world[metric_name] = value
            logger.debug(f"Updated metric: {path} = {value}")

        elif parts[0] == "actors" and len(parts) >= 4:
            # Actor metric: actors.ActorName.public/private.metric_name
            actor_name = parts[1]
            visibility = parts[2]  # "public" or "private"
            metric_name = ".".join(parts[3:])  # Handle nested metrics

            # Ensure actor metrics exist
            if actor_name not in state.metrics.actors:
                state.metrics.actors[actor_name] = ActorMetricsData()

            if visibility == "private":
                state.metrics.actors[actor_name].private[metric_name] = value
            elif visibility == "public":
                state.metrics.actors[actor_name].public[metric_name] = value
            else:
                logger.warning(f"Unknown visibility level: {visibility}")
                return

            logger.debug(f"Updated metric: {path} = {value}")
        else:
            logger.warning(f"Unrecognized metric path: {path}")

    def modify_metric(
        self,
        state: WorldState,
        path: str,
        delta: float
    ) -> None:
        """
        Modify a numeric metric by a delta.

        Args:
            state: World state to modify
            path: Dot-separated path to metric
            delta: Amount to add (can be negative)
        """
        from .models import ActorMetricsData

        parts = path.split(".")

        if parts[0] == "world":
            # World metric: world.metric_name
            metric_name = ".".join(parts[1:])
            current_value = state.metrics.world.get(metric_name, 0)
            new_value = current_value + delta
            state.metrics.world[metric_name] = new_value
            logger.debug(f"Modified metric: {path} {current_value} -> {new_value} (delta: {delta})")

        elif parts[0] == "actors" and len(parts) >= 4:
            # Actor metric: actors.ActorName.public/private.metric_name
            actor_name = parts[1]
            visibility = parts[2]  # "public" or "private"
            metric_name = ".".join(parts[3:])  # Handle nested metrics

            # Ensure actor metrics exist
            if actor_name not in state.metrics.actors:
                state.metrics.actors[actor_name] = ActorMetricsData()

            if visibility == "private":
                metrics_dict = state.metrics.actors[actor_name].private
            elif visibility == "public":
                metrics_dict = state.metrics.actors[actor_name].public
            else:
                logger.warning(f"Unknown visibility level: {visibility}")
                return

            current_value = metrics_dict.get(metric_name, 0)
            new_value = current_value + delta
            metrics_dict[metric_name] = new_value
            logger.debug(f"Modified metric: {path} {current_value} -> {new_value} (delta: {delta})")
        else:
            logger.warning(f"Unrecognized metric path: {path}")

    def set_outcome_flag(
        self,
        state: WorldState,
        flag: str,
        value: Any
    ) -> None:
        """
        Set an outcome flag for analysis.

        Args:
            state: World state to modify
            flag: Flag name (e.g., "war_declared")
            value: Flag value (can be bool, string, list, etc.)
        """
        state.outcome_flags[flag] = value
        logger.info(f"Set outcome flag: {flag} = {value}")

    def get_relationship(
        self,
        state: WorldState,
        actor1: str,
        actor2: str
    ):
        """
        Get relationship state between two actors.

        Args:
            state: World state
            actor1: First actor
            actor2: Second actor

        Returns:
            RelationshipState instance
        """
        return state.get_relationship(actor1, actor2)

    # === Generic Action Primitives for World Interpreter ===

    def adjust_metric(
        self,
        state: WorldState,
        metric_path: str,
        magnitude: str,
        direction: str,
        reason: str = ""
    ) -> float:
        """
        Adjust a metric by a magnitude (small/medium/large) in a direction.

        This is a generic primitive used by the World Interpreter.

        Args:
            state: World state to modify
            metric_path: Full path to metric (e.g., "actors.USA.private.budget")
            magnitude: "small", "medium", or "large"
            direction: "increase" or "decrease"
            reason: Explanation for the change (for logging)

        Returns:
            New metric value after adjustment

        Example:
            adjust_metric(state, "actors.USA.private.budget", "medium", "decrease",
                         "Major AI research investment")
        """
        import random

        # Get current value
        current_value = state.metrics.get_value(metric_path) or 0.0

        # Get metadata for magnitude ranges
        metadata = state.metrics.get_metadata(metric_path)

        # Determine change range
        if metadata and metadata.change_magnitudes:
            if magnitude == "small":
                change_range = metadata.change_magnitudes.small
            elif magnitude == "medium":
                change_range = metadata.change_magnitudes.medium
            elif magnitude == "large":
                change_range = metadata.change_magnitudes.large
            else:
                logger.warning(f"Unknown magnitude: {magnitude}, using default medium")
                change_range = metadata.change_magnitudes.medium
        else:
            # Default ranges
            default_ranges = {
                "small": (0.01, 0.05),
                "medium": (0.05, 0.15),
                "large": (0.15, 0.5),
            }
            change_range = default_ranges.get(magnitude, (0.05, 0.15))

        # Pick random value within range
        change_fraction = random.uniform(*change_range)

        # Apply randomness if specified in metadata
        if metadata and metadata.randomness > 0:
            variance = random.uniform(-metadata.randomness, metadata.randomness)
            change_fraction *= (1 + variance)

        # Calculate delta based on current value (percentage change)
        if current_value != 0:
            delta = abs(current_value) * change_fraction
        else:
            # If current value is 0, use absolute change (scaled by 100 as base)
            delta = 100 * change_fraction

        # Apply direction
        if direction == "increase":
            new_value = current_value + delta
        elif direction == "decrease":
            new_value = current_value - delta
        else:
            logger.warning(f"Unknown direction: {direction}, no change applied")
            new_value = current_value

        # Validate bounds
        if metadata:
            if metadata.min is not None:
                new_value = max(new_value, metadata.min)
            if metadata.max is not None:
                new_value = min(new_value, metadata.max)

        # Update the metric
        state.metrics.set_value(metric_path, new_value)

        logger.info(
            f"Adjusted metric: {metric_path} "
            f"{current_value:.2f} -> {new_value:.2f} "
            f"({magnitude} {direction}, delta: {delta:.2f}) "
            f"| {reason}"
        )

        return new_value

    def set_metric_direct(
        self,
        state: WorldState,
        metric_path: str,
        value: float,
        reason: str = ""
    ) -> float:
        """
        Set a metric to an exact value.

        Used for events or direct assignments (not typically by actors).

        Args:
            state: World state to modify
            metric_path: Full path to metric
            value: New value
            reason: Explanation for the change

        Returns:
            The value that was set (after bounds validation)
        """
        # Get metadata for bounds
        metadata = state.metrics.get_metadata(metric_path)

        # Validate bounds
        if metadata:
            if metadata.min is not None:
                value = max(value, metadata.min)
            if metadata.max is not None:
                value = min(value, metadata.max)

        # Update the metric
        old_value = state.metrics.get_value(metric_path) or 0.0
        state.metrics.set_value(metric_path, value)

        logger.info(
            f"Set metric: {metric_path} "
            f"{old_value:.2f} -> {value:.2f} "
            f"| {reason}"
        )

        return value

    def apply_random_variation(
        self,
        state: WorldState,
        metric_path: str
    ) -> float:
        """
        Apply random variation to a metric based on its randomness setting.

        Used during post-turn processing to add stochastic elements.

        Args:
            state: World state to modify
            metric_path: Full path to metric

        Returns:
            New metric value after variation
        """
        import random

        metadata = state.metrics.get_metadata(metric_path)
        if not metadata or metadata.randomness == 0:
            # No randomness configured
            return state.metrics.get_value(metric_path) or 0.0

        current_value = state.metrics.get_value(metric_path) or 0.0

        # Apply randomness as variance
        variance = random.uniform(-metadata.randomness, metadata.randomness)
        new_value = current_value * (1 + variance)

        # Validate bounds
        if metadata.min is not None:
            new_value = max(new_value, metadata.min)
        if metadata.max is not None:
            new_value = min(new_value, metadata.max)

        state.metrics.set_value(metric_path, new_value)

        logger.debug(
            f"Applied random variation: {metric_path} "
            f"{current_value:.2f} -> {new_value:.2f} "
            f"(randomness: {metadata.randomness})"
        )

        return new_value


class EmptyScenarioMethods(ScenarioMethods):
    """
    Empty implementation for testing.

    Provides no actions, useful for testing the engine without scenario logic.
    """

    def _register_actions(self) -> None:
        """No actions registered."""
        pass
