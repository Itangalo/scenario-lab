"""LLM client for OpenRouter API."""

import httpx
import json
import os
import re
import time
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

    def extract_json(self) -> dict:
        """Extract JSON from markdown code block or raw content."""
        # Try to find ```json ... ``` block
        match = re.search(r"```json\s*(.*?)\s*```", self.content, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # Try to find {...} or [...] in content
        match = re.search(r"(\{.*?\}|\[.*?\])", self.content, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # Try raw JSON
        return json.loads(self.content)

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
        # Find ## Metrics section with JSON
        metrics_match = re.search(
            r"##\s*Metrics\s*\n+```json\s*(.*?)\s*```", self.content, re.DOTALL | re.IGNORECASE
        )
        if not metrics_match:
            # Try without code block
            metrics_match = re.search(
                r"##\s*Metrics\s*\n+(\{.*?\})", self.content, re.DOTALL | re.IGNORECASE
            )

        if not metrics_match:
            raise LLMParseError("Could not find metrics in response")

        metrics = json.loads(metrics_match.group(1))

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


class LLMClient:
    """Client for OpenRouter API with fallback support."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Union[str, List[str]] = "anthropic/claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """Initialize LLM client with optional fallback models.

        Args:
            api_key: OpenRouter API key
            model: Single model string or list of models for fallback
            temperature: Temperature for generation
            max_tokens: Max tokens for generation
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Set it in environment or pass to constructor."
            )

        # Store as list for fallback handling
        self.models = [model] if isinstance(model, str) else model
        self.model = self.models[0]  # Primary model for compatibility
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.Client(timeout=120.0)

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Send a completion request with fallback support.

        Tries each model in self.models list until one succeeds.
        For each model, retries on rate limits and timeouts.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            LLMResponse with parsed content

        Raises:
            LLMError: If all models fail
        """
        last_error = None
        max_retries = 3

        # Try each model in fallback list
        for model_index, model in enumerate(self.models):
            is_fallback = model_index > 0

            if is_fallback:
                print(f"  → Falling back to: {model}")

            # Try this model with retries for transient errors
            for attempt in range(max_retries):
                try:
                    response = self.client.post(
                        self.API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": self.temperature,
                            "max_tokens": self.max_tokens,
                        },
                    )
                    response.raise_for_status()

                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    if is_fallback:
                        print(f"  ✓ Fallback successful")

                    return LLMResponse(content=content, raw_response=data)

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        if attempt < max_retries - 1:
                            wait_time = 2**attempt  # Exponential backoff
                            print(f"  Rate limit hit, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        # Rate limit exhausted for this model, try next model
                        last_error = LLMError(f"Rate limit exceeded for {model}")
                        print(f"  ✗ {model} unavailable (rate limit)")
                        break

                    # Other HTTP errors (e.g., 503 unavailable) - try next model immediately
                    last_error = LLMError(f"HTTP {e.response.status_code} for {model}")
                    print(f"  ✗ {model} unavailable (HTTP {e.response.status_code})")
                    break

                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        print(f"  Request timed out, retrying ({attempt + 1}/{max_retries})...")
                        continue
                    # Timeout exhausted for this model, try next model
                    last_error = LLMError(f"Timeout for {model}")
                    print(f"  ✗ {model} timed out")
                    break

                except Exception as e:
                    last_error = LLMError(f"Error with {model}: {e}")
                    print(f"  ✗ {model} error: {e}")
                    break

        # All models failed
        models_tried = ", ".join(self.models)
        raise LLMError(f"All models failed ({models_tried}). Last error: {last_error}")

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.close()


class MockLLMClient:
    """Mock client for testing without API calls."""

    def __init__(self, responses: dict[str, str]):
        """
        Args:
            responses: Dict mapping prompt substrings to response content.
                      Example: {"events": "[{...}]", "government": "## Goals\\n..."}
        """
        self.responses = responses
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return pre-configured response based on prompt content."""
        self.calls.append((system_prompt, user_prompt))

        # Match based on keywords in prompts
        for key, content in self.responses.items():
            if key.lower() in user_prompt.lower() or key.lower() in system_prompt.lower():
                return LLMResponse(content=content, raw_response={})

        raise ValueError(f"No mock response configured for this prompt. Add key to responses dict.")

    def close(self):
        """No-op for mock."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
