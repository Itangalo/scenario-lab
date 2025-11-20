# Scenario Lab Version 2.1 - Strategic Plan

## Executive Summary

Version 1 successfully validated the core concept: AI-powered multi-actor simulations can explore complex policy questions with rich outputs. We've proven researchers want this tool. Now Version 2 must transform a working prototype into a robust research platform that scales to production use.

**Key Insight from V1 Implementation**: The monolithic architecture wasn't a mistake - it let us iterate fast and prove the concept. But now that we know what we're building, we can architect it properly.

**Core Principle for V2**: Incremental evolution, not rewrite. V1 runs continue working while V2 capabilities emerge.

---

## What Version 1 Achieved (Celebrate This)

### Technical Accomplishments
- ✅ **Full simulation engine**: Multi-phase turns, information asymmetry, coalitions, world state synthesis
- ✅ **Cost management**: Estimation, tracking, limits, resume/branch - game-changing for research
- ✅ **Local LLM support**: Zero-cost batch runs with Ollama
- ✅ **Rich outputs**: Markdown narratives + JSON metrics + validation reports
- ✅ **Quality controls**: QA Validator catches inconsistencies automatically
- ✅ **188 passing tests**: Solid foundation for refactoring
- ✅ **Web backend started**: FastAPI + WebSocket foundation exists

### Research Validation
- Researchers can actually use this for policy analysis
- The YAML scenario format is intuitive
- The resume/branch workflow enables proper sensitivity analysis
- Batch processing with pattern recognition provides real insights

### What We Learned
1. **Markdown output is essential** - experts need narrative review
2. **Cost controls are non-negotiable** - without them, it's too risky to experiment
3. **Human-in-the-loop is the killer feature** - but needs better UX
4. **The monolithic runner is now the bottleneck** - it blocks web integration and testing

---

## Version 2 Vision

### Primary Goals

**1. Modular Architecture**
- Scenario execution as composable services, not monolithic script
- Each phase (comms, decisions, world update, QA, persistence) is independent
- Web API and CLI use the same execution engine

**2. Production-Ready Reliability**
- Schema validation catches errors before execution
- Comprehensive test coverage including integration tests
- Structured logging and observability
- Graceful degradation and error recovery

**3. Enhanced UX**
- Web dashboard for monitoring, human participation, and analysis
- Scenario editor with validation and templates
- Rich analytics without parsing raw files

**4. Scalability**
- Efficient batch processing
- Optional parallelization when needed
- Database-backed analytics queries

### Non-Goals (Explicitly Out of Scope)

- ❌ Distributed execution across machines (premature)
- ❌ Complex plugin architecture (YAGNI)
- ❌ Multi-tenancy / SaaS deployment (not the use case)
- ❌ Real-time collaboration (Phase 5 feature)

---

## Architecture Transformation

### Current State (V1)
```
run_scenario.py (640 lines)
    ├─ Parse YAML
    ├─ Initialize components
    ├─ Main loop:
    │   ├─ Private comms
    │   ├─ Coalitions
    │   ├─ Public actions
    │   ├─ World update
    │   ├─ QA validation
    │   ├─ Metrics extraction
    │   └─ Save markdown/JSON
    └─ CLI only, no API
```

**Problems**:
- Can't test phases independently
- Can't reuse in web API
- Can't pause/resume granularly
- Hard to extend

### Target State (V2)
```
Execution Engine (Event-Driven)
    ├─ ScenarioOrchestrator
    │   └─ Emits events: TurnStarted, PhaseComplete, etc.
    ├─ Phase Services (each independent)
    │   ├─ CommunicationPhase
    │   ├─ CoalitionPhase
    │   ├─ DecisionPhase
    │   ├─ WorldUpdatePhase
    │   ├─ ValidationPhase
    │   └─ PersistencePhase
    ├─ State Management
    │   ├─ In-memory for execution
    │   └─ SQLite for persistence/analytics
    └─ Interfaces
        ├─ CLI (backwards compatible)
        ├─ Web API (async)
        └─ Python SDK (for notebooks)
```

**Benefits**:
- Test each phase with mocked dependencies
- Web API and CLI use same engine
- Pause between any phase, not just turns
- Easy to add new phases (e.g., custom metrics)

### Data Flow Transformation

**V1: String-Based**
```
Actor → Markdown → Regex Parse → Internal State → Markdown File
```
- Fragile parsing
- Data loss risk
- Hard to validate

**V2: Structured with Views**
```
Actor → JSON Schema → Validated Data → {
    ├─ Internal State (structured)
    ├─ Markdown View (generated)
    └─ Database Record (analytics)
}
```
- Type-safe
- Lossless
- Machine-readable + human-readable

---

## Target API Design

This is the contract we're designing towards. All architectural decisions should support this interface.

### Python SDK (Primary Interface)

```python
from scenario_lab import Scenario, Runner, Database, Event

# Simple usage
scenario = Scenario.load('scenarios/ai-summit')
result = Runner().run(scenario, end_turn=10, credit_limit=5.0)
print(f"Completed in {result.turns} turns, cost ${result.total_cost:.2f}")

# Advanced usage with event handlers
runner = Runner()

@runner.on('turn_complete')
async def log_turn(event: Event):
    print(f"Turn {event.data['turn']} done, cost: ${event.data['cost']:.2f}")

@runner.on('credit_limit_warning')
async def warn_cost(event: Event):
    remaining = event.data['remaining']
    print(f"Warning: Only ${remaining:.2f} credit remaining")

result = await runner.run_async(scenario)

# Human actor control
human_actor = HumanActor('EU Commission')
result = runner.run(scenario, human_actors={'eu_commission': human_actor})

# Analytics
db = Database('scenario-lab.db')
similar_runs = db.find_similar(result, threshold=0.8)
comparison = db.compare_runs([result.id, 'run-001', 'run-002'])
metrics_df = db.query_metrics(scenario='ai-summit', actor='eu_commission')
```

### CLI (Backwards Compatible + Enhanced)

```bash
# V1 still works
python src/run_scenario.py scenarios/ai-summit

# V2 enhanced CLI
scenario-lab run scenarios/ai-summit --end-turn 10 --credit-limit 5.0
scenario-lab run scenarios/ai-summit --resume output/ai-summit/run-003
scenario-lab run scenarios/ai-summit --branch-from run-003 --branch-at-turn 5

# New capabilities
scenario-lab validate scenarios/ai-summit  # Schema validation
scenario-lab estimate scenarios/ai-summit  # Cost estimation
scenario-lab compare run-001 run-002 run-003  # Side-by-side comparison
scenario-lab export run-001 --format csv  # Export to different formats
```

### Web API (For Dashboard)

```python
# FastAPI endpoints
POST   /api/scenarios/{id}/execute
GET    /api/scenarios/{id}/status
POST   /api/scenarios/{id}/pause
POST   /api/scenarios/{id}/resume
WS     /api/scenarios/{id}/stream  # Real-time updates

POST   /api/actors/{id}/decide  # Human actor input
GET    /api/runs
GET    /api/runs/{id}
GET    /api/runs/{id}/compare?other={id2},{id3}
```

### Design Principles

- **Consistency**: All interfaces use the same engine
- **Discoverability**: Clear naming, good defaults
- **Safety**: Cost limits enforced everywhere
- **Observability**: Events expose all internal state changes
- **Flexibility**: Can swap components (actors, validators, metrics)

---

## Detailed Roadmap

### Phase 2.0: Foundation (1-2 months)

**Goals**: Enable safe refactoring + validate architectural choices

**Prerequisites**:

**Performance Baseline Establishment** (Week 0 - run before Phase 2.0 starts)
   - Measure current V1 performance to establish improvement targets
   - **Metrics to capture**:
     ```bash
     scenario-lab benchmark scenarios/test-regulation-negotiation
     # Outputs:
     # - Average turn time: [measure]
     # - P95 turn time: [measure]
     # - Memory usage peak: [measure]
     # - Cost per turn: [measure]
     # - Startup time: [measure]
     ```
   - **Purpose**: V2 performance goals will be relative to baseline
     - Turn execution: Target -20% time vs baseline
     - Memory usage: Target -30% vs baseline (through optimizations)
     - Startup time: Target <2s (absolute)
   - **Deliverable**: `docs/performance-baseline.md` with benchmark results

**Architecture Validation Spike** (Week 0 - 1 week before full commitment)
   - Proof-of-concept: Event-driven orchestrator with phase isolation
   - **Goals**:
     - Validate event bus performance (overhead <10% vs monolithic)
     - Test phase isolation pattern with one real scenario
     - Measure memory overhead and execution time
     - Verify WebSocket integration works cleanly
     - Identify unforeseen integration pain points
   - **Success Criteria**:
     - Can execute full test-regulation-negotiation scenario
     - Event overhead <10% vs current run_scenario.py
     - Phase boundaries are clean (no shared mutable state)
     - WebSocket updates work without blocking execution
     - Team confident in architecture direction
   - **Deliverable**: Go/No-go decision document with findings

**Deliverables**:

1. **Pydantic Schemas** (Week 1-2)
   - `ScenarioConfig`, `ActorConfig`, `MetricsConfig` models
   - Validation on load (catches 80% of user errors)
   - Backward compatible: convert YAML → Pydantic → YAML
   - **Impact**: Immediate error reduction

2. **Integration Tests** (Week 2-3)
   - Mock LLM responses (deterministic outputs)
   - Test full scenarios end-to-end
   - Resume/branch regression tests
   - Golden file comparisons
   - **Impact**: Safe to refactor

   **Mock Strategy**:
   ```python
   class DeterministicLLM:
       """Returns pre-scripted responses for reproducible testing"""
       def __init__(self, responses: dict[str, str]):
           self.responses = responses
           self.call_count = 0

       async def generate(self, prompt: str, **kwargs) -> str:
           # Return based on call sequence for determinism
           key = f"{kwargs.get('actor', 'system')}_{self.call_count}"
           self.call_count += 1
           return self.responses.get(key, self._default_response(prompt))

       def _default_response(self, prompt: str) -> str:
           # Minimal valid response structure
           return '{"goals": [], "reasoning": "test", "action": "wait"}'
   ```

   **Test Coverage Requirements**:
   - Minimum 5 golden-file scenarios (happy path)
   - Edge cases: rate limits (429), partial responses, timeout recovery
   - Cost tracking validation (without real API calls)
   - Resume/branch with mocked state
   - Multi-turn consistency checks
   - Target: 80% code coverage, 100% critical path coverage

3. **Structured Logging** (Week 3)
   - Replace print() with proper logging
   - Add context (turn, actor, phase)
   - Cost tracking in logs
   - **Impact**: Debuggable production runs

4. **JSON Agent Outputs** (Week 4)
   - Actors output `{"goals": [...], "reasoning": "...", "action": "..."}`
   - Generate markdown from JSON (keep human readability)
   - Fallback parser for v1 scenarios
   - **Impact**: Eliminates parsing fragility

**Success Criteria**:
- All v1 scenarios still run
- New scenarios use schemas
- 200+ tests passing
- Zero print() in core code

### Phase 2.1: Modular Engine (2-3 months)

**Goals**: Refactor execution while maintaining v1 compatibility

**Deliverables**:

1. **ScenarioOrchestrator** (Week 5-7)
   ```python
   class ScenarioOrchestrator:
       async def execute_turn(self, state: ScenarioState) -> TurnResult:
           # Event-driven phase execution
           await self.emit('turn_started', turn=state.turn)

           comms_result = await self.communication_phase.execute(state)
           await self.emit('phase_complete', phase='communications')

           decisions_result = await self.decision_phase.execute(state)
           # ... etc
   ```
   - Each phase is a separate service
   - State is immutable between phases
   - Events for observability
   - **Impact**: Web integration becomes trivial

2. **Phase Services** (Week 7-10)
   - Extract each phase from run_scenario.py
   - Unit tests for each phase
   - Mock-friendly interfaces
   - Reuse existing components (ActorEngine, WorldStateUpdater, etc.)
   - **Impact**: Maintainable, testable

3. **Execution Modes** (Week 10-11)
   - `SyncExecutor` (current CLI behavior)
   - `AsyncExecutor` (for web API)
   - `BatchExecutor` (parallel runs)
   - All use same orchestrator
   - **Impact**: One engine, multiple interfaces

4. **Migration Path** (Week 11-12)
   - run_scenario.py becomes thin wrapper over orchestrator
   - Existing scenarios run unchanged
   - New `scenario-lab run` CLI with rich output
   - **Impact**: Smooth transition

**Success Criteria**:
- run_scenario.py is <200 lines
- Web API can execute scenarios
- Batch processing works with new engine
- Performance is equal or better

**Non-Negotiable Requirements** (Cost Management):
   - V1's cost tracking strength MUST be preserved and enhanced
   - **Mandatory features**:
     - All LLM calls go through centralized cost tracker (no bypass possible)
     - Credit limits enforced at orchestrator level before execution
     - Cost estimates shown before any scenario execution
     - Real-time cost updates during execution (via events)
     - Cost tracking survives crashes/resumes (persisted state)
     - Per-actor, per-phase, and total cost breakdowns
   - **Acceptance criteria**:
     - Cost tracking accuracy: ±2% of actual API costs
     - Credit limit enforcement: 100% (never exceeded)
     - Resume preserves exact cost state
     - Cost estimation available in <1s
   - **Why critical**: Cost controls are what makes experimentation safe. Regression here makes V2 unusable for research.

### Phase 2.2: Database & Analytics (1-2 months)

**Goals**: Move from files to database without losing file artifacts

**Deliverables**:

1. **SQLite Schema** (Week 13-14)
   ```sql
   -- Runs table
   runs(id, scenario, created, status, total_cost, ...)

   -- Turns table
   turns(id, run_id, turn_num, timestamp, ...)

   -- Decisions table
   decisions(id, turn_id, actor, goals, reasoning, action, ...)

   -- Metrics table
   metrics(id, turn_id, name, value, ...)

   -- Communications table
   communications(id, turn_id, type, participants, content, ...)
   ```
   - Still write markdown files (for expert review)
   - Also store in SQLite (for analytics)
   - **Impact**: Fast queries

2. **Query API** (Week 14-15)
   ```python
   # New capabilities:
   db.runs.filter(scenario='ai-summit').where(cost < 1.0)
   db.metrics.aggregate('cooperation_level').by_scenario()
   db.decisions.for_actor('EU').across_runs()
   ```
   - Replaces file parsing in compare_runs.py
   - Orders of magnitude faster
   - **Impact**: Rich analytics

3. **Migration Tools** (Week 15-16)
   - `scenario-lab import` loads v1 runs into database
   - Preserves all data
   - Can regenerate markdown from database
   - **Impact**: Historic runs remain valuable

**Migration Scenarios** (Support all user transition paths):

**Scenario A: Gradual Adoption**
   - User continues running new scenarios with V1
   - Occasionally tests V2 features
   - **Approach**:
     - V1 and V2 write to separate directories
     - `scenario-lab import` syncs V1 runs → database when convenient
     - Compare tool works across both (reads files + DB)
   - **Timeline**: Indefinite coexistence

**Scenario B: Active Migration**
   - User commits to V2 for new work
   - Wants historic data accessible
   - **Approach**:
     - New runs use V2 (write to DB + markdown files)
     - Old runs imported on-demand (lazy loading)
     - `scenario-lab import output/` for bulk import
     - Dashboard shows both old and new runs seamlessly
   - **Timeline**: 1-2 weeks transition period

**Scenario C: Complete Migration**
   - User wants full V2 benefits
   - Willing to do one-time migration
   - **Approach**:
     - One-time import: `scenario-lab import --all output/`
     - Verification: Check counts, spot-check runs
     - V1 retired (but `run_scenario.py` still works for reproduction)
     - All analytics now database-powered
   - **Timeline**: 1-2 days for import + verification

**Migration Safety**:
   - Import is idempotent (safe to re-run)
   - Original files never modified
   - Can rollback by deleting database
   - Validation report shows import success rate

**Success Criteria**:
- compare_runs.py query time: 10s → <1s
- analyze_patterns.py works on database
- Markdown files still generated
- Can query across 1000+ runs

### Phase 2.3a: Core Web Interface (2 months)

**Goals**: Enable core human-in-the-loop workflow via web

**Deliverables**:

1. **React Frontend Foundation** (Week 17-19)
   - Project setup: React + TypeScript + TailwindCSS + Vite
   - Authentication & session management (see Security section below)
   - Responsive layout shell
   - WebSocket integration with backend
   - **Impact**: Foundation for all web features

**Security & Access Control** (integrated throughout Phase 2.3a):
   - **Authentication**: Local-first approach (no cloud accounts required initially)
     - Simple password protection for web interface
     - Session tokens with expiration
     - Optional: OAuth2 for team deployments (future)
   - **Authorization**: Role-based access control
     - Read-only users: View scenarios and results
     - Operators: Execute scenarios, control actors
     - Admins: Create/edit scenarios, manage API keys
   - **Scenario Visibility**: Private by default
     - Scenarios owned by creator
     - Explicit sharing for collaboration
   - **API Key Management**: Secure storage for LLM credentials
     - Encrypted at rest (using OS keyring)
     - Never exposed in logs or responses
     - Per-user or shared keys (configurable)
   - **Rate Limiting**: Prevent accidental cost explosions
     - Per-user execution limits (e.g., 3 concurrent scenarios)
     - Per-user cost budgets (daily/weekly)
     - Hard stops at credit limits
   - **Audit Log**: Track all significant actions
     - Who executed what scenario, when
     - Cost attribution per user
     - Configuration changes logged
     - Retention: 90 days default
   - **Why critical**: Multi-user deployments need clear boundaries to prevent accidents and attribute costs correctly

2. **Real-Time Monitoring** (Week 19-21)
   - Live scenario execution view
   - Turn-by-turn progress display
   - Cost tracking widget
   - Phase status indicators
   - Pause/resume controls
   - **Impact**: Makes scenarios observable

3. **Human Actor Interface** (Week 21-23)
   - Actor decision input form
   - Context display (world state, communications)
   - Decision validation before submission
   - **Impact**: Core human-in-the-loop capability

4. **Scenario Browser** (Week 23-24)
   - List available scenarios
   - View scenario details
   - Basic run history
   - Start new run with parameters
   - **Impact**: Usable without CLI

**Success Criteria**:
- Human can control actors via web
- Real-time monitoring works smoothly
- WebSocket updates <500ms latency
- Works on mobile devices
- Can start/stop/resume scenarios

### Phase 2.3b: Advanced UX & Analytics (2-3 months)

**Goals**: Rich editing and analytics capabilities

**Deliverables**:

1. **Scenario Editor** (Week 25-28)
   - Visual YAML editor with syntax highlighting
   - Live schema validation with error highlighting
   - Actor templates library
   - Scenario templates (common patterns)
   - Test/preview mode (dry-run with cost estimate)
   - **Impact**: Lower barrier to entry, faster iteration

2. **Analytics Dashboard** (Week 28-31)
   - Metrics visualization over time (Recharts)
   - Compare runs side-by-side (diff view)
   - Pattern recognition results display
   - Cost analysis and breakdowns
   - Export to CSV/JSON
   - Filter and search across runs
   - **Impact**: Research insights without CLI tools

3. **Run Comparison Tool** (Week 31-32)
   - Visual diff of world states
   - Actor decision comparison
   - Metrics comparison charts
   - Branch visualization
   - **Impact**: Deep analysis capability

**Success Criteria**:
- Can create new scenarios entirely in web UI
- Scenarios validated before execution
- Analytics replace CLI tools for 80% of use cases
- Comparison works for 100+ run datasets
- Export works for all data formats

---

## Technical Decisions

### 1. Event-Driven Architecture

**Why**: Decouples components, enables observability, natural for async

**Implementation**:
```python
from dataclasses import dataclass
from typing import Any, Callable
import asyncio

@dataclass
class Event:
    type: str
    data: dict[str, Any]
    timestamp: float

class EventBus:
    def __init__(self):
        self.handlers: dict[str, list[Callable]] = {}

    async def emit(self, event_type: str, **data):
        event = Event(type=event_type, data=data, timestamp=time.time())
        for handler in self.handlers.get(event_type, []):
            await handler(event)

    def on(self, event_type: str, handler: Callable):
        self.handlers.setdefault(event_type, []).append(handler)
```

**Benefits**:
- WebSocket updates are just event handlers
- Metrics tracking is an event handler
- Logging is an event handler
- Easy to add new observers

### 2. Immutable State Between Phases

**Why**: Prevents subtle bugs, enables time-travel debugging, testable

**Implementation**:
```python
@dataclass(frozen=True)
class ScenarioState:
    turn: int
    world_state: WorldState
    actors: dict[str, ActorState]
    communications: list[Communication]
    metrics: dict[str, float]

    def with_turn(self, turn: int) -> 'ScenarioState':
        return replace(self, turn=turn)

    def with_decision(self, actor: str, decision: Decision) -> 'ScenarioState':
        new_actors = {**self.actors, actor: decision}
        return replace(self, actors=new_actors)
```

**Benefits**:
- Can rollback to any state
- Phases can't accidentally corrupt state
- Easy to implement branching

### 3. Validation at Every Boundary

**Why**: Fail fast, clear errors, safe refactoring

**Layers**:
1. **YAML Load**: Pydantic validates schema
2. **Actor Output**: JSON schema validation
3. **World Update**: Consistency checks
4. **QA Validator**: Semantic validation
5. **Database Write**: Constraint checks

### 4. Backward Compatibility Strategy

**Principle**: V1 scenarios always work, V2 is opt-in

**Approach**:
```python
def load_scenario(path: str) -> ScenarioConfig:
    yaml_data = load_yaml(path)

    if 'schema_version' in yaml_data:
        # V2 scenario with schema
        return ScenarioConfig.parse_obj(yaml_data)
    else:
        # V1 scenario - convert
        return convert_v1_to_v2(yaml_data)
```

**Migration Path**:
- Run `scenario-lab validate` to check v1 scenarios
- Run `scenario-lab upgrade` to add schemas
- Old scenarios work forever

---

## Organizational Considerations

### Team Size Assumptions

**Current (Phase 3)**: 1 developer (you + me)
**V2.0-2.2**: 1-2 developers (backend focus)
**V2.3a (Core Web)**: 2 developers (1 backend + 1 frontend)
**V2.3b (Advanced UX)**: 2-3 developers (frontend expertise critical)

### Timeline

**By Phase**:
- Phase 2.0 (Foundation): 2-3 months
- Phase 2.1 (Modular Engine): 3-4 months
- Phase 2.2 (Database): 2-3 months
- Phase 2.3a (Core Web): 2-3 months
- Phase 2.3b (Advanced UX): 2-3 months

**Total Timeline**:
- **Optimistic**: 8-10 months (with 2 full-time developers, phases overlap)
- **Realistic**: 12-15 months (with 1.5 developers average, sequential phases)
- **Conservative**: 18-24 months (with 1 part-time developer, interruptions)

**Key Dependencies**:
- 2.1 can start before 2.0 fully complete (schemas + tests enable refactor)
- 2.2 requires 2.1 complete (database schema depends on final state model)
- 2.3a requires 2.1 complete (web API needs orchestrator)
- 2.3b can partially overlap with 2.2 (analytics needs database)

### Risk Mitigation

**Risk**: Rewrite takes too long, V1 users suffer
**Mitigation**: Incremental phases, V1 always works

**Risk**: Breaking changes alienate early adopters
**Mitigation**: Backward compatibility, migration tools

**Risk**: Over-engineering before product-market fit
**Mitigation**: Only build what's proven necessary, defer premature optimization

### User Communication

**During V2 Development**:
1. **Roadmap visibility**: Keep ROADMAP.md updated
2. **Migration guides**: Document upgrade path
3. **Breaking change warnings**: Deprecation notices
4. **Preview releases**: Let users test V2 before migration

---

## What Makes This Plan Different from version-2.md

### Additional Insights

1. **Phase 3 web work is V1.5, not V2**
   - We're learning what modular architecture needs
   - ScenarioExecutor pattern is the bridge
   - This work informs V2 design

2. **Event-driven architecture is key**
   - version-2.md didn't emphasize this
   - Events are how web integration actually works
   - Natural fit for observability

3. **Immutable state is game-changing**
   - Enables safe parallelization
   - Makes branching trivial
   - Time-travel debugging for free

4. **The database is for analytics, not execution**
   - version-2.md suggested full database migration
   - Better: Keep files for artifacts, use DB for queries
   - Hybrid approach preserves simplicity

5. **Backward compatibility is essential**
   - version-2.md didn't address migration
   - This plan ensures V1 users aren't stranded

### What We Kept from version-2.md

- ✅ Pydantic schemas (critical)
- ✅ Modular phases (essential)
- ✅ JSON outputs + markdown views (correct balance)
- ✅ Integration tests (necessary)
- ✅ Structured logging (quick win)

### What We Adjusted

- **Parallel execution**: Deferred to "only if needed"
- **Plugin system**: Removed from scope (YAGNI)
- **Packaging**: Simplified to "pip installable" only
- **Database**: Hybrid file + DB, not full migration

---

## Success Metrics

### Technical Health
- Test coverage >80%
- Integration test suite runs <5 minutes
- Zero print() statements in core
- All scenarios schema-validated
- Logs are structured (JSON)

### User Experience
- Web dashboard usage >50% of runs (Phase 2.3a)
- Average time to create scenario: <30 min (Phase 2.3b with editor)
- Human actor participation in >20% of runs (Phase 2.3a)
- Comparison/analysis via web, not CLI (Phase 2.3b)
- Schema validation catches >80% of user errors before execution (Phase 2.0)

### Research Impact
- Batch runs of 100+ scenarios
- Published research using the platform
- Community-contributed scenarios
- Average cost per run <$0.50

### Performance
- Startup time <2 seconds
- Turn execution time <5 seconds (for typical scenario)
- Database query time <1 second (for 1000 runs)
- Can execute 10 concurrent scenarios

---

## Migration Strategy

### For End Users

**Phase 2.0** (Schemas):
```bash
# Check v1 scenarios
scenario-lab validate scenarios/my-scenario

# Upgrade to v2 format (adds schema_version)
scenario-lab upgrade scenarios/my-scenario

# Or keep using v1 format (works forever)
```

**Phase 2.1** (New Engine):
```bash
# V1 command still works
python src/run_scenario.py scenarios/my-scenario

# New command (same behavior, better output)
scenario-lab run scenarios/my-scenario

# Or use Python SDK
from scenario_lab import Scenario
scenario = Scenario.load('scenarios/my-scenario')
result = scenario.run(end_turn=10)
```

**Phase 2.2** (Database):
```bash
# Import historic runs
scenario-lab import output/

# Query from Python
from scenario_lab.db import RunDatabase
db = RunDatabase('scenario-lab.db')
runs = db.runs.filter(scenario='ai-summit', cost__lt=1.0)
```

**Phase 2.3** (Web):
```bash
# Start web server
scenario-lab serve

# Access at http://localhost:8000
# All CLI features available in web UI
```

### For Developers

- V1 codebase remains in `src/` (frozen)
- V2 code in `scenario_lab/` package
- Tests for both
- V1 is thin wrapper over V2
- Deprecation warnings guide migration

---

## Conclusion

Version 2 isn't about discarding Version 1 - it's about evolving a successful prototype into a production platform. By taking an incremental approach with clear phases, backward compatibility, and realistic timelines, we can achieve the architectural improvements needed for scale while keeping existing users productive.

The key insight: **The web interface work (Phase 3) is teaching us how to architect V2.** The modular executor pattern, event-driven updates, and async execution are all V2 patterns emerging organically from real needs.

**Recommendation**: Complete Phase 3 (web backend + basic frontend) as currently scoped. This gives us battle-tested patterns for V2.0. Then begin V2.0 (schemas + tests) while maintaining momentum.

The future is bright. We're building something researchers actually want.

---

## Version 2.1 Plan Improvements (2025-11-16)

This plan has been enhanced with the following critical additions:

### Risk Reduction
1. **Architecture Validation Spike**: 1-week proof-of-concept before Phase 2.0 commitment to validate event-driven architecture and identify integration issues early
2. **Performance Baselines**: Establish measurable V1 baseline to track V2 improvements objectively

### Quality & Safety
3. **Concrete Test Strategy**: Detailed mock patterns, coverage requirements (80% overall, 100% critical path), and edge case specifications
4. **Cost Management Requirements**: Explicit non-negotiable requirements ensuring V2 preserves V1's cost control strengths (±2% accuracy, 100% credit limit enforcement)

### Clarity & Scope
5. **Target API Design**: Clear contract for Python SDK, CLI, and Web API that all architectural decisions support
6. **Phase 2.3 Split**: Divided into 2.3a (Core Web, 2 months) and 2.3b (Advanced UX, 2-3 months) for more achievable milestones and earlier value delivery
7. **Realistic Timeline**: Updated to 8-24 months depending on team size, with explicit phase dependencies

### User Experience
8. **Security Design**: Comprehensive authentication, authorization, API key management, and audit logging for multi-user deployments
9. **Migration Scenarios**: Three concrete migration paths (Gradual/Active/Complete) supporting different user needs and timelines

### Impact
These improvements strengthen the plan by:
- **Reducing risk** through validation spike and comprehensive testing
- **Ensuring quality** with explicit cost management and security requirements
- **Improving execution** with clearer API contracts and manageable phases
- **Supporting users** with flexible migration paths and safety guarantees

The enhanced plan maintains the original vision while adding critical details that increase likelihood of successful delivery.
