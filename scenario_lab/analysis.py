"""Post-run analysis for completed Scenario Lab runs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from pathlib import Path
from typing import Any, Optional

from .llm import LLMClient
from .loader import get_time_period, load_scenario
from .models import Scenario
from .prompts import PromptBuilder
from .resume import detect_last_turn, get_scenario_path_from_run, validate_run_directory


PROMPT_TOKEN_THRESHOLD = 80000


@dataclass
class RunTurnArtifacts:
    """Artifacts persisted for a single completed turn."""

    turn: int
    time_period: str
    events: Any
    actor_outputs: dict[str, str]
    metric_rules: str
    metric_rules_metadata: Optional[dict[str, Any]]
    world_state: str
    metrics: dict[str, Any]
    constitutional_check: Optional[dict[str, Any]]
    notepad: str
    historical_summary: str


@dataclass
class RunAnalysisBundle:
    """Complete analysis input assembled from a saved run."""

    run_dir: Path
    scenario_dir: Path
    scenario: Scenario
    config: dict[str, Any]
    summary: dict[str, Any]
    costs: Optional[dict[str, Any]]
    turns: list[RunTurnArtifacts]
    metric_overview: list[dict[str, Any]]


@dataclass
class AnalysisResult:
    """Rendered analysis plus save metadata."""

    report: str
    output_path: Optional[Path]
    summary_text: str
    output_format: str
    prompt_context_mode: str


def load_run_analysis_bundle(run_dir: Path | str) -> RunAnalysisBundle:
    """Load a completed run plus scenario definitions for analysis."""
    run_path = Path(run_dir)
    is_valid, errors = validate_run_directory(run_path)
    if not is_valid:
        raise ValueError(f"Invalid run directory: {', '.join(errors)}")

    scenario_dir = get_scenario_path_from_run(run_path)
    scenario = load_scenario(scenario_dir)

    config = _read_json_required(run_path / "config.json")
    summary = _read_json_required(run_path / "summary.json")
    costs = _read_json_optional(run_path / "costs.json")

    last_turn = detect_last_turn(run_path)
    if last_turn < 1:
        raise ValueError(f"No completed turns found in run directory: {run_path}")

    turns: list[RunTurnArtifacts] = []
    for turn in range(1, last_turn + 1):
        turn_dir = run_path / f"turn-{turn:02d}"
        if not turn_dir.exists():
            raise ValueError(f"Missing turn directory: {turn_dir}")

        turns.append(
            RunTurnArtifacts(
                turn=turn,
                time_period=get_time_period(
                    scenario.config.start_date,
                    turn,
                    scenario.config.time_scale,
                ),
                events=_read_json_optional(turn_dir / "1-events.json", default=[]),
                actor_outputs=_read_actor_outputs(turn_dir / "2-actors"),
                metric_rules=_read_text_optional(turn_dir / "3-metric-rules.md"),
                metric_rules_metadata=_read_json_optional(turn_dir / "3-metric-rules-metadata.json"),
                world_state=_read_text_optional(turn_dir / "4-world-state.md"),
                metrics=_read_json_optional(turn_dir / "4-metrics.json", default={}),
                constitutional_check=_read_json_optional(turn_dir / "5-constitutional-check.json"),
                notepad=_read_text_optional(turn_dir / "5-notepad.md"),
                historical_summary=_read_text_optional(turn_dir / "6-historical-summary.md"),
            )
        )

    metric_overview = _build_metric_overview(scenario, summary, turns)

    return RunAnalysisBundle(
        run_dir=run_path,
        scenario_dir=scenario_dir,
        scenario=scenario,
        config=config,
        summary=summary,
        costs=costs,
        turns=turns,
        metric_overview=metric_overview,
    )


def generate_run_analysis(
    run_dir: Path | str,
    model: Optional[str] = None,
    output_path: Optional[Path | str] = None,
    json_output: bool = False,
    no_save: bool = False,
) -> AnalysisResult:
    """Generate a markdown or JSON analysis report for a completed run."""
    bundle = load_run_analysis_bundle(run_dir)
    builder = PromptBuilder(bundle.scenario)
    output_format = "json" if json_output else "markdown"
    prompt_context_mode = _choose_context_mode(builder, bundle, output_format)

    analysis_context = _build_analysis_context(bundle, output_format, prompt_context_mode)
    system_prompt, user_prompt = builder.build_analysis_prompt(analysis_context)

    llm_config = bundle.scenario.config.llm
    client = LLMClient(
        model=model or llm_config.analysis,
        temperature=0.3,
        max_tokens=llm_config.get_task_max_tokens("analysis"),
    )

    try:
        response = client.complete(system_prompt, user_prompt)
    finally:
        client.close()

    report = _normalize_report(response.content, json_output)
    destination = None if no_save else _resolve_output_path(bundle.run_dir, output_path, json_output)
    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8")

    return AnalysisResult(
        report=report,
        output_path=destination,
        summary_text=_extract_summary_text(report, json_output),
        output_format=output_format,
        prompt_context_mode=prompt_context_mode,
    )


def _choose_context_mode(
    builder: PromptBuilder,
    bundle: RunAnalysisBundle,
    output_format: str,
) -> str:
    """Pick a prompt context density that fits comfortably in the model window."""
    for mode in ("full", "condensed", "minimal"):
        analysis_context = _build_analysis_context(bundle, output_format, mode)
        system_prompt, user_prompt = builder.build_analysis_prompt(analysis_context)
        if _estimate_tokens(system_prompt) + _estimate_tokens(user_prompt) <= PROMPT_TOKEN_THRESHOLD:
            return mode
    return "minimal"


def _build_analysis_context(
    bundle: RunAnalysisBundle,
    output_format: str,
    context_mode: str,
) -> dict[str, Any]:
    """Build the render context for the analysis prompt template."""
    run_metadata = {
        "scenario_name": bundle.scenario.config.name,
        "scenario_description": bundle.scenario.config.description,
        "run_dir": str(bundle.run_dir),
        "run_status": bundle.summary.get("status"),
        "completed_turns": len(bundle.turns),
        "time_scale": bundle.scenario.config.time_scale,
        "start_date": bundle.scenario.config.start_date,
        "occurred_events": bundle.summary.get("occurred_events", []),
        "costs": bundle.costs,
    }

    return {
        "output_format": output_format,
        "context_mode": context_mode,
        "run_metadata_json": _to_json(run_metadata),
        "metric_overview_json": _to_json(bundle.metric_overview),
        "scenario_metrics_markdown": _format_metric_catalog(bundle.scenario),
        "scenario_events_markdown": _format_event_catalog(bundle.scenario),
        "scenario_actors_markdown": _format_actor_catalog(bundle.scenario),
        "scenario_metric_rules_markdown": bundle.scenario.metric_rules.strip() or "(No metric rules defined.)",
        "scenario_constitution_markdown": (
            bundle.scenario.constitution.strip()
            if bundle.scenario.constitution and bundle.scenario.constitution.strip()
            else "(No constitution defined for this scenario.)"
        ),
        "turn_artifacts_markdown": _format_turn_artifacts(bundle, context_mode),
    }


def _build_metric_overview(
    scenario: Scenario,
    summary: dict[str, Any],
    turns: list[RunTurnArtifacts],
) -> list[dict[str, Any]]:
    """Compute metric start/end deltas for prompt grounding."""
    final_metrics = summary.get("final_metrics")
    if not isinstance(final_metrics, dict):
        final_metrics = turns[-1].metrics if turns else {}

    rows: list[dict[str, Any]] = []
    for metric_id, metric in scenario.metrics.metrics.items():
        start_value = metric.value
        end_value = final_metrics.get(metric_id, start_value)
        delta = end_value - start_value
        if delta > 0:
            direction = "up"
        elif delta < 0:
            direction = "down"
        else:
            direction = "flat"

        rows.append(
            {
                "metric_id": metric_id,
                "description": metric.description,
                "unit": metric.unit,
                "start_value": start_value,
                "end_value": end_value,
                "delta": delta,
                "direction": direction,
                "absolute_change": abs(delta),
            }
        )
    return rows


def _format_metric_catalog(scenario: Scenario) -> str:
    lines: list[str] = []
    for metric in scenario.metrics.metrics.values():
        lines.append(f"### {metric.id}")
        lines.append(f"- Description: {metric.description}")
        lines.append(f"- Start value: {metric.value}")
        lines.append(f"- Range: {metric.min_value} to {metric.max_value} {metric.unit}")
        if metric.reference_points:
            lines.append("- Reference points:")
            for value, description in sorted(metric.reference_points.items()):
                lines.append(f"  - {value}: {description}")
        lines.append("")
    return "\n".join(lines).strip() or "(No metrics defined.)"


def _format_event_catalog(scenario: Scenario) -> str:
    lines: list[str] = []
    for event in scenario.events:
        lines.append(f"### {event.id}")
        lines.append(f"- Description: {event.description}")
        lines.append(f"- Condition: {event.condition}")
        lines.append(f"- Probability: {event.probability}")
        lines.append(f"- Can repeat: {'yes' if event.can_repeat else 'no'}")
        lines.append("")
    return "\n".join(lines).strip() or "(No events defined.)"


def _format_actor_catalog(scenario: Scenario) -> str:
    lines: list[str] = []
    for actor in scenario.actors.values():
        lines.append(f"### {actor.name} ({actor.id})")
        lines.append(f"- Short description: {actor.short_description}")
        lines.append(f"- Long description: {actor.long_description}")
        if actor.initial_goals:
            lines.append("- Initial goals:")
            for goal in actor.initial_goals:
                lines.append(f"  - {goal}")
        lines.append("")
    return "\n".join(lines).strip() or "(No actors defined.)"


def _format_turn_artifacts(bundle: RunAnalysisBundle, context_mode: str) -> str:
    """Render saved per-turn artifacts into prompt-ready markdown."""
    lines: list[str] = []
    for turn in bundle.turns:
        lines.append(f"## Turn {turn.turn} ({turn.time_period})")
        lines.append("")
        lines.append("### Triggered or persisted events")
        lines.append("```json")
        lines.append(_to_json(turn.events))
        lines.append("```")
        lines.append("")
        lines.append("### Metrics")
        lines.append("```json")
        lines.append(_to_json(turn.metrics))
        lines.append("```")
        lines.append("")

        if turn.metric_rules_metadata:
            lines.append("### Metric rules metadata")
            lines.append("```json")
            lines.append(_to_json(turn.metric_rules_metadata))
            lines.append("```")
            lines.append("")

        lines.append("### Metric rules")
        lines.append(_truncate_text(turn.metric_rules, _limit_for("rules", context_mode)))
        lines.append("")

        lines.append("### World state")
        lines.append(_truncate_text(turn.world_state, _limit_for("world_state", context_mode)))
        lines.append("")

        if turn.constitutional_check is not None:
            lines.append("### Constitutional check")
            lines.append("```json")
            lines.append(_to_json(turn.constitutional_check))
            lines.append("```")
            lines.append("")

        lines.append("### Game master notes")
        lines.append(_truncate_text(turn.notepad, _limit_for("notepad", context_mode)))
        lines.append("")

        if turn.historical_summary.strip():
            lines.append("### Historical summary")
            lines.append(_truncate_text(turn.historical_summary, _limit_for("historical_summary", context_mode)))
            lines.append("")

        lines.append("### Actor outputs")
        for actor_id, actor_output in turn.actor_outputs.items():
            actor_name = bundle.scenario.actors.get(actor_id).name if actor_id in bundle.scenario.actors else actor_id
            lines.append(f"#### {actor_name} ({actor_id})")
            lines.append(_truncate_text(actor_output, _limit_for("actor_output", context_mode)))
            lines.append("")

    return "\n".join(lines).strip()


def _limit_for(section: str, context_mode: str) -> int:
    """Character caps used by prompt condensation."""
    limits = {
        "full": {
            "rules": 12000,
            "world_state": 16000,
            "notepad": 6000,
            "historical_summary": 6000,
            "actor_output": 5000,
        },
        "condensed": {
            "rules": 2500,
            "world_state": 3000,
            "notepad": 1200,
            "historical_summary": 1200,
            "actor_output": 1200,
        },
        "minimal": {
            "rules": 1200,
            "world_state": 1500,
            "notepad": 700,
            "historical_summary": 700,
            "actor_output": 700,
        },
    }
    return limits[context_mode][section]


def _estimate_tokens(text: str) -> int:
    """Rough tokenizer-free estimate for prompt sizing."""
    return math.ceil(len(text) / 4)


def _truncate_text(text: str, limit: int) -> str:
    """Truncate long artifact text while preserving scanability."""
    stripped = text.strip()
    if not stripped:
        return "(Empty)"
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}\n\n[Truncated for analysis context]"


def _normalize_report(content: str, json_output: bool) -> str:
    """Normalize raw LLM output into a persisted report string."""
    if not json_output:
        return content.strip() + "\n"

    from .llm import LLMResponse

    parsed = LLMResponse(content=content, raw_response={}).extract_json()
    return json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"


def _extract_summary_text(report: str, json_output: bool) -> str:
    """Extract a short top-line summary for CLI output."""
    if json_output:
        try:
            payload = json.loads(report)
        except json.JSONDecodeError:
            return ""
        summary = payload.get("summary", "")
        if isinstance(summary, str):
            return summary.strip()
        return ""

    match = re.search(r"##\s*Summary\s*(.*?)(?=\n##\s|\Z)", report, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    summary = match.group(1).strip()
    return " ".join(summary.split())


def _resolve_output_path(run_dir: Path, output_path: Optional[Path | str], json_output: bool) -> Path:
    """Pick the final path for the saved report."""
    if output_path is not None:
        return Path(output_path)
    return run_dir / ("analysis.json" if json_output else "analysis.md")


def _read_actor_outputs(actors_dir: Path) -> dict[str, str]:
    """Read all actor output markdown files for a turn."""
    if not actors_dir.exists():
        return {}
    outputs: dict[str, str] = {}
    for path in sorted(actors_dir.glob("*.md")):
        outputs[path.stem] = path.read_text(encoding="utf-8")
    return outputs


def _read_json_required(path: Path) -> dict[str, Any]:
    """Read a required JSON file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing required JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _read_json_optional(path: Path, default: Any = None) -> Any:
    """Read an optional JSON file."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _read_text_optional(path: Path, default: str = "") -> str:
    """Read optional text content."""
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def _to_json(data: Any) -> str:
    """Dump data to readable JSON for prompt injection."""
    return json.dumps(data, indent=2, ensure_ascii=False)
