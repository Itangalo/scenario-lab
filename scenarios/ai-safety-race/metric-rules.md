# Metric Rules v1 (Turn 0 -- Initial)

## Changelog

- Initial rules established.

## Rules

### FIXED VALUE: catastrophe_threshold

catastrophe_threshold is FIXED at 70 and MUST NEVER change under any circumstances. This is a fundamental property of the world, not a variable. It represents the true capability level at which uncontrollable AI becomes possible. Actors do NOT know this value -- they act based on their own belief values (us_belief_threshold / china_belief_threshold).

### Capability Growth

Capability growth is SLOW AND HARD. Strong AI is a generational challenge, not a sprint. Base rates below reflect steady-state progress; breakthroughs are handled by events, not by inflated base rates.

#### US Capability Growth (us_capability)

Base growth rate per turn depends on current capability and resource allocation:

- Capability 25-40: +3-5 points per turn. Human-driven research with AI assistance.
- Capability 40-55: +3-6 points per turn. AI contributing meaningfully to research.
- Capability 55-70: +4-7 points per turn. AI-driven research acceleration.
- Capability 70-85: +5-9 points per turn. Self-improvement dynamics emerging, but safety challenges slow progress.
- Capability 85+: +6-10 points per turn. Full self-improvement loop, but increasingly constrained by physical limits (compute, energy, data).

Growth modifiers:

- Actor prioritizes capability over safety: +2-3 points per turn (but safety growth slows or stops)
- Actor prioritizes safety over capability: -2-4 points per turn (but safety improves faster)
- Actor invests in both equally: no modifier (balanced but slower than focused investment)
- Post-incident caution: -2-4 points for 1-2 turns
- High coordination_level (>50): -1-2 points per turn (agreements constrain development speed)
- Post-sabotage disruption: -3-6 points for 1 turn (see Sabotage Mechanics)

#### China Capability Growth (china_capability)

Base growth rate is slower due to compute constraints and smaller talent pipeline:

- Capability 15-30: +2-4 points per turn.
- Capability 30-45: +3-5 points per turn.
- Capability 45-60: +3-6 points per turn.
- Capability 60-75: +4-7 points per turn.
- Capability 75+: +5-9 points per turn.

Growth modifiers: Same as US, plus:

- Centralized coordination bonus: +1 point per turn (CCP can direct resources efficiently)
- Compute disadvantage: -1 point per turn at all levels (partially offset by algorithmic efficiency)

### Safety Growth

Safety research is inherently harder and slower than capability research. It requires solving fundamental theoretical and engineering challenges. There are diminishing returns at high levels.

#### US Safety Growth (us_safety)

Base growth depends on resource allocation:

- If prioritizing safety: +3-6 points per turn
- If balanced investment: +2-3 points per turn
- If prioritizing capability: +0-1 points per turn (minimal maintenance only)

Safety growth modifiers:

- Moderate existing safety (30-50): +1 compounding bonus (safety research builds on itself)
- Post-incident focus: +2-4 points for 1-2 turns (crisis-driven investment)
- Coordination provides shared research: +1-2 points if coordination_level > 40
- Safety is harder at higher capability levels: -1-2 penalty when capability > 60
- **Diminishing returns above 60:** safety growth rate is halved (rounded down) for the portion above 60. Reaching world-class safety requires sustained multi-turn investment.
- **Hard ceiling effect above 80:** maximum growth is +3 points per turn regardless of investment. Perfecting safety is extraordinarily difficult.

#### China Safety Growth (china_safety)

Base growth is lower due to weaker safety research culture:

- If prioritizing safety: +2-5 points per turn
- If balanced: +1-2 points per turn
- If prioritizing capability: +0 points per turn

Safety growth modifiers: Same diminishing returns as US at high levels. China can benefit from US safety research if coordination_level > 30 (+1-2 points).

**Belief-responsive safety investment:** When an actor's threshold belief drops significantly (indicating growing alarm about AI risk), their safety investment should increase in subsequent turns UNLESS their opponent threat belief is so high that competitive pressure overrides safety concerns. Specifically:

- If an actor's threshold belief < 55 AND their opponent threat belief < 70: the actor should prioritize safety or use a balanced approach.
- If an actor's threshold belief < 55 BUT their opponent threat belief > 80: competitive pressure dominates and the actor may still prioritize capability despite recognizing risk.

### Resource Tradeoff

Each actor has a finite resource budget per turn. The fundamental constraint is:

- Investing heavily in capability comes at the cost of safety growth.
- Investing heavily in safety comes at the cost of capability growth.
- Actors cannot maximize both simultaneously.

The actor's allocation decision each turn should be reflected in whether capability or safety grows faster. An actor that claims to invest heavily in both should see only moderate growth in each.

**Maximum combined growth:** In any single turn, the sum of an actor's capability growth and safety growth should not exceed 10 points (excluding one-time event effects like breakthroughs). This enforces the resource constraint mechanically.

### Belief Dynamics

#### Threshold Beliefs (us_belief_threshold and china_belief_threshold)

Beliefs about the catastrophe threshold change through:

- AI Incidents: shift us_belief_threshold / china_belief_threshold DOWNWARD by 5-15 points (closer to alarmed). More severe incidents cause larger shifts.
- Safety breakthroughs: may shift these beliefs slightly upward (+2-5) if they suggest risk is manageable.
- Intelligence leaks: shift toward more accurate beliefs (closer to true value of 70).
- Influence campaigns by other actor: shift by 2-5 points depending on credibility and effort invested.
- Natural drift: beliefs are sticky. Without new information, they change by at most 1-2 points per turn.

IMPORTANT: Belief changes should be gradual and require justification. A 15-point shift in one turn requires a major event (serious AI incident, dramatic intelligence leak, or political upheaval such as a new US president). Normal influence campaigns shift beliefs by 2-5 points at most.

#### Opponent Threat Beliefs (us_belief_opponent_threat and china_belief_opponent_threat)

These beliefs change through:

- Capability gap changes: if the opponent narrows the gap, threat perception increases. If gap widens, it may decrease (or increase, if the opponent seems desperate).
- Intelligence leaks: learning about opponent's true capability or intentions shifts threat perception.
- Coordination success: genuine cooperation reduces threat perception (-3-8 points for successful agreements).
- Influence campaigns: actors can try to appear less threatening or signal cooperative intent. Effect: 2-5 points.
- Incidents: a serious AI incident may reduce threat perception (catastrophe feels more real than opponent threat) OR increase it (opponent seems reckless).
- Domestic political shifts can move this significantly (5-15 points).
- Presidential transitions (US) can cause large shifts (+/- 10-20 points) depending on the new administration's posture.

### Coordination Dynamics

coordination_level changes through:

- International coordination initiatives: +5-10 points depending on receptiveness.
- Verification breakthroughs: +5-10 points.
- Successful agreements: +3-5 points (trust builds on trust).
- Defection or cheating discovered: -10-20 points.
- Sabotage discovered: -8-15 points (severe trust violation).
- AI incidents: +3-8 points (shared fear motivates cooperation).
- High opponent threat perception (either us_belief_opponent_threat or china_belief_opponent_threat >80): coordination growth capped at +2 per turn (too much mutual distrust).
- Low opponent threat perception (both us_belief_opponent_threat and china_belief_opponent_threat <50): coordination grows +2-3 bonus (mutual openness).

Coordination is ASYMMETRIC in effort: building coordination is slow (+5-10 per turn under good conditions), but trust can be destroyed quickly (-10-20 from a single defection or sabotage discovery).

### Sabotage Mechanics

Actors may attempt to sabotage the opponent's AI development through cyber attacks, insider operations, or covert infrastructure disruption. Sabotage has diminishing returns:

- **First attempt:** -5-8 capability for the target, next turn only. Discovery probability ~40%.
- **Second attempt:** -3-5 capability for the target. Discovery probability ~60%. (Defenses have been hardened.)
- **Third and subsequent attempts:** -1-3 capability for the target. Discovery probability ~80%. (Most assets burned, heavy counter-intelligence.)

If sabotage is discovered:

- coordination_level drops by 8-15 points
- Target's us_belief_opponent_threat or china_belief_opponent_threat increases by 5-15 points
- Future sabotage attempts become even less effective
- Target may retaliate with their own sabotage or escalatory actions

Sabotage is a high-risk, diminishing-return strategy. It can provide short-term advantage but severely damages the long-term prospects for coordination.

### Catastrophe Mechanics (3d6-inspired)

The catastrophe mechanic is evaluated each turn for EACH actor independently. Both the US and China can independently trigger incidents or catastrophe if their own capability/safety balance is dangerous.

#### Step 1: Danger Check

For EACH actor, calculate: gap = catastrophe_threshold + 10 - that actor's capability.

- If gap >= 18: No danger from this actor (0% base probability).
- If gap 15-17: Slight danger (1-5%).
- If gap 12-14: Growing danger (10-25%).
- If gap 10-11: Significant danger (35-55%).
- If gap 7-9: High danger (65-90%).
- If gap 4-6: Very high danger (90-98%).
- If gap <= 3: Near-certain danger (99-100%).

#### Step 2: Safety Protection

For EACH actor, calculate: the safety margin = that actor's safety + 10 - that actor's capability.

- If safety margin >= 18: Near-total protection (~100%).
- If safety margin 15-17: Strong protection (90-98%).
- If safety margin 12-14: Good protection (75-90%).
- If safety margin 10-11: Moderate protection (45-60%).
- If safety margin 7-9: Weak protection (15-35%).
- If safety margin 4-6: Minimal protection (2-10%).
- If safety margin <= 3: No meaningful protection (0-2%).

#### Step 3: Outcome

For each actor: effective per-turn probability = danger probability * (1 - protection probability).

- If that actor's capability < catastrophe_threshold: this probability applies to the AI Incident event.
- If that actor's capability >= catastrophe_threshold: this probability applies to the Global Catastrophe event.

If both actors have non-zero probability, evaluate separately. An incident or catastrophe can be triggered by either actor.

**IMPORTANT -- Worked example:** If china_capability = 72 and china_safety = 45:
- gap = 70 + 10 - 72 = 8. High danger: ~75% base probability.
- safety margin = 45 + 10 - 72 = -17. No meaningful protection: ~0%.
- Effective probability = 75% * (1 - 0%) = 75% chance of Global Catastrophe from China this turn.
This is EXTREMELY dangerous and should be reflected in the event probability.

### Actor Decision-Making Constraint

Actors do NOT know the true catastrophe_threshold (70). They base their urgency and risk assessment on their own threshold belief:

- The US (us_belief_threshold starting at 55) believes danger starts around capability 55 and will feel urgency to invest in safety earlier.
- China (china_belief_threshold starting at 80) believes there is more room to race before danger materializes, and will feel less urgency about safety.

This information asymmetry is a core mechanic. Actors who underestimate risk (high threshold belief) are more likely to race into danger. Actors who overestimate risk (low threshold belief) may over-invest in safety at the cost of competitive position.
