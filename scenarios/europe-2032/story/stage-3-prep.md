# Stage-3 prep: turn-10 fixtures + pools (ready morning 2026-09-11)

Stage 2 done overnight: 120/120 reps (pilot A11 + 119 batch, 0 failures),
paths locked at rep 1 per block (`stage-2-PATHS.md`), fault scan clean except
three accepted referee deadlocks (recorded there). 12 turn-10 fixtures
completed; 12 pools of 10 drawn (120/120 valid store blocks).

## Fixture events per block (pinned for Stage-3 turns 10-13)

| block | fixture run | turn-10 fires |
|---|---|---|
| A11 | run-20260911-014820-07 | openweight_frontier_release, labour_displacement, catastrophic_great_power_conflict, emergent_infrastructure_sabotage_wave |
| A12 | run-20260911-014820-04 | research_breakthrough, medical_breakthrough, taiwan_tension_rise, automated_decision_scandal |
| A21 | run-20260911-014820-01 | medical_breakthrough, catastrophic_great_power_conflict |
| A22 | run-20260911-014820-08 | cyber_major_incident, eval_anomaly_reports, opaque_reasoning, catastrophic_loss_of_control_incident, safety_breakthrough, us_china_agreement, joint_threat_response |
| V11 | run-20260911-014820-09 | cyber_major_incident, loss_of_control_incident, middle_power_coalition |
| V12 | run-20260911-014819 | joint_threat_response |
| V21 | run-20260911-014820-02 | bio_incident, capability_jump, eu_frontier_access_denied |
| V22 | run-20260911-014820-05 | cyber_major_incident, capability_jump, labour_displacement, export_control_escalation |
| P11 | run-20260911-014820-03 | bio_incident, opaque_reasoning |
| P12 | run-20260911-014846 | cyber_defence_breakthrough, bio_uplift_findings |
| P21 | run-20260911-014820 | bio_uplift_findings, openweight_frontier_release |
| P22 | run-20260911-014820-06 | ai_investment_collapse, export_control_escalation, adoption_success, emergent_fallback_sabotage |

War fires at turn 10 on A11 and A21; catastrophic loss-of-control on A22.
Per the earlier decision the blocks continue through them.

## Pool textures (`story/pool-10-<BLOCK>-20260911/`, 10 samples each)

Ready to pick (split found): A11 (9 wartime shields vs 1 wait), A12 (7
redress registries vs 3 wait-for-Corps), A22 (5 rogue-containment vs 5
graduate-transition), V11 (9 lockdowns vs 1 none), V22 (5 cyber-recovery vs
5 transition/municipal), P12 (8 patch/sentinel vs 2 transition), P21 (8
None at capital 0 vs 2 bio-shield adds), P22 (8 hold-Black-Start vs 2 adds).

Needs a closer read for an internal axis (uniform at first glance): A21
(10 wartime shelters -- stay-out vs shelter?), V12 (10 cyber-command
accessions), V21 (10 fallback stacks -- clinical vs bio-corps?), P11
(10 bio containment -- triage vs surge?). Extend the pool if no honest
axis emerges.

## Timings (wall clock, for the record)

- Turn-1 pool (30 draws): ~3 min. Base runs (6x1 turn): ~5 min.
- Stage 1 (60x4 turns, 6-wide + 1 resume): ~22:30-23:39 (~70 min).
- Stage-2 pilot (1x4 turns): ~10 min. Stage-2 batch (119x4 turns, 6-wide): 00:28-01:47 (~80 min).
- 150-run stats batch: 17:29-21:48 (~4h20m, incl. one 502 resume), $11.59.
