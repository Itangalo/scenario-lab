"""
Actor configuration schema for Scenario Lab V2

Validates actor YAML files with clear error messages.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class ActorControl(str, Enum):
    """How an actor is controlled"""
    AI = "ai"
    HUMAN = "human"


class ActorConfig(BaseModel):
    """
    Configuration for a single actor

    Example actor YAML:
        name: United States
        short_name: united-states
        llm_model: openai/gpt-4o
        system_prompt: |
          You represent the US in negotiations...
        goals:
          - Maintain AI leadership
          - Protect national security
        constraints:
          - Must consider Congressional support
        expertise:
          ai_technology: expert
          international_diplomacy: advanced
        decision_style: Pragmatic and innovation-focused
    """

    # Required fields
    name: str = Field(
        ...,
        description="Actor display name",
        min_length=1,
    )

    short_name: str = Field(
        ...,
        description="Actor identifier used in filenames (lowercase, hyphens)",
        pattern=r"^[a-z0-9-]+$",
    )

    # Model configuration (support both field names)
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model to use (e.g., 'openai/gpt-4o', 'ollama/llama3')",
    )

    model: Optional[str] = Field(
        default=None,
        description="Alternative field name for llm_model",
    )

    # Actor characteristics
    goals: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Long-term objectives (list or multiline string)",
    )

    # Optional fields
    role: Optional[str] = Field(
        default=None,
        description="Actor's role in the scenario",
    )

    description: Optional[str] = Field(
        default=None,
        description="Actor description",
    )

    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for this actor",
    )

    control: Optional[ActorControl] = Field(
        default=ActorControl.AI,
        description="AI or human controlled",
    )

    constraints: Optional[List[str]] = Field(
        default=None,
        description="Limitations or rules actor must follow",
    )

    expertise: Optional[Union[Dict[str, str], List[Dict[str, str]], str]] = Field(
        default=None,
        description="Domain expertise levels (dict, list of dicts, or string)",
    )

    decision_style: Optional[str] = Field(
        default=None,
        description="How actor makes decisions",
    )

    decision_making_style: Optional[str] = Field(
        default=None,
        description="Alternative field name for decision_style",
    )

    private_information: Optional[str] = Field(
        default=None,
        description="Information only this actor knows",
    )

    personality_traits: Optional[List[str]] = Field(
        default=None,
        description="Behavioral characteristics",
    )

    expertise_level: Optional[str] = Field(
        default=None,
        description="Overall expertise level",
    )

    communication_style: Optional[str] = Field(
        default=None,
        description="How actor communicates",
    )

    preferred_coalitions: Optional[List[str]] = Field(
        default=None,
        description="Actors this actor prefers to ally with",
    )

    @field_validator('goals')
    @classmethod
    def normalize_goals(cls, v: Optional[Union[str, List[str]]]) -> List[str]:
        """Convert goals to list format"""
        if v is None:
            return []

        if isinstance(v, str):
            # Split by newlines and filter out empty lines
            lines = [line.strip() for line in v.split('\n') if line.strip()]
            # Remove bullet points if present
            lines = [line.lstrip('- ') for line in lines]
            return lines if lines else [v]

        return v

    @model_validator(mode='after')
    def validate_model_field(self):
        """Ensure at least one model field is specified"""
        if self.llm_model is None and self.model is None:
            self.llm_model = "openai/gpt-4o-mini"  # Default model

        # Use llm_model if model not specified
        if self.model is None and self.llm_model is not None:
            self.model = self.llm_model

        # Use model if llm_model not specified
        if self.llm_model is None and self.model is not None:
            self.llm_model = self.model

        return self

    @model_validator(mode='after')
    def validate_decision_style_field(self):
        """Merge decision_style and decision_making_style fields"""
        if self.decision_style is None and self.decision_making_style is not None:
            self.decision_style = self.decision_making_style

        return self

    model_config = {
        "extra": "allow",  # Allow extra fields for forward compatibility
        "use_enum_values": True,
    }
