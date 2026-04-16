"""Shared LLM types and mock client."""

import json
import re
from dataclasses import dataclass
from typing import Optional, Union, List


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""

    pass


class LLMParseError(LLMError):
    """Could not parse LLM response."""

    pass


@dataclass
class LLMResponse:
    """Parsed response from LLM."""

    content: str
    raw_response: dict

    def get_finish_reason(self) -> Optional[str]:
        """Extract finish_reason from OpenRouter raw_response if available."""
        choices = self.raw_response.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                reason = first.get("finish_reason")
                if isinstance(reason, str):
                    return reason
        return None

    def extract_json(self) -> dict:
        """Extract JSON from markdown code block or raw content.

        Prefers fenced ```json blocks. If none are present, attempts to locate
        the first valid JSON object/array within the text using a streaming decoder.
        """
        # Prefer fenced ```json ... ``` blocks
        match = re.search(r"```json\s*(.*?)\s*```", self.content, re.DOTALL | re.IGNORECASE)
        if match:
            return json.loads(match.group(1))

        # Fallback: scan for first decodable JSON object/array in content
        decoder = json.JSONDecoder()
        text = self.content.strip()

        # Try whole content first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        for i, ch in enumerate(text):
            if ch not in "{[":
                continue
            try:
                obj, _ = decoder.raw_decode(text[i:])
                if isinstance(obj, (dict, list)):
                    return obj
            except json.JSONDecodeError:
                continue

        raise json.JSONDecodeError("No valid JSON found in response", self.content, 0)

    def extract_json_array(self) -> list:
        """Extract JSON array from response."""
        data = self.extract_json()
        if isinstance(data, list):
            return data
        raise ValueError(f"Expected JSON array, got {type(data)}")

    def extract_metrics_and_narrative(self) -> tuple[dict, str, str]:
        """Extract metrics JSON, narrative, and notepad from metrics update response.

        Expected format:
        ## Metrics
        ```json
        {"metric1": value1, ...}
        ```

        ## Narrativ
        narrative text...

        ## Notepad
        notepad text...
        """
        # Find the ## Metrics section and extract JSON from within it
        section_match = re.search(
            r"##\s*Metrics\b(.*?)(?=##\s*\w|\Z)", self.content, re.DOTALL | re.IGNORECASE
        )
        if not section_match:
            raise LLMParseError("Could not find metrics in response")

        section = section_match.group(1)

        # Try code fence first
        metrics_match = re.search(r"```json\s*(.*?)\s*```", section, re.DOTALL | re.IGNORECASE)
        if metrics_match:
            metrics = json.loads(metrics_match.group(1))
        else:
            # Scan for first JSON object in the section (handles raw, inline-backtick, or prose before JSON)
            decoder = json.JSONDecoder()
            metrics = None
            for i, ch in enumerate(section):
                if ch == "{":
                    try:
                        obj, _ = decoder.raw_decode(section[i:])
                        if isinstance(obj, dict):
                            metrics = obj
                            break
                    except json.JSONDecodeError:
                        continue
            if metrics is None:
                raise LLMParseError("Could not find metrics in response")

        # Find ## Narrative/Narrativ section (stop at ## Notepad if present)
        narrative_match = re.search(
            r"##\s*(Narrative|Narrativ)\s*\n+(.*?)(?=##\s*Notepad|\Z)", self.content, re.DOTALL | re.IGNORECASE
        )

        narrative = narrative_match.group(2).strip() if narrative_match else ""

        # Find ## Notepad section (optional)
        notepad_match = re.search(
            r"##\s*Notepad\s*\n+(.*)", self.content, re.DOTALL | re.IGNORECASE
        )

        notepad = notepad_match.group(1).strip() if notepad_match else ""

        return metrics, narrative, notepad

    def get_usage(self) -> Optional["TokenUsage"]:
        """Extract token usage from raw_response.

        Supports both OpenRouter and Anthropic response shapes.
        Anthropic providers store usage under the same keys but add
        ``_provider`` and optional cache token fields.

        Returns:
            TokenUsage object or None if usage data not available
        """
        from .cost import TokenUsage

        usage_data = self.raw_response.get("usage")
        if not usage_data:
            return None

        provider = self.raw_response.get("_provider", "openrouter")

        return TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            model=self.raw_response.get("model", "unknown"),
            provider=provider,
            cache_creation_input_tokens=usage_data.get(
                "cache_creation_input_tokens", 0
            ) or 0,
            cache_read_input_tokens=usage_data.get(
                "cache_read_input_tokens", 0
            ) or 0,
        )


class MockLLMClient:
    """Mock client for testing without API calls.

    Exposes the same complete(system_prompt, user_prompt) surface as FallbackRouter,
    so tests can inject it anywhere a router is expected.
    """

    def __init__(
        self,
        responses: dict[str, str],
        model: Union[str, List[str]] = "mock/model",
        provider: str = "mock",
        **kwargs,
    ):
        """
        Args:
            responses: Dict mapping prompt substrings to response content.
                      Example: {"events": "[{...}]", "government": "## Goals\\n..."}
            model: Model name(s) for compatibility with orchestrator reuse logic.
            provider: Provider name reported in mock usage data.
        """
        self.responses = responses
        self.calls: list[tuple[str, str]] = []
        self.models = [model] if isinstance(model, str) else model
        self.provider = provider
        # Orchestrator may pass other kwargs (temperature, max_tokens) – ignore them.

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return pre-configured response based on prompt content."""
        self.calls.append((system_prompt, user_prompt))

        for key, content in self.responses.items():
            if key.lower() in user_prompt.lower() or key.lower() in system_prompt.lower():
                raw_response = {
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                    },
                    "model": self.models[0] if self.models else "mock/model",
                }
                return LLMResponse(content=content, raw_response=raw_response)

        raise ValueError("No mock response configured for this prompt. Add key to responses dict.")

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
