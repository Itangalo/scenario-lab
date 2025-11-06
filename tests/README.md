# Scenario Lab Test Suite

Automated tests for core Scenario Lab components.

## Running Tests

### Run all tests

```bash
python run_tests.py
```

### Run in quiet mode

```bash
python run_tests.py --quiet
```

### Run specific test file

```bash
python -m unittest tests.test_world_state
```

### Run specific test case

```bash
python -m unittest tests.test_world_state.TestWorldState.test_initialization
```

## Test Coverage

### Unit Tests

**test_world_state.py** (8 tests)
- WorldState initialization
- State updates and retrieval
- Actor decision recording
- Markdown generation

**test_communication_manager.py** (10 tests)
- Channel creation (bilateral, coalition)
- Message sending
- Visibility rules
- Channel serialization
- Duplicate prevention

**test_context_manager.py** (5 tests)
- Context windowing
- History formatting
- Cache management
- Cost estimation

**test_cost_tracker.py** (6 tests)
- Cost recording (actors and world state)
- Multi-turn and multi-actor tracking
- JSON export
- Cost estimation

**test_qa_validator.py** (13 tests)
- QA validator initialization
- Validation check parsing
- Actor decision consistency checks
- World state coherence validation
- Information access validation
- Report generation
- Cost tracking for validation

**test_scenario_wizard.py** (6 tests)
- Helper function validation (colors, models)
- Scenario file structure creation
- Actor YAML file generation
- Metrics configuration
- Complete scenario structure validation

**test_response_cache.py** (28 tests)
- Cache key generation
- In-memory and disk caching
- TTL and eviction
- Cache statistics
- Thread safety

**test_error_handler.py** (28 tests)
- Error categorization (10 categories)
- Severity levels
- Recovery suggestions
- User-friendly messaging

**test_progressive_fallback.py** (28 tests)
- Model fallback chains
- Conditional fallback logic
- Fallback tracking

**test_graceful_fallback.py** (24 tests)
- Graceful degradation without optional dependencies
- Console, progress, table fallbacks

**test_api_utils.py** (27 tests)
- API retry logic
- Local LLM support (Ollama)
- Connection pooling
- Error handling

**test_api_error_handling.py** (11 tests)
- HTTP error retry
- Rate limiting
- Network error recovery
- Context tracking

**test_integration.py** (5 tests)
- Full scenario execution
- Resumption workflow
- Branching workflow
- Bilateral communications
- Credit limit enforcement

**Total:** 177 tests covering all major framework components

## Test Organization

```
tests/
├── __init__.py
├── README.md
├── test_world_state.py              # World state management
├── test_communication_manager.py     # Communication channels
├── test_context_manager.py           # Context windowing
├── test_cost_tracker.py              # Cost tracking
├── test_qa_validator.py              # Quality assurance validation
├── test_scenario_wizard.py           # Scenario creation wizard
├── test_response_cache.py            # Response caching
├── test_error_handler.py             # Error handling
├── test_progressive_fallback.py      # Progressive fallback
├── test_graceful_fallback.py         # Graceful degradation
├── test_api_utils.py                 # API utilities
├── test_api_error_handling.py        # API error handling
├── test_integration.py               # End-to-end integration tests
├── test_metrics_tracker.py           # Metrics tracking
├── test_response_parser.py           # Response parsing
├── test_world_state_updater.py       # World state updates
└── test_markdown_utils.py            # Markdown utilities
```

## Writing New Tests

Follow the existing test structure:

```python
import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from your_module import YourClass


class TestYourClass(unittest.TestCase):
    """Test YourClass functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.instance = YourClass()

    def test_feature(self):
        """Test specific feature"""
        result = self.instance.do_something()
        self.assertEqual(result, expected_value)


if __name__ == '__main__':
    unittest.main()
```

**test_batch_runner.py** (18 tests)
- ParameterVariator: variation generation, Cartesian products
- BatchCostManager: budget limits, cost tracking
- Variation statistics and cost management

### Integration Tests

**test_batch_integration.py** (9 tests)
- Complete batch execution workflows (sequential & parallel)
- Resume functionality
- Cost tracking and budget enforcement
- Batch analysis pipeline integration
- Output directory structure validation

**⚠️  Note:** Integration tests make real LLM API calls and require:
- Valid OpenRouter API key in `.env`
- Network connection
- Runtime: 2-5 minutes
- Cost: ~$0.10-0.50

See [INTEGRATION_TESTS.md](INTEGRATION_TESTS.md) for detailed documentation.

### Fast vs. Slow Tests

**Fast Tests (Unit Tests):** No API calls, < 1 second
```bash
python run_tests.py
```

**Slow Tests (Integration):** Real API calls, 2-5 minutes
```bash
python -m unittest tests.test_batch_integration -v
```

## What's Not Tested (Requires API Keys)

The following components require actual API calls in production:
- LLM integration (actor_engine.py _call_llm)
- World state synthesis (world_state_updater.py)
- Context summarization (context_manager.py _generate_summary)

**Integration tests now cover these** with real API calls for end-to-end validation.

## Continuous Integration

To add CI testing (GitHub Actions, etc.):

1. Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py
```

2. Commit and push - tests will run automatically

## Future Test Additions

**Integration Tests:** ✅ IMPLEMENTED
- ✅ End-to-end batch execution
- ✅ State persistence and resumption
- ✅ Parallel execution workflows
- ⏸️  Branching scenarios (single runs)
- ⏸️  Coalition formation workflows (needs real API testing)
- ⏸️  Mock LLM provider for faster testing

**Performance Tests:**
- Large scenario handling (100+ runs)
- Memory usage with many turns
- Parallel execution scaling
- Rate limit handling under load

**Validation Tests:**
- YAML scenario file validation (partially in schemas.py)
- Actor configuration validation (partially in schemas.py)
- Metric extraction accuracy
