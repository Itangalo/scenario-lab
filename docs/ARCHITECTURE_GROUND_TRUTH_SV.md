# Scenario Lab - Architecture Ground Truth

> **Syfte**: Detta dokument är den auktoritativa referensen för AI-agenter som arbetar med kodbasen. Det beskriver arkitektur, datastrukturer, designmönster och konventioner som gäller för projektet. När det finns konflikt mellan tester och kod, använd detta dokument för att avgöra vad som är korrekt.

> **Status**: V2 Pure Architecture (2025-11-20). All V1-kod har tagits bort. Systemet är 100% V2.

---

## 1. Arkitekturöversikt

### 1.1 Kärnprinciper

Scenario Lab är byggt på fyra grundläggande principer:

1. **Immutabilitet**: All state är oföränderlig (frozen dataclasses). Operationer returnerar nya state-objekt.
2. **Async-first**: Alla LLM-anrop är asynkrona. Phases implementerar `async execute()`.
3. **Event-driven**: Komponenter kommunicerar via EventBus, inte direkta anrop.
4. **Komposition**: Tjänster komponeras, inte ärvs. Beroenden injiceras.

### 1.2 Paketstruktur

```
scenario_lab/
├── core/                    # Kärnlogik och domänobjekt
│   ├── actor.py            # Immutable Actor dataclass
│   ├── events.py           # EventBus och EventType enum
│   ├── orchestrator.py     # Faskoordinering
│   ├── prompt_builder.py   # LLM-promptkonstruktion
│   ├── world_synthesizer.py # Världssyntes från beslut
│   ├── context_manager.py  # Kontextfönster och sammanfattning
│   ├── communication_manager.py # Aktörkommunikation
│   ├── metrics_tracker_v2.py   # Metrisk extraktion (Pydantic)
│   └── qa_validator_v2.py      # Kvalitetssäkring (Pydantic)
│
├── models/                  # Immutable state dataclasses
│   └── state.py            # ScenarioState, WorldState, etc.
│
├── schemas/                 # Pydantic-valideringsscheman
│   ├── scenario.py         # ScenarioConfig
│   ├── actor.py            # ActorConfig
│   ├── metrics.py          # MetricsConfig
│   ├── validation.py       # ValidationConfig
│   └── exogenous_events.py # ExogenousEventsConfig
│
├── loaders/                 # YAML-konfigurationsladdare
│   ├── scenario_loader.py  # Laddar scenario.yaml + aktörer
│   ├── actor_loader.py     # Laddar actors/*.yaml
│   ├── metrics_loader.py   # Laddar metrics.yaml
│   └── validation_loader.py # Laddar validation-rules.yaml
│
├── services/                # Fasimplementationer
│   ├── decision_phase_v2.py     # Aktörbeslut (pure V2)
│   ├── world_update_phase_v2.py # Världsuppdatering (pure V2)
│   ├── communication_phase.py   # Kommunikationsfas
│   ├── persistence_phase.py     # Filutmatning
│   └── database_persistence_phase.py # Databaslagring (valfri)
│
├── runners/                 # Exekveringsrunners
│   └── sync_runner.py      # Pure V2 synkron runner
│
├── batch/                   # Batch-processering
│   ├── parameter_variator.py    # Variationsgenerering
│   ├── batch_runner.py          # Batchorkestrering
│   ├── batch_cost_manager.py    # Budgetspårning
│   └── batch_analyzer.py        # Statistisk analys
│
├── interfaces/              # Användargränssnitt
│   └── cli.py              # Click-baserad CLI
│
├── api/                     # REST API
│   └── app.py              # FastAPI-applikation
│
└── utils/                   # Tvärgående verktyg
    ├── api_client.py       # LLM API-anrop
    ├── response_parser.py  # LLM-svarsanalys
    ├── response_cache.py   # SHA256-caching
    ├── model_pricing.py    # Kostnadsberäkning
    ├── state_persistence.py # State-serialisering
    └── error_handler.py    # Felhantering
```

---

## 2. Datamodeller (Ground Truth)

### 2.1 ScenarioState

**Plats**: `scenario_lab/models/state.py`

ScenarioState är det centrala tillståndsobjektet som flödar genom exekveringen.

```python
@dataclass(frozen=True)
class ScenarioState:
    # Identifierare
    scenario_id: str
    scenario_name: str
    run_id: str

    # Status
    status: ScenarioStatus  # created|running|paused|completed|halted|failed
    turn: int               # Aktuell tur (0-indexerad internt, 1-indexerad i filer)
    current_phase: Optional[PhaseType]

    # Kärndata
    world_state: WorldState
    actors: Dict[str, ActorState]

    # Turdata
    communications: List[Communication]  # Alla kommunikationer
    decisions: Dict[str, Decision]       # Aktuell turs beslut (per aktör)

    # Spårning
    metrics: List[MetricRecord]
    costs: List[CostRecord]

    # Metadata
    execution_metadata: Dict[str, Any]
    triggered_events: List[str]
```

**Transformationsmetoder** (returnerar alltid nya objekt):

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

**Beräknade egenskaper**:

- `total_cost() -> float`: Summerar alla kostnader
- `actor_cost(name: str) -> float`: Kostnad för specifik aktör
- `phase_cost(phase: PhaseType) -> float`: Kostnad per fas
- `get_metrics_by_name(name: str) -> List[MetricRecord]`: Filtrerar metrics

**Serialisering**:

- `to_dict() -> Dict`: Konverterar till JSON-kompatibel dict
- `ScenarioState.from_dict(d: Dict) -> ScenarioState`: Rekonstruerar från dict

### 2.2 WorldState

```python
@dataclass(frozen=True)
class WorldState:
    turn: int           # Tur då detta tillstånd skapades
    content: str        # Markdown-beskrivning av världen
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_content(self, content: str) -> WorldState:
        """Returnerar ny WorldState med uppdaterat innehåll"""
```

### 2.3 ActorState

```python
@dataclass(frozen=True)
class ActorState:
    name: str
    short_name: str
    model: str
    current_goals: List[str]
    recent_decisions: List[Decision]  # Senaste 5 besluten
    private_information: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_decision(self, decision: Decision) -> ActorState:
        """Lägger till beslut, uppdaterar mål, trimmar historik till 5"""
```

### 2.4 Decision

```python
@dataclass(frozen=True)
class Decision:
    actor: str
    turn: int
    goals: List[str]        # Aktörens mål vid beslutet
    reasoning: str          # Resonemang/analys
    action: str             # Konkret handling
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.5 Communication

```python
@dataclass(frozen=True)
class Communication:
    turn: int
    sender: str
    recipients: List[str]   # Tom lista = offentligt
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
    actor: Optional[str]    # None för systemkostnader
    phase: str              # 'decision' | 'world_update' | 'validation' etc.
    model: str              # 'openai/gpt-4o' etc.
    input_tokens: int
    output_tokens: int
    cost: float             # I USD
```

### 2.7 MetricRecord

```python
@dataclass(frozen=True)
class MetricRecord:
    name: str               # Metrisk-ID från metrics.yaml
    turn: int
    value: Any              # float | str | bool beroende på typ
    actor: Optional[str]    # None för globala metrics
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

## 3. Fasexekveringsflöde

### 3.1 Sekvens per Tur

```
TUR START
  │
  ├─→ Emit TURN_STARTED event
  │
  ▼
KOMMUNIKATIONSFAS (om aktiverad)
  │ - Bilaterala förhandlingar
  │ - Koalitionsförslag
  │ - Offentliga uttalanden
  │ - → state med Communications
  │
  ▼
BESLUTSFAS
  │ For each actor (concurrent):
  │   1. ContextManager → kontextualiserad världsstat
  │   2. CommunicationManager → synliga kommunikationer
  │   3. PromptBuilder → beslutsprompt
  │   4. APIClient → LLM-anrop
  │   5. ResponseParser → Decision-objekt
  │   6. → state med Decision + CostRecord
  │
  │ Skriver: actor-name-NNN.md
  │
  ▼
VÄRLDSUPPDATERINGSFAS
  │ 1. Samla alla beslut från turen
  │ 2. WorldSynthesizer → syntesprompt
  │ 3. APIClient → LLM-anrop
  │ 4. ResponseParser → ny världsstat
  │ 5. MetricsTracker → extrahera metrics (om metrics.yaml finns)
  │ 6. → state med WorldState + MetricRecords + CostRecord
  │
  │ Skriver: world-state-NNN.md
  │
  ▼
VALIDERINGSFAS (om validation-rules.yaml finns)
  │ 1. Validera beslut mot aktörsmål
  │ 2. Validera världsstats koherens
  │ 3. Validera informationsåtkomst
  │ 4. → state med ValidationRecords + CostRecord
  │
  │ Skriver: validation-NNN.md
  │
  ▼
PERSISTENSFAS
  │ 1. StatePersistence.save() → scenario-state.json
  │ 2. DatabasePersistence (om aktiverad)
  │ 3. Sammanfattningar
  │
  ▼
TUR SLUT
  │
  ├─→ Emit TURN_COMPLETED event
  │
  ├─→ Kontrollera credit_limit → HALTED om överskriden
  ├─→ Kontrollera end_turn → COMPLETED om uppnådd
  │
  └─→ Fortsätt till nästa tur eller avsluta
```

### 3.2 Nyckelprinciper

1. **Samtidig turexekvering**: Alla aktörer fattar beslut parallellt inom en tur
2. **State immutabilitet**: Varje fas tar emot state, returnerar ny state
3. **Event-driven övervakning**: Events emitteras vid varje milstolpe
4. **Felisolering**: En aktörs fel kraschar inte hela fasen
5. **Kontextfönster**: ContextManager förhindrar tokenöverflöde

---

## 4. Konfigurationsscheman

### 4.1 scenario.yaml

```yaml
# OBLIGATORISKA FÄLT
name: string                      # Scenariots namn
initial_world_state: |            # Markdown, kan vara multiline
  Beskrivning av världens utgångsläge...
turn_duration: "6 months"         # Mönster: "N unit"
actors:                           # Lista med aktörs-filnamn (utan .yaml)
  - actor-one
  - actor-two

# TEMPORAL (en av dessa krävs)
turns: 10                         # Enkelt: antal turer
# ELLER
scenario_length:
  type: fixed                     # 'fixed' eller 'condition'
  turns: 10                       # Om type=fixed
  condition: "..."                # Om type=condition

# VALFRIA INSTÄLLNINGAR
world_state_model: "openai/gpt-4o-mini"    # Standard LLM
system_prompt: string                       # Scenario-nivå prompt
description: string
context_window_size: 3                      # Antal turer i fulldetalj

# KOMMUNIKATION
enable_bilateral_communication: true
enable_coalition_formation: false
enable_public_statements: true
max_communications_per_turn: 2

# AVANCERAT
enable_black_swans: false
allow_actor_reflection: false
parallel_action_resolution: true
```

### 4.2 actors/*.yaml

```yaml
# OBLIGATORISKA
name: "Full Actor Name"           # Visningsnamn
short_name: actor-id              # Identifierare (lowercase, bindestreck)
llm_model: "openai/gpt-4o"        # Eller "model:"

# BETEENDE
goals:                            # Lista eller multiline string
  - "Primary goal"
  - "Secondary goal"
role: "Actor's role description"
description: |
  Längre beskrivning av aktören...

# VALFRIA
constraints:
  - "Constraint 1"
expertise:
  domain: "level"
decision_style: "Analytical and cautious"
private_information: |
  Information endast denna aktör har...
control: ai                       # 'ai' eller 'human'
```

### 4.3 metrics.yaml

```yaml
metrics:
  - name: metric_identifier       # lowercase_underscore
    description: "What this measures"
    type: continuous              # continuous | categorical | boolean
    range: [0, 100]               # För continuous
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

## 5. Designmönster

### 5.1 Immutable Update Pattern

```python
# FEL - mutation
state.actors[name].goals = new_goals  # Kraschar (frozen)

# RÄTT - returnera nytt objekt
from dataclasses import replace
new_actor = replace(actor, current_goals=new_goals)
state = state.with_actor(name, new_actor)
```

### 5.2 Async Phase Service Pattern

```python
class ExamplePhase:
    """Alla faser följer detta mönster"""

    def __init__(self, api_client: APIClient, ...):
        self.api_client = api_client  # Injicera beroenden

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Tar emot immutable state, returnerar ny immutable state.
        Får INTE mutera state.
        """
        # Gör arbete
        result = await self.api_client.call(...)

        # Returnera ny state
        return state.with_something(result)
```

### 5.3 Event Emission Pattern

```python
from scenario_lab.core.events import get_event_bus, EventType

bus = get_event_bus()

# Emittera event
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

# Lyssna på event
@bus.on(EventType.TURN_COMPLETED)
async def handle_turn(event):
    print(f"Turn {event.data['turn']} done")
```

### 5.4 Composition Pattern

```python
# FEL - arv
class DecisionPhase(BasePhase):  # Undvik arv
    pass

# RÄTT - komposition
class DecisionPhaseV2:
    def __init__(self, context_manager, api_client, prompt_builder):
        self.context_manager = context_manager  # Komponera
        self.api_client = api_client
        self.prompt_builder = prompt_builder
```

### 5.5 Lazy Import Pattern

```python
# För valfria beroenden
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

## 6. Konventioner

### 6.1 Filnamnskonventioner

```
# Markdown-utdata (NNN = turnummer med nollpadding)
world-state-001.md
world-state-002.md
actor-name-001.md
actor-name-002.md
validation-001.md

# State-filer
scenario-state.json      # Huvudsaklig state
costs.json              # Kostnadssammanställning
metrics.json            # Metrisk data
```

### 6.2 Namnkonventioner

```python
# Klasser: PascalCase
class ScenarioState:
class DecisionPhaseV2:

# Funktioner och metoder: snake_case
def calculate_cost():
async def execute():

# Konstanter: UPPER_SNAKE_CASE
DEFAULT_CONTEXT_WINDOW = 3
MAX_RETRIES = 3

# Filer: lowercase med understreck eller bindestreck
scenario_loader.py
world-state-001.md
```

### 6.3 Importkonventioner

```python
# ALLTID importera från scenario_lab.*
from scenario_lab.models.state import ScenarioState
from scenario_lab.core.events import EventBus
from scenario_lab.utils.api_client import make_llm_call_async

# ALDRIG importera från src/ (V1 borttagen)
# ALDRIG sys.path.insert
```

### 6.4 Kostnadskonventioner

- Alla LLM-anrop spåras med CostRecord
- Kostnader i USD (float)
- Tokens separerade: input_tokens, output_tokens
- Aggregering via state.total_cost(), state.actor_cost(), state.phase_cost()

### 6.5 Felhanteringskonventioner

```python
# Logga och hantera, kasta inte vidare om möjligt
try:
    result = await api_call()
except RateLimitError:
    await asyncio.sleep(exponential_backoff)
    result = await api_call()  # Retry
except Exception as e:
    logger.error(f"API call failed: {e}")
    # Returnera graceful default eller re-raise med kontext
    raise ScenarioExecutionError(f"Decision phase failed: {e}") from e
```

---

## 7. Validering: Test vs Kod

### 7.1 När koden är fel

Koden är troligen fel om:

1. **Den muterar frozen dataclasses**: Alla state-objekt är `frozen=True`
2. **Den importerar från `src/`**: V1 är borttagen
3. **Den använder synkrona LLM-anrop**: Alla anrop ska vara `async`
4. **Den inte returnerar ny state**: Faser måste returnera `ScenarioState`
5. **Den använder globala variabler för state**: State flödar genom parametrar

### 7.2 När testerna är fel

Testerna är troligen fel om:

1. **De förväntar sig V1-beteende**: V1 är borttagen
2. **De testar mutation av state**: Immutabilitet är korrekt
3. **De mockar fel gränssnitt**: Kontrollera mot faktiska metoder
4. **De förväntar sig synkrona anrop**: V2 är async
5. **De importerar från `src/`**: Ska importera från `scenario_lab.*`

### 7.3 Prioriteringsordning

Vid konflikt, prioritera:

1. **Detta dokument** - Auktoritativ arkitektur
2. **Pydantic-scheman** - `scenario_lab/schemas/` definierar dataformat
3. **Datamodeller** - `scenario_lab/models/state.py` definierar state
4. **Fasimplementationer** - `scenario_lab/services/` är referensimplementationer
5. **Tester** - Kan vara föråldrade
6. **Kommentarer i kod** - Kan vara inaktuella

---

## 8. Exekveringspunkter

### 8.1 CLI

```bash
# Kör scenario
scenario-lab run SCENARIO_PATH [OPTIONS]
  --end-turn N          # Kör N turer
  --credit-limit X      # Stoppa vid $X kostnad
  --resume PATH         # Återuppta från tidigare körning
  --branch-from PATH    # Skapa gren
  --branch-at-turn N    # Gren vid specifik tur

# Skapa scenario
scenario-lab create

# Validera konfiguration
scenario-lab validate SCENARIO_PATH

# Batch-körning
scenario-lab run-batch CONFIG [--resume]

# Starta API-server
scenario-lab serve
```

### 8.2 Programmatisk användning

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

print(f"Kostnad: ${final_state.total_cost():.2f}")
print(f"Turer: {final_state.turn}")
```

---

## 9. Batchprocessering

### 9.1 Komponenter

- **ParameterVariator**: Genererar kartesisk produkt av variationer
- **BatchCostManager**: Budgetspårning och gränser
- **BatchParallelExecutor**: Asynkron exekvering med rate-limiting
- **BatchAnalyzer**: Statistisk analys av resultat

### 9.2 Batch-konfiguration

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

## 10. API-struktur

### 10.1 REST Endpoints

```
POST /api/scenarios/execute     # Starta scenario
GET  /api/scenarios/{id}        # Hämta status
WS   /api/scenarios/{id}/stream # WebSocket för events
GET  /api/runs                  # Lista körningar
POST /api/runs/{id}/decisions   # Human-in-the-loop beslut
DELETE /api/scenarios/{id}      # Stoppa scenario
```

---

## 11. Checklista för Nya Funktioner

När du lägger till ny funktionalitet:

- [ ] Placera kod i rätt `scenario_lab/`-subdirectory
- [ ] Använd immutable dataclasses för state
- [ ] Implementera async/await för I/O-operationer
- [ ] Emittera events för observabilitet
- [ ] Injicera beroenden via konstruktor
- [ ] Importera endast från `scenario_lab.*`
- [ ] Skriv tester som verifierar immutabilitet
- [ ] Dokumentera i detta dokument om det är arkitektoniskt signifikant
- [ ] Uppdatera CLI om det är användarsynligt

---

## 12. Versionshistorik

| Datum | Version | Förändring |
|-------|---------|------------|
| 2025-11-20 | V2.0 | V1 fullständigt borttagen, pure V2 |
| 2025-11-21 | V2.1 | Testrensning, dokumentationsuppdatering |
| 2025-11-22 | V2.2 | Ground Truth-dokument skapat |

---

*Detta dokument är den auktoritativa källan för Scenario Lab-arkitekturen. Vid osäkerhet, konsultera detta dokument först.*
