# Scenario Calibration Guide

This guide explains how to use calibration scenarios to validate the Scenario Lab framework's realism and identify areas for improvement.

## What is Scenario Calibration?

**Calibration** is the process of validating simulation realism by comparing simulated outcomes against known real-world events. It helps us:

- **Validate framework quality**: Ensure simulations produce realistic results
- **Identify blind spots**: Find what the framework misses or gets wrong
- **Tune prompts**: Improve actor and scenario prompts based on evidence
- **Set confidence bounds**: Know which results to trust and which to question
- **Guide research use**: Understand when simulations are suitable for policy analysis

## When to Use Calibration

**You should calibrate when:**
- Starting to use the framework for research
- After major framework changes
- Before using results for policy recommendations
- Periodically (quarterly/annually) to maintain quality

**You don't need to calibrate every scenario:**
- Exploratory "what-if" scenarios
- Teaching/demonstration scenarios
- Scenarios with no real-world comparison available

## AI 2027 as Calibration Scenario

The **AI 2027** scenario serves as Scenario Lab's primary calibration tool because:

1. **Recent events**: Covers 2024-2025 with known outcomes
2. **Well-documented**: Real AI developments are well-tracked
3. **Multiple actors**: Tests company, government, and researcher behavior
4. **Quantifiable metrics**: AI capabilities, regulations, etc. are measurable
5. **Policy-relevant**: Directly applicable to AI governance research

## Quick Start

### 1. Run Initial Calibration

```bash
# Run AI 2027 for 12 turns (1 year from mid-2024)
python src/run_scenario.py scenarios/ai-2027 --max-turns 12 --credit-limit 5.00

# Expected cost: ~$3-5 for 12 turns
# Expected time: ~15-30 minutes
```

### 2. Copy Results Template

```bash
# Create results file
cp scenarios/ai-2027/calibration-results-template.md \
   scenarios/ai-2027/calibration-results-2025-01.md
```

### 3. Fill In Comparison

Open `calibration-results-2025-01.md` and:
- Record your run information
- Compare each simulated event to real 2024 events
- Score decision realism, timeline accuracy, etc.
- Document findings

### 4. Calculate Scores

For each comparison dimension, score 0-10:
- **10**: Perfect match to reality
- **8-9**: Very close, minor differences
- **6-7**: Broadly correct, some inaccuracies
- **4-5**: Captures general pattern but significant errors
- **2-3**: Wrong direction or major misses
- **0-1**: Complete mismatch

### 5. Identify Improvements

Based on scores:
- **<6/10**: Significant prompt refinement needed
- **6-7/10**: Good baseline, targeted improvements
- **>7/10**: High quality, minor tuning only

## Detailed Calibration Process

### Step 1: Select Time Period

Choose a period with:
- Known outcomes (recent past)
- Sufficient events for comparison (at least 5-10 major events)
- Relevance to your research questions

**For AI 2027:**
- Use January 2024 - January 2025 (12 months, 12 turns)
- Covers major model releases, regulatory developments, research advances

### Step 2: Run Baseline Simulation

Run without modifications to prompts:

```bash
python src/run_scenario.py scenarios/ai-2027 \
  --max-turns 12 \
  --credit-limit 5.00 \
  --output-dir scenarios/ai-2027/calibration-runs/baseline-2025-01
```

**Important settings:**
- Use default prompts (don't tune yet)
- Enable validation if available
- Track all metrics
- Save complete outputs

### Step 3: Gather Real Events

For your chosen time period, compile:

**AI Capability Milestones:**
- Model releases (GPT-4o, Claude 3.5, o1, etc.)
- Capability benchmarks achieved
- Performance improvements

**Policy/Regulatory:**
- New regulations or enforcement actions
- Government AI initiatives
- International agreements or tensions

**Research Advances:**
- Published alignment research
- Safety technique breakthroughs
- Scaling laws discoveries

**Economic Impact:**
- Adoption metrics
- Job market changes
- Productivity data

**Sources:**
- Company announcements (OpenAI, Anthropic, etc.)
- Government press releases
- Academic publications
- News coverage from reputable outlets

### Step 4: Event-by-Event Comparison

For each major real event:

**1. Check if simulation predicted it:**
- Yes, very similar event: +3 points
- Yes, somewhat similar: +2 points
- Vaguely related event: +1 point
- Not predicted: 0 points

**2. Compare timing:**
- Within 1 month: +3 points
- Within 2 months: +2 points
- Within 3-4 months: +1 point
- Off by >4 months or not predicted: 0 points

**3. Compare magnitude:**
- Impact/importance very similar: +2 points
- Roughly similar magnitude: +1 point
- Very different or missing: 0 points

**4. Compare actor responses:**
- Reactions very similar to reality: +2 points
- Broadly similar reactions: +1 point
- Different or missing: 0 points

**Total per event:** 0-10 points

**Average across all events:** Overall calibration score

### Step 5: Actor Behavior Analysis

For each actor, assess:

**Decision quality:**
- Do decisions reflect real counterpart's priorities?
- Are reasoning patterns realistic?
- Do they miss obvious considerations?

**Behavioral patterns:**
- Risk tolerance matches reality?
- Time horizons appropriate?
- Competitive vs. cooperative balance realistic?

**Blind spots:**
- What do they consistently miss?
- What do they overemphasize?

### Step 6: Prompt Refinement

Based on comparison, refine prompts:

**If actors are too risk-averse:**
```yaml
# Add to actor prompt:
- You face significant competitive pressure from [competitors]
- Delays cost you market share and investor confidence
- Your board expects aggressive timelines
```

**If actors ignore safety:**
```yaml
# Add to actor prompt:
- You are deeply concerned about long-term safety risks
- Your alignment team has raised serious concerns
- You must balance speed with responsible development
```

**If timeline too slow:**
```yaml
# Adjust scenario initial state:
- Breakthrough in [technology] has accelerated timelines
- Compute costs have dropped faster than expected
- Competitive pressure has intensified
```

**If timeline too fast:**
```yaml
# Add realistic constraints:
- Talent shortage limiting parallel development
- Hardware delivery delays
- Safety review processes taking longer
```

### Step 7: Validation Run

After refinements:

```bash
python src/run_scenario.py scenarios/ai-2027 \
  --max-turns 12 \
  --output-dir scenarios/ai-2027/calibration-runs/refined-2025-01
```

Compare improvement:
- Did calibration scores increase?
- Were specific issues addressed?
- Did new problems emerge?

### Step 8: Documentation

Record in calibration results file:

**1. Executive Summary:**
- Overall score and assessment
- Key findings
- Recommended actions

**2. Detailed Comparison:**
- Event-by-event analysis
- Actor behavior assessment
- Timeline accuracy

**3. Lessons Learned:**
- What works well
- What needs improvement
- Framework limitations

**4. Action Items:**
- Prompt changes to implement
- Metrics to add/modify
- Future calibration plans

## Interpreting Calibration Scores

### Overall Calibration Score

**8-10/10: Excellent**
- Framework produces highly realistic simulations
- Suitable for policy research and recommendations
- Minor refinements only

**Characteristics:**
- Predicts 70%+ of major events
- Timing accurate within ±1 month average
- Actor decisions closely match real counterparts
- Causal chains are realistic

**Use cases:**
- Policy analysis and recommendations
- Strategic planning
- Research publications

**6-7.9/10: Good**
- Framework captures broad patterns reliably
- Useful for research with expert review
- Some areas need improvement

**Characteristics:**
- Predicts 50-70% of major events
- Timing accurate within ±2 months average
- Actor decisions generally realistic
- Some systematic biases present

**Use cases:**
- Exploratory policy analysis
- Hypothesis generation
- Teaching and demonstration
- With expert interpretation

**4-5.9/10: Fair**
- Framework shows promise but significant gaps
- Requires substantial expert interpretation
- Major refinements needed

**Characteristics:**
- Predicts 30-50% of major events
- Timing often off by 3+ months
- Actor decisions partially realistic
- Notable blind spots

**Use cases:**
- Internal research only
- Framework development
- Not for external recommendations

**<4/10: Poor**
- Framework not yet suitable for research
- Fundamental issues need addressing
- Extensive refinement required

**Characteristics:**
- Predicts <30% of events
- Poor timing accuracy
- Unrealistic actor behavior
- Major blind spots

**Use cases:**
- Framework debugging
- Methodology development
- Proof-of-concept only

### Component-Specific Scores

Even with overall good calibration, some components may need work:

**Actor-specific issues:**
- Specific actor consistently unrealistic
- → Refine that actor's prompts
- → Consider different LLM model

**Timeline issues:**
- Events happen too fast/slow
- → Adjust scenario pacing
- → Modify initial conditions

**Causality problems:**
- Events don't follow realistically from actions
- → Improve world state synthesis
- → Use better world state model

**Interaction issues:**
- Actor relationships unrealistic
- → Add explicit relationship dynamics
- → Model power dynamics better

## Common Calibration Findings

### Finding 1: Actors Too Cautious

**Symptoms:**
- AI development slower than reality
- Excessive safety measures
- Conservative timelines

**Fixes:**
- Add competitive pressure language
- Emphasize market incentives
- Include board/investor expectations
- Reduce safety emphasis (if overweight)

### Finding 2: Actors Too Aggressive

**Symptoms:**
- Reckless development speed
- Ignoring safety concerns
- Unrealistic risk-taking

**Fixes:**
- Strengthen safety culture
- Add reputational risk considerations
- Include past incidents in background
- Emphasize long-term thinking

### Finding 3: Missing Second-Order Effects

**Symptoms:**
- Events happen in isolation
- No cascading consequences
- Unrealistic stability

**Fixes:**
- Improve world state synthesis prompts
- Use more capable world state model
- Add explicit feedback loops to scenario

### Finding 4: Weak Actor Interactions

**Symptoms:**
- Actors operate independently
- No realistic competition/cooperation
- Missing coalitions

**Fixes:**
- Enable bilateral communication
- Enable coalition formation
- Add explicit relationship dynamics
- Model information asymmetry

### Finding 5: Timeline Compression/Expansion

**Symptoms:**
- All events happen too fast/slow
- Unrealistic pacing

**Fixes:**
- Adjust turn duration
- Modify initial compute/capability levels
- Add/remove bottlenecks
- Calibrate against real development timelines

## Advanced Calibration Techniques

### Batch Calibration

Run multiple calibration scenarios with variations:

```yaml
# calibration-batch-config.yaml
experiment_name: "AI 2027 Calibration Batch"
base_scenario: "scenarios/ai-2027"

runs_per_variation: 5  # For statistical significance

variations:
  - type: "actor_model"
    actor: "openbrain-ceo"
    values: ["openai/gpt-4o", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"]

budget_limit: 50.00
```

```bash
python src/batch_runner.py calibration-batch-config.yaml
```

**Benefits:**
- Test model sensitivity
- Identify robust vs. fragile results
- Statistical confidence in scores

### Temporal Calibration

Test different time horizons:

```bash
# Short-term (3 months)
python src/run_scenario.py scenarios/ai-2027 --max-turns 3

# Medium-term (6 months)
python src/run_scenario.py scenarios/ai-2027 --max-turns 6

# Long-term (12 months)
python src/run_scenario.py scenarios/ai-2027 --max-turns 12
```

**Findings:**
- Does accuracy degrade over time?
- What's the reliable prediction horizon?
- When do simulations diverge from reality?

### Cross-Scenario Validation

After calibrating AI 2027, test on other scenarios:

- **Different domains**: Climate policy, cybersecurity
- **Different time periods**: Historical events
- **Different scales**: 2 actors vs. 7 actors

**Purpose:**
- Does framework generalize?
- Are improvements scenario-specific?
- What are universal vs. domain-specific issues?

## Ongoing Calibration

### Quarterly Updates

Every 3 months:

1. **Run new calibration** against recent events
2. **Compare to previous calibrations** - improving or degrading?
3. **Update prompts** based on new patterns
4. **Document trends** - what's changing over time?

### Annual Comprehensive Review

Once per year:

1. **Full re-calibration** across multiple scenarios
2. **Methodology review** - framework changes needed?
3. **Prompt library update** - capture learning
4. **Publication** - share findings with community

## Using Calibration Results

### For Research

**High calibration (>7/10):**
- ✓ Cite simulations in research papers
- ✓ Use for policy recommendations
- ✓ Present to stakeholders
- Note limitations in methods section

**Medium calibration (5-7/10):**
- ⚠ Use for hypothesis generation
- ⚠ Require expert review
- ⚠ Do not make strong claims
- Clearly communicate uncertainty

**Low calibration (<5/10):**
- ✗ Do not use for external research
- ✗ Internal development only
- Focus on improvement

### For Framework Development

Calibration guides improvements:

**Priority 1: Fix issues causing <6/10 scores**
- These are critical for basic realism

**Priority 2: Address 6-7/10 components**
- Get these to >7/10 for research use

**Priority 3: Refine >7/10 components**
- Polish for excellence

## Troubleshooting

### "My calibration scores are very low (<4/10)"

**Possible causes:**
- Prompts fundamentally misaligned
- Wrong LLM models chosen
- Scenario initial conditions unrealistic
- Framework bug or configuration error

**Actions:**
1. Check logs for errors
2. Review prompt-reality alignment
3. Try different models
4. Consult example scenarios
5. Request help from framework maintainers

### "Scores vary wildly between runs"

**Possible causes:**
- High LLM temperature
- Scenario has multiple valid paths
- Insufficient prompt constraints
- Stochastic events dominating

**Actions:**
1. Check temperature settings
2. Run batch (5-10 runs) for averaging
3. Tighten prompt constraints
4. Add more structure to scenario

### "Good overall scores but one actor terrible"

**Possible causes:**
- That actor's prompt poorly designed
- Wrong model for that role
- Missing critical context
- Unrealistic goals/constraints

**Actions:**
1. Focus refinement on that actor
2. Try premium model
3. Add domain expertise
4. Consult subject matter experts

## Resources

### Templates
- `scenarios/ai-2027/calibration-results-template.md` - Results documentation
- `scenarios/ai-2027/CALIBRATION.md` - Methodology details

### Existing Calibrations
- `scenarios/ai-2027/calibration-results-*.md` - Past calibration runs

### Related Guides
- `docs/scenario-creation-guide.md` - Creating calibration scenarios
- `docs/batch-execution-guide.md` - Running batch calibrations

### Support
- Open an issue for calibration questions
- Share calibration results with community
- Contribute improvements

## Next Steps

1. **Run your first calibration** following Quick Start
2. **Document findings** using results template
3. **Refine prompts** based on comparison
4. **Validate improvements** with new run
5. **Share results** to help improve framework

Good calibration is the foundation of trustworthy simulations. Take time to do it thoroughly!
