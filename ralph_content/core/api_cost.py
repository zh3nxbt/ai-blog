"""API cost calculation utilities."""

from config import settings


def calculate_api_cost(input_tokens: int, output_tokens: int, model: str = None) -> int:
    """
    Calculate API cost in cents based on token usage.

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        model: Model name (defaults to settings.anthropic_model)

    Returns:
        Cost in cents as an integer
    """
    if model is None:
        model = settings.anthropic_model

    # Pricing for Claude models (as of 2026-01-13)
    # Source: https://www.anthropic.com/api-pricing
    pricing = {
        "claude-opus-4-5": {
            "input_per_mtok": 15.00,   # $15 per million input tokens
            "output_per_mtok": 75.00   # $75 per million output tokens
        },
        "claude-sonnet-4-5": {
            "input_per_mtok": 3.00,    # $3 per million input tokens
            "output_per_mtok": 15.00   # $15 per million output tokens
        },
        "claude-sonnet-3-5": {
            "input_per_mtok": 3.00,
            "output_per_mtok": 15.00
        },
        "claude-haiku-3-5": {
            "input_per_mtok": 0.25,
            "output_per_mtok": 1.25
        }
    }

    # Default to Opus pricing if model not found
    model_pricing = pricing.get(model, pricing["claude-opus-4-5"])

    # Calculate cost in dollars
    input_cost = (input_tokens / 1_000_000) * model_pricing["input_per_mtok"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output_per_mtok"]
    total_cost_dollars = input_cost + output_cost

    # Convert to cents and round up
    cost_cents = int(total_cost_dollars * 100 + 0.5)

    return cost_cents
