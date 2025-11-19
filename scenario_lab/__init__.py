"""
Scenario Lab V2 - AI-powered multi-actor scenario simulation framework

Version 2 represents a complete architectural evolution:
- Event-driven execution
- Immutable state management
- Modular phase services
- Web API support
- Database-backed analytics

While maintaining:
- Full backward compatibility with V1
- All existing features (resume, branch, batch, QA)
- Cost management and controls
"""

__version__ = "2.0.0-alpha.3"

# Core exports
from scenario_lab.core.events import EventBus, Event, EventType, get_event_bus, set_event_bus
from scenario_lab.core.orchestrator import ScenarioOrchestrator, PhaseService

# Model exports
from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    PhaseType,
    WorldState,
    ActorState,
    Decision,
    Communication,
    CostRecord,
    MetricRecord,
)

# Loader exports
from scenario_lab.loaders import ScenarioLoader

# Runner exports
from scenario_lab.runners import SyncRunner

# Database exports
from scenario_lab.database import Database

__all__ = [
    "__version__",
    # Events
    "EventBus",
    "Event",
    "EventType",
    "get_event_bus",
    "set_event_bus",
    # Orchestrator
    "ScenarioOrchestrator",
    "PhaseService",
    # State models
    "ScenarioState",
    "ScenarioStatus",
    "PhaseType",
    "WorldState",
    "ActorState",
    "Decision",
    "Communication",
    "CostRecord",
    "MetricRecord",
    # Loaders
    "ScenarioLoader",
    # Runners
    "SyncRunner",
    # Database
    "Database",
]
