# V2 Rewrite Completion Plan

**Date:** 2025-11-20
**Status:** PLANNING

---

## Background

V2 migration is **partially complete** but contains hybrid V1/V2 architecture that causes integration bugs.

**Original Vision:** V2 should be a **clean rewrite from scratch**, not V1 code copied into `scenario_lab/`.

**Current Reality:** `scenario_lab/` contains mix of:
- ✅ Pure V2 components (decision_phase_v2, world_update_phase_v2, schemas, loaders)
- ❌ V1 components copied without updating (metrics_tracker, context_manager, qa_validator)

**Result:** Schema incompatibilities, parameter mismatches, 11 bugs found in Phase 6.4 QA.

---

## Goal

**Complete V2 rewrite** by replacing all V1-copied components with clean V2-native implementations.

**Success Criteria:**
1. Zero V1 code in `scenario_lab/`
2. All components use V2 patterns (immutable state, async, Pydantic schemas)
3. Integration tests pass end-to-end
4. No schema conversion/adapter layers needed

---

## V1 Components That Need V2 Rewrites

### 1. MetricsTracker (CRITICAL - BUG-011)

**Current:** `scenario_lab/core/metrics_tracker.py` (V1-copied)
- Expects V1 dict-based metrics format
- Mutable state pattern
- Direct YAML loading

**V2 Rewrite Required:**
```python
# File: scenario_lab/core/metrics_tracker_v2.py

class MetricsTrackerV2:
    """V2-native metrics tracker using V2 schemas"""

    def __init__(self, metrics_config: MetricsConfig):
        """
        Args:
            metrics_config: Pydantic MetricsConfig from scenario_lab.schemas.metrics
        """
        self.metrics = {m.name: m for m in metrics_config.metrics}  # Convert list to dict
        self.export_format = metrics_config.export_format

    def extract_metrics_from_state(self, state: ScenarioState) -> Dict[str, Any]:
        """
        Extract metrics from immutable state

        Uses V2 extraction patterns (llm, pattern, keyword)
        Returns dict of metric_name -> value
        """
        pass
```

**Key Changes:**
- Takes Pydantic `MetricsConfig` not raw YAML
- Works with immutable `ScenarioState`
- Supports V2 extraction types (llm, pattern, keyword)
- No internal mutable state

**Priority:** HIGH (blocks scenarios with metrics)

---

### 2. ContextManager (MEDIUM PRIORITY)

**Current:** `scenario_lab/core/context_manager.py` (V1-copied)
- Works but uses V1 patterns
- window_size can be None (BUG-010 root cause)

**V2 Rewrite Required:**
```python
# File: scenario_lab/core/context_manager_v2.py

class ContextManagerV2:
    """V2-native context windowing"""

    def __init__(self, window_size: int = 3, summarization_model: str = "openai/gpt-4o-mini"):
        """
        Args:
            window_size: Must be > 0 (validated)
            summarization_model: Model for summaries
        """
        if window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {window_size}")
        self.window_size = window_size
        self.summarization_model = summarization_model

    async def get_context_for_actor(
        self,
        actor_name: str,
        state: ScenarioState
    ) -> str:
        """Pure async function - no mutable state"""
        pass
```

**Key Changes:**
- Validate parameters in __init__ (no None values)
- Pure async functions
- No internal cache (if needed, use external cache)

**Priority:** MEDIUM (works but fragile)

---

### 3. QAValidator (MEDIUM PRIORITY)

**Current:** `scenario_lab/core/qa_validator.py` (partially V2)
- Uses V2 async patterns
- But has V1-style parameter handling

**V2 Rewrite Required:**
```python
# File: scenario_lab/core/qa_validator_v2.py

class QAValidatorV2:
    """V2-native quality assurance validator"""

    def __init__(self, validation_config: ValidationConfig):
        """
        Args:
            validation_config: Pydantic ValidationConfig from scenario_lab.schemas.validation
        """
        self.config = validation_config
        self.validation_model = validation_config.validation_model

    async def validate_turn(self, state: ScenarioState) -> List[ValidationResult]:
        """
        Validate a turn from immutable state

        Returns list of ValidationResult dataclasses
        """
        pass
```

**Key Changes:**
- Takes Pydantic `ValidationConfig`
- Works with immutable state
- Returns structured ValidationResult objects

**Priority:** MEDIUM (works but inconsistent API)

---

### 4. Communication Manager (LOW PRIORITY)

**Current:** `scenario_lab/core/communication_manager.py`
- Seems mostly V2-compatible
- Needs audit for V1 patterns

**Action:** Audit and refactor if needed

**Priority:** LOW

---

## V2 Design Patterns (Required)

All V2 components MUST follow these patterns:

### 1. Immutable State
```python
# ❌ V1 Pattern - Mutation
def process(self, state):
    state.decisions.append(new_decision)  # Mutates
    return state

# ✅ V2 Pattern - Immutable
def process(self, state: ScenarioState) -> ScenarioState:
    return state.with_decision(actor_name, decision)  # Returns new state
```

### 2. Pydantic Schemas
```python
# ❌ V1 Pattern - Raw dicts/YAML
def __init__(self, config_path: str):
    with open(config_path) as f:
        self.config = yaml.safe_load(f)

# ✅ V2 Pattern - Pydantic
def __init__(self, config: MetricsConfig):
    self.config = config  # Already validated by Pydantic
```

### 3. Async by Default
```python
# ❌ V1 Pattern - Sync
def make_llm_call(self, prompt):
    return requests.post(...)

# ✅ V2 Pattern - Async
async def make_llm_call_async(self, prompt):
    async with aiohttp.ClientSession() as session:
        return await session.post(...)
```

### 4. Dataclasses for Results
```python
# ❌ V1 Pattern - Dicts
def validate(self) -> dict:
    return {"passed": True, "issues": []}

# ✅ V2 Pattern - Dataclasses
@dataclass
class ValidationResult:
    passed: bool
    issues: List[str]

def validate(self) -> ValidationResult:
    return ValidationResult(passed=True, issues=[])
```

### 5. No sys.path Manipulation
```python
# ❌ V1 Pattern
sys.path.insert(0, "src/")
from some_module import func

# ✅ V2 Pattern
from scenario_lab.module import func
```

---

## Implementation Plan

### Phase 1: MetricsTracker Rewrite (CRITICAL)

**Goal:** Fix BUG-011, enable scenarios with metrics

**Tasks:**
1. Create `scenario_lab/core/metrics_tracker_v2.py`
2. Implement MetricsTrackerV2 class
   - Constructor takes `MetricsConfig` from Pydantic
   - Convert metrics list to dict internally
   - Implement extraction for all V2 types (llm, pattern, keyword)
3. Update `sync_runner.py` to use MetricsTrackerV2
4. Write integration test: scenario with metrics runs end-to-end
5. Delete old `metrics_tracker.py` (or move to src/)

**Acceptance:**
- `python -m scenario_lab.interfaces.cli run scenarios/ai-negotiation-test-scenario --end-turn 2` completes successfully

**Estimated Effort:** 2-3 hours

---

### Phase 2: ContextManager Rewrite

**Goal:** Clean V2 implementation with proper validation

**Tasks:**
1. Create `scenario_lab/core/context_manager_v2.py`
2. Add parameter validation (__init__ raises on invalid)
3. Make all methods pure async functions
4. Update DecisionPhaseV2 to use ContextManagerV2
5. Write unit tests for context windowing
6. Delete old context_manager.py

**Acceptance:**
- Context windowing works correctly
- No None-value bugs
- Tests pass

**Estimated Effort:** 1-2 hours

---

### Phase 3: QAValidator Rewrite

**Goal:** Consistent V2 API

**Tasks:**
1. Create `scenario_lab/core/qa_validator_v2.py`
2. Take ValidationConfig in constructor
3. Return structured ValidationResult objects
4. Update sync_runner.py
5. Write tests
6. Delete old qa_validator.py

**Acceptance:**
- QA validation works with V2 patterns
- Tests pass

**Estimated Effort:** 1-2 hours

---

### Phase 4: Integration Tests

**Goal:** Prevent regression

**Tasks:**
1. Create `tests/test_v2_end_to_end.py`
2. Add smoke test: simple scenario runs without error
3. Add schema compatibility tests
4. Add CLI command tests
5. Ensure 100% of V2 components covered

**Tests Needed:**
```python
def test_scenario_runs_end_to_end():
    """Smoke test - scenario completes without errors"""
    pass

def test_scenario_with_metrics():
    """Scenario with metrics.yaml completes"""
    pass

def test_scenario_with_validation():
    """Scenario with validation-rules.yaml completes"""
    pass

def test_cli_validate_command():
    """CLI validate works on valid scenario"""
    pass

def test_cli_estimate_command():
    """CLI estimate returns cost estimate"""
    pass
```

**Acceptance:**
- All integration tests pass
- Coverage >80% for V2 components

**Estimated Effort:** 3-4 hours

---

### Phase 5: Remove V1 Code (FINAL)

**Goal:** Clean codebase

**Tasks:**
1. Delete or archive `src/` directory entirely
2. Update .gitignore if needed
3. Remove all V1 tests from `tests/`
4. Update README/CLAUDE.md to remove V1 references
5. Git commit: "Complete V2 migration - remove all V1 code"

**Acceptance:**
- Zero references to `src/` in codebase
- All tests pass
- Documentation up to date

**Estimated Effort:** 1 hour

---

## Success Metrics

**Before (current state):**
- ❌ 11 bugs found in QA
- ❌ Scenarios crash with metrics
- ❌ V1/V2 hybrid architecture
- ❌ 40 test failures
- ❌ Integration test gap

**After (completion):**
- ✅ Zero critical bugs
- ✅ All scenarios run end-to-end
- ✅ Pure V2 architecture
- ✅ All tests pass
- ✅ Integration tests cover major workflows

---

## Timeline Estimate

**Total Effort:** 8-12 hours

**Breakdown:**
- Phase 1 (MetricsTracker): 2-3 hours
- Phase 2 (ContextManager): 1-2 hours
- Phase 3 (QAValidator): 1-2 hours
- Phase 4 (Integration Tests): 3-4 hours
- Phase 5 (Cleanup): 1 hour

**Can be split across multiple sessions.**

---

## Next Session Checklist

When you're ready to continue:

1. **Start with Phase 1 (MetricsTracker)**
   - Creates immediate value (fixes BUG-011)
   - Unblocks scenario execution
   - Good warm-up for V2 patterns

2. **Test incrementally**
   - After each phase, run: `python -m scenario_lab.interfaces.cli run scenarios/ai-negotiation-test-scenario --end-turn 2`
   - Verify one more thing works

3. **Commit after each phase**
   - Small, focused commits
   - Easy to review and rollback if needed

4. **Don't rush**
   - V2 rewrite is about **quality**, not speed
   - Take time to get patterns right
   - Write tests as you go

---

## Questions to Consider

Before starting, discuss:

1. **Keep V1 code?**
   - Archive in `src/` directory?
   - Delete entirely?
   - Move to separate branch?

2. **Test strategy?**
   - Write tests first (TDD)?
   - Write tests alongside?
   - Integration tests vs unit tests priority?

3. **Breaking changes?**
   - Can we change APIs during rewrite?
   - Need backward compatibility?

4. **Documentation?**
   - Update docs as we rewrite?
   - Or big doc update at end?

---

## Reference: V2 Architecture Principles

**From original V2 design:**

1. **Event-driven:** All phase transitions emit events
2. **Immutable state:** ScenarioState is frozen dataclass
3. **Async by default:** All LLM calls, all phases use async/await
4. **Type-safe:** Pydantic everywhere for validation
5. **Testable:** Dependency injection, pure functions
6. **Observable:** EventBus for monitoring
7. **Modular:** Phases are pluggable services

**These principles should guide all rewrites.**

---

## Conclusion

V2 migration will be complete when:
- ✅ All components in `scenario_lab/` are pure V2
- ✅ Zero V1 code in codebase
- ✅ Integration tests prove it works end-to-end
- ✅ No schema adapters or conversion layers needed

**Start tomorrow with Phase 1 (MetricsTracker rewrite).** That alone will fix the most critical blocker and demonstrate the V2 pattern correctly.
