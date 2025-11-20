# Phase 6.1: V1 Component Removal Plan

**Date**: 2025-11-20
**Status**: IN PROGRESS

---

## Summary

All V2 components have been implemented in Phases 1-5. Phase 6.1 removes all V1 dependencies from the codebase to complete the migration.

---

## V1 Dependencies Analysis

### V2 Code Files with V1 Imports (5 files)

#### 1. `scenario_lab/runners/sync_runner.py`

**Current V1 Imports:**
```python
from world_state import WorldState as V1WorldState
from world_state_updater import WorldStateUpdater
from context_manager import ContextManager
from communication_manager import CommunicationManager
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator
from exogenous_events import ExogenousEventManager
```

**Current Phase Imports:**
```python
from scenario_lab.services.decision_phase import DecisionPhase  # ❌ V1 hybrid
from scenario_lab.services.world_update_phase import WorldUpdatePhase  # ❌ V1 hybrid
```

**V2 Replacements:**
- Use `DecisionPhaseV2` instead of `DecisionPhase`
- Use `WorldUpdatePhaseV2` instead of `WorldUpdatePhase`
- Remove all V1 component instantiation
- Remove `sys.path.insert`

---

#### 2. `scenario_lab/services/decision_phase.py`

**Status**: ❌ **OBSOLETE - Replace with decision_phase_v2.py**

**V1 Imports:**
```python
from actor_engine import Actor
from context_manager import ContextManager
from world_state import WorldState as V1WorldState
from communication_manager import CommunicationManager
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator
```

**Action**: Delete this file, use `decision_phase_v2.py` instead

---

#### 3. `scenario_lab/services/world_update_phase.py`

**Status**: ❌ **OBSOLETE - Replace with world_update_phase_v2.py**

**V1 Imports:**
```python
from world_state_updater import WorldStateUpdater
from world_state import WorldState as V1WorldState
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator
from exogenous_events import ExogenousEventManager
```

**Action**: Delete this file, use `world_update_phase_v2.py` instead

---

#### 4. `scenario_lab/services/communication_phase.py`

**Status**: ⏳ **CHECK - May have V1 dependencies**

**Action**: Review and update if needed

---

#### 5. `scenario_lab/utils/json_response_parser.py`

**V1 Import (in main block):**
```python
# Line 214
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from response_parser import parse_actor_decision
```

**Action**: This is only in the `if __name__ == "__main__"` block for testing. Can be removed or updated to use V2 parser.

---

### V2 Code Files with Intentional V1 Bridges (2 files)

#### 6. `scenario_lab/interfaces/cli.py`

**V1 Imports**: Wizards only (intentional bridge)
```python
from create_scenario import create_scenario_interactive
from create_batch_config import create_batch_config_interactive
```

**Status**: ✅ **ACCEPTABLE - Temporary bridge until Phase 6.2**

**Action**: Keep for now, migrate wizards in Phase 6.2

---

### Legacy V1 Files (Already Deprecated)

#### 7-8. `web/app.py` and `web/scenario_executor.py`

**Status**: ✅ **DEPRECATED in Phase 5.2**

**Action**: Delete in Phase 6.2 cleanup

---

## V2 Components Available

All V2 replacements exist and are tested:

| Component | V2 Location | Status |
|-----------|-------------|--------|
| Actor | `scenario_lab/core/actor.py` | ✅ Complete |
| ContextManager | `scenario_lab/core/context_manager.py` | ✅ Complete (ContextManagerV2) |
| CommunicationManager | `scenario_lab/core/communication_manager.py` | ✅ Complete |
| MetricsTracker | `scenario_lab/core/metrics_tracker.py` | ✅ Complete |
| QAValidator | `scenario_lab/core/qa_validator.py` | ✅ Complete |
| WorldSynthesizer | `scenario_lab/core/world_synthesizer.py` | ✅ Complete |
| DecisionPhase | `scenario_lab/services/decision_phase_v2.py` | ✅ Complete |
| WorldUpdatePhase | `scenario_lab/services/world_update_phase_v2.py` | ✅ Complete |

---

## Phase 6.1 Tasks

### Task 1: Update SyncRunner to Use V2 Phases

**File**: `scenario_lab/runners/sync_runner.py`

**Changes**:
1. Replace phase imports:
   ```python
   # OLD
   from scenario_lab.services.decision_phase import DecisionPhase
   from scenario_lab.services.world_update_phase import WorldUpdatePhase

   # NEW
   from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
   from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
   ```

2. Remove all V1 component imports

3. Update phase instantiation to use V2 classes

4. Remove `sys.path.insert`

5. Update any V1 component usage to V2 equivalents

**Testing**: Run integration tests to ensure sync_runner still works

---

### Task 2: Remove Obsolete Hybrid Phase Files

**Files to Delete**:
- `scenario_lab/services/decision_phase.py`
- `scenario_lab/services/world_update_phase.py`

**Testing**: Ensure no imports remain for these files

---

### Task 3: Review and Update Communication Phase

**File**: `scenario_lab/services/communication_phase.py`

**Action**: Check for V1 dependencies and update if needed

---

### Task 4: Clean Up json_response_parser

**File**: `scenario_lab/utils/json_response_parser.py`

**Action**: Remove V1 import from main block or update to use V2

---

### Task 5: Verify No V1 Imports in V2 Code

**Command**:
```bash
grep -r "sys.path.insert.*src" scenario_lab/ --exclude-dir=__pycache__
```

**Expected**: Only `interfaces/cli.py` (wizard bridge)

---

## Success Criteria

- [ ] SyncRunner uses DecisionPhaseV2 and WorldUpdatePhaseV2
- [ ] No V1 imports in `scenario_lab/` except CLI wizard bridge
- [ ] Obsolete hybrid phase files deleted
- [ ] All integration tests pass
- [ ] CLI commands work (`scenario-lab run`, `scenario-lab validate`, etc.)
- [ ] Batch execution works

---

## Risks

**Risk 1**: SyncRunner may have complex V1 component wiring

**Mitigation**: Review SyncRunner carefully, update incrementally, test after each change

**Risk 2**: V2 phases may not fully support all V1 features

**Mitigation**: Run comprehensive integration tests, check for missing functionality

**Risk 3**: Breaking changes in phase interfaces

**Mitigation**: Check phase constructor signatures match, add compatibility shims if needed

---

## Next Steps (Phase 6.2)

After Phase 6.1:
- Migrate scenario creation wizards to V2
- Migrate batch config wizard to V2
- Remove wizard bridge from CLI
- Delete or archive `src/` directory
- Clean up test suite

---

## Notes

- The V2 architecture is functionally complete (Phases 1-5)
- All V2 components have been tested
- This phase is primarily cleanup and removal, not new development
- Main effort is in sync_runner.py - need to wire V2 phases correctly
