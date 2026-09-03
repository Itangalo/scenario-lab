"""Generic OpenAI-compatible LLM provider.

Covers any backend speaking the OpenAI chat-completions dialect:

- OpenAI itself (``OPENAI_API_KEY``, default base URL)
- Local servers: Ollama (``http://localhost:11434/v1``), LM Studio, vLLM
- OAuth-to-OpenAI proxy bridges (e.g. a local Codex-OAuth proxy)
- Any other OpenAI-compatible gateway

Endpoint selection mirrors how the coding CLIs do it: ``OPENAI_BASE_URL``
overrides the default, ``OPENAI_API_KEY`` authenticates (local servers
typically accept any non-empty value such as ``ollama``).
"""

import json
import os
import time
from typing import Optional

import httpx

from ..llm import (
    LLMCallTimeoutError,
    LLMError,
    LLMResponse,
    LLMTransientError,
    LLMUnsupportedStructuredError,
)
from .base import LLMProvider


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_CALL_TIMEOUT_SECONDS = 300


class OpenAICompatibleProvider(LLMProvider):
    """LLM backend adapter for OpenAI-compatible chat-completions APIs."""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        call_timeout_seconds: int = DEFAULT_CALL_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Set it in environment or pass to constructor. "
                "(Local servers such as Ollama accept any non-empty value, e.g. 'ollama'.)"
            )
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.call_timeout_seconds = call_timeout_seconds
        self._client = httpx.Client(timeout=120.0)

    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    @staticmethod
    def _extract_content(data: object, model: str = "") -> str:
        """Extract assistant text from an OpenAI-style response payload."""
        if not isinstance(data, dict):
            raise ValueError("Response payload was not a JSON object")

        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message", "")
            code = error.get("code", "")
            detail = f"{message} (code {code})".strip() if code else str(message)
            raise LLMError(f"Backend error for {model}: {detail}")
        if isinstance(error, str) and error.strip():
            raise LLMError(f"Backend error for {model}: {error.strip()}")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Response payload did not include choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("First choice was not an object")

        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content:
                return content
            if isinstance(content, list):
                text_parts: list[str] = []
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        text_parts.append(item["text"])
                if text_parts:
                    return "".join(text_parts)
            if isinstance(content, str):
                return content

        text = first_choice.get("text")
        if isinstance(text, str):
            return text

        raise ValueError("Response payload did not include assistant content")

    def _post_with_deadline(
        self, payload: dict, model: str, call_timeout_seconds: Optional[int] = None
    ) -> dict:
        """POST and parse JSON under a true wall-clock deadline.

        Same rationale as OpenRouterProvider: httpx applies its timeout per
        read operation, so the body is streamed and elapsed time is checked
        against a single deadline for the whole call.
        """
        timeout = call_timeout_seconds or self.call_timeout_seconds
        deadline = time.monotonic() + timeout
        chunks: list[bytes] = []

        with self._client.stream(
            "POST",
            self.completions_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            if time.monotonic() > deadline:
                raise LLMCallTimeoutError(
                    f"Call to {model} exceeded {timeout}s before response headers arrived"
                )
            response.raise_for_status()

            for chunk in response.iter_bytes():
                chunks.append(chunk)
                if time.monotonic() > deadline:
                    raise LLMCallTimeoutError(
                        f"Call to {model} exceeded {timeout}s while receiving the response body"
                    )

        body = b"".join(chunks)
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise LLMError(
                f"Backend returned non-JSON for {model}: {body[:200]!r}"
            ) from e

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
        """Send a single completion request to the configured endpoint."""
        from ..llm import LLMRateLimitError

        try:
            data = self._post_with_deadline(
                {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                model,
                call_timeout_seconds=call_timeout_seconds,
            )
            content = self._extract_content(data, model)
            return LLMResponse(content=content, raw_response=data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"Rate limit for {model}") from e
            raise LLMError(
                f"HTTP {e.response.status_code} from {self.base_url} for {model}"
            ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(
                f"Connection/timeout error from {self.base_url} for {model}: {e}"
            ) from e

    def complete_structured(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        schema: dict,
        schema_name: str,
        call_timeout_seconds: Optional[int] = None,
    ) -> LLMResponse:
        """Send a schema-constrained request via ``response_format``.

        Backends that reject ``response_format`` (many local models do) raise
        ``LLMUnsupportedStructuredError`` so the caller falls back to the
        legacy text-parsing path.
        """
        from ..llm import LLMRateLimitError

        try:
            data = self._post_with_deadline(
                {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": schema,
                        },
                    },
                },
                model,
                call_timeout_seconds=call_timeout_seconds,
            )
            content = self._extract_content(data, model)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"Rate limit for {model}") from e
            if 400 <= e.response.status_code < 500:
                raise LLMUnsupportedStructuredError(
                    f"Model {model} rejected structured output "
                    f"(HTTP {e.response.status_code})"
                ) from e
            raise LLMError(
                f"HTTP {e.response.status_code} from {self.base_url} for {model}"
            ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(
                f"Connection/timeout error from {self.base_url} for {model}: {e}"
            ) from e

        try:
            structured = json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMUnsupportedStructuredError(
                f"Model {model} returned non-JSON structured content."
            ) from e

        return LLMResponse(
            content=content, raw_response=data, structured_data=structured
        )

    def close(self) -> None:
        self._client.close()
