"""Integration tests for Orchestrator."""

import pytest
from threading import Barrier
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient, LLMResponse
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.models import Scenario, ScenarioConfig, Metrics, Metric, Actor, WorldState

@pytest.fixture
def test_scenario() -> Scenario:
    """Load the Sweden AI 2030 scenario for testing."""
    return load_scenario("scenarios/sweden-ai-2030")

@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Create a mock LLM client with predefined responses."""
    mock_responses = {
        "list of potential external events looks like this": '[{"id": "ai_breakthrough", "probability": 0.15}]',
        "which actions you want to take during the turn": """## Goals

* Increase AI adoption in Sweden
* Ensure workforce transition

## Actions

The government launches a comprehensive AI support program for small and medium-sized enterprises.""",
        "Respond with an updated list of Metric Rules": """1. ai_capability increases by 1 point per 6 months
2. If unemployment > 10, public_sentiment_to_ai decreases by 1
3. If ai_adoption_sweden increases by more than 5 points, unemployment increases by 1""",
        "A JSON object describing all metrics": """## Metrics

```json
{"ai_capability": 6, "ai_adoption_sweden": 48, "unemployment": 7, "public_sentiment_to_ai": 1}
```

## Narrative

Sweden undergoes a period of intense AI adoption following the government's support program. Small and medium-sized enterprises begin implementing AI solutions, driving up adoption rates. At the same time, early signs of concern appear in the labor market as certain routine jobs are automated.

## Notepad

The government's AI support program was launched during this turn. The program is expected to continue for at least 2 turns.""",
        "CURRENT NARRATIVE": "Summarized history: Sweden saw AI adoption rise.",
        "Constitutional Referee": "APPROVED",
    }
    return MockLLMClient(mock_responses)

def test_orchestrator_run_turn(test_scenario, mock_llm_client):
    """Test running a full turn with the orchestrator."""
    orchestrator = Orchestrator(test_scenario, mock_llm_client)
    
    # Run turn 1
    result = orchestrator.run_turn(1)
    
    # Verify results
    assert result.turn == 1
    assert len(result.triggered_events) >= 0
    assert len(result.actor_outputs) == len(test_scenario.actors)
    
    # Check metrics update
    assert result.metrics["ai_capability"] == 6
    assert result.metrics["ai_adoption_sweden"] == 48
    
    # Check narrative
    assert "Sweden undergoes a period of intense AI adoption" in result.narrative
    
    # Check summary update (mocked response)
    assert orchestrator.scenario.world_state.historical_summary == "Summarized history: Sweden saw AI adoption rise."


def test_actors_step_runs_in_parallel():
    """Actor step should execute prompts concurrently when multiple actors exist."""
    scenario = Scenario(
        config=ScenarioConfig(
            name="Parallel Actor Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=1,
            actor_ids=["actor1", "actor2"],
        ),
        metrics=Metrics(
            metrics={
                "m1": Metric(
                    id="m1",
                    description="Metric",
                    value=0,
                    min_value=0,
                    max_value=100,
                    unit="",
                )
            }
        ),
        events=[],
        actors={
            "actor1": Actor(
                id="actor1",
                name="Actor 1",
                short_description="Short",
                long_description="Long",
                initial_goals=[],
            ),
            "actor2": Actor(
                id="actor2",
                name="Actor 2",
                short_description="Short",
                long_description="Long",
                initial_goals=[],
            ),
        },
        metric_rules="Rules",
        world_state=WorldState(narrative="World", turn=0, time_period="Start: 2026-01"),
        context="Context",
    )

    class BarrierClient:
        """Client that requires two concurrent calls to proceed."""

        def __init__(self):
            self.barrier = Barrier(2)

        def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            # This will raise BrokenBarrierError if calls are sequential.
            self.barrier.wait(timeout=1.0)
            return LLMResponse(
                content="## Goals\n- Goal\n\n## Actions\n- Action",
                raw_response={"model": "mock/model"},
            )

        def close(self):
            pass

    barrier_client = BarrierClient()
    clients = {
        "events": barrier_client,
        "actors": {"actor1": barrier_client, "actor2": barrier_client},
        "rules": barrier_client,
        "metrics": barrier_client,
        "summary": barrier_client,
    }

    orchestrator = Orchestrator(scenario, llm_client=clients)
    outputs = orchestrator._run_actors_step(turn=1, triggered_events=[])

    assert set(outputs.keys()) == {"actor1", "actor2"}
    assert scenario.actors["actor1"].last_actions
    assert scenario.actors["actor2"].last_actions


def test_rules_step_retries_on_length_truncation(test_scenario):
    """Rules step should retry with concise constraints when first response is truncated."""

    class SequentialRulesClient:
        def __init__(self):
            self.calls = 0
            self.models = ["mock/model"]

        def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            self.calls += 1
            if self.calls == 1:
                # Truncated output: has header/changelog but no Rules section.
                return LLMResponse(
                    content="# Metric Rules v2 (Turn 2)\n\n## Changelog from v1\n\n- **Added:** `x`",
                    raw_response={"choices": [{"finish_reason": "length"}], "model": "mock/model"},
                )
            return LLMResponse(
                content=(
                    "# Metric Rules v2 (Turn 2)\n\n"
                    "## Changelog from v1\n\n"
                    "- **Added:** `x`\n"
                    "  - **Rule:** rule text\n"
                    "  - **Motivation:** concise motivation.\n"
                    "  - **Expected impact:** concise impact.\n\n"
                    "## Rules\n\n"
                    "1. ai_capability increases by 10% per turn.\n"
                    "2. If unemployment > 10 then public_sentiment_to_ai decreases by 1.\n"
                ),
                raw_response={"choices": [{"finish_reason": "stop"}], "model": "mock/model"},
            )

        def close(self):
            pass

    rules_client = SequentialRulesClient()
    clients = {
        "events": rules_client,
        "actors": {},
        "rules": rules_client,
        "metrics": rules_client,
        "summary": rules_client,
        "referee": rules_client,
    }

    orchestrator = Orchestrator(test_scenario, llm_client=clients)
    actor_outputs = {actor_id: "No major action." for actor_id in test_scenario.actors}

    output = orchestrator._run_rules_step(turn=2, actor_outputs=actor_outputs, triggered_events=[])

    assert rules_client.calls == 2
    assert "## Rules" in output


def test_constitutional_referee_requests_correction_before_approval(test_scenario):
    """A referee violation should trigger one correction pass before final approval."""

    class SequenceClient:
        def __init__(self, contents: list[str]):
            self.contents = contents
            self.calls = 0
            self.models = ["mock/model"]

        def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            if self.calls >= len(self.contents):
                raise AssertionError("Client received more calls than expected")
            content = self.contents[self.calls]
            self.calls += 1
            return LLMResponse(
                content=content,
                raw_response={"model": "mock/model"},
            )

        def close(self):
            pass

    class MetadataRecorder:
        def __init__(self):
            self.calls = []

        def save_constitutional_metadata(self, turn: int, metadata: dict):
            self.calls.append((turn, metadata))

    referee_client = SequenceClient(
        [
            "VIOLATIONS:\n- Budget increase is too large for one turn.\n- Hiring ramp exceeds capacity.",
            "APPROVED",
        ]
    )
    correction_client = SequenceClient(
        [
            """## Metrics

```json
{"ai_capability": 3, "ai_adoption_sweden": 10, "unemployment": 9, "public_sentiment_to_ai": 3}
```

## Narrative

The rollout is phased in over time, so unemployment rises more gradually while the broader policy remains in place."""
        ]
    )
    metadata_recorder = MetadataRecorder()
    clients = {
        "events": correction_client,
        "actors": {},
        "rules": correction_client,
        "metrics": correction_client,
        "summary": correction_client,
        "referee": referee_client,
    }

    orchestrator = Orchestrator(
        test_scenario,
        llm_client=clients,
        output_manager=metadata_recorder,
    )

    proposed_metrics = {metric_id: metric.value for metric_id, metric in test_scenario.metrics.metrics.items()}
    proposed_metrics["unemployment"] = 20
    narrative = "Unemployment spikes sharply after rapid automation."

    final_metrics, final_narrative = orchestrator._run_constitutional_referee_step(
        turn=1,
        proposed_metrics=proposed_metrics,
        narrative=narrative,
    )

    assert referee_client.calls == 2
    assert correction_client.calls == 1
    assert final_metrics["unemployment"] == 9
    assert final_metrics["ai_capability"] == 3
    assert "phased in over time" in final_narrative
    assert len(metadata_recorder.calls) == 1

    saved_turn, metadata = metadata_recorder.calls[0]
    assert saved_turn == 1
    assert metadata["status"] == "approved"
    assert metadata["iterations"] == 2
    assert metadata["final_action"] == "corrected_and_approved"
    assert metadata["violations_found"] == [
        {
            "iteration": 1,
            "violations": "- Budget increase is too large for one turn.\n- Hiring ramp exceeds capacity.",
        }
    ]


def test_constitutional_referee_records_parse_error_metadata(test_scenario):
    """Unexpected referee output should be persisted as parse_error metadata."""

    class RefereeClient:
        def __init__(self, content: str):
            self.content = content
            self.calls = 0
            self.models = ["mock/model"]

        def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            self.calls += 1
            return LLMResponse(
                content=self.content,
                raw_response={"model": "mock/model"},
            )

        def close(self):
            pass

    class MetadataRecorder:
        def __init__(self):
            self.calls = []

        def save_constitutional_metadata(self, turn: int, metadata: dict):
            self.calls.append((turn, metadata))

    malformed_response = "Needs review before approval."
    referee_client = RefereeClient(malformed_response)
    metadata_recorder = MetadataRecorder()
    clients = {
        "events": referee_client,
        "actors": {},
        "rules": referee_client,
        "metrics": referee_client,
        "summary": referee_client,
        "referee": referee_client,
    }

    orchestrator = Orchestrator(
        test_scenario,
        llm_client=clients,
        output_manager=metadata_recorder,
    )

    proposed_metrics = {metric_id: metric.value for metric_id, metric in test_scenario.metrics.metrics.items()}
    narrative = "The turn completes with moderate economic changes."

    final_metrics, final_narrative = orchestrator._run_constitutional_referee_step(
        turn=2,
        proposed_metrics=proposed_metrics,
        narrative=narrative,
    )

    assert referee_client.calls == 1
    assert final_metrics == proposed_metrics
    assert final_narrative == narrative
    assert len(metadata_recorder.calls) == 1

    saved_turn, metadata = metadata_recorder.calls[0]
    assert saved_turn == 2
    assert metadata["status"] == "parse_error"
    assert metadata["iterations"] == 1
    assert metadata["violations_found"] == []
    assert metadata["error"] == "Unexpected response format"
    assert metadata["response_preview"] == malformed_response
