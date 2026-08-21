"""Tests for the OpenRouter provider adapter."""

import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scenario_lab.llm import LLMError, LLMRateLimitError
from scenario_lab.providers.openrouter import OpenRouterProvider


class _MockHTTPResponse:
    """Stands in for an httpx streaming response.

    The provider streams the body so it can enforce a wall-clock deadline that
    httpx's per-read timeout cannot, so mocks must behave as context managers
    yielding bytes rather than exposing .json().
    """

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def read(self):
        return json.dumps(self.json_data).encode("utf-8")

    def iter_bytes(self):
        yield json.dumps(self.json_data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            mock_req = MagicMock()
            raise httpx.HTTPStatusError(
                "Error", request=mock_req, response=self
            )


def _success_response(content="Hello"):
    return _MockHTTPResponse(
        {"choices": [{"message": {"content": content}}]}
    )


class TestOpenRouterProviderInit:
    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY not set"):
                OpenRouterProvider()

    def test_explicit_key(self):
        provider = OpenRouterProvider(api_key="test_key")
        assert provider.api_key == "test_key"

    def test_key_from_env(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "env_key"}):
            provider = OpenRouterProvider()
            assert provider.api_key == "env_key"


class TestOpenRouterProviderComplete:
    def test_successful_completion(self):
        provider = OpenRouterProvider(api_key="key")
        with patch.object(provider._client, "stream", return_value=_success_response("Hi")):
            resp = provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)
        assert resp.content == "Hi"

    def test_rate_limit_raises_rate_limit_error(self):
        provider = OpenRouterProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=429)
        with patch.object(provider._client, "stream", return_value=mock_resp):
            with pytest.raises(LLMRateLimitError):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_http_error_raises_llm_error(self):
        provider = OpenRouterProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=503)
        with patch.object(provider._client, "stream", return_value=mock_resp):
            with pytest.raises(LLMError):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_network_error_raises_llm_error(self):
        provider = OpenRouterProvider(api_key="key")
        with patch.object(provider._client, "stream", side_effect=httpx.ConnectError("fail")):
            with pytest.raises(LLMError, match="Connection"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_malformed_response_raises_value_error(self):
        """Malformed payloads raise ValueError so FallbackRouter can retry them."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client,
            "stream",
            return_value=_MockHTTPResponse({"id": "no-choices"}),
        ):
            with pytest.raises(ValueError, match="choices"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_content_array_is_flattened(self):
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client,
            "stream",
            return_value=_MockHTTPResponse({
                "choices": [{
                    "message": {
                        "content": [
                            {"type": "text", "text": "Hello"},
                            {"type": "text", "text": " world"},
                        ]
                    }
                }]
            }),
        ):
            resp = provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)
        assert resp.content == "Hello world"


# ---------------------------------------------------------------------------
# Failure diagnosis and bounded calls
#
# Three failure modes cost real time during model evaluation: provider errors
# reported as "did not include choices" with the real reason discarded;
# reasoning models exhausting their budget and being retried identically three
# times; and single calls blocking for 11-23 minutes because httpx times out
# per read rather than per request.
# ---------------------------------------------------------------------------

class TestProviderErrorSurfacing:
    def test_provider_error_is_surfaced_when_choices_missing(self):
        """OpenRouter's own explanation must reach the user, not be discarded."""
        provider = OpenRouterProvider(api_key="key")
        payload = {"error": {"message": "Rate limit exceeded for free models", "code": 429}}
        with patch.object(provider._client, "stream", return_value=_MockHTTPResponse(payload)):
            with pytest.raises(LLMError, match="Rate limit exceeded for free models"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_plain_missing_choices_still_raises_value_error(self):
        """Without a provider error, keep the retryable ValueError behaviour."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client, "stream", return_value=_MockHTTPResponse({"id": "nothing"})
        ):
            with pytest.raises(ValueError, match="choices"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)


class TestReasoningBudgetDetection:
    def _exhausted(self):
        return _MockHTTPResponse({
            "choices": [{
                "finish_reason": "length",
                "message": {"content": "", "reasoning": "Let me think about this at length..."},
            }],
            "usage": {"completion_tokens": 32000},
        })

    def test_reasoning_exhaustion_raises_dedicated_error(self):
        from scenario_lab.llm import LLMReasoningBudgetError

        provider = OpenRouterProvider(api_key="key")
        with patch.object(provider._client, "stream", return_value=self._exhausted()):
            with pytest.raises(LLMReasoningBudgetError, match="reasoning model"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_reasoning_error_is_not_retried_by_router(self):
        """It is an LLMError, so FallbackRouter moves on instead of retrying."""
        from scenario_lab.llm import LLMError as _LLMError, LLMReasoningBudgetError

        assert issubclass(LLMReasoningBudgetError, _LLMError)

    def test_reasoning_present_with_content_is_fine(self):
        """Reasoning models that do produce content must work normally."""
        provider = OpenRouterProvider(api_key="key")
        response = _MockHTTPResponse({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": "the answer", "reasoning": "thinking..."},
            }]
        })
        with patch.object(provider._client, "stream", return_value=response):
            result = provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)
        assert result.content == "the answer"


class TestCallDeadline:
    def test_slow_body_is_aborted(self):
        """A trickling body must hit the wall-clock deadline, not stream forever."""
        from scenario_lab.llm import LLMCallTimeoutError

        provider = OpenRouterProvider(api_key="key", call_timeout_seconds=1)

        class _Trickle(_MockHTTPResponse):
            def iter_bytes(self):
                import time as _t
                for _ in range(100):
                    _t.sleep(0.05)
                    yield b"{"

        with patch.object(provider._client, "stream", return_value=_Trickle({})):
            with pytest.raises(LLMCallTimeoutError, match="exceeded 1s"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_timeout_is_configurable(self):
        provider = OpenRouterProvider(api_key="key", call_timeout_seconds=42)
        assert provider.call_timeout_seconds == 42

    def test_default_timeout_applied(self):
        provider = OpenRouterProvider(api_key="key")
        assert provider.call_timeout_seconds == 300
