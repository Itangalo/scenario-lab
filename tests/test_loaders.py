"""
Tests for Loader modules

Tests scenario and actor loading from YAML files.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from scenario_lab.loaders.actor_loader import (
    load_actor_yaml,
    load_all_actors,
    create_actor_from_config,
    create_v1_actor_for_migration,
)
from scenario_lab.loaders.scenario_loader import ScenarioLoader
from scenario_lab.core.actor import Actor


class TestLoadActorYaml:
    """Tests for load_actor_yaml function"""

    def test_load_valid_actor(self):
        """Test loading a valid actor YAML file"""
        actor_yaml = """
name: United States
short_name: us
llm_model: openai/gpt-4o-mini
system_prompt: You are the US President.
description: The United States of America.
goals:
  - Maintain global leadership
  - Protect the economy
constraints:
  - Constitutional limits on power
decision_style: Pragmatic
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(actor_yaml)
            f.flush()

            try:
                result = load_actor_yaml(Path(f.name))

                assert result['name'] == 'United States'
                assert result['short_name'] == 'us'
                assert result['llm_model'] == 'openai/gpt-4o-mini'
                assert len(result['goals']) == 2
            finally:
                os.unlink(f.name)

    def test_load_minimal_actor(self):
        """Test loading actor with only required fields"""
        actor_yaml = """
name: Test Actor
short_name: test
llm_model: openai/gpt-4o-mini
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(actor_yaml)
            f.flush()

            try:
                result = load_actor_yaml(Path(f.name))

                assert result['name'] == 'Test Actor'
                assert result['short_name'] == 'test'
            finally:
                os.unlink(f.name)

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error"""
        with pytest.raises(Exception):  # FileNotFoundError or similar
            load_actor_yaml(Path('/nonexistent/path/actor.yaml'))


class TestLoadAllActors:
    """Tests for load_all_actors function"""

    def test_load_multiple_actors(self):
        """Test loading multiple actor files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create actor files
            actor1 = """
name: Actor One
short_name: a1
llm_model: openai/gpt-4o-mini
"""
            actor2 = """
name: Actor Two
short_name: a2
llm_model: openai/gpt-4o
"""
            (Path(tmpdir) / 'actor1.yaml').write_text(actor1)
            (Path(tmpdir) / 'actor2.yaml').write_text(actor2)

            result = load_all_actors(Path(tmpdir))

            assert len(result) == 2
            assert 'a1' in result
            assert 'a2' in result
            assert result['a1']['name'] == 'Actor One'
            assert result['a2']['name'] == 'Actor Two'

    def test_load_no_actors_raises_error(self):
        """Test that empty directory raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="No actors found"):
                load_all_actors(Path(tmpdir))

    def test_load_nonexistent_directory_raises_error(self):
        """Test that nonexistent directory raises error"""
        with pytest.raises(FileNotFoundError):
            load_all_actors(Path('/nonexistent/actors'))

    def test_ignores_non_yaml_files(self):
        """Test that non-YAML files are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            actor_yaml = """
name: Test Actor
short_name: test
llm_model: model
"""
            (Path(tmpdir) / 'actor.yaml').write_text(actor_yaml)
            (Path(tmpdir) / 'readme.txt').write_text("This is not YAML")
            (Path(tmpdir) / 'notes.md').write_text("# Notes")

            result = load_all_actors(Path(tmpdir))

            assert len(result) == 1
            assert 'test' in result


class TestCreateActorFromConfig:
    """Tests for create_actor_from_config function"""

    def test_create_actor_basic(self):
        """Test creating actor from config dict"""
        config = {
            "name": "Test Actor",
            "short_name": "test",
            "llm_model": "openai/gpt-4o-mini",
            "goals": ["Goal 1"]
        }

        actor = create_actor_from_config(config)

        assert isinstance(actor, Actor)
        assert actor.name == "Test Actor"
        assert actor.short_name == "test"
        assert actor.goals == ["Goal 1"]

    def test_create_actor_with_scenario_prompt(self):
        """Test creating actor with scenario system prompt"""
        config = {
            "name": "Test",
            "short_name": "test",
            "llm_model": "model"
        }

        actor = create_actor_from_config(
            config,
            scenario_system_prompt="Simulation context"
        )

        assert actor.scenario_system_prompt == "Simulation context"

    def test_create_actor_with_json_mode(self):
        """Test creating actor with JSON mode enabled"""
        config = {
            "name": "Test",
            "short_name": "test",
            "llm_model": "model"
        }

        actor = create_actor_from_config(config, json_mode=True)

        assert actor.json_mode is True


class TestCreateV1ActorForMigration:
    """Tests for deprecated create_v1_actor_for_migration function"""

    def test_deprecation_warning(self):
        """Test that deprecation warning is logged"""
        config = {
            "name": "Test",
            "short_name": "test",
            "llm_model": "model"
        }

        with patch('scenario_lab.loaders.actor_loader.logger') as mock_logger:
            actor = create_v1_actor_for_migration(config)
            mock_logger.warning.assert_called_once()

        assert isinstance(actor, Actor)

    def test_still_creates_actor(self):
        """Test that it still creates a valid actor"""
        config = {
            "name": "Test Actor",
            "short_name": "test",
            "llm_model": "openai/gpt-4o-mini"
        }

        actor = create_v1_actor_for_migration(config, "Scenario prompt", True)

        assert actor.name == "Test Actor"
        assert actor.scenario_system_prompt == "Scenario prompt"
        assert actor.json_mode is True


class TestScenarioLoader:
    """Tests for ScenarioLoader class"""

    def test_init(self):
        """Test ScenarioLoader initialization"""
        loader = ScenarioLoader("/path/to/scenario")

        assert loader.scenario_path == Path("/path/to/scenario")
        assert loader.json_mode is False

    def test_init_with_json_mode(self):
        """Test ScenarioLoader initialization with JSON mode"""
        loader = ScenarioLoader("/path/to/scenario", json_mode=True)

        assert loader.json_mode is True

    @patch('scenario_lab.loaders.scenario_loader.load_and_validate_scenario')
    @patch('scenario_lab.loaders.scenario_loader.load_all_actors')
    @patch('scenario_lab.loaders.scenario_loader.create_actor_from_config')
    def test_load_scenario(self, mock_create_actor, mock_load_actors, mock_load_scenario):
        """Test loading a complete scenario"""
        # Mock scenario config
        mock_scenario_config = MagicMock()
        mock_scenario_config.model_dump.return_value = {
            "name": "Test Scenario",
            "initial_world_state": "The world is at peace.",
            "system_prompt": "Simulation context"
        }
        mock_validation = MagicMock()
        mock_validation.success = True
        mock_validation.errors = []
        mock_validation.warnings = []
        mock_load_scenario.return_value = (mock_scenario_config, mock_validation)

        # Mock actors
        mock_load_actors.return_value = {
            "us": {"name": "US", "short_name": "us", "llm_model": "model", "goals": []}
        }

        # Mock actor creation
        mock_actor = MagicMock()
        mock_actor.name = "US"
        mock_actor.short_name = "us"
        mock_actor.llm_model = "model"
        mock_actor.goals = []
        mock_create_actor.return_value = mock_actor

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create required directories and files
            (Path(tmpdir) / 'scenario.yaml').write_text("name: test")
            (Path(tmpdir) / 'actors').mkdir()
            (Path(tmpdir) / 'actors' / 'us.yaml').write_text("name: US\nshort_name: us\nllm_model: model")

            loader = ScenarioLoader(tmpdir)
            initial_state, actors, config = loader.load()

            assert initial_state.scenario_name == "Test Scenario"
            assert "us" in actors

    def test_load_invalid_scenario_raises_error(self):
        """Test that invalid scenario raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid scenario file
            (Path(tmpdir) / 'scenario.yaml').write_text("invalid: yaml: content:")

            loader = ScenarioLoader(tmpdir)

            with pytest.raises(Exception):  # YAML parsing or validation error
                loader.load()


class TestScenarioLoaderInitialState:
    """Tests for ScenarioLoader._create_initial_state method"""

    @patch('scenario_lab.loaders.scenario_loader.load_and_validate_scenario')
    @patch('scenario_lab.loaders.scenario_loader.load_all_actors')
    @patch('scenario_lab.loaders.scenario_loader.create_actor_from_config')
    def test_creates_correct_initial_state(self, mock_create_actor, mock_load_actors, mock_load_scenario):
        """Test that initial state is created correctly"""
        # Mock scenario config
        mock_scenario_config = MagicMock()
        mock_scenario_config.model_dump.return_value = {
            "name": "Test Scenario",
            "initial_world_state": "Initial state content",
            "system_prompt": ""
        }
        mock_validation = MagicMock()
        mock_validation.success = True
        mock_validation.errors = []
        mock_validation.warnings = []
        mock_load_scenario.return_value = (mock_scenario_config, mock_validation)

        # Mock actors
        mock_load_actors.return_value = {
            "a1": {"name": "Actor 1", "short_name": "a1", "llm_model": "model", "goals": ["Goal"]}
        }

        mock_actor = MagicMock()
        mock_actor.name = "Actor 1"
        mock_actor.short_name = "a1"
        mock_actor.llm_model = "model"
        mock_actor.goals = ["Goal"]
        mock_create_actor.return_value = mock_actor

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / 'scenario.yaml').write_text("name: test")
            (Path(tmpdir) / 'actors').mkdir()
            (Path(tmpdir) / 'actors' / 'a1.yaml').write_text("name: A1\nshort_name: a1\nllm_model: model")

            loader = ScenarioLoader(tmpdir)
            initial_state, actors, config = loader.load()

            # Check initial state
            assert initial_state.world_state.turn == 0
            assert initial_state.world_state.content == "Initial state content"
            assert "Actor 1" in initial_state.actors


class TestLoaderIntegration:
    """Integration tests for loader functionality"""

    def test_full_scenario_load(self):
        """Test loading a complete scenario from files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scenario.yaml
            scenario_yaml = """
name: Integration Test Scenario
description: A test scenario
initial_world_state: The world is at peace.
turns: 5
system_prompt: You are in a geopolitical simulation.
"""
            (Path(tmpdir) / 'scenario.yaml').write_text(scenario_yaml)

            # Create actors directory
            actors_dir = Path(tmpdir) / 'actors'
            actors_dir.mkdir()

            # Create actor files
            us_actor = """
name: United States
short_name: us
llm_model: openai/gpt-4o-mini
description: The United States of America
goals:
  - Maintain global leadership
"""
            china_actor = """
name: China
short_name: cn
llm_model: openai/gpt-4o-mini
description: The People's Republic of China
goals:
  - Economic growth
"""
            (actors_dir / 'us.yaml').write_text(us_actor)
            (actors_dir / 'china.yaml').write_text(china_actor)

            # Load scenario
            loader = ScenarioLoader(tmpdir)
            initial_state, actors, config = loader.load()

            # Verify scenario config
            assert config['name'] == 'Integration Test Scenario'
            assert config['turns'] == 5

            # Verify actors
            assert len(actors) == 2
            assert 'us' in actors
            assert 'cn' in actors

            # Verify initial state
            assert initial_state.scenario_name == 'Integration Test Scenario'
            assert "peace" in initial_state.world_state.content
