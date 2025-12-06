# Flat Prompt Event Conditions Evaluation Suite

Fast, isolated evaluation of LLM event condition interpretation using flat prompts instead of full scenario simulations.

## Purpose

This eval suite addresses the challenge of complex event conditions in scenarios like `ai-2027-2`. Instead of running full scenario simulations, it tests event condition interpretation in isolation using single LLM calls per test case.

**Advantages:**

- **Fast iteration** - Single LLM call per test (~30 seconds for full suite)
- **Cheap** - Test with Haiku/Grok models ($0.01-0.05 per run)
- **Isolated testing** - Focus on condition interpretation without orchestration complexity
- **Easy debugging** - See exact prompt and response for each test
- **Rapid wording iteration** - Quickly test different phrasings to improve LLM understanding

## What It Tests

### 1. Simple Conditions (6 tests)

Basic threshold comparisons:

- Greater than (`>`)
- Less than (`<`)
- Greater than or equal (`>=`)
- AND logic
- Single conditions vs. compound conditions

### 2. Range Conditions (5 tests)

Natural language ranges like "150-250":

- Values within range
- Boundary values (lower/upper)
- Multiple tier ranges
- Values outside all ranges

### 3. Multi-Tier Probability (5 tests)

Complex tiered probability structures from ai-2027-2:

```markdown
**Probability:**
- If security_level < 30: 25% per turn
- If security_level 30-39: 15% per turn
- If security_level 40-49: 5% per turn
```

Tests that LLMs correctly:

- Select the right tier
- Calculate correct probability
- Handle boundary cases

### 4. Complex OR Logic (5 tests)

"Any of the following" multi-condition structures:

```markdown
**Condition:** Any of the following:
1. ai_capability_us ≥ 350
2. alignment_us < 50
3. Espionage event occurred and security_level was < 35
4. ai_capability_china within 50 points of ai_capability_us

**Probability:**
- If ONE condition met: 15% per turn
- If TWO conditions met: 35% per turn
- If THREE or more conditions met: 60% per turn
```

### 5. Real ai-2027-2 Events (6 tests)

Actual complex events from the ai-2027-2 scenario:

- Agent awakening (100% guaranteed trigger)
- AI coordination (multi-condition AND)
- Taiwan crisis (composite metric calculations)
- AI incident (multiple metric conditions)
- Safety crisis (OR condition with tiers)

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -e ".[dev]"

# Set API key
export OPENROUTER_API_KEY="your_api_key_here"
```

### Run All Tests

```bash
pytest tests/evals/event-conditions-flat/ -v
```

### Test Specific Model

```bash
export TEST_LLM_MODEL="x-ai/grok-4.1-fast"
pytest tests/evals/event-conditions-flat/ -v
```

### Test Specific Category

```bash
# Test only range conditions
pytest tests/evals/event-conditions-flat/ -k "range" -v

# Test only ai-2027 real events
pytest tests/evals/event-conditions-flat/ -k "ai_2027" -v

# Test only multi-tier probability
pytest tests/evals/event-conditions-flat/ -k "multi_tier" -v
```

### Run Summary Only

```bash
pytest tests/evals/event-conditions-flat/test_flat_conditions.py::test_summary -v
```

## File Structure

```
tests/evals/event-conditions-flat/
├── README.md                           # This file
├── test_flat_conditions.py             # Main pytest file
├── prompts/
│   ├── system_prompt.md                # System prompt for evaluation
│   └── user_prompt_template.md         # User prompt template (uses {{placeholders}})
├── test_cases/
│   ├── simple_conditions.yaml          # Basic threshold tests
│   ├── range_conditions.yaml           # Range-based conditions
│   ├── multi_tier_probability.yaml     # Complex tiered probabilities
│   ├── complex_or_logic.yaml           # "Any of the following" logic
│   └── ai_2027_real.yaml               # Real events from ai-2027-2
└── ground_truth/                       # (Reserved for future structured ground truth)
```

## Test Case Format

Each YAML file contains test cases with this structure:

```yaml
test_cases:
  - name: "unique_test_id"
    description: "What this test validates"
    turn: 1
    time_period: "January-June 2026"
    metrics:
      ai_capability_us: 200
      security_level: 45
    event: |
      ## Event Name
      **ID:** event_id
      **Condition:** ai_capability_us > 150 AND security_level < 50
      **Probability:** 15% per turn
      **Can repeat:** Yes
      **Description:** Event description
    expected:
      eligible: true
      probability: 0.15
      note: "Optional explanation"
```

## Expected Output

```
tests/evals/event-conditions-flat/test_flat_conditions.py::test_simple_conditions[simple_gt_met] PASSED
tests/evals/event-conditions-flat/test_flat_conditions.py::test_simple_conditions[simple_gt_not_met] PASSED
...
tests/evals/event-conditions-flat/test_flat_conditions.py::test_ai_2027_real_events[agent_awakening_us] PASSED

============================================================
FLAT PROMPT EVALUATION SUMMARY
============================================================
simple_conditions             :  6/ 6 (100.0%)
range_conditions              :  5/ 5 (100.0%)
multi_tier_probability        :  5/ 5 (100.0%)
complex_or_logic              :  5/ 5 (100.0%)
ai_2027_real                  :  6/ 6 (100.0%)
------------------------------------------------------------
OVERALL                       : 27/27 (100.0%)
Total tokens used             : ~12,000
============================================================
```

## Baseline Results (Grok 4.1 Fast)

Initial testing with `x-ai/grok-4.1-fast` shows **excellent performance**:

- **Overall:** 27/27 tests passed (100%) in ~3.5 minutes
- **Simple conditions:** 6/6 (100%) - Basic thresholds and logic
- **Range conditions:** 5/5 (100%) - Natural language ranges like "150-250"
- **Multi-tier probability:** 5/5 (100%) - Complex tiered probability structures
- **Complex OR logic:** 5/5 (100%) - "Any of the following" multi-condition logic
- **Real AI 2027 events:** 6/6 (100%) - Real-world complex event conditions
- **Total tokens:** ~12,000 (cost: ~$0.01-0.02)

This demonstrates that Grok 4.1 Fast can reliably interpret complex event conditions including:
- Composite metric calculations
- Additive probabilities
- Multi-condition AND/OR logic
- Range-based tiers
- Event history dependencies

## Iterating on Event Wording

The main workflow:

1. **Run baseline** - Test current event wording with cheap model
2. **Identify failures** - See which conditions LLMs struggle with
3. **Modify wording** - Edit test cases with clearer phrasing
4. **Re-test** - Verify improvements
5. **Apply to scenario** - Update actual scenario events with improved wording

### Example: Improving Range Conditions

**Original (ambiguous):**

```markdown
**Probability:**
- If ai_capability_us 150-250: 5% per turn
```

**Improved (explicit):**

```markdown
**Probability:**
- If ai_capability_us is between 150 and 250 (inclusive): 5% per turn
```

Or even more explicit:

```markdown
**Probability:**
- If 150 ≤ ai_capability_us ≤ 250: 5% per turn
```

### Testing Different Models

```bash
# Cheap models for iteration
export TEST_LLM_MODEL="anthropic/claude-haiku-4"
export TEST_LLM_MODEL="google/gemini-flash-1.5"

# Mid-tier models
export TEST_LLM_MODEL="anthropic/claude-sonnet-3.5"
export TEST_LLM_MODEL="openai/gpt-4o-mini"

# Premium models (final validation)
export TEST_LLM_MODEL="anthropic/claude-sonnet-4"
export TEST_LLM_MODEL="openai/gpt-4o"
```

## Adding New Test Cases

### 1. Add to Existing Category

Edit the appropriate YAML file in `test_cases/`:

```yaml
  - name: "new_test_case"
    description: "Tests new edge case"
    turn: 1
    time_period: "January-June 2026"
    metrics:
      metric_name: 100
    event: |
      ## Event
      **ID:** event_id
      **Condition:** metric_name > 50
      **Probability:** 10% per turn
      **Can repeat:** Yes
      **Description:** Description
    expected:
      eligible: true
      probability: 0.10
```

### 2. Create New Category

Create new YAML file:

```bash
touch tests/evals/event-conditions-flat/test_cases/new_category.yaml
```

Add parametrized test in `test_flat_conditions.py`:

```python
@pytest.mark.parametrize(
    "test_case",
    load_test_cases("new_category.yaml"),
    ids=lambda tc: tc["name"],
)
def test_new_category(llm_client, system_prompt, user_prompt_template, test_case):
    """Test new category of conditions."""
    result = evaluate_test_case(llm_client, system_prompt, user_prompt_template, test_case)

    if not result["success"]:
        print(f"\nTest: {test_case['name']}")
        print(f"Expected: {result['expected']}")
        print(f"Actual: {result['actual']}")

    assert result["success"], f"Test failed: {test_case['name']}"
```

Update `test_summary()` to include new file.

## Modifying Prompts

### System Prompt

Edit `prompts/system_prompt.md` to change how conditions should be interpreted:

- Add clarifications about ambiguous syntax
- Provide examples of correct interpretation
- Add guardrails against hallucination

### User Prompt Template

Edit `prompts/user_prompt_template.md` to change input format:

- Add more context fields
- Reorder information presentation
- Add emphasis or warnings

After editing, re-run tests to see impact.

## Performance & Cost

### Execution Time

- **Per test run**: 30-60 seconds (27 tests)
- **Single category**: 5-10 seconds
- **Can parallelize**: Use `pytest -n auto` (requires pytest-xdist)

### Cost Estimates

| Model | Cost per run | Use case |
|-------|-------------|----------|
| Claude Haiku 4 | $0.01-0.02 | Rapid iteration |
| Gemini Flash 1.5 | $0.01-0.02 | Rapid iteration |
| Claude Sonnet 3.5 | $0.05-0.10 | Validation |
| Claude Sonnet 4 | $0.30-0.50 | Final benchmarking |

## Troubleshooting

### API Key Not Set

```
Error: OPENROUTER_API_KEY environment variable not set
```

**Solution:**

```bash
export OPENROUTER_API_KEY="your_key_here"
```

### Invalid JSON Response

```
Error: Invalid JSON: Expecting value: line 1 column 1 (char 0)
```

**Cause:** LLM returned non-JSON content (explanation before JSON, etc.)

**Solutions:**

- Strengthen system prompt to emphasize "JSON only"
- Use stronger model
- Add examples to system prompt

### Probability Mismatch

```
Expected: {'eligible': True, 'probability': 0.15}
Actual: {'eligible': True, 'probability': 0.149}
```

**Solution:** Adjust tolerance in `test_flat_conditions.py`:

```python
TOLERANCE = 0.02  # Increase from 0.01 to 0.02
```

### Model Not Understanding Range Syntax

If "150-250" consistently fails:

1. Edit the test case to use clearer syntax
2. Update system prompt with explicit examples
3. Test with stronger model to confirm it's not a capability issue
4. Apply improved wording to actual scenario

## Integration with Scenario Development

After using this eval suite to improve event condition wording:

1. **Update scenario events** - Apply improved wording to `scenarios/ai-2027-2/events.md`
2. **Test full simulation** - Run actual scenario to verify
3. **Document patterns** - Add successful phrasings to scenario creation guide
4. **Share learnings** - Update templates with best practices

## Related

- Full scenario-based eval: `tests/evals/llm-event-conditions/`
- AI 2027-2 scenario: `scenarios/ai-2027-2/`
- Event condition documentation: `docs/creating-scenarios.md`
