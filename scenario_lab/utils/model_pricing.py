"""
Model pricing database for Scenario Lab

Provides pricing information for LLM models to enable cost estimation.
Prices are in USD per million tokens.
"""
from typing import Dict, Tuple, Optional


# Model pricing: (input_price_per_million, output_price_per_million)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.150, 0.600),
    "openai/gpt-4-turbo": (10.00, 30.00),
    "openai/gpt-4": (30.00, 60.00),
    "openai/gpt-3.5-turbo": (0.50, 1.50),

    # Anthropic models
    "anthropic/claude-3-5-sonnet": (3.00, 15.00),
    "anthropic/claude-3-opus": (15.00, 75.00),
    "anthropic/claude-3-sonnet": (3.00, 15.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),

    # Google models
    "google/gemini-pro": (0.50, 1.50),
    "google/gemini-1.5-pro": (1.25, 5.00),
    "google/gemini-1.5-flash": (0.075, 0.30),

    # Meta models (via providers)
    "meta-llama/llama-3.1-70b": (0.35, 0.40),
    "meta-llama/llama-3.1-8b": (0.055, 0.08),
    "meta-llama/llama-3-70b": (0.59, 0.79),

    # Mistral models
    "mistralai/mistral-large": (2.00, 6.00),
    "mistralai/mistral-medium": (2.70, 8.10),
    "mistralai/mistral-small": (0.20, 0.60),

    # DeepSeek models
    "deepseek/deepseek-chat": (0.14, 0.28),
    "deepseek/deepseek-coder": (0.14, 0.28),

    # Alibaba models (OpenRouter)
    "alibaba/tongyi-deepresearch-30b-a3b": (0.00, 0.00),  # Free tier

    # Local models (Ollama) - zero cost
    "ollama/llama3": (0.00, 0.00),
    "ollama/llama3.1": (0.00, 0.00),
    "ollama/deepseek-r1:8b": (0.00, 0.00),
    "ollama/mistral": (0.00, 0.00),
    "ollama/qwen2.5": (0.00, 0.00),
}


def get_model_pricing(model: str) -> Optional[Tuple[float, float]]:
    """
    Get pricing for a model

    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini")

    Returns:
        Tuple of (input_price_per_million, output_price_per_million) or None if unknown
    """
    # Direct lookup
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]

    # Try without provider prefix
    model_lower = model.lower()
    for known_model in MODEL_PRICING:
        if known_model.lower().endswith(model_lower.split('/')[-1]):
            return MODEL_PRICING[known_model]

    # Unknown model
    return None


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Estimate cost for a model call

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier

    Returns:
        Estimated cost in USD
    """
    pricing = get_model_pricing(model)
    if pricing is None:
        # Unknown model - use gpt-4o-mini pricing as conservative estimate
        pricing = MODEL_PRICING["openai/gpt-4o-mini"]

    input_price, output_price = pricing

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return input_cost + output_cost


def is_expensive_model(model: str, threshold: float = 5.0) -> bool:
    """
    Check if a model is considered expensive

    Args:
        model: Model identifier
        threshold: Price threshold in USD per million output tokens

    Returns:
        True if model output pricing exceeds threshold
    """
    pricing = get_model_pricing(model)
    if pricing is None:
        return False

    _, output_price = pricing
    return output_price >= threshold


def is_free_model(model: str) -> bool:
    """
    Check if a model is free (local or free tier)

    Args:
        model: Model identifier

    Returns:
        True if model has zero cost
    """
    pricing = get_model_pricing(model)
    if pricing is None:
        return False

    input_price, output_price = pricing
    return input_price == 0.0 and output_price == 0.0
