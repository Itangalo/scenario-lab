"""
Unit tests for ContextManagerV2

Tests V2 context manager parameter validation.
"""
import pytest
from scenario_lab.core.context_manager import ContextManagerV2


class TestContextManagerV2Validation:
    """Test ContextManagerV2 parameter validation"""

    def test_initialization_valid(self):
        """Test valid initialization"""
        manager = ContextManagerV2(
            window_size=3,
            summarization_model="openai/gpt-4o-mini",
            max_cache_size=100
        )

        assert manager.window_size == 3
        assert manager.summarization_model == "openai/gpt-4o-mini"
        assert manager.max_cache_size == 100

    def test_initialization_defaults(self):
        """Test initialization with defaults"""
        manager = ContextManagerV2()

        assert manager.window_size == 3
        assert manager.summarization_model == "openai/gpt-4o-mini"
        assert manager.max_cache_size == 1000

    def test_window_size_validation_zero(self):
        """Test that window_size=0 raises ValueError"""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            ContextManagerV2(window_size=0)

    def test_window_size_validation_negative(self):
        """Test that negative window_size raises ValueError"""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            ContextManagerV2(window_size=-5)

    def test_max_cache_size_validation_zero(self):
        """Test that max_cache_size=0 raises ValueError"""
        with pytest.raises(ValueError, match="max_cache_size must be >= 1"):
            ContextManagerV2(max_cache_size=0)

    def test_max_cache_size_validation_negative(self):
        """Test that negative max_cache_size raises ValueError"""
        with pytest.raises(ValueError, match="max_cache_size must be >= 1"):
            ContextManagerV2(max_cache_size=-10)

    def test_summarization_model_validation_empty(self):
        """Test that empty summarization_model raises ValueError"""
        with pytest.raises(ValueError, match="summarization_model cannot be empty"):
            ContextManagerV2(summarization_model="")

    def test_summarization_model_validation_whitespace(self):
        """Test that whitespace-only summarization_model raises ValueError"""
        with pytest.raises(ValueError, match="summarization_model cannot be empty"):
            ContextManagerV2(summarization_model="   ")

    def test_window_size_one_is_valid(self):
        """Test that window_size=1 is valid"""
        manager = ContextManagerV2(window_size=1)
        assert manager.window_size == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
