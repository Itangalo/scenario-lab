"""Pricing lookup for all LLM providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .openrouter import (
    DEFAULT_PRICING,
    OpenRouterPricingCache,
    fetch_openrouter_pricing_snapshot,
    get_pricing_cache,
    load_pricing_snapshot,
)
from .anthropic import (
    AnthropicPricingCache,
    fetch_anthropic_pricing_snapshot,
    get_anthropic_pricing_cache,
)

if TYPE_CHECKING:
    from ..models import ModelRoute

__all__ = [
    "DEFAULT_PRICING",
    "OpenRouterPricingCache",
    "fetch_openrouter_pricing_snapshot",
    "get_pricing_cache",
    "load_pricing_snapshot",
    "AnthropicPricingCache",
    "fetch_anthropic_pricing_snapshot",
    "get_anthropic_pricing_cache",
    "get_pricing_for",
]


def get_pricing_for(route: "ModelRoute") -> Optional[dict]:
    """Return pricing for a ModelRoute, dispatching to the right cache.

    Args:
        route: ModelRoute with provider and model fields

    Returns:
        Dict with "prompt" and "completion" pricing per million tokens, or None
    """
    if route.provider == "anthropic":
        return get_anthropic_pricing_cache().get_model_pricing(route.model)
    # Default: OpenRouter cache handles all other providers
    return get_pricing_cache().get_model_pricing(route.model)
