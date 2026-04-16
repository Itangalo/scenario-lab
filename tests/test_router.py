"""Tests for FallbackRouter."""

import pytest
from unittest.mock import MagicMock, call

from scenario_lab.llm import LLMError, LLMRateLimitError, LLMResponse
from scenario_lab.models import ModelRoute
from scenario_lab.providers.registry import ProviderRegistry
from scenario_lab.router import FallbackRouter


def _make_route(provider="openrouter", model="x/y"):
    return ModelRoute(provider, model)


def _mock_registry(*providers):
    """Build a ProviderRegistry pre-loaded with MagicMock providers."""
    registry = ProviderRegistry()
    for p in providers:
        registry.register(p)
    return registry


def _mock_provider(name="openrouter", complete_side_effect=None, complete_return=None):
    prov = MagicMock()
    prov.name = name
    if complete_side_effect is not None:
        prov.complete.side_effect = complete_side_effect
    elif complete_return is not None:
        prov.complete.return_value = complete_return
    else:
        prov.complete.return_value = LLMResponse(content="ok", raw_response={})
    return prov


class TestFallbackRouterSingleRoute:
    def test_success(self):
        prov = _mock_provider()
        registry = _mock_registry(prov)
        router = FallbackRouter(
            routes=[_make_route()],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )
        resp = router.complete("sys", "usr")
        assert resp.content == "ok"

    def test_empty_routes_raises(self):
        with pytest.raises(ValueError, match="at least one route"):
            FallbackRouter(routes=[], registry=ProviderRegistry(), temperature=0.7, max_tokens=100)

    def test_primary_route(self):
        route = _make_route()
        prov = _mock_provider()
        router = FallbackRouter(
            routes=[route],
            registry=_mock_registry(prov),
            temperature=0.7,
            max_tokens=100,
        )
        assert router.primary_route is route


class TestFallbackRouterRetries:
    def test_rate_limit_retries_then_succeeds(self):
        prov = _mock_provider(
            complete_side_effect=[
                LLMRateLimitError("hit limit"),
                LLMResponse(content="recovered", raw_response={}),
            ]
        )
        registry = _mock_registry(prov)
        router = FallbackRouter(
            routes=[_make_route()],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )
        # Patch sleep to avoid waiting in tests
        import scenario_lab.router as router_module
        original_sleep = router_module.time.sleep
        router_module.time.sleep = lambda _: None
        try:
            resp = router.complete("sys", "usr")
        finally:
            router_module.time.sleep = original_sleep
        assert resp.content == "recovered"
        assert prov.complete.call_count == 2

    def test_rate_limit_exhausted_raises(self):
        prov = _mock_provider(
            complete_side_effect=LLMRateLimitError("always limited")
        )
        registry = _mock_registry(prov)
        router = FallbackRouter(
            routes=[_make_route()],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )
        import scenario_lab.router as router_module
        router_module.time.sleep = lambda _: None
        try:
            with pytest.raises(LLMError, match="All routes failed"):
                router.complete("sys", "usr")
        finally:
            router_module.time.sleep = __import__("time").sleep

        assert prov.complete.call_count == FallbackRouter.MAX_RETRIES


class TestFallbackRouterFallback:
    def test_falls_back_to_second_route_on_error(self):
        prov1 = _mock_provider(
            name="openrouter",
            complete_side_effect=LLMError("first failed"),
        )
        prov2 = _mock_provider(
            name="anthropic",
            complete_return=LLMResponse(content="fallback ok", raw_response={}),
        )
        registry = _mock_registry(prov1, prov2)
        router = FallbackRouter(
            routes=[_make_route("openrouter"), _make_route("anthropic")],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )
        resp = router.complete("sys", "usr")
        assert resp.content == "fallback ok"
        assert prov1.complete.call_count == 1
        assert prov2.complete.call_count == 1

    def test_all_routes_fail_raises(self):
        prov1 = _mock_provider(name="openrouter", complete_side_effect=LLMError("fail"))
        prov2 = _mock_provider(name="anthropic", complete_side_effect=LLMError("also fail"))
        registry = _mock_registry(prov1, prov2)
        router = FallbackRouter(
            routes=[_make_route("openrouter"), _make_route("anthropic")],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )
        with pytest.raises(LLMError, match="All routes failed"):
            router.complete("sys", "usr")
