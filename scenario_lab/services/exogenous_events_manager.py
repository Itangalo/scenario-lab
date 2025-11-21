"""
Exogenous Events Manager for Scenario Lab V2

Manages background events that occur independently of actor decisions.
Evaluates event triggers based on turn number, probabilities, and metric thresholds.
"""
from __future__ import annotations
import random
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

from scenario_lab.schemas.exogenous_events import (
    ExogenousEventBase,
    TrendEvent,
    RandomEvent,
    ConditionalEvent,
    ScheduledEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class TriggeredEvent:
    """Represents an event that has been triggered"""

    name: str
    description: str
    event_type: str  # trend, random, conditional, scheduled


class ExogenousEventManager:
    """
    Manages exogenous events for a scenario

    This class:
    1. Stores event definitions from configuration
    2. Evaluates which events should trigger each turn
    3. Tracks which one-time events have already triggered
    4. Returns triggered events for integration into world state
    """

    def __init__(
        self,
        events: List[ExogenousEventBase],
        triggered_event_ids: Optional[Set[str]] = None,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize event manager

        Args:
            events: List of event definitions
            triggered_event_ids: Set of event IDs that have already triggered (for resume)
            random_seed: Optional seed for reproducible random events
        """
        self.events = events
        self.triggered_event_ids = triggered_event_ids or set()

        # Set random seed if provided (for reproducibility in testing)
        if random_seed is not None:
            random.seed(random_seed)

        logger.info(
            f"Initialized ExogenousEventManager with {len(events)} events "
            f"({len(self.triggered_event_ids)} already triggered)"
        )

    def get_events_for_turn(
        self,
        turn: int,
        metrics: Optional[Dict[str, float]] = None,
    ) -> List[TriggeredEvent]:
        """
        Get all events that should trigger for this turn

        Args:
            turn: Current turn number (1-indexed)
            metrics: Current metric values for conditional events

        Returns:
            List of triggered events to be integrated into world state
        """
        triggered = []

        for event in self.events:
            # Check if event can trigger this turn
            if not self._is_event_active(event, turn):
                continue

            # Check if already triggered (for one-time events)
            event_id = self._get_event_id(event)
            if event.once and event_id in self.triggered_event_ids:
                continue

            # Evaluate trigger condition based on event type
            should_trigger = False

            if isinstance(event, TrendEvent):
                should_trigger = self._evaluate_trend_event(event, turn)
            elif isinstance(event, RandomEvent):
                should_trigger = self._evaluate_random_event(event, turn)
            elif isinstance(event, ConditionalEvent):
                should_trigger = self._evaluate_conditional_event(event, turn, metrics or {})
            elif isinstance(event, ScheduledEvent):
                should_trigger = self._evaluate_scheduled_event(event, turn)

            # Trigger event if conditions met
            if should_trigger:
                triggered.append(
                    TriggeredEvent(
                        name=event.name,
                        description=event.description,
                        event_type=event.type,
                    )
                )

                # Mark as triggered if it's a one-time event
                if event.once:
                    self.triggered_event_ids.add(event_id)
                    logger.debug(f"Event '{event.name}' triggered (one-time, will not repeat)")
                else:
                    logger.debug(f"Event '{event.name}' triggered (can repeat)")

        if triggered:
            logger.info(f"Turn {turn}: {len(triggered)} exogenous event(s) triggered")
            for evt in triggered:
                logger.info(f"  • {evt.name}")

        return triggered

    def _is_event_active(self, event: ExogenousEventBase, turn: int) -> bool:
        """Check if event is active for this turn based on turn_range"""
        if event.turn_range is None:
            return True

        min_turn, max_turn = event.turn_range
        return min_turn <= turn <= max_turn

    def _get_event_id(self, event: ExogenousEventBase) -> str:
        """Generate unique ID for event (for tracking triggered events)"""
        return f"{event.type}:{event.name}"

    def _evaluate_trend_event(self, event: TrendEvent, turn: int) -> bool:
        """Evaluate whether trend event should trigger this turn"""
        # Trends occur every N turns starting from the first turn in their range
        if event.turn_range is None:
            return False

        min_turn = event.turn_range[0]
        offset = turn - min_turn

        # Trigger if we're at the start or every frequency turns thereafter
        return offset >= 0 and offset % event.frequency == 0

    def _evaluate_random_event(self, event: RandomEvent, turn: int) -> bool:
        """Evaluate whether random event should trigger this turn"""
        # Random events use probability check
        roll = random.random()
        return roll < event.probability

    def _evaluate_conditional_event(
        self,
        event: ConditionalEvent,
        turn: int,
        metrics: Dict[str, float]
    ) -> bool:
        """Evaluate whether conditional event should trigger this turn"""
        # All conditions must be met for event to trigger
        for metric_name, condition_str in event.conditions.items():
            if not self._evaluate_condition(metric_name, condition_str, metrics):
                return False

        return True

    def _evaluate_condition(
        self,
        metric_name: str,
        condition_str: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        Evaluate a single metric condition

        Args:
            metric_name: Name of the metric
            condition_str: Condition string (e.g., '>= 7', '< 5')
            metrics: Current metric values

        Returns:
            True if condition is met, False otherwise
        """
        # Get metric value (return False if metric doesn't exist yet)
        if metric_name not in metrics:
            logger.debug(f"Metric '{metric_name}' not found for conditional evaluation")
            return False

        metric_value = metrics[metric_name]

        # Parse condition (e.g., '>= 7')
        condition_str = condition_str.strip()

        # Try each operator in order of length (longest first to match >= before >)
        operators = ['>=', '<=', '==', '!=', '>', '<']

        for op in operators:
            if op in condition_str:
                parts = condition_str.split(op)
                if len(parts) != 2:
                    logger.warning(f"Invalid condition format: '{condition_str}'")
                    return False

                try:
                    threshold = float(parts[1].strip())
                except ValueError:
                    logger.warning(f"Invalid threshold value in condition: '{condition_str}'")
                    return False

                # Evaluate condition
                if op == '>=':
                    result = metric_value >= threshold
                elif op == '>':
                    result = metric_value > threshold
                elif op == '<=':
                    result = metric_value <= threshold
                elif op == '<':
                    result = metric_value < threshold
                elif op == '==':
                    result = abs(metric_value - threshold) < 0.0001  # Float equality
                elif op == '!=':
                    result = abs(metric_value - threshold) >= 0.0001
                else:
                    logger.warning(f"Unknown operator: {op}")
                    return False

                logger.debug(
                    f"Condition '{metric_name} {op} {threshold}': "
                    f"{metric_value} {op} {threshold} = {result}"
                )
                return result

        logger.warning(f"No valid operator found in condition: '{condition_str}'")
        return False

    def _evaluate_scheduled_event(self, event: ScheduledEvent, turn: int) -> bool:
        """Evaluate whether scheduled event should trigger this turn"""
        return turn == event.turn

    def get_triggered_event_ids(self) -> Set[str]:
        """Get set of triggered event IDs (for state persistence)"""
        return self.triggered_event_ids.copy()
