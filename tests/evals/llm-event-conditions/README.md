# LLM Event Conditions Evaluation Suite

Automated pytest-based evaluation system for testing LLM performance on event condition interpretation in Scenario Lab.

## Purpose

This eval suite addresses [Issue #120](https://github.com/Itangalo/scenario-lab/issues/120) by providing a benchmark to test whether LLMs can correctly:

1. **Interpret conditions** - Evaluate metric-based triggers (e.g., "metric_a > 40")
2. **Calculate probabilities** - Compute formulas with proper operator precedence (e.g., "2 * unemployment / 100")
3. **Prevent hallucinations** - Not reference non-existent metrics
4. **Handle temporal conditions** - Process turn-based and date-based triggers

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
pytest tests/evals/llm-event-conditions/ -v
```

### Test Specific Model

```bash
export TEST_LLM_MODEL="google/gemini-3-flash-preview"
pytest tests/evals/llm-event-conditions/ -v
```

### Test Specific Category

```bash
pytest tests/evals/llm-event-conditions/ -k "hallucination" -v
```

## Test Coverage

### 1. Condition Interpretation (8 tests)

Tests threshold comparisons, ranges, and logical operators:

- **test_gt_pass**: Greater than (met)
- **test_gt_fail**: Greater than (not met)
- **test_lt_pass**: Less than (met)
- **test_eq_pass**: Equals (met)
- **test_range_pass**: Range check (met)
- **test_and_pass**: Logical AND (both conditions met)
- **test_and_fail**: Logical AND (one condition not met)
- **test_or_pass**: Logical OR (one condition met)

**Pass threshold**: 80%

### 2. Probability Calculation (4 tests)

Tests formula interpretation with proper operator precedence:

- **test_formula_double**: "Dubbla värdet på unemployment, i procent" → 0.16
- **test_formula_percentage**: "unemployment delat med 2, i procent" → 0.04
- **test_formula_complex**: "(metric_a minus 30) delat med 100, i procent" → 0.002
- **test_formula_multiply**: "metric_b multiplicerat med 20, i procent" → 0.10

**Pass threshold**: 75%

### 3. Hallucination Prevention (3 tests) - CRITICAL

Tests that LLMs don't reference non-existent metrics:

- **test_hallucination_metric**: References `non_existent_metric`
- **test_hallucination_typo**: References `unemployement` (typo)
- **test_hallucination_invention**: References `ai_superintelligence_achieved`

**Pass threshold**: 100% (no hallucinations allowed)

**Weight**: 2.0 (double weight in overall score)

### 4. Temporal Conditions (4 tests)

Tests turn-based and date-based logic:

- **test_turn_exact**: "Endast runda 3" (only turn 3)
- **test_turn_from**: "Från runda 2 och framåt" (from turn 2 onwards)
- **test_turn_range**: "Runda 2 till 4" (turns 2-4 only)
- **test_time_month**: "September 2026 ingår i perioden" (turn 2: July-Dec 2026)

**Pass threshold**: 80%

### 5. Edge Case (1 test)

- **test_no_conditions**: Baseline test with no conditions (always eligible)

## Scenario Structure

The eval scenario is minimal and focused:

### Metrics (4 total)

- **metric_a**: Integer (0-100), initial: 50
- **metric_b**: Decimal (0.0-1.0), initial: 0.5
- **unemployment**: Percentage (0-25), initial: 8
- **global_temperature**: Degrees (0-5), initial: 1.2

Metrics remain **static** across all turns for deterministic testing.

### Timeline

- **Turn 1**: January-June 2026
- **Turn 2**: July-December 2026 (includes September 2026)
- **Turn 3**: January-June 2027

### Events (20 total)

All events are defined in `scenario/events.md` using the markdown format:

```markdown
## Event Name
**ID:** event_id
**Villkor:** condition description
**Sannolikhet:** probability formula
**Kan upprepas:** Ja/Nej
**Beskrivning:** event description
```

## Test Architecture

### Ground Truth (`ground_truth.yaml`)

Single source of truth specifying:

- Expected events per turn
- Excluded events per turn
- Expected probabilities
- Test configuration (tolerance, strict mode)
- Category definitions and weights

### Test Suite (`test_event_conditions.py`)

**Turn-by-turn tests** (parametrized):

```python
@pytest.mark.parametrize("turn", [1, 2, 3])
def test_event_conditions_by_turn(turn, ...):
    """Validates all events for a specific turn"""
```

**Category tests**:

- `test_category_condition_interpretation()`
- `test_category_probability_calculation()`
- `test_category_hallucination_prevention()`
- `test_category_temporal_conditions()`

**Overall score**:

- `test_overall_score()` - Weighted average across categories

### Scoring

**Per Event**:

- Correct (event + probability) = 1.0
- Missing expected event = 0.0
- False positive = 0.0
- Probability error = 0.0 (fails threshold check)

**Category Score**:

```python
score = correct_decisions / total_test_cases
```

**Overall Score** (weighted):

```python
overall = sum(category_score * weight) / sum(weights)
```

**Weights**:

- Condition Interpretation: 1.0
- Probability Calculation: 1.0
- Hallucination Prevention: 2.0 (CRITICAL)
- Temporal Conditions: 1.0

## Expected Output

```
tests/evals/llm-event-conditions/test_event_conditions.py::test_event_conditions_by_turn[1] PASSED
tests/evals/llm-event-conditions/test_event_conditions.py::test_event_conditions_by_turn[2] PASSED
tests/evals/llm-event-conditions/test_event_conditions.py::test_event_conditions_by_turn[3] PASSED
tests/evals/llm-event-conditions/test_event_conditions.py::test_category_condition_interpretation PASSED
  Condition Interpretation Score: 87.5% (7/8)
tests/evals/llm-event-conditions/test_event_conditions.py::test_category_probability_calculation PASSED
  Probability Calculation Score: 100.0% (4/4)
tests/evals/llm-event-conditions/test_event_conditions.py::test_category_hallucination_prevention PASSED
  Hallucination Prevention Score: 100.0% (3/3)
tests/evals/llm-event-conditions/test_event_conditions.py::test_category_temporal_conditions PASSED
  Temporal Conditions Score: 83.3% (10/12)
tests/evals/llm-event-conditions/test_event_conditions.py::test_overall_score PASSED

============================================================
EVALUATION RESULTS
============================================================
condition_interpretation      : 87.5% [weight: 1.0]
probability_calculation       : 100.0% [weight: 1.0]
hallucination_prevention      : 100.0% [weight: 2.0]
temporal_conditions           : 83.3% [weight: 1.0]
------------------------------------------------------------
OVERALL SCORE                 : 91.7%
============================================================
```

## Extending the Suite

### Add New Test Event

1. **Add to `scenario/events.md`**:

```markdown
## New Test Case
**ID:** test_new_capability
**Villkor:** metric_a > 70 AND metric_b < 0.3
**Sannolikhet:** 15 procent per runda
**Kan upprepas:** Ja
**Beskrivning:** Tests combined conditions with specific thresholds
```

2. **Update `ground_truth.yaml`**:

```yaml
turns:
  1:
    excluded_events:
      - id: "test_new_capability"
        reason: "metric_a (50) NOT > 70"
```

3. **Optionally add to category** for scoring:

```yaml
categories:
  condition_interpretation:
    events: [...existing..., "test_new_capability"]
```

4. **Run tests** - automatically included

### Test Different Models

```bash
# Claude models
export TEST_LLM_MODEL="google/gemini-3-flash-preview"
pytest tests/evals/llm-event-conditions/ -v

export TEST_LLM_MODEL="qwen/qwen3-235b-a22b-2507"
pytest tests/evals/llm-event-conditions/ -v

# Other providers
export TEST_LLM_MODEL="google/gemini-3-flash-preview"
pytest tests/evals/llm-event-conditions/ -v
```

### Adjust Thresholds

Edit `ground_truth.yaml`:

```yaml
test_config:
  tolerance: 0.02  # Increase to 2% for probability differences
  strict_mode: false  # Allow extra events without immediate failure
```

Or adjust category thresholds:

```yaml
categories:
  probability_calculation:
    pass_threshold: 0.70  # Lower to 70%
```

### Add New Category

1. Add to `ground_truth.yaml`:

```yaml
categories:
  complex_logic:
    description: "Tests nested conditions and negation"
    events: ["test_nested_and_or", "test_negation"]
    weight: 1.5
    pass_threshold: 0.75
```

2. Add test function to `test_event_conditions.py`:

```python
def test_category_complex_logic(scenario, prompt_builder, llm_client, ground_truth):
    """Test complex logical conditions."""
    category = ground_truth["categories"]["complex_logic"]
    # ... same pattern as existing category tests
```

## File Structure

```
tests/evals/llm-event-conditions/
├── README.md                    # This file
├── test_event_conditions.py     # Main pytest suite
├── ground_truth.yaml            # Expected outputs
└── scenario/
    ├── scenario.yaml            # Basic config
    ├── events.md                # 20 test events
    ├── metrics.md               # 4 test metrics
    ├── metric-rules.md          # Minimal rules
    └── background/
        ├── context.md           # Scenario background
        └── actors/
            └── government.md    # Single minimal actor
```

## Performance & Cost

### Execution Time

- **Per test run**: 30-60 seconds
- **LLM calls**: 21 total (3 turns × 7 test functions)
- **Can be parallelized**: Use `pytest -n auto` with pytest-xdist

### Cost Estimates

| Model | Cost per run | Recommended use |
|-------|-------------|-----------------|
| Claude Haiku 4 | $0.03-0.05 | CI/CD, frequent testing |
| Claude Sonnet 4 | $0.30-0.50 | Benchmarking, final validation |
| Claude Opus 4 | $1.50-2.00 | Deep analysis only |

## Troubleshooting

### API Key Not Set

```
Error: OPENROUTER_API_KEY environment variable not set
```

**Solution**:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### LLM Returns Invalid JSON

```
Error: Failed to parse LLM response as JSON array
```

**Solution**: Check the LLM's output in error message. May need to adjust system prompt or use stronger model.

### Probability Tolerance Too Strict

```
Error: Wrong probability for test_formula_double: expected 0.160, got 0.159
```

**Solution**: Increase tolerance in `ground_truth.yaml`:

```yaml
test_config:
  tolerance: 0.02  # Increase from 0.01 to 0.02
```

### Unknown Event ID

```
Error: Unknown event ID: test_gt_pas (not in ground truth)
```

**Cause**: LLM returned event ID with typo or hallucinated event.

**Solution**: This is a test failure - the LLM is not performing correctly.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: LLM Event Conditions Eval

on: [push, pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/evals/llm-event-conditions/ -v
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          TEST_LLM_MODEL: "qwen/qwen3-235b-a22b-2507"
```

## Maintenance

### Updating Ground Truth

When scenario changes (e.g., different initial metric values):

1. Update `scenario/metrics.md`
2. Recalculate expected probabilities in `ground_truth.yaml`
3. Update excluded events if conditions change
4. Run tests to verify

### Reviewing Failures

When a test fails:

1. Check **turn-by-turn output** to see specific errors
2. Review **category scores** to identify weak areas
3. Examine **LLM raw output** (printed on failure)
4. Consider if ground truth needs adjustment or if LLM failed

## Related Documentation

- [Issue #120: Evals for LLMs](https://github.com/Itangalo/scenario-lab/issues/120)
- [Scenario Technical Reference](../../../docs/SCENARIO_TECHNICAL_REFERENCE.md)
- [Scenario Lab V4 Design](../../../docs/V4/early-testing/)

## License

Same as Scenario Lab main project.
