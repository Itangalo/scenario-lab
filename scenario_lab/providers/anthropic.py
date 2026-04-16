"""Anthropic LLM provider using the official SDK."""

import os
from typing import Optional

from ..llm import LLMError, LLMResponse
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """LLM backend adapter for the Anthropic Messages API."""

    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None) -> None:
        try:
            import anthropic as _anthropic_sdk
        except ImportError as e:
            raise ImportError(
                "The 'anthropic' package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            ) from e

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Set it in environment or pass to constructor."
            )
        self._sdk = _anthropic_sdk
        self._client = _anthropic_sdk.Anthropic(api_key=resolved_key)

    def complete(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Send a single completion request to the Anthropic Messages API.

        Raises LLMRateLimitError on 429, LLMError on other non-retryable failures.
        The FallbackRouter handles retry/fallback logic.
        """
        from ..llm import LLMRateLimitError

        try:
            message = self._client.messages.create(
                model=model,
                system=system,
                messages=[{"role": "user", "content": user}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except self._sdk.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit for {model}") from e
        except self._sdk.APIStatusError as e:
            raise LLMError(
                f"Anthropic API error {e.status_code} for {model}: {e.message}"
            ) from e
        except Exception as e:
            raise LLMError(f"Unexpected error from Anthropic for {model}: {e}") from e

        # Concatenate all TextBlock content
        content_parts = []
        for block in message.content:
            if hasattr(block, "text"):
                content_parts.append(block.text)
        content = "".join(content_parts)

        # Build a normalized raw_response dict so get_usage() works
        usage = message.usage
        raw_response = {
            "_provider": "anthropic",
            "model": model,
            "id": message.id,
            "usage": {
                "prompt_tokens": usage.input_tokens,
                "completion_tokens": usage.output_tokens,
                "total_tokens": usage.input_tokens + usage.output_tokens,
                "cache_creation_input_tokens": getattr(
                    usage, "cache_creation_input_tokens", 0
                ) or 0,
                "cache_read_input_tokens": getattr(
                    usage, "cache_read_input_tokens", 0
                ) or 0,
            },
            "stop_reason": message.stop_reason,
        }

        return LLMResponse(content=content, raw_response=raw_response)

    def close(self) -> None:
        self._client.close()
