# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Scenario Lab** is an experimental framework for AI-automated scenario exercises focused on exploring complex policy and strategic questions, particularly around AI governance and policy. The system enables multi-actor simulations where AI agents interact in dynamic environments, providing both statistical insights from batch runs and deep qualitative analysis.

**Current Status:** Phase 4 COMPLETE, Phase 5 PARTIAL. The framework includes:

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

## Core Architecture Concepts

The system is designed around these key components (see README.md for full details):

**Core Simulation:**
1. **Scenario Definition Parser** - Loads and validates scenario specifications from YAML
2. **World State Manager** - Maintains and updates global state across simulation steps
3. **Actor Engine** - Manages AI-controlled and human-controlled actors, supports multiple LLM models per scenario
4. **Action Resolver** - Processes actor decisions and updates world state
5. **Metrics Tracker** - Records and analyzes key performance indicators, exports structured data (JSON)
6. **Documentation Generator** - Creates markdown records of each simulation step
7. **Quality Assurance Validator** - Uses lightweight models to check consistency of actions and world states

**Batch Processing:**
8. **Parameter Variator** - Generates scenario variations with Cartesian products
9. **Batch Runner** - Orchestrates execution of multiple scenario variations
10. **Batch Cost Manager** - Enforces budget limits and tracks spending
11. **Batch Progress Tracker** - Real-time progress display with rich formatting
12. **Batch Parallel Executor** - Async execution with rate limiting
13. **Batch Analyzer** - Statistical analysis and pattern identification

**User Experience & Safety:**
14. **Config Wizard** - Interactive batch configuration creation
15. **Error Handler** - User-friendly error messages with recovery suggestions (10 categories)
16. **Progressive Fallback** - Automatic model fallback strategies

**Performance & Optimization:**
17. **Response Cache** - SHA256-based caching of LLM responses
18. **Memory Optimizer** - Garbage collection and memory monitoring
19. **Graceful Fallback** - Works without optional dependencies (rich, psutil)

## Expected Directory Structure

When implementation begins, the structure should follow this pattern:

```
scenario-name/
├── definition/
│   ├── scenario.yaml          # Initial world state and rules
│   ├── actors/
│   │   ├── actor1.yaml        # Actor profiles (including LLM model specification)
│   │   └── actor2.yaml
│   ├── metrics.yaml           # Defined metrics and thresholds
│   ├── validation-rules.yaml  # Instructions for quality assurance checks
│   ├── black-swans.yaml       # Optional: black swan event definitions
│   └── background/            # Optional: background data and information
│       ├── historical-data.md
│       └── reference-docs.md
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

## Key Design Principles

1. **AI-Controlled Actors**: All actors can be AI agents with goals, information, and decision-making capabilities. Different actors may use different LLM models. Actor behavior (including bounded rationality, biases, expertise) is specified in open actor descriptions.
2. **Dynamic World State**: World evolves based on actor decisions, including potential black swan events
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

The README.md outlines a 5-phase development roadmap:

- **Phase 1**: ✅ COMPLETE - Core Framework (scenario format, world state, basic actor engine)
- **Phase 2**: ✅ COMPLETE - AI Integration (LLM integration, prompt templates)
- **Phase 3**: 🔄 IN PROGRESS - Human Interaction (human actor control, visualization)
- **Phase 4**: ✅ COMPLETE - Batch Processing (parallel execution, statistical analysis, cost management, error handling, performance optimization)
- **Phase 5**: 🔄 PARTIAL - Advanced Features (✅ branching, ✅ resumable scenarios, ✅ scenario creation wizard, ⏳ dashboard)

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

## Implementation Guidance

When beginning implementation:

1. Start with defining the YAML schema for scenario definitions (including validation-rules.yaml for QA checks)
2. Build the world state manager as the foundational component
3. Create simple markdown generation AND structured JSON metrics export early
4. Design actor prompting strategy carefully - this is critical for simulation quality
5. Plan for multi-model support from the start (consider OpenRouter or similar for unified API access)
6. Implement cost estimation and tracking BEFORE running large batches
7. Build quality assurance validation early - use lightweight models to check consistency
8. Plan for context management as scenarios may be long-running
9. Design communication types and visibility rules into the core architecture
10. Use "AI 2027" calibration scenario for validation testing - compare against real 2024-2025 events

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
- `--max-turns N` - Stop after N turns
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
