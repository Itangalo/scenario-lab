"""Security tests for Scenario Lab."""

import pytest
from pathlib import Path
import tempfile
import yaml
from jinja2.exceptions import SecurityError, UndefinedError

from scenario_lab.loader import load_config, load_scenario
from scenario_lab.prompts import PromptBuilder
from scenario_lab.models import Scenario, ScenarioConfig, Metrics, Metric, WorldState, LLMConfig


def test_path_traversal_in_base_scenario():
    """Test that base scenario path cannot escape allowed directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create scenario directory structure
        scenario_dir = tmpdir / "scenarios" / "test-scenario"
        scenario_dir.mkdir(parents=True)

        # Create a malicious scenario.yaml that tries to escape to /etc/passwd
        malicious_config = {
            "name": "Malicious Scenario",
            "description": "Attempts path traversal",
            "base": "../../../etc/passwd",  # Try to escape to system files
            "time_scale": "6 months",
            "start_date": "2026-01",
            "max_turns": 5,
            "actors": ["test-actor"],
        }

        scenario_file = scenario_dir / "scenario.yaml"
        scenario_file.write_text(yaml.dump(malicious_config), encoding="utf-8")

        # Attempt to load should raise ValueError with security message
        with pytest.raises(ValueError, match="Security.*escape.*allowed directory"):
            load_config(scenario_file)


def test_path_traversal_with_relative_paths():
    """Test various path traversal attempts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        scenario_dir = tmpdir / "scenarios" / "test-scenario"
        scenario_dir.mkdir(parents=True)

        # Test cases of malicious paths
        malicious_paths = [
            "../../../../etc/passwd",
            "../../../home/user/.ssh/id_rsa",
            "../../../../../../bin/bash",
            "/etc/passwd",  # Absolute path
            "../../../../../tmp/evil",
        ]

        for malicious_path in malicious_paths:
            config = {
                "name": "Test",
                "description": "Test",
                "base": malicious_path,
                "time_scale": "6 months",
                "start_date": "2026-01",
                "max_turns": 5,
                "actors": ["test"],
            }

            scenario_file = scenario_dir / "scenario.yaml"
            scenario_file.write_text(yaml.dump(config), encoding="utf-8")

            with pytest.raises(ValueError, match="Security.*escape.*allowed directory"):
                load_config(scenario_file)


def test_legitimate_base_scenario():
    """Test that legitimate base scenario references work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create base scenario
        base_dir = tmpdir / "scenarios" / "base-scenario"
        base_dir.mkdir(parents=True)

        base_config = {
            "name": "Base Scenario",
            "description": "Base config",
            "time_scale": "6 months",
            "start_date": "2026-01",
            "max_turns": 10,
            "actors": ["base-actor"],
        }

        base_file = base_dir / "scenario.yaml"
        base_file.write_text(yaml.dump(base_config), encoding="utf-8")

        # Create derived scenario that references base (sibling directory)
        derived_dir = tmpdir / "scenarios" / "derived-scenario"
        derived_dir.mkdir(parents=True)

        derived_config = {
            "name": "Derived Scenario",
            "description": "Inherits from base",
            "base": "../base-scenario/scenario.yaml",  # Legitimate sibling reference
            "max_turns": 5,  # Override
        }

        derived_file = derived_dir / "scenario.yaml"
        derived_file.write_text(yaml.dump(derived_config), encoding="utf-8")

        # This should load successfully
        config = load_config(derived_file)

        # Verify inheritance worked
        assert config.name == "Derived Scenario"
        assert config.max_turns == 5  # Override applied
        assert config.time_scale == "6 months"  # Inherited from base
        assert "base-actor" in config.actor_ids  # Inherited from base


# =============================================================================
# Template Injection (SSTI) Security Tests
# =============================================================================


def test_template_injection_file_access_blocked():
    """Test that template injection cannot access files on the system."""
    # Create a minimal scenario with malicious custom template
    malicious_template = """
    Turn {{turn}}

    {{''.__class__.__mro__[1].__subclasses__()[104].__init__.__globals__['sys'].modules['os'].popen('cat /etc/passwd').read()}}
    """

    scenario = _create_test_scenario(custom_user_prompts={"events": malicious_template})
    builder = PromptBuilder(scenario)

    # Attempt to build prompt - should raise SecurityError or not execute malicious code
    with pytest.raises((SecurityError, UndefinedError)):
        template = builder._get_user_template("events")
        template.render(turn=1)


def test_template_injection_attribute_access_blocked():
    """Test that template injection cannot access dangerous object attributes.

    SandboxedEnvironment either raises SecurityError or returns empty/safe strings.
    """
    # These raise SecurityError when accessing chained dangerous attributes
    error_templates = [
        "{{''.__class__.__mro__}}",  # Chained dangerous access
        "{{().__class__.__bases__}}",  # Another common attack
        "{{[].__class__.__bases__[0].__subclasses__()}}",  # Subclasses attack
    ]

    for malicious_template in error_templates:
        scenario = _create_test_scenario(custom_user_prompts={"events": malicious_template})
        builder = PromptBuilder(scenario)

        template = builder._get_user_template("events")

        # Should raise SecurityError when trying to access dangerous attributes
        with pytest.raises(SecurityError):
            template.render(turn=1)

    # This returns empty string (safe behavior - no actual class info exposed)
    safe_empty_template = "{{''.__class__}}"
    scenario = _create_test_scenario(custom_user_prompts={"events": safe_empty_template})
    builder = PromptBuilder(scenario)
    template = builder._get_user_template("events")
    result = template.render(turn=1)
    # Verify no actual class information is exposed
    assert result.strip() == ""
    assert "<class" not in result


def test_template_injection_import_blocked():
    """Test that template injection cannot import modules."""
    from jinja2.exceptions import TemplateSyntaxError

    malicious_template = """
    {% import os %}
    {{os.system('whoami')}}
    """

    scenario = _create_test_scenario(custom_user_prompts={"events": malicious_template})
    builder = PromptBuilder(scenario)

    # Import statements have wrong syntax in Jinja2 - should raise TemplateSyntaxError
    with pytest.raises(TemplateSyntaxError):
        template = builder._get_user_template("events")
        template.render(turn=1)


def test_template_injection_code_execution_blocked():
    """Test various code execution attempts raise SecurityError or other safe errors.

    SandboxedEnvironment prevents access to dangerous attributes and methods.
    """
    dangerous_templates = [
        "{{().__class__.__bases__[0].__subclasses__()}}",
        "{{{}.__class__.__bases__[0].__subclasses__()[104]}}",
    ]

    for malicious_template in dangerous_templates:
        scenario = _create_test_scenario(custom_user_prompts={"events": malicious_template})
        builder = PromptBuilder(scenario)

        template = builder._get_user_template("events")

        # Should raise SecurityError or TypeError (safe errors that prevent execution)
        with pytest.raises((SecurityError, TypeError)):
            template.render(turn=1)


def test_safe_template_placeholders_work():
    """Test that legitimate template placeholders still work correctly."""
    safe_template = """
    It is now turn {{turn}}.

    Current metrics:
    ```json
    {{metrics_json}}
    ```

    World state: {{world_state}}
    """

    scenario = _create_test_scenario(custom_user_prompts={"events": safe_template})
    builder = PromptBuilder(scenario)

    template = builder._get_user_template("events")
    result = template.render(
        turn=5,
        metrics_json='{"ai_capability": 100}',
        world_state="AI has advanced significantly."
    )

    assert "turn 5" in result
    assert "ai_capability" in result
    assert "AI has advanced" in result


def test_default_templates_use_sandboxed_environment():
    """Test that even default (trusted) templates use sandboxed environment."""
    scenario = _create_test_scenario()
    builder = PromptBuilder(scenario)

    # Get a default template
    template = builder._get_user_template("events")

    # Verify it's from the sandboxed environment
    assert template.environment.__class__.__name__ == "SandboxedEnvironment"


# Helper function to create test scenario
def _create_test_scenario(custom_user_prompts=None):
    """Create a minimal test scenario for template injection tests."""
    config = ScenarioConfig(
        name="Test Scenario",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["test-actor"],
        llm=LLMConfig(),
    )

    metrics = Metrics(metrics={
        "test_metric": Metric(
            id="test_metric",
            description="Test metric",
            value=50.0,
            min_value=0.0,
            max_value=100.0,
            unit="points"
        )
    })

    world_state = WorldState(
        narrative="Initial state",
        turn=0,
        time_period="2026-01 to 2026-06"
    )

    scenario = Scenario(
        config=config,
        metrics=metrics,
        events=[],
        actors={},
        metric_rules="# Rules\n1. Test rule",
        world_state=world_state,
        context="Test context",
        custom_user_prompts=custom_user_prompts or {},
    )

    return scenario
