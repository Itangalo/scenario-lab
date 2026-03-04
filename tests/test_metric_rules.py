"""Tests for metric rules versioning and changelog parsing."""

import pytest
from scenario_lab.metric_rules import (
    parse_versioned_rules,
    validate_rules_format,
    get_changelog_summary,
    VersionedRules,
)


def test_parse_initial_version():
    """Test parsing initial version (v1, Turn 0)."""
    content = """# Metric Rules v1 (Turn 0 - Initial)

## Rules

1. ai_capability doubles every six months
2. High unemployment decreases public_sentiment
"""
    parsed = parse_versioned_rules(content, expected_turn=0)

    assert parsed.version == 1
    assert parsed.turn == 0
    assert not parsed.has_changelog
    assert len(parsed.changelog_entries) == 0
    assert "ai_capability doubles" in parsed.rules_content


def test_parse_versioned_update_with_changelog():
    """Test parsing versioned update with changelog."""
    content = """# Metric Rules v2 (Turn 3)

## Changelog from v1

- **Added:** `unemployment_lag_effect`
  - **Rule:** Unemployment changes lag 1 turn behind AI adoption shifts
  - **Motivation:** Realistic time for labor market adjustment
  - **Expected impact:** Smoother unemployment curves

- **Modified:** `ai_capability_growth`
  - **Change:** Reduced growth rate from doubles to +50%
  - **Motivation:** Compute constraints
  - **Expected impact:** Slower AI progress

- **Removed:** `public_sentiment_media_boost`
  - **Motivation:** Media strategy changed
  - **Expected impact:** Sentiment driven by economics

## Rules

1. ai_capability increases by 50% every six months
2. Unemployment changes lag 1 turn behind AI adoption
3. High unemployment decreases public_sentiment
"""
    parsed = parse_versioned_rules(content, expected_turn=3)

    assert parsed.version == 2
    assert parsed.turn == 3
    assert parsed.has_changelog
    assert len(parsed.changelog_entries) == 3

    # Check added entry
    added = next(e for e in parsed.changelog_entries if e.change_type == "added")
    assert added.rule_name == "unemployment_lag_effect"
    assert "Realistic time" in added.motivation
    assert "Smoother unemployment" in added.expected_impact

    # Check modified entry
    modified = next(e for e in parsed.changelog_entries if e.change_type == "modified")
    assert modified.rule_name == "ai_capability_growth"
    assert "Compute constraints" in modified.motivation

    # Check removed entry
    removed = next(e for e in parsed.changelog_entries if e.change_type == "removed")
    assert removed.rule_name == "public_sentiment_media_boost"

    # Check rules content
    assert "50% every six months" in parsed.rules_content


def test_parse_missing_header():
    """Test that missing header raises error."""
    content = """Some rules without proper header

1. rule one
2. rule two
"""
    with pytest.raises(ValueError, match="header not found"):
        parse_versioned_rules(content, expected_turn=1)


def test_parse_turn_mismatch():
    """Test that turn mismatch raises error."""
    content = """# Metric Rules v2 (Turn 5)

## Rules

1. some rule
"""
    with pytest.raises(ValueError, match="Turn mismatch"):
        parse_versioned_rules(content, expected_turn=3)


def test_validate_format_valid():
    """Test validation of properly formatted rules."""
    content = """# Metric Rules v2 (Turn 3)

## Changelog from v1

- **Added:** `new_rule`
  - **Rule:** Description of new rule
  - **Motivation:** Why we need it
  - **Expected impact:** What will happen

## Rules

1. Rule one
2. Rule two
"""
    is_valid, warnings = validate_rules_format(content, expected_turn=3)

    assert is_valid
    assert len(warnings) == 0


def test_validate_format_missing_changelog():
    """Test validation warns about missing changelog."""
    content = """# Metric Rules v2 (Turn 3)

## Rules

1. Rule one
2. Rule two
"""
    is_valid, warnings = validate_rules_format(content, expected_turn=3)

    assert not is_valid
    assert any("Changelog missing" in w for w in warnings)


def test_validate_format_initial_no_changelog_ok():
    """Test that initial version doesn't require changelog."""
    content = """# Metric Rules v1 (Turn 0 - Initial)

## Rules

1. Rule one
"""
    is_valid, warnings = validate_rules_format(content, expected_turn=0)

    # Should be valid even without changelog for initial version
    assert is_valid or all("Changelog" not in w for w in warnings)


def test_validate_format_missing_motivation():
    """Test validation warns about incomplete changelog entries."""
    content = """# Metric Rules v2 (Turn 3)

## Changelog from v1

- **Added:** `new_rule`
  - **Rule:** Description

## Rules

1. Rule one
"""
    is_valid, warnings = validate_rules_format(content, expected_turn=3)

    assert not is_valid
    assert any("missing motivation" in w for w in warnings)
    assert any("missing expected impact" in w for w in warnings)


def test_get_changelog_summary_no_changes():
    """Test changelog summary with no changes."""
    parsed = VersionedRules(
        version=1,
        turn=0,
        full_content="",
        changelog_entries=[],
        rules_content="",
        has_changelog=False,
    )

    summary = get_changelog_summary(parsed)
    assert summary == "No changes"


def test_get_changelog_summary_mixed_changes():
    """Test changelog summary with multiple change types."""
    from scenario_lab.metric_rules import RulesChangelog

    parsed = VersionedRules(
        version=2,
        turn=3,
        full_content="",
        changelog_entries=[
            RulesChangelog("added", "rule1"),
            RulesChangelog("added", "rule2"),
            RulesChangelog("modified", "rule3"),
            RulesChangelog("removed", "rule4"),
        ],
        rules_content="",
        has_changelog=True,
    )

    summary = get_changelog_summary(parsed)
    assert "2 added" in summary
    assert "1 modified" in summary
    assert "1 removed" in summary


def test_parse_changelog_without_backticks():
    """Test parsing changelog entries without backticks around rule names."""
    content = """# Metric Rules v2 (Turn 3)

## Changelog from v1

- **Added:** unemployment_lag_effect
  - **Rule:** Unemployment lags behind adoption
  - **Motivation:** Realistic timing
  - **Expected impact:** Smoother curves

## Rules

1. Some rule
"""
    parsed = parse_versioned_rules(content, expected_turn=3)

    assert len(parsed.changelog_entries) == 1
    assert parsed.changelog_entries[0].rule_name == "unemployment_lag_effect"


def test_parse_changelog_with_parenthetical_rule_suffix():
    """Test parsing changelog entries that annotate rule position after the name."""
    content = """# Metric Rules v3 (Turn 2)

## Changelog from v2

- **Modified:** `ai_adoption_growth` (rule 2)
  - **Change:** Increased baseline growth
  - **Motivation:** Stronger rollout than expected
  - **Expected impact:** Faster adoption this turn

- **Removed:** `resistance_halt` (ex-rule 6)
  - **Motivation:** Negative trigger no longer applies
  - **Expected impact:** Simplifies the ruleset

## Rules

1. Rule one
2. Rule two
"""
    parsed = parse_versioned_rules(content, expected_turn=2)

    assert len(parsed.changelog_entries) == 2
    assert parsed.changelog_entries[0].rule_name == "ai_adoption_growth"
    assert parsed.changelog_entries[1].rule_name == "resistance_halt"


def test_parse_versioned_rules_wrapped_in_markdown_code_fence():
    """Test parsing rules output when the whole response is wrapped in a markdown fence."""
    content = """```markdown
# Metric Rules v3 (Turn 2)

## Changelog from v2

- **Added:** `new_rule`
  - **Rule:** New quantitative rule
  - **Motivation:** Needed after a major event
  - **Expected impact:** Clearer metric shifts

## Rules

1. Rule one
2. Rule two
```"""
    parsed = parse_versioned_rules(content, expected_turn=2)
    is_valid, warnings = validate_rules_format(content, expected_turn=2)

    assert parsed.version == 3
    assert len(parsed.changelog_entries) == 1
    assert "Rule one" in parsed.rules_content
    assert is_valid
    assert warnings == []


def test_parse_complex_rules_section():
    """Test parsing rules with complex markdown structure."""
    content = """# Metric Rules v1 (Turn 0 - Initial)

## Rules

## Capability Growth Dynamics

### US Capability Growth
- **100-150:** +15-25 points per turn
- **150-200:** +20-30 points per turn

**Growth modifiers:**
- High compute: +5 points
- Low compute: -5 points

## Alignment Dynamics

Base degradation: -3-5 points per turn
"""
    parsed = parse_versioned_rules(content, expected_turn=0)

    assert parsed.version == 1
    assert "Capability Growth" in parsed.rules_content
    assert "Alignment Dynamics" in parsed.rules_content
    assert "+15-25 points" in parsed.rules_content
