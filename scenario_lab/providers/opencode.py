"""OpenCode routing provider.

Sends each simulation LLM call through an OpenCode server
(``opencode serve`` HTTP API): one fresh session per call, the system prompt
via the ``system`` field, the user prompt as a text part, ``agent: "plan``
with ``tools: {}`` so the model answers instead of acting.

This gives Scenario Lab access to every model authenticated in OpenCode
(``opencode auth login``) – subscription logins, API keys, OpenRouter free
models, local models – without managing each auth flow natively. Routes look
like ``opencode:<providerID>/<modelID>``, e.g.
``opencode:opencode/muse-spark-1.3-contributor-free`` or
``opencode:openrouter/qwen/qwen3-235b-a22b-2507`` (see ``opencode models``).

Server lifecycle: by default the provider spawns its own
``opencode serve`` on a free localhost port in an isolated working directory
(a bare temp dir, so project files like AGENTS.md do not leak into the
simulation context) and stops it on ``close()``. Set ``OPENCODE_SERVER_URL``
to attach to an already-running server instead.

Two opencode-side limitations, documented rather than hidden:

- The message API takes no per-call ``temperature``/``max_tokens``; those
  come from the OpenCode model configuration. The arguments are accepted
  for interface compatibility and otherwise ignored.
- Structured output is not implemented; the base class raises
  ``LLMUnsupportedStructuredError`` so callers use the legacy text path.
"""

import os
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Optional

import httpx

from ..llm import LLMError, LLMResponse, LLMTransientError
from .base import LLMProvider


DEFAULT_CALL_TIMEOUT_SECONDS = 600
_HEALTH_POLL_SECONDS = 30.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class OpenCodeProvider(LLMProvider):
    """LLM backend adapter routing through an OpenCode server."""

    name = "opencode"

    def __init__(
        self,
        server_url: Optional[str] = None,
        opencode_bin: Optional[str] = None,
        workdir: Optional[str] = None,
        call_timeout_seconds: int = DEFAULT_CALL_TIMEOUT_SECONDS,
    ) -> None:
        self.server_url = (server_url or os.environ.get("OPENCODE_SERVER_URL") or "").rstrip("/")
        self._process: Optional[subprocess.Popen] = None
        self._owned_workdir: Optional[str] = None
        self.call_timeout_seconds = call_timeout_seconds
        self._client = httpx.Client(timeout=120.0)

        if not self.server_url:
            self.server_url = self._spawn_server(
                opencode_bin=opencode_bin or os.environ.get("OPENCODE_BIN", "opencode"),
                workdir=workdir or os.environ.get("OPENCODE_WORKDIR"),
            )

    def _spawn_server(self, *, opencode_bin: str, workdir: Optional[str]) -> str:
        """Start ``opencode serve`` on a free port and wait for health."""
        if shutil.which(opencode_bin) is None:
            raise ValueError(
                f"OpenCode binary '{opencode_bin}' not found on PATH. "
                "Install OpenCode or set OPENCODE_SERVER_URL to a running server."
            )
        if workdir is None:
            workdir = tempfile.mkdtemp(prefix="scenario-lab-opencode-")
            self._owned_workdir = workdir

        port = _find_free_port()
        try:
            self._process = subprocess.Popen(
                [opencode_bin, "serve", "--port", str(port), "--hostname", "127.0.0.1"],
                cwd=workdir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as e:
            raise LLMError(f"Could not start opencode serve: {e}") from e

        url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + _HEALTH_POLL_SECONDS
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise LLMError(
                    f"opencode serve exited immediately (code {self._process.returncode}). "
                    f"Check that '{opencode_bin} serve' works in {workdir}."
                )
            try:
                resp = self._client.get(f"{url}/global/health", timeout=5.0)
                if resp.status_code == 200:
                    return url
            except httpx.HTTPError:
                pass
            time.sleep(0.5)
        self._stop_server()
        raise LLMTransientError(
            f"opencode serve did not become healthy within {_HEALTH_POLL_SECONDS}s at {url}"
        )

    def _stop_server(self) -> None:
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self._process.kill()
                except OSError:
                    pass
            self._process = None
        if self._owned_workdir is not None:
            shutil.rmtree(self._owned_workdir, ignore_errors=True)
            self._owned_workdir = None

    @staticmethod
    def _split_model(model: str) -> tuple[str, str]:
        """Split an opencode model id into (providerID, modelID)."""
        provider_id, sep, model_id = model.partition("/")
        if not sep or not provider_id or not model_id:
            raise LLMError(
                f"Invalid opencode model '{model}'. Use '<providerID>/<modelID>' "
                "as listed by `opencode models`, e.g. "
                "'opencode/muse-spark-1.3-contributor-free'."
            )
        return provider_id, model_id

    def _request(self, method: str, path: str, payload: Optional[dict] = None, timeout: float = 120.0) -> dict:
        url = f"{self.server_url}{path}"
        try:
            resp = self._client.request(method, url, json=payload, timeout=timeout)
            resp.raise_for_status()
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(f"OpenCode server at {self.server_url}: {e}") from e
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenCode server HTTP {e.response.status_code} on {path}") from e
        try:
            data = resp.json()
        except ValueError as e:
            raise LLMError(f"OpenCode server returned non-JSON on {path}") from e
        if not isinstance(data, dict):
            raise LLMError(f"OpenCode server returned unexpected shape on {path}")
        return data

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
        """Send one prompt through OpenCode and return the assistant text.

        ``temperature``/``max_tokens`` are accepted for interface
        compatibility; OpenCode owns sampling configuration server-side.
        """
        del temperature, max_tokens  # Owned by the OpenCode model configuration.
        timeout = call_timeout_seconds or self.call_timeout_seconds
        provider_id, model_id = self._split_model(model)

        session = self._request("POST", "/session", {"title": "scenario-lab call"})
        session_id = session.get("id")
        if not isinstance(session_id, str) or not session_id:
            raise LLMError("OpenCode server did not return a session id")

        try:
            # The message endpoint blocks until the reply completes, so the
            # per-call wall-clock deadline applies to this request directly.
            result = self._request(
                "POST",
                f"/session/{session_id}/message",
                {
                    "agent": "plan",
                    "model": {"providerID": provider_id, "modelID": model_id},
                    "system": system,
                    "tools": {},
                    "parts": [{"type": "text", "text": user}],
                },
                timeout=float(timeout),
            )
        except (LLMError, LLMTransientError):
            self._delete_session(session_id)
            raise

        texts: list[str] = []
        prompt_tokens = completion_tokens = 0
        reported_cost: Optional[float] = None
        for part in result.get("parts", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
            elif part.get("type") == "step-finish":
                tokens = part.get("tokens") or {}
                if isinstance(tokens, dict):
                    prompt_tokens = int(tokens.get("input", 0) or 0)
                    completion_tokens = int(tokens.get("output", 0) or 0)
                if isinstance(part.get("cost"), (int, float)):
                    reported_cost = float(part["cost"])

        self._delete_session(session_id)

        content = "".join(texts).strip()
        if not content:
            raise ValueError(f"OpenCode model {model} returned no text content")

        raw_response: dict = {
            "_provider": "opencode",
            "model": model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        if reported_cost is not None:
            raw_response["opencode_cost"] = reported_cost
        return LLMResponse(content=content, raw_response=raw_response)

    def _delete_session(self, session_id: str) -> None:
        try:
            self._request("DELETE", f"/session/{session_id}")
        except (LLMError, LLMTransientError):
            pass  # Best-effort hygiene; a stray session is harmless.

    def close(self) -> None:
        self._stop_server()
        self._client.close()
