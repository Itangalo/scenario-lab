# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Scenario Lab** is an experimental framework for AI-automated scenario exercises focused on exploring complex policy and strategic questions, particularly around AI governance and policy. The system enables multi-actor simulations where AI agents interact in dynamic environments, providing both statistical insights from batch runs and deep qualitative analysis.

**Current Status:** **Version 2.0 - V2 Migration COMPLETE**. The framework now uses a modern Python package architecture with clean separation of concerns. The framework includes:

**Core Simulation (Phase 1-2):**
- ✅ Multi-actor AI-controlled scenarios with simultaneous turn execution
- ✅ LLM-powered world state synthesis (not simple concatenation)
- ✅ Cost estimation and tracking for all LLM API calls
- ✅ Structured metrics extraction and export (JSON)
- ✅ Resumable scenarios - graceful handling of rate limits and budget constraints
- ✅ Scenario branching - create alternative paths from any completed turn
- ✅ Quality assurance validator - automated consistency checking with validation reports
- ✅ Auto-incrementing run numbers to preserve history

**Batch Processing (Phase 4):**
- ✅ Parameter variation system with Cartesian products
- ✅ Sequential and parallel execution with rate limiting
- ✅ Cost tracking and budget controls (per-run and total)
- ✅ Real-time progress tracking
- ✅ Statistical analysis and reporting
- ✅ Resumable batch execution

**User Experience & Safety:**
- ✅ Interactive batch config wizard with validation
- ✅ Scenario creation wizard - complete scenario generation in 5-10 minutes
- ✅ Dry-run preview mode with cost/time estimation
- ✅ Comprehensive error handling (10 categories) with user-friendly messages
- ✅ Progressive fallback strategies for model failures
- ✅ Automatic recovery suggestions

**Performance & Optimization:**
- ✅ Response caching system (30-70% cost savings)
- ✅ HTTP connection pooling (15-40% speed improvement)
- ✅ Memory optimization with automatic garbage collection
- ✅ Memory monitoring and OOM prevention
- ✅ Graceful degradation (works without optional dependencies)

## AI-Assisted Scenario Creation

For AI assistants helping users create scenarios, see **[AGENTS.md](AGENTS.md)**. This file contains:

- Complete YAML schema documentation for all configuration files
- Step-by-step workflow for scenario generation
- Actor design guidelines and archetypes
- Metrics configuration examples
- Validation and troubleshooting guidance

When a user requests help creating a scenario (e.g., "simulate US-China dynamics during an AI crisis"), use AGENTS.md as the primary reference for generating valid, well-designed scenario configurations.

## V2 Architecture (Current)

The system uses a modern Python package architecture with clean separation of concerns:

**Package Structure: `scenario_lab/`**

**Core Components (`scenario_lab/core/`):**
- `actor.py` - Immutable Actor dataclass for V2
- `events.py` - Event bus for real-time updates
- `orchestrator.py` - Phase orchestration and execution flow
- `prompt_builder.py` - LLM prompt construction
- `world_synthesizer.py` - World state synthesis from decisions
- `context_manager.py` - Context windowing and summarization (V2 with validation)
- `communication_manager.py` - Actor communication handling
- `metrics_tracker_v2.py` - **Pure V2 metrics extraction** (Pydantic schemas, async)
- `qa_validator_v2.py` - **Pure V2 quality assurance** (Pydantic schemas)

**Phase Services (`scenario_lab/services/`):**
- `decision_phase_v2.py` - Actor decision-making (pure V2)
- `world_update_phase_v2.py` - World state synthesis (pure V2)
- `communication_phase.py` - Actor communications
- `persistence_phase.py` - File output generation
- `database_persistence_phase.py` - Optional database persistence

**Loaders (`scenario_lab/loaders/`):**
- `scenario_loader.py` - Loads scenarios from YAML
- `actor_loader.py` - Creates V2 Actor instances
- `metrics_loader.py` - **V2 Pydantic-based metrics config loader**
- `validation_loader.py` - **V2 Pydantic-based validation config loader**

**Batch Processing (`scenario_lab/batch/`):**
- `parameter_variator.py` - Generate scenario variations
- `batch_runner.py` - Execute batches with parallelism
- `batch_cost_manager.py` - Budget tracking and limits
- `batch_progress_tracker.py` - Real-time progress display
- `batch_parallel_executor.py` - Async execution with rate limiting
- `batch_analyzer.py` - Statistical analysis

**Utilities (`scenario_lab/utils/`):**
- `api_client.py` - Async LLM API calls
- `response_parser.py` - Parse LLM responses (markdown/JSON)
- `model_pricing.py` - LLM cost calculation
- `response_cache.py` - SHA256-based response caching
- `error_handler.py` - User-friendly error messages
- `progressive_fallback.py` - Model fallback strategies
- `memory_optimizer.py` - Memory management

**Interfaces:**
- `scenario_lab/interfaces/cli.py` - CLI commands (`scenario-lab` command)
- `scenario_lab/api/app.py` - REST API with FastAPI
- `web/frontend/` - React TypeScript frontend

**Runners:**
- `scenario_lab/runners/sync_runner.py` - **Pure V2 synchronous runner**

## V2 Migration Status

**Status: COMPLETE** (Phase 6.1-6.2 complete, 2025-11-20)

**V2 Rewrite Completion** (2025-11-20):
- ✅ MetricsTrackerV2: Pure V2 with Pydantic schemas, async extraction (pattern, keyword, LLM)
- ✅ ContextManagerV2: Enhanced with parameter validation (prevents BUG-010)
- ✅ QAValidatorV2: Pydantic-based configuration with wrapper pattern
- ✅ Integration smoke tests: 26 tests verifying V2 components work correctly
- ✅ All V2 components use Pydantic schemas (no raw YAML dicts)
- ✅ Pure async patterns for all LLM calls
- ✅ Immutable state management throughout

The V2 migration is functionally complete:
- ✅ All V2 code uses pure V2 architecture (zero V1 dependencies)
- ✅ `sync_runner.py` is pure V2 (uses DecisionPhaseV2, WorldUpdatePhaseV2)
- ✅ CLI commands available: `scenario-lab create`, `scenario-lab run`, `scenario-lab create-batch`, `scenario-lab serve`
- ✅ REST API with WebSocket streaming
- ✅ React frontend integrated with V2 API

**Legacy V1 Code:**
- V1 code remains in `src/` directory for reference
- V1 is no longer actively used by V2 components
- CLI wizard commands still bridge to V1 wizards (temporary, will be migrated)

**Documentation:**
- Migration plan: `docs/v2_migration_plan.md`
- Phase 6 summary: `docs/PHASE_6_SUMMARY.md`
- V1 removal plan: `docs/PHASE_6_1_V1_REMOVAL_PLAN.md`
- Test status: `docs/PHASE_6_2_TEST_STATUS.md`
- Web integration: `docs/PHASE_5_WEB_INTEGRATION.md`

## Scenario Directory Structure

When working with scenarios, the structure follows this pattern:

```
scenario-name/
├── scenario.yaml              # Main scenario configuration (name, world state, rules)
├── actors/
│   ├── actor1.yaml            # Actor profiles (including LLM model specification)
│   └── actor2.yaml
├── metrics.yaml               # Optional: defined metrics and thresholds
├── validation-rules.yaml      # Optional: instructions for quality assurance checks
├── exogenous-events.yaml      # Optional: background event definitions
├── background/                # Optional: background data and information
│   ├── historical-data.md
│   └── reference-docs.md
├── runs/
│   ├── run-001/
│   │   ├── world-state-001.md
│   │   ├── world-state-002.md
│   │   ├── actor-name-001.md
│   │   ├── metrics.json       # Structured metrics data for analysis
│   │   └── ...
│   └── run-002/
│       └── ...
└── analysis/
    ├── statistics.md
    ├── critical-factors.md
    └── metrics-summary.json   # Aggregated structured data across runs
```

**Note:** Configuration files (`scenario.yaml`, `actors/`, etc.) are placed directly in the scenario root directory, not in a `definition/` subdirectory.

## Key Design Principles

1. **AI-Controlled Actors**: All actors can be AI agents with goals, information, and decision-making capabilities. Different actors may use different LLM models. Actor behavior (including bounded rationality, biases, expertise) is specified in open actor descriptions.
2. **Dynamic World State**: World evolves based on actor decisions, including exogenous background events (trends, random, conditional, scheduled)
3. **Human-in-the-Loop**: Any AI actor can be replaced by a human expert at any time
4. **Information Asymmetry**: Actors maintain both public and private information. Actors evaluate information quality themselves.
5. **Step-by-Step Documentation**: Each simulation step documented in markdown files, with structured metrics data (JSON) for analysis
6. **Batch Simulation**: Support for running hundreds/thousands of scenarios with systematic variations. Actors have no memory between runs - each run is independent.
7. **Temporal Model**: Simultaneous turn-based execution. Turn duration defined by scenario and may vary during execution.
8. **Communication**: Multiple communication types (public statements, bilateral negotiations, coalition formation) with different visibility rules
9. **Validation**: Use calibration scenarios (e.g., "AI 2027"), expert evaluation of documentation, and automated consistency checking
10. **Cost Management**: Comprehensive cost estimation, tracking, and controls for LLM API usage

## Primary Research Focus

The framework is specifically designed to explore AI policy and governance questions:

- Regulatory effectiveness under various conditions
- Governance structures for AI deployment
- International coordination mechanisms
- Corporate strategy in AI disruption
- AI safety interventions and their impact
- Risk assessment and critical decision factors

## Development Phases

**V2 Migration - All Phases Complete:**

- **Phase 1-4**: ✅ COMPLETE - Core simulation, batch processing, cost management, performance optimization
- **Phase 5**: ✅ COMPLETE - CLI tools, scenario wizards, web interface integration
- **Phase 6**: ✅ COMPLETE (6.1-6.2) - V1 dependency removal, test suite cleanup, documentation update

**Features Implemented:**
- ✅ Pure V2 architecture with zero V1 dependencies
- ✅ CLI commands: `scenario-lab create`, `scenario-lab run`, `scenario-lab create-batch`, `scenario-lab serve`
- ✅ Resumable scenarios with state persistence
- ✅ Scenario branching from any turn
- ✅ Batch execution with parameter variations
- ✅ Cost tracking and budget controls
- ✅ Response caching (30-70% cost savings)
- ✅ Quality assurance validation
- ✅ REST API with WebSocket streaming
- ✅ React TypeScript frontend

## Calibration and Validation

The framework includes comprehensive calibration capabilities using the **AI 2027** scenario as a validation tool.

**Purpose:**
- Validate framework realism by comparing simulations against real AI developments (2024-2025)
- Identify systematic biases and blind spots
- Tune actor and scenario prompts based on evidence
- Establish confidence bounds for research use

**Calibration Methodology:**
- Compare simulated events against real-world timeline
- Score decision realism, timeline plausibility, causality coherence, actor interactions
- Target ≥7.5/10 average for research suitability
- Document findings and refine prompts iteratively

**Key Documents:**
- `scenarios/ai-2027/CALIBRATION.md` - Detailed methodology
- `scenarios/ai-2027/calibration-results-template.md` - Results documentation template
- `docs/calibration-guide.md` - Complete calibration guide

**Calibration Metrics:**
- Decision Realism (0-10): Do actors behave like real counterparts?
- Timeline Plausibility (0-10): Is progression pace realistic?
- Causality Coherence (0-10): Do events cause realistic downstream effects?
- Actor Interaction Realism (0-10): Are dynamics between actors realistic?

**Historical Baseline:**
- Real AI events from 2024-2025 (model releases, regulations, research advances)
- Comparison scoring system for event prediction accuracy
- Systematic prompt refinement based on findings

## Working with V2 Architecture

**Key Principles:**

1. **Pure V2 Code**: All code in `scenario_lab/` uses V2 architecture. Do not add V1 dependencies (`sys.path.insert` to `src/`).

2. **Immutable State**: V2 uses immutable state management via dataclasses (frozen=True). Always create new state objects rather than mutating existing ones.

3. **Phase-Based Execution**: The orchestrator runs phases in sequence:
   - Communication Phase → Decision Phase → World Update Phase → Persistence Phase
   - Each phase receives immutable state and returns new state

4. **Async by Default**: V2 phases use async/await for LLM API calls to support concurrent operations.

5. **Event-Driven**: Use the EventBus (`scenario_lab.core.events`) for real-time updates and monitoring.

6. **CLI Commands**: Use Click-based CLI in `scenario_lab/interfaces/cli.py` for user-facing commands.

**When Adding New Features:**

1. Place code in appropriate `scenario_lab/` subdirectory (core/, services/, utils/, etc.)
2. Use V2 patterns: immutable dataclasses, async methods, pure functions
3. Import from `scenario_lab.*` packages, never from `src/`
4. Write tests using V2 fixtures and mocks
5. Update CLI if adding user-facing functionality
6. Document in README.md and relevant docs/ files

**Cost Management:**
- Cost tracking is built into the state model (`CostRecord` in `scenario_lab/models/state.py`)
- Use `scenario_lab.utils.model_pricing` for LLM cost calculation
- Always estimate costs before execution (use `--dry-run` for batch operations)

**Testing:**
- V2-native tests go in `tests/` with standard Python imports
- Use `scenario_lab.*` imports (not `src/`)
- Mock LLM calls using `unittest.mock` or pytest fixtures

## Example Use Cases

See README.md section "Example Scenarios" for concrete examples, including:

- AI 2027 (calibration scenario for validation)
- AI Regulatory Negotiation
- AI Safety Incident Response
- Corporate AI Governance
- AI Arms Race Dynamics
- Automated Decision System Deployment

These examples should guide the design of flexible, reusable scenario components.

## Implemented Features

### Resumable Scenarios

The framework supports stopping and resuming scenario runs, crucial for handling API rate limits and budget constraints:

**Key Components:**
- `src/scenario_state_manager.py` - Saves/loads complete scenario state
- `scenario-state.json` - Auto-generated state file in each run directory
- State includes: world state, actor states, costs, metrics, execution metadata

**Command-line arguments:**
- `--end-turn N` - Execute N turns (e.g., --end-turn 5 runs 5 actor decision rounds)
- `--credit-limit X` - Halt if cost exceeds $X
- `--resume <path>` - Resume from halted run

**Error handling:**
- Rate limit errors (429) are caught gracefully
- State is saved before exit
- Clear resume instructions displayed
- All tracking (costs, metrics) preserved across resume

**State persistence:**
- State saved after each successful turn
- JSON keys properly converted (string → int) on load
- WorldState, CostTracker, MetricsTracker all fully serializable

See `notes/resumable-scenarios-plan.md` for full implementation details.

### Scenario Branching

The framework supports creating alternative scenario paths by branching from any completed turn:

**Command-line arguments:**
- `--branch-from <path>` - Source run directory to branch from
- `--branch-at-turn N` - Turn number to branch from (0 to current_turn)

**Implementation details:**
- `branch_scenario()` function in run_scenario.py
- Creates new run directory with auto-incremented number
- Copies all markdown files (world states, actor decisions) up to branch point
- Truncates state data (world state, costs, metrics) to branch point
- Recalculates totals for cost tracking and metrics
- Adds branch metadata to execution_metadata (branched_from, branch_point)

**Use cases:**
- Explore "what-if" scenarios from critical decision points
- Test different actor strategies from same starting conditions
- Compare outcomes with different prompts or models
- Sensitivity analysis by varying parameters from branch point

**Workflow:**
1. Branch creates new run with copied history
2. Resume the branch to continue from next turn
3. Modify scenario/actors if exploring alternatives
4. Compare outputs between original and branch runs

### Quality Assurance Validator

The framework includes automated consistency checking using lightweight LLM models to validate expensive model outputs:

**Key Components:**
- `src/qa_validator.py` - QAValidator class with validation logic
- `validation-rules.yaml` - Configuration file in each scenario directory
- Validation reports generated per turn and as summary

**Validation Checks:**
1. **Actor Decision Consistency** - Validates that actor decisions align with:
   - Stated goals and objectives
   - Declared constraints
   - Expertise levels
   - Decision-making style

2. **World State Coherence** - Validates that world state updates:
   - Logically follow from actor actions
   - Show appropriate consequences
   - Maintain internal consistency
   - Are realistic and proportionate

3. **Information Access Consistency** - Validates that actors:
   - Only reference information they have access to
   - Don't use knowledge from private communications they weren't part of
   - Respect information asymmetry rules

**Configuration:**
```yaml
validation_model: "openai/gpt-4o-mini"  # Lightweight model for cost efficiency
checks:
  actor_decision_consistency:
    enabled: true
  world_state_coherence:
    enabled: true
  information_access_consistency:
    enabled: true
run_after_each_turn: true
generate_turn_reports: true
```

**Outputs:**
- `validation-001.md`, `validation-002.md`, etc. - Per-turn validation reports
- `validation-summary.md` - Overall summary with statistics
- Validation costs tracked in `costs.json` under `validation` key

**Usage:**
- Validation runs automatically if `validation-rules.yaml` exists
- Can be disabled by removing the file or setting `enabled: false`
- Warnings displayed during execution if issues found
- Severity levels: Low (logged), Medium (warned), High (warned/halt)

**Testing:**
- 13 comprehensive unit tests in `tests/test_qa_validator.py`
- Tests cover initialization, parsing, report generation, cost tracking
- All tests pass as part of the 95-test suite

### Scenario Creation Wizard

The framework includes an interactive CLI wizard for creating complete scenario configurations from scratch:

**Key Components:**
- `src/create_scenario.py` - Interactive wizard with 9-step workflow
- `docs/scenario-creation-guide.md` - Comprehensive guide (500+ lines)
- `tests/test_scenario_wizard.py` - 6 unit tests for wizard functions

**Features:**

1. **9-Step Guided Workflow**:
   - Basic scenario information (name, description)
   - System prompt configuration (with template)
   - Initial world state definition
   - Scenario parameters (turns, duration)
   - World state model selection
   - Actor creation (unlimited, minimum 2)
   - Metrics configuration (optional)
   - Validation rules setup (optional)
   - Preview and save

2. **Actor Creation**:
   - Name and short name
   - LLM model selection with pricing info
   - System prompt (template provided)
   - Goals, constraints, expertise, decision style
   - All fields validated

3. **Smart Defaults**:
   - 9 common LLM models with descriptions and pricing
   - Template system prompts for scenarios and actors
   - Suggested metrics patterns
   - Validation rule presets

4. **Output Files**:
   - `scenario.yaml` - Main scenario configuration
   - `actors/*.yaml` - Actor definitions
   - `metrics.yaml` - Metric definitions (optional)
   - `validation-rules.yaml` - QA configuration (optional)

**Benefits:**
- Reduces scenario creation from 30+ minutes to 5-10 minutes
- Ensures consistent, valid YAML structure
- Built-in Pydantic validation
- Preview before save
- Template support for common patterns

**Usage:**
```bash
python src/create_scenario.py
```

**Testing:**
- 6 comprehensive tests covering all major functions
- Tests for scenario structure, actor creation, metrics, full workflow
- All tests pass as part of 177-test suite

## Working with the Repository

### Notes Directory

The `notes/` directory is for personal and temporary notes during development. All contents (except `.gitkeep`) are ignored by git. Use this for:

- Development scratch notes
- Personal TODO lists
- Temporary analysis or calculations
- Draft ideas and planning
- Any local notes that shouldn't be committed

## Important Notes

- Markdown files should be preceded by blank lines before lists (per user's global CLAUDE.md)
- Focus is on AI policy research through simulation, not general-purpose gaming or simulation
- Statistical rigor is important - design for hypothesis testing and pattern discovery
- Documentation is a first-class concern - every simulation step should be reviewable by experts
- Cost management is critical - batch runs can easily cost thousands of dollars without proper controls
- Quality assurance must be built in - use lightweight models to validate consistency
- Multi-model support is essential - different actors may need different LLM capabilities
- Validation through calibration scenarios and expert review ensures simulation realism
- Actor behavior should remain flexible and described openly, not locked to specific parameters
