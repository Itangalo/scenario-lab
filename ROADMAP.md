# Scenario Lab Development Roadmap

This document outlines the development phases, current status, and future plans for Scenario Lab.

## Overview

Scenario Lab is being developed in phases, with each phase building on previous work. The focus is on creating a robust foundation before adding advanced features.

## Completed Phases

### Phase 0: Proof of Concept ✅ (October 2025)

**Goal:** Validate core concept with minimal viable implementation

**What We Built:**
- Simple scenario definition (YAML)
- Basic actor engine with LLM integration
- Minimal world state manager
- Markdown documentation generation
- Test scenario: AI regulation negotiation
- Explicit system prompts for scenarios and actors

**Key Findings:**
- ✅ Concept validated: AI agents can role-play policy actors convincingly
- ✅ Prompting strategy works with detailed actor descriptions
- ✅ Free models produce reasonable results for testing
- ✅ Markdown output is readable for expert evaluation

---

### Phase 1: Core Framework ✅ (October 2025)

**Goal:** Build production-ready core system with essential features

**What We Built:**

1. **Multi-Model Support**
   - Different LLM models per actor
   - OpenRouter integration
   - Model selection in actor YAML files
   - World state model configurable in scenario.yaml

2. **LLM-Powered World State Updates**
   - Replaced naive concatenation with LLM synthesis
   - WorldStateUpdater generates coherent narratives
   - Shows emergent consequences and interactions
   - Structured output with key changes

3. **Structured Metrics Export**
   - JSON output alongside markdown (metrics.json)
   - Define metrics in metrics.yaml
   - Regex-based automatic extraction
   - Aggregated metrics summary per run

4. **Cost Management System**
   - Pre-execution cost estimation
   - Real-time cost tracking during runs
   - Budget limits via `--credit-limit` flag
   - Cost reporting per run, per actor, per turn (costs.json)

5. **Resumable Scenarios**
   - Graceful rate limit handling (429 errors)
   - State persistence after each turn (scenario-state.json)
   - `--max-turns` for incremental execution
   - `--resume` flag to continue halted runs

6. **Scenario Branching**
   - `--branch-from` to create alternative paths
   - `--branch-at-turn` to specify branch point
   - State truncation and recalculation
   - "What-if" exploration and comparative analysis

7. **Improved Documentation**
   - Clean markdown formatting with timestamps
   - Reasoning/Action separation in actor files
   - World state files with actions summary
   - Auto-incrementing run numbers preserve history

**Not Yet Implemented from Phase 1:**
- Quality Assurance Validator (consistency checking)
- Enhanced scenario specification (validation rules, background data)

---

### Phase 2: AI Integration Enhancements (October 2025)

**Goal:** Advanced AI capabilities and communication

**Status:** ✅ Complete (4 of 5 sub-phases done, 1 deferred)

#### 2.1: Communication Types ✅

**Implemented:**
- CommunicationManager class for managing channels
- Three channel types: PUBLIC, BILATERAL, COALITION
- Multi-phase turn execution:
  1. Phase 1: Private Communications (bilateral and coalition)
  2. Phase 2: Public Actions (informed by private negotiations)
- Actor methods for deciding on and responding to communications
- State persistence for all communications
- Markdown export for private channels

**Features:**
- Bilateral negotiations: Private communication between two actors
- Coalition formation: 3+ actors can form alliances
- Strategic information asymmetry
- Actors can honor or betray private agreements

#### 2.2: Coalition Support ✅

**Implemented:**
- Coalition proposal and acceptance workflow
- All members must accept for coalition to form
- Coalition coordination within private channels
- Duplicate coalition prevention within same turn
- Markdown export: `coalition-Members-NNN.md`

#### 2.3: Advanced Prompting ⏳

**Status:** Deferred (lower priority)

**Planned:**
- Few-shot examples in system prompts
- Chain-of-thought reasoning prompts
- Self-critique mechanisms
- Dynamic prompt adaptation based on scenario progress

#### 2.4: Context Management ✅

**Implemented:**
- ContextManager class with sliding window approach
- Recent turns (default: last 3) provided in full detail
- Older turns automatically summarized using lightweight LLM
- Summary caching to avoid re-generation
- Cost-efficient: ~$0.0001 per summary using gpt-4o-mini
- Configurable via `context_window_size` in scenario.yaml

**Benefits:**
- Enables scenarios with 10-20+ turns without context overflow
- Dramatically reduces token usage in long scenarios
- Maintains decision quality with recent full-detail context

#### 2.5: Evolving Actor Goals ✅

**Implemented:**
- Goals as part of turn-by-turn actor decisions
- Actors explicitly state LONG-TERM GOALS (2-4 objectives) and SHORT-TERM PRIORITIES (1-3 objectives)
- Recent goals (last 2 turns) passed to actors for continuity
- Natural goal evolution through LLM reasoning
- Goals exported in markdown decision files

**Features:**
- Simple and elegant - no complex subsystems
- Self-documenting - goals visible in every decision
- Persuadable - actors can be convinced to change goals through negotiation
- Coherent - recent goals maintain consistency across turns
- Realistic - goals evolve based on world events and actor interactions

**Example Use Case:**
In cooperation scenarios, an actor's goal can evolve from "defeat competitor X" to "establish international standards" based on negotiations and world developments, making genuine collaboration realistic.

---

### Testing Infrastructure ✅ (October 2025)

**Implemented:**
- Comprehensive unit test suite (29 tests, all passing)
- Tests for: WorldState, CommunicationManager, ContextManager, CostTracker
- Test runner with summary output (`run_tests.py`)
- Test documentation in `tests/README.md`
- CI-ready infrastructure

---

## Current Phase: Phase 3 (Not Started)

### Phase 3: Human Interaction

**Goal:** Enable human experts to participate in scenarios

**Planned Components:**

1. **Human Actor Interface**
   - CLI or web interface for human input
   - Display current world state to human
   - Input reasoning and action
   - Format matching AI actor output

2. **Actor Hand-off Mechanism**
   - Switch actor from AI to human mid-scenario
   - Switch from human back to AI
   - Preserve context and history
   - Clear handoff documentation

3. **Real-time Scenario Visualization**
   - Dashboard showing current state
   - Actor positions and decisions
   - Metrics visualization
   - Turn-by-turn timeline

4. **Decision Explanation System**
   - Show AI reasoning transparently
   - Allow humans to question AI decisions
   - Alternative action suggestions
   - Impact previews

**Success Criteria:**
- Human can replace any AI actor
- Seamless handoff between AI and human
- Real-time view of scenario state
- Clear documentation when human participates

---

## Future Phases

### Phase 4: Batch Processing

**Goal:** Run and analyze multiple scenarios systematically

**Planned Components:**

1. **Batch Runner with Variations**
   - Run same scenario with different actor configurations
   - Systematic parameter variations
   - Run same scenario N times for stochastic analysis
   - Parallel execution support

2. **Cost Management for Batches**
   - Early stopping when patterns converge
   - Adaptive sampling strategies
   - Tiered execution (cheap models for exploration, expensive for detail)

3. **Statistical Analysis Tools**
   - Aggregate metrics across runs
   - Outcome distribution analysis
   - Identify critical decision points
   - Sensitivity analysis

4. **Pattern Recognition**
   - Cluster similar outcomes
   - Identify common decision patterns
   - Find divergence points
   - Anomaly detection

5. **Comparison Tools**
   - Side-by-side run comparison
   - Diff view for decisions
   - Metric comparisons
   - What-if analysis

**Success Criteria:**
- Can run 100+ scenarios automatically
- Cost stays within budget
- Statistical analysis generates insights
- Easy comparison of different configurations
- Patterns identified across runs

**Note:** We already have foundations for Phase 4 (branching, cost management, resumability)

---

### Phase 5: Advanced Features

**Goal:** Polish and extend capabilities

**Planned Components:**

1. **Scenario Editor and Validator**
   - GUI for creating scenarios
   - YAML validation and linting
   - Actor template library
   - Scenario testing tools

2. **Comprehensive Analysis Dashboard**
   - Web-based visualization
   - Interactive exploration of runs
   - Filter and search scenarios
   - Export reports

3. **Scenario Library and Reusability**
   - Actor archetypes library
   - Event templates
   - Metric templates
   - Composition system for building scenarios

4. **Advanced Validation**
   - Calibration scenarios (e.g., "AI 2027")
   - Expert review workflows
   - Historical scenario comparison
   - Realism scoring

5. **Checkpointing and Replay**
   - Save scenario state at any turn
   - Restart from checkpoint
   - Replay with different decisions
   - Time-travel debugging

**Success Criteria:**
- Easy scenario creation and editing
- Reusable components reduce duplication
- Calibration against historical events
- Professional analysis and reporting
- Full scenario lifecycle support

---

## Development Principles

- **Phase flexibility:** Phases may overlap in practice
- **User feedback driven:** Prioritization adapts to user needs
- **Quality over speed:** Solid foundations before advanced features
- **Cost consciousness:** Batch processing and optimization remain priorities
- **Open development:** Regular updates and transparent progress

---

## How to Contribute

Interested in contributing? Here are ways to help:

1. **Testing:** Run scenarios and report issues or unexpected behaviors
2. **Scenario Creation:** Design and share interesting test scenarios
3. **Documentation:** Improve guides, examples, or API documentation
4. **Feature Requests:** Suggest features aligned with the roadmap
5. **Code Contributions:** See CONTRIBUTING.md (if available)

---

## Version History

- **v0.3** (October 2025): Phase 2 complete - Communication types, coalitions, context management, evolving goals, test suite
- **v0.2** (October 2025): Phase 1 - Core framework with multi-model support, resumability, branching
- **v0.1** (October 2025): Phase 0 - Proof of concept

---

## Questions or Feedback?

Open an issue on GitHub or reach out through the repository discussions.
