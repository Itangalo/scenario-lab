"""
Pydantic schemas for exogenous events configuration

Exogenous events are background developments that occur independently of actor decisions.
They enable more realistic scenarios where the world evolves through both actor choices and
external factors.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class ExogenousEventBase(BaseModel):
    """Base class for all exogenous events"""

    type: str = Field(description="Event type: trend, random, conditional, or scheduled")
    name: str = Field(description="Short name for the event")
    description: str = Field(description="What happens when this event occurs")
    turn_range: Optional[List[int]] = Field(
        default=None,
        description="Turn range [min, max] when event can occur (inclusive)"
    )
    once: bool = Field(
        default=True,
        description="Whether event can only trigger once (default: true)"
    )


class TrendEvent(ExogenousEventBase):
    """Regular recurring background development"""

    type: str = Field(default="trend", frozen=True)
    frequency: int = Field(
        description="Event occurs every N turns",
        ge=1
    )
    # Override turn_range to be required for TrendEvent (not Optional)
    turn_range: List[int] = Field(
        description="Turn range [min, max] when event can occur (required for trend events)"
    )

    @field_validator('turn_range')
    @classmethod
    def validate_turn_range(cls, v: List[int]) -> List[int]:
        """Validate turn_range format for trend events"""
        if len(v) != 2:
            raise ValueError("turn_range must be [min, max]")
        if v[0] > v[1]:
            raise ValueError("turn_range min must be <= max")
        return v


class RandomEvent(ExogenousEventBase):
    """Probabilistic event that may occur"""

    type: str = Field(default="random", frozen=True)
    probability: float = Field(
        description="Probability of occurring each turn (0.0-1.0)",
        ge=0.0,
        le=1.0
    )


class ConditionalEvent(ExogenousEventBase):
    """Event triggered when metrics reach thresholds"""

    type: str = Field(default="conditional", frozen=True)
    conditions: Dict[str, str] = Field(
        description="Metric conditions that must be met (e.g., {'ai_capability_level': '>= 7'})"
    )

    @field_validator('conditions')
    @classmethod
    def validate_conditions(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate condition format"""
        if not v:
            raise ValueError("At least one condition is required for conditional events")

        valid_operators = ['>=', '>', '<=', '<', '==', '!=']
        for metric_name, condition in v.items():
            # Check that condition contains a valid operator
            has_valid_op = any(op in condition for op in valid_operators)
            if not has_valid_op:
                raise ValueError(
                    f"Condition '{condition}' for metric '{metric_name}' must use one of: "
                    f"{', '.join(valid_operators)}"
                )
        return v


class ScheduledEvent(ExogenousEventBase):
    """Event at a specific turn"""

    type: str = Field(default="scheduled", frozen=True)
    turn: int = Field(
        description="Turn number when event occurs",
        ge=1
    )
    once: bool = Field(
        default=True,
        frozen=True,
        description="Scheduled events always occur once (cannot be changed)"
    )


class ExogenousEventsConfig(BaseModel):
    """Complete exogenous events configuration"""

    exogenous_events: List[Any] = Field(
        default_factory=list,
        description="List of exogenous events (mixed types)"
    )

    @field_validator('exogenous_events', mode='before')
    @classmethod
    def parse_events(cls, v: Any) -> List[ExogenousEventBase]:
        """Parse events into appropriate typed objects"""
        if not isinstance(v, list):
            raise ValueError("exogenous_events must be a list")

        parsed_events = []
        for i, event_data in enumerate(v):
            if not isinstance(event_data, dict):
                raise ValueError(f"Event {i} must be a dictionary")

            event_type = event_data.get('type')
            if not event_type:
                raise ValueError(f"Event {i} missing 'type' field")

            # Parse based on type
            try:
                if event_type == 'trend':
                    parsed_events.append(TrendEvent(**event_data))
                elif event_type == 'random':
                    parsed_events.append(RandomEvent(**event_data))
                elif event_type == 'conditional':
                    parsed_events.append(ConditionalEvent(**event_data))
                elif event_type == 'scheduled':
                    parsed_events.append(ScheduledEvent(**event_data))
                else:
                    raise ValueError(f"Unknown event type: {event_type}")
            except Exception as e:
                raise ValueError(f"Error parsing event {i} ('{event_data.get('name', 'unnamed')}'): {e}")

        return parsed_events

    class Config:
        arbitrary_types_allowed = True
