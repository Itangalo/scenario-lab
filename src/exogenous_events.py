"""
Exogenous Event Manager - Handles world events independent of actor decisions

This enables scenarios to include:
- Background trends (e.g., compute costs declining)
- Random events (e.g., research breakthroughs, incidents)
- Conditional events (e.g., triggered when metrics reach thresholds)
"""
import random
from typing import Dict, List, Any, Optional
import re


class ExogenousEventManager:
    """
    Manages events that occur independently of actor decisions.

    Events are defined in plain text YAML and evaluated each turn.
    The manager simply determines which events occur - the WorldStateUpdater
    integrates them into the narrative.
    """

    def __init__(self, events_config: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize with events configuration

        Args:
            events_config: List of event definitions from YAML
                Each event has: type, name, description, and type-specific fields
        """
        self.events = events_config or []
        self.triggered_events = set()  # Track one-time events

    def get_events_for_turn(
        self,
        turn: int,
        metrics: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, str]]:
        """
        Get all events that occur on this turn

        Args:
            turn: Current turn number (1-indexed)
            metrics: Current scenario metrics (for conditional events)

        Returns:
            List of events that occur, each with 'name' and 'description'
        """
        active_events = []

        for event in self.events:
            event_type = event.get('type', 'scheduled')

            if event_type == 'scheduled':
                if self._check_scheduled(event, turn):
                    active_events.append({
                        'name': event['name'],
                        'description': event['description']
                    })

            elif event_type == 'random':
                if self._check_random(event, turn):
                    active_events.append({
                        'name': event['name'],
                        'description': event['description']
                    })

            elif event_type == 'conditional':
                if self._check_conditional(event, turn, metrics):
                    active_events.append({
                        'name': event['name'],
                        'description': event['description']
                    })

            elif event_type == 'trend':
                # Trends occur every turn in their range
                if self._check_trend(event, turn):
                    active_events.append({
                        'name': event['name'],
                        'description': event['description']
                    })

        return active_events

    def _check_scheduled(self, event: Dict, turn: int) -> bool:
        """Check if scheduled event occurs this turn"""
        event_turn = event.get('turn')

        if event_turn is None:
            return False

        # Check if it's a one-time event that already triggered
        event_id = f"scheduled_{event['name']}_{event_turn}"
        if event.get('once', True) and event_id in self.triggered_events:
            return False

        if turn == event_turn:
            if event.get('once', True):
                self.triggered_events.add(event_id)
            return True

        return False

    def _check_random(self, event: Dict, turn: int) -> bool:
        """Check if random event occurs this turn (probabilistic)"""
        probability = event.get('probability', 0.0)
        turn_range = event.get('turn_range', [1, 999])

        # Check if we're in the valid turn range
        if not (turn_range[0] <= turn <= turn_range[1]):
            return False

        # Check if it's a one-time event that already triggered
        event_id = f"random_{event['name']}"
        if event.get('once', True) and event_id in self.triggered_events:
            return False

        # Roll for probability
        if random.random() < probability:
            if event.get('once', True):
                self.triggered_events.add(event_id)
            return True

        return False

    def _check_conditional(self, event: Dict, turn: int, metrics: Optional[Dict]) -> bool:
        """Check if conditional event occurs (based on metrics)"""
        if metrics is None:
            return False

        conditions = event.get('conditions', {})
        turn_range = event.get('turn_range', [1, 999])

        # Check if we're in the valid turn range
        if not (turn_range[0] <= turn <= turn_range[1]):
            return False

        # Check if it's a one-time event that already triggered
        event_id = f"conditional_{event['name']}"
        if event.get('once', True) and event_id in self.triggered_events:
            return False

        # Check all conditions
        for metric_name, condition_str in conditions.items():
            if metric_name not in metrics:
                return False

            if not self._evaluate_condition(metrics[metric_name], condition_str):
                return False

        # All conditions met
        if event.get('once', True):
            self.triggered_events.add(event_id)
        return True

    def _check_trend(self, event: Dict, turn: int) -> bool:
        """Check if trend applies this turn (repeating background events)"""
        turn_range = event.get('turn_range', [1, 999])
        frequency = event.get('frequency', 1)  # How often it occurs (every N turns)

        # Check if we're in the valid turn range
        if not (turn_range[0] <= turn <= turn_range[1]):
            return False

        # Check if it's time for this trend to occur
        return (turn - turn_range[0]) % frequency == 0

    def _evaluate_condition(self, value: float, condition_str: str) -> bool:
        """
        Evaluate a condition string against a metric value

        Examples:
            ">= 7" checks if value >= 7
            "< 5" checks if value < 5
            "== 3.5" checks if value == 3.5
        """
        condition_str = condition_str.strip()

        # Parse condition (e.g., ">= 7", "< 5", "== 3")
        match = re.match(r'([<>=!]+)\s*([\d.]+)', condition_str)
        if not match:
            return False

        operator, threshold_str = match.groups()
        threshold = float(threshold_str)

        if operator == '>':
            return value > threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<':
            return value < threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==' or operator == '=':
            return abs(value - threshold) < 0.001  # Float equality with tolerance
        elif operator == '!=':
            return abs(value - threshold) >= 0.001

        return False
