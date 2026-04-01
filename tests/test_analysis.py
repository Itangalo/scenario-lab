"""Tests for post-run analysis."""

import json
from pathlib import Path
from unittest.mock import patch

from scenario_lab.analysis import generate_run_analysis, load_run_analysis_bundle
from scenario_lab.cli import main


class FakeLLMResponse:
    """Minimal fake LLM response."""

    def __init__(self, content: str):
        self.content = content
        self.raw_response = {}


class FakeLLMClient:
    """Fake client used to avoid real API calls in analysis tests."""

    response_content = ""
    last_system_prompt = ""
    last_user_prompt = ""
    last_model = None
    last_max_tokens = None

    def __init__(self, api_key=None, model=None, temperature=0.7, max_tokens=2000):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        FakeLLMClient.last_model = model
        FakeLLMClient.last_max_tokens = max_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> FakeLLMResponse:
        FakeLLMClient.last_system_prompt = system_prompt
        FakeLLMClient.last_user_prompt = user_prompt
        return FakeLLMResponse(self.response_content)

    def close(self):
        return None


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_analysis_fixture(tmp_path: Path, *, with_costs: bool = True, with_constitution: bool = True) -> Path:
    """Create a minimal scenario plus completed run for analysis tests."""
    scenario_dir = tmp_path / "scenarios" / "analysis-scenario"
    runs_dir = scenario_dir / "runs"
    run_dir = runs_dir / "run-20260401-120000"
    run_dir.mkdir(parents=True)

    _write(
        scenario_dir / "scenario.yaml",
        """
name: "Analysis Scenario"
description: "Scenario for testing post-run analysis"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 2
actors:
  - government
  - company
llm:
  events: "model-events"
  actors: "model-actors"
  rules: "model-rules"
  metrics: "model-metrics"
  summary: "model-summary"
  analysis: "model-analysis"
  referee: "model-referee"
  max_tokens_by_task:
    analysis: 4321
""".strip()
        + "\n",
    )
    _write(
        scenario_dir / "metrics.md",
        """
# Metrics

## stability
**Description:** Social and institutional stability
**ID:** stability
**Start value:** 70
**Min:** 0
**Max:** 100
**Unit:** points

## growth
**Description:** Economic growth
**ID:** growth
**Start value:** 40
**Min:** 0
**Max:** 100
**Unit:** points
""".strip()
        + "\n",
    )
    _write(
        scenario_dir / "events.md",
        """
# Events

## Protest Wave
**ID:** protest_wave
**Condition:** stability < 60
**Probability:** 0.4
**Can repeat:** No
**Description:** Public protests disrupt the political agenda.

## Investment Boom
**ID:** investment_boom
**Condition:** growth > 45
**Probability:** 0.5
**Can repeat:** Yes
**Description:** Private investment accelerates.
""".strip()
        + "\n",
    )
    _write(
        scenario_dir / "metric-rules.md",
        """
# Metric Rules v0

1. Growth usually improves when private investment increases.
2. Stability falls when public trust erodes.
""".strip()
        + "\n",
    )
    if with_constitution:
        _write(
            scenario_dir / "constitution.md",
            """
# Constitution

1. Public spending changes must remain gradual.
2. Institutions cannot double their capacity in a single turn.
""".strip()
            + "\n",
        )

    _write(scenario_dir / "background" / "context.md", "Initial background context.\n")
    _write(
        scenario_dir / "background" / "actors" / "government.md",
        """
# Government
## Short description
Sets policy and responds to crises.
## Long description
The government tries to preserve stability while supporting growth.
""".strip()
        + "\n",
    )
    _write(
        scenario_dir / "background" / "actors" / "company.md",
        """
# Company
## Short description
Large domestic AI company.
## Long description
The company pushes for deregulation and investment.
""".strip()
        + "\n",
    )

    _write(
        run_dir / "config.json",
        json.dumps(
            {
                "name": "Analysis Scenario",
                "description": "Scenario for testing post-run analysis",
                "start_date": "2026-01",
                "time_scale": "6 months per turn",
                "max_turns": 2,
                "actors": ["government", "company"],
            },
            indent=2,
        )
        + "\n",
    )
    _write(
        run_dir / "summary.json",
        json.dumps(
            {
                "scenario": "Analysis Scenario",
                "status": "completed",
                "total_turns": 2,
                "final_metrics": {"stability": 58, "growth": 63},
                "history": [
                    {"turn": 1, "metrics": {"stability": 66, "growth": 48}},
                    {"turn": 2, "metrics": {"stability": 58, "growth": 63}},
                ],
                "occurred_events": ["investment_boom", "protest_wave"],
            },
            indent=2,
        )
        + "\n",
    )
    if with_costs:
        _write(
            run_dir / "costs.json",
            json.dumps({"total_cost_usd": 1.23, "total_tokens": 4567}, indent=2) + "\n",
        )

    _write(run_dir / "turn-01" / "1-events.json", '[{"id": "investment_boom"}]\n')
    _write(run_dir / "turn-01" / "2-actors" / "government.md", "Government expands subsidies.\n")
    _write(run_dir / "turn-01" / "2-actors" / "company.md", "Company announces hiring and investment.\n")
    _write(run_dir / "turn-01" / "3-metric-rules.md", "# Metric Rules v1\n\nGrowth momentum strengthens.\n")
    _write(
        run_dir / "turn-01" / "3-metric-rules-metadata.json",
        json.dumps({"version": 1, "changelog_entries": ["Adjusted growth momentum"]}, indent=2) + "\n",
    )
    _write(run_dir / "turn-01" / "4-world-state.md", "Growth accelerates and optimism increases.\n")
    _write(
        run_dir / "turn-01" / "4-metrics.json",
        json.dumps({"stability": 66, "growth": 48}, indent=2) + "\n",
    )
    _write(run_dir / "turn-01" / "5-notepad.md", "Turn 1 note.\n")

    _write(run_dir / "turn-02" / "1-events.json", '[{"id": "protest_wave"}]\n')
    _write(run_dir / "turn-02" / "2-actors" / "government.md", "Government imposes emergency controls.\n")
    _write(run_dir / "turn-02" / "2-actors" / "company.md", "Company lobbies against the new controls.\n")
    _write(run_dir / "turn-02" / "3-metric-rules.md", "# Metric Rules v2\n\nSocial backlash now drags on stability.\n")
    _write(
        run_dir / "turn-02" / "3-metric-rules-metadata.json",
        json.dumps({"version": 2, "changelog_entries": ["Added backlash rule"]}, indent=2) + "\n",
    )
    _write(run_dir / "turn-02" / "4-world-state.md", "Street protests force the government into reactive measures.\n")
    _write(
        run_dir / "turn-02" / "4-metrics.json",
        json.dumps({"stability": 58, "growth": 63}, indent=2) + "\n",
    )
    _write(
        run_dir / "turn-02" / "5-constitutional-check.json",
        json.dumps({"status": "approved", "violations_found": []}, indent=2) + "\n",
    )
    _write(run_dir / "turn-02" / "5-notepad.md", "Turn 2 note.\n")
    _write(run_dir / "turn-02" / "6-historical-summary.md", "Turn 1 established faster growth.\n")

    return run_dir


def test_load_run_analysis_bundle_reads_turns_and_optional_metadata(tmp_path):
    """Analysis loading should include scenario context, turns, costs, and deltas."""
    run_dir = create_analysis_fixture(tmp_path)

    bundle = load_run_analysis_bundle(run_dir)

    assert bundle.scenario.config.name == "Analysis Scenario"
    assert bundle.costs == {"total_cost_usd": 1.23, "total_tokens": 4567}
    assert len(bundle.turns) == 2
    assert bundle.turns[1].constitutional_check["status"] == "approved"
    assert bundle.metric_overview[0]["metric_id"] == "stability"
    assert bundle.metric_overview[0]["start_value"] == 70
    assert bundle.metric_overview[0]["end_value"] == 58


def test_generate_run_analysis_markdown_saves_default_report(tmp_path):
    """Markdown analysis should be saved to analysis.md by default."""
    run_dir = create_analysis_fixture(tmp_path)
    FakeLLMClient.response_content = """
## Summary
The run ends with higher growth but lower stability after a protest wave shifts the trajectory.

## Key Metrics Overview
| Metric | Start | End | Direction | Delta |
| --- | --- | --- | --- | --- |
| stability | 70 | 58 | down | -12 |
| growth | 40 | 63 | up | +23 |

## Turning Points
1. Turn 2 becomes the decisive inflection point.

## Event Analysis
Triggered events were consequential.

## Actor Behavior Patterns
Government became reactive while the company stayed expansionary.

## Rule Evolution
Rules shifted toward social backlash effects.

## Constitutional Interventions
No referee correction was needed.

## Observations and Caveats
- Stability fell quickly.
""".strip()

    with patch("scenario_lab.analysis.LLMClient", FakeLLMClient):
        result = generate_run_analysis(run_dir)

    saved_path = run_dir / "analysis.md"
    assert result.output_path == saved_path
    assert saved_path.exists()
    assert "higher growth but lower stability" in saved_path.read_text(encoding="utf-8")
    assert result.summary_text.startswith("The run ends with higher growth")
    assert FakeLLMClient.last_model == "model-analysis"
    assert FakeLLMClient.last_max_tokens == 4321
    assert "## Metric Overview" in FakeLLMClient.last_user_prompt


def test_generate_run_analysis_json_no_save_handles_missing_optional_files(tmp_path):
    """JSON analysis should work without costs or constitution and skip saving when requested."""
    run_dir = create_analysis_fixture(tmp_path, with_costs=False, with_constitution=False)
    FakeLLMClient.response_content = json.dumps(
        {
            "summary": "Growth rises, but protests reduce stability.",
            "key_metrics_overview": [],
            "turning_points": [],
            "event_analysis": {
                "triggered_events": [],
                "not_triggered_events": [],
                "impact_assessment": "Mixed.",
            },
            "actor_behavior_patterns": [],
            "rule_evolution": "Rules hardened after protests.",
            "constitutional_interventions": None,
            "observations_and_caveats": ["No constitution was defined."],
        }
    )

    with patch("scenario_lab.analysis.LLMClient", FakeLLMClient):
        result = generate_run_analysis(run_dir, json_output=True, no_save=True)

    assert result.output_path is None
    assert not (run_dir / "analysis.json").exists()
    parsed = json.loads(result.report)
    assert parsed["summary"] == "Growth rises, but protests reduce stability."


def test_cli_analyze_invokes_pipeline_and_writes_custom_output(tmp_path, capsys):
    """CLI analyze should generate a report and print the summary."""
    run_dir = create_analysis_fixture(tmp_path)
    custom_output = tmp_path / "reports" / "analysis-output.md"
    FakeLLMClient.response_content = """
## Summary
The decisive shift came in turn 2 when protests undercut stability.

## Key Metrics Overview
| Metric | Start | End | Direction | Delta |
| --- | --- | --- | --- | --- |
| stability | 70 | 58 | down | -12 |

## Turning Points
1. Turn 2.

## Event Analysis
The protest wave mattered most.

## Actor Behavior Patterns
Government turned reactive.

## Rule Evolution
Rules became more pessimistic.

## Constitutional Interventions
None.

## Observations and Caveats
- Calibration may be aggressive.
""".strip()

    with patch("scenario_lab.analysis.LLMClient", FakeLLMClient):
        with patch("sys.argv", ["scenario_lab", "analyze", str(run_dir), "--output", str(custom_output)]):
            assert main() == 0

    captured = capsys.readouterr()
    assert "Analysis saved to:" in captured.out
    assert "The decisive shift came in turn 2" in captured.out
    assert custom_output.exists()
