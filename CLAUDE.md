# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Scenario Lab** is an experimental framework for AI-automated scenario exercises focused on exploring complex policy and strategic questions, particularly around AI governance and policy. The system enables multi-actor simulations where AI agents interact in dynamic environments, providing both statistical insights from batch runs and deep qualitative analysis.

**Current Status:** Phase 1 core features implemented and working. The framework includes:

- ✅ Multi-actor AI-controlled scenarios with simultaneous turn execution
- ✅ LLM-powered world state synthesis (not simple concatenation)
- ✅ Cost estimation and tracking for all LLM API calls
- ✅ Structured metrics extraction and export (JSON)
- ✅ **Resumable scenarios** - graceful handling of rate limits and budget constraints
- ✅ **Scenario branching** - create alternative paths from any completed turn
- ✅ Auto-incrementing run numbers to preserve history
- ⏳ Quality assurance validator (planned)

## Core Architecture Concepts

The system is designed around these key components (see README.md for full details):

1. **Scenario Definition Parser** - Loads and validates scenario specifications from YAML
2. **World State Manager** - Maintains and updates global state across simulation steps
3. **Actor Engine** - Manages AI-controlled and human-controlled actors, supports multiple LLM models per scenario
4. **Action Resolver** - Processes actor decisions and updates world state
5. **Metrics Tracker** - Records and analyzes key performance indicators, exports structured data (JSON)
6. **Documentation Generator** - Creates markdown records of each simulation step
7. **Batch Runner** - Executes multiple scenarios for statistical analysis with cost management
8. **Analysis Engine** - Identifies patterns and critical factors across runs
9. **Quality Assurance Validator** - Uses lightweight models to check consistency of actions and world states
10. **Cost Management System** - Estimates, tracks, and controls LLM API costs across batch runs

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

- **Phase 1**: Core Framework (scenario format, world state, basic actor engine)
- **Phase 2**: AI Integration (LLM integration, prompt templates)
- **Phase 3**: Human Interaction (human actor control, visualization)
- **Phase 4**: Batch Processing (parallel execution, statistical analysis)
- **Phase 5**: Advanced Features (branching, replay, editor)

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
10. Create "AI 2027" calibration scenario for validation testing

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
