# Scenario Lab Architecture

This document serves as the "ground truth" for the Scenario Lab architecture. It describes how the system is intended to work and should be updated before adding new functionality.

## 1. Design Philosophy: Pure LLM Architecture

V4 represents a radical simplification from previous versions. Instead of complex Python game logic, **we lean into the LLM**.

- **LLMs handle ALL complexity:** Narrative generation, metric updates, rule interpretation, and event evaluation are all performed by the LLM.
- **Python is minimal orchestration:** The Python code is strictly for loading data, constructing prompts, calling APIs, and persisting results to files. It does *not* contain game rules or simulation logic.
- **No communication phases:** There are no complex multi-step communication protocols between actors.
- **No hybrid architecture:** We do not mix Python-based rules with LLM-based reasoning. The simulation is purely LLM-driven.
- **One simple turn loop:** The simulation proceeds in a linear sequence of steps for each turn.

## 2. Core Concepts

### Metrics
- **Definition:** Pure quantitative values representing the state of the world (e.g., `ai_capability`, `unemployment`, `public_sentiment`).
- **Structure:** Each metric has a unique ID, a value, min/max bounds, a unit, and optional reference points for interpretation.
- **Handling:** Metrics are passed to the LLM as JSON and updated by the LLM as JSON. The Python code only validates that values are within bounds (clamping if necessary).

### Metric Rules
- **Definition:** Quantitative rules describing how metrics change over time or in relation to each other.
- **Examples:** "ai_capability doubles every 6 months", "high unemployment decreases public_sentiment".
- **Evolution:** The LLM reviews and updates these rules *every turn* based on world events. This allows the "physics" of the simulation to evolve.

### World State
- **Definition:** A narrative description of what happened during the turn, plus a persistent summary of history.
- **Components:**
  * `narrative`: Detailed description of the *current* turn.
  * `historical_summary`: Concise summary of all *previous* turns.
- **Purpose:** It serves as the shared context for all actors in the next turn. There is no information asymmetry; all actors see the same world state.

### Actors
- **Definition:** Simulation participants (governments, organizations, companies) with defined goals and behaviors.
- **Actions:** Actors decide on goals and actions each turn. These are descriptive text, not structured data.

### Events
- **Definition:** Exogenous happenings with probabilities and conditions.
- **Evaluation:** The LLM evaluates whether conditions are met and calculates probabilities. The Python orchestrator then "rolls the dice" to see if the event actually triggers.

## 3. System Architecture

### File Structure & Loading (`loader.py`)
- **`scenario.yaml`**: Configuration (time scale, actors, LLM settings, output language).
  * **LLM Settings:** Now includes `summary` model configuration alongside `events`, `actors`, `rules`, and `metrics`.
- **Markdown Resources**: `metrics.md`, `events.md`, `metric-rules.md`, `background/*.md`.
- **Inheritance:** Scenarios can inherit from others via the `base` field in `scenario.yaml`.

### The Turn Loop (`orchestrator.py`)
Each turn executes the following steps in order:

1. **Events Step**:
  * **Input:** World state (history + current), current metrics, list of potential events.
  * **LLM Task:** Determine which events meet their conditions and calculate their probabilities.
  * **Python Action:** Parse JSON response, roll dice for probabilities, determine triggered events.

2. **Actors Step**:
  * **Input:** World state (history + current), metrics, triggered events.
  * **LLM Task:** For *each* actor, review goals and describe actions for the turn.
  * **Parallelization:** Actor prompts are independent and can be executed in parallel (though currently sequential in implementation).

3. **Rules Step**:
  * **Input:** World state, triggered events, all actor actions, current rules.
  * **LLM Task:** Review and update the list of Metric Rules.

4. **Metrics Step**:
  * **Input:** World state, triggered events, actor actions, updated rules.
  * **LLM Task:**
    * Determine success of actor actions.
    * Calculate new metric values.
    * Write a narrative summary of the turn.
    * Update the "Notepad" (persistent and secret game master notes).
  * **Output Parsing:** Requires verbatim headers (`## Metrics`, `## Narrative`, `## Notepad`) for reliable parsing.

4. **Summarization Step**:
  * **Input:** Current `historical_summary` and the new `narrative` from Step 4.
  * **LLM Task:** Condense the new narrative and append it to the historical summary, keeping the total length manageable.
  * **Purpose:** Prevent context window explosion over long simulations.

### Prompt Engineering (`prompts.py` & Templates)
- **Jinja2 Templates:** All prompts are generated using Jinja2 templates located in `scenarios/{name}/system-prompts/` and `scenarios/{name}/user-prompts/`, defaulting to `templates/systemp-prompts/` and `templates/user-prompts/` if none are found.
- **Context:** Templates receive a rich context object including `turn`, `time_period`, `metrics_json`, `world_state`, `events_list`, and individual metric variables (`metric_X`).
- **Output Language:** The `output_language` setting injects instructions into templates to control the language of the LLM's response (e.g., "Please write your response in Swedish").

### LLM Integration (`llm.py`)
- **Client:** Uses `httpx` to call OpenRouter API.
- **Fallback:** Supports a list of models for fallback (e.g., try Claude 3.5 Sonnet, then Haiku).
- **Parsing:** Includes strict regex-based parsing for JSON and specific Markdown headers.

### Persistence (`output.py`)
- **Incremental Writing:** Results are saved to disk *immediately* after each step of the turn loop.
- **Structure:** Each run gets a timestamped directory. Each turn gets a subdirectory.
- **Crash Resilience:** If the simulation crashes, all progress up to the last successful step is preserved.
- **Resumption:** The directory structure and `summary.json` support resuming crashed runs or extending completed runs.

### Resume & Branching (`resume.py`)

**Module:** `scenario_lab/resume.py` provides core functionality for loading and manipulating run state.

**Key Functions:**
- `detect_last_turn(run_dir)`: Finds the highest completed turn by validating turn directory structure.
- `validate_run_directory(run_dir)`: Checks for required files (`config.json`, `summary.json`, turn directories).
- `get_scenario_path_from_run(run_dir)`: Navigates from run directory to scenario directory.
- `load_run_state(run_dir, from_turn, state_modifications)`: Loads complete scenario state from disk, with optional modifications.
- `create_branch(parent_run_dir, from_turn, output_base, state_modifications, config_overrides)`: Creates a new branched run.

**Resume Implementation:**
- **CLI Command:** `python -m scenario_lab.cli resume <run_dir> [options]`
- **Options:**
  * `--from-turn N`: Resume from specific turn (default: auto-detect last completed)
  * `--turns N`: Total turns to run (overrides config)
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
- **Behavior:**
  * Loads state from the specified turn (metrics, narrative, rules, notepad, historical summary, occurred events)
  * Continues execution in the *same* run directory (no duplication)
  * Updates `summary.json` with `resumed_at` and `resumed_from_turn` metadata
  * Useful for: crashed runs, extending completed scenarios, switching to better/cheaper models
- **State Loading:**
  * Reads `turn-XX/4-metrics.json` to restore metric values
  * Reads `turn-XX/4-world-state.md` to restore narrative
  * Reads `turn-XX/3-metric-rules.md` to restore rules
  * Reads `turn-XX/5-notepad.md` to restore game master notes
  * Reads `turn-XX/6-historical-summary.md` to restore turn history
  * Reads `summary.json` to restore occurred events list

**Branch Implementation:**
- **CLI Command:** `python -m scenario_lab.cli branch <run_dir> --from-turn N [options]`
- **Options:**
  * `--from-turn N`: **Required** - Turn number to branch from
  * `--modify-metric id=value`: Modify metric value(s) for "what-if" scenarios (repeatable)
  * `--modify-narrative "text"`: Replace narrative text
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
  * `--turns N`: Total turns to run from branch point
- **Behavior:**
  * Creates a *new* timestamped run directory
  * Copies turn directories 1 through N from parent run
  * Loads state from turn N and applies modifications
  * Continues execution from turn N+1 in new directory
  * Useful for: "what-if" experiments, sensitivity analysis, model comparison
- **Metadata Tracking:**
  * `config.json` includes: `parent_run`, `branch_turn`, `branch_created_at`, `state_modifications`, `config_overrides`
  * `summary.json` includes: `metadata` object with parent run reference, branch point, and all modifications
  * Preserves full lineage for analysis and reproducibility
- **State Modifications:**
  * Metrics: Modified values are clamped to min/max bounds with warnings
  * Narrative: Completely replaces the world state narrative
  * Notepad: Replaces game master notes
  * Rules: Replaces metric rules markdown

**Orchestrator Integration:**
- `run_simulation()` now accepts `start_turn` parameter (default: 1)
- Turn loop iterates from `start_turn` to `max_turns` instead of 1 to `max_turns`
- No other orchestrator changes needed - pre-loaded scenario state works seamlessly

**File Structure for Resume/Branch:**
```
run-YYYYMMDD-HHMMSS/
├── config.json              # Contains metadata for branched runs
├── summary.json             # Contains resume/branch metadata
└── turn-XX/                 # Validated for completeness before loading
    ├── 1-events.json
    ├── 2-actors/*.md
    ├── 3-metric-rules.md
    ├── 4-metrics.json       # Source of truth for metric values
    ├── 4-world-state.md     # Source of truth for narrative
    ├── 5-notepad.md         # Source of truth for GM notes
    └── 6-historical-summary.md  # Source of truth for history
```

**Future Extensions:**
- Batch resume: Resume all incomplete runs in a batch directory
- Batch branch: Create multiple branches from a batch of runs
- Parallel execution: Run multiple resume/branch operations concurrently

### CLI (`cli.py`)
- **Entry Point:** `python -m scenario_lab.cli`.
- **Overrides:** Supports `--override key=value` to modify configuration at runtime (e.g., `--override output_language=Spanish`).

## 4. Evaluation & Testing
- **Unit Tests:** Standard pytest suite for Python logic.
- **LLM Evals:** Specialized suite in `tests/evals/llm-event-conditions/` to benchmark LLM performance on logic, math, and hallucination prevention.

## 5. Extension Guidelines
- **Update This Document first:** This document must be the ground truth and reflect how the project should work. Before adding or changing substantial functionality, it should be described here.
- **New Features:** Must not break the "Pure LLM" philosophy. Avoid adding game logic to Python.
- **Prompts:** Modify templates, not Python code, whenever possible.
- **No backwards Compatibility:** As the project is still in an early phase, there is no need for backwards compatibility. Old scenarios (e.g., `sweden-ai-2030`) and other files are either updated or deleted when changing data models.
- **Language:** Both code and scenarios should be written in English. Code comments, documentation, scenario files (YAML, Markdown), and all technical content should use English for consistency and broader accessibility.
