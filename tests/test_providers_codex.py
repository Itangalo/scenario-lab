"""Tests for the Codex subscription provider adapter.

HTTP is faked throughout; no credentials or network are needed. The auth
file is faked via tmp_path.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scenario_lab.llm import LLMError, LLMRateLimitError, LLMTransientError
from scenario_lab.providers.codex import CodexProvider


def _write_auth(path, access="ACCESS", refresh="REFRESH"):
    path.write_text(json.dumps({
        "auth_mode": "chatgpt",
        "tokens": {"access_token": access, "refresh_token": refresh, "account_id": "acc"},
        "last_refresh": "2026-01-01T00:00:00.000000Z",
    }))


def _sse_response(lines, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.iter_lines.return_value = iter(lines)
    if status_code >= 400:
        mock_resp.json.return_value = {"detail": "bad stuff"}
        mock_resp.text = "bad stuff"
        mock_req = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=mock_req, response=mock_resp
        )
    else:
        mock_resp.raise_for_status.return_value = None
    mock_resp.close.return_value = None
    return mock_resp


def _completed_sse(text="Hello", prompt=18, completion=7):
    return [
        'data: {"type": "response.created"}',
        'data: {"type": "response.output_text.done", "text": "%s"}' % text,
        'data: {"type": "response.completed", "response": {"usage": '
        '{"input_tokens": %d, "output_tokens": %d, "total_tokens": %d}}}' % (prompt, completion, prompt + completion),
    ]


class TestCodexComplete:
    def test_successful_completion(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        with patch.object(
            provider._client, "post", return_value=_sse_response(_completed_sse("Hi"))
        ) as mock_post:
            resp = provider.complete("sys", "usr", model="gpt-5.6-sol", temperature=0.7, max_tokens=100)
        assert resp.content == "Hi"
        usage = resp.get_usage()
        assert usage is not None
        assert (usage.prompt_tokens, usage.completion_tokens) == (18, 7)
        assert usage.provider == "codex"
        # Payload contract: instructions, list input, forced stream/store.
        _, kwargs = mock_post.call_args
        body = kwargs["json"]
        assert body["instructions"] == "sys"
        assert body["stream"] is True and body["store"] is False
        assert "temperature" not in body and "max_output_tokens" not in body
        assert kwargs["headers"]["Authorization"] == "Bearer ACCESS"

    def test_missing_auth_file_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            CodexProvider(auth_path=str(tmp_path / "nope.json"))

    def test_empty_text_raises_value_error(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        with patch.object(
            provider._client, "post", return_value=_sse_response(['data: {"type": "response.completed", "response": {}}'])
        ):
            with pytest.raises(ValueError, match="no text content"):
                provider.complete("s", "u", model="m", temperature=0, max_tokens=1)

    def test_401_refreshes_and_retries_once(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth, access="OLD", refresh="REFRESH")
        provider = CodexProvider(auth_path=str(auth))

        unauthorized = _sse_response([], status_code=401)
        ok = _sse_response(_completed_sse("After refresh"))

        with patch.object(provider._client, "post", side_effect=[unauthorized, ok]) as mock_post:
            with patch.object(
                provider, "_refresh_access_token", return_value="NEW"
            ) as mock_refresh:
                # Bypass file write; simulate the token update.
                def _fake_refresh():
                    provider._access_token = "NEW"
                    return "NEW"
                mock_refresh.side_effect = _fake_refresh
                resp = provider.complete("s", "u", model="m", temperature=0, max_tokens=1)
        assert resp.content == "After refresh"
        second_headers = mock_post.call_args_list[1][1]["headers"]
        assert second_headers["Authorization"] == "Bearer NEW"

    def test_rate_limit_raises_rate_limit_error(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        with patch.object(
            provider._client, "post", return_value=_sse_response([], status_code=429)
        ):
            with pytest.raises(LLMRateLimitError):
                provider.complete("s", "u", model="m", temperature=0, max_tokens=1)

    def test_backend_error_detail_surfaced(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        with patch.object(
            provider._client, "post", return_value=_sse_response([], status_code=400)
        ):
            with pytest.raises(LLMError, match="bad stuff"):
                provider.complete("s", "u", model="m", temperature=0, max_tokens=1)

    def test_network_error_is_transient(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        with patch.object(provider._client, "post", side_effect=httpx.ConnectError("fail")):
            with pytest.raises(LLMTransientError):
                provider.complete("s", "u", model="m", temperature=0, max_tokens=1)


class TestCodexRefresh:
    def test_refresh_writes_tokens_back(self, tmp_path):
        import os

        auth = tmp_path / "auth.json"
        _write_auth(auth)
        os.chmod(auth, 0o600)
        provider = CodexProvider(auth_path=str(auth))

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "access_token": "NEW_ACCESS",
            "refresh_token": "NEW_REFRESH",
            "id_token": "NEW_ID",
        }
        with patch.object(provider._client, "post", return_value=mock_resp):
            token = provider._refresh_access_token()
        assert token == "NEW_ACCESS"
        saved = json.loads(auth.read_text())
        assert saved["tokens"]["access_token"] == "NEW_ACCESS"
        assert saved["tokens"]["refresh_token"] == "NEW_REFRESH"
        assert saved["tokens"]["id_token"] == "NEW_ID"
        assert "last_refresh" in saved
        assert oct(os.stat(auth).st_mode & 0o777) == "0o600"

    def test_refresh_failure_is_hard_error(self, tmp_path):
        auth = tmp_path / "auth.json"
        _write_auth(auth)
        provider = CodexProvider(auth_path=str(auth))
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_resp
        )
        with patch.object(provider._client, "post", return_value=mock_resp):
            with pytest.raises(LLMError, match="refresh failed"):
                provider._refresh_access_token()
