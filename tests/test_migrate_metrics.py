"""
Tests for the V1 to V2 metrics migration tool.
"""
import pytest
from scenario_lab.tools.migrate_metrics import (
    detect_v1_format,
    migrate_v1_to_v2,
    convert_data_type_to_v2_type,
    infer_range_from_prompt,
)
from scenario_lab.loaders.metrics_loader import load_metrics_config, _detect_v1_format
from scenario_lab.schemas.metrics import MetricsConfig
from pathlib import Path


class TestV1FormatDetection:
    """Tests for V1 format detection"""

    def test_detects_extraction_model(self):
        """Top-level extraction_model indicates V1"""
        data = {
            "extraction_model": "openai/gpt-4o-mini",
            "metrics": []
        }
        assert detect_v1_format(data) is True

    def test_detects_thresholds_section(self):
        """Separate thresholds section indicates V1"""
        data = {
            "metrics": [],
            "thresholds": {"metric1": {"warning": 5}}
        }
        assert detect_v1_format(data) is True

    def test_detects_dict_metrics(self):
        """Dict-based metrics indicate V1"""
        data = {
            "metrics": {
                "metric1": {"description": "test"}
            }
        }
        assert detect_v1_format(data) is True

    def test_detects_extraction_type_field(self):
        """extraction_type field in metric indicates V1"""
        data = {
            "metrics": [
                {"name": "test", "extraction_type": "llm"}
            ]
        }
        assert detect_v1_format(data) is True

    def test_detects_data_type_field(self):
        """data_type field in metric indicates V1"""
        data = {
            "metrics": [
                {"name": "test", "data_type": "float"}
            ]
        }
        assert detect_v1_format(data) is True

    def test_detects_aggregation_field(self):
        """aggregation field in metric indicates V1"""
        data = {
            "metrics": [
                {"name": "test", "aggregation": "sum"}
            ]
        }
        assert detect_v1_format(data) is True

    def test_v2_format_not_detected(self):
        """V2 format should not be detected as V1"""
        data = {
            "metrics": [
                {
                    "name": "test",
                    "description": "Test metric",
                    "type": "continuous",
                    "range": [0, 10],
                    "extraction": {"type": "llm", "prompt": "test"}
                }
            ]
        }
        assert detect_v1_format(data) is False


class TestDataTypeConversion:
    """Tests for V1 data_type to V2 type conversion"""

    def test_float_to_continuous(self):
        assert convert_data_type_to_v2_type("float") == "continuous"

    def test_integer_to_continuous(self):
        assert convert_data_type_to_v2_type("integer") == "continuous"

    def test_int_to_continuous(self):
        assert convert_data_type_to_v2_type("int") == "continuous"

    def test_string_to_categorical(self):
        assert convert_data_type_to_v2_type("string") == "categorical"

    def test_bool_to_boolean(self):
        assert convert_data_type_to_v2_type("bool") == "boolean"

    def test_unknown_defaults_continuous(self):
        assert convert_data_type_to_v2_type("unknown") == "continuous"


class TestRangeInference:
    """Tests for inferring range from LLM prompts"""

    def test_infers_0_to_10_scale(self):
        prompt = "Rate the cooperation level on a 0-10 scale"
        assert infer_range_from_prompt(prompt) == (0, 10)

    def test_infers_1_to_5_scale(self):
        prompt = "Rate on a 1-5 scale"
        assert infer_range_from_prompt(prompt) == (1, 5)

    def test_infers_scale_of_pattern(self):
        prompt = "Give a score on a scale of 0-100"
        assert infer_range_from_prompt(prompt) == (0, 100)

    def test_defaults_when_no_range(self):
        prompt = "Assess the general situation"
        assert infer_range_from_prompt(prompt) == (0, 10)


class TestV1ToV2Migration:
    """Tests for full V1 to V2 migration"""

    def test_migrates_dict_metrics(self):
        """V1 dict-based metrics are converted to V2 list"""
        v1_data = {
            "extraction_model": "openai/gpt-4o-mini",
            "metrics": {
                "test_metric": {
                    "description": "A test metric",
                    "extraction_type": "llm",
                    "extraction_prompt": "Rate from 0-10",
                    "data_type": "float"
                }
            }
        }

        v2_data = migrate_v1_to_v2(v1_data)

        assert "metrics" in v2_data
        assert isinstance(v2_data["metrics"], list)
        assert len(v2_data["metrics"]) == 1

        metric = v2_data["metrics"][0]
        assert metric["name"] == "test_metric"
        assert metric["type"] == "continuous"
        assert "extraction" in metric
        assert metric["extraction"]["type"] == "llm"
        assert "prompt" in metric["extraction"]

    def test_migrates_thresholds(self):
        """V1 thresholds section is migrated to per-metric thresholds"""
        v1_data = {
            "metrics": {
                "test_metric": {
                    "description": "Test",
                    "extraction_type": "pattern",
                    "pattern": r"\d+",
                    "data_type": "float"
                }
            },
            "thresholds": {
                "test_metric": {
                    "warning": 7.0,
                    "critical": 9.0
                }
            }
        }

        v2_data = migrate_v1_to_v2(v1_data)

        metric = v2_data["metrics"][0]
        assert metric["warning_threshold"] == 7.0
        assert metric["critical_threshold"] == 9.0

    def test_migrates_keyword_metric(self):
        """V1 keyword metrics are properly migrated"""
        v1_data = {
            "metrics": {
                "keyword_metric": {
                    "description": "Keyword count",
                    "extraction_type": "keyword",
                    "keywords": ["test", "example"],
                    "data_type": "integer"
                }
            }
        }

        v2_data = migrate_v1_to_v2(v1_data)

        metric = v2_data["metrics"][0]
        assert metric["extraction"]["type"] == "keyword"
        assert metric["extraction"]["keywords"] == ["test", "example"]
        assert metric["extraction"]["scoring"] == "count"

    def test_migrates_categorical_metric(self):
        """V1 string data_type becomes categorical with categories"""
        v1_data = {
            "metrics": {
                "outcome": {
                    "description": "Scenario outcome",
                    "extraction_type": "keyword",
                    "keywords": ["success", "failure"],
                    "data_type": "string"
                }
            }
        }

        v2_data = migrate_v1_to_v2(v1_data)

        metric = v2_data["metrics"][0]
        assert metric["type"] == "categorical"
        assert metric["categories"] == ["success", "failure"]
        assert "range" not in metric

    def test_result_validates(self):
        """Migrated output validates against V2 schema"""
        v1_data = {
            "extraction_model": "openai/gpt-4o-mini",
            "metrics": {
                "test_metric": {
                    "description": "A test metric",
                    "extraction_type": "llm",
                    "extraction_prompt": "Rate from 0-10",
                    "data_type": "float"
                }
            }
        }

        v2_data = migrate_v1_to_v2(v1_data)

        # Should not raise
        config = MetricsConfig(**v2_data)
        assert len(config.metrics) == 1


class TestLoaderV1Detection:
    """Tests for V1 detection in the metrics loader"""

    def test_loader_detect_v1_format(self):
        """Loader's _detect_v1_format returns indicators"""
        data = {
            "extraction_model": "test",
            "thresholds": {}
        }

        is_v1, indicators = _detect_v1_format(data)

        assert is_v1 is True
        assert len(indicators) >= 2
        assert any("extraction_model" in ind for ind in indicators)
        assert any("thresholds" in ind for ind in indicators)

    def test_loader_raises_on_v1_file(self):
        """Loading V1 file raises ValueError with helpful message"""
        v1_file = Path("tests/fixtures/sample_v1_metrics.yaml")

        if not v1_file.exists():
            pytest.skip("Sample V1 metrics file not found")

        with pytest.raises(ValueError) as exc_info:
            load_metrics_config(v1_file)

        error_msg = str(exc_info.value)
        assert "V1 metrics format detected" in error_msg
        assert "migrate_metrics" in error_msg
        assert "METRICS_MIGRATION.md" in error_msg
