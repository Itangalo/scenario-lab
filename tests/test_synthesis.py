"""Tests for cross-run synthesis and declared research questions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scenario_lab.loader import load_scenario, parse_research_questions
from scenario_lab.synthesis import (
    _build_synthesis_context,
    _condense_ensemble,
    AnalysisCoverage,
    RunAnalysisEntry,
    ensure_run_analyses,
    read_cached_analysis,
    synthesize_scenario,
)
from scenario_lab.validator import validate_research_questions


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write_scenario(tmp_path: Path, research_questions: list | None = None) -> Path:
    """Create a minimal but loadable scenario directory."""
    scenario_dir = tmp_path / "test-scenario"
    scenario_dir.mkdir()

    (scenario_dir / "metrics.md").write_text(
        "## trust\n"
        "**Description:** Public trust\n"
        "**ID:** trust\n"
        "**Min:** 0\n"
        "**Max:** 100\n"
        "**Unit:** index\n"
        "**Start value:** 50\n",
        encoding="utf-8",
    )
    (scenario_dir / "events.md").write_text(
        "## Scandal\n"
        "**ID:** scandal\n"
        "**Condition:** Trust is falling\n"
        "**Probability:** 10%\n"
        "**Can repeat:** No\n"
        "**Description:** A scandal breaks.\n",
        encoding="utf-8",
    )
    (scenario_dir / "metric-rules.md").write_text("1. Scandals reduce trust by 10.\n", encoding="utf-8")

    background = scenario_dir / "background"
    (background / "actors").mkdir(parents=True)
    (background / "context.md").write_text("A small world.\n", encoding="utf-8")
    (background / "actors" / "regulator.md").write_text(
        "# Regulator\n\n"
        "## Short description\nThe regulator.\n\n"
        "## Long description\nRegulates things.\n\n"
        "### Statements\n- `keep_trust` (position): Keep trust high\n\n"
        "### Behavioral traits\n- Cautious\n",
        encoding="utf-8",
    )

    config: dict = {
        "name": "Test Scenario",
        "description": "A test scenario",
        "start_date": "2026-01",
        "time_scale": "1 month per turn",
        "max_turns": 3,
        "actors": ["regulator"],
    }
    if research_questions is not None:
        config["research_questions"] = research_questions
    (scenario_dir / "scenario.yaml").write_text(yaml.dump(config), encoding="utf-8")

    return scenario_dir


def _write_run(scenario_dir: Path, name: str, analysis: dict | None = None) -> Path:
    """Write a completed run, optionally with a cached structured analysis."""
    run_dir = scenario_dir / "runs" / name
    run_dir.mkdir(parents=True)

    history = [{"turn": 1, "metrics": {"trust": 45.0}}, {"turn": 2, "metrics": {"trust": 40.0}}]
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "scenario": "Test Scenario",
                "total_turns": 2,
                "final_metrics": {"trust": 40.0},
                "history": history,
                "occurred_events": ["scandal"],
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "config.json").write_text(
        json.dumps({"name": "Test Scenario", "llm": {"events": "openrouter:model-a"}}),
        encoding="utf-8",
    )

    for turn, entry in enumerate(history, start=1):
        turn_dir = run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir()
        (turn_dir / "1-events.json").write_text(json.dumps([]), encoding="utf-8")
        (turn_dir / "4-metrics.json").write_text(json.dumps(entry["metrics"]), encoding="utf-8")

    if analysis is not None:
        (run_dir / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")

    return run_dir


def _analysis(summary: str = "Trust fell after a scandal.") -> dict:
    return {
        "summary": summary,
        "turning_points": [{"turn": 1, "description": "Scandal broke"}],
        "event_analysis": {"triggered_events": ["scandal"]},
        "actor_behavior_patterns": [{"actor_id": "regulator", "analysis": "Reacted late."}],
        "observations_and_caveats": ["Only two turns."],
    }


# ---------------------------------------------------------------------------
# Research question parsing
# ---------------------------------------------------------------------------

def test_parse_research_questions_accepts_bare_strings():
    questions = parse_research_questions(["Does trust recover after a scandal?"])

    assert len(questions) == 1
    assert questions[0].question == "Does trust recover after a scandal?"
    assert questions[0].id  # derived from the text
    assert questions[0].metrics == []


def test_parse_research_questions_accepts_mappings():
    questions = parse_research_questions(
        [
            {
                "id": "rq_trust",
                "question": "Does trust recover?",
                "metrics": ["trust"],
                "events": ["scandal"],
                "notes": "Central question.",
            }
        ]
    )

    assert questions[0].id == "rq_trust"
    assert questions[0].metrics == ["trust"]
    assert questions[0].events == ["scandal"]
    assert questions[0].notes == "Central question."


def test_parse_research_questions_accepts_scalar_metric():
    questions = parse_research_questions([{"question": "Q?", "metrics": "trust"}])
    assert questions[0].metrics == ["trust"]


def test_parse_research_questions_rejects_bad_shapes():
    with pytest.raises(ValueError, match="must be a list"):
        parse_research_questions({"question": "Q?"})

    with pytest.raises(ValueError, match="no 'question' text"):
        parse_research_questions([{"id": "rq_1"}])

    with pytest.raises(ValueError, match="must be a string or a list of strings"):
        parse_research_questions([{"question": "Q?", "metrics": [1, 2]}])


def test_research_questions_load_from_yaml(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[{"id": "rq_trust", "question": "Does trust recover?", "metrics": ["trust"]}],
    )
    scenario = load_scenario(scenario_dir)

    assert len(scenario.config.research_questions) == 1
    assert scenario.config.research_questions[0].id == "rq_trust"


def test_research_questions_default_to_empty(tmp_path):
    scenario = load_scenario(_write_scenario(tmp_path))
    assert scenario.config.research_questions == []


def test_research_questions_inherit_from_base(tmp_path):
    base = _write_scenario(
        tmp_path, research_questions=[{"id": "rq_base", "question": "Base Q?", "metrics": ["trust"]}]
    )
    variants = base / "variants"
    variants.mkdir()
    (variants / "v1.yaml").write_text(
        yaml.dump({"base": "../scenario.yaml", "name": "Variant"}), encoding="utf-8"
    )

    scenario = load_scenario(variants / "v1.yaml")
    assert [q.id for q in scenario.config.research_questions] == ["rq_base"]
    assert scenario.config.research_questions[0].metrics == ["trust"]


def test_research_questions_override_base_entirely(tmp_path):
    base = _write_scenario(
        tmp_path, research_questions=[{"id": "rq_base", "question": "Base Q?", "metrics": ["trust"]}]
    )
    variants = base / "variants"
    variants.mkdir()
    (variants / "v2.yaml").write_text(
        yaml.dump(
            {
                "base": "../scenario.yaml",
                "name": "Variant",
                "research_questions": [{"id": "rq_own", "question": "Own Q?", "events": ["scandal"]}],
            }
        ),
        encoding="utf-8",
    )

    scenario = load_scenario(variants / "v2.yaml")
    assert [q.id for q in scenario.config.research_questions] == ["rq_own"]


# ---------------------------------------------------------------------------
# Research question validation
# ---------------------------------------------------------------------------

def test_validate_research_questions_flags_unknown_metric(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[{"id": "rq_bad", "question": "Q?", "metrics": ["unemployment"]}],
    )
    errors, _ = validate_research_questions(load_scenario(scenario_dir))

    assert any("unknown metric 'unemployment'" in e for e in errors)


def test_validate_research_questions_flags_unknown_event(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[{"id": "rq_bad", "question": "Q?", "events": ["war"]}],
    )
    errors, _ = validate_research_questions(load_scenario(scenario_dir))

    assert any("unknown event 'war'" in e for e in errors)


def test_validate_research_questions_flags_duplicate_ids(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[
            {"id": "rq_1", "question": "A?", "metrics": ["trust"]},
            {"id": "rq_1", "question": "B?", "metrics": ["trust"]},
        ],
    )
    errors, _ = validate_research_questions(load_scenario(scenario_dir))

    assert any("Duplicate research question id" in e for e in errors)


def test_validate_research_questions_warns_when_ungrounded(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path, research_questions=[{"id": "rq_vague", "question": "What happens?"}]
    )
    errors, warnings = validate_research_questions(load_scenario(scenario_dir))

    assert errors == []
    assert any("names no metrics or events" in w for w in warnings)


def test_valid_research_questions_pass(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[
            {"id": "rq_trust", "question": "Q?", "metrics": ["trust"], "events": ["scandal"]}
        ],
    )
    errors, warnings = validate_research_questions(load_scenario(scenario_dir))

    assert errors == []
    assert warnings == []


# ---------------------------------------------------------------------------
# Analysis caching
# ---------------------------------------------------------------------------

def test_read_cached_analysis_returns_none_for_missing(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_dir = _write_run(scenario_dir, "run-1")

    assert read_cached_analysis(run_dir) is None


def test_read_cached_analysis_rejects_malformed(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_dir = _write_run(scenario_dir, "run-1")
    (run_dir / "analysis.json").write_text("{not json", encoding="utf-8")

    assert read_cached_analysis(run_dir) is None


def test_read_cached_analysis_rejects_wrong_shape(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_dir = _write_run(scenario_dir, "run-1")
    (run_dir / "analysis.json").write_text(json.dumps({"nope": 1}), encoding="utf-8")

    assert read_cached_analysis(run_dir) is None


def test_ensure_run_analyses_reuses_cached(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_a = _write_run(scenario_dir, "run-1", analysis=_analysis("A"))
    run_b = _write_run(scenario_dir, "run-2", analysis=_analysis("B"))

    with patch("scenario_lab.synthesis.generate_run_analysis") as mock_generate:
        coverage = ensure_run_analyses([run_a, run_b])

    mock_generate.assert_not_called()
    assert coverage.reused == 2
    assert coverage.generated == 0
    assert [e.analysis["summary"] for e in coverage.entries] == ["A", "B"]


def test_ensure_run_analyses_generates_missing(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_a = _write_run(scenario_dir, "run-1", analysis=_analysis("cached"))
    run_b = _write_run(scenario_dir, "run-2")

    def _fake_generate(run_dir, model=None, json_output=False):
        (Path(run_dir) / "analysis.json").write_text(
            json.dumps(_analysis("fresh")), encoding="utf-8"
        )

    with patch("scenario_lab.synthesis.generate_run_analysis", side_effect=_fake_generate) as mock:
        coverage = ensure_run_analyses([run_a, run_b])

    assert mock.call_count == 1
    assert coverage.reused == 1
    assert coverage.generated == 1


def test_ensure_run_analyses_refresh_regenerates_everything(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_a = _write_run(scenario_dir, "run-1", analysis=_analysis("cached"))

    def _fake_generate(run_dir, model=None, json_output=False):
        (Path(run_dir) / "analysis.json").write_text(
            json.dumps(_analysis("fresh")), encoding="utf-8"
        )

    with patch("scenario_lab.synthesis.generate_run_analysis", side_effect=_fake_generate):
        coverage = ensure_run_analyses([run_a], refresh=True)

    assert coverage.generated == 1
    assert coverage.entries[0].analysis["summary"] == "fresh"


def test_ensure_run_analyses_records_failures_without_aborting(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    run_a = _write_run(scenario_dir, "run-1")
    run_b = _write_run(scenario_dir, "run-2")

    def _fake_generate(run_dir, model=None, json_output=False):
        if Path(run_dir).name == "run-1":
            raise RuntimeError("provider exploded")
        (Path(run_dir) / "analysis.json").write_text(
            json.dumps(_analysis("ok")), encoding="utf-8"
        )

    with patch("scenario_lab.synthesis.generate_run_analysis", side_effect=_fake_generate):
        coverage = ensure_run_analyses([run_a, run_b])

    assert len(coverage.failures) == 1
    assert "provider exploded" in coverage.failures[0][1]
    assert coverage.generated == 1


# ---------------------------------------------------------------------------
# Prompt context assembly
# ---------------------------------------------------------------------------

def test_condense_ensemble_trims_trajectories_outside_full_mode():
    ensemble = {
        "metric_trajectories": {"trust": {1: {"mean": 50}, 2: {"mean": 45}, 3: {"mean": 40}}},
        "event_statistics": {"scandal": {"count": 3}},
    }

    assert _condense_ensemble(ensemble, "full") == ensemble

    condensed = _condense_ensemble(ensemble, "condensed")
    assert set(condensed["metric_trajectories"]["trust"].keys()) == {1, 2, 3}
    assert condensed["event_statistics"] == {"scandal": {"count": 3}}


def test_condense_ensemble_keeps_first_middle_last():
    ensemble = {"metric_trajectories": {"trust": {t: {"mean": t} for t in range(1, 11)}}}

    condensed = _condense_ensemble(ensemble, "condensed")
    assert set(condensed["metric_trajectories"]["trust"].keys()) == {1, 6, 10}
    assert "metric_trajectories_note" in condensed


def test_synthesis_context_includes_research_questions(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[{"id": "rq_trust", "question": "Does trust recover?", "metrics": ["trust"]}],
    )
    scenario = load_scenario(scenario_dir)
    coverage = AnalysisCoverage(
        entries=[RunAnalysisEntry(scenario_dir / "runs" / "run-1", _analysis(), reused=True)]
    )

    context = _build_synthesis_context(scenario, {}, coverage, "markdown", "full")

    assert context["research_questions"][0]["id"] == "rq_trust"
    assert "run-1" in context["per_run_analyses_markdown"]
    assert "Trust fell after a scandal." in context["per_run_analyses_markdown"]


def test_synthesis_context_minimal_mode_drops_detail(tmp_path):
    scenario = load_scenario(_write_scenario(tmp_path))
    coverage = AnalysisCoverage(
        entries=[RunAnalysisEntry(Path("runs/run-1"), _analysis(), reused=True)]
    )

    full = _build_synthesis_context(scenario, {}, coverage, "markdown", "full")
    minimal = _build_synthesis_context(scenario, {}, coverage, "markdown", "minimal")

    assert "Reacted late." in full["per_run_analyses_markdown"]
    assert "Reacted late." not in minimal["per_run_analyses_markdown"]
    assert "Trust fell after a scandal." in minimal["per_run_analyses_markdown"]


def test_synthesis_context_lists_excluded_runs(tmp_path):
    scenario = load_scenario(_write_scenario(tmp_path))
    coverage = AnalysisCoverage(
        entries=[RunAnalysisEntry(Path("runs/run-1"), _analysis(), reused=True)],
        failures=[(Path("runs/run-2"), "provider exploded")],
    )

    context = _build_synthesis_context(scenario, {}, coverage, "markdown", "full")

    assert "Runs excluded" in context["per_run_analyses_markdown"]
    assert "run-2" in context["per_run_analyses_markdown"]


# ---------------------------------------------------------------------------
# End-to-end synthesis
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


def test_synthesize_scenario_writes_report(tmp_path):
    scenario_dir = _write_scenario(
        tmp_path,
        research_questions=[{"id": "rq_trust", "question": "Does trust recover?", "metrics": ["trust"]}],
    )
    _write_run(scenario_dir, "run-1", analysis=_analysis("A"))
    _write_run(scenario_dir, "run-2", analysis=_analysis("B"))

    report = "## Summary\n\nTrust fell in both runs.\n\n## Outcome Patterns\n\nOne pattern.\n"

    with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
        mock_router_cls.return_value.complete.return_value = _FakeResponse(report)
        result = synthesize_scenario(scenario_dir)

    assert result.num_runs == 2
    assert result.coverage.reused == 2
    assert result.output_path == scenario_dir / "synthesis.md"
    assert result.output_path.exists()
    assert result.summary_text == "Trust fell in both runs."

    # The declared question must reach the prompt, or synthesis answers nothing
    # in particular.
    _, user_prompt = mock_router_cls.return_value.complete.call_args[0]
    assert "Does trust recover?" in user_prompt
    assert "run-1" in user_prompt


def test_synthesize_scenario_json_output(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    _write_run(scenario_dir, "run-1", analysis=_analysis())

    payload = {"summary": "Trust fell.", "outcome_patterns": []}

    with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
        mock_router_cls.return_value.complete.return_value = _FakeResponse(json.dumps(payload))
        result = synthesize_scenario(scenario_dir, json_output=True)

    assert result.output_path == scenario_dir / "synthesis.json"
    assert json.loads(result.output_path.read_text(encoding="utf-8"))["summary"] == "Trust fell."
    assert result.summary_text == "Trust fell."


def test_synthesize_scenario_no_save(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    _write_run(scenario_dir, "run-1", analysis=_analysis())

    with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
        mock_router_cls.return_value.complete.return_value = _FakeResponse("## Summary\n\nX.\n")
        result = synthesize_scenario(scenario_dir, no_save=True)

    assert result.output_path is None
    assert not (scenario_dir / "synthesis.md").exists()


def test_synthesize_scenario_requires_completed_runs(tmp_path):
    scenario_dir = _write_scenario(tmp_path)

    with pytest.raises(ValueError, match="No completed runs"):
        synthesize_scenario(scenario_dir)


def test_synthesize_scenario_respects_max_runs(tmp_path):
    scenario_dir = _write_scenario(tmp_path)
    _write_run(scenario_dir, "run-1", analysis=_analysis("A"))
    _write_run(scenario_dir, "run-2", analysis=_analysis("B"))
    _write_run(scenario_dir, "run-3", analysis=_analysis("C"))

    with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
        mock_router_cls.return_value.complete.return_value = _FakeResponse("## Summary\n\nX.\n")
        result = synthesize_scenario(scenario_dir, max_runs=2)

    assert result.num_runs == 2
    _, user_prompt = mock_router_cls.return_value.complete.call_args[0]
    assert "run-1" not in user_prompt
    assert "run-3" in user_prompt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_synthesize_dry_run_makes_no_calls(tmp_path, capsys):
    from scenario_lab.cli import main

    scenario_dir = _write_scenario(tmp_path)
    _write_run(scenario_dir, "run-1", analysis=_analysis())
    _write_run(scenario_dir, "run-2")

    with patch("sys.argv", ["scenario_lab", "synthesize", str(scenario_dir), "--dry-run"]):
        with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
            result = main()

    mock_router_cls.assert_not_called()
    captured = capsys.readouterr()
    assert result == 0
    assert "Completed runs: 2" in captured.out
    assert "Cached analyses reusable: 1" in captured.out
    assert "Per-run analyses to generate: 1" in captured.out


def test_cli_synthesize_reports_coverage(tmp_path, capsys):
    from scenario_lab.cli import main

    scenario_dir = _write_scenario(tmp_path)
    _write_run(scenario_dir, "run-1", analysis=_analysis())

    with patch("sys.argv", ["scenario_lab", "synthesize", str(scenario_dir)]):
        with patch("scenario_lab.synthesis.FallbackRouter") as mock_router_cls:
            mock_router_cls.return_value.complete.return_value = _FakeResponse(
                "## Summary\n\nTrust fell.\n"
            )
            result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "Runs synthesized: 1" in captured.out
    assert "Synthesis written to" in captured.out


def test_cli_synthesize_reports_failure(tmp_path, capsys):
    from scenario_lab.cli import main

    scenario_dir = _write_scenario(tmp_path)

    with patch("sys.argv", ["scenario_lab", "synthesize", str(scenario_dir)]):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "Synthesis failed" in captured.out


# ---------------------------------------------------------------------------
# call_timeout_seconds config plumbing
# ---------------------------------------------------------------------------

def test_call_timeout_defaults_and_parses(tmp_path):
    scenario = load_scenario(_write_scenario(tmp_path))
    assert scenario.config.llm.call_timeout_seconds == 300

    custom = tmp_path / "custom"
    custom.mkdir()
    d = _write_scenario(custom)
    cfg = yaml.safe_load((d / "scenario.yaml").read_text())
    cfg["llm"] = {"call_timeout_seconds": 90}
    (d / "scenario.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    assert load_scenario(d).config.llm.call_timeout_seconds == 90


def test_validator_rejects_absurd_call_timeout(tmp_path):
    from scenario_lab.validator import validate_llm_config

    d = _write_scenario(tmp_path)
    scenario = load_scenario(d)

    scenario.config.llm.call_timeout_seconds = 5
    assert any("call_timeout_seconds" in e for e in validate_llm_config(scenario))

    scenario.config.llm.call_timeout_seconds = 99999
    assert any("call_timeout_seconds" in e for e in validate_llm_config(scenario))

    scenario.config.llm.call_timeout_seconds = 300
    assert not any("call_timeout_seconds" in e for e in validate_llm_config(scenario))


def test_registry_forwards_timeout_to_provider():
    from scenario_lab.providers.registry import ProviderRegistry

    registry = ProviderRegistry(call_timeout_seconds=77)
    import os
    from unittest.mock import patch as _patch

    with _patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}):
        provider = registry.get("openrouter")
    assert provider.call_timeout_seconds == 77


# ---------------------------------------------------------------------------
# audit-models catalog checks (withdrawn models, reasoning models)
# ---------------------------------------------------------------------------

_FAKE_CATALOG = [
    {"id": "vendor/instruct-model", "supported_parameters": ["temperature", "max_tokens"]},
    {"id": "vendor/thinking-model", "supported_parameters": ["temperature", "reasoning"]},
]


def _scenario_with_model(tmp_path: Path, model: str) -> Path:
    d = _write_scenario(tmp_path)
    cfg = yaml.safe_load((d / "scenario.yaml").read_text())
    cfg["llm"] = {
        task: model
        for task in ("events", "actors", "rules", "metrics", "summary", "analysis", "referee")
    }
    (d / "scenario.yaml").write_text(yaml.dump(cfg), encoding="utf-8")
    return d


def test_audit_flags_withdrawn_model(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "openrouter:vendor/removed-model")
    findings = audit_catalog_availability(d, catalog=_FAKE_CATALOG)

    assert any("not in the OpenRouter catalog" in f.message for f in findings)


def test_audit_flags_reasoning_model(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "openrouter:vendor/thinking-model")
    findings = audit_catalog_availability(d, catalog=_FAKE_CATALOG)

    assert any("reasoning tokens" in f.message for f in findings)


def test_audit_accepts_instruct_model(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "openrouter:vendor/instruct-model")
    assert audit_catalog_availability(d, catalog=_FAKE_CATALOG) == []


def test_audit_reports_each_model_once_listing_tasks(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "openrouter:vendor/thinking-model")
    findings = audit_catalog_availability(d, catalog=_FAKE_CATALOG)

    assert len(findings) == 1
    assert "events" in findings[0].task and "metrics" in findings[0].task


def test_audit_skips_non_openrouter_providers(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "anthropic:claude-sonnet-4-6")
    assert audit_catalog_availability(d, catalog=_FAKE_CATALOG) == []


def test_audit_degrades_gracefully_without_catalog(tmp_path):
    from scenario_lab.model_audit import audit_catalog_availability

    d = _scenario_with_model(tmp_path, "openrouter:vendor/removed-model")
    assert audit_catalog_availability(d, catalog=[]) == []
