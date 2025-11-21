"""
Immutable state models for Scenario Lab V2

These models enable:
- Safe state management (no accidental mutations)
- Time-travel debugging
- Trivial branching
- Safe parallelization
- Easy rollback

Based on ROADMAP_V2.md Phase 2.1 architecture design.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum


class ScenarioStatus(str, Enum):
    """Scenario execution status"""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    HALTED = "halted"  # Stopped early (credit limit, manual stop, end turn reached)
    FAILED = "failed"


class PhaseType(str, Enum):
    """Execution phase types"""

    COMMUNICATION = "communication"
    COALITION = "coalition"
    DECISION = "decision"
    WORLD_UPDATE = "world_update"
    VALIDATION = "validation"
    PERSISTENCE = "persistence"


def _make_timestamp() -> datetime:
    """Factory function for creating timestamps"""
    return datetime.now()


@dataclass(frozen=True)
class Communication:
    """
    Immutable communication record

    Represents any communication between actors (bilateral, coalition, public)
    """

    id: str
    turn: int
    type: str  # 'bilateral', 'coalition', 'public'
    sender: str
    recipients: List[str]
    content: str
    timestamp: datetime = field(default_factory=_make_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    """
    Immutable actor decision record

    Represents a single actor's decision in a turn
    """

    actor: str
    turn: int
    goals: List[str]
    reasoning: str
    action: str
    timestamp: datetime = field(default_factory=_make_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorldState:
    """
    Immutable world state

    Represents the state of the world at a specific point in time
    """

    turn: int
    content: str  # Markdown content describing the world
    timestamp: datetime = field(default_factory=_make_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_content(self, content: str) -> WorldState:
        """Create new WorldState with updated content"""
        return replace(self, content=content, timestamp=datetime.now())


def _make_empty_world_state() -> WorldState:
    """Factory function for creating empty world state"""
    return WorldState(turn=0, content="")


@dataclass(frozen=True)
class ActorState:
    """
    Immutable actor state

    Represents an actor's state at a specific point in time
    """

    name: str
    short_name: str
    model: str
    current_goals: List[str] = field(default_factory=list)
    recent_decisions: List[Decision] = field(default_factory=list)
    private_information: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_decision(self, decision: Decision) -> ActorState:
        """Create new ActorState with added decision"""
        new_decisions = self.recent_decisions + [decision]
        # Keep only recent decisions (e.g., last 5)
        new_decisions = new_decisions[-5:]
        return replace(
            self, recent_decisions=new_decisions, current_goals=decision.goals
        )


@dataclass(frozen=True)
class CostRecord:
    """
    Immutable cost record

    Tracks a single LLM API call cost
    """

    timestamp: datetime
    actor: Optional[str]
    phase: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricRecord:
    """
    Immutable metric record

    Tracks a single metric measurement
    """

    name: str
    value: float
    turn: int
    timestamp: datetime = field(default_factory=_make_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioState:
    """
    Complete immutable scenario state

    This is the central state object that flows through the execution engine.
    Each phase returns a new ScenarioState rather than mutating the existing one.

    Benefits:
    - Can rollback to any previous state
    - Phases can't accidentally corrupt state
    - Easy to implement branching
    - Safe for parallel execution
    """

    # Scenario metadata
    scenario_id: str
    scenario_name: str
    run_id: str
    status: ScenarioStatus = ScenarioStatus.CREATED
    scenario_config: Dict[str, Any] = field(default_factory=dict)  # Scenario configuration (loaded from YAML)

    # Execution state
    turn: int = 0
    current_phase: Optional[PhaseType] = None

    # World and actors
    world_state: WorldState = field(default_factory=_make_empty_world_state)
    actors: Dict[str, ActorState] = field(default_factory=dict)

    # Communications and decisions
    communications: List[Communication] = field(default_factory=list)
    decisions: Dict[str, Decision] = field(default_factory=dict)  # actor -> decision for current turn

    # Metrics and costs
    metrics: List[MetricRecord] = field(default_factory=list)
    costs: List[CostRecord] = field(default_factory=list)

    # Exogenous events
    triggered_event_ids: Set[str] = field(default_factory=set)  # Track one-time events that have triggered

    # Execution metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Derived properties (cached)
    def total_cost(self) -> float:
        """Calculate total cost across all records"""
        return sum(c.cost for c in self.costs)

    def actor_cost(self, actor: str) -> float:
        """Calculate cost for a specific actor"""
        return sum(c.cost for c in self.costs if c.actor == actor)

    def phase_cost(self, phase: str) -> float:
        """Calculate cost for a specific phase"""
        return sum(c.cost for c in self.costs if c.phase == phase)

    # State transformations (all return new ScenarioState)

    def with_turn(self, turn: int) -> ScenarioState:
        """Advance to next turn"""
        return replace(self, turn=turn, decisions={})

    def with_status(self, status: ScenarioStatus) -> ScenarioState:
        """Update status"""
        return replace(self, status=status)

    def with_phase(self, phase: Optional[PhaseType]) -> ScenarioState:
        """Update current phase"""
        return replace(self, current_phase=phase)

    def with_world_state(self, world_state: WorldState) -> ScenarioState:
        """Update world state"""
        return replace(self, world_state=world_state)

    def with_actor(self, actor_name: str, actor_state: ActorState) -> ScenarioState:
        """Update a single actor's state"""
        new_actors = {**self.actors, actor_name: actor_state}
        return replace(self, actors=new_actors)

    def with_decision(self, actor: str, decision: Decision) -> ScenarioState:
        """Add a decision for current turn"""
        new_decisions = {**self.decisions, actor: decision}
        # Also update actor state
        if actor in self.actors:
            new_actor_state = self.actors[actor].with_decision(decision)
            new_actors = {**self.actors, actor: new_actor_state}
        else:
            new_actors = self.actors
        return replace(self, decisions=new_decisions, actors=new_actors)

    def with_communication(self, comm: Communication) -> ScenarioState:
        """Add a communication record"""
        new_comms = self.communications + [comm]
        return replace(self, communications=new_comms)

    def with_cost(self, cost: CostRecord) -> ScenarioState:
        """Add a cost record"""
        new_costs = self.costs + [cost]
        return replace(self, costs=new_costs)

    def with_metric(self, metric: MetricRecord) -> ScenarioState:
        """Add a metric record"""
        new_metrics = self.metrics + [metric]
        return replace(self, metrics=new_metrics)

    def with_triggered_events(self, event_ids: Set[str]) -> ScenarioState:
        """Update triggered event IDs"""
        return replace(self, triggered_event_ids=event_ids)

    def with_error(self, error: str) -> ScenarioState:
        """Set error state"""
        return replace(self, error=error, status=ScenarioStatus.FAILED)

    def with_started(self) -> ScenarioState:
        """Mark as started"""
        return replace(
            self, status=ScenarioStatus.RUNNING, started_at=datetime.now()
        )

    def with_completed(self) -> ScenarioState:
        """Mark as completed"""
        return replace(
            self, status=ScenarioStatus.COMPLETED, completed_at=datetime.now()
        )

    def with_paused(self) -> ScenarioState:
        """Mark as paused"""
        return replace(self, status=ScenarioStatus.PAUSED)

    def with_halted(self, reason: str = "") -> ScenarioState:
        """Mark as halted (stopped early)"""
        return replace(
            self,
            status=ScenarioStatus.HALTED,
            completed_at=datetime.now(),
            error=reason if reason else "Scenario halted",
        )

    def get_communications_for_turn(self, turn: int) -> List[Communication]:
        """Get all communications for a specific turn"""
        return [c for c in self.communications if c.turn == turn]

    def get_communications_for_actor(self, actor: str) -> List[Communication]:
        """Get all communications involving an actor"""
        return [
            c
            for c in self.communications
            if c.sender == actor or actor in c.recipients
        ]

    def get_metrics_by_name(self, name: str) -> List[MetricRecord]:
        """Get all metrics with a specific name"""
        return [m for m in self.metrics if m.name == name]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns a JSON-serializable dictionary
        """
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "run_id": self.run_id,
            "status": self.status.value,
            "scenario_config": self.scenario_config,  # Include scenario configuration
            "turn": self.turn,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "world_state": {
                "turn": self.world_state.turn,
                "content": self.world_state.content,
                "timestamp": self.world_state.timestamp.isoformat(),
                "metadata": self.world_state.metadata,
            },
            "actors": {
                name: {
                    "name": actor.name,
                    "short_name": actor.short_name,
                    "model": actor.model,
                    "current_goals": actor.current_goals,
                    "recent_decisions": [
                        {
                            "actor": d.actor,
                            "turn": d.turn,
                            "goals": d.goals,
                            "reasoning": d.reasoning,
                            "action": d.action,
                            "timestamp": d.timestamp.isoformat(),
                            "metadata": d.metadata,
                        }
                        for d in actor.recent_decisions
                    ],
                    "private_information": actor.private_information,
                    "metadata": actor.metadata,
                }
                for name, actor in self.actors.items()
            },
            "communications": [
                {
                    "id": c.id,
                    "turn": c.turn,
                    "type": c.type,
                    "sender": c.sender,
                    "recipients": c.recipients,
                    "content": c.content,
                    "timestamp": c.timestamp.isoformat(),
                    "metadata": c.metadata,
                }
                for c in self.communications
            ],
            "decisions": {
                actor: {
                    "actor": d.actor,
                    "turn": d.turn,
                    "goals": d.goals,
                    "reasoning": d.reasoning,
                    "action": d.action,
                    "timestamp": d.timestamp.isoformat(),
                    "metadata": d.metadata,
                }
                for actor, d in self.decisions.items()
            },
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "turn": m.turn,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata,
                }
                for m in self.metrics
            ],
            "costs": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "actor": c.actor,
                    "phase": c.phase,
                    "model": c.model,
                    "input_tokens": c.input_tokens,
                    "output_tokens": c.output_tokens,
                    "cost": c.cost,
                    "metadata": c.metadata,
                }
                for c in self.costs
            ],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata,
            "total_cost": self.total_cost(),
        }
