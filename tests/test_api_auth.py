"""
Tests for API Authentication and Rate Limiting

Tests for API key authentication, rate limiting, and configuration settings.
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock, Mock
from fastapi.testclient import TestClient

from scenario_lab.api.settings import APISettings, get_settings, reset_settings
from scenario_lab.api.auth import verify_api_key, optional_api_key
from scenario_lab.api.rate_limit import (
    RateLimiter,
    get_rate_limiter,
    reset_rate_limiter,
)


class TestAPISettings:
    """Tests for APISettings configuration"""

    def setup_method(self):
        """Reset settings before each test"""
        reset_settings()

    def teardown_method(self):
        """Clean up environment after each test"""
        reset_settings()
        # Clean up environment variables
        for key in [
            "SCENARIO_LAB_API_KEY",
            "SCENARIO_LAB_AUTH_ENABLED",
            "SCENARIO_LAB_RATE_LIMIT_ENABLED",
            "SCENARIO_LAB_RATE_LIMIT_REQUESTS",
            "SCENARIO_LAB_RATE_LIMIT_WINDOW",
            "SCENARIO_LAB_DEV_MODE",
        ]:
            os.environ.pop(key, None)

    def test_default_settings_no_keys(self):
        """Test default settings with no API keys configured"""
        settings = APISettings.from_env()

        assert settings.api_keys == []
        assert settings.auth_enabled is False  # No keys = auth disabled
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window == 60
        assert settings.dev_mode is False

    def test_settings_with_single_api_key(self):
        """Test settings with a single API key"""
        os.environ["SCENARIO_LAB_API_KEY"] = "test-key-123"

        settings = APISettings.from_env()

        assert settings.api_keys == ["test-key-123"]
        assert settings.auth_enabled is True

    def test_settings_with_multiple_api_keys(self):
        """Test settings with multiple API keys"""
        os.environ["SCENARIO_LAB_API_KEY"] = "key1, key2, key3"

        settings = APISettings.from_env()

        assert settings.api_keys == ["key1", "key2", "key3"]
        assert len(settings.api_keys) == 3

    def test_dev_mode_disables_auth_and_rate_limit(self):
        """Test that dev mode disables auth and rate limiting"""
        os.environ["SCENARIO_LAB_DEV_MODE"] = "true"
        os.environ["SCENARIO_LAB_API_KEY"] = "test-key"

        settings = APISettings.from_env()

        assert settings.dev_mode is True
        assert settings.auth_enabled is False
        assert settings.rate_limit_enabled is False

    def test_custom_rate_limit_settings(self):
        """Test custom rate limit settings"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "50"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "30"

        settings = APISettings.from_env()

        assert settings.rate_limit_requests == 50
        assert settings.rate_limit_window == 30

    def test_explicit_auth_override(self):
        """Test explicit auth enabled/disabled override"""
        os.environ["SCENARIO_LAB_API_KEY"] = "test-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"

        settings = APISettings.from_env()

        assert settings.auth_enabled is False
        assert settings.api_keys == ["test-key"]  # Key is still stored

    def test_validate_api_key_valid(self):
        """Test API key validation with valid key"""
        settings = APISettings(
            api_keys=["valid-key-1", "valid-key-2"],
            auth_enabled=True,
        )

        assert settings.validate_api_key("valid-key-1") is True
        assert settings.validate_api_key("valid-key-2") is True

    def test_validate_api_key_invalid(self):
        """Test API key validation with invalid key"""
        settings = APISettings(
            api_keys=["valid-key"],
            auth_enabled=True,
        )

        assert settings.validate_api_key("invalid-key") is False
        assert settings.validate_api_key("") is False
        assert settings.validate_api_key(None) is False

    def test_validate_api_key_auth_disabled(self):
        """Test that any key passes when auth is disabled"""
        settings = APISettings(
            api_keys=["valid-key"],
            auth_enabled=False,
        )

        assert settings.validate_api_key("any-key") is True
        assert settings.validate_api_key(None) is True

    def test_is_auth_required(self):
        """Test is_auth_required method"""
        # Auth required
        settings = APISettings(api_keys=["key"], auth_enabled=True, dev_mode=False)
        assert settings.is_auth_required() is True

        # Auth disabled
        settings = APISettings(api_keys=["key"], auth_enabled=False, dev_mode=False)
        assert settings.is_auth_required() is False

        # Dev mode
        settings = APISettings(api_keys=["key"], auth_enabled=True, dev_mode=True)
        assert settings.is_auth_required() is False

    def test_get_settings_singleton(self):
        """Test that get_settings returns same instance"""
        os.environ["SCENARIO_LAB_API_KEY"] = "test-key"

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


class TestRateLimiter:
    """Tests for RateLimiter class"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        reset_rate_limiter()
        reset_settings()

    def teardown_method(self):
        """Clean up after each test"""
        reset_rate_limiter()
        reset_settings()
        for key in [
            "SCENARIO_LAB_API_KEY",
            "SCENARIO_LAB_RATE_LIMIT_ENABLED",
            "SCENARIO_LAB_RATE_LIMIT_REQUESTS",
            "SCENARIO_LAB_RATE_LIMIT_WINDOW",
            "SCENARIO_LAB_DEV_MODE",
        ]:
            os.environ.pop(key, None)

    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under the limit are allowed"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "5"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "60"

        limiter = RateLimiter()
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # First 5 requests should be allowed
        for i in range(5):
            allowed, remaining, reset = limiter.check_rate_limit(mock_request)
            assert allowed is True
            assert remaining == 4 - i

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over the limit are blocked"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "3"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "60"

        limiter = RateLimiter()
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Make 3 requests (at limit)
        for _ in range(3):
            allowed, _, _ = limiter.check_rate_limit(mock_request)
            assert allowed is True

        # 4th request should be blocked
        allowed, remaining, reset = limiter.check_rate_limit(mock_request)
        assert allowed is False
        assert remaining == 0
        assert reset > 0

    def test_rate_limiter_tracks_by_ip(self):
        """Test that rate limits are tracked per IP"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"

        limiter = RateLimiter()

        # Client 1
        mock_request_1 = Mock()
        mock_request_1.headers = {}
        mock_request_1.client = Mock()
        mock_request_1.client.host = "192.168.1.1"

        # Client 2
        mock_request_2 = Mock()
        mock_request_2.headers = {}
        mock_request_2.client = Mock()
        mock_request_2.client.host = "192.168.1.2"

        # Client 1 makes 2 requests
        limiter.check_rate_limit(mock_request_1)
        limiter.check_rate_limit(mock_request_1)

        # Client 1 should be blocked
        allowed, _, _ = limiter.check_rate_limit(mock_request_1)
        assert allowed is False

        # Client 2 should still be allowed
        allowed, _, _ = limiter.check_rate_limit(mock_request_2)
        assert allowed is True

    def test_rate_limiter_tracks_by_api_key(self):
        """Test that rate limits are tracked per API key"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"

        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # API key 1 makes 2 requests
        limiter.check_rate_limit(mock_request, api_key="key-1")
        limiter.check_rate_limit(mock_request, api_key="key-1")

        # API key 1 should be blocked
        allowed, _, _ = limiter.check_rate_limit(mock_request, api_key="key-1")
        assert allowed is False

        # API key 2 should still be allowed
        allowed, _, _ = limiter.check_rate_limit(mock_request, api_key="key-2")
        assert allowed is True

    def test_rate_limiter_respects_x_forwarded_for(self):
        """Test that X-Forwarded-For header is used for client identification"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"

        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"  # Proxy IP

        # Make 2 requests
        limiter.check_rate_limit(mock_request)
        limiter.check_rate_limit(mock_request)

        # Should be blocked based on forwarded IP
        allowed, _, _ = limiter.check_rate_limit(mock_request)
        assert allowed is False

    def test_rate_limiter_disabled_in_dev_mode(self):
        """Test that rate limiting is disabled in dev mode"""
        os.environ["SCENARIO_LAB_DEV_MODE"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "1"

        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Should allow many requests in dev mode
        for _ in range(10):
            allowed, _, _ = limiter.check_rate_limit(mock_request)
            assert allowed is True

    def test_rate_limiter_window_sliding(self):
        """Test that old requests expire from the window"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "1"  # 1 second window

        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Make 2 requests (at limit)
        limiter.check_rate_limit(mock_request)
        limiter.check_rate_limit(mock_request)

        # 3rd request should be blocked
        allowed, _, _ = limiter.check_rate_limit(mock_request)
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed, _, _ = limiter.check_rate_limit(mock_request)
        assert allowed is True

    def test_reset_clears_state(self):
        """Test that reset clears all rate limit state"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "1"

        limiter = RateLimiter()

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        # Make 1 request (at limit)
        limiter.check_rate_limit(mock_request)

        # Should be blocked
        allowed, _, _ = limiter.check_rate_limit(mock_request)
        assert allowed is False

        # Reset
        limiter.reset()

        # Should be allowed again
        allowed, _, _ = limiter.check_rate_limit(mock_request)
        assert allowed is True


class TestAPIEndpointsAuth:
    """Integration tests for API authentication on endpoints"""

    def setup_method(self):
        """Reset state before each test"""
        reset_settings()
        reset_rate_limiter()

    def teardown_method(self):
        """Clean up after each test"""
        reset_settings()
        reset_rate_limiter()
        for key in [
            "SCENARIO_LAB_API_KEY",
            "SCENARIO_LAB_AUTH_ENABLED",
            "SCENARIO_LAB_DEV_MODE",
            "SCENARIO_LAB_RATE_LIMIT_ENABLED",
        ]:
            os.environ.pop(key, None)

    def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require auth"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "true"

        # Import app after setting env vars
        from scenario_lab.api.app import app

        client = TestClient(app)

        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "auth_enabled" in data

    def test_root_endpoint_no_auth_required(self):
        """Test that root endpoint doesn't require auth"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "true"

        from scenario_lab.api.app import app

        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200

    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require auth when enabled"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "false"  # Disable rate limiting for this test

        from scenario_lab.api.app import app

        client = TestClient(app)

        # Request without API key should fail
        response = client.get("/api/runs")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_protected_endpoint_with_valid_key(self):
        """Test that protected endpoints work with valid API key"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "false"

        from scenario_lab.api.app import app

        client = TestClient(app)

        response = client.get(
            "/api/runs",
            headers={"X-API-Key": "secret-key"}
        )
        # Will be 503 because database is not configured in tests, but not 401
        assert response.status_code == 503  # Database not configured
        assert "Database not configured" in response.json()["detail"]

    def test_protected_endpoint_with_invalid_key(self):
        """Test that protected endpoints reject invalid API key"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "false"

        from scenario_lab.api.app import app

        client = TestClient(app)

        response = client.get(
            "/api/runs",
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_dev_mode_bypasses_auth(self):
        """Test that dev mode bypasses authentication"""
        os.environ["SCENARIO_LAB_API_KEY"] = "secret-key"
        os.environ["SCENARIO_LAB_DEV_MODE"] = "true"

        from scenario_lab.api.app import app

        client = TestClient(app)

        # Should work without API key in dev mode
        response = client.get("/api/runs")
        # Will be 503 because database is not configured, but not 401
        assert response.status_code == 503

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included in response"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "100"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"

        from scenario_lab.api.app import app

        client = TestClient(app)

        response = client.get("/api/runs")
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_exceeded_returns_429(self):
        """Test that exceeding rate limit returns 429"""
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "60"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"

        from scenario_lab.api.app import app

        client = TestClient(app)

        # Make requests up to limit
        client.get("/api/runs")
        client.get("/api/runs")

        # Next request should be rate limited
        response = client.get("/api/runs")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
