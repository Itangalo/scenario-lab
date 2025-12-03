"""Scenario validator."""

from pathlib import Path
from typing import List
from .models import Scenario
from .loader import load_scenario


class ValidationResult:
    def __init__(self, errors: List[str] = None, warnings: List[str] = None):
        self.errors = errors or []
        self.warnings = warnings or []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_scenario(scenario_path: Path) -> ValidationResult:
    """Validate a scenario structure and content."""
    errors = []
    warnings = []

    try:
        scenario = load_scenario(scenario_path)
    except Exception as e:
        return ValidationResult(errors=[f"Failed to load scenario: {str(e)}"])

    # 1. Config Validation
    if not scenario.config.name:
        errors.append("Scenario name is missing")
    if not scenario.config.actor_ids:
        errors.append("No actors defined in config")

    # 2. Actor Validation
    for actor_id in scenario.config.actor_ids:
        if actor_id not in scenario.actors:
            errors.append(f"Actor '{actor_id}' defined in config but missing description file")
        else:
            actor = scenario.actors[actor_id]
            if not actor.name:
                warnings.append(f"Actor '{actor_id}' has no display name")
            if not actor.short_description:
                warnings.append(f"Actor '{actor_id}' has no short description")

    # 3. Metrics Validation
    if not scenario.metrics.metrics:
        warnings.append("No metrics defined")
    
    for m_id, metric in scenario.metrics.metrics.items():
        if metric.min_value >= metric.max_value:
            errors.append(f"Metric '{m_id}': min value must be less than max value")
        if not (metric.min_value <= metric.value <= metric.max_value):
            errors.append(f"Metric '{m_id}': start value {metric.value} outside range [{metric.min_value}, {metric.max_value}]")

    # 4. Events Validation
    if not scenario.events:
        warnings.append("No events defined")
    
    for event in scenario.events:
        if not event.id:
            errors.append("Event found without ID")
        if not event.condition:
            warnings.append(f"Event '{event.id}' has no condition")

    # 5. Content Validation
    if not scenario.context.strip():
        warnings.append("Context description is empty")
    
    if not scenario.metric_rules.strip():
        warnings.append("Metric rules are empty")

    return ValidationResult(errors, warnings)
