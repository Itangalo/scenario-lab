"""Tests for model-scoped call limits (llm.model_limits).

Limits follow the model, not the step: a reasoning model needs a large budget
and a long deadline whatever it is doing. Task entries and model entries are
lower bounds; the resolved value is the larger of the applicable floors.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import yaml

from scenario_lab.loader import load_scenario, parse_model_limits
from scenario_lab.models import LLMConfig, ModelLimits, ModelRoute
from scenario_lab.router import FallbackRouter
from scenario_lab.validator import validate_llm_config


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def _config(**overrides) -> LLMConfig:
    defaults = dict(
        max_tokens=3000,
        call_timeout_seconds=300,
        model_limits={
            "openrouter:stealth/ox-alpha": ModelLimits(
                max_tokens=32000, call_timeout_seconds=1800
            )
        },
    )
    defaults.update(overrides)
    return LLMConfig(**defaults)


def test_resolve_limits_applies_model_floors():
    config = _config()
    route = ModelRoute("openrouter", "stealth/ox-alpha")

    limits = config.resolve_limits(route)

    assert limits.max_tokens == 32000
    assert limits.call_timeout_seconds == 1800


def test_resolve_limits_composes_task_and_model_as_lower_bounds():
    """max(3500, 32000) = 32000: a task entry raises the floor, never caps."""
    config = _config(max_tokens_by_task={"rules": 3500})
    route = ModelRoute("openrouter", "stealth/ox-alpha")

    assert config.resolve_limits(route, task="rules").max_tokens == 32000


def test_resolve_limits_leaves_other_models_untouched():
    config = _config()

    limits = config.resolve_limits(ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"))

    assert limits.max_tokens == 3000
    assert limits.call_timeout_seconds == 300


def test_resolve_limits_accepts_route_string_key():
    config = _config()
    assert config.resolve_limits("openrouter:stealth/ox-alpha").max_tokens == 32000


def test_resolve_limits_partial_entry_only_raises_one_floor():
    config = _config(
        model_limits={"openrouter:stealth/ox-alpha": ModelLimits(max_tokens=8000)}
    )

    limits = config.resolve_limits(ModelRoute("openrouter", "stealth/ox-alpha"))

    assert limits.max_tokens == 8000
    assert limits.call_timeout_seconds == 300


def test_limits_resolver_binds_task_and_default():
    config = _config(max_tokens_by_task={"rules": 3500})
    ox = ModelRoute("openrouter", "stealth/ox-alpha")
    qwen = ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")

    # Task-bound: per-route resolution for a fallback list
    resolver = config.limits_resolver("rules")
    assert resolver(ox).max_tokens == 32000
    assert resolver(qwen).max_tokens == 3500

    # Default override replaces the task lookup as the starting budget
    chained = config.limits_resolver("synthesis", max_tokens_default=4000)
    assert chained(qwen).max_tokens == 4000
    assert chained(ox).max_tokens == 32000


# ---------------------------------------------------------------------------
# Parsing and inheritance
# ---------------------------------------------------------------------------

def _scenario_with_llm(tmp_path, llm_block: dict):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "metrics.md").write_text(
        "## m\n**ID:** m\n**Min:** 0\n**Max:** 100\n**Start value:** 1\n"
    )
    (scenario_dir / "events.md").write_text("")
    (scenario_dir / "metric-rules.md").write_text("1. x\n")
    background = scenario_dir / "background" / "actors"
    background.mkdir(parents=True)
    (scenario_dir / "background" / "context.md").write_text("x")
    (background / "reg.md").write_text(
        "# R\n## Short description\nR\n## Long description\nR\n"
        "### Statements\n- `s` (position): x\n"
    )
    (scenario_dir / "scenario.yaml").write_text(
        yaml.dump({
            "name": "t", "description": "t", "start_date": "2026-01",
            "time_scale": "months", "max_turns": 2, "actors": ["reg"],
            "llm": llm_block,
        })
    )
    return scenario_dir


def test_loader_parses_model_limits(tmp_path):
    scenario = load_scenario(_scenario_with_llm(tmp_path, {
        "model": "openrouter:qwen/qwen3-235b-a22b-2507",
        "model_limits": {
            "openrouter:stealth/ox-alpha": {
                "max_tokens": 32000, "call_timeout_seconds": 1800,
            }
        },
    }))
    llm = scenario.config.llm

    assert llm.model_limits["openrouter:stealth/ox-alpha"].max_tokens == 32000
    assert llm.model_limits["openrouter:stealth/ox-alpha"].call_timeout_seconds == 1800


def test_loader_rejects_unknown_model_limits_field(tmp_path):
    with pytest.raises(ValueError, match="unknown field"):
        parse_model_limits({"openrouter:x": {"max_tokns": 5}})


def test_loader_rejects_prefix_less_model_limits_key():
    with pytest.raises(ValueError, match="provider:model"):
        parse_model_limits({"x/y": {"max_tokens": 5}})


def test_loader_rejects_non_integer_model_limits_value():
    with pytest.raises(ValueError, match="must be an integer"):
        parse_model_limits({"openrouter:x": {"max_tokens": "big"}})


def test_model_limits_inherit_from_base_and_merge(tmp_path):
    llm_base = {
        "model": "openrouter:qwen/qwen3-235b-a22b-2507",
        "model_limits": {
            "openrouter:stealth/ox-alpha": {"max_tokens": 32000},
        },
    }
    scenario_dir = _scenario_with_llm(tmp_path, llm_base)

    # Variants live inside the scenario so its resources stay resolvable.
    variants = scenario_dir / "variants"
    variants.mkdir()
    (variants / "v.yaml").write_text(yaml.dump({
        "base": "../scenario.yaml",
        "name": "v",
        "llm": {
            "model": "openrouter:qwen/qwen3-235b-a22b-2507",
            "model_limits": {
                "anthropic:claude-sonnet-4-6": {"call_timeout_seconds": 900},
            },
        },
    }))

    llm = load_scenario(variants / "v.yaml").config.llm
    assert "openrouter:stealth/ox-alpha" in llm.model_limits
    assert "anthropic:claude-sonnet-4-6" in llm.model_limits


# ---------------------------------------------------------------------------
# Routing: limits resolve per route attempt
# ---------------------------------------------------------------------------

def _registry_with(*providers) -> MagicMock:
    registry = MagicMock()
    providers = list(providers)
    registry.get.side_effect = lambda name: next(
        p for p in providers if p.name == name
    )
    return registry


def test_router_resolves_limits_per_route():
    """A fallback list pairs a reasoning model with an instruct one correctly."""
    slow_prov = MagicMock()
    slow_prov.name = "openrouter"
    fast_prov = MagicMock()
    fast_prov.name = "anthropic"
    from scenario_lab.llm import LLMError

    slow_prov.complete.side_effect = LLMError("rejected")
    fast_prov.complete.return_value.content = "ok"

    config = _config()
    router = FallbackRouter(
        routes=[
            ModelRoute("openrouter", "stealth/ox-alpha"),
            ModelRoute("anthropic", "claude-haiku"),
        ],
        registry=_registry_with(slow_prov, fast_prov),
        temperature=0.7,
        max_tokens=100,
        limits_resolver=config.limits_resolver(),
    )
    router.complete("sys", "usr")

    # Primary got the model floors; fallback got the global defaults.
    assert slow_prov.complete.call_args.kwargs["max_tokens"] == 32000
    assert slow_prov.complete.call_args.kwargs["call_timeout_seconds"] == 1800
    assert fast_prov.complete.call_args.kwargs["max_tokens"] == 3000
    assert fast_prov.complete.call_args.kwargs["call_timeout_seconds"] == 300


def test_router_without_resolver_passes_none_timeout():
    prov = MagicMock()
    prov.name = "openrouter"
    prov.complete.return_value.content = "ok"

    router = FallbackRouter(
        routes=[ModelRoute("openrouter", "x/y")],
        registry=_registry_with(prov),
        temperature=0.7,
        max_tokens=250,
    )
    router.complete("sys", "usr")

    assert prov.complete.call_args.kwargs["max_tokens"] == 250
    assert prov.complete.call_args.kwargs["call_timeout_seconds"] is None


def test_router_requires_max_tokens_or_resolver():
    with pytest.raises(ValueError, match="limits_resolver"):
        FallbackRouter(
            routes=[ModelRoute("openrouter", "x/y")],
            registry=_registry_with(MagicMock()),
            temperature=0.7,
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_validator_flags_unknown_model_limits_key(tmp_path):
    scenario = load_scenario(_scenario_with_llm(tmp_path, {
        "model": "openrouter:qwen/qwen3-235b-a22b-2507",
        "model_limits": {"openrouter:nobody/uses-this": {"max_tokens": 5000}},
    }))

    _errors, warnings = validate_llm_config(scenario)

    assert any("'openrouter:nobody/uses-this'" in w for w in warnings)


def test_validator_bounds_per_model_values(tmp_path):
    scenario = load_scenario(_scenario_with_llm(tmp_path, {
        "model": "openrouter:qwen/qwen3-235b-a22b-2507",
        "model_limits": {
            "openrouter:qwen/qwen3-235b-a22b-2507": {
                "max_tokens": 50, "call_timeout_seconds": 2,
            }
        },
    }))

    errors, _warnings = validate_llm_config(scenario)

    assert any("max_tokens=50" in e for e in errors)
    assert any("call_timeout_seconds" in e for e in errors)


def test_validator_accepts_known_model_limits_key(tmp_path):
    scenario = load_scenario(_scenario_with_llm(tmp_path, {
        "events": [
            "openrouter:stealth/ox-alpha",
            "openrouter:google/gemini-3-flash-preview",
        ],
        "model_limits": {
            "openrouter:stealth/ox-alpha": {
                "max_tokens": 32000, "call_timeout_seconds": 1800,
            }
        },
    }))

    assert validate_llm_config(scenario) == ([], [])
