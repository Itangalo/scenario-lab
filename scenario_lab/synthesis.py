"""Cross-run synthesis over an ensemble of completed runs.

This is the join between the two halves of batch analysis. ``analysis.py``
produces a structured reading of a single run; ``ensemble.py`` produces
deterministic statistics across every run without an LLM in the loop. Neither
alone answers "what does this world tend to do".

This module runs (or reuses) a per-run analysis for each completed run, then
makes one LLM call that synthesizes those readings against the ensemble
statistics. Python assembles, aggregates, and counts; the LLM judges. World
rules do not live here.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Callable, Optional

from .analysis import (
    _format_actor_catalog,
    _format_event_catalog,
    _format_metric_catalog,
    generate_run_analysis,
)
from .ensemble import _discover_completed_runs, analyze_ensemble
from .loader import load_scenario, parse_route
from .models import Scenario
from .prompts import PromptBuilder
from .providers.registry import ProviderRegistry
from .router import FallbackRouter


PROMPT_TOKEN_THRESHOLD = 80000

# Keys of a per-run analysis.json that carry cross-run signal. Metric tables
# and rule-evolution prose are deliberately excluded: the ensemble statistics
# cover the former exactly, and the latter rarely generalizes across runs.
_ANALYSIS_SECTIONS_BY_MODE: dict[str, tuple[str, ...]] = {
    "full": (
        "summary",
        "turning_points",
        "event_analysis",
        "actor_behavior_patterns",
        "observations_and_caveats",
    ),
    "condensed": ("summary", "turning_points", "observations_and_caveats"),
    "minimal": ("summary",),
}


@dataclass
class RunAnalysisEntry:
    """One run's structured analysis, plus how it was obtained."""

    run_dir: Path
    analysis: dict[str, Any]
    reused: bool


@dataclass
class AnalysisCoverage:
    """Outcome of the per-run analysis pass."""

    entries: list[RunAnalysisEntry] = field(default_factory=list)
    failures: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def reused(self) -> int:
        return sum(1 for entry in self.entries if entry.reused)

    @property
    def generated(self) -> int:
        return sum(1 for entry in self.entries if not entry.reused)


@dataclass
class SynthesisResult:
    """Rendered synthesis plus save metadata."""

    report: str
    output_path: Optional[Path]
    summary_text: str
    output_format: str
    prompt_context_mode: str
    num_runs: int
    coverage: AnalysisCoverage


def read_cached_analysis(run_dir: Path) -> Optional[dict[str, Any]]:
    """Return a run's saved structured analysis, or None if unusable.

    A completed run is immutable, so a readable ``analysis.json`` is always
    still valid for it. Anything unreadable or shaped wrong is treated as
    absent so the caller regenerates it.
    """
    path = run_dir / "analysis.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or "summary" not in data:
        return None
    return data


def ensure_run_analyses(
    run_dirs: list[Path],
    model: Optional[str] = None,
    refresh: bool = False,
    max_concurrency: int = 4,
    on_progress: Optional[Callable[[Path, str], None]] = None,
) -> AnalysisCoverage:
    """Make sure every run has a structured analysis, generating what is missing.

    Args:
        run_dirs: Completed run directories.
        model: Optional model override forwarded to per-run analysis.
        refresh: Regenerate even when a cached analysis exists.
        max_concurrency: Parallel analysis calls.
        on_progress: Called with (run_dir, status) as each run resolves, where
            status is one of "reused", "generated", or "failed".

    Returns:
        AnalysisCoverage with one entry per run that resolved, plus failures.
    """
    coverage = AnalysisCoverage()

    pending: list[Path] = []
    for run_dir in run_dirs:
        cached = None if refresh else read_cached_analysis(run_dir)
        if cached is not None:
            coverage.entries.append(RunAnalysisEntry(run_dir, cached, reused=True))
            if on_progress:
                on_progress(run_dir, "reused")
        else:
            pending.append(run_dir)

    if not pending:
        coverage.entries.sort(key=lambda entry: entry.run_dir.name)
        return coverage

    def _analyze(run_dir: Path) -> tuple[Path, Optional[dict[str, Any]], Optional[str]]:
        try:
            generate_run_analysis(run_dir, model=model, json_output=True)
        except Exception as exc:  # noqa: BLE001 - reported per run, never fatal
            return run_dir, None, str(exc)
        analysis = read_cached_analysis(run_dir)
        if analysis is None:
            return run_dir, None, "analysis completed but produced unreadable JSON"
        return run_dir, analysis, None

    workers = max(1, min(max_concurrency, len(pending)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for run_dir, analysis, error in pool.map(_analyze, pending):
            if analysis is None:
                coverage.failures.append((run_dir, error or "unknown error"))
                if on_progress:
                    on_progress(run_dir, "failed")
            else:
                coverage.entries.append(RunAnalysisEntry(run_dir, analysis, reused=False))
                if on_progress:
                    on_progress(run_dir, "generated")

    coverage.entries.sort(key=lambda entry: entry.run_dir.name)
    return coverage


def synthesize_scenario(
    scenario_dir: Path | str,
    max_runs: Optional[int] = None,
    model: Optional[str] = None,
    analysis_model: Optional[str] = None,
    refresh_analyses: bool = False,
    max_concurrency: int = 4,
    output_path: Optional[Path | str] = None,
    json_output: bool = False,
    no_save: bool = False,
    on_progress: Optional[Callable[[Path, str], None]] = None,
) -> SynthesisResult:
    """Synthesize every completed run of a scenario into one report."""
    scenario_path = Path(scenario_dir)
    run_dirs = _discover_completed_runs(scenario_path, max_runs)
    if not run_dirs:
        raise ValueError(f"No completed runs found in: {scenario_path / 'runs'}")

    scenario = load_scenario(scenario_path)
    ensemble = analyze_ensemble(scenario_path, max_runs=max_runs)

    coverage = ensure_run_analyses(
        run_dirs,
        model=analysis_model,
        refresh=refresh_analyses,
        max_concurrency=max_concurrency,
        on_progress=on_progress,
    )
    if not coverage.entries:
        raise ValueError(
            "No run analyses available to synthesize "
            f"({len(coverage.failures)} failed)"
        )

    builder = PromptBuilder(scenario)
    output_format = "json" if json_output else "markdown"
    context_mode = _choose_context_mode(builder, scenario, ensemble, coverage, output_format)
    context = _build_synthesis_context(scenario, ensemble, coverage, output_format, context_mode)
    system_prompt, user_prompt = builder.build_synthesis_prompt(context)

    llm_config = scenario.config.llm
    if model is not None:
        routes = [parse_route(model)]
    else:
        cfg_routes = llm_config.analysis
        routes = cfg_routes if isinstance(cfg_routes, list) else [cfg_routes]

    router = FallbackRouter(
        routes=routes,
        registry=ProviderRegistry(call_timeout_seconds=llm_config.call_timeout_seconds),
        temperature=0.3,
        max_tokens=llm_config.get_task_max_tokens("synthesis", default=llm_config.get_task_max_tokens("analysis")),
    )
    try:
        response = router.complete(system_prompt, user_prompt)
    finally:
        router.close()

    report = _normalize_report(response.content, json_output)
    destination = None
    if not no_save:
        destination = (
            Path(output_path)
            if output_path is not None
            else scenario_path / ("synthesis.json" if json_output else "synthesis.md")
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8")

    return SynthesisResult(
        report=report,
        output_path=destination,
        summary_text=_extract_summary_text(report, json_output),
        output_format=output_format,
        prompt_context_mode=context_mode,
        num_runs=len(coverage.entries),
        coverage=coverage,
    )


def _choose_context_mode(
    builder: PromptBuilder,
    scenario: Scenario,
    ensemble: dict[str, Any],
    coverage: AnalysisCoverage,
    output_format: str,
) -> str:
    """Pick a prompt density that fits comfortably in the model window."""
    for mode in ("full", "condensed", "minimal"):
        context = _build_synthesis_context(scenario, ensemble, coverage, output_format, mode)
        system_prompt, user_prompt = builder.build_synthesis_prompt(context)
        if _estimate_tokens(system_prompt) + _estimate_tokens(user_prompt) <= PROMPT_TOKEN_THRESHOLD:
            return mode
    return "minimal"


def _build_synthesis_context(
    scenario: Scenario,
    ensemble: dict[str, Any],
    coverage: AnalysisCoverage,
    output_format: str,
    context_mode: str,
) -> dict[str, Any]:
    """Build the render context for the synthesis prompt template."""
    config = scenario.config
    scenario_metadata = {
        "scenario_name": config.name,
        "scenario_description": config.description,
        "start_date": config.start_date,
        "time_scale": config.time_scale,
        "max_turns": config.max_turns,
        "runs_synthesized": len(coverage.entries),
        "runs_failed_analysis": len(coverage.failures),
    }

    return {
        "output_format": output_format,
        "context_mode": context_mode,
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
        "scenario_metadata_json": _to_json(scenario_metadata),
        "scenario_metrics_markdown": _format_metric_catalog(scenario),
        "scenario_events_markdown": _format_event_catalog(scenario),
        "scenario_actors_markdown": _format_actor_catalog(scenario),
        "ensemble_statistics_json": _to_json(_condense_ensemble(ensemble, context_mode)),
        "per_run_analyses_markdown": _format_per_run_analyses(coverage, context_mode),
    }


def _condense_ensemble(ensemble: dict[str, Any], context_mode: str) -> dict[str, Any]:
    """Trim ensemble statistics to what fits the chosen prompt density.

    Event statistics, divergence, and narrative diversity are small and always
    kept whole – they are the countable evidence the synthesis leans on. Metric
    trajectories grow with turns times metrics, so outside "full" they are
    reduced to first, middle, and last turn per metric.
    """
    condensed = dict(ensemble)
    if context_mode == "full":
        return condensed

    trajectories = ensemble.get("metric_trajectories")
    if not isinstance(trajectories, dict):
        return condensed

    trimmed: dict[str, Any] = {}
    for metric_id, turns_data in trajectories.items():
        if not isinstance(turns_data, dict) or not turns_data:
            continue
        turns = sorted(turns_data.keys(), key=lambda t: int(t))
        keep = {turns[0], turns[len(turns) // 2], turns[-1]}
        trimmed[metric_id] = {turn: turns_data[turn] for turn in turns if turn in keep}

    condensed["metric_trajectories"] = trimmed
    condensed["metric_trajectories_note"] = (
        "Trimmed to first, middle, and final turn per metric to fit the context window."
    )
    return condensed


def _format_per_run_analyses(coverage: AnalysisCoverage, context_mode: str) -> str:
    """Render each run's structured analysis into prompt-ready markdown."""
    sections = _ANALYSIS_SECTIONS_BY_MODE[context_mode]
    limit = {"full": 6000, "condensed": 2000, "minimal": 900}[context_mode]

    lines: list[str] = []
    for entry in coverage.entries:
        lines.append(f"### {entry.run_dir.name}")
        lines.append("")
        for key in sections:
            value = entry.analysis.get(key)
            if value in (None, "", [], {}):
                continue
            heading = key.replace("_", " ").title()
            lines.append(f"**{heading}**")
            lines.append("")
            lines.append(_truncate_text(_render_value(value), limit))
            lines.append("")

    if coverage.failures:
        lines.append("### Runs excluded")
        lines.append("")
        for run_dir, error in coverage.failures:
            lines.append(f"- {run_dir.name}: analysis failed ({error})")
        lines.append("")

    return "\n".join(lines).strip()


def _render_value(value: Any) -> str:
    """Render an analysis field as readable text rather than raw JSON."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        rendered = []
        for item in value:
            if isinstance(item, str):
                rendered.append(f"- {item.strip()}")
            else:
                rendered.append(f"- {_compact_json(item)}")
        return "\n".join(rendered)
    return _compact_json(value)


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _truncate_text(text: str, limit: int) -> str:
    stripped = text.strip()
    if not stripped:
        return "(Empty)"
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}\n\n[Truncated for synthesis context]"


def _estimate_tokens(text: str) -> int:
    """Rough tokenizer-free estimate for prompt sizing."""
    return math.ceil(len(text) / 4)


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
        return summary.strip() if isinstance(summary, str) else ""

    import re

    match = re.search(r"##\s*Summary\s*(.*?)(?=\n##\s|\Z)", report, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def _to_json(data: Any) -> str:
    """Dump data to readable JSON for prompt injection."""
    return json.dumps(data, indent=2, ensure_ascii=False)
