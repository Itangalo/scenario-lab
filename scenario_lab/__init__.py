"""
Scenario Lab V3 - AI-powered scenario simulation framework.

A hybrid architecture combining LLM narrative generation with deterministic
Python logic for complex strategic simulations.
"""

from .engine import Simulation
from .models import (
    Actor,
    WorldState,
    ActorView,
    Metrics,
    ActorMetricsData,
    Message,
    MessageVisibility,
    ScenarioConfig,
    MetricsConfig,
    EventsConfig,
    RelationshipState,
    FactLedgerEntry,
)
from .methods_base import ScenarioMethods
from .llm_provider import get_provider

__version__ = "3.0.0"

__all__ = [
    "Simulation",
    "Actor",
    "WorldState",
    "ActorView",
    "Metrics",
    "ActorMetricsData",
    "Message",
    "MessageVisibility",
    "ScenarioConfig",
    "MetricsConfig",
    "EventsConfig",
    "RelationshipState",
    "FactLedgerEntry",
    "ScenarioMethods",
    "get_provider",
]
