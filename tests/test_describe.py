"""Tests for the describe command (scenario overview)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scenario_lab.describe import describe_scenario, format_describe_report


def test_describe_scenario_structure():
    overview = describe_scenario(Path("scenarios/sweden-ai-2030"))

    assert overview["name"] == "Sweden and AI 2030"
    assert overview["time"]["max_turns"] == 10
    assert len(overview["actors"]) == 4
    assert len(overview["metrics"]) == 4
    assert len(overview["events"]) == 9
    assert overview["constitution"]["present"] is True
    assert overview["metric_rules_count"] > 0
    assert overview["llm"]["probability_samples"] >= 1
    assert overview["runs"]["total"] >= 0

    # Reference points must survive loading (regression for the bolded
    # "- **8:** text" format silently dropping them).
    ai_capability = next(m for m in overview["metrics"] if m["id"] == "ai_capability")
    assert ai_capability["reference_points"] == 4


def test_format_describe_report_sections():
    overview = describe_scenario(Path("scenarios/sweden-ai-2030"))
    report = format_describe_report(overview)

    for section in (
        "# Scenario Overview: Sweden and AI 2030",
        "## Actors (4)",
        "## Metrics (4)",
        "## Events (9)",
        "## World Model",
        "## LLM Configuration",
        "## Files and Runs",
    ):
        assert section in report

    # One-page ambition: compact even for a full scenario.
    assert len(report.splitlines()) < 120


def test_cli_describe_markdown(capsys):
    from scenario_lab.cli import main

    with patch("sys.argv", ["scenario_lab", "describe", "scenarios/sweden-ai-2030"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "# Scenario Overview: Sweden and AI 2030" in captured.out


def test_cli_describe_json(capsys):
    from scenario_lab.cli import main

    with patch(
        "sys.argv", ["scenario_lab", "describe", "scenarios/sweden-ai-2030", "--json"]
    ):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    data = json.loads(captured.out)
    assert data["name"] == "Sweden and AI 2030"


def test_cli_describe_output_file(tmp_path, capsys):
    from scenario_lab.cli import main

    out = tmp_path / "overview.md"
    with patch(
        "sys.argv",
        ["scenario_lab", "describe", "scenarios/sweden-ai-2030", "--output", str(out)],
    ):
        result = main()

    assert result == 0
    assert "Scenario Overview" in out.read_text(encoding="utf-8")


def test_cli_describe_missing_scenario(capsys):
    from scenario_lab.cli import main

    with patch("sys.argv", ["scenario_lab", "describe", "scenarios/does-not-exist"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "Error describing scenario" in captured.out


def test_describe_lists_info_file_sections(tmp_path):
    """describe shows which records have rich descriptions behind info_file."""
    import shutil

    from scenario_lab.describe import describe_scenario

    dest = tmp_path / "case"
    shutil.copytree("scenarios/sweden-ai-2030", dest, ignore=shutil.ignore_patterns("runs"))
    (dest / "background" / "measures-info.md").write_text(
        "# Measures\n\n## Solar build-out\nBig and slow.\n\n## Pilot\nSmall.\n",
        encoding="utf-8",
    )
    scenario_yaml = (dest / "scenario.yaml").read_text(encoding="utf-8")
    (dest / "scenario.yaml").write_text(
        scenario_yaml
        + "\nstore:\n  measures:\n    scope: actor\n"
        "    info_file: background/measures-info.md\n"
        "    columns:\n      id: {owner: system, type: text}\n"
        "      name: {owner: actor, type: text, required: true}\n",
        encoding="utf-8",
    )

    overview = describe_scenario(dest)
    table = overview["store"]["measures"]
    assert table["info_file"] == "background/measures-info.md"
    assert table["info_sections"] == ["Solar build-out", "Pilot"]
