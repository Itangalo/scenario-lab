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

class ActorMetricsData(BaseModel):
    """
    Metrics for a single actor with private/public split.

    Private metrics: Only visible to the actor
    Public metrics: Visible to all actors
    """
    private: Dict[str, Any] = Field(default_factory=dict)
    public: Dict[str, Any] = Field(default_factory=dict)


class Metrics(BaseModel):
    """
    Complete metrics structure for the simulation.

    Structure:
    - world: Global metrics visible to all (e.g., temperature, risk levels)
    - actors: Per-actor metrics with private/public split
    """
    world: Dict[str, Any] = Field(default_factory=dict)
    actors: Dict[str, ActorMetricsData] = Field(default_factory=dict)

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


# === Action Models ===

class FunctionCall(BaseModel):
    """A function call representing a concrete action."""
    name: str
    arguments: Dict[str, Any]


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
