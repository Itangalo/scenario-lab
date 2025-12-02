"""Test output manager."""

from pathlib import Path
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.orchestrator import run_simulation
from scenario_lab.output import OutputManager

# Load test scenario
print("Loading scenario...")
scenario = load_scenario("scenarios/sweden-ai-2030")
print(f"✓ Loaded scenario: {scenario.config.name}")

# Create mock LLM
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

Sverige genomgår en period av intensiv AI-adoption efter regeringens stödprogram. Små och medelstora företag börjar implementera AI-lösningar, vilket driver upp adoptionsgraden. Samtidigt syns tidiga tecken på oro på arbetsmarknaden när vissa rutinjobb automatiseras.""",
}

mock_llm = MockLLMClient(mock_responses)

# Create output manager
output = OutputManager(scenario, Path("scenarios/sweden-ai-2030"))

# Start run
run_dir = output.start_run()
print(f"\n✓ Created run directory: {run_dir.name}")

# Run 2 turns with incremental output
print("\nRunning 2 turns with incremental writing...")
results = run_simulation(scenario, mock_llm, num_turns=2, output_manager=output)

# Finalize summary
output.finalize_summary(results)
print("  ✓ Simulation complete, summary finalized")

# Verify files
print("\nVerifying output structure...")
config_file = run_dir / "config.json"
summary_file = run_dir / "summary.json"
turn1_dir = run_dir / "turn-01"
turn2_dir = run_dir / "turn-02"

assert config_file.exists(), "config.json not found"
assert summary_file.exists(), "summary.json not found"
assert turn1_dir.exists(), "turn-01 directory not found"
assert turn2_dir.exists(), "turn-02 directory not found"

# Check turn 1 files
assert (turn1_dir / "1-events.json").exists()
assert (turn1_dir / "2-actors").exists()
assert (turn1_dir / "3-metric-rules.md").exists()
assert (turn1_dir / "4-metrics.json").exists()
assert (turn1_dir / "4-world-state.md").exists()

print("✓ All expected files created")

# Show some content
import json
config = json.loads(config_file.read_text())
print(f"\nScenario: {config['name']}")
print(f"LLM Events: {config['llm']['events']}")
print(f"Actors: {', '.join(config['actors'])}")

summary = json.loads(summary_file.read_text())
print(f"\nCompleted {summary['total_turns']} turns")
print(f"Status: {summary['status']}")
print(f"Finished at: {summary['completed_at']}")
print(f"\nFinal metrics:")
for metric_id, value in summary['final_metrics'].items():
    print(f"  {metric_id}: {value}")

print(f"\n✓ Output test successful!")
print(f"  Run directory: {run_dir}")
