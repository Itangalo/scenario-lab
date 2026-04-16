"""Anthropic pricing lookup using LiteLLM's model catalog."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import json
import os

import httpx


LITELLM_PRICES_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
DEFAULT_CACHE_TTL_HOURS = 72
BUNDLED_PRICING_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "anthropic_pricing_seed.json"
)
DEFAULT_CACHE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / ".scenario-lab-cache"
    / "anthropic-pricing.json"
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _normalize_snapshot(data: object) -> Optional[dict]:
    """Normalize a pricing snapshot loaded from disk (same format as OpenRouter)."""
    if not isinstance(data, dict):
        return None

    raw_models = data.get("models")
    if not isinstance(raw_models, dict):
        return None

    models: dict[str, dict[str, float]] = {}
    for model_id, raw_pricing in raw_models.items():
        if not isinstance(model_id, str) or not isinstance(raw_pricing, dict):
            continue
        try:
            prompt = float(raw_pricing["prompt"])
            completion = float(raw_pricing["completion"])
        except (KeyError, TypeError, ValueError):
            continue
        models[model_id] = {
            "prompt": round(prompt, 4),
            "completion": round(completion, 4),
        }

    if not models:
        return None

    fetched_at = data.get("fetched_at")
    return {
        "fetched_at": fetched_at if isinstance(fetched_at, str) else None,
        "models": models,
        "source": data.get("source", "unknown"),
    }


def load_pricing_snapshot(path: Path) -> Optional[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return _normalize_snapshot(raw)


def fetch_anthropic_pricing_snapshot() -> Optional[dict]:
    """Fetch LiteLLM model catalog and extract Anthropic pricing."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(LITELLM_PRICES_URL)
            response.raise_for_status()
            catalog = response.json()
    except Exception:
        return None

    if not isinstance(catalog, dict):
        return None

    models: dict[str, dict[str, float]] = {}
    for model_id, entry in catalog.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("litellm_provider") != "anthropic":
            continue
        try:
            prompt = float(entry["input_cost_per_token"]) * 1_000_000
            completion = float(entry["output_cost_per_token"]) * 1_000_000
        except (KeyError, TypeError, ValueError):
            continue
        models[model_id] = {
            "prompt": round(prompt, 4),
            "completion": round(completion, 4),
        }

    if not models:
        return None

    return {
        "fetched_at": _now_utc().isoformat().replace("+00:00", "Z"),
        "models": models,
        "source": "litellm",
    }


class AnthropicPricingCache:
    """Pricing cache for Anthropic models backed by LiteLLM catalog."""

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        bundled_path: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
    ):
        resolved_ttl_hours = ttl_hours
        if resolved_ttl_hours is None or resolved_ttl_hours < 1:
            resolved_ttl_hours = DEFAULT_CACHE_TTL_HOURS

        if cache_path is not None:
            resolved_cache_path = Path(cache_path)
        else:
            resolved_cache_path = DEFAULT_CACHE_PATH

        self.cache_path = resolved_cache_path
        self.bundled_path = bundled_path or BUNDLED_PRICING_PATH
        self.ttl = timedelta(hours=resolved_ttl_hours)
        self._snapshot: Optional[dict] = None
        self._refresh_attempted = False

    def get_model_pricing(self, model: str) -> Optional[dict]:
        """Return pricing for a model, refreshing the cache if needed."""
        snapshot = self._load_snapshot()
        model_missing = snapshot is None or model not in snapshot["models"]
        cache_stale = self._is_snapshot_stale(snapshot)

        if (model_missing or cache_stale) and not self._refresh_attempted:
            self.refresh()
            self._refresh_attempted = True
            snapshot = self._load_snapshot(force_reload=True)

        if snapshot is None:
            return None

        pricing = snapshot["models"].get(model)
        if pricing is None:
            return None

        return {"prompt": pricing["prompt"], "completion": pricing["completion"]}

    def refresh(self) -> bool:
        """Fetch the latest pricing and persist locally."""
        snapshot = fetch_anthropic_pricing_snapshot()
        if snapshot is None:
            return False
        self._snapshot = snapshot
        self._write_snapshot(snapshot)
        return True

    def _load_snapshot(self, force_reload: bool = False) -> Optional[dict]:
        if self._snapshot is not None and not force_reload:
            return self._snapshot
        runtime_snapshot = load_pricing_snapshot(self.cache_path)
        bundled_snapshot = load_pricing_snapshot(self.bundled_path)
        self._snapshot = runtime_snapshot or bundled_snapshot
        return self._snapshot

    def _is_snapshot_stale(self, snapshot: Optional[dict]) -> bool:
        if snapshot is None:
            return True
        fetched_at = _parse_timestamp(snapshot.get("fetched_at"))
        if fetched_at is None:
            return True
        return _now_utc() - fetched_at > self.ttl

    def _write_snapshot(self, snapshot: dict) -> None:
        payload = json.dumps(snapshot, indent=2, ensure_ascii=False)
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(payload, encoding="utf-8")
        except OSError:
            return


_DEFAULT_ANTHROPIC_PRICING_CACHE = AnthropicPricingCache()


def get_anthropic_pricing_cache() -> AnthropicPricingCache:
    """Return the process-wide Anthropic pricing cache."""
    return _DEFAULT_ANTHROPIC_PRICING_CACHE
