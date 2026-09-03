"""Tests for the OpenCode routing provider adapter.

The HTTP layer is faked; no opencode server is spawned. Lifecycle tests use
a fake Popen so no binary is needed either.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from scenario_lab.llm import LLMError, LLMTransientError, LLMUnsupportedStructuredError
from scenario_lab.providers.opencode import OpenCodeProvider


def _response(json_data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if status_code >= 400:
        mock_req = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=mock_req, response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None
    return mock_resp


def _make_provider(**kwargs):
    """Build a provider attached to a fake server URL (no spawning)."""
    return OpenCodeProvider(server_url="http://127.0.0.1:4099", **kwargs)


def _message_result(text="Hello", prompt=10, completion=5):
    return {
        "info": {},
        "parts": [
            {"type": "step-start"},
            {"type": "text", "text": text},
            {
                "type": "step-finish",
                "reason": "stop",
                "tokens": {"input": prompt, "output": completion},
                "cost": 0.0,
            },
        ],
    }


class TestOpenCodeComplete:
    def test_successful_completion(self):
        provider = _make_provider()
        calls = []

        def fake_request(method, path, payload=None, timeout=120.0):
            calls.append((method, path))
            if method == "POST" and path == "/session":
                return {"id": "ses_test"}
            if path == "/session/ses_test/message":
                assert payload["agent"] == "plan"
                assert payload["tools"] == {}
                assert payload["system"] == "sys"
                assert payload["model"] == {"providerID": "opencode", "modelID": "m"}
                return _message_result("Hi")
            return True

        with patch.object(provider, "_request", side_effect=fake_request):
            resp = provider.complete("sys", "usr", model="opencode/m", temperature=0.7, max_tokens=100)
        assert resp.content == "Hi"
        usage = resp.get_usage()
        assert usage is not None
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.provider == "opencode"
        # Session hygiene: created, messaged, deleted.
        assert ("DELETE", "/session/ses_test") in calls

    def test_model_id_is_split_for_opencode(self):
        provider = _make_provider()
        seen = {}

        def fake_request(method, path, payload=None, timeout=120.0):
            if method == "DELETE":
                return True
            if path == "/session":
                return {"id": "ses_x"}
            seen.update(payload["model"])
            return _message_result()

        with patch.object(provider, "_request", side_effect=fake_request):
            provider.complete("s", "u", model="openrouter/qwen/qwen3", temperature=0, max_tokens=1)
        assert seen == {"providerID": "openrouter", "modelID": "qwen/qwen3"}

    def test_bare_model_id_is_rejected(self):
        provider = _make_provider()
        with pytest.raises(LLMError, match="providerID"):
            provider.complete("s", "u", model="noslash", temperature=0, max_tokens=1)

    def test_empty_text_raises_value_error(self):
        """Empty replies raise ValueError so the router retries like other providers."""
        provider = _make_provider()

        def fake_request(method, path, payload=None, timeout=120.0):
            if path == "/session":
                return {"id": "ses_x"}
            return {"info": {}, "parts": [{"type": "step-finish", "reason": "stop"}]}

        with patch.object(provider, "_request", side_effect=fake_request):
            with pytest.raises(ValueError, match="no text content"):
                provider.complete("s", "u", model="a/b", temperature=0, max_tokens=1)

    def test_server_error_propagates(self):
        provider = _make_provider()
        with patch.object(provider, "_request", side_effect=LLMError("HTTP 500")):
            with pytest.raises(LLMError):
                provider.complete("s", "u", model="a/b", temperature=0, max_tokens=1)

    def test_structured_is_unsupported(self):
        """Structured output falls back to the legacy text path via the base class."""
        provider = _make_provider()
        with pytest.raises(LLMUnsupportedStructuredError):
            provider.complete_structured(
                "s", "u", model="a/b", temperature=0, max_tokens=1,
                schema={"type": "array"}, schema_name="events",
            )


class TestOpenCodeServerLifecycle:
    def test_missing_binary_raises_helpful_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("shutil.which", return_value=None):
                with pytest.raises(ValueError, match="not found on PATH"):
                    OpenCodeProvider()

    def test_immediate_exit_raises(self):
        import subprocess as _sp

        fake_proc = MagicMock()
        fake_proc.poll.return_value = 1
        fake_proc.returncode = 1
        with patch.dict("os.environ", {}, clear=True):
            with patch("shutil.which", return_value="/usr/bin/opencode"):
                with patch.object(_sp, "Popen", return_value=fake_proc):
                    with pytest.raises(LLMError, match="exited immediately"):
                        OpenCodeProvider()

    def test_close_terminates_spawned_server(self):
        provider = _make_provider()
        fake_proc = MagicMock()
        provider._process = fake_proc
        provider.close()
        fake_proc.terminate.assert_called_once()

    def test_transient_connection_error(self):
        provider = _make_provider()
        with patch.object(
            provider._client, "request", side_effect=httpx.ConnectError("refused")
        ):
            with pytest.raises(LLMTransientError, match="OpenCode server"):
                provider._request("GET", "/global/health")
