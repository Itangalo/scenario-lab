# Scenario Lab V3 – Software Design Document

## 1. Executive Summary

**Scenario Lab** is a framework for simulating complex strategic and political scenarios using AI agents. The system focuses on AI policy, geopolitics, and organizational strategy.

The project's primary purpose is to explore how LLMs can be used for scenario simulation. Secondarily, it aims to identify patterns in outcomes through repeated simulations – both quantitatively (frequencies) and qualitatively (causal relationships).

V3 is a reboot that solves fundamental problems from earlier versions through a **hybrid architecture**:

- **Narrative flexibility:** LLMs handle diplomacy, intentions, and qualitative descriptions.
- **Deterministic logic:** Python code handles quantitative consequences, resource flows, and verifiable facts.
- **Information asymmetry:** Actors have private and public information, creating realistic uncertainty.

---

## 2. Architecture & Core Concepts

The system consists of a central **Engine** (Python) that orchestrates the game, calls **LLM APIs** to act as different actors, and maintains **World State**.

### 2.1 Key Concepts

- **World State:** The truth about the world at a given point in time. Consists of four layers:
  1. **Narrative State:** Running text description (history + current situation).
  2. **Metrics:** Quantitative data, divided into global, private, and public (see 2.2).
  3. **Fact Ledger:** Verified hard facts that are never summarized away.
  4. **Relationship State:** Structured data per actor pair (trust, active_agreements).

- **The Director:** A specialized system agent that weaves actions and events into coherent narrative.

- **Actors:** The simulation's participants (countries, companies, organizations). Controlled by LLM personas with specific goals.

- **Action Points (AP):** Currency that limits communication and attention.

### 2.2 Metrics & Information Asymmetry

Metrics are divided into three categories:
````yaml
# metrics.yaml
world:
  global_temperature: 1.2
  ai_catastrophe_risk: 0.05

actors:
  USA:
    private:
      military_capacity: 85
      nuclear_stockpile: 5500
    public:
      budget: 500
      gdp: 25000
  China:
    private:
      military_capacity: 90
      nuclear_stockpile: 350
    public:
      budget: 400
      gdp: 18000
````

**Visibility rules:**
- `world`: Visible to all actors.
- `public`: Visible to all actors.
- `private`: Visible only to the owner.

If private metrics are revealed through actions (e.g., military capacity during a declaration of war), actors draw their own conclusions based on the narrative.

### 2.3 Goal Dynamics

Actors have semi-hard goals that persist between turns. The system defines explicit triggers for "World Altering Events" in scenario.yaml:
````yaml
world_altering_triggers:
  - condition: "tension > 90"
  - condition: "war_declared == true"
  - condition: "ai_catastrophe_risk > 0.5"
````

When a trigger activates, the system signals affected actors: "A drastic event has occurred. You may freely adjust your goals this turn." In other turns, actors are instructed to only adjust goals marginally.

### 2.4 Relationship State

To handle long-term relationships without relying on narrative continuity:
````yaml
# Generated automatically, updated by methods.py
relationships:
  USA-China:
    trust: -2
    active_agreements: ["Climate Accord 2024"]
    conflict_history: ["Trade War 2025"]
  USA-EU:
    trust: 3
    active_agreements: ["NATO", "Trade Deal"]
```

---

## 3. The Simulation Loop

Each turn represents a time period (e.g., 6 months).

### Pre-Turn

1. **Event Check:** The system evaluates scheduled and conditional events.
2. **Trigger Check:** World Altering Events are flagged.
3. **AP Reset:** All actors receive their Action Points.
4. **View Generation:** The system generates actor-specific World State (filtered by visibility).

### Phase 1: Initiative & Communication

Actors receive their filtered World State. They may initiate diplomacy.

- **Action:** Send messages (Signals/Cables).
- **Cost:** 1 AP per recipient.
- **Output:** Text messages with metadata (intent, visibility).

### Phase 2: Response & Final Negotiation

Actors receive incoming messages from Phase 1.

- **Reply to sender:** 0 AP (guarantees negotiations can complete).
- **New message/Forward:** 1 AP.

### Phase 3: Execution & Goal Adjustment

Diplomacy is concluded. Everyone acts.

- **Input:** Filtered World State + communication results + current goals + any World Altering Event flag.
- **Output:**
  - Narrative text (reasoning).
  - Structured function calls for metrics impact.
  - Updated goal list (`next_turn_goals`).
- **Constraint:** Maximum 2 major initiatives per turn, validated by `methods.py`.

### Post-Turn Synthesis

1. **Validation:** `methods.py` validates and executes function calls. Invalid actions are rejected.
2. **Metrics Update:** Code updates metrics and generates data interpretations.
3. **Relationship Update:** Trust and agreements are updated structurally.
4. **Fact Ledger Update:** New facts and outcome flags are added.
5. **Narrative Synthesis:** The Director generates `world_state.md` based on actions, events, and data interpretations.

---

## 4. Data Model & File Structure
```
scenario-name/
├── background/
│   ├── context.md
│   └── actors/
│       ├── USA.md
│       └── China.md
├── scenario.yaml          # Time scale, AP rules, world_altering_triggers
├── metrics.yaml           # World + actors (private/public)
├── events.yaml            # Exogenous events
├── methods.py             # Logic, validation, interpretations
└── runs/
    └── run-001/
        ├── turn-01/
        │   ├── views/
        │   │   ├── USA.json      # Actor-specific World State
        │   │   └── China.json
        │   ├── comms_phase_1.json
        │   ├── comms_phase_2.json
        │   ├── actions.json
        │   ├── world_state.md
        │   ├── metrics.json
        │   ├── relationships.json
        │   └── fact_ledger.json
        └── summary.json          # Outcome flags for analysis
````

### 4.1 Outcome Flags

To enable quantitative analysis without NLP, structured flags are set by `methods.py`:
````python
def declare_war(attacker, defender, state):
    state["outcome_flags"]["war_declared"] = True
    state["outcome_flags"]["war_parties"] = [attacker, defender]
    # ... remaining logic
````

These are aggregated in `summary.json` after each run for batch analysis.

### 4.2 The methods.py Contract

`methods.py` is scenario-specific. Each scenario defines its own action functions. The engine calls them dynamically based on `function_call` names in LLM output.

**Standard signature:**
````python
def action_name(actor: str, args: dict, state: WorldState) -> list[str]:
    """
    Modify state.metrics and state.outcome_flags as needed.
    Return list of interpretation strings for the Director.
    """
    pass
````

**Example:**
````python
def invest_research(actor: str, args: dict, state: WorldState) -> list[str]:
    amount = args["amount"]
    current_budget = state.get_metric(actor, "budget")
    
    if amount > current_budget:
        return [f"{actor} attempted to invest {amount} but only has {current_budget}."]
    
    state.set_metric(actor, "budget", current_budget - amount)
    ai_cap = state.get_metric(actor, "ai_capability", default=0)
    state.set_metric(actor, "ai_capability", ai_cap + amount * 0.1)
    
    return [f"{actor} invested {amount} in AI research, advancing their capabilities."]
````

---

## 5. Memory Management

For long simulations:

1. **Narrative:** Rolling window – last 2 turns in detail, summary of earlier epochs.
2. **Fact Ledger:** Critical points that are never summarized away.
3. **Relationship State:** Structured data that replaces the need for narrative relationship memory.
4. **Metrics:** Latest snapshot + data interpretations.

---

## 6. Analysis

### Batch Runs

Outcome flags enable quantitative analysis:
````python
# Example: Analyze 50 runs
results = [load_summary(f"run-{i:03d}") for i in range(50)]
war_rate = sum(r["war_declared"] for r in results) / len(results)
````

### Observer Agent

For qualitative analysis, a separate LLM process reads logs and answers predefined research questions. Used as a complement to outcome flags, not a replacement.

---

## 7. Technical Specifications

### 7.1 Stack

- **Python:** 3.11+
- **Dependencies:** pydantic, pyyaml, httpx
- **Execution model:** Synchronous for MVP (async can be added later for parallel actors)
- **Type hints:** Required throughout

### 7.2 LLM Provider Abstraction

The system supports multiple LLM backends through a provider abstraction:
````python
# llm_provider.py

class LLMProvider(Protocol):
    def complete(self, messages: list[dict], model: str) -> str:
        """Send messages, return assistant response."""
        ...

class OpenRouterProvider:
    """Primary provider. Supports Claude, GPT, Llama, etc."""
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        ...

class LocalProvider:
    """For local models via Ollama, llama.cpp server, or similar."""
    def __init__(self, base_url: str = "http://localhost:11434"):
        ...
````

**Configuration in scenario.yaml:**
````yaml
llm:
  provider: "openrouter"  # or "local"
  model: "anthropic/claude-sonnet-4"  # OpenRouter model string
  api_key_env: "OPENROUTER_API_KEY"   # Environment variable name
  
  # For local models:
  # provider: "local"
  # model: "llama3"
  # base_url: "http://localhost:11434/v1"
````

---

## 8. Example Scenario Files

### scenario.yaml
````yaml
name: "US-China AI Race"
time_scale: "6 months per turn"
max_turns: 10
action_points_per_turn: 3

world_altering_triggers:
  - condition: "war_declared == true"
  - condition: "ai_catastrophe_risk > 0.5"

llm:
  provider: "openrouter"
  model: "anthropic/claude-sonnet-4"
  api_key_env: "OPENROUTER_API_KEY"
````

### metrics.yaml
````yaml
world:
  global_temperature: 1.2
  ai_catastrophe_risk: 0.05
  year: 2025

actors:
  USA:
    private:
      military_capacity: 85
      ai_capability: 70
    public:
      budget: 500
      gdp: 25000
  China:
    private:
      military_capacity: 90
      ai_capability: 65
    public:
      budget: 400
      gdp: 18000
````

### events.yaml
````yaml
scheduled:
  - turn: 3
    name: "US Election"
    description: "Presidential election changes administration priorities."
    effects:
      - target: "USA.public.budget"
        delta: -50

conditional:
  - condition: "ai_catastrophe_risk > 0.3"
    name: "Public AI Panic"
    description: "Global concern about AI safety leads to regulatory pressure."
    effects:
      - target: "world.ai_catastrophe_risk"
        delta: -0.05
````

### background/actors/USA.md
````markdown
# United States of America

## Identity
The United States is a global superpower with significant technological 
and military capabilities. It seeks to maintain its leadership position 
in AI development while managing great power competition.

## Initial Goals
1. Maintain technological superiority over China in AI
2. Prevent AI-related catastrophic risks
3. Strengthen alliances with democratic partners

## Behavioral Traits
- Values transparency with allies
- Responds firmly to perceived threats
- Balances domestic political pressures with international strategy
````

---

## 9. Implementation Roadmap (MVP)

1. **Core Engine:** Loop that reads YAML, generates actor-specific views, runs turns.
2. **Metrics Filter:** Implement `get_visible_metrics()`.
3. **Action Validation:** `methods.py` validates and constrains actions.
4. **Mock LLM:** Dummy agent to test the flow.
5. **LLM Integration:** OpenRouter provider with retry logic and error handling.
6. **Prompt Engineering:** System prompts for all phases.
7. **Director:** Narrative synthesis based on inputs and interpretations.
8. **Outcome Flags:** Structured data for analysis.
9. **CLI:** Real-time display of simulation.

---

## 10. Development Guidelines

- **Version prompts separately.** Store in `prompts/` directory for iteration without code changes.
- **Log everything.** Save raw LLM input/output for debugging.
- **Start small.** 2 actors, 3 turns. Scale up when it works.
- **Use cheap models for iteration.** Switch to stronger models for production runs.
