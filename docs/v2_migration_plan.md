# V2-Only Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate Scenario Lab from its hybrid V1/V2 architecture to a pure V2 implementation. The migration will eliminate all V1 dependencies, establish a consistent V2 pipeline across all execution flows, and deliver a unified developer experience.

**Status:** Phase 1 (Core Simulation) is 60% complete. Phases 2-6 not started.

**Recommended Approach:** Gradual migration with continuous validation

**Estimated Timeline:** 5 weeks total (25 working days + ~6-day buffer)

**Key Risk:** Scope is larger than initially estimated - includes batch processing, web interface, CLI tools, and utilities in addition to core simulation.

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Migration Strategy](#migration-strategy)
3. [Core Principles](#core-principles)
4. [Critical Technical Decisions](#critical-technical-decisions)
5. [Migration Phases](#migration-phases)
6. [Detailed Component Plans](#detailed-component-plans)
7. [Risk Assessment](#risk-assessment)
8. [Validation Strategy](#validation-strategy)
9. [Success Criteria](#success-criteria)
10. [Timeline and Effort Estimates](#timeline-and-effort-estimates)

---

## Current State Assessment

### Component Inventory

**V1 Components (src/)** - 30 files requiring migration or removal:

**Core Simulation (8 files):**
- `actor_engine.py` - Actor decision-making logic
- `world_state.py` - World state management
- `world_state_updater.py` - World state synthesis via LLM
- `context_manager.py` - Context windowing for prompts
- `communication_manager.py` - Actor communication system
- `cost_tracker.py` - Cost tracking and accumulation
- `metrics_tracker.py` - Metrics extraction from scenarios
- `exogenous_events.py` - Black swan event management

**Batch Processing (6 files):**
- `batch_runner.py` - Orchestrates batch scenario execution
- `batch_analyzer.py` - Statistical analysis of batch results
- `batch_cost_manager.py` - Budget enforcement for batches
- `batch_progress_tracker.py` - Real-time progress display
- `batch_parallel_executor.py` - Async execution with rate limiting
- `parameter_variator.py` - Cartesian product generation

**Utilities (10 files):**
- `qa_validator.py` - Quality assurance validation
- `response_cache.py` - LLM response caching
- `response_parser.py` - Response parsing utilities
- `api_utils.py` - LLM API call wrapper
- `error_handler.py` - User-friendly error handling
- `progressive_fallback.py` - Model fallback strategies
- `graceful_fallback.py` - Optional dependency handling
- `memory_optimizer.py` - Memory management and GC
- `markdown_utils.py` - Markdown formatting utilities
- `logging_config.py` - Logging configuration

**CLI Tools (4 files):**
- `run_scenario.py` - Main scenario execution script
- `create_scenario.py` - Interactive scenario creation wizard
- `create_batch_config.py` - Interactive batch config wizard
- `cache_cli.py` - Cache management CLI

**Schemas (1 file):**
- `schemas.py` - V1 Pydantic schemas and loaders

**State Management (1 file):**
- `scenario_state_manager.py` - State persistence for resume/branch

---

**V2 Components (scenario_lab/)** - 42 files with varying V1 dependencies (29 implementation modules detailed below plus 13 package infrastructure files such as `__init__.py` stubs and `py.typed`).

**Core (2 files):**
- ✅ `core/events.py` - Event bus (no V1 dependencies)
- ✅ `core/orchestrator.py` - Scenario orchestrator (no V1 dependencies)

**Models (1 file):**
- ✅ `models/state.py` - Immutable state models (no V1 dependencies)

**Schemas (5 files):**
- ✅ `schemas/scenario.py` - Scenario config schema (no V1 dependencies)
- ✅ `schemas/actor.py` - Actor config schema (no V1 dependencies)
- ✅ `schemas/metrics.py` - Metrics schema (no V1 dependencies)
- ✅ `schemas/validation.py` - Validation schema (no V1 dependencies)
- ⚠️ `schemas/loader.py` - Schema loader utilities (minimal V1 usage)

**Loaders (1 file):**
- ⚠️ `loaders/scenario_loader.py` - **DEPENDS ON V1** (actor_engine, schemas)

**Services/Phases (5 files):**
- ⚠️ `services/communication_phase.py` - **DEPENDS ON V1** (heavy V1 usage)
- ⚠️ `services/decision_phase.py` - **DEPENDS ON V1** (heavy V1 usage)
- ⚠️ `services/world_update_phase.py` - **DEPENDS ON V1** (heavy V1 usage)
- ⚠️ `services/persistence_phase.py` - Partial V1 dependency
- ✅ `services/database_persistence_phase.py` - No V1 dependencies

**Runners (2 files):**
- ⚠️ `runners/sync_runner.py` - **DEPENDS ON V1** (orchestrates V1 components)
- ✅ `runners/async_executor.py` - No V1 dependencies

**Utils (6 files):**
- ✅ `utils/state_persistence.py` - No V1 dependencies
- ✅ `utils/model_pricing.py` - No V1 dependencies
- ⚠️ `utils/json_response_parser.py` - **DEPENDS ON V1** (imports response_parser)
- ✅ `utils/logging_config.py` - No V1 dependencies
- ✅ `utils/cost_estimator.py` - No V1 dependencies
- ✅ `utils/cli_helpers.py` - No V1 dependencies

**CLI (2 files):**
- ✅ `cli.py` - Main CLI entry point (no V1 dependencies)
- ✅ `interfaces/cli.py` - CLI interface (no V1 dependencies)

**API/Web (1 file):**
- ✅ `api/app.py` - FastAPI app (no direct V1 dependencies)

*Note:* The API currently wires up the SyncRunner, so it indirectly inherits remaining V1 dependencies until the runner is migrated.

**Database (1 file):**
- ✅ `database/models.py` - SQLAlchemy models

**Tests (3 files):**
- ✅ `tests/test_events.py` - No V1 dependencies
- ✅ `tests/test_orchestrator.py` - No V1 dependencies
- ✅ `tests/test_state.py` - No V1 dependencies

**Package Infrastructure (13 files):**
- ✅ `scenario_lab/__init__.py`
- ✅ `scenario_lab/py.typed`
- ✅ `core/__init__.py`
- ✅ `loaders/__init__.py`
- ✅ `services/__init__.py`
- ✅ `schemas/__init__.py`
- ✅ `runners/__init__.py`
- ✅ `utils/__init__.py`
- ✅ `models/__init__.py`
- ✅ `database/__init__.py`
- ✅ `api/__init__.py`
- ✅ `interfaces/__init__.py`
- ✅ `tests/__init__.py`

---

**Test Suite (tests/):**
- 24 Python test modules (excluding `__init__.py`)
- 22 of those tests use `sys.path.insert` to import V1 components; another 16 non-test files across the repo still do the same
- Key V2 tests: `test_v2_integration.py`, `test_v2_phases.py`

---

### Dependency Analysis

**V2 Components with V1 Dependencies (6 critical files):**

1. **scenario_lab/loaders/scenario_loader.py**
   - Imports: `actor_engine.Actor`, `schemas.load_scenario_config`, `schemas.load_actor_config`
   - Creates V1 Actor objects
   - Uses V1 schema loaders

2. **scenario_lab/services/decision_phase.py**
   - Imports: `Actor`, `ContextManager`, `WorldState`, `CommunicationManager`, `MetricsTracker`, `QAValidator`
   - Calls `actor.make_decision()`
   - Heavy integration with V1 components

3. **scenario_lab/services/world_update_phase.py**
   - Imports: `WorldStateUpdater`, `WorldState`, `MetricsTracker`, `QAValidator`, `ExogenousEventManager`
   - Calls `world_state_updater.update_world_state()`

4. **scenario_lab/services/communication_phase.py**
   - Imports: `Actor`, `ContextManager`, `WorldState`, `CommunicationManager`
   - Manages actor communication via V1 components

5. **scenario_lab/runners/sync_runner.py**
   - Imports all V1 core components
   - Orchestrates V1/V2 hybrid execution
   - Central integration point

6. **scenario_lab/utils/json_response_parser.py**
   - Imports: `response_parser.parse_json_response`
   - Can be easily migrated

---

## Migration Strategy

### Chosen Approach: **Gradual Migration with Continuous Validation**

**Why Gradual:**
- Maintains system stability throughout migration
- Allows continuous testing and validation
- Enables rollback at any point
- Reduces risk of breaking existing functionality
- Supports parallel development if needed

**Why Not Big Bang:**
- Too risky given system complexity
- Hard to debug if multiple components break simultaneously
- Difficult to isolate regressions
- No intermediate working states

### Strategy Principles

1. **Migrate one phase/component at a time**
2. **Keep V1 components as temporary dependencies until all dependents are migrated**
3. **Write V2 tests before migration to establish behavior contracts**
4. **Use SyncRunner as compatibility bridge during transition**
5. **Validate after each component migration (golden file tests)**
6. **Remove V1 components only when ALL dependents are converted**
7. **Document decisions and trade-offs in code comments**

### Migration Order

**Phase 1: Core Simulation Foundation** (Week 1)
- Loader and schemas
- Decision phase
- World update phase
- Persistence phase

**Phase 2: Communication and Context** (Week 2)
- Communication phase
- Context management
- Actor engine adaptation

**Phase 3: Utilities and Supporting Systems** (Week 2-3)
- Cost tracking
- Metrics tracking
- QA validation
- Response parsing and caching
- Error handling

**Phase 4: Batch Processing** (Week 3)
- Batch runner
- Parameter variation
- Cost management
- Progress tracking
- Parallel execution
- Batch analyzer

**Phase 5: CLI and Web Interface** (Week 4)
- CLI entry points
- Scenario creation wizard
- Batch config wizard
- Web interface integration

**Phase 6: Cleanup and Finalization** (Week 4)
- Remove all V1 components
- Remove `sys.path.insert` from all files
- Update all tests
- Update documentation
- Performance validation
- Final integration tests

---

## Core Principles

### 1. V1 Component Isolation

**V1 components (legacy `src/*` modules) should no longer be imported anywhere under `scenario_lab/` or tests.**

**Current violations:** 6 V2 files import V1 components (see Dependency Analysis)

**Target:** Zero V1 imports in V2 code

### 2. Uniform V2 Pipeline

**All execution flows (CLI, runners, tests) must use the same V2 pipeline.**

For now we build a minimal pipeline that hits essential phases (decision, world update, persistence) and stubs/defers others.

**Current state:** SyncRunner orchestrates hybrid V1/V2 execution

**Target:** Pure V2 orchestrator → phases → state updates

### 3. V2-Native Testing

**Tests should rely on internal fixtures/helper classes in `scenario_lab` rather than patching into `src`.**

Test fixtures should create scenario directories compatible with V2 schemas.

**Current state:** Many tests use `sys.path.insert` and V1 patching

**Target:** All tests use V2 fixtures and mock V2 interfaces

---

## Critical Technical Decisions

These decisions must be made before implementation begins. Each decision affects multiple components.

### Decision 1: Actor Engine Strategy

**Options:**

A. **Rewrite Actor class in V2**
   - Pros: Clean break, pure V2, no legacy code
   - Cons: High effort, risk of behavior changes, need to replicate all V1 features
   - Effort: 5-7 days

B. **Adapt V1 Actor class for V2 use**
   - Pros: Preserves behavior, less effort, gradual transition
   - Cons: Still depends on V1, not "pure V2"
   - Effort: 2-3 days

C. **Create thin V2 wrapper around V1 Actor**
   - Pros: Minimal effort, preserves behavior exactly
   - Cons: Still has V1 dependency, adds layer of indirection
   - Effort: 1 day

**Recommendation:** **Option B (Adapt)** in Phase 1, then **Option A (Rewrite)** in Phase 2
- Phase 1: Move Actor to `scenario_lab/core/actor.py`, update imports, remove V1-specific code
- Phase 2: Gradually refactor to pure V2 patterns
- Rationale: Balances risk and effort, allows validation at each step

### Decision 2: Communication System

**Options:**

A. **Implement full V2 communication system**
   - Pros: Feature parity with V1
   - Cons: High complexity, many dependencies
   - Effort: 4-5 days

B. **Defer communication features (stub phase)**
   - Pros: Faster migration, simpler system
   - Cons: Scenarios using communication won't work
   - Effort: 1 day (stub)

C. **Migrate CommunicationManager to V2**
   - Pros: Preserves functionality, moderate effort
   - Cons: Complex component with many interactions
   - Effort: 3-4 days

**Recommendation:** **Option C (Migrate)** in Phase 2
- Rationale: Communication is used in several scenarios (ai-2027, bilateral negotiations)
- Can't defer without breaking existing scenarios
- Migration is tractable if done after Phase 1 foundation is solid

### Decision 3: Cost Tracking

**Current state:** Two systems exist:
- V1: `src/cost_tracker.py` - Mutable accumulator
- V2: `scenario_lab/utils/model_pricing.py` + cost fields in `ScenarioState`

**Options:**

A. **Use V2 immutable approach (costs in ScenarioState)**
   - Pros: Aligns with V2 immutability, already partially implemented
   - Cons: Need to migrate all V1 cost tracking code
   - Effort: 2-3 days

B. **Keep V1 CostTracker as mutable side-car**
   - Pros: Minimal changes needed
   - Cons: Violates V2 immutability principle
   - Effort: 1 day

**Recommendation:** **Option A (V2 immutable)**
- Rationale: Cost tracking is core to V2 state model
- Already partially implemented in `CostRecord` and `ScenarioState.total_cost()`
- Clean break from V1 patterns

### Decision 4: Metrics Extraction

**Options:**

A. **Rewrite MetricsTracker in V2**
   - Pros: Clean implementation, no V1 dependencies
   - Cons: Complex component, risk of behavior changes
   - Effort: 4-5 days

B. **Migrate V1 MetricsTracker to V2**
   - Pros: Preserves behavior, moderate effort
   - Cons: May carry V1 patterns
   - Effort: 2-3 days

C. **Defer metrics extraction**
   - Pros: Faster core migration
   - Cons: Breaks batch analysis, no metrics output
   - Effort: N/A

**Recommendation:** **Option B (Migrate)** in Phase 3
- Rationale: Metrics are essential for batch analysis and research use
- Migration is manageable after core phases are stable
- Can refactor later if needed

### Decision 5: QA Validation

**Options:**

A. **Migrate QAValidator to V2**
   - Pros: Preserves validation capabilities
   - Cons: Moderate complexity
   - Effort: 2-3 days

B. **Defer QA validation**
   - Pros: Faster migration
   - Cons: Loses quality assurance features
   - Effort: N/A

**Recommendation:** **Option A (Migrate)** in Phase 3
- Rationale: QA validation is valuable for research quality
- Optional feature (only runs if `validation-rules.yaml` exists)
- Can be migrated independently after core phases

### Decision 6: Context Management

**Options:**

A. **Rewrite ContextManager in V2**
   - Pros: Cleaner implementation
   - Cons: Risk of behavior changes
   - Effort: 2-3 days

B. **Migrate V1 ContextManager to V2**
   - Pros: Preserves windowing logic
   - Cons: May carry V1 patterns
   - Effort: 1-2 days

**Recommendation:** **Option B (Migrate)** in Phase 2
- Rationale: Context windowing logic is well-tested and stable
- Migration is straightforward (mostly data transformation)
- Can refactor later if performance issues arise

---

## Migration Phases

### Phase 1: Core Simulation Foundation (Week 1)

**Goal:** Establish V2 foundation for scenario execution (decision → world update → persistence pipeline)

**Status:** 60% complete (schemas ✅, orchestrator ✅, state models ✅, phases ⚠️)

#### 1.1 Loader and Schema Alignment (2 days)

**Objective:** Use `scenario_lab/schemas/...` exclusively for all loading

**Tasks:**
- [ ] Review V1 `schemas.py` for features not in V2 schemas
- [ ] Ensure V2 schemas support all V1 scenario fields
- [ ] Create V2 actor loading function in `scenario_lab/loaders/actor_loader.py`
- [ ] Update `scenario_loader.py` to use V2 schemas only
- [ ] Remove dependency on `src/schemas.py`
- [ ] Write tests for loader with various scenario formats

**Success Criteria:**
- `scenario_loader.py` has no `sys.path.insert`
- All scenarios load successfully with V2 schemas
- Tests pass with V2 loader

#### 1.2 Decision Phase (3 days)

**Objective:** Implement native V2 `DecisionPhase` that doesn't depend on V1 Actor engine

**Current Dependencies:**
- `actor_engine.Actor` - Actor decision-making
- `context_manager.ContextManager` - Context windowing
- `world_state.WorldState` - World state access
- `communication_manager.CommunicationManager` - Communication context
- `metrics_tracker.MetricsTracker` - Metrics extraction
- `qa_validator.QAValidator` - Validation

**Tasks:**
- [ ] Create `scenario_lab/core/prompt_builder.py` for prompt construction
- [ ] Move actor decision logic from V1 Actor to V2 DecisionPhase
- [ ] Use `scenario_lab.utils.api_client` (to be created) for LLM calls instead of V1 Actor
- [ ] Parse responses with `scenario_lab.utils.json_response_parser` (migrate from V1)
- [ ] Track costs via `ScenarioState.add_cost()` instead of CostTracker
- [ ] Defer metrics extraction to Phase 3 (stub for now)
- [ ] Defer QA validation to Phase 3 (stub for now)
- [ ] Write unit tests that mock LLM calls (like current `test_v2_phases.py`)

**Success Criteria:**
- `decision_phase.py` has no V1 imports
- Tests pass with mocked LLM calls
- Decision markdown files match V1 format
- Costs tracked in ScenarioState

**Migration Notes:**
- Context management deferred to Phase 2 (use full world state for now)
- Communication context deferred to Phase 2 (no communication yet)

#### 1.3 World Update Phase (2 days)

**Objective:** Implement native V2 `WorldUpdatePhase` for world state synthesis

**Current Dependencies:**
- `world_state_updater.WorldStateUpdater` - LLM-based synthesis
- `world_state.WorldState` - State management
- `metrics_tracker.MetricsTracker` - Metrics extraction
- `qa_validator.QAValidator` - Validation
- `exogenous_events.ExogenousEventManager` - Black swan events

**Tasks:**
- [ ] Create `scenario_lab/core/world_synthesizer.py` for world state synthesis
- [ ] Move world update logic from V1 WorldStateUpdater to V2
- [ ] Build prompts from actor decisions and previous state
- [ ] Use `scenario_lab.utils.api_client` for LLM calls
- [ ] Update `ScenarioState.world_state` with new content
- [ ] Defer metrics extraction to Phase 3 (stub for now)
- [ ] Defer QA validation to Phase 3 (stub for now)
- [ ] Defer exogenous events to Phase 3 (stub for now)
- [ ] Write unit tests with mocked LLM calls

**Success Criteria:**
- `world_update_phase.py` has no V1 imports
- Tests pass with mocked LLM calls
- World state markdown files match V1 format
- State updated correctly in ScenarioState

#### 1.4 Persistence Phase (1 day)

**Objective:** Ensure persistence uses only V2 types

**Current State:** Already mostly V2-compatible

**Tasks:**
- [ ] Verify `PersistencePhase` doesn't call V1 `.to_markdown()` methods
- [ ] Ensure all markdown generation uses V2 state fields
- [ ] Verify `StatePersistence` serializes `scenario_config` correctly
- [ ] Test resume/branch scenarios with V2 state files

**Success Criteria:**
- No V1 imports in persistence code
- Resume works with V2 state files
- Branch works with V2 state files

#### 1.5 Phase 1 Integration Test (1 day)

**Tasks:**
- [ ] Create golden file test with known V1 scenario
- [ ] Run scenario with V1 pipeline, capture output
- [ ] Run same scenario with Phase 1 V2 pipeline
- [ ] Compare outputs (should be nearly identical)
- [ ] Document any acceptable differences

**Success Criteria:**
- Simple scenario runs end-to-end with Phase 1 components
- Output matches V1 golden files (within tolerance)
- All Phase 1 tests pass

---

### Phase 2: Communication and Context (Week 2)

**Goal:** Add communication and context management to V2 pipeline

#### 2.1 Context Management (2 days)

**Tasks:**
- [ ] Create `scenario_lab/core/context_manager.py`
- [ ] Move windowing logic from V1 ContextManager
- [ ] Adapt to work with immutable ScenarioState
- [ ] Integrate with DecisionPhase
- [ ] Write unit tests for context windowing

**Success Criteria:**
- Context windowing works with V2 state
- Actors see appropriate historical context
- No V1 dependencies

#### 2.2 Communication Phase (3 days)

**Tasks:**
- [ ] Create `scenario_lab/core/communication_manager.py`
- [ ] Move communication logic from V1 CommunicationManager
- [ ] Support bilateral negotiations, public statements, coalition formation
- [ ] Track communications in ScenarioState
- [ ] Integrate with DecisionPhase (actors see relevant communications)
- [ ] Write tests for communication scenarios

**Success Criteria:**
- Communication features work in V2
- Scenarios with bilateral negotiations execute correctly
- No V1 dependencies

#### 2.3 Actor Engine Migration (3 days)

**Tasks:**
- [ ] Move V1 Actor class to `scenario_lab/core/actor.py`
- [ ] Remove V1-specific patterns (use V2 state, LLM client, etc.)
- [ ] Update loader to create V2 Actor objects
- [ ] Ensure all actor configuration fields supported
- [ ] Write comprehensive actor tests

**Success Criteria:**
- Actor logic fully in V2
- All actor features preserved
- No V1 dependencies

#### 2.4 Phase 2 Integration Test (1 day)

**Tasks:**
- [ ] Run scenarios with communication (e.g., ai-2027 bilateral negotiations)
- [ ] Compare with V1 golden files
- [ ] Verify context windowing works correctly
- [ ] Test edge cases (no communication, many actors, etc.)

**Success Criteria:**
- Communication scenarios run correctly
- Output matches V1 (within tolerance)
- All Phase 2 tests pass

---

### Phase 3: Utilities and Supporting Systems (Week 2-3)

**Goal:** Migrate supporting utilities to V2

#### 3.1 API Client and Response Parsing (1 day)

**Tasks:**
- [ ] Create `scenario_lab/utils/api_client.py`
- [ ] Consolidate LLM API logic from V1 `api_utils.py`
- [ ] Move response parsing from V1 to V2
- [ ] Update all phases to use V2 API client
- [ ] Add tests for API client and parsing

**Success Criteria:**
- Single API client for all LLM calls
- Response parsing works for all response types
- No V1 api_utils dependencies

#### 3.2 Response Caching (1 day)

**Tasks:**
- [ ] Move `response_cache.py` to `scenario_lab/utils/`
- [ ] Integrate with V2 API client
- [ ] Test cache hit/miss behavior
- [ ] Verify cost savings calculations

**Success Criteria:**
- Caching works with V2 API client
- Cache stats reported correctly
- No V1 dependencies

#### 3.3 Metrics Tracking (2 days)

**Tasks:**
- [ ] Create `scenario_lab/core/metrics_tracker.py`
- [ ] Move metrics extraction logic from V1
- [ ] Adapt to work with ScenarioState
- [ ] Integrate with DecisionPhase and WorldUpdatePhase
- [ ] Test metrics extraction with various scenarios

**Success Criteria:**
- Metrics extracted correctly
- metrics.json files match V1 format
- No V1 dependencies

#### 3.4 QA Validation (2 days)

**Tasks:**
- [ ] Create `scenario_lab/core/qa_validator.py`
- [ ] Move validation logic from V1
- [ ] Adapt to work with ScenarioState
- [ ] Integrate with phases
- [ ] Test validation with various scenarios

**Success Criteria:**
- Validation reports generated correctly
- Validation costs tracked
- No V1 dependencies

#### 3.5 Error Handling (1 day)

**Tasks:**
- [ ] Move error handling to `scenario_lab/utils/error_handler.py`
- [ ] Integrate with V2 phases
- [ ] Test error scenarios (rate limits, API failures, etc.)

**Success Criteria:**
- User-friendly error messages
- Proper recovery suggestions
- No V1 dependencies

#### 3.6 Progressive Fallback (1 day)

**Tasks:**
- [ ] Move fallback logic to `scenario_lab/utils/progressive_fallback.py`
- [ ] Integrate with V2 API client
- [ ] Test fallback scenarios

**Success Criteria:**
- Fallback works when primary models fail
- Costs tracked correctly
- No V1 dependencies

#### 3.7 Memory Optimization (1 day)

**Tasks:**
- [ ] Move memory optimization to `scenario_lab/utils/memory_optimizer.py`
- [ ] Integrate with orchestrator
- [ ] Test OOM prevention

**Success Criteria:**
- Memory monitoring works
- GC triggered appropriately
- No V1 dependencies

---

### Phase 4: Batch Processing (Week 3)

**Goal:** Migrate batch processing system to V2

#### 4.1 Parameter Variation (1 day)

**Tasks:**
- [ ] Move `parameter_variator.py` to `scenario_lab/batch/`
- [ ] Update to work with V2 schemas
- [ ] Test Cartesian product generation

**Success Criteria:**
- Parameter variation works with V2
- Generates correct scenario variations
- No V1 dependencies

#### 4.2 Batch Cost Manager (1 day)

**Tasks:**
- [ ] Move `batch_cost_manager.py` to `scenario_lab/batch/`
- [ ] Adapt to V2 cost tracking (ScenarioState)
- [ ] Test budget enforcement

**Success Criteria:**
- Budget limits enforced correctly
- Cost tracking accurate
- No V1 dependencies

#### 4.3 Batch Progress Tracker (1 day)

**Tasks:**
- [ ] Move `batch_progress_tracker.py` to `scenario_lab/batch/`
- [ ] Integrate with V2 event bus
- [ ] Test progress display

**Success Criteria:**
- Progress tracking works
- Rich formatting displays correctly
- No V1 dependencies

#### 4.4 Batch Parallel Executor (1 day)

**Tasks:**
- [ ] Move `batch_parallel_executor.py` to `scenario_lab/batch/`
- [ ] Use V2 SyncRunner (or create V2 async runner)
- [ ] Test rate limiting and concurrency

**Success Criteria:**
- Parallel execution works
- Rate limiting enforced
- No V1 dependencies

#### 4.5 Batch Runner (2 days)

**Tasks:**
- [ ] Move `batch_runner.py` to `scenario_lab/batch/`
- [ ] Integrate all batch components
- [ ] Use V2 runner for scenario execution
- [ ] Test full batch workflow

**Success Criteria:**
- Batch runs execute correctly
- All batch features work (cost limits, progress, resume, etc.)
- No V1 dependencies

#### 4.6 Batch Analyzer (2 days)

**Tasks:**
- [ ] Move `batch_analyzer.py` to `scenario_lab/batch/`
- [ ] Adapt to V2 state and metrics format
- [ ] Test statistical analysis

**Success Criteria:**
- Statistical analysis works
- Reports generated correctly
- No V1 dependencies

---

### Phase 5: CLI and Web Interface (Week 4)

**Goal:** Migrate CLI tools and web interface

#### 5.1 Main CLI Runner (1 day)

**Tasks:**
- [ ] Update `scenario_lab/cli.py` to use pure V2 runner
- [ ] Remove any remaining V1 dependencies
- [ ] Test all CLI commands (run, validate, estimate, etc.)

**Success Criteria:**
- CLI runs scenarios with V2 only
- All commands work
- Help text updated

#### 5.2 Scenario Creation Wizard (2 days)

**Tasks:**
- [ ] Move `create_scenario.py` to `scenario_lab/wizards/`
- [ ] Update to use V2 schemas exclusively
- [ ] Test wizard with various inputs

**Success Criteria:**
- Wizard creates V2-compatible scenarios
- All features work (actors, metrics, validation)
- No V1 dependencies

#### 5.3 Batch Config Wizard (1 day)

**Tasks:**
- [ ] Move `create_batch_config.py` to `scenario_lab/wizards/`
- [ ] Update to use V2 batch system
- [ ] Test wizard

**Success Criteria:**
- Wizard creates V2-compatible batch configs
- No V1 dependencies

#### 5.4 Web Interface (2 days)

**Tasks:**
- [ ] Update web interface to use V2 runner
- [ ] Remove V1 dependencies
- [ ] Test web execution

**Success Criteria:**
- Web interface runs scenarios with V2
- All features work
- No V1 dependencies

---

### Phase 6: Cleanup and Finalization (Week 4)

**Goal:** Remove all V1 code and finalize migration

#### 6.1 Remove V1 Components (1 day)

**Tasks:**
- [ ] Verify no V2 code imports from `src/`
- [ ] Verify no tests import from `src/`
- [ ] Remove or archive `src/` directory
- [ ] Update `pyproject.toml` to remove V1-only dependencies

**Success Criteria:**
- Zero V1 imports in codebase
- All tests pass without `src/`
- Dependencies cleaned up

#### 6.2 Test Suite Cleanup (2 days)

**Tasks:**
- [ ] Remove all `sys.path.insert` from tests
- [ ] Convert V1 tests to V2 or delete if obsolete
- [ ] Ensure 100% test pass rate
- [ ] Review test coverage

**Success Criteria:**
- No `sys.path.insert` in any test file
- All tests use V2 fixtures
- Test coverage ≥ 80%

#### 6.3 Documentation Update (1 day)

**Tasks:**
- [ ] Update README.md to describe V2 only
- [ ] Update CLAUDE.md with V2 architecture
- [ ] Remove V1 references from all docs
- [ ] Update examples to use V2 CLI
- [ ] Mark V2_MIGRATION.md as complete

**Success Criteria:**
- Documentation accurate for V2
- No V1 references (except historical context)
- Examples work with V2

#### 6.4 Performance Validation (1 day)

**Tasks:**
- [ ] Run performance benchmarks (V1 baseline vs V2)
- [ ] Identify any performance regressions
- [ ] Optimize if needed
- [ ] Document performance characteristics

**Success Criteria:**
- V2 performance within 10% of V1
- No major regressions
- Bottlenecks identified and documented

#### 6.5 Final Integration Testing (2 days)

**Tasks:**
- [ ] Run all example scenarios end-to-end
- [ ] Test resume and branch functionality
- [ ] Test batch processing with real scenarios
- [ ] Verify web interface works
- [ ] Run full test suite

**Success Criteria:**
- All scenarios run successfully
- All features work correctly
- Zero V1 dependencies in entire codebase

---

## Detailed Component Plans

### Loader Migration

**Current State:** `scenario_loader.py` uses V1 `load_scenario_config`, `load_actor_config`, and creates V1 `Actor` objects

**Target State:** Load with V2 schemas, create V2 actor representations

**Implementation:**
```python
# scenario_lab/loaders/scenario_loader.py (V2)

from scenario_lab.schemas.scenario import ScenarioConfig
from scenario_lab.schemas.actor import ActorConfig
from scenario_lab.core.actor import Actor  # V2 actor
from scenario_lab.models.state import ScenarioState, ActorState

class ScenarioLoader:
    def load(self):
        # Load scenario config
        scenario_config = ScenarioConfig.from_yaml(
            self.scenario_path / "scenario.yaml"
        )

        # Load actors
        actors = {}
        for actor_file in (self.scenario_path / "actors").glob("*.yaml"):
            actor_config = ActorConfig.from_yaml(actor_file)
            actors[actor_config.short_name] = Actor(actor_config)

        # Create initial state
        initial_state = ScenarioState.from_config(
            scenario_config=scenario_config.dict(),
            actors={
                name: ActorState.from_config(actor.config)
                for name, actor in actors.items()
            }
        )

        return initial_state, actors, scenario_config.dict()
```

**Dependencies:** Requires V2 Actor class (Phase 2)

**Workaround for Phase 1:** Keep V1 Actor temporarily, focus on schema loading

---

### Decision Phase Migration

**Current State:** Heavily depends on V1 Actor.make_decision()

**Target State:** Self-contained decision logic with V2 LLM client

**Implementation:**
```python
# scenario_lab/services/decision_phase.py (V2)

from scenario_lab.utils.api_client import make_llm_call
from scenario_lab.utils.json_response_parser import parse_json_response
from scenario_lab.core.prompt_builder import build_decision_prompt

class DecisionPhase:
    async def execute(self, state: ScenarioState) -> ScenarioState:
        decisions = []
        costs = []

        for actor_name, actor in self.actors.items():
            # Build prompt
            prompt = build_decision_prompt(
                actor=actor,
                world_state=state.world_state.content,
                turn=state.turn,
                total_turns=state.scenario_config.get("num_turns", 10)
            )

            # Make LLM call
            response, tokens = await make_llm_call(
                model=actor.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            # Parse response
            decision_data = parse_json_response(response)

            # Create decision object
            decision = Decision(
                actor=actor_name,
                content=decision_data,
                turn=state.turn
            )
            decisions.append(decision)

            # Track cost
            cost = CostRecord(
                phase="decision",
                actor=actor_name,
                model=actor.config.model,
                tokens=tokens,
                amount=calculate_cost(actor.config.model, tokens)
            )
            costs.append(cost)

        # Update state
        new_state = state.add_decisions(decisions).add_costs(costs)
        return new_state
```

**New Components Needed:**
- `scenario_lab/core/prompt_builder.py` - Prompt construction utilities
- `scenario_lab/utils/api_client.py` - LLM API client

---

### World Update Phase Migration

**Current State:** Uses V1 WorldStateUpdater

**Target State:** Self-contained world synthesis with V2 LLM client

**Implementation:**
```python
# scenario_lab/services/world_update_phase.py (V2)

from scenario_lab.utils.api_client import make_llm_call
from scenario_lab.core.prompt_builder import build_world_update_prompt

class WorldUpdatePhase:
    async def execute(self, state: ScenarioState) -> ScenarioState:
        # Build prompt from actor decisions
        prompt = build_world_update_prompt(
            current_state=state.world_state.content,
            decisions=[d.content for d in state.current_turn_decisions()],
            turn=state.turn
        )

        # Make LLM call
        response, tokens = await make_llm_call(
            model=self.world_state_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        # Update world state
        new_world_state = WorldState(
            content=response,
            turn=state.turn + 1,
            timestamp=datetime.now()
        )

        # Track cost
        cost = CostRecord(
            phase="world_update",
            model=self.world_state_model,
            tokens=tokens,
            amount=calculate_cost(self.world_state_model, tokens)
        )

        # Update state
        new_state = (
            state
            .update_world_state(new_world_state)
            .increment_turn()
            .add_cost(cost)
        )

        return new_state
```

---

### Test Migration Example

**Current V1 Test:**
```python
# tests/test_actor_engine.py (V1)

import sys
sys.path.insert(0, "src")

from actor_engine import Actor
from unittest.mock import patch

def test_actor_decision():
    with patch("actor_engine.make_llm_call") as mock_call:
        mock_call.return_value = ('{"action": "test"}', 100)
        actor = Actor(...)
        decision = actor.make_decision(...)
        assert decision["action"] == "test"
```

**Target V2 Test:**
```python
# tests/test_decision_phase.py (V2)

from scenario_lab.services.decision_phase import DecisionPhase
from scenario_lab.models.state import ScenarioState
from unittest.mock import AsyncMock, patch

async def test_decision_phase():
    # Create test state
    state = create_test_state(turn=1)

    # Mock LLM call
    with patch("scenario_lab.utils.api_client.make_llm_call") as mock_call:
        mock_call.return_value = ('{"action": "test"}', 100)

        # Execute phase
        phase = DecisionPhase(actors=test_actors)
        new_state = await phase.execute(state)

        # Verify
        assert len(new_state.decisions) > 0
        assert new_state.decisions[0].content["action"] == "test"
```

---

## Risk Assessment

### High Risk

**1. Behavior Changes in Migrated Components**
- **Risk:** V2 versions produce different outputs than V1
- **Impact:** Scenarios may behave differently, research results invalidated
- **Mitigation:** Golden file tests, side-by-side comparison, gradual rollout
- **Contingency:** Keep V1 available for reproduction, document differences

**2. Breaking Resume/Branch Functionality**
- **Risk:** State file format changes break existing runs
- **Impact:** Can't resume or branch from V1 runs
- **Mitigation:** State file versioning, migration utilities
- **Contingency:** Provide V1→V2 state converter

**3. Performance Regressions**
- **Risk:** V2 is significantly slower than V1
- **Impact:** Batch runs take longer, higher costs
- **Mitigation:** Performance benchmarking, profiling, optimization
- **Contingency:** Identify and optimize bottlenecks before completion

### Medium Risk

**4. Test Coverage Gaps**
- **Risk:** Tests don't catch regressions during migration
- **Impact:** Bugs in V2 not discovered until production use
- **Mitigation:** Write V2 tests before migration, golden file tests
- **Contingency:** Extensive manual testing, user beta testing

**5. Incomplete V1 Feature Coverage**
- **Risk:** V2 doesn't support all V1 features
- **Impact:** Some scenarios can't run on V2
- **Mitigation:** Feature inventory, parity checklist
- **Contingency:** Document unsupported features, provide V1 fallback

**6. Communication System Complexity**
- **Risk:** Communication migration is harder than expected
- **Impact:** Phase 2 delayed, scenarios with communication don't work
- **Mitigation:** Start with simple cases, incremental testing
- **Contingency:** Defer communication to later phase, provide workarounds

### Low Risk

**7. Documentation Drift**
- **Risk:** Docs don't match V2 implementation
- **Impact:** User confusion, support burden
- **Mitigation:** Update docs during migration, not after
- **Contingency:** Quick doc fixes as issues arise

**8. Batch Processing Edge Cases**
- **Risk:** Batch system has untested edge cases
- **Impact:** Some batch configurations fail
- **Mitigation:** Comprehensive batch testing
- **Contingency:** Fix edge cases as discovered

---

## Validation Strategy

### Golden File Testing

**Approach:** Run same scenarios with V1 and V2, compare outputs

**Process:**
1. Select representative scenarios (simple, complex, with communication, batch)
2. Run with V1, save outputs (world states, decisions, metrics, costs)
3. Run with V2, save outputs
4. Compare files using diff or custom comparison tool
5. Document acceptable differences (timestamps, minor wording changes)
6. Investigate and fix unacceptable differences

**Scenarios for Validation:**
- `test-scenario` - Minimal 2-actor scenario
- `ai-2027` - Complex multi-actor with communication
- `ai-regulatory-negotiation` - Batch scenario with variations
- Custom edge cases (many actors, long runs, exogenous events)

### Behavioral Testing

**Unit Tests:** Test individual components in isolation
- Mock LLM calls, verify prompt construction
- Test state transitions
- Test cost calculations
- Test error handling

**Integration Tests:** Test phase interactions
- Decision → World Update → Persistence pipeline
- Communication → Decision integration
- Metrics extraction across phases
- Resume/branch functionality

**End-to-End Tests:** Test full scenarios
- Run scenarios from start to finish
- Verify all outputs produced
- Check markdown formatting
- Validate JSON structures

### Performance Testing

**Benchmarks:**
- Scenario execution time (V1 baseline vs V2)
- Memory usage
- LLM API call efficiency
- Cost per scenario

**Targets:**
- Execution time within 10% of V1
- Memory usage within 20% of V1
- No unnecessary API calls
- Cost accuracy within 1%

### Manual Testing

**Checklist:**
- [ ] Simple scenario runs end-to-end
- [ ] Complex scenario with all features
- [ ] Resume from interrupted run
- [ ] Branch from completed run
- [ ] Batch execution with variations
- [ ] Web interface execution
- [ ] Error handling (rate limits, API failures)
- [ ] Cost limits enforced
- [ ] Metrics extraction works
- [ ] QA validation runs
- [ ] Exogenous events trigger

---

## Success Criteria

### Technical Success

**Zero V1 Dependencies:**
- [ ] No `sys.path.insert(0, "src")` anywhere in `scenario_lab/`
- [ ] No `from src.*` imports
- [ ] No `import` statements referencing V1 modules
- [ ] `src/` directory archived or removed

**All Tests Pass:**
- [ ] 100% test pass rate
- [ ] Test coverage ≥ 80%
- [ ] No skipped tests
- [ ] All integration tests pass
- [ ] Golden file tests pass

**Feature Parity:**
- [ ] All V1 features work in V2
- [ ] Resume functionality works
- [ ] Branch functionality works
- [ ] Batch processing works
- [ ] Communication works
- [ ] Metrics extraction works
- [ ] QA validation works
- [ ] Web interface works

**Performance:**
- [ ] Execution time within 10% of V1
- [ ] Memory usage within 20% of V1
- [ ] Cost calculation accuracy within 1%

### Documentation Success

**Updated Documentation:**
- [ ] README.md describes V2 architecture
- [ ] CLAUDE.md updated for V2
- [ ] All examples use V2 CLI
- [ ] Migration guide marked complete
- [ ] API documentation current

**Removed V1 References:**
- [ ] No V1 instructions in docs (except historical)
- [ ] No V1 examples
- [ ] Clear V2-only messaging

### User Success

**Scenarios Run Successfully:**
- [ ] All example scenarios execute
- [ ] Test scenarios pass
- [ ] AI-2027 calibration scenario works
- [ ] Batch scenarios complete

**CLI Works Intuitively:**
- [ ] `scenario-lab run` works
- [ ] All CLI commands functional
- [ ] Help text clear and accurate
- [ ] Error messages helpful

**Migration Support:**
- [ ] V1 state files can be migrated (or documented as incompatible)
- [ ] Clear migration path for users
- [ ] No data loss

---

## Timeline and Effort Estimates

### Summary

| Phase | Duration | Effort (person-days) |
|-------|----------|---------------------|
| Phase 1: Core Simulation | 5 days | 9 days |
| Phase 2: Communication & Context | 5 days | 9 days |
| Phase 3: Utilities & Support | 5 days | 9 days |
| Phase 4: Batch Processing | 4 days | 8 days |
| Phase 5: CLI & Web | 3 days | 6 days |
| Phase 6: Cleanup & Finalization | 3 days | 7 days |
| **Total** | **25 days** | **48 days** |

**Note:** Duration assumes some parallel work and overlapping phases. Effort is total developer time.

### Detailed Timeline

**Week 1: Core Simulation Foundation (Phase 1)**
- Day 1: Loader and schema alignment
- Day 2: Loader regression tests and state validation
- Day 3: Decision phase migration (actors + context hooks)
- Day 4: Decision QA plus world update scaffolding
- Day 5: World update migration, persistence verification, smoke test

**Week 2: Communication and Context (Phase 2)**
- Day 6: Context management migration
- Day 7: Prompt/context integration tests and cleanup
- Day 8: Communication phase migration
- Day 9: Actor engine migration kickoff
- Day 10: Actor engine completion and Phase 2 integration testing

**Week 3: Utilities and Support (Phase 3)**
- Day 11: API client and response parsing migration
- Day 12: Response caching and model-pricing updates
- Day 13: Metrics tracker and QA validator port
- Day 14: Error handling plus fallback strategy consolidation
- Day 15: Remaining utilities and regression sweep

**Week 4: Batch Processing + CLI Kickoff (Phase 4 + Phase 5 overlap)**
- Day 16: Parameter variation and batch cost manager
- Day 17: Batch runner and executor
- Day 18: Parallel executor and analyzer scaffolding
- Day 19: Batch analyzer and validation tests
- Day 20: CLI foundation and shared helper alignment

**Week 5: CLI, Web, and Finalization (Phases 5-6)**
- Day 21: CLI wizards migration completion
- Day 22: Web interface update and manual QA pass
- Day 23: V1 removal prep and state migration scripts
- Day 24: Golden-path integration plus test cleanup
- Day 25: Documentation updates and release readiness review

### Dependencies

**Critical Path:**
1. Phase 1.1 (Loader) → Phase 1.2 (Decision) → Phase 1.3 (World Update)
2. Phase 2.3 (Actor) must complete before Phase 5.2 (Wizards)
3. Phase 3.3 (Metrics) must complete before Phase 4.6 (Batch Analyzer)
4. All phases 1-5 must complete before Phase 6 (Cleanup)

**Parallelizable Work:**
- Phase 3.1-3.7 utilities can be done in parallel
- Phase 4.1-4.4 batch components can be done in parallel
- Phase 5.1-5.3 CLI work can overlap with Phase 4

### Risk Buffer

**Recommended Buffer:** +25% (6 days)

**Reasons:**
- Communication system may be more complex than estimated
- Integration issues may arise
- Performance optimization may be needed
- Documentation updates may take longer than planned

**Adjusted Timeline:** Approximately 5 weeks (31 working days including buffer)

---

## Appendix: Component Dependency Map

### V2 Components by V1 Dependency Level

**Level 0: No V1 Dependencies (Ready to Use)**
- ✅ All schemas in `scenario_lab/schemas/`
- ✅ All models in `scenario_lab/models/`
- ✅ Event bus (`core/events.py`)
- ✅ Orchestrator (`core/orchestrator.py`)
- ✅ State persistence (`utils/state_persistence.py`)
- ✅ Model pricing (`utils/model_pricing.py`)
- ✅ Cost estimator (`utils/cost_estimator.py`)
- ✅ CLI helpers (`utils/cli_helpers.py`)
- ✅ Database models (`database/`)

**Level 1: Light V1 Dependencies (Easy to Migrate)**
- ⚠️ JSON response parser (`utils/json_response_parser.py`) - imports V1 response_parser
- ⚠️ Persistence phase (`services/persistence_phase.py`) - minor V1 usage

**Level 2: Moderate V1 Dependencies (Requires Refactoring)**
- ⚠️ Scenario loader (`loaders/scenario_loader.py`) - uses V1 schemas and Actor
- ⚠️ Communication phase (`services/communication_phase.py`) - uses multiple V1 components

**Level 3: Heavy V1 Dependencies (Major Refactoring)**
- ⚠️ Decision phase (`services/decision_phase.py`) - depends on V1 Actor engine, trackers, validators
- ⚠️ World update phase (`services/world_update_phase.py`) - depends on V1 updater, trackers, validators, events
- ⚠️ Sync runner (`runners/sync_runner.py`) - orchestrates all V1 components

### Migration Priority Order

1. **First:** Level 1 components (quick wins)
2. **Second:** Level 2 components (moderate effort)
3. **Third:** Level 3 components (major effort, requires earlier migrations)
4. **Finally:** Remove V1 components when all dependents migrated

---

## Appendix: V1 Component Status Tracker

Track which V1 components can be removed:

| V1 Component | V2 Dependents | Can Remove After |
|--------------|---------------|------------------|
| `actor_engine.py` | loader, decision_phase, communication_phase | Phase 2.3 |
| `schemas.py` | loader | Phase 1.1 |
| `world_state.py` | All phases, runner | Phase 1.3 |
| `world_state_updater.py` | world_update_phase | Phase 1.3 |
| `context_manager.py` | decision_phase, communication_phase | Phase 2.1 |
| `communication_manager.py` | decision_phase, communication_phase | Phase 2.2 |
| `cost_tracker.py` | All phases | Phase 1.5 |
| `metrics_tracker.py` | decision_phase, world_update_phase | Phase 3.3 |
| `qa_validator.py` | decision_phase, world_update_phase | Phase 3.4 |
| `exogenous_events.py` | world_update_phase | Phase 3 |
| `response_parser.py` | json_response_parser | Phase 3.1 |
| `api_utils.py` | All LLM-calling code | Phase 3.1 |
| `batch_*.py` (6 files) | None yet | Phase 4 |
| `run_scenario.py` | None | Phase 5.1 |
| `create_scenario.py` | None | Phase 5.2 |
| `create_batch_config.py` | None | Phase 5.3 |
| Others (utilities) | Various | Phase 3 |

**Removal Strategy:** Only remove when ALL dependents migrated and verified working

---

## Document History

- **2025-11-20:** Comprehensive revision with full system scope, detailed phases, risk assessment, validation strategy
- **2025-11-XX:** Initial draft with core principles and basic outline

---

## Next Steps

1. **Review and Approve Plan** (stakeholders)
2. **Make Critical Technical Decisions** (Section 4)
3. **Set Up Golden File Test Infrastructure**
4. **Begin Phase 1.1: Loader Migration**
5. **Track Progress** (update completion status in Component Inventory)

---

**Questions or Concerns?** Review the Risk Assessment and Validation Strategy sections. If major concerns arise, consider:
- Breaking phases into smaller increments
- Doing more prototyping before full migration
- Running parallel V1/V2 systems longer
- Adjusting timeline estimates based on team capacity
