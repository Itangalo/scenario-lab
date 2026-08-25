"""Compact one-page overview of a scenario definition.

Used as the review step of the scenario-authoring workflow: after drafting or
editing scenario files, ``describe`` shows the human what exists at a glance
without reading every file. Reads only the scenario definition – no API calls.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union

from .loader import load_scenario
from .models import ModelRoute, Scenario


def _route_str(value: Union[ModelRoute, list, dict]) -> str:
    """Render a route value (single, fallback list, or per-actor dict)."""
    if isinstance(value, ModelRoute):
        return str(value)
    if isinstance(value, list):
        return " -> ".join(str(r) for r in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_route_str(v)}" for k, v in value.items())
    return str(value)


def _count_rules(metric_rules: str) -> int:
    """Count numbered or bulleted rule entries in the rules markdown."""
    return len(re.findall(r"^\s*(?:\d+\.|[-*])\s+\S", metric_rules, flags=re.MULTILINE))


def _count_constraints(constitution: str) -> int:
    return len(re.findall(r"^\s*(?:\d+\.|[-*])\s+\S", constitution, flags=re.MULTILINE))


def describe_scenario(
    scenario_path: Path,
    initial_state: Optional[Path] = None,
) -> dict[str, Any]:
    """Build a structured overview of a scenario directory.

    Args:
        scenario_path: Path to the scenario directory.
        initial_state: Optional starting-state draw to apply first, so the
            overview shows the world a specific run would actually begin from.

    Returns:
        Dict suitable for JSON export or markdown rendering.
    """
    scenario: Scenario = load_scenario(scenario_path, initial_state=initial_state)
    scenario_dir = Path(scenario_path)
    config = scenario.config

    actors = [
        {
            "id": actor.id,
            "name": actor.name,
            "short_description": actor.short_description,
            "statements": [
                {"id": s.id, "tier": s.tier, "text": s.text}
                for s in actor.initial_statements
            ],
        }
        for actor in scenario.actors.values()
    ]

    metrics = [
        {
            "id": metric.id,
            "start_value": metric.value,
            "min": metric.min_value,
            "max": metric.max_value,
            "unit": metric.unit,
            "reference_points": len(metric.reference_points),
            "description": metric.description,
        }
        for metric in scenario.metrics.metrics.values()
    ]

    events = [
        {
            "id": event.id,
            "condition": event.condition,
            "probability": event.probability,
            "can_repeat": event.can_repeat,
            "description": event.description,
        }
        for event in scenario.events
    ]

    runs_dir = scenario_dir / "runs"
    completed_runs = 0
    total_runs = 0
    if runs_dir.is_dir():
        import json as _json

        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
                continue
            total_runs += 1
            try:
                summary = _json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
                if summary.get("status") == "completed":
                    completed_runs += 1
            except (OSError, ValueError):
                continue

    variants_dir = scenario_dir / "variants"
    variants = (
        sorted(p.name for p in variants_dir.iterdir() if p.suffix in {".yaml", ".yml"})
        if variants_dir.is_dir()
        else []
    )

    background_dir = scenario_dir / "background"
    background_files = (
        sorted(
            str(p.relative_to(background_dir))
            for p in background_dir.rglob("*.md")
        )
        if background_dir.is_dir()
        else []
    )

    llm = config.llm
    return {
        "name": config.name,
        "description": config.description,
        "path": str(scenario_dir),
        "time": {
            "start_date": config.start_date,
            "time_scale": config.time_scale,
            "max_turns": config.max_turns,
        },
        "output_language": config.output_language,
        "research_questions": [
            {
                "id": rq.id,
                "question": rq.question,
                "metrics": list(rq.metrics),
                "events": list(rq.events),
                "notes": rq.notes,
            }
            for rq in config.research_questions
        ],
        "actors": actors,
        "metrics": metrics,
        "events": events,
        "metric_rules_count": _count_rules(scenario.metric_rules),
        "constitution": (
            {"present": True, "constraints": _count_constraints(scenario.constitution)}
            if scenario.constitution
            else {"present": False}
        ),
        "llm": {
            "events": _route_str(llm.events),
            "actors": _route_str(llm.actors),
            "rules": _route_str(llm.rules),
            "metrics": _route_str(llm.metrics),
            "summary": _route_str(llm.summary),
            "referee": _route_str(llm.referee),
            "temperature": llm.temperature,
            "max_tokens": llm.max_tokens,
            "structured_outputs": llm.structured_outputs,
            "probability_samples": llm.probability_samples,
            "call_timeout_seconds": llm.call_timeout_seconds,
            "model_limits": {
                key: {
                    field: value
                    for field, value in (
                        ("max_tokens", limits.max_tokens),
                        ("call_timeout_seconds", limits.call_timeout_seconds),
                    )
                    if value is not None
                }
                for key, limits in llm.model_limits.items()
            },
        },
        "emergent_events": {
            "enabled": config.emergent_events.enabled,
            "max_per_turn": config.emergent_events.max_per_turn,
            "max_probability": config.emergent_events.max_probability,
        },
        "rule_evolution": {
            "freeze_until_turn": config.rule_evolution.freeze_until_turn,
            "max_changes_per_turn": config.rule_evolution.max_changes_per_turn,
        },
        "custom_system_prompts": sorted(scenario.custom_system_prompts),
        "custom_user_prompts": sorted(scenario.custom_user_prompts),
        "background_files": background_files,
        "variants": variants,
        "runs": {"total": total_runs, "completed": completed_runs},
    }


def _truncate(text: str, limit: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def format_describe_report(overview: dict[str, Any]) -> str:
    """Render a scenario overview as a one-page markdown report."""
    lines: list[str] = []
    lines.append(f"# Scenario Overview: {overview['name']}")
    lines.append("")
    lines.append(overview["description"])
    lines.append("")
    time = overview["time"]
    lines.append(
        f"**Time:** starts {time['start_date']}, {time['time_scale']}, "
        f"max {time['max_turns']} turns"
        + (f" · **Language:** {overview['output_language']}" if overview["output_language"] else "")
    )
    lines.append("")

    research_questions = overview.get("research_questions") or []
    if research_questions:
        lines.append(f"## Research Questions ({len(research_questions)})")
        lines.append("")
        for rq in research_questions:
            lines.append(f"- **{rq['id']}** – {rq['question']}")
            grounding = []
            if rq["metrics"]:
                grounding.append("metrics: " + ", ".join(f"`{m}`" for m in rq["metrics"]))
            if rq["events"]:
                grounding.append("events: " + ", ".join(f"`{e}`" for e in rq["events"]))
            if grounding:
                lines.append(f"  - {' · '.join(grounding)}")
        lines.append("")

    lines.append(f"## Actors ({len(overview['actors'])})")
    lines.append("")
    for actor in overview["actors"]:
        lines.append(f"- **{actor['name']}** (`{actor['id']}`) – {_truncate(actor['short_description'])}")
        for stmt in actor["statements"][:3]:
            lines.append(f"  - [{stmt['tier']}] {_truncate(stmt['text'])}")
        if len(actor["statements"]) > 3:
            lines.append(f"  - … and {len(actor['statements']) - 3} more statement(s)")
    lines.append("")

    lines.append(f"## Metrics ({len(overview['metrics'])})")
    lines.append("")
    lines.append("| metric | start | range | unit | ref points |")
    lines.append("|--------|-------|-------|------|------------|")
    for metric in overview["metrics"]:
        lines.append(
            f"| {metric['id']} | {metric['start_value']} | "
            f"{metric['min']}–{metric['max']} | {metric['unit']} | "
            f"{metric['reference_points']} |"
        )
    lines.append("")

    lines.append(f"## Events ({len(overview['events'])})")
    lines.append("")
    for event in overview["events"]:
        repeat = "repeatable" if event["can_repeat"] else "one-off"
        lines.append(f"- **{event['id']}** ({repeat}, p: {_truncate(str(event['probability']), 40)})")
        lines.append(f"  - Condition: {_truncate(event['condition'])}")
    lines.append("")

    constitution = overview["constitution"]
    lines.append("## World Model")
    lines.append("")
    lines.append(f"- Metric rules: {overview['metric_rules_count']} rule(s) at start")
    if constitution["present"]:
        lines.append(f"- Constitution: yes ({constitution['constraints']} constraint(s))")
    else:
        lines.append("- Constitution: none")
    emergent = overview["emergent_events"]
    if emergent["enabled"]:
        lines.append(
            f"- Emergent events: enabled (max {emergent['max_per_turn']}/turn, "
            f"probability cap {emergent['max_probability']})"
        )
    else:
        lines.append("- Emergent events: disabled")
    rule_evo = overview["rule_evolution"]
    lines.append(
        f"- Rule evolution: frozen through turn {rule_evo['freeze_until_turn']}, "
        f"max {rule_evo['max_changes_per_turn']} change(s)/turn"
    )
    lines.append("")

    llm = overview["llm"]
    lines.append("## LLM Configuration")
    lines.append("")
    for task in ("events", "actors", "rules", "metrics", "summary", "referee"):
        lines.append(f"- {task}: {llm[task]}")
    lines.append(
        f"- temperature {llm['temperature']}, max_tokens {llm['max_tokens']}, "
        f"structured_outputs {llm['structured_outputs']}, "
        f"probability_samples {llm['probability_samples']}, "
        f"call_timeout_seconds {llm['call_timeout_seconds']}"
    )
    if llm["model_limits"]:
        for key, limits in llm["model_limits"].items():
            parts = [f"{field} {value}" for field, value in limits.items()]
            lines.append(f"- model limits {key}: {', '.join(parts)}")
    lines.append("")

    lines.append("## Files and Runs")
    lines.append("")
    lines.append(f"- Background files: {len(overview['background_files'])}")
    if overview["custom_system_prompts"] or overview["custom_user_prompts"]:
        overrides = sorted(
            set(overview["custom_system_prompts"]) | set(overview["custom_user_prompts"])
        )
        lines.append(f"- Custom prompt overrides: {', '.join(overrides)}")
    else:
        lines.append("- Custom prompt overrides: none (default templates)")
    if overview["variants"]:
        lines.append(f"- Variants: {', '.join(overview['variants'])}")
    runs = overview["runs"]
    lines.append(f"- Runs: {runs['completed']} completed of {runs['total']} total")
    lines.append("")

    return "\n".join(lines)
