"""
Scenario configuration schema for Scenario Lab V2

Validates scenario.yaml files with clear error messages.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class ScenarioLengthType(str, Enum):
    """How scenario length is determined"""
    FIXED = "fixed"
    CONDITION = "condition"


class ScenarioLength(BaseModel):
    """
    How long the scenario runs

    Examples:
        # Fixed length:
        scenario_length:
          type: fixed
          turns: 10

        # Condition-based:
        scenario_length:
          type: condition
          condition: "cooperation_level >= 8 or turns >= 20"
    """
    type: ScenarioLengthType = Field(
        ...,
        description="Whether scenario has fixed turns or runs until a condition",
    )

    turns: Optional[int] = Field(
        default=None,
        description="Number of turns (required if type is 'fixed')",
        gt=0,
    )

    condition: Optional[str] = Field(
        default=None,
        description="End condition (required if type is 'condition')",
    )

    @model_validator(mode='after')
    def validate_length_config(self):
        """Validate that required fields are present for each type"""
        if self.type == ScenarioLengthType.FIXED and self.turns is None:
            raise ValueError("'turns' field required when type is 'fixed'")

        if self.type == ScenarioLengthType.CONDITION and self.condition is None:
            raise ValueError("'condition' field required when type is 'condition'")

        return self

    model_config = {
        "use_enum_values": True,
    }


class ScenarioConfig(BaseModel):
    """
    Complete scenario configuration

    Example scenario.yaml:
        name: AI Safety Summit 2025
        description: International negotiation on AI governance
        initial_world_state: |
          ## Setting: Virtual Summit, March 2025
          Two major powers are negotiating AI safety standards...
        turns: 10
        turn_duration: "1 week"
        world_state_model: openai/gpt-4o-mini
        actors:
          - united-states
          - european-union
    """

    # Required fields
    name: str = Field(
        ...,
        description="Scenario display name",
        min_length=1,
    )

    initial_world_state: str = Field(
        ...,
        description="Starting world state description (markdown)",
        min_length=10,
    )

    turn_duration: str = Field(
        ...,
        description="How long each turn represents (e.g., '1 day', '1 week')",
        pattern=r"^\d+\s+(second|minute|hour|day|week|month|year)s?$",
    )

    actors: List[str] = Field(
        ...,
        description="List of actor short names (must match actor file names)",
        min_length=1,
    )

    # Temporal settings (support both formats)
    turns: Optional[int] = Field(
        default=None,
        description="Number of turns (simplified format)",
        gt=0,
    )

    num_turns: Optional[int] = Field(
        default=None,
        description="Alternative field name for turns",
        gt=0,
    )

    scenario_length: Optional[ScenarioLength] = Field(
        default=None,
        description="Scenario length configuration (advanced format)",
    )

    # Model configuration
    world_state_model: Optional[str] = Field(
        default="openai/gpt-4o-mini",
        description="LLM model for world state synthesis",
    )

    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for all actors (can be overridden per-actor)",
    )

    # Optional settings
    description: Optional[str] = Field(
        default=None,
        description="Brief scenario summary",
    )

    context_window_size: Optional[int] = Field(
        default=3,
        description="Number of previous turns to include in context",
        gt=0,
    )

    context_window: Optional[int] = Field(
        default=None,
        description="Alternative field name for context_window_size",
        gt=0,
    )

    # Communication settings
    enable_bilateral_communication: Optional[bool] = Field(
        default=False,
        description="Enable bilateral communication phase",
    )

    enable_coalition_formation: Optional[bool] = Field(
        default=False,
        description="Enable coalition formation phase",
    )

    enable_public_statements: Optional[bool] = Field(
        default=False,
        description="Enable public statements phase",
    )

    max_communications_per_turn: Optional[int] = Field(
        default=2,
        description="Maximum communications per actor per turn",
        ge=0,
    )

    # Black swan events
    enable_black_swans: Optional[bool] = Field(
        default=False,
        description="Enable random black swan events",
    )

    # Advanced settings
    allow_actor_reflection: Optional[bool] = Field(
        default=False,
        description="Allow actors to reflect on past decisions",
    )

    parallel_action_resolution: Optional[bool] = Field(
        default=False,
        description="Resolve actor actions in parallel vs sequentially",
    )

    @field_validator('actors')
    @classmethod
    def validate_actor_names(cls, v: List[str]) -> List[str]:
        """Validate actor short names"""
        if not v:
            raise ValueError("At least one actor is required")

        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate actor names found")

        # Validate format
        for actor in v:
            if not actor or not actor.strip():
                raise ValueError("Actor names cannot be empty")
            # Should match lowercase-with-hyphens pattern
            if not all(c.islower() or c.isdigit() or c == '-' for c in actor):
                raise ValueError(
                    f"Actor name '{actor}' should be lowercase with hyphens (e.g., 'united-states')"
                )

        return v

    @field_validator('turn_duration')
    @classmethod
    def validate_turn_duration(cls, v: str) -> str:
        """Validate and normalize turn duration"""
        v = v.strip()

        # Common formats: "1 week", "2 days", "3 hours"
        valid_units = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']

        parts = v.split()
        if len(parts) != 2:
            raise ValueError(
                f"Turn duration must be in format '<number> <unit>' (e.g., '1 week'), got: '{v}'"
            )

        try:
            int(parts[0])
        except ValueError:
            raise ValueError(f"Turn duration must start with a number, got: '{parts[0]}'")

        unit = parts[1].rstrip('s')  # Remove trailing 's' for plural
        if unit not in valid_units:
            raise ValueError(
                f"Turn duration unit must be one of {valid_units}, got: '{parts[1]}'"
            )

        return v

    @model_validator(mode='after')
    def validate_turns_field(self):
        """Ensure at least one turn specification exists"""
        if self.turns is None and self.num_turns is None and self.scenario_length is None:
            raise ValueError(
                "Scenario must specify turns (e.g., 'turns: 10') or scenario_length"
            )

        # Normalize field names
        if self.num_turns is not None and self.turns is None:
            self.turns = self.num_turns

        if self.turns is not None and self.scenario_length is None:
            # Create scenario_length from turns for consistency
            self.scenario_length = ScenarioLength(
                type=ScenarioLengthType.FIXED,
                turns=self.turns
            )

        return self

    @model_validator(mode='after')
    def normalize_context_window(self):
        """Merge context_window and context_window_size fields"""
        if self.context_window is not None and self.context_window_size == 3:
            self.context_window_size = self.context_window

        return self

    model_config = {
        "extra": "allow",  # Allow extra fields for forward compatibility
    }
