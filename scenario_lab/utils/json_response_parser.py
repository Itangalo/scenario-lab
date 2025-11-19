"""
JSON Response Parser for V2 Architecture

Provides robust JSON parsing for actor decisions with:
- Strict JSON parsing with schema validation
- Markdown fallback for V1 compatibility
- Markdown generation from JSON
- Error recovery strategies
"""
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ActorDecisionJSON(BaseModel):
    """Schema for actor decision in JSON format"""

    goals: Dict[str, str] = Field(
        ...,
        description="Dictionary with 'long_term' and 'short_term' goal descriptions",
    )
    reasoning: str = Field(..., min_length=10, description="Actor's reasoning")
    action: str = Field(..., min_length=10, description="Actor's action")

    class Config:
        extra = "allow"  # Allow extra fields for future extension


def extract_json_from_response(content: str) -> Optional[str]:
    """
    Extract JSON object from LLM response

    Handles cases where JSON is:
    - Wrapped in markdown code blocks (```json ... ```)
    - Wrapped in plain code blocks (``` ... ```)
    - Plain JSON in the response
    - Preceded by text explanation

    Args:
        content: Raw LLM response

    Returns:
        Extracted JSON string, or None if not found
    """
    # Strategy 1: Look for JSON in code blocks
    patterns = [
        r"```json\s*\n(.+?)\n```",  # ```json ... ```
        r"```\s*\n(\{.+?\})\n```",  # ``` {...} ```
        r"```\s*\n(\[.+?\])\n```",  # ``` [...] ```
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            logger.debug("Found JSON in markdown code block")
            return match.group(1).strip()

    # Strategy 2: Look for raw JSON objects
    # Find content between first { and last }
    brace_pattern = r"(\{(?:[^{}]|(?:\{[^{}]*\}))*\})"
    match = re.search(brace_pattern, content, re.DOTALL)
    if match:
        logger.debug("Found raw JSON object in response")
        return match.group(1).strip()

    # Strategy 3: Look for JSON arrays
    bracket_pattern = r"(\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\])"
    match = re.search(bracket_pattern, content, re.DOTALL)
    if match:
        logger.debug("Found raw JSON array in response")
        return match.group(1).strip()

    logger.debug("No JSON found in response")
    return None


def parse_json_decision(
    content: str, validate: bool = True
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse actor decision from JSON format

    Args:
        content: Raw LLM response (may contain JSON)
        validate: Whether to validate against schema

    Returns:
        Tuple of (parsed_dict, error_message)
        If successful: (dict, None)
        If failed: (None, error_message)
    """
    # Extract JSON from response
    json_str = extract_json_from_response(content)
    if not json_str:
        return None, "No JSON found in response"

    # Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed: {e}")
        return None, f"Invalid JSON: {e}"

    # Validate schema if requested
    if validate:
        try:
            validated = ActorDecisionJSON(**data)
            return validated.dict(), None
        except ValidationError as e:
            logger.warning(f"JSON validation failed: {e}")
            # Return raw data anyway, but with warning
            return data, f"Schema validation failed: {e}"

    return data, None


def json_to_markdown(decision: Dict[str, Any]) -> str:
    """
    Convert JSON decision to markdown format for human readability

    Args:
        decision: Parsed decision dictionary

    Returns:
        Markdown-formatted string
    """
    markdown_parts = []

    # Goals section
    if "goals" in decision and isinstance(decision["goals"], dict):
        goals = decision["goals"]

        if "long_term" in goals:
            markdown_parts.append("**LONG-TERM GOALS:**")
            markdown_parts.append(goals["long_term"])
            markdown_parts.append("")

        if "short_term" in goals:
            markdown_parts.append("**SHORT-TERM PRIORITIES:**")
            markdown_parts.append(goals["short_term"])
            markdown_parts.append("")

    # Reasoning section
    if "reasoning" in decision:
        markdown_parts.append("**REASONING:**")
        markdown_parts.append(decision["reasoning"])
        markdown_parts.append("")

    # Action section
    if "action" in decision:
        markdown_parts.append("**ACTION:**")
        markdown_parts.append(decision["action"])
        markdown_parts.append("")

    return "\n".join(markdown_parts).strip()


def parse_decision_with_fallback(content: str) -> Dict[str, str]:
    """
    Parse actor decision with JSON-first strategy and markdown fallback

    Tries in order:
    1. JSON parsing
    2. Markdown parsing (V1 fallback)

    Args:
        content: Raw LLM response

    Returns:
        Dict with 'goals', 'reasoning', 'action' keys
    """
    # Try JSON parsing first
    parsed_json, error = parse_json_decision(content, validate=False)

    if parsed_json:
        logger.debug("Successfully parsed JSON decision")

        # Convert to expected format
        result = {
            "goals": "",
            "reasoning": parsed_json.get("reasoning", ""),
            "action": parsed_json.get("action", ""),
        }

        # Handle goals (could be dict or string)
        if "goals" in parsed_json:
            goals_data = parsed_json["goals"]
            if isinstance(goals_data, dict):
                # Convert dict to formatted string
                goals_parts = []
                if "long_term" in goals_data:
                    goals_parts.append(f"**LONG-TERM GOALS:**\n{goals_data['long_term']}")
                if "short_term" in goals_data:
                    goals_parts.append(
                        f"**SHORT-TERM PRIORITIES:**\n{goals_data['short_term']}"
                    )
                result["goals"] = "\n\n".join(goals_parts)
            elif isinstance(goals_data, str):
                result["goals"] = goals_data

        return result

    # Fallback to V1 markdown parsing
    logger.debug("JSON parsing failed, falling back to markdown parser")

    # Import V1 parser
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from response_parser import parse_actor_decision

    return parse_actor_decision(content)


def format_json_prompt_instructions() -> str:
    """
    Get JSON format instructions to append to actor prompts

    Returns:
        Markdown string with JSON format instructions
    """
    return """
## Response Format

Respond with a valid JSON object in this format:

```json
{
  "goals": {
    "long_term": "Your long-term strategic goals...",
    "short_term": "Your immediate priorities for this turn..."
  },
  "reasoning": "Your analysis of the situation and rationale for your decision...",
  "action": "Your specific action this turn..."
}
```

**Important:**
- Provide a valid JSON object only
- Include all three fields: goals (with long_term and short_term), reasoning, action
- Reasoning and action should be at least one substantial paragraph each
- You may include markdown formatting within the string values
"""
