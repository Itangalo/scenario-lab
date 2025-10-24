"""
Markdown Utilities - Clean and validate markdown output
"""
import re
from typing import List, Tuple


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


def clean_markdown_formatting(markdown_content: str) -> str:
    """
    Clean and normalize markdown formatting

    - Remove duplicate sections
    - Normalize section headers
    - Remove excessive blank lines
    - Ensure consistent formatting

    Args:
        markdown_content: Raw markdown content

    Returns:
        Cleaned and normalized markdown
    """
    # First pass: remove duplicates
    content = remove_duplicate_sections(markdown_content)

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
