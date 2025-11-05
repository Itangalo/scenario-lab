"""
Response Parser - Robust parsing of LLM responses with flexible format matching

Provides comprehensive parsing capabilities with:
- Multiple format pattern matching
- Fallback strategies for format variations
- Logging and diagnostics for debugging
- Statistics tracking for parse success/failure
"""
import re
import logging
from typing import Dict, Optional, List, Tuple
from collections import defaultdict


# Global statistics tracker for parsing operations
_parse_statistics = defaultdict(lambda: {'success': 0, 'failure': 0, 'patterns_used': defaultdict(int)})


def get_parse_statistics() -> dict:
    """
    Get parsing statistics for debugging and optimization

    Returns:
        Dictionary with success/failure counts per parser function
    """
    return dict(_parse_statistics)


def reset_parse_statistics():
    """Reset parsing statistics"""
    _parse_statistics.clear()


def extract_section(
    content: str,
    section_name: str,
    next_section: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Extract a section from markdown-style content using flexible regex matching

    Args:
        content: Full content to parse
        section_name: Name of section to extract (e.g., "GOALS", "REASONING")
        next_section: Optional next section name to stop at
        logger: Optional logger for diagnostic information

    Returns:
        Extracted section content, or empty string if not found
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Track parsing attempt
    stats_key = f"extract_section_{section_name}"

    # Build flexible pattern that matches variations
    # Matches: **SECTION_NAME:** or **Section Name:** or ## Section Name, etc.
    # Stop at: next bold header, heading, or separator (---)
    patterns = [
        # Bold with colon: **SECTION NAME:**
        (
            'bold_with_colon',
            rf'\*\*\s*{re.escape(section_name)}\s*:\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*:\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)'
        ),
        # Bold without colon: **SECTION NAME**
        (
            'bold_without_colon',
            rf'\*\*\s*{re.escape(section_name)}\s*\*\*\s*(.+?)(?=\*\*\s*[\w\s]+\s*\*\*|^#{2,}\s+[\w\s]+|^---+\s*$|\Z)'
        ),
        # Heading 2 or 3: ## SECTION NAME or ### SECTION NAME (with optional colon)
        (
            'heading',
            rf'^#{2,}\s*{re.escape(section_name)}\s*:?\s*$\s*(.+?)(?=^#{2,}\s+[\w\s]+|^---+\s*$|\Z)'
        ),
        # Uppercase with colon (no bold): SECTION NAME:
        (
            'uppercase_with_colon',
            rf'^{re.escape(section_name.upper())}\s*:\s*(.+?)(?=^[A-Z\s]+:\s*|^#{2,}\s+|^---+\s*$|\Z)'
        ),
    ]

    for pattern_name, pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()

            # If next_section specified, stop at that section
            if next_section:
                next_patterns = [
                    rf'\*\*\s*{re.escape(next_section)}\s*:\*\*',
                    rf'\*\*\s*{re.escape(next_section)}\s*\*\*',
                    rf'^#{2,}\s*{re.escape(next_section)}\s*:?\s*$',  # Heading 2 or 3
                    rf'^{re.escape(next_section.upper())}\s*:',  # Uppercase
                    rf'^---+\s*$',  # Also stop at separator
                ]
                for next_pattern in next_patterns:
                    next_match = re.search(next_pattern, extracted, re.MULTILINE | re.IGNORECASE)
                    if next_match:
                        extracted = extracted[:next_match.start()].strip()
                        break

            # Record success
            _parse_statistics[stats_key]['success'] += 1
            _parse_statistics[stats_key]['patterns_used'][pattern_name] += 1

            logger.debug(f"Extracted '{section_name}' using pattern '{pattern_name}' ({len(extracted)} chars)")
            return extracted

    # Record failure
    _parse_statistics[stats_key]['failure'] += 1
    logger.debug(f"Failed to extract '{section_name}' - tried {len(patterns)} patterns")

    return ""


def parse_actor_decision(content: str, logger: Optional[logging.Logger] = None) -> Dict[str, str]:
    """
    Parse actor decision response with flexible format matching

    Attempts multiple parsing strategies to extract:
    - Long-term goals
    - Short-term priorities
    - Reasoning
    - Action

    Args:
        content: Raw LLM response content
        logger: Optional logger for diagnostic information

    Returns:
        Dict with 'goals', 'reasoning', 'action' keys
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Track parsing attempt
    stats_key = "parse_actor_decision"
    _parse_statistics[stats_key]['attempts'] = _parse_statistics[stats_key].get('attempts', 0) + 1

    result = {
        'goals': '',
        'reasoning': '',
        'action': ''
    }

    # Strategy 1: Try to extract goals section (LONG-TERM GOALS + SHORT-TERM PRIORITIES)
    goals_text = []

    # Look for long-term goals
    long_term = extract_section(content, "LONG-TERM GOALS", "SHORT-TERM", logger)
    if not long_term:
        long_term = extract_section(content, "LONG TERM GOALS", "SHORT", logger)
    if not long_term:
        long_term = extract_section(content, "LONG-TERM", "SHORT-TERM", logger)
    if long_term:
        goals_text.append(f"**LONG-TERM GOALS:**\n{long_term}")
        logger.debug(f"Found long-term goals ({len(long_term)} chars)")

    # Look for short-term priorities (try multiple stop points for next section)
    short_term = None
    for stop_section in ["REASONING", "CURRENT REASONING", "ACTION", "DECISION"]:
        if not short_term:
            short_term = extract_section(content, "SHORT-TERM PRIORITIES", stop_section, logger)
        if not short_term:
            short_term = extract_section(content, "SHORT-TERM", stop_section, logger)
        if not short_term:
            short_term = extract_section(content, "SHORT TERM", stop_section, logger)
        if short_term:
            logger.debug(f"Found short-term priorities ({len(short_term)} chars)")
            break

    if short_term:
        goals_text.append(f"**SHORT-TERM PRIORITIES:**\n{short_term}")

    if goals_text:
        result['goals'] = "\n\n".join(goals_text)
        _parse_statistics[stats_key]['goals_found'] = _parse_statistics[stats_key].get('goals_found', 0) + 1
    else:
        logger.warning("No goals sections found in actor decision")
        _parse_statistics[stats_key]['goals_missing'] = _parse_statistics[stats_key].get('goals_missing', 0) + 1

    # Strategy 2: Extract reasoning (try multiple variations)
    reasoning = extract_section(content, "REASONING", "ACTION", logger)
    if not reasoning:
        reasoning = extract_section(content, "CURRENT REASONING", "ACTION", logger)
    if not reasoning:
        reasoning = extract_section(content, "RATIONALE", "ACTION", logger)
    if not reasoning:
        reasoning = extract_section(content, "THINKING", "ACTION", logger)

    if reasoning:
        result['reasoning'] = reasoning
        _parse_statistics[stats_key]['reasoning_found'] = _parse_statistics[stats_key].get('reasoning_found', 0) + 1
        logger.debug(f"Found reasoning ({len(reasoning)} chars)")
    else:
        # Fallback: try to extract text between GOALS/SHORT-TERM and ACTION (but not including goals)
        # This ensures we don't accidentally include goals sections in reasoning
        fallback_pattern = r'(?:\*\*\s*(?:SHORT-TERM|SHORT TERM)[^\*]*\*\*.*?)(?:\n\n|\n)(.+?)(?=\*\*\s*(?:ACTION|DECISION)|\Z)'
        match = re.search(fallback_pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match and match.group(1).strip() and '**LONG-TERM' not in match.group(1) and '**SHORT-TERM' not in match.group(1):
            extracted = match.group(1).strip()
            # Make sure we didn't extract a goals section by mistake
            if len(extracted) > 20:  # Minimum length for valid reasoning
                result['reasoning'] = extracted
                logger.warning("Using fallback strategy for reasoning extraction")
                _parse_statistics[stats_key]['reasoning_fallback'] = _parse_statistics[stats_key].get('reasoning_fallback', 0) + 1
            else:
                result['reasoning'] = "No structured reasoning provided"
                _parse_statistics[stats_key]['reasoning_missing'] = _parse_statistics[stats_key].get('reasoning_missing', 0) + 1
        else:
            result['reasoning'] = "No structured reasoning provided"
            logger.warning("No reasoning section found in actor decision")
            _parse_statistics[stats_key]['reasoning_missing'] = _parse_statistics[stats_key].get('reasoning_missing', 0) + 1

    # Strategy 3: Extract action
    action = extract_section(content, "ACTION", None, logger)
    if not action:
        action = extract_section(content, "ACTIONS", None, logger)
    if not action:
        action = extract_section(content, "DECISION", None, logger)
    if not action:
        action = extract_section(content, "PLAN", None, logger)

    if action:
        result['action'] = action
        _parse_statistics[stats_key]['action_found'] = _parse_statistics[stats_key].get('action_found', 0) + 1
        logger.debug(f"Found action ({len(action)} chars)")
    else:
        # Fallback: Extract text after last recognized section
        # Try to find content after reasoning/goals
        fallback_pattern = r'(?:\*\*\s*(?:REASONING|ACTION|DECISION)\s*:\*\*\s*)(.+?)$'
        match = re.search(fallback_pattern, content, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match and match.group(1).strip():
            result['action'] = match.group(1).strip()
            logger.warning("Using fallback strategy for action extraction")
            _parse_statistics[stats_key]['action_fallback'] = _parse_statistics[stats_key].get('action_fallback', 0) + 1
        else:
            # Last resort: use entire content
            result['action'] = content
            logger.error("Failed to extract action - using entire content as fallback")
            _parse_statistics[stats_key]['action_missing'] = _parse_statistics[stats_key].get('action_missing', 0) + 1

    return result


def diagnose_parsing_failure(content: str, expected_sections: List[str]) -> str:
    """
    Diagnose why parsing failed by analyzing the content structure

    Args:
        content: The content that failed to parse
        expected_sections: List of section names that were expected

    Returns:
        Diagnostic string explaining likely issues
    """
    diagnostics = []

    # Check for common formatting issues
    if not content.strip():
        return "Content is empty"

    # Check if content has any markdown formatting
    has_bold = '**' in content
    has_headings = re.search(r'^#{2,}\s+', content, re.MULTILINE)
    has_uppercase_sections = re.search(r'^[A-Z\s]+:\s*', content, re.MULTILINE)

    if not (has_bold or has_headings or has_uppercase_sections):
        diagnostics.append("No structured formatting detected (no bold, headings, or uppercase sections)")

    # Check for each expected section
    for section in expected_sections:
        # Try case-insensitive search for the section name
        if re.search(re.escape(section), content, re.IGNORECASE):
            diagnostics.append(f"Section '{section}' found but not in expected format")
        else:
            diagnostics.append(f"Section '{section}' not found in content")

    # Check content length
    if len(content) < 50:
        diagnostics.append(f"Content is very short ({len(content)} chars)")

    # Check for potential alternative section names
    words = re.findall(r'\b[A-Z][A-Z\s]+\b', content)
    if words:
        unique_words = set(words[:5])  # First 5 unique uppercase phrases
        diagnostics.append(f"Found uppercase phrases: {', '.join(unique_words)}")

    return "; ".join(diagnostics)


def parse_bilateral_decision(content: str, logger: Optional[logging.Logger] = None) -> Dict[str, any]:
    """
    Parse bilateral communication decision

    Extracts:
    - Whether to initiate bilateral (yes/no)
    - Target actor
    - Initial message

    Args:
        content: Raw LLM response
        logger: Optional logger for diagnostic information

    Returns:
        Dict with 'initiate_bilateral', 'target_actor', 'message'
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        'initiate_bilateral': False,
        'target_actor': None,
        'message': ''
    }

    # Look for INITIATE_BILATERAL
    initiate_patterns = [
        r'\*\*\s*INITIATE[_\s]BILATERAL\s*:\*\*\s*(yes|no)',
        r'##\s*INITIATE[_\s]BILATERAL\s*\n\s*(yes|no)',
        r'^INITIATE[_\s]BILATERAL\s*:\s*(yes|no)',  # Uppercase without formatting
    ]

    for pattern in initiate_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            result['initiate_bilateral'] = 'yes' in match.group(1).lower()
            logger.debug(f"Found INITIATE_BILATERAL: {match.group(1)}")
            break

    if not result['initiate_bilateral']:
        logger.debug("INITIATE_BILATERAL not found or set to 'no'")

    # Look for TARGET_ACTOR
    target_patterns = [
        r'\*\*\s*TARGET[_\s]ACTOR\s*:\*\*\s*(.+?)(?=\*\*|\n\n)',
        r'##\s*TARGET[_\s]ACTOR\s*\n\s*(.+?)(?=##|\n\n)',
        r'^TARGET[_\s]ACTOR\s*:\s*(.+?)$',  # Uppercase without formatting
    ]

    for pattern in target_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            result['target_actor'] = match.group(1).strip()
            logger.debug(f"Found TARGET_ACTOR: {result['target_actor']}")
            break

    # Look for MESSAGE
    message = extract_section(content, "MESSAGE", None, logger)
    if not message:
        message = extract_section(content, "INITIAL MESSAGE", None, logger)
    if message:
        result['message'] = message
        logger.debug(f"Found MESSAGE ({len(message)} chars)")
    elif result['initiate_bilateral']:
        logger.warning("INITIATE_BILATERAL is yes but no MESSAGE found")

    return result


def parse_coalition_decision(content: str, logger: Optional[logging.Logger] = None) -> Dict[str, any]:
    """
    Parse coalition formation decision

    Extracts:
    - Whether to propose coalition (yes/no)
    - Coalition members
    - Purpose

    Args:
        content: Raw LLM response
        logger: Optional logger for diagnostic information

    Returns:
        Dict with 'propose_coalition', 'members', 'purpose'
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        'propose_coalition': False,
        'members': [],
        'purpose': ''
    }

    # Look for PROPOSE_COALITION
    propose_patterns = [
        r'\*\*\s*PROPOSE[_\s]COALITION\s*:\*\*\s*(yes|no)',
        r'##\s*PROPOSE[_\s]COALITION\s*\n\s*(yes|no)',
        r'^PROPOSE[_\s]COALITION\s*:\s*(yes|no)',  # Uppercase without formatting
    ]

    for pattern in propose_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            result['propose_coalition'] = 'yes' in match.group(1).lower()
            logger.debug(f"Found PROPOSE_COALITION: {match.group(1)}")
            break

    # Look for MEMBERS (comma-separated list)
    members_patterns = [
        r'\*\*\s*MEMBERS\s*:\*\*\s*(.+?)(?=\*\*|\n\n)',
        r'##\s*MEMBERS\s*\n\s*(.+?)(?=##|\n\n)',
        r'^MEMBERS\s*:\s*(.+?)$',  # Uppercase without formatting
    ]

    for pattern in members_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            members_str = match.group(1).strip()
            # Split by comma or newline
            members = [m.strip() for m in re.split(r'[,\n]', members_str) if m.strip()]
            result['members'] = members
            logger.debug(f"Found MEMBERS: {', '.join(members)}")
            break

    # Look for PURPOSE
    purpose = extract_section(content, "PURPOSE", None, logger)
    if not purpose:
        purpose = extract_section(content, "COALITION PURPOSE", None, logger)
    if purpose:
        result['purpose'] = purpose
        logger.debug(f"Found PURPOSE ({len(purpose)} chars)")

    return result


def parse_coalition_response(content: str, logger: Optional[logging.Logger] = None) -> Dict[str, any]:
    """
    Parse coalition invitation response

    Extracts:
    - Decision (accept/reject)
    - Response message
    - Internal notes

    Args:
        content: Raw LLM response
        logger: Optional logger for diagnostic information

    Returns:
        Dict with 'decision', 'response', 'internal_notes'
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    result = {
        'decision': 'reject',
        'response': '',
        'internal_notes': ''
    }

    # Look for DECISION
    decision_patterns = [
        r'\*\*\s*DECISION\s*:\*\*\s*(accept|reject)',
        r'##\s*DECISION\s*\n\s*(accept|reject)',
        r'^DECISION\s*:\s*(accept|reject)',  # Uppercase without formatting
    ]

    for pattern in decision_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            result['decision'] = match.group(1).lower()
            logger.debug(f"Found DECISION: {result['decision']}")
            break

    # Look for RESPONSE
    response = extract_section(content, "RESPONSE", None, logger)
    if not response:
        response = extract_section(content, "MESSAGE", None, logger)
    if response:
        result['response'] = response
        logger.debug(f"Found RESPONSE ({len(response)} chars)")

    # Look for INTERNAL_NOTES
    internal_notes = extract_section(content, "INTERNAL NOTES", None, logger)
    if not internal_notes:
        internal_notes = extract_section(content, "INTERNAL_NOTES", None, logger)
    if not internal_notes:
        internal_notes = extract_section(content, "NOTES", None, logger)
    if internal_notes:
        result['internal_notes'] = internal_notes
        logger.debug(f"Found INTERNAL_NOTES ({len(internal_notes)} chars)")

    return result
