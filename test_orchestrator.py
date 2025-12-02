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
mock_responses = {
    "events": '[{"id": "ai_breakthrough", "probability": 0.15}]',
    "government": """## Mål

* Öka AI-adoption i Sverige
* Säkerställa arbetskraftens omställning

## Handlingar

Regeringen lanserar ett omfattande AI-stödprogram för små och medelstora företag.""",
    "metric-rules": """1. AI-capability ökar med 1 poäng per 6 månader
2. Om unemployment > 10 minskar public_sentiment_to_ai med 1
3. Om ai_adoption_sweden ökar med mer än 5 poäng ökar unemployment med 1""",
    "metrics": """## Metrics

```json
{"ai_capability": 6, "ai_adoption_sweden": 48, "unemployment": 7, "public_sentiment_to_ai": 1}
```

## Narrativ

Sverige genomgår en period av intensiv AI-adoption efter regeringens stödprogram. Små och medelstora företag börjar implementera AI-lösningar, vilket driver upp adoptionsgraden. Samtidigt syns tidiga tecken på oro på arbetsmarknaden när vissa rutinjobb automatiseras.

## Notepad

Regeringens AI-stödprogram lanserades under denna runda. Programmet förväntas pågå i minst 2 rundor.""",
}

mock_llm = MockLLMClient(mock_responses)

# Run one turn
print("\n" + "="*60)
print("Running test turn...")
print("="*60)

orchestrator = Orchestrator(scenario, mock_llm)
result = orchestrator.run_turn(1)

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
