# Metric Rules v1 (Turn 0 – Initial)

Ranges below mean judge within the range, not average it. One level on a capability metric is a lane jump; fractions are partial progress.

## Rules

1. `us_capability` advances 0.2–0.4 per turn from Alphabet R&D and talent/compute accumulation (rule 1).
- Frontier breakthrough or successful exfiltration for the US bloc: +0.3 to +0.6 once.
- Taiwan crisis in force: −0.1 to −0.3 per turn (slows, never stops).
- Preventive strike hitting US assets: −0.3 to −0.6 once, plus lost safety work (see rule 3).
- Binding slowdown treaty in force (agreement_strength >= 60): −0.1 per turn while verified.
- Never past 4; reaching 4 triggers deployment resolution, not further growth.

2. `china_capability` advances 0.2–0.4 per turn from Tencent R&D with state backing (rule 2).
- Frontier breakthrough or successful exfiltration for the China bloc: +0.3 to +0.6 once.
- Taiwan crisis in force: +0.0 to +0.2 per turn for China if fabs are exploited, else −0.1 to −0.2 like everyone else; judge from the narrative.
- Preventive strike hitting Chinese assets: −0.3 to −0.6 once, plus lost safety work (see rule 3).
- Binding slowdown treaty in force (agreement_strength >= 60): −0.1 per turn while verified.
- Never past 4; reaching 4 triggers deployment resolution, not further growth.

3. `safety_progress` rises only from funded work and cooperation (rule 3).
- Sustained multi-actor safety investment or joint breakthrough: +8 to +15 in the turn.
- Single lab's internal measures: +2 to +5.
- Endgame hasty top-up (capability 3.5+ rushing): at most +5, and it does not integrate with deployed systems.
- Preventive strike, war, or exposed defection destroys safety work: −5 to −15 once.
- No passive drift: absent funded work it stays flat; complacency after early action can let it slip −2.

4. `global_stability` decays under unmitigated impacts and adversarial action, recovers only through verified calm (rule 4).
- Each turn with an unmitigated concern wave or major adversarial action: −1 to −2.
- Taiwan crisis onset, exposed defection, or preventive strike: −2 to −3 once each.
- Warning-shot incident: −1 once, then possible +1 if serious policy follows within 2 turns.
- Verified treaty operating (agreement_strength >= 60, no defection): +1 per turn up to 7.
- Never moves more than 3 points in a single turn.

5. `us_china_tension` tracks the rivalry temperature (rule 5).
- Exfiltration reveal, blockade, or weapons deployment: +10 to +20 once each.
- Exposed defection or preventive strike: +15 to +25 once.
- Successful summit with follow-through: −10 to −15; failed summit: +5.
- Disruptive US election outcome: +5 to +10 in the following turn.
- Drifts toward 45 absent fresh drivers (±5 per turn toward the midpoint).

6. `agreement_strength` moves only through negotiation and verification, and collapses on betrayal (rule 6).
- Signed binding treaty with verification: +15 to +25 once.
- Summit without verification: +3 to +8.
- Exposed defection: −25 to −40 once; preventive strike or war: −20 to −30.
- Disruptive US election: −10 to −20 in the following turn as commitments freeze.
- Decays −3 per turn without maintenance once above 30; reactive band-aids never hold it above 40.

## Standing conditions

- Attention economy: each actor completes at most two major policy initiatives per turn; broader wish-lists are partially executed or deferred – judge visible progress accordingly.
- Secrecy: private actions and R&D succeed or fail before the narrative reveals them; exfiltration and defection move metrics first and surface publicly when exposed.
- Multipolar arrival: if both blocs reach 4, resolve each deployment separately against safety_progress and agreement_strength; any unsafe deployment poisons the shared outcome regardless of the other's roll.
- Deployment resolution at capability 4: safety_progress >= 75 with agreement_strength >= 60 means controlled deployment; 50–75 means contested deployment with incident costs; below 50 means catastrophe or war extends the game – do not narrate a clean victory.
