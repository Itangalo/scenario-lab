"""
YAML helper utilities for safe serialization.

Handles YAML-problematic characters in user input.
"""
import re
from typing import Any, Dict, List, Union


def sanitize_yaml_string(value: str) -> str:
    """
    Sanitize a string for safe YAML serialization.

    YAML interprets "KEY: value" as a mapping when used in list items:
        constraints:
          - "WARNING: this breaks"  # Works (quoted)
          - WARNING: this breaks    # Fails (parsed as mapping)

    This function replaces ': ' (colon-space) with ' - ' (space-dash-space)
    to prevent YAML parsing issues while preserving readability.

    Args:
        value: String that may contain YAML-problematic characters

    Returns:
        Sanitized string safe for YAML list items
    """
    if not isinstance(value, str):
        return value

    # Replace ": " with " - " to avoid YAML mapping interpretation
    # Only replace when colon is followed by space (actual YAML mapping syntax)
    return re.sub(r':\s+', ' - ', value)


def sanitize_yaml_list(items: List[str]) -> List[str]:
    """
    Sanitize all strings in a list for YAML safety.

    Args:
        items: List of strings to sanitize

    Returns:
        List with all strings sanitized
    """
    if items is None:
        return None
    return [sanitize_yaml_string(item) for item in items]


def sanitize_actor_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize an actor configuration dict for safe YAML serialization.

    Handles known list fields that may contain user input:
    - goals
    - constraints
    - personality_traits
    - preferred_coalitions

    Args:
        config: Actor configuration dictionary

    Returns:
        Config with sanitized string lists
    """
    result = config.copy()

    # Fields that are lists of strings
    list_fields = ['goals', 'constraints', 'personality_traits', 'preferred_coalitions']

    for field in list_fields:
        if field in result and isinstance(result[field], list):
            result[field] = sanitize_yaml_list(result[field])

    return result


def sanitize_scenario_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a scenario configuration dict for safe YAML serialization.

    Args:
        config: Scenario configuration dictionary

    Returns:
        Config with sanitized strings
    """
    # Currently scenarios don't have list fields prone to this issue
    # but this provides a hook for future sanitization
    return config
