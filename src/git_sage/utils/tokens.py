"""Token counting and cost estimation utilities."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate the token count for a string.

    Uses a rough heuristic of ~4 characters per token.
    For more accurate counting, install tiktoken.
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: ~4 chars per token
        return len(text) // 4


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gemini-3.1-flash-lite") -> float:
    """Estimate the cost of an LLM call in USD.

    Pricing is approximate and may change. Update as needed.
    """
    # Approximate pricing per 1M tokens (as of 2025)
    pricing = {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-2.0-flash-lite": {"input": 0.02, "output": 0.10},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-3.1-flash-lite": {"input": 0.075, "output": 0.30},
    }

    model_pricing = pricing.get(model, pricing["gemini-3.1-flash-lite"])

    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost


def format_cost(cost: float) -> str:
    """Format a cost value for display."""
    if cost < 0.01:
        return f"~${cost:.4f}"
    return f"~${cost:.2f}"
