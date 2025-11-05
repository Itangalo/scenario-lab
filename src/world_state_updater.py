"""
World State Updater - Uses LLM to synthesize actor decisions into coherent world state updates
"""
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from api_utils import make_llm_call

load_dotenv()


class WorldStateUpdater:
    """
    Uses an LLM to synthesize multiple actors' decisions and generate
    coherent world state updates with emergent consequences
    """

    def __init__(self, model: str = "alibaba/tongyi-deepresearch-30b-a3b:free"):
        """
        Initialize the world state updater

        Args:
            model: LLM model to use for world state synthesis
        """
        self.model = model
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

    def update_world_state(
        self,
        current_state: str,
        turn: int,
        total_turns: int,
        actor_decisions: Dict[str, Dict[str, Any]],
        scenario_name: str,
        exogenous_events: list = None
    ) -> Dict[str, Any]:
        """
        Generate updated world state based on actor decisions and exogenous events

        Args:
            current_state: Current world state description
            turn: Current turn number
            total_turns: Total number of turns in scenario
            actor_decisions: Dict of {actor_name: {reasoning, action}} for this turn
            scenario_name: Name of the scenario
            exogenous_events: List of events occurring independently of actors (optional)

        Returns:
            Dict with 'updated_state' (str) and 'metadata' (dict) keys
        """
        system_prompt = self._build_system_prompt(scenario_name)
        user_prompt = self._build_user_prompt(
            current_state, turn, total_turns, actor_decisions, exogenous_events
        )

        response = self._call_llm(system_prompt, user_prompt)

        return {
            'updated_state': response['updated_state'],
            'metadata': {
                'consequences_identified': response.get('consequences', []),
                'key_changes': response.get('key_changes', []),
                'exogenous_events_count': len(exogenous_events) if exogenous_events else 0,
                'tokens_used': response.get('tokens_used', 0)
            }
        }

    def _build_system_prompt(self, scenario_name: str) -> str:
        """Build system prompt for world state synthesis"""
        return f"""You are a scenario simulation narrator for "{scenario_name}".

Your task is to synthesize multiple actors' decisions AND background events into a coherent, realistic world state update.

Your responsibilities:
1. Integrate all actors' actions into a unified narrative
2. Integrate any exogenous events (background trends, random events) that occur
3. Generate realistic consequences (both intended and unintended)
4. Show second-order effects and emergent dynamics
5. Maintain logical consistency with previous state
6. Be specific and concrete about what changed
7. Show how actors' actions and background events interact

Guidelines:
- Write in third-person, present tense
- Focus on what actually happened and its effects
- Include both immediate and longer-term consequences
- Show realistic friction, delays, and complications
- Avoid editorializing - describe objectively what occurred
- Keep the narrative focused and relevant to the scenario
- Weave background events naturally into the narrative (don't just list them)"""

    def _build_user_prompt(
        self,
        current_state: str,
        turn: int,
        total_turns: int,
        actor_decisions: Dict[str, Dict[str, Any]],
        exogenous_events: list = None
    ) -> str:
        """Build user prompt with current state, decisions, and exogenous events"""

        # Format actor decisions
        actions_text = ""
        for actor_name, decision in actor_decisions.items():
            actions_text += f"\n### {actor_name}\n\n"
            actions_text += f"**Action taken:**\n{decision['action']}\n"

        # Format exogenous events if present
        events_text = ""
        if exogenous_events and len(exogenous_events) > 0:
            events_text = "\n## Background Events This Turn\n\n"
            events_text += "Independent of actor decisions, the following also occurred:\n\n"
            for event in exogenous_events:
                events_text += f"**{event['name']}:** {event['description']}\n\n"
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
2. **Background developments**: How did any background events affect the situation?
3. **Interactions**: How did actors' actions, and background events, affect each other?
4. **Consequences**: What are the immediate and near-term effects?
5. **New dynamics**: What new situations or tensions emerged?
6. **Current status**: What is the state of the situation now?

Provide your response in this format:

**UPDATED STATE:**
[Write a cohesive narrative (2-4 paragraphs) describing the new world state after this turn's actions and events]

**KEY CHANGES:**
- [Change 1]
- [Change 2]
- [Change 3]

**CONSEQUENCES:**
- [Consequence 1]
- [Consequence 2]

Remember: Be specific, realistic, and show how actions and events create ripple effects. Weave background events naturally into the narrative."""

        return prompt

    def _call_llm(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API for world state synthesis"""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # Use unified LLM call (routes to Ollama or OpenRouter automatically)
        content, tokens_used = make_llm_call(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            max_retries=3
        )

        # Parse the response
        updated_state = ""
        key_changes = []
        consequences = []

        # Extract UPDATED STATE
        if "**UPDATED STATE:**" in content:
            parts = content.split("**KEY CHANGES:**")
            state_part = parts[0].split("**UPDATED STATE:**")[1].strip()
            updated_state = state_part

            # Extract KEY CHANGES if present
            if len(parts) > 1:
                changes_part = parts[1]
                if "**CONSEQUENCES:**" in changes_part:
                    changes_section, consequences_section = changes_part.split("**CONSEQUENCES:**")
                    # Parse key changes
                    for line in changes_section.strip().split('\n'):
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            key_changes.append(line[1:].strip())
                    # Parse consequences
                    for line in consequences_section.strip().split('\n'):
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            consequences.append(line[1:].strip())
                else:
                    # No consequences section, just parse changes
                    for line in changes_part.strip().split('\n'):
                        line = line.strip()
                        if line.startswith('-') or line.startswith('•'):
                            key_changes.append(line[1:].strip())
        else:
            # Fallback if format not followed
            updated_state = content

        # tokens_used is already returned from make_llm_call()

        return {
            'updated_state': updated_state,
            'key_changes': key_changes,
            'consequences': consequences,
            'tokens_used': tokens_used
        }
