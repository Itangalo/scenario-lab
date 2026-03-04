"""Heuristic model hygiene checks for configured LLMs."""

from dataclasses import dataclass, field
from datetime import date
import os
from pathlib import Path
from typing import Iterable, Optional, Union
import re

import httpx
import yaml

from .loader import load_config
from .models import LLMConfig


DEFAULT_SNAPSHOT_MAX_AGE_DAYS = 180
MODELS_API_URL = "https://openrouter.ai/api/v1/models"
USER_MODELS_API_URL = "https://openrouter.ai/api/v1/models/user"
DEFAULT_POLICY_PATH = Path(__file__).parent.parent / "model-policy.yaml"
LEGACY_FAMILY_PATTERNS = {
    r"(^|[^a-z0-9])gpt-3\.5([^a-z0-9]|$)": "legacy GPT-3.5 family",
    r"(^|[^a-z0-9])claude-2([^a-z0-9]|$)": "legacy Claude 2 family",
    r"(^|[^a-z0-9])claude-instant([^a-z0-9]|$)": "legacy Claude Instant family",
    r"(^|[^a-z0-9])llama-2([^a-z0-9]|$)": "legacy Llama 2 family",
    r"(^|[^a-z0-9])palm([^a-z0-9]|$)": "legacy PaLM family",
}


@dataclass
class ModelAuditFinding:
    """A single model hygiene finding."""

    scope: str
    task: str
    model: str
    message: str


@dataclass
class ModelAuditReport:
    """Aggregate report for one or more scenario configs."""

    root: str
    checked_configs: int
    findings: list[ModelAuditFinding]

    def to_dict(self) -> dict:
        """Convert to JSON-serializable structure."""
        return {
            "root": self.root,
            "checked_configs": self.checked_configs,
            "findings": [
                {
                    "scope": finding.scope,
                    "task": finding.task,
                    "model": finding.model,
                    "message": finding.message,
                }
                for finding in self.findings
            ],
        }


@dataclass
class ModelConfigLocation:
    """Address of a concrete model string within LLMConfig."""

    task: str
    path: tuple[Union[str, int], ...]
    model: str


@dataclass
class ModelRecommendation:
    """Recommended replacement for a stale model."""

    task: str
    current_model: str
    suggested_model: str
    reason: str


@dataclass
class ModelPolicy:
    """Repository-local policy for model hygiene checks."""

    max_snapshot_age_days: int = DEFAULT_SNAPSHOT_MAX_AGE_DAYS
    allowed_patterns: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)


def load_model_policy(policy_path: Optional[Union[str, Path]] = None) -> ModelPolicy:
    """Load model policy from disk, falling back to defaults if absent or invalid."""
    path = Path(policy_path) if policy_path is not None else DEFAULT_POLICY_PATH
    if not path.exists():
        return ModelPolicy()

    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return ModelPolicy()

    if not isinstance(raw_data, dict):
        return ModelPolicy()

    max_snapshot_age_days = raw_data.get("max_snapshot_age_days", DEFAULT_SNAPSHOT_MAX_AGE_DAYS)
    if not isinstance(max_snapshot_age_days, int) or max_snapshot_age_days < 1:
        max_snapshot_age_days = DEFAULT_SNAPSHOT_MAX_AGE_DAYS

    allowed_patterns = raw_data.get("allowed_patterns", [])
    if not isinstance(allowed_patterns, list):
        allowed_patterns = []
    allowed_patterns = [pattern for pattern in allowed_patterns if isinstance(pattern, str)]

    blocked_patterns = raw_data.get("blocked_patterns", [])
    if not isinstance(blocked_patterns, list):
        blocked_patterns = []
    blocked_patterns = [pattern for pattern in blocked_patterns if isinstance(pattern, str)]

    return ModelPolicy(
        max_snapshot_age_days=max_snapshot_age_days,
        allowed_patterns=allowed_patterns,
        blocked_patterns=blocked_patterns,
    )


def evaluate_model_hygiene(
    model: str,
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> list[str]:
    """Return heuristic warnings for model names that look stale or risky.

    This intentionally uses local heuristics rather than online lookups:
    - clearly legacy model families
    - dated snapshot models older than the configured threshold
    - optional repo allow/deny policy patterns
    """
    warnings = []
    today = today or date.today()
    policy = policy or load_model_policy()
    lower_model = model.lower()

    for pattern, label in LEGACY_FAMILY_PATTERNS.items():
        if re.search(pattern, lower_model):
            warnings.append(f"appears to use the {label}; review whether a newer family should replace it")
            break

    snapshot_date = extract_model_snapshot_date(model)
    if snapshot_date is not None:
        age_days = (today - snapshot_date).days
        if age_days > policy.max_snapshot_age_days:
            warnings.append(
                f"uses a dated snapshot from {snapshot_date.isoformat()} ({age_days} days old); review whether a fresher snapshot is available"
            )

    if policy.allowed_patterns and not any(
        re.search(pattern, model, re.IGNORECASE) for pattern in policy.allowed_patterns
    ):
        warnings.append("falls outside the repository allowlist in model-policy.yaml")

    for pattern in policy.blocked_patterns:
        if re.search(pattern, model, re.IGNORECASE):
            warnings.append(
                f"matches a blocked pattern from model-policy.yaml ('{pattern}')"
            )
            break

    return warnings


def extract_model_snapshot_date(model: str) -> Optional[date]:
    """Extract an embedded YYYY-MM[-DD] or YYYYMMDD snapshot date if present."""
    patterns = [
        r"(20\d{2})[-_](\d{2})[-_](\d{2})",
        r"(20\d{2})(\d{2})(\d{2})",
        r"(20\d{2})[-_](\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, model)
        if not match:
            continue

        parts = [int(group) for group in match.groups()]
        try:
            if len(parts) == 3:
                return date(parts[0], parts[1], parts[2])
            return date(parts[0], parts[1], 1)
        except ValueError:
            continue

    return None


def collect_model_hygiene_warnings(
    llm_config: LLMConfig,
    scope: str = "scenario",
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> list[str]:
    """Collect human-readable model hygiene warnings for one scenario config."""
    warnings = []
    policy = policy or load_model_policy()
    for task, model in iter_configured_models(llm_config):
        for message in evaluate_model_hygiene(model, today=today, policy=policy):
            warnings.append(f"{scope}: Task '{task}' model '{model}' {message}")
    return warnings


def find_stale_model_locations(
    llm_config: LLMConfig,
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> list[ModelConfigLocation]:
    """Return concrete model config locations that trigger hygiene warnings."""
    locations = []
    policy = policy or load_model_policy()
    for location in iter_model_locations(llm_config):
        if evaluate_model_hygiene(location.model, today=today, policy=policy):
            locations.append(location)
    return locations


def audit_model_configs(
    path: Union[str, Path],
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> ModelAuditReport:
    """Audit one scenario config or a directory tree of scenario configs."""
    path = Path(path)
    config_paths = list(discover_config_paths(path))
    findings: list[ModelAuditFinding] = []
    policy = policy or load_model_policy()

    for config_path in config_paths:
        config = load_config(config_path)
        for task, model in iter_configured_models(config.llm):
            for message in evaluate_model_hygiene(model, today=today, policy=policy):
                findings.append(
                    ModelAuditFinding(
                        scope=str(config_path),
                        task=task,
                        model=model,
                        message=message,
                    )
                )

    return ModelAuditReport(
        root=str(path),
        checked_configs=len(config_paths),
        findings=findings,
    )


def recommend_replacements(
    llm_config: LLMConfig,
    api_key: Optional[str] = None,
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> list[ModelRecommendation]:
    """Suggest replacements for stale models using OpenRouter's models catalog."""
    policy = policy or load_model_policy()
    locations = find_stale_model_locations(llm_config, today=today, policy=policy)
    if not locations:
        return []

    catalog = fetch_openrouter_models(api_key=api_key)
    if not catalog:
        return []

    catalog_by_id = {
        model["id"]: model
        for model in catalog
        if isinstance(model, dict) and isinstance(model.get("id"), str)
    }

    recommendations = []
    for location in locations:
        suggestion = choose_replacement_model(
            location.model,
            catalog,
            catalog_by_id,
            today=today,
            policy=policy,
        )
        if suggestion is None:
            continue
        recommendations.append(
            ModelRecommendation(
                task=location.task,
                current_model=location.model,
                suggested_model=suggestion["id"],
                reason=suggestion["reason"],
            )
        )

    return recommendations


def apply_recommendations(llm_config: LLMConfig, recommendations: list[ModelRecommendation]) -> int:
    """Apply suggested replacements directly to the loaded config."""
    locations_by_key = {
        (location.task, location.model): location
        for location in iter_model_locations(llm_config)
    }

    applied = 0
    for recommendation in recommendations:
        key = (recommendation.task, recommendation.current_model)
        location = locations_by_key.get(key)
        if location is None:
            continue
        set_model_at_path(llm_config, location.path, recommendation.suggested_model)
        applied += 1

    return applied


def format_model_audit_report(report: ModelAuditReport) -> str:
    """Format a text report for CLI display."""
    lines = [
        "=" * 60,
        "MODEL AUDIT",
        "=" * 60,
        f"Root: {report.root}",
        f"Scenario configs checked: {report.checked_configs}",
    ]

    if not report.findings:
        lines.append("")
        lines.append("No model hygiene warnings found.")
        lines.append("=" * 60)
        return "\n".join(lines)

    lines.append("")
    lines.append("Warnings:")
    for finding in report.findings:
        lines.append(
            f"- {finding.scope} | {finding.task} | {finding.model} | {finding.message}"
        )

    lines.append("")
    lines.append(f"Total warnings: {len(report.findings)}")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_recommendations(recommendations: list[ModelRecommendation]) -> str:
    """Format replacement suggestions for CLI display."""
    if not recommendations:
        return "No OpenRouter replacement suggestions available."

    lines = ["Suggested replacements from OpenRouter:"]
    for recommendation in recommendations:
        lines.append(
            f"- {recommendation.task}: {recommendation.current_model} -> "
            f"{recommendation.suggested_model} ({recommendation.reason})"
        )
    return "\n".join(lines)


def discover_config_paths(path: Path) -> Iterable[Path]:
    """Discover scenario.yaml files from a file or directory."""
    if path.is_file():
        yield path
        return

    if (path / "scenario.yaml").exists():
        yield path / "scenario.yaml"
        return

    for config_path in sorted(path.rglob("scenario.yaml")):
        if "runs" in config_path.parts:
            continue
        yield config_path


def iter_model_locations(llm_config: LLMConfig) -> Iterable[ModelConfigLocation]:
    """Flatten all configured models into concrete locations."""
    for task in ("events", "rules", "metrics", "summary", "referee"):
        yield from _yield_task_locations(task, (task,), getattr(llm_config, task))

    actors = llm_config.actors
    if isinstance(actors, dict):
        for actor_id, value in actors.items():
            yield from _yield_task_locations(f"actors.{actor_id}", ("actors", actor_id), value)
    else:
        yield from _yield_task_locations("actors", ("actors",), actors)


def iter_configured_models(llm_config: LLMConfig) -> Iterable[tuple[str, str]]:
    """Flatten all configured models into task/model pairs."""
    for location in iter_model_locations(llm_config):
        yield location.task, location.model


def fetch_openrouter_models(api_key: Optional[str] = None) -> list[dict]:
    """Fetch model metadata from OpenRouter's documented models endpoint."""
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    headers = {}
    url = MODELS_API_URL
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        url = USER_MODELS_API_URL

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return []

    models = data.get("data", [])
    return models if isinstance(models, list) else []


def choose_replacement_model(
    current_model: str,
    catalog: list[dict],
    catalog_by_id: dict[str, dict],
    today: Optional[date] = None,
    policy: Optional[ModelPolicy] = None,
) -> Optional[dict]:
    """Choose a replacement model based on modality match, recency, and price."""
    today = today or date.today()
    policy = policy or load_model_policy()
    current_meta = catalog_by_id.get(current_model, {})

    required_inputs = set(_get_nested(current_meta, "architecture", "input_modalities") or ["text"])
    required_outputs = set(_get_nested(current_meta, "architecture", "output_modalities") or ["text"])
    current_context = int(current_meta.get("context_length") or 0)
    current_created = _created_timestamp(current_meta)
    current_cost = _blended_token_cost(current_meta)

    candidates = []
    for candidate in catalog:
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or candidate_id == current_model:
            continue

        if evaluate_model_hygiene(candidate_id, today=today, policy=policy):
            continue

        candidate_inputs = set(_get_nested(candidate, "architecture", "input_modalities") or ["text"])
        candidate_outputs = set(_get_nested(candidate, "architecture", "output_modalities") or ["text"])
        if not required_inputs.issubset(candidate_inputs):
            continue
        if not required_outputs.issubset(candidate_outputs):
            continue

        context_length = int(candidate.get("context_length") or 0)
        context_ok = context_length >= current_context if current_context else True
        created = _created_timestamp(candidate)
        if created and (today - date.fromtimestamp(created)).days > policy.max_snapshot_age_days:
            continue
        blended_cost = _blended_token_cost(candidate)
        cheaper_than_current = blended_cost < current_cost if current_cost != float("inf") else False
        newer_than_current = created > current_created if current_created else False

        candidates.append(
            {
                "context_ok": context_ok,
                "created": created,
                "cost": blended_cost,
                "cheaper_than_current": cheaper_than_current,
                "newer_than_current": newer_than_current,
                "candidate": candidate,
            }
        )

    if not candidates:
        return None

    best = _select_best_candidate(candidates)
    if best is None:
        return None
    candidate = best["candidate"]

    reason_parts = []
    if best["newer_than_current"] and best["cheaper_than_current"]:
        reason_parts.append("newer and cheaper than the current model")
    elif best["cheaper_than_current"]:
        reason_parts.append("cheaper than the current model")
    elif best["newer_than_current"]:
        reason_parts.append("newer than the current model")
    else:
        reason_parts.append("best fresh modality-compatible match")
    if current_context:
        if int(candidate.get("context_length") or 0) >= current_context:
            reason_parts.append("meets or exceeds current context length")
        else:
            reason_parts.append("closest stable modality-compatible match")
    reason_parts.append("filtered by OpenRouter recency and ranked by lower published token price")

    return {"id": candidate["id"], "reason": ", ".join(reason_parts)}


def set_model_at_path(llm_config: LLMConfig, path: tuple[Union[str, int], ...], new_model: str) -> None:
    """Replace a specific model string within LLMConfig."""
    current = llm_config
    for part in path[:-1]:
        if isinstance(part, str):
            current = getattr(current, part) if not isinstance(current, dict) else current[part]
        else:
            current = current[part]

    last = path[-1]
    if isinstance(last, str):
        if isinstance(current, dict):
            current[last] = new_model
        else:
            setattr(current, last, new_model)
    else:
        current[last] = new_model


def _yield_task_locations(
    task: str,
    path_prefix: tuple[Union[str, int], ...],
    value: Union[str, list[str]],
) -> Iterable[ModelConfigLocation]:
    """Yield concrete config locations for a task."""
    if isinstance(value, str):
        yield ModelConfigLocation(task=task, path=path_prefix, model=value)
        return

    for index, model in enumerate(value):
        yield ModelConfigLocation(
            task=f"{task}[{index + 1}]",
            path=path_prefix + (index,),
            model=model,
        )


def _get_nested(obj: dict, *keys: str):
    """Get a nested dict value safely."""
    current = obj
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _blended_token_cost(model: dict) -> float:
    """Estimate relative token cost from published prompt + completion price."""
    pricing = model.get("pricing")
    if isinstance(pricing, list):
        pricing = pricing[0] if pricing else {}
    if not isinstance(pricing, dict):
        return float("inf")

    try:
        prompt_cost = float(pricing.get("prompt", "inf"))
        completion_cost = float(pricing.get("completion", "inf"))
    except (TypeError, ValueError):
        return float("inf")

    return prompt_cost + completion_cost


def _created_timestamp(model: dict) -> int:
    """Return the model's created timestamp as an integer, or 0 if missing."""
    try:
        return int(model.get("created") or 0)
    except (TypeError, ValueError, AttributeError):
        return 0


def _select_best_candidate(candidates: list[dict]) -> Optional[dict]:
    """Select the best candidate, preferring both newer and cheaper when available."""
    for predicate in (
        lambda c: c["context_ok"] and c["newer_than_current"] and c["cheaper_than_current"],
        lambda c: c["context_ok"] and c["cheaper_than_current"],
        lambda c: c["context_ok"] and c["newer_than_current"],
        lambda c: c["context_ok"],
        lambda c: c["newer_than_current"] and c["cheaper_than_current"],
        lambda c: c["cheaper_than_current"],
        lambda c: c["newer_than_current"],
        lambda c: True,
    ):
        subset = [candidate for candidate in candidates if predicate(candidate)]
        if subset:
            subset.sort(
                key=lambda item: (
                    item["cost"] == float("inf"),
                    item["cost"],
                    -item["created"],
                )
            )
            return subset[0]

    return None
