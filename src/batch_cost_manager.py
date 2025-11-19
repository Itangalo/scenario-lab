"""
Batch Cost Manager - Manages budget and cost controls for batch execution
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class BatchCostManager:
    """
    Manages costs and budget limits for batch scenario execution
    """

    def __init__(
        self,
        budget_limit: Optional[float] = None,
        cost_per_run_limit: Optional[float] = None
    ):
        """
        Initialize batch cost manager

        Args:
            budget_limit: Maximum total spend for entire batch (USD)
            cost_per_run_limit: Maximum cost per individual run (USD)
        """
        self.budget_limit = budget_limit
        self.cost_per_run_limit = cost_per_run_limit

        # Tracking
        self.total_spent = 0.0
        self.run_costs = []  # List of {run_id, variation_id, cost, timestamp}
        self.variation_costs = {}  # {variation_id: total_cost}
        self.start_time = None
        self.end_time = None

        # Statistics
        self.runs_completed = 0
        self.runs_failed = 0
        self.runs_budget_exceeded = 0

    def start_batch(self):
        """Mark the start of batch execution"""
        self.start_time = datetime.now()

    def end_batch(self):
        """Mark the end of batch execution"""
        self.end_time = datetime.now()

    def can_start_run(self) -> tuple[bool, Optional[str]]:
        """
        Check if a new run can be started within budget constraints

        Returns:
            Tuple of (can_start: bool, reason: Optional[str])
        """
        if self.budget_limit is not None:
            if self.total_spent >= self.budget_limit:
                return False, f"Budget limit reached (${self.total_spent:.2f} / ${self.budget_limit:.2f})"

            # Check if we have enough budget for at least one more run
            if self.cost_per_run_limit is not None:
                remaining = self.budget_limit - self.total_spent
                if remaining < self.cost_per_run_limit:
                    return False, f"Insufficient budget for another run (${remaining:.2f} remaining, need ${self.cost_per_run_limit:.2f})"

        return True, None

    def record_run_cost(
        self,
        run_id: str,
        variation_id: int,
        cost: float,
        success: bool = True
    ):
        """
        Record the cost of a completed run

        Args:
            run_id: Unique identifier for the run
            variation_id: ID of the variation
            cost: Actual cost incurred (USD)
            success: Whether the run completed successfully
        """
        self.run_costs.append({
            'run_id': run_id,
            'variation_id': variation_id,
            'cost': cost,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

        self.total_spent += cost

        # Track by variation
        if variation_id not in self.variation_costs:
            self.variation_costs[variation_id] = 0.0
        self.variation_costs[variation_id] += cost

        # Update statistics
        if success:
            self.runs_completed += 1
        else:
            self.runs_failed += 1

    def check_run_cost(self, cost: float) -> tuple[bool, Optional[str]]:
        """
        Check if a run's cost is within limits

        Args:
            cost: Cost to check

        Returns:
            Tuple of (within_limit: bool, reason: Optional[str])
        """
        if self.cost_per_run_limit is not None and cost > self.cost_per_run_limit:
            self.runs_budget_exceeded += 1
            return False, f"Run cost ${cost:.2f} exceeds limit ${self.cost_per_run_limit:.2f}"

        return True, None

    def get_remaining_budget(self) -> Optional[float]:
        """
        Get remaining budget

        Returns:
            Remaining budget in USD, or None if no limit set
        """
        if self.budget_limit is None:
            return None

        return max(0.0, self.budget_limit - self.total_spent)

    def estimate_runs_remaining(self) -> Optional[int]:
        """
        Estimate how many more runs can be completed within budget

        Returns:
            Estimated number of runs, or None if no limit set
        """
        remaining = self.get_remaining_budget()
        if remaining is None:
            return None

        if self.cost_per_run_limit is not None:
            # Use per-run limit as estimate
            return int(remaining / self.cost_per_run_limit)

        if self.runs_completed > 0:
            # Use average cost of completed runs
            # Safe division: runs_completed > 0 is checked above
            avg_cost = self.total_spent / self.runs_completed
            if avg_cost > 0:
                return int(remaining / avg_cost)

        return None

    def get_average_cost_per_run(self) -> Optional[float]:
        """
        Get average cost per run for completed runs

        Returns:
            Average cost in USD, or None if no runs completed
        """
        if self.runs_completed == 0:
            return None

        return self.total_spent / self.runs_completed

    def get_variation_statistics(self) -> Dict[int, Dict[str, Any]]:
        """
        Get cost statistics per variation

        Returns:
            Dict mapping variation_id to statistics
        """
        stats = {}

        for variation_id, total_cost in self.variation_costs.items():
            # Count runs for this variation (single pass optimization)
            num_runs = 0
            successful_runs = 0
            for r in self.run_costs:
                if r['variation_id'] == variation_id:
                    num_runs += 1
                    if r['success']:
                        successful_runs += 1

            stats[variation_id] = {
                'total_cost': total_cost,
                'num_runs': num_runs,
                'successful_runs': successful_runs,
                'avg_cost_per_run': total_cost / num_runs if num_runs > 0 else 0.0
            }

        return stats

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of batch costs

        Returns:
            Summary dictionary
        """
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            'total_spent': self.total_spent,
            'budget_limit': self.budget_limit,
            'cost_per_run_limit': self.cost_per_run_limit,
            'remaining_budget': self.get_remaining_budget(),
            'runs_completed': self.runs_completed,
            'runs_failed': self.runs_failed,
            'runs_budget_exceeded': self.runs_budget_exceeded,
            'avg_cost_per_run': self.get_average_cost_per_run(),
            'duration_seconds': duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

    def save_to_file(self, output_path: str):
        """
        Save cost tracking data to JSON file

        Args:
            output_path: Path to save JSON file
        """
        data = {
            'summary': self.get_summary(),
            'run_costs': self.run_costs,
            'variation_statistics': self.get_variation_statistics()
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, input_path: str):
        """
        Load cost tracking data from JSON file (for resumption)

        Args:
            input_path: Path to JSON file
        """
        with open(input_path, 'r') as f:
            data = json.load(f)

        summary = data.get('summary', {})
        self.total_spent = summary.get('total_spent', 0.0)
        self.runs_completed = summary.get('runs_completed', 0)
        self.runs_failed = summary.get('runs_failed', 0)
        self.runs_budget_exceeded = summary.get('runs_budget_exceeded', 0)

        if summary.get('start_time'):
            self.start_time = datetime.fromisoformat(summary['start_time'])

        self.run_costs = data.get('run_costs', [])

        # Rebuild variation_costs
        self.variation_costs = {}
        for run in self.run_costs:
            var_id = run['variation_id']
            if var_id not in self.variation_costs:
                self.variation_costs[var_id] = 0.0
            self.variation_costs[var_id] += run['cost']
