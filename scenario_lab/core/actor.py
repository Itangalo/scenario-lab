"""
Actor Engine for Scenario Lab V2

Provides Actor class for managing actor profiles and decision-making.
Unlike V1, this is a thin wrapper around V2 utilities (prompt_builder, api_client, etc.)

V2 Design Philosophy:
- Actor is a data container (frozen dataclass)
- Decision logic lives in DecisionPhaseV2, not in Actor
- Communication logic uses pure functions from communication_manager
- Actor can be used for convenience, but phases can work with dicts too
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from scenario_lab.utils.api_client import make_llm_call_async
from scenario_lab.core.prompt_builder import build_messages_for_llm
from scenario_lab.utils.response_parser import parse_decision

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Actor:
    """
    Represents a single actor in the scenario (V2 - immutable)

    This is a data container for actor configuration. Unlike V1, this doesn't
    contain decision logic - that lives in DecisionPhaseV2.

    Use this class for:
    - Type safety and validation
    - Convenient access to actor properties
    - Backward compatibility with V1 code patterns

    Or use plain dicts with DecisionPhaseV2 for more functional style.
    """
    name: str
    short_name: str
    llm_model: str
    system_prompt: str = ""
    description: str = ""
    goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    expertise: Dict[str, Any] = field(default_factory=dict)
    decision_style: str = ""

    # Scenario context (passed at initialization)
    scenario_system_prompt: str = ""
    json_mode: bool = False

    @classmethod
    def from_dict(cls, actor_data: Dict[str, Any],
                  scenario_system_prompt: str = "",
                  json_mode: bool = False) -> Actor:
        """
        Create Actor from dictionary (V1 compatibility)

        Args:
            actor_data: Actor configuration dict
            scenario_system_prompt: Scenario-level system prompt
            json_mode: Whether to use JSON response format

        Returns:
            Actor instance
        """
        return cls(
            name=actor_data['name'],
            short_name=actor_data['short_name'],
            llm_model=actor_data['llm_model'],
            system_prompt=actor_data.get('system_prompt', ''),
            description=actor_data.get('description', ''),
            goals=actor_data.get('goals', []),
            constraints=actor_data.get('constraints', []),
            expertise=actor_data.get('expertise', {}),
            decision_style=actor_data.get('decision_style', ''),
            scenario_system_prompt=scenario_system_prompt,
            json_mode=json_mode
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (for use with V2 phases)

        Returns:
            Dict with actor configuration
        """
        return {
            'name': self.name,
            'short_name': self.short_name,
            'llm_model': self.llm_model,
            'system_prompt': self.system_prompt,
            'description': self.description,
            'goals': self.goals,
            'constraints': self.constraints,
            'expertise': self.expertise,
            'decision_style': self.decision_style,
        }

    def to_config_dict(self) -> Dict[str, Any]:
        """
        Convert to config dict (includes scenario context)

        This is useful when you want to pass actor config to V2 phases.

        Returns:
            Dict with full actor configuration including scenario context
        """
        config = self.to_dict()
        # Don't include scenario_system_prompt in config - that's passed separately
        return config

    async def make_decision(
        self,
        world_state: str,
        turn: int,
        total_turns: int,
        communications_context: str = "",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a decision (convenience method for V1 compatibility)

        Note: In V2, decision making typically happens in DecisionPhaseV2.
        This method is provided for backward compatibility and standalone use.

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            communications_context: Optional communication context
            api_key: Optional API key for LLM calls

        Returns:
            Dict with 'goals', 'reasoning', 'action', 'raw_response', 'tokens_used'
        """
        # Build prompts using V2 prompt_builder
        from scenario_lab.core.prompt_builder import build_decision_prompt

        system_prompt, user_prompt = build_decision_prompt(
            world_state=world_state,
            turn=turn,
            total_turns=total_turns,
            actor_name=self.name,
            scenario_system_prompt=self.scenario_system_prompt,
            actor_system_prompt=self.system_prompt,
            communications_context=communications_context,
            json_mode=self.json_mode
        )

        # Call LLM using V2 api_client
        messages = build_messages_for_llm(system_prompt, user_prompt)

        llm_response = await make_llm_call_async(
            model=self.llm_model,
            messages=messages,
            api_key=api_key,
            max_retries=3,
            context={'phase': 'decision', 'actor': self.short_name, 'turn': turn}
        )

        # Parse response using V2 response_parser
        parsed = parse_decision(llm_response.content, json_mode=self.json_mode)

        return {
            'goals': parsed.get('goals', ''),
            'reasoning': parsed.get('reasoning', ''),
            'action': parsed.get('action', ''),
            'raw_response': llm_response.content,
            'tokens_used': llm_response.tokens_used,
            'input_tokens': llm_response.input_tokens,
            'output_tokens': llm_response.output_tokens,
            'model': llm_response.model
        }

    async def respond_to_bilateral(
        self,
        world_state: str,
        turn: int,
        total_turns: int,
        initiator: str,
        message: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Respond to bilateral communication

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            initiator: Name of actor who initiated communication
            message: Message from initiator
            api_key: Optional API key for LLM calls

        Returns:
            Dict with 'response', 'internal_notes', 'tokens_used'
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

        messages = build_messages_for_llm(system_prompt, user_prompt)

        llm_response = await make_llm_call_async(
            model=self.llm_model,
            messages=messages,
            api_key=api_key,
            max_retries=3,
            context={'phase': 'bilateral_response', 'actor': self.short_name, 'turn': turn}
        )

        # Parse response
        response_text = ""
        internal_notes = ""

        content = llm_response.content
        if '**RESPONSE:**' in content:
            parts = content.split('**RESPONSE:**')[1]
            if '**INTERNAL_NOTES:**' in parts:
                response_text = parts.split('**INTERNAL_NOTES:**')[0].strip()
                internal_notes = parts.split('**INTERNAL_NOTES:**')[1].strip()
            else:
                response_text = parts.strip()

        return {
            'response': response_text,
            'internal_notes': internal_notes,
            'tokens_used': llm_response.tokens_used,
            'input_tokens': llm_response.input_tokens,
            'output_tokens': llm_response.output_tokens,
            'model': llm_response.model
        }

    async def respond_to_coalition(
        self,
        world_state: str,
        turn: int,
        total_turns: int,
        proposer: str,
        members: List[str],
        purpose: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Respond to coalition proposal

        Args:
            world_state: Current world state
            turn: Current turn number
            total_turns: Total turns in scenario
            proposer: Name of actor who proposed coalition
            members: Proposed coalition members (including self)
            purpose: Stated purpose of coalition
            api_key: Optional API key for LLM calls

        Returns:
            Dict with 'decision', 'response', 'internal_notes', 'tokens_used'
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

        messages = build_messages_for_llm(system_prompt, user_prompt)

        llm_response = await make_llm_call_async(
            model=self.llm_model,
            messages=messages,
            api_key=api_key,
            max_retries=3,
            context={'phase': 'coalition_response', 'actor': self.short_name, 'turn': turn}
        )

        # Parse response
        content = llm_response.content

        decision = 'reject'  # Default to reject
        if '**DECISION:**' in content:
            try:
                decision_text = content.split('**DECISION:**')[1].split('**')[0].lower().strip()
                decision = 'accept' if 'accept' in decision_text else 'reject'
            except (IndexError, AttributeError):
                decision = 'reject'

        response_text = ""
        if '**RESPONSE:**' in content:
            try:
                parts = content.split('**RESPONSE:**')[1]
                if '**INTERNAL_NOTES:**' in parts:
                    response_text = parts.split('**INTERNAL_NOTES:**')[0].strip()
                else:
                    response_text = parts.strip()
            except (IndexError, AttributeError):
                pass

        internal_notes = ""
        if '**INTERNAL_NOTES:**' in content:
            try:
                internal_notes = content.split('**INTERNAL_NOTES:**')[1].strip()
            except (IndexError, AttributeError):
                pass

        return {
            'decision': decision,
            'response': response_text,
            'internal_notes': internal_notes,
            'tokens_used': llm_response.tokens_used,
            'input_tokens': llm_response.input_tokens,
            'output_tokens': llm_response.output_tokens,
            'model': llm_response.model
        }
