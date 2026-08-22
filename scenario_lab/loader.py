"""Scenario loading from disk."""

import calendar
import json
import re
import yaml
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Union, Optional, List
from .models import (
    ModelRoute,
    Scenario,
    ScenarioConfig,
    LLMConfig,
    EmergentEventsConfig,
    RuleEvolutionConfig,
    ConstitutionalEnforcementConfig,
    LoggingConfig,
    Metric,
    Metrics,
    Event,
    Actor,
    InitialState,
    ResearchQuestion,
    WorldState,
)


def _parse_routes_field(value: object) -> "ModelRoute | list[ModelRoute]":
    """Return a single ModelRoute for a single value, or list for a list value."""
    if isinstance(value, list):
        return [parse_route(item) for item in value]
    return parse_route(value)


def _route_to_yaml_str(route: "ModelRoute") -> str:
    return str(route)  # "provider:model"


def _routes_to_yaml(value: object) -> object:
    """Serialize a ModelRoute/list/dict back to YAML-serializable strings for deep_merge."""
    from .models import ModelRoute as _MR
    if isinstance(value, _MR):
        return str(value)
    if isinstance(value, list):
        return [str(r) if isinstance(r, _MR) else r for r in value]
    if isinstance(value, dict):
        return {k: _routes_to_yaml(v) for k, v in value.items()}
    return value


def parse_route(value: object) -> ModelRoute:
    """Parse a single model route from YAML config value.

    Accepts:
    - "provider:model" string, e.g. "openrouter:qwen/qwen3-235b-a22b-2507"
    - {"provider": "openrouter", "model": "qwen/qwen3-235b-a22b-2507"} dict

    Raises ValueError for bare strings without a provider prefix.
    """
    if isinstance(value, dict):
        provider = value.get("provider")
        model = value.get("model")
        if not provider or not model:
            raise ValueError(
                f"Route dict must have 'provider' and 'model' keys, got: {value}"
            )
        return ModelRoute(provider=str(provider), model=str(model))

    if isinstance(value, str):
        if ":" not in value:
            raise ValueError(
                f"Model string '{value}' is missing a provider prefix. "
                f"Use 'openrouter:{value}' or 'anthropic:{value}'."
            )
        provider, model = value.split(":", 1)
        if not provider or not model:
            raise ValueError(f"Invalid route string '{value}': provider and model must be non-empty.")
        return ModelRoute(provider=provider, model=model)

    raise ValueError(f"Expected a string or dict for model route, got {type(value).__name__}: {value!r}")


def parse_routes(value: object) -> list[ModelRoute]:
    """Parse one or more model routes from a YAML config value.

    Accepts a single route or a list of routes (each in any form parse_route accepts).
    Returns a list with at least one element.
    """
    if isinstance(value, list):
        return [parse_route(item) for item in value]
    return [parse_route(value)]


def parse_actor_routes(value: object) -> object:
    """Parse the actors field which can be a route, list of routes, or per-actor dict.

    Returns ModelRoute, list[ModelRoute], or dict[str, ModelRoute | list[ModelRoute]].
    """
    if isinstance(value, dict) and not ("provider" in value and "model" in value):
        # Per-actor dict: keys are actor IDs (or "default"), values are routes
        result = {}
        for actor_id, route_value in value.items():
            if isinstance(route_value, list):
                result[actor_id] = [parse_route(r) for r in route_value]
            else:
                result[actor_id] = parse_route(route_value)
        return result

    return parse_routes(value) if isinstance(value, list) else parse_route(value)


def _slugify_question(text: str, index: int) -> str:
    """Derive a stable id for a research question declared as a bare string."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = "_".join(slug.split("_")[:6])
    return slug or f"rq_{index + 1}"


def parse_research_questions(value: object) -> List[ResearchQuestion]:
    """Parse the optional ``research_questions`` block from scenario.yaml.

    Accepts either bare strings (id derived from the text) or mappings with
    ``question`` plus optional ``id``, ``metrics``, ``events``, and ``notes``.
    Shape problems raise here; semantic problems (unknown metric ids, and so
    on) are reported by the validator so that `validate` can show them all at
    once rather than failing on the first.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(
            f"research_questions must be a list, got {type(value).__name__}"
        )

    def _as_id_list(raw: object, field_name: str, question_id: str) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            return list(raw)
        raise ValueError(
            f"research_questions['{question_id}'].{field_name} must be a string "
            f"or a list of strings"
        )

    questions: List[ResearchQuestion] = []
    for index, entry in enumerate(value):
        if isinstance(entry, str):
            text = entry.strip()
            if not text:
                raise ValueError(f"research_questions[{index}] is empty")
            questions.append(
                ResearchQuestion(id=_slugify_question(text, index), question=text)
            )
            continue

        if not isinstance(entry, dict):
            raise ValueError(
                f"research_questions[{index}] must be a string or a mapping, "
                f"got {type(entry).__name__}"
            )

        text = str(entry.get("question", "")).strip()
        if not text:
            raise ValueError(f"research_questions[{index}] has no 'question' text")

        question_id = str(entry.get("id") or _slugify_question(text, index)).strip()
        questions.append(
            ResearchQuestion(
                id=question_id,
                question=text,
                metrics=_as_id_list(entry.get("metrics"), "metrics", question_id),
                events=_as_id_list(entry.get("events"), "events", question_id),
                notes=str(entry.get("notes", "")).strip(),
            )
        )

    return questions


_INITIAL_STATE_KEYS = {"metrics", "context", "notes"}


def load_initial_state(path: Union[Path, str]) -> InitialState:
    """Load starting-state overrides from a JSON data file.

    The file is read as data only. Unknown top-level keys are rejected so that
    a typo in a generated draw fails loudly instead of being silently ignored.

    Args:
        path: Path to the initial-state JSON file

    Returns:
        Parsed InitialState

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is not a JSON object with the expected shape
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Initial state file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Initial state file {path} is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Initial state file {path} must contain a JSON object, got {type(data).__name__}"
        )

    unknown = sorted(set(data) - _INITIAL_STATE_KEYS)
    if unknown:
        allowed = ", ".join(sorted(_INITIAL_STATE_KEYS))
        raise ValueError(
            f"Initial state file {path} has unknown key(s): {', '.join(unknown)}. "
            f"Allowed keys: {allowed}"
        )

    raw_metrics = data.get("metrics", {})
    if not isinstance(raw_metrics, dict):
        raise ValueError(
            f"Initial state file {path}: 'metrics' must be an object, "
            f"got {type(raw_metrics).__name__}"
        )

    metrics: dict[str, float] = {}
    for metric_id, value in raw_metrics.items():
        if not isinstance(metric_id, str):
            raise ValueError(
                f"Initial state file {path}: metric ids must be strings, got {metric_id!r}"
            )
        # bool is a subclass of int; a boolean metric value is always a mistake.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"Initial state file {path}: metric '{metric_id}' must be a number, "
                f"got {type(value).__name__}"
            )
        metrics[metric_id] = float(value)

    context = data.get("context", "")
    if not isinstance(context, str):
        raise ValueError(
            f"Initial state file {path}: 'context' must be a string, "
            f"got {type(context).__name__}"
        )

    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError(
            f"Initial state file {path}: 'notes' must be a string, got {type(notes).__name__}"
        )

    return InitialState(
        metrics=metrics,
        context=context,
        notes=notes,
        source=str(path),
    )


def apply_initial_state(scenario: Scenario, state: InitialState) -> None:
    """Apply starting-state overrides to a freshly loaded scenario, in place.

    Metric ids must exist and values must fall inside the declared bounds. Both
    are hard errors rather than silent fixes: a draw that names an unknown
    metric or lands out of bounds indicates a broken sampler, and clamping it
    would hide that while quietly biasing the batch.

    Args:
        scenario: Scenario to modify
        state: Parsed initial state

    Raises:
        ValueError: If a metric is unknown or its value is out of bounds
    """
    unknown = sorted(set(state.metrics) - set(scenario.metrics.metrics))
    if unknown:
        known = ", ".join(sorted(scenario.metrics.metrics))
        raise ValueError(
            f"Initial state names unknown metric(s): {', '.join(unknown)}. "
            f"Scenario metrics: {known}"
        )

    for metric_id, value in state.metrics.items():
        metric = scenario.metrics.metrics[metric_id]
        if not (metric.min_value <= value <= metric.max_value):
            raise ValueError(
                f"Initial state sets '{metric_id}' to {value}, outside its bounds "
                f"[{metric.min_value}, {metric.max_value}]"
            )
        metric.value = value

    if state.context:
        # The world state starts as a copy of the context, so both need the
        # addition for turn 1 prompts to see the same starting world.
        scenario.context = f"{scenario.context.rstrip()}\n\n{state.context.strip()}\n"
        scenario.world_state.narrative = scenario.context

    scenario.initial_state = state


def load_scenario(
    path: Union[Path, str],
    initial_state: Optional[Union[Path, str]] = None,
) -> Scenario:
    """Load a complete scenario from directory or YAML file.

    Args:
        path: Either a directory containing scenario.yaml, or a direct path to a .yaml file
        initial_state: Optional path to a JSON file with starting-state overrides

    Returns:
        Loaded Scenario
    """
    path = Path(path)

    # Determine config file and scenario directory
    if path.is_file() and path.suffix in [".yaml", ".yml"]:
        # Direct path to a scenario YAML file (e.g., variant)
        config_file = path
        # For variants, we need to find the actual scenario directory
        # The variant may reference files relative to base scenario
        # We'll use the base scenario's directory for loading resources
        config = load_config(config_file)
        # Find the base scenario directory by looking for metrics.md
        scenario_dir = path.parent
        while scenario_dir != scenario_dir.parent:
            if (scenario_dir / "metrics.md").exists():
                break
            scenario_dir = scenario_dir.parent
        if not (scenario_dir / "metrics.md").exists():
            raise ValueError(f"Could not find scenario resources (metrics.md) for {path}")
    elif path.is_dir():
        # Directory containing scenario.yaml
        config_file = path / "scenario.yaml"
        scenario_dir = path
        config = load_config(config_file)
    else:
        raise ValueError(f"Path must be a directory or .yaml file: {path}")

    # Now scenario_dir points to the directory with resources

    # Load metrics
    metrics = load_metrics(scenario_dir / "metrics.md")

    # Load events
    events = load_events(scenario_dir / "events.md")

    # Load actors
    actors = {}
    actors_dir = scenario_dir / "background" / "actors"
    for actor_id in config.actor_ids:
        actors[actor_id] = load_actor(actors_dir / f"{actor_id}.md", actor_id)

    # Load context
    context = (scenario_dir / "background" / "context.md").read_text(encoding="utf-8")

    # Load initial metric rules
    metric_rules = (scenario_dir / "metric-rules.md").read_text(encoding="utf-8")

    # Load constitutional constraints if present (optional)
    constitution = None
    constitution_path = scenario_dir / "constitution.md"
    if constitution_path.exists():
        constitution = constitution_path.read_text(encoding="utf-8")

    # Create initial world state from context
    world_state = WorldState(
        narrative=context,
        turn=0,
        time_period=get_time_period(config.start_date, 0, config.time_scale),
    )

    # Load custom system prompts if they exist
    custom_system_prompts = load_custom_system_prompts(scenario_dir, config.actor_ids)

    # Load custom user prompts if they exist
    custom_user_prompts = load_custom_user_prompts(scenario_dir)

    scenario = Scenario(
        config=config,
        metrics=metrics,
        events=events,
        actors=actors,
        metric_rules=metric_rules,
        world_state=world_state,
        context=context,
        constitution=constitution,
        custom_system_prompts=custom_system_prompts,
        custom_user_prompts=custom_user_prompts,
    )

    if initial_state is not None:
        apply_initial_state(scenario, load_initial_state(initial_state))

    return scenario


def load_custom_user_prompts(scenario_dir: Path) -> dict[str, str]:
    """Load scenario-specific user prompt templates if they exist.

    Args:
        scenario_dir: Path to scenario directory

    Returns:
        Dictionary mapping prompt name to content.
        Keys include "events", "actor", "metric_rules", "metrics_update",
        "constitutional_referee", and "constitutional_referee_correction"
    """
    custom_prompts = {}
    prompts_dir = scenario_dir / "user-prompts"

    if not prompts_dir.exists():
        return custom_prompts

    prompt_files = [
        "events.md",
        "actor.md",
        "metric-rules.md",
        "metrics-update.md",
        "analysis.md",
        "constitutional-referee.md",
        "constitutional-referee-correction.md",
    ]
    for filename in prompt_files:
        prompt_path = prompts_dir / filename
        if prompt_path.exists():
            # Use base name without extension as key and replace hyphens with underscores
            # e.g., "metric-rules.md" -> "metric_rules"
            key = filename.replace(".md", "").replace("-", "_")
            custom_prompts[key] = prompt_path.read_text(encoding="utf-8")

    return custom_prompts


def load_custom_system_prompts(scenario_dir: Path, actor_ids: list[str]) -> dict[str, str]:
    """Load scenario-specific system prompts if they exist.

    Args:
        scenario_dir: Path to scenario directory
        actor_ids: List of actor IDs from scenario config

    Returns:
        Dictionary mapping prompt name to content.
        For actor prompts, keys are "actor_{actor_id}" (e.g., "actor_government")
        For other prompts, keys include "events", "metric_rules", "metrics_update",
        "constitutional_referee", and "constitutional_referee_correction"
    """
    custom_prompts = {}
    prompts_dir = scenario_dir / "system-prompts"

    if not prompts_dir.exists():
        return custom_prompts

    # Load non-actor system prompt files
    prompt_files = [
        "events.md",
        "metric-rules.md",
        "metrics-update.md",
        "actor.md",
        "analysis.md",
        "constitutional-referee.md",
        "constitutional-referee-correction.md",
    ]
    for filename in prompt_files:
        prompt_path = prompts_dir / filename
        if prompt_path.exists():
            # Use base name without extension as key (e.g., "events" for "events.md")
            key = filename.replace(".md", "").replace("-", "_")
            custom_prompts[key] = prompt_path.read_text(encoding="utf-8")

    # Load actor-specific prompts
    for actor_id in actor_ids:
        actor_prompt_path = prompts_dir / f"actor_{actor_id}.md"
        if actor_prompt_path.exists():
            key = f"actor_{actor_id}"
            custom_prompts[key] = actor_prompt_path.read_text(encoding="utf-8")

    return custom_prompts


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Override wins for scalars, lists, or new keys
            result[key] = value

    return result


def load_config(path: Path, _loading_stack: Optional[List[str]] = None) -> ScenarioConfig:
    """Load scenario.yaml with support for inheritance and per-task LLM configuration.

    Args:
        path: Path to scenario.yaml file
        _loading_stack: Internal parameter to detect circular dependencies

    Returns:
        ScenarioConfig with merged configuration from base scenarios
    """
    if _loading_stack is None:
        _loading_stack = []

    # Detect circular dependencies
    path_str = str(path.resolve())
    if path_str in _loading_stack:
        raise ValueError(f"Circular dependency detected: {' -> '.join(_loading_stack + [path_str])}")

    _loading_stack.append(path_str)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    # Check for base scenario
    if "base" in data:
        base_path_str = data.pop("base")  # Remove 'base' from data

        # SECURITY: Validate base path doesn't escape scenario directory structure
        base_path = (path.parent / base_path_str).resolve()

        # Get the absolute path of the current scenario's parent (allows sibling scenarios)
        scenario_root = path.parent.resolve()

        # Ensure base_path is within the scenarios directory structure
        # Allow base scenarios from parent directory (for shared base scenarios)
        # but prevent arbitrary filesystem access
        try:
            # Try to make base_path relative to scenario_root.parent
            # This allows ../base-scenario but not ../../etc/passwd
            base_path.relative_to(scenario_root.parent)
        except ValueError:
            raise ValueError(
                f"Security: Base scenario path '{base_path_str}' attempts to escape "
                f"allowed directory structure. Base scenarios must be relative paths "
                f"within the scenarios directory."
            )

        if not base_path.exists():
            raise FileNotFoundError(f"Base scenario not found: {base_path}")

        # Load base configuration
        base_config_dict = yaml.safe_load(base_path.read_text(encoding="utf-8"))

        # Recursively handle base's base (multi-level inheritance)
        if "base" in base_config_dict:
            # Load base's config through load_config to handle its inheritance
            base_config = load_config(base_path, _loading_stack)
            # Convert back to dict for merging
            base_config_dict = {
                "name": base_config.name,
                "description": base_config.description,
                "start_date": base_config.start_date,
                "time_scale": base_config.time_scale,
                "max_turns": base_config.max_turns,
                "actors": base_config.actor_ids,
                "output_language": base_config.output_language,
                "research_questions": [
                    {
                        "id": rq.id,
                        "question": rq.question,
                        "metrics": list(rq.metrics),
                        "events": list(rq.events),
                        "notes": rq.notes,
                    }
                    for rq in base_config.research_questions
                ],
                "llm": {
                    "events": _routes_to_yaml(base_config.llm.events),
                    "actors": _routes_to_yaml(base_config.llm.actors),
                    "rules": _routes_to_yaml(base_config.llm.rules),
                    "metrics": _routes_to_yaml(base_config.llm.metrics),
                    "summary": _routes_to_yaml(base_config.llm.summary),
                    "analysis": _routes_to_yaml(base_config.llm.analysis),
                    "referee": _routes_to_yaml(base_config.llm.referee),
                    "temperature": base_config.llm.temperature,
                    "max_tokens": base_config.llm.max_tokens,
                    "max_tokens_by_task": base_config.llm.max_tokens_by_task,
                    "structured_outputs": base_config.llm.structured_outputs,
                    "probability_samples": base_config.llm.probability_samples,
                    "call_timeout_seconds": base_config.llm.call_timeout_seconds,
                },
                "emergent_events": {
                    "enabled": base_config.emergent_events.enabled,
                    "max_per_turn": base_config.emergent_events.max_per_turn,
                    "max_probability": base_config.emergent_events.max_probability,
                },
                "rule_evolution": {
                    "freeze_until_turn": base_config.rule_evolution.freeze_until_turn,
                    "max_changes_per_turn": base_config.rule_evolution.max_changes_per_turn,
                },
                "constitutional_enforcement": {
                    "max_attempts": base_config.constitutional_enforcement.max_attempts,
                    "on_failure": base_config.constitutional_enforcement.on_failure,
                },
                "logging": {
                    "llm_io": base_config.logging.llm_io,
                },
            }

        # Merge configurations (override wins)
        data = deep_merge(base_config_dict, data)

    # Parse LLM configuration
    llm_data = data.get("llm", {})

    _default_main = "openrouter:google/gemini-3-flash-preview"
    _default_cheap = "openrouter:qwen/qwen3-235b-a22b-2507"

    # structured_outputs: accept YAML strings or native booleans, normalize to
    # the canonical "auto" | "true" | "false" strings the model validates.
    def _normalize_structured(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value).lower()

    _structured = _normalize_structured(llm_data.get("structured_outputs", "auto"))
    _probability_samples = llm_data.get("probability_samples", 1)
    _call_timeout = llm_data.get("call_timeout_seconds", 300)

    # Support both old format (single model) and new format (per-task models)
    if "model" in llm_data and not any(k in llm_data for k in ["events", "actors", "rules", "metrics"]):
        # Old format: single model for everything
        _m = llm_data.get("model", _default_main)
        llm_config = LLMConfig(
            events=parse_route(_m),
            actors=parse_route(_m),
            rules=parse_route(_m),
            metrics=parse_route(_m),
            summary=parse_route(llm_data.get("summary", _m)),
            analysis=parse_route(llm_data.get("analysis", llm_data.get("summary", _m))),
            referee=parse_route(llm_data.get("referee", _default_cheap)),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
            max_tokens_by_task=llm_data.get("max_tokens_by_task", {}),
            structured_outputs=_structured,
            probability_samples=_probability_samples,
            call_timeout_seconds=_call_timeout,
        )
    else:
        # New format: per-task models
        llm_config = LLMConfig(
            events=_parse_routes_field(llm_data.get("events", _default_main)),
            actors=parse_actor_routes(llm_data.get("actors", _default_main)),
            rules=_parse_routes_field(llm_data.get("rules", _default_main)),
            metrics=_parse_routes_field(llm_data.get("metrics", _default_main)),
            summary=_parse_routes_field(llm_data.get("summary", _default_cheap)),
            analysis=_parse_routes_field(
                llm_data.get("analysis", llm_data.get("summary", _default_cheap))
            ),
            referee=_parse_routes_field(llm_data.get("referee", _default_cheap)),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
            max_tokens_by_task=llm_data.get("max_tokens_by_task", {}),
            structured_outputs=_structured,
            probability_samples=_probability_samples,
            call_timeout_seconds=_call_timeout,
        )

    emergent_events_data = data.get("emergent_events", {})
    emergent_events = EmergentEventsConfig(
        enabled=bool(emergent_events_data.get("enabled", False)),
        max_per_turn=emergent_events_data.get("max_per_turn", 1),
        max_probability=emergent_events_data.get("max_probability", 0.35),
    )

    rule_evolution_data = data.get("rule_evolution", {})
    rule_evolution = RuleEvolutionConfig(
        freeze_until_turn=rule_evolution_data.get("freeze_until_turn", 0),
        max_changes_per_turn=rule_evolution_data.get("max_changes_per_turn", 6),
    )

    constitutional_data = data.get("constitutional_enforcement", {})
    constitutional_enforcement = ConstitutionalEnforcementConfig(
        max_attempts=constitutional_data.get("max_attempts", 2),
        on_failure=constitutional_data.get("on_failure", "accept_with_violations"),
    )

    logging_data = data.get("logging", {})
    logging_config = LoggingConfig(
        llm_io=bool(logging_data.get("llm_io", False)),
    )

    return ScenarioConfig(
        name=data["name"],
        description=data["description"],
        start_date=data["start_date"],
        time_scale=data["time_scale"],
        max_turns=data["max_turns"],
        actor_ids=data["actors"],
        output_language=data.get("output_language"),
        research_questions=parse_research_questions(data.get("research_questions")),
        llm=llm_config,
        emergent_events=emergent_events,
        rule_evolution=rule_evolution,
        constitutional_enforcement=constitutional_enforcement,
        logging=logging_config,
    )


def load_metrics(path: Path) -> Metrics:
    """Parse metrics from markdown file.

    Expected format:
    ## metric_id
    **Description:** ...
    **ID:** metric_id
    **Min:** 0
    **Max:** 100
    **Unit:** percent
    **Start value:** 50
    **Reference points:** (optional)
    - 0: description
    - 50: description
    """
    content = path.read_text(encoding="utf-8")
    metrics = {}

    current_metric_id = None
    metric_data = {}

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("## "):
            # Save previous metric
            if current_metric_id and metric_data:
                metrics[current_metric_id] = create_metric(current_metric_id, metric_data)
            current_metric_id = line[3:].strip()
            metric_data = {}

        elif line.startswith("**") and ":" in line:
            key, value = parse_key_value(line)
            metric_data[normalize_markdown_key(key)] = value

        elif current_metric_id and line.startswith("- ") and ":" in line:
            # Reference point: "- 0: description"
            if "reference_points" not in metric_data:
                metric_data["reference_points"] = {}

            if not isinstance(metric_data["reference_points"], dict):
                metric_data["reference_points"] = {}

            try:
                ref_value, ref_desc = line[2:].split(":", 1)
                # Accept both "- 8: text" and the bolded "- **8:** text" form
                # that scenario files commonly use.
                ref_value = ref_value.strip().strip("*").strip()
                ref_desc = ref_desc.strip().lstrip("*").strip()
                metric_data["reference_points"][float(ref_value)] = ref_desc
            except ValueError:
                pass

    # Don't forget last metric
    if current_metric_id and metric_data:
        metrics[current_metric_id] = create_metric(current_metric_id, metric_data)

    return Metrics(metrics=metrics)


def create_metric(metric_id: str, data: dict) -> Metric:
    """Create a Metric from parsed data."""
    description = data.get("description", "")
    
    # Accept the English labels used in metrics.md and tests.
    value_str = (
        data.get("starting_value")
        or data.get("start_value")
        or data.get("value", "0")
    )
    value = float(value_str)
    
    min_val = float(data.get("min", 0))
    max_val = float(data.get("max", 100))
    
    unit = data.get("unit", "")
    
    ref_points = data.get("reference_points", {})
    
    return Metric(
        id=metric_id,
        description=description,
        value=value,
        min_value=min_val,
        max_value=max_val,
        unit=unit,
        reference_points=ref_points,
    )


def load_events(path: Path) -> list[Event]:
    """Parse events from markdown file.

    Expected format:
    ## Event Name
    **ID:** event_id
    **Condition:** condition description
    **Probability:** 0.10 or formula
    **Can repeat:** Yes/No
    **Description:** event description
    """
    content = path.read_text(encoding="utf-8")
    events = []
    current_event = {}

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("## ") and current_event.get("id"):
            # Save previous event (skip ## headings before first event)
            events.append(create_event(current_event))
            current_event = {"name": line[3:].strip()}

        elif line.startswith("## "):
            current_event = {"name": line[3:].strip()}

        elif line.startswith("**") and ":" in line:
            key, value = parse_key_value(line)
            current_event[normalize_markdown_key(key)] = value

    # Don't forget last event
    if current_event.get("id"):
        events.append(create_event(current_event))

    return events


def create_event(data: dict) -> Event:
    """Create an Event from parsed data."""
    can_repeat_str = data.get("can_repeat", "no").lower()
    can_repeat = can_repeat_str in ["yes", "true"]

    # Handle probability - could be number or formula
    probability = data.get("probability", "0")
    
    description = data.get("description", "")
    condition = data.get("condition", "")

    return Event(
        id=data["id"],
        description=description,
        condition=condition,
        probability=probability,
        can_repeat=can_repeat,
    )


def load_actor(path: Path, actor_id: str) -> Actor:
    """Parse actor from markdown file.

    Expected format:
    # Actor Name
    ## Short description
    short description text
    ## Long description
    long description text
    """
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    name = ""
    short_desc = ""
    long_desc = ""
    initial_goals: list[str] = []
    behavioral_traits: list[str] = []
    current_section = None

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if line_stripped.startswith("# "):
            name = line_stripped[2:].strip()
        elif line_lower.startswith("### initial goals"):
            current_section = "goals"
        elif (
            line_lower.startswith("### behavioral traits")
            or line_lower.startswith("### behavioural traits")
            or line_lower.startswith("### traits")
        ):
            current_section = "traits"
        elif line_lower.startswith("## short description"):
            current_section = "short"
        elif line_lower.startswith("## long description"):
            current_section = "long"
        elif line_stripped.startswith("##") or line_stripped.startswith("###"):
            current_section = None
        elif current_section == "short" and line_stripped:
            short_desc += line_stripped + " "
        elif current_section == "long" and line_stripped:
            long_desc += line_stripped + " "
        elif current_section in {"goals", "traits"} and line_stripped:
            item = re.sub(r"^[-*]\s+", "", line_stripped)
            item = re.sub(r"^\d+\.\s+", "", item)
            if not item:
                continue
            if current_section == "goals":
                initial_goals.append(item)
            else:
                behavioral_traits.append(item)

    return Actor(
        id=actor_id,
        name=name or actor_id,
        short_description=short_desc.strip(),
        long_description=long_desc.strip(),
        initial_goals=initial_goals,
        behavioral_traits=behavioral_traits,
    )


def parse_key_value(line: str) -> tuple[str, str]:
    """Parse a markdown line like '**Key:** value' -> ('Key', 'value')."""
    # Remove ** markers
    line = line.replace("**", "")
    if ":" not in line:
        return "", ""

    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def normalize_markdown_key(key: str) -> str:
    """Normalize markdown field labels to stable lookup keys."""
    return re.sub(r"\s+", "_", key.strip().lower())


def get_time_period(start_date: str, turn: int, time_scale: str) -> str:
    """Calculate time period string for a given turn.

    Args:
        start_date: Format "2026-01" (YYYY-MM), "2026", or "2026-03-09" (YYYY-MM-DD)
        turn: Turn number (0 = initial state, 1 = first turn)
        time_scale: e.g., "6 months per turn", "2 weeks per turn"

    Returns:
        String like "January-June 2026" or "2026-03-09 to 2026-03-22"
    """
    if turn == 0:
        return f"Start: {start_date}"

    start = _parse_start_date(start_date)
    amount, unit = _parse_time_scale(time_scale)

    if unit == "days":
        period_start = start + timedelta(days=(turn - 1) * amount)
        period_end = period_start + timedelta(days=amount - 1)
    elif unit == "weeks":
        period_start = start + timedelta(weeks=(turn - 1) * amount)
        period_end = period_start + timedelta(weeks=amount) - timedelta(days=1)
    else:
        months = amount if unit == "months" else amount * 12
        period_start = _add_months(start, (turn - 1) * months)
        period_end = _add_months(period_start, months) - timedelta(days=1)

    return _format_time_period(period_start, period_end)


def _parse_start_date(start_date: str) -> date:
    """Parse supported start_date formats into a date object."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", start_date):
        return datetime.strptime(start_date, "%Y-%m-%d").date()
    if re.fullmatch(r"\d{4}-\d{2}", start_date):
        return datetime.strptime(start_date, "%Y-%m").date().replace(day=1)
    if re.fullmatch(r"\d{4}", start_date):
        return datetime.strptime(start_date, "%Y").date().replace(month=1, day=1)
    raise ValueError(f"Unsupported start_date format: {start_date}")


def _parse_time_scale(time_scale: str) -> tuple[int, str]:
    """Parse time_scale into (amount, normalized unit)."""
    match = re.search(
        r"(\d+)\s*(day|days|week|weeks|month|months|year|years)\b",
        time_scale.lower(),
    )
    if not match:
        # Backward-compatible default.
        return 6, "months"

    amount = int(match.group(1))
    raw_unit = match.group(2)

    if raw_unit.startswith("day"):
        return amount, "days"
    if raw_unit.startswith("week"):
        return amount, "weeks"
    if raw_unit.startswith("year"):
        return amount, "years"
    return amount, "months"


def _add_months(input_date: date, months: int) -> date:
    """Add months while clamping day to target month length."""
    total_months = (input_date.year * 12 + input_date.month - 1) + months
    year = total_months // 12
    month = total_months % 12 + 1
    max_day = calendar.monthrange(year, month)[1]
    day = min(input_date.day, max_day)
    return date(year, month, day)


def _format_time_period(period_start: date, period_end: date) -> str:
    """Format periods as month ranges when clean, otherwise full date ranges."""
    starts_at_month_start = period_start.day == 1
    ends_at_month_end = period_end.day == calendar.monthrange(period_end.year, period_end.month)[1]
    is_full_month_window = starts_at_month_start and ends_at_month_end

    if is_full_month_window:
        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        start_name = month_names[period_start.month - 1]
        end_name = month_names[period_end.month - 1]
        if period_start.year == period_end.year:
            return f"{start_name}-{end_name} {period_start.year}"
        return f"{start_name} {period_start.year}-{end_name} {period_end.year}"

    return f"{period_start.isoformat()} to {period_end.isoformat()}"
