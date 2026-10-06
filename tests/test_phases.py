"""Per-phase persistence and mid-turn resume (v5 three-phase cycle)."""

import json
import shutil
from pathlib import Path

from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.orchestrator import (
    Orchestrator,
    PHASE_ACTORS,
    PHASE_EVENTS,
    PHASE_WORLD,
    run_simulation,
)
from scenario_lab.output import OutputManager
from scenario_lab.resume import detect_last_phase, load_run_state, next_phase


def _mock_client() -> MockLLMClient:
    return MockLLMClient(
        {
            "list of potential external events looks like this": (
                '[{"id": "ai_breakthrough", "probability": 0.15}]'
            ),
            "which actions you want to take during the turn": (
                "## Goals\n\n* Increase AI adoption\n\n## Actions\n\n"
                "The government launches an AI support program."
            ),
            "Respond with an updated list of Metric Rules": (
                "1. ai_capability increases by 1 point per 6 months"
            ),
            "A JSON object describing all metrics": (
                "## Metrics\n\n```json\n"
                '{"ai_capability": 6, "ai_adoption_sweden": 48, '
                '"unemployment": 7, "public_sentiment_to_ai": 1}\n```\n\n'
                "## Narrative\n\nAdoption rises.\n\n## Notepad\n\nProgram launched."
            ),
            "CURRENT NARRATIVE": "Summarized history: adoption rose.",
            "Constitutional Referee": "APPROVED",
        }
    )


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_two_turns(tmp_path):
    # Runs must sit under a scenario-like directory: resume resolves the
    # scenario through the run's location, so link the real definition in.
    fake_dir = tmp_path / "sweden-ai-2030"
    fake_dir.mkdir()
    for name in ("scenario.yaml", "metrics.md"):
        (fake_dir / name).symlink_to(REPO_ROOT / "scenarios/sweden-ai-2030" / name)
    scenario = load_scenario("scenarios/sweden-ai-2030")
    manager = OutputManager(scenario, fake_dir)
    run_dir = manager.start_run()
    run_simulation(scenario, _mock_client(), num_turns=2, output_manager=manager)
    return run_dir


def test_phases_recorded_in_summary(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    phases = json.loads((run_dir / "summary.json").read_text())["phases"]
    assert phases == {"1": PHASE_WORLD, "2": PHASE_WORLD}


def test_detect_last_phase_needs_every_actor(tmp_path):
    """One answered actor is not a completed actors phase (regression)."""
    run_dir = _run_two_turns(tmp_path)
    actors_dir = run_dir / "turn-02" / "2-actors"
    kept = []
    for path in sorted(actors_dir.iterdir()):
        if path.name.endswith(".md") and not path.name.endswith(
            ("-statements.md", "-store.md")
        ):
            kept.append(path)
    assert len(kept) >= 2
    for path in kept[1:]:
        path.unlink()
    for path in list(actors_dir.glob("*-statements.md")):
        path.unlink()
    for name in (
        "3-metric-rules.md",
        "4-metrics.json",
        "4-world-state.md",
        "5-notepad.md",
        "6-historical-summary.md",
    ):
        path = run_dir / "turn-02" / name
        if path.exists():
            path.unlink()
    from scenario_lab.resume import detect_last_phase as _detect

    assert _detect(run_dir, 2) == "events"


def test_detect_last_phase_needs_store_files_when_declared(tmp_path):
    """A crash mid-store must not resume past the actors phase."""
    import json as _json

    run_dir = _run_two_turns(tmp_path)
    config_path = run_dir / "config.json"
    config = _json.loads(config_path.read_text())
    config["store"] = {"measures": {"scope": "actor"}}
    config_path.write_text(_json.dumps(config))
    actors_dir = run_dir / "turn-02" / "2-actors"
    actor_ids = sorted(
        p.name[: -len(".md")]
        for p in actors_dir.iterdir()
        if p.name.endswith(".md")
        and not p.name.endswith(("-statements.md", "-store.md"))
    )
    for actor_id in actor_ids[:-1]:
        (actors_dir / f"{actor_id}-store.json").write_text("{}")
    for name in (
        "3-metric-rules.md",
        "4-metrics.json",
        "4-world-state.md",
        "5-notepad.md",
        "6-historical-summary.md",
    ):
        path = run_dir / "turn-02" / name
        if path.exists():
            path.unlink()

    from scenario_lab.resume import detect_last_phase as _detect

    assert _detect(run_dir, 2) == "events"
    (actors_dir / f"{actor_ids[-1]}-store.json").write_text("{}")
    assert _detect(run_dir, 2) == "actors"


def test_detect_last_phase_partial_turn(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    assert detect_last_phase(run_dir, 1) == PHASE_WORLD
    # Simulate a crash after the actors phase of turn 2.
    for name in (
        "3-metric-rules.md",
        "3-metric-rules-metadata.json",
        "4-metrics.json",
        "4-metrics-metadata.json",
        "4-world-state.md",
        "5-notepad.md",
        "6-historical-summary.md",
    ):
        path = run_dir / "turn-02" / name
        if path.exists():
            path.unlink()
    assert detect_last_phase(run_dir, 2) == PHASE_ACTORS
    assert next_phase(PHASE_EVENTS) == PHASE_ACTORS
    assert next_phase(PHASE_ACTORS) == PHASE_WORLD


def test_mid_turn_resume_reproduces_world_phase(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    backup = tmp_path / "turn-02-backup"
    shutil.copytree(run_dir / "turn-02", backup)

    for name in (
        "3-metric-rules.md",
        "3-metric-rules-metadata.json",
        "4-metrics.json",
        "4-metrics-metadata.json",
        "4-world-state.md",
        "5-notepad.md",
        "6-historical-summary.md",
    ):
        path = run_dir / "turn-02" / name
        if path.exists():
            path.unlink()

    scenario, loaded_turn = load_run_state(run_dir, 1)
    assert loaded_turn == 1
    manager = OutputManager(scenario, tmp_path)
    manager.run_dir = run_dir
    orchestrator = Orchestrator(scenario, _mock_client(), manager)
    orchestrator.run_turn(2, from_phase=PHASE_WORLD)

    regenerated = sorted(
        p.relative_to(run_dir / "turn-02")
        for p in (run_dir / "turn-02").rglob("*")
        if p.is_file()
    )
    original = sorted(
        p.relative_to(backup) for p in backup.rglob("*") if p.is_file()
    )
    assert regenerated == original
    for rel in original:
        assert (run_dir / "turn-02" / rel).read_bytes() == (backup / rel).read_bytes()


def test_skipped_phases_make_no_llm_calls(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    scenario, _ = load_run_state(run_dir, 1)
    manager = OutputManager(scenario, tmp_path)
    manager.run_dir = run_dir
    client = _mock_client()
    Orchestrator(scenario, client, manager).run_turn(2, from_phase=PHASE_ACTORS)
    prompts = " ".join(s for call in client.calls for s in call).lower()
    assert "list of potential external events looks like this" not in prompts
