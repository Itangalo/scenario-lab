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
