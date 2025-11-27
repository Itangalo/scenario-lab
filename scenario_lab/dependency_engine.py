"""
Dependency Engine for Scenario Lab V3.

Handles inter-metric dependencies where one metric affects another.
"""

import logging
import re
from typing import List, Set

from scenario_lab.models import WorldState, MetricDependency, MetricMetadata

logger = logging.getLogger(__name__)


class DependencyEngine:
    """
    Resolves and applies inter-metric dependencies.

    Dependencies allow metrics to automatically affect other metrics based on rules.
    For example:
    - If budget > 1000, international_influence gains +0.1 (additive)
    - If regulation > 50, catastrophe_risk multiplies by 0.8 (multiplicative)
    """

    def __init__(self):
        """Initialize the dependency engine."""
        self.processed_metrics: Set[str] = set()

    def apply_dependencies(self, state: WorldState, changed_metrics: List[str]) -> None:
        """
        Apply dependencies triggered by metric changes.

        Args:
            state: Current world state (modified in place)
            changed_metrics: List of metric paths that changed this turn

        Process:
        1. For each changed metric, check if other metrics depend on it
        2. Evaluate dependency conditions
        3. Apply dependency effects (additive or multiplicative)
        4. Track applied dependencies to avoid cycles
        """
        self.processed_metrics.clear()

        for metric_path in changed_metrics:
            self._apply_metric_dependencies(state, metric_path)

    def _apply_metric_dependencies(self, state: WorldState, source_metric: str) -> None:
        """
        Apply all dependencies that reference a given source metric.

        Args:
            state: World state
            source_metric: The metric that changed and may trigger dependencies
        """
        # Scan all metrics for dependencies on this source
        for target_path, metadata in state.metrics.metadata_registry.items():
            if not metadata.dependencies:
                continue

            for dependency in metadata.dependencies:
                if dependency.metric == source_metric:
                    self._apply_dependency(state, target_path, dependency, source_metric)

    def _apply_dependency(
        self,
        state: WorldState,
        target_metric: str,
        dependency: MetricDependency,
        source_metric: str,
    ) -> None:
        """
        Apply a single dependency.

        Args:
            state: World state
            target_metric: The metric being affected
            dependency: The dependency rule
            source_metric: The metric causing the effect
        """
        # Avoid cycles
        dep_key = f"{source_metric}->{target_metric}"
        if dep_key in self.processed_metrics:
            logger.debug(f"Skipping already processed dependency: {dep_key}")
            return

        # Get source metric value
        source_value = state.metrics.get_value(source_metric)
        if source_value is None:
            logger.warning(f"Source metric not found: {source_metric}")
            return

        # Check condition if specified
        if dependency.condition:
            if not self._evaluate_condition(source_value, dependency.condition):
                logger.debug(
                    f"Dependency condition not met: {source_metric} {dependency.condition} "
                    f"(value: {source_value})"
                )
                return

        # Get target metric value
        target_value = state.metrics.get_value(target_metric)
        if target_value is None:
            target_value = 0.0

        # Apply dependency effect
        if dependency.type == "additive":
            new_value = target_value + dependency.coefficient
        elif dependency.type == "multiplicative":
            new_value = target_value * dependency.coefficient
        else:
            logger.warning(f"Unknown dependency type: {dependency.type}")
            return

        # Validate bounds
        metadata = state.metrics.get_metadata(target_metric)
        if metadata:
            if metadata.min is not None:
                new_value = max(new_value, metadata.min)
            if metadata.max is not None:
                new_value = min(new_value, metadata.max)

        # Apply change
        state.metrics.set_value(target_metric, new_value)

        # Mark as processed
        self.processed_metrics.add(dep_key)

        logger.info(
            f"Applied dependency: {source_metric} ({source_value:.2f}) "
            f"-> {target_metric} ({target_value:.2f} -> {new_value:.2f}) "
            f"[{dependency.type}, coeff: {dependency.coefficient}]"
        )

    def _evaluate_condition(self, value: float, condition: str) -> bool:
        """
        Evaluate a condition string against a value.

        Supports:
        - "> X" (greater than)
        - "< X" (less than)
        - ">= X" (greater than or equal)
        - "<= X" (less than or equal)
        - "== X" (equal)
        - "!= X" (not equal)

        Args:
            value: The value to test
            condition: Condition string (e.g., "> 50", "<= 0.5")

        Returns:
            True if condition is met, False otherwise
        """
        condition = condition.strip()

        # Parse condition
        patterns = [
            (r"^>=\s*([\d.]+)$", lambda v, x: v >= x),
            (r"^<=\s*([\d.]+)$", lambda v, x: v <= x),
            (r"^>\s*([\d.]+)$", lambda v, x: v > x),
            (r"^<\s*([\d.]+)$", lambda v, x: v < x),
            (r"^==\s*([\d.]+)$", lambda v, x: v == x),
            (r"^!=\s*([\d.]+)$", lambda v, x: v != x),
        ]

        for pattern, comparator in patterns:
            match = re.match(pattern, condition)
            if match:
                threshold = float(match.group(1))
                return comparator(value, threshold)

        logger.warning(f"Could not parse condition: {condition}")
        return False

    def get_dependency_graph(self, state: WorldState) -> dict:
        """
        Build a dependency graph showing metric relationships.

        Returns a dictionary mapping metric paths to lists of metrics they affect.

        Args:
            state: World state with metadata registry

        Returns:
            Dict mapping source metrics to lists of (target, dependency) tuples
        """
        graph = {}

        for target_path, metadata in state.metrics.metadata_registry.items():
            if not metadata.dependencies:
                continue

            for dependency in metadata.dependencies:
                source = dependency.metric
                if source not in graph:
                    graph[source] = []

                graph[source].append((target_path, dependency))

        return graph

    def detect_cycles(self, state: WorldState) -> List[List[str]]:
        """
        Detect circular dependencies in the metric graph.

        Returns a list of cycles, where each cycle is a list of metric paths.

        Args:
            state: World state with metadata registry

        Returns:
            List of cycles (each cycle is a list of metric paths)
        """
        graph = self.get_dependency_graph(state)
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in graph:
                for target, _ in graph[node]:
                    if target not in visited:
                        dfs(target, path[:])
                    elif target in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(target)
                        cycle = path[cycle_start:] + [target]
                        cycles.append(cycle)

            rec_stack.remove(node)

        for metric_path in graph:
            if metric_path not in visited:
                dfs(metric_path, [])

        return cycles
