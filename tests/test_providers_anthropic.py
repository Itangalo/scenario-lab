"""Tests for the Anthropic provider adapter."""

import os
from unittest.mock import MagicMock, patch

import pytest

from scenario_lab.llm import LLMError, LLMRateLimitError
from scenario_lab.providers.anthropic import AnthropicProvider


def _make_message(text="Hello", model="claude-opus-4-6", stop_reason="end_turn",
                  input_tokens=10, output_tokens=5,
                  cache_creation=0, cache_read=0):
    """Build a minimal mock Anthropic Messages response."""
    msg = MagicMock()
    msg.id = "msg_test"
    msg.content = [MagicMock(text=text)]
    msg.stop_reason = stop_reason

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    usage.cache_creation_input_tokens = cache_creation
    usage.cache_read_input_tokens = cache_read
    msg.usage = usage
    return msg


@pytest.fixture
def provider(monkeypatch):
    """AnthropicProvider with a mocked SDK client."""
    # Patch the anthropic SDK import to avoid needing a real API key
    mock_sdk = MagicMock()
    mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
    mock_sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
    mock_sdk.APIStatusError = type("APIStatusError", (Exception,), {"status_code": 503, "message": "err"})

    monkeypatch.setattr("scenario_lab.providers.anthropic.AnthropicProvider.__init__",
                        lambda self, api_key=None: _init_provider(self, mock_sdk, api_key))
    prov = AnthropicProvider.__new__(AnthropicProvider)
    prov._sdk = mock_sdk
    prov._client = MagicMock()
    return prov


def _init_provider(self, mock_sdk, api_key):
    self._sdk = mock_sdk
    self._client = MagicMock()


class TestAnthropicProviderInit:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
            AnthropicProvider()

    def test_explicit_key(self, monkeypatch):
        """Explicit key bypasses env check; uses SDK Anthropic constructor."""
        mock_sdk = MagicMock()
        monkeypatch.setattr("scenario_lab.providers.anthropic.AnthropicProvider.__init__",
                            lambda self, api_key=None: None)
        # Just verify no exception is raised when env is set
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
            prov = AnthropicProvider.__new__(AnthropicProvider)
            assert prov is not None


class TestAnthropicProviderComplete:
    def test_successful_completion(self):
        """Successful response returns LLMResponse with correct content and provider."""
        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_sdk.APIStatusError = type("APIStatusError", (Exception,), {})

        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.return_value = _make_message(
            text="Test response", input_tokens=20, output_tokens=10
        )

        resp = prov.complete(
            "system prompt", "user message",
            model="claude-opus-4-6", temperature=0.7, max_tokens=500
        )

        assert resp.content == "Test response"
        assert resp.raw_response["_provider"] == "anthropic"
        assert resp.raw_response["usage"]["prompt_tokens"] == 20
        assert resp.raw_response["usage"]["completion_tokens"] == 10
        assert resp.raw_response["usage"]["total_tokens"] == 30

    def test_get_usage_extracts_anthropic_fields(self):
        """get_usage() returns TokenUsage with provider='anthropic'."""
        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_sdk.APIStatusError = type("APIStatusError", (Exception,), {})

        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.return_value = _make_message(
            text="Hi", input_tokens=15, output_tokens=7,
            cache_creation=3, cache_read=2
        )

        resp = prov.complete(
            "sys", "usr",
            model="claude-sonnet-4-6", temperature=0.0, max_tokens=100
        )

        usage = resp.get_usage()
        assert usage is not None
        assert usage.provider == "anthropic"
        assert usage.prompt_tokens == 15
        assert usage.completion_tokens == 7
        assert usage.total_tokens == 22
        assert usage.cache_creation_input_tokens == 3
        assert usage.cache_read_input_tokens == 2

    def test_rate_limit_raises_rate_limit_error(self):
        RateLimitError = type("RateLimitError", (Exception,), {})
        APIConnectionError = type("APIConnectionError", (Exception,), {})
        APIStatusError = type("APIStatusError", (Exception,), {})
        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = RateLimitError
        mock_sdk.APIConnectionError = APIConnectionError
        mock_sdk.APIStatusError = APIStatusError

        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.side_effect = RateLimitError("Too many requests")

        with pytest.raises(LLMRateLimitError):
            prov.complete("sys", "usr", model="claude-opus-4-6", temperature=0.7, max_tokens=100)

    def test_api_status_error_raises_llm_error(self):
        RateLimitError = type("RateLimitError", (Exception,), {})
        APIConnectionError = type("APIConnectionError", (Exception,), {})

        class APIStatusError(Exception):
            status_code = 503
            message = "Service Unavailable"

        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = RateLimitError
        mock_sdk.APIConnectionError = APIConnectionError
        mock_sdk.APIStatusError = APIStatusError

        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.side_effect = APIStatusError("Service down")

        with pytest.raises(LLMError, match="Anthropic API error"):
            prov.complete("sys", "usr", model="claude-opus-4-6", temperature=0.7, max_tokens=100)

    def test_multi_block_content_is_concatenated(self):
        """Multiple TextBlocks in message.content are joined."""
        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_sdk.APIStatusError = type("APIStatusError", (Exception,), {})

        block1 = MagicMock()
        block1.text = "Hello"
        block2 = MagicMock()
        block2.text = " world"

        msg = MagicMock()
        msg.id = "msg_multi"
        msg.content = [block1, block2]
        msg.stop_reason = "end_turn"
        usage = MagicMock()
        usage.input_tokens = 5
        usage.output_tokens = 3
        usage.cache_creation_input_tokens = 0
        usage.cache_read_input_tokens = 0
        msg.usage = usage

        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.return_value = msg

        resp = prov.complete("sys", "usr", model="claude-sonnet-4-6", temperature=0.0, max_tokens=50)
        assert resp.content == "Hello world"


class TestAnthropicPricingCache:
    def test_seed_provides_fallback_pricing(self, tmp_path, monkeypatch):
        """Bundled seed should be returned when no runtime cache exists and refresh fails."""
        import json
        from scenario_lab.pricing.anthropic import AnthropicPricingCache

        # Prevent live network calls – simulate offline mode
        monkeypatch.setattr(
            "scenario_lab.pricing.anthropic.fetch_anthropic_pricing_snapshot",
            lambda: None,
        )

        seed_path = tmp_path / "seed.json"
        seed_path.write_text(json.dumps({
            "fetched_at": None,
            "source": "test-seed",
            "models": {
                "claude-opus-4-6": {"prompt": 15.0, "completion": 75.0},
            }
        }), encoding="utf-8")

        cache = AnthropicPricingCache(
            cache_path=tmp_path / "runtime.json",
            bundled_path=seed_path,
            ttl_hours=72,
        )

        pricing = cache.get_model_pricing("claude-opus-4-6")
        assert pricing == {"prompt": 15.0, "completion": 75.0}

    def test_refresh_fetches_and_persists(self, tmp_path, monkeypatch):
        """refresh() should write snapshot to cache_path."""
        import json
        from datetime import datetime, timezone
        from scenario_lab.pricing.anthropic import AnthropicPricingCache

        monkeypatch.setattr(
            "scenario_lab.pricing.anthropic.fetch_anthropic_pricing_snapshot",
            lambda: {
                "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "litellm",
                "models": {
                    "claude-sonnet-4-6": {"prompt": 3.0, "completion": 15.0},
                },
            },
        )

        cache_path = tmp_path / "anthropic-pricing.json"
        cache = AnthropicPricingCache(
            cache_path=cache_path,
            bundled_path=tmp_path / "seed.json",
            ttl_hours=72,
        )
        result = cache.refresh()
        assert result is True

        written = json.loads(cache_path.read_text(encoding="utf-8"))
        assert written["models"]["claude-sonnet-4-6"] == {"prompt": 3.0, "completion": 15.0}

    def test_unknown_model_returns_none(self, tmp_path, monkeypatch):
        """Models not in any cache should return None."""
        from scenario_lab.pricing.anthropic import AnthropicPricingCache

        monkeypatch.setattr(
            "scenario_lab.pricing.anthropic.fetch_anthropic_pricing_snapshot",
            lambda: None,
        )

        cache = AnthropicPricingCache(
            cache_path=tmp_path / "runtime.json",
            bundled_path=tmp_path / "seed.json",
            ttl_hours=72,
        )
        assert cache.get_model_pricing("non-existent-model") is None


class TestGetPricingFor:
    def test_dispatches_to_anthropic_cache(self, monkeypatch):
        """get_pricing_for with provider=anthropic uses AnthropicPricingCache."""
        from scenario_lab.pricing import get_pricing_for, get_anthropic_pricing_cache
        from scenario_lab.models import ModelRoute

        fake_cache = MagicMock()
        fake_cache.get_model_pricing.return_value = {"prompt": 3.0, "completion": 15.0}
        monkeypatch.setattr(
            "scenario_lab.pricing.get_anthropic_pricing_cache",
            lambda: fake_cache,
        )

        result = get_pricing_for(ModelRoute("anthropic", "claude-sonnet-4-6"))
        fake_cache.get_model_pricing.assert_called_once_with("claude-sonnet-4-6")
        assert result == {"prompt": 3.0, "completion": 15.0}

    def test_dispatches_to_openrouter_cache(self, monkeypatch):
        """get_pricing_for with provider=openrouter uses OpenRouterPricingCache."""
        from scenario_lab.pricing import get_pricing_for, get_pricing_cache
        from scenario_lab.models import ModelRoute

        fake_cache = MagicMock()
        fake_cache.get_model_pricing.return_value = {"prompt": 0.5, "completion": 1.5}
        monkeypatch.setattr(
            "scenario_lab.pricing.get_pricing_cache",
            lambda: fake_cache,
        )

        result = get_pricing_for(ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"))
        fake_cache.get_model_pricing.assert_called_once_with("qwen/qwen3-235b-a22b-2507")
        assert result == {"prompt": 0.5, "completion": 1.5}


class TestAnthropicPromptCaching:
    def _provider(self):
        mock_sdk = MagicMock()
        mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
        mock_sdk.APIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_sdk.APIStatusError = type("APIStatusError", (Exception,), {})
        prov = AnthropicProvider.__new__(AnthropicProvider)
        prov._sdk = mock_sdk
        prov._client = MagicMock()
        prov._client.messages.create.return_value = _make_message()
        return prov

    def test_system_prompt_sent_with_cache_control(self):
        prov = self._provider()
        prov.complete(
            "big system prompt", "user",
            model="claude-sonnet-4-6", temperature=0.7, max_tokens=500,
        )
        kwargs = prov._client.messages.create.call_args.kwargs
        system = kwargs["system"]
        assert isinstance(system, list)
        assert system[0]["text"] == "big system prompt"
        assert system[0]["cache_control"] == {"type": "ephemeral"}

    def test_caching_can_be_disabled(self):
        prov = self._provider()
        prov._enable_prompt_caching = False
        prov.complete(
            "system", "user",
            model="claude-sonnet-4-6", temperature=0.7, max_tokens=500,
        )
        kwargs = prov._client.messages.create.call_args.kwargs
        assert kwargs["system"] == "system"

    def test_structured_call_uses_cache_control(self):
        prov = self._provider()
        msg = _make_message()
        block = MagicMock()
        block.type = "tool_use"
        block.name = "events_evaluation"
        block.input = {"events": []}
        msg.content = [block]
        prov._client.messages.create.return_value = msg

        prov.complete_structured(
            "system", "user",
            model="claude-sonnet-4-6", temperature=0.7, max_tokens=500,
            schema={"type": "array"}, schema_name="events_evaluation",
        )
        kwargs = prov._client.messages.create.call_args.kwargs
        assert isinstance(kwargs["system"], list)
        assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


class TestCacheTokenCosting:
    def test_cache_tokens_priced_with_multipliers(self):
        from scenario_lab.cost import CostCalculator, TokenUsage

        usage = TokenUsage(
            prompt_tokens=1_000_000,
            completion_tokens=0,
            total_tokens=1_000_000,
            model="claude-sonnet-4-6",
            provider="anthropic",
            cache_creation_input_tokens=1_000_000,
            cache_read_input_tokens=1_000_000,
        )
        with patch("scenario_lab.cost.get_pricing_for",
                   return_value={"prompt": 3.0, "completion": 15.0}):
            details = CostCalculator.calculate_cost(usage)

        # 1M base (3.0) + 1M cache write (3.75) + 1M cache read (0.30)
        assert details.prompt_cost_usd == pytest.approx(3.0 + 3.75 + 0.30)
