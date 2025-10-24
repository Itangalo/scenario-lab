"""
Scenario State Manager - Handles saving and loading scenario state for resumption
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from world_state import WorldState
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker


class ScenarioStateManager:
    """Manages saving and loading scenario state for resumption and branching"""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.state_file = os.path.join(output_path, 'scenario-state.json')

    def save_state(
        self,
        scenario_name: str,
        scenario_path: str,
        status: str,
        current_turn: int,
        total_turns: int,
        world_state: WorldState,
        actors: Dict[str, Any],
        cost_tracker: CostTracker,
        metrics_tracker: MetricsTracker,
        communication_manager: Any = None,
        halt_reason: Optional[str] = None,
        started_at: Optional[str] = None
    ):
        """
        Save complete scenario state to JSON file

        Args:
            scenario_name: Name of the scenario
            scenario_path: Path to scenario definition directory
            status: running, halted, or completed
            current_turn: Most recently completed turn (0 if none completed)
            total_turns: Total turns planned for scenario
            world_state: WorldState object
            actors: Dictionary of Actor objects by short_name
            cost_tracker: CostTracker object
            metrics_tracker: MetricsTracker object
            communication_manager: CommunicationManager object (optional)
            halt_reason: Optional reason for halt (rate_limit, credit_limit, max_turns, etc.)
            started_at: ISO timestamp when run started (preserved on resume)
        """
        # Prepare actor data
        actors_data = {}
        for short_name, actor in actors.items():
            actors_data[short_name] = {
                'name': actor.name,
                'short_name': actor.short_name,
                'llm_model': actor.llm_model
            }

        # Build state object
        state = {
            'scenario_name': scenario_name,
            'scenario_path': scenario_path,
            'status': status,
            'halt_reason': halt_reason,
            'current_turn': current_turn,
            'total_turns': total_turns,
            'completed_turns': list(range(1, current_turn + 1)) if current_turn > 0 else [],
            'world_state': {
                'current_state': world_state.get_current_state(),
                'current_turn': world_state.current_turn,
                'turn_duration': world_state.turn_duration,
                'scenario_name': world_state.scenario_name,
                'states': world_state.states,
                'actor_decisions': world_state.actor_decisions
            },
            'actors': actors_data,
            'cost_tracker_state': {
                'total_cost': cost_tracker.total_cost,
                'total_tokens': cost_tracker.total_tokens,
                'costs_by_actor': cost_tracker.costs_by_actor,
                'costs_by_turn': cost_tracker.costs_by_turn,
                'world_state_costs': cost_tracker.world_state_costs
            },
            'metrics_tracker_state': {
                'metrics_by_turn': metrics_tracker.metrics_by_turn,
                'final_metrics': metrics_tracker.final_metrics
            },
            'communication_manager_state': communication_manager.to_dict() if communication_manager else None,
            'execution_metadata': {
                'started_at': started_at or datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'output_path': self.output_path
            }
        }

        # Write to file
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> Dict[str, Any]:
        """
        Load scenario state from JSON file

        Returns:
            Dictionary containing complete scenario state

        Raises:
            FileNotFoundError: If state file doesn't exist
        """
        if not self.state_exists():
            raise FileNotFoundError(f"No state file found at {self.state_file}")

        with open(self.state_file, 'r') as f:
            return json.load(f)

    def state_exists(self) -> bool:
        """Check if state file exists"""
        return os.path.exists(self.state_file)

    def mark_completed(self):
        """Mark scenario as completed in state file"""
        if self.state_exists():
            state = self.load_state()
            state['status'] = 'completed'
            state['halt_reason'] = None
            state['execution_metadata']['last_updated'] = datetime.now().isoformat()

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

    def mark_halted(self, reason: str):
        """
        Mark scenario as halted with reason

        Args:
            reason: Reason for halt (rate_limit, credit_limit, max_turns, manual, etc.)
        """
        if self.state_exists():
            state = self.load_state()
            state['status'] = 'halted'
            state['halt_reason'] = reason
            state['execution_metadata']['last_updated'] = datetime.now().isoformat()

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

    def get_status(self) -> Optional[str]:
        """Get current status of scenario run (running, halted, completed, or None if no state)"""
        if not self.state_exists():
            return None

        state = self.load_state()
        return state.get('status')

    def get_halt_reason(self) -> Optional[str]:
        """Get halt reason if scenario is halted"""
        if not self.state_exists():
            return None

        state = self.load_state()
        return state.get('halt_reason')
