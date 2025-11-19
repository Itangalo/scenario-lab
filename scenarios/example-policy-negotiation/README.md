# Example Scenario: AI Safety Policy Negotiation

## Purpose

This is a **template scenario** designed to help you understand how to configure Scenario Lab simulations. It demonstrates all core features with detailed comments explaining each design choice.

**You can use this scenario in two ways:**

1. **As a learning resource**: Read the YAML files to understand the configuration format
2. **As a starting template**: Use the scenario creation wizard with the "Start from example" option to create your own scenarios based on this template

## Scenario Overview

A two-party negotiation between:

- **National AI Safety Regulator**: Proposing new safety requirements for advanced AI
- **FrontierAI Technologies**: A tech company developing frontier AI models

The parties negotiate over:

- Safety testing requirements
- Incident reporting timelines
- Third-party auditing
- Compute thresholds for regulatory oversight

## What This Example Demonstrates

### 1. **Scenario Configuration** (`scenario.yaml`)
   - How to set up initial world state with clear stakes
   - Choosing turn count and duration
   - Selecting appropriate world state models
   - Writing effective system prompts

### 2. **Actor Design** (`actors/*.yaml`)
   - Creating distinct actor identities with conflicting goals
   - Defining realistic constraints that shape behavior
   - Specifying expertise levels across domains
   - Describing decision-making styles

### 3. **Metrics** (`metrics.yaml`)
   - Automatic extraction with regex patterns (for objective values)
   - Manual extraction (for subjective assessments)
   - Actor-specific vs. scenario-level metrics
   - Process metrics (what was proposed) vs. outcome metrics (what was agreed)

### 4. **Quality Assurance** (`validation-rules.yaml`)
   - Automated consistency checking
   - Three validation types: actor decisions, world state coherence, information access
   - Configuration options and severity thresholds

## File Structure

```
example-policy-negotiation/
├── README.md                    # This file
├── scenario.yaml                # Main scenario configuration
├── actors/
│   ├── regulator.yaml          # Regulator actor definition
│   └── tech-company.yaml       # Tech company actor definition
├── metrics.yaml                 # Metrics tracking configuration
└── validation-rules.yaml        # Quality assurance rules
```

## Key Design Choices Explained

### Why 5 turns?
Enough for a complete negotiation arc: initial positions → proposals → counter-proposals → compromise → finalization. Not so many that costs get high during testing.

### Why 2 weeks per turn?
Realistic timeframe for policy negotiations. Short enough to maintain urgency, long enough for meaningful progress between rounds.

### Why gpt-4o-mini for world state?
World state synthesis happens once per turn, so even this affordable model provides good quality. In production, you might upgrade to gpt-4o or claude-3.5-sonnet.

### Why gpt-4o for actors?
Actors make the critical strategic decisions. Using a higher-quality model ensures more realistic and sophisticated behavior. For testing, you could downgrade to gpt-4o-mini.

### Why these specific goals and constraints?
The goals create tension (regulator wants safety, company wants flexibility), while constraints prevent extreme positions (regulator can't ignore industry, company can't appear irresponsible). This creates realistic negotiation dynamics.

## Using This Example

### Option 1: Learn by Reading

Open each YAML file and read the comments. They explain:
- Why each field exists
- What values are appropriate
- How choices affect simulation behavior

### Option 2: Start from Example in Wizard

Run the scenario creation wizard:

```bash
python src/create_scenario.py
```

When prompted, choose "Start from example scenario". The wizard will load these configurations and let you:
- See each value as you step through
- Modify values to fit your use case
- Understand the format by example

### Option 3: Copy and Modify Directly

Copy this directory and edit the YAML files directly:

```bash
cp -r scenarios/example-policy-negotiation scenarios/my-new-scenario
# Edit YAML files in scenarios/my-new-scenario/
```

## Running This Example

You can run this scenario directly to see how it works:

```bash
# Test run (2 turns only, to save costs)
python src/run_scenario.py scenarios/example-policy-negotiation --max-turns 2

# Full run with budget limit
python src/run_scenario.py scenarios/example-policy-negotiation --credit-limit 1.00

# Full 5-turn run
python src/run_scenario.py scenarios/example-policy-negotiation
```

**Expected cost**: ~$0.10-0.30 for full 5-turn run with gpt-4o actors and gpt-4o-mini world state.

## Next Steps

After understanding this example:

1. **Create your own scenario** using the wizard
2. **Test with cheap models** first (gpt-4o-mini for all actors)
3. **Review outputs** to see if actors behave as intended
4. **Refine prompts** based on actual behavior
5. **Upgrade models** for production runs
6. **Create batch experiments** to test variations systematically

## Related Documentation

- **[Scenario Creation Guide](../../docs/scenario-creation-guide.md)**: Complete guide to creating scenarios
- **[README.md](../../README.md)**: Framework overview and core concepts
- **[Batch Execution Guide](../../docs/batch-execution-guide.md)**: Running systematic experiments

## Questions This Example Should Answer

- How specific should initial world state be? → See `scenario.yaml` line 24-48
- What's a good number of goals per actor? → See actors/*.yaml goals sections (4-5 goals)
- How do I write effective constraints? → See actors/*.yaml constraints sections
- What metrics should I track? → See `metrics.yaml` with 10 example metrics
- Do I need validation? → Yes, costs <2% and catches important issues
- Which models should I use? → Depends on testing vs. production (see comments in files)

## Support

If you have questions about this example or scenario creation:

1. Check the comments in each YAML file
2. Review the [Scenario Creation Guide](../../docs/scenario-creation-guide.md)
3. Ask in the project repository
