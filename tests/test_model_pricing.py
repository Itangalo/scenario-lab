"""
Tests for Model Pricing module

Tests cost calculation, pricing lookup, and model classification.
"""
import pytest
from unittest.mock import patch, MagicMock

from scenario_lab.utils.model_pricing import (
    calculate_cost,
    get_model_pricing,
    estimate_cost,
    is_free_model,
    is_expensive_model,
    get_popular_models,
    fetch_openrouter_models,
    MODEL_PRICING,
)


class TestCalculateCost:
    """Tests for calculate_cost function"""

    def test_calculate_cost_known_model(self):
        """Test cost calculation for a known model"""
        # GPT-4o-mini: $0.15 input, $0.60 output per 1M tokens
        cost = calculate_cost("openai/gpt-4o-mini", 1000, 500)

        expected_input = (1000 / 1_000_000) * 0.15
        expected_output = (500 / 1_000_000) * 0.60
        expected_total = expected_input + expected_output

        assert abs(cost - expected_total) < 0.0000001

    def test_calculate_cost_expensive_model(self):
        """Test cost calculation for an expensive model"""
        # Claude 3 Opus: $15 input, $75 output per 1M tokens
        cost = calculate_cost("anthropic/claude-3-opus", 10000, 5000)

        expected_input = (10000 / 1_000_000) * 15.00
        expected_output = (5000 / 1_000_000) * 75.00
        expected_total = expected_input + expected_output

        assert abs(cost - expected_total) < 0.0000001

    def test_calculate_cost_local_model_ollama(self):
        """Test that Ollama models are free"""
        cost = calculate_cost("ollama/llama3.1:70b", 100000, 50000)
        assert cost == 0.0

    def test_calculate_cost_local_model_prefix(self):
        """Test that local/ prefix models are free"""
        cost = calculate_cost("local/my-model", 100000, 50000)
        assert cost == 0.0

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        cost = calculate_cost("openai/gpt-4o", 0, 0)
        assert cost == 0.0

    def test_calculate_cost_unknown_model_uses_default(self):
        """Test that unknown models use default pricing"""
        # Unknown model should use default (gpt-4o-mini level: $0.15/$0.60)
        cost = calculate_cost("unknown/model-xyz", 1_000_000, 1_000_000)
        expected = 0.15 + 0.60  # Default pricing
        assert abs(cost - expected) < 0.01


class TestGetModelPricing:
    """Tests for get_model_pricing function"""

    def test_get_pricing_known_model(self):
        """Test getting pricing for a known model"""
        input_cost, output_cost = get_model_pricing("openai/gpt-4o")
        assert input_cost == 2.50
        assert output_cost == 10.00

    def test_get_pricing_local_model(self):
        """Test that local models return zero pricing"""
        input_cost, output_cost = get_model_pricing("ollama/mistral")
        assert input_cost == 0.0
        assert output_cost == 0.0

    def test_get_pricing_unknown_model_returns_default(self):
        """Test that unknown models return default pricing"""
        input_cost, output_cost = get_model_pricing("unknown/model")
        # Default is gpt-4o-mini level
        assert input_cost == 0.15
        assert output_cost == 0.60


class TestEstimateCost:
    """Tests for estimate_cost function"""

    def test_estimate_cost_same_as_calculate(self):
        """Test that estimate_cost returns same result as calculate_cost"""
        model = "openai/gpt-4o-mini"
        input_tokens = 5000
        output_tokens = 2000

        estimated = estimate_cost(model, input_tokens, output_tokens)
        calculated = calculate_cost(model, input_tokens, output_tokens)

        assert estimated == calculated


class TestIsFreeModel:
    """Tests for is_free_model function"""

    def test_ollama_models_are_free(self):
        """Test that Ollama models are identified as free"""
        assert is_free_model("ollama/llama3.1:70b") is True
        assert is_free_model("ollama/mistral") is True

    def test_local_models_are_free(self):
        """Test that local models are identified as free"""
        assert is_free_model("local/my-model") is True

    def test_free_tier_models_are_free(self):
        """Test that :free suffix models are identified as free"""
        assert is_free_model("meta-llama/llama-3.1-8b:free") is True

    def test_cloud_models_not_free(self):
        """Test that cloud models are not identified as free"""
        assert is_free_model("openai/gpt-4o") is False
        assert is_free_model("anthropic/claude-3-opus") is False


class TestIsExpensiveModel:
    """Tests for is_expensive_model function"""

    def test_opus_is_expensive(self):
        """Test that Claude 3 Opus is identified as expensive"""
        assert is_expensive_model("anthropic/claude-3-opus") is True

    def test_mini_not_expensive(self):
        """Test that GPT-4o-mini is not identified as expensive"""
        assert is_expensive_model("openai/gpt-4o-mini") is False

    def test_local_models_not_expensive(self):
        """Test that local models are not identified as expensive"""
        assert is_expensive_model("ollama/llama3.1:70b") is False

    def test_custom_threshold(self):
        """Test expensive detection with custom threshold"""
        # GPT-4o has $2.50 input cost and $10 output cost
        # is_expensive_model checks if EITHER cost is >= threshold
        assert is_expensive_model("openai/gpt-4o", threshold=2.0) is True
        assert is_expensive_model("openai/gpt-4o", threshold=15.0) is False


class TestGetPopularModels:
    """Tests for get_popular_models function"""

    @patch('scenario_lab.utils.model_pricing.fetch_openrouter_models')
    def test_returns_list_of_models(self, mock_fetch):
        """Test that popular models returns a list"""
        mock_fetch.return_value = {}

        models = get_popular_models()

        assert isinstance(models, list)
        assert len(models) > 0

    @patch('scenario_lab.utils.model_pricing.fetch_openrouter_models')
    def test_models_have_required_fields(self, mock_fetch):
        """Test that each model has required fields"""
        mock_fetch.return_value = {}

        models = get_popular_models()

        required_fields = ['id', 'name', 'description', 'tier',
                          'input_cost_per_1m', 'output_cost_per_1m', 'price_display']

        for model in models:
            for field in required_fields:
                assert field in model, f"Model missing field: {field}"

    @patch('scenario_lab.utils.model_pricing.fetch_openrouter_models')
    def test_includes_common_models(self, mock_fetch):
        """Test that common models are included"""
        mock_fetch.return_value = {}

        models = get_popular_models()
        model_ids = [m['id'] for m in models]

        # Should include these common models
        assert "openai/gpt-4o-mini" in model_ids
        assert "openai/gpt-4o" in model_ids
        assert "anthropic/claude-sonnet-4" in model_ids


class TestFetchOpenrouterModels:
    """Tests for fetch_openrouter_models function"""

    def test_fetch_with_api_key(self):
        """Test fetching models with API key"""
        # Reset cache
        import scenario_lab.utils.model_pricing as mp
        mp._dynamic_pricing_cache = {}
        mp._cache_loaded = False

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {
                        "id": "test/model",
                        "pricing": {
                            "prompt": 0.000001,  # $1 per 1M
                            "completion": 0.000002  # $2 per 1M
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = fetch_openrouter_models(api_key="test-key")

            assert "test/model" in result
            assert result["test/model"] == (1.0, 2.0)  # Converted to per 1M

    def test_fetch_without_api_key_returns_empty(self):
        """Test that fetching without API key returns empty dict"""
        # Reset cache
        import scenario_lab.utils.model_pricing as mp
        mp._dynamic_pricing_cache = {}
        mp._cache_loaded = False

        # Ensure no env var
        import os
        old_key = os.environ.pop('OPENROUTER_API_KEY', None)

        try:
            result = fetch_openrouter_models()
            assert result == {}
        finally:
            if old_key:
                os.environ['OPENROUTER_API_KEY'] = old_key


class TestModelPricingData:
    """Tests for the MODEL_PRICING data structure"""

    def test_all_prices_are_tuples(self):
        """Test that all pricing values are tuples"""
        for model, pricing in MODEL_PRICING.items():
            assert isinstance(pricing, tuple), f"{model} pricing is not a tuple"
            assert len(pricing) == 2, f"{model} pricing doesn't have 2 elements"

    def test_all_prices_are_non_negative(self):
        """Test that all prices are non-negative"""
        for model, (input_cost, output_cost) in MODEL_PRICING.items():
            assert input_cost >= 0, f"{model} has negative input cost"
            assert output_cost >= 0, f"{model} has negative output cost"

    def test_common_models_present(self):
        """Test that common models are in the pricing table"""
        expected_models = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash",
        ]

        for model in expected_models:
            assert model in MODEL_PRICING, f"Missing common model: {model}"

    def test_local_models_are_free(self):
        """Test that local model entries have zero cost"""
        assert MODEL_PRICING.get("ollama") == (0.0, 0.0)
        assert MODEL_PRICING.get("local") == (0.0, 0.0)
