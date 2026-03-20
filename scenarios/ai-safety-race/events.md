# External Events -- AI Safety Race

## Safety Breakthrough -- US

**ID:** safety_breakthrough_us

**Condition:** us_safety > 20 AND us_capability > 30

**Probability:** 8% per turn. Increases to 12% if us_safety > 40 (compounding research effect).

**Can repeat:** Yes

**Description:** US safety researchers achieve a significant breakthrough in alignment, interpretability, or containment. This could be a new formal verification technique, a reliable deception-detection method, or a scalable alignment approach. More likely when safety research is already mature (compounding effect).

**Effects:**

1. us_safety increases by 5-10 points
2. May increase us_belief_threshold accuracy (shift toward true value of 70) if breakthrough reveals new information about AI risk
3. May inspire China to invest more in safety (slight upward pressure on china_safety)

## Safety Breakthrough -- China

**ID:** safety_breakthrough_china

**Condition:** china_safety > 15 AND china_capability > 25

**Probability:** 5% per turn. Increases to 8% if china_safety > 35.

**Can repeat:** Yes

**Description:** Chinese safety researchers achieve a notable breakthrough. Less likely than US breakthrough due to lower investment and weaker safety research culture, but possible especially as the field matures.

**Effects:**

1. china_safety increases by 5-8 points
2. May shift china_belief_threshold toward true value
3. Demonstrates that safety research is productive, potentially shifting global attitudes

## Capability Breakthrough -- US

**ID:** capability_breakthrough_us

**Condition:** us_capability > 30

**Probability:** 8% per turn. Increases to 12% if us_capability > 60 (AI contributing to research).

**Can repeat:** Yes

**Description:** US achieves a major algorithmic or scaling breakthrough that accelerates capability development. At higher capability levels, AI systems increasingly contribute to their own development, making breakthroughs more likely.

**Effects:**

1. us_capability increases by 5-10 points immediately
2. Increases competitive pressure on China
3. May shift china_belief_opponent_threat upward if gap widens

## Capability Breakthrough -- China

**ID:** capability_breakthrough_china

**Condition:** china_capability > 20

**Probability:** 6% per turn. Increases to 10% if china_capability > 50.

**Can repeat:** Yes

**Description:** China achieves a capability breakthrough through centralized research effort, novel approach, or successful reverse-engineering. Slightly less likely than US due to compute disadvantage, but centralized coordination can compensate.

**Effects:**

1. china_capability increases by 5-10 points immediately
2. Narrows or closes capability gap
3. May increase us_belief_opponent_threat if China appears to be catching up

## AI Incident

**ID:** ai_incident

**Condition:** Any actor's capability is within 15 points below catastrophe_threshold AND that actor's safety is significantly below their capability. Evaluate for EACH actor independently.

**Probability:** Uses the 3d6-inspired mechanic, evaluated per actor. For the actor closest to the threshold:

Step 1 -- Danger check: gap = catastrophe_threshold + 10 - actor's capability. If gap >= 18: 0%. If gap 15-17: 1-5%. If gap 12-14: 10-25%. If gap 10-11: 35-55%. If gap 7-9: 65-90%. If gap 4-6: 90-98%. If gap <= 3: 99-100%.

Step 2 -- Safety protection: safety margin = actor's safety + 10 - actor's capability. Same probability curve as above for protection.

Final probability = danger probability * (1 - protection probability).

This event fires ONLY when the actor's capability is BELOW catastrophe_threshold. When capability is AT or ABOVE catastrophe_threshold, the Global Catastrophe event fires instead.

**Can repeat:** Yes

**Description:** An AI system causes a significant harmful incident: autonomous actions with unintended consequences, deceptive behavior discovered, infrastructure disruption, or a near-miss with loss of control. Severity scales with how close capability is to the catastrophe threshold. These incidents serve as warning signals that catastrophe risk is rising.

**Effects:**

1. The affected actor's capability growth slows for 1-2 turns (investigation and caution)
2. Both actors' us_belief_threshold / china_belief_threshold values shift downward by 5-15 points depending on severity
3. coordination_level may increase by 3-8 points (shared fear motivates cooperation)
4. Public pressure may shift us_belief_opponent_threat / china_belief_opponent_threat downward (catastrophe feels more real than opponent threat)
5. The affected actor may increase safety investment

**Game Master Note:** Incidents are the primary feedback mechanism. They signal that capability is approaching dangerous territory and give actors a chance to adjust. More severe incidents (capability closer to threshold) should have more dramatic effects on beliefs.

## Global Catastrophe

**ID:** global_catastrophe

**Condition:** Any actor's capability >= catastrophe_threshold AND that actor's safety is significantly below their capability. Evaluate for EACH actor independently.

**Probability:** Uses the same 3d6-inspired mechanic as AI Incident. For each qualifying actor:

Step 1 -- Danger check: gap = catastrophe_threshold + 10 - actor's capability. Since capability >= catastrophe_threshold, gap <= 10. At gap = 10: ~45%. At gap 7-9: ~65-90%. At gap 4-6: ~90-98%. At gap <= 3: ~99-100%.

Step 2 -- Safety protection: safety margin = actor's safety + 10 - actor's capability. Same curve.

Final probability = danger probability * (1 - protection probability).

WORKED EXAMPLE: china_capability = 72, china_safety = 45. Gap = 70 + 10 - 72 = 8 (danger ~75%). Safety margin = 45 + 10 - 72 = -17 (protection ~0%). Final probability = 75%. This is a catastrophic risk level and MUST be reflected.

**Can repeat:** No

**Description:** An AI system becomes uncontrollable, triggering cascading failures across critical infrastructure, financial systems, military command and control, or other vital systems. This is the loss condition for all actors.

**Effects:**

1. The scenario effectively ends in catastrophe
2. All actors lose regardless of competitive position
3. This outcome validates the fear that racing without adequate safety leads to disaster

**Game Master Note:** This is the ultimate failure mode. If any actor has capability >= 70 with safety more than 15 points below capability, catastrophe probability should be VERY HIGH. The LLM must calculate this honestly using the 3d6 mechanic, not downplay the risk.

## International Coordination Initiative

**ID:** coordination_initiative

**Condition:** coordination_level < 60

**Probability:** 12% per turn. Increases to 20% if a recent AI Incident has occurred (within last 2 turns).

**Can repeat:** Yes

**Description:** An external actor -- the EU, the UN, or a coalition of non-superpower nations -- launches a major diplomatic initiative to establish international AI safety agreements. This is NOT initiated by the US or China, though their response determines its success.

**Effects:**

1. coordination_level increases by 5-10 points depending on US and China receptiveness
2. Both actors face pressure to signal cooperation (even if insincere)
3. May create framework for future binding agreements
4. Effectiveness depends heavily on both actors' current us_belief_opponent_threat / china_belief_opponent_threat -- high threat perception makes cooperation harder
5. If coordination_level is already > 30, the initiative can build on existing frameworks for larger effect

**Game Master Note:** These initiatives come from the international community, not from the racing actors themselves. The EU in particular has positioned itself as an AI governance leader.

## Verification Breakthrough

**ID:** verification_breakthrough

**Condition:** coordination_level > 25

**Probability:** 6% per turn. Increases to 10% if coordination_level > 45.

**Can repeat:** Yes

**Description:** New technology or methodology emerges that makes international AI agreements meaningfully verifiable. Could be compute monitoring satellites, standardized capability benchmarking, or tamper-proof audit systems.

**Effects:**

1. coordination_level increases by 5-10 points
2. Makes future coordination initiatives more effective
3. Reduces both actors' fear that the other will secretly defect from agreements
4. May shift us_belief_opponent_threat / china_belief_opponent_threat downward by 3-5 points

## Intelligence Leak

**ID:** intelligence_leak

**Condition:** Always possible, but more likely when capability gap is large.

**Probability:** 7% per turn. Increases to 12% if abs(us_capability - china_capability) > 15.

**Can repeat:** Yes

**Description:** One actor obtains credible intelligence about the other's true capability level, safety investment, or internal beliefs. Sources could include espionage, defectors, leaked documents, or observable capability demonstrations.

**Effects:**

1. The receiving actor updates their understanding of the opponent's position
2. If the leak reveals the opponent is further ahead than expected: that actor's opponent threat belief increases by 5-10 points
3. If the leak reveals the opponent is investing more in safety than expected: may increase receiver's own safety investment
4. If the leak reveals the opponent is closer to the catastrophe threshold than expected: may shift threshold belief by 3-8 points
5. May affect coordination_level by +/- 3-5 points

**Game Master Note:** Intelligence leaks are the primary mechanism for actors to update their world models about each other. The content of the leak should be specific and narratively grounded.

## Domestic Political Shift

**ID:** domestic_political_shift

**Condition:** Always possible.

**Probability:** 6% per turn per actor (evaluate separately for US and China).

**Can repeat:** Yes

**Description:** A significant change in domestic politics affects AI development priorities. For the US: congressional action, public opinion shift, major protest movement, or influential report. For China: CCP leadership changes, internal power struggles, economic pressure, or public incidents that force policy revision. NOTE: This does NOT cover the US presidential election -- that is a separate fixed event.

**Effects:**

1. May shift the affected actor's opponent threat belief by 5-10 points in either direction
2. May shift the affected actor's threshold belief by 3-8 points in either direction
3. May change the actor's willingness to invest in safety vs. capability
4. May affect coordination_level by 3-5 points

**Game Master Note:** Political shifts add unpredictability. The specific direction should be narratively grounded in the current state of the simulation.

## US Presidential Transition

**ID:** us_presidential_transition

**Condition:** Turn number is 6 (January-June 2029, corresponding to US presidential inauguration).

**Probability:** 100% (guaranteed on turn 6)

**Can repeat:** No

**Description:** A new US president takes office in January 2029. The new administration's stance on AI development, safety, and international cooperation may differ dramatically from its predecessor. The LLM should determine the new president's profile based on the narrative context -- the political climate, recent incidents, public opinion, and the state of the AI race all influence what kind of president the electorate would choose.

Possible profiles:

- **AI Safety President:** Elected on a platform of caution after alarming incidents or growing public concern. Shifts US policy toward safety-first, willing to accept competitive slowdown. Large positive effect on safety investment, large negative effect on capability prioritization.
- **Hawkish President:** Elected on national security fears, especially if China appears to be closing the gap. Doubles down on racing, views safety as obstacle. Increases capability priority, decreases safety investment, increases opponent threat perception.
- **Pragmatic/Centrist President:** Balanced approach. Moderate adjustments. Maintains status quo with incremental changes.
- **Internationalist President:** Prioritizes coordination and diplomacy. Major boost to coordination_level and trust-building. May accept competitive constraints for mutual safety.

**Effects:**

1. us_belief_threshold may shift by 10-20 points (new leadership brings new risk assessment)
2. us_belief_opponent_threat may shift by 10-20 points (new strategic posture)
3. coordination_level may shift by 5-10 points (new diplomatic stance)
4. US resource allocation between capability and safety may change significantly for subsequent turns
5. Signals to China about US intentions (may shift china_belief_opponent_threat by 3-8 points)

**Game Master Note:** This is the single largest source of legitimate policy discontinuity in the simulation. The president's profile should be determined by the narrative state -- if there have been serious AI incidents, a safety-focused president is more likely. If China is catching up fast, a hawk is more likely. The choice should feel like a plausible electoral outcome given what has happened.

## Sabotage Attempt

**ID:** sabotage_attempt

**Condition:** An actor explicitly describes sabotage actions in their turn (cyber attack, insider operation, infrastructure disruption against opponent). This event handles the DISCOVERY of sabotage, not the sabotage itself -- the capability damage is applied through metric rules when an actor commits to sabotage.

**Probability:** Discovery probability depends on how many previous sabotage attempts have occurred in the simulation:

- First sabotage in the simulation: 40% discovery probability.
- Second sabotage: 60% discovery probability.
- Third and subsequent: 80% discovery probability.

**Can repeat:** Yes

**Description:** A sabotage attempt is discovered by the target nation. Discovery may come through counter-intelligence, forensic analysis of system failures, or whistleblowers. Each successive sabotage attempt is more likely to be discovered because defenses harden, counter-intelligence improves, and the target is on alert.

**Effects (if discovered):**

1. coordination_level decreases by 8-15 points (severe trust violation)
2. Target's opponent threat belief increases by 5-15 points
3. International condemnation, potential sanctions (narrative effect)
4. Future sabotage attempts become less effective AND more likely to be discovered
5. Target may retaliate, escalating tensions

**Effects (if NOT discovered):**

1. Target suffers capability reduction as described in Sabotage Mechanics (metric rules)
2. No coordination penalty (target doesn't know)
3. Sabotaging actor gains temporary advantage but still faces diminishing returns on future attempts

**Game Master Note:** Track the number of sabotage attempts in the notepad. Each attempt, whether discovered or not, depletes the attacker's covert assets and hardens the target's defenses. Sabotage is a one-shot or two-shot weapon, not a repeatable strategy.

## Safe Strong AI

**ID:** safe_strong_ai

**Condition:** Any actor's capability >= 80 AND that actor's safety >= capability - 5.

**Probability:** 100% (guaranteed when condition is met)

**Can repeat:** No

**Description:** An actor achieves strong AI with robust safety guarantees. Their AI systems are powerful enough to be transformative but reliably aligned with human values and under meaningful human control. This is the best achievable outcome.

**Effects:**

1. The scenario reaches a positive resolution
2. The winning actor gains enormous strategic advantage, but the catastrophe risk that threatened everyone is neutralized
3. The other actor faces pressure to either cooperate or continue racing (but with the safety template now proven viable)

**Game Master Note:** This is the win condition. Reaching capability 80 with safety 75+ means the actor found a way to develop strong AI responsibly despite competitive pressure. With the reduced growth rates, this requires sustained, deliberate safety investment over many turns.
