"""
Model Pricing for Scenario Lab V2

Calculates costs for LLM API calls based on model and token usage.
Supports both static pricing data and dynamic fetching from OpenRouter API.

Pricing data based on OpenRouter pricing as of November 2025.
"""
import os
import logging
from typing import Dict, Tuple, List, Optional

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (input, output) for popular models
# Format: "model_identifier": (input_cost_per_1m, output_cost_per_1m)
# Updated November 2025 - focus on most popular/useful models
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),

    # Anthropic models
    "anthropic/claude-sonnet-4": (3.00, 15.00),
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "anthropic/claude-3.5-haiku": (0.80, 4.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),
    "anthropic/claude-3-opus": (15.00, 75.00),  # Very expensive

    # Google models
    "google/gemini-2.0-flash": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.15, 0.60),
    "google/gemini-1.5-pro": (1.25, 5.00),

    # DeepSeek models (very cost effective)
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek/deepseek-r1": (0.55, 2.19),

    # Meta Llama
    "meta-llama/llama-3.3-70b-instruct": (0.30, 0.30),

    # Local models (no cost)
    "ollama": (0.00, 0.00),
    "local": (0.00, 0.00),
}

# Cache for dynamically fetched pricing
_dynamic_pricing_cache: Dict[str, Tuple[float, float]] = {}
_cache_loaded: bool = False


def fetch_openrouter_models(api_key: Optional[str] = None) -> Dict[str, Tuple[float, float]]:
    """
    Fetch current model pricing from OpenRouter API.

    Args:
        api_key: OpenRouter API key (optional, uses env var if not provided)

    Returns:
        Dict mapping model IDs to (input_cost_per_1m, output_cost_per_1m)
    """
    global _dynamic_pricing_cache, _cache_loaded

    if _cache_loaded:
        return _dynamic_pricing_cache

    if api_key is None:
        api_key = os.environ.get('OPENROUTER_API_KEY')

    if not api_key:
        logger.debug("No API key available for dynamic model fetching")
        return {}

    try:
        import requests

        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        models = data.get("data", [])

        for model in models:
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})

            # OpenRouter returns price per token, convert to per 1M
            prompt_price = float(pricing.get("prompt", 0)) * 1_000_000
            completion_price = float(pricing.get("completion", 0)) * 1_000_000

            if model_id:
                _dynamic_pricing_cache[model_id] = (prompt_price, completion_price)

        _cache_loaded = True
        logger.info(f"Loaded pricing for {len(_dynamic_pricing_cache)} models from OpenRouter")
        return _dynamic_pricing_cache

    except Exception as e:
        logger.debug(f"Could not fetch OpenRouter models: {e}")
        return {}


def get_popular_models() -> List[Dict[str, any]]:
    """
    Get list of popular models for UI display (wizards, etc).

    Returns:
        List of dicts with model info: id, name, description, pricing
    """
    # Try to get fresh data from OpenRouter
    dynamic = fetch_openrouter_models()

    # Curated list of popular models for UI
    popular = [
        {
            "id": "openai/gpt-4o-mini",
            "name": "GPT-4o Mini",
            "description": "Fast, cheap, good for most tasks",
            "tier": "budget",
        },
        {
            "id": "openai/gpt-4o",
            "name": "GPT-4o",
            "description": "OpenAI flagship model",
            "tier": "premium",
        },
        {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "description": "Anthropic latest balanced model",
            "tier": "premium",
        },
        {
            "id": "anthropic/claude-3.5-haiku",
            "name": "Claude 3.5 Haiku",
            "description": "Fast and affordable Claude",
            "tier": "budget",
        },
        {
            "id": "google/gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "description": "Google fast model, very cheap",
            "tier": "budget",
        },
        {
            "id": "google/gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "description": "Google flagship, huge context",
            "tier": "premium",
        },
        {
            "id": "deepseek/deepseek-chat",
            "name": "DeepSeek V3",
            "description": "Extremely cheap, great quality",
            "tier": "budget",
        },
        {
            "id": "deepseek/deepseek-r1",
            "name": "DeepSeek R1",
            "description": "Reasoning model, very capable",
            "tier": "mid",
        },
        {
            "id": "meta-llama/llama-3.3-70b-instruct",
            "name": "Llama 3.3 70B",
            "description": "Open source, good performance",
            "tier": "budget",
        },
        {
            "id": "anthropic/claude-3-haiku",
            "name": "Claude 3 Haiku",
            "description": "Cheapest Claude, still capable",
            "tier": "budget",
        },
    ]

    # Add pricing info from dynamic or static source
    for model in popular:
        model_id = model["id"]
        if model_id in dynamic:
            input_cost, output_cost = dynamic[model_id]
        elif model_id in MODEL_PRICING:
            input_cost, output_cost = MODEL_PRICING[model_id]
        else:
            input_cost, output_cost = 0.15, 0.60  # default

        model["input_cost_per_1m"] = input_cost
        model["output_cost_per_1m"] = output_cost
        model["price_display"] = f"${input_cost:.2f}/${output_cost:.2f} per 1M tokens"

    return popular


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for an LLM API call

    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    # Handle local models
    if model.startswith("ollama/") or model.startswith("local/"):
        return 0.0

    # Try dynamic pricing first, then static
    input_cost_per_1m, output_cost_per_1m = get_model_pricing(model)

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * output_cost_per_1m

    return input_cost + output_cost


def get_model_pricing(model: str) -> Tuple[float, float]:
    """
    Get pricing information for a model

    Args:
        model: Model identifier

    Returns:
        Tuple of (input_cost_per_1m, output_cost_per_1m)
    """
    # Handle local models
    if model.startswith("ollama/") or model.startswith("local/"):
        return (0.0, 0.0)

    # Check dynamic cache first
    dynamic = fetch_openrouter_models()
    if model in dynamic:
        return dynamic[model]

    # Fall back to static pricing
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]

    # Default pricing (gpt-4o-mini level)
    return (0.15, 0.60)


def estimate_cost(
    model: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int
) -> float:
    """
    Estimate cost for a planned LLM call

    Args:
        model: Model identifier
        estimated_input_tokens: Estimated number of input tokens
        estimated_output_tokens: Estimated number of output tokens

    Returns:
        Estimated cost in USD
    """
    return calculate_cost(model, estimated_input_tokens, estimated_output_tokens)


def is_free_model(model: str) -> bool:
    """
    Check if a model is free (no API cost)

    Args:
        model: Model identifier

    Returns:
        True if model is free, False otherwise
    """
    # Local models
    if model.startswith("ollama/") or model.startswith("local/"):
        return True

    # Free models on OpenRouter
    if ":free" in model:
        return True

    # Check if pricing is 0
    input_cost, output_cost = get_model_pricing(model)
    return input_cost == 0.0 and output_cost == 0.0


def is_expensive_model(model: str, threshold: float = 5.0) -> bool:
    """
    Check if a model is expensive (high API cost)

    Args:
        model: Model identifier
        threshold: Cost threshold per 1M input tokens (default: $5.00)

    Returns:
        True if model is expensive, False otherwise
    """
    # Local models are not expensive
    if model.startswith("ollama/") or model.startswith("local/"):
        return False

    # Free models are not expensive
    if is_free_model(model):
        return False

    # Check pricing
    input_cost, output_cost = get_model_pricing(model)
    return input_cost >= threshold or output_cost >= threshold
