# Scenario Lab V4 – Implementation Plan

## Executive Summary

This document provides a complete implementation plan for Scenario Lab V4, a Python-based orchestration system for LLM-driven scenario simulations. The design philosophy is **radical simplicity**: Python handles orchestration only, while LLMs handle all reasoning and world simulation.

**Key Insight**: V4 eliminates the complex game logic from V3 (2000+ lines) in favor of a simple turn loop with four sequential LLM calls. The prompts *are* the logic.

---

## 1. Architecture Design

### 1.1 Core Design Principles

1. **LLM-First**: All simulation logic lives in prompts, not code
2. **Minimal Python**: Only orchestration, file I/O, and API calls
3. **Explicit Over Clever**: Simple, readable code over abstractions
4. **Testable Without LLM**: Support frozen prompts and mocked responses

### 1.2 Turn Structure

Each turn executes four sequential LLM calls:

```
┌─────────────────────────────────────────────────────────────────────┐
│  TURN N                                                             │
├─────────────────────────────────────────────────────────────────────┤
│  1. EVENTS          │ Which external events occur this turn?        │
│     Input:          │ metrics, world_state, events_list             │
│     Output:         │ JSON array of triggered events                │
├─────────────────────────────────────────────────────────────────────┤
│  2. ACTORS          │ What does each actor do? (parallel)           │
│     Input:          │ metrics, world_state, actor_background,       │
│                     │ triggered_events                              │
│     Output:         │ Markdown: goals + actions                     │
├─────────────────────────────────────────────────────────────────────┤
│  3. METRIC RULES    │ How should rules change based on actions?     │
│     Input:          │ current_rules, world_state, actor_actions     │
│     Output:         │ Markdown: numbered list of updated rules      │
├─────────────────────────────────────────────────────────────────────┤
│  4. METRICS UPDATE  │ Update metrics and generate narrative         │
│     Input:          │ metrics, rules, actor_actions, events         │
│     Output:         │ JSON metrics + Markdown narrative             │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Core Data Structures

```python
# scenario_lab/models.py

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
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
        return json.dumps({m.id: m.value for m in self.metrics.values()})
    
    def update_from_json(self, json_str: str) -> None:
        """Update values from LLM response."""
        data = json.loads(json_str)
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


@dataclass
class ScenarioConfig:
    """Scenario configuration."""
    name: str
    description: str
    start_date: str
    time_scale: str  # e.g., "6 months per turn"
    max_turns: int
    actor_ids: list[str]
    
    # LLM settings
    model: str = "anthropic/claude-sonnet-4"
    temperature: float = 0.7
    max_tokens: int = 2000


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
    
    # History
    turn_history: list[TurnResult] = field(default_factory=list)
    occurred_events: set[str] = field(default_factory=set)
```

### 1.4 Module Organization

```
scenario_lab/
├── __init__.py
├── models.py           # Data structures (above)
├── loader.py           # Load scenarios from disk
├── prompts.py          # Build prompts from templates + data
├── llm.py              # OpenRouter API client
├── orchestrator.py     # Main turn loop
├── output.py           # Save results to disk
└── cli.py              # Command-line interface

prompts/                # Prompt templates (markdown)
├── 01-events.md
├── 02-actor.md
├── 03-metric-rules.md
└── 04-metrics-update.md

scenarios/              # Scenario data
└── sweden-ai-2030/
    ├── scenario.yaml
    ├── metrics.md
    ├── metric-rules.md
    ├── events.md
    ├── background/
    │   ├── context.md
    │   └── actors/
    │       ├── government.md
    │       ├── labor-unions.md
    │       ├── media.md
    │       └── business-sector.md
    └── runs/
        └── run-YYYYMMDD-HHMMSS/
            ├── config.json
            ├── turn-01/
            │   ├── 1-events.json
            │   ├── 2-actors/
            │   │   └── *.md
            │   ├── 3-metric-rules.md
            │   ├── 4-metrics.json
            │   └── 4-world-state.md
            └── summary.json
```

---

## 2. File Structure

### 2.1 Complete Directory Tree

```
scenario-lab/
├── pyproject.toml              # Project configuration
├── README.md                   # User documentation
├── .env.example                # Environment template
├── .gitignore
│
├── scenario_lab/               # Main package
│   ├── __init__.py
│   ├── models.py               # Dataclasses for all entities
│   ├── loader.py               # Scenario loading from YAML/MD
│   ├── prompts.py              # Prompt construction
│   ├── llm.py                  # OpenRouter client
│   ├── orchestrator.py         # Turn execution logic
│   ├── output.py               # Results saving
│   └── cli.py                  # CLI entry point
│
├── prompts/                    # Prompt templates
│   ├── system/                 # System prompts (static per scenario)
│   │   ├── events.md
│   │   ├── actor.md
│   │   ├── metric-rules.md
│   │   └── metrics-update.md
│   └── user/                   # User prompt templates (turn-specific)
│       ├── events.md
│       ├── actor.md
│       ├── metric-rules.md
│       └── metrics-update.md
│
├── scenarios/                  # Scenario data
│   └── sweden-ai-2030/
│       ├── scenario.yaml
│       ├── metrics.md
│       ├── metric-rules.md
│       ├── events.md
│       ├── background/
│       │   ├── context.md
│       │   └── actors/
│       │       ├── government.md
│       │       ├── labor-unions.md
│       │       ├── media.md
│       │       └── business-sector.md
│       └── runs/               # Output directory
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_loader.py
│   ├── test_prompts.py
│   ├── test_llm.py
│   ├── test_orchestrator.py
│   ├── fixtures/               # Test data
│   │   ├── frozen_prompts/
│   │   └── expected_outputs/
│   └── conftest.py
│
└── docs/                       # Documentation
    ├── design.md
    └── prompts.md
```

### 2.2 Configuration Files

**pyproject.toml**
```toml
[project]
name = "scenario-lab"
version = "4.0.0"
description = "LLM-driven scenario simulation framework"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
scenario-lab = "scenario_lab.cli:main"
```

**.env.example**
```
OPENROUTER_API_KEY=your-key-here
```

---

## 3. Implementation Phases

### Phase 1: Foundation (Models + Loader)
**Goal**: Load scenario data from disk into memory.

**Files to Create**:
- `scenario_lab/models.py` - All dataclasses
- `scenario_lab/loader.py` - YAML/Markdown parsing

**Implementation**:

```python
# scenario_lab/loader.py

import yaml
from pathlib import Path
from .models import (
    Scenario, ScenarioConfig, Metric, Metrics, 
    Event, Actor, WorldState
)

def load_scenario(path: Path) -> Scenario:
    """Load a complete scenario from directory."""
    scenario_dir = Path(path)
    
    # Load config
    config = load_config(scenario_dir / "scenario.yaml")
    
    # Load metrics
    metrics = load_metrics(scenario_dir / "metrics.md")
    
    # Load events
    events = load_events(scenario_dir / "events.md")
    
    # Load actors
    actors = {}
    actors_dir = scenario_dir / "background" / "actors"
    for actor_id in config.actor_ids:
        actors[actor_id] = load_actor(actors_dir / f"{actor_id}.md")
    
    # Load context
    context = (scenario_dir / "background" / "context.md").read_text()
    
    # Load initial metric rules
    metric_rules = (scenario_dir / "metric-rules.md").read_text()
    
    # Create initial world state from context
    world_state = WorldState(
        narrative=context,
        turn=0,
        time_period=get_time_period(config.start_date, 0, config.time_scale)
    )
    
    return Scenario(
        config=config,
        metrics=metrics,
        events=events,
        actors=actors,
        metric_rules=metric_rules,
        world_state=world_state,
        context=context,
    )


def load_config(path: Path) -> ScenarioConfig:
    """Load scenario.yaml."""
    data = yaml.safe_load(path.read_text())
    return ScenarioConfig(
        name=data["name"],
        description=data["description"],
        start_date=data["start_date"],
        time_scale=data["time_scale"],
        max_turns=data["max_turns"],
        actor_ids=data["actors"],
        model=data.get("llm", {}).get("model", "anthropic/claude-sonnet-4"),
        temperature=data.get("llm", {}).get("temperature", 0.7),
        max_tokens=data.get("llm", {}).get("max_tokens", 2000),
    )


def load_metrics(path: Path) -> Metrics:
    """Parse metrics from markdown file."""
    content = path.read_text()
    metrics = {}
    
    # Parse markdown structure
    # Expected format: ## metric_id, then **Key:** Value
    current_metric = None
    metric_data = {}
    
    for line in content.split("\n"):
        if line.startswith("## "):
            # Save previous metric
            if current_metric and metric_data:
                metrics[current_metric] = create_metric(current_metric, metric_data)
            current_metric = line[3:].strip()
            metric_data = {}
        elif line.startswith("**") and ":" in line:
            key, value = parse_key_value(line)
            metric_data[key.lower()] = value
    
    # Don't forget last metric
    if current_metric and metric_data:
        metrics[current_metric] = create_metric(current_metric, metric_data)
    
    return Metrics(metrics=metrics)


def load_events(path: Path) -> list[Event]:
    """Parse events from markdown file."""
    content = path.read_text()
    events = []
    current_event = {}
    
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_event:
                events.append(create_event(current_event))
            current_event = {"name": line[3:].strip()}
        elif line.startswith("**") and ":" in line:
            key, value = parse_key_value(line)
            current_event[key.lower()] = value
    
    if current_event:
        events.append(create_event(current_event))
    
    return events


def load_actor(path: Path) -> Actor:
    """Parse actor from markdown file."""
    content = path.read_text()
    # Parse sections: # Name, ## Kort beskrivning, ## Längre beskrivning, etc.
    # Implementation details omitted for brevity
    ...


def get_time_period(start_date: str, turn: int, time_scale: str) -> str:
    """Calculate time period string for a given turn."""
    # Parse "6 months per turn" and calculate
    # Return format like "January-June 2026"
    ...
```

**Testing Phase 1**:
```python
# tests/test_loader.py

def test_load_scenario():
    scenario = load_scenario(Path("scenarios/sweden-ai-2030"))
    
    assert scenario.config.name == "Sverige och AI 2030"
    assert len(scenario.actors) == 4
    assert "ai_capability" in scenario.metrics.metrics
    assert len(scenario.events) > 0
```

**Dependencies**: None
**Deliverable**: Can load any scenario from disk

---

### Phase 2: Prompt Builder
**Goal**: Construct complete prompts from templates and data.

**Files to Create**:
- `scenario_lab/prompts.py`
- `prompts/system/*.md`
- `prompts/user/*.md`

**Implementation**:

```python
# scenario_lab/prompts.py

from pathlib import Path
from .models import Scenario, Actor, TurnResult
import json

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptBuilder:
    """Constructs prompts from templates and scenario data."""
    
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates."""
        self.templates = {
            "events_system": (PROMPTS_DIR / "system" / "events.md").read_text(),
            "events_user": (PROMPTS_DIR / "system" / "events.md").read_text(),
            "actor_system": (PROMPTS_DIR / "system" / "actor.md").read_text(),
            "actor_user": (PROMPTS_DIR / "user" / "actor.md").read_text(),
            "rules_system": (PROMPTS_DIR / "system" / "metric-rules.md").read_text(),
            "rules_user": (PROMPTS_DIR / "user" / "metric-rules.md").read_text(),
            "metrics_system": (PROMPTS_DIR / "system" / "metrics-update.md").read_text(),
            "metrics_user": (PROMPTS_DIR / "user" / "metrics-update.md").read_text(),
        }
    
    def build_events_prompt(self, turn: int) -> tuple[str, str]:
        """Build system and user prompts for events step."""
        time_period = self._get_time_period(turn)
        
        system = self._fill_template(
            self.templates["events_system"],
            actors_list=self._format_actors_short(),
            metrics_definitions=self._format_metrics_definitions(),
        )
        
        user = self._fill_template(
            self.templates["events_user"],
            turn=turn,
            time_period=time_period,
            current_metrics=self.scenario.metrics.to_json(),
            metrics_history=self._format_metrics_history(),
            world_state=self.scenario.world_state.narrative,
            events_list=self._format_events_list(),
        )
        
        return system, user
    
    def build_actor_prompt(self, actor_id: str, turn: int, 
                           triggered_events: list[dict]) -> tuple[str, str]:
        """Build prompts for a specific actor."""
        actor = self.scenario.actors[actor_id]
        time_period = self._get_time_period(turn)
        
        system = self._fill_template(
            self.templates["actor_system"],
            scenario_focus=self.scenario.config.description,
            metrics_definitions=self._format_metrics_definitions(),
            actors_list=self._format_actors_short(),
            actor_name=actor.name,
            actor_description=actor.long_description,
            actor_traits=self._format_traits(actor),
            actor_goals=self._format_goals(actor),
        )
        
        user = self._fill_template(
            self.templates["actor_user"],
            turn=turn,
            time_period=time_period,
            current_metrics=self.scenario.metrics.to_json(),
            metrics_history=self._format_metrics_history(),
            world_state=self.scenario.world_state.narrative,
            triggered_events=self._format_triggered_events(triggered_events),
        )
        
        return system, user
    
    def build_rules_prompt(self, turn: int, actor_actions: dict[str, str],
                           triggered_events: list[dict]) -> tuple[str, str]:
        """Build prompts for metric rules update."""
        time_period = self._get_time_period(turn)
        
        system = self._fill_template(
            self.templates["rules_system"],
            actors_list=self._format_actors_short(),
            metrics_definitions=self._format_metrics_definitions(),
        )
        
        user = self._fill_template(
            self.templates["rules_user"],
            turn=turn,
            time_period=time_period,
            current_rules=self.scenario.metric_rules,
            world_state=self.scenario.world_state.narrative,
            triggered_events=self._format_triggered_events(triggered_events),
            actor_actions=self._format_actor_actions(actor_actions),
        )
        
        return system, user
    
    def build_metrics_prompt(self, turn: int, actor_actions: dict[str, str],
                             triggered_events: list[dict]) -> tuple[str, str]:
        """Build prompts for metrics update."""
        time_period = self._get_time_period(turn)
        
        system = self._fill_template(
            self.templates["metrics_system"],
            actors_list=self._format_actors_short(),
            metrics_definitions=self._format_metrics_definitions(),
        )
        
        user = self._fill_template(
            self.templates["metrics_user"],
            turn=turn,
            time_period=time_period,
            current_metrics=self.scenario.metrics.to_json(),
            current_rules=self.scenario.metric_rules,
            world_state=self.scenario.world_state.narrative,
            triggered_events=self._format_triggered_events(triggered_events),
            actor_actions=self._format_actor_actions(actor_actions),
        )
        
        return system, user
    
    def _fill_template(self, template: str, **kwargs) -> str:
        """Simple template filling with {key} placeholders."""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _format_actors_short(self) -> str:
        """Format actors list for prompts."""
        lines = []
        for actor in self.scenario.actors.values():
            lines.append(f"* {actor.name}: {actor.short_description}")
        return "\n".join(lines)
    
    def _format_metrics_definitions(self) -> str:
        """Format metrics with full definitions."""
        lines = []
        for m in self.scenario.metrics.metrics.values():
            lines.append(f"* {m.id}")
            lines.append(f"  * Beskrivning: {m.description}")
            lines.append(f"  * Min: {m.min_value}, Max: {m.max_value}, Enhet: {m.unit}")
            if m.reference_points:
                refs = ", ".join(f"{v} ({desc})" for v, desc in m.reference_points.items())
                lines.append(f"  * Referenspunkter: {refs}")
        return "\n".join(lines)
    
    def _format_events_list(self) -> str:
        """Format available events for events prompt."""
        lines = []
        for event in self.scenario.events:
            # Skip already-occurred non-repeatable events
            if event.occurred and not event.can_repeat:
                continue
            lines.append(f"**{event.id}**")
            lines.append(f"- Villkor: {event.condition}")
            lines.append(f"- Sannolikhet: {event.probability}")
            lines.append(f"- Kan upprepas: {'Ja' if event.can_repeat else 'Nej'}")
            lines.append(f"- Beskrivning: {event.description}")
            lines.append("")
        return "\n".join(lines)
    
    # Additional helper methods...
```

**Testing Phase 2**:
```python
# tests/test_prompts.py

def test_events_prompt_construction():
    scenario = load_scenario(Path("scenarios/sweden-ai-2030"))
    builder = PromptBuilder(scenario)
    
    system, user = builder.build_events_prompt(turn=1)
    
    assert "ai_capability" in system
    assert "runda 1" in user
    assert "ai_breakthrough" in user  # Event should be listed


def test_actor_prompt_construction():
    scenario = load_scenario(Path("scenarios/sweden-ai-2030"))
    builder = PromptBuilder(scenario)
    
    system, user = builder.build_actor_prompt("government", turn=1, triggered_events=[])
    
    assert "Regeringen" in system
    assert "Mål" in system
```

**Dependencies**: Phase 1
**Deliverable**: Can construct all four types of prompts

---

### Phase 3: LLM Client
**Goal**: Call OpenRouter API and parse responses.

**Files to Create**:
- `scenario_lab/llm.py`

**Implementation**:

```python
# scenario_lab/llm.py

import httpx
import json
import os
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMResponse:
    """Parsed response from LLM."""
    content: str
    raw_response: dict
    
    def extract_json(self) -> dict:
        """Extract JSON from markdown code block or raw content."""
        # Try to find ```json ... ``` block
        match = re.search(r'```json\s*(.*?)\s*```', self.content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Try raw JSON
        return json.loads(self.content)
    
    def extract_json_array(self) -> list:
        """Extract JSON array from response."""
        data = self.extract_json()
        if isinstance(data, list):
            return data
        raise ValueError("Expected JSON array")
    
    def extract_metrics_and_narrative(self) -> tuple[dict, str]:
        """Extract metrics JSON and narrative from metrics update response."""
        # Find ## Metrics section with JSON
        metrics_match = re.search(
            r'##\s*Metrics\s*\n+```json\s*(.*?)\s*```',
            self.content, re.DOTALL | re.IGNORECASE
        )
        if not metrics_match:
            # Try without code block
            metrics_match = re.search(
                r'##\s*Metrics\s*\n+(\{.*?\})',
                self.content, re.DOTALL | re.IGNORECASE
            )
        
        if not metrics_match:
            raise ValueError("Could not find metrics in response")
        
        metrics = json.loads(metrics_match.group(1))
        
        # Find ## Narrativ section
        narrative_match = re.search(
            r'##\s*Narrativ\s*\n+(.*)',
            self.content, re.DOTALL | re.IGNORECASE
        )
        
        narrative = narrative_match.group(1).strip() if narrative_match else ""
        
        return metrics, narrative


class LLMClient:
    """Client for OpenRouter API."""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-sonnet-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.Client(timeout=120.0)
    
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Send a completion request."""
        response = self.client.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
        )
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        return LLMResponse(content=content, raw_response=data)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


class MockLLMClient:
    """Mock client for testing without API calls."""
    
    def __init__(self, responses: dict[str, str]):
        """
        responses: dict mapping prompt substrings to response content.
        Example: {"events": "[{...}]", "government": "## Mål\n..."}
        """
        self.responses = responses
        self.calls: list[tuple[str, str]] = []
    
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return pre-configured response based on prompt content."""
        self.calls.append((system_prompt, user_prompt))
        
        for key, content in self.responses.items():
            if key.lower() in user_prompt.lower() or key.lower() in system_prompt.lower():
                return LLMResponse(content=content, raw_response={})
        
        raise ValueError(f"No mock response configured for prompt")
    
    def close(self):
        pass
```

**Testing Phase 3**:
```python
# tests/test_llm.py

def test_extract_json():
    response = LLMResponse(
        content='```json\n[{"id": "test", "probability": 0.1}]\n```',
        raw_response={}
    )
    result = response.extract_json_array()
    assert result == [{"id": "test", "probability": 0.1}]


def test_extract_metrics_and_narrative():
    response = LLMResponse(
        content='''## Metrics
```json
{"ai_capability": 6, "unemployment": 8}
```

## Narrativ

Sweden is changing...''',
        raw_response={}
    )
    metrics, narrative = response.extract_metrics_and_narrative()
    assert metrics["ai_capability"] == 6
    assert "Sweden" in narrative
```

**Dependencies**: None (can be developed in parallel with Phase 2)
**Deliverable**: Can make API calls and parse all response formats

---

### Phase 4: Orchestrator
**Goal**: Execute the complete turn loop.

**Files to Create**:
- `scenario_lab/orchestrator.py`

**Implementation**:

```python
# scenario_lab/orchestrator.py

import random
from typing import Protocol
from .models import Scenario, TurnResult, Event
from .prompts import PromptBuilder
from .llm import LLMClient, LLMResponse


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (real or mock)."""
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse: ...
    def close(self): ...


class Orchestrator:
    """Executes the simulation turn loop."""
    
    def __init__(self, scenario: Scenario, llm_client: LLMClientProtocol):
        self.scenario = scenario
        self.llm = llm_client
        self.prompt_builder = PromptBuilder(scenario)
    
    def run_turn(self, turn: int) -> TurnResult:
        """Execute one complete turn."""
        time_period = self._get_time_period(turn)
        
        # Step 1: Determine events
        triggered_events = self._run_events_step(turn)
        
        # Step 2: Get actor actions (could be parallelized)
        actor_outputs = self._run_actors_step(turn, triggered_events)
        
        # Step 3: Update metric rules
        new_rules = self._run_rules_step(turn, actor_outputs, triggered_events)
        self.scenario.metric_rules = new_rules
        
        # Step 4: Update metrics and generate narrative
        new_metrics, narrative = self._run_metrics_step(
            turn, actor_outputs, triggered_events
        )
        
        # Update scenario state
        self._update_scenario_state(new_metrics, narrative, turn, time_period)
        
        # Build and return result
        return TurnResult(
            turn=turn,
            time_period=time_period,
            triggered_events=triggered_events,
            actor_outputs=actor_outputs,
            metric_rules=new_rules,
            metrics=new_metrics,
            narrative=narrative,
        )
    
    def _run_events_step(self, turn: int) -> list[dict]:
        """Step 1: Determine which events occur."""
        system, user = self.prompt_builder.build_events_prompt(turn)
        response = self.llm.complete(system, user)
        
        # Parse LLM response: list of events with probabilities
        candidate_events = response.extract_json_array()
        
        # Roll dice for each event
        triggered = []
        for event_data in candidate_events:
            event_id = event_data["id"]
            probability = event_data["probability"]
            
            if random.random() < probability:
                triggered.append(event_data)
                # Mark non-repeatable events as occurred
                self._mark_event_occurred(event_id)
        
        return triggered
    
    def _run_actors_step(self, turn: int, 
                         triggered_events: list[dict]) -> dict[str, str]:
        """Step 2: Get actions from each actor."""
        outputs = {}
        
        for actor_id in self.scenario.actors:
            system, user = self.prompt_builder.build_actor_prompt(
                actor_id, turn, triggered_events
            )
            response = self.llm.complete(system, user)
            outputs[actor_id] = response.content
            
            # Update actor's goals/actions in scenario
            self.scenario.actors[actor_id].last_actions = response.content
        
        return outputs
    
    def _run_rules_step(self, turn: int, actor_outputs: dict[str, str],
                        triggered_events: list[dict]) -> str:
        """Step 3: Update metric rules."""
        system, user = self.prompt_builder.build_rules_prompt(
            turn, actor_outputs, triggered_events
        )
        response = self.llm.complete(system, user)
        return response.content
    
    def _run_metrics_step(self, turn: int, actor_outputs: dict[str, str],
                          triggered_events: list[dict]) -> tuple[dict, str]:
        """Step 4: Update metrics and generate narrative."""
        system, user = self.prompt_builder.build_metrics_prompt(
            turn, actor_outputs, triggered_events
        )
        response = self.llm.complete(system, user)
        return response.extract_metrics_and_narrative()
    
    def _mark_event_occurred(self, event_id: str):
        """Mark event as occurred (for non-repeatable events)."""
        for event in self.scenario.events:
            if event.id == event_id and not event.can_repeat:
                event.occurred = True
                self.scenario.occurred_events.add(event_id)
    
    def _update_scenario_state(self, new_metrics: dict, narrative: str,
                               turn: int, time_period: str):
        """Update scenario with turn results."""
        self.scenario.metrics.update_from_json(json.dumps(new_metrics))
        self.scenario.world_state.narrative = narrative
        self.scenario.world_state.turn = turn
        self.scenario.world_state.time_period = time_period
    
    def _get_time_period(self, turn: int) -> str:
        """Calculate time period for turn."""
        # Implementation depends on time_scale
        ...


def run_simulation(scenario: Scenario, llm_client: LLMClientProtocol,
                   num_turns: Optional[int] = None) -> list[TurnResult]:
    """Run a complete simulation."""
    orchestrator = Orchestrator(scenario, llm_client)
    max_turns = num_turns or scenario.config.max_turns
    results = []
    
    for turn in range(1, max_turns + 1):
        result = orchestrator.run_turn(turn)
        results.append(result)
        scenario.turn_history.append(result)
    
    return results
```

**Testing Phase 4**:
```python
# tests/test_orchestrator.py

def test_orchestrator_with_mock():
    scenario = load_scenario(Path("scenarios/sweden-ai-2030"))
    
    # Load frozen responses
    mock_responses = {
        "events": '[{"id": "ai_breakthrough", "probability": 0.05}]',
        "government": "## Mål\n- Goal 1\n\n## Handlingar\n...",
        # ... other responses
    }
    
    mock_llm = MockLLMClient(mock_responses)
    orchestrator = Orchestrator(scenario, mock_llm)
    
    result = orchestrator.run_turn(1)
    
    assert result.turn == 1
    assert "government" in result.actor_outputs
```

**Dependencies**: Phases 1, 2, 3
**Deliverable**: Can execute complete turns

---

### Phase 5: Output & Persistence
**Goal**: Save results to disk in the specified format.

**Files to Create**:
- `scenario_lab/output.py`

**Implementation**:

```python
# scenario_lab/output.py

import json
from pathlib import Path
from datetime import datetime
from .models import Scenario, TurnResult, ScenarioConfig


class OutputManager:
    """Manages saving simulation results to disk."""
    
    def __init__(self, scenario: Scenario, base_path: Path):
        self.scenario = scenario
        self.base_path = base_path
        self.run_dir: Optional[Path] = None
    
    def start_run(self) -> Path:
        """Create a new run directory."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = self.base_path / "runs" / f"run-{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save config snapshot
        self._save_config()
        
        return self.run_dir
    
    def save_turn(self, result: TurnResult):
        """Save results from a single turn."""
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")
        
        turn_dir = self.run_dir / f"turn-{result.turn:02d}"
        turn_dir.mkdir(exist_ok=True)
        
        # 1. Events
        (turn_dir / "1-events.json").write_text(
            json.dumps(result.triggered_events, indent=2)
        )
        
        # 2. Actor outputs
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir(exist_ok=True)
        for actor_id, output in result.actor_outputs.items():
            (actors_dir / f"{actor_id}.md").write_text(output)
        
        # 3. Metric rules
        (turn_dir / "3-metric-rules.md").write_text(result.metric_rules)
        
        # 4. Metrics
        (turn_dir / "4-metrics.json").write_text(
            json.dumps(result.metrics, indent=2)
        )
        
        # 5. World state narrative
        (turn_dir / "4-world-state.md").write_text(result.narrative)
    
    def save_summary(self, results: list[TurnResult]):
        """Save final summary."""
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")
        
        summary = {
            "scenario": self.scenario.config.name,
            "total_turns": len(results),
            "final_metrics": results[-1].metrics if results else {},
            "occurred_events": list(self.scenario.occurred_events),
            "completed_at": datetime.now().isoformat(),
        }
        
        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2)
        )
    
    def _save_config(self):
        """Save scenario configuration snapshot."""
        config = {
            "name": self.scenario.config.name,
            "description": self.scenario.config.description,
            "start_date": self.scenario.config.start_date,
            "time_scale": self.scenario.config.time_scale,
            "max_turns": self.scenario.config.max_turns,
            "actors": self.scenario.config.actor_ids,
            "model": self.scenario.config.model,
            "temperature": self.scenario.config.temperature,
        }
        (self.run_dir / "config.json").write_text(
            json.dumps(config, indent=2)
        )
```

**Dependencies**: Phase 4
**Deliverable**: Complete file output matching specification

---

### Phase 6: CLI
**Goal**: Command-line interface for running simulations.

**Files to Create**:
- `scenario_lab/cli.py`

**Implementation**:

```python
# scenario_lab/cli.py

import argparse
from pathlib import Path
from dotenv import load_dotenv

from .loader import load_scenario
from .llm import LLMClient
from .orchestrator import run_simulation
from .output import OutputManager


def main():
    """CLI entry point."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Scenario Lab V4 - LLM-driven scenario simulation"
    )
    parser.add_argument(
        "scenario",
        type=Path,
        help="Path to scenario directory"
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to run (default: from config)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override LLM model"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling LLM"
    )
    
    args = parser.parse_args()
    
    # Load scenario
    print(f"Loading scenario from {args.scenario}...")
    scenario = load_scenario(args.scenario)
    
    if args.model:
        scenario.config.model = args.model
    
    if args.dry_run:
        run_dry(scenario)
        return
    
    # Run simulation
    print(f"Running simulation: {scenario.config.name}")
    print(f"Model: {scenario.config.model}")
    print(f"Turns: {args.turns or scenario.config.max_turns}")
    
    llm_client = LLMClient(
        model=scenario.config.model,
        temperature=scenario.config.temperature,
        max_tokens=scenario.config.max_tokens,
    )
    
    output_manager = OutputManager(scenario, args.scenario)
    run_dir = output_manager.start_run()
    print(f"Output directory: {run_dir}")
    
    try:
        results = run_simulation(scenario, llm_client, args.turns)
        
        for result in results:
            output_manager.save_turn(result)
            print(f"Turn {result.turn} complete: {result.time_period}")
        
        output_manager.save_summary(results)
        print(f"\nSimulation complete. Results saved to {run_dir}")
        
    finally:
        llm_client.close()


def run_dry(scenario):
    """Print prompts without calling LLM."""
    from .prompts import PromptBuilder
    
    builder = PromptBuilder(scenario)
    
    print("\n=== EVENTS PROMPT ===")
    system, user = builder.build_events_prompt(1)
    print("SYSTEM:", system[:500], "...")
    print("\nUSER:", user[:500], "...")
    
    print("\n=== ACTOR PROMPT (government) ===")
    system, user = builder.build_actor_prompt("government", 1, [])
    print("SYSTEM:", system[:500], "...")
    print("\nUSER:", user[:500], "...")


if __name__ == "__main__":
    main()
```

**Dependencies**: All previous phases
**Deliverable**: Working command-line tool

---

## 4. Data Flow

### 4.1 Complete Turn Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         TURN N BEGINS                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT STATE:                                                        │
│  ├── metrics: {ai_capability: 3, unemployment: 8, ...}              │
│  ├── world_state: "Sweden stands at a turning point..."             │
│  ├── metric_rules: "1. ai_capability doubles every 6 months..."     │
│  ├── events: [ai_breakthrough, ai_stall, taiwan_blockade, ...]      │
│  └── occurred_events: {}                                            │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STEP 1: EVENTS                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PromptBuilder.build_events_prompt(turn=N)                     │ │
│  │  ↓                                                              │ │
│  │  LLM Call → "[{id: ai_breakthrough, probability: 0.05}, ...]"  │ │
│  │  ↓                                                              │ │
│  │  Orchestrator rolls dice → triggered_events = [{...}]          │ │
│  │  ↓                                                              │ │
│  │  Mark non-repeatable events as occurred                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  STEP 2: ACTORS (can run in parallel)                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  For each actor_id in [government, labor-unions, ...]:         │ │
│  │    PromptBuilder.build_actor_prompt(actor_id, turn, events)    │ │
│  │    ↓                                                            │ │
│  │    LLM Call → "## Mål\n- Goal 1...\n## Handlingar\n..."        │ │
│  │    ↓                                                            │ │
│  │    actor_outputs[actor_id] = response                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  STEP 3: METRIC RULES                                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PromptBuilder.build_rules_prompt(turn, actor_outputs, events) │ │
│  │  ↓                                                              │ │
│  │  LLM Call → "1. ai_capability...\n2. unemployment..."          │ │
│  │  ↓                                                              │ │
│  │  scenario.metric_rules = response                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  STEP 4: METRICS UPDATE                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PromptBuilder.build_metrics_prompt(turn, actions, events)     │ │
│  │  ↓                                                              │ │
│  │  LLM Call → "## Metrics\n{...}\n## Narrativ\n..."              │ │
│  │  ↓                                                              │ │
│  │  Parse JSON metrics + narrative                                │ │
│  │  ↓                                                              │ │
│  │  scenario.metrics.update(new_metrics)                          │ │
│  │  scenario.world_state.narrative = narrative                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  OUTPUT STATE (ready for Turn N+1):                                 │
│  ├── metrics: {ai_capability: 6, unemployment: 8.5, ...}           │
│  ├── world_state: "The first half of 2026 saw..."                  │
│  ├── metric_rules: "1. ai_capability doubles...\n2. ..."           │
│  └── occurred_events: {ai_breakthrough}                            │
│                                                                      │
│  SAVED TO DISK:                                                     │
│  └── turn-01/                                                       │
│      ├── 1-events.json                                              │
│      ├── 2-actors/{government, labor-unions, ...}.md                │
│      ├── 3-metric-rules.md                                          │
│      ├── 4-metrics.json                                             │
│      └── 4-world-state.md                                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 State Management

**Immutable During Turn**:
- Scenario config
- Actor backgrounds
- Event definitions

**Mutable After Each Step**:
- `scenario.occurred_events` (after Step 1)
- `scenario.actors[*].last_actions` (after Step 2)
- `scenario.metric_rules` (after Step 3)
- `scenario.metrics` (after Step 4)
- `scenario.world_state` (after Step 4)

---

## 5. Error Handling Strategy

### 5.1 API Errors

```python
# scenario_lab/llm.py

class LLMError(Exception):
    """Base exception for LLM errors."""
    pass

class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass

class LLMParseError(LLMError):
    """Could not parse LLM response."""
    pass


def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
    """Send request with retry logic."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = self.client.post(...)
            response.raise_for_status()
            return LLMResponse(...)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise LLMRateLimitError(f"Rate limit exceeded after {max_retries} retries")
            raise LLMError(f"HTTP error: {e.response.status_code}")
            
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                continue
            raise LLMError("Request timed out")
```

### 5.2 Response Validation

```python
# scenario_lab/orchestrator.py

def _run_events_step(self, turn: int) -> list[dict]:
    """Step 1 with validation."""
    system, user = self.prompt_builder.build_events_prompt(turn)
    response = self.llm.complete(system, user)
    
    try:
        events = response.extract_json_array()
    except (json.JSONDecodeError, ValueError) as e:
        # Log the raw response for debugging
        self._log_parse_error("events", response.content, e)
        # Return empty list - no events this turn
        return []
    
    # Validate event structure
    validated = []
    for event in events:
        if "id" not in event or "probability" not in event:
            continue
        if not 0 <= event["probability"] <= 1:
            continue
        if event["id"] not in {e.id for e in self.scenario.events}:
            continue
        validated.append(event)
    
    return validated


def _run_metrics_step(self, ...) -> tuple[dict, str]:
    """Step 4 with validation."""
    response = self.llm.complete(system, user)
    
    try:
        metrics, narrative = response.extract_metrics_and_narrative()
    except (json.JSONDecodeError, ValueError) as e:
        self._log_parse_error("metrics", response.content, e)
        # Return previous metrics with error narrative
        return (
            {m.id: m.value for m in self.scenario.metrics.metrics.values()},
            f"[ERROR: Could not parse metrics response. Keeping previous values.]"
        )
    
    # Validate metric values
    for metric_id, value in metrics.items():
        if metric_id in self.scenario.metrics.metrics:
            metric = self.scenario.metrics.metrics[metric_id]
            if not metric.min_value <= value <= metric.max_value:
                # Clamp to valid range
                metrics[metric_id] = max(metric.min_value, 
                                         min(metric.max_value, value))
    
    return metrics, narrative
```

### 5.3 Graceful Degradation

| Error | Recovery Strategy |
|-------|-------------------|
| Events parse failure | Return empty list, log warning |
| Actor parse failure | Keep previous goals/actions |
| Rules parse failure | Keep previous rules |
| Metrics parse failure | Keep previous metrics |
| API timeout | Retry with exponential backoff |
| Rate limit | Wait and retry |

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Location**: `tests/test_*.py`

```python
# tests/test_loader.py
def test_load_metrics_from_markdown(): ...
def test_load_events_from_markdown(): ...
def test_load_actor_from_markdown(): ...
def test_load_complete_scenario(): ...

# tests/test_prompts.py
def test_events_prompt_includes_metrics(): ...
def test_events_prompt_excludes_occurred_events(): ...
def test_actor_prompt_includes_background(): ...
def test_actor_prompt_includes_triggered_events(): ...

# tests/test_llm.py
def test_extract_json_from_code_block(): ...
def test_extract_json_array(): ...
def test_extract_metrics_and_narrative(): ...
def test_retry_on_rate_limit(): ...

# tests/test_orchestrator.py
def test_events_step_rolls_dice(): ...
def test_marks_non_repeatable_events(): ...
def test_full_turn_with_mock(): ...
```

### 6.2 Integration Tests with Frozen Prompts

Use the frozen prompts from `docs/V4/early-testing/frozen prompts/` to test without API calls:

```python
# tests/test_integration.py

from pathlib import Path

FROZEN_DIR = Path("docs/V4/early-testing/frozen prompts")


def test_full_turn_with_frozen_data():
    """Test complete turn using frozen prompts and expected outputs."""
    
    # Load frozen system prompts
    system_prompts = {
        "events": (FROZEN_DIR / "system prompts/events.md").read_text(),
        "government": (FROZEN_DIR / "system prompts/actor_government.md").read_text(),
        # ...
    }
    
    # Load frozen user prompts for turn 1
    user_prompts = {
        "events": (FROZEN_DIR / "turn1/events.md").read_text(),
        "government": (FROZEN_DIR / "turn1/actor_government.md").read_text(),
        # ...
    }
    
    # Load expected outputs
    expected_outputs = {
        "events": (FROZEN_DIR / "turn1/output/events.md").read_text(),
        "government": (FROZEN_DIR / "turn1/output/government.md").read_text(),
        # ...
    }
    
    # Configure mock with expected outputs
    mock_llm = MockLLMClient(expected_outputs)
    
    # Run turn
    scenario = load_scenario(Path("scenarios/sweden-ai-2030"))
    orchestrator = Orchestrator(scenario, mock_llm)
    result = orchestrator.run_turn(1)
    
    # Verify prompts were constructed correctly
    assert len(mock_llm.calls) == 6  # events + 4 actors + rules + metrics
```

### 6.3 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=scenario_lab

# Run specific test file
pytest tests/test_loader.py -v
```

---

## 7. Prompt Templates

### 7.1 System Prompt: Events (`prompts/system/events.md`)

```markdown
Det här är en del i en AI-driven scenarioövning. Du är Game Master för övningen.

Scenarioövningen omfattar de här aktörerna:
{actors_list}

En viktig del av beskrivningen av världen är dessa metrics:
{metrics_definitions}

Din uppgift är att gå igenom listan med möjliga externa händelser och för varje 
händelse utvärdera om dess villkor är uppfyllt utifrån nuvarande världsläge.

Om sannolikheten anges som en formel eller beskrivning, ska du beräkna det faktiska värdet.

Ditt svar ska vara en JSON-array med objekt för varje händelse vars villkor är 
uppfyllt, på det här formatet:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

Sannolikheten ska anges som ett värde mellan 0 och 1. Om ingen händelse uppfyller 
villkoren ska du svara med en tom array: `[]`
```

### 7.2 User Prompt: Events (`prompts/user/events.md`)

```markdown
Det är nu runda {turn} som omfattar {time_period}.

Nuvarande metrics:
```json
{current_metrics}
```

Världens tillstånd:
{world_state}

Listan över potentiella externa händelser:
{events_list}

Använd bakgrundsinformationen för att avgöra vilka externa event som kan inträffa.
Svara *endast* med JSON-arrayen, inget annat.
```

*(Similar templates for actor, rules, and metrics prompts)*

---

## 8. Implementation Checklist

### Week 1: Foundation
- [ ] Set up project structure and pyproject.toml
- [ ] Implement `models.py` with all dataclasses
- [ ] Implement `loader.py` with YAML/Markdown parsing
- [ ] Write unit tests for loader
- [ ] Verify loading works with sweden-ai-2030 scenario

### Week 2: Prompts & LLM
- [ ] Create prompt templates (4 system + 4 user)
- [ ] Implement `prompts.py` PromptBuilder
- [ ] Implement `llm.py` OpenRouter client
- [ ] Implement MockLLMClient for testing
- [ ] Write tests for prompt construction
- [ ] Test API calls manually

### Week 3: Orchestrator
- [ ] Implement `orchestrator.py` turn loop
- [ ] Add dice rolling for events
- [ ] Add state updates after each step
- [ ] Implement error handling
- [ ] Write integration tests with frozen prompts
- [ ] Test complete turn manually

### Week 4: Output & CLI
- [ ] Implement `output.py` file saving
- [ ] Implement `cli.py` command-line interface
- [ ] Add --dry-run mode
- [ ] Test full simulation run
- [ ] Write documentation
- [ ] Clean up and refactor

---

## 9. Design Decisions & Trade-offs

### Q1: Dataclasses vs Pydantic?

**Decision**: Use dataclasses with manual validation.

**Rationale**: Pydantic adds complexity and a dependency. The validation needs are simple (bounds checking, type conversion). Dataclasses are built-in and sufficient.

### Q2: Class-based vs Functional?

**Decision**: Hybrid approach.

**Rationale**: 
- Classes for stateful entities (Scenario, Orchestrator)
- Pure functions for parsing and formatting
- This balances testability with natural state management

### Q3: Parallel Actor Execution?

**Decision**: Sequential for MVP, parallelizable architecture.

**Rationale**: Actor calls are independent and could use `asyncio.gather()`. But sequential is simpler to debug. The architecture supports adding parallelism later without changes.

### Q4: Dynamic vs Frozen Prompts?

**Decision**: Support both.

**Rationale**: 
- Dynamic prompts for production
- Frozen prompts for testing and debugging
- The PromptBuilder output can be saved/loaded

### Q5: Store Raw LLM Responses?

**Decision**: Yes, in debug mode.

**Rationale**: Essential for debugging prompt engineering. Add optional `--debug` flag that saves full request/response to `turn-XX/debug/`.

---

## 10. Future Extensions

These are **not** in scope for V4 MVP but the architecture supports them:

1. **Batch Runs**: Run same scenario N times, aggregate statistics
2. **Actor Communication**: Add negotiation phase between actors
3. **Outcome Flags**: Structured markers for analysis
4. **Web UI**: Real-time visualization of simulation
5. **Async Execution**: Parallel actor calls
6. **Multi-Model**: Different models for different steps
7. **Human-in-the-Loop**: Allow human to control one actor

---

## Appendix A: Example Run Output

```
$ scenario-lab scenarios/sweden-ai-2030 --turns 2

Loading scenario from scenarios/sweden-ai-2030...
Running simulation: Sverige och AI 2030
Model: anthropic/claude-sonnet-4
Turns: 2
Output directory: scenarios/sweden-ai-2030/runs/run-20251202-143022

Turn 1 complete: January-June 2026
  Events: ai_breakthrough (triggered)
  Actors: government, labor-unions, media, business-sector
  Metrics: ai_capability=6, unemployment=8.2, public_sentiment=2

Turn 2 complete: July-December 2026
  Events: general_election_2026 (triggered)
  Actors: government, labor-unions, media, business-sector  
  Metrics: ai_capability=12, unemployment=9.1, public_sentiment=1

Simulation complete. Results saved to scenarios/sweden-ai-2030/runs/run-20251202-143022
```

---

*Document created: December 2, 2025*
*For: Scenario Lab V4 Implementation*
