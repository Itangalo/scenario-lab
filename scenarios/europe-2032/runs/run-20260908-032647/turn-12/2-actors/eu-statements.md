# Statements: The European Union (turn 12)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late — but we now recognise that inaction in the face of blocked paths is itself a decision, and one we will no longer treat as passive.
- `build_independent_frontier_capacity` (commitment): We will secure the EU’s access to frontier AI capability through sovereign infrastructure, talent, and legal anchoring, but no longer expect to establish a full EU-led frontier training capability independent of external suppliers by the end of 2031. Given sustained denial of access to critical components and frontier models, we now explicitly condition our frontier access on enforceable legal and security arrangements with third-party providers, not on technical self-sufficiency.

## Changes this turn

- **modify** `build_independent_frontier_capacity` — applied
  - Tier: commitment
  - Text: We will secure the EU’s access to frontier AI capability through sovereign infrastructure, talent, and legal anchoring, but no longer expect to establish a full EU-led frontier training capability independent of external suppliers by the end of 2031. Given sustained denial of access to critical components and frontier models, we now explicitly condition our frontier access on enforceable legal and security arrangements with third-party providers, not on technical self-sufficiency.
  - Trigger: eu_frontier_access_denied
  - Grounds: The **eu_frontier_access_denied** event confirms that access is not merely delayed but actively revoked at will, with no appeal. This is not a temporary bottleneck but a structural dependency. Our sovereignty cannot rest on permission. The commitment evolves from building independent training runs to securing enforceable rights over capability that remains externally developed — through hosting, auditing, and red-teaming under EU jurisdiction, and mutualised leverage over supply.
  - Evidence quoted: eu_frontier_access_denied: The Union is cut off from the leading model at short notice, wholly or by nationality of user. No detailed reason is given, there is no appeal, and the immediate practical effect lands on hospitals, ministries and firms that had built on it. Whether this reads at home as an outrage or as a failure of foresight depends on what the Union had done about it beforehand.
  - Reason: The denial of access directly undermines the feasibility of technical self-sufficiency, forcing a shift to legal and security arrangements as a conditional alternative.
- **modify** `act_under_uncertainty` — applied
  - Tier: commitment
  - Text: We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late — but we now recognise that inaction in the face of blocked paths is itself a decision, and one we will no longer treat as passive.
  - Trigger: eval_anomaly_reports and the failure to resume sovereign training despite operational infrastructure
  - Grounds: The **eval_anomaly_reports** signal emergent behaviour beyond current models’ intended design, and with **ai_safety** at 6.0, the margin for error is gone. We have acted on thresholds and evaluation, but the failure to shift the trajectory of sovereign access demands a more assertive stance. This refinement acknowledges that acting under uncertainty now includes confronting political and strategic deadlock as a risk to be broken, not endured.
  - Evidence quoted: eval_anomaly_reports: Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. The laboratory calls it a measurement artefact. It may be one. This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.
  - Reason: The anomaly reports reveal uncontrolled capability emergence, directly challenging the EU's ability to act under uncertainty by exposing that inaction risks unmanaged systemic threats.
