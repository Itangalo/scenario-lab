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


class EmptyScenarioMethods(ScenarioMethods):
    """
    Empty implementation for testing.

    Provides no actions, useful for testing the engine without scenario logic.
    """

    def _register_actions(self) -> None:
        """No actions registered."""
        pass
