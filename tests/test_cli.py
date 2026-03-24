"""Tests for CLI module."""

import pytest
import sys
import json
from unittest.mock import patch, MagicMock
from scenario_lab.cli import (
    build_batch_resume_command,
    main,
    run_model_preflight_checks,
    BatchJobResult,
    BatchJobView,
    summarize_batch_activity,
    update_batch_view_from_line,
)
from scenario_lab.model_audit import ModelRecommendation
from scenario_lab.models import LLMConfig


def _write_manifest(path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_cli_missing_args(capsys):
    """Test running CLI without arguments prints usage."""
    with patch("sys.argv", ["scenario_lab"]):
        # If main doesn't exit, it means it didn't find a command. 
        # We just check that it printed usage/help.
        try:
            main()
        except SystemExit:
            pass
        
        captured = capsys.readouterr()
        assert "usage:" in captured.err or "usage:" in captured.out

def test_cli_run_scenario(tmp_path):
    """Test running a scenario via CLI."""
    with patch("scenario_lab.cli.run_simulation") as mock_run:
        with patch("scenario_lab.cli.load_scenario") as mock_load:
            with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                # Setup mock scenario
                mock_scenario = MagicMock()
                mock_scenario.config.name = "Test Scenario"
                mock_load.return_value = mock_scenario
                
                # Setup mock output manager
                mock_output = MockOutputManager.return_value
                mock_output.start_run.return_value = tmp_path / "run_dir"
                
                # Mock LLM client
                with patch("scenario_lab.cli.LLMClient"):
                    # Run CLI
                    scenario_path = str(tmp_path / "scenarios/test-scenario")
                    with patch("sys.argv", ["scenario_lab", "run", scenario_path, "--turns", "5"]):
                        main()
                    
                    # Verify calls
                    mock_load.assert_called_once()
                    mock_run.assert_called_once()
                    _, kwargs = mock_run.call_args
                    assert kwargs["num_turns"] == 5

def test_cli_override_args():
    """Test --override arguments are parsed correctly."""
    with patch("scenario_lab.cli.run_simulation") as mock_run:
        with patch("scenario_lab.cli.load_scenario") as mock_load:
            with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                mock_scenario = MagicMock()
                mock_scenario.config.name = "Test Scenario"
                # Ensure config attributes exist so they can be set
                mock_scenario.config.foo = None 
                mock_scenario.config.baz = None
                mock_load.return_value = mock_scenario
                
                mock_output = MockOutputManager.return_value
                mock_output.start_run.return_value = MagicMock()

                with patch("scenario_lab.cli.LLMClient"):
                    with patch("sys.argv", ["scenario_lab", "run", "path", "--override", "foo=bar", "--override", "baz=qux"]):
                        main()
                    
                    # Check that overrides were applied
                    assert mock_scenario.config.foo == "bar"
                    assert mock_scenario.config.baz == "qux"


def test_cli_run_model_overrides_all_llm_tasks(tmp_path):
    """--model on run should override events/actors/rules/metrics/summary/referee."""
    with patch("scenario_lab.cli.run_simulation"):
        with patch("scenario_lab.cli.load_scenario") as mock_load:
            with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                mock_scenario = MagicMock()
                mock_scenario.config.name = "Test Scenario"
                mock_scenario.config.max_turns = 2
                mock_scenario.config.actor_ids = []
                mock_scenario.config.llm.events = "old"
                mock_scenario.config.llm.actors = "old"
                mock_scenario.config.llm.rules = "old"
                mock_scenario.config.llm.metrics = "old"
                mock_scenario.config.llm.summary = "old"
                mock_scenario.config.llm.referee = "old"
                mock_load.return_value = mock_scenario

                mock_output = MockOutputManager.return_value
                mock_output.start_run.return_value = tmp_path / "run_dir"

                with patch("sys.argv", ["scenario_lab", "run", "path", "--model", "new-model"]):
                    main()

                assert mock_scenario.config.llm.events == "new-model"
                assert mock_scenario.config.llm.actors == "new-model"
                assert mock_scenario.config.llm.rules == "new-model"
                assert mock_scenario.config.llm.metrics == "new-model"
                assert mock_scenario.config.llm.summary == "new-model"
                assert mock_scenario.config.llm.referee == "new-model"


def test_run_model_preflight_checks_applies_recommendations(capsys):
    """Interactive preflight should offer and apply model replacements."""
    scenario = MagicMock()
    scenario.config.name = "Test Scenario"
    scenario.config.llm = LLMConfig(
        events="google/gemini-3-flash-preview",
        actors="google/gemini-3-flash-preview",
        rules="x-ai/grok-4.1-fast",
        metrics="x-ai/grok-4.1-fast",
        summary="x-ai/grok-4.1-fast",
        referee="x-ai/grok-4.1-fast",
    )

    recommendations = [
        ModelRecommendation(
            task="events",
            current_model="google/gemini-3-flash-preview",
            suggested_model="x-ai/grok-4.1-fast",
            reason="stable model",
        )
    ]

    with patch("scenario_lab.cli.collect_model_hygiene_warnings", return_value=["warning"]):
        with patch("scenario_lab.cli.recommend_replacements", return_value=recommendations):
            with patch("scenario_lab.cli.apply_model_recommendations", return_value=1) as mock_apply:
                with patch("scenario_lab.cli.sys.stdin.isatty", return_value=True):
                    with patch("builtins.input", return_value="y"):
                        assert run_model_preflight_checks(scenario) is True

    mock_apply.assert_called_once_with(scenario.config.llm, recommendations)
    captured = capsys.readouterr()
    assert "Model hygiene warnings" in captured.out
    assert "Suggested replacements from OpenRouter" in captured.out


def test_cli_run_skip_model_checks_bypasses_preflight(tmp_path):
    """--skip-model-checks should bypass the default preflight prompt."""
    with patch("scenario_lab.cli.run_model_preflight_checks") as mock_preflight:
        with patch("scenario_lab.cli.run_simulation"):
            with patch("scenario_lab.cli.load_scenario") as mock_load:
                with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                    mock_scenario = MagicMock()
                    mock_scenario.config.name = "Test Scenario"
                    mock_load.return_value = mock_scenario

                    mock_output = MockOutputManager.return_value
                    mock_output.start_run.return_value = tmp_path / "run_dir"

                    with patch("sys.argv", ["scenario_lab", "run", "path", "--skip-model-checks"]):
                        main()

    mock_preflight.assert_not_called()


def test_summarize_batch_activity_uses_short_aliases():
    """Known step labels should map to short, stable batch activity text."""
    assert summarize_batch_activity("Updating historical summary") == "Writing history"
    assert summarize_batch_activity("Updating metrics and narrative") == "Updating metrics"
    assert summarize_batch_activity("Updating metric rules") == "Adjusting rules"
    assert summarize_batch_activity("Validating constitutional constraints") == "Validating contraints"


def test_update_batch_view_from_line_shortens_step_activity():
    """Batch view should use the short aliases for step lines."""
    view = BatchJobView(label="test")

    update_batch_view_from_line(view, "[6/6] Updating historical summary...")
    assert view.activity == "Writing history"

    update_batch_view_from_line(view, "[4/6] Updating metrics and narrative...")
    assert view.activity == "Updating metrics"


def test_update_batch_view_from_line_tracks_run_directory():
    """Batch view should keep the created run directory visible in the table."""
    view = BatchJobView(label="test")

    update_batch_view_from_line(view, "Output directory: run-20260304-134833-03")
    assert view.run_dir == "run-20260304-134833-03"
    assert view.activity == "Run dir ready"

    update_batch_view_from_line(
        view,
        "Results saved to: /tmp/scenario/runs/run-20260304-134833-03",
    )
    assert view.run_dir == "run-20260304-134833-03"
    assert view.activity == "Saved results"


def test_update_batch_view_from_line_normalizes_completion_text():
    """Batch view should use one stable completion label for passthrough lines."""
    view = BatchJobView(label="test")

    update_batch_view_from_line(view, "  ✓ complete")
    assert view.activity == "Done"

    update_batch_view_from_line(view, "  → completed")
    assert view.activity == "Done"


def test_build_batch_resume_command_uses_no_progress(tmp_path):
    """batch-resume child commands should use the same plain-text mode as batch-run."""
    run_dir = tmp_path / "runs" / "run-123"
    args = MagicMock(turns=10, model=None, from_turn=None, override=None)

    command = build_batch_resume_command(run_dir, args)

    assert "--no-progress" in command


def test_cli_compare_runs_fail_on_diff_returns_error(tmp_path):
    """compare-runs should support CI-style failure when differences are present."""
    baseline_run = tmp_path / "runs" / "run-a"
    candidate_run = tmp_path / "runs" / "run-b"
    baseline_run.mkdir(parents=True)
    candidate_run.mkdir(parents=True)

    with patch("scenario_lab.regression.compare_runs", return_value={"has_differences": True}):
        with patch("scenario_lab.regression.format_run_comparison", return_value="diff report"):
            with patch(
                "sys.argv",
                [
                    "scenario_lab",
                    "compare-runs",
                    str(baseline_run),
                    str(candidate_run),
                    "--fail-on-diff",
                ],
            ):
                result = main()

    assert result == 1


def test_cli_check_regressions_fail_on_diff_returns_error(tmp_path):
    """check-regressions should fail when the suite reports differences."""
    manifest = tmp_path / "regressions.yaml"
    manifest.write_text("comparisons: []", encoding="utf-8")

    with patch(
        "scenario_lab.regression.run_regression_suite",
        return_value={"has_differences": True, "has_errors": False},
    ):
        with patch("scenario_lab.regression.format_regression_suite", return_value="suite report"):
            with patch(
                "sys.argv",
                [
                    "scenario_lab",
                    "check-regressions",
                    str(manifest),
                    "--fail-on-diff",
                ],
            ):
                result = main()

    assert result == 1


def test_cli_check_regressions_accepts_scenario_directory(tmp_path):
    """check-regressions should autodiscover pairwise manifests from a scenario directory."""
    scenario_dir = tmp_path / "scenario"
    regressions_dir = scenario_dir / "regressions"
    _write_manifest(
        regressions_dir / "pairwise.yaml",
        "\n".join(
            [
                "comparisons:",
                "  - label: pair",
                "    baseline: ../runs/run-a",
                "    candidate: ../runs/run-b",
            ]
        ),
    )
    _write_manifest(
        regressions_dir / "distribution.yaml",
        "\n".join(
            [
                "comparisons:",
                "  - label: dist",
                "    baseline:",
                "      runs:",
                "        - ../runs/run-a",
                "    candidate:",
                "      runs:",
                "        - ../runs/run-b",
            ]
        ),
    )

    with patch("scenario_lab.regression.run_regression_suite", return_value={"has_differences": False, "has_errors": False}) as mock_run:
        with patch("scenario_lab.regression.format_regression_suite", return_value="suite report"):
            with patch("sys.argv", ["scenario_lab", "check-regressions", str(scenario_dir)]):
                result = main()

    assert result == 0
    assert mock_run.call_count == 1
    assert mock_run.call_args.args[0] == regressions_dir / "pairwise.yaml"


def test_cli_check_run_integrity_returns_error_for_invalid_run(tmp_path):
    """check-run-integrity should return non-zero for invalid runs."""
    run_dir = tmp_path / "runs" / "run-bad"
    run_dir.mkdir(parents=True)

    with patch(
        "scenario_lab.regression.check_run_integrity",
        return_value={"is_valid": False, "run_name": "run-bad", "errors": ["bad"], "warnings": []},
    ):
        with patch("scenario_lab.regression.format_run_integrity", return_value="integrity report"):
            with patch("sys.argv", ["scenario_lab", "check-run-integrity", str(run_dir)]):
                result = main()

    assert result == 1


def test_cli_compare_distributions_returns_error_when_suite_has_errors(tmp_path):
    """compare-distributions should return non-zero when a comparison errors."""
    manifest = tmp_path / "distribution.yaml"
    manifest.write_text("comparisons: []", encoding="utf-8")

    with patch(
        "scenario_lab.regression.compare_distributions",
        return_value={"comparison_count": 1, "error_count": 1},
    ):
        with patch(
            "scenario_lab.regression.format_distribution_comparison",
            return_value="distribution report",
        ):
            with patch(
                "sys.argv",
                [
                    "scenario_lab",
                    "compare-distributions",
                    str(manifest),
                ],
            ):
                result = main()

    assert result == 1


def test_cli_compare_distributions_accepts_scenario_directory(tmp_path):
    """compare-distributions should autodiscover distribution manifests from a scenario directory."""
    scenario_dir = tmp_path / "scenario"
    regressions_dir = scenario_dir / "regressions"
    _write_manifest(
        regressions_dir / "pairwise.yaml",
        "\n".join(
            [
                "comparisons:",
                "  - label: pair",
                "    baseline: ../runs/run-a",
                "    candidate: ../runs/run-b",
            ]
        ),
    )
    _write_manifest(
        regressions_dir / "distribution.yaml",
        "\n".join(
            [
                "comparisons:",
                "  - label: dist",
                "    baseline:",
                "      runs:",
                "        - ../runs/run-a",
                "    candidate:",
                "      runs:",
                "        - ../runs/run-b",
            ]
        ),
    )

    with patch(
        "scenario_lab.regression.compare_distributions",
        return_value={"comparison_count": 1, "error_count": 0},
    ) as mock_compare:
        with patch(
            "scenario_lab.regression.format_distribution_comparison",
            return_value="distribution report",
        ):
            with patch("sys.argv", ["scenario_lab", "compare-distributions", str(scenario_dir)]):
                result = main()

    assert result == 0
    assert mock_compare.call_count == 1
    assert mock_compare.call_args.args[0] == regressions_dir / "distribution.yaml"


def test_cli_resume_no_additional_turns_skips_simulation(tmp_path):
    """Resume should finalize immediately when start_turn is beyond requested turns."""
    run_dir = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"status": "completed"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "model-e"
    mock_scenario.config.llm.actors = "model-a"
    mock_scenario.config.llm.rules = "model-r"
    mock_scenario.config.llm.metrics = "model-m"
    mock_scenario.config.llm.summary = "model-s"
    mock_scenario.config.llm.referee = "model-ref"

    with patch("scenario_lab.resume.validate_run_directory", return_value=(True, [])):
        with patch("scenario_lab.resume.detect_last_turn", return_value=2):
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                    with patch("scenario_lab.cli.run_simulation") as mock_run:
                        with patch("sys.argv", ["scenario_lab", "resume", str(run_dir), "--turns", "2"]):
                            main()

                        mock_run.assert_not_called()
                        MockOutputManager.return_value.finalize_summary.assert_called_once_with([])


def test_cli_resume_model_overrides_all_llm_tasks(tmp_path):
    """--model on resume should override all task models including summary/referee."""
    run_dir = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"status": "completed"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "old"
    mock_scenario.config.llm.actors = "old"
    mock_scenario.config.llm.rules = "old"
    mock_scenario.config.llm.metrics = "old"
    mock_scenario.config.llm.summary = "old"
    mock_scenario.config.llm.referee = "old"

    with patch("scenario_lab.resume.validate_run_directory", return_value=(True, [])):
        with patch("scenario_lab.resume.detect_last_turn", return_value=2):
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.cli.OutputManager"):
                    with patch("scenario_lab.cli.run_simulation"):
                        with patch("sys.argv", ["scenario_lab", "resume", str(run_dir), "--turns", "2", "--model", "new-model"]):
                            main()

    assert mock_scenario.config.llm.events == "new-model"
    assert mock_scenario.config.llm.actors == "new-model"
    assert mock_scenario.config.llm.rules == "new-model"
    assert mock_scenario.config.llm.metrics == "new-model"
    assert mock_scenario.config.llm.summary == "new-model"
    assert mock_scenario.config.llm.referee == "new-model"


def test_cli_branch_no_additional_turns_skips_simulation(tmp_path):
    """Branch should finalize immediately when no turns remain after branch point."""
    parent_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-parent"
    parent_run.mkdir(parents=True)
    new_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-new"
    new_run.mkdir(parents=True)
    (new_run / "summary.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "model-e"
    mock_scenario.config.llm.actors = "model-a"
    mock_scenario.config.llm.rules = "model-r"
    mock_scenario.config.llm.metrics = "model-m"
    mock_scenario.config.llm.summary = "model-s"
    mock_scenario.config.llm.referee = "model-ref"
    mock_scenario.metrics.metrics = {}

    with patch("scenario_lab.resume.get_scenario_path_from_run", return_value=tmp_path / "scenarios" / "test-scenario"):
        with patch("scenario_lab.resume.create_branch", return_value=new_run):
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.resume.persist_scenario_state_at_turn") as mock_persist:
                    with patch("scenario_lab.resume.sync_summary_turn_state") as mock_sync:
                        with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                            with patch("scenario_lab.cli.run_simulation") as mock_run:
                                with patch("sys.argv", ["scenario_lab", "branch", str(parent_run), "--from-turn", "2", "--turns", "2"]):
                                    main()

                                mock_persist.assert_called_once()
                                mock_sync.assert_called_once()
                                mock_run.assert_not_called()
                                MockOutputManager.return_value.finalize_summary.assert_called_once_with([])


def test_cli_branch_model_sets_full_config_overrides(tmp_path):
    """--model on branch should include summary/referee config overrides."""
    parent_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-parent"
    parent_run.mkdir(parents=True)
    new_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-new"
    new_run.mkdir(parents=True)
    (new_run / "summary.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "old"
    mock_scenario.config.llm.actors = "old"
    mock_scenario.config.llm.rules = "old"
    mock_scenario.config.llm.metrics = "old"
    mock_scenario.config.llm.summary = "old"
    mock_scenario.config.llm.referee = "old"
    mock_scenario.metrics.metrics = {}

    with patch("scenario_lab.resume.get_scenario_path_from_run", return_value=tmp_path / "scenarios" / "test-scenario"):
        with patch("scenario_lab.resume.create_branch", return_value=new_run) as mock_create_branch:
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.resume.persist_scenario_state_at_turn"):
                    with patch("scenario_lab.resume.sync_summary_turn_state"):
                        with patch("scenario_lab.cli.OutputManager"):
                            with patch("scenario_lab.cli.run_simulation"):
                                with patch("sys.argv", ["scenario_lab", "branch", str(parent_run), "--from-turn", "2", "--turns", "2", "--model", "new-model"]):
                                    main()

    _, kwargs = mock_create_branch.call_args
    overrides = kwargs["config_overrides"]
    assert overrides["llm.events"] == "new-model"
    assert overrides["llm.actors"] == "new-model"
    assert overrides["llm.rules"] == "new-model"
    assert overrides["llm.metrics"] == "new-model"
    assert overrides["llm.summary"] == "new-model"
    assert overrides["llm.referee"] == "new-model"


def test_cli_estimate_model_overrides_all_llm_tasks():
    """--model on estimate should override all task models including summary/referee."""
    mock_scenario = MagicMock()
    mock_scenario.config.name = "Test Scenario"
    mock_scenario.config.max_turns = 2
    mock_scenario.config.llm.events = "old"
    mock_scenario.config.llm.actors = "old"
    mock_scenario.config.llm.rules = "old"
    mock_scenario.config.llm.metrics = "old"
    mock_scenario.config.llm.summary = "old"
    mock_scenario.config.llm.referee = "old"

    with patch("scenario_lab.cli.load_scenario", return_value=mock_scenario):
        with patch("scenario_lab.estimator.CostEstimator") as MockEstimator:
            with patch("scenario_lab.estimator.format_estimate_report", return_value="report"):
                with patch("sys.argv", ["scenario_lab", "estimate", "path", "--model", "new-model"]):
                    main()

    assert mock_scenario.config.llm.events == "new-model"
    assert mock_scenario.config.llm.actors == "new-model"
    assert mock_scenario.config.llm.rules == "new-model"
    assert mock_scenario.config.llm.metrics == "new-model"
    assert mock_scenario.config.llm.summary == "new-model"
    assert mock_scenario.config.llm.referee == "new-model"


def test_cli_calibrate_runs_analysis_without_api_calls(tmp_path):
    """calibrate command should run local analysis and print report."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    run_dir = scenario_dir / "runs" / "run-20250101-000001"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "scenario": "Test",
                "total_turns": 1,
                "final_metrics": {"m1": 10},
                "history": [{"turn": 1, "metrics": {"m1": 10}}],
                "occurred_events": [],
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )
    turn_dir = run_dir / "turn-01"
    turn_dir.mkdir()
    (turn_dir / "1-events.json").write_text(
        json.dumps([{"id": "e1", "probability": 0.1}]), encoding="utf-8"
    )

    with patch("sys.argv", ["scenario_lab", "calibrate", str(scenario_dir)]):
        main()


def test_cli_audit_models_reports_project_warnings(tmp_path, capsys):
    """audit-models should scan scenario configs and report model hygiene warnings."""
    scenario_dir = tmp_path / "scenarios" / "demo"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "scenario.yaml").write_text(
        "\n".join(
            [
                "name: Demo",
                "description: Demo scenario",
                "start_date: '2026-01'",
                "time_scale: '6 months'",
                "max_turns: 3",
                "actors: ['government']",
                "llm:",
                "  events: x-ai/grok-4.1-fast",
                "  actors: openai/gpt-3.5-turbo-2024-01-15",
                "  rules: x-ai/grok-4.1-fast",
                "  metrics: x-ai/grok-4.1-fast",
                "  summary: x-ai/grok-4.1-fast",
                "  referee: x-ai/grok-4.1-fast",
            ]
        ),
        encoding="utf-8",
    )

    with patch("sys.argv", ["scenario_lab", "audit-models", str(tmp_path / "scenarios")]):
        main()

    captured = capsys.readouterr()
    assert "MODEL AUDIT" in captured.out
    assert "gpt-3.5-turbo-2024-01-15" in captured.out


def test_cli_batch_run_variants_launches_one_child_per_variant(tmp_path):
    """batch-run should expand variants and launch one child run per YAML file."""
    scenario_dir = tmp_path / "scenario"
    variants_dir = scenario_dir / "variants"
    variants_dir.mkdir(parents=True)
    variant_a = variants_dir / "a.yaml"
    variant_b = variants_dir / "b.yml"
    variant_a.write_text("name: A\n", encoding="utf-8")
    variant_b.write_text("name: B\n", encoding="utf-8")

    captured_specs = []

    def fake_execute(specs, max_concurrency, title):
        captured_specs.extend(specs)
        return (
            [BatchJobResult(target=spec.target, returncode=0, log_path=spec.log_path) for spec in specs],
            [],
        )

    with patch("scenario_lab.cli.execute_batch_specs", side_effect=fake_execute):
        with patch(
            "sys.argv",
            [
                "scenario_lab",
                "batch-run",
                str(scenario_dir),
                "--variants",
                "--max-concurrency",
                "2",
                "--turns",
                "3",
                "--model",
                "test-model",
                "--override",
                "foo=bar",
                "--validate",
                "--repeat",
                "2",
            ],
        ):
            result = main()

    assert result == 0
    assert len(captured_specs) == 4

    command_texts = [" ".join(spec.command) for spec in captured_specs]
    assert sum(str(variant_a) in text for text in command_texts) == 2
    assert sum(str(variant_b) in text for text in command_texts) == 2

    for spec in captured_specs:
        assert spec.command[:5] == [sys.executable, "-u", "-m", "scenario_lab.cli", "run"]
        assert "--skip-model-checks" in spec.command
        assert "--no-progress" in spec.command
        assert "--validate" in spec.command
        assert "--turns" in spec.command
        assert "--model" in spec.command
        assert "--override" in spec.command


def test_cli_batch_run_repeat_reuses_same_target(tmp_path):
    """batch-run --repeat should run the same target multiple times."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    captured_specs = []

    def fake_execute(specs, max_concurrency, title):
        captured_specs.extend(specs)
        return (
            [BatchJobResult(target=spec.target, returncode=0, log_path=spec.log_path) for spec in specs],
            [],
        )

    with patch("scenario_lab.cli.execute_batch_specs", side_effect=fake_execute):
        with patch(
            "sys.argv",
            [
                "scenario_lab",
                "batch-run",
                str(scenario_dir),
                "--repeat",
                "3",
                "--max-concurrency",
                "2",
            ],
        ):
            result = main()

    assert result == 0
    assert len(captured_specs) == 3
    for spec in captured_specs:
        assert spec.command[:5] == [sys.executable, "-u", "-m", "scenario_lab.cli", "run"]
        assert str(scenario_dir) in spec.command


def test_cli_batch_resume_scenario_only_launches_incomplete_runs(tmp_path):
    """batch-resume should discover only incomplete runs under a scenario directory."""
    scenario_dir = tmp_path / "scenario"
    runs_dir = scenario_dir / "runs"
    runs_dir.mkdir(parents=True)

    active_run = runs_dir / "run-20260304-100000"
    done_run = runs_dir / "run-20260304-101000"

    for run_dir, max_turns, status, completed_turns in [
        (active_run, 3, "running", 1),
        (done_run, 1, "completed", 1),
    ]:
        run_dir.mkdir()
        (run_dir / "config.json").write_text(
            json.dumps({"max_turns": max_turns}),
            encoding="utf-8",
        )
        (run_dir / "summary.json").write_text(
            json.dumps({"status": status}),
            encoding="utf-8",
        )
        turn_dir = run_dir / f"turn-{completed_turns:02d}"
        turn_dir.mkdir()
        (turn_dir / "1-events.json").write_text("[]", encoding="utf-8")
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir()
        (actors_dir / "actor.md").write_text("actions", encoding="utf-8")
        (turn_dir / "3-metric-rules.md").write_text("rules", encoding="utf-8")
        (turn_dir / "4-metrics.json").write_text("{}", encoding="utf-8")
        (turn_dir / "4-world-state.md").write_text("world", encoding="utf-8")
        (turn_dir / "5-notepad.md").write_text("notes", encoding="utf-8")

    captured_specs = []

    def fake_execute(specs, max_concurrency, title):
        captured_specs.extend(specs)
        return (
            [BatchJobResult(target=spec.target, returncode=0, log_path=spec.log_path) for spec in specs],
            [],
        )

    with patch("scenario_lab.cli.execute_batch_specs", side_effect=fake_execute):
        with patch(
            "sys.argv",
            [
                "scenario_lab",
                "batch-resume",
                str(scenario_dir),
                "--max-concurrency",
                "2",
                "--turns",
                "5",
                "--model",
                "test-model",
                "--override",
                "foo=bar",
            ],
        ):
            result = main()

    assert result == 0
    assert len(captured_specs) == 1
    spec = captured_specs[0]
    assert spec.command[:5] == [sys.executable, "-u", "-m", "scenario_lab.cli", "resume"]
    assert str(active_run) in spec.command
    assert str(done_run) not in spec.command
    assert "--turns" in spec.command
    assert "--model" in spec.command
    assert "--override" in spec.command
