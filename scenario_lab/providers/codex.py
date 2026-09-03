"""Codex subscription provider (ChatGPT plan, OAuth).

Talks to the Codex backend (``https://chatgpt.com/backend-api/codex``) with
the ChatGPT OAuth tokens from ``~/.codex/auth.json`` – the same credential
store the Codex CLI uses – so simulation calls bill to the ChatGPT
subscription instead of API credits. Routes look like ``codex:gpt-5.6-sol``.

Backend contract (probed 2026-09-03, undocumented, may drift):

- ``POST /responses`` with ``{model, instructions, input, stream: true,
  store: false}``. ``store`` must be false and ``stream`` must be true or
  the backend rejects the call. ``temperature`` and ``max_output_tokens``
  are rejected as unsupported – sampling and output budget are owned by the
  Codex side, so the arguments are accepted for interface compatibility and
  otherwise ignored (same limitation as the opencode provider).
- Server-sent events; assistant text comes from
  ``response.output_text.done`` events, token usage from
  ``response.completed``. Error payloads carry a ``detail`` string.
- Access tokens expire; on a 401 the provider refreshes via
  ``https://auth.openai.com/oauth/token`` (refresh-token grant) and retries
  once, writing the new tokens back to ``~/.codex/auth.json``.

This is deliberately *not* the OpenAI Platform API: ChatGPT OAuth tokens
carry identity scopes and always 401 on ``api.openai.com``. Do not point
this provider there.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from ..llm import LLMError, LLMResponse, LLMTransientError
from .base import LLMProvider


CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
OAUTH_TOKEN_URL = "https://auth.openai.com/oauth/token"
OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
DEFAULT_CALL_TIMEOUT_SECONDS = 600


def _default_auth_path() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "auth.json"


class CodexProvider(LLMProvider):
    """LLM backend adapter for the Codex subscription backend."""

    name = "codex"

    def __init__(
        self,
        auth_path: Optional[str] = None,
        base_url: str = CODEX_BASE_URL,
        call_timeout_seconds: int = DEFAULT_CALL_TIMEOUT_SECONDS,
    ) -> None:
        self.auth_path = Path(auth_path or os.environ.get("CODEX_AUTH_PATH") or _default_auth_path())
        if not self.auth_path.is_file():
            raise ValueError(
                f"Codex auth file not found at {self.auth_path}. "
                "Sign in with `codex login` (ChatGPT plan) first."
            )
        self.base_url = base_url.rstrip("/")
        self.call_timeout_seconds = call_timeout_seconds
        self._client = httpx.Client(timeout=120.0)
        self._access_token: Optional[str] = None

    # -- credentials --------------------------------------------------------

    def _load_auth_file(self) -> dict:
        try:
            with open(self.auth_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise LLMError(f"Could not read Codex auth file {self.auth_path}: {e}") from e
        if not isinstance(data, dict):
            raise LLMError(f"Codex auth file {self.auth_path} has unexpected shape")
        return data

    def _get_access_token(self) -> str:
        if self._access_token is None:
            tokens = self._load_auth_file().get("tokens") or {}
            access = tokens.get("access_token")
            if not isinstance(access, str) or not access:
                raise LLMError(
                    f"No access_token in {self.auth_path}. Re-run `codex login`."
                )
            self._access_token = access
        return self._access_token

    def _refresh_access_token(self) -> str:
        """Refresh OAuth tokens and write them back to the auth file."""
        auth_data = self._load_auth_file()
        tokens = auth_data.get("tokens") or {}
        refresh = tokens.get("refresh_token")
        if not isinstance(refresh, str) or not refresh:
            raise LLMError(
                f"No refresh_token in {self.auth_path}. Re-run `codex login`."
            )
        try:
            resp = self._client.post(
                OAUTH_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh,
                    "client_id": OAUTH_CLIENT_ID,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            body = resp.json()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(f"Codex token refresh connection error: {e}") from e
        except httpx.HTTPStatusError as e:
            raise LLMError(
                f"Codex token refresh failed (HTTP {e.response.status_code}). "
                "Re-run `codex login`."
            ) from e
        except ValueError as e:
            raise LLMError(f"Codex token refresh returned non-JSON: {e}") from e

        new_access = body.get("access_token")
        new_refresh = body.get("refresh_token", refresh)
        if not isinstance(new_access, str) or not new_access:
            raise LLMError("Codex token refresh returned no access_token")
        auth_data["tokens"] = {
            **tokens,
            "access_token": new_access,
            "refresh_token": new_refresh,
        }
        if isinstance(body.get("id_token"), str):
            auth_data["tokens"]["id_token"] = body["id_token"]
        auth_data["last_refresh"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        try:
            mode = os.stat(self.auth_path).st_mode
            with open(self.auth_path, "w", encoding="utf-8") as f:
                json.dump(auth_data, f)
            os.chmod(self.auth_path, mode)
        except OSError as e:
            raise LLMError(f"Could not write refreshed tokens to {self.auth_path}: {e}") from e

        self._access_token = new_access
        return new_access

    # -- HTTP ----------------------------------------------------------------

    def _headers(self, access_token: str) -> dict:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

    def _stream_response_events(
        self, payload: dict, access_token: str, timeout: int
    ) -> tuple[str, dict]:
        """POST /responses and fold the SSE stream into (text, usage)."""
        deadline = time.monotonic() + timeout
        texts: list[str] = []
        usage: dict = {}
        refreshed = False

        def _do_request(token: str) -> httpx.Response:
            return self._client.post(
                f"{self.base_url}/responses",
                headers=self._headers(token),
                json=payload,
                timeout=timeout,
            )

        try:
            resp = _do_request(access_token)
            if resp.status_code == 401 and not refreshed:
                access_token = self._refresh_access_token()
                refreshed = True
                resp = _do_request(access_token)
            resp.raise_for_status()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(f"Connection/timeout error from Codex backend: {e}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                from ..llm import LLMRateLimitError

                raise LLMRateLimitError("Codex backend rate limit") from e
            detail = self._error_detail(e.response)
            raise LLMError(
                f"HTTP {e.response.status_code} from Codex backend"
                + (f": {detail}" if detail else "")
            ) from e

        try:
            for line in resp.iter_lines():
                if time.monotonic() > deadline:
                    raise LLMTransientError(
                        f"Codex backend call exceeded {timeout}s wall-clock deadline"
                    )
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[6:])
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                etype = event.get("type")
                if etype == "response.output_text.done" and isinstance(event.get("text"), str):
                    texts.append(event["text"])
                elif etype == "response.completed":
                    maybe_usage = (event.get("response") or {}).get("usage")
                    if isinstance(maybe_usage, dict):
                        usage = maybe_usage
                elif etype == "response.failed":
                    raise LLMError(
                        f"Codex backend reported failure: {json.dumps(event)[:300]}"
                    )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.StreamClosed) as e:
            raise LLMTransientError(f"Codex backend stream interrupted: {e}") from e
        finally:
            resp.close()

        return "".join(texts), usage

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text[:300]
        if isinstance(body, dict):
            detail = body.get("detail")
            if isinstance(detail, str):
                return detail[:300]
        return ""

    # -- LLMProvider ----------------------------------------------------------

    def complete(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        call_timeout_seconds: Optional[int] = None,
    ) -> LLMResponse:
        """Send one prompt through the Codex backend and return assistant text.

        ``temperature``/``max_tokens`` are accepted for interface
        compatibility; the backend rejects both, so Codex-side configuration
        owns sampling.
        """
        del temperature, max_tokens  # Rejected by the backend; Codex owns sampling.
        timeout = call_timeout_seconds or self.call_timeout_seconds
        payload = {
            "model": model,
            "instructions": system,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": user}]}],
            "stream": True,
            "store": False,
        }
        content, usage = self._stream_response_events(payload, self._get_access_token(), timeout)
        if not content.strip():
            raise ValueError(f"Codex model {model} returned no text content")

        prompt_tokens = int(usage.get("input_tokens", 0) or 0)
        completion_tokens = int(usage.get("output_tokens", 0) or 0)
        raw_response: dict = {
            "_provider": "codex",
            "model": model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": int(usage.get("total_tokens", 0) or 0)
                or (prompt_tokens + completion_tokens),
            },
        }
        return LLMResponse(content=content, raw_response=raw_response)

    def close(self) -> None:
        self._client.close()
