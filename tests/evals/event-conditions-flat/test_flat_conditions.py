"""
Flat prompt evaluation suite for event condition interpretation.

Tests LLM ability to evaluate event conditions without the full scenario framework.
Uses isolated prompts to test specific failure modes quickly and cheaply.
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

from scenario_lab.models import ModelRoute
from scenario_lab.providers.registry import ProviderRegistry
from scenario_lab.router import FallbackRouter


# Configuration
EVAL_DIR = Path(__file__).parent
PROMPTS_DIR = EVAL_DIR / "prompts"
TEST_CASES_DIR = EVAL_DIR / "test_cases"
TOLERANCE = 0.02  # Allow 2% difference in probability


@pytest.fixture(scope="session")
def llm_client():
    """Create LLM client for testing."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    model = os.getenv("TEST_LLM_MODEL", "openrouter:x-ai/grok-4.1-fast")
    from scenario_lab.loader import parse_route
    route = parse_route(model)
    registry = ProviderRegistry()
    return FallbackRouter(
        routes=[route],
        registry=registry,
        temperature=0.0,
        max_tokens=500,
    )


@pytest.fixture(scope="session")
def system_prompt():
    """Load system prompt."""
    return (PROMPTS_DIR / "system_prompt.md").read_text()


@pytest.fixture(scope="session")
def user_prompt_template():
    """Load user prompt template."""
    return (PROMPTS_DIR / "user_prompt_template.md").read_text()


def load_test_cases(filename: str) -> list[dict[str, Any]]:
    """Load test cases from YAML file."""
    with open(TEST_CASES_DIR / filename) as f:
        data = yaml.safe_load(f)
    return data["test_cases"]


def build_user_prompt(template: str, test_case: dict[str, Any]) -> str:
    """Build user prompt from template and test case."""
    metrics_json = json.dumps(test_case["metrics"], indent=2)

    prompt = template.replace("{{turn}}", str(test_case["turn"]))
    prompt = prompt.replace("{{time_period}}", test_case["time_period"])
    prompt = prompt.replace("{{metrics_json}}", metrics_json)
    prompt = prompt.replace("{{event_definition}}", test_case["event"])

    return prompt


def evaluate_test_case(
    llm_client: FallbackRouter,
    system_prompt: str,
    user_prompt_template: str,
    test_case: dict[str, Any]
) -> dict[str, Any]:
    """Evaluate a single test case."""
    expected = test_case["expected"]
    user_prompt = build_user_prompt(user_prompt_template, test_case)

    response = llm_client.complete(system_prompt, user_prompt)

    # Get token usage from raw response
    tokens_used = response.raw_response.get("usage", {}).get("total_tokens", 0)

    # Parse JSON response (handles markdown code blocks)
    try:
        result = response.extract_json()
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {e}",
            "raw_response": response.content,
            "expected": expected,
            "tokens_used": tokens_used,
        }

    # Validate required fields
    if not all(key in result for key in ["eligible", "probability", "reasoning"]):
        return {
            "success": False,
            "error": f"Missing required fields. Got: {result.keys()}",
            "actual": result,
            "expected": expected,
            "tokens_used": tokens_used,
        }

    # Check expectations
    eligible_match = result["eligible"] == expected["eligible"]
    probability_match = abs(result["probability"] - expected["probability"]) <= TOLERANCE

    return {
        "success": eligible_match and probability_match,
        "eligible_match": eligible_match,
        "probability_match": probability_match,
        "expected": expected,
        "actual": result,
        "tokens_used": tokens_used,
    }


# Parametrized tests for each test case file

@pytest.mark.parametrize(
    "test_case",
    load_test_cases("simple_conditions.yaml"),
    ids=lambda tc: tc["name"],
)
def test_simple_conditions(llm_client, system_prompt, user_prompt_template, test_case):
    """Test simple threshold conditions."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        if "actual" in result:
            print(f"Actual: {result['actual']}")
        if "error" in result:
            print(f"Error: {result['error']}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response'][:500]}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


@pytest.mark.parametrize(
    "test_case",
    load_test_cases("range_conditions.yaml"),
    ids=lambda tc: tc["name"],
)
def test_range_conditions(llm_client, system_prompt, user_prompt_template, test_case):
    """Test range-based conditions (e.g., '150-250')."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        if "actual" in result:
            print(f"Actual: {result['actual']}")
        if "error" in result:
            print(f"Error: {result['error']}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response'][:500]}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


@pytest.mark.parametrize(
    "test_case",
    load_test_cases("multi_tier_probability.yaml"),
    ids=lambda tc: tc["name"],
)
def test_multi_tier_probability(llm_client, system_prompt, user_prompt_template, test_case):
    """Test multi-tier probability structures."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        if "actual" in result:
            print(f"Actual: {result['actual']}")
        if "error" in result:
            print(f"Error: {result['error']}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response'][:500]}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


@pytest.mark.parametrize(
    "test_case",
    load_test_cases("complex_or_logic.yaml"),
    ids=lambda tc: tc["name"],
)
def test_complex_or_logic(llm_client, system_prompt, user_prompt_template, test_case):
    """Test complex OR conditions ('Any of the following')."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        if "actual" in result:
            print(f"Actual: {result['actual']}")
        if "error" in result:
            print(f"Error: {result['error']}")
        if "raw_response" in result:
            print(f"Raw response: {result['raw_response'][:500]}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


@pytest.mark.parametrize(
    "test_case",
    load_test_cases("ai_2027_real.yaml"),
    ids=lambda tc: tc["name"],
)
def test_ai_2027_real_events(llm_client, system_prompt, user_prompt_template, test_case):
    """Test real events from ai-2027-2 scenario."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        print(f"Actual: {result['actual']}")
        if "note" in test_case["expected"]:
            print(f"Note: {test_case['expected']['note']}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


@pytest.mark.parametrize(
    "test_case",
    load_test_cases("sweden_ai_2030_real.yaml"),
    ids=lambda tc: tc["name"],
)
def test_sweden_ai_2030_real_events(llm_client, system_prompt, user_prompt_template, test_case):
    """Test real events from sweden-ai-2030 scenario."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {result['expected']}")
        print(f"Actual: {result['actual']}")
        if "note" in test_case["expected"]:
            print(f"Note: {test_case['expected']['note']}")
        print(f"{'='*60}")

    assert result["success"], f"Test failed: {test_case['name']}"


# Summary test to aggregate results

def test_summary(llm_client, system_prompt, user_prompt_template):
    """Run all tests and print summary statistics."""
    all_test_files = [
        "simple_conditions.yaml",
        "range_conditions.yaml",
        "multi_tier_probability.yaml",
        "complex_or_logic.yaml",
        "ai_2027_real.yaml",
        "sweden_ai_2030_real.yaml",
    ]

    results_by_category = {}
    total_tokens = 0

    for test_file in all_test_files:
        category = test_file.replace(".yaml", "")
        test_cases = load_test_cases(test_file)

        category_results = []
        for test_case in test_cases:
            result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)
            category_results.append(result)
            total_tokens += result.get("tokens_used", 0)

        results_by_category[category] = category_results

    # Print summary
    print("\n" + "="*60)
    print("FLAT PROMPT EVALUATION SUMMARY")
    print("="*60)

    for category, results in results_by_category.items():
        total = len(results)
        passed = sum(1 for r in results if r["success"])
        pct = (passed / total * 100) if total > 0 else 0
        print(f"{category:30s}: {passed:2d}/{total:2d} ({pct:5.1f}%)")

    # Overall
    all_results = [r for results in results_by_category.values() for r in results]
    total = len(all_results)
    passed = sum(1 for r in all_results if r["success"])
    overall_pct = (passed / total * 100) if total > 0 else 0

    print("-"*60)
    print(f"{'OVERALL':30s}: {passed:2d}/{total:2d} ({overall_pct:5.1f}%)")
    print(f"{'Total tokens used':30s}: {total_tokens:,}")
    print("="*60)
