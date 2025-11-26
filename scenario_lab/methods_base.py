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
        function_call: FunctionCall,
        state: WorldState
    ) -> List[str]:
        """
        Execute a function call and return interpretations.

        Args:
            actor: Name of the actor performing the action
            function_call: The function call to execute
            state: Current world state (will be modified in place)

        Returns:
            List of interpretation strings for the Director

        Raises:
            ValueError: If action is not registered
        """
        action_name = function_call.name

        if action_name not in self.action_registry:
            logger.error(f"Unknown action: {action_name}")
            raise ValueError(f"Action not registered: {action_name}")

        logger.info(f"Executing action: {actor}.{action_name}")

        # Execute the action function
        action_func = self.action_registry[action_name]
        interpretations = action_func(actor, function_call.arguments, state)

        return interpretations

    def validate_actor_actions(
        self,
        actor: str,
        function_calls: List[FunctionCall],
        state: WorldState
    ) -> tuple[bool, str]:
        """
        Validate all actions for an actor before execution.

        Default implementation checks for max 2 major initiatives.
        Subclasses can override for scenario-specific validation.

        Args:
            actor: Name of the actor
            function_calls: List of function calls to validate
            state: Current world state

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check max 2 major initiatives per turn
        if len(function_calls) > 2:
            return False, f"Actor {actor} attempted {len(function_calls)} actions (max 2)"

        return True, ""

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
        parts = path.split(".")
        current = state.metrics

        # Navigate to the parent of the target
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        current[parts[-1]] = value
        logger.debug(f"Updated metric: {path} = {value}")

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
        parts = path.split(".")
        current = state.metrics

        # Navigate to the parent of the target
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Get current value and add delta
        key = parts[-1]
        current_value = current.get(key, 0)
        new_value = current_value + delta
        current[key] = new_value

        logger.debug(f"Modified metric: {path} {current_value} -> {new_value} (delta: {delta})")

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
