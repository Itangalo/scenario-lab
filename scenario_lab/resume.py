"""Resume and branch functionality for loading run state from disk."""

import json
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from .models import Scenario, EmergingDevelopment
from .loader import load_scenario, get_time_period
from .statements import parse_ledger_file, render_statements_file


def detect_last_turn(run_dir: Path) -> int:
    """Detect the last completed turn in a run directory.

    Args:
        run_dir: Path to run directory

    Returns:
        Turn number (0 if no turns completed, N for highest turn-NN directory with complete files)

    Raises:
        ValueError: If run directory doesn't exist or is invalid
    """
    if not run_dir.exists():
        raise ValueError(f"Run directory does not exist: {run_dir}")

    if not run_dir.is_dir():
        raise ValueError(f"Path is not a directory: {run_dir}")

    # Find all turn directories
    turn_dirs = sorted([d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("turn-")])

    if not turn_dirs:
        return 0

    # Check each turn directory in reverse order (highest first)
    for turn_dir in reversed(turn_dirs):
        turn_num = int(turn_dir.name.split("-")[1])

        # Required files for a complete turn
        required_files = [
            "1-events.json",
            "3-metric-rules.md",
            "4-metrics.json",
            "4-world-state.md",
            "5-notepad.md",
        ]

        # Historical summary required for turns > 1
        if turn_num > 1:
            required_files.append("6-historical-summary.md")

        # Check if 2-actors directory exists and has at least one file
        actors_dir = turn_dir / "2-actors"
        has_actors = actors_dir.exists() and actors_dir.is_dir() and any(actors_dir.iterdir())

        # Check all required files exist
        all_files_exist = all((turn_dir / f).exists() for f in required_files)

        if all_files_exist and has_actors:
            return turn_num

    # No complete turns found
    return 0


def validate_run_directory(run_dir: Path) -> Tuple[bool, list[str]]:
    """Validate run directory structure.

    Args:
        run_dir: Path to run directory

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []

    if not run_dir.exists():
        errors.append(f"Run directory does not exist: {run_dir}")
        return (False, errors)

    if not run_dir.is_dir():
        errors.append(f"Path is not a directory: {run_dir}")
        return (False, errors)

    # Check for required files
    if not (run_dir / "config.json").exists():
        errors.append("Missing config.json")

    if not (run_dir / "summary.json").exists():
        errors.append("Missing summary.json")

    # Check for at least one turn directory
    turn_dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("turn-")]
    if not turn_dirs:
        errors.append("No turn directories found")

    return (len(errors) == 0, errors)


def get_scenario_path_from_run(run_dir: Path) -> Path:
    """Determine original scenario path from run directory.

    Args:
        run_dir: Path to run directory (e.g., scenarios/X/runs/run-YYYYMMDD-HHMMSS)

    Returns:
        Path to scenario directory

    Raises:
        ValueError: If scenario directory cannot be found
    """
    # Navigate up from run directory
    # Expected structure: scenarios/X/runs/run-YYYYMMDD-HHMMSS
    # We need to go up 2 levels to get to scenarios/X

    if not run_dir.exists():
        raise ValueError(f"Run directory does not exist: {run_dir}")

    # Go up to runs directory
    runs_dir = run_dir.parent
    if runs_dir.name != "runs":
        raise ValueError(f"Expected parent directory to be 'runs', got: {runs_dir.name}")

    # Go up to scenario directory
    scenario_dir = runs_dir.parent

    # Verify scenario directory has expected files
    if not (scenario_dir / "metrics.md").exists() and not (scenario_dir / "scenario.yaml").exists():
        raise ValueError(f"Scenario directory does not contain metrics.md or scenario.yaml: {scenario_dir}")

    return scenario_dir


def get_scenario_source_from_run(run_dir: Path) -> Path:
    """Determine which scenario YAML a run was started from.

    Prefers the ``scenario_source`` recorded in the run's config.json, so a
    variant run reloads its own YAML -- with its actors and resource patches --
    rather than the base scenario.yaml. Falls back to the scenario directory for
    runs made before that field existed, and for runs whose recorded source has
    since moved.

    Args:
        run_dir: Path to run directory

    Returns:
        Path to the scenario YAML file, or the scenario directory as a fallback
    """
    scenario_dir = get_scenario_path_from_run(run_dir)

    config_file = run_dir / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            config = {}
        source = config.get("scenario_source") if isinstance(config, dict) else None
        if isinstance(source, str) and source:
            source_path = Path(source)
            if source_path.exists():
                return source_path
            # The run may have been moved between machines or checkouts. Try the
            # same file name relative to the scenario directory this run sits in.
            relocated = scenario_dir / "variants" / source_path.name
            if source_path.name != "scenario.yaml" and relocated.exists():
                return relocated
            print(
                f"  Warning: recorded scenario source not found ({source}); "
                f"falling back to {scenario_dir}"
            )

    return scenario_dir


def load_run_state(
    run_dir: Path,
    from_turn: Optional[int] = None,
    state_modifications: Optional[dict] = None
) -> Tuple[Scenario, int]:
    """Load scenario state from a run directory.

    Args:
        run_dir: Path to run directory
        from_turn: Specific turn to load (default: last completed turn)
        state_modifications: Optional dict with modifications:
            {
                "metrics": {"metric_id": new_value, ...},
                "narrative": "new narrative text",
                "notepad": "new notepad text",
                "rules": "new rules markdown"
            }

    Returns:
        Tuple of (loaded Scenario, turn_number)

    Raises:
        ValueError: If run directory is invalid or turn doesn't exist
    """
    # Validate run directory
    is_valid, errors = validate_run_directory(run_dir)
    if not is_valid:
        raise ValueError(f"Invalid run directory: {', '.join(errors)}")

    # Determine which turn to load from
    if from_turn is None:
        from_turn = detect_last_turn(run_dir)

    if from_turn == 0:
        raise ValueError("No completed turns found in run directory")

    # Verify the turn exists
    turn_dir = run_dir / f"turn-{from_turn:02d}"
    if not turn_dir.exists():
        last_turn = detect_last_turn(run_dir)
        raise ValueError(f"Turn {from_turn} does not exist. Last completed turn: {last_turn}")

    # Get scenario path and load original scenario. This must be the YAML the
    # run actually started from, not merely its directory: branching a variant
    # off the base scenario.yaml would swap its actors and resource patches.
    scenario_path = get_scenario_source_from_run(run_dir)
    scenario = load_scenario(scenario_path)

    # Load state from turn directory

    # 1. Load metrics
    metrics_file = turn_dir / "4-metrics.json"
    metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    scenario.metrics.update_from_dict(metrics)

    # 2. Load narrative
    narrative_file = turn_dir / "4-world-state.md"
    narrative = narrative_file.read_text(encoding="utf-8")
    scenario.world_state.narrative = narrative

    # 3. Load metric rules
    rules_file = turn_dir / "3-metric-rules.md"
    rules = rules_file.read_text(encoding="utf-8")
    scenario.metric_rules = rules

    # 4. Load notepad
    notepad_file = turn_dir / "5-notepad.md"
    if notepad_file.exists():
        notepad = notepad_file.read_text(encoding="utf-8")
        scenario.notepad = notepad

    # 4b. Load actor statement ledgers, so a resumed run continues from the
    # statements as they stood rather than from the actor files' initial ones.
    actors_dir = turn_dir / "2-actors"
    if actors_dir.exists():
        for actor_id, actor in scenario.actors.items():
            ledger_file = actors_dir / f"{actor_id}-statements.md"
            if ledger_file.exists():
                loaded = parse_ledger_file(ledger_file.read_text(encoding="utf-8"))
                if loaded:
                    actor.statements = loaded

    # 5. Load historical summary (if exists)
    summary_file = turn_dir / "6-historical-summary.md"
    if summary_file.exists():
        historical_summary = summary_file.read_text(encoding="utf-8")
        scenario.world_state.historical_summary = historical_summary

    # 6. Load occurred events from summary.json
    summary_json_file = run_dir / "summary.json"
    summary = json.loads(summary_json_file.read_text(encoding="utf-8"))

    if "occurred_events" in summary:
        scenario.occurred_events = set(summary["occurred_events"])
        # The record now contains repeatable events too, so restoring it must
        # not mark those as occurred: ``Event.occurred`` is the one-shot
        # suppression flag, and setting it on a repeatable event would claim
        # something the record does not say.
        for event in scenario.events:
            if event.id in scenario.occurred_events and not event.can_repeat:
                event.occurred = True

    if isinstance(summary.get("event_log"), list):
        scenario.event_log = [
            entry for entry in summary["event_log"]
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
            and isinstance(entry.get("turn"), int)
            and (from_turn is None or entry["turn"] <= from_turn)
        ]

    # 6b. Restore emerging developments (unfired emergent proposals carried
    # forward), so a resumed or branched run keeps tracking what was in flight.
    if "emerging_events" in summary and isinstance(summary["emerging_events"], list):
        restored: list[EmergingDevelopment] = []
        for entry in summary["emerging_events"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                continue
            restored.append(
                EmergingDevelopment(
                    id=entry["id"],
                    description=entry.get("description", ""),
                    first_turn=int(entry.get("first_turn", from_turn)),
                    last_turn=int(entry.get("last_turn", from_turn)),
                )
            )
        scenario.emerging_developments = restored

    # 7. Apply state modifications if provided
    if state_modifications:
        if "metrics" in state_modifications:
            for metric_id, value in state_modifications["metrics"].items():
                if metric_id in scenario.metrics.metrics:
                    scenario.metrics.metrics[metric_id].value = float(value)
                    scenario.metrics.metrics[metric_id].clamp()
                else:
                    # Print warning for unknown metrics
                    print(f"  Warning: Unknown metric '{metric_id}' in modifications, skipping")

        if "narrative" in state_modifications:
            scenario.world_state.narrative = state_modifications["narrative"]

        if "notepad" in state_modifications:
            scenario.notepad = state_modifications["notepad"]

        if "rules" in state_modifications:
            scenario.metric_rules = state_modifications["rules"]

    # 8. Update turn and time_period
    scenario.world_state.turn = from_turn
    scenario.world_state.time_period = get_time_period(
        scenario.config.start_date,
        from_turn,
        scenario.config.time_scale
    )

    return (scenario, from_turn)


def create_branch(
    parent_run_dir: Path,
    from_turn: int,
    output_base: Path,
    state_modifications: Optional[dict] = None,
    config_overrides: Optional[dict] = None
) -> Path:
    """Create a new branched run from an existing run.

    Args:
        parent_run_dir: Path to parent run
        from_turn: Turn number to branch from
        output_base: Base path for new run (scenario directory)
        state_modifications: State changes to apply (same format as load_run_state)
        config_overrides: Config changes (e.g., {"llm.events": "model-name"})

    Returns:
        Path to new run directory

    Raises:
        ValueError: If parent run is invalid or turn doesn't exist
    """
    # Validate parent run and turn
    is_valid, errors = validate_run_directory(parent_run_dir)
    if not is_valid:
        raise ValueError(f"Invalid parent run directory: {', '.join(errors)}")

    last_turn = detect_last_turn(parent_run_dir)
    if from_turn > last_turn:
        raise ValueError(f"Turn {from_turn} does not exist. Last completed turn: {last_turn}")

    if from_turn < 1:
        raise ValueError(f"Cannot branch from turn {from_turn}. Must be at least turn 1.")

    # Create new timestamped run directory. On a same-second collision (for
    # example many branches launched concurrently), append a numeric suffix
    # instead of silently merging into an existing directory.
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = f"run-{timestamp}"
    (output_base / "runs").mkdir(parents=True, exist_ok=True)
    new_run_dir = output_base / "runs" / base_name
    suffix = 0
    while True:
        try:
            new_run_dir.mkdir(exist_ok=False)
            break
        except FileExistsError:
            suffix += 1
            new_run_dir = output_base / "runs" / f"{base_name}-{suffix:02d}"

    # Copy turn directories 1 through from_turn
    for turn_num in range(1, from_turn + 1):
        turn_dir_name = f"turn-{turn_num:02d}"
        parent_turn_dir = parent_run_dir / turn_dir_name
        new_turn_dir = new_run_dir / turn_dir_name

        if parent_turn_dir.exists():
            shutil.copytree(parent_turn_dir, new_turn_dir)

    # Load and modify config.json
    parent_config_file = parent_run_dir / "config.json"
    config = json.loads(parent_config_file.read_text(encoding="utf-8"))

    # Apply config overrides
    if config_overrides:
        for key, value in config_overrides.items():
            # Handle nested keys (e.g., "llm.events")
            keys = key.split(".")
            target = config
            for i, k in enumerate(keys[:-1]):
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value

    # Add metadata
    if "metadata" not in config:
        config["metadata"] = {}

    config["metadata"]["parent_run"] = parent_run_dir.name
    config["metadata"]["branch_turn"] = from_turn
    config["metadata"]["branch_created_at"] = datetime.now().isoformat()

    if state_modifications:
        config["metadata"]["state_modifications"] = state_modifications

    if config_overrides:
        config["metadata"]["config_overrides"] = config_overrides

    # Save config.json to new run directory
    new_config_file = new_run_dir / "config.json"
    new_config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Create summary.json for the branch
    parent_summary_file = parent_run_dir / "summary.json"
    parent_summary = json.loads(parent_summary_file.read_text(encoding="utf-8"))

    # Copy history up to from_turn
    new_history = [h for h in parent_summary.get("history", []) if h["turn"] <= from_turn]

    # Get final metrics from the branch point
    final_metrics = new_history[-1]["metrics"] if new_history else {}

    new_summary = {
        "scenario": parent_summary["scenario"],
        "total_turns": from_turn,
        "final_metrics": final_metrics,
        "history": new_history,
        "occurred_events": parent_summary.get("occurred_events", []),
        "emerging_events": parent_summary.get("emerging_events", []),
        "status": "running",
        "last_updated": datetime.now().isoformat(),
        "metadata": {
            "parent_run": parent_run_dir.name,
            "branch_turn": from_turn,
            "branch_created_at": datetime.now().isoformat()
        }
    }

    if state_modifications:
        new_summary["metadata"]["state_modifications"] = state_modifications

    if config_overrides:
        new_summary["metadata"]["config_overrides"] = config_overrides

    # Save summary.json to new run directory
    new_summary_file = new_run_dir / "summary.json"
    new_summary_file.write_text(json.dumps(new_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    return new_run_dir


def persist_scenario_state_at_turn(run_dir: Path, turn: int, scenario: Scenario) -> None:
    """Persist in-memory scenario state to a specific turn directory.

    Useful for branch workflows where state modifications are applied in memory
    and should be reflected on disk immediately, even before running new turns.
    """
    turn_dir = run_dir / f"turn-{turn:02d}"
    if not turn_dir.exists():
        raise ValueError(f"Turn directory does not exist: {turn_dir}")

    metrics = {metric_id: metric.value for metric_id, metric in scenario.metrics.metrics.items()}
    (turn_dir / "4-metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (turn_dir / "4-world-state.md").write_text(scenario.world_state.narrative, encoding="utf-8")
    (turn_dir / "3-metric-rules.md").write_text(scenario.metric_rules, encoding="utf-8")
    (turn_dir / "5-notepad.md").write_text(scenario.notepad, encoding="utf-8")

    # Statement ledgers, so a branch created here starts from the right ones.
    actors_dir = turn_dir / "2-actors"
    actors_dir.mkdir(exist_ok=True)
    for actor_id, actor in scenario.actors.items():
        (actors_dir / f"{actor_id}-statements.md").write_text(
            render_statements_file(actor, turn, []), encoding="utf-8"
        )

    # Keep historical summary aligned with loaded state when present.
    if scenario.world_state.historical_summary:
        (turn_dir / "6-historical-summary.md").write_text(
            scenario.world_state.historical_summary, encoding="utf-8"
        )


def sync_summary_turn_state(run_dir: Path, turn: int, metrics: dict) -> None:
    """Upsert one turn's metrics in summary.json and keep totals consistent."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise ValueError(f"Missing summary.json in run directory: {run_dir}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    history = summary.get("history", [])

    replaced = False
    for entry in history:
        if isinstance(entry, dict) and entry.get("turn") == turn:
            entry["metrics"] = metrics
            replaced = True
            break

    if not replaced:
        history.append({"turn": turn, "metrics": metrics})

    history = sorted(
        [h for h in history if isinstance(h, dict) and "turn" in h and "metrics" in h],
        key=lambda x: x["turn"],
    )

    summary["history"] = history
    if history:
        summary["total_turns"] = history[-1]["turn"]
        summary["final_metrics"] = history[-1]["metrics"]
    summary["last_updated"] = datetime.now().isoformat()

    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
