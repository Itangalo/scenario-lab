"""Unit tests for loader module parsing logic."""

import pytest
from pathlib import Path
from scenario_lab.loader import load_metrics, load_events, load_actor, create_metric, create_event, get_time_period

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
    assert actor.initial_goals == [] # Defaults


def test_get_time_period_accepts_year_month():
    """Time period calculation works with YYYY-MM start dates."""
    period = get_time_period("2026-01", turn=1, time_scale="6 months per turn")
    assert period == "January-June 2026"


def test_get_time_period_accepts_year_only():
    """Time period calculation works with YYYY start dates (defaults to January)."""
    period = get_time_period("2026", turn=2, time_scale="6 months per turn")
    assert period == "July-December 2026"
