"""Tests for the OpenRouter provider adapter."""

import json
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scenario_lab.llm import LLMError, LLMRateLimitError
from scenario_lab.providers.openrouter import OpenRouterProvider


class _MockHTTPResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

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
        with patch.object(provider._client, "post", return_value=_success_response("Hi")):
            resp = provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)
        assert resp.content == "Hi"

    def test_rate_limit_raises_rate_limit_error(self):
        provider = OpenRouterProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=429)
        with patch.object(provider._client, "post", return_value=mock_resp):
            with pytest.raises(LLMRateLimitError):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_http_error_raises_llm_error(self):
        provider = OpenRouterProvider(api_key="key")
        mock_resp = _MockHTTPResponse({}, status_code=503)
        with patch.object(provider._client, "post", return_value=mock_resp):
            with pytest.raises(LLMError):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_network_error_raises_llm_error(self):
        provider = OpenRouterProvider(api_key="key")
        with patch.object(provider._client, "post", side_effect=httpx.ConnectError("fail")):
            with pytest.raises(LLMError, match="Connection"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_malformed_response_raises_value_error(self):
        """Malformed payloads raise ValueError so FallbackRouter can retry them."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client,
            "post",
            return_value=_MockHTTPResponse({"id": "no-choices"}),
        ):
            with pytest.raises(ValueError, match="choices"):
                provider.complete("sys", "usr", model="x/y", temperature=0.7, max_tokens=100)

    def test_content_array_is_flattened(self):
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client,
            "post",
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
