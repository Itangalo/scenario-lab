"""Metaculus anchors on events: parsing, validation, and patch support."""

from pathlib import Path

from scenario_lab.loader import load_events
from scenario_lab.resource_patches import apply_event_patches, parse_event_patch
from scenario_lab.validator import validate_market_anchors

REPO_ROOT = Path(__file__).resolve().parents[1]


def _events_with_anchor(tmp_path):
    path = tmp_path / "events.md"
    path.write_text(
        "# Events\n\n## The Big One\n\n**ID:** big_one\n\n"
        "**Condition:** none\n\n**Probability:** 10 percent per round\n\n"
        "**Can repeat:** No\n\n"
        "**Description:** Something big happens.\n\n"
        "**Metaculus:** https://www.metaculus.com/questions/12345/big-event/\n\n"
        "**Retrieved:** 2026-10-01\n\n**Market probability:** 34%\n",
        encoding="utf-8",
    )
    return load_events(path)


def test_anchor_fields_parsed(tmp_path):
    (event,) = _events_with_anchor(tmp_path)
    assert event.metaculus_url == "https://www.metaculus.com/questions/12345/big-event/"
    assert event.metaculus_retrieved == "2026-10-01"
    assert event.metaculus_probability == "34%"


def test_anchor_absent_by_default():
    events = load_events(REPO_ROOT / "scenarios/sweden-ai-2030/events.md")
    assert events
    assert all(
        not e.metaculus_url and not e.metaculus_retrieved and not e.metaculus_probability
        for e in events
    )


def _scenario_like(events):
    from scenario_lab.loader import load_scenario

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.events = events
    return scenario


def test_anchor_validation_accepts_good(tmp_path):
    errors, warnings = validate_market_anchors(_scenario_like(_events_with_anchor(tmp_path)))
    assert errors == [] and warnings == []


def test_anchor_validation_rejects_bad(tmp_path):
    path = tmp_path / "events.md"
    path.write_text(
        "# Events\n\n## Bad URL\n\n**ID:** bad_url\n\n**Condition:** none\n\n"
        "**Probability:** 10 percent\n\n**Can repeat:** No\n\n**Description:** x.\n\n"
        "**Metaculus:** https://example.com/poll\n\n**Retrieved:** yesterday\n\n"
        "**Market probability:** lots\n",
        encoding="utf-8",
    )
    errors, _ = validate_market_anchors(_scenario_like(load_events(path)))
    assert len(errors) == 3


def test_anchor_patch_override(tmp_path):
    events = _events_with_anchor(tmp_path)
    patch = tmp_path / "anchor.patch.md"
    patch.write_text(
        "## The Big One\n\n**ID:** big_one\n\n"
        "**Market probability:** 41%\n\n**Retrieved:** 2026-10-06\n",
        encoding="utf-8",
    )
    entries = parse_event_patch(patch)
    assert entries[0]["updates"]["market_probability"] == "41%"
    updated = apply_event_patches(events, patch)
    assert updated[0].metaculus_probability == "41%"
    assert updated[0].metaculus_retrieved == "2026-10-06"
    assert updated[0].metaculus_url.startswith("https://www.metaculus.com/")
