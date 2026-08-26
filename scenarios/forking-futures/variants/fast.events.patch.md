## Reconnaissance Wave in Critical Infrastructure
**ID:** cyber_recon_wave
**Condition:** Possible in any turn. More likely as capability rises.
**Probability:** 18%. Add 5 percentage points if openweight_gap is below 20.

## Model-Assisted Pathogen Design Reported
**ID:** bio_uplift_findings
**Probability:** 14%. Add 6 points if openweight_gap is below 25.

## Evaluation Anomalies Surface
**ID:** eval_anomaly_reports
**Probability:** 25%.

## Capability Jump
**ID:** capability_jump
**Condition:** Always eligible; list this event every turn. The gate is open if eval_anomaly_reports occurred in either of the previous 2 completed turns, and shut otherwise — that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 35%. Gate shut: 12%. Reduce by a third if a fully implemented category 1 or 3 measure imposes pre-release evaluation or capability restrictions on the leading lab's jurisdiction.
**Description:** A discontinuous advance is released or demonstrated. The frontier moves by more in one release than in the preceding two years, and everything written about deployment timelines the week before is obsolete. It moves the releasing jurisdiction's capability metric by roughly +3 to +7.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** us_capability >= 65 or cn_capability >= 65
**Condition:** Requires capability at or above 65 in either jurisdiction (the gate above). When it is listed, the event is live.

## Orbital Datacentre Comes Online
**ID:** orbital_datacenter_success
**Probability:** 10%.

## Grid Capacity Crisis
**ID:** grid_capacity_crisis
**Probability:** 12%.

## Agent Misconduct Disclosure
**ID:** agent_misconduct_disclosure
**Probability:** 12%.
