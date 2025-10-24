"""
Response Parser - Robust parsing of LLM responses with flexible format matching
"""
import re
from typing import Dict, Optional, List, Tuple


def extract_section(content: str, section_name: str, next_section: Optional[str] = None) -> str:
    """
    Extract a section from markdown-style content using flexible regex matching

    Args:
        content: Full content to parse
        section_name: Name of section to extract (e.g., "GOALS", "REASONING")
        next_section: Optional next section name to stop at

    Returns:
        Extracted section content, or empty string if not found
    """
    # Build flexible pattern that matches variations
    # Matches: **SECTION_NAME:** or **Section Name:** or ## Section Name, etc.
    # Stop at: next bold header, heading, or separator (---)
    patterns = [
        # Bold with colon: **SECTION NAME:**
        rf'\*\*\s*{re.escape(section_name)}\s*:\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*:\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
        # Bold without colon: **SECTION NAME**
        rf'\*\*\s*{re.escape(section_name)}\s*\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
        # Heading 2 or 3: ## SECTION NAME or ### SECTION NAME (with optional colon)
        rf'^#{2,}\s*{re.escape(section_name)}\s*:?\s*$\s*(.+?)(?=^#{2,}\s+[\w\s]+|^---+\s*$|\Z)',
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
                    rf'^#{2,}\s*{re.escape(next_section)}\s*:?\s*$',  # Heading 2 or 3
                    rf'^---+\s*$',  # Also stop at separator
                ]
                for next_pattern in next_patterns:
                    next_match = re.search(next_pattern, extracted, re.MULTILINE | re.IGNORECASE)
                    if next_match:
                        extracted = extracted[:next_match.start()].strip()
                        break

            return extracted

    return ""


def parse_actor_decision(content: str) -> Dict[str, str]:
    """
    Parse actor decision response with flexible format matching

    Attempts multiple parsing strategies to extract:
    - Long-term goals
    - Short-term priorities
    - Reasoning
    - Action

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

    # Strategy 1: Try to extract goals section (LONG-TERM GOALS + SHORT-TERM PRIORITIES)
    goals_text = []

    # Look for long-term goals
    long_term = extract_section(content, "LONG-TERM GOALS", "SHORT-TERM")
    if not long_term:
        long_term = extract_section(content, "LONG TERM GOALS", "SHORT")
    if long_term:
        goals_text.append(f"**LONG-TERM GOALS:**\n{long_term}")

    # Look for short-term priorities (try multiple stop points for next section)
    short_term = None
    for stop_section in ["REASONING", "CURRENT REASONING", "ACTION"]:
        if not short_term:
            short_term = extract_section(content, "SHORT-TERM PRIORITIES", stop_section)
        if not short_term:
            short_term = extract_section(content, "SHORT-TERM", stop_section)
        if not short_term:
            short_term = extract_section(content, "SHORT TERM", stop_section)
        if short_term:
            break

    if short_term:
        goals_text.append(f"**SHORT-TERM PRIORITIES:**\n{short_term}")

    if goals_text:
        result['goals'] = "\n\n".join(goals_text)

    # Strategy 2: Extract reasoning (try multiple variations)
    reasoning = extract_section(content, "REASONING", "ACTION")
    if not reasoning:
        reasoning = extract_section(content, "CURRENT REASONING", "ACTION")
    if not reasoning:
        reasoning = extract_section(content, "RATIONALE", "ACTION")
    if reasoning:
        result['reasoning'] = reasoning
    else:
        result['reasoning'] = "No structured reasoning provided"

    # Strategy 3: Extract action
    action = extract_section(content, "ACTION")
    if not action:
        action = extract_section(content, "ACTIONS")
    if not action:
        action = extract_section(content, "DECISION")

    if action:
        result['action'] = action
    else:
        # Fallback: if no action section found, use everything after reasoning
        if "**REASONING:**" in content or "**ACTION:**" in content:
            result['action'] = content
        else:
            result['action'] = content

    return result


def parse_bilateral_decision(content: str) -> Dict[str, any]:
    """
    Parse bilateral communication decision

    Extracts:
    - Whether to initiate bilateral (yes/no)
    - Target actor
    - Initial message

    Args:
        content: Raw LLM response

    Returns:
        Dict with 'initiate_bilateral', 'target_actor', 'message'
    """
    result = {
        'initiate_bilateral': False,
        'target_actor': None,
        'message': ''
    }

    # Look for INITIATE_BILATERAL
    initiate_patterns = [
        r'\*\*\s*INITIATE[_\s]BILATERAL\s*:\*\*\s*(yes|no)',
        r'##\s*INITIATE[_\s]BILATERAL\s*\n\s*(yes|no)',
    ]

    for pattern in initiate_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result['initiate_bilateral'] = 'yes' in match.group(1).lower()
            break

    # Look for TARGET_ACTOR
    target_patterns = [
        r'\*\*\s*TARGET[_\s]ACTOR\s*:\*\*\s*(.+?)(?=\*\*|\n\n)',
        r'##\s*TARGET[_\s]ACTOR\s*\n\s*(.+?)(?=##|\n\n)',
    ]

    for pattern in target_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            result['target_actor'] = match.group(1).strip()
            break

    # Look for MESSAGE
    message = extract_section(content, "MESSAGE")
    if not message:
        message = extract_section(content, "INITIAL MESSAGE")
    if message:
        result['message'] = message

    return result


def parse_coalition_decision(content: str) -> Dict[str, any]:
    """
    Parse coalition formation decision

    Extracts:
    - Whether to propose coalition (yes/no)
    - Coalition members
    - Purpose

    Args:
        content: Raw LLM response

    Returns:
        Dict with 'propose_coalition', 'members', 'purpose'
    """
    result = {
        'propose_coalition': False,
        'members': [],
        'purpose': ''
    }

    # Look for PROPOSE_COALITION
    propose_patterns = [
        r'\*\*\s*PROPOSE[_\s]COALITION\s*:\*\*\s*(yes|no)',
        r'##\s*PROPOSE[_\s]COALITION\s*\n\s*(yes|no)',
    ]

    for pattern in propose_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result['propose_coalition'] = 'yes' in match.group(1).lower()
            break

    # Look for MEMBERS (comma-separated list)
    members_patterns = [
        r'\*\*\s*MEMBERS\s*:\*\*\s*(.+?)(?=\*\*|\n\n)',
        r'##\s*MEMBERS\s*\n\s*(.+?)(?=##|\n\n)',
    ]

    for pattern in members_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            members_str = match.group(1).strip()
            # Split by comma or newline
            members = [m.strip() for m in re.split(r'[,\n]', members_str) if m.strip()]
            result['members'] = members
            break

    # Look for PURPOSE
    purpose = extract_section(content, "PURPOSE")
    if not purpose:
        purpose = extract_section(content, "COALITION PURPOSE")
    if purpose:
        result['purpose'] = purpose

    return result


def parse_coalition_response(content: str) -> Dict[str, any]:
    """
    Parse coalition invitation response

    Extracts:
    - Decision (accept/reject)
    - Response message
    - Internal notes

    Args:
        content: Raw LLM response

    Returns:
        Dict with 'decision', 'response', 'internal_notes'
    """
    result = {
        'decision': 'reject',
        'response': '',
        'internal_notes': ''
    }

    # Look for DECISION
    decision_patterns = [
        r'\*\*\s*DECISION\s*:\*\*\s*(accept|reject)',
        r'##\s*DECISION\s*\n\s*(accept|reject)',
    ]

    for pattern in decision_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result['decision'] = match.group(1).lower()
            break

    # Look for RESPONSE
    response = extract_section(content, "RESPONSE")
    if not response:
        response = extract_section(content, "MESSAGE")
    if response:
        result['response'] = response

    # Look for INTERNAL_NOTES
    internal_notes = extract_section(content, "INTERNAL NOTES")
    if not internal_notes:
        internal_notes = extract_section(content, "INTERNAL_NOTES")
    if not internal_notes:
        internal_notes = extract_section(content, "NOTES")
    if internal_notes:
        result['internal_notes'] = internal_notes

    return result
