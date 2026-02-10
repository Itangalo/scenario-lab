"""Test output manager with pytest."""

import json
import pytest
from pathlib import Path
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.models import TurnResult
from scenario_lab.orchestrator import run_simulation
from scenario_lab.output import OutputManager

@pytest.fixture
def test_scenario():
    return load_scenario("scenarios/sweden-ai-2030")

@pytest.fixture
def mock_llm_client():
    mock_responses = {
        "list of potential external events looks like this": '[{"id": "ai_breakthrough", "probability": 0.15}]',
        "which actions you want to take during the turn": """## Goals

* Increase AI adoption in Sweden
* Ensure workforce transition

## Actions

The government launches a comprehensive AI support program for small and medium-sized enterprises.""",
        "Respond with an updated list of Metric Rules": """1. ai_capability increases by 1 point per 6 months
2. If unemployment > 10, public_sentiment_to_ai decreases by 1
3. If ai_adoption_sweden increases by more than 5 points, unemployment increases by 1""",
        "A JSON object describing all metrics": """## Metrics

```json
{"ai_capability": 6, "ai_adoption_sweden": 48, "unemployment": 7, "public_sentiment_to_ai": 1}
```

## Narrative

Sweden undergoes a period of intense AI adoption following the government's support program. Small and medium-sized enterprises begin implementing AI solutions, driving up adoption rates. At the same time, early signs of concern appear in the labor market as certain routine jobs are automated.

## Notepad

The government's AI support program was launched during this turn. The program is expected to continue for at least 2 turns.""",
        "CURRENT NARRATIVE": "Summary of narrative",
    }
    return MockLLMClient(mock_responses)

def test_output_manager_structure(test_scenario, mock_llm_client, tmp_path):
    """Test that OutputManager creates correct directory structure and files."""
    
    # Create output manager using tmp_path as base
    output = OutputManager(test_scenario, tmp_path)

    # Start run
    run_dir = output.start_run()
    assert run_dir.parent == tmp_path / "runs"
    assert run_dir.exists()

    # Run 2 turns with incremental writing
    results = run_simulation(test_scenario, mock_llm_client, num_turns=2, output_manager=output)

    # Finalize summary
    output.finalize_summary(results)

    # Verify files
    config_file = run_dir / "config.json"
    summary_file = run_dir / "summary.json"
    turn1_dir = run_dir / "turn-01"
    turn2_dir = run_dir / "turn-02"

    assert config_file.exists(), "config.json not found"
    assert summary_file.exists(), "summary.json not found"
    assert turn1_dir.exists(), "turn-01 directory not found"
    assert turn2_dir.exists(), "turn-02 directory not found"

    # Check turn 1 files
    assert (turn1_dir / "1-events.json").exists()
    assert (turn1_dir / "2-actors").exists()
    assert (turn1_dir / "3-metric-rules.md").exists()
    assert (turn1_dir / "4-metrics.json").exists()
    assert (turn1_dir / "4-world-state.md").exists()

    # Verify config content
    config = json.loads(config_file.read_text())
    assert config['name'] == test_scenario.config.name
    
    # Verify summary content
    summary = json.loads(summary_file.read_text())
    assert summary['total_turns'] == 2
    assert summary['status'] == "completed"
    assert 'final_metrics' in summary

def test_crash_preservation(test_scenario, mock_llm_client, tmp_path):
    """Test that data is preserved if simulation crashes (no finalize called)."""
    output = OutputManager(test_scenario, tmp_path)
    run_dir = output.start_run()
    
    # Run just one turn
    run_simulation(test_scenario, mock_llm_client, num_turns=1, output_manager=output)
    
    # Simulate crash by NOT calling finalize_summary
    
    # Verify summary exists and shows running status
    summary_file = run_dir / "summary.json"
    assert summary_file.exists()
    
    summary = json.loads(summary_file.read_text())
    assert summary['status'] == "running"
    assert summary['total_turns'] == 1
    assert 'final_metrics' in summary
    
    # Verify turn 1 files exist
    turn1_dir = run_dir / "turn-01"
    assert turn1_dir.exists()
    assert (turn1_dir / "4-metrics.json").exists()

def test_output_content(test_scenario, mock_llm_client, tmp_path):
    """Test that written files contain correct data."""
    output = OutputManager(test_scenario, tmp_path)
    run_dir = output.start_run()
    
    results = run_simulation(test_scenario, mock_llm_client, num_turns=1, output_manager=output)
    output.finalize_summary(results)
    
    turn1_dir = run_dir / "turn-01"
    
    # Check metrics.json content
    metrics_file = turn1_dir / "4-metrics.json"
    data = json.loads(metrics_file.read_text())
    assert data["ai_capability"] == 6
    assert data["ai_adoption_sweden"] == 48
    
    # Check world-state.md content
    ws_file = turn1_dir / "4-world-state.md"
    content = ws_file.read_text()
    # World state file only saves the narrative part, not the full LLM output
    assert "Sweden undergoes a period" in content

def test_output_write_error(test_scenario, mock_llm_client, tmp_path):
    """Test graceful handling of write errors."""
    output = OutputManager(test_scenario, tmp_path)
    run_dir = output.start_run()
    
    # Make turn directory read-only to force write error
    turn1_dir = run_dir / "turn-01"
    turn1_dir.mkdir()
    turn1_dir.chmod(0o444) # Read-only
    
    try:
        # Should likely raise PermissionError or similar, 
        # or handle it gracefully depending on implementation.
        # If implementation raises, we catch it.
        with pytest.raises(PermissionError):
            run_simulation(test_scenario, mock_llm_client, num_turns=1, output_manager=output)
    finally:
        # Cleanup: restore permissions so pytest can delete tmp_path
        turn1_dir.chmod(0o777)


def test_finalize_summary_preserves_existing_history_for_resume(test_scenario, tmp_path):
    """Finalization must keep prior history when only new turns are provided."""
    output = OutputManager(test_scenario, tmp_path)
    run_dir = output.start_run()

    existing_summary = {
        "scenario": test_scenario.config.name,
        "total_turns": 2,
        "final_metrics": {"ai_capability": 5},
        "history": [
            {"turn": 1, "metrics": {"ai_capability": 4}},
            {"turn": 2, "metrics": {"ai_capability": 5}},
        ],
        "occurred_events": ["event_a"],
        "metadata": {"resumed_from_turn": 2},
        "status": "running",
    }
    (run_dir / "summary.json").write_text(json.dumps(existing_summary), encoding="utf-8")

    test_scenario.occurred_events.add("event_b")

    new_result = TurnResult(
        turn=3,
        time_period="January-June 2027",
        triggered_events=[],
        actor_outputs={},
        metric_rules="rules",
        metrics={"ai_capability": 6},
        narrative="narrative",
        notepad="notepad",
    )

    output.finalize_summary([new_result])

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

    assert summary["total_turns"] == 3
    assert summary["final_metrics"] == {"ai_capability": 6}
    assert [entry["turn"] for entry in summary["history"]] == [1, 2, 3]
    assert set(summary["occurred_events"]) == {"event_a", "event_b"}
    assert summary["metadata"]["resumed_from_turn"] == 2
    assert summary["status"] == "completed"
    assert "completed_at" in summary


def test_finalize_summary_with_no_new_results_keeps_existing_history(test_scenario, tmp_path):
    """If no new turns are produced, finalization must not wipe existing summary history."""
    output = OutputManager(test_scenario, tmp_path)
    run_dir = output.start_run()

    existing_summary = {
        "scenario": test_scenario.config.name,
        "total_turns": 2,
        "final_metrics": {"ai_capability": 5},
        "history": [
            {"turn": 1, "metrics": {"ai_capability": 4}},
            {"turn": 2, "metrics": {"ai_capability": 5}},
        ],
        "occurred_events": [],
        "status": "running",
    }
    (run_dir / "summary.json").write_text(json.dumps(existing_summary), encoding="utf-8")

    output.finalize_summary([])

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["total_turns"] == 2
    assert summary["final_metrics"] == {"ai_capability": 5}
    assert [entry["turn"] for entry in summary["history"]] == [1, 2]
    assert summary["status"] == "completed"
