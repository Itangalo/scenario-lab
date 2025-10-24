# Test AI Regulation Negotiation

A proof-of-concept scenario for testing the Scenario Lab framework.

## Scenario Description

This scenario simulates a 3-turn negotiation between a national AI safety regulator and a frontier AI technology company over proposed AI safety regulations.

**Key issues:**

- Mandatory safety testing before deployment
- Incident reporting requirements
- Third-party auditing of AI systems
- Compute thresholds that trigger regulation

## Actors

- **National AI Safety Regulator** - Safety-focused but pragmatic regulatory agency
- **FrontierAI Technologies** - Innovation-focused tech company with competitive pressures

## Running This Scenario

From the project root:

```bash
python src/run_scenario.py scenarios/test-regulation-negotiation
```

## Scenario Dynamics

Each turn:

1. Both actors simultaneously make decisions based on the current world state
2. Their decisions are recorded in markdown files
3. The world state is updated to reflect their actions
4. Process repeats for the next turn

The negotiation progresses over 3 turns (1 month each), allowing actors to respond to each other's positions and find areas of compromise.

## Output

Results are saved to `output/test-regulation-negotiation/run-001/`:

- `world-state-000.md` - Initial situation
- `regulator-001.md` - Regulator's reasoning and action for turn 1
- `tech-company-001.md` - Company's reasoning and action for turn 1
- `world-state-001.md` - Updated world state after turn 1
- ... and so on for each turn

## Configuration

- **Turns:** 3
- **Turn duration:** 1 month
- **Default model:** `alibaba/tongyi-deepresearch-30b-a3b:free` (OpenRouter)

## Expected Outcomes

Through this negotiation, actors typically:

- Move from initial positions toward compromise
- Reference specific technical details (FLOP thresholds, reporting timelines)
- Balance competing priorities (safety vs. innovation, transparency vs. IP protection)
- Develop concrete proposals and counter-proposals

## Notes

This is a proof-of-concept scenario used to validate the Scenario Lab framework. It demonstrates:

- ✅ AI actors can role-play policy negotiation convincingly
- ✅ Strategic thinking and realistic compromise emerges
- ✅ Technical sophistication in proposals
- ✅ Readable documentation for expert evaluation
