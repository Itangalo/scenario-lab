"""
Rate Limiting for Scenario Lab API

Provides configurable rate limiting using an in-memory sliding window approach.
"""
from __future__ import annotations

import ipaddress
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException, Request, status

from scenario_lab.api.settings import get_settings

logger = logging.getLogger(__name__)


# Trusted proxy IP ranges (private networks by default)
# Can be configured via SCENARIO_LAB_TRUSTED_PROXIES environment variable
# Format: comma-separated CIDR notation (e.g., "10.0.0.0/8,172.16.0.0/12")
DEFAULT_TRUSTED_PROXIES = [
    "127.0.0.0/8",      # Localhost
    "10.0.0.0/8",       # Private Class A
    "172.16.0.0/12",    # Private Class B
    "192.168.0.0/16",   # Private Class C
    "::1/128",          # IPv6 localhost
    "fc00::/7",         # IPv6 private
]


def _get_trusted_proxy_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """
    Get list of trusted proxy networks from environment or defaults.

    Returns:
        List of IP network objects representing trusted proxies
    """
    env_proxies = os.environ.get("SCENARIO_LAB_TRUSTED_PROXIES", "")
    if env_proxies.strip():
        proxy_strs = [p.strip() for p in env_proxies.split(",") if p.strip()]
    else:
        proxy_strs = DEFAULT_TRUSTED_PROXIES

    networks = []
    for proxy_str in proxy_strs:
        try:
            networks.append(ipaddress.ip_network(proxy_str, strict=False))
        except ValueError as e:
            logger.warning(f"Invalid trusted proxy CIDR '{proxy_str}': {e}")

    return networks


def _is_trusted_proxy(client_ip: str) -> bool:
    """
    Check if the client IP is from a trusted proxy.

    Args:
        client_ip: The IP address to check

    Returns:
        True if the IP is within a trusted proxy network
    """
    if not client_ip or client_ip == "unknown":
        return False

    try:
        ip = ipaddress.ip_address(client_ip)
    except ValueError:
        logger.warning(f"Invalid IP address format: {client_ip}")
        return False

    trusted_networks = _get_trusted_proxy_networks()
    return any(ip in network for network in trusted_networks)


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
        Only trusts X-Forwarded-For header when request comes from a trusted proxy
        to prevent header spoofing attacks that could bypass rate limiting.

        Args:
            request: The FastAPI request
            api_key: Optional API key

        Returns:
            Client identifier string
        """
        if api_key:
            return f"key:{api_key[:16]}"

        # Get the direct client IP first
        direct_client_ip = request.client.host if request.client else "unknown"

        # Only trust X-Forwarded-For if request comes from a trusted proxy
        # This prevents attackers from spoofing the header to bypass rate limits
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded and _is_trusted_proxy(direct_client_ip):
            # Request is from a trusted proxy, use the original client IP
            client_ip = forwarded.split(",")[0].strip()
            logger.debug(f"Using X-Forwarded-For IP {client_ip} from trusted proxy {direct_client_ip}")
        else:
            # Either no X-Forwarded-For or untrusted source - use direct IP
            client_ip = direct_client_ip
            if forwarded:
                logger.debug(f"Ignoring X-Forwarded-For from untrusted source {direct_client_ip}")

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
