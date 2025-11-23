"""
API Authentication for Scenario Lab

Provides API key authentication via X-API-Key header.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from scenario_lab.api.settings import get_settings

logger = logging.getLogger(__name__)

# API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Verify the API key from the X-API-Key header.

    This dependency can be used on routes that require authentication.
    When dev_mode is enabled or auth is disabled, authentication is bypassed.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If authentication fails
    """
    settings = get_settings()

    # Skip authentication if not required
    if not settings.is_auth_required():
        logger.debug("Authentication bypassed (dev_mode or auth disabled)")
        return None

    # Check if API key is provided
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate the API key
    if not settings.validate_api_key(api_key):
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API key validated successfully")
    return api_key


async def optional_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Optional API key verification for endpoints that work with or without auth.

    Unlike verify_api_key, this doesn't raise an exception if no key is provided.
    It only validates if a key IS provided.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The validated API key or None

    Raises:
        HTTPException: Only if an invalid key is provided
    """
    settings = get_settings()

    # No key provided - that's okay for optional auth
    if not api_key:
        return None

    # Key provided - validate it if auth is enabled
    if settings.auth_enabled and not settings.validate_api_key(api_key):
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def verify_websocket_token(token: Optional[str]) -> bool:
    """
    Verify a WebSocket authentication token.

    WebSocket connections cannot use headers for authentication in the same way
    as REST endpoints, so they use a query parameter token instead.

    Args:
        token: The authentication token from query parameter

    Returns:
        True if authentication passes (valid token or auth disabled)
    """
    settings = get_settings()

    # Skip authentication if not required
    if not settings.is_auth_required():
        logger.debug("WebSocket authentication bypassed (dev_mode or auth disabled)")
        return True

    # Check if token is provided
    if not token:
        logger.warning("WebSocket connection without authentication token")
        return False

    # Validate the token (using same API keys)
    if not settings.validate_api_key(token):
        logger.warning(f"Invalid WebSocket token attempt: {token[:8]}...")
        return False

    logger.debug("WebSocket token validated successfully")
    return True
