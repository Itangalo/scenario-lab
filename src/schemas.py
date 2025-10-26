"""
Pydantic schemas for Scenario Lab

Provides validation and type safety for:
- Scenario configurations
- Actor definitions
- Metrics configurations
- Validation rules

This is Phase 2.0 (Foundation) work that benefits both Phase 3 and Version 2.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# Enums and Constants
# ============================================================================

class ActorControl(str, Enum):
    """How an actor is controlled"""
    AI = "ai"
    HUMAN = "human"


class CommunicationType(str, Enum):
    """Types of communication between actors"""
    PUBLIC = "public"
    BILATERAL = "bilateral"
    COALITION = "coalition"


class ScenarioLengthType(str, Enum):
    """How scenario length is determined"""
    FIXED = "fixed"
    CONDITION = "condition"


# ============================================================================
# Actor Schemas
# ============================================================================

class ActorConfig(BaseModel):
    """
    Configuration for a single actor

    Example:
        name: EU Representative
        control: ai
        model: gpt-4o
        role: European Union negotiator
        goals:
          - Ensure AI safety standards
          - Protect European values
    """
    name: str = Field(..., description="Actor display name")
    control: ActorControl = Field(default=ActorControl.AI, description="AI or human controlled")
    role: str = Field(..., description="Actor's role in the scenario")
    model: Optional[str] = Field(default="gpt-4o-mini", description="LLM model to use (if AI controlled)")

    # Actor characteristics
    goals: List[str] = Field(..., min_items=1, description="Long-term objectives")
    constraints: Optional[List[str]] = Field(default=None, description="Limitations or rules actor must follow")
    private_information: Optional[str] = Field(default=None, description="Information only this actor knows")
    personality_traits: Optional[List[str]] = Field(default=None, description="Behavioral characteristics")
    expertise_level: Optional[str] = Field(default="expert", description="Level of domain expertise")
    decision_making_style: Optional[str] = Field(default="rational", description="How actor makes decisions")

    # Communication preferences
    communication_style: Optional[str] = Field(default=None, description="How actor communicates")
    preferred_coalitions: Optional[List[str]] = Field(default=None, description="Actors this actor prefers to ally with")

    class Config:
        use_enum_values = True


# ============================================================================
# Scenario Schemas
# ============================================================================

class ScenarioLength(BaseModel):
    """How long the scenario runs"""
    type: ScenarioLengthType
    turns: Optional[int] = Field(default=None, description="Number of turns (if fixed)")
    condition: Optional[str] = Field(default=None, description="End condition (if condition-based)")

    @validator('turns')
    def validate_fixed_turns(cls, v, values):
        if values.get('type') == ScenarioLengthType.FIXED and v is None:
            raise ValueError("turns required when type is 'fixed'")
        return v

    @validator('condition')
    def validate_condition(cls, v, values):
        if values.get('type') == ScenarioLengthType.CONDITION and v is None:
            raise ValueError("condition required when type is 'condition'")
        return v

    class Config:
        use_enum_values = True


class BlackSwan(BaseModel):
    """Unexpected event that can occur during scenario"""
    name: str = Field(..., description="Event name")
    description: str = Field(..., description="What happens")
    probability: float = Field(..., ge=0.0, le=1.0, description="Chance of occurring each turn")
    turn_range: Optional[tuple[int, int]] = Field(default=None, description="When event can occur")
    effects: Optional[Dict[str, Any]] = Field(default=None, description="Impact on world state")


class ScenarioConfig(BaseModel):
    """
    Complete scenario configuration

    Example:
        name: AI Safety Summit 2025
        description: International negotiation on AI governance
        initial_world_state: |
          The year is 2025. Major AI capabilities...
        turn_duration: 1 week
        communication_types:
          - public
          - bilateral
        scenario_length:
          type: fixed
          turns: 10
    """
    # Basic metadata
    name: str = Field(..., description="Scenario display name")
    description: str = Field(..., description="Brief scenario summary")
    initial_world_state: str = Field(..., description="Starting world state description")

    # Temporal settings
    turn_duration: str = Field(..., description="How long each turn represents (e.g., '1 day', '1 week')")
    scenario_length: ScenarioLength = Field(..., description="How scenario length is determined")

    # Communication settings
    communication_types: List[CommunicationType] = Field(
        default=[CommunicationType.PUBLIC],
        description="Types of communication allowed"
    )

    # Optional features
    black_swans: Optional[List[BlackSwan]] = Field(default=None, description="Random events")
    background_information: Optional[str] = Field(default=None, description="Additional context for actors")
    success_criteria: Optional[List[str]] = Field(default=None, description="What constitutes success")

    # Metadata
    schema_version: str = Field(default="2.0", description="Schema version for compatibility")
    created_date: Optional[str] = Field(default=None, description="When scenario was created")
    author: Optional[str] = Field(default=None, description="Scenario creator")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")

    class Config:
        use_enum_values = True


# ============================================================================
# Metrics Schemas
# ============================================================================

class MetricExtraction(BaseModel):
    """How to extract a metric from scenario data"""
    type: Literal["keyword", "sentiment", "custom"] = Field(..., description="Extraction method")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to search for")
    prompt: Optional[str] = Field(default=None, description="Custom extraction prompt")


class MetricConfig(BaseModel):
    """
    Configuration for a tracked metric

    Example:
        name: cooperation_level
        description: Degree of cooperation between actors
        type: continuous
        range: [0, 10]
        extraction:
          type: keyword
          keywords: ["cooperate", "collaborate", "together"]
    """
    name: str = Field(..., description="Metric identifier")
    description: str = Field(..., description="What the metric measures")
    type: Literal["continuous", "categorical", "boolean"] = Field(..., description="Metric data type")

    # Range/options
    range: Optional[tuple[float, float]] = Field(default=None, description="Min/max for continuous metrics")
    categories: Optional[List[str]] = Field(default=None, description="Options for categorical metrics")

    # Extraction
    extraction: MetricExtraction = Field(..., description="How to extract this metric")

    # Thresholds
    warning_threshold: Optional[float] = Field(default=None, description="Value that triggers warning")
    critical_threshold: Optional[float] = Field(default=None, description="Value that triggers critical alert")


class MetricsConfig(BaseModel):
    """Configuration for all scenario metrics"""
    metrics: List[MetricConfig] = Field(..., min_items=1, description="Metrics to track")
    export_format: Optional[Literal["json", "csv", "both"]] = Field(default="json", description="Export format")


# ============================================================================
# Validation Schemas
# ============================================================================

class ValidationCheck(BaseModel):
    """A single validation check configuration"""
    name: str = Field(..., description="Check identifier")
    enabled: bool = Field(default=True, description="Whether check is active")
    severity: Literal["low", "medium", "high"] = Field(default="medium", description="Issue severity")


class ValidationConfig(BaseModel):
    """
    Configuration for QA validation

    Example:
        validation_model: gpt-4o-mini
        checks:
          actor_decision_consistency:
            enabled: true
            severity: medium
          world_state_coherence:
            enabled: true
            severity: high
    """
    validation_model: str = Field(default="gpt-4o-mini", description="LLM model for validation")

    checks: Dict[str, ValidationCheck] = Field(
        default={
            "actor_decision_consistency": ValidationCheck(name="actor_decision_consistency"),
            "world_state_coherence": ValidationCheck(name="world_state_coherence"),
            "information_access_consistency": ValidationCheck(name="information_access_consistency")
        },
        description="Validation checks to run"
    )

    run_after_each_turn: bool = Field(default=True, description="Run validation after every turn")
    generate_turn_reports: bool = Field(default=True, description="Generate per-turn reports")
    halt_on_critical: bool = Field(default=False, description="Stop scenario on critical issues")


# ============================================================================
# Helper Functions
# ============================================================================

def load_scenario_config(yaml_data: Dict[str, Any]) -> ScenarioConfig:
    """
    Load and validate scenario configuration from YAML data

    Args:
        yaml_data: Parsed YAML data

    Returns:
        Validated ScenarioConfig

    Raises:
        pydantic.ValidationError: If data is invalid
    """
    return ScenarioConfig(**yaml_data)


def load_actor_config(yaml_data: Dict[str, Any]) -> ActorConfig:
    """
    Load and validate actor configuration from YAML data

    Args:
        yaml_data: Parsed YAML data

    Returns:
        Validated ActorConfig

    Raises:
        pydantic.ValidationError: If data is invalid
    """
    return ActorConfig(**yaml_data)


def load_metrics_config(yaml_data: Dict[str, Any]) -> MetricsConfig:
    """
    Load and validate metrics configuration from YAML data

    Args:
        yaml_data: Parsed YAML data

    Returns:
        Validated MetricsConfig

    Raises:
        pydantic.ValidationError: If data is invalid
    """
    return MetricsConfig(**yaml_data)


def load_validation_config(yaml_data: Dict[str, Any]) -> ValidationConfig:
    """
    Load and validate validation configuration from YAML data

    Args:
        yaml_data: Parsed YAML data

    Returns:
        Validated ValidationConfig

    Raises:
        pydantic.ValidationError: If data is invalid
    """
    return ValidationConfig(**yaml_data)
