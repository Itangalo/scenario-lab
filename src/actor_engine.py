"""
Actor Engine - Manages AI-controlled actors and their decision-making
"""
import os
import yaml
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from api_utils import make_llm_call
from response_parser import parse_actor_decision, parse_bilateral_decision, parse_coalition_decision, parse_coalition_response
from schemas import load_actor_config, ActorConfig
from pydantic import ValidationError

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

    def make_decision(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None, communications_context: str = "", recent_goals: str = "") -> Dict[str, Any]:
        """
        Have the actor make a decision based on current world state

        Args:
            world_state: Current world state description
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors_decisions: Optional other actors' decisions
            communications_context: Optional context from private communications
            recent_goals: Optional recent goal statements from previous turns

        Returns:
            Dict with 'reasoning', 'action', and 'goals' keys
        """
        system_prompt, user_prompt = self._build_prompts(world_state, turn, total_turns, other_actors_decisions, communications_context, recent_goals)
        response = self._call_llm(system_prompt, user_prompt)

        return {
            'goals': response.get('goals', ''),
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

        # Parse response with robust error handling
        raw_response = response.get('raw', '')

        initiate = False
        if '**INITIATE_BILATERAL:**' in raw_response:
            try:
                parts = raw_response.split('**INITIATE_BILATERAL:**')[1].split('**')
                if len(parts) > 0:
                    initiate = 'yes' in parts[0].lower()
            except (IndexError, AttributeError):
                initiate = False

        target_actor = None
        message = None

        if initiate and '**TARGET_ACTOR:**' in raw_response:
            try:
                target_text = raw_response.split('**TARGET_ACTOR:**')[1].split('**')[0].strip()
                if target_text.lower() != 'none' and target_text in other_actors:
                    target_actor = target_text
            except (IndexError, AttributeError):
                pass

        if initiate and target_actor and '**PROPOSED_MESSAGE:**' in raw_response:
            try:
                message_text = raw_response.split('**PROPOSED_MESSAGE:**')[1].split('**REASONING:**')[0].strip()
                if message_text.lower() != 'none':
                    message = message_text
            except (IndexError, AttributeError):
                pass

        reasoning = ""
        if '**REASONING:**' in raw_response:
            try:
                reasoning = raw_response.split('**REASONING:**')[1].strip()
            except (IndexError, AttributeError):
                pass

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

    def decide_coalition(self, world_state: str, turn: int, total_turns: int, other_actors: List[str]) -> Dict[str, Any]:
        """
        Decide whether to propose forming a coalition

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors: List of other actor names

        Returns:
            Dict with coalition proposal
        """
        system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            system_prompt += "\n\n" + self.system_prompt

        other_actors_list = ", ".join(other_actors)

        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}

## Coalition Formation

You can propose forming a coalition with 2 or more other actors to coordinate strategy.

Available actors: {other_actors_list}

Consider:
- Would a coalition help achieve your goals?
- Which actors have aligned interests?
- What would be the coalition's purpose?

## Your Response

**PROPOSE_COALITION:** [yes/no]
**COALITION_MEMBERS:** [if yes, list actor names separated by commas; if no, write "none"]
**COALITION_PURPOSE:** [if yes, brief description of coalition's goal; if no, write "none"]

**REASONING:** [Brief explanation]
"""

        response = self._call_llm(system_prompt, user_prompt)

        # Parse response with robust error handling
        raw_response = response.get('raw', '')

        propose = False
        if '**PROPOSE_COALITION:**' in raw_response:
            try:
                parts = raw_response.split('**PROPOSE_COALITION:**')[1].split('**')
                if len(parts) > 0:
                    propose = 'yes' in parts[0].lower()
            except (IndexError, AttributeError):
                propose = False

        members = []
        purpose = ""

        if propose and '**COALITION_MEMBERS:**' in raw_response:
            try:
                members_text = raw_response.split('**COALITION_MEMBERS:**')[1].split('**')[0].strip()
                if members_text.lower() != 'none':
                    # Parse comma-separated list
                    proposed_members = [m.strip() for m in members_text.split(',')]
                    # Validate members exist
                    members = [m for m in proposed_members if m in other_actors]
            except (IndexError, AttributeError):
                pass

        if propose and members and '**COALITION_PURPOSE:**' in raw_response:
            try:
                purpose_text = raw_response.split('**COALITION_PURPOSE:**')[1].split('**REASONING:**')[0].strip()
                if purpose_text.lower() != 'none':
                    purpose = purpose_text
            except (IndexError, AttributeError):
                pass

        reasoning = ""
        if '**REASONING:**' in raw_response:
            try:
                reasoning = raw_response.split('**REASONING:**')[1].strip()
            except (IndexError, AttributeError):
                pass

        return {
            'propose_coalition': bool(propose and len(members) >= 2 and purpose),
            'members': members if propose else [],
            'purpose': purpose,
            'reasoning': reasoning,
            'tokens_used': response.get('tokens_used', 0)
        }

    def respond_to_coalition(self, world_state: str, turn: int, total_turns: int, proposer: str, members: List[str], purpose: str) -> Dict[str, Any]:
        """
        Respond to a coalition proposal

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            proposer: Name of actor who proposed coalition
            members: Proposed coalition members (including self)
            purpose: Stated purpose of coalition

        Returns:
            Dict with response (accept/reject)
        """
        system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            system_prompt += "\n\n" + self.system_prompt

        members_list = ", ".join(members)

        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}

## Coalition Proposal

**{proposer}** has proposed forming a coalition:

**Members:** {members_list}
**Purpose:** {purpose}

## Your Response

Should you join this coalition?

**DECISION:** [accept/reject]
**RESPONSE:** [Your message to the coalition members]

**INTERNAL_NOTES:** [Your private thoughts - are you committed? Will you follow through?]
"""

        response = self._call_llm(system_prompt, user_prompt)

        # Parse response with robust error handling
        raw_response = response.get('raw', '')

        decision = 'reject'  # Default to reject
        if '**DECISION:**' in raw_response:
            try:
                decision_text = raw_response.split('**DECISION:**')[1].split('**')[0].lower()
                decision = 'accept' if 'accept' in decision_text else 'reject'
            except (IndexError, AttributeError):
                decision = 'reject'

        response_text = ""
        if '**RESPONSE:**' in raw_response:
            try:
                response_text = raw_response.split('**RESPONSE:**')[1].split('**INTERNAL_NOTES:**')[0].strip()
            except (IndexError, AttributeError):
                pass

        internal_notes = ""
        if '**INTERNAL_NOTES:**' in raw_response:
            try:
                internal_notes = raw_response.split('**INTERNAL_NOTES:**')[1].strip()
            except (IndexError, AttributeError):
                pass

        return {
            'decision': decision,
            'response': response_text,
            'internal_notes': internal_notes,
            'tokens_used': response.get('tokens_used', 0)
        }

    def communicate_in_coalition(self, world_state: str, turn: int, total_turns: int, coalition_members: List[str], coalition_purpose: str, previous_messages: List[Dict]) -> Dict[str, Any]:
        """
        Communicate within an established coalition

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            coalition_members: Members of this coalition
            coalition_purpose: Purpose of the coalition
            previous_messages: Previous messages in this coalition

        Returns:
            Dict with message
        """
        system_prompt = self.scenario_system_prompt
        if self.system_prompt:
            system_prompt += "\n\n" + self.system_prompt

        members_list = ", ".join(coalition_members)

        # Format previous messages
        messages_text = ""
        if previous_messages:
            messages_text = "\n\n**Previous Messages:**\n\n"
            for msg in previous_messages:
                messages_text += f"**{msg['sender']}:** {msg['content']}\n\n"

        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}

## Coalition Communication

You are part of a coalition:

**Members:** {members_list}
**Purpose:** {coalition_purpose}
{messages_text}

## Your Message

What do you want to communicate to your coalition members? Coordinate strategy, share information, or propose actions.

**MESSAGE:**
[Your message to the coalition]
"""

        response = self._call_llm(system_prompt, user_prompt)

        message = ""
        if '**MESSAGE:**' in response.get('raw', ''):
            message = response.get('raw', '').split('**MESSAGE:**')[1].strip()
        else:
            message = response.get('raw', '')

        return {
            'message': message,
            'tokens_used': response.get('tokens_used', 0)
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert actor profile to dictionary for validation

        Returns:
            Dict with actor profile information
        """
        return {
            'name': self.name,
            'short_name': self.short_name,
            'llm_model': self.llm_model,
            'description': self.description,
            'goals': self.goals,
            'constraints': self.constraints,
            'expertise': self.expertise,
            'decision_style': self.decision_style
        }

    def _build_prompts(self, world_state: str, turn: int, total_turns: int, other_actors_decisions: Dict[str, str] = None, communications_context: str = "", recent_goals: str = "") -> tuple:
        """
        Build system and user prompts for the LLM

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            other_actors_decisions: Optional other actors' decisions
            communications_context: Optional context from private communications
            recent_goals: Optional recent goal statements from previous turns

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

        # Add recent goals if provided
        recent_goals_text = ""
        if recent_goals:
            recent_goals_text = f"\n\n## Your Recent Goals\n\n{recent_goals}\n"

        # Build user prompt with current situation and task
        user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}
{communications_text}
{other_decisions_text}
{recent_goals_text}

## Your Task

First, state your current goals given recent developments:

**LONG-TERM GOALS:**
[List 2-4 enduring objectives you're pursuing. These may evolve based on events, but changes should be justified.]

**SHORT-TERM PRIORITIES:**
[List 1-3 immediate objectives for the next few turns.]

Then decide your action:

**REASONING:**
[Explain your thinking, how this action serves your goals, and why your goals may have evolved or remained stable]

**ACTION:**
[Describe the specific action you will take this turn - be concrete and specific]

Remember: This is turn {turn} of {total_turns}. Your goals can evolve based on experience, but maintain some continuity unless events strongly justify change.
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

        # Use unified LLM call (routes to Ollama or OpenRouter automatically)
        content, tokens_used = make_llm_call(
            model=self.llm_model,
            messages=messages,
            api_key=api_key,
            max_retries=3
        )

        # Parse the response using robust parser
        parsed = parse_actor_decision(content)

        return {
            'goals': parsed['goals'],
            'reasoning': parsed['reasoning'],
            'action': parsed['action'],
            'raw': content,
            'tokens_used': tokens_used
        }


def load_actor(scenario_path: str, actor_short_name: str, scenario_system_prompt: str = "") -> Actor:
    """
    Load and validate an actor from YAML file

    Args:
        scenario_path: Path to scenario directory
        actor_short_name: Actor identifier (e.g., 'regulator', 'tech-company')
        scenario_system_prompt: System prompt from scenario configuration

    Returns:
        Validated Actor instance

    Raises:
        FileNotFoundError: If actor YAML file not found
        ValidationError: If actor configuration is invalid
    """
    actor_file = os.path.join(scenario_path, 'actors', f'{actor_short_name}.yaml')

    if not os.path.exists(actor_file):
        raise FileNotFoundError(
            f"Actor file not found: {actor_file}\n"
            f"Expected {actor_short_name}.yaml in {os.path.join(scenario_path, 'actors')}"
        )

    try:
        with open(actor_file, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Validate using Pydantic schema
        actor_config = load_actor_config(yaml_data)

        # Convert back to dict for backward compatibility with Actor class
        actor_data = actor_config.dict()

        return Actor(actor_data, scenario_system_prompt)

    except ValidationError as e:
        # Format Pydantic validation errors nicely
        error_messages = []
        for error in e.errors():
            field = ".".join(str(x) for x in error['loc'])
            message = error['msg']
            error_messages.append(f"  - {field}: {message}")

        error_text = (
            f"Invalid actor configuration in {actor_file}:\n" +
            "\n".join(error_messages)
        )
        raise ValueError(error_text) from e

    except yaml.YAMLError as e:
        raise ValueError(
            f"Invalid YAML syntax in {actor_file}:\n{str(e)}"
        )
