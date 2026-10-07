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
    assert event.market_url == "https://www.metaculus.com/questions/12345/big-event/"
    assert event.market_retrieved == "2026-10-01"
    assert event.market_probability == "34%"


def test_anchor_absent_by_default():
    events = load_events(REPO_ROOT / "scenarios/sweden-ai-2030/events.md")
    assert events
    assert all(
        not e.market_url and not e.market_retrieved and not e.market_probability
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
    assert updated[0].market_probability == "41%"
    assert updated[0].market_retrieved == "2026-10-06"
    assert updated[0].market_url.startswith("https://www.metaculus.com/")


def test_market_check_compares_turn_1_pricing(tmp_path):
    """Turn-1 evaluated probabilities sit beside the snapshotted figures."""
    import json as _json

    from scenario_lab.market_check import format_market_check, market_check

    scenario_dir = tmp_path / "case"
    (scenario_dir / "runs").mkdir(parents=True)
    import shutil as _shutil

    _shutil.copytree(
        REPO_ROOT / "scenarios/sweden-ai-2030", scenario_dir,
        ignore=_shutil.ignore_patterns("runs"),
        dirs_exist_ok=True,
    )
    anchor = (
        "\n**Metaculus:** https://www.metaculus.com/questions/99999/x/\n\n"
        "**Retrieved:** 2026-10-01\n\n**Market probability:** 30%\n"
    )
    events_text = (scenario_dir / "events.md").read_text(encoding="utf-8")
    assert "## AI Development Plateaus" in events_text
    (scenario_dir / "events.md").write_text(
        events_text.replace("## AI Development Plateaus", anchor + "\n## AI Development Plateaus"),
        encoding="utf-8",
    )
    run_dir = scenario_dir / "runs" / "run-20261006-000000"
    turn_dir = run_dir / "turn-01"
    turn_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(
        _json.dumps({"scenario_source": str(scenario_dir / "scenario.yaml")})
    )
    (turn_dir / "1-event-evaluations.json").write_text(
        _json.dumps(
            [
                {"id": "ai_breakthrough", "probability": 0.1, "roll": 0.5,
                 "triggered": False},
                {"id": "ghost", "probability": 0.2, "roll": 0.1,
                 "triggered": True},
            ]
        )
    )

    report = market_check(run_dir)
    assert len(report["comparisons"]) == 1
    entry = report["comparisons"][0]
    assert entry["id"] == "ai_breakthrough"
    assert entry["market"] == 0.30
    assert entry["gm_turn_1"] == 0.10
    assert entry["gap"] == round(0.10 - 0.30, 4)
    text = format_market_check(report)
    assert "ai_breakthrough" in text and "30%" in text
