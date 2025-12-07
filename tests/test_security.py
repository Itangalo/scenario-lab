"""Security tests for Scenario Lab."""

import pytest
from pathlib import Path
import tempfile
import yaml

from scenario_lab.loader import load_config


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
