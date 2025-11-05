# Integration Tests for Batch Execution System

This document describes the integration tests for the batch execution system and how to run them.

## Overview

Integration tests verify that all batch components work correctly together in real-world scenarios. These tests:

- Create minimal test scenarios
- Execute complete batch runs
- Verify output structure and data integrity
- Test resume functionality
- Validate cost tracking
- Test analysis pipeline

## Test Categories

### 1. Fast Tests (No API Calls)
These tests verify component integration without making actual LLM API calls:

```bash
python -m unittest tests.test_batch_integration.TestBatchWorkflow -v
```

**Runtime:** < 1 second
**Cost:** $0

### 2. Full Integration Tests (With API Calls)
These tests execute real batch runs with actual LLM API calls:

```bash
python -m unittest tests.test_batch_integration.TestBatchIntegration -v
```

**Runtime:** 2-5 minutes (depends on API speed)
**Cost:** ~$0.10-0.50 (uses gpt-4o-mini)

**⚠️  Requirements:**
- Valid OpenRouter API key in `.env`
- Network connection
- Sufficient API credits

## Individual Test Descriptions

### TestBatchIntegration

**test_sequential_batch_execution**
- Tests complete sequential batch execution
- Creates 2 runs with 1 variation
- Verifies all output files are created
- Validates batch summary and costs

**test_parallel_batch_execution**
- Tests parallel execution with 2 concurrent workers
- Verifies rate limiting works correctly
- Checks that all runs complete successfully

**test_multiple_variations**
- Tests parameter variation system
- Creates 2x2 variation matrix
- Verifies correct number of runs generated

**test_batch_resume_functionality**
- Tests halt and resume capability
- Runs partial batch, then resumes
- Verifies state persistence works correctly

**test_cost_tracking**
- Validates cost tracking accuracy
- Checks per-run and total cost calculation
- Verifies cost data structure

**test_batch_analysis_integration**
- Tests BatchAnalyzer integration
- Runs batch then analyzes results
- Verifies analysis outputs and reports

**test_budget_limit_enforcement**
- Tests budget limit enforcement
- Sets low budget limit
- Verifies batch stops when limit reached

**test_output_directory_structure**
- Validates output directory organization
- Checks all expected files are created
- Verifies runs are organized correctly

### TestBatchWorkflow

**test_complete_research_workflow**
- Smoke test for component availability
- Verifies all classes can be imported
- No actual execution

## Running Tests

### Run All Tests

```bash
# All tests (including full integration)
python -m unittest tests.test_batch_integration -v

# Just fast tests
python -m unittest tests.test_batch_integration.TestBatchWorkflow -v
```

### Run Specific Test

```bash
python -m unittest tests.test_batch_integration.TestBatchIntegration.test_sequential_batch_execution -v
```

### Run with Coverage

```bash
# If you have coverage installed
coverage run -m unittest tests.test_batch_integration
coverage report
```

## Test Fixtures

Integration tests use a minimal test scenario created automatically:

- **Scenario:** 2 actors, 2 turns
- **Models:** openai/gpt-4o-mini (cost-effective)
- **Metrics:** Simple test metrics
- **Duration:** Fast execution (~30s per run)

Fixtures are created in a temporary directory and cleaned up after tests.

## Expected Behavior

### All Tests Should Pass

When running the full integration test suite, you should see:

```
test_batch_analysis_integration ... ok
test_budget_limit_enforcement ... ok
test_cost_tracking ... ok
test_multiple_variations ... ok
test_output_directory_structure ... ok
test_parallel_batch_execution ... ok
test_batch_resume_functionality ... ok
test_sequential_batch_execution ... ok
test_complete_research_workflow ... ok

----------------------------------------------------------------------
Ran 9 tests in 180.23s

OK
```

### Typical Runtime

- **Fast tests:** < 1 second
- **Full integration:** 2-5 minutes total
- **Per test:** 20-60 seconds each (with API calls)

### Typical Cost

- **Fast tests:** $0
- **Full integration:** ~$0.10-0.50 total
- Uses gpt-4o-mini which is very cost-effective

## Troubleshooting

### "ModuleNotFoundError"

Make sure you're running from the repository root:

```bash
cd /path/to/scenario-lab
python -m unittest tests.test_batch_integration -v
```

### "API Key Not Found"

Set up your `.env` file:

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### "Rate Limit Errors"

The tests include retry logic, but if you hit rate limits:

1. Wait a few minutes
2. Run tests again
3. Or run just fast tests: `python -m unittest tests.test_batch_integration.TestBatchWorkflow -v`

### Tests Time Out

If tests take too long:

1. Check network connection
2. Verify API key is valid
3. Check OpenRouter service status
4. Increase timeout in individual tests if needed

## CI/CD Integration

For continuous integration, you may want to:

1. **Skip integration tests by default:**
   ```yaml
   # Only run fast tests
   - python -m unittest tests.test_batch_integration.TestBatchWorkflow
   ```

2. **Run integration tests in separate job:**
   ```yaml
   # Nightly integration test run
   - python -m unittest tests.test_batch_integration.TestBatchIntegration
   ```

3. **Use environment variable to control:**
   ```python
   @unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), "Skipping integration tests")
   class TestBatchIntegration(unittest.TestCase):
       ...
   ```

## Adding New Integration Tests

When adding new tests:

1. Use `setUp()` to create fresh experiment directory
2. Use `tearDown()` to clean up
3. Use `self.test_scenario_dir` for test scenario
4. Keep tests independent (don't rely on other test state)
5. Use descriptive test names
6. Document expected runtime and cost

Example:

```python
def test_new_feature(self):
    """Test new batch feature (Runtime: 30s, Cost: ~$0.05)"""
    # Test implementation
    pass
```

## Performance Benchmarks

Expected performance on modern hardware:

| Test | Runtime | API Calls | Cost |
|------|---------|-----------|------|
| test_sequential_batch_execution | 40-60s | ~10 | $0.05 |
| test_parallel_batch_execution | 25-35s | ~10 | $0.05 |
| test_multiple_variations | 20-30s | ~5 | $0.02 |
| test_batch_resume_functionality | 60-90s | ~15 | $0.08 |
| test_cost_tracking | 40-60s | ~10 | $0.05 |
| test_batch_analysis_integration | 40-60s | ~10 | $0.05 |
| test_budget_limit_enforcement | 5-10s | ~2 | $0.01 |
| test_output_directory_structure | 20-30s | ~5 | $0.02 |

**Total:** 2-5 minutes, ~$0.30-0.50

## Future Improvements

Potential enhancements to integration tests:

- [ ] Add mocked LLM provider for faster testing
- [ ] Add performance regression tests
- [ ] Add load testing for parallel execution
- [ ] Add tests for edge cases and error recovery
- [ ] Add tests for very large batches (100+ runs)
- [ ] Add tests with different LLM providers
