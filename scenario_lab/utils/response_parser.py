"""
Response Parser for Scenario Lab V2

Parses LLM responses into structured data.
Handles both markdown and JSON response formats.
"""
import re
import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


def extract_section(
    content: str,
    section_name: str,
    next_section: Optional[str] = None
) -> str:
    """
    Extract a section from markdown-style content

    Args:
        content: Full content to parse
        section_name: Name of section to extract (e.g., "GOALS", "REASONING")
        next_section: Optional next section name to stop at

    Returns:
        Extracted section content, or empty string if not found
    """
    # Try multiple pattern variations
    patterns = [
        # Bold with colon: **SECTION NAME:**
        rf'\*\*\s*{re.escape(section_name)}\s*:\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*:\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
        # Bold without colon: **SECTION NAME**
        rf'\*\*\s*{re.escape(section_name)}\s*\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
        # Heading: ## SECTION NAME
        rf'^#{2,}\s*{re.escape(section_name)}\s*:?\s*$\s*(.+?)(?=^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
        # Uppercase with colon: SECTION NAME:
        rf'^{re.escape(section_name.upper())}\s*:\s*(.+?)(?=^[A-Z\s]+:\s*|^#{2,}\s+|^---+\s*$|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()

            # If next_section specified, stop at that section
            if next_section:
                next_patterns = [
                    rf'\*\*\s*{re.escape(next_section)}\s*:\*\*',
                    rf'\*\*\s*{re.escape(next_section)}\s*\*\*',
                    rf'^#{2,}\s*{re.escape(next_section)}\s*:?\s*$',
                    rf'^{re.escape(next_section.upper())}\s*:',
                ]
                for next_pattern in next_patterns:
                    next_match = re.search(next_pattern, extracted, re.MULTILINE | re.IGNORECASE)
                    if next_match:
                        extracted = extracted[:next_match.start()].strip()
                        break

            logger.debug(f"Extracted '{section_name}' ({len(extracted)} chars)")
            return extracted

    logger.debug(f"Failed to extract '{section_name}'")
    return ""


def parse_decision_markdown(content: str) -> Dict[str, str]:
    """
    Parse actor decision from markdown format

    Expected format:
        **LONG-TERM GOALS:**
        [goals text]

        **SHORT-TERM PRIORITIES:**
        [priorities text]

        **REASONING:**
        [reasoning text]

        **ACTION:**
        [action text]

    Args:
        content: Raw LLM response content

    Returns:
        Dict with 'goals', 'reasoning', 'action' keys
    """
    result = {
        'goals': '',
        'reasoning': '',
        'action': ''
    }

    # Extract goals
    goals_parts = []

    long_term = extract_section(content, "LONG-TERM GOALS", "SHORT-TERM PRIORITIES")
    if long_term:
        goals_parts.append(f"**Long-term:**\n{long_term}")

    short_term = extract_section(content, "SHORT-TERM PRIORITIES", "REASONING")
    if short_term:
        goals_parts.append(f"**Short-term:**\n{short_term}")

    # Fallback: try just "GOALS"
    if not goals_parts:
        goals = extract_section(content, "GOALS", "REASONING")
        if goals:
            goals_parts.append(goals)

    result['goals'] = "\n\n".join(goals_parts)

    # Extract reasoning
    result['reasoning'] = extract_section(content, "REASONING", "ACTION")

    # Extract action
    result['action'] = extract_section(content, "ACTION")

    # If action is empty, use remaining content after REASONING
    if not result['action'] and result['reasoning']:
        # Take everything after the reasoning section
        pass  # Already handled by extract_section

    return result


def parse_decision_json(content: str) -> Dict[str, str]:
    """
    Parse actor decision from JSON format

    Expected format:
        {
          "goals": {
            "long_term": "...",
            "short_term": "..."
          },
          "reasoning": "...",
          "action": "..."
        }

    Args:
        content: Raw LLM response content (may contain markdown code blocks)

    Returns:
        Dict with 'goals', 'reasoning', 'action' keys
    """
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```json\s*(\{.+?\})\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r'\{.+\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No JSON found in response")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    result = {
        'goals': '',
        'reasoning': data.get('reasoning', ''),
        'action': data.get('action', '')
    }

    # Parse goals structure
    goals_data = data.get('goals', {})
    if isinstance(goals_data, dict):
        goals_parts = []
        if goals_data.get('long_term'):
            goals_parts.append(f"**Long-term:**\n{goals_data['long_term']}")
        if goals_data.get('short_term'):
            goals_parts.append(f"**Short-term:**\n{goals_data['short_term']}")
        result['goals'] = "\n\n".join(goals_parts)
    elif isinstance(goals_data, str):
        result['goals'] = goals_data
    else:
        result['goals'] = str(goals_data)

    return result


def parse_decision(content: str, json_mode: bool = False) -> Dict[str, str]:
    """
    Parse actor decision response with format auto-detection

    Tries JSON format first (if json_mode=True), then falls back to markdown.

    Args:
        content: Raw LLM response content
        json_mode: Whether to expect JSON format (default: False)

    Returns:
        Dict with 'goals', 'reasoning', 'action' keys
    """
    if json_mode:
        try:
            return parse_decision_json(content)
        except (ValueError, KeyError) as e:
            logger.warning(f"JSON parsing failed ({e}), falling back to markdown")

    return parse_decision_markdown(content)


def parse_communication_decision(content: str) -> Dict[str, any]:
    """
    Parse communication decision response

    Expected format:
        **INITIATE_BILATERAL:** [yes/no]
        **TARGET_ACTOR:** [actor name or "none"]
        **PROPOSED_MESSAGE:** [message or "none"]
        **REASONING:** [reasoning]

    Args:
        content: Raw LLM response content

    Returns:
        Dict with 'initiate_bilateral', 'target_actor', 'message', 'reasoning' keys
    """
    result = {
        'initiate_bilateral': False,
        'target_actor': None,
        'message': None,
        'reasoning': ''
    }

    # Extract initiate decision
    initiate_text = extract_section(content, "INITIATE_BILATERAL", "TARGET_ACTOR")
    result['initiate_bilateral'] = 'yes' in initiate_text.lower()

    # Extract target actor
    target_text = extract_section(content, "TARGET_ACTOR", "PROPOSED_MESSAGE")
    if target_text and target_text.lower() != 'none':
        result['target_actor'] = target_text.strip()

    # Extract message
    message_text = extract_section(content, "PROPOSED_MESSAGE", "REASONING")
    if message_text and message_text.lower() != 'none':
        result['message'] = message_text

    # Extract reasoning
    result['reasoning'] = extract_section(content, "REASONING")

    # Only set initiate_bilateral to True if we have both target and message
    result['initiate_bilateral'] = bool(result['target_actor'] and result['message'])

    return result


def parse_bilateral_response(content: str) -> Dict[str, str]:
    """
    Parse bilateral communication response

    Expected format:
        **RESPONSE:**
        [response text]

        **INTERNAL_NOTES:**
        [internal notes]

    Args:
        content: Raw LLM response content

    Returns:
        Dict with 'response', 'internal_notes' keys
    """
    result = {
        'response': '',
        'internal_notes': ''
    }

    result['response'] = extract_section(content, "RESPONSE", "INTERNAL_NOTES")
    result['internal_notes'] = extract_section(content, "INTERNAL_NOTES")

    return result
