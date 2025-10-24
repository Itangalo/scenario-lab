"""
World State Manager - Tracks and updates the state of the scenario world
"""
from typing import Dict, List, Any
from datetime import datetime
from markdown_utils import clean_markdown_formatting


class WorldState:
    """Manages the world state throughout the scenario"""

    def __init__(self, initial_state: str, scenario_name: str, turn_duration: str):
        self.scenario_name = scenario_name
        self.turn_duration = turn_duration
        self.current_turn = 0
        self.states = {0: initial_state}  # Turn 0 is the initial state
        self.actor_decisions = {}  # {turn: {actor_name: {reasoning, action}}}

    def get_current_state(self) -> str:
        """Get the current world state description"""
        return self.states[self.current_turn]

    def record_actor_decision(self, turn: int, actor_name: str, decision: Dict[str, Any]):
        """Record an actor's decision for a given turn"""
        if turn not in self.actor_decisions:
            self.actor_decisions[turn] = {}
        self.actor_decisions[turn][actor_name] = decision

    def update_state(self, new_state: str):
        """Update the world state for the next turn"""
        self.current_turn += 1
        self.states[self.current_turn] = new_state

    def get_actor_decisions_for_turn(self, turn: int) -> Dict[str, Dict[str, Any]]:
        """Get all actor decisions for a specific turn"""
        return self.actor_decisions.get(turn, {})

    def to_markdown(self, turn: int) -> str:
        """Generate markdown representation of world state for a specific turn"""
        state = self.states.get(turn, "No state available")
        decisions = self.actor_decisions.get(turn, {})

        md = f"# World State - Turn {turn}\n\n"
        md += f"**Scenario:** {self.scenario_name}\n\n"
        md += f"**Turn Duration:** {self.turn_duration}\n\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"
        md += "## Current Situation\n\n"
        md += f"{state}\n\n"

        if decisions:
            md += "---\n\n"
            md += "## Actions Taken This Turn\n\n"
            for actor_name, decision in decisions.items():
                md += f"### {actor_name}\n\n"
                md += f"{decision['action']}\n\n"

        return md

    def actor_decision_to_markdown(self, turn: int, actor_name: str, decision: Dict[str, Any]) -> str:
        """Generate markdown for a specific actor's decision"""
        md = f"# {actor_name} - Turn {turn}\n\n"
        md += f"**Scenario:** {self.scenario_name}\n\n"
        md += f"**Turn Duration:** {self.turn_duration}\n\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"

        # Include goals if present
        if decision.get('goals'):
            md += "## Current Goals\n\n"
            md += f"{decision['goals']}\n\n"
            md += "---\n\n"

        md += "## Reasoning\n\n"
        md += f"{decision['reasoning']}\n\n"
        md += "---\n\n"
        md += "## Action\n\n"
        md += f"{decision['action']}\n\n"

        # Clean markdown to remove duplicates and normalize formatting
        md = clean_markdown_formatting(md)

        return md
