"""
Rate Limiting for Scenario Lab API

Provides configurable rate limiting using an in-memory sliding window approach.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException, Request, status

from scenario_lab.api.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """Track request timestamps for a single client."""

    timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    Tracks requests per client (identified by IP or API key) and enforces
    configurable rate limits.
    """

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self._clients: dict[str, RateLimitState] = defaultdict(RateLimitState)

    def _get_client_id(self, request: Request, api_key: Optional[str] = None) -> str:
        """
        Get a unique identifier for the client.

        Uses API key if available, otherwise falls back to IP address.

        Args:
            request: The FastAPI request
            api_key: Optional API key

        Returns:
            Client identifier string
        """
        if api_key:
            return f"key:{api_key[:16]}"

        # Get client IP (handle proxies via X-Forwarded-For)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain (original client)
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _cleanup_old_timestamps(
        self, state: RateLimitState, window_seconds: int
    ) -> None:
        """
        Remove timestamps older than the current window.

        Args:
            state: The rate limit state to clean
            window_seconds: The window size in seconds
        """
        cutoff = time.time() - window_seconds
        state.timestamps = [ts for ts in state.timestamps if ts > cutoff]

    def check_rate_limit(
        self,
        request: Request,
        api_key: Optional[str] = None,
    ) -> tuple[bool, int, int]:
        """
        Check if a request is within rate limits.

        Args:
            request: The FastAPI request
            api_key: Optional API key for client identification

        Returns:
            Tuple of (allowed, remaining, reset_seconds)
        """
        settings = get_settings()

        # Rate limiting disabled
        if not settings.rate_limit_enabled or settings.dev_mode:
            return True, settings.rate_limit_requests, 0

        client_id = self._get_client_id(request, api_key)
        state = self._clients[client_id]

        # Clean up old timestamps
        self._cleanup_old_timestamps(state, settings.rate_limit_window)

        # Check if limit exceeded
        current_count = len(state.timestamps)
        remaining = max(0, settings.rate_limit_requests - current_count)

        if current_count >= settings.rate_limit_requests:
            # Calculate reset time
            if state.timestamps:
                oldest = min(state.timestamps)
                reset_seconds = int(settings.rate_limit_window - (time.time() - oldest))
            else:
                reset_seconds = settings.rate_limit_window

            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False, 0, max(1, reset_seconds)

        # Record this request
        state.timestamps.append(time.time())

        return True, remaining - 1, 0

    def reset(self) -> None:
        """Reset all rate limit state (useful for testing)."""
        self._clients.clear()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the rate limiter (useful for testing)."""
    global _rate_limiter
    if _rate_limiter:
        _rate_limiter.reset()
    _rate_limiter = None


async def check_rate_limit(
    request: Request,
    api_key: Optional[str] = None,
) -> None:
    """
    FastAPI dependency to check rate limits.

    Raises HTTPException with 429 status if rate limit is exceeded.

    Args:
        request: The FastAPI request
        api_key: Optional API key for client identification

    Raises:
        HTTPException: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    allowed, remaining, reset_seconds = limiter.check_rate_limit(request, api_key)

    # Add rate limit headers to response
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_reset = reset_seconds

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {reset_seconds} seconds.",
            headers={
                "Retry-After": str(reset_seconds),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
            },
        )
