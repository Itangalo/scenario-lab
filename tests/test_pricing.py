"""Tests for OpenRouter pricing cache behavior."""

from datetime import datetime, timedelta, timezone
import json

from scenario_lab.cost import CostCalculator
from scenario_lab.pricing import OpenRouterPricingCache


def _timestamp(hours_ago: int) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    ).isoformat().replace("+00:00", "Z")


def _write_snapshot(path, fetched_at: str, models: dict[str, dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "fetched_at": fetched_at,
                "source": "test",
                "models": models,
            }
        ),
        encoding="utf-8",
    )


def test_pricing_cache_uses_fresh_runtime_cache(monkeypatch, tmp_path):
    """Fresh cache entries should be used without an online refresh."""
    cache_path = tmp_path / "runtime.json"
    bundled_path = tmp_path / "bundled.json"
    _write_snapshot(
        cache_path,
        _timestamp(hours_ago=1),
        {"provider/model-a": {"prompt": 1.1, "completion": 2.2}},
    )

    refresh_calls = []

    def _unexpected_refresh():
        refresh_calls.append("called")
        return None

    monkeypatch.setattr(
        "scenario_lab.pricing.fetch_openrouter_pricing_snapshot",
        _unexpected_refresh,
    )

    cache = OpenRouterPricingCache(
        cache_path=cache_path,
        bundled_path=bundled_path,
        ttl_hours=72,
    )

    assert cache.get_model_pricing("provider/model-a") == {
        "prompt": 1.1,
        "completion": 2.2,
    }
    assert refresh_calls == []


def test_pricing_cache_refreshes_stale_snapshot(monkeypatch, tmp_path):
    """Stale cache data should be replaced from OpenRouter when refresh succeeds."""
    cache_path = tmp_path / "runtime.json"
    bundled_path = tmp_path / "bundled.json"
    _write_snapshot(
        bundled_path,
        _timestamp(hours_ago=200),
        {"provider/model-a": {"prompt": 1.0, "completion": 2.0}},
    )

    monkeypatch.setattr(
        "scenario_lab.pricing.fetch_openrouter_pricing_snapshot",
        lambda: {
            "fetched_at": _timestamp(hours_ago=0),
            "source": "openrouter",
            "models": {
                "provider/model-a": {"prompt": 3.0, "completion": 4.0},
            },
        },
    )

    cache = OpenRouterPricingCache(
        cache_path=cache_path,
        bundled_path=bundled_path,
        ttl_hours=72,
    )

    assert cache.get_model_pricing("provider/model-a") == {
        "prompt": 3.0,
        "completion": 4.0,
    }
    written = json.loads(cache_path.read_text(encoding="utf-8"))
    assert written["models"]["provider/model-a"] == {
        "prompt": 3.0,
        "completion": 4.0,
    }


def test_pricing_cache_refreshes_when_model_missing(monkeypatch, tmp_path):
    """Missing models should trigger a refresh even when the cache is fresh."""
    cache_path = tmp_path / "runtime.json"
    bundled_path = tmp_path / "bundled.json"
    _write_snapshot(
        bundled_path,
        _timestamp(hours_ago=1),
        {"provider/model-a": {"prompt": 1.0, "completion": 2.0}},
    )

    monkeypatch.setattr(
        "scenario_lab.pricing.fetch_openrouter_pricing_snapshot",
        lambda: {
            "fetched_at": _timestamp(hours_ago=0),
            "source": "openrouter",
            "models": {
                "provider/model-a": {"prompt": 1.0, "completion": 2.0},
                "provider/model-b": {"prompt": 5.0, "completion": 6.0},
            },
        },
    )

    cache = OpenRouterPricingCache(
        cache_path=cache_path,
        bundled_path=bundled_path,
        ttl_hours=72,
    )

    assert cache.get_model_pricing("provider/model-b") == {
        "prompt": 5.0,
        "completion": 6.0,
    }


def test_pricing_cache_falls_back_to_stale_data_when_refresh_fails(monkeypatch, tmp_path):
    """Stale cached pricing should still be used if OpenRouter refresh fails."""
    cache_path = tmp_path / "runtime.json"
    bundled_path = tmp_path / "bundled.json"
    _write_snapshot(
        cache_path,
        _timestamp(hours_ago=200),
        {"provider/model-a": {"prompt": 7.0, "completion": 8.0}},
    )

    monkeypatch.setattr(
        "scenario_lab.pricing.fetch_openrouter_pricing_snapshot",
        lambda: None,
    )

    cache = OpenRouterPricingCache(
        cache_path=cache_path,
        bundled_path=bundled_path,
        ttl_hours=72,
    )

    assert cache.get_model_pricing("provider/model-a") == {
        "prompt": 7.0,
        "completion": 8.0,
    }


class _FakePricingCache:
    def __init__(self, prices: dict[str, dict[str, float]]):
        self.prices = prices

    def get_model_pricing(self, model: str):
        return self.prices.get(model)


def test_cost_normalization_maps_dated_openrouter_revision_to_base(monkeypatch):
    """Dated OpenRouter model ids should resolve to the stable base model price."""
    monkeypatch.setattr(
        CostCalculator,
        "_pricing_cache",
        _FakePricingCache(
            {
                "openai/gpt-5.4-nano": {"prompt": 0.2, "completion": 1.25},
            }
        ),
    )

    assert (
        CostCalculator.normalize_model_name("openai/gpt-5.4-nano-20260317")
        == "openai/gpt-5.4-nano"
    )


def test_cost_normalization_keeps_exact_dated_model_when_cache_knows_it(monkeypatch):
    """Exact cache hits should win over stripping a dated suffix."""
    monkeypatch.setattr(
        CostCalculator,
        "_pricing_cache",
        _FakePricingCache(
            {
                "openai/gpt-5.4-nano": {"prompt": 0.2, "completion": 1.25},
                "openai/gpt-5.4-nano-20260317": {
                    "prompt": 0.21,
                    "completion": 1.3,
                },
            }
        ),
    )

    assert (
        CostCalculator.get_model_pricing("openai/gpt-5.4-nano-20260317")
        == {"prompt": 0.21, "completion": 1.3}
    )
