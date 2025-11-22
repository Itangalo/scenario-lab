# Scenario Lab Test Suite (V2)

Automated tests for Scenario Lab V2 components.

## Running Tests

### Run all tests

```bash
pytest tests/
```

Or with unittest:

```bash
python -m pytest tests/ -v
```

### Run specific test file

```bash
pytest tests/test_v2_smoke.py -v
```

### Run specific test case

```bash
pytest tests/test_v2_phases.py::TestDecisionPhaseV2::test_decision_phase_initialization -v
```

## Test Coverage

### V2 Core Tests

**test_v2_smoke.py** - Quick smoke tests verifying V2 components load correctly

**test_v2_phases.py** - Phase service tests:
- Decision phase V2 (actor decision-making)
- World update phase V2 (state synthesis)
- Communication phase
- Phase orchestration

**test_context_manager_v2.py** - Context management:
- Context windowing with validation
- History formatting
- Parameter validation (prevents BUG-010)

**test_metrics_tracker_v2.py** - Metrics tracking V2:
- Pydantic schema-based configuration
- Pattern, keyword, and LLM extraction methods
- Async metrics extraction

**test_async_executor.py** - Async execution:
- Concurrent actor decisions
- Rate limiting
- Error handling

**test_exogenous_events.py** - Background events:
- Event loading and validation
- Scheduled, conditional, random events
- Event triggering logic

**test_database_analytics.py** - Database integration:
- Scenario persistence
- Analytics queries
- Run comparison

**test_cli_wizards.py** - CLI interface tests

## Test Organization

```
tests/
├── __init__.py
├── README.md
├── test_v2_smoke.py              # Quick V2 component verification
├── test_v2_phases.py             # Phase service tests
├── test_context_manager_v2.py    # Context management
├── test_metrics_tracker_v2.py    # Metrics tracking
├── test_async_executor.py        # Async execution
├── test_exogenous_events.py      # Background events
├── test_database_analytics.py    # Database integration
└── test_cli_wizards.py           # CLI tests
```

Additional tests are in `scenario_lab/tests/`:

```
scenario_lab/tests/
├── test_orchestrator.py          # Orchestration tests
├── test_state.py                 # State model tests
└── test_events.py                # Event bus tests
```

## Writing New Tests

Follow the V2 test structure (use scenario_lab imports, not sys.path):

```python
import pytest
from unittest.mock import Mock, patch

from scenario_lab.core.context_manager import ContextManagerV2
from scenario_lab.models.state import ScenarioState


class TestYourFeature:
    """Test your feature"""

    def test_feature(self):
        """Test specific feature"""
        # Arrange
        manager = ContextManagerV2(max_tokens=1000)

        # Act
        result = manager.do_something()

        # Assert
        assert result == expected_value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## Integration Tests

Integration tests that require API keys are marked and can be run separately:

```bash
# Skip integration tests
pytest tests/ -m "not integration"

# Run only integration tests (requires API key)
pytest tests/ -m "integration"
```

## Continuous Integration

For CI testing (GitHub Actions):

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
          pip install -e .
          pip install pytest
      - name: Run tests
        run: pytest tests/ -v
```
