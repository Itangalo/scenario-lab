"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import ClassVar

from ..llm import LLMResponse


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
    ) -> LLMResponse:
        """Send a completion request and return a parsed response."""
        ...

    def close(self) -> None:
        """Release any held resources (HTTP clients, SDK handles, etc.)."""
        pass
