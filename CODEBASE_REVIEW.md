# Codebase Review - Pre-Phase 4

Comprehensive review of Scenario Lab codebase before starting Phase 4 (Batch Processing).

**Date:** October 2025
**Current Status:** Phase 2 complete (v0.3)

---

## Executive Summary

The codebase is in **good shape overall** but would benefit from:
1. **Test coverage** for new utility modules (HIGH priority)
2. **Refactoring** of run_scenario.py (MEDIUM priority)
3. **Minor cleanups** and consistency improvements (LOW priority)

**Recommendation:** Add tests for new modules, then proceed to Phase 4. Refactoring can wait.

---

## Test Coverage Analysis

### ✅ Well-Tested Modules (29 passing tests)

| Module | Tests | Status |
|--------|-------|--------|
| world_state.py | 8 tests | ✅ Complete |
| communication_manager.py | 10 tests | ✅ Complete |
| context_manager.py | 5 tests | ✅ Complete |
| cost_tracker.py | 6 tests | ✅ Complete |

### ⚠️ Untested Modules

| Module | Lines | Priority | Risk |
|--------|-------|----------|------|
| **response_parser.py** | 298 | **HIGH** | Recently added, complex regex logic |
| **api_utils.py** | 110 | **HIGH** | Critical for reliability |
| **markdown_utils.py** | 136 | **MEDIUM** | Recently added, text processing |
| **actor_engine.py** | 558 | **MEDIUM** | Large, but stable |
| metrics_tracker.py | 200 | LOW | Simple, regex-based |
| scenario_state_manager.py | 163 | LOW | Straightforward serialization |
| world_state_updater.py | 211 | LOW | Simple LLM wrapper |

### 🎯 Testing Priorities

**Before Phase 4, add tests for:**

1. **response_parser.py** (HIGH)
   - Test extract_section() with various formats
   - Test parse_actor_decision() with malformed inputs
   - Test all format variations discovered during testing
   - **Estimated effort:** 2-3 hours

2. **api_utils.py** (HIGH)
   - Test retry logic with mocked failures
   - Test exponential backoff timing
   - Test max retries behavior
   - **Estimated effort:** 1-2 hours

3. **markdown_utils.py** (MEDIUM)
   - Test duplicate detection and removal
   - Test section normalization
   - Test validation logic
   - **Estimated effort:** 1-2 hours

**Total testing effort:** 4-7 hours

---

## Code Quality Issues

### 1. Large Function in run_scenario.py

**Issue:** The `run_scenario()` function is ~640 lines (lines 60-698).

**Impact:**
- Hard to understand
- Difficult to test in isolation
- Fragile - changes can break unrelated parts

**Recommended Refactoring:**

Split into smaller functions:
```python
def execute_turn(turn, actors, world_state, communication_manager, ...):
    """Execute a single turn"""
    execute_private_communications(actors, ...)
    execute_coalition_formation(actors, ...)
    execute_public_actions(actors, ...)
    synthesize_world_state(world_state, ...)
    save_turn_outputs(...)

def execute_private_communications(...):
    """Phase 1: Private communications"""
    # Extract bilateral logic

def execute_coalition_formation(...):
    """Coalition formation logic"""
    # Extract coalition logic

def execute_public_actions(...):
    """Phase 2: Public actions"""
    # Extract public action logic
```

**Benefits:**
- Each function < 100 lines
- Easier to test
- Clearer responsibility
- Easier to modify

**Estimated effort:** 3-4 hours
**Priority:** MEDIUM (works fine as-is, but harder to maintain)

---

### 2. Import Organization

**Issue:** Some inconsistent import ordering.

**Example from actor_engine.py:**
```python
import os
import yaml
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from api_utils import make_openrouter_call
from response_parser import parse_actor_decision, ...
```

**Recommended:** Follow PEP 8 - standard library, third-party, local
```python
# Standard library
import os
from typing import Dict, Any, List

# Third-party
import requests
import yaml
from dotenv import load_dotenv

# Local
from api_utils import make_openrouter_call
from response_parser import parse_actor_decision, ...
```

**Estimated effort:** 30 minutes
**Priority:** LOW (cosmetic)

---

### 3. Error Messages and Logging

**Issue:** Inconsistent error reporting approach.

**Current mix:**
- Print statements: `print(f"⚠️  API error ...")`
- Simple prints: `print("Loading scenario...")`
- No structured logging

**Recommendation:** Add proper logging module (from TECHNICAL_DEBT.md #10)

**Estimated effort:** 2-3 hours
**Priority:** LOW (print statements work, but logging is better for production)

---

### 4. Docstring Coverage

**Issue:** Some functions lack docstrings.

**Good examples:**
```python
def extract_section(content: str, section_name: str, ...) -> str:
    """
    Extract a section from markdown-style content...

    Args:
        content: Full content to parse
        ...

    Returns:
        Extracted section content, or empty string
    """
```

**Missing docstrings in:**
- Some helper functions in run_scenario.py
- Some methods in scenario_state_manager.py

**Estimated effort:** 1 hour
**Priority:** LOW

---

## Architecture Review

### ✅ Good Architectural Decisions

1. **Modular design:** Clear separation of concerns
2. **Dependency injection:** Functions pass dependencies explicitly
3. **State management:** Centralized in WorldState and StateManager
4. **Utility modules:** Good abstraction for retry logic, parsing, markdown cleaning
5. **Error handling:** Robust with retry logic and graceful degradation

### 🔧 Areas for Improvement

1. **run_scenario.py complexity:** Main workflow function is very large
2. **Test coverage gaps:** New modules not yet tested
3. **Logging:** Using print statements instead of proper logging

---

## Security Review

### ✅ Secure Practices

1. **API keys:** Stored in .env, not in code ✅
2. **File permissions:** No obvious security issues ✅
3. **Input validation:** YAML loading is safe ✅

### ⚠️ Minor Concerns

1. **Path handling:** Uses os.path.join correctly, but no explicit path traversal checks
2. **File writes:** No size limits on generated files (could fill disk in batch mode)

**Recommendation:** Add file size monitoring for Phase 4 batch runs.

---

## Performance Review

### ✅ Efficient Design

1. **Context summaries:** Cached to avoid re-generation ✅
2. **State persistence:** Only saves when needed ✅
3. **Lazy loading:** Scenarios loaded on demand ✅

### 🔧 Future Optimizations (for Phase 4)

1. **Parallel actor decisions:** Currently sequential, could parallelize
2. **Batch API calls:** Could bundle multiple requests
3. **Output caching:** Could cache identical world states

---

## Recommendations by Priority

### HIGH Priority (Do Before Phase 4)

1. **Add tests for new utility modules** (4-7 hours)
   - response_parser.py
   - api_utils.py
   - markdown_utils.py

**Rationale:** These modules are critical and recently added. Testing will catch bugs before batch processing multiplies them.

---

### MEDIUM Priority (Nice to Have)

2. **Refactor run_scenario.py** (3-4 hours)
   - Split into smaller functions
   - Improve testability

**Rationale:** Would make codebase more maintainable, but current code works fine.

---

### LOW Priority (Can Wait)

3. **Code cleanups** (2-3 hours)
   - Import organization
   - Add logging module
   - Complete docstrings

**Rationale:** Cosmetic improvements that don't affect functionality.

---

## Final Verdict

**Overall Grade: B+**

The codebase is in good shape. The core architecture is solid, recent improvements are working, and there are no critical bugs.

**Before Phase 4:**
- **Must do:** Add tests for new utility modules (4-7 hours)
- **Optional:** Refactoring can wait until it becomes a problem

**Proceed to Phase 4?** YES - after adding the high-priority tests.

The system is stable enough for batch processing, and testing the new utilities will ensure reliability at scale.
