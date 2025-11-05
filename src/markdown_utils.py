"""
Markdown Utilities - Clean and validate markdown output
"""
import re
from typing import List, Tuple, Dict
from difflib import SequenceMatcher


def text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    # Normalize whitespace for comparison
    text1_normalized = ' '.join(text1.split())
    text2_normalized = ' '.join(text2.split())

    return SequenceMatcher(None, text1_normalized, text2_normalized).ratio()


def extract_section_content(markdown_content: str, section_name: str) -> str:
    """
    Extract content from a specific section

    Args:
        markdown_content: Full markdown content
        section_name: Name of section (e.g., "Reasoning", "Action")

    Returns:
        Content of the section, empty string if not found
    """
    # Try to match section header
    pattern = rf'^##\s+{re.escape(section_name)}\s*$'
    match = re.search(pattern, markdown_content, re.MULTILINE | re.IGNORECASE)

    if not match:
        return ""

    # Find content between this section and next section or separator
    start_pos = match.end()
    next_section = re.search(r'\n##\s+|\n---', markdown_content[start_pos:])

    if next_section:
        end_pos = start_pos + next_section.start()
        content = markdown_content[start_pos:end_pos]
    else:
        content = markdown_content[start_pos:]

    return content.strip()


def detect_content_duplication(markdown_content: str, similarity_threshold: float = 0.7) -> Dict[str, any]:
    """
    Detect if ACTION section contains content from GOALS or REASONING sections

    Args:
        markdown_content: Full markdown content
        similarity_threshold: Minimum similarity to consider as duplicate (0.0-1.0)

    Returns:
        Dict with duplication info: {
            'has_duplication': bool,
            'action_contains_goals': bool,
            'action_contains_reasoning': bool,
            'details': str
        }
    """
    goals_content = extract_section_content(markdown_content, "Current Goals")
    reasoning_content = extract_section_content(markdown_content, "Reasoning")
    action_content = extract_section_content(markdown_content, "Action")

    result = {
        'has_duplication': False,
        'action_contains_goals': False,
        'action_contains_reasoning': False,
        'details': []
    }

    if not action_content:
        return result

    # Check if ACTION contains GOALS content
    if goals_content and len(goals_content) > 50:
        similarity = text_similarity(goals_content, action_content)
        if similarity > similarity_threshold:
            result['has_duplication'] = True
            result['action_contains_goals'] = True
            result['details'].append(f"ACTION contains GOALS content (similarity: {similarity:.2f})")

    # Check if ACTION contains REASONING content
    if reasoning_content and len(reasoning_content) > 50:
        similarity = text_similarity(reasoning_content, action_content)
        if similarity > similarity_threshold:
            result['has_duplication'] = True
            result['action_contains_reasoning'] = True
            result['details'].append(f"ACTION contains REASONING content (similarity: {similarity:.2f})")

        # Also check if ACTION contains REASONING as substring
        # (for cases where reasoning is embedded in action text)
        reasoning_normalized = ' '.join(reasoning_content.split())
        action_normalized = ' '.join(action_content.split())

        if len(reasoning_normalized) > 100 and reasoning_normalized in action_normalized:
            result['has_duplication'] = True
            result['action_contains_reasoning'] = True
            result['details'].append("ACTION contains REASONING as substring")

    return result


def remove_duplicate_sections(markdown_content: str) -> str:
    """
    Remove duplicate sections from markdown content

    Detects when the same section (Goals, Reasoning, Action) appears multiple times
    and keeps only the first occurrence.

    Args:
        markdown_content: Raw markdown content

    Returns:
        Cleaned markdown with duplicates removed
    """
    # Define section markers
    section_patterns = [
        (r'^## Current Goals\s*$', '## Current Goals'),
        (r'^## Reasoning\s*$', '## Reasoning'),
        (r'^## Action\s*$', '## Action'),
        (r'^##\s*ACTION\s*$', '## Action'),  # Variations
        (r'^##\s*REASONING\s*$', '## Reasoning'),
    ]

    lines = markdown_content.split('\n')
    result_lines = []
    seen_sections = set()
    current_section = None
    skip_until_next_section = False

    for i, line in enumerate(lines):
        # Check if this line is a section header
        is_section_header = False
        section_name = None

        for pattern, normalized_name in section_patterns:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                is_section_header = True
                section_name = normalized_name
                break

        if is_section_header:
            # If we've seen this section before, skip it and its content
            if section_name in seen_sections:
                skip_until_next_section = True
                continue
            else:
                seen_sections.add(section_name)
                skip_until_next_section = False
                result_lines.append(section_name)
                current_section = section_name
                continue

        # Check if we hit a separator or new section (stop skipping)
        if line.strip().startswith('##') and not skip_until_next_section:
            current_section = None

        # Add line if we're not skipping
        if not skip_until_next_section:
            result_lines.append(line)

    return '\n'.join(result_lines)


def remove_embedded_duplicates(markdown_content: str) -> str:
    """
    Remove content duplication where ACTION contains GOALS or REASONING

    If ACTION section contains the same content as GOALS or REASONING sections,
    this function will clean it to avoid duplication.

    Args:
        markdown_content: Markdown content to clean

    Returns:
        Cleaned markdown with embedded duplicates removed
    """
    # Detect duplication
    duplication_info = detect_content_duplication(markdown_content)

    if not duplication_info['has_duplication']:
        return markdown_content

    # Extract sections
    goals_content = extract_section_content(markdown_content, "Current Goals")
    reasoning_content = extract_section_content(markdown_content, "Reasoning")
    action_content = extract_section_content(markdown_content, "Action")

    # If ACTION contains everything, try to extract just the action part
    if duplication_info['action_contains_reasoning'] or duplication_info['action_contains_goals']:
        # Try to find "action" markers in the ACTION section
        action_markers = [
            r'(?:^|\n)\s*\*\*\s*ACTION\s*:\*\*\s*(.+?)(?=\n\*\*|\Z)',
            r'(?:^|\n)\s*\*\*\s*DECISION\s*:\*\*\s*(.+?)(?=\n\*\*|\Z)',
            r'(?:^|\n)\s*\*\*\s*PLAN\s*:\*\*\s*(.+?)(?=\n\*\*|\Z)',
            r'(?:^|\n)\s*Action:\s*(.+?)(?=\n\n|\Z)',
        ]

        extracted_action = None
        for pattern in action_markers:
            match = re.search(pattern, action_content, re.DOTALL | re.IGNORECASE)
            if match:
                extracted_action = match.group(1).strip()
                # Only use if it's reasonably sized (not empty, not entire content)
                if 20 < len(extracted_action) < len(action_content) * 0.9:
                    break

        # If we found a clean action, replace the ACTION section
        if extracted_action:
            # Rebuild markdown with cleaned action
            pattern = r'(##\s+Action\s*\n\n)(.+?)(?=\n##|\n---|$)'
            replacement = r'\g<1>' + extracted_action + '\n'
            markdown_content = re.sub(pattern, replacement, markdown_content, flags=re.DOTALL)

    return markdown_content


def clean_markdown_formatting(markdown_content: str, enable_deduplication: bool = True) -> str:
    """
    Clean and normalize markdown formatting

    - Remove duplicate sections
    - Remove embedded content duplication
    - Normalize section headers
    - Remove excessive blank lines
    - Ensure consistent formatting

    Args:
        markdown_content: Raw markdown content
        enable_deduplication: If True, remove embedded duplicates (default: True)

    Returns:
        Cleaned and normalized markdown
    """
    # First pass: remove duplicate section headers
    content = remove_duplicate_sections(markdown_content)

    # Second pass: remove embedded duplicates (where ACTION contains GOALS/REASONING)
    if enable_deduplication:
        content = remove_embedded_duplicates(content)

    # Normalize section headers (ensure proper case)
    content = re.sub(r'^##\s*CURRENT GOALS\s*$', '## Current Goals', content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'^##\s*REASONING\s*$', '## Reasoning', content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'^##\s*ACTION\s*$', '## Action', content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    # Ensure file ends with single newline
    content = content.rstrip() + '\n'

    return content


def validate_markdown_structure(markdown_content: str) -> Tuple[bool, List[str]]:
    """
    Validate that markdown has expected structure

    Checks for:
    - Header information (actor name, turn, scenario)
    - Expected sections (may include Goals, Reasoning, Action)

    Args:
        markdown_content: Markdown content to validate

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check for required header elements
    if not re.search(r'^#\s+\w+.*Turn\s+\d+', markdown_content, re.MULTILINE):
        issues.append("Missing or malformed header (should be '# ActorName - Turn N')")

    if '**Scenario:**' not in markdown_content:
        issues.append("Missing scenario name")

    if '**Turn Duration:**' not in markdown_content:
        issues.append("Missing turn duration")

    # Check for at least Reasoning or Action section
    has_reasoning = bool(re.search(r'^##\s+(Reasoning|REASONING)', markdown_content, re.MULTILINE | re.IGNORECASE))
    has_action = bool(re.search(r'^##\s+(Action|ACTION)', markdown_content, re.MULTILINE | re.IGNORECASE))

    if not (has_reasoning or has_action):
        issues.append("Missing both Reasoning and Action sections")

    is_valid = len(issues) == 0
    return is_valid, issues
