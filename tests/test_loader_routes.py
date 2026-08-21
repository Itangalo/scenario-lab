"""Tests for parse_route / parse_routes helpers in loader.py."""

import pytest

from scenario_lab.loader import parse_route, parse_routes, parse_actor_routes
from scenario_lab.models import ModelRoute


class TestParseRoute:
    def test_shorthand_string(self):
        route = parse_route("openrouter:qwen/qwen3-235b-a22b-2507")
        assert route == ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")

    def test_anthropic_shorthand(self):
        route = parse_route("anthropic:claude-opus-4-6")
        assert route == ModelRoute("anthropic", "claude-opus-4-6")

    def test_dict_form(self):
        route = parse_route({"provider": "openrouter", "model": "qwen/qwen3-235b-a22b-2507"})
        assert route == ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")

    def test_bare_string_raises(self):
        with pytest.raises(ValueError, match="missing a provider prefix"):
            parse_route("qwen/qwen3-235b-a22b-2507")

    def test_dict_missing_provider_raises(self):
        with pytest.raises(ValueError, match="provider"):
            parse_route({"model": "qwen/qwen3-235b-a22b-2507"})

    def test_dict_missing_model_raises(self):
        with pytest.raises(ValueError, match="model"):
            parse_route({"provider": "openrouter"})

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            parse_route(42)

    def test_model_str(self):
        route = parse_route("openrouter:qwen/qwen3-235b-a22b-2507")
        assert str(route) == "openrouter:qwen/qwen3-235b-a22b-2507"


class TestParseRoutes:
    def test_single_string(self):
        routes = parse_routes("openrouter:qwen/qwen3-235b-a22b-2507")
        assert routes == [ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")]

    def test_single_dict(self):
        routes = parse_routes({"provider": "anthropic", "model": "claude-opus-4-6"})
        assert routes == [ModelRoute("anthropic", "claude-opus-4-6")]

    def test_list_of_strings(self):
        routes = parse_routes(["openrouter:qwen/qwen3-235b-a22b-2507", "anthropic:claude-opus-4-6"])
        assert routes == [
            ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
            ModelRoute("anthropic", "claude-opus-4-6"),
        ]

    def test_mixed_list(self):
        routes = parse_routes([
            "anthropic:claude-opus-4-6",
            {"provider": "openrouter", "model": "qwen/qwen3-235b-a22b-2507"},
        ])
        assert routes == [
            ModelRoute("anthropic", "claude-opus-4-6"),
            ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
        ]

    def test_bare_string_in_list_raises(self):
        with pytest.raises(ValueError, match="missing a provider prefix"):
            parse_routes(["qwen/qwen3-235b-a22b-2507"])


class TestParseActorRoutes:
    def test_single_route_string(self):
        result = parse_actor_routes("openrouter:qwen/qwen3-235b-a22b-2507")
        assert result == ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")

    def test_list_of_routes(self):
        result = parse_actor_routes([
            "openrouter:qwen/qwen3-235b-a22b-2507",
            "openrouter:google/gemini-3-flash-preview",
        ])
        assert result == [
            ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
            ModelRoute("openrouter", "google/gemini-3-flash-preview"),
        ]

    def test_per_actor_dict(self):
        result = parse_actor_routes({
            "government": "openrouter:qwen/qwen3-235b-a22b-2507",
            "media": "anthropic:claude-opus-4-6",
        })
        assert result == {
            "government": ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
            "media": ModelRoute("anthropic", "claude-opus-4-6"),
        }

    def test_per_actor_dict_with_fallback_lists(self):
        result = parse_actor_routes({
            "government": [
                "anthropic:claude-opus-4-6",
                "openrouter:qwen/qwen3-235b-a22b-2507",
            ],
        })
        assert result == {
            "government": [
                ModelRoute("anthropic", "claude-opus-4-6"),
                ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
            ],
        }
