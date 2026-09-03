"""A metrics response that drops a metric must not pass silently.

`Metrics.update_from_dict` only touches the keys it is given, so a metric left
out of the JSON keeps its old value and the run completes clean. The turn then
reads as one in which the metric did not move, when in fact it was never
considered. These tests pin the catch: one repair attempt, an explicit record
of what was dropped, and no artefact missing a key.
"""

import json

import pytest

from scenario_lab.llm import MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager


METRICS_PROMPT_KEY = "A JSON object describing all metrics"
FIX_PROMPT_KEY = "did not match the required format"

INCOMPLETE = """## Metrics

```json
{"ai_capability": 8, "ai_adoption_sweden": 12, "unemployment": 9}
```

## Narrative

Adoption picked up and unemployment edged higher.

## Notepad

Support programme running.
"""

COMPLETE_FIX = """## Metrics

```json
{"ai_capability": 8, "ai_adoption_sweden": 12, "unemployment": 9, "public_sentiment_to_ai": 4}
```

## Narrative

Adoption picked up and unemployment edged higher.

## Notepad

Support programme running.
"""


@pytest.fixture
def scenario():
    return load_scenario("scenarios/sweden-ai-2030")


def _output_manager(scenario, tmp_path) -> OutputManager:
    om = OutputManager(scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    return om


def _metadata(om) -> dict:
    path = om.run_dir / "turn-01" / "4-metrics-metadata.json"
    assert path.exists(), "metrics step wrote no metadata"
    return json.loads(path.read_text(encoding="utf-8"))


def test_dropped_metric_is_recovered_by_the_repair(scenario, tmp_path):
    """The repair prompt names the omitted metric, and its answer is used."""
    client = MockLLMClient(
        {FIX_PROMPT_KEY: COMPLETE_FIX, METRICS_PROMPT_KEY: INCOMPLETE}
    )
    om = _output_manager(scenario, tmp_path)
    orchestrator = Orchestrator(scenario, client, output_manager=om)

    metrics, _, _ = orchestrator._run_metrics_step(1, {"government": "..."}, [])

    assert metrics["public_sentiment_to_ai"] == 4
    metadata = _metadata(om)
    assert metadata["missing_metrics"] == ["public_sentiment_to_ai"]
    assert metadata["repaired"] is True
    assert "carried_forward" not in metadata

    fix_prompts = [user for _, user in client.calls if FIX_PROMPT_KEY in user]
    assert len(fix_prompts) == 1
    # The metric is named, with the value it holds going in, because a metric
    # the response never mentioned has nothing to recover it from.
    assert "public_sentiment_to_ai" in fix_prompts[0]
    assert "currently 3.0" in fix_prompts[0]


def test_unrepaired_drop_is_recorded_and_carried_forward_explicitly(scenario, tmp_path):
    """When the repair fails too, the omission is written down, not swallowed."""
    client = MockLLMClient(
        {FIX_PROMPT_KEY: INCOMPLETE, METRICS_PROMPT_KEY: INCOMPLETE}
    )
    om = _output_manager(scenario, tmp_path)
    orchestrator = Orchestrator(scenario, client, output_manager=om)

    metrics, _, _ = orchestrator._run_metrics_step(1, {"government": "..."}, [])

    # The value the run actually uses is now in the saved metrics, rather than
    # being an absent key that every reader has to know to carry forward.
    assert metrics["public_sentiment_to_ai"] == 3.0

    metadata = _metadata(om)
    assert metadata["missing_metrics"] == ["public_sentiment_to_ai"]
    assert metadata["repaired"] is False
    assert metadata["still_missing"] == ["public_sentiment_to_ai"]
    assert metadata["carried_forward"] == {"public_sentiment_to_ai": 3.0}


def test_complete_response_records_a_clean_turn(scenario, tmp_path):
    """A clean turn is recorded as clean, so silence is not ambiguous."""
    client = MockLLMClient({METRICS_PROMPT_KEY: COMPLETE_FIX})
    om = _output_manager(scenario, tmp_path)
    orchestrator = Orchestrator(scenario, client, output_manager=om)

    orchestrator._run_metrics_step(1, {"government": "..."}, [])

    assert _metadata(om) == {"missing_metrics": []}
    assert not [user for _, user in client.calls if FIX_PROMPT_KEY in user]


def test_constitutional_correction_may_not_drop_a_metric(scenario, tmp_path):
    """A correction that omits a metric keeps this turn's proposed value.

    Otherwise the metric silently reverts to last turn's value -- a correction
    to a metric the referee never raised.
    """
    correction = """## Metrics

```json
{"ai_capability": 8, "ai_adoption_sweden": 11, "unemployment": 9}
```

## Narrative

Adoption revised down.
"""
    client = MockLLMClient({"correction": correction})
    orchestrator = Orchestrator(scenario, client)

    proposed = {
        "ai_capability": 8,
        "ai_adoption_sweden": 12,
        "unemployment": 9,
        "public_sentiment_to_ai": 4,
    }
    corrected_metrics, _ = orchestrator._request_constitutional_correction(
        turn=1,
        previous_metrics={m.id: m.value for m in scenario.metrics.metrics.values()},
        proposed_metrics=proposed,
        narrative="Adoption picked up.",
        violations="ai_adoption_sweden moved further than the rules allow",
    )

    assert corrected_metrics["ai_adoption_sweden"] == 11  # the correction applies
    assert corrected_metrics["public_sentiment_to_ai"] == 4  # the omission does not
