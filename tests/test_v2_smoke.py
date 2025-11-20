"""
V2 Integration Smoke Tests

Simple smoke tests to verify V2 components can be initialized and work together.
"""
import pytest
from pathlib import Path

from scenario_lab.loaders import load_metrics_config, load_validation_config
from scenario_lab.core.metrics_tracker_v2 import MetricsTrackerV2
from scenario_lab.core.context_manager import ContextManagerV2
from scenario_lab.core.qa_validator_v2 import QAValidatorV2


class TestV2ComponentInitialization:
    """Test that all V2 components can be initialized correctly"""

    def test_metrics_tracker_v2_initialization(self):
        """Test MetricsTrackerV2 can be created with valid config"""
        # Load test metrics config
        metrics_file = Path("scenarios/test-metrics-v2/metrics.yaml")

        if metrics_file.exists():
            config = load_metrics_config(metrics_file)
            assert config is not None

            tracker = MetricsTrackerV2(metrics_config=config, api_key="test-key")
            assert tracker is not None
            assert len(tracker.metrics) > 0

    def test_context_manager_v2_initialization(self):
        """Test ContextManagerV2 can be created with valid parameters"""
        manager = ContextManagerV2(
            window_size=3,
            summarization_model="openai/gpt-4o-mini"
        )

        assert manager is not None
        assert manager.window_size == 3
        assert manager.summarization_model == "openai/gpt-4o-mini"

    def test_qa_validator_v2_initialization(self):
        """Test QAValidatorV2 can be created with valid config"""
        from scenario_lab.schemas.validation import ValidationConfig, ValidationCheck

        config = ValidationConfig(
            validation_model="openai/gpt-4o-mini",
            checks={
                "test_check": ValidationCheck(
                    enabled=True,
                    severity="medium",
                    description="Test check"
                )
            }
        )

        validator = QAValidatorV2(validation_config=config, api_key="test-key")
        assert validator is not None
        assert validator.validation_model == "openai/gpt-4o-mini"
        assert validator.is_enabled()


class TestV2LoaderIntegration:
    """Test that V2 loaders work correctly"""

    def test_load_metrics_config_v2_format(self):
        """Test loading V2 format metrics.yaml"""
        metrics_file = Path("scenarios/test-metrics-v2/metrics.yaml")

        if metrics_file.exists():
            config = load_metrics_config(metrics_file)
            assert config is not None
            assert len(config.metrics) > 0
            assert config.export_format == "json"

    def test_load_validation_config_returns_none_for_missing_file(self):
        """Test loader returns None for nonexistent file"""
        validation_file = Path("nonexistent/validation-rules.yaml")
        config = load_validation_config(validation_file)
        assert config is None


class TestV2ParameterValidation:
    """Test that V2 components validate parameters correctly"""

    def test_context_manager_rejects_invalid_window_size(self):
        """Test ContextManagerV2 rejects invalid window_size"""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            ContextManagerV2(window_size=0)

    def test_context_manager_rejects_empty_model(self):
        """Test ContextManagerV2 rejects empty model"""
        with pytest.raises(ValueError, match="summarization_model cannot be empty"):
            ContextManagerV2(summarization_model="")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
