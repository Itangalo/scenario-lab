"""Command-line interface for Scenario Lab V4."""

import argparse
import json
import queue
import re
import shlex
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import yaml
from typing import Optional

from .analysis import generate_run_analysis
from .loader import load_scenario
from .model_audit import (
    apply_recommendations as apply_model_recommendations,
    audit_model_configs,
    collect_model_hygiene_warnings,
    format_model_audit_report,
    format_recommendations,
    recommend_replacements,
)
from .models import LLMConfig
from .loader import parse_route
from .orchestrator import run_simulation
from .output import OutputManager
from .validator import validate_scenario


def apply_model_override(llm_config, model: str):
    """Apply a single model override (provider:model string) to all LLM task slots."""
    route = parse_route(model)
    llm_config.events = route
    llm_config.actors = route
    llm_config.rules = route
    llm_config.metrics = route
    llm_config.summary = route
    llm_config.analysis = route
    llm_config.referee = route


def run_model_preflight_checks(scenario) -> bool:
    """Run default model hygiene checks before a real simulation run.

    Returns:
        True if execution should continue, False if the run should stop.
    """
    llm_config = getattr(scenario.config, "llm", None)
    if not isinstance(llm_config, LLMConfig):
        return True

    warnings = collect_model_hygiene_warnings(llm_config, scope=scenario.config.name)
    if not warnings:
        return True

    print("\n⚠️  Model hygiene warnings:")
    for warning in warnings:
        print(f"  - {warning}")

    recommendations = recommend_replacements(llm_config)
    if recommendations:
        print()
        print(format_recommendations(recommendations))

    if not sys.stdin.isatty():
        print("Non-interactive terminal detected; continuing with current models.")
        return True

    if recommendations:
        response = input("\nApply the suggested replacements before running? [y/N]: ").strip().lower()
        if response in {"y", "yes"}:
            applied = apply_model_recommendations(llm_config, recommendations)
            print(f"  → Applied {applied} model replacement(s)")
            return True

    response = input("Continue with the current model configuration? [y/N]: ").strip().lower()
    if response in {"y", "yes"}:
        return True

    print("Run cancelled. Adjust model settings or use --skip-model-checks to bypass this prompt.")
    return False


@dataclass
class BatchJobResult:
    """Result of one batch-run child process."""

    target: Path
    returncode: int
    log_path: Path


@dataclass
class BatchJobSpec:
    """Definition of one child process to launch for a batch command."""

    target: Path
    command: list[str]
    log_path: Path


@dataclass
class BatchJobView:
    """Mutable display state for one batch job."""

    label: str
    run_dir: str = "-"
    status: str = "queued"
    turn: str = "-"
    activity: str = "Waiting"
    warning: str = ""
    warning_count: int = 0


def resolve_output_base(scenario_path: Path) -> Path:
    """Resolve the scenario directory that should own the run output."""
    output_base = Path(scenario_path)
    if output_base.is_file():
        original_parent = output_base.parent
        output_base = original_parent
        while output_base != output_base.parent:
            if (output_base / "metrics.md").exists():
                return output_base
            output_base = output_base.parent
        return original_parent
    return output_base


def normalize_batch_targets(targets: list[Path], use_variants: bool, repeat: int) -> list[Path]:
    """Expand batch targets into concrete scenario directories or variant files."""
    normalized: list[Path] = []

    for target in targets:
        if not target.exists():
            raise ValueError(f"Target does not exist: {target}")

        if use_variants and target.is_dir():
            variants_dir = target / "variants"
            if not variants_dir.is_dir():
                raise ValueError(f"No variants/ directory found for: {target}")

            variant_files = sorted(
                path
                for path in variants_dir.iterdir()
                if path.is_file() and path.suffix in {".yaml", ".yml"}
            )
            if not variant_files:
                raise ValueError(f"No variant YAML files found in: {variants_dir}")

            for _ in range(repeat):
                normalized.extend(variant_files)
            continue

        normalized.extend([target] * repeat)

    return normalized


def build_batch_run_command(target: Path, args: argparse.Namespace) -> list[str]:
    """Build the child command used for one batch run job."""
    command = [
        sys.executable,
        "-u",
        "-m",
        "scenario_lab.cli",
        "run",
        str(target),
        "--skip-model-checks",
        "--no-progress",
    ]

    if args.turns is not None:
        command.extend(["--turns", str(args.turns)])

    if args.model:
        command.extend(["--model", args.model])

    if args.validate:
        command.append("--validate")

    for override in args.override or []:
        command.extend(["--override", override])

    return command


def sanitize_batch_label(path: Path) -> str:
    """Create a filesystem-safe label for batch log filenames."""
    source = path.stem if path.is_file() else path.name
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", source).strip("-")
    return label or "scenario"


def detect_regression_manifest_kind(manifest_path: Path) -> str:
    """Infer whether a manifest is pairwise or distribution based on its contents."""
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        raise ValueError(f"Manifest must define a non-empty comparisons list: {manifest_path}")

    baseline = comparisons[0].get("baseline") if isinstance(comparisons[0], dict) else None
    candidate = comparisons[0].get("candidate") if isinstance(comparisons[0], dict) else None

    if isinstance(baseline, str) and isinstance(candidate, str):
        return "pairwise"
    if isinstance(baseline, dict) and isinstance(candidate, dict):
        return "distribution"
    raise ValueError(f"Could not infer manifest kind from: {manifest_path}")


def resolve_regression_manifests(target: Path, expected_kind: str) -> list[Path]:
    """Resolve one or more manifest files from a file path or scenario directory."""
    if target.is_file():
        kind = detect_regression_manifest_kind(target)
        if kind != expected_kind:
            raise ValueError(
                f"Expected a {expected_kind} manifest, but {target} is {kind}"
            )
        return [target]

    if not target.is_dir():
        raise ValueError(f"Target does not exist: {target}")

    regressions_dir = target / "regressions"
    if not regressions_dir.is_dir():
        raise ValueError(f"No regressions/ directory found for: {target}")

    manifest_paths = sorted(
        path for path in regressions_dir.iterdir() if path.is_file() and path.suffix in {".yaml", ".yml"}
    )
    if not manifest_paths:
        raise ValueError(f"No regression manifests found in: {regressions_dir}")

    selected: list[Path] = []
    for manifest_path in manifest_paths:
        kind = detect_regression_manifest_kind(manifest_path)
        if kind == expected_kind:
            selected.append(manifest_path)

    if not selected:
        raise ValueError(
            f"No {expected_kind} manifests found in: {regressions_dir}"
        )

    return selected


def resolve_integrity_targets(target: Path, max_runs: Optional[int] = None) -> list[Path]:
    """Resolve one or more run directories for integrity checking."""
    if not target.exists():
        raise ValueError(f"Target does not exist: {target}")

    if target.is_dir() and target.name.startswith("run-") and target.parent.name == "runs":
        return [target]

    runs_dir = target
    if target.is_dir() and (target / "runs").is_dir():
        runs_dir = target / "runs"

    if runs_dir.is_dir():
        run_dirs = sorted(
            path for path in runs_dir.iterdir() if path.is_dir() and path.name.startswith("run-")
        )
        if max_runs is not None:
            run_dirs = run_dirs[-max_runs:]
        if run_dirs:
            return run_dirs

    raise ValueError(
        "Expected a run directory, a runs/ directory, or a scenario directory containing runs/"
    )


def build_quality_report(
    target: Path,
    integrity_summary: dict,
    regression_reports: list[dict],
    distribution_reports: list[dict],
) -> dict:
    """Build a unified quality-check report."""
    return {
        "target": str(target.resolve()),
        "integrity": integrity_summary,
        "regressions": regression_reports,
        "distributions": distribution_reports,
    }


def format_quality_report(report: dict) -> str:
    """Format a unified quality-check report."""
    integrity = report["integrity"]
    lines = [
        "=" * 60,
        "QUALITY CHECK",
        "=" * 60,
        f"Target              : {report['target']}",
        f"Integrity runs      : {integrity['run_count']}",
        f"Integrity invalid   : {integrity['invalid_count']}",
        f"Integrity warnings  : {integrity['warning_count']}",
        f"Regression suites   : {len(report['regressions'])}",
        f"Distribution suites : {len(report['distributions'])}",
    ]

    if integrity["reports"]:
        lines.extend(["", "Integrity summary:"])
        for item in integrity["reports"]:
            status = "VALID" if item["is_valid"] else "INVALID"
            warning_note = f", warnings={len(item['warnings'])}" if item["warnings"] else ""
            lines.append(f"  - {item['run_name']}: {status}{warning_note}")

    if report["regressions"]:
        lines.extend(["", "Regression summary:"])
        for suite in report["regressions"]:
            lines.append(
                f"  - {Path(suite['manifest_path']).name}: diffs={suite['differing_count']}, errors={suite['error_count']}"
            )

    if report["distributions"]:
        lines.extend(["", "Distribution summary:"])
        for suite in report["distributions"]:
            lines.append(
                f"  - {Path(suite['manifest_path']).name}: comparisons={suite['comparison_count']}, errors={suite['error_count']}"
            )

    return "\n".join(lines)


def build_batch_run_specs(targets: list[Path], args: argparse.Namespace, batch_id: str) -> list[BatchJobSpec]:
    """Build batch-run job specs."""
    specs: list[BatchJobSpec] = []
    for index, target in enumerate(targets, start=1):
        output_base = resolve_output_base(target)
        log_dir = output_base / "runs" / "batch-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"batch-{batch_id}-{index:03d}-{sanitize_batch_label(target)}.log"
        specs.append(
            BatchJobSpec(
                target=target,
                command=build_batch_run_command(target, args),
                log_path=log_path,
            )
        )
    return specs


def is_incomplete_run(run_dir: Path) -> bool:
    """Check whether a run directory should be included in batch-resume discovery."""
    from .resume import detect_last_turn, validate_run_directory

    is_valid, _ = validate_run_directory(run_dir)
    if not is_valid:
        return False

    try:
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True

    try:
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        max_turns = int(config.get("max_turns", 0))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        max_turns = 0

    completed_turns = detect_last_turn(run_dir)
    if max_turns and completed_turns < max_turns:
        return True

    return summary.get("status") != "completed"


def collect_batch_resume_runs(targets: list[Path]) -> list[Path]:
    """Expand batch-resume targets into concrete run directories."""
    collected: list[Path] = []

    for target in targets:
        if not target.exists():
            raise ValueError(f"Target does not exist: {target}")

        if target.is_dir() and target.parent.name == "runs" and target.name.startswith("run-"):
            collected.append(target)
            continue

        if target.is_dir() and target.name == "runs":
            run_dirs = sorted(
                path for path in target.iterdir() if path.is_dir() and path.name.startswith("run-")
            )
            collected.extend(run_dir for run_dir in run_dirs if is_incomplete_run(run_dir))
            continue

        if target.is_dir() and (target / "runs").is_dir():
            runs_dir = target / "runs"
            run_dirs = sorted(
                path for path in runs_dir.iterdir() if path.is_dir() and path.name.startswith("run-")
            )
            collected.extend(run_dir for run_dir in run_dirs if is_incomplete_run(run_dir))
            continue

        raise ValueError(f"Unsupported batch-resume target: {target}")

    deduped: list[Path] = []
    seen: set[Path] = set()
    for run_dir in collected:
        resolved = run_dir.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(run_dir)

    return deduped


def build_batch_resume_command(run_dir: Path, args: argparse.Namespace) -> list[str]:
    """Build the child command used for one batch resume job."""
    command = [
        sys.executable,
        "-u",
        "-m",
        "scenario_lab.cli",
        "resume",
        str(run_dir),
        "--no-progress",
    ]

    if args.turns is not None:
        command.extend(["--turns", str(args.turns)])

    if args.model:
        command.extend(["--model", args.model])

    if args.from_turn is not None:
        command.extend(["--from-turn", str(args.from_turn)])

    for override in args.override or []:
        command.extend(["--override", override])

    return command


def build_batch_resume_specs(run_dirs: list[Path], args: argparse.Namespace, batch_id: str) -> list[BatchJobSpec]:
    """Build batch-resume job specs."""
    specs: list[BatchJobSpec] = []
    for index, run_dir in enumerate(run_dirs, start=1):
        log_dir = run_dir.parent / "batch-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"batch-resume-{batch_id}-{index:03d}-{sanitize_batch_label(run_dir)}.log"
        specs.append(
            BatchJobSpec(
                target=run_dir,
                command=build_batch_resume_command(run_dir, args),
                log_path=log_path,
            )
        )
    return specs


def truncate_batch_text(text: str, limit: int = 56) -> str:
    """Trim long status text for inline batch display."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def normalize_batch_activity_text(text: str) -> str:
    """Map raw child output onto stable batch activity labels."""
    normalized = " ".join(text.split())
    if normalized.lower() in {"done", "complete", "completed"}:
        return "Done"
    return truncate_batch_text(normalized)


def summarize_batch_activity(text: str) -> str:
    """Convert verbose child output into short, stable batch activity labels."""
    normalized = " ".join(text.split())
    activity_aliases = {
        "Determining external events": "Determining events",
        "Getting actor actions": "Getting actions",
        "Updating metric rules": "Adjusting rules",
        "Updating metrics and narrative": "Updating metrics",
        "Validating constitutional constraints": "Validating contraints",
        "Updating historical summary": "Writing history",
    }
    if normalized in activity_aliases:
        return activity_aliases[normalized]
    return truncate_batch_text(normalized)


def update_batch_view_from_line(view: BatchJobView, line: str):
    """Update one batch job's display state from a child output line."""
    text = line.strip()
    if not text:
        return

    turns_match = re.match(r"^Turns:\s+(?:(\d+)\s+to\s+)?(\d+)$", text)
    if turns_match:
        start_turn = turns_match.group(1)
        end_turn = turns_match.group(2)
        if start_turn:
            view.turn = f"{start_turn}-{end_turn}"
        elif view.turn == "-":
            view.turn = f"0/{end_turn}"
        return

    turn_match = re.match(r"^TURN\s+(\d+)(?:/(\d+))?:", text)
    if turn_match:
        current = turn_match.group(1)
        total = turn_match.group(2)
        view.turn = f"{current}/{total}" if total else current
        view.activity = "Running turn"
        return

    quiet_turn_match = re.match(r"^Turn\s+(\d+)/(\d+):", text)
    if quiet_turn_match:
        view.turn = f"{quiet_turn_match.group(1)}/{quiet_turn_match.group(2)}"
        view.activity = "Running turn"
        return

    step_match = re.match(r"^\[\d+/\d+\]\s+(.+?)\.\.\.$", text)
    if step_match:
        view.activity = summarize_batch_activity(step_match.group(1))
        return

    if text.startswith("Warning:") or text.startswith("⚠️") or " Warning:" in text:
        view.warning = truncate_batch_text(text)
        view.warning_count += 1
        return

    if text.startswith("❌"):
        view.warning = truncate_batch_text(text)
        view.warning_count += 1
        view.activity = "Error"
        return

    if text.startswith("SIMULATION COMPLETE") or text.startswith("RESUMED SIMULATION COMPLETE"):
        view.activity = "Finalizing"
        return

    if text.startswith("Cost report saved:"):
        view.activity = "Saving costs"
        return

    if text.startswith("Output directory:"):
        run_dir = text.partition(":")[2].strip()
        if run_dir:
            view.run_dir = run_dir
        view.activity = "Run dir ready"
        return

    if text.startswith("Results saved to:"):
        saved_path = text.partition(":")[2].strip()
        if saved_path:
            view.run_dir = Path(saved_path).name
        view.activity = "Saved results"
        return

    if text.startswith("Loading scenario from"):
        view.activity = "Loading scenario"
        return

    if text.startswith("Resuming run:"):
        resumed_path = text.partition(":")[2].strip()
        if resumed_path:
            view.run_dir = Path(resumed_path).name
        view.activity = "Loading run"
        return

    if text.startswith("→ ") or text.startswith("✓ "):
        view.activity = normalize_batch_activity_text(text[2:])
        return


def render_batch_table(
    title: str,
    views: list[BatchJobView],
    pending_count: int,
    running_count: int,
    completed_count: int,
    failed_count: int,
):
    """Render an inline table for batch progress."""
    from rich import box
    from rich.table import Table

    table = Table(title=title, box=box.SIMPLE_HEAVY)
    table.caption = (
        f"Pending: {pending_count}  Running: {running_count}  "
        f"Completed: {completed_count}  Failed: {failed_count}"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Scenario", overflow="fold")
    table.add_column("Run", overflow="fold")
    table.add_column("Status", width=11)
    table.add_column("Turn", width=9)
    table.add_column("Activity", overflow="fold")
    table.add_column("Warning", overflow="fold")

    for index, view in enumerate(views, start=1):
        warning_text = ""
        if view.warning:
            warning_text = view.warning
            if view.warning_count > 1:
                warning_text = f"{warning_text} ({view.warning_count})"

        table.add_row(
            str(index),
            view.label,
            view.run_dir,
            view.status,
            view.turn,
            view.activity,
            warning_text,
        )

    return table


def execute_batch_specs(specs: list[BatchJobSpec], max_concurrency: int, title: str) -> tuple[list[BatchJobResult], list[tuple[Path, str]]]:
    """Run batch jobs with bounded concurrency and inline status updates."""
    from rich.console import Console
    from rich.live import Live

    views = [BatchJobView(label=sanitize_batch_label(spec.target)) for spec in specs]
    results: list[BatchJobResult] = []
    failures: list[tuple[Path, str]] = []

    console = Console()
    use_live = console.is_terminal

    pending = list(enumerate(specs, start=1))
    line_queue: "queue.Queue[tuple[int, str | None]]" = queue.Queue()
    active: dict[int, dict] = {}

    def start_job(job_id: int, spec: BatchJobSpec):
        view = views[job_id - 1]
        view.status = "starting"
        view.activity = "Launching"

        try:
            log_file = spec.log_path.open("w", encoding="utf-8")
            log_file.write(f"$ {' '.join(shlex.quote(part) for part in spec.command)}\n\n")
            log_file.flush()
            process = subprocess.Popen(
                spec.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            failures.append((spec.target, str(exc)))
            view.status = "failed"
            view.activity = "Launch error"
            view.warning = truncate_batch_text(str(exc))
            return

        def pump_output():
            try:
                assert process.stdout is not None
                for raw_line in process.stdout:
                    log_file.write(raw_line)
                    log_file.flush()
                    line_queue.put((job_id, raw_line.rstrip("\n")))
            finally:
                if process.stdout is not None:
                    process.stdout.close()
                line_queue.put((job_id, None))

        thread = threading.Thread(target=pump_output, daemon=True)
        thread.start()

        active[job_id] = {
            "spec": spec,
            "process": process,
            "log_file": log_file,
            "thread": thread,
            "output_done": False,
        }
        view.status = "running"
        view.activity = "Starting"

    def refresh_live(live):
        if not use_live:
            return
        pending_count = len(pending)
        running_count = sum(1 for view in views if view.status == "running")
        completed_count = sum(1 for view in views if view.status == "completed")
        failed_count = sum(1 for view in views if view.status == "failed")
        live.update(
            render_batch_table(
                title,
                views,
                pending_count,
                running_count,
                completed_count,
                failed_count,
            ),
            refresh=True,
        )

    def finalize_finished_jobs():
        finished_ids: list[int] = []
        for job_id, state in active.items():
            process = state["process"]
            if process.poll() is None or not state["output_done"]:
                continue

            view = views[job_id - 1]
            thread = state["thread"]
            thread.join(timeout=0.1)
            state["log_file"].close()

            result = BatchJobResult(
                target=state["spec"].target,
                returncode=process.returncode or 0,
                log_path=state["spec"].log_path,
            )
            results.append(result)

            if result.returncode == 0:
                view.status = "completed"
                view.activity = "Done"
            else:
                view.status = "failed"
                view.activity = f"Exit {result.returncode}"
                if not view.warning:
                    view.warning = f"Exited with code {result.returncode}"

            finished_ids.append(job_id)

        for job_id in finished_ids:
            active.pop(job_id, None)

    live = None
    if use_live:
        live = Live(
            render_batch_table(title, views, len(pending), 0, 0, 0),
            console=console,
            refresh_per_second=8,
        )
        live.start()

    try:
        while pending or active:
            while pending and len(active) < max_concurrency:
                job_id, spec = pending.pop(0)
                start_job(job_id, spec)
                refresh_live(live)

            try:
                job_id, line = line_queue.get(timeout=0.1)
                if job_id in active:
                    if line is None:
                        active[job_id]["output_done"] = True
                    else:
                        update_batch_view_from_line(views[job_id - 1], line)
                        if not use_live and views[job_id - 1].warning and views[job_id - 1].warning_count == 1:
                            print(f"⚠️  {specs[job_id - 1].target}: {views[job_id - 1].warning}")
                refresh_live(live)
            except queue.Empty:
                pass

            finalize_finished_jobs()
            refresh_live(live)
    finally:
        if live is not None:
            live.stop()

    if use_live:
        console.print(
            render_batch_table(
                title,
                views,
                pending_count=0,
                running_count=0,
                completed_count=sum(1 for view in views if view.status == "completed"),
                failed_count=sum(1 for view in views if view.status == "failed"),
            )
        )

    return results, failures


def main():
    """CLI entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Scenario Lab V4 - LLM-driven scenario simulation"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command (default)
    run_parser = subparsers.add_parser("run", help="Run a simulation")
    run_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    run_parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to run (default: from config)",
    )
    run_parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true", help="Print prompts without calling LLM"
    )
    run_parser.add_argument(
        "--override",
        action="append",
        help="Override scenario config (e.g. 'output_language=Swedish' or 'llm.temperature=0.5')",
    )
    run_parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress display"
    )
    run_parser.add_argument(
        "--quiet", action="store_true", help="Minimal output mode"
    )
    run_parser.add_argument(
        "--validate", action="store_true", help="Validate scenario before running"
    )
    run_parser.add_argument(
        "--skip-model-checks",
        action="store_true",
        help="Skip default model hygiene checks before running",
    )

    # Batch run command
    batch_run_parser = subparsers.add_parser(
        "batch-run",
        help="Run multiple scenarios or variants in parallel",
    )
    batch_run_parser.add_argument(
        "targets",
        nargs="+",
        type=Path,
        help="Scenario directories or variant YAML files",
    )
    batch_run_parser.add_argument(
        "--variants",
        action="store_true",
        help="Expand directory targets to all YAML files in variants/",
    )
    batch_run_parser.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
        help="Maximum number of runs to execute at the same time",
    )
    batch_run_parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to run for each scenario (default: from config)",
    )
    batch_run_parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model for all batch jobs"
    )
    batch_run_parser.add_argument(
        "--override",
        action="append",
        help="Override scenario config for all batch jobs (repeatable)",
    )
    batch_run_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate each scenario before running",
    )
    batch_run_parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Run each resolved target N times",
    )

    # Batch resume command
    batch_resume_parser = subparsers.add_parser(
        "batch-resume",
        help="Resume multiple runs in parallel",
    )
    batch_resume_parser.add_argument(
        "targets",
        nargs="+",
        type=Path,
        help="Run directories, runs/ directories, or scenario directories",
    )
    batch_resume_parser.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
        help="Maximum number of resumes to execute at the same time",
    )
    batch_resume_parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Total turns to run for each resumed scenario",
    )
    batch_resume_parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model for all resumed jobs"
    )
    batch_resume_parser.add_argument(
        "--override",
        action="append",
        help="Override config for all resumed jobs (repeatable)",
    )
    batch_resume_parser.add_argument(
        "--from-turn",
        type=int,
        default=None,
        help="Force all resumes to load from a specific turn",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a scenario")
    validate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume an interrupted or completed run")
    resume_parser.add_argument("run_dir", type=Path, help="Path to run directory")
    resume_parser.add_argument("--turns", type=int, default=None, help="Total turns to run")
    resume_parser.add_argument("--model", type=str, default=None, help="Override all LLM models")
    resume_parser.add_argument("--override", action="append", help="Override config (e.g., 'llm.temperature=0.5')")
    resume_parser.add_argument("--from-turn", type=int, default=None, help="Resume from specific turn")
    resume_parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress display"
    )

    # Branch command
    branch_parser = subparsers.add_parser("branch", help="Create a branch from an existing run")
    branch_parser.add_argument("run_dir", type=Path, help="Path to parent run directory")
    branch_parser.add_argument("--from-turn", type=int, required=True, help="Turn number to branch from")
    branch_parser.add_argument("--turns", type=int, default=None, help="Total turns to run from branch point")
    branch_parser.add_argument("--modify-metric", action="append", help="Modify metric: 'metric_id=value'")
    branch_parser.add_argument("--modify-narrative", type=str, help="Replace narrative text")
    branch_parser.add_argument("--model", type=str, help="Override all LLM models")
    branch_parser.add_argument("--override", action="append", help="Override config values")

    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate charts for a run")
    viz_parser.add_argument("run_dir", type=Path, help="Path to run directory (e.g. scenarios/x/runs/run-123)")

    # Costs command
    costs_parser = subparsers.add_parser("costs", help="Display cost report for a run")
    costs_parser.add_argument("run_dir", type=Path, help="Path to run directory")
    costs_parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown by turn")

    analyze_parser = subparsers.add_parser("analyze", help="Generate a post-run analysis report")
    analyze_parser.add_argument("run_dir", type=Path, help="Path to run directory")
    analyze_parser.add_argument("--model", type=str, default=None, help="Override analysis model")
    analyze_parser.add_argument("--output", type=Path, default=None, help="Write report to a custom path")
    analyze_parser.add_argument("--json", action="store_true", help="Write structured JSON instead of markdown")
    analyze_parser.add_argument("--no-save", action="store_true", help="Print report summary only without saving")

    # Compare runs command
    compare_runs_parser = subparsers.add_parser(
        "compare-runs",
        help="Compare two saved runs for regressions or divergences",
    )
    compare_runs_parser.add_argument("baseline_run", type=Path, help="Baseline run directory")
    compare_runs_parser.add_argument("candidate_run", type=Path, help="Candidate run directory")
    compare_runs_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    compare_runs_parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with status 1 if any differences are detected",
    )

    integrity_parser = subparsers.add_parser(
        "check-run-integrity",
        help="Run strict structural validation on a saved run",
    )
    integrity_parser.add_argument(
        "run_dir",
        type=Path,
        help="Run directory, runs/ directory, or scenario directory to validate",
    )
    integrity_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    integrity_parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="When checking a runs/ or scenario directory, only inspect the most recent N runs",
    )

    regression_parser = subparsers.add_parser(
        "check-regressions",
        help="Run a manifest of saved-run regression comparisons",
    )
    regression_parser.add_argument(
        "manifest",
        type=Path,
        help="Path to a regression manifest YAML or a scenario directory with regressions/",
    )
    regression_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    regression_parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with status 1 if any comparison differs or errors",
    )

    distribution_parser = subparsers.add_parser(
        "compare-distributions",
        help="Compare output distributions across sets of saved runs",
    )
    distribution_parser.add_argument(
        "manifest",
        type=Path,
        help="Path to a distribution manifest YAML or a scenario directory with regressions/",
    )
    distribution_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")

    quality_parser = subparsers.add_parser(
        "quality-check",
        help="Run integrity, regression, and distribution checks for a target",
    )
    quality_parser.add_argument(
        "target",
        type=Path,
        help="Run directory, runs/ directory, scenario directory, or manifest-backed scenario target",
    )
    quality_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    quality_parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="When checking runs from a scenario or runs/ directory, only inspect the most recent N runs",
    )
    quality_parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with status 1 when pairwise regression suites contain differences",
    )

    # Estimate command
    estimate_parser = subparsers.add_parser("estimate", help="Estimate costs before running")
    estimate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    estimate_parser.add_argument("--turns", type=int, help="Number of turns (default: from config)")
    estimate_parser.add_argument("--model", type=str, help="Override all LLM models for estimation")

    refresh_pricing_parser = subparsers.add_parser(
        "refresh-pricing",
        help="Refresh the cached LLM pricing snapshot(s)",
    )
    refresh_pricing_parser.add_argument(
        "--json",
        action="store_true",
        help="Print refresh metadata as JSON",
    )
    refresh_pricing_parser.add_argument(
        "--provider",
        choices=["openrouter", "anthropic"],
        default=None,
        help="Refresh only this provider (default: all)",
    )

    # Calibrate command
    calibrate_parser = subparsers.add_parser(
        "calibrate",
        help="Analyze existing runs for scenario calibration (no API calls)",
    )
    calibrate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    calibrate_parser.add_argument("--max-runs", type=int, default=None, help="Analyze most recent N runs")
    calibrate_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    calibrate_parser.add_argument("--output", type=Path, default=None, help="Write report to file")

    # Audit models command
    audit_models_parser = subparsers.add_parser(
        "audit-models",
        help="Audit configured LLM models for stale or risky selections",
    )
    audit_models_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("scenarios"),
        help="Path to a scenario, scenario config, or directory tree (default: scenarios/)",
    )
    audit_models_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")

    args = parser.parse_args()

    # Default to run if no command specified (backward compatibility)
    if args.command is None and hasattr(args, "scenario"):
        args.command = "run"
    elif args.command is None:
        parser.print_help()
        return

    if args.command == "visualize":
        try:
            # Import here to avoid dependency requirement for basic runs if plotly missing
            from .visualizer import create_visualization
            print(f"Generating visualization for: {args.run_dir}")
            output_path = create_visualization(args.run_dir)
            print(f"✅ Visualization saved to: {output_path}")
        except ImportError:
            print("❌ Error: 'plotly' not installed. Run 'pip install plotly' to use this feature.")
        except Exception as e:
            print(f"❌ Error generating visualization: {e}")
        return

    if args.command == "batch-run":
        if args.max_concurrency < 1:
            print("❌ --max-concurrency must be at least 1")
            return 1
        if args.repeat < 1:
            print("❌ --repeat must be at least 1")
            return 1

        try:
            targets = normalize_batch_targets(args.targets, args.variants, args.repeat)
        except ValueError as e:
            print(f"❌ {e}")
            return 1

        if not targets:
            print("No batch targets resolved.")
            return 1

        batch_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        worker_count = min(args.max_concurrency, len(targets))
        print(f"Launching batch: {len(targets)} run(s)")
        print(f"Max concurrency: {worker_count}")

        if args.variants:
            print("Mode: variants")

        specs = build_batch_run_specs(targets, args, batch_id)
        results, failures = execute_batch_specs(specs, worker_count, "Batch Run Progress")

        success_count = sum(1 for result in results if result.returncode == 0)
        failed_results = [result for result in results if result.returncode != 0]
        total_failures = len(failed_results) + len(failures)

        print(f"\n{'='*60}")
        print("BATCH RUN COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_failures}")

        for result in failed_results:
            print(f"  - {result.target} (log: {result.log_path})")

        for target, error_text in failures:
            print(f"  - {target} (launch error: {error_text})")

        return 1 if total_failures else 0

    if args.command == "batch-resume":
        if args.max_concurrency < 1:
            print("❌ --max-concurrency must be at least 1")
            return 1

        try:
            run_dirs = collect_batch_resume_runs(args.targets)
        except ValueError as e:
            print(f"❌ {e}")
            return 1

        if not run_dirs:
            print("No incomplete runs found.")
            return 0

        batch_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        worker_count = min(args.max_concurrency, len(run_dirs))
        print(f"Launching batch resume: {len(run_dirs)} run(s)")
        print(f"Max concurrency: {worker_count}")

        specs = build_batch_resume_specs(run_dirs, args, batch_id)
        results, failures = execute_batch_specs(specs, worker_count, "Batch Resume Progress")

        success_count = sum(1 for result in results if result.returncode == 0)
        failed_results = [result for result in results if result.returncode != 0]
        total_failures = len(failed_results) + len(failures)

        print(f"\n{'='*60}")
        print("BATCH RESUME COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_failures}")

        for result in failed_results:
            print(f"  - {result.target} (log: {result.log_path})")

        for run_dir, error_text in failures:
            print(f"  - {run_dir} (launch error: {error_text})")

        return 1 if total_failures else 0

    if args.command == "validate":
        print(f"Validating scenario: {args.scenario}...")
        result = validate_scenario(args.scenario)

        if result.errors:
            print("\n❌ Validation FAILED with the following errors:")
            for error in result.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Scenario is valid!")

        if result.warnings:
            print("\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        return

    if args.command == "costs":
        costs_file = args.run_dir / "costs.json"

        if not costs_file.exists():
            print(f"❌ No costs.json found in {args.run_dir}")
            print("   This run may not have cost tracking enabled.")
            return

        try:
            costs_data = json.loads(costs_file.read_text())
        except json.JSONDecodeError as e:
            print(f"❌ Error reading costs.json: {e}")
            return

        # Display cost report
        print("=" * 60)
        print("COST REPORT")
        print("=" * 60)
        print(f"Run: {args.run_dir.name}")
        print(f"\nTotal cost: ${costs_data['total_cost_usd']:.4f}")
        print(f"Total tokens: {costs_data['total_tokens']:,}")

        num_turns = len(costs_data.get('by_turn', []))
        if num_turns > 0:
            avg_cost = costs_data['total_cost_usd'] / num_turns
            avg_tokens = costs_data['total_tokens'] / num_turns
            print(f"Average per turn: ${avg_cost:.4f} ({avg_tokens:,.0f} tokens)")

        # By task summary
        if 'by_task_total' in costs_data:
            print("\nBy Task (Total):")
            sorted_tasks = sorted(
                costs_data['by_task_total'].items(),
                key=lambda x: x[1]['cost_usd'],
                reverse=True
            )
            for task_name, task_data in sorted_tasks:
                print(
                    f"  {task_name:20s}: ${task_data['cost_usd']:.4f} "
                    f"({task_data['tokens']:,} tokens, {task_data['calls']} calls)"
                )

        # By model summary
        if 'by_model' in costs_data:
            print("\nBy Model:")
            sorted_models = sorted(
                costs_data['by_model'].items(),
                key=lambda x: x[1]['cost_usd'],
                reverse=True
            )
            for model, data in sorted_models:
                print(
                    f"  {model:40s}: ${data['cost_usd']:.4f} "
                    f"({data['tokens']:,} tokens, {data['calls']} calls)"
                )

        # Detailed: by turn
        if args.detailed and 'by_turn' in costs_data:
            print("\nBy Turn:")
            for turn_data in costs_data['by_turn']:
                turn = turn_data['turn']
                print(
                    f"  Turn {turn:2d}: ${turn_data['cost_usd']:.4f} "
                    f"({turn_data['tokens']:,} tokens)"
                )

                # Task breakdown for this turn
                if 'by_task' in turn_data:
                    for task_name, task_data in sorted(turn_data['by_task'].items()):
                        print(
                            f"    {task_name:18s}: ${task_data['cost_usd']:.4f} "
                            f"({task_data['tokens']:,} tokens)"
                        )

        print("=" * 60)
        return

    if args.command == "analyze":
        try:
            result = generate_run_analysis(
                args.run_dir,
                model=args.model,
                output_path=args.output,
                json_output=args.json,
                no_save=args.no_save,
            )
        except Exception as e:
            print(f"❌ Run analysis failed: {e}")
            return 1

        if result.output_path is not None:
            print(f"Analysis saved to: {result.output_path}")
        elif not args.no_save:
            print("Analysis generated.")

        if result.summary_text:
            print()
            print(result.summary_text)

        return 0

    if args.command == "compare-runs":
        from .regression import compare_runs, format_run_comparison

        try:
            report = compare_runs(args.baseline_run, args.candidate_run)
        except Exception as e:
            print(f"❌ Run comparison failed: {e}")
            return 1

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_run_comparison(report))

        return 1 if args.fail_on_diff and report["has_differences"] else 0

    if args.command == "check-run-integrity":
        from .regression import (
            check_run_integrity,
            format_integrity_suite,
            format_run_integrity,
            summarize_integrity_reports,
        )

        try:
            run_dirs = resolve_integrity_targets(args.run_dir, max_runs=args.max_runs)
        except Exception as e:
            print(f"❌ Integrity check failed: {e}")
            return 1

        reports = [check_run_integrity(run_dir) for run_dir in run_dirs]
        if len(reports) == 1 and run_dirs[0] == args.run_dir:
            report = reports[0]
            if args.json:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print(format_run_integrity(report))
            return 0 if report["is_valid"] else 1

        summary = summarize_integrity_reports(reports, str(args.run_dir.resolve()))
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            print(format_integrity_suite(summary))
        return 0 if summary["invalid_count"] == 0 else 1

    if args.command == "check-regressions":
        from .regression import format_regression_suite, run_regression_suite

        try:
            manifests = resolve_regression_manifests(args.manifest, "pairwise")
        except Exception as e:
            print(f"❌ Regression check failed: {e}")
            return 1

        reports = [run_regression_suite(manifest) for manifest in manifests]

        if args.json:
            payload = reports[0] if len(reports) == 1 else {"reports": reports}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for index, report in enumerate(reports):
                if index:
                    print()
                print(format_regression_suite(report))

        should_fail = any(report["has_differences"] or report["has_errors"] for report in reports)
        return 1 if args.fail_on_diff and should_fail else 0

    if args.command == "compare-distributions":
        from .regression import compare_distributions, format_distribution_comparison

        try:
            manifests = resolve_regression_manifests(args.manifest, "distribution")
        except Exception as e:
            print(f"❌ Distribution comparison failed: {e}")
            return 1

        reports = [compare_distributions(manifest) for manifest in manifests]

        if args.json:
            payload = reports[0] if len(reports) == 1 else {"reports": reports}
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for index, report in enumerate(reports):
                if index:
                    print()
                print(format_distribution_comparison(report))
        return 0 if all(report["error_count"] == 0 for report in reports) else 1

    if args.command == "quality-check":
        from .regression import (
            check_run_integrity,
            compare_distributions,
            run_regression_suite,
            summarize_integrity_reports,
        )

        try:
            run_dirs = resolve_integrity_targets(args.target, max_runs=args.max_runs)
        except Exception as e:
            print(f"❌ Quality check failed during integrity target resolution: {e}")
            return 1

        integrity_reports = [check_run_integrity(run_dir) for run_dir in run_dirs]
        integrity_summary = summarize_integrity_reports(
            integrity_reports,
            str(args.target.resolve()),
        )

        regression_reports: list[dict] = []
        distribution_reports: list[dict] = []
        if args.target.is_dir() and (args.target / "regressions").is_dir():
            try:
                manifests = resolve_regression_manifests(args.target, "pairwise")
                regression_reports = [run_regression_suite(manifest) for manifest in manifests]
            except ValueError:
                regression_reports = []

            try:
                manifests = resolve_regression_manifests(args.target, "distribution")
                distribution_reports = [compare_distributions(manifest) for manifest in manifests]
            except ValueError:
                distribution_reports = []

        report = build_quality_report(
            args.target,
            integrity_summary,
            regression_reports,
            distribution_reports,
        )

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_quality_report(report))

        has_invalid_integrity = integrity_summary["invalid_count"] > 0
        has_regression_errors = any(item["has_errors"] for item in regression_reports)
        has_distribution_errors = any(item["error_count"] > 0 for item in distribution_reports)
        has_regression_diffs = any(item["has_differences"] for item in regression_reports)

        should_fail = has_invalid_integrity or has_regression_errors or has_distribution_errors
        if args.fail_on_diff:
            should_fail = should_fail or has_regression_diffs
        return 1 if should_fail else 0

    if args.command == "estimate":
        from .estimator import CostEstimator, format_estimate_report

        print(f"Loading scenario: {args.scenario}...")
        try:
            scenario = load_scenario(args.scenario)
        except Exception as e:
            print(f"❌ Error loading scenario: {e}")
            return

        # Override model if specified
        if args.model:
            apply_model_override(scenario.config.llm, args.model)

        # Determine number of turns
        num_turns = args.turns or scenario.config.max_turns

        # Estimate costs
        print(f"Estimating costs for {num_turns} turns...\n")
        estimator = CostEstimator(scenario)
        estimate = estimator.estimate_costs(num_turns)

        # Display report
        report = format_estimate_report(estimate, scenario.config.name, num_turns)
        print(report)
        return

    if args.command == "refresh-pricing":
        from .pricing import OpenRouterPricingCache, AnthropicPricingCache

        provider_filter = getattr(args, "provider", None)
        results = []

        providers_to_refresh = []
        if provider_filter in (None, "openrouter"):
            providers_to_refresh.append(("openrouter", OpenRouterPricingCache()))
        if provider_filter in (None, "anthropic"):
            providers_to_refresh.append(("anthropic", AnthropicPricingCache()))

        if not args.json:
            label = provider_filter or "all"
            print(f"Refreshing pricing cache ({label})...")

        any_failure = False
        for provider_name, cache in providers_to_refresh:
            ok = cache.refresh()
            if ok:
                snapshot = cache._snapshot or {"models": {}, "fetched_at": None}
                results.append({
                    "provider": provider_name,
                    "status": "ok",
                    "cache_path": str(cache.cache_path),
                    "fetched_at": snapshot.get("fetched_at"),
                    "model_count": len(snapshot.get("models", {})),
                })
            else:
                any_failure = True
                results.append({
                    "provider": provider_name,
                    "status": "error",
                    "cache_path": str(cache.cache_path),
                    "message": f"Could not fetch pricing from {provider_name}.",
                })

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for entry in results:
                if entry["status"] == "ok":
                    print(
                        f"  ✅ {entry['provider']}: {entry['model_count']} models "
                        f"(fetched_at: {entry['fetched_at']})"
                    )
                else:
                    print(f"  ❌ {entry['provider']}: {entry['message']}")

        return 1 if any_failure else 0

    if args.command == "calibrate":
        from .calibration import analyze_runs, format_analysis_report

        scenario_dir = args.scenario if args.scenario.is_dir() else args.scenario.parent
        print(f"Analyzing runs for: {scenario_dir}")

        try:
            analysis = analyze_runs(scenario_dir, max_runs=args.max_runs)
        except Exception as e:
            print(f"❌ Calibration analysis failed: {e}")
            return

        if args.json:
            report = json.dumps(analysis, indent=2, ensure_ascii=False)
        else:
            report = format_analysis_report(analysis)

        if args.output:
            args.output.write_text(report, encoding="utf-8")
            print(f"✅ Calibration report written to: {args.output}")
        else:
            print(report)
        return

    if args.command == "audit-models":
        try:
            report = audit_model_configs(args.path)
        except Exception as e:
            print(f"❌ Model audit failed: {e}")
            return

        if args.json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(format_model_audit_report(report))
        return

    if args.command == "resume":
        from .resume import load_run_state, detect_last_turn, validate_run_directory

        print(f"Resuming run: {args.run_dir}")

        # Validate
        is_valid, errors = validate_run_directory(args.run_dir)
        if not is_valid:
            print(f"❌ Invalid run directory:")
            for error in errors:
                print(f"  - {error}")
            return 1

        # Determine resume point
        from_turn = args.from_turn or detect_last_turn(args.run_dir)
        if from_turn == 0:
            print("❌ No completed turns found")
            return 1
        print(f"  Resuming from turn {from_turn}")

        # Load state
        scenario, loaded_turn = load_run_state(args.run_dir, from_turn)
        print(f"  ✓ Loaded scenario state from turn {loaded_turn}")

        # Apply overrides (reuse existing logic from run command)
        if args.override:
            for override in args.override:
                if "=" not in override:
                    print(f"Warning: Invalid override format '{override}', skipping. Use 'key=value'.")
                    continue

                key_path, value = override.split("=", 1)
                keys = key_path.split(".")

                # Try to convert value to int/float/bool
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string

                # Navigate to the correct object
                target = scenario.config
                for i, key in enumerate(keys[:-1]):
                    if hasattr(target, key):
                        target = getattr(target, key)
                    elif isinstance(target, dict) and key in target:
                        target = target[key]
                    else:
                        print(f"Warning: Could not find key '{key}' in path '{key_path}', skipping override.")
                        target = None
                        break

                if target is not None:
                    last_key = keys[-1]
                    if hasattr(target, last_key):
                        setattr(target, last_key, value)
                        print(f"  → Overrode {key_path} = {value}")
                    elif isinstance(target, dict):
                        target[last_key] = value
                        print(f"  → Overrode {key_path} = {value}")
                    else:
                        try:
                            setattr(target, last_key, value)
                            print(f"  → Overrode {key_path} = {value}")
                        except Exception as e:
                            print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

        if args.model:
            apply_model_override(scenario.config.llm, args.model)
            print(f"  → Overrode all models to: {args.model}")

        # Setup OutputManager for existing directory
        scenario_dir = args.run_dir.parent.parent
        output_manager = OutputManager(scenario, scenario_dir)
        output_manager.run_dir = args.run_dir  # Use existing directory

        num_turns = args.turns or scenario.config.max_turns
        start_turn = loaded_turn + 1

        # Update summary.json resume metadata
        summary_path = args.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text())
        summary["resumed_at"] = datetime.now().isoformat()
        summary["resumed_from_turn"] = loaded_turn
        if start_turn <= num_turns:
            summary["status"] = "running"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

        # Run simulation
        print(f"\nContinuing simulation from turn {start_turn}")
        print(f"LLM Configuration:")
        print(f"  Events: {scenario.config.llm.events}")
        actors_cfg = scenario.config.llm.actors
        if isinstance(actors_cfg, dict):
            print(f"  Actors:")
            for actor_id, model in actors_cfg.items():
                print(f"    {actor_id}: {model}")
        else:
            print(f"  Actors: {actors_cfg} (all)")
        print(f"  Rules: {scenario.config.llm.rules}")
        print(f"  Metrics: {scenario.config.llm.metrics}")
        print(f"Turns: {start_turn} to {num_turns}")

        if start_turn > num_turns:
            print("No additional turns to run. Finalizing existing run state.")
            output_manager.finalize_summary([])
            print(f"\n{'='*60}")
            print(f"RESUMED SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Results saved to: {args.run_dir}")
            return 0

        results = run_simulation(
            scenario,
            llm_client=None,
            num_turns=num_turns,
            output_manager=output_manager,
            start_turn=start_turn
        )

        # Finalize
        output_manager.finalize_summary(results)
        print(f"\n{'='*60}")
        print(f"RESUMED SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {args.run_dir}")
        return 0

    if args.command == "branch":
        from .resume import (
            load_run_state,
            create_branch,
            get_scenario_path_from_run,
            persist_scenario_state_at_turn,
            sync_summary_turn_state,
        )

        print(f"Creating branch from: {args.run_dir}")
        print(f"  Branch point: Turn {args.from_turn}")

        # Parse state modifications
        state_mods = {}
        if args.modify_metric:
            state_mods["metrics"] = {}
            for mod in args.modify_metric:
                if "=" not in mod:
                    print(f"Warning: Invalid metric modification format '{mod}', skipping. Use 'metric_id=value'.")
                    continue
                metric_id, value = mod.split("=", 1)
                try:
                    state_mods["metrics"][metric_id] = float(value)
                except ValueError:
                    print(f"Warning: Invalid metric value '{value}' for metric '{metric_id}', skipping.")
                    continue

        if args.modify_narrative:
            state_mods["narrative"] = args.modify_narrative

        # Parse config overrides
        config_overrides = {}
        if args.override:
            for override in args.override:
                if "=" not in override:
                    print(f"Warning: Invalid override format '{override}', skipping. Use 'key=value'.")
                    continue
                key, value = override.split("=", 1)
                config_overrides[key] = value

        if args.model:
            config_overrides["llm.events"] = args.model
            config_overrides["llm.actors"] = args.model
            config_overrides["llm.rules"] = args.model
            config_overrides["llm.metrics"] = args.model
            config_overrides["llm.summary"] = args.model
            config_overrides["llm.referee"] = args.model

        # Determine output location
        try:
            scenario_path = get_scenario_path_from_run(args.run_dir)
            output_base = scenario_path if scenario_path.is_dir() else scenario_path.parent
        except Exception as e:
            print(f"❌ Error determining scenario path: {e}")
            return

        # Create branch
        try:
            new_run_dir = create_branch(
                args.run_dir,
                args.from_turn,
                output_base,
                state_modifications=state_mods if state_mods else None,
                config_overrides=config_overrides if config_overrides else None
            )
            print(f"  ✓ Created branch: {new_run_dir.name}")
        except Exception as e:
            print(f"❌ Error creating branch: {e}")
            return

        # Load branched state
        try:
            scenario, loaded_turn = load_run_state(
                new_run_dir,
                from_turn=args.from_turn,
                state_modifications=state_mods if state_mods else None
            )
            print(f"  ✓ Loaded scenario state from turn {loaded_turn}")
        except Exception as e:
            print(f"❌ Error loading branched state: {e}")
            return

        # Apply config overrides to scenario
        if args.override:
            for override in args.override:
                if "=" not in override:
                    continue

                key_path, value = override.split("=", 1)
                keys = key_path.split(".")

                # Try to convert value to int/float/bool
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string

                # Navigate to the correct object
                target = scenario.config
                for i, key in enumerate(keys[:-1]):
                    if hasattr(target, key):
                        target = getattr(target, key)
                    elif isinstance(target, dict) and key in target:
                        target = target[key]
                    else:
                        print(f"Warning: Could not find key '{key}' in path '{key_path}', skipping override.")
                        target = None
                        break

                if target is not None:
                    last_key = keys[-1]
                    if hasattr(target, last_key):
                        setattr(target, last_key, value)
                        print(f"  → Overrode {key_path} = {value}")
                    elif isinstance(target, dict):
                        target[last_key] = value
                        print(f"  → Overrode {key_path} = {value}")
                    else:
                        try:
                            setattr(target, last_key, value)
                            print(f"  → Overrode {key_path} = {value}")
                        except Exception as e:
                            print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

        if args.model:
            apply_model_override(scenario.config.llm, args.model)
            print(f"  → Overrode all models to: {args.model}")

        # Run from branch point
        output_manager = OutputManager(scenario, output_base)
        output_manager.run_dir = new_run_dir

        # Persist branched state at branch point so modifications are durable on disk.
        persist_scenario_state_at_turn(new_run_dir, loaded_turn, scenario)
        branch_point_metrics = {m.id: m.value for m in scenario.metrics.metrics.values()}
        sync_summary_turn_state(new_run_dir, loaded_turn, branch_point_metrics)

        start_turn = loaded_turn + 1
        num_turns = args.turns or scenario.config.max_turns
        print(f"\nRunning simulation from turn {start_turn}")
        print(f"LLM Configuration:")
        print(f"  Events: {scenario.config.llm.events}")
        actors_cfg = scenario.config.llm.actors
        if isinstance(actors_cfg, dict):
            print(f"  Actors:")
            for actor_id, model in actors_cfg.items():
                print(f"    {actor_id}: {model}")
        else:
            print(f"  Actors: {actors_cfg} (all)")
        print(f"  Rules: {scenario.config.llm.rules}")
        print(f"  Metrics: {scenario.config.llm.metrics}")
        print(f"Turns: {start_turn} to {num_turns}")

        if start_turn > num_turns:
            print("No additional turns to run from branch point. Finalizing branch state.")
            output_manager.finalize_summary([])
            print(f"\n{'='*60}")
            print(f"BRANCH SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Results saved to: {new_run_dir}")
            return

        results = run_simulation(
            scenario,
            llm_client=None,
            num_turns=num_turns,
            output_manager=output_manager,
            start_turn=start_turn
        )

        # Finalize
        output_manager.finalize_summary(results)
        print(f"\n{'='*60}")
        print(f"BRANCH SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {new_run_dir}")
        return

    # Run logic starts here
    # Load scenario
    print(f"Loading scenario from {args.scenario}...")
    scenario = load_scenario(args.scenario)
    
    # Apply overrides
    if args.override:
        for override in args.override:
            if "=" not in override:
                print(f"Warning: Invalid override format '{override}', skipping. Use 'key=value'.")
                continue
            
            key_path, value = override.split("=", 1)
            keys = key_path.split(".")
            
            # Try to convert value to int/float/bool
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # Keep as string
            
            # Navigate to the correct object
            target = scenario.config
            for i, key in enumerate(keys[:-1]):
                if hasattr(target, key):
                    target = getattr(target, key)
                elif isinstance(target, dict) and key in target:
                    target = target[key]
                else:
                    print(f"Warning: Could not find key '{key}' in path '{key_path}', skipping override.")
                    target = None
                    break
            
            if target is not None:
                last_key = keys[-1]
                if hasattr(target, last_key):
                    setattr(target, last_key, value)
                    print(f"  → Overrode {key_path} = {value}")
                elif isinstance(target, dict):
                    target[last_key] = value
                    print(f"  → Overrode {key_path} = {value}")
                else:
                    # Special case for ScenarioConfig fields that might not be dicts but we want to set attr
                    try:
                        setattr(target, last_key, value)
                        print(f"  → Overrode {key_path} = {value}")
                    except Exception as e:
                        print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

    print(f"✓ Loaded: {scenario.config.name}")
    print(f"  Actors: {len(scenario.actors)}")
    print(f"  Metrics: {len(scenario.metrics.metrics)}")
    print(f"  Events: {len(scenario.events)}")

    # Validate scenario if requested
    if hasattr(args, 'validate') and args.validate:
        print("\nValidating scenario...")
        result = validate_scenario(args.scenario)

        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.errors:
            print("\n❌ Validation FAILED with the following errors:")
            for error in result.errors:
                print(f"  - {error}")
            print("\nFix the errors above before running the simulation.")
            return 1
        else:
            print("✅ Scenario validation passed!\n")

    if args.model:
        # Override all task models if --model is specified
        apply_model_override(scenario.config.llm, args.model)

    if args.dry_run:
        run_dry(scenario)
        return

    if not getattr(args, "skip_model_checks", False):
        if not run_model_preflight_checks(scenario):
            return 1

    # Run simulation
    print(f"\nRunning simulation: {scenario.config.name}")
    print(f"LLM Configuration:")
    print(f"  Events: {scenario.config.llm.events}")
    actors_cfg = scenario.config.llm.actors
    if isinstance(actors_cfg, dict):
        print(f"  Actors:")
        for actor_id, model in actors_cfg.items():
            print(f"    {actor_id}: {model}")
    else:
        print(f"  Actors: {actors_cfg} (all)")
    print(f"  Rules: {scenario.config.llm.rules}")
    print(f"  Metrics: {scenario.config.llm.metrics}")
    print(f"Turns: {args.turns or scenario.config.max_turns}")

    # Determine output directory (use parent dir if args.scenario is a .yaml file)
    output_base = resolve_output_base(args.scenario)

    output_manager = OutputManager(scenario, output_base)
    run_dir = output_manager.start_run()
    print(f"Output directory: {run_dir.name}\n")

    # Create progress tracker
    from .progress import ProgressTracker

    num_turns = args.turns or scenario.config.max_turns
    progress_tracker = ProgressTracker(
        total_turns=num_turns,
        actors=scenario.config.actor_ids,
        enabled=not args.no_progress,
        quiet=args.quiet,
        has_constitution=bool(getattr(scenario, "constitution", None)),
    )

    # run_simulation will create LLM clients and write incrementally
    results = run_simulation(
        scenario,
        llm_client=None,
        num_turns=args.turns,
        output_manager=output_manager,
        progress_tracker=progress_tracker
    )

    # Mark simulation as complete
    output_manager.finalize_summary(results)
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved to: {run_dir}")
    return 0


def run_dry(scenario):
    """Print prompts without calling LLM."""
    from .prompts import PromptBuilder

    builder = PromptBuilder(scenario)

    print("\n" + "=" * 60)
    print("DRY RUN - PROMPT PREVIEW")
    print("=" * 60)

    print("\n=== EVENTS PROMPT (Turn 1) ===")
    system, user = builder.build_events_prompt(1)
    print("\nSYSTEM PROMPT:")
    print(system[:500] + "..." if len(system) > 500 else system)
    print("\nUSER PROMPT:")
    print(user[:500] + "..." if len(user) > 500 else user)

    if scenario.actors:
        first_actor_id = list(scenario.actors.keys())[0]
        actor_name = scenario.actors[first_actor_id].name
        print(f"\n=== ACTOR PROMPT ({actor_name}, Turn 1) ===")
        system, user = builder.build_actor_prompt(first_actor_id, 1, [])
        print("\nSYSTEM PROMPT:")
        print(system[:500] + "..." if len(system) > 500 else system)
        print("\nUSER PROMPT:")
        print(user[:500] + "..." if len(user) > 500 else user)

    print("\n" + "=" * 60)
    print("Dry run complete. Use without --dry-run to execute.")
    print("=" * 60)


if __name__ == "__main__":
    raise SystemExit(main() or 0)
