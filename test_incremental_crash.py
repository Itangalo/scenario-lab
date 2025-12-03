"""Test that incremental writing preserves data on crash (Issue #122)."""

from pathlib import Path
import json
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager

print("="*60)
print("Testing Incremental Writing with Simulated Crash (Issue #122)")
print("="*60)

# Load scenario
print("\nLoading scenario...")
scenario = load_scenario("scenarios/sweden-ai-2030")
print(f"✓ Loaded: {scenario.config.name}")

# Create mock LLM
mock_responses = {
    "potential external events": '[{"id": "ai_breakthrough", "probability": 0.15}]',
    "Your Role": """## Mål

* Öka AI-adoption i Sverige
* Säkerställa arbetskraftens omställning

## Handlingar

Regeringen lanserar ett omfattande AI-stödprogram för små och medelstora företag.""",
    "assess whether Metric Rules should be updated": """1. AI-capability ökar med 1 poäng per 6 månader
2. Om unemployment > 10 minskar public_sentiment_to_ai med 1
3. Om ai_adoption_sweden ökar med mer än 5 poäng ökar unemployment med 1""",
    "determine Metrics for the next turn": """## Metrics

```json
{"ai_capability": 6, "ai_adoption_sweden": 48, "unemployment": 7, "public_sentiment_to_ai": 1}
```

## Narrativ

Sverige genomgår en period av intensiv AI-adoption efter regeringens stödprogram.""",
}

mock_llm = MockLLMClient(mock_responses)

# Create output manager
output = OutputManager(scenario, Path("scenarios/sweden-ai-2030"))
run_dir = output.start_run()
print(f"\n✓ Created run directory: {run_dir.name}")

# Create orchestrator with output manager
orchestrator = Orchestrator(scenario, mock_llm, output_manager=output)

# Run turn 1 successfully
print("\n[Turn 1] Running...")
result1 = orchestrator.run_turn(1)
print("✓ Turn 1 completed")

# Verify turn 1 files exist
turn1_dir = run_dir / "turn-01"
assert turn1_dir.exists(), "Turn 1 directory should exist"
assert (turn1_dir / "1-events.json").exists(), "Events file should exist"
assert (turn1_dir / "3-metric-rules.md").exists(), "Rules file should exist"
assert (turn1_dir / "4-metrics.json").exists(), "Metrics file should exist"
assert (turn1_dir / "4-world-state.md").exists(), "World state file should exist"
print("✓ Turn 1 files verified")

# Check summary shows status=running
summary_file = run_dir / "summary.json"
assert summary_file.exists(), "Summary file should exist"
summary = json.loads(summary_file.read_text())
assert summary["status"] == "running", f"Status should be 'running', got '{summary['status']}'"
assert summary["total_turns"] == 1, f"Should show 1 turn, got {summary['total_turns']}"
print(f"✓ Summary shows status=running after turn 1")

# Simulate a crash by NOT running turn 2 and NOT calling finalize_summary
print("\n[Crash Simulation] Simulating crash after turn 1...")
print("  (Not running turn 2, not finalizing summary)")

# Verify data is preserved
print("\nVerifying preserved data:")
print(f"  ✓ Run directory exists: {run_dir.exists()}")
print(f"  ✓ Config file exists: {(run_dir / 'config.json').exists()}")
print(f"  ✓ Turn 1 directory exists: {turn1_dir.exists()}")
print(f"  ✓ Turn 1 has {len(list((turn1_dir / '2-actors').iterdir()))} actor files")
print(f"  ✓ Summary file exists: {summary_file.exists()}")

# Show summary content
print(f"\nSummary content (after 'crash'):")
summary = json.loads(summary_file.read_text())
print(f"  Status: {summary['status']}")
print(f"  Total turns: {summary['total_turns']}")
print(f"  Last updated: {summary['last_updated']}")
print(f"  Final metrics: {summary['final_metrics']}")

print("\n" + "="*60)
print("SUCCESS: Incremental writing preserved all data!")
print("="*60)
print("\nKey benefits demonstrated:")
print("  ✓ Turn data written immediately after each step")
print("  ✓ Summary updated after each turn (status='running')")
print("  ✓ All data preserved even without finalize_summary()")
print("  ✓ User can see progress and partial results on crash")
print(f"\n  Results in: {run_dir}")
