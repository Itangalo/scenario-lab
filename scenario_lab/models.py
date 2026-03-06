"""Data models for Scenario Lab V4."""

from dataclasses import dataclass, field
from typing import Optional, Union, List
import json


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


@dataclass
class Event:
    """An external event that can occur."""

    id: str
    description: str
    condition: str  # Natural language condition
    probability: str  # Can be formula like "2 * unemployment / 100"
    can_repeat: bool = False
    occurred: bool = False


@dataclass
class Actor:
    """A stakeholder in the scenario."""

    id: str
    name: str
    short_description: str
    long_description: str
    initial_goals: list[str]
    behavioral_traits: list[str] = field(default_factory=list)

    # Updated each turn
    current_goals: list[str] = field(default_factory=list)
    last_actions: str = ""

    def __post_init__(self):
        if not self.current_goals:
            self.current_goals = self.initial_goals.copy()


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
    - Single string: "google/gemini-3-flash-preview"
    - Fallback list: ["x-ai/grok-4.1-fast", "google/gemini-3-flash-preview"]
    - Dict for actors: {"actor1": "model1", "actor2": ["model1", "model2"]}
    """

    # Per-task model selection (string or list for fallback)
    events: Union[str, List[str]] = "google/gemini-3-flash-preview"
    actors: Union[str, List[str], dict] = "google/gemini-3-flash-preview"  # actor_id -> model/list, or default
    rules: Union[str, List[str]] = "google/gemini-3-flash-preview"
    metrics: Union[str, List[str]] = "google/gemini-3-flash-preview"
    summary: Union[str, List[str]] = "x-ai/grok-4.1-fast"  # Default to cheap model for summarization
    referee: Union[str, List[str]] = "x-ai/grok-4.1-fast"  # Default to fast, cheap model for validation

    # Global settings
    temperature: float = 0.7
    max_tokens: int = 2000
    max_tokens_by_task: dict[str, int] = field(default_factory=dict)

    def get_actor_models(self, actor_id: str) -> Union[str, List[str]]:
        """Get model(s) for a specific actor.

        Returns:
            String or list of strings (for fallback)
        """
        if isinstance(self.actors, (str, list)):
            return self.actors

        # Dict case
        result = self.actors.get(actor_id, self.actors.get("default", "google/gemini-3-flash-preview"))
        return result

    def normalize_to_list(self, value: Union[str, List[str]]) -> List[str]:
        """Convert a model value to a list (for fallback processing)."""
        return [value] if isinstance(value, str) else value

    def get_task_max_tokens(self, task: str, default: Optional[int] = None) -> int:
        """Get max_tokens for a task, falling back to global max_tokens.

        Args:
            task: Task name (events, actors, rules, metrics, summary, referee)
            default: Optional fallback if task-specific value is not set
        """
        if task in self.max_tokens_by_task:
            return self.max_tokens_by_task[task]
        if default is not None:
            return default
        return self.max_tokens


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
class ScenarioConfig:
    """Scenario configuration with optional inheritance."""

    name: str
    description: str
    start_date: str
    time_scale: str  # e.g., "6 months per turn"
    max_turns: int
    actor_ids: list[str]
    output_language: Optional[str] = None

    # LLM settings
    llm: LLMConfig = None
    rule_evolution: RuleEvolutionConfig = field(default_factory=RuleEvolutionConfig)
    constitutional_enforcement: ConstitutionalEnforcementConfig = field(
        default_factory=ConstitutionalEnforcementConfig
    )

    # Inheritance (set during loading, not in YAML)
    base: Optional[str] = None  # Path to base scenario (relative to current)

    def __post_init__(self):
        # Ensure llm config exists
        if self.llm is None:
            self.llm = LLMConfig()


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

    # History
    turn_history: list[TurnResult] = field(default_factory=list)
    occurred_events: set[str] = field(default_factory=set)
