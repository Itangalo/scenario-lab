"""
Pydantic data models for Scenario Lab V3.

Defines the core data structures for world state, actors, configurations,
and simulation tracking.
"""

from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# === Actor Models ===

class Actor(BaseModel):
    """
    An actor in the simulation.

    Represents a participant (country, organization, company) with:
    - Identity and background
    - Current goals
    - Action points for communication
    """
    name: str
    goals: List[str] = Field(default_factory=list)
    action_points: int = Field(default=0, ge=0)
    background: str = ""  # Loaded from background/actors/{name}.md

    def deduct_action_points(self, cost: int) -> bool:
        """
        Deduct action points if sufficient.

        Args:
            cost: Number of action points to deduct

        Returns:
            True if deduction successful, False if insufficient points
        """
        if self.action_points >= cost:
            self.action_points -= cost
            return True
        return False

    def reset_action_points(self, amount: int) -> None:
        """Reset action points to specified amount."""
        self.action_points = amount


# === Metrics Models ===

class ChangeMagnitude(BaseModel):
    """Range for a magnitude of change (small/medium/large)."""
    small: tuple[float, float] = (0.01, 0.05)
    medium: tuple[float, float] = (0.05, 0.15)
    large: tuple[float, float] = (0.15, 0.5)


class MetricDependency(BaseModel):
    """Dependency relationship between metrics."""
    metric: str  # Path to dependent metric (e.g., "world.ai_catastrophe_risk")
    type: Literal["additive", "multiplicative"] = "additive"
    coefficient: float = 1.0
    condition: Optional[str] = None  # e.g., "> 50", "< 0.5"


class MetricMetadata(BaseModel):
    """
    Metadata for a metric in the enhanced schema.

    Defines constraints, change magnitudes, randomness, and dependencies.
    """
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    change_magnitudes: Optional[ChangeMagnitude] = None
    randomness: float = Field(default=0.0, ge=0.0, le=1.0)
    dependencies: List[MetricDependency] = Field(default_factory=list)


class EnhancedMetric(BaseModel):
    """
    A metric with value and metadata.

    Supports both simple (value only) and enhanced (value + metadata) formats.
    """
    value: float
    metadata: Optional[MetricMetadata] = None

    @classmethod
    def from_simple(cls, value: float) -> "EnhancedMetric":
        """Create from simple numeric value."""
        return cls(value=value)

    @classmethod
    def from_dict(cls, data: dict) -> "EnhancedMetric":
        """Create from YAML dict with value + metadata fields."""
        if isinstance(data, (int, float)):
            return cls.from_simple(float(data))

        value = data.get("value")
        if value is None:
            raise ValueError("Enhanced metric must have 'value' field")

        metadata_dict = {k: v for k, v in data.items() if k != "value"}
        metadata = MetricMetadata(**metadata_dict) if metadata_dict else None

        return cls(value=value, metadata=metadata)

    def get_change_range(self, magnitude: Literal["small", "medium", "large"]) -> tuple[float, float]:
        """Get the change range for a given magnitude."""
        if self.metadata and self.metadata.change_magnitudes:
            return getattr(self.metadata.change_magnitudes, magnitude)

        # Default ranges if not specified
        defaults = ChangeMagnitude()
        return getattr(defaults, magnitude)

    def validate_bounds(self, new_value: float) -> float:
        """Validate and clamp value to bounds if specified."""
        if self.metadata:
            if self.metadata.min is not None and new_value < self.metadata.min:
                return self.metadata.min
            if self.metadata.max is not None and new_value > self.metadata.max:
                return self.metadata.max
        return new_value


class ActorMetricsData(BaseModel):
    """
    Metrics for a single actor with private/public split.

    Private metrics: Only visible to the actor
    Public metrics: Visible to all actors

    Supports both simple (Dict[str, float]) and enhanced (Dict[str, EnhancedMetric]) formats.
    """
    private: Dict[str, Any] = Field(default_factory=dict)
    public: Dict[str, Any] = Field(default_factory=dict)


class Metrics(BaseModel):
    """
    Complete metrics structure for the simulation.

    Structure:
    - world: Global metrics visible to all (e.g., temperature, risk levels)
    - actors: Per-actor metrics with private/public split
    - metadata_registry: Maps metric paths to their metadata (for enhanced metrics)
    """
    world: Dict[str, Any] = Field(default_factory=dict)
    actors: Dict[str, ActorMetricsData] = Field(default_factory=dict)
    metadata_registry: Dict[str, MetricMetadata] = Field(default_factory=dict)

    def get_metadata(self, path: str) -> Optional[MetricMetadata]:
        """Get metadata for a metric by path (e.g., 'world.temperature' or 'actors.USA.private.budget')."""
        return self.metadata_registry.get(path)

    def set_metadata(self, path: str, metadata: MetricMetadata) -> None:
        """Set metadata for a metric path."""
        self.metadata_registry[path] = metadata

    def get_value(self, path: str) -> Optional[float]:
        """
        Get numeric value from a metric path.

        Handles both simple (float) and enhanced (EnhancedMetric) formats.
        """
        parts = path.split(".")
        if parts[0] == "world":
            metric_name = ".".join(parts[1:])
            value = self.world.get(metric_name)
        elif parts[0] == "actors" and len(parts) >= 3:
            actor = parts[1]
            visibility = parts[2]  # 'private' or 'public'
            metric_name = ".".join(parts[3:]) if len(parts) > 3 else parts[2]

            if actor not in self.actors:
                return None

            actor_data = self.actors[actor]
            if visibility == "private":
                value = actor_data.private.get(metric_name)
            elif visibility == "public":
                value = actor_data.public.get(metric_name)
            else:
                # Assume public if not specified
                value = actor_data.public.get(visibility)
        else:
            return None

        # Handle EnhancedMetric vs simple value
        if isinstance(value, EnhancedMetric):
            return value.value
        elif isinstance(value, (int, float)):
            return float(value)
        return value

    def set_value(self, path: str, value: float) -> None:
        """
        Set numeric value for a metric path.

        Maintains existing metadata if present.
        """
        parts = path.split(".")
        if parts[0] == "world":
            metric_name = ".".join(parts[1:])
            metadata = self.get_metadata(path)
            if metadata:
                self.world[metric_name] = EnhancedMetric(value=value, metadata=metadata)
            else:
                self.world[metric_name] = value
        elif parts[0] == "actors" and len(parts) >= 3:
            actor = parts[1]
            visibility = parts[2]
            metric_name = ".".join(parts[3:]) if len(parts) > 3 else parts[2]

            if actor not in self.actors:
                self.actors[actor] = ActorMetricsData()

            metadata = self.get_metadata(path)
            actor_data = self.actors[actor]

            if visibility == "private":
                if metadata:
                    actor_data.private[metric_name] = EnhancedMetric(value=value, metadata=metadata)
                else:
                    actor_data.private[metric_name] = value
            elif visibility == "public":
                if metadata:
                    actor_data.public[metric_name] = EnhancedMetric(value=value, metadata=metadata)
                else:
                    actor_data.public[metric_name] = value
            else:
                # Assume public if not specified
                if metadata:
                    actor_data.public[visibility] = EnhancedMetric(value=value, metadata=metadata)
                else:
                    actor_data.public[visibility] = value

    def get_actor_metric(self, actor: str, metric: str, private: bool = False) -> Any:
        """
        Get a specific metric for an actor.

        Args:
            actor: Actor name
            metric: Metric key
            private: Whether to look in private or public metrics

        Returns:
            Metric value or None if not found
        """
        if actor not in self.actors:
            return None

        metrics_dict = self.actors[actor].private if private else self.actors[actor].public
        return metrics_dict.get(metric)

    def set_actor_metric(self, actor: str, metric: str, value: Any, private: bool = False) -> None:
        """
        Set a specific metric for an actor.

        Args:
            actor: Actor name
            metric: Metric key
            value: Metric value
            private: Whether to set in private or public metrics
        """
        if actor not in self.actors:
            self.actors[actor] = ActorMetricsData()

        if private:
            self.actors[actor].private[metric] = value
        else:
            self.actors[actor].public[metric] = value


# === World State Models ===

class RelationshipState(BaseModel):
    """Relationship state between two actors."""
    trust: float = Field(default=0.5, ge=0.0, le=1.0)
    active_agreements: List[str] = Field(default_factory=list)
    history_summary: str = ""


class FactLedgerEntry(BaseModel):
    """A verifiable fact that never gets summarized away."""
    timestamp: str  # e.g., "Turn 3"
    fact: str
    source: str  # e.g., "action:declare_war" or "event:pandemic"


class WorldState(BaseModel):
    """
    The complete state of the simulation world.

    Four layers:
    - narrative_state: Current story and context
    - metrics: Quantitative data (world + actors with private/public split)
    - fact_ledger: Verifiable facts that persist
    - relationship_state: Structured relationships between actors
    - outcome_flags: Flags for quantitative analysis
    """
    narrative_state: str = ""
    metrics: Metrics = Field(default_factory=Metrics)
    fact_ledger: List[FactLedgerEntry] = Field(default_factory=list)
    relationship_state: Dict[str, RelationshipState] = Field(default_factory=dict)
    outcome_flags: Dict[str, Any] = Field(default_factory=dict)

    def get_relationship_key(self, actor1: str, actor2: str) -> str:
        """Generate canonical relationship key (alphabetically sorted)."""
        return f"{min(actor1, actor2)}:{max(actor1, actor2)}"

    def get_relationship(self, actor1: str, actor2: str) -> RelationshipState:
        """Get relationship between two actors, creating if needed."""
        key = self.get_relationship_key(actor1, actor2)
        if key not in self.relationship_state:
            self.relationship_state[key] = RelationshipState()
        return self.relationship_state[key]

    def get_metric(self, actor: Optional[str], path: str) -> Any:
        """Gets a metric from the world state."""
        if actor is None:
            return self.metrics.world.get(path, 0.0)
        
        if "." in path:
            category, metric_name = path.split(".", 1)
            if category == "private":
                return self.metrics.actors.get(actor, ActorMetricsData()).private.get(metric_name, 0.0)
            elif category == "public":
                return self.metrics.actors.get(actor, ActorMetricsData()).public.get(metric_name, 0.0)
        
        return self.metrics.actors.get(actor, ActorMetricsData()).public.get(path, 0.0)

    def set_metric(self, actor: Optional[str], path: str, value: Any):
        """Sets a metric in the world state."""
        if actor is None:
            self.metrics.world[path] = value
        else:
            if actor not in self.metrics.actors:
                self.metrics.actors[actor] = ActorMetricsData()
            
            if "." in path:
                category, metric_name = path.split(".", 1)
                if category == "private":
                    self.metrics.actors[actor].private[metric_name] = value
                elif category == "public":
                    self.metrics.actors[actor].public[metric_name] = value
                else:
                    self.metrics.actors[actor].public[path] = value
            else:
                self.metrics.actors[actor].public[path] = value
            
    def add_fact(self, fact: str, source: str = "unknown"):
        """Adds a fact to the fact ledger."""
        # A real implementation would get the turn from the engine
        entry = FactLedgerEntry(timestamp="Turn X", fact=fact, source=source)
        self.fact_ledger.append(entry)

    def set_outcome_flag(self, key: str, value: Any):
        """Sets an outcome flag."""
        self.outcome_flags[key] = value


class ActorView(BaseModel):
    """
    Filtered world state visible to a specific actor.

    This represents what a single actor can see, implementing information asymmetry:
    - Full narrative state
    - Filtered metrics (world + own private/public + others' public only)
    - Complete fact ledger
    - All relationship states
    - Own current goals
    - Own action points
    """
    actor_name: str
    narrative_state: str
    visible_metrics: Metrics
    fact_ledger: List[FactLedgerEntry]
    relationship_state: Dict[str, RelationshipState]
    current_goals: List[str] = Field(default_factory=list)
    action_points: int = 0


# === Configuration Models ===

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = "openrouter"
    model: str = "anthropic/claude-sonnet-4"
    api_key_env: str = "OPENROUTER_API_KEY"
    temperature: float = 0.7
    max_tokens: int = 4000


class ActionPointRules(BaseModel):
    """Rules for action point allocation and costs."""
    initial_per_turn: int = 3
    message_to_new_recipient: int = 1
    message_reply: int = 0
    forward_message: int = 1


class ScenarioConfig(BaseModel):
    """Main scenario configuration from scenario.yaml."""
    name: str
    start_date: Optional[str] = None  # e.g., "2026-01-01"
    time_scale: str  # e.g., "6 months per turn"
    max_turns: int = 10
    actors: List[str]
    llm: LLMConfig
    action_point_rules: ActionPointRules
    world_altering_triggers: List[Dict[str, Any]] = Field(default_factory=list)


class MetricsConfig(BaseModel):
    """
    Metrics configuration from metrics.yaml.

    Note: Uses ActorMetricsData for the structure.
    This is the initial configuration loaded from metrics.yaml.
    """
    world: Dict[str, Any] = Field(default_factory=dict)
    actors: Dict[str, ActorMetricsData] = Field(default_factory=dict)


class ExogenousEvent(BaseModel):
    """
    An exogenous event that occurs at a specific turn.

    Events can be:
    - Scheduled: Occur at a specific turn
    - Conditional: Occur when certain conditions are met
    """
    turn: int
    name: str
    description: str
    effects: Dict[str, Any] = Field(default_factory=dict)
    scheduled: bool = True  # If False, event is conditional
    conditional: Optional[Dict[str, Any]] = None  # Conditions for conditional events


class EventsConfig(BaseModel):
    """Events configuration from events.yaml."""
    events: List[ExogenousEvent] = Field(default_factory=list)


# === Communication Models ===

class MessageVisibility(str, Enum):
    """Visibility levels for messages."""
    PRIVATE = "private"  # Only sender and recipient
    PUBLIC = "public"    # Visible to all actors
    LEAKED = "leaked"    # Was private but became public


class Message(BaseModel):
    """
    A message sent between actors.

    Messages can have different intents (negotiate, threaten, inform, etc.)
    and visibility levels (private, public, leaked).
    """
    from_actor: str
    to_actor: str
    content: str
    turn: int
    phase: int  # 1 or 2
    intent: Optional[str] = None  # e.g., "negotiate", "threaten", "inform", "request"
    visibility: MessageVisibility = MessageVisibility.PRIVATE
    timestamp: datetime = Field(default_factory=datetime.now)

    def is_visible_to(self, actor: str) -> bool:
        """
        Check if a message is visible to a given actor.

        Args:
            actor: Actor name to check visibility for

        Returns:
            True if the message is visible to the actor
        """
        if self.visibility == MessageVisibility.PUBLIC or self.visibility == MessageVisibility.LEAKED:
            return True
        return actor == self.from_actor or actor == self.to_actor


class CommunicationRound(BaseModel):
    """All communications in a phase."""
    phase: int
    messages: List[Message] = Field(default_factory=list)


# === World Interpreter Models ===

class MetricChange(BaseModel):
    """
    A single metric change requested by the World Interpreter.

    Represents how an actor's narrative translates to a mechanical change.
    """
    metric: str  # Full path (e.g., "world.temperature" or "actors.USA.private.budget")
    operation: Literal["adjust", "set"] = "adjust"
    magnitude: Optional[Literal["small", "medium", "large"]] = None  # For adjust operation
    direction: Optional[Literal["increase", "decrease"]] = None  # For adjust operation
    value: Optional[float] = None  # For set operation
    reasoning: str  # Why this change makes sense given the narrative


class InterpreterOutput(BaseModel):
    """
    Output from the World Interpreter after processing an actor's narrative.

    Contains structured metric changes and an interpretation for the Director.
    """
    metric_changes: List[MetricChange] = Field(default_factory=list)
    interpretation: str  # Narrative summary for Director synthesis
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)  # How confident the interpretation is


class MetricChangeLog(BaseModel):
    """
    Log entry tracking a metric change for debugging.

    Records before/after values, the change request, and why it was applied.
    """
    turn: int
    actor: str
    metric_path: str
    old_value: float
    new_value: float
    change_request: MetricChange
    applied_at: datetime = Field(default_factory=datetime.now)


# === Action Models ===

class FunctionCall(BaseModel):
    """A function call representing a concrete action."""
    name: str
    args: Dict[str, Any]


class ActorAction(BaseModel):
    """An actor's action in the execution phase."""
    actor: str
    narrative: str  # Narrative description of what they're doing
    function_calls: List[FunctionCall] = Field(default_factory=list)
    updated_goals: List[str] = Field(default_factory=list)


class TurnActions(BaseModel):
    """All actor actions for a turn."""
    turn: int
    actions: List[ActorAction] = Field(default_factory=list)


# === Turn State Models ===

class TurnState(BaseModel):
    """Complete state for a single turn."""
    turn_number: int
    actor_views: Dict[str, ActorView] = Field(default_factory=dict)
    communications_phase_1: CommunicationRound
    communications_phase_2: CommunicationRound
    actions: TurnActions
    world_state_after: WorldState


# === Run Summary Models ===

class RunSummary(BaseModel):
    """Summary of a complete simulation run for analysis."""
    scenario_name: str
    run_id: str
    total_turns: int
    outcome_flags: Dict[str, Any]
    final_metrics: Dict[str, Any]
    key_events: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
