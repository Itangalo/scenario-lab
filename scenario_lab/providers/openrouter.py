"""OpenRouter LLM provider."""

import json
import os
import time
from typing import Optional

import httpx

from ..llm import LLMError, LLMResponse, LLMUnsupportedStructuredError
from .base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """LLM backend adapter for OpenRouter's chat-completions API."""

    name = "openrouter"
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Set it in environment or pass to constructor."
            )
        self._client = httpx.Client(timeout=120.0)

    @staticmethod
    def _extract_content(data: object) -> str:
        """Extract assistant text from an OpenRouter-style response payload."""
        if not isinstance(data, dict):
            raise ValueError("Response payload was not a JSON object")

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Response payload did not include choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("First choice was not an object")

        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
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

        text = first_choice.get("text")
        if isinstance(text, str):
            return text

        raise ValueError("Response payload did not include assistant content")

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
            response = self._client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()

            data = response.json()
            content = self._extract_content(data)
            return LLMResponse(content=content, raw_response=data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit for {model}") from e
            raise LLMError(f"HTTP {e.response.status_code} from OpenRouter for {model}") from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMError(f"Connection/timeout error from OpenRouter for {model}: {e}") from e

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
            response = self._client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
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
            )
            response.raise_for_status()

            data = response.json()
            content = self._extract_content(data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LLMRateLimitError(f"OpenRouter rate limit for {model}") from e
            # 4xx (except 429) typically means the model rejected response_format.
            if 400 <= e.response.status_code < 500:
                raise LLMUnsupportedStructuredError(
                    f"OpenRouter model {model} rejected structured output "
                    f"(HTTP {e.response.status_code})."
                ) from e
            raise LLMError(
                f"HTTP {e.response.status_code} from OpenRouter for {model}"
            ) from e

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            raise LLMError(
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
