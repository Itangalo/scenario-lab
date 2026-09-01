"""Unit tests for loader module parsing logic."""

import pytest
from pathlib import Path
from scenario_lab.loader import load_metrics, load_events, load_actor, create_metric, create_event, get_time_period, collect_unknown_event_fields

def test_load_metrics(tmp_path):
    """Test parsing of metrics markdown file."""
    content = """
## metric1
**Description:** First metric
**ID:** metric1
**Min:** 0
**Max:** 100
**Unit:** percent
**Starting value:** 50
**Reference points:**
- 0: low
- 100: high

## metric_two
**Description:** Second metric (English)
**ID:** metric_two
**Min:** -10
**Max:** 10
**Unit:** index
**Starting value:** 0
**Reference points:**
- -10: bad
- 10: good
"""
    f = tmp_path / "metrics.md"
    f.write_text(content, encoding="utf-8")
    
    metrics = load_metrics(f)
    
    assert len(metrics.metrics) == 2
    
    m1 = metrics.metrics["metric1"]
    assert m1.value == 50
    assert m1.min_value == 0
    assert m1.max_value == 100
    assert m1.unit == "percent"
    assert m1.reference_points[0] == "low"
    
    m2 = metrics.metrics["metric_two"]
    assert m2.value == 0
    assert m2.min_value == -10
    assert m2.description == "Second metric (English)"
    assert m2.reference_points[10] == "good"

def test_load_events(tmp_path):
    """Test parsing of events markdown file."""
    content = """
## Event One
**ID:** event1
**Condition:** condition1
**Probability:** 0.5
**Can repeat:** Yes
**Description:** Desc 1

## Event Two
**ID:** event2
**Condition:** condition2
**Probability:** (metric1 - 10) / 100
**Can repeat:** No
**Description:** Desc 2
"""
    f = tmp_path / "events.md"
    f.write_text(content, encoding="utf-8")
    
    events = load_events(f)
    
    assert len(events) == 2
    
    e1 = events[0]
    assert e1.id == "event1"
    assert e1.condition == "condition1"
    assert e1.probability == "0.5"
    assert e1.can_repeat is True
    assert e1.description == "Desc 1"
    
    e2 = events[1]
    assert e2.id == "event2"
    assert e2.condition == "condition2"
    assert e2.probability == "(metric1 - 10) / 100"
    assert e2.can_repeat is False

def test_load_actor(tmp_path):
    """Test parsing of actor markdown file."""
    content = """# My Actor
## Short description
A short summary.
## Long description
A longer description
spanning multiple lines.
"""
    f = tmp_path / "actor.md"
    f.write_text(content, encoding="utf-8")
    
    actor = load_actor(f, "actor_id")
    
    assert actor.id == "actor_id"
    assert actor.name == "My Actor"
    assert actor.short_description == "A short summary."
    assert "spanning multiple lines" in actor.long_description
    assert actor.initial_statements == [] # Defaults


def test_load_actor_parses_statements_and_traits(tmp_path):
    """Actor parser should load h3 statements/traits sections under long description."""
    content = """# My Actor
## Short description
A short summary.
## Long description
Long details here.
### Statements
- `protect_infrastructure` (commitment): Protect critical infrastructure
- `investor_confidence` (position): Maintain investor confidence
- `we_are_reliable` (identity): We are the reliable operator
### Behavioral traits
- Pragmatic under pressure
1. Risk-aware communicator
"""
    f = tmp_path / "actor.md"
    f.write_text(content, encoding="utf-8")

    actor = load_actor(f, "actor_id")

    assert [(s.id, s.tier, s.text) for s in actor.initial_statements] == [
        ("protect_infrastructure", "commitment", "Protect critical infrastructure"),
        ("investor_confidence", "position", "Maintain investor confidence"),
        ("we_are_reliable", "identity", "We are the reliable operator"),
    ]
    assert actor.behavioral_traits == [
        "Pragmatic under pressure",
        "Risk-aware communicator",
    ]
    # The live ledger starts as a copy, not as a shared reference.
    assert [s.id for s in actor.statements] == [s.id for s in actor.initial_statements]
    actor.statements[0].text = "changed"
    assert actor.initial_statements[0].text == "Protect critical infrastructure"


def test_load_actor_rejects_the_old_goals_section(tmp_path):
    """`### Initial goals` is gone; the loader must say so rather than read prose."""
    content = """# My Actor
## Short description
A short summary.
## Long description
Long details here.
### Initial goals
- Protect critical infrastructure
"""
    f = tmp_path / "actor.md"
    f.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Initial goals"):
        load_actor(f, "actor_id")


def test_load_actor_rejects_a_malformed_statement(tmp_path):
    """A statement without an id and tier is an error, not a silently dropped line."""
    content = """# My Actor
## Short description
A short summary.
## Long description
Long details here.
### Statements
- Protect critical infrastructure
"""
    f = tmp_path / "actor.md"
    f.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="malformed statement"):
        load_actor(f, "actor_id")


def test_load_actor_does_not_parse_h2_traits(tmp_path):
    """Legacy h2 sections should not populate statements/traits."""
    content = """# My Actor
## Short description
A short summary.
## Long description
Long details here.
## Behavioral traits
- Legacy trait format
"""
    f = tmp_path / "actor.md"
    f.write_text(content, encoding="utf-8")

    actor = load_actor(f, "actor_id")

    assert actor.initial_statements == []
    assert actor.behavioral_traits == []


def test_get_time_period_accepts_year_month():
    """Time period calculation works with YYYY-MM start dates."""
    period = get_time_period("2026-01", turn=1, time_scale="6 months per turn")
    assert period == "January-June 2026"


def test_get_time_period_accepts_year_only():
    """Time period calculation works with YYYY start dates (defaults to January)."""
    period = get_time_period("2026", turn=2, time_scale="6 months per turn")
    assert period == "July-December 2026"


def test_get_time_period_supports_weeks_with_day_precision():
    """Time period calculation supports weekly cadence with YYYY-MM-DD start dates."""
    period_1 = get_time_period("2026-03-09", turn=1, time_scale="2 weeks per turn")
    period_2 = get_time_period("2026-03-09", turn=2, time_scale="2 weeks per turn")

    assert period_1 == "2026-03-09 to 2026-03-22"
    assert period_2 == "2026-03-23 to 2026-04-05"


def test_collect_unknown_event_fields_reports_discarded_labels(tmp_path):
    """Fields the parser drops are reported, keyed by event."""
    content = """# Events

## Framing

**Note:** prose outside an event block is not an event field.

---

## Real Event
**ID:** real_event
**Condition:** Always
**Probability:** 0.1
**Can repeat:** No
**Makes the case for:** categories 1 and 6, for 3 turns
**Effects:** something the model never sees
**Description:** A thing happens.

## Clean Event
**ID:** clean_event
**Condition:** Always
**Probability:** 0.2
**Can repeat:** Yes
**Eligible:** metric_a > 10
**Description:** Another thing happens.
"""
    path = tmp_path / "events.md"
    path.write_text(content)

    unknown = collect_unknown_event_fields(path)

    assert unknown == {"real_event": ["Makes the case for", "Effects"]}
    assert "clean_event" not in unknown


def test_collect_unknown_event_fields_clean_file_is_silent(tmp_path):
    """A file using only the six parsed fields reports nothing."""
    content = """## Only Known Fields
**ID:** e1
**Condition:** Always
**Probability:** 0.5
**Can repeat:** No
**Description:** Text.
"""
    path = tmp_path / "events.md"
    path.write_text(content)

    assert collect_unknown_event_fields(path) == {}
