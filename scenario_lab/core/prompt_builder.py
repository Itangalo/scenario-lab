"""
Prompt Builder for Scenario Lab V2

Extracts prompt construction logic from V1 Actor engine.
Responsible for building LLM prompts for various actor decision types.

This module contains the prompt templates and logic for:
- Actor decision-making
- Communication decisions
- Coalition formation
- Other actor interactions
"""
from typing import Dict, Any, Optional, List


def build_actor_system_prompt(
    scenario_system_prompt: str,
    actor_system_prompt: Optional[str] = None
) -> str:
    """
    Build combined system prompt from scenario and actor prompts

    Args:
        scenario_system_prompt: Global scenario system prompt
        actor_system_prompt: Actor-specific system prompt (optional)

    Returns:
        Combined system prompt
    """
    combined = scenario_system_prompt or ""

    if actor_system_prompt:
        if combined:
            combined += "\n\n"
        combined += actor_system_prompt

    return combined


def build_decision_prompt(
    world_state: str,
    turn: int,
    total_turns: int,
    actor_name: str = "",
    scenario_system_prompt: str = "",
    actor_system_prompt: Optional[str] = None,
    other_actors_decisions: Optional[Dict[str, str]] = None,
    communications_context: Optional[str] = None,
    recent_goals: Optional[str] = None,
    json_mode: bool = False
) -> tuple[str, str]:
    """
    Build decision-making prompts for an actor

    Args:
        world_state: Current world state description
        turn: Current turn number
        total_turns: Total number of turns
        actor_name: Name of the actor making the decision
        scenario_system_prompt: Global scenario system prompt
        actor_system_prompt: Actor-specific system prompt
        other_actors_decisions: Optional other actors' decisions (for simultaneous reveal)
        communications_context: Optional context from private communications
        recent_goals: Optional recent goal statements from previous turns
        json_mode: Whether to request JSON format response (default: False)

    Returns:
        tuple: (system_prompt, user_prompt)
    """
    # Build system prompt
    system_prompt = build_actor_system_prompt(scenario_system_prompt, actor_system_prompt)

    # Format other actors' decisions if provided
    other_decisions_text = ""
    if other_actors_decisions:
        other_decisions_text = "\n\n## Other Actors' Decisions This Turn\n\n"
        for other_actor_name, decision in other_actors_decisions.items():
            other_decisions_text += f"**{other_actor_name}:**\n{decision}\n\n"

    # Add communications context if provided
    communications_text = ""
    if communications_context:
        communications_text = "\n\n" + communications_context

    # Add recent goals if provided
    recent_goals_text = ""
    if recent_goals:
        recent_goals_text = f"\n\n## Your Recent Goals\n\n{recent_goals}\n"

    # Build format instructions based on mode
    if json_mode:
        # JSON format instructions
        format_instructions = f"""
## Your Task

Analyze the situation and respond with a valid JSON object:

```json
{{
  "goals": {{
    "long_term": "List 2-4 enduring objectives you're pursuing. These may evolve based on events, but changes should be justified.",
    "short_term": "List 1-3 immediate objectives for the next few turns."
  }},
  "reasoning": "Explain your thinking, how this action serves your goals, and why your goals may have evolved or remained stable.",
  "action": "Describe the specific action you will take this turn - be concrete and specific."
}}
```

**Important:** Provide only the JSON object. You may use markdown formatting within the string values.

Remember: This is turn {turn} of {total_turns}. Your goals can evolve based on experience, but maintain some continuity unless events strongly justify change.
"""
    else:
        # Markdown format instructions (V1 compatibility)
        format_instructions = f"""
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

    # Build user prompt
    user_prompt = f"""## Current Situation (Turn {turn} of {total_turns})

{world_state}
{communications_text}
{other_decisions_text}
{recent_goals_text}
{format_instructions}"""

    return system_prompt, user_prompt


def build_communication_decision_prompt(
    world_state: str,
    turn: int,
    total_turns: int,
    other_actors: List[str],
    scenario_system_prompt: str = "",
    actor_system_prompt: Optional[str] = None
) -> tuple[str, str]:
    """
    Build prompts for deciding whether to initiate private communication

    Args:
        world_state: Current world state
        turn: Current turn number
        total_turns: Total number of turns
        other_actors: List of other actor names available for communication
        scenario_system_prompt: Global scenario system prompt
        actor_system_prompt: Actor-specific system prompt

    Returns:
        tuple: (system_prompt, user_prompt)
    """
    system_prompt = build_actor_system_prompt(scenario_system_prompt, actor_system_prompt)

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

    return system_prompt, user_prompt


def build_bilateral_response_prompt(
    world_state: str,
    turn: int,
    total_turns: int,
    initiator: str,
    message: str,
    scenario_system_prompt: str = "",
    actor_system_prompt: Optional[str] = None
) -> tuple[str, str]:
    """
    Build prompts for responding to bilateral communication

    Args:
        world_state: Current world state
        turn: Current turn number
        total_turns: Total number of turns
        initiator: Name of actor who initiated communication
        message: Message from initiator
        scenario_system_prompt: Global scenario system prompt
        actor_system_prompt: Actor-specific system prompt

    Returns:
        tuple: (system_prompt, user_prompt)
    """
    system_prompt = build_actor_system_prompt(scenario_system_prompt, actor_system_prompt)

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

    return system_prompt, user_prompt


def build_messages_for_llm(
    system_prompt: str,
    user_prompt: str
) -> List[Dict[str, str]]:
    """
    Build messages array for LLM API call

    Args:
        system_prompt: System prompt (may be empty)
        user_prompt: User prompt

    Returns:
        List of message dicts with 'role' and 'content'
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_prompt})

    return messages
