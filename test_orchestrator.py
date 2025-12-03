"""Test orchestrator with mock LLM."""

from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.orchestrator import Orchestrator

# Load test scenario
print("Loading scenario...")
scenario = load_scenario("scenarios/sweden-ai-2030")
print(f"✓ Loaded scenario: {scenario.config.name}")
print(f"  Actors: {len(scenario.actors)}")
print(f"  Metrics: {len(scenario.metrics.metrics)}")
print(f"  Events: {len(scenario.events)}")

# Create mock LLM with responses for each step
# Note: Metrics response format must match the regex in extract_metrics_and_narrative()
# Keys must be unique phrases that only appear in ONE specific prompt type
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
}

mock_llm = MockLLMClient(mock_responses)

# Run one turn
print("\n" + "="*60)
print("Running test turn...")
print("="*60)

orchestrator = Orchestrator(scenario, mock_llm)
try:
    result = orchestrator.run_turn(1)
except Exception as e:
    print(f"\nError occurred: {e}")
    print("\nMock LLM calls made:")
    for i, (sys_prompt, user_prompt) in enumerate(mock_llm.calls):
        print(f"\nCall {i+1}:")
        print(f"System prompt (first 100 chars): {sys_prompt[:100]}")
        print(f"User prompt (first 200 chars): {user_prompt[:200]}")
    raise

print("\n" + "="*60)
print("TURN COMPLETE")
print("="*60)
print(f"\nTriggered events: {len(result.triggered_events)}")
print(f"Actor outputs: {len(result.actor_outputs)}")
print(f"\nUpdated metrics:")
for metric_id, value in result.metrics.items():
    print(f"  {metric_id}: {value}")
print(f"\nNarrative preview:")
print(result.narrative[:200] + "...")
print(f"\nNotepad:")
print(result.notepad if result.notepad else "(empty)")
