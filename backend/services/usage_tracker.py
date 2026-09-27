"""Records model token usage and estimated cost for the admin analytics."""

import contextvars
from typing import Any, Optional

from utils.logger import logger

# The authenticated user for the current request; background workers have none
current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_user_id", default=None)

# Estimated list prices in USD per 1M tokens (input, output). Update when provider pricing changes.
PRICING = {
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-3.5-turbo": (0.50, 1.50),
    "text-embedding-ada-002": (0.10, 0.0),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
}


def _price(model: str):
    # Dated snapshots (e.g. gpt-4.1-mini-2025-04-14) use the base model's price
    for name in sorted(PRICING, key=len, reverse=True):
        if model.startswith(name):
            return PRICING[name]
    return (0.0, 0.0)


def record_usage(model: str, usage: Any, feature: str) -> None:
    """Store token counts from an OpenAI response's `usage`. Never raises."""
    if usage is None:
        return
    try:
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        price_in, price_out = _price(model)
        cost = (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000
        from .platform_store import get_platform_store

        get_platform_store().record_llm_usage(
            model, feature, prompt_tokens, completion_tokens, round(cost, 6), current_user_id.get()
        )
    except Exception as e:  # analytics must never break a request
        logger.warning(f"Could not record model usage: {str(e)}")
