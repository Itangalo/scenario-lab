"""
World State Updater - Uses LLM to synthesize actor decisions into coherent world state updates
"""
import os
import requests
import re
from typing import Dict, Any
from dotenv import load_dotenv
from api_utils import make_llm_call
from response_parser import extract_section

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
        exogenous_events: list = None,
        has_metrics: bool = False
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
            has_metrics: If True, will ensure UPDATED METRICS section is present (optional)

        Returns:
            Dict with 'updated_state' (str) and 'metadata' (dict) keys
        """
        system_prompt = self._build_system_prompt(scenario_name)
        user_prompt = self._build_user_prompt(
            current_state, turn, total_turns, actor_decisions, exogenous_events
        )

        response = self._call_llm(system_prompt, user_prompt, metrics_required=has_metrics)

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
8. **CRITICAL: Include updated metrics/polling data in a separate UPDATED METRICS section**

Guidelines:
- Write in third-person, present tense
- Focus on what actually happened and its effects
- Include both immediate and longer-term consequences
- Show realistic friction, delays, and complications
- Avoid editorializing - describe objectively what occurred
- Keep the narrative focused and relevant to the scenario
- Weave background events naturally into the narrative (don't just list them)

**CRITICAL OUTPUT FORMAT:**
You MUST follow the exact format specified in the user prompt. This includes:
1. **UPDATED STATE:** section with narrative (2-4 paragraphs)
2. **UPDATED METRICS:** section with ALL tracked metrics (if applicable)
3. **KEY CHANGES:** bulleted list
4. **CONSEQUENCES:** bulleted list

Do NOT skip any sections. Do NOT merge sections together."""

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
7. **Updated metrics**: If this scenario tracks quantitative metrics (e.g., opinion polls, approval ratings), provide updated values based on realistic reactions to this turn's events.

Provide your response in this format:

**UPDATED STATE:**
[Write a cohesive narrative (2-4 paragraphs) describing the new world state after this turn's actions and events]

**UPDATED METRICS:**
CRITICAL: You MUST include this section if the scenario tracks metrics (opinion polls, approval ratings, etc.)
For election scenarios, list ALL parties with their updated support percentages and changes from previous turn.
Format: "- Party Name: XX.X% (+/-X.X)"
Example:
- Socialdemokraterna (S): 34.1% (+0.3)
- Moderaterna (M): 18.2% (-0.3)
[Continue for ALL tracked parties]

**KEY CHANGES:**
- [Change 1]
- [Change 2]
- [Change 3]

**CONSEQUENCES:**
- [Consequence 1]
- [Consequence 2]

CRITICAL REQUIREMENTS:
1. ALWAYS include UPDATED METRICS section for election/polling scenarios
2. List ALL parties/metrics being tracked (check previous world states for which ones)
3. Changes should be gradual and realistic (rarely >1-2% per month for opinion polls)
4. Be specific, realistic, and show how actions create ripple effects"""

        return prompt

    def _call_llm(self, system_prompt: str, user_prompt: str, metrics_required: bool = False) -> Dict[str, Any]:
        """Call OpenRouter API for world state synthesis

        Args:
            system_prompt: System-level instructions
            user_prompt: User prompt with current state and actions
            metrics_required: If True, will retry if UPDATED METRICS section is missing
        """
        import logging
        logger = logging.getLogger("scenario_lab")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Try up to 2 times if metrics are required and missing
        max_attempts = 2 if metrics_required else 1

        for attempt in range(max_attempts):
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

            # Check if UPDATED METRICS section exists when required
            has_metrics = "UPDATED METRICS" in content or "Updated Metrics" in content

            if metrics_required and not has_metrics and attempt < max_attempts - 1:
                logger.warning(f"⚠️  UPDATED METRICS section missing in world state synthesis (attempt {attempt + 1}/{max_attempts})")
                logger.warning("   Retrying with explicit reminder...")
                # Add explicit reminder to the prompt for retry
                user_prompt += "\n\n🚨 CRITICAL REMINDER: You MUST include the **UPDATED METRICS:** section with updated values for ALL tracked metrics! This is mandatory, not optional."
                continue  # Retry with enhanced prompt

            if metrics_required and not has_metrics:
                logger.error("❌ UPDATED METRICS section still missing after retry")
                logger.error("   Metrics will not be tracked for this turn!")

            # Parse the response
            # Use robust section extraction (handles variations in formatting)
            # IMPORTANT: Try UPDATED METRICS first to exclude it from the narrative
            updated_state = extract_section(content, "UPDATED STATE", "UPDATED METRICS")
            if not updated_state:
                # Fallback: try without markdown bold
                updated_state = extract_section(content, "Updated State", "Updated Metrics")
            if not updated_state:
                # Fallback: extract up to KEY CHANGES (if no UPDATED METRICS section exists)
                updated_state = extract_section(content, "UPDATED STATE", "KEY CHANGES")
            if not updated_state:
                updated_state = extract_section(content, "Updated State", "Key Changes")
            if not updated_state:
                # Final fallback if format not followed - use entire content
                updated_state = content

            # Extract KEY CHANGES section
            key_changes_text = extract_section(content, "KEY CHANGES", "CONSEQUENCES")
            if not key_changes_text:
                key_changes_text = extract_section(content, "Key Changes", "Consequences")

            # Parse bulleted list from key changes
            key_changes = []
            if key_changes_text:
                for line in key_changes_text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        key_changes.append(line[1:].strip())

            # Extract CONSEQUENCES section
            consequences_text = extract_section(content, "CONSEQUENCES", None)
            if not consequences_text:
                consequences_text = extract_section(content, "Consequences", None)

            # Parse bulleted list from consequences
            consequences = []
            if consequences_text:
                for line in consequences_text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        consequences.append(line[1:].strip())

            # Successfully parsed - return results
            return {
                'updated_state': updated_state,
                'key_changes': key_changes,
                'consequences': consequences,
                'tokens_used': tokens_used,
                'full_response': content  # Include full response for metrics extraction
            }

        # Should never reach here due to loop, but just in case
        raise Exception("Failed to generate valid world state after maximum attempts")
