"""
Actor Engine - Manages AI-controlled actors and their decision-making
"""
import os
import yaml
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Actor:
    """Represents a single actor in the scenario"""

    def __init__(self, actor_data: Dict[str, Any]):
        self.name = actor_data['name']
        self.short_name = actor_data['short_name']
        self.llm_model = actor_data['llm_model']
        self.description = actor_data['description']
        self.goals = actor_data.get('goals', [])
        self.constraints = actor_data.get('constraints', [])
        self.expertise = actor_data.get('expertise', {})
        self.decision_style = actor_data.get('decision_style', '')

    def make_decision(self, world_state: str, turn: int, other_actors_decisions: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Have the actor make a decision based on current world state

        Returns:
            Dict with 'reasoning' and 'action' keys
        """
        prompt = self._build_prompt(world_state, turn, other_actors_decisions)
        response = self._call_llm(prompt)

        return {
            'reasoning': response.get('reasoning', ''),
            'action': response.get('action', ''),
            'raw_response': response.get('raw', '')
        }

    def _build_prompt(self, world_state: str, turn: int, other_actors_decisions: Dict[str, str] = None) -> str:
        """Build the prompt for the LLM"""

        # Format goals
        goals_text = "\n".join([f"  - {goal}" for goal in self.goals])

        # Format constraints
        constraints_text = "\n".join([f"  - {constraint}" for constraint in self.constraints])

        # Format other actors' decisions if this is simultaneous reveal
        other_decisions_text = ""
        if other_actors_decisions:
            other_decisions_text = "\n\n## Other Actors' Decisions This Turn\n\n"
            for actor_name, decision in other_actors_decisions.items():
                other_decisions_text += f"**{actor_name}:**\n{decision}\n\n"

        prompt = f"""You are participating in a scenario simulation.

## Your Identity

{self.description}

## Your Goals

{goals_text}

## Your Constraints

{constraints_text}

## Your Decision-Making Style

{self.decision_style}

## Current Situation (Turn {turn})

{world_state}
{other_decisions_text}

## Your Task

Decide what action to take this turn. Provide your response in the following format:

**REASONING:**
[Explain your thinking, considering your goals, constraints, and the current situation]

**ACTION:**
[Describe the specific action you will take this turn - be concrete and specific]

Remember: This is turn {turn} of a 3-turn negotiation. Consider how your action moves toward your goals while addressing the current situation.
"""
        return prompt

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.llm_model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Parse the response
        reasoning = ""
        action = ""

        if "**REASONING:**" in content and "**ACTION:**" in content:
            parts = content.split("**ACTION:**")
            reasoning_part = parts[0].split("**REASONING:**")[1].strip()
            action_part = parts[1].strip()
            reasoning = reasoning_part
            action = action_part
        else:
            # Fallback if format not followed
            reasoning = "No structured reasoning provided"
            action = content

        return {
            'reasoning': reasoning,
            'action': action,
            'raw': content
        }


def load_actor(scenario_path: str, actor_short_name: str) -> Actor:
    """Load an actor from YAML file"""
    actor_file = os.path.join(scenario_path, 'actors', f'{actor_short_name}.yaml')

    with open(actor_file, 'r') as f:
        actor_data = yaml.safe_load(f)

    return Actor(actor_data)
