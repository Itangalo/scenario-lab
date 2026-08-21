"""Provider registry: maps provider names to LLMProvider instances."""

from __future__ import annotations


from .base import LLMProvider
from ..llm import LLMError


class ProviderRegistry:
    """Holds one LLMProvider instance per provider name, created lazily."""

    def __init__(self, call_timeout_seconds: int | None = None) -> None:
        """
        Args:
            call_timeout_seconds: Wall-clock deadline applied to each LLM call
                by providers that support it. None keeps the provider default.
        """
        self._providers: dict[str, LLMProvider] = {}
        self._call_timeout_seconds = call_timeout_seconds

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

    def _create_builtin(self, name: str) -> LLMProvider:
        if name == "openrouter":
            from .openrouter import OpenRouterProvider

            if self._call_timeout_seconds is not None:
                return OpenRouterProvider(call_timeout_seconds=self._call_timeout_seconds)
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
