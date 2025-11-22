# Scenario Lab - Architecture Ground Truth

> **Purpose**: This document is the authoritative reference for AI agents working with the codebase. It describes architecture, data structures, design patterns, and conventions that apply to the project. When there is conflict between tests and code, use this document to determine what is correct.

> **Status**: V2 Pure Architecture (2025-11-20). All V1 code has been removed. The system is 100% V2.

---

## 1. Architecture Overview

### 1.1 Core Principles

Scenario Lab is built on four fundamental principles:

1. **Immutability**: All state is immutable (frozen dataclasses). Operations return new state objects.
2. **Async-first**: All LLM calls are asynchronous. Phases implement `async execute()`.
3. **Event-driven**: Components communicate via EventBus, not direct calls.
4. **Composition**: Services are composed, not inherited. Dependencies are injected.

### 1.2 Package Structure

```
scenario_lab/
├── core/                    # Core logic and domain objects
│   ├── actor.py            # Immutable Actor dataclass
│   ├── events.py           # EventBus and EventType enum
│   ├── orchestrator.py     # Phase coordination
│   ├── prompt_builder.py   # LLM prompt construction
│   ├── world_synthesizer.py # World synthesis from decisions
│   ├── context_manager.py  # Context window and summarization
│   ├── communication_manager.py # Actor communication
│   ├── metrics_tracker_v2.py   # Metrics extraction (Pydantic)
│   └── qa_validator_v2.py      # Quality assurance (Pydantic)
│
├── models/                  # Immutable state dataclasses
│   └── state.py            # ScenarioState, WorldState, etc.
│
├── schemas/                 # Pydantic validation schemas
│   ├── scenario.py         # ScenarioConfig
│   ├── actor.py            # ActorConfig
│   ├── metrics.py          # MetricsConfig
│   ├── validation.py       # ValidationConfig
│   └── exogenous_events.py # ExogenousEventsConfig
│
├── loaders/                 # YAML configuration loaders
│   ├── scenario_loader.py  # Loads scenario.yaml + actors
│   ├── actor_loader.py     # Loads actors/*.yaml
│   ├── metrics_loader.py   # Loads metrics.yaml
│   └── validation_loader.py # Loads validation-rules.yaml
│
├── services/                # Phase implementations
│   ├── decision_phase_v2.py     # Actor decisions (pure V2)
│   ├── world_update_phase_v2.py # World update (pure V2)
│   ├── communication_phase.py   # Communication phase
│   ├── persistence_phase.py     # File output
│   └── database_persistence_phase.py # Database storage (optional)
│
├── runners/                 # Execution runners
│   └── sync_runner.py      # Pure V2 synchronous runner
│
├── batch/                   # Batch processing
│   ├── parameter_variator.py    # Variation generation
│   ├── batch_runner.py          # Batch orchestration
│   ├── batch_cost_manager.py    # Budget tracking
│   └── batch_analyzer.py        # Statistical analysis
│
├── interfaces/              # User interfaces
│   └── cli.py              # Click-based CLI
│
├── api/                     # REST API
│   └── app.py              # FastAPI application
│
└── utils/                   # Cross-cutting utilities
    ├── api_client.py       # LLM API calls
    ├── response_parser.py  # LLM response parsing
    ├── response_cache.py   # SHA256 caching
    ├── model_pricing.py    # Cost calculation
    ├── state_persistence.py # State serialization
    └── error_handler.py    # Error handling
```

---

## 2. Data Models (Ground Truth)

### 2.1 ScenarioState

**Location**: `scenario_lab/models/state.py`

ScenarioState is the central state object that flows through execution.

```python
@dataclass(frozen=True)
class ScenarioState:
    # Identifiers
    scenario_id: str
    scenario_name: str
    run_id: str

    # Status
    status: ScenarioStatus  # created|running|paused|completed|halted|failed
    turn: int               # Current turn (0-indexed internally, 1-indexed in files)
    current_phase: Optional[PhaseType]

    # Core data
    world_state: WorldState
    actors: Dict[str, ActorState]

    # Turn data
    communications: List[Communication]  # All communications
    decisions: Dict[str, Decision]       # Current turn's decisions (per actor)

    # Tracking
    metrics: List[MetricRecord]
    costs: List[CostRecord]

    # Metadata
    execution_metadata: Dict[str, Any]
    triggered_events: List[str]
```

**Transformation methods** (always return new objects):

- `with_turn(turn: int) -> ScenarioState`
- `with_status(status: ScenarioStatus) -> ScenarioState`
- `with_world_state(world_state: WorldState) -> ScenarioState`
- `with_decision(actor: str, decision: Decision) -> ScenarioState`
- `with_cost(cost: CostRecord) -> ScenarioState`
- `with_metric(metric: MetricRecord) -> ScenarioState`
- `with_communication(comm: Communication) -> ScenarioState`
- `with_actor(name: str, actor_state: ActorState) -> ScenarioState`
- `with_started() -> ScenarioState`
- `with_completed() -> ScenarioState`

**Computed properties**:

- `total_cost() -> float`: Sums all costs
- `actor_cost(name: str) -> float`: Cost for specific actor
- `phase_cost(phase: PhaseType) -> float`: Cost per phase
- `get_metrics_by_name(name: str) -> List[MetricRecord]`: Filters metrics

**Serialization**:

- `to_dict() -> Dict`: Converts to JSON-compatible dict
- `ScenarioState.from_dict(d: Dict) -> ScenarioState`: Reconstructs from dict

### 2.2 WorldState

```python
@dataclass(frozen=True)
class WorldState:
    turn: int           # Turn when this state was created
    content: str        # Markdown description of the world
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_content(self, content: str) -> WorldState:
        """Returns new WorldState with updated content"""
```

### 2.3 ActorState

```python
@dataclass(frozen=True)
class ActorState:
    name: str
    short_name: str
    model: str
    current_goals: List[str]
    recent_decisions: List[Decision]  # Last 5 decisions
    private_information: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_decision(self, decision: Decision) -> ActorState:
        """Adds decision, updates goals, trims history to 5"""
```

### 2.4 Decision

```python
@dataclass(frozen=True)
class Decision:
    actor: str
    turn: int
    goals: List[str]        # Actor's goals at decision time
    reasoning: str          # Reasoning/analysis
    action: str             # Concrete action
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.5 Communication

```python
@dataclass(frozen=True)
class Communication:
    turn: int
    sender: str
    recipients: List[str]   # Empty list = public
    content: str
    comm_type: str          # 'bilateral' | 'coalition' | 'public'
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.6 CostRecord

```python
@dataclass(frozen=True)
class CostRecord:
    timestamp: datetime
    actor: Optional[str]    # None for system costs
    phase: str              # 'decision' | 'world_update' | 'validation' etc.
    model: str              # 'openai/gpt-4o' etc.
    input_tokens: int
    output_tokens: int
    cost: float             # In USD
```

### 2.7 MetricRecord

```python
@dataclass(frozen=True)
class MetricRecord:
    name: str               # Metric ID from metrics.yaml
    turn: int
    value: Any              # float | str | bool depending on type
    actor: Optional[str]    # None for global metrics
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.8 Enums

```python
class ScenarioStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    HALTED = "halted"
    FAILED = "failed"

class PhaseType(Enum):
    COMMUNICATION = "communication"
    COALITION = "coalition"
    DECISION = "decision"
    WORLD_UPDATE = "world_update"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"
```

---

## 3. Phase Execution Flow

### 3.1 Sequence Per Turn

```
TURN START
  │
  ├─→ Emit TURN_STARTED event
  │
  ▼
COMMUNICATION PHASE (if enabled)
  │ - Bilateral negotiations
  │ - Coalition proposals
  │ - Public statements
  │ - → state with Communications
  │
  ▼
DECISION PHASE
  │ For each actor (concurrent):
  │   1. ContextManager → contextualized world state
  │   2. CommunicationManager → visible communications
  │   3. PromptBuilder → decision prompt
  │   4. APIClient → LLM call
  │   5. ResponseParser → Decision object
  │   6. → state with Decision + CostRecord
  │
  │ Writes: actor-name-NNN.md
  │
  ▼
WORLD UPDATE PHASE
  │ 1. Collect all decisions from turn
  │ 2. WorldSynthesizer → synthesis prompt
  │ 3. APIClient → LLM call
  │ 4. ResponseParser → new world state
  │ 5. MetricsTracker → extract metrics (if metrics.yaml exists)
  │ 6. → state with WorldState + MetricRecords + CostRecord
  │
  │ Writes: world-state-NNN.md
  │
  ▼
VALIDATION PHASE (if validation-rules.yaml exists)
  │ 1. Validate decisions against actor goals
  │ 2. Validate world state coherence
  │ 3. Validate information access
  │ 4. → state with ValidationRecords + CostRecord
  │
  │ Writes: validation-NNN.md
  │
  ▼
PERSISTENCE PHASE
  │ 1. StatePersistence.save() → scenario-state.json
  │ 2. DatabasePersistence (if enabled)
  │ 3. Summaries
  │
  ▼
TURN END
  │
  ├─→ Emit TURN_COMPLETED event
  │
  ├─→ Check credit_limit → HALTED if exceeded
  ├─→ Check end_turn → COMPLETED if reached
  │
  └─→ Continue to next turn or finish
```

### 3.2 Key Principles

1. **Simultaneous turn execution**: All actors make decisions in parallel within a turn
2. **State immutability**: Each phase receives state, returns new state
3. **Event-driven monitoring**: Events emitted at each milestone
4. **Error isolation**: One actor's failure doesn't crash the entire phase
5. **Context window**: ContextManager prevents token overflow

---

## 4. Configuration Schemas

### 4.1 scenario.yaml

```yaml
# REQUIRED FIELDS
name: string                      # Scenario name
initial_world_state: |            # Markdown, can be multiline
  Description of the world's initial state...
turn_duration: "6 months"         # Pattern: "N unit"
actors:                           # List of actor filenames (without .yaml)
  - actor-one
  - actor-two

# TEMPORAL (one of these required)
turns: 10                         # Simple: number of turns
# OR
scenario_length:
  type: fixed                     # 'fixed' or 'condition'
  turns: 10                       # If type=fixed
  condition: "..."                # If type=condition

# OPTIONAL SETTINGS
world_state_model: "openai/gpt-4o-mini"    # Default LLM
system_prompt: string                       # Scenario-level prompt
description: string
context_window_size: 3                      # Number of turns in full detail

# COMMUNICATION
enable_bilateral_communication: true
enable_coalition_formation: false
enable_public_statements: true
max_communications_per_turn: 2

# ADVANCED
enable_black_swans: false
allow_actor_reflection: false
parallel_action_resolution: true
```

### 4.2 actors/*.yaml

```yaml
# REQUIRED
name: "Full Actor Name"           # Display name
short_name: actor-id              # Identifier (lowercase, hyphens)
llm_model: "openai/gpt-4o"        # Or "model:"

# BEHAVIOR
goals:                            # List or multiline string
  - "Primary goal"
  - "Secondary goal"
role: "Actor's role description"
description: |
  Longer description of the actor...

# OPTIONAL
constraints:
  - "Constraint 1"
expertise:
  domain: "level"
decision_style: "Analytical and cautious"
private_information: |
  Information only this actor has...
control: ai                       # 'ai' or 'human'
```

### 4.3 metrics.yaml

```yaml
metrics:
  - name: metric_identifier       # lowercase_underscore
    description: "What this measures"
    type: continuous              # continuous | categorical | boolean
    range: [0, 100]               # For continuous
    extraction:
      type: llm                   # llm | keyword | pattern | manual
      prompt: "Evaluate X on scale 0-100"
    unit: "percent"
    actor_specific: false

export_format: json               # json | csv | both
auto_export: true
```

### 4.4 validation-rules.yaml

```yaml
validation_model: "openai/gpt-4o-mini"
checks:
  actor_decision_consistency:
    enabled: true
    severity: medium              # low | medium | high
  world_state_coherence:
    enabled: true
    severity: high
  information_access_consistency:
    enabled: true
run_after_each_turn: true
generate_turn_reports: true
halt_on_critical: false
```

---

## 5. Design Patterns

### 5.1 Immutable Update Pattern

```python
# WRONG - mutation
state.actors[name].goals = new_goals  # Crashes (frozen)

# RIGHT - return new object
from dataclasses import replace
new_actor = replace(actor, current_goals=new_goals)
state = state.with_actor(name, new_actor)
```

### 5.2 Async Phase Service Pattern

```python
class ExamplePhase:
    """All phases follow this pattern"""

    def __init__(self, api_client: APIClient, ...):
        self.api_client = api_client  # Inject dependencies

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Receives immutable state, returns new immutable state.
        MUST NOT mutate state.
        """
        # Do work
        result = await self.api_client.call(...)

        # Return new state
        return state.with_something(result)
```

### 5.3 Event Emission Pattern

```python
from scenario_lab.core.events import get_event_bus, EventType

bus = get_event_bus()

# Emit event
await bus.emit(
    EventType.PHASE_COMPLETED,
    data={
        "phase": "decision",
        "turn": state.turn,
        "cost": cost_record.cost,
    },
    source="decision_phase",
    correlation_id=state.run_id
)

# Listen to event
@bus.on(EventType.TURN_COMPLETED)
async def handle_turn(event):
    print(f"Turn {event.data['turn']} done")
```

### 5.4 Composition Pattern

```python
# WRONG - inheritance
class DecisionPhase(BasePhase):  # Avoid inheritance
    pass

# RIGHT - composition
class DecisionPhaseV2:
    def __init__(self, context_manager, api_client, prompt_builder):
        self.context_manager = context_manager  # Compose
        self.api_client = api_client
        self.prompt_builder = prompt_builder
```

### 5.5 Lazy Import Pattern

```python
# For optional dependencies
try:
    from scenario_lab.database import Database
except ImportError:
    Database = None

def save_to_database(data):
    if Database is None:
        logger.warning("Database not available")
        return
    Database.save(data)
```

---

## 6. Conventions

### 6.1 File Naming Conventions

```
# Markdown output (NNN = turn number with zero padding)
world-state-001.md
world-state-002.md
actor-name-001.md
actor-name-002.md
validation-001.md

# State files
scenario-state.json      # Main state
costs.json              # Cost summary
metrics.json            # Metric data
```

### 6.2 Naming Conventions

```python
# Classes: PascalCase
class ScenarioState:
class DecisionPhaseV2:

# Functions and methods: snake_case
def calculate_cost():
async def execute():

# Constants: UPPER_SNAKE_CASE
DEFAULT_CONTEXT_WINDOW = 3
MAX_RETRIES = 3

# Files: lowercase with underscores or hyphens
scenario_loader.py
world-state-001.md
```

### 6.3 Import Conventions

```python
# ALWAYS import from scenario_lab.*
from scenario_lab.models.state import ScenarioState
from scenario_lab.core.events import EventBus
from scenario_lab.utils.api_client import make_llm_call_async

# NEVER import from src/ (V1 removed)
# NEVER sys.path.insert
```

### 6.4 Cost Conventions

- All LLM calls are tracked with CostRecord
- Costs in USD (float)
- Tokens separated: input_tokens, output_tokens
- Aggregation via state.total_cost(), state.actor_cost(), state.phase_cost()

### 6.5 Error Handling Conventions

```python
# Log and handle, don't re-raise if possible
try:
    result = await api_call()
except RateLimitError:
    await asyncio.sleep(exponential_backoff)
    result = await api_call()  # Retry
except Exception as e:
    logger.error(f"API call failed: {e}")
    # Return graceful default or re-raise with context
    raise ScenarioExecutionError(f"Decision phase failed: {e}") from e
```

---

## 7. Validation: Test vs Code

### 7.1 When the Code is Wrong

The code is likely wrong if:

1. **It mutates frozen dataclasses**: All state objects are `frozen=True`
2. **It imports from `src/`**: V1 is removed
3. **It uses synchronous LLM calls**: All calls should be `async`
4. **It doesn't return new state**: Phases must return `ScenarioState`
5. **It uses global variables for state**: State flows through parameters

### 7.2 When the Tests are Wrong

The tests are likely wrong if:

1. **They expect V1 behavior**: V1 is removed
2. **They test mutation of state**: Immutability is correct
3. **They mock the wrong interface**: Check against actual methods
4. **They expect synchronous calls**: V2 is async
5. **They import from `src/`**: Should import from `scenario_lab.*`

### 7.3 Priority Order

In case of conflict, prioritize:

1. **This document** - Authoritative architecture
2. **Pydantic schemas** - `scenario_lab/schemas/` defines data formats
3. **Data models** - `scenario_lab/models/state.py` defines state
4. **Phase implementations** - `scenario_lab/services/` are reference implementations
5. **Tests** - May be outdated
6. **Comments in code** - May be stale

---

## 8. Execution Entry Points

### 8.1 CLI

```bash
# Run scenario
scenario-lab run SCENARIO_PATH [OPTIONS]
  --end-turn N          # Run N turns
  --credit-limit X      # Stop at $X cost
  --resume PATH         # Resume from previous run
  --branch-from PATH    # Create branch
  --branch-at-turn N    # Branch at specific turn

# Create scenario
scenario-lab create

# Validate configuration
scenario-lab validate SCENARIO_PATH

# Batch run
scenario-lab run-batch CONFIG [--resume]

# Start API server
scenario-lab serve
```

### 8.2 Programmatic Usage

```python
from scenario_lab.runners import SyncRunner
import asyncio

runner = SyncRunner(
    scenario_path="scenarios/my-scenario",
    end_turn=10,
    credit_limit=5.0
)
runner.setup()
final_state = asyncio.run(runner.run())

print(f"Cost: ${final_state.total_cost():.2f}")
print(f"Turns: {final_state.turn}")
```

---

## 9. Batch Processing

### 9.1 Components

- **ParameterVariator**: Generates Cartesian product of variations
- **BatchCostManager**: Budget tracking and limits
- **BatchParallelExecutor**: Async execution with rate-limiting
- **BatchAnalyzer**: Statistical analysis of results

### 9.2 Batch Configuration

```yaml
base_scenario: "scenarios/my-scenario"
variations:
  - type: actor_model
    actor: us-government
    values: ["openai/gpt-4o", "anthropic/claude-3-sonnet"]
  - type: parameter
    name: context_window_size
    values: [3, 5, 7]
max_parallel: 3
cost_limit_per_run: 5.0
total_cost_limit: 100.0
```

---

## 10. API Structure

### 10.1 REST Endpoints

```
POST /api/scenarios/execute     # Start scenario
GET  /api/scenarios/{id}        # Get status
WS   /api/scenarios/{id}/stream # WebSocket for events
GET  /api/runs                  # List runs
POST /api/runs/{id}/decisions   # Human-in-the-loop decisions
DELETE /api/scenarios/{id}      # Stop scenario
```

---

## 11. Checklist for New Features

When adding new functionality:

- [ ] Place code in the correct `scenario_lab/` subdirectory
- [ ] Use immutable dataclasses for state
- [ ] Implement async/await for I/O operations
- [ ] Emit events for observability
- [ ] Inject dependencies via constructor
- [ ] Import only from `scenario_lab.*`
- [ ] Write tests that verify immutability
- [ ] Document in this document if architecturally significant
- [ ] Update CLI if user-facing

---

## 12. Version History

| Date | Version | Change |
|------|---------|--------|
| 2025-11-20 | V2.0 | V1 completely removed, pure V2 |
| 2025-11-21 | V2.1 | Test cleanup, documentation update |
| 2025-11-22 | V2.2 | Ground Truth document created |

---

*This document is the authoritative source for Scenario Lab architecture. When in doubt, consult this document first.*
