# Scenario Lab - Proof of Concept

This is a minimal viable implementation to test the core concept of AI-automated scenario exercises.

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Set up OpenRouter API key:**

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

Get a free API key from [OpenRouter](https://openrouter.ai/)

3. **Run the test scenario:**

```bash
cd src
python run_scenario.py ../scenarios/test-regulation-negotiation
```

## What This Does

The PoC simulates a 3-turn negotiation between:

- **National AI Safety Regulator** - wants robust safety standards
- **FrontierAI Technologies** - wants minimal regulatory burden

Each turn:

1. Both actors simultaneously make decisions based on the current world state
2. Their decisions are recorded in markdown files
3. The world state is updated to reflect their actions
4. Process repeats for next turn

## Output

Results are saved to `output/test-regulation-negotiation/run-001/`:

- `world-state-000.md` - Initial situation
- `regulator-001.md` - Regulator's reasoning and action for turn 1
- `tech-company-001.md` - Company's reasoning and action for turn 1
- `world-state-001.md` - Updated world state after turn 1
- ... and so on for each turn

## Model Used

This PoC uses `alibaba/tongyi-deepresearch-30b-a3b:free` from OpenRouter - a no-cost model for testing.

## What's Missing (For Full Phase 1)

- Multi-model support
- Structured metrics (JSON)
- Quality assurance validation
- Better world state updates (currently just text concatenation)
- Communication types (bilateral, public statements, etc.)
- Cost tracking
- Parallel execution
- Statistical analysis across multiple runs

## Success Criteria

- ✅ Does it generate 3 turns with 2 actors?
- ✅ Is the markdown output readable?
- ✅ Do actors show somewhat realistic behavior?
- ✅ Is the cost reasonable? (Free tier for testing!)
