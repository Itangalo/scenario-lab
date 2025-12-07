"""Scenario validator."""

from pathlib import Path
from typing import List, Set
import re
from datetime import datetime
from .models import Scenario
from .loader import load_scenario


class ValidationResult:
    def __init__(self, errors: List[str] = None, warnings: List[str] = None):
        self.errors = errors or []
        self.warnings = warnings or []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# Helper functions

def extract_metric_references(text: str) -> Set[str]:
    """Extract metric ID references from text.

    Looks for patterns like:
    - metric_name
    - Common metric naming patterns (lowercase with underscores)
    """
    # Match words that look like metric IDs (lowercase_with_underscores)
    # This is a heuristic - we'll check against actual metric IDs
    pattern = r'\b([a-z][a-z0-9_]*)\b'
    potential_refs = set(re.findall(pattern, text))
    return potential_refs


def is_static_probability(prob_str: str) -> bool:
    """Check if probability is static (e.g., '10 procent per runda')."""
    # Check for common static patterns
    static_patterns = [
        r'\d+\s*%',  # "10%"
        r'\d+\s*procent',  # "10 procent"
        r'\d+\s*percent',  # "10 percent"
        r'0\.\d+',  # "0.1"
    ]

    for pattern in static_patterns:
        if re.search(pattern, prob_str.lower()):
            return True
    return False


def parse_static_probability(prob_str: str) -> float:
    """Parse static probability string to float [0, 1]."""
    # Extract number
    match = re.search(r'(\d+(?:\.\d+)?)', prob_str)
    if not match:
        return 0.0

    value = float(match.group(1))

    # If it looks like a percentage, convert to [0, 1]
    if '%' in prob_str or 'procent' in prob_str.lower() or 'percent' in prob_str.lower():
        value = value / 100.0

    # If already decimal, use as-is
    if 0 <= value <= 1:
        return value

    # If > 1, assume percentage
    if value > 1:
        return value / 100.0

    return value


def eval_probability_formula(formula: str, context: dict) -> float:
    """Safely evaluate a probability formula.

    Args:
        formula: Mathematical expression (may reference metrics)
        context: Dict of metric_id -> value

    Returns:
        Evaluated result as float
    """
    # Create safe evaluation context with only allowed operations
    safe_context = {
        '__builtins__': {},
        'min': min,
        'max': max,
    }

    # Add metric values
    safe_context.update(context)

    # Evaluate
    result = eval(formula, safe_context, {})
    return float(result)


def is_valid_model_string(model: str) -> bool:
    """Check if model string follows expected format.

    Expected format: provider/model-name
    Examples: anthropic/claude-sonnet-4, openai/gpt-4o
    """
    if not isinstance(model, str):
        return False

    # Must contain a slash
    if '/' not in model:
        return False

    parts = model.split('/')
    if len(parts) != 2:
        return False

    provider, model_name = parts

    # Both parts should be non-empty
    if not provider or not model_name:
        return False

    return True


# Validation functions

def validate_metric_references(scenario: Scenario) -> List[str]:
    """Check that all metric references are valid.

    Checks:
    - Actor descriptions reference valid metrics
    - Event conditions reference valid metrics
    - Event probabilities reference valid metrics
    - Metric rules reference valid metrics

    Returns:
        List of validation errors
    """
    errors = []
    valid_metric_ids = set(scenario.metrics.metrics.keys())

    # Check actor descriptions
    for actor_id, actor in scenario.actors.items():
        text = f"{actor.short_description} {actor.long_description}"
        referenced_metrics = extract_metric_references(text)

        # Only flag if the reference looks like a metric ID AND exists in our metrics
        for metric in referenced_metrics:
            # Skip common English words that aren't metrics
            if metric in ['the', 'a', 'an', 'and', 'or', 'to', 'of', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'is', 'are', 'be', 'has', 'have', 'will', 'can', 'may']:
                continue
            # Only check metrics that could plausibly be metric IDs (contain underscore or match a known metric pattern)
            if '_' in metric or metric in valid_metric_ids:
                if metric not in valid_metric_ids:
                    errors.append(f"Actor '{actor_id}' may reference unknown metric '{metric}'")

    # Check events
    for event in scenario.events:
        # Check conditions - look for metric-like patterns
        referenced_metrics = extract_metric_references(event.condition)
        for metric in referenced_metrics:
            if '_' in metric and metric not in valid_metric_ids:
                errors.append(f"Event '{event.id}' condition references unknown metric '{metric}'")

        # Check probability formulas - only if it looks like a formula (not natural language or static)
        if not is_static_probability(event.probability) and is_formula_probability(event.probability, valid_metric_ids):
            referenced_metrics = extract_metric_references(event.probability)
            for metric in referenced_metrics:
                # Skip mathematical keywords
                if metric in ['min', 'max', 'abs']:
                    continue
                if metric not in valid_metric_ids:
                    errors.append(f"Event '{event.id}' probability references unknown metric '{metric}'")

    # Check metric rules for cross-references
    if scenario.metric_rules:
        referenced_metrics = extract_metric_references(scenario.metric_rules)
        for metric in referenced_metrics:
            if '_' in metric and metric not in valid_metric_ids:
                errors.append(f"Metric rules reference unknown metric '{metric}'")

    return errors


def is_formula_probability(prob_str: str, valid_metrics: Set[str]) -> bool:
    """Check if probability string looks like a mathematical formula.

    A formula is:
    - Contains only metric IDs, numbers, and operators
    - No complex natural language

    Examples of formulas:
    - "unemployment / 100"
    - "2 * unemployment / 100"
    - "min(unemployment, 50) / 100"

    Examples of natural language (not formulas):
    - "Double the value of unemployment, in percent"
    - "15 percent rounds 1-2, 10 percent rounds 3-4"
    """
    # If it contains words like "the", "of", "value", "round", it's natural language
    natural_language_words = ['the', 'of', 'value', 'round', 'double', 'triple', 'half', 'twice']
    for word in natural_language_words:
        if re.search(rf'\b{word}\b', prob_str.lower()):
            return False

    # If it contains metric IDs and math operators, it's likely a formula
    # Extract all word-like tokens
    tokens = re.findall(r'\b[a-z_][a-z0-9_]*\b', prob_str.lower())

    # Check if all tokens are either metrics or math functions
    math_functions = {'min', 'max', 'abs'}
    for token in tokens:
        if token not in valid_metrics and token not in math_functions:
            # Unknown token - probably natural language
            return False

    # If we got here, it looks like a formula
    return True


def validate_event_probabilities(scenario: Scenario) -> List[str]:
    """Validate that probability formulas are evaluable.

    Checks:
    - Static probabilities are in valid format
    - Formulas are valid Python expressions
    - Natural language descriptions are accepted (LLM will interpret)

    Returns:
        List of validation errors
    """
    errors = []
    warnings = []
    valid_metric_ids = set(scenario.metrics.metrics.keys())

    for event in scenario.events:
        prob = event.probability

        # Check if it's a static probability (e.g., "10 percent", "5%", "0.1")
        if is_static_probability(prob):
            try:
                value = parse_static_probability(prob)
                if not 0 <= value <= 1:
                    errors.append(f"Event '{event.id}' static probability {value} outside valid range [0, 1]")
                elif value < 0.001:
                    warnings.append(f"Event '{event.id}' has very low probability ({value:.1%})")
            except Exception as e:
                # If it fails to parse but has "percent" in it, it might be natural language
                if 'percent' in prob.lower() or '%' in prob:
                    # Skip - LLM will interpret
                    continue
                errors.append(f"Event '{event.id}' has unparseable probability: {e}")
            continue

        # Check if it looks like a formula (vs. natural language)
        if not is_formula_probability(prob, valid_metric_ids):
            # Natural language - LLM will interpret, skip validation
            continue

        # It's a formula - validate it
        try:
            # Create test context with sample metric values (50 for all)
            test_context = {m_id: 50.0 for m_id in valid_metric_ids}

            # Try to evaluate
            result = eval_probability_formula(prob, test_context)

            # Check result is valid
            if not isinstance(result, (int, float)):
                errors.append(f"Event '{event.id}' probability formula doesn't return a number")
            elif result < 0:
                errors.append(f"Event '{event.id}' probability formula returns negative value: {result}")
            elif result > 1:
                # Could be percentage - warn but don't error
                warnings.append(f"Event '{event.id}' probability formula returns value > 1: {result} (remember to use 0-1 range, not 0-100)")

        except NameError as e:
            # Likely undefined metric reference
            errors.append(f"Event '{event.id}' probability formula references undefined metric: {e}")
        except SyntaxError as e:
            errors.append(f"Event '{event.id}' has invalid probability formula syntax: {e}")
        except Exception as e:
            errors.append(f"Event '{event.id}' probability formula error: {e}")

    # Return both as errors for now (warnings will be separate in future)
    return errors + warnings


def validate_llm_config(scenario: Scenario) -> List[str]:
    """Validate LLM configuration.

    Checks:
    - Model strings follow OpenRouter format
    - Temperature is in valid range [0, 2]
    - Max tokens is reasonable (> 100, < 100000)

    Returns:
        List of validation errors and warnings
    """
    errors = []
    config = scenario.config.llm

    # Validate temperature
    if not 0 <= config.temperature <= 2:
        errors.append(f"Temperature {config.temperature} outside valid range [0, 2]")

    # Validate max_tokens
    if config.max_tokens < 100:
        errors.append(f"max_tokens {config.max_tokens} is too low (minimum 100)")
    elif config.max_tokens > 100000:
        errors.append(f"max_tokens {config.max_tokens} is unusually high (maximum 100000)")

    # Validate model strings for each task
    task_fields = ["events", "rules", "metrics", "summary"]

    for task in task_fields:
        model_value = getattr(config, task)

        if isinstance(model_value, str):
            if not is_valid_model_string(model_value):
                errors.append(f"Task '{task}' has invalid model string: '{model_value}'")
        elif isinstance(model_value, list):
            for m in model_value:
                if not is_valid_model_string(m):
                    errors.append(f"Task '{task}' has invalid model in fallback list: '{m}'")

    # Validate actors field (can be str, list, or dict)
    if isinstance(config.actors, str):
        if not is_valid_model_string(config.actors):
            errors.append(f"Actors model has invalid string: '{config.actors}'")
    elif isinstance(config.actors, list):
        for m in config.actors:
            if not is_valid_model_string(m):
                errors.append(f"Actors model has invalid model in fallback list: '{m}'")
    elif isinstance(config.actors, dict):
        for actor_id, model_value in config.actors.items():
            if isinstance(model_value, str):
                if not is_valid_model_string(model_value):
                    errors.append(f"Actor '{actor_id}' has invalid model string: '{model_value}'")
            elif isinstance(model_value, list):
                for m in model_value:
                    if not is_valid_model_string(m):
                        errors.append(f"Actor '{actor_id}' has invalid model in fallback list: '{m}'")

    return errors


def validate_actor_references(scenario: Scenario) -> List[str]:
    """Validate that scenario.yaml actors match actor files.

    Checks:
    - All actors in config have corresponding files
    - No orphaned actor files (already in base validator)

    Returns:
        List of validation errors
    """
    errors = []

    # Check all configured actors have definitions
    for actor_id in scenario.config.actor_ids:
        if actor_id not in scenario.actors:
            errors.append(f"Actor '{actor_id}' defined in config but missing description file")

    return errors


def validate_time_config(scenario: Scenario) -> List[str]:
    """Validate start_date and time_scale.

    Checks:
    - start_date is in valid format (YYYY-MM or YYYY)
    - max_turns doesn't exceed reasonable limits

    Returns:
        List of validation errors
    """
    errors = []

    # Validate start_date format
    start_date = scenario.config.start_date
    if start_date:
        # Accept YYYY-MM or YYYY formats
        if not re.match(r'^\d{4}(-\d{2})?$', start_date):
            errors.append(f"start_date '{start_date}' has invalid format (expected YYYY-MM or YYYY)")
        else:
            # Try to parse if it's YYYY-MM
            if '-' in start_date:
                try:
                    datetime.strptime(start_date, '%Y-%m')
                except ValueError:
                    errors.append(f"start_date '{start_date}' is not a valid date")

    # Validate max_turns
    if scenario.config.max_turns < 1:
        errors.append(f"max_turns must be at least 1, got {scenario.config.max_turns}")
    elif scenario.config.max_turns > 100:
        errors.append(f"max_turns {scenario.config.max_turns} exceeds reasonable limit (100)")

    return errors


def validate_scenario(scenario_path: Path) -> ValidationResult:
    """Run all validation checks on a scenario.

    Performs comprehensive validation including:
    - Structural validation (config, actors, metrics, events)
    - Metric reference validation
    - Event probability validation
    - LLM configuration validation
    - Actor reference validation
    - Time configuration validation
    """
    errors = []
    warnings = []

    try:
        scenario = load_scenario(scenario_path)
    except Exception as e:
        return ValidationResult(errors=[f"Failed to load scenario: {str(e)}"])

    # 1. Basic Config Validation
    if not scenario.config.name:
        errors.append("Scenario name is missing")
    if not scenario.config.actor_ids:
        errors.append("No actors defined in config")

    # 2. Basic Actor Validation
    for actor_id in scenario.config.actor_ids:
        if actor_id not in scenario.actors:
            errors.append(f"Actor '{actor_id}' defined in config but missing description file")
        else:
            actor = scenario.actors[actor_id]
            if not actor.name:
                warnings.append(f"Actor '{actor_id}' has no display name")
            if not actor.short_description:
                warnings.append(f"Actor '{actor_id}' has no short description")

    # 3. Basic Metrics Validation
    if not scenario.metrics.metrics:
        warnings.append("No metrics defined")

    for m_id, metric in scenario.metrics.metrics.items():
        if metric.min_value >= metric.max_value:
            errors.append(f"Metric '{m_id}': min value must be less than max value")
        if not (metric.min_value <= metric.value <= metric.max_value):
            errors.append(f"Metric '{m_id}': start value {metric.value} outside range [{metric.min_value}, {metric.max_value}]")

    # 4. Basic Events Validation
    if not scenario.events:
        warnings.append("No events defined")

    for event in scenario.events:
        if not event.id:
            errors.append("Event found without ID")
        if not event.condition:
            warnings.append(f"Event '{event.id}' has no condition")

    # 5. Basic Content Validation
    if not scenario.context.strip():
        warnings.append("Context description is empty")

    if not scenario.metric_rules.strip():
        warnings.append("Metric rules are empty")

    # 6. Comprehensive Validation (New)
    errors.extend(validate_metric_references(scenario))
    errors.extend(validate_event_probabilities(scenario))
    errors.extend(validate_llm_config(scenario))
    errors.extend(validate_actor_references(scenario))
    errors.extend(validate_time_config(scenario))

    return ValidationResult(errors, warnings)
