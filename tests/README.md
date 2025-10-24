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

**Total:** 29 unit tests covering core framework components

## Test Organization

```
tests/
├── __init__.py
├── README.md
├── test_world_state.py          # World state management
├── test_communication_manager.py # Communication channels
├── test_context_manager.py       # Context windowing
└── test_cost_tracker.py          # Cost tracking
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

## What's Not Tested (Requires API Keys)

The following components require actual API calls and are tested manually:
- LLM integration (actor_engine.py _call_llm)
- World state synthesis (world_state_updater.py)
- Context summarization (context_manager.py _generate_summary)

These could be tested with:
- Mock objects for LLM responses
- Integration tests with test API keys
- Recorded response fixtures

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

**Integration Tests:**
- End-to-end scenario execution with mock LLMs
- State persistence and resumption
- Branching scenarios
- Coalition formation workflows

**Performance Tests:**
- Large scenario handling
- Memory usage with many turns
- Token counting accuracy

**Validation Tests:**
- YAML scenario file validation
- Actor configuration validation
- Metric extraction accuracy
