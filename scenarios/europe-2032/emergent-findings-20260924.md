# Emergent findings in the 150-run stats batch (2026-09-24)

Material for a short piece. Everything below is measured on the `stats-20260910-spark-storev2` corpus: 150 runs, 50 per arm, 13 turns, Muse Spark GM, store-branch architecture, current 37-event catalogue. Checkpoint logs `runs/batch-logs/batch-20260910-172940-*` (21 runs) plus scaleup logs `batch-20260910-184012-*` (129 runs).

Deliberately excluded: anything the event catalogue already states (capability gates, precursor bonuses, mitigation halvings). What follows is what the runs added on their own.

Caveats: metric moves are LLM-judged — the model that writes "sabotage!" also scores sovereignty down. Catastrophe links are small-n. The measure-holder comparisons are observational, not causal.

## 1. The simulation invents a politics of concrete

331 distinct emergent event ids, 387 firings across the corpus. The head of the distribution is physical-world friction the catalogue never mentions: `datacentre_siting_backlash` (9 firings), `anti_datacentre_blockades` (6), `datacentre_backlash` (5), `infrastructure_sabotage_wave` (5), plus graduate protests, insurance repricing, and a Kimi-model crime wave. Local resistance to buildout is the single most common thing the model adds unprompted.

Turn-level metric deltas (turns with the emergent family vs ordinary turns):
- Siting fights (n=154 turns): sovereignty −0.94 vs −0.58, sentiment −3.87 vs −2.30. Capability growth unaffected (+1.66 vs +1.84).
- Sabotage (n=18): sovereignty −1.94 vs −0.59 — roughly triple bleed.
- Insurance, protest, cybercrime, revelation turns: sentiment roughly 1 point worse than baseline each; capability never slows.

Reading: resistance is priced as a political tax, never a brake. The buildout continues; the EU bleeds standing. That worldview lives nowhere in the written rules.

## 2. An un-designed early-warning signature

Pre-catastrophe vs clean per-slot rates on the Acceleration arm: insurance-crunch events 4.3×, lab-leak/coverup revelations 3.2×. Examples: `cyber_insurance_repricing` at turn 2, then war at 10 and bio plus loss-of-control at 11 (`run-20260910-185206`); `eval_coverup_leak` at turn 3, then loss-of-control at 10 (`run-20260910-192034`). 6 of 8 A-runs touching either family end in catastrophe, against a 58% arm base rate. Small-n — hold lightly — but it is the only precursor signal in the corpus that is not the catalogue mechanics restating itself.

Mirror image: protest events run at 0.36× pre-catastrophe, talent events 0 for 3. Catastrophizing worlds are quiet first.

## 3. The mitigation that bites, and the one that does not

The EU invents constantly: 1,317 distinct measure names across the corpus. The asymmetry is the finding:
- Bio detection/screening holders: 19 runs, zero bio-catastrophes. Both catastrophes among holders were wars — a different die. Base bio rate is roughly 9% of runs.
- Loss-of-control containment holders: 63 runs, catastrophes in 16 — the same rate as non-holders. No protection at all.

Both halve dice on paper. In practice halving bites on the low-base-rate bio die (3%/1%, quartered with both measure types in place) and is irrelevant against the Acceleration juggernaut, where the loss-of-control gate is nearly always open and safety always below 45. Mitigation works where the risk is rare, not where it is structural — and the EU built bio-screening in only 19 of 150 runs while producing 63 containment protocols for the risk it cannot touch.

## 4. The EU does not answer the door

New-measure rate after emergent-event turns is 0.74 per turn against 0.76 overall: no responsiveness whatever. One instance: `emergent_siting_backlash_freeze` freezes an InvestAI site (`run-20260910-172941-01`, turn 4); the next turn's addition is `EU Bio Detection and Care Continuity Surge`. The portfolio marches to its own cadence while siting wars and sabotage go unanswered.

## Corpus reference

- Catastrophe totals: 32/150 runs (Acceleration 29/50, Verification 2/50, Plateau 1/50). War 20 firings, loss-of-control 15, bio 14. Earliest turn 6, peak turn 11; 14 runs stack multiple catastrophes.
- The published compare popups are built from 160 runs, not 150: `story/build_compare.py` globs `batch-20260910-*.log` and silently includes the 10 pilot runs (`batch-20260910-1353*`, zero catastrophes). Scope that glob to the stats batch before trusting popup numbers.
