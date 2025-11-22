"""
API Settings for Scenario Lab

Configuration for authentication, rate limiting, and other API settings.
Settings are loaded from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


# Default CORS origins (localhost only for security)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


@dataclass
class APISettings:
    """
    API configuration settings loaded from environment variables.

    Environment Variables:
        SCENARIO_LAB_API_KEY: Required API key for authentication (comma-separated for multiple keys)
        SCENARIO_LAB_AUTH_ENABLED: Enable/disable authentication (default: true in production)
        SCENARIO_LAB_RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: true)
        SCENARIO_LAB_RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
        SCENARIO_LAB_RATE_LIMIT_WINDOW: Time window in seconds (default: 60)
        SCENARIO_LAB_DEV_MODE: Enable development mode with relaxed security (default: false)
        SCENARIO_LAB_CORS_ORIGINS: Comma-separated list of allowed CORS origins
                                   (default: localhost only for security)
    """

    # Authentication settings
    api_keys: list[str] = field(default_factory=list)
    auth_enabled: bool = True

    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 60  # seconds

    # Development mode (disables auth and rate limiting)
    dev_mode: bool = False

    # CORS settings
    cors_allowed_origins: list[str] = field(default_factory=lambda: DEFAULT_CORS_ORIGINS.copy())

    @classmethod
    def from_env(cls) -> "APISettings":
        """
        Load settings from environment variables.

        Returns:
            APISettings instance configured from environment
        """
        # Parse API keys (comma-separated)
        api_keys_str = os.environ.get("SCENARIO_LAB_API_KEY", "")
        api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

        # Parse dev mode first (affects other defaults)
        dev_mode = os.environ.get("SCENARIO_LAB_DEV_MODE", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        # Auth enabled: default to False if dev_mode or no keys configured
        auth_enabled_default = "false" if (dev_mode or not api_keys) else "true"
        auth_enabled = os.environ.get(
            "SCENARIO_LAB_AUTH_ENABLED", auth_enabled_default
        ).lower() in ("true", "1", "yes")

        # Rate limiting: default to False in dev mode
        rate_limit_enabled_default = "false" if dev_mode else "true"
        rate_limit_enabled = os.environ.get(
            "SCENARIO_LAB_RATE_LIMIT_ENABLED", rate_limit_enabled_default
        ).lower() in ("true", "1", "yes")

        # Rate limit configuration
        rate_limit_requests = int(
            os.environ.get("SCENARIO_LAB_RATE_LIMIT_REQUESTS", "100")
        )
        rate_limit_window = int(
            os.environ.get("SCENARIO_LAB_RATE_LIMIT_WINDOW", "60")
        )

        # CORS origins (comma-separated, defaults to localhost only)
        cors_origins_str = os.environ.get("SCENARIO_LAB_CORS_ORIGINS", "")
        if cors_origins_str.strip():
            cors_allowed_origins = [
                origin.strip() for origin in cors_origins_str.split(",") if origin.strip()
            ]
        else:
            cors_allowed_origins = DEFAULT_CORS_ORIGINS.copy()

        return cls(
            api_keys=api_keys,
            auth_enabled=auth_enabled,
            rate_limit_enabled=rate_limit_enabled,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window=rate_limit_window,
            dev_mode=dev_mode,
            cors_allowed_origins=cors_allowed_origins,
        )

    def validate_api_key(self, key: Optional[str]) -> bool:
        """
        Validate an API key.

        Args:
            key: The API key to validate

        Returns:
            True if the key is valid, False otherwise
        """
        if not self.auth_enabled:
            return True
        if not key:
            return False
        return key in self.api_keys

    def is_auth_required(self) -> bool:
        """Check if authentication is required."""
        return self.auth_enabled and not self.dev_mode


# Global settings instance (lazy-loaded)
_settings: Optional[APISettings] = None


def get_settings() -> APISettings:
    """
    Get the global API settings instance.

    Settings are loaded once from environment variables.

    Returns:
        APISettings instance
    """
    global _settings
    if _settings is None:
        _settings = APISettings.from_env()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
