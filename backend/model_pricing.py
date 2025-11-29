"""
LLM Model Pricing Data
Maintains up-to-date pricing for cost calculations.
Follows SSOT principle - single source for all pricing data.
"""

from typing import Dict, Optional

from backend.telemetry import logger

# Pricing per 1,000 tokens (USD)
# Updated as of October 2025
MODEL_PRICING = {
    # OpenAI Models
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-2024-04-09": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-0613": {"input": 0.03, "output": 0.06},
    "gpt-4-32k": {"input": 0.06, "output": 0.12},
    "gpt-4-32k-0613": {"input": 0.06, "output": 0.12},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    "gpt-5-mini": {"input": 0.00025, "output": 0.002},  # GPT-5 mini model (Aug 2025)
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # GPT-4o mini model
    # Anthropic Models
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
    # Add more models as pricing becomes available
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    custom_pricing: Optional[Dict[str, Dict[str, float]]] = None,
) -> float:
    """
    Calculate LLM API cost based on token usage.

    Args:
        model: Model name (e.g., "gpt-4-turbo-preview")
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        custom_pricing: Optional custom pricing override for testing

    Returns:
        Cost in USD (rounded to 6 decimal places)

    Example:
        >>> calculate_cost("gpt-4-turbo-preview", 1000, 500)
        0.025000  # $0.01 + $0.015
    """
    pricing_table = custom_pricing or MODEL_PRICING

    if model not in pricing_table:
        logger.warning(
            "unknown_model_pricing",
            extra={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )
        return 0.0

    pricing = pricing_table[model]

    # Calculate cost (pricing is per 1K tokens)
    input_cost = (input_tokens / 1000.0) * pricing["input"]
    output_cost = (output_tokens / 1000.0) * pricing["output"]
    total_cost = input_cost + output_cost

    logger.debug(
        "cost_calculated",
        extra={
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        },
    )

    return round(total_cost, 6)  # Round to 6 decimal places


def get_model_pricing(model: str) -> Optional[Dict[str, float]]:
    """
    Get pricing for a specific model.

    Args:
        model: Model name

    Returns:
        Dict with "input" and "output" pricing per 1K tokens, or None if not found

    Example:
        >>> get_model_pricing("gpt-4-turbo-preview")
        {"input": 0.01, "output": 0.03}
    """
    return MODEL_PRICING.get(model)


def list_supported_models() -> list:
    """
    Get list of models with known pricing.

    Returns:
        List of model names

    Example:
        >>> models = list_supported_models()
        >>> "gpt-4-turbo-preview" in models
        True
    """
    return list(MODEL_PRICING.keys())


def is_model_supported(model: str) -> bool:
    """
    Check if a model has known pricing.

    Args:
        model: Model name

    Returns:
        True if model pricing is available

    Example:
        >>> is_model_supported("gpt-4-turbo-preview")
        True
        >>> is_model_supported("unknown-model")
        False
    """
    return model in MODEL_PRICING
