"""Tests for emergent events and multi-sample probability elicitation."""

import json

import pytest

from scenario_lab.llm import LLMResponse, MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager
from scenario_lab.prompts import PromptBuilder
from scenario_lab.schemas import events_array_schema
from scenario_lab.validator import validate_llm_config


@pytest.fixture
def test_scenario():
    """Load the Sweden AI 2030 scenario for testing."""
    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.random_seed = 42
    return scenario


def _events_client(payload: str) -> MockLLMClient:
    return MockLLMClient(
        {"list of potential external events looks like this": payload}
    )


class SequenceClient:
    """Mock client returning queued responses in call order.

    Used for multi-sample tests where each events elicitation (and any
    format-fix retry) must yield a different response.
    """

    def __init__(self, contents: list[str]):
        self.contents = list(contents)
        self.calls: list[tuple[str, str]] = []
        self.models = ["mock/model"]
        self.provider = "mock"

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.calls.append((system_prompt, user_prompt))
        content = self.contents.pop(0)
        return LLMResponse(
            content=content,
            raw_response={
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "model": "mock/model",
            },
        )

    def close(self):
        pass


def _recording_output_manager(scenario, tmp_path) -> OutputManager:
    om = OutputManager(scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    return om


def _read_evaluations(om: OutputManager, turn: int = 1) -> list[dict]:
    path = om.run_dir / f"turn-{turn:02d}" / "1-event-evaluations.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Emergent events: config defaults and loading
# ---------------------------------------------------------------------------


def test_emergent_events_defaults(test_scenario):
    emergent = test_scenario.config.emergent_events
    assert emergent.enabled is False
    assert emergent.max_per_turn == 1
    assert emergent.max_probability == 0.35
    assert emergent.track_unfired is False
    assert emergent.window_turns == 3
    assert test_scenario.config.llm.probability_samples == 1


def test_config_parsing_from_yaml(tmp_path):
    from scenario_lab.loader import load_config

    yaml_path = tmp_path / "scenario.yaml"
    yaml_path.write_text(
        """
name: "Test"
description: "Test scenario"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 5
actors:
  - actor-a
llm:
  model: "openrouter:qwen/qwen3-235b-a22b-2507"
  probability_samples: 3
emergent_events:
  enabled: true
  max_per_turn: 2
  max_probability: 0.5
  track_unfired: true
  window_turns: 4
""",
        encoding="utf-8",
    )
    config = load_config(yaml_path)
    assert config.llm.probability_samples == 3
    assert config.emergent_events.enabled is True
    assert config.emergent_events.max_per_turn == 2
    assert config.emergent_events.max_probability == 0.5
    assert config.emergent_events.track_unfired is True
    assert config.emergent_events.window_turns == 4


def test_validator_rejects_bad_values(test_scenario):
    test_scenario.config.llm.probability_samples = 0
    test_scenario.config.emergent_events.max_per_turn = 0
    test_scenario.config.emergent_events.max_probability = 1.5
    test_scenario.config.emergent_events.track_unfired = "yes"
    test_scenario.config.emergent_events.window_turns = 0

    # probability_samples validation happens in LLMConfig.__post_init__ too,
    # but the validator must also catch values set after construction.
    errors, _ = validate_llm_config(test_scenario)
    assert any("probability_samples" in e for e in errors)
    assert any("max_per_turn" in e for e in errors)
    assert any("max_probability" in e for e in errors)
    assert any("track_unfired" in e for e in errors)
    assert any("window_turns" in e for e in errors)


def test_llm_config_rejects_bad_probability_samples():
    from scenario_lab.models import LLMConfig

    with pytest.raises(ValueError):
        LLMConfig(probability_samples=0)


# ---------------------------------------------------------------------------
# Emergent events: orchestrator behavior
# ---------------------------------------------------------------------------


def _emergent_payload(**overrides) -> str:
    entry = {
        "id": "emergent_solar_storm",
        "probability": 1.0,
        "emergent": True,
        "description": "A severe solar storm damages satellite infrastructure.",
    }
    entry.update(overrides)
    return json.dumps([entry])


def test_emergent_skipped_when_disabled(test_scenario, tmp_path):
    """With the feature off (default), emergent proposals are skipped."""
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_emergent_payload()), output_manager=om
    )

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered == []

    entry = _read_evaluations(om)[0]
    assert entry["skipped"] == "Emergent events are disabled for this scenario"
    assert entry["triggered"] is False


def test_emergent_triggers_when_enabled(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.max_probability = 1.0
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_emergent_payload()), output_manager=om
    )

    triggered = orchestrator._run_events_step(turn=1)
    assert len(triggered) == 1
    assert triggered[0]["id"] == "emergent_solar_storm"
    assert triggered[0]["description"].startswith("A severe solar storm")

    entry = _read_evaluations(om)[0]
    assert entry["emergent"] is True
    assert entry["triggered"] is True
    assert "roll" in entry

    # Emergent events are recorded as occurred (one-off by definition).
    assert "emergent_solar_storm" in test_scenario.occurred_events


def test_emergent_probability_capped(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_emergent_payload(probability=0.9)), output_manager=om
    )

    orchestrator._run_events_step(turn=1)

    entry = _read_evaluations(om)[0]
    assert entry["probability"] == 0.35
    assert entry["probability_capped_from"] == 0.9


def test_emergent_max_per_turn_enforced(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    payload = json.dumps(
        [
            {"id": "emergent_a", "probability": 0.2, "emergent": True, "description": "First."},
            {"id": "emergent_b", "probability": 0.2, "emergent": True, "description": "Second."},
        ]
    )
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    orchestrator._run_events_step(turn=1)

    by_id = {e["id"]: e for e in _read_evaluations(om)}
    assert "roll" in by_id["emergent_a"]
    assert by_id["emergent_b"]["skipped"].startswith("Exceeds emergent_events.max_per_turn")


def test_emergent_requires_description(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_emergent_payload(description="")), output_manager=om
    )

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered == []
    entry = _read_evaluations(om)[0]
    assert entry["skipped"] == "Emergent event missing description"


def test_emergent_id_normalized(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.max_probability = 1.0
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario,
        _events_client(_emergent_payload(id="solar_storm", probability=1.0)),
        output_manager=om,
    )

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered[0]["id"] == "emergent_solar_storm"

    entry = _read_evaluations(om)[0]
    assert entry["id"] == "emergent_solar_storm"
    assert entry["id_normalized_from"] == "solar_storm"


def test_listed_events_unaffected_and_filler_stripped(test_scenario, tmp_path):
    """Listed events still work when emergent is on; contract filler removed."""
    test_scenario.config.emergent_events.enabled = True
    payload = json.dumps(
        [{"id": "ai_breakthrough", "probability": 1.0, "emergent": False, "description": ""}]
    )
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered == [{"id": "ai_breakthrough", "probability": 1.0}]


# ---------------------------------------------------------------------------
# Emergent events: prompts and schema
# ---------------------------------------------------------------------------


def test_events_prompt_mentions_emergent_only_when_enabled(test_scenario):
    # Use the default events template (the scenario ships a custom override).
    test_scenario.custom_user_prompts.pop("events", None)
    builder = PromptBuilder(test_scenario)
    _, user_disabled = builder.build_events_prompt(turn=1)
    assert "emergent" not in user_disabled.lower()

    test_scenario.config.emergent_events.enabled = True
    builder = PromptBuilder(test_scenario)
    _, user_enabled = builder.build_events_prompt(turn=1)
    assert "emergent_" in user_enabled
    assert '"emergent": true' in user_enabled


def test_triggered_emergent_event_reaches_actor_prompt(test_scenario):
    builder = PromptBuilder(test_scenario)
    triggered = [
        {"id": "ai_breakthrough", "probability": 1.0},
        {
            "id": "emergent_solar_storm",
            "probability": 0.3,
            "emergent": True,
            "description": "A severe solar storm damages satellite infrastructure.",
        },
    ]
    actor_id = next(iter(test_scenario.actors))
    _, user = builder.build_actor_prompt(actor_id, turn=2, triggered_events=triggered)
    assert "emergent_solar_storm (emergent event)" in user
    assert "solar storm damages satellite infrastructure" in user


def test_structured_schema_extended_when_emergent_enabled(test_scenario):
    plain = events_array_schema()
    assert plain["items"]["required"] == ["id", "probability"]

    extended = events_array_schema(emergent=True)
    assert set(extended["items"]["required"]) == {"id", "probability", "emergent", "description"}

    # Orchestrator threads the flag through to complete_structured.
    test_scenario.config.emergent_events.enabled = True
    client = MockLLMClient(
        {"list of potential external events looks like this": "[]"},
        structured_data=[],
        supports_structured=True,
    )
    orchestrator = Orchestrator(test_scenario, client)
    orchestrator._run_events_step(turn=1)
    assert client.structured_calls, "structured path was not used"
    _, _, schema, _ = client.structured_calls[0]
    assert "emergent" in schema["items"]["properties"]


# ---------------------------------------------------------------------------
# Multi-sample probability elicitation
# ---------------------------------------------------------------------------


def test_single_sample_has_no_aggregation_fields(test_scenario, tmp_path):
    """Default probability_samples=1 keeps today's artifact shape exactly."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 1.0}])
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    orchestrator._run_events_step(turn=1)
    entry = _read_evaluations(om)[0]
    assert "probability_samples" not in entry
    assert "n_samples" not in entry


def test_multi_sample_probability_is_absent_as_zero_mean(test_scenario, tmp_path):
    test_scenario.config.llm.probability_samples = 3
    samples = [
        json.dumps(
            [
                {"id": "ai_breakthrough", "probability": 0.3},
                {"id": "strike", "probability": 0.6},
            ]
        ),
        json.dumps([{"id": "ai_breakthrough", "probability": 0.6}]),
        json.dumps([{"id": "ai_breakthrough", "probability": 0.9}]),
    ]
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, SequenceClient(samples), output_manager=om)

    orchestrator._run_events_step(turn=1)
    by_id = {e["id"]: e for e in _read_evaluations(om)}

    breakthrough = by_id["ai_breakthrough"]
    assert breakthrough["probability"] == pytest.approx(0.6)
    assert breakthrough["probability_samples"] == [0.3, 0.6, 0.9]
    assert breakthrough["samples_present"] == 3
    assert breakthrough["n_samples"] == 3

    strike = by_id["strike"]
    assert strike["probability"] == pytest.approx(0.2)
    assert strike["probability_samples"] == [0.6, 0.0, 0.0]
    assert strike["samples_present"] == 1


def test_multi_sample_excludes_failed_samples_from_denominator(test_scenario, tmp_path):
    test_scenario.config.llm.probability_samples = 3
    good = json.dumps([{"id": "ai_breakthrough", "probability": 0.4}])
    # Call order: sample1 ok, sample2 fails parse (then its format-fix retry
    # also fails), sample3 ok -> 2 valid samples.
    contents = [good, "not json", "still not json", good]
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, SequenceClient(contents), output_manager=om)

    orchestrator._run_events_step(turn=1)
    entry = _read_evaluations(om)[0]
    assert entry["n_samples"] == 2
    assert entry["probability"] == pytest.approx(0.4)
    assert entry["samples_present"] == 2


def test_multi_sample_all_failed_records_parse_failure(test_scenario, tmp_path):
    test_scenario.config.llm.probability_samples = 2
    contents = ["bad", "bad", "bad", "bad"]  # 2 samples x (parse + format-fix)
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, SequenceClient(contents), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered == []
    assert _read_evaluations(om) == [{"parse_failure": True, "triggered": False}]


def test_multi_sample_downweights_one_off_emergent(test_scenario, tmp_path):
    """An emergent proposal appearing in 1 of N samples gets its probability divided by N."""
    test_scenario.config.llm.probability_samples = 2
    test_scenario.config.emergent_events.enabled = True
    samples = [
        _emergent_payload(probability=0.3),
        json.dumps([]),
    ]
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, SequenceClient(samples), output_manager=om)

    orchestrator._run_events_step(turn=1)
    entry = _read_evaluations(om)[0]
    assert entry["emergent"] is True
    assert entry["probability"] == pytest.approx(0.15)
    assert entry["description"].startswith("A severe solar storm")


def test_estimator_scales_events_tokens_with_samples(test_scenario):
    from scenario_lab.estimator import CostEstimator

    single = CostEstimator(test_scenario)._estimate_events_tokens()
    test_scenario.config.llm.probability_samples = 3
    tripled = CostEstimator(test_scenario)._estimate_events_tokens()

    assert tripled == 3 * single


# ---------------------------------------------------------------------------
# Emerging developments: unfired emergent proposals carried forward
# ---------------------------------------------------------------------------


def _unfired_emergent_payload() -> str:
    """A proposal with probability 0.0 can never fire (roll < 0 is impossible)."""
    return _emergent_payload(probability=0.0)


def test_unfired_emergent_carried_as_emerging_development(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(_unfired_emergent_payload()), output_manager=om)

    orchestrator._run_events_step(turn=1)

    assert len(test_scenario.emerging_developments) == 1
    dev = test_scenario.emerging_developments[0]
    assert dev.id == "emergent_solar_storm"
    assert dev.first_turn == 1
    assert dev.last_turn == 1
    assert dev.appearances == 1
    assert dev.description.startswith("A severe solar storm")


def test_emerging_development_expires_after_three_appearances(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(_unfired_emergent_payload()), output_manager=om)

    orchestrator._run_events_step(turn=1)
    assert test_scenario.emerging_developments[0].appearances == 1

    orchestrator._run_events_step(turn=2)
    assert test_scenario.emerging_developments[0].appearances == 2

    # Third listing without firing closes the window.
    orchestrator._run_events_step(turn=3)
    assert test_scenario.emerging_developments == []


def test_fired_emergent_leaves_tracking(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    test_scenario.config.emergent_events.max_probability = 1.0
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(_emergent_payload()), output_manager=om)

    orchestrator._run_events_step(turn=1)

    assert "emergent_solar_storm" in test_scenario.occurred_events
    assert test_scenario.emerging_developments == []


def test_emergent_not_reproposed_fizzles(test_scenario, tmp_path):
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True

    class VanishingClient(SequenceClient):
        def complete(self, system_prompt, user_prompt):
            if self.contents:
                return super().complete(system_prompt, user_prompt)
            return LLMResponse(
                content="[]",
                raw_response={"usage": {}, "model": "mock/model"},
            )

    client = VanishingClient([_unfired_emergent_payload()])
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, client, output_manager=om)

    orchestrator._run_events_step(turn=1)
    assert len(test_scenario.emerging_developments) == 1

    orchestrator._run_events_step(turn=2)
    assert test_scenario.emerging_developments == []


def test_tracking_inert_when_emergent_disabled(test_scenario, tmp_path):
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_unfired_emergent_payload()), output_manager=om
    )

    orchestrator._run_events_step(turn=1)

    assert test_scenario.emerging_developments == []


def test_tracking_off_by_default_when_enabled(test_scenario, tmp_path):
    """Emergent events alone keep one-shot semantics; tracking is opt-in."""
    test_scenario.config.emergent_events.enabled = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, _events_client(_unfired_emergent_payload()), output_manager=om
    )

    orchestrator._run_events_step(turn=1)

    assert test_scenario.emerging_developments == []


# ---------------------------------------------------------------------------
# Emerging developments: prompt composition and persistence
# ---------------------------------------------------------------------------


def test_compose_notepad_appends_tracked_section_once(test_scenario):
    from scenario_lab.models import EmergingDevelopment
    from scenario_lab.prompts import PromptBuilder

    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    test_scenario.notepad = "GM note: keep an eye on the grid."
    test_scenario.emerging_developments = [
        EmergingDevelopment(
            id="emergent_solar_storm",
            description="A severe solar storm is trending.",
            first_turn=2,
            last_turn=3,
        )
    ]
    builder = PromptBuilder(test_scenario)

    first = builder._compose_notepad()
    assert "GM note: keep an eye on the grid." in first
    assert "## Emerging developments (tracked)" in first
    assert "`emergent_solar_storm`" in first
    assert "listed in 2 turn(s)" in first

    # A model that copies the tracked section into its own notepad must not
    # produce a duplicated section on the next composition.
    test_scenario.notepad = first
    second = builder._compose_notepad()
    assert second.count("## Emerging developments (tracked)") == 1


def test_update_summary_persists_emerging_developments(test_scenario, tmp_path):
    import json as json_mod

    from scenario_lab.models import EmergingDevelopment

    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    test_scenario.emerging_developments = [
        EmergingDevelopment(
            id="emergent_solar_storm",
            description="A severe solar storm is trending.",
            first_turn=1,
            last_turn=2,
        )
    ]
    om = _recording_output_manager(test_scenario, tmp_path)
    om.update_summary(current_turn=2, latest_metrics={"cap": 50})

    summary = json_mod.loads((om.run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["emerging_events"] == [
        {
            "id": "emergent_solar_storm",
            "description": "A severe solar storm is trending.",
            "first_turn": 1,
            "last_turn": 2,
        }
    ]


def test_events_template_mentions_carried_entries(test_scenario):
    """The re-listing instruction appears exactly when there are entries to carry."""
    from scenario_lab.models import EmergingDevelopment

    # Use the default events template (the scenario ships a custom override).
    test_scenario.custom_user_prompts.pop("events", None)
    test_scenario.config.emergent_events.enabled = True
    test_scenario.config.emergent_events.track_unfired = True
    builder = PromptBuilder(test_scenario)

    # Tracking on but nothing in flight: no instruction, no section reference.
    _, user_empty = builder.build_events_prompt(turn=3)
    assert "Emerging developments (tracked)" not in user_empty

    # Entries in flight: the instruction to re-list them at higher probability.
    test_scenario.emerging_developments = [
        EmergingDevelopment(
            id="emergent_solar_storm",
            description="A severe solar storm is trending.",
            first_turn=2,
            last_turn=2,
        )
    ]
    builder = PromptBuilder(test_scenario)
    _, user = builder.build_events_prompt(turn=3)
    assert "Emerging developments (tracked)" in user
    assert "higher" in user
