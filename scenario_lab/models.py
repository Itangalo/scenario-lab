"""Data models for Scenario Lab V4."""

from dataclasses import dataclass, field
from typing import Optional, Union, List
import json


@dataclass
class ModelRoute:
    """A (provider, model) pair identifying where to send an LLM request."""

    provider: str
    model: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"

    def __hash__(self) -> int:
        return hash((self.provider, self.model))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelRoute):
            return NotImplemented
        return self.provider == other.provider and self.model == other.model


@dataclass
class Metric:
    """A single quantitative metric."""

    id: str
    description: str
    value: float
    min_value: float
    max_value: float
    unit: str
    reference_points: dict[float, str] = field(default_factory=dict)

    def validate(self) -> bool:
        """Ensure value is within bounds."""
        return self.min_value <= self.value <= self.max_value

    def clamp(self) -> None:
        """Clamp value to valid range."""
        self.value = max(self.min_value, min(self.max_value, self.value))


@dataclass
class Metrics:
    """Collection of all metrics."""

    metrics: dict[str, Metric]

    def to_json(self) -> str:
        """Export as simple JSON for prompts."""
        return json.dumps({m.id: m.value for m in self.metrics.values()}, indent=2)

    def to_env(self) -> dict[str, float]:
        """Metric id -> current value, for expression evaluation."""
        return {m_id: m.value for m_id, m in self.metrics.items()}

    def update_from_json(self, json_str: str) -> None:
        """Update values from LLM response."""
        data = json.loads(json_str)
        for metric_id, value in data.items():
            if metric_id in self.metrics:
                self.metrics[metric_id].value = value
                self.metrics[metric_id].clamp()

    def update_from_dict(self, data: dict) -> None:
        """Update values from dictionary."""
        for metric_id, value in data.items():
            if metric_id in self.metrics:
                self.metrics[metric_id].value = value
                self.metrics[metric_id].clamp()


def build_expression_env(scenario: "Scenario") -> dict[str, float]:
    """Variable environment for event eligibility gates: metrics plus regime flags.

    Gate expressions may reference metric ids directly and one flag per known
    trajectory regime (`is_fast`, `is_plateau`, `is_rlvr_limited`). The regime
    is read from the run's starting-state context ("REGIME: FAST." etc.), which
    apply_initial_state folds into scenario.context; without a draw all flags
    are 0. Flags are floats so the sandboxed evaluator needs nothing beyond its
    arithmetic vocabulary.
    """
    env = scenario.metrics.to_env()
    import re

    match = re.search(r"REGIME:\s*([A-Z\-]+)\.", scenario.context or "")
    regime = match.group(1).strip().upper() if match else ""
    env["is_fast"] = 1.0 if regime == "FAST" else 0.0
    env["is_plateau"] = 1.0 if regime == "PLATEAU" else 0.0
    env["is_rlvr_limited"] = 1.0 if regime == "RLVR-LIMITED" else 0.0
    return env


@dataclass
class Event:
    """An external event that can occur."""

    id: str
    description: str
    condition: str  # Natural language condition
    probability: str  # Can be formula like "2 * unemployment / 100"
    can_repeat: bool = False
    occurred: bool = False
    # Optional deterministic eligibility gate, e.g. "public_sentiment_to_ai < 30".
    # Evaluated by Python against current metric values (same sandboxed evaluator
    # as termination conditions); a false gate removes the event from the events
    # prompt entirely and rejects any candidate for it that turn. Prose
    # conditions the metrics cannot express stay in `condition` for the LLM.
    eligible: str = ""


STATEMENT_TIERS = ("position", "commitment", "identity")


@dataclass
class Statement:
    """One adjustable thing an actor holds: a goal, a value, or a stance.

    The three are deliberately one category. What governs whether a statement
    can move is its ``tier`` -- what the actor has staked on it -- not which
    grammatical kind of thing it is.
    """

    id: str
    tier: str
    text: str

    def __post_init__(self) -> None:
        if self.tier not in STATEMENT_TIERS:
            raise ValueError(
                f"Statement '{self.id}' has tier '{self.tier}'; "
                f"expected one of {', '.join(STATEMENT_TIERS)}"
            )


@dataclass
class Actor:
    """A stakeholder in the scenario."""

    id: str
    name: str
    short_description: str
    long_description: str
    initial_statements: list[Statement] = field(default_factory=list)
    behavioral_traits: list[str] = field(default_factory=list)

    # The live ledger. Carried forward verbatim between turns; only an accepted
    # change proposal alters it, so a diff between turns is empty unless the
    # actor deliberately changed something.
    statements: list[Statement] = field(default_factory=list)
    last_actions: str = ""

    def __post_init__(self):
        if not self.statements:
            self.statements = [
                Statement(s.id, s.tier, s.text) for s in self.initial_statements
            ]

    def statement(self, statement_id: str) -> Optional[Statement]:
        """Return the live statement with this id, or None."""
        for stmt in self.statements:
            if stmt.id == statement_id:
                return stmt
        return None


@dataclass
class ResearchQuestion:
    """A question the scenario exists to answer.

    Declared in ``scenario.yaml`` so that cross-run synthesis has something
    specific to answer instead of producing generic summaries. ``metrics`` and
    ``events`` name the parts of the scenario that bear on the question; they
    are validated against the scenario's actual metrics and events, which is
    what catches a question the scenario cannot answer before runs are spent
    on it.
    """

    id: str
    question: str
    metrics: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class WorldState:
    """The narrative state of the world."""

    narrative: str
    turn: int
    time_period: str  # e.g., "January-June 2026"
    historical_summary: str = ""  # Concise summary of previous turns


@dataclass
class TurnResult:
    """Results from a single turn."""

    turn: int
    time_period: str
    triggered_events: list[dict]  # [{"id": "...", "probability": 0.1}, ...]
    actor_outputs: dict[str, str]  # actor_id -> markdown output
    metric_rules: str  # Markdown numbered list
    metrics: dict[str, float]  # metric_id -> value
    narrative: str  # World state narrative
    notepad: str  # Game Master notes


@dataclass
class LLMConfig:
    """LLM configuration with per-task model selection and fallback lists.

    Each model field supports:
    - Single ModelRoute: ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")
    - Fallback list: [ModelRoute(...), ModelRoute(...)]
    - Dict for actors: {"actor1": ModelRoute(...), "actor2": [ModelRoute(...), ...]}
    """

    # Per-task model selection (ModelRoute or list for fallback)
    events: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "google/gemini-3-flash-preview")
    )
    actors: Union[ModelRoute, List[ModelRoute], dict] = field(
        default_factory=lambda: ModelRoute("openrouter", "google/gemini-3-flash-preview")
    )
    rules: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "google/gemini-3-flash-preview")
    )
    metrics: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "google/gemini-3-flash-preview")
    )
    summary: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")
    )
    analysis: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")
    )
    referee: Union[ModelRoute, List[ModelRoute]] = field(
        default_factory=lambda: ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507")
    )

    # Global settings
    temperature: float = 0.7
    max_tokens: int = 2000
    max_tokens_by_task: dict[str, int] = field(default_factory=dict)

    # Provider-native structured outputs for the events step.
    #   "auto"  – try structured; on "unsupported" fall back silently to the
    #             legacy parse + format-fix path and remember it for the run.
    #   "true"  – structured required; hard error if the model doesn't support it.
    #   "false" – legacy parse path only (never attempt structured output).
    structured_outputs: str = "auto"

    # Wall-clock deadline for a single LLM call, in seconds. Bounds the whole
    # request rather than each read, so a provider that trickles bytes cannot
    # block a run indefinitely.
    call_timeout_seconds: int = 300

    # How many times the events step elicits the candidate-event list per turn.
    # With N > 1, per-event probabilities are aggregated (mean, absent-as-zero)
    # before the dice roll, and per-sample values are persisted.
    probability_samples: int = 1

    def __post_init__(self) -> None:
        allowed = {"auto", "true", "false"}
        if self.structured_outputs not in allowed:
            raise ValueError(
                f"llm.structured_outputs must be one of {sorted(allowed)}, "
                f"got {self.structured_outputs!r}"
            )
        if not isinstance(self.probability_samples, int) or self.probability_samples < 1:
            raise ValueError(
                f"llm.probability_samples must be an integer >= 1, "
                f"got {self.probability_samples!r}"
            )
        if not isinstance(self.call_timeout_seconds, int) or self.call_timeout_seconds < 1:
            raise ValueError(
                f"llm.call_timeout_seconds must be an integer >= 1, "
                f"got {self.call_timeout_seconds!r}"
            )

    def get_actor_routes(self, actor_id: str) -> Union[ModelRoute, List[ModelRoute]]:
        """Get route(s) for a specific actor.

        Returns:
            ModelRoute or list of ModelRoute (for fallback)
        """
        if isinstance(self.actors, (ModelRoute, list)):
            return self.actors

        # Dict case
        default_route = ModelRoute("openrouter", "google/gemini-3-flash-preview")
        result = self.actors.get(actor_id, self.actors.get("default", default_route))
        return result

    # Keep old name as alias for backward compatibility with any call sites not yet updated
    def get_actor_models(self, actor_id: str) -> Union[ModelRoute, List[ModelRoute]]:
        return self.get_actor_routes(actor_id)

    def normalize_to_list(self, value: Union[ModelRoute, List[ModelRoute]]) -> List[ModelRoute]:
        """Convert a route value to a list (for fallback processing)."""
        return [value] if isinstance(value, ModelRoute) else value

    def get_task_max_tokens(self, task: str, default: Optional[int] = None) -> int:
        """Get max_tokens for a task, falling back to global max_tokens.

        Args:
            task: Task name (events, actors, rules, metrics, summary, analysis, referee)
            default: Optional fallback if task-specific value is not set
        """
        if task in self.max_tokens_by_task:
            return self.max_tokens_by_task[task]
        if default is not None:
            return default
        return self.max_tokens


@dataclass
class EmergentEventsConfig:
    """Policy for Game Master-proposed events not listed in events.md.

    When enabled, the events step may propose up to ``max_per_turn`` novel
    exogenous events per turn. Python only applies guardrails: shape
    validation, a probability cap, and the per-turn limit. The proposals
    themselves come from the LLM, keeping the pure LLM architecture.

    When ``track_unfired`` is also enabled (opt-in), a proposal that does not
    fire is carried forward as an emerging development for up to
    ``window_turns`` consecutive listed turns: it is rendered into the tracked
    notepad section, and the events step is instructed to re-list it with an
    escalating probability until it fires or its window closes. Off by default,
    so enabling emergent events alone preserves one-shot proposal semantics.
    """

    enabled: bool = False
    max_per_turn: int = 1
    max_probability: float = 0.35
    track_unfired: bool = False
    window_turns: int = 3


@dataclass
class RuleEvolutionConfig:
    """Guardrails for how freely metric rules may evolve."""

    freeze_until_turn: int = 0
    max_changes_per_turn: int = 6


@dataclass
class ConstitutionalEnforcementConfig:
    """Guardrails for how constitutional referee failures are handled."""

    max_attempts: int = 2
    on_failure: str = "accept_with_violations"


@dataclass
class LoggingConfig:
    """Optional logging behavior for a run."""

    llm_io: bool = False


@dataclass
class EventOverrides:
    """Forced/suppressed events applied to a single executed turn.

    Used by branch counterfactuals: forced events trigger regardless of the
    rolled probability, suppressed events never trigger. Both apply only to the
    `turn` they are scoped to (the first turn executed in the branched run).
    """

    turn: int
    force: list[str] = field(default_factory=list)
    suppress: list[str] = field(default_factory=list)


@dataclass
class TerminationCondition:
    """A condition that ends a run early when it becomes true.

    Some scenarios have a definite finish: a government forms, a war ends, a
    deadline passes. Without this the loop runs every turn regardless, spending
    money on a world whose answer is already settled and inviting the model to
    contradict it.

    ``when`` is evaluated in Python against current metric values using the same
    sandboxed AST evaluator as event probability formulas. It is deliberately not
    an LLM judgement: whether a run is over should be reproducible.
    """

    id: str
    when: str  # Safe expression over metric ids, e.g. "snap_election_risk >= 100"
    description: str = ""


@dataclass
class ScenarioConfig:
    """Scenario configuration with optional inheritance."""

    name: str
    description: str
    start_date: str
    time_scale: str  # e.g., "6 months per turn"
    max_turns: int
    actor_ids: list[str]
    output_language: Optional[str] = None

    # Questions the scenario exists to answer; consumed by cross-run synthesis.
    research_questions: list[ResearchQuestion] = field(default_factory=list)

    # LLM settings
    llm: LLMConfig = None
    emergent_events: EmergentEventsConfig = field(default_factory=EmergentEventsConfig)
    rule_evolution: RuleEvolutionConfig = field(default_factory=RuleEvolutionConfig)
    constitutional_enforcement: ConstitutionalEnforcementConfig = field(
        default_factory=ConstitutionalEnforcementConfig
    )
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Conditions that end a run before max_turns (evaluated after each turn).
    termination: list[TerminationCondition] = field(default_factory=list)

    # Some scenarios are incoherent without a starting-state draw (for example
    # one whose world begins with an election result supplied per run). Setting
    # this makes running without --initial-state a hard error instead of a
    # silently broken simulation.
    requires_initial_state: bool = False

    # Randomness: seed for the derived dice RNG (set at run time if None).
    random_seed: Optional[int] = None

    # Event forcing for branch counterfactuals (set at run time, not in YAML).
    event_overrides: Optional[EventOverrides] = None

    # Inheritance (set during loading, not in YAML)
    base: Optional[str] = None  # Path to base scenario (relative to current)

    def __post_init__(self):
        # Ensure llm config exists
        if self.llm is None:
            self.llm = LLMConfig()


@dataclass
class InitialState:
    """Starting-state overrides applied to a scenario before turn 1.

    Supplied as a JSON data file via ``--initial-state``. This lets a batch of
    runs explore a distribution of starting worlds (a Monte Carlo over initial
    conditions) rather than only over event dice.

    Scenario Lab reads this file as *data* and never executes scenario-supplied
    code. Producing the file is a deliberate, separate step owned by the user,
    which keeps the code-execution guarantees described in
    ``docs/ARCHITECTURE.md`` intact.
    """

    metrics: dict[str, float] = field(default_factory=dict)
    context: str = ""
    notes: str = ""
    source: Optional[str] = None  # Path the state was loaded from, for provenance

    def to_dict(self) -> dict:
        """Serialize for persistence alongside run artifacts."""
        return {
            "metrics": dict(self.metrics),
            "context": self.context,
            "notes": self.notes,
            "source": self.source,
        }


@dataclass
class EmergingDevelopment:
    """An emergent proposal that did not fire and is carried forward.

    Python tracks only existence, wording and age (persistence); what the
    development means and how likely it is stay with the LLM steps, which see
    these entries through the tracked section of the notepad.
    """

    id: str
    description: str
    first_turn: int
    last_turn: int

    @property
    def appearances(self) -> int:
        return self.last_turn - self.first_turn + 1


@dataclass
class Scenario:
    """Complete scenario state."""

    config: ScenarioConfig
    metrics: Metrics
    events: list[Event]
    actors: dict[str, Actor]
    metric_rules: str  # Current rules as markdown
    world_state: WorldState
    context: str  # Background context
    notepad: str = ""  # Game Master notes that persist across turns
    constitution: Optional[str] = None  # Constitutional constraints (optional)
    custom_system_prompts: dict[str, str] = field(default_factory=dict)  # Optional scenario-specific system prompts
    custom_user_prompts: dict[str, str] = field(default_factory=dict)  # Optional scenario-specific user prompts

    # Starting-state overrides applied before turn 1 (via --initial-state).
    initial_state: Optional[InitialState] = None

    # History
    turn_history: list[TurnResult] = field(default_factory=list)
    occurred_events: set[str] = field(default_factory=set)

    # Emergent proposals that have not fired yet and are being carried forward
    # as emerging developments (see ARCHITECTURE.md).
    emerging_developments: list[EmergingDevelopment] = field(default_factory=list)
