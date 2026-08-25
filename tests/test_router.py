"""Tests for FallbackRouter."""

import pytest
from unittest.mock import MagicMock, call, patch

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
        original_sleep = router_module.time.sleep
        router_module.time.sleep = lambda _: None
        try:
            with pytest.raises(LLMError, match="All routes failed"):
                router.complete("sys", "usr")
        finally:
            # Restore the captured original – re-reading the attribute here
            # would return the lambda we just installed and leak the patch.
            router_module.time.sleep = original_sleep

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


# ---------------------------------------------------------------------------
# Regression: a transient network failure must not end a run
#
# A qwen3-235b run died at turn 3 with "The read operation timed out". httpx
# raised correctly, but the provider wrapped it as a plain LLMError, which the
# router classifies as non-retryable. With a single configured route – what
# most scenarios have – that ended the whole run on one slow response.
# ---------------------------------------------------------------------------

class TestTransientErrorRetry:
    def _router(self, provider, routes=None):
        from scenario_lab.router import FallbackRouter
        from scenario_lab.models import ModelRoute

        registry = MagicMock()
        registry.get.return_value = provider
        return FallbackRouter(
            routes=routes or [ModelRoute("openrouter", "vendor/model-a")],
            registry=registry,
            temperature=0.7,
            max_tokens=100,
        )

    def test_read_timeout_is_retried_on_the_same_route(self):
        from scenario_lab.llm import LLMResponse, LLMTransientError

        provider = MagicMock()
        provider.complete.side_effect = [
            LLMTransientError("The read operation timed out"),
            LLMResponse(content="recovered", raw_response={}),
        ]

        with patch("time.sleep"):
            result = self._router(provider).complete("sys", "usr")

        assert result.content == "recovered"
        assert provider.complete.call_count == 2

    def test_single_route_survives_transient_failures(self):
        """The exact shape of the crash: one route, one transient failure."""
        from scenario_lab.llm import LLMResponse, LLMTransientError

        provider = MagicMock()
        provider.complete.side_effect = [
            LLMTransientError("timed out"),
            LLMTransientError("timed out again"),
            LLMResponse(content="third time lucky", raw_response={}),
        ]

        with patch("time.sleep"):
            result = self._router(provider).complete("sys", "usr")

        assert result.content == "third time lucky"

    def test_transient_failures_eventually_give_up(self):
        from scenario_lab.llm import LLMError, LLMTransientError

        provider = MagicMock()
        provider.complete.side_effect = LLMTransientError("permanently unreachable")

        with patch("time.sleep"):
            with pytest.raises(LLMError, match="All routes failed"):
                self._router(provider).complete("sys", "usr")

        assert provider.complete.call_count == 3

    def test_wall_clock_timeout_is_treated_as_transient(self):
        from scenario_lab.llm import LLMCallTimeoutError, LLMResponse

        provider = MagicMock()
        provider.complete.side_effect = [
            LLMCallTimeoutError("exceeded 300s"),
            LLMResponse(content="ok", raw_response={}),
        ]

        with patch("time.sleep"):
            result = self._router(provider).complete("sys", "usr")

        assert result.content == "ok"

    def test_reasoning_budget_error_is_not_retried(self):
        """Retrying an exhausted reasoning budget identically cannot succeed."""
        from scenario_lab.llm import LLMError, LLMReasoningBudgetError

        provider = MagicMock()
        provider.complete.side_effect = LLMReasoningBudgetError("budget spent on reasoning")

        with patch("time.sleep"):
            with pytest.raises(LLMError, match="All routes failed"):
                self._router(provider).complete("sys", "usr")

        assert provider.complete.call_count == 1

    def test_transient_retry_also_covers_structured_calls(self):
        from scenario_lab.llm import LLMResponse, LLMTransientError

        provider = MagicMock()
        provider.complete_structured.side_effect = [
            LLMTransientError("timed out"),
            LLMResponse(content="{}", raw_response={}, structured_data={}),
        ]

        with patch("time.sleep"):
            result = self._router(provider).complete_structured(
                "sys", "usr", schema={"type": "object"}, schema_name="s"
            )

        assert result.structured_data == {}
        assert provider.complete_structured.call_count == 2
