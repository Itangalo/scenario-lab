"""Scenario loading from disk."""

import yaml
from pathlib import Path
from typing import Union, Optional, List
from .models import (
    Scenario,
    ScenarioConfig,
    LLMConfig,
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
        custom_system_prompts=custom_system_prompts,
        custom_user_prompts=custom_user_prompts,
    )


def load_custom_user_prompts(scenario_dir: Path) -> dict[str, str]:
    """Load scenario-specific user prompt templates if they exist.

    Args:
        scenario_dir: Path to scenario directory

    Returns:
        Dictionary mapping prompt name to content.
        Keys: "events", "actor", "metric_rules", "metrics_update"
    """
    custom_prompts = {}
    prompts_dir = scenario_dir / "user-prompts"

    if not prompts_dir.exists():
        return custom_prompts

    prompt_files = ["events.md", "actor.md", "metric-rules.md", "metrics-update.md"]
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
        For other prompts, keys are "events", "metric_rules", "metrics_update"
    """
    custom_prompts = {}
    prompts_dir = scenario_dir / "system-prompts"

    if not prompts_dir.exists():
        return custom_prompts

    # Load non-actor system prompt files
    prompt_files = ["events.md", "metric-rules.md", "metrics-update.md"]
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
        base_path = (path.parent / base_path_str).resolve()

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
                    "temperature": base_config.llm.temperature,
                    "max_tokens": base_config.llm.max_tokens,
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
            events=llm_data.get("model", "anthropic/claude-sonnet-4"),
            actors=llm_data.get("model", "anthropic/claude-sonnet-4"),
            rules=llm_data.get("model", "anthropic/claude-sonnet-4"),
            metrics=llm_data.get("model", "anthropic/claude-sonnet-4"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
        )
    else:
        # New format: per-task models
        llm_config = LLMConfig(
            events=llm_data.get("events", "anthropic/claude-sonnet-4"),
            actors=llm_data.get("actors", "anthropic/claude-sonnet-4"),
            rules=llm_data.get("rules", "anthropic/claude-sonnet-4"),
            metrics=llm_data.get("metrics", "anthropic/claude-sonnet-4"),
            summary=llm_data.get("summary", "anthropic/claude-haiku-4"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 2000),
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
    )


def load_metrics(path: Path) -> Metrics:
    """Parse metrics from markdown file.

    Expected format:
    ## metric_id
    **Beskrivning:** ...
    **ID:** metric_id
    **Min:** 0
    **Max:** 100
    **Enhet:** percent
    **Startvärde:** 50
    **Referenspunkter:** (optional)
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
            metric_data[key.lower()] = value

        elif current_metric_id and line.startswith("- ") and ":" in line:
            # Reference point: "- 0: description"
            # Check for either Swedish or English key
            ref_key_swe = "referenspunkter"
            ref_key_eng = "reference_points"
            
            if ref_key_swe not in metric_data and ref_key_eng not in metric_data:
                # Default to English if neither exists (will be merged in create_metric)
                metric_data[ref_key_eng] = {}
            
            # Use whichever key exists (or English if we just created it)
            active_ref_key = ref_key_swe if ref_key_swe in metric_data else ref_key_eng
            
            try:
                ref_value, ref_desc = line[2:].split(":", 1)
                metric_data[active_ref_key][float(ref_value.strip())] = ref_desc.strip()
            except ValueError:
                pass

    # Don't forget last metric
    if current_metric_id and metric_data:
        metrics[current_metric_id] = create_metric(current_metric_id, metric_data)

    return Metrics(metrics=metrics)


def create_metric(metric_id: str, data: dict) -> Metric:
    """Create a Metric from parsed data."""
    # Handle bilingual keys (prefer Swedish for backward compat, fallback to English)
    description = data.get("beskrivning") or data.get("description", "")
    
    # Value can be startvärde or value
    value_str = data.get("startvärde") or data.get("value", "0")
    value = float(value_str)
    
    min_val = float(data.get("min", 0))
    max_val = float(data.get("max", 100))
    
    unit = data.get("enhet") or data.get("unit", "")
    
    # Reference points can be referenspunkter or reference_points
    ref_points = data.get("referenspunkter") or data.get("reference_points", {})
    
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
    **Villkor:** condition description
    **Sannolikhet:** 0.10 or formula
    **Kan upprepas:** Ja/Nej
    **Beskrivning:** event description
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
            current_event[key.lower()] = value

    # Don't forget last event
    if current_event.get("id"):
        events.append(create_event(current_event))

    return events


def create_event(data: dict) -> Event:
    """Create an Event from parsed data."""
    # Handle bilingual keys for can_repeat
    can_repeat_str_swe = data.get("kan upprepas")
    can_repeat_str_eng = data.get("can repeat")
    
    can_repeat_str = (can_repeat_str_swe or can_repeat_str_eng or "nej").lower()
    can_repeat = can_repeat_str in ["ja", "yes", "true"]

    # Handle probability - could be number or formula
    probability = data.get("sannolikhet") or data.get("probability", "0")
    
    description = data.get("beskrivning") or data.get("description", "")
    condition = data.get("villkor") or data.get("condition", "")

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
    ## Kort beskrivning
    short description text
    ## Längre beskrivning
    long description text
    """
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    name = ""
    short_desc = ""
    long_desc = ""
    current_section = None

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        if line_stripped.startswith("# "):
            name = line_stripped[2:].strip()
        elif line_lower.startswith("## kort beskrivning") or line_lower.startswith("## short description"):
            current_section = "short"
        elif line_lower.startswith("## längre beskrivning") or line_lower.startswith("## long description"):
            current_section = "long"
        elif line_stripped.startswith("##"):
            current_section = None
        elif current_section == "short" and line_stripped:
            short_desc += line_stripped + " "
        elif current_section == "long" and line_stripped:
            long_desc += line_stripped + " "

    # Default goals - can be extracted from description if needed
    initial_goals = []

    return Actor(
        id=actor_id,
        name=name or actor_id,
        short_description=short_desc.strip(),
        long_description=long_desc.strip(),
        initial_goals=initial_goals,
    )


def parse_key_value(line: str) -> tuple[str, str]:
    """Parse a markdown line like '**Key:** value' -> ('Key', 'value')."""
    # Remove ** markers
    line = line.replace("**", "")
    if ":" not in line:
        return "", ""

    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def get_time_period(start_date: str, turn: int, time_scale: str) -> str:
    """Calculate time period string for a given turn.

    Args:
        start_date: Format "2026-01" (YYYY-MM)
        turn: Turn number (0 = initial state, 1 = first turn)
        time_scale: e.g., "6 months per turn"

    Returns:
        String like "January-June 2026"
    """
    if turn == 0:
        return f"Start: {start_date}"

    # Parse start date
    year, month = map(int, start_date.split("-"))

    # Parse time scale
    months_per_turn = 6  # default
    if "month" in time_scale.lower():
        parts = time_scale.lower().split()
        for i, part in enumerate(parts):
            if part.isdigit():
                months_per_turn = int(part)
                break

    # Calculate period
    start_month = month + (turn - 1) * months_per_turn
    end_month = start_month + months_per_turn - 1

    # Handle year overflow
    start_year = year + (start_month - 1) // 12
    start_month = ((start_month - 1) % 12) + 1

    end_year = year + (end_month - 1) // 12
    end_month = ((end_month - 1) % 12) + 1

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

    start_name = month_names[start_month - 1]
    end_name = month_names[end_month - 1]

    if start_year == end_year:
        return f"{start_name}-{end_name} {start_year}"
    else:
        return f"{start_name} {start_year}-{end_name} {end_year}"
