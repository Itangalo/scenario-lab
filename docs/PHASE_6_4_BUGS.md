# Phase 6.4: Manual QA - Bugs and Issues

**Date**: 2025-11-20
**Status**: IN PROGRESS

---

## Overview

This document tracks bugs and issues discovered during Phase 6.4 manual QA testing.

---

## Critical Bugs

### BUG-001: CLI wizard commands fail (src/ directory missing)

**Status**: 🔴 CRITICAL - Blocks scenario creation via CLI

**Commands affected:**
- `python -m scenario_lab.interfaces.cli create`
- `python -m scenario_lab.interfaces.cli create-batch`

**Error:**
```
create_scenario_interactive() takes 0 positional arguments but 1 was given
```

**Root cause:**
1. Phase 6.1 removed the `src/` directory containing V1 wizard code
2. CLI commands in `scenario_lab/interfaces/cli.py` (lines 480-512) still attempt to load wizards from `src/`:
   ```python
   sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
   from create_scenario import create_scenario_interactive
   ```
3. Additionally, the wizard function signature mismatch: CLI passes `output_dir` argument, but function takes no arguments

**Impact:**
- Users cannot create new scenarios via CLI wizard
- Documentation instructs users to use `scenario-lab create` (which fails)

**Workaround:**
Manual scenario creation:
1. Copy existing scenario: `cp -r scenarios/ai-negotiation-test-scenario scenarios/new-scenario`
2. Edit YAML files manually in editor
3. Validate: `python -m scenario_lab.interfaces.cli validate scenarios/new-scenario`

**Fixes required:**

**Option A - Quick fix (restore V1 wizards):**
1. Restore wizard files from git history to `src/`
2. Fix function signature mismatch (add `output_dir` parameter)
3. Update CLI bridge code if needed

**Option B - Proper fix (V2-native wizards):**
1. Implement new wizard in `scenario_lab/wizards/scenario_wizard.py`
2. Use V2 schemas and validation (scenario_lab.schemas.*)
3. Update CLI to use V2 wizard
4. Remove sys.path.insert hack

**Recommendation:** Option A for immediate unblocking, Option B for long-term

**Files:**
- `scenario_lab/interfaces/cli.py:480-512` (create command)
- `scenario_lab/interfaces/cli.py:516-571` (create-batch command)
- Missing: `src/create_scenario.py`
- Missing: `src/create_batch_config.py`

---

## Schema Validation Issues

### BUG-002: Actor name validation too strict

**Status**: 🟡 MEDIUM - Requires manual fixes

**Issue:**
Actor names and short_names must be lowercase with hyphens (pattern: `^[a-z0-9-]+$`), but wizard and examples don't enforce this.

**Example:**
- Actor file named `CCP.yaml` → fails validation
- Actor with `short_name: CCP` → fails validation
- Must be: `ccp.yaml` with `short_name: ccp`

**Error message:**
```
✗ Scenario
  ✗ actors: Value error, Actor name 'CCP' should be lowercase with hyphens (e.g., 'united-states')
✗ Actors
  ✗ CCP.yaml: short_name: String should match pattern '^[a-z0-9-]+$'
```

**Impact:**
- Existing scenarios may fail validation
- Non-intuitive naming convention for proper nouns (e.g., CCP, EU, NATO)

**Workaround:**
Manually fix actor files:
1. Rename file: `mv actors/CCP.yaml actors/ccp.yaml`
2. Edit file: change `short_name: CCP` to `short_name: ccp`
3. Update `scenario.yaml`: change actor reference from `CCP` to `ccp`

**Fixes required:**
1. Update wizard to enforce lowercase conversion
2. Add helpful error messages suggesting correct format
3. Consider: Allow uppercase in display name but auto-convert short_name?

**Files:**
- `scenario_lab/schemas/scenario.py` - Name validation pattern
- `scenario_lab/schemas/actor.py` - short_name validation

---

### BUG-003: Metrics YAML format incompatible with V2 schema

**Status**: 🟡 MEDIUM - Breaking change from V1 to V2

**Issue:**
V1 metrics format (dict-based) incompatible with V2 schema (list-based).

**V1 format (fails in V2):**
```yaml
scenario_name: AI Safety Policy Negotiation
metrics:
  willingness_to_negotiate:
    description: ...
    type: integer
    extraction_method: regex
```

**V2 format (required):**
```yaml
metrics:
  - name: willingness_to_negotiate
    description: ...
    type: continuous
    range: [0, 10]
    extraction:
      type: pattern
      pattern: '...'
```

**Key differences:**
1. Top-level: dict → list
2. Metric name: dict key → `name` field
3. Type: `integer` → `continuous` with `range`
4. Extraction: `extraction_method: regex` → nested `extraction: {type: pattern}`
5. No `scenario_name` field in V2

**Error message:**
```
✗ Metrics
  ✗ metrics: Input should be a valid list
```

**Impact:**
- All V1 scenarios with metrics fail validation
- Migration path unclear for users

**Workaround:**
Manual conversion (see scenarios/ai-negotiation-test-scenario/metrics.yaml for example)

**Fixes required:**
1. Document migration guide for metrics.yaml
2. Update wizard to generate V2 format
3. Consider: Auto-migration tool or helpful error messages with conversion hints

**Files:**
- `scenario_lab/schemas/metrics.py` - V2 schema definition
- All existing scenarios with metrics.yaml

---

## Test Suite Issues

### BUG-004: pytest-asyncio missing from requirements

**Status**: 🟡 MEDIUM - Missing development dependency

**Issue:**
Test suite requires `pytest-asyncio` but it's not in `requirements.txt` or any requirements file.

**Error:**
```
Failed: async def functions are not natively supported.
```

**Impact:**
- 26 async tests fail without the package
- New developers cannot run tests without manual package installation

**Workaround:**
```bash
pip install pytest-asyncio
```

**Fix required:**
Create `requirements-dev.txt`:
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

**Files to create:**
- `requirements-dev.txt`

---

## Test Results Summary

**Test run**: 2025-11-20

**Results:**
- ✅ 310 tests passed
- ❌ 40 tests failed
- ⚠️ 119 warnings
- 🔴 8 errors

**Failure categories:**
1. **Async tests** (26) - Fixed with pytest-asyncio installation
2. **API tests** (6) - Expected (require external services: OpenRouter API, Ollama)
3. **Database tests** (8) - Database.close() method missing
4. **V1 component tests** - Expected (V1 src/ directory no longer exists)

**Status:** Test failures are expected and documented in PHASE_6_2_TEST_STATUS.md. Core V2 functionality tests pass.

---

### BUG-005: Incorrect "expensive model" warning for gpt-4o-mini

**Status**: 🟡 LOW - Cosmetic issue, causes confusion

**Issue:**
Actor validation warns that `gpt-4o-mini` is expensive and suggests using `gpt-4o-mini` instead.

**Error message:**
```
⚠ Actors
  ⚠ us-government.yaml: Using expensive model (openai/gpt-4o-mini) - consider gpt-4o-mini for testing
  ⚠ ccp.yaml: Using expensive model (openai/gpt-4o-mini) - consider gpt-4o-mini for testing
```

**Root cause:**
`scenario_lab/schemas/loader.py:136-137`:
```python
if config.llm_model and 'gpt-4' in config.llm_model.lower():
    warnings.append(f"Using expensive model ({config.llm_model}) - consider gpt-4o-mini for testing")
```

The check uses substring matching `'gpt-4' in model_name`, which matches:
- ✅ `gpt-4` (expensive - correct warning)
- ✅ `gpt-4-turbo` (expensive - correct warning)
- ❌ `gpt-4o-mini` (CHEAP - false positive!)

**Impact:**
- Confusing warning messages
- Users may think they're using expensive models when they're not

**Fix:**
Replace substring check with explicit model list or better pattern matching:

```python
# Option 1: Explicit expensive models list
EXPENSIVE_MODELS = ['gpt-4', 'gpt-4-turbo', 'gpt-4-32k', 'claude-opus']
if config.llm_model and any(m in config.llm_model for m in EXPENSIVE_MODELS):
    if 'mini' not in config.llm_model.lower():  # Exclude mini variants
        warnings.append(...)

# Option 2: Exclude mini explicitly
if config.llm_model and 'gpt-4' in config.llm_model.lower() and 'mini' not in config.llm_model.lower():
    warnings.append(...)
```

**Files:**
- `scenario_lab/schemas/loader.py:136-137`

---

### BUG-011: MetricsTracker incompatible with V2 metrics schema

**Status**: 🔴 CRITICAL - Blocks scenario execution when metrics.yaml present

**Issue:**
MetricsTracker (V1 code) expects metrics to be a dict, but V2 schema uses a list.

**Error:**
```
AttributeError: 'list' object has no attribute 'items'
  File "scenario_lab/core/metrics_tracker.py", line 86
    for metric_name, metric_def in self.metrics_definitions.items():
```

**Root cause:**
V1 metrics format (dict-based):
```yaml
metrics:
  willingness_to_negotiate:
    description: ...
    type: integer
```

V2 metrics format (list-based):
```yaml
metrics:
  - name: willingness_to_negotiate
    description: ...
    type: continuous
    range: [-10, 10]
```

MetricsTracker loads YAML and expects `config.get('metrics', {})` to be a dict, but V2 schema makes it a list.

**Location:**
- `scenario_lab/core/metrics_tracker.py:86` - Iterates with `.items()`
- `scenario_lab/core/metrics_tracker.py:58` - Loads as dict: `self.metrics_definitions = config.get('metrics', {})`

**Impact:**
- Scenarios with metrics.yaml fail after Decision phase completes
- Decisions are successfully recorded before crash
- Cost tracking works ($0.0008 for 2 actors, ~2,500 tokens)

**Workaround:**
Remove or rename metrics.yaml to skip metrics tracking

**Fix required:**
Update MetricsTracker to handle V2 list-based format:
```python
# Convert list to dict for compatibility
metrics_list = config.get('metrics', [])
self.metrics_definitions = {m['name']: m for m in metrics_list}
```

Or: Rewrite MetricsTracker as V2-native component

**Files:**
- `scenario_lab/core/metrics_tracker.py:58, 86`

---

## Additional Findings

### Finding-001: setup.py installation incomplete

**Issue:**
`pip install -e .` doesn't properly register CLI commands. Users must use `python -m scenario_lab.interfaces.cli` instead of `scenario-lab`.

**Impact:**
- Documentation shows `scenario-lab` commands
- Actual command is `python -m scenario_lab.interfaces.cli`
- User confusion

**Investigation needed:**
Check `setup.py` entry_points configuration.

---

## Next Steps

### Immediate (Phase 6.4 completion)

1. ✅ Document bugs (this file)
2. ⏳ Fix BUG-001 (wizard) - Option A (restore from git)
3. ⏳ Fix BUG-004 (requirements-dev.txt)
4. ⏳ Test scenario execution end-to-end with manual scenario
5. ⏳ Update Phase 6.4 completion criteria

### Post-Phase 6

1. Fix BUG-002 (schema validation) - update wizard
2. Fix BUG-003 (metrics migration) - create migration guide
3. Implement V2-native wizards (BUG-001 Option B)
4. Fix Finding-001 (setup.py)
5. Rewrite V2 integration tests

---

## Summary

**Critical blockers:** 2 (BUG-001, BUG-011)
**Fixed in session:** 5 (BUG-006 through BUG-010)
**Medium issues:** 3 (BUG-002, BUG-003, BUG-004)
**Low priority:** 1 (BUG-005)
**Findings:** 1 (Finding-001)

**Total bugs found:** 11 (5 fixed, 6 remaining)

V2 migration is functionally incomplete due to V1/V2 incompatibilities (metrics schema, wizard missing). Core execution works but hits schema mismatches.

---

## Test Coverage Analysis

### Problem: Integration Test Gap

The project has **310 passing unit tests** but **lacks integration tests** that would have caught these bugs:

**What unit tests cover:**
- ✅ Individual component logic (decision parsing, cost calculation, etc.)
- ✅ V1 component behavior
- ✅ Schema validation with valid inputs

**What unit tests miss:**
- ❌ V2 end-to-end execution flow
- ❌ Component integration (how phases wire together)
- ❌ Schema compatibility between loader and consumers
- ❌ Default value handling (Pydantic model_dump() behavior)
- ❌ Parameter passing between CLI → Runner → Phases

### Root Cause: V1/V2 Hybrid

The bugs stem from **V1 code consuming V2 schemas**:

1. **BUG-006-010**: Parameter mismatches - V2 CLI calling V1-style components
2. **BUG-011**: Schema incompatibility - MetricsTracker (V1) vs metrics.yaml (V2)
3. **BUG-001**: Wizard missing - Removed src/ but CLI still references it

### What's Missing: Integration Tests

**Needed tests:**
```python
def test_scenario_execution_end_to_end():
    """Test full scenario from CLI to output files"""
    # Would have caught BUG-006 through BUG-011
    runner = SyncRunner("scenarios/test")
    runner.setup()
    result = asyncio.run(runner.run())
    assert result.turn > 0
    assert len(result.decisions) > 0
```

```python
def test_v2_schema_compatibility():
    """Test V2 schemas work with all consumers"""
    # Would have caught BUG-011
    loader = ScenarioLoader("scenarios/test")
    state, actors, config = loader.load()

    # Test MetricsTracker can load V2 metrics
    metrics_tracker = MetricsTracker(Path("scenarios/test/metrics.yaml"))
    metrics = metrics_tracker.extract_metrics_from_decisions(state)
```

**Current test suite status:**
- 20 V1 component tests (obsolete after src/ removal)
- 2 V2 integration tests (broken, need V2 API mocking)
- 5 V2-native tests (pass but don't cover integration)

### Recommendation

**Short-term (Phase 6.4):**
1. Add smoke test: `test_simple_scenario_runs_without_error()`
2. Test each CLI command with real scenario
3. Manual QA checklist (what we did today)

**Long-term (Post-Phase 6):**
1. Rewrite V2 integration tests with proper mocking
2. Add end-to-end tests for each major workflow
3. Add schema compatibility tests
4. Consider contract tests between V2 components
5. Remove obsolete V1 tests when src/ is deleted

**The core issue:** Migration changed schemas (V1 → V2) but didn't update all consumers (MetricsTracker, wizards, etc.). Integration tests would catch this immediately.
