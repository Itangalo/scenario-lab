# Scenario Lab Architecture

This document serves as the "ground truth" for the Scenario Lab architecture. It describes how the system is intended to work and should be updated before adding new functionality.

## 1. Design Philosophy: Pure LLM Architecture

V4 represents a radical simplification from previous versions. Instead of complex Python game logic, **we lean into the LLM**.

-   **LLMs handle ALL complexity:** Narrative generation, metric updates, rule interpretation, and event evaluation are all performed by the LLM.
-   **Python is minimal orchestration:** The Python code is strictly for loading data, constructing prompts, calling APIs, and persisting results to files. It does *not* contain game rules or simulation logic.
-   **No communication phases:** There are no complex multi-step communication protocols between actors.
-   **No hybrid architecture:** We do not mix Python-based rules with LLM-based reasoning. The simulation is purely LLM-driven.
-   **One simple turn loop:** The simulation proceeds in a linear sequence of steps for each turn.

## 2. Core Concepts

### Metrics
-   **Definition:** Pure quantitative values representing the state of the world (e.g., `ai_capability`, `unemployment`, `public_sentiment`).
-   **Structure:** Each metric has a unique ID, a value, min/max bounds, a unit, and optional reference points for interpretation.
-   **Handling:** Metrics are passed to the LLM as JSON and updated by the LLM as JSON. The Python code only validates that values are within bounds (clamping if necessary).

### Metric Rules
-   **Definition:** Quantitative rules describing how metrics change over time or in relation to each other.
-   **Examples:** "ai_capability doubles every 6 months", "high unemployment decreases public_sentiment".
-   **Evolution:** The LLM reviews and updates these rules *every turn* based on world events. This allows the "physics" of the simulation to evolve.

### World State
-   **Definition:** A narrative description of what happened during the turn.
-   **Purpose:** It serves as the shared context for all actors in the next turn. There is no information asymmetry; all actors see the same world state.

### Actors
-   **Definition:** Simulation participants (governments, organizations, companies) with defined goals and behaviors.
-   **Actions:** Actors decide on goals and actions each turn. These are descriptive text, not structured data.

### Events
-   **Definition:** Exogenous happenings with probabilities and conditions.
-   **Evaluation:** The LLM evaluates whether conditions are met and calculates probabilities. The Python orchestrator then "rolls the dice" to see if the event actually triggers.

## 3. System Architecture

### File Structure & Loading (`loader.py`)
-   **`scenario.yaml`**: Configuration (time scale, actors, LLM settings, output language).
-   **Markdown Resources**: `metrics.md`, `events.md`, `metric-rules.md`, `background/*.md`.
-   **Inheritance:** Scenarios can inherit from others via the `base` field in `scenario.yaml`.
-   **Bilingual Support:** The loader supports both English and Swedish keys for metrics and events to maintain backward compatibility.

### The Turn Loop (`orchestrator.py`)
Each turn executes the following steps in order:

1.  **Events Step**:
    *   **Input:** World state, current metrics, list of potential events.
    *   **LLM Task:** Determine which events meet their conditions and calculate their probabilities.
    *   **Python Action:** Parse JSON response, roll dice for probabilities, determine triggered events.

2.  **Actors Step**:
    *   **Input:** World state, metrics, triggered events.
    *   **LLM Task:** For *each* actor, review goals and describe actions for the turn.
    *   **Parallelization:** Actor prompts are independent and can be executed in parallel (though currently sequential in implementation).

3.  **Rules Step**:
    *   **Input:** World state, triggered events, all actor actions, current rules.
    *   **LLM Task:** Review and update the list of Metric Rules.

4.  **Metrics Step**:
    *   **Input:** World state, triggered events, actor actions, updated rules.
    *   **LLM Task:**
        *   Determine success of actor actions.
        *   Calculate new metric values.
        *   Write a narrative summary of the turn.
        *   Update the "Notepad" (persistent game master notes).
    *   **Output Parsing:** Requires verbatim headers (`## Metrics`, `## Narrative`, `## Notepad`) for reliable parsing.

### Prompt Engineering (`prompts.py` & Templates)
-   **Jinja2 Templates:** All prompts are generated using Jinja2 templates located in `templates/user-prompts/` or scenario-specific overrides in `scenarios/{name}/user-prompts/`.
-   **Context:** Templates receive a rich context object including `turn`, `time_period`, `metrics_json`, `world_state`, `events_list`, and individual metric variables (`metric_X`).
-   **Output Language:** The `output_language` setting injects instructions into templates to control the language of the LLM's response (e.g., "Please write your response in Swedish").

### LLM Integration (`llm.py`)
-   **Client:** Uses `httpx` to call OpenRouter API.
-   **Fallback:** Supports a list of models for fallback (e.g., try Claude 3.5 Sonnet, then Haiku).
-   **Parsing:** Includes strict regex-based parsing for JSON and specific Markdown headers.

### Persistence (`output.py`)
-   **Incremental Writing:** Results are saved to disk *immediately* after each step of the turn loop.
-   **Structure:** Each run gets a timestamped directory. Each turn gets a subdirectory.
-   **Crash Resilience:** If the simulation crashes, all progress up to the last successful step is preserved.

### CLI (`cli.py`)
-   **Entry Point:** `python -m scenario_lab.cli`.
-   **Overrides:** Supports `--override key=value` to modify configuration at runtime (e.g., `--override output_language=Spanish`).

## 4. Evaluation & Testing
-   **Unit Tests:** Standard pytest suite for Python logic.
-   **LLM Evals:** Specialized suite in `tests/evals/llm-event-conditions/` to benchmark LLM performance on logic, math, and hallucination prevention.

## 5. Extension Guidelines
-   **New Features:** Must not break the "Pure LLM" philosophy. Avoid adding game logic to Python.
-   **Prompts:** Modify templates, not Python code, whenever possible.
-   **Backwards Compatibility:** Maintain support for existing scenarios (e.g., `sweden-ai-2030`) when changing data models.
