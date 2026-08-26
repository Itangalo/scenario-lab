## Reconnaissance Wave in Critical Infrastructure
**ID:** cyber_recon_wave
**Condition:** Possible in any turn. Offensive cyber is one of the domains that keeps improving under this regime, so this precursor is markedly more likely here than elsewhere.
**Probability:** 25%. Add 5 percentage points if openweight_gap is below 20.

## Model-Assisted Pathogen Design Reported
**ID:** bio_uplift_findings
**Probability:** 10%. Add 6 points if openweight_gap is below 25.

## Evaluation Anomalies Surface
**ID:** eval_anomaly_reports
**Probability:** 18%.

## Capability Jump
**ID:** capability_jump
**Condition:** Always eligible; list this event every turn. The gate is open if eval_anomaly_reports occurred in either of the previous 2 completed turns, and shut otherwise — that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 25%. Gate shut: 8%. Reduce by a third if a fully implemented category 1 or 3 measure imposes pre-release evaluation or capability restrictions on the leading lab's jurisdiction.
**Description:** A discontinuous advance in a verifiable domain — code, mathematics, cyber, narrow engineering — is released or demonstrated. It moves the releasing jurisdiction's capability metric by only +1 to +2, because general competence saturates early; the jump lands where reward can be verified, and shows up first in offensive-cyber capability.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** us_capability < 0
**Condition:** Impossible under RLVR-LIMITED: verifiable domains improve without end, but recursive self-improvement of general competence does not begin within this horizon. The id is kept only so run statistics stay comparable across arms; the gate above never opens.

## Orbital Datacentre Comes Online
**ID:** orbital_datacenter_success
**Probability:** 6%.

## Grid Capacity Crisis
**ID:** grid_capacity_crisis
**Probability:** 8%.

## Agent Misconduct Disclosure
**ID:** agent_misconduct_disclosure
**Probability:** 14%.
