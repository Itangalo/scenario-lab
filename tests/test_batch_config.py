"""
Tests for Batch Configuration module

Tests configuration loading, validation, and normalization.
"""
import pytest
import tempfile
from pathlib import Path

from scenario_lab.batch.batch_config import (
    BatchConfig,
    load_batch_config,
    _normalize_variations,
    _validate_required_fields,
    save_config_copy
)


class TestBatchConfig:
    """Tests for BatchConfig dataclass"""

    def test_from_dict_with_required_fields(self):
        """Test creating config with only required fields"""
        config_dict = {
            'experiment_name': 'Test Experiment',
            'base_scenario': '/path/to/scenario',
            'output_dir': '/path/to/output'
        }
        config = BatchConfig.from_dict(config_dict)

        assert config.experiment_name == 'Test Experiment'
        assert config.base_scenario == '/path/to/scenario'
        assert config.output_dir == '/path/to/output'
        assert config.runs_per_variation == 1  # default
        assert config.max_parallel == 1  # default
        assert config.budget_limit is None
        assert config.cost_per_run_limit is None

    def test_from_dict_with_all_fields(self):
        """Test creating config with all fields"""
        config_dict = {
            'experiment_name': 'Test Experiment',
            'base_scenario': '/path/to/scenario',
            'output_dir': '/path/to/output',
            'runs_per_variation': 5,
            'max_parallel': 4,
            'budget_limit': 100.0,
            'cost_per_run_limit': 5.0,
            'description': 'Test description',
            'variations': [{'type': 'test'}]
        }
        config = BatchConfig.from_dict(config_dict)

        assert config.runs_per_variation == 5
        assert config.max_parallel == 4
        assert config.budget_limit == 100.0
        assert config.cost_per_run_limit == 5.0
        assert config.description == 'Test description'
        assert len(config.variations) == 1

    def test_runs_dir_computed(self):
        """Test that runs_dir is computed correctly"""
        config = BatchConfig(
            experiment_name='Test',
            base_scenario='/path/to/scenario',
            output_dir='/path/to/output'
        )
        assert config.runs_dir == '/path/to/output/runs'


class TestNormalizeVariations:
    """Tests for variations normalization"""

    def test_list_format_unchanged(self):
        """Test that list format is returned unchanged"""
        variations = [{'type': 'actor_model', 'actor': 'a1', 'values': ['m1', 'm2']}]
        result = _normalize_variations(variations)
        assert result == variations

    def test_dict_format_converted(self):
        """Test that dict format is converted to list format"""
        variations = {
            'actor_models': {
                'actor1': ['model1', 'model2'],
                'actor2': ['model3']
            }
        }
        result = _normalize_variations(variations)

        assert len(result) == 2
        assert all(v['type'] == 'actor_model' for v in result)

        # Find actor1 variation
        actor1_var = next(v for v in result if v['actor'] == 'actor1')
        assert actor1_var['values'] == ['model1', 'model2']

    def test_empty_list_returns_empty(self):
        """Test that empty list returns empty list"""
        assert _normalize_variations([]) == []

    def test_empty_dict_returns_empty(self):
        """Test that empty dict returns empty list"""
        assert _normalize_variations({}) == []

    def test_none_returns_empty(self):
        """Test that None returns empty list"""
        assert _normalize_variations(None) == []


class TestValidateRequiredFields:
    """Tests for required field validation"""

    def test_all_required_fields_present(self):
        """Test no error when all required fields present"""
        config = {
            'experiment_name': 'Test',
            'base_scenario': '/path',
            'output_dir': '/output'
        }
        _validate_required_fields(config)  # Should not raise

    def test_missing_experiment_name(self):
        """Test error when experiment_name missing"""
        config = {'base_scenario': '/path', 'output_dir': '/output'}
        with pytest.raises(ValueError, match="experiment_name"):
            _validate_required_fields(config)

    def test_missing_base_scenario(self):
        """Test error when base_scenario missing"""
        config = {'experiment_name': 'Test', 'output_dir': '/output'}
        with pytest.raises(ValueError, match="base_scenario"):
            _validate_required_fields(config)

    def test_missing_output_dir(self):
        """Test error when output_dir missing"""
        config = {'experiment_name': 'Test', 'base_scenario': '/path'}
        with pytest.raises(ValueError, match="output_dir"):
            _validate_required_fields(config)


class TestLoadBatchConfig:
    """Tests for loading configuration from file"""

    def test_load_valid_config(self):
        """Test loading a valid configuration file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scenario directory
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text('name: Test')

            # Create config file
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test Experiment
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
runs_per_variation: 3
""")

            config = load_batch_config(str(config_path))

            assert config.experiment_name == 'Test Experiment'
            assert config.runs_per_variation == 3

    def test_load_missing_file(self):
        """Test loading non-existent file raises error"""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_batch_config('/nonexistent/config.yaml')

    def test_load_missing_scenario(self):
        """Test loading config with missing base scenario raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: /nonexistent/scenario
output_dir: {tmpdir}/output
""")

            with pytest.raises(FileNotFoundError, match="Base scenario not found"):
                load_batch_config(str(config_path))


class TestSaveConfigCopy:
    """Tests for saving configuration copy"""

    def test_save_config_copy(self):
        """Test that config copy is saved to output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scenario and config
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            # Create output dir
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            save_config_copy(config, str(config_path), str(output_dir))

            # Check copy exists
            copy_path = output_dir / 'batch-config.yaml'
            assert copy_path.exists()

    def test_save_config_copy_no_overwrite(self):
        """Test that existing copy is not overwritten"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text("experiment_name: Original\nbase_scenario: x\noutput_dir: y")

            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()

            # Create existing copy
            copy_path = output_dir / 'batch-config.yaml'
            copy_path.write_text("experiment_name: Existing")

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            save_config_copy(config, str(config_path), str(output_dir))

            # Check copy was not overwritten
            assert copy_path.read_text() == "experiment_name: Existing"
