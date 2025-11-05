"""
Batch Analyzer - Statistical analysis and pattern recognition for batch results
"""
import os
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import statistics


class BatchAnalyzer:
    """
    Analyzes results from batch scenario execution to identify patterns and statistics
    """

    def __init__(self, batch_output_dir: str):
        """
        Initialize batch analyzer

        Args:
            batch_output_dir: Path to batch output directory (e.g., experiments/model-comparison)
        """
        self.batch_dir = batch_output_dir
        self.runs_dir = os.path.join(batch_output_dir, 'runs')
        self.analysis_dir = os.path.join(batch_output_dir, 'analysis')

        # Ensure analysis directory exists
        os.makedirs(self.analysis_dir, exist_ok=True)

        # Load batch configuration and state
        self.batch_config = self._load_batch_config()
        self.batch_summary = self._load_batch_summary()
        self.batch_costs = self._load_batch_costs()

        # Collected data
        self.run_data = []  # List of {run_id, variation_id, metrics, cost, success}
        self.variation_data = {}  # {variation_id: {description, runs: []}}

    def _load_batch_config(self) -> Optional[Dict]:
        """Load batch configuration"""
        config_path = os.path.join(self.batch_dir, 'batch-config.yaml')
        if not os.path.exists(config_path):
            return None

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_batch_summary(self) -> Optional[Dict]:
        """Load batch summary"""
        summary_path = os.path.join(self.batch_dir, 'batch-summary.json')
        if not os.path.exists(summary_path):
            return None

        with open(summary_path, 'r') as f:
            return json.load(f)

    def _load_batch_costs(self) -> Optional[Dict]:
        """Load batch costs"""
        costs_path = os.path.join(self.batch_dir, 'batch-costs.json')
        if not os.path.exists(costs_path):
            return None

        with open(costs_path, 'r') as f:
            return json.load(f)

    def collect_run_data(self):
        """Collect data from all runs in the batch"""
        if not os.path.exists(self.runs_dir):
            raise FileNotFoundError(f"Runs directory not found: {self.runs_dir}")

        # Iterate through all run directories
        for run_id in os.listdir(self.runs_dir):
            run_path = os.path.join(self.runs_dir, run_id)

            if not os.path.isdir(run_path):
                continue

            # Extract variation ID from run_id (format: var-XXX-run-YYY)
            try:
                variation_id = int(run_id.split('-')[1])
            except (IndexError, ValueError):
                continue

            # Load run data
            metrics_path = os.path.join(run_path, 'metrics.json')
            costs_path = os.path.join(run_path, 'costs.json')
            state_path = os.path.join(run_path, 'scenario-state.json')

            run_info = {
                'run_id': run_id,
                'variation_id': variation_id,
                'metrics': {},
                'cost': 0.0,
                'success': False,
                'turns_completed': 0
            }

            # Load metrics
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    metrics_data = json.load(f)
                    run_info['metrics'] = metrics_data.get('final_metrics', {})

            # Load cost
            if os.path.exists(costs_path):
                with open(costs_path, 'r') as f:
                    cost_data = json.load(f)
                    run_info['cost'] = cost_data.get('total_cost', 0.0)

            # Load state for success status
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state_data = json.load(f)
                    run_info['success'] = state_data.get('status') == 'completed'
                    run_info['turns_completed'] = state_data.get('current_turn', 0)

            self.run_data.append(run_info)

            # Group by variation
            if variation_id not in self.variation_data:
                self.variation_data[variation_id] = {
                    'runs': [],
                    'description': ''  # Will be filled later
                }
            self.variation_data[variation_id]['runs'].append(run_info)

    def calculate_metric_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate statistics for each metric across all runs

        Returns:
            Dict mapping metric_name to statistics (mean, std, min, max, etc.)
        """
        # Collect all metrics across runs
        metric_values = defaultdict(list)

        for run in self.run_data:
            if run['success']:
                for metric_name, value in run['metrics'].items():
                    # Only include numeric metrics
                    if isinstance(value, (int, float)):
                        metric_values[metric_name].append(value)

        # Calculate statistics
        stats = {}
        for metric_name, values in metric_values.items():
            if len(values) == 0:
                continue

            stats[metric_name] = {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0.0,
                'values': values  # Keep raw values for further analysis
            }

        return stats

    def calculate_variation_statistics(self) -> Dict[int, Dict[str, Any]]:
        """
        Calculate statistics per variation

        Returns:
            Dict mapping variation_id to statistics
        """
        variation_stats = {}

        for variation_id, var_data in self.variation_data.items():
            runs = var_data['runs']
            successful_runs = [r for r in runs if r['success']]

            # Basic stats
            stats = {
                'variation_id': variation_id,
                'description': var_data.get('description', ''),
                'total_runs': len(runs),
                'successful_runs': len(successful_runs),
                'success_rate': len(successful_runs) / len(runs) if len(runs) > 0 else 0.0,
                'metrics': {}
            }

            # Aggregate metrics
            if successful_runs:
                # Collect metric values per variation
                metric_values = defaultdict(list)
                for run in successful_runs:
                    for metric_name, value in run['metrics'].items():
                        if isinstance(value, (int, float)):
                            metric_values[metric_name].append(value)

                # Calculate per-metric stats for this variation
                for metric_name, values in metric_values.items():
                    if len(values) > 0:
                        stats['metrics'][metric_name] = {
                            'mean': statistics.mean(values),
                            'median': statistics.median(values),
                            'min': min(values),
                            'max': max(values),
                            'stdev': statistics.stdev(values) if len(values) > 1 else 0.0
                        }

            # Cost statistics
            costs = [r['cost'] for r in runs]
            if costs:
                stats['cost'] = {
                    'total': sum(costs),
                    'mean': statistics.mean(costs),
                    'min': min(costs),
                    'max': max(costs)
                }

            variation_stats[variation_id] = stats

        return variation_stats

    def compare_variations(self, metric_name: str) -> List[Tuple[int, float]]:
        """
        Compare variations based on a specific metric

        Args:
            metric_name: Name of metric to compare

        Returns:
            List of (variation_id, mean_value) tuples, sorted by mean value
        """
        comparison = []

        for variation_id, var_data in self.variation_data.items():
            successful_runs = [r for r in var_data['runs'] if r['success']]
            metric_values = []

            for run in successful_runs:
                if metric_name in run['metrics']:
                    value = run['metrics'][metric_name]
                    if isinstance(value, (int, float)):
                        metric_values.append(value)

            if metric_values:
                mean_value = statistics.mean(metric_values)
                comparison.append((variation_id, mean_value))

        # Sort by mean value (descending)
        comparison.sort(key=lambda x: x[1], reverse=True)
        return comparison

    def identify_patterns(self) -> Dict[str, Any]:
        """
        Identify patterns across runs (e.g., success factors, failure modes)

        Returns:
            Dict with identified patterns
        """
        patterns = {
            'success_factors': [],
            'failure_modes': [],
            'cost_efficiency': []
        }

        # Analyze success vs failure
        successful_runs = [r for r in self.run_data if r['success']]
        failed_runs = [r for r in self.run_data if not r['success']]

        patterns['success_rate'] = len(successful_runs) / len(self.run_data) if self.run_data else 0.0
        patterns['total_runs'] = len(self.run_data)
        patterns['successful_runs'] = len(successful_runs)
        patterns['failed_runs'] = len(failed_runs)

        # Identify variations with highest success rate
        variation_success = {}
        for variation_id, var_data in self.variation_data.items():
            runs = var_data['runs']
            successful = len([r for r in runs if r['success']])
            success_rate = successful / len(runs) if runs else 0.0
            variation_success[variation_id] = success_rate

        if variation_success:
            best_variation = max(variation_success.items(), key=lambda x: x[1])
            patterns['best_variation'] = {
                'variation_id': best_variation[0],
                'success_rate': best_variation[1]
            }

        # Analyze cost efficiency (success per dollar)
        cost_efficiency = []
        for variation_id, stats in self.calculate_variation_statistics().items():
            if stats['successful_runs'] > 0 and stats['cost']['total'] > 0:
                efficiency = stats['successful_runs'] / stats['cost']['total']
                cost_efficiency.append((variation_id, efficiency))

        if cost_efficiency:
            cost_efficiency.sort(key=lambda x: x[1], reverse=True)
            patterns['cost_efficiency'] = [
                {'variation_id': var_id, 'runs_per_dollar': eff}
                for var_id, eff in cost_efficiency
            ]

        return patterns

    def generate_analysis_report(self) -> str:
        """
        Generate comprehensive markdown analysis report

        Returns:
            Markdown report as string
        """
        # Collect data
        self.collect_run_data()

        metric_stats = self.calculate_metric_statistics()
        variation_stats = self.calculate_variation_statistics()
        patterns = self.identify_patterns()

        # Build report
        report = []
        report.append("# Batch Analysis Report\n")

        if self.batch_config:
            report.append(f"**Experiment:** {self.batch_config.get('experiment_name', 'Unknown')}\n")

        report.append(f"**Total Runs:** {patterns['total_runs']}")
        report.append(f"**Successful Runs:** {patterns['successful_runs']}")
        report.append(f"**Failed Runs:** {patterns['failed_runs']}")
        report.append(f"**Success Rate:** {patterns['success_rate']*100:.1f}%\n")

        # Overall metrics
        report.append("## Overall Metrics\n")
        for metric_name, stats in sorted(metric_stats.items()):
            report.append(f"### {metric_name}")
            report.append(f"- Mean: {stats['mean']:.2f}")
            report.append(f"- Median: {stats['median']:.2f}")
            report.append(f"- Std Dev: {stats['stdev']:.2f}")
            report.append(f"- Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
            report.append("")

        # Variation comparison
        report.append("## Variation Comparison\n")
        for variation_id, stats in sorted(variation_stats.items()):
            report.append(f"### Variation {variation_id}")
            if stats['description']:
                report.append(f"**Configuration:** {stats['description']}\n")
            report.append(f"- Runs: {stats['successful_runs']}/{stats['total_runs']}")
            report.append(f"- Success Rate: {stats['success_rate']*100:.1f}%")

            if 'cost' in stats:
                report.append(f"- Total Cost: ${stats['cost']['total']:.2f}")
                report.append(f"- Avg Cost/Run: ${stats['cost']['mean']:.3f}")

            if stats['metrics']:
                report.append("\n**Metrics:**")
                for metric_name, metric_stats in sorted(stats['metrics'].items()):
                    report.append(f"  - {metric_name}: {metric_stats['mean']:.2f} " +
                                f"(±{metric_stats['stdev']:.2f})")

            report.append("")

        # Cost efficiency
        if patterns.get('cost_efficiency'):
            report.append("## Cost Efficiency\n")
            report.append("Ranked by successful runs per dollar:\n")
            for item in patterns['cost_efficiency']:
                report.append(f"- Variation {item['variation_id']}: " +
                            f"{item['runs_per_dollar']:.2f} runs/$")
            report.append("")

        # Save report
        report_path = os.path.join(self.analysis_dir, 'analysis-report.md')
        report_text = '\n'.join(report)
        with open(report_path, 'w') as f:
            f.write(report_text)

        return report_text

    def save_analysis_data(self):
        """Save all analysis data as JSON files"""
        self.collect_run_data()

        # Metrics analysis
        metrics_stats = self.calculate_metric_statistics()
        # Remove raw values to keep file size manageable
        for stats in metrics_stats.values():
            stats.pop('values', None)

        metrics_path = os.path.join(self.analysis_dir, 'metrics-analysis.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics_stats, f, indent=2)

        # Variation statistics
        variation_stats = self.calculate_variation_statistics()
        variation_path = os.path.join(self.analysis_dir, 'variation-statistics.json')
        with open(variation_path, 'w') as f:
            json.dump(variation_stats, f, indent=2)

        # Patterns
        patterns = self.identify_patterns()
        patterns_path = os.path.join(self.analysis_dir, 'patterns.json')
        with open(patterns_path, 'w') as f:
            json.dump(patterns, f, indent=2)


def main():
    """Command-line interface for batch analyzer"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze results from batch scenario execution'
    )
    parser.add_argument(
        'batch_dir',
        help='Path to batch output directory'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate and display analysis report'
    )

    args = parser.parse_args()

    analyzer = BatchAnalyzer(args.batch_dir)

    # Save analysis data
    analyzer.save_analysis_data()
    print(f"✓ Analysis data saved to {analyzer.analysis_dir}")

    # Generate report if requested
    if args.report:
        report = analyzer.generate_analysis_report()
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)


if __name__ == '__main__':
    main()
