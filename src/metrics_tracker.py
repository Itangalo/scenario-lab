"""
Metrics Tracker - Manages and tracks quantitative metrics throughout scenario execution
"""
import json
import yaml
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class MetricsTracker:
    """
    Tracks quantitative metrics defined in scenario configuration
    """

    def __init__(self, metrics_config_path: Optional[str] = None):
        """
        Initialize metrics tracker

        Args:
            metrics_config_path: Path to metrics.yaml file (optional)
        """
        self.metrics_definitions = {}
        self.metrics_by_turn = {}  # {turn: {metric_name: value}}
        self.final_metrics = {}
        self.scenario_name = ""

        if metrics_config_path and Path(metrics_config_path).exists():
            self.load_metrics_definitions(metrics_config_path)

    def load_metrics_definitions(self, config_path: str):
        """Load metrics definitions from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.metrics_definitions = config.get('metrics', {})
        self.scenario_name = config.get('scenario_name', '')

    def record_metric(self, turn: int, metric_name: str, value: Any):
        """
        Record a metric value for a specific turn

        Args:
            turn: Turn number
            metric_name: Name of the metric
            value: Metric value (number, string, etc.)
        """
        if turn not in self.metrics_by_turn:
            self.metrics_by_turn[turn] = {}

        self.metrics_by_turn[turn][metric_name] = value

    def extract_metrics_from_text(
        self,
        turn: int,
        text: str,
        actor_name: Optional[str] = None
    ):
        """
        Extract metrics from text using patterns defined in metrics config

        Args:
            turn: Turn number
            text: Text to extract metrics from (world state, actor decision, etc.)
            actor_name: Optional actor name for actor-specific metrics
        """
        for metric_name, metric_def in self.metrics_definitions.items():
            # Skip if this is an actor-specific metric and we don't have actor context
            if metric_def.get('actor_specific') and not actor_name:
                continue

            # Skip if metric is for a different actor
            if metric_def.get('actor_specific') and metric_def.get('actor') != actor_name:
                continue

            extraction_method = metric_def.get('extraction_method', 'regex')

            if extraction_method == 'regex':
                pattern = metric_def.get('pattern')
                if pattern:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Take the last match (most recent mention)
                        value = matches[-1]

                        # If value is a tuple (from multiple regex groups), extract the non-empty value
                        if isinstance(value, tuple):
                            value = next((v for v in value if v), '')

                        # Convert to appropriate type
                        value_type = metric_def.get('type', 'string')
                        value = self._convert_value(value, value_type)

                        self.record_metric(turn, metric_name, value)

            elif extraction_method == 'manual':
                # Manual extraction - value will be set directly via record_metric
                pass

    def set_final_metrics(self):
        """Set final metrics from the last turn"""
        if self.metrics_by_turn:
            last_turn = max(self.metrics_by_turn.keys())
            self.final_metrics = self.metrics_by_turn[last_turn].copy()

    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        return {
            "scenario": self.scenario_name,
            "metrics_definitions": self.metrics_definitions,
            "metrics_by_turn": self.metrics_by_turn,
            "final_metrics": self.final_metrics,
            "summary_statistics": self._calculate_summary_statistics()
        }

    def save_to_file(self, filepath: str):
        """Save metrics to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_metric_summary(), f, indent=2)

    def _convert_value(self, value: str, value_type: str) -> Any:
        """Convert string value to appropriate type"""
        try:
            if value_type == 'integer':
                return int(value)
            elif value_type == 'float':
                # Handle scientific notation (e.g., "10^25")
                if '^' in value:
                    base, exp = value.split('^')
                    return float(base) ** float(exp)
                return float(value)
            elif value_type == 'boolean':
                # For boolean metrics, any non-empty match indicates True
                # (the pattern itself defines what constitutes a "true" condition)
                if value:
                    return True
                return value.lower() in ['true', 'yes', '1', 'enabled']
            else:  # string or unknown
                return value
        except (ValueError, TypeError):
            return value  # Return as-is if conversion fails

    def _calculate_summary_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics for numeric metrics"""
        stats = {}

        for metric_name, metric_def in self.metrics_definitions.items():
            metric_type = metric_def.get('type', 'string')

            if metric_type in ['integer', 'float']:
                values = []
                for turn_metrics in self.metrics_by_turn.values():
                    if metric_name in turn_metrics:
                        values.append(turn_metrics[metric_name])

                if values:
                    stats[metric_name] = {
                        "min": min(values),
                        "max": max(values),
                        "mean": sum(values) / len(values),
                        "count": len(values),
                        "values": values
                    }

        return stats

    def get_current_metrics(self) -> Optional[Dict[str, float]]:
        """
        Get the most recent metrics values for conditional event evaluation

        Returns:
            Dict mapping metric names to their latest values, or None if no metrics yet
        """
        if not self.metrics_by_turn:
            return None

        # Get metrics from the most recent turn
        last_turn = max(self.metrics_by_turn.keys())
        return self.metrics_by_turn[last_turn].copy()

    def print_summary(self):
        """Print a formatted metrics summary"""
        print("\n" + "="*60)
        print("METRICS SUMMARY")
        print("="*60)

        if not self.metrics_by_turn:
            print("\nNo metrics recorded.")
            return

        print("\nMetrics by Turn:")
        for turn in sorted(self.metrics_by_turn.keys()):
            print(f"\n  Turn {turn}:")
            for metric_name, value in self.metrics_by_turn[turn].items():
                metric_def = self.metrics_definitions.get(metric_name, {})
                unit = metric_def.get('unit', '')
                if unit:
                    print(f"    {metric_name}: {value} {unit}")
                else:
                    print(f"    {metric_name}: {value}")

        if self.final_metrics:
            print("\nFinal Metrics:")
            for metric_name, value in self.final_metrics.items():
                metric_def = self.metrics_definitions.get(metric_name, {})
                unit = metric_def.get('unit', '')
                if unit:
                    print(f"  {metric_name}: {value} {unit}")
                else:
                    print(f"  {metric_name}: {value}")

        stats = self._calculate_summary_statistics()
        if stats:
            print("\nSummary Statistics:")
            for metric_name, stat_data in stats.items():
                print(f"\n  {metric_name}:")
                print(f"    Min: {stat_data['min']}")
                print(f"    Max: {stat_data['max']}")
                print(f"    Mean: {stat_data['mean']:.2f}")
                print(f"    Trend: {stat_data['values']}")

        print("="*60 + "\n")
