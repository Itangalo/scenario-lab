"""Tests for the generic OpenAI-compatible provider adapter."""

import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scenario_lab.llm import LLMError, LLMRateLimitError, LLMUnsupportedStructuredError
from scenario_lab.providers.openai_compatible import OpenAICompatibleProvider


class _MockHTTPResponse:
    """Stands in for an httpx streaming response (context manager yielding bytes)."""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def iter_bytes(self):
        yield json.dumps(self.json_data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            mock_req = MagicMock()
            raise httpx.HTTPStatusError("Error", request=mock_req, response=self)


def _success_response(content="Hello"):
    return _MockHTTPResponse({"choices": [{"message": {"content": content}}]})


class TestOpenAICompatibleInit:
    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
                OpenAICompatibleProvider()

    def test_explicit_key(self):
        provider = OpenAICompatibleProvider(api_key="test_key")
        assert provider.api_key == "test_key"

    def test_key_from_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env_key"}):
            provider = OpenAICompatibleProvider()
            assert provider.api_key == "env_key"

    def test_default_base_url(self):
        provider = OpenAICompatibleProvider(api_key="k")
        assert provider.completions_url == "https://api.openai.com/v1/chat/completions"

    def test_ollama_base_url_from_env(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "ollama", "OPENAI_BASE_URL": "http://localhost:11434/v1/"}):
            provider = OpenAICompatibleProvider()
            assert provider.completions_url == "http://localhost:11434/v1/chat/completions"

    def test_explicit_base_url(self):
        provider = OpenAICompatibleProvider(api_key="k", base_url="http://proxy:10531/v1")
        assert provider.completions_url == "http://proxy:10531/v1/chat/completions"


class TestOpenAICompatibleComplete:
    def test_successful_completion(self):
        provider = OpenAICompatibleProvider(api_key="key")
        with patch.object(provider._client, "stream", return_value=_success_response("Hi")):
            resp = provider.complete("sys", "usr", model="llama3.1", temperature=0.7, max_tokens=100)
        assert resp.content == "Hi"

    def test_rate_limit_raises_rate_limit_error(self):
        provider = OpenAICompatibleProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=429)
        with patch.object(provider._client, "stream", return_value=mock_resp):
            with pytest.raises(LLMRateLimitError):
                provider.complete("sys", "usr", model="m", temperature=0.7, max_tokens=100)

    def test_http_error_raises_llm_error(self):
        provider = OpenAICompatibleProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=503)
        with patch.object(provider._client, "stream", return_value=mock_resp):
            with pytest.raises(LLMError):
                provider.complete("sys", "usr", model="m", temperature=0.7, max_tokens=100)

    def test_network_error_is_transient(self):
        from scenario_lab.llm import LLMTransientError

        provider = OpenAICompatibleProvider(api_key="key")
        with patch.object(provider._client, "stream", side_effect=httpx.ConnectError("fail")):
            with pytest.raises(LLMTransientError, match="Connection"):
                provider.complete("sys", "usr", model="m", temperature=0.7, max_tokens=100)

    def test_malformed_response_raises_value_error(self):
        provider = OpenAICompatibleProvider(api_key="key")
        with patch.object(provider._client, "stream", return_value=_MockHTTPResponse({"id": "no-choices"})):
            with pytest.raises(ValueError, match="choices"):
                provider.complete("sys", "usr", model="m", temperature=0.7, max_tokens=100)

    def test_backend_error_is_surfaced(self):
        provider = OpenAICompatibleProvider(api_key="key")
        payload = {"error": {"message": "model not found", "code": "model_not_found"}}
        with patch.object(provider._client, "stream", return_value=_MockHTTPResponse(payload)):
            with pytest.raises(LLMError, match="model not found"):
                provider.complete("sys", "usr", model="m", temperature=0.7, max_tokens=100)


class TestOpenAICompatibleStructured:
    def test_structured_success(self):
        provider = OpenAICompatibleProvider(api_key="key")
        payload = {"choices": [{"message": {"content": '[{"id": "e1"}]'}}]}
        with patch.object(provider._client, "stream", return_value=_MockHTTPResponse(payload)):
            resp = provider.complete_structured(
                "sys", "usr", model="m", temperature=0.7, max_tokens=100,
                schema={"type": "array"}, schema_name="events",
            )
        assert resp.structured_data == [{"id": "e1"}]

    def test_structured_rejection_is_unsupported(self):
        """Backends rejecting response_format (many local models) must fall back."""
        provider = OpenAICompatibleProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=400)
        with patch.object(provider._client, "stream", return_value=mock_resp):
            with pytest.raises(LLMUnsupportedStructuredError):
                provider.complete_structured(
                    "sys", "usr", model="m", temperature=0.7, max_tokens=100,
                    schema={"type": "array"}, schema_name="events",
                )
