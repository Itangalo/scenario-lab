# Scenario Lab

## Overview

An experimental framework for exploring complex policy and strategic questions through AI-automated scenario exercises. The system enables multi-actor simulations where AI agents interact in dynamic environments, providing both statistical insights from batch runs and deep qualitative analysis of decision-making patterns.

The primary focus is exploring AI-related policy questions and strategic challenges through simulation, testing how different actors, policies, and interventions perform across diverse scenarios—including unexpected black swan events.

## Core Principles

### 1. AI-Controlled Actors

All actors in the scenario can be controlled by AI agents, each with their own goals, information, and decision-making capabilities. Different actors may use different LLM models to leverage specific capabilities (e.g., technical reasoning, negotiation, domain expertise).

**Evolving Goals**: Actor goals are not fixed but evolve naturally throughout scenarios. Each turn, actors explicitly state their LONG-TERM GOALS (2-4 enduring objectives) and SHORT-TERM PRIORITIES (1-3 immediate objectives). Recent goals from previous turns inform future decisions, allowing actors to adapt based on:
- Negotiations and agreements with other actors
- World events and their consequences
- Successes and failures of previous actions
- New information and changing circumstances

This enables realistic scenarios where, for example, an actor's goal can evolve from "defeat competitor X" to "establish collaborative international standards" through natural diplomatic progression.

### 2. Dynamic World State
The world state evolves based on actor decisions, with AI managing the consequences and cascading effects of actions taken. Scenarios can include black swan events—low-probability, high-impact occurrences that test actors' ability to respond to unexpected disruptions.

### 3. Human-in-the-Loop Capability
Human experts can replace any AI-controlled actor at any time, allowing for:
- Training exercises
- Testing specific strategies
- Expert validation of AI decisions
- Hybrid human-AI collaboration

### 4. Scenario Flexibility
The framework supports diverse scenarios through structured initial state definitions that describe:
- World state and conditions
- Actor profiles and capabilities
- Available actions and constraints
- Environmental factors

### 5. Metrics and Observability
Each scenario defines meaningful metrics that track:
- World state evolution
- Actor performance
- Key decision points
- Success/failure criteria

### 6. Batch Simulation and Analysis

The system supports:

- Running hundreds or thousands of scenarios with systematic variations
- Statistical analysis of outcomes across multiple runs
- Identification of critical decision points
- Pattern recognition in successful/failed runs
- Qualitative analysis of recurring factors
- Testing policy variations by modifying actor definitions or world states between runs

Note: Actors have no memory between scenario runs. Each run is independent, allowing for controlled experimentation.

### 7. Step-by-Step Documentation
Each simulation step is documented in Markdown files:
- `world-state-[step].md` - Public world state
- `actor-[name]-[step].md` - Actor-specific state and decisions
- Chronological record of all actions and consequences

### 8. Information Asymmetry
Actors maintain:
- **Public information**: Visible to all actors and recorded in world state
- **Private information**: Known only to specific actors, affecting their decisions

### 9. Termination Criteria

Each scenario definition includes clear criteria for when the scenario ends:

- Success/failure conditions
- Time limits
- Critical threshold breaches
- Deadlock detection

### 10. Temporal Model and Communication

The framework operates on a simultaneous turn-based model where all actors make decisions concurrently:

- **Simultaneous turns**: All actors decide and act within the same time period
- **Variable turn duration**: Each scenario defines appropriate turn duration (e.g., "1 day", "1 month", "1 quarter"), which may vary throughout the scenario as needed
- **Communication types**: Actors can engage in different forms of communication including public statements, bilateral negotiations, coalition formation, and information sharing
- **Communication visibility**: Different communication types have different visibility rules (e.g., public statements visible to all, bilateral negotiations visible only to participants)

### 11. Communication System

Each turn consists of three phases that enable different types of actor interaction:

#### Phase 1: Private Communications

**Bilateral Negotiations**
- Any actor can initiate private communication with one other actor
- Both actors exchange messages in a private channel
- Only the two participants can see these messages
- Useful for: Deal-making, information sharing, coordination, trust-building

**Example workflow:**
1. Actor A decides whether to initiate bilateral communication
2. If yes, Actor A chooses target (Actor B) and sends initial message
3. Actor B receives message and responds
4. Both messages are saved to a bilateral channel for this turn

**Coalition Formation**
- Any actor can propose forming a coalition with 2+ other actors
- Proposed members are asked to accept or reject the invitation
- If all members accept, a coalition channel is created
- All coalition members can communicate within the coalition
- Only coalition members can see these messages
- Useful for: Strategic alliances, coordinated action, power consolidation

**Example workflow:**
1. Actor A proposes coalition with Actors B and C
2. Actor A specifies the coalition's purpose
3. Actors B and C independently decide to accept or reject
4. If both accept, coalition channel is created
5. All three actors (A, B, C) coordinate strategy within the coalition

**Key features:**
- Coalitions require at least 3 members (2+ in addition to proposer)
- Duplicate coalitions within a turn are automatically prevented
- Coalition members see all previous messages in the channel when deciding what to say
- Coalitions are formed per turn (actors can reform with different members each turn)

#### Phase 2: Public Actions

After private communications conclude:
- All actors see a summary of communications they participated in
- Actors make public decisions informed by private negotiations and coalition coordination
- Public decisions are visible to all actors and recorded in world state
- Actors may honor or betray private agreements made in Phase 1

**Information flow:**
- Bilateral messages: Visible only to the two participants
- Coalition messages: Visible only to coalition members
- Public actions: Visible to all actors

#### Documentation

Private communications are exported to markdown files:
- `bilateral-ActorA-ActorB-001.md` - Bilateral negotiations between two actors in turn 1
- `coalition-ActorA-ActorB-ActorC-001.md` - Coalition communication in turn 1
- Actor decision files include internal notes about negotiations and commitments

This multi-phase structure enables realistic strategic interaction, including:
- Private deal-making before public action
- Coalition building among multiple actors
- Strategic information asymmetry
- Testing whether actors honor private commitments
- Emergent alliance patterns over multiple turns

### 12. Context Management for Long Scenarios

For scenarios lasting many turns, the framework implements intelligent context management to prevent token overflow while maintaining decision quality:

**Sliding Window Approach**
- Recent turns (default: last 3) are provided in full detail
- Older turns are automatically summarized using a lightweight LLM
- Actors always receive complete communication history they participated in

**Benefits:**
- **Cost reduction**: Summaries use far fewer tokens than full history
- **Scalability**: Enables scenarios with 10+ turns without context overflow
- **Quality preservation**: Recent context in full detail maintains decision quality
- **Automatic operation**: No manual intervention required

**Configuration:**
Scenarios can configure window size in `scenario.yaml`:
```yaml
context_window_size: 3  # Number of recent turns in full detail (default: 3)
```

**Example context structure for turn 8 with window size 3:**
```
## Earlier Events (Summary)
[AI-generated summary of turns 0-5]

---

## Recent History (Last 3 Turns)

### Turn 6
**World State:** [Full detail]
**Actions Taken:** [All actor actions]
**Communications:** [Any bilateral/coalition messages]

### Turn 7
[Full detail...]

### Turn 8
[Full detail...]
```

**Cost efficiency:**
- Summaries generated once and cached
- Uses gpt-4o-mini (~$0.0001 per summary)
- Dramatically reduces per-decision token counts in long scenarios

## Primary Research Focus: AI Policy and Strategy

This framework is designed to explore critical questions about AI governance, policy, and strategic decision-making through simulation:

### Key Research Questions

- **Regulatory effectiveness**: How do different AI regulatory approaches perform under various market conditions and technological trajectories?
- **Governance structures**: Which organizational structures and decision-making processes best handle AI deployment challenges?
- **International coordination**: How do different international cooperation mechanisms affect global AI safety and development?
- **Corporate strategy**: What strategies prove most resilient for organizations navigating AI disruption and regulation?
- **Safety interventions**: Which AI safety measures and interventions have the greatest impact across different scenarios?
- **Risk assessment**: What factors consistently predict successful vs. failed outcomes in AI-related crises?

### Why Automated Scenarios for AI Policy?

Traditional scenario exercises are valuable but limited by:
- **Scale constraints**: Manual exercises can only explore a handful of scenarios
- **Human bias**: Facilitators and participants bring assumptions that limit exploration
- **Resource intensity**: Each exercise requires significant expert time
- **Limited iteration**: Difficult to systematically vary conditions and compare outcomes

Automated scenario exercises enable:
- **Systematic exploration**: Test hundreds or thousands of policy variations
- **Pattern discovery**: Identify critical factors and decision points across many runs
- **Hypothesis testing**: Rigorously test policy theories against diverse conditions
- **Black swan preparation**: Include low-probability events to test resilience
- **Controlled experimentation**: Isolate variables to understand causal mechanisms

### Validation and Calibration

To ensure simulation quality and realism, the framework uses multiple validation approaches:

- **Calibration scenarios**: Use historical scenarios with known outcomes (e.g., "AI 2027") to test whether the framework produces realistic results. Compare simulation outputs against actual historical events.
- **Expert evaluation**: Domain experts review generated markdown documentation (world states and actor decisions) to assess realism, consistency, and plausibility of actor behavior and scenario evolution.
- **Consistency checking**: Lightweight AI models validate that actor decisions align with their stated goals, capabilities, and available information, and that world state updates are logically consistent.

## Use Cases

- **Crisis management training**: Simulate organizational responses to emergencies
- **Strategic planning**: Test strategies against various scenarios
- **Policy analysis**: Model impacts of policy decisions
- **Game theory research**: Study multi-agent interactions
- **Decision-making research**: Identify critical factors in complex scenarios
- **Risk assessment**: Evaluate vulnerabilities across multiple scenarios

## Technical Architecture

### Components

1. **Scenario Definition Parser**: Loads and validates scenario specifications
2. **World State Manager**: Maintains and updates global state
3. **Actor Engine**: Manages AI-controlled and human-controlled actors, supports multiple LLM models per scenario
4. **Action Resolver**: Processes actor decisions and updates world state
5. **Metrics Tracker**: Records and analyzes key performance indicators, exports structured data
6. **Documentation Generator**: Creates markdown records of each step
7. **Batch Runner**: Executes multiple scenarios for statistical analysis with cost management
8. **Analysis Engine**: Identifies patterns and critical factors
9. **Quality Assurance Validator**: Uses lightweight models to check consistency of actions and world states against scenario rules
10. **Cost Management System**: Estimates, tracks, and controls LLM API costs across batch runs

### Cost Management

Running hundreds or thousands of AI-powered scenarios can incur significant LLM API costs. The framework includes comprehensive cost management:

- **Pre-execution estimation**: Calculate expected costs based on scenario complexity, number of actors, and planned iterations
- **Cost tracking**: Monitor actual API costs in real-time during batch execution
- **Cost controls**: Set budget limits, implement early stopping when patterns converge, use adaptive sampling strategies
- **Model optimization**: Use lightweight models for quality assurance checks and exploration, reserve stronger models for detailed analysis
- **Efficient caching**: Avoid re-executing identical scenario segments across multiple runs

### Quality Assurance Validation

The QA Validator automatically checks simulation consistency using lightweight LLM models to validate outputs from more expensive models:

**What it validates:**
- **Actor decision consistency**: Checks that actor decisions align with their stated goals, constraints, and expertise levels
- **World state coherence**: Validates that world state updates logically follow from actor actions
- **Information access**: Ensures actors only reference information they should have access to

**Configuration:**
- Define validation rules in `validation-rules.yaml` within each scenario
- Specify which checks to enable/disable
- Set severity thresholds (low/medium/high)
- Choose validation model (default: `openai/gpt-4o-mini` for cost efficiency)

**Outputs:**
- `validation-NNN.md`: Per-turn validation reports
- `validation-summary.md`: Overall validation results across the scenario
- Validation costs tracked separately in `costs.json`

**Benefits:**
- **Quality assurance**: Catch inconsistencies and logic errors automatically
- **Cost-effective**: Lightweight models validate expensive model outputs
- **Transparent**: Detailed reports explain what was checked and any issues found
- **Configurable**: Enable only the checks you need

### Data Structure

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

## Development Roadmap

### Phase 0: Proof of Concept ✅
- [x] Basic scenario execution
- [x] Actor decision-making via LLM
- [x] Simple world state tracking
- [x] Markdown output

### Phase 1: Core Framework ✅
- [x] Define scenario specification format (including LLM model specs, metrics definitions)
- [x] Implement world state manager
- [x] Create basic actor engine with multi-model support
- [x] Build markdown documentation generator
- [x] Implement LLM-powered world state synthesis
- [x] Implement structured metrics data export (JSON)
- [x] Implement cost tracking and estimation
- [x] Auto-incrementing run numbers
- [x] Create quality assurance validator

### Phase 2: AI Integration ✅
- [x] Integrate LLM for actor decision-making (support multiple models via OpenRouter)
- [x] Implement AI world state updates
- [x] Create prompt templates for different actor types
- [x] Add context management for long-running scenarios
- [x] Implement different communication types (public statements, bilateral negotiations, coalition formation)

### Phase 3: Human Interaction
- [ ] Build interface for human actor control
- [ ] Implement actor hand-off mechanism
- [ ] Create real-time scenario visualization
- [ ] Add decision explanation system

### Phase 4: Batch Processing ✅ COMPLETE

**Core Batch Execution:**
- [x] Develop batch runner for multiple scenarios with systematic variations
- [x] Implement cost estimation and tracking for batch runs
- [x] Implement cost controls (limits, early stopping)
- [x] Add local LLM support (Ollama, llama.cpp) for cost-free batch runs
- [x] Create statistical analysis tools for structured metrics data
- [x] Build pattern recognition system
- [x] Implement parallel execution with rate limiting
- [x] Add real-time progress tracking with rich progress bars

**User Experience & Safety:** ✅ NEW
- [x] Interactive config wizard with validation and model suggestions
- [x] Dry-run preview mode with cost/time estimation
- [x] Comprehensive error handling with user-friendly messages (10 categories)
- [x] Progressive fallback strategies for model failures
- [x] Automatic recovery suggestions for common errors

**Performance & Optimization:** ✅ NEW
- [x] Response caching system (30-70% cost savings, SHA256-based)
- [x] HTTP connection pooling (15-40% speed improvement)
- [x] Memory optimization with automatic garbage collection
- [x] Memory monitoring and warnings (prevents OOM errors)
- [x] Graceful degradation (works without optional dependencies)

**Future Enhancements:**
- [ ] Hardware temperature monitoring for local LLM usage (prevent thermal throttling)
- [ ] Adaptive sampling (early stopping when pattern clear)

### Phase 5: Advanced Features
- [x] Add scenario branching from any completed turn (✅ implemented in Phase 4)
- [x] Implement checkpointing and resumable scenarios (✅ implemented in Phase 4)
- [ ] Create scenario editor and validator
- [ ] Build comprehensive analysis dashboard
- [ ] Add scenario replay and debugging tools

## Example Scenarios

### AI Policy and Governance

- **AI 2027** (Calibration scenario): Historical scenario for framework validation and calibration
- **AI Regulatory Negotiation**: Multiple nations negotiate international AI safety standards while balancing innovation, security, and economic interests
- **AI Safety Incident Response**: Government agencies and tech companies coordinate response to a major AI system failure or misuse incident
- **Corporate AI Governance**: Organization navigates deployment of advanced AI systems amid regulatory uncertainty, safety concerns, and competitive pressure
- **AI Arms Race Dynamics**: Nations and corporations decide on AI development speed, safety investments, and cooperation mechanisms
- **Automated Decision System Deployment**: Public sector organization implements AI decision-making system while managing accountability, bias, and public trust concerns

### General Strategic Scenarios

- **Cybersecurity Incident Response**: Organization responds to data breach
- **Climate Policy Negotiation**: Multiple nations negotiate climate agreement
- **Supply Chain Disruption**: Company manages global supply chain crisis
- **Pandemic Response**: Government agencies coordinate public health response

## Getting Started

### Prerequisites

- Python 3.11+
- OpenRouter API key (get a free one at [OpenRouter](https://openrouter.ai/))

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/Itangalo/scenario-lab.git
cd scenario-lab
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run tests (optional but recommended):**

```bash
python run_tests.py
```

All tests should pass. See `tests/README.md` for details.

4. **Set up your API key:**

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Running a Scenario

Run the test scenario:

```bash
python src/run_scenario.py scenarios/test-regulation-negotiation
```

Output will be saved to `output/test-regulation-negotiation/run-001/` (subsequent runs auto-increment to run-002, run-003, etc.)

Each run produces:

- **Markdown files**: Human-readable documentation
  - `world-state-000.md` through `world-state-00N.md` - Evolution of world state
  - `actor-name-001.md` through `actor-name-00N.md` - Actor decisions and reasoning

- **JSON files**: Structured data for analysis
  - `costs.json` - Complete cost breakdown (by actor, turn, and world state updates)
  - `metrics.json` - Quantitative metrics tracked throughout the scenario
  - `scenario-state.json` - Complete execution state for resumption

The system estimates costs before execution and tracks actual API usage throughout the run

### Resumable Scenarios

Scenario runs can be stopped and resumed, enabling graceful handling of API rate limits, budget constraints, and incremental execution.

**Stop after a fixed number of turns:**
```bash
python src/run_scenario.py scenarios/test-regulation-negotiation --max-turns 2
```

**Set a budget limit:**
```bash
python src/run_scenario.py scenarios/test-regulation-negotiation --credit-limit 0.50
```
The scenario will halt if total cost exceeds $0.50.

**Resume a halted scenario:**
```bash
python src/run_scenario.py --resume output/test-regulation-negotiation/run-003
```

**How it works:**
- After each turn, the complete scenario state is saved to `scenario-state.json`
- If a run is halted (rate limit, credit limit, max turns, or error), the state is preserved
- Resume restores all components: world state, actor states, cost tracking, and metrics
- The run continues from the next incomplete turn

**Halt reasons:**
- `rate_limit` - API rate limit exceeded (429 error)
- `credit_limit` - Cost threshold exceeded
- `max_turns` - Reached specified turn limit
- `manual` - User interruption (Ctrl+C)

Each run directory contains `scenario-state.json` with execution status and full state for resumption.

### Scenario Branching

Create alternative scenario paths by branching from any completed turn. This enables exploring "what-if" scenarios and testing different strategies from the same starting point.

**Branch from an existing run:**
```bash
python src/run_scenario.py --branch-from output/test-regulation-negotiation/run-001 --branch-at-turn 2
```

**How it works:**
- Creates a new run directory (e.g., run-008) with auto-incremented number
- Copies all state and output files up to the branch point
- Truncates cost tracking and metrics to the branch point
- Sets status to 'running' so you can resume from the next turn
- Preserves branch metadata (source run, branch point) in state file

**Use cases:**
- Test different actor strategies from the same starting conditions
- Explore alternative policy approaches after a critical decision point
- Compare outcomes with different actor models or prompts
- Run sensitivity analysis by branching and varying parameters

**Example workflow:**
```bash
# Run initial scenario
python src/run_scenario.py scenarios/test-regulation-negotiation

# Branch from turn 2 of run-001
python src/run_scenario.py --branch-from output/test-regulation-negotiation/run-001 --branch-at-turn 2

# Continue the branch with modified scenario or actors
python src/run_scenario.py --resume output/test-regulation-negotiation/run-002
```

### Batch Execution

Run multiple scenario variations for statistical analysis. The batch system enables systematic exploration of parameter spaces, model comparisons, and robustness testing.

**Create a batch configuration interactively (recommended):**

```bash
# Interactive wizard with validation and model suggestions
python src/create_batch_config.py --interactive

# Follow the prompts to:
# - Select scenario
# - Choose number of runs
# - Configure parallelism
# - Set budget limits
# - Define variations
# - Preview before saving
```

**Or create a batch configuration manually:**

```yaml
# experiments/model-comparison/batch-config.yaml
experiment_name: "Model Comparison Study"
base_scenario: "scenarios/test-regulation-negotiation"

runs_per_variation: 10
budget_limit: 20.00

variations:
  - type: "actor_model"
    actor: "regulator"
    values: ["openai/gpt-4o-mini", "anthropic/claude-3-haiku"]
  - type: "actor_model"
    actor: "tech-company"
    values: ["openai/gpt-4o-mini", "anthropic/claude-3-haiku"]

# Creates 2×2 = 4 variations × 10 runs = 40 total runs

output_dir: "experiments/model-comparison"
```

**Preview before running (dry-run):**

```bash
# See what will execute without actually running
python src/batch_runner.py experiments/model-comparison/batch-config.yaml --dry-run

# Shows:
# - Variation count and total runs
# - Estimated cost and time
# - Budget warnings if limits exceeded
# - All variations with model details
```

**Run the batch:**

```bash
python src/batch_runner.py experiments/model-comparison/batch-config.yaml
```

**Analyze results:**

```bash
# Generate analysis report
python src/batch_analyzer.py experiments/model-comparison/ --report

# View results
cat experiments/model-comparison/analysis/analysis-report.md
```

**Output includes:**

- Individual run outputs in `runs/var-XXX-run-YYY/`
- Statistical analysis: means, standard deviations, ranges
- Variation comparison: which parameter combinations performed best
- Cost efficiency analysis: runs per dollar spent
- Pattern identification: success factors and failure modes

**Resume interrupted batches:**

```bash
python src/batch_runner.py experiments/model-comparison/batch-config.yaml --resume
```

**Features:**

- Systematic parameter variation (actor models, more to come)
- Configurable parallelism (respects API rate limits)
- Budget controls (per-run and total batch limits)
- Automatic cost tracking and analysis
- Resumable execution
- Statistical analysis and reporting

See [Batch Execution Guide](docs/batch-execution-guide.md) for detailed documentation.

### Available Scenarios

- **test-regulation-negotiation**: AI safety regulation negotiation between regulator and tech company ([docs](scenarios/test-regulation-negotiation/README.md))

## Documentation

Comprehensive guides are available in the `docs/` directory:

### Core Documentation

- **[Batch Execution Guide](docs/batch-execution-guide.md)** - Complete guide to running batch experiments with parameter variations
- **[Batch Config Wizard Guide](docs/batch-config-wizard-guide.md)** - Interactive wizard for creating batch configurations, including dry-run mode
- **[Error Handling Guide](docs/error-handling-guide.md)** - User-friendly error messages, recovery strategies, and troubleshooting
- **[Performance Optimizations](docs/performance-optimizations.md)** - Caching, connection pooling, memory management, and graceful degradation

### Specialized Topics

- **[Local LLMs](docs/LOCAL_LLMS.md)** - Running scenarios with local models (Ollama, llama.cpp) for cost-free execution

### Key Features Covered

**User Experience:**
- Interactive config wizard with validation
- Dry-run preview with cost/time estimates
- Comprehensive error messages with suggested fixes
- Step-by-step troubleshooting guides

**Performance:**
- Response caching (30-70% cost savings)
- Connection pooling (15-40% faster)
- Memory optimization (prevents OOM errors)
- Works without optional dependencies

**Cost Management:**
- Budget limits (total and per-run)
- Cost estimation and tracking
- Cache hit rate analysis
- Cost savings reports

**Execution Control:**
- Resumable scenarios (handle rate limits gracefully)
- Scenario branching from any turn
- Parallel execution with rate limiting
- Real-time progress tracking

## License and Usage

_To be determined_
