"""
YAML loader with schema validation

Provides helpers to load and validate scenario configuration files.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pydantic import ValidationError

from scenario_lab.schemas.scenario import ScenarioConfig
from scenario_lab.schemas.actor import ActorConfig
from scenario_lab.schemas.metrics import MetricsConfig
from scenario_lab.schemas.validation import ValidationConfig


class ValidationResult:
    """Result of a validation attempt"""

    def __init__(self, success: bool, errors: List[str] = None, warnings: List[str] = None):
        self.success = success
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self):
        return self.success

    def __repr__(self):
        if self.success:
            return "ValidationResult(success=True)"
        return f"ValidationResult(success=False, errors={len(self.errors)})"


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Load a YAML file

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}")


def load_and_validate_scenario(yaml_path: Path) -> Tuple[ScenarioConfig, ValidationResult]:
    """
    Load and validate a scenario.yaml file

    Args:
        yaml_path: Path to scenario.yaml

    Returns:
        Tuple of (ScenarioConfig, ValidationResult)
    """
    errors = []
    warnings = []

    try:
        # Load YAML
        yaml_data = load_yaml_file(yaml_path)

        # Validate with Pydantic
        config = ScenarioConfig(**yaml_data)

        # Additional validation checks
        if config.turns and config.turns > 100:
            warnings.append(f"Scenario has {config.turns} turns - this may be expensive to run")

        if not config.system_prompt and not config.description:
            warnings.append("No system_prompt or description provided - consider adding context for actors")

        return config, ValidationResult(success=True, warnings=warnings)

    except FileNotFoundError as e:
        errors.append(str(e))
        return None, ValidationResult(success=False, errors=errors)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return None, ValidationResult(success=False, errors=errors)

    except ValidationError as e:
        # Format Pydantic errors nicely
        for error in e.errors():
            field = " → ".join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")

        return None, ValidationResult(success=False, errors=errors)

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return None, ValidationResult(success=False, errors=errors)


def load_and_validate_actor(yaml_path: Path) -> Tuple[ActorConfig, ValidationResult]:
    """
    Load and validate an actor YAML file

    Args:
        yaml_path: Path to actor.yaml

    Returns:
        Tuple of (ActorConfig, ValidationResult)
    """
    errors = []
    warnings = []

    try:
        # Load YAML
        yaml_data = load_yaml_file(yaml_path)

        # Validate with Pydantic
        config = ActorConfig(**yaml_data)

        # Additional validation checks
        if not config.goals:
            warnings.append("No goals specified - actor may not have clear objectives")

        if not config.system_prompt and not config.description:
            warnings.append("No system_prompt or description - actor behavior may be unclear")

        if config.llm_model and 'gpt-4' in config.llm_model.lower():
            warnings.append(f"Using expensive model ({config.llm_model}) - consider gpt-4o-mini for testing")

        return config, ValidationResult(success=True, warnings=warnings)

    except FileNotFoundError as e:
        errors.append(str(e))
        return None, ValidationResult(success=False, errors=errors)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return None, ValidationResult(success=False, errors=errors)

    except ValidationError as e:
        # Format Pydantic errors nicely
        for error in e.errors():
            field = " → ".join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")

        return None, ValidationResult(success=False, errors=errors)

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return None, ValidationResult(success=False, errors=errors)


def load_and_validate_metrics(yaml_path: Path) -> Tuple[MetricsConfig, ValidationResult]:
    """
    Load and validate a metrics.yaml file

    Args:
        yaml_path: Path to metrics.yaml

    Returns:
        Tuple of (MetricsConfig, ValidationResult)
    """
    errors = []
    warnings = []

    try:
        # Load YAML
        yaml_data = load_yaml_file(yaml_path)

        # Validate with Pydantic
        config = MetricsConfig(**yaml_data)

        # Additional validation checks
        llm_metrics = [m for m in config.metrics if m.extraction.type == 'llm']
        if len(llm_metrics) > 5:
            warnings.append(
                f"Scenario has {len(llm_metrics)} LLM-extracted metrics - "
                "this will increase costs significantly"
            )

        return config, ValidationResult(success=True, warnings=warnings)

    except FileNotFoundError as e:
        errors.append(str(e))
        return None, ValidationResult(success=False, errors=errors)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return None, ValidationResult(success=False, errors=errors)

    except ValidationError as e:
        # Format Pydantic errors nicely
        for error in e.errors():
            field = " → ".join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")

        return None, ValidationResult(success=False, errors=errors)

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return None, ValidationResult(success=False, errors=errors)


def load_and_validate_validation_rules(yaml_path: Path) -> Tuple[ValidationConfig, ValidationResult]:
    """
    Load and validate a validation-rules.yaml file

    Args:
        yaml_path: Path to validation-rules.yaml

    Returns:
        Tuple of (ValidationConfig, ValidationResult)
    """
    errors = []
    warnings = []

    try:
        # Load YAML
        yaml_data = load_yaml_file(yaml_path)

        # Validate with Pydantic
        config = ValidationConfig(**yaml_data)

        # Additional validation checks
        if config.halt_on_critical and config.max_issues_before_halt is None:
            warnings.append(
                "halt_on_critical=true without max_issues_before_halt - "
                "scenario will stop on first critical issue"
            )

        enabled_checks = [name for name, check in config.checks.items() if check.enabled]
        if not enabled_checks:
            warnings.append("No validation checks enabled - validation will not run")

        return config, ValidationResult(success=True, warnings=warnings)

    except FileNotFoundError as e:
        errors.append(str(e))
        return None, ValidationResult(success=False, errors=errors)

    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return None, ValidationResult(success=False, errors=errors)

    except ValidationError as e:
        # Format Pydantic errors nicely
        for error in e.errors():
            field = " → ".join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"{field}: {message}")

        return None, ValidationResult(success=False, errors=errors)

    except Exception as e:
        errors.append(f"Unexpected error: {e}")
        return None, ValidationResult(success=False, errors=errors)


def validate_scenario_directory(scenario_path: Path) -> Dict[str, ValidationResult]:
    """
    Validate all configuration files in a scenario directory

    Args:
        scenario_path: Path to scenario directory

    Returns:
        Dictionary mapping file type to ValidationResult
    """
    results = {}

    # Validate scenario.yaml
    scenario_file = scenario_path / "scenario.yaml"
    if scenario_file.exists():
        _, result = load_and_validate_scenario(scenario_file)
        results['scenario'] = result
    else:
        results['scenario'] = ValidationResult(
            success=False,
            errors=["scenario.yaml not found"]
        )

    # Validate actors
    actors_dir = scenario_path / "actors"
    if actors_dir.exists() and actors_dir.is_dir():
        actor_files = list(actors_dir.glob("*.yaml"))
        if not actor_files:
            results['actors'] = ValidationResult(
                success=False,
                errors=["No actor files found in actors/ directory"]
            )
        else:
            actor_errors = []
            actor_warnings = []
            for actor_file in actor_files:
                _, result = load_and_validate_actor(actor_file)
                if not result.success:
                    actor_errors.extend([f"{actor_file.name}: {e}" for e in result.errors])
                actor_warnings.extend([f"{actor_file.name}: {w}" for w in result.warnings])

            results['actors'] = ValidationResult(
                success=len(actor_errors) == 0,
                errors=actor_errors,
                warnings=actor_warnings
            )
    else:
        results['actors'] = ValidationResult(
            success=False,
            errors=["actors/ directory not found"]
        )

    # Validate metrics.yaml (optional)
    metrics_file = scenario_path / "metrics.yaml"
    if metrics_file.exists():
        _, result = load_and_validate_metrics(metrics_file)
        results['metrics'] = result

    # Validate validation-rules.yaml (optional)
    validation_file = scenario_path / "validation-rules.yaml"
    if validation_file.exists():
        _, result = load_and_validate_validation_rules(validation_file)
        results['validation'] = result

    return results
