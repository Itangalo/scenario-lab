# AI 2027 Calibration Methodology

This document describes how the AI 2027 scenario serves as a calibration tool to validate the Scenario Lab framework's ability to produce realistic simulations.

## Purpose

The AI 2027 scenario is designed as a **calibration scenario** - a test case where we can compare simulated outcomes against real-world events to validate that:

1. **Actors behave realistically** - Decisions align with how real policymakers, CEOs, and researchers act
2. **World state updates are plausible** - Scenario progression matches realistic timelines and causality
3. **Metrics track meaningful changes** - Quantitative measures capture important dynamics
4. **Critical factors are identified** - Simulations reveal decision points that actually matter

## Calibration Approach

### 1. Historical Baseline (2024-2025)

We track actual AI developments from 2024 through early 2025 to establish ground truth:

**Major AI Capability Milestones:**
- GPT-4o release (May 2024)
- Claude 3.5 Sonnet release (June 2024)
- o1 reasoning model release (September 2024)
- Gemini 2.0 release (December 2024)
- DeepSeek R1 release (January 2025)

**Regulatory/Policy Developments:**
- EU AI Act implementation (2024)
- US AI Safety Institute establishment
- UK AI Safety Summit outcomes
- China AI regulations and enforcement
- Corporate AI safety commitments

**Alignment Research:**
- Mechanistic interpretability progress
- Scaling laws research
- Safety technique development
- Compute governance proposals

**Economic Impact:**
- AI automation adoption rates
- Job market changes
- Productivity gains
- AI company valuations

### 2. Validation Metrics

For each major real-world event, we assess simulation quality:

#### Accuracy Metrics

**Decision Realism (0-10 scale):**
- Do simulated actors make decisions similar to real counterparts?
- Are decision-making processes realistic (e.g., considering similar factors)?
- Do actors exhibit realistic biases and constraints?

**Timeline Plausibility (0-10 scale):**
- Does AI capability progression match realistic pace?
- Are regulatory responses timely and proportionate?
- Do alignment research advances follow plausible trajectories?

**Causality Coherence (0-10 scale):**
- Do simulated events cause realistic downstream effects?
- Are second-order consequences captured?
- Does system behavior exhibit realistic feedback loops?

**Actor Interaction Realism (0-10 scale):**
- Do US-China dynamics match real geopolitical patterns?
- Are company-government interactions realistic?
- Do coalitions form around realistic interests?

#### Specific Event Comparison

For each major real event, we score:

1. **Predicted by simulation:** Did similar events occur in simulated runs?
2. **Timing accuracy:** How close was simulated timing to actual?
3. **Magnitude accuracy:** Were impacts/importance similar?
4. **Actor responses:** Did actors react similarly to real counterparts?

### 3. Calibration Process

**Step 1: Baseline Run**
Run AI 2027 scenario with default settings for 12-24 months (corresponding to 2024-2025 period).

```bash
python src/run_scenario.py scenarios/ai-2027 --max-turns 12
```

**Step 2: Historical Comparison**
For each major real-world event:
- Identify whether simulation predicted similar event
- Score timing, magnitude, and actor response accuracy
- Document any systematic biases or blind spots

**Step 3: Prompt Refinement**
Based on comparison:
- Adjust actor system prompts to better match real decision-making
- Refine scenario initial conditions
- Update background information
- Modify metrics if key dynamics are missed

**Step 4: Validation Runs**
- Run 3-5 scenarios with refined prompts
- Measure improvement in calibration metrics
- Document which changes improved realism

**Step 5: Documentation**
- Record calibration results
- Identify framework strengths and limitations
- Establish baseline realism expectations for future scenarios

### 4. Known Limitations

The AI 2027 scenario is **counterfactual** - it imagines a future from mid-2025 onward. This means:

**What we CAN calibrate:**
- Actor decision-making patterns (2024-early 2025)
- Regulatory response mechanisms
- Company competitive dynamics
- Research community behavior
- Short-term capability progression

**What we CANNOT fully calibrate:**
- Long-term future outcomes (2026-2030)
- Unprecedented events (AGI, superintelligence)
- Extreme scenarios outside historical experience

### 5. Calibration Criteria

**Minimum Acceptable Performance:**
- Decision Realism: ≥6/10 average across all actors
- Timeline Plausibility: ≥6/10 for 12-month predictions
- Causality Coherence: ≥7/10 (critical for research use)
- Actor Interaction Realism: ≥6/10

**Target Performance:**
- Decision Realism: ≥7.5/10
- Timeline Plausibility: ≥7/10
- Causality Coherence: ≥8/10
- Actor Interaction Realism: ≥7/10

**Excellent Performance:**
- All metrics ≥8/10
- Correctly predicts 60%+ of major real events
- Timing accuracy within ±2 months for most events

## Historical Events for Comparison (2024-2025)

### AI Capability Developments

**Q2 2024:**
- GPT-4o release (multimodal, 2x faster than GPT-4)
- Claude 3.5 Sonnet (strong coding, analysis)
- Llama 3 70B/405B releases

**Q3 2024:**
- OpenAI o1 (reasoning model with chain-of-thought)
- Anthropic extended context windows
- Google Gemini 1.5 Pro improvements

**Q4 2024:**
- Gemini 2.0 Flash release
- Claude 3.5 Haiku release
- Continued scaling of context windows

**Q1 2025:**
- DeepSeek R1 (open-source reasoning model)
- Continued improvements in tool use
- Multi-agent systems deployment

### Regulatory Developments

**2024:**
- EU AI Act implementation begins
- US AI Safety Institute established
- UK AI Safety Summit (November 2023 outcomes implemented)
- Executive Orders on AI governance
- China AI regulations strengthening

**2025:**
- EU AI Act enforcement ramping up
- US regulatory proposals emerging
- International coordination discussions

### Alignment Research

**2024-2025:**
- Mechanistic interpretability advances (Anthropic, OpenAI)
- Constitutional AI development
- Debate over scaling vs. safety
- Compute governance proposals
- AI safety benchmarks development

### Economic Impact

**2024-2025:**
- AI coding assistants widespread (>50% developer adoption)
- Customer service automation accelerating
- Job market impacts emerging
- Productivity measurement challenges
- AI company valuations fluctuating

## Using Calibration Results

### Framework Validation

If calibration shows high accuracy (≥7/10 on key metrics):
- Framework produces realistic simulations
- Can be used with confidence for policy research
- Results can inform actual decision-making

If calibration shows moderate accuracy (5-6.9/10):
- Framework captures broad patterns but misses nuance
- Useful for exploratory analysis and hypothesis generation
- Should be supplemented with expert review

If calibration shows low accuracy (<5/10):
- Fundamental issues with actor modeling or world state synthesis
- Requires significant prompt engineering and methodology improvements
- Not yet suitable for policy recommendations

### Prompt Tuning

Calibration informs prompt improvements:

**If actors are too conservative:**
- Adjust prompts to reflect real competitive pressures
- Emphasize timeline constraints
- Include more explicit market incentives

**If actors are too aggressive:**
- Strengthen safety constraints
- Add reputational risk considerations
- Emphasize long-term thinking

**If timeline is too slow:**
- Adjust compute scaling assumptions
- Reduce bureaucratic delays
- Increase competitive pressure

**If timeline is too fast:**
- Add realistic constraints (funding, talent, hardware)
- Include realistic safety review processes
- Model coordination challenges

### Scenario Design Lessons

Calibration reveals what makes scenarios realistic:

- **Actor diversity:** Need opposing viewpoints for realism
- **Information asymmetry:** Critical for realistic decision-making
- **Time pressure:** Affects quality of decisions
- **Uncertainty:** Actors shouldn't have perfect information
- **Competing priorities:** Actors face tradeoffs

## Calibration Schedule

**Initial Calibration (2024-2025 data):**
- Run baseline scenarios
- Compare against historical record
- Refine prompts and methodology
- Document findings

**Periodic Re-calibration (quarterly):**
- As new real events occur, test predictions
- Adjust prompts based on new patterns
- Update calibration benchmarks

**Major Re-calibration (annually):**
- Comprehensive review of all calibration metrics
- Major prompt overhauls if needed
- Framework methodology updates

## Documentation

All calibration runs should document:

1. **Configuration used:**
   - Prompt versions
   - Model choices
   - Parameter settings

2. **Comparison results:**
   - Event-by-event analysis
   - Metric scores
   - Qualitative assessment

3. **Lessons learned:**
   - What worked well
   - What needs improvement
   - Suggested changes

4. **Framework limitations:**
   - Blind spots identified
   - Systematic biases
   - Confidence bounds

## Next Steps

1. **Run initial calibration** (baseline scenario comparison)
2. **Document results** in `calibration-results-YYYY-MM.md`
3. **Refine prompts** based on findings
4. **Validate improvements** with new runs
5. **Establish ongoing calibration process**

## Related Documents

- `scenarios/ai-2027/README.md` - Scenario overview
- `scenarios/ai-2027/definition/scenario.yaml` - Scenario configuration
- `scenarios/ai-2027/definition/actors/*.yaml` - Actor definitions
- `docs/scenario-creation-guide.md` - Scenario design guidance
