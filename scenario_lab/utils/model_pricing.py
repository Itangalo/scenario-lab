"""
Model Pricing for Scenario Lab V2

Calculates costs for LLM API calls based on model and token usage.
Pricing data based on OpenRouter pricing as of early 2025.
"""
from typing import Dict, Tuple


# Pricing per 1M tokens (input, output) for common models
# Format: "model_identifier": (input_cost_per_1m, output_cost_per_1m)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # OpenAI models
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-4-turbo": (10.00, 30.00),
    "openai/gpt-3.5-turbo": (0.50, 1.50),

    # Anthropic models
    "anthropic/claude-3.5-sonnet": (3.00, 15.00),
    "anthropic/claude-3-opus": (15.00, 75.00),
    "anthropic/claude-3-sonnet": (3.00, 15.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),

    # Google models
    "google/gemini-pro": (0.50, 1.50),
    "google/gemini-pro-1.5": (3.50, 10.50),
    "google/gemini-flash": (0.075, 0.30),

    # Meta Llama
    "meta-llama/llama-3.1-405b-instruct": (2.70, 2.70),
    "meta-llama/llama-3.1-70b-instruct": (0.52, 0.75),
    "meta-llama/llama-3.1-8b-instruct": (0.06, 0.06),

    # Mistral
    "mistralai/mistral-large": (4.00, 12.00),
    "mistralai/mistral-medium": (2.70, 8.10),
    "mistralai/mixtral-8x7b": (0.54, 0.54),

    # Alibaba (free models on OpenRouter)
    "alibaba/tongyi-deepresearch-30b-a3b:free": (0.00, 0.00),
    "alibaba/qwen-2.5-72b-instruct:free": (0.00, 0.00),

    # Local models (no cost)
    "ollama": (0.00, 0.00),
    "local": (0.00, 0.00),
}


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

    # Look up pricing
    if model in MODEL_PRICING:
        input_cost_per_1m, output_cost_per_1m = MODEL_PRICING[model]
    else:
        # Default pricing if model not found (assume gpt-4o-mini pricing)
        input_cost_per_1m, output_cost_per_1m = 0.15, 0.60

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

    return MODEL_PRICING.get(model, (0.15, 0.60))


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
    if model in MODEL_PRICING:
        input_cost, output_cost = MODEL_PRICING[model]
        return input_cost == 0.0 and output_cost == 0.0

    return False


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
    if model in MODEL_PRICING:
        input_cost, output_cost = MODEL_PRICING[model]
        return input_cost >= threshold or output_cost >= threshold

    # Unknown models - assume not expensive (use default pricing)
    return False
