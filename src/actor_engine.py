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

    def __init__(self, actor_data: Dict[str, Any], scenario_system_prompt: str = ""):
        self.name = actor_data['name']
        self.short_name = actor_data['short_name']
        self.llm_model = actor_data['llm_model']
        self.system_prompt = actor_data.get('system_prompt', '')
        self.scenario_system_prompt = scenario_system_prompt
        self.description = actor_data.get('description', '')
        self.goals = actor_data.get('goals', [])
        self.constraints = actor_data.get('constraints', [])
        self.expertise = actor_data.get('expertise', {})
        self.decision_style = actor_data.get('decision_style', '')

    def make_decision(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Have the actor make a decision based on current world state

        Returns:
            Dict with 'reasoning' and 'action' keys
        """
        system_prompt, user_prompt = self._build_prompts(world_state, turn, total_turns, other_actors_decisions)
        response = self._call_llm(system_prompt, user_prompt)

        return {
            'reasoning': response.get('reasoning', ''),
            'action': response.get('action', ''),
            'raw_response': response.get('raw', '')
        }

    def _build_prompts(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None) -> tuple:
        """
        Build system and user prompts for the LLM

        Returns:
            tuple: (system_prompt, user_prompt)
        """
        # Combine scenario and actor system prompts
        combined_system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            combined_system_prompt += "\n\n" + self.system_prompt

        # Format other actors' decisions if this is simultaneous reveal
        other_decisions_text = ""
        if other_actors_decisions:
            other_decisions_text = "\n\n## Other Actors' Decisions This Turn\n\n"
            for actor_name, decision in other_actors_decisions.items():
                other_decisions_text += f"**{actor_name}:**\n{decision}\n\n"

        # Build user prompt with current situation and task
        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}
{other_decisions_text}

## Your Task

Decide what action to take this turn. Provide your response in the following format:

**REASONING:**
[Explain your thinking, considering your goals, constraints, and the current situation]

**ACTION:**
[Describe the specific action you will take this turn - be concrete and specific]

Remember: This is turn {turn} of {total_turns}. Consider how your action moves toward your goals while addressing the current situation.
"""

        return combined_system_prompt, user_prompt

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API with system and user prompts"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Build messages array with system and user roles
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": self.llm_model,
            "messages": messages
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


def load_actor(scenario_path: str, actor_short_name: str, scenario_system_prompt: str = "") -> Actor:
    """Load an actor from YAML file"""
    actor_file = os.path.join(scenario_path, 'actors', f'{actor_short_name}.yaml')

    with open(actor_file, 'r') as f:
        actor_data = yaml.safe_load(f)

    return Actor(actor_data, scenario_system_prompt)
