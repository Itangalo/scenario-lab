"""Scenario loading from disk."""

import calendar
import re
import yaml
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Union, Optional, List
from .models import (
    Scenario,
    ScenarioConfig,
    LLMConfig,
    RuleEvolutionConfig,
    ConstitutionalEnforcementConfig,
    Metric,
    Metrics,
    Event,
    Actor,
    WorldState,
)


def load_scenario(path: Union[Path, str]) -> Scenario:
    """Load a complete scenario from directory or YAML file.

    Args:
        path: Either a directory containing scenario.yaml, or a direct path to a .yaml file

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

    return Scenario(
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
                "llm": {
                    "events": base_config.llm.events,
                    "actors": base_config.llm.actors,
                    "rules": base_config.llm.rules,
                    "metrics": base_config.llm.metrics,
                    "summary": base_config.llm.summary,
                    "analysis": base_config.llm.analysis,
                    "referee": base_config.llm.referee,
                    "temperature": base_config.llm.temperature,
                    "max_tokens": base_config.llm.max_tokens,
                    "max_tokens_by_task": base_config.llm.max_tokens_by_task,
                },
                "rule_evolution": {
                    "freeze_until_turn": base_config.rule_evolution.freeze_until_turn,
                    "max_changes_per_turn": base_config.rule_evolution.max_changes_per_turn,
                },
                "constitutional_enforcement": {
                    "max_attempts": base_config.constitutional_enforcement.max_attempts,
                    "on_failure": base_config.constitutional_enforcement.on_failure,
                },
            }

        # Merge configurations (override wins)
        data = deep_merge(base_config_dict, data)

    # Parse LLM configuration
    llm_data = data.get("llm", {})

    # Support both old format (single model) and new format (per-task models)
    if "model" in llm_data and not any(k in llm_data for k in ["events", "actors", "rules", "metrics"]):
        # Old format: single model for everything
        llm_config = LLMConfig(
            events=llm_data.get("model", "google/gemini-3-flash-preview"),
            actors=llm_data.get("model", "google/gemini-3-flash-preview"),
            rules=llm_data.get("model", "google/gemini-3-flash-preview"),
            metrics=llm_data.get("model", "google/gemini-3-flash-preview"),
            summary=llm_data.get("summary", llm_data.get("model", "google/gemini-3-flash-preview")),
            analysis=llm_data.get(
                "analysis",
                llm_data.get("summary", llm_data.get("model", "google/gemini-3-flash-preview")),
            ),
            referee=llm_data.get("referee", "x-ai/grok-4.1-fast"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
            max_tokens_by_task=llm_data.get("max_tokens_by_task", {}),
        )
    else:
        # New format: per-task models
        llm_config = LLMConfig(
            events=llm_data.get("events", "google/gemini-3-flash-preview"),
            actors=llm_data.get("actors", "google/gemini-3-flash-preview"),
            rules=llm_data.get("rules", "google/gemini-3-flash-preview"),
            metrics=llm_data.get("metrics", "google/gemini-3-flash-preview"),
            summary=llm_data.get("summary", "x-ai/grok-4.1-fast"),
            analysis=llm_data.get("analysis", llm_data.get("summary", "x-ai/grok-4.1-fast")),
            referee=llm_data.get("referee", "x-ai/grok-4.1-fast"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
            max_tokens_by_task=llm_data.get("max_tokens_by_task", {}),
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

    return ScenarioConfig(
        name=data["name"],
        description=data["description"],
        start_date=data["start_date"],
        time_scale=data["time_scale"],
        max_turns=data["max_turns"],
        actor_ids=data["actors"],
        output_language=data.get("output_language"),
        llm=llm_config,
        rule_evolution=rule_evolution,
        constitutional_enforcement=constitutional_enforcement,
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
                metric_data["reference_points"][float(ref_value.strip())] = ref_desc.strip()
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
