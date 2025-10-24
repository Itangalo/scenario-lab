"""
Actor Engine - Manages AI-controlled actors and their decision-making
"""
import os
import yaml
import requests
from typing import Dict, Any, List
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

    def make_decision(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None, communications_context: str = "") -> Dict[str, Any]:
        """
        Have the actor make a decision based on current world state

        Args:
            world_state: Current world state description
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors_decisions: Optional other actors' decisions
            communications_context: Optional context from private communications

        Returns:
            Dict with 'reasoning' and 'action' keys
        """
        system_prompt, user_prompt = self._build_prompts(world_state, turn, total_turns, other_actors_decisions, communications_context)
        response = self._call_llm(system_prompt, user_prompt)

        return {
            'reasoning': response.get('reasoning', ''),
            'action': response.get('action', ''),
            'raw_response': response.get('raw', ''),
            'tokens_used': response.get('tokens_used', 0)
        }

    def decide_communication(self, world_state: str, turn: int, total_turns: int, other_actors: List[str]) -> Dict[str, Any]:
        """
        Decide whether to initiate private communication before public action

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors: List of other actor names

        Returns:
            Dict with communication preferences
        """
        system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            system_prompt += "\n\n" + self.system_prompt

        other_actors_list = ", ".join(other_actors)

        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}

## Communication Phase

Before making your public action, you have the opportunity to communicate privately with other actors.

Available actors for private communication: {other_actors_list}

Consider:
- Would private negotiation help achieve your goals?
- Do you want to propose a deal or share information privately?
- Would forming a coalition be beneficial?

## Your Response

Respond in this format:

**INITIATE_BILATERAL:** [yes/no - do you want to negotiate privately with one actor?]
**TARGET_ACTOR:** [if yes, which actor name? if no, write "none"]
**PROPOSED_MESSAGE:** [if yes, what would you say to them? if no, write "none"]

**REASONING:** [Brief explanation of your communication strategy]
"""

        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        initiate = 'yes' in response.get('raw', '').lower().split('**INITIATE_BILATERAL:**')[1].split('**')[0].lower() if '**INITIATE_BILATERAL:**' in response.get('raw', '') else False

        target_actor = None
        message = None

        if initiate and '**TARGET_ACTOR:**' in response.get('raw', ''):
            target_text = response.get('raw', '').split('**TARGET_ACTOR:**')[1].split('**')[0].strip()
            if target_text.lower() != 'none' and target_text in other_actors:
                target_actor = target_text

        if initiate and target_actor and '**PROPOSED_MESSAGE:**' in response.get('raw', ''):
            message_text = response.get('raw', '').split('**PROPOSED_MESSAGE:**')[1].split('**REASONING:**')[0].strip()
            if message_text.lower() != 'none':
                message = message_text

        reasoning = ""
        if '**REASONING:**' in response.get('raw', ''):
            reasoning = response.get('raw', '').split('**REASONING:**')[1].strip()

        return {
            'initiate_bilateral': bool(target_actor and message),
            'target_actor': target_actor,
            'message': message,
            'reasoning': reasoning,
            'tokens_used': response.get('tokens_used', 0)
        }

    def respond_to_bilateral(self, world_state: str, turn: int, total_turns: int, initiator: str, message: str) -> Dict[str, Any]:
        """
        Respond to a bilateral communication initiation

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            initiator: Name of actor who initiated communication
            message: Message from initiator

        Returns:
            Dict with response
        """
        system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            system_prompt += "\n\n" + self.system_prompt

        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}

## Private Communication

**{initiator}** has initiated private communication with you:

"{message}"

## Your Response

Respond to their message. This is a private negotiation - only you and {initiator} will see this.

Provide your response in this format:

**RESPONSE:**
[Your response to {initiator}]

**INTERNAL_NOTES:**
[Your private thoughts about this negotiation - what are you trying to achieve? Will you follow through?]
"""

        response = self._call_llm(system_prompt, user_prompt)

        # Parse response
        response_text = ""
        internal_notes = ""

        if '**RESPONSE:**' in response.get('raw', ''):
            response_text = response.get('raw', '').split('**RESPONSE:**')[1].split('**INTERNAL_NOTES:**')[0].strip()

        if '**INTERNAL_NOTES:**' in response.get('raw', ''):
            internal_notes = response.get('raw', '').split('**INTERNAL_NOTES:**')[1].strip()

        return {
            'response': response_text,
            'internal_notes': internal_notes,
            'tokens_used': response.get('tokens_used', 0)
        }

    def _build_prompts(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None, communications_context: str = "") -> tuple:
        """
        Build system and user prompts for the LLM

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors_decisions: Optional other actors' decisions
            communications_context: Optional context from private communications

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

        # Add communications context if provided
        communications_text = ""
        if communications_context:
            communications_text = "\n\n" + communications_context

        # Build user prompt with current situation and task
        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}
{communications_text}
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

        # Get token usage if available
        tokens_used = 0
        if 'usage' in result:
            tokens_used = result['usage'].get('total_tokens', 0)

        return {
            'reasoning': reasoning,
            'action': action,
            'raw': content,
            'tokens_used': tokens_used
        }


def load_actor(scenario_path: str, actor_short_name: str, scenario_system_prompt: str = "") -> Actor:
    """Load an actor from YAML file"""
    actor_file = os.path.join(scenario_path, 'actors', f'{actor_short_name}.yaml')

    with open(actor_file, 'r') as f:
        actor_data = yaml.safe_load(f)

    return Actor(actor_data, scenario_system_prompt)
