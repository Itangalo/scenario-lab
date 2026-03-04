"""Metric rules versioning and changelog parsing."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RulesChangelog:
    """Parsed changelog entry from metric rules update."""

    change_type: str  # "added", "modified", "removed"
    rule_name: str
    change_description: Optional[str] = None
    motivation: Optional[str] = None
    expected_impact: Optional[str] = None


@dataclass
class VersionedRules:
    """Parsed versioned metric rules with changelog."""

    version: int
    turn: int
    full_content: str
    changelog_entries: list[RulesChangelog]
    rules_content: str  # The actual rules section
    has_changelog: bool


def _strip_surrounding_code_fence(content: str) -> str:
    """Remove a single surrounding fenced code block wrapper if present."""
    stripped = content.strip()
    fenced_match = re.match(r"^```[^\n]*\n(?P<body>.*)\n```$", stripped, re.DOTALL)
    if fenced_match:
        return fenced_match.group("body").strip()
    return content


def parse_versioned_rules(content: str, expected_turn: int) -> VersionedRules:
    """Parse versioned metric rules output from LLM.

    Args:
        content: Raw LLM output containing versioned rules
        expected_turn: Expected turn number for validation

    Returns:
        VersionedRules object with parsed information

    Raises:
        ValueError: If content doesn't match expected format
    """
    normalized_content = _strip_surrounding_code_fence(content)

    # Extract version and turn from header
    # Format: "# Metric Rules v2 (Turn 3)" or "# Metric Rules v1 (Turn 0 - Initial)"
    header_match = re.search(
        r"#\s*Metric\s+Rules\s+v(\d+)\s*\(Turn\s+(\d+)(?:\s*-\s*Initial)?\)",
        normalized_content,
        re.IGNORECASE,
    )

    if not header_match:
        raise ValueError(
            "Metric rules header not found. Expected format: '# Metric Rules v2 (Turn 3)'"
        )

    version = int(header_match.group(1))
    turn = int(header_match.group(2))

    if turn != expected_turn:
        raise ValueError(f"Turn mismatch: expected {expected_turn}, found {turn} in header")

    # Check if this is initial version (Turn 0 or Turn 1 with "Initial")
    is_initial = turn == 0 or "Initial" in header_match.group(0)

    # Extract changelog section if present
    changelog_entries = []
    has_changelog = False

    if not is_initial:
        # Look for changelog section
        changelog_match = re.search(
            r"##\s*Changelog\s+from\s+v(\d+)(.*?)(?=##\s*Rules|##\s*[A-Z]|\Z)",
            normalized_content,
            re.DOTALL | re.IGNORECASE,
        )

        if changelog_match:
            has_changelog = True
            changelog_content = changelog_match.group(2)
            changelog_entries = _parse_changelog_content(changelog_content)
        else:
            # Changelog should be present for non-initial versions
            # But we'll allow it to be missing with a warning (handled by caller)
            pass

    # Extract rules section
    # Look for "## Rules" header
    rules_match = re.search(r"##\s*Rules\s*\n(.*)", normalized_content, re.DOTALL | re.IGNORECASE)

    if rules_match:
        rules_content = rules_match.group(1).strip()
    else:
        # If no explicit "## Rules" section, take everything after changelog (or after header if no changelog)
        if has_changelog and changelog_match:
            rules_content = normalized_content[changelog_match.end() :].strip()
        else:
            # Take everything after header
            rules_content = normalized_content[header_match.end() :].strip()

    return VersionedRules(
        version=version,
        turn=turn,
        full_content=normalized_content,
        changelog_entries=changelog_entries,
        rules_content=rules_content,
        has_changelog=has_changelog,
    )


def _parse_changelog_content(changelog_text: str) -> list[RulesChangelog]:
    """Parse changelog section into structured entries.

    Args:
        changelog_text: Text content of changelog section

    Returns:
        List of RulesChangelog entries
    """
    entries = []

    # Match patterns like:
    # - **Added:** `rule_name`
    #   - **Rule:** description
    #   - **Motivation:** why
    #   - **Expected impact:** impact
    entry_pattern = re.compile(
        r"-\s*\*\*(Added|Modified|Removed):\*\*\s*"
        r"(?:`([^`\n]+)`|([^\n(]+?))"
        r"\s*(?:\([^)\n]*\))?\s*\n"
        r"((?:.*?\n)*?)(?=-\s*\*\*(?:Added|Modified|Removed)|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    for match in entry_pattern.finditer(changelog_text):
        change_type = match.group(1).lower()
        rule_name = (match.group(2) or match.group(3) or "").strip()
        details = match.group(4)

        # Extract sub-fields from details
        change_desc = None
        motivation = None
        expected_impact = None

        # Look for **Rule:**, **Change:**, **Motivation:**, **Expected impact:**
        if change_match := re.search(r"\*\*(?:Rule|Change):\*\*\s*(.*?)(?=\n\s*-\s*\*\*|\Z)", details, re.DOTALL):
            change_desc = change_match.group(1).strip()

        if motivation_match := re.search(r"\*\*Motivation:\*\*\s*(.*?)(?=\n\s*-\s*\*\*|\Z)", details, re.DOTALL):
            motivation = motivation_match.group(1).strip()

        if impact_match := re.search(
            r"\*\*Expected impact:\*\*\s*(.*?)(?=\n\s*-\s*\*\*|\Z)", details, re.DOTALL
        ):
            expected_impact = impact_match.group(1).strip()

        entries.append(
            RulesChangelog(
                change_type=change_type,
                rule_name=rule_name,
                change_description=change_desc,
                motivation=motivation,
                expected_impact=expected_impact,
            )
        )

    return entries


def validate_rules_format(content: str, expected_turn: int) -> tuple[bool, list[str]]:
    """Validate that metric rules follow the expected versioned format.

    Args:
        content: Raw LLM output
        expected_turn: Expected turn number

    Returns:
        Tuple of (is_valid, list of warning messages)
    """
    warnings = []

    try:
        parsed = parse_versioned_rules(content, expected_turn)

        # Check version number is reasonable
        if parsed.version < 1:
            warnings.append(f"Version number {parsed.version} should be >= 1")

        # Check changelog presence for non-initial turns
        if expected_turn > 1 and not parsed.has_changelog:
            warnings.append(
                f"Changelog missing for turn {expected_turn}. All updates after turn 1 should include changelog."
            )

        # Check that changelog has entries if present
        if parsed.has_changelog and len(parsed.changelog_entries) == 0:
            warnings.append("Changelog section present but no parseable entries found")

        # Check that rules content is not empty
        if not parsed.rules_content or len(parsed.rules_content.strip()) < 10:
            warnings.append("Rules content is empty or too short")

        # Validate changelog entries have required fields
        for entry in parsed.changelog_entries:
            if not entry.motivation:
                warnings.append(f"Changelog entry '{entry.rule_name}' missing motivation")
            if not entry.expected_impact:
                warnings.append(f"Changelog entry '{entry.rule_name}' missing expected impact")

        return len(warnings) == 0, warnings

    except ValueError as e:
        return False, [f"Parse error: {str(e)}"]


def get_changelog_summary(parsed: VersionedRules) -> str:
    """Generate a human-readable summary of changelog.

    Args:
        parsed: Parsed VersionedRules

    Returns:
        Summary string
    """
    if not parsed.has_changelog or not parsed.changelog_entries:
        return "No changes"

    summary_parts = []
    added = sum(1 for e in parsed.changelog_entries if e.change_type == "added")
    modified = sum(1 for e in parsed.changelog_entries if e.change_type == "modified")
    removed = sum(1 for e in parsed.changelog_entries if e.change_type == "removed")

    if added:
        summary_parts.append(f"{added} added")
    if modified:
        summary_parts.append(f"{modified} modified")
    if removed:
        summary_parts.append(f"{removed} removed")

    return ", ".join(summary_parts)
