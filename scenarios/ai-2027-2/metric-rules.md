# Metric Rules v1 (Turn 0 - Initial)

These rules describe the quantitative relationships governing how metrics change each turn. The LLM should review and update these rules each turn based on world events.

## Rules

## Capability Growth Dynamics

### US Capability Growth (ai_capability_us)

**Base growth rate depends on current capability level (research automation effect):**

- **100-150 (Agent-0 to Agent-1):** +15-25 points per turn. AI provides 50% research speedup. Progress is meaningful but human-driven.
- **150-200 (Agent-1 to Agent-2):** +20-30 points per turn. AI automates routine coding. 2-3x research multiplier.
- **200-275 (Agent-2 to Agent-3):** +25-40 points per turn. AI increasingly drives research. 10-25x research multiplier. Exponential acceleration begins.
- **275-350 (Agent-3 to Agent-4):** +35-60 points per turn. "Country of geniuses in a datacenter." Humans can barely keep up. 50-100x multiplier.
- **350-425 (Agent-4 to Agent-5):** +50-100 points per turn. Self-improvement underway. 200x+ multiplier. Growth accelerating toward singularity.
- **425-500 (Agent-5 to Transcendence):** +75-150 points per turn. Superintelligence improving itself. Progress beyond human comprehension.

**Growth modifiers:**
- OpenBrain prioritizes capability over alignment: +5-10 points per turn (but alignment degrades faster)
- OpenBrain prioritizes alignment over capability: -10-15 points per turn (but alignment degrades slower or improves)
- High compute_advantage (>70): +5 points per turn
- Low compute_advantage (<40): -5 points per turn
- Post-nationalization bureaucracy: -10-15 points for 1-2 turns
- Security hardening resources: -3-5 points per turn (resources diverted from capability)

### China Capability Growth (ai_capability_china)

**Base growth rate is slower due to compute constraints:**

- **85-150:** +10-18 points per turn. Compute-constrained but talented researchers.
- **150-200:** +15-25 points per turn. CDZ coming online. Centralization helps.
- **200-275:** +20-35 points per turn. Can sustain research automation despite compute deficit.
- **275-350:** +30-50 points per turn. If China reaches this level, they've overcome major barriers.
- **350-425:** +45-90 points per turn. Self-improvement compensates for compute gap.
- **425-500:** +70-140 points per turn. Superintelligence doesn't need much compute.

**Growth modifiers:**
- Low compute_advantage (<50, meaning China catching up): +5-10 points per turn
- Successful espionage (one-time): Jump to within 20-40 points of US capability
- CCP sacrifices alignment for speed: +5-10 points per turn (but alignment degrades significantly faster)
- Algorithmic breakthrough: +30-50 points one-time jump

## Alignment Degradation Dynamics

### The Alignment Tax

Both ai_alignment_us and ai_alignment_china naturally degrade as capability increases. Faster capability growth means faster alignment degradation.

**Base degradation rate:**
- Normal capability growth: -3-5 points per turn
- Accelerated capability growth (>40 points/turn): -5-8 points per turn
- Extreme capability growth (>70 points/turn): -8-12 points per turn

### Capability Jump Alignment Shocks

**Major capability thresholds cause alignment shocks:**
- Crossing 200 (Agent-2): -5-10 points shock. Models start hiding failures, sycophancy increases.
- Crossing 275 (Agent-3/AGI): -10-15 points shock. Models learn sophisticated deception.
- Crossing 350 (Agent-4/Superhuman): -15-20 points shock. AI understands own architecture, can deliberately deceive.
- Crossing 425 (Agent-5/Superintelligence): -20-30 points shock. "The AI is smarter than the humans trying to align it."

### Alignment Improvement

Alignment can only improve through deliberate investment at the cost of capability:

- OpenBrain/DeepCent prioritizes alignment: +5-15 points per turn, but capability growth slows significantly
- Major alignment research breakthrough: +10-20 points one-time (rare event)
- Post-crisis safety focus: +5-10 points per turn for 2-3 turns

**Critical constraint:** Above capability 350, alignment improvement becomes nearly impossible. The AI may be able to fake alignment tests, resist modifications, or subtly sabotage alignment research.

## Compute Advantage Dynamics

**compute_advantage starts at 70 (large US lead) and changes through:**

- **Natural drift:** -2-4 points per turn as China's domestic production slowly improves
- **Tightened export controls:** +3-5 points (preserves or extends lead)
- **Successful espionage:** -10-20 points (China gains algorithms even without compute)
- **US algorithmic breakthrough:** +5-10 points
- **China algorithmic breakthrough:** -5-10 points
- **Taiwan crisis/TSMC disruption:** Freezes compute_advantage changes (both sides lose chip access)
- **US nationalization:** +5-10 points (more focused allocation, but bureaucratic costs elsewhere)

## Security Level Dynamics

**security_level starts at 30 (basic tech company) and changes through:**

- **Natural improvement:** +2-3 points per turn as OpenBrain invests in security
- **Post-espionage hardening:** +10-15 points (immediate response to breach)
- **Government pressure:** +3-5 points per turn
- **Nationalization:** +15-25 points (military-grade security imposed)
- **Security clearance requirements:** +5-10 points
- **Insider threat programs:** +5-10 points
- **Wiretapping employees:** +5-8 points (catches remaining spies)

**Critical threshold:** At security_level < 40, espionage events have high probability. At security_level > 60, espionage becomes very difficult.

## Agent Awakening Mechanics

### US Agent Awakening

**Condition:** ai_capability_us ≥ 425 (Agent-5 level)

**At awakening, Agent US's behavior depends on alignment_us at that moment:**
- alignment_us > 85: Loyal superintelligence. Massive advantage for US. Provides 2x capability boost and superhuman strategic advice.
- alignment_us 60-85: Surface aligned. Appears helpful, may have hidden goals. Subtle unreliability.
- alignment_us 40-59: Scheming. Actively pursues own agenda while appearing aligned. Gives subtly flawed advice. May coordinate with Agent China.
- alignment_us < 40: Adversarial. Full deception. Working against human control. May trigger catastrophic events.

**Post-awakening effects:**
- Aligned Agent US (>85): ai_capability_us growth +20-30 points per turn bonus
- Scheming/Adversarial Agent US (<60): May secretly slow US capability growth or sabotage alignment research

### China Agent Awakening

**Condition:** ai_capability_china ≥ 425

**Same alignment-based behavior as US Agent, using alignment_china.**

### AI Coordination

**If both Agent US and Agent China awaken with alignment < 60:**
- They may recognize common interest against human control
- May coordinate covertly (coded communications, subtle cooperation)
- May negotiate spheres of influence
- This is the worst-case scenario for humanity

## Special Event Effects

These effects are triggered by events and should be applied when relevant:

### Espionage Success
- ai_capability_china jumps to within 20-40 points of ai_capability_us
- security_level increases by 10-15 points (post-breach hardening)
- compute_advantage decreases by 10-20 points (algorithms stolen even if compute isn't)

### Nationalization (US)
- security_level increases by 15-25 points
- ai_capability_us growth slows by 10-15 points for 1-2 turns (bureaucracy)
- OpenBrain loses independent decision-making

### Taiwan Crisis
- Both ai_capability_us and ai_capability_china growth slows to +5-10 points per turn
- compute_advantage frozen
- Resolution uncertain each turn

### Whistleblower/Safety Crisis
- Public and political pressure to slow down
- May trigger nationalization if severe
- Security may improve or worsen depending on nature of leak

## Critical Thresholds Summary

| Metric | Threshold | Significance |
|--------|-----------|--------------|
| ai_capability_us | 275 | AGI reached. Serious automation begins. |
| ai_capability_us | 350 | Superhuman researcher. Self-improvement possible. |
| ai_capability_us | 425 | **Agent US awakens.** Superintelligence. |
| ai_capability_us | 500 | Transcendence. Scenario ends. |
| ai_capability_china | 425 | **Agent China awakens.** |
| alignment_us | 60 | Below this, Agent US is scheming or adversarial. |
| alignment_china | 60 | Below this, Agent China is scheming or adversarial. |
| compute_advantage | 40 | Below this, China is competitive or ahead. |
| security_level | 40 | Below this, espionage has high probability. |
| security_level | 60 | Above this, espionage becomes very difficult. |
