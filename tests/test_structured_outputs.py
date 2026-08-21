"""Tests for provider-native structured outputs in the events step."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
import yaml

from scenario_lab.llm import (
    LLMError,
    LLMRateLimitError,
    LLMResponse,
    LLMUnsupportedStructuredError,
    MockLLMClient,
)
from scenario_lab.loader import load_scenario
from scenario_lab.models import LLMConfig, ModelRoute
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager
from scenario_lab.providers.anthropic import AnthropicProvider
from scenario_lab.providers.openrouter import OpenRouterProvider
from scenario_lab.providers.registry import ProviderRegistry
from scenario_lab.router import FallbackRouter
from scenario_lab.schemas import (
    EVENTS_SCHEMA_NAME,
    events_array_schema,
    events_object_schema,
)


EVENTS_PAYLOAD = [{"id": "ai_breakthrough", "probability": 1.0}]


# ---------------------------------------------------------------------------
# OpenRouter structured path
# ---------------------------------------------------------------------------


class _MockHTTPResponse:
    """Streaming-capable stand-in; the provider reads the body incrementally
    so it can enforce a wall-clock deadline per call."""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def read(self):
        return json.dumps(self.json_data).encode("utf-8")

    def iter_bytes(self):
        yield json.dumps(self.json_data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=MagicMock(), response=self)


def _openrouter_success(content: str) -> _MockHTTPResponse:
    return _MockHTTPResponse({"choices": [{"message": {"content": content}}]})


class TestOpenRouterStructured:
    def test_request_body_shape(self):
        """The request body carries response_format with a strict json_schema."""
        provider = OpenRouterProvider(api_key="key")
        schema = events_array_schema()
        with patch.object(
            provider._client, "stream", return_value=_openrouter_success("[]")
        ) as mock_post:
            provider.complete_structured(
                "sys", "usr",
                model="x/y", temperature=0.5, max_tokens=200,
                schema=schema, schema_name=EVENTS_SCHEMA_NAME,
            )

        body = mock_post.call_args.kwargs["json"]
        assert body["model"] == "x/y"
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 200
        assert body["response_format"] == {
            "type": "json_schema",
            "json_schema": {
                "name": EVENTS_SCHEMA_NAME,
                "strict": True,
                "schema": schema,
            },
        }

    def test_structured_data_unwrapped(self):
        """Valid JSON content is parsed into structured_data."""
        provider = OpenRouterProvider(api_key="key")
        content = json.dumps(EVENTS_PAYLOAD)
        with patch.object(
            provider._client, "stream", return_value=_openrouter_success(content)
        ):
            resp = provider.complete_structured(
                "sys", "usr",
                model="x/y", temperature=0.7, max_tokens=100,
                schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
            )

        assert resp.structured_data == EVENTS_PAYLOAD
        assert resp.content == content

    def test_4xx_raises_unsupported(self):
        """A 4xx rejection surfaces as LLMUnsupportedStructuredError."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client, "stream", return_value=_MockHTTPResponse({}, status_code=400)
        ):
            with pytest.raises(LLMUnsupportedStructuredError):
                provider.complete_structured(
                    "sys", "usr",
                    model="x/y", temperature=0.7, max_tokens=100,
                    schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
                )

    def test_429_raises_rate_limit(self):
        """Rate limits keep their type so the router can retry."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client, "stream", return_value=_MockHTTPResponse({}, status_code=429)
        ):
            with pytest.raises(LLMRateLimitError):
                provider.complete_structured(
                    "sys", "usr",
                    model="x/y", temperature=0.7, max_tokens=100,
                    schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
                )

    def test_5xx_raises_llm_error(self):
        """Server errors stay generic LLMError (not unsupported)."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client, "stream", return_value=_MockHTTPResponse({}, status_code=503)
        ):
            with pytest.raises(LLMError) as exc_info:
                provider.complete_structured(
                    "sys", "usr",
                    model="x/y", temperature=0.7, max_tokens=100,
                    schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
                )
        assert not isinstance(exc_info.value, LLMUnsupportedStructuredError)

    def test_non_json_content_raises_unsupported(self):
        """A model that ignores the schema contract is treated as unsupported."""
        provider = OpenRouterProvider(api_key="key")
        with patch.object(
            provider._client, "stream", return_value=_openrouter_success("not json")
        ):
            with pytest.raises(LLMUnsupportedStructuredError):
                provider.complete_structured(
                    "sys", "usr",
                    model="x/y", temperature=0.7, max_tokens=100,
                    schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
                )


# ---------------------------------------------------------------------------
# Anthropic structured path (forced tool call)
# ---------------------------------------------------------------------------


def _anthropic_provider():
    mock_sdk = MagicMock()
    mock_sdk.RateLimitError = type("RateLimitError", (Exception,), {})
    mock_sdk.APIStatusError = type(
        "APIStatusError", (Exception,), {"status_code": 500, "message": "err"}
    )
    prov = AnthropicProvider.__new__(AnthropicProvider)
    prov._sdk = mock_sdk
    prov._client = MagicMock()
    return prov


def _anthropic_tool_message(events: list, schema_name: str = EVENTS_SCHEMA_NAME):
    block = MagicMock()
    block.type = "tool_use"
    block.name = schema_name
    block.input = {"events": events}

    msg = MagicMock()
    msg.id = "msg_structured"
    msg.content = [block]
    msg.stop_reason = "tool_use"

    usage = MagicMock()
    usage.input_tokens = 20
    usage.output_tokens = 10
    usage.cache_creation_input_tokens = 0
    usage.cache_read_input_tokens = 0
    msg.usage = usage
    return msg


class TestAnthropicStructured:
    def test_forced_tool_call_request_shape(self):
        """The request includes a tool wrapping the array schema and a forced tool_choice."""
        prov = _anthropic_provider()
        prov._client.messages.create.return_value = _anthropic_tool_message([])
        schema = events_array_schema()

        prov.complete_structured(
            "sys", "usr",
            model="claude-sonnet-4-6", temperature=0.5, max_tokens=300,
            schema=schema, schema_name=EVENTS_SCHEMA_NAME,
        )

        kwargs = prov._client.messages.create.call_args.kwargs
        assert kwargs["tool_choice"] == {"type": "tool", "name": EVENTS_SCHEMA_NAME}
        assert len(kwargs["tools"]) == 1
        tool = kwargs["tools"][0]
        assert tool["name"] == EVENTS_SCHEMA_NAME
        assert tool["input_schema"]["type"] == "object"
        assert tool["input_schema"]["properties"]["events"] == schema
        assert tool["input_schema"]["required"] == ["events"]

    def test_tool_use_input_unwrapped(self):
        """The tool-use input is unwrapped back to the array."""
        prov = _anthropic_provider()
        prov._client.messages.create.return_value = _anthropic_tool_message(
            EVENTS_PAYLOAD
        )

        resp = prov.complete_structured(
            "sys", "usr",
            model="claude-sonnet-4-6", temperature=0.7, max_tokens=300,
            schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
        )

        assert resp.structured_data == EVENTS_PAYLOAD
        assert json.loads(resp.content) == EVENTS_PAYLOAD
        usage = resp.get_usage()
        assert usage is not None
        assert usage.provider == "anthropic"
        assert usage.total_tokens == 30

    def test_4xx_raises_unsupported(self):
        """A 4xx APIStatusError surfaces as LLMUnsupportedStructuredError."""
        prov = _anthropic_provider()

        class APIStatusError(Exception):
            status_code = 400
            message = "tools not supported"

        prov._sdk.APIStatusError = APIStatusError
        prov._client.messages.create.side_effect = APIStatusError("bad request")

        with pytest.raises(LLMUnsupportedStructuredError):
            prov.complete_structured(
                "sys", "usr",
                model="claude-sonnet-4-6", temperature=0.7, max_tokens=300,
                schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
            )

    def test_5xx_raises_llm_error(self):
        """Server-side APIStatusError stays a generic LLMError."""
        prov = _anthropic_provider()

        class APIStatusError(Exception):
            status_code = 503
            message = "overloaded"

        prov._sdk.APIStatusError = APIStatusError
        prov._client.messages.create.side_effect = APIStatusError("down")

        with pytest.raises(LLMError) as exc_info:
            prov.complete_structured(
                "sys", "usr",
                model="claude-sonnet-4-6", temperature=0.7, max_tokens=300,
                schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
            )
        assert not isinstance(exc_info.value, LLMUnsupportedStructuredError)

    def test_missing_tool_use_raises_unsupported(self):
        """A response without a usable tool call is treated as unsupported."""
        prov = _anthropic_provider()
        msg = _anthropic_tool_message([])
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "I cannot use tools."
        msg.content = [text_block]
        prov._client.messages.create.return_value = msg

        with pytest.raises(LLMUnsupportedStructuredError):
            prov.complete_structured(
                "sys", "usr",
                model="claude-sonnet-4-6", temperature=0.7, max_tokens=300,
                schema=events_array_schema(), schema_name=EVENTS_SCHEMA_NAME,
            )


# ---------------------------------------------------------------------------
# Router threading
# ---------------------------------------------------------------------------


def _registry_with(*providers) -> ProviderRegistry:
    registry = ProviderRegistry()
    for p in providers:
        registry.register(p)
    return registry


class TestRouterStructured:
    def test_threads_parameters_to_provider(self):
        """complete_structured passes route, sampling, and schema parameters through."""
        prov = MagicMock()
        prov.name = "openrouter"
        expected = LLMResponse(
            content="[]", raw_response={}, structured_data=[]
        )
        prov.complete_structured.return_value = expected

        router = FallbackRouter(
            routes=[ModelRoute("openrouter", "x/y")],
            registry=_registry_with(prov),
            temperature=0.4,
            max_tokens=250,
        )
        schema = events_array_schema()
        resp = router.complete_structured("sys", "usr", schema, EVENTS_SCHEMA_NAME)

        assert resp is expected
        prov.complete_structured.assert_called_once_with(
            "sys", "usr",
            model="x/y", temperature=0.4, max_tokens=250,
            schema=schema, schema_name=EVENTS_SCHEMA_NAME,
        )

    def test_unsupported_propagates_without_fallback(self):
        """LLMUnsupportedStructuredError skips route fallback entirely."""
        prov1 = MagicMock()
        prov1.name = "p1"
        prov1.complete_structured.side_effect = LLMUnsupportedStructuredError("nope")
        prov2 = MagicMock()
        prov2.name = "p2"

        router = FallbackRouter(
            routes=[ModelRoute("p1", "a"), ModelRoute("p2", "b")],
            registry=_registry_with(prov1, prov2),
            temperature=0.7,
            max_tokens=100,
        )
        with pytest.raises(LLMUnsupportedStructuredError):
            router.complete_structured("sys", "usr", events_array_schema(), EVENTS_SCHEMA_NAME)

        prov2.complete_structured.assert_not_called()

    def test_llm_error_falls_through_to_next_route(self):
        """Generic LLMError on the primary route falls back like complete()."""
        prov1 = MagicMock()
        prov1.name = "p1"
        prov1.complete_structured.side_effect = LLMError("boom")
        prov2 = MagicMock()
        prov2.name = "p2"
        prov2.complete_structured.return_value = LLMResponse(
            content="[]", raw_response={}, structured_data=[]
        )

        router = FallbackRouter(
            routes=[ModelRoute("p1", "a"), ModelRoute("p2", "b")],
            registry=_registry_with(prov1, prov2),
            temperature=0.7,
            max_tokens=100,
        )
        resp = router.complete_structured(
            "sys", "usr", events_array_schema(), EVENTS_SCHEMA_NAME
        )
        assert resp.structured_data == []


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------


def _write_minimal_scenario(tmp_path, llm_block: dict):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    (scenario_dir / "metrics.md").write_text(
        "## metric1\n**ID:** metric1\n**Min:** 0\n**Max:** 100\n"
        "**Value:** 50\n**Unit:** points\n"
    )
    (scenario_dir / "events.md").write_text("")
    (scenario_dir / "metric-rules.md").write_text("")
    bg_dir = scenario_dir / "background"
    bg_dir.mkdir()
    (bg_dir / "context.md").write_text("Context")
    actors_dir = bg_dir / "actors"
    actors_dir.mkdir()
    (actors_dir / "actor1.md").write_text(
        "# Actor 1\n## Short description\nShort\n## Long description\nLong"
    )
    config = {
        "name": "Structured Test",
        "description": "Test",
        "start_date": "2026-01",
        "time_scale": "6 months",
        "max_turns": 2,
        "actors": ["actor1"],
        "llm": llm_block,
    }
    (scenario_dir / "scenario.yaml").write_text(yaml.dump(config))
    return scenario_dir


class TestStructuredOutputsConfig:
    def test_default_is_auto(self, tmp_path):
        scenario = load_scenario(str(_write_minimal_scenario(tmp_path, {})))
        assert scenario.config.llm.structured_outputs == "auto"

    def test_explicit_auto(self, tmp_path):
        scenario = load_scenario(
            str(_write_minimal_scenario(tmp_path, {"structured_outputs": "auto"}))
        )
        assert scenario.config.llm.structured_outputs == "auto"

    def test_yaml_true_normalized(self, tmp_path):
        """YAML boolean true is normalized to the canonical 'true' string."""
        scenario = load_scenario(
            str(_write_minimal_scenario(tmp_path, {"structured_outputs": True}))
        )
        assert scenario.config.llm.structured_outputs == "true"

    def test_yaml_false_normalized(self, tmp_path):
        scenario = load_scenario(
            str(_write_minimal_scenario(tmp_path, {"structured_outputs": False}))
        )
        assert scenario.config.llm.structured_outputs == "false"

    def test_invalid_value_raises(self, tmp_path):
        with pytest.raises(ValueError, match="structured_outputs"):
            load_scenario(
                str(_write_minimal_scenario(tmp_path, {"structured_outputs": "maybe"}))
            )

    def test_llm_config_validates_directly(self):
        with pytest.raises(ValueError, match="structured_outputs"):
            LLMConfig(structured_outputs="sometimes")


# ---------------------------------------------------------------------------
# Orchestrator behavior
# ---------------------------------------------------------------------------


@pytest.fixture
def test_scenario():
    return load_scenario("scenarios/sweden-ai-2030")


def _recording_output_manager(scenario, tmp_path) -> OutputManager:
    om = OutputManager(scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    return om


def _structured_client(data=None) -> MockLLMClient:
    return MockLLMClient(
        {"list of potential external events looks like this": "unused"},
        structured_data=EVENTS_PAYLOAD if data is None else data,
        supports_structured=True,
    )


def _legacy_client(payload: str) -> MockLLMClient:
    return MockLLMClient(
        {"list of potential external events looks like this": payload}
    )


class TestOrchestratorStructuredEvents:
    def test_auto_uses_structured_when_supported(self, test_scenario, tmp_path):
        """In auto mode a structured-capable client skips the text parse path."""
        test_scenario.config.random_seed = 42
        client = _structured_client()
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        triggered = orchestrator._run_events_step(turn=1)

        assert {e["id"] for e in triggered} == {"ai_breakthrough"}
        assert len(client.structured_calls) == 1
        assert client.calls == []  # no legacy complete() call

        _, _, schema, schema_name = client.structured_calls[0]
        assert schema_name == EVENTS_SCHEMA_NAME
        assert schema == events_array_schema()

    def test_auto_falls_back_and_remembers_unsupported(self, test_scenario, tmp_path):
        """Unsupported structured output falls back silently and is not retried."""
        payload = json.dumps(EVENTS_PAYLOAD)
        test_scenario.config.random_seed = 42
        client = _legacy_client(payload)  # supports_structured=False
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        triggered = orchestrator._run_events_step(turn=1)
        assert {e["id"] for e in triggered} == {"ai_breakthrough"}
        assert len(client.structured_calls) == 1
        assert len(client.calls) == 1
        assert orchestrator._structured_events_unsupported is True

        # Second turn must not retry the structured path.
        orchestrator._run_events_step(turn=2)
        assert len(client.structured_calls) == 1
        assert len(client.calls) == 2

    def test_true_mode_hard_errors_when_unsupported(self, test_scenario, tmp_path):
        """structured_outputs=true raises when the model lacks support."""
        test_scenario.config.random_seed = 42
        test_scenario.config.llm.structured_outputs = "true"
        client = _legacy_client("[]")
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        with pytest.raises(LLMError, match="structured_outputs"):
            orchestrator._run_events_step(turn=1)
        assert client.calls == []  # never reached the legacy path

    def test_false_mode_never_attempts_structured(self, test_scenario, tmp_path):
        """structured_outputs=false uses only the legacy path."""
        payload = json.dumps(EVENTS_PAYLOAD)
        test_scenario.config.random_seed = 42
        test_scenario.config.llm.structured_outputs = "false"
        client = MockLLMClient(
            {"list of potential external events looks like this": payload},
            structured_data=EVENTS_PAYLOAD,
            supports_structured=True,
        )
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        triggered = orchestrator._run_events_step(turn=1)
        assert {e["id"] for e in triggered} == {"ai_breakthrough"}
        assert client.structured_calls == []
        assert len(client.calls) == 1

    def test_auto_non_list_structured_falls_back(self, test_scenario, tmp_path):
        """Defensive: a non-array structured payload falls through to legacy parsing."""
        payload = json.dumps(EVENTS_PAYLOAD)
        test_scenario.config.random_seed = 42
        client = MockLLMClient(
            {"list of potential external events looks like this": payload},
            structured_data={"not": "a list"},
            supports_structured=True,
        )
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        triggered = orchestrator._run_events_step(turn=1)
        assert {e["id"] for e in triggered} == {"ai_breakthrough"}
        assert len(client.structured_calls) == 1
        assert len(client.calls) == 1

    def test_structured_calls_are_recorded_in_llm_io(self, test_scenario, tmp_path):
        """The recording wrapper persists transcripts for structured calls too."""
        test_scenario.config.random_seed = 42
        test_scenario.config.logging.llm_io = True
        client = _structured_client()
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        orchestrator._run_events_step(turn=1)

        io_dir = om.run_dir / "turn-01" / "llm-io"
        assert io_dir.exists()
        files = sorted(io_dir.iterdir())
        assert len(files) == 1
        assert files[0].name == "01-events.md"
        content = files[0].read_text(encoding="utf-8")
        assert "ai_breakthrough" in content

    def test_parse_failure_marker_recorded(self, test_scenario, tmp_path):
        """A legacy parse failure leaves a visible marker in the evaluations artifact."""
        test_scenario.config.random_seed = 42
        test_scenario.config.llm.structured_outputs = "false"
        client = MockLLMClient(
            {
                "list of potential external events looks like this": "garbage not json",
                "Rewrite it to be a valid JSON array": "still not json",
            }
        )
        om = _recording_output_manager(test_scenario, tmp_path)
        orchestrator = Orchestrator(test_scenario, client, output_manager=om)

        triggered = orchestrator._run_events_step(turn=1)
        assert triggered == []

        evaluations = json.loads(
            (om.run_dir / "turn-01" / "1-event-evaluations.json").read_text(
                encoding="utf-8"
            )
        )
        assert evaluations == [{"parse_failure": True, "triggered": False}]

    def test_parse_failure_marker_passes_integrity_check(self, tmp_path):
        """The integrity validator accepts a parse-failure marker entry."""
        from scenario_lab.regression import check_run_integrity

        run_dir = tmp_path / "runs" / "parse-failure"
        turn_dir = run_dir / "turn-01"
        turn_dir.mkdir(parents=True)
        (run_dir / "config.json").write_text(
            json.dumps({"name": "Test Scenario", "random_seed": 1}), encoding="utf-8"
        )
        metrics = {"gdp": 100}
        (run_dir / "summary.json").write_text(
            json.dumps(
                {
                    "scenario": "Test Scenario",
                    "status": "completed",
                    "total_turns": 1,
                    "final_metrics": metrics,
                    "history": [{"turn": 1, "metrics": metrics}],
                    "occurred_events": [],
                }
            ),
            encoding="utf-8",
        )
        (turn_dir / "1-events.json").write_text(json.dumps([]), encoding="utf-8")
        (turn_dir / "1-event-evaluations.json").write_text(
            json.dumps([{"parse_failure": True, "triggered": False}]),
            encoding="utf-8",
        )
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir()
        (actors_dir / "actor.md").write_text("output", encoding="utf-8")
        (turn_dir / "3-metric-rules.md").write_text(
            "# Metric Rules v1\n\nRules", encoding="utf-8"
        )
        (turn_dir / "4-metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
        (turn_dir / "4-world-state.md").write_text("narrative", encoding="utf-8")
        (turn_dir / "5-notepad.md").write_text("notes", encoding="utf-8")

        report = check_run_integrity(run_dir)
        assert report["is_valid"] is True


# ---------------------------------------------------------------------------
# Schema shapes
# ---------------------------------------------------------------------------


class TestEventSchemas:
    def test_array_schema_matches_prompt_contract(self):
        """The schema mirrors the prompt: objects with id and probability only."""
        schema = events_array_schema()
        assert schema["type"] == "array"
        item = schema["items"]
        assert set(item["properties"].keys()) == {"id", "probability"}
        assert item["required"] == ["id", "probability"]
        assert item["additionalProperties"] is False
        assert item["properties"]["probability"]["minimum"] == 0
        assert item["properties"]["probability"]["maximum"] == 1

    def test_object_schema_wraps_array(self):
        schema = events_object_schema()
        assert schema["type"] == "object"
        assert schema["properties"]["events"] == events_array_schema()
        assert schema["required"] == ["events"]
