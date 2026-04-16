"""Provider registry: maps provider names to LLMProvider instances."""

from __future__ import annotations

from .base import LLMProvider
from ..llm import LLMError


class ProviderRegistry:
    """Holds one LLMProvider instance per provider name, created lazily."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> LLMProvider:
        """Return the provider for *name*, creating it lazily if not yet registered.

        Built-in providers (openrouter, anthropic) are created on first access.
        """
        if name in self._providers:
            return self._providers[name]

        provider = self._create_builtin(name)
        self._providers[name] = provider
        return provider

    @staticmethod
    def _create_builtin(name: str) -> LLMProvider:
        if name == "openrouter":
            from .openrouter import OpenRouterProvider
            return OpenRouterProvider()
        if name == "anthropic":
            from .anthropic import AnthropicProvider
            return AnthropicProvider()
        raise LLMError(f"Unknown provider '{name}'. Register it explicitly or use a built-in.")

    def close_all(self) -> None:
        """Close all registered providers."""
        for provider in self._providers.values():
            provider.close()
        self._providers.clear()
