"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from ..llm import LLMResponse, LLMUnsupportedStructuredError


class LLMProvider(ABC):
    """Abstract base for an LLM backend adapter."""

    name: ClassVar[str]

    @abstractmethod
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
        """Send a completion request and return a parsed response.

        ``call_timeout_seconds`` overrides the provider's instance default for
        this one call; limits follow the model being called, not the step.
        """
        ...

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
        """Send a schema-constrained completion and return parsed structured data.

        ``schema`` is a JSON schema for the *array* the caller expects. The
        returned ``LLMResponse`` has ``structured_data`` set to the parsed
        payload (typically a list).

        Providers that do not implement structured output raise
        ``LLMUnsupportedStructuredError`` so the caller can fall back to the
        legacy text-parsing path. Providers that do implement it must also raise
        ``LLMUnsupportedStructuredError`` (rather than a generic LLMError) when
        the *model* rejects the request as unsupported.
        """
        raise LLMUnsupportedStructuredError(
            f"Provider '{self.name}' does not support structured output."
        )

    def close(self) -> None:
        """Release any held resources (HTTP clients, SDK handles, etc.)."""
        pass
