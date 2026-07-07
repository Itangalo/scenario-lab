"""Anthropic LLM provider using the official SDK."""

import json
import os
from typing import Optional

from ..llm import LLMError, LLMResponse, LLMUnsupportedStructuredError
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """LLM backend adapter for the Anthropic Messages API."""

    name = "anthropic"

    # Class-level default so instances constructed without __init__ (tests)
    # still get caching behavior.
    _enable_prompt_caching: bool = True

    def __init__(
        self, api_key: Optional[str] = None, enable_prompt_caching: bool = True
    ) -> None:
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
        self._enable_prompt_caching = enable_prompt_caching

    def _system_param(self, system: str):
        """Return the system parameter, with prompt caching when enabled.

        The system prompt for a given task is stable across turns (scenario
        background, metrics list), while the user prompt changes every call.
        Marking the system block with an ephemeral cache_control lets repeated
        turn-loop calls read it from cache. Blocks below Anthropic's minimum
        cacheable length are silently not cached, so this is always safe.
        """
        if not self._enable_prompt_caching:
            return system
        return [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

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
                system=self._system_param(system),
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
        """Send a schema-constrained request via a forced tool call.

        ``schema`` is the array schema the caller expects. The Anthropic
        ``input_schema`` must have an object at the top level, so the array is
        wrapped under an ``events`` property; the tool-use input is unwrapped
        back to the array before returning. ``structured_data`` therefore matches
        the OpenRouter path (a list).
        """
        from ..llm import LLMRateLimitError

        input_schema = {
            "type": "object",
            "properties": {"events": schema},
            "required": ["events"],
        }
        tool = {
            "name": schema_name,
            "description": "Return the evaluated events as a structured array.",
            "input_schema": input_schema,
        }

        try:
            message = self._client.messages.create(
                model=model,
                system=self._system_param(system),
                messages=[{"role": "user", "content": user}],
                max_tokens=max_tokens,
                temperature=temperature,
                tools=[tool],
                tool_choice={"type": "tool", "name": schema_name},
            )
        except self._sdk.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit for {model}") from e
        except self._sdk.APIStatusError as e:
            # 4xx generally means the model/params don't support forced tools –
            # surface as unsupported so the caller falls back.
            status = getattr(e, "status_code", None)
            if isinstance(status, int) and 400 <= status < 500 and status != 429:
                raise LLMUnsupportedStructuredError(
                    f"Anthropic model {model} rejected structured tool call "
                    f"(HTTP {status})."
                ) from e
            raise LLMError(
                f"Anthropic API error {status} for {model}: {e.message}"
            ) from e
        except Exception as e:
            raise LLMError(f"Unexpected error from Anthropic for {model}: {e}") from e

        # Find the forced tool_use block and unwrap its input.
        tool_input = None
        for block in message.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == schema_name:
                tool_input = block.input
                break

        if not isinstance(tool_input, dict) or "events" not in tool_input:
            raise LLMUnsupportedStructuredError(
                f"Anthropic model {model} did not return a usable tool call."
            )

        structured = tool_input["events"]
        content = json.dumps(structured)

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

        return LLMResponse(
            content=content, raw_response=raw_response, structured_data=structured
        )

    def close(self) -> None:
        self._client.close()
