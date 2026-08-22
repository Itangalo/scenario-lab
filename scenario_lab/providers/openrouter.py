"""OpenRouter LLM provider."""

import json
import os
import time
from typing import Optional

import httpx

from ..llm import (
    LLMCallTimeoutError,
    LLMError,
    LLMReasoningBudgetError,
    LLMResponse,
    LLMTransientError,
    LLMUnsupportedStructuredError,
)
from .base import LLMProvider


DEFAULT_CALL_TIMEOUT_SECONDS = 300


class OpenRouterProvider(LLMProvider):
    """LLM backend adapter for OpenRouter's chat-completions API."""

    name = "openrouter"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        call_timeout_seconds: int = DEFAULT_CALL_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Set it in environment or pass to constructor."
            )
        self.call_timeout_seconds = call_timeout_seconds
        # Per-operation timeouts still apply as a first line of defence; the
        # wall-clock deadline in _post_with_deadline is what actually bounds a
        # call, since httpx resets its read timeout on every received chunk.
        self._client = httpx.Client(timeout=120.0)

    @staticmethod
    def _describe_provider_error(data: dict) -> str:
        """Extract OpenRouter's own error text from a payload, if present.

        Without this, a payload carrying a real explanation (rate limited, no
        capacity, moderation) surfaces only as "did not include choices", which
        sends the reader hunting for a bug that is not theirs.
        """
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            code = error.get("code")
            parts = [str(message) if message else "", f"(code {code})" if code else ""]
            detail = " ".join(p for p in parts if p).strip()
            if detail:
                return detail
        if isinstance(error, str) and error.strip():
            return error.strip()
        return ""

    @classmethod
    def _extract_content(cls, data: object, model: str = "") -> str:
        """Extract assistant text from an OpenRouter-style response payload."""
        if not isinstance(data, dict):
            raise ValueError("Response payload was not a JSON object")

        provider_error = cls._describe_provider_error(data)

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            if provider_error:
                raise LLMError(
                    f"OpenRouter returned no choices for {model}: {provider_error}"
                )
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
                    if not isinstance(item, dict):
                        continue
                    text = item.get("text")
                    if isinstance(text, str):
                        text_parts.append(text)
                if text_parts:
                    return "".join(text_parts)

            # A reasoning model that ran out of budget mid-thought returns empty
            # content alongside a populated reasoning field. Name that case so
            # the router stops retrying it and the user gets a fix to apply.
            cls._raise_if_reasoning_exhausted(first_choice, message, data, model)

            if isinstance(content, str):
                return content

        text = first_choice.get("text")
        if isinstance(text, str):
            return text

        if provider_error:
            raise LLMError(
                f"OpenRouter returned no assistant content for {model}: {provider_error}"
            )
        raise ValueError("Response payload did not include assistant content")

    @staticmethod
    def _raise_if_reasoning_exhausted(
        choice: dict, message: dict, data: dict, model: str
    ) -> None:
        """Raise LLMReasoningBudgetError when reasoning consumed the budget."""
        reasoning = message.get("reasoning") or message.get("reasoning_details")
        if not reasoning:
            return

        finish_reason = choice.get("finish_reason") or choice.get("native_finish_reason")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        completion_tokens = usage.get("completion_tokens")

        detail = f"finish_reason={finish_reason!r}"
        if completion_tokens is not None:
            detail += f", completion_tokens={completion_tokens}"

        raise LLMReasoningBudgetError(
            f"{model} is a reasoning model and spent its entire token budget on "
            f"reasoning without emitting content ({detail}). Raise llm.max_tokens, "
            f"or switch to a non-reasoning (instruct) model. Retrying as-is will "
            f"fail identically."
        )

    def _post_with_deadline(self, payload: dict, model: str) -> dict:
        """POST and parse JSON under a true wall-clock deadline.

        httpx applies its timeout per read operation, so a provider that emits
        bytes slowly resets the clock indefinitely and a call can block for as
        long as the connection stays open. Streaming the body and checking
        elapsed time against a single deadline bounds the whole call regardless
        of how the bytes arrive.
        """
        deadline = time.monotonic() + self.call_timeout_seconds
        chunks: list[bytes] = []

        with self._client.stream(
            "POST",
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            if time.monotonic() > deadline:
                raise LLMCallTimeoutError(
                    f"Call to {model} exceeded {self.call_timeout_seconds}s "
                    f"before response headers arrived"
                )
            response.raise_for_status()

            for chunk in response.iter_bytes():
                chunks.append(chunk)
                if time.monotonic() > deadline:
                    raise LLMCallTimeoutError(
                        f"Call to {model} exceeded {self.call_timeout_seconds}s "
                        f"while receiving the response body"
                    )

        body = b"".join(chunks)
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise LLMError(
                f"OpenRouter returned non-JSON for {model}: {body[:200]!r}"
            ) from e

    def complete(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Send a single completion request to OpenRouter.

        Raises LLMError on non-retryable failure, LLMRateLimitError on 429.
        The FallbackRouter handles retry/fallback logic.
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
                },
                model,
            )
            content = self._extract_content(data, model)
            return LLMResponse(content=content, raw_response=data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit for {model}") from e
            raise LLMError(
                f"HTTP {e.response.status_code} from OpenRouter for {model}"
                f"{self._http_error_detail(e)}"
            ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(
                f"Connection/timeout error from OpenRouter for {model}: {e}"
            ) from e

    @staticmethod
    def _http_error_detail(error: httpx.HTTPStatusError) -> str:
        """Append the provider's error body to an HTTP failure, when readable."""
        try:
            body = error.response.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - diagnostics must never mask the real error
            return ""
        body = body.strip()
        if not body:
            return ""
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return f": {body[:300]}"
        if isinstance(payload, dict):
            detail = OpenRouterProvider._describe_provider_error(payload)
            if detail:
                return f": {detail}"
        return f": {body[:300]}"

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
    ) -> LLMResponse:
        """Send a schema-constrained request via OpenRouter's ``response_format``.

        Many models reject ``response_format``; any provider-side rejection is
        surfaced as ``LLMUnsupportedStructuredError`` so the caller falls back to
        the legacy parse path. Rate limits and transient errors keep their normal
        types so FallbackRouter can retry them.
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
            )
            content = self._extract_content(data, model)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit for {model}") from e
            # 4xx (except 429) typically means the model rejected response_format.
            if 400 <= e.response.status_code < 500:
                raise LLMUnsupportedStructuredError(
                    f"OpenRouter model {model} rejected structured output "
                    f"(HTTP {e.response.status_code}){self._http_error_detail(e)}"
                ) from e
            raise LLMError(
                f"HTTP {e.response.status_code} from OpenRouter for {model}"
                f"{self._http_error_detail(e)}"
            ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMTransientError(
                f"Connection/timeout error from OpenRouter for {model}: {e}"
            ) from e

        try:
            structured = json.loads(content)
        except json.JSONDecodeError as e:
            # Schema-constrained output that is not valid JSON means the model
            # did not honor the contract – treat as unsupported and fall back.
            raise LLMUnsupportedStructuredError(
                f"OpenRouter model {model} returned non-JSON structured content."
            ) from e

        return LLMResponse(
            content=content, raw_response=data, structured_data=structured
        )

    def close(self) -> None:
        self._client.close()
