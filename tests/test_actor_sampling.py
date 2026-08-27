"""Tests for sampling an actor's choice under identical conditions."""

import json
from pathlib import Path

import pytest

from scenario_lab.actor_sampling import (
    ActorSample,
    is_run_dir,
    load_opening_state,
    SamplingResult,
    load_triggered_events,
    sample_actor,
    write_samples,
)
from tests.test_resume import (  # noqa: F401 - fixtures
    create_complete_turn,
    scenario_dir,
    temp_run_dir,
)


class FakeResponse:
    """Minimal stand-in for LLMResponse with no usage reported."""

    def __init__(self, content: str):
        self.content = content
        self.raw_response = {}
        self.structured_data = None

    def get_usage(self):
        return None


class CountingClient:
    """Records every prompt it is given and returns a distinct response each time."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str):
        self.calls.append((system_prompt, user_prompt))
        return FakeResponse(f"choice {len(self.calls)}")


@pytest.fixture
def sampled_run(temp_run_dir, scenario_dir):  # noqa: F811
    """A run with two complete turns, the second carrying an event."""
    create_complete_turn(temp_run_dir, 1)
    create_complete_turn(temp_run_dir, 2)
    (temp_run_dir / "turn-02" / "1-events.json").write_text(
        json.dumps([{"id": "test_event", "description": "Something happened"}])
    )
    return temp_run_dir


def _patch_client(monkeypatch, client):
    """Route every actor call through the given client."""
    monkeypatch.setattr(
        "scenario_lab.orchestrator.Orchestrator.client_for_actor",
        lambda self, actor_id: client,
    )


class TestConditionsAreIdentical:
    def test_every_sample_gets_the_same_prompt(self, sampled_run, monkeypatch):
        client = CountingClient()
        _patch_client(monkeypatch, client)

        result = sample_actor(sampled_run, turn=2, samples=5)

        assert len(client.calls) == 5
        assert len(set(client.calls)) == 1, "prompts differed between samples"
        assert client.calls[0] == (result.system_prompt, result.user_prompt)

    def test_samples_are_distinct_and_ordered(self, sampled_run, monkeypatch):
        _patch_client(monkeypatch, CountingClient())

        result = sample_actor(sampled_run, turn=2, samples=4)

        assert [s.index for s in result.samples] == [1, 2, 3, 4]
        assert len({s.content for s in result.samples}) == 4

    def test_turn_events_reach_the_prompt(self, sampled_run, monkeypatch):
        _patch_client(monkeypatch, CountingClient())

        result = sample_actor(sampled_run, turn=2, samples=1)

        assert [e["id"] for e in result.triggered_events] == ["test_event"]
        assert "Something happened" in result.user_prompt

    def test_events_can_be_borrowed_from_another_run(
        self, sampled_run, tmp_path, monkeypatch
    ):
        """--events-from composes a situation instead of accepting the dice."""
        other = sampled_run.parent / "run-20251205-130000"
        other.mkdir()
        (other / "turn-02").mkdir()
        (other / "turn-02" / "1-events.json").write_text(
            json.dumps([{"id": "borrowed", "description": "Borrowed event"}])
        )
        _patch_client(monkeypatch, CountingClient())

        result = sample_actor(sampled_run, turn=2, samples=1, events_from=other)

        assert [e["id"] for e in result.triggered_events] == ["borrowed"]
        assert "Borrowed event" in result.user_prompt


class TestValidation:
    def test_later_turns_need_a_run(self, scenario_dir):  # noqa: F811
        with pytest.raises(ValueError, match="needs a run directory"):
            sample_actor(scenario_dir, turn=2, samples=1)

    def test_initial_state_is_rejected_after_turn_one(self, sampled_run, tmp_path):
        with pytest.raises(ValueError, match="turn 1 only"):
            sample_actor(
                sampled_run, turn=2, samples=1, initial_state=tmp_path / "draw.json"
            )

    def test_unsimulated_turn_is_rejected(self, sampled_run):
        with pytest.raises(ValueError, match="no recorded events"):
            sample_actor(sampled_run, turn=3, samples=2)

    def test_zero_samples_is_rejected(self, sampled_run):
        with pytest.raises(ValueError, match="at least 1"):
            sample_actor(sampled_run, turn=2, samples=0)

    def test_unknown_actor_is_rejected(self, sampled_run, monkeypatch):
        _patch_client(monkeypatch, CountingClient())
        with pytest.raises(ValueError, match="Unknown actor"):
            sample_actor(sampled_run, turn=2, samples=1, actor_id="nobody")

    def test_missing_events_file_names_the_turn(self, sampled_run):
        with pytest.raises(ValueError, match="Turn 9"):
            load_triggered_events(sampled_run, 9)


class TestPersistence:
    def test_prompt_and_samples_are_written(self, tmp_path):
        result = SamplingResult(
            actor_id="actor1",
            turn=2,
            system_prompt="SYSTEM",
            user_prompt="USER",
            triggered_events=[{"id": "test_event"}],
            samples=[
                ActorSample(index=1, content="first", tokens=10, cost_usd=0.001),
                ActorSample(index=2, content="second", tokens=20, cost_usd=0.002),
            ],
            model="openrouter:test/model",
            temperature=0.7,
        )
        out = tmp_path / "actor-samples"

        write_samples(result, out)

        assert (out / "prompt-system.md").read_text() == "SYSTEM"
        assert (out / "prompt-user.md").read_text() == "USER"
        assert (out / "sample-01.md").read_text() == "first"
        assert (out / "sample-02.md").read_text() == "second"

        index = json.loads((out / "index.json").read_text())
        assert index["actor"] == "actor1"
        assert index["turn"] == 2
        assert index["triggered_events"] == ["test_event"]
        assert index["total_tokens"] == 30
        assert index["total_cost_usd"] == pytest.approx(0.003)
        assert len(index["samples"]) == 2

    def test_prompt_hash_tracks_the_prompt(self):
        def build(user: str) -> SamplingResult:
            return SamplingResult(
                actor_id="a",
                turn=2,
                system_prompt="SYSTEM",
                user_prompt=user,
                triggered_events=[],
                samples=[],
                model="m",
                temperature=0.7,
            )

        assert build("USER").prompt_hash == build("USER").prompt_hash
        assert build("USER").prompt_hash != build("OTHER").prompt_hash

    def test_on_sample_fires_for_each_sample(self, sampled_run, monkeypatch):
        _patch_client(monkeypatch, CountingClient())
        seen = []

        sample_actor(sampled_run, turn=2, samples=3, on_sample=seen.append)

        assert len(seen) == 3
        assert {s.index for s in seen} == {1, 2, 3}


class TestOpeningMove:
    """Turn 1's actor acts on the scenario's initial state, not a recorded turn."""

    def test_sampled_from_a_scenario_before_any_run(self, scenario_dir, monkeypatch):  # noqa: F811
        client = CountingClient()
        _patch_client(monkeypatch, client)

        result = sample_actor(scenario_dir, turn=1, samples=3)

        assert len(client.calls) == 3
        assert len(set(client.calls)) == 1
        assert result.turn == 1
        assert result.triggered_events == []
        assert "Initial world state." in result.user_prompt

    def test_sampled_from_a_run_reuses_its_recorded_events(
        self, sampled_run, monkeypatch
    ):
        _patch_client(monkeypatch, CountingClient())
        (sampled_run / "turn-01" / "1-events.json").write_text(
            json.dumps([{"id": "opening_event", "description": "Opening shock"}])
        )

        result = sample_actor(sampled_run, turn=1, samples=1)

        assert [e["id"] for e in result.triggered_events] == ["opening_event"]
        assert "Opening shock" in result.user_prompt

    def test_opening_state_ignores_later_turns(self, sampled_run, monkeypatch):
        """Turn 1 must not inherit state that turn 1's actor could not have seen."""
        _patch_client(monkeypatch, CountingClient())
        (sampled_run / "turn-01" / "4-world-state.md").write_text("LATER NARRATIVE")

        result = sample_actor(sampled_run, turn=1, samples=1)

        assert "LATER NARRATIVE" not in result.user_prompt
        assert "Initial world state." in result.user_prompt

    def test_recorded_starting_draw_is_applied(self, sampled_run, monkeypatch):
        """A run's initial_state draw is part of the world its turn 1 began in."""
        _patch_client(monkeypatch, CountingClient())
        config = json.loads((sampled_run / "config.json").read_text())
        config["initial_state"] = {
            "metrics": {"test_metric": 73},
            "context": "",
            "notes": "",
            "source": "draw-01.json",
        }
        (sampled_run / "config.json").write_text(json.dumps(config, indent=2))

        scenario = load_opening_state(sampled_run)

        assert scenario.metrics.metrics["test_metric"].value == 73

    def test_events_can_be_borrowed_for_turn_one(
        self, scenario_dir, sampled_run, monkeypatch  # noqa: F811
    ):
        _patch_client(monkeypatch, CountingClient())
        (sampled_run / "turn-01" / "1-events.json").write_text(
            json.dumps([{"id": "borrowed_opening", "description": "Borrowed opening"}])
        )

        result = sample_actor(scenario_dir, turn=1, samples=1, events_from=sampled_run)

        assert [e["id"] for e in result.triggered_events] == ["borrowed_opening"]

    def test_borrowed_events_must_exist(self, scenario_dir, sampled_run):  # noqa: F811
        with pytest.raises(ValueError, match="no recorded events"):
            sample_actor(scenario_dir, turn=1, samples=1, events_from=sampled_run.parent)


class TestRunDirDetection:
    def test_run_directory_is_recognised(self, sampled_run):
        assert is_run_dir(sampled_run) is True

    def test_scenario_directory_is_not_a_run(self, scenario_dir):  # noqa: F811
        assert is_run_dir(scenario_dir) is False
