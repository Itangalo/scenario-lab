## Evaluation Anomalies Surface
**ID:** eval_anomaly_reports
**Probability:** 10%.

## Capability Jump
**ID:** capability_jump
**Probability:** Gate open: 10%. Gate shut: 3%. Reduce by a third if a finished category 1 or 3 measure imposes pre-release evaluation or capability restrictions that actually bind the jurisdiction where the leading models are built.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** ai_capability < 0
**Condition:** Impossible in this run: general competence saturates before recursive self-improvement becomes possible. The id is kept only so run statistics stay comparable across arms; the gate above never opens.

## Verification Frontier Widens
**ID:** verification_widens
**Probability:** 8%.

## Evidence of a Bending Curve
**ID:** capability_plateau_evidence
**Probability:** 22%.

## Reasoning Stops Being Legible
**ID:** opaque_reasoning
**Probability:** 5%.

## Medicine Delivers
**ID:** medical_breakthrough
**Probability:** 8%.

## AI Investment Collapse
**ID:** ai_investment_collapse
**Probability:** 10%. Add 10 points if `capability_plateau_evidence` occurred in any of the previous 3 completed turns. Add 5 points if `public_sentiment` is below 30.

## Open Weights Reach the Frontier
**ID:** openweight_frontier_release
**Probability:** 15%. Halve if a finished restriction on open release above a capability threshold binds a jurisdiction where such models are actually trained.
