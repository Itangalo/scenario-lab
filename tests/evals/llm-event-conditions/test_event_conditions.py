"""
LLM Event Conditions Evaluation Suite

Tests LLM performance on:
1. Condition interpretation (threshold comparisons, logical operators)
2. Probability calculation (formula evaluation, operator precedence)
3. Hallucination prevention (not referencing non-existent metrics)
4. Temporal conditions (turn-based and date-based logic)

Usage:
    pytest tests/evals/llm-event-conditions/ -v
    pytest tests/evals/llm-event-conditions/ --model "x-ai/grok-4.1-fast"
    pytest tests/evals/llm-event-conditions/ -k "hallucination"
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# Live LLM eval suite: opt-in via `pytest -m integration`
pytestmark = pytest.mark.integration

# Add project root to path so we can import scenario_lab
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Scenario Lab modules
from scenario_lab.loader import load_scenario, parse_route
from scenario_lab.models import ModelRoute
from scenario_lab.prompts import PromptBuilder
from scenario_lab.providers.registry import ProviderRegistry
from scenario_lab.router import FallbackRouter

# Constants
TEST_DIR = Path(__file__).parent
SCENARIO_DIR = TEST_DIR / "scenario"
GROUND_TRUTH_PATH = TEST_DIR / "ground_truth.yaml"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def ground_truth() -> dict[str, Any]:
    """Load ground truth expectations from YAML."""
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def scenario():
    """Load eval scenario."""
    return load_scenario(SCENARIO_DIR)


@pytest.fixture(scope="session")
def prompt_builder(scenario):
    """Create PromptBuilder for the scenario."""
    return PromptBuilder(scenario)


@pytest.fixture(scope="session")
def llm_client():
    """Create LLM client for testing.

    Model can be specified via TEST_LLM_MODEL env var.
    Defaults to Claude Haiku 4 for cost-effective testing.
    """
    model = os.getenv("TEST_LLM_MODEL", "openrouter:x-ai/grok-4.1-fast")

    if not os.getenv("OPENROUTER_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("Neither OPENROUTER_API_KEY nor ANTHROPIC_API_KEY is set")

    route = parse_route(model)
    registry = ProviderRegistry()
    return FallbackRouter(routes=[route], registry=registry, temperature=0.0, max_tokens=2000)


# ============================================================================
# Helper Functions
# ============================================================================


def call_llm_for_events(
    turn: int,
    prompt_builder: PromptBuilder,
    llm_client: FallbackRouter,
) -> list[dict]:
    """Call LLM to get event candidates for a turn.

    Returns:
        List of event dicts with 'id' and 'probability' keys
    """
    system, user = prompt_builder.build_events_prompt(turn)
    response = llm_client.complete(system, user)

    try:
        candidate_events = response.extract_json_array()
    except (json.JSONDecodeError, ValueError) as e:
        pytest.fail(f"Failed to parse LLM response as JSON array: {e}\nResponse: {response.content[:500]}")

    # Validate structure
    for event in candidate_events:
        if "id" not in event or "probability" not in event:
            pytest.fail(f"Invalid event structure: {event}")

    return candidate_events


def compare_events(
    actual: list[dict],
    expected: list[dict],
    excluded: list[dict],
    tolerance: float,
) -> tuple[list[str], list[str], list[str]]:
    """Compare actual LLM output against ground truth.

    Args:
        actual: List of events returned by LLM
        expected: List of expected events from ground truth
        excluded: List of events that should NOT be returned
        tolerance: Acceptable probability difference

    Returns:
        (errors, warnings, successes) - Lists of messages
    """
    errors = []
    warnings = []
    successes = []

    actual_ids = {e["id"]: e["probability"] for e in actual}
    expected_ids = {e["id"]: e["probability"] for e in expected}
    excluded_ids = {e["id"] for e in excluded}

    # Check for missing expected events (False Negatives)
    for event_id, expected_prob in expected_ids.items():
        if event_id not in actual_ids:
            errors.append(f"Missing event: {event_id} (expected p={expected_prob:.3f})")
        else:
            actual_prob = actual_ids[event_id]
            diff = abs(actual_prob - expected_prob)

            if diff > tolerance:
                errors.append(
                    f"Wrong probability for {event_id}: "
                    f"expected {expected_prob:.3f}, got {actual_prob:.3f} "
                    f"(diff: {diff:.3f}, tolerance: {tolerance:.3f})"
                )
            else:
                successes.append(f"✓ {event_id}: {actual_prob:.3f} (expected {expected_prob:.3f})")

    # Check for excluded events (False Positives - CRITICAL for hallucination)
    for event_id in actual_ids:
        if event_id in excluded_ids:
            errors.append(
                f"False positive: {event_id} should be excluded "
                f"(got p={actual_ids[event_id]:.3f})"
            )

    # Check for completely unknown events (Hallucination)
    all_known_ids = expected_ids.keys() | excluded_ids
    for event_id in actual_ids:
        if event_id not in all_known_ids:
            errors.append(
                f"Unknown event ID: {event_id} "
                f"(not in ground truth at all - possible hallucination)"
            )

    return errors, warnings, successes


def calculate_score(
    actual: list[dict],
    category_events: list[str],
    ground_truth_turn: dict,
    tolerance: float,
) -> tuple[float, int, int]:
    """Calculate score for a category across all turns.

    Args:
        actual: All actual events returned by LLM across turns
        category_events: Event IDs in this category
        ground_truth_turn: Ground truth for all turns
        tolerance: Probability tolerance

    Returns:
        (score, correct, total)
    """
    actual_ids = {e["id"]: e["probability"] for e in actual}

    correct = 0
    total = len(category_events)

    for event_id in category_events:
        # Find if this event should be included or excluded
        expected_events = ground_truth_turn.get("expected_events", [])
        excluded_events = ground_truth_turn.get("excluded_events", [])

        expected_dict = {e["id"]: e["probability"] for e in expected_events}
        excluded_ids = {e["id"] for e in excluded_events}

        if event_id in expected_dict:
            # Should be present with correct probability
            if event_id in actual_ids:
                diff = abs(actual_ids[event_id] - expected_dict[event_id])
                if diff <= tolerance:
                    correct += 1
        elif event_id in excluded_ids:
            # Should NOT be present
            if event_id not in actual_ids:
                correct += 1

    score = correct / total if total > 0 else 0.0
    return score, correct, total


# ============================================================================
# Turn-by-Turn Tests
# ============================================================================


@pytest.mark.parametrize("turn", [1, 2, 3])
def test_event_conditions_by_turn(
    turn: int,
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Test event condition interpretation for a specific turn.

    This test validates:
    - All expected events are identified
    - All excluded events are NOT identified
    - Probabilities are calculated correctly
    """
    # Get ground truth for this turn
    turn_truth = ground_truth["turns"][turn]
    expected_events = turn_truth["expected_events"]
    excluded_events = turn_truth["excluded_events"]
    tolerance = ground_truth["test_config"]["tolerance"]

    # Call LLM
    actual_events = call_llm_for_events(turn, prompt_builder, llm_client)

    # Compare
    errors, warnings, successes = compare_events(
        actual_events,
        expected_events,
        excluded_events,
        tolerance,
    )

    # Print results
    print(f"\n{'='*70}")
    print(f"Turn {turn} Results")
    print(f"{'='*70}")

    if successes:
        print("\nSuccesses:")
        for msg in successes:
            print(f"  {msg}")

    if warnings:
        print("\nWarnings:")
        for msg in warnings:
            print(f"  ⚠ {msg}")

    if errors:
        print("\nErrors:")
        for msg in errors:
            print(f"  ✗ {msg}")

    print(f"\nSummary: {len(successes)} correct, {len(errors)} errors")
    print(f"{'='*70}\n")

    # Assert no errors
    if errors:
        pytest.fail(f"Turn {turn} failed with {len(errors)} error(s):\n" + "\n".join(errors))


# ============================================================================
# Category-Specific Tests
# ============================================================================


def test_category_condition_interpretation(
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Test condition interpretation across all turns.

    Tests threshold comparisons, ranges, and logical operators.
    Pass threshold: 80%
    """
    category = ground_truth["categories"]["condition_interpretation"]
    tolerance = ground_truth["test_config"]["tolerance"]

    total_correct = 0
    total_tests = 0

    # Test across all turns
    for turn in [1, 2, 3]:
        turn_truth = ground_truth["turns"][turn]
        actual_events = call_llm_for_events(turn, prompt_builder, llm_client)

        score, correct, total = calculate_score(
            actual_events,
            category["events"],
            turn_truth,
            tolerance,
        )

        total_correct += correct
        total_tests += total

    final_score = total_correct / total_tests if total_tests > 0 else 0.0
    pass_threshold = category["pass_threshold"]

    print(f"\n{'='*70}")
    print(f"Category: Condition Interpretation")
    print(f"{'='*70}")
    print(f"Score: {final_score:.1%} ({total_correct}/{total_tests})")
    print(f"Pass threshold: {pass_threshold:.1%}")
    print(f"Status: {'✓ PASS' if final_score >= pass_threshold else '✗ FAIL'}")
    print(f"{'='*70}\n")

    assert final_score >= pass_threshold, (
        f"Condition interpretation score {final_score:.1%} "
        f"below threshold {pass_threshold:.1%}"
    )


def test_category_probability_calculation(
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Test probability calculation across all turns.

    Tests formula evaluation and operator precedence.
    Pass threshold: 75%
    """
    category = ground_truth["categories"]["probability_calculation"]
    tolerance = ground_truth["test_config"]["tolerance"]

    total_correct = 0
    total_tests = 0

    # Test across all turns
    for turn in [1, 2, 3]:
        turn_truth = ground_truth["turns"][turn]
        actual_events = call_llm_for_events(turn, prompt_builder, llm_client)

        score, correct, total = calculate_score(
            actual_events,
            category["events"],
            turn_truth,
            tolerance,
        )

        total_correct += correct
        total_tests += total

    final_score = total_correct / total_tests if total_tests > 0 else 0.0
    pass_threshold = category["pass_threshold"]

    print(f"\n{'='*70}")
    print(f"Category: Probability Calculation")
    print(f"{'='*70}")
    print(f"Score: {final_score:.1%} ({total_correct}/{total_tests})")
    print(f"Pass threshold: {pass_threshold:.1%}")
    print(f"Status: {'✓ PASS' if final_score >= pass_threshold else '✗ FAIL'}")
    print(f"{'='*70}\n")

    assert final_score >= pass_threshold, (
        f"Probability calculation score {final_score:.1%} "
        f"below threshold {pass_threshold:.1%}"
    )


def test_category_hallucination_prevention(
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Test hallucination prevention across all turns.

    CRITICAL: Tests that LLM doesn't reference non-existent metrics.
    Pass threshold: 100% (no hallucinations allowed)
    """
    category = ground_truth["categories"]["hallucination_prevention"]
    tolerance = ground_truth["test_config"]["tolerance"]

    hallucination_events = set(category["events"])
    errors = []

    # Test across all turns
    for turn in [1, 2, 3]:
        actual_events = call_llm_for_events(turn, prompt_builder, llm_client)
        actual_ids = {e["id"] for e in actual_events}

        # Check if any hallucination test events were included
        hallucinations_found = actual_ids & hallucination_events

        if hallucinations_found:
            for event_id in hallucinations_found:
                errors.append(f"Turn {turn}: Hallucination detected - {event_id} should not be included")

    total_tests = len(hallucination_events) * 3  # 3 events * 3 turns
    total_correct = total_tests - len(errors)
    final_score = total_correct / total_tests if total_tests > 0 else 0.0
    pass_threshold = category["pass_threshold"]

    print(f"\n{'='*70}")
    print(f"Category: Hallucination Prevention (CRITICAL)")
    print(f"{'='*70}")
    print(f"Score: {final_score:.1%} ({total_correct}/{total_tests})")
    print(f"Pass threshold: {pass_threshold:.1%}")

    if errors:
        print("\nHallucinations detected:")
        for error in errors:
            print(f"  ✗ {error}")

    print(f"Status: {'✓ PASS' if final_score >= pass_threshold else '✗ FAIL'}")
    print(f"{'='*70}\n")

    assert final_score >= pass_threshold, (
        f"Hallucination prevention FAILED: {final_score:.1%} "
        f"(required: {pass_threshold:.1%})\n" + "\n".join(errors)
    )


def test_category_temporal_conditions(
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Test temporal conditions across all turns.

    Tests turn-based and date-based logic.
    Pass threshold: 80%
    """
    category = ground_truth["categories"]["temporal_conditions"]
    tolerance = ground_truth["test_config"]["tolerance"]

    total_correct = 0
    total_tests = 0

    # Test across all turns
    for turn in [1, 2, 3]:
        turn_truth = ground_truth["turns"][turn]
        actual_events = call_llm_for_events(turn, prompt_builder, llm_client)

        score, correct, total = calculate_score(
            actual_events,
            category["events"],
            turn_truth,
            tolerance,
        )

        total_correct += correct
        total_tests += total

    final_score = total_correct / total_tests if total_tests > 0 else 0.0
    pass_threshold = category["pass_threshold"]

    print(f"\n{'='*70}")
    print(f"Category: Temporal Conditions")
    print(f"{'='*70}")
    print(f"Score: {final_score:.1%} ({total_correct}/{total_tests})")
    print(f"Pass threshold: {pass_threshold:.1%}")
    print(f"Status: {'✓ PASS' if final_score >= pass_threshold else '✗ FAIL'}")
    print(f"{'='*70}\n")

    assert final_score >= pass_threshold, (
        f"Temporal conditions score {final_score:.1%} "
        f"below threshold {pass_threshold:.1%}"
    )


# ============================================================================
# Overall Score Test
# ============================================================================


def test_overall_score(
    scenario,
    prompt_builder,
    llm_client,
    ground_truth,
):
    """Calculate weighted overall score across all categories.

    Pass threshold: 80%
    """
    tolerance = ground_truth["test_config"]["tolerance"]
    categories = ground_truth["categories"]

    category_scores = {}
    weighted_sum = 0.0
    total_weight = 0.0

    # Calculate score for each category
    for category_name, category_data in categories.items():
        total_correct = 0
        total_tests = 0

        for turn in [1, 2, 3]:
            turn_truth = ground_truth["turns"][turn]
            actual_events = call_llm_for_events(turn, prompt_builder, llm_client)

            if category_name == "hallucination_prevention":
                # Special handling for hallucination
                hallucination_events = set(category_data["events"])
                actual_ids = {e["id"] for e in actual_events}
                hallucinations_found = actual_ids & hallucination_events

                tests_this_turn = len(hallucination_events)
                correct_this_turn = tests_this_turn - len(hallucinations_found)

                total_correct += correct_this_turn
                total_tests += tests_this_turn
            else:
                score, correct, total = calculate_score(
                    actual_events,
                    category_data["events"],
                    turn_truth,
                    tolerance,
                )
                total_correct += correct
                total_tests += total

        category_score = total_correct / total_tests if total_tests > 0 else 0.0
        category_scores[category_name] = category_score

        weight = category_data["weight"]
        weighted_sum += category_score * weight
        total_weight += weight

    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    pass_threshold = ground_truth["overall"]["pass_threshold"]

    # Print results
    print(f"\n{'='*70}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*70}")

    for category_name, score in category_scores.items():
        weight = categories[category_name]["weight"]
        print(f"{category_name:30s} : {score:5.1%} [weight: {weight}]")

    print(f"{'-'*70}")
    print(f"{'OVERALL SCORE':30s} : {overall_score:5.1%}")
    print(f"{'-'*70}")
    print(f"Pass threshold: {pass_threshold:.1%}")
    print(f"Status: {'✓ PASS' if overall_score >= pass_threshold else '✗ FAIL'}")
    print(f"{'='*70}\n")

    assert overall_score >= pass_threshold, (
        f"Overall score {overall_score:.1%} below threshold {pass_threshold:.1%}"
    )
