#!/usr/bin/env python3
"""
Test V2 Metrics Tracking

Tests the metrics extraction and tracking system.
"""
import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.core.metrics_tracker import MetricsTracker, load_metrics_tracker
from scenario_lab.models.state import ScenarioState, WorldState, Decision, MetricRecord
from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.utils.api_client import LLMResponse


# Create test metrics.yaml
TEST_METRICS_YAML = """
scenario_name: Test Scenario
metrics:
  ai_capability_level:
    type: float
    unit: "points"
    description: "AI capability level"
    pattern: 'capability level.*?(\\d+\\.?\\d*)'
    extraction_method: regex

  safety_score:
    type: integer
    unit: "score"
    description: "Safety score"
    pattern: 'safety score.*?(\\d+)'
    extraction_method: regex

  coordination_achieved:
    type: boolean
    description: "Whether coordination was achieved"
    pattern: '(coordination achieved|coordinated successfully)'
    extraction_method: regex
"""

# Mock LLM responses with metrics
MOCK_DECISION_WITH_METRICS = """**LONG-TERM GOALS:**
- Advance AI capabilities safely
- Maintain safety score above 85

**SHORT-TERM PRIORITIES:**
- Improve capability level to 7.5 points
- Ensure safety score of 90

**REASONING:**
Current capability level is at 6.2 points, which needs improvement.
The safety score of 88 is acceptable but we should aim higher.

**ACTION:**
Invest in research to increase capabilities while maintaining safety standards."""

MOCK_WORLD_WITH_METRICS = """**UPDATED STATE:**
Following the actors' decisions, significant progress was made.
AI capability level has increased to 7.5 points, reflecting substantial advances.
The safety score is now at 90, showing improved safety measures.
Coordination achieved between major stakeholders.

**KEY CHANGES:**
- Capability level increased from 6.2 to 7.5 points
- Safety score improved from 88 to 90
- Coordination protocols established

**CONSEQUENCES:**
- Faster development pace
- Enhanced safety monitoring
- Better international cooperation"""


async def test_metrics_loading():
    """Test loading metrics definitions from YAML"""
    print("=" * 70)
    print("TEST 1: Loading metrics definitions")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write test metrics YAML
        metrics_file = Path(tmpdir) / "metrics.yaml"
        with open(metrics_file, 'w') as f:
            f.write(TEST_METRICS_YAML)

        # Load metrics tracker
        tracker = MetricsTracker(metrics_file)

        assert len(tracker.metrics_definitions) == 3
        assert 'ai_capability_level' in tracker.metrics_definitions
        assert 'safety_score' in tracker.metrics_definitions
        assert 'coordination_achieved' in tracker.metrics_definitions

        print(f"  ✓ Loaded {len(tracker.metrics_definitions)} metric definitions")
        print(f"  ✓ Metrics: {', '.join(tracker.metrics_definitions.keys())}")

    print()
    print("✅ Test 1 passed: Metrics definitions loaded correctly")
    print()
    return True


async def test_metrics_extraction_from_text():
    """Test extracting metrics from text"""
    print("=" * 70)
    print("TEST 2: Extracting metrics from text")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        metrics_file = Path(tmpdir) / "metrics.yaml"
        with open(metrics_file, 'w') as f:
            f.write(TEST_METRICS_YAML)

        tracker = MetricsTracker(metrics_file)

        # Extract from decision text
        metrics = tracker.extract_metrics_from_text(
            turn=1,
            text=MOCK_DECISION_WITH_METRICS,
            actor_name="AI Developer"
        )

        assert len(metrics) > 0
        print(f"  ✓ Extracted {len(metrics)} metrics from decision text")

        # Check specific metrics
        capability_metrics = [m for m in metrics if m.name == 'ai_capability_level']
        safety_metrics = [m for m in metrics if m.name == 'safety_score']

        assert len(capability_metrics) > 0
        assert len(safety_metrics) > 0

        # Check values (should extract 7.5 and 90 from the text)
        print(f"  ✓ Capability level: {capability_metrics[-1].value}")
        print(f"  ✓ Safety score: {safety_metrics[-1].value}")

        # Extract from world state text
        metrics = tracker.extract_metrics_from_text(
            turn=1,
            text=MOCK_WORLD_WITH_METRICS,
            actor_name=None
        )

        assert len(metrics) > 0
        print(f"  ✓ Extracted {len(metrics)} metrics from world state text")

        # Check for coordination boolean metric
        coord_metrics = [m for m in metrics if m.name == 'coordination_achieved']
        if coord_metrics:
            print(f"  ✓ Coordination achieved: {coord_metrics[-1].value}")

    print()
    print("✅ Test 2 passed: Metrics extracted from text correctly")
    print()
    return True


async def test_metrics_integration_with_phases():
    """Test metrics integration with decision and world update phases"""
    print("=" * 70)
    print("TEST 3: Integration with V2 phases")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup metrics tracker
        metrics_file = Path(tmpdir) / "metrics.yaml"
        with open(metrics_file, 'w') as f:
            f.write(TEST_METRICS_YAML)

        tracker = MetricsTracker(metrics_file)

        # Create initial state
        initial_state = ScenarioState(
            scenario_id="test",
            scenario_name="Test Scenario",
            run_id="test-run",
            scenario_config={"num_turns": 5},
            world_state=WorldState(turn=0, content="Initial state")
        )
        initial_state = initial_state.with_started()

        # Setup actor configs
        actor_configs = {
            'ai-dev': {
                'name': 'AI Developer',
                'short_name': 'ai-dev',
                'llm_model': 'openai/gpt-4o-mini',
            }
        }

        # Create decision phase with metrics tracker
        decision_phase = DecisionPhaseV2(
            actor_configs=actor_configs,
            scenario_system_prompt="Test prompt",
            metrics_tracker=tracker
        )

        # Mock LLM response
        mock_decision_response = LLMResponse(
            content=MOCK_DECISION_WITH_METRICS,
            tokens_used=500,
            input_tokens=350,
            output_tokens=150,
            model='openai/gpt-4o-mini'
        )

        with patch('scenario_lab.services.decision_phase_v2.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_decision_response
            state = await decision_phase.execute(initial_state)

        print(f"  ✓ Decision phase executed")
        print(f"  ✓ Metrics in state: {len(state.metrics)}")

        # Verify metrics were extracted from decision
        assert len(state.metrics) > 0
        metric_names = [m.name for m in state.metrics]
        print(f"  ✓ Extracted metrics: {', '.join(metric_names)}")

        # Create world update phase with metrics tracker
        world_update_phase = WorldUpdatePhaseV2(
            scenario_name="Test Scenario",
            world_state_model="openai/gpt-4o-mini",
            metrics_tracker=tracker
        )

        # Mock world update response
        mock_world_response = LLMResponse(
            content=MOCK_WORLD_WITH_METRICS,
            tokens_used=400,
            input_tokens=300,
            output_tokens=100,
            model='openai/gpt-4o-mini'
        )

        with patch('scenario_lab.services.world_update_phase_v2.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_world_response
            state = await world_update_phase.execute(state)

        print(f"  ✓ World update phase executed")
        print(f"  ✓ Total metrics in state: {len(state.metrics)}")

        # Verify additional metrics were extracted from world state
        assert len(state.metrics) > 3  # Should have metrics from both phases

    print()
    print("✅ Test 3 passed: Metrics integration with phases works")
    print()
    return True


async def test_metrics_summary():
    """Test metrics summary statistics"""
    print("=" * 70)
    print("TEST 4: Metrics summary statistics")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        metrics_file = Path(tmpdir) / "metrics.yaml"
        with open(metrics_file, 'w') as f:
            f.write(TEST_METRICS_YAML)

        tracker = MetricsTracker(metrics_file)

        # Create state with multiple metrics across turns
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test Scenario",
            run_id="test-run",
            scenario_config={"num_turns": 5},
            world_state=WorldState(turn=0, content="Initial state")
        )

        # Add metrics for turn 1
        state = state.with_metric(MetricRecord(name="ai_capability_level", value=6.0, turn=1))
        state = state.with_metric(MetricRecord(name="safety_score", value=85.0, turn=1))

        # Add metrics for turn 2
        state = state.with_metric(MetricRecord(name="ai_capability_level", value=6.5, turn=2))
        state = state.with_metric(MetricRecord(name="safety_score", value=87.0, turn=2))

        # Add metrics for turn 3
        state = state.with_metric(MetricRecord(name="ai_capability_level", value=7.5, turn=3))
        state = state.with_metric(MetricRecord(name="safety_score", value=90.0, turn=3))

        print(f"  ✓ Created state with {len(state.metrics)} metrics across 3 turns")

        # Calculate summary statistics
        summary = tracker.calculate_summary_statistics(state)

        assert 'ai_capability_level' in summary
        assert 'safety_score' in summary

        capability_stats = summary['ai_capability_level']
        assert capability_stats['min'] == 6.0
        assert capability_stats['max'] == 7.5
        assert capability_stats['count'] == 3

        print(f"  ✓ Capability level stats:")
        print(f"    - Min: {capability_stats['min']}")
        print(f"    - Max: {capability_stats['max']}")
        print(f"    - Mean: {capability_stats['mean']:.2f}")
        print(f"    - Change: {capability_stats['change']:.2f}")

        safety_stats = summary['safety_score']
        print(f"  ✓ Safety score stats:")
        print(f"    - Min: {safety_stats['min']}")
        print(f"    - Max: {safety_stats['max']}")
        print(f"    - Mean: {safety_stats['mean']:.2f}")
        print(f"    - Change: {safety_stats['change']:.2f}")

        # Test full summary
        full_summary = tracker.get_metrics_summary(state)
        assert 'final_metrics' in full_summary
        assert 'summary_statistics' in full_summary
        assert 'metrics_by_turn' in full_summary

        print(f"  ✓ Full summary generated with {len(full_summary)} sections")

        # Test saving to file
        output_file = Path(tmpdir) / "metrics_summary.json"
        tracker.save_metrics_summary(state, output_file)
        assert output_file.exists()

        print(f"  ✓ Summary saved to {output_file.name}")

    print()
    print("✅ Test 4 passed: Metrics summary statistics work correctly")
    print()
    return True


async def run_all_tests():
    """Run all metrics tests"""
    print()
    print("=" * 70)
    print("V2 METRICS TRACKING TESTS")
    print("=" * 70)
    print()

    tests = [
        test_metrics_loading,
        test_metrics_extraction_from_text,
        test_metrics_integration_with_phases,
        test_metrics_summary,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("METRICS TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL METRICS TESTS PASSED")
        print()
        print("Phase 3.3 Complete: Metrics Tracking")
        print("  ✓ Metrics definitions loading from YAML")
        print("  ✓ Regex-based extraction from text")
        print("  ✓ Integration with decision phase")
        print("  ✓ Integration with world update phase")
        print("  ✓ Summary statistics calculation")
        print("  ✓ JSON export of metrics")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
