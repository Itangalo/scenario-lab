"""
World Synthesizer for Scenario Lab V2

Responsible for synthesizing actor decisions into coherent world state updates.
Uses LLM to generate realistic consequences and emergent dynamics.

Migrated from V1's WorldStateUpdater with V2 architecture:
- No global state dependencies
- Clean separation of concerns
- Uses V2 API client
- Returns structured data
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorldUpdateResult:
    """Result of world state synthesis"""
    updated_state: str
    key_changes: List[str]
    consequences: List[str]
    tokens_used: int
    input_tokens: int
    output_tokens: int
    full_response: str  # For metrics extraction in Phase 3


class WorldSynthesizer:
    """
    Uses an LLM to synthesize multiple actors' decisions and generate
    coherent world state updates with emergent consequences
    """

    def __init__(self, model: str = "openai/gpt-4o-mini", scenario_name: str = ""):
        """
        Initialize the world state synthesizer

        Args:
            model: LLM model to use for world state synthesis
            scenario_name: Name of the scenario (for context in prompts)
        """
        self.model = model
        self.scenario_name = scenario_name

    def build_system_prompt(self) -> str:
        """Build system prompt for world state synthesis"""
        return f"""You are a scenario simulation narrator for "{self.scenario_name}".

Your task is to synthesize multiple actors' decisions into a coherent, realistic world state update.

Your responsibilities:
1. Integrate all actors' actions into a unified narrative
2. Generate realistic consequences (both intended and unintended)
3. Show second-order effects and emergent dynamics
4. Maintain logical consistency with previous state
5. Be specific and concrete about what changed
6. Show how actors' actions interact with each other

Guidelines:
- Write in third-person, present tense
- Focus on what actually happened and its effects
- Include both immediate and longer-term consequences
- Show realistic friction, delays, and complications
- Avoid editorializing - describe objectively what occurred
- Keep the narrative focused and relevant to the scenario

**CRITICAL OUTPUT FORMAT:**
You MUST follow the exact format specified in the user prompt. This includes:
1. **UPDATED STATE:** section with narrative (2-4 paragraphs)
2. **KEY CHANGES:** bulleted list
3. **CONSEQUENCES:** bulleted list

Do NOT skip any sections. Do NOT merge sections together."""

    def build_user_prompt(
        self,
        current_state: str,
        turn: int,
        total_turns: int,
        actor_decisions: Dict[str, Dict[str, str]],
        exogenous_events: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Build user prompt with current state and actor decisions

        Args:
            current_state: Current world state description
            turn: Current turn number
            total_turns: Total number of turns
            actor_decisions: Dict of {actor_name: {action, reasoning}} for this turn
            exogenous_events: Optional list of background events (Phase 1.3: stub)

        Returns:
            User prompt string
        """
        # Format actor decisions
        actions_text = ""
        for actor_name, decision in actor_decisions.items():
            actions_text += f"\n### {actor_name}\n\n"
            actions_text += f"**Action taken:**\n{decision.get('action', 'No action specified')}\n"

        # Phase 1.3: Stub for exogenous events (to be implemented in Phase 3)
        events_text = ""
        if exogenous_events and len(exogenous_events) > 0:
            events_text = "\n## Background Events This Turn\n\n"
            events_text += "Independent of actor decisions, the following also occurred:\n\n"
            for event in exogenous_events:
                events_text += f"**{event.get('name', 'Event')}:** {event.get('description', '')}\n\n"
            events_text += "---\n\n"

        prompt = f"""## Current World State (Turn {turn} of {total_turns})

{current_state}

---

## Actor Actions This Turn
{actions_text}

---
{events_text}
## Your Task

Synthesize these actions{' and background events' if exogenous_events else ''} into an updated world state. Describe:

1. **What happened**: How did each actor's action play out?
{f'2. **Background developments**: How did any background events affect the situation?' if exogenous_events else ''}
3. **Interactions**: How did actors' actions affect each other?
4. **Consequences**: What are the immediate and near-term effects?
5. **New dynamics**: What new situations or tensions emerged?
6. **Current status**: What is the state of the situation now?

Provide your response in this format:

**UPDATED STATE:**
[Write a cohesive narrative (2-4 paragraphs) describing the new world state after this turn's actions{' and events' if exogenous_events else ''}]

**KEY CHANGES:**
- [Change 1]
- [Change 2]
- [Change 3]

**CONSEQUENCES:**
- [Consequence 1]
- [Consequence 2]

CRITICAL REQUIREMENTS:
1. Be specific, realistic, and show how actions create ripple effects
2. Include both intended and unintended consequences
3. Maintain logical consistency with the previous state"""

        return prompt

    def parse_world_update_response(self, content: str) -> Dict[str, Any]:
        """
        Parse world update response

        Args:
            content: Raw LLM response

        Returns:
            Dict with 'updated_state', 'key_changes', 'consequences' keys
        """
        from scenario_lab.utils.response_parser import extract_section

        result = {
            'updated_state': '',
            'key_changes': [],
            'consequences': []
        }

        # Extract UPDATED STATE section (stop at KEY CHANGES)
        updated_state = extract_section(content, "UPDATED STATE", "KEY CHANGES")
        if not updated_state:
            # Fallback: try without markdown bold
            updated_state = extract_section(content, "Updated State", "Key Changes")
        if not updated_state:
            # Final fallback - use entire content
            updated_state = content

        result['updated_state'] = updated_state

        # Extract KEY CHANGES section
        key_changes_text = extract_section(content, "KEY CHANGES", "CONSEQUENCES")
        if not key_changes_text:
            key_changes_text = extract_section(content, "Key Changes", "Consequences")

        # Parse bulleted list
        if key_changes_text:
            for line in key_changes_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    result['key_changes'].append(line[1:].strip())

        # Extract CONSEQUENCES section
        consequences_text = extract_section(content, "CONSEQUENCES", None)
        if not consequences_text:
            consequences_text = extract_section(content, "Consequences", None)

        # Parse bulleted list
        if consequences_text:
            for line in consequences_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    result['consequences'].append(line[1:].strip())

        return result
