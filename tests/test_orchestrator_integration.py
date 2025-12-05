"""Integration tests for Orchestrator."""

import pytest
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.models import Scenario

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
