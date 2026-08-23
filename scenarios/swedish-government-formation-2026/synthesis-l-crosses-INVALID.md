> **INVALID — do not read this as an answer.**
>
> This report analyses the first `l-crosses` batch, which failed to condition.
> All twenty draws gave the Liberals 14–21 seats, but the runs simulated them as
> outside the chamber: in one run drawn with 17 seats the Liberals actor wrote of
> acting "despite lacking parliamentary representation". The batch therefore does
> not measure what L's entry does, and its headline figures — including the
> six-in-twenty extraordinary elections — describe something else.
>
> The report itself caught the problem and refused to answer `rq_threshold_leverage`
> on those grounds, which is why it is kept rather than deleted.
>
> Cause and fix: the seat table stated L's status only as a table row, which lost
> against every other signal in the scenario. The sampler now states it as its own
> sentence in both directions. Re-run started 2026-08-22 22:0x; its report will
> replace this file.

# Swedish Government Formation 2026 — Ensemble Synthesis

## Summary

Twenty completed runs (8–20 turns each; all `completed`, no failed analyses) of the September 2026 Swedish formation scenario converge on a starkly narrow outcome space. Exactly two terminal states occur: an **S-led cross-bloc minority government** — Social Democrats (usually with the Greens in cabinet), tolerated by Centre Party abstention under negative parliamentarism — formed in **14 of 20 runs**, and an **extraordinary election with no government** in **6 of 20 runs** (outcome counts tallied by me from the 20 per-run summaries; they are consistent with the metric trajectories). A right-bloc government formed in **0 of 20** runs and a left-bloc government in **0 of 20**. The Sweden Democrats entered cabinet in **0 of 20** runs (`sd_in_cabinet` never exceeded 80). The machinery of the ensemble is highly regular: Speaker mandate switches (`speaker_switches_mandate`, 14/20 runs, 28 firings) opened the procedural gate, budget-for-abstention offers (`budget_deal_offered`, 18/20 runs) supplied the policy substance, the Centre Party acted as universal last-mover, and snap-election-date announcements (11/20 runs) split evenly between catalysing a deal (5 runs) and presiding over collapse (6 runs). The dominant caveats are event-log gaps (narrated vote failures without logged events), metric artefacts near termination, and the possibility that the cross-bloc funnel is a property of the scenario's incentive design rather than a discovered political tendency.

## Research Questions

### rq_reachable_constellations

**Only one constellation is reachable with meaningful frequency: the cross-bloc S-led minority government (S, with MP, enabled by Centre Party abstention), which formed in 14 of 20 runs; the sole alternative terminal state is an extraordinary election (6 of 20); right-bloc and left-bloc governments formed in 0 of 20 runs.**

- **Metrics.** `viability_cross_bloc` is the only viability that climbs: ensemble mean rises from 22.0 (turn 1) to 74.0 (turn 8) and 83.4 (turn 11), reaching 100 in multiple runs. `viability_right_bloc` plateaus (means 44–51 from turn 12; absolute maximum 75 at turn 15, n=8 — the "a vote would probably pass" band, never a passed vote). `viability_left_bloc` stays flat (means 30–40 throughout; absolute maximum 70 at turns 17–18, n=4). Neither traditional bloc ever came close to 100.
- **Events.** `speaker_switches_mandate` (14/20 runs) is the procedural unlock that pushes cross-bloc viability past 50; `snap_election_date_announced` fired in 11/20 runs; `pm_vote_failed` fired in only 4 runs (5 firings: run-20260822-193752-01 at turn 4; run-20260822-193752-06 and run-20260822-200226 at turn 10; run-20260822-195607 twice, turns 12 and 14 — identification from the per-run analyses, fully accounting for the per-turn totals).
- **Conditions.** Success required the Centre Party's final abstention commitment plus a neutralised Left Party. The six failures separate into recognisable modes: Left Party obstruction that actually landed (run-20260822-195344, where V's housing ultimatum shattered a 95-viability cross-bloc deal; run-20260822-195750, where V refused abstention; run-20260822-193752-03, where V's refusal combined with constitutional scrutiny of the abstention framework), Centre Party withholding at the finish (run-20260822-193752-08, cross-bloc stalling at 90 despite a announced date), and accumulated real vote failures (run-20260822-193752-01; run-20260822-195607, where a 98-viability arrangement lost the floor vote with 176 against).

### rq_sd_in_cabinet

**SD entered cabinet in 0 of 20 runs; `sd_in_cabinet` never exceeded 80 (ensemble maximum, turns 17–18), and its typical late-run state was "cabinet seats explicitly on the table" (medians 55–65 from turn 12 onward), never concession.**

- **When it moved.** The metric rose when the right bloc took formal procedural steps on portfolios, almost always brokered by KD: run-20260822-193752-02 (68 via KD backchannel portfolio talks), run-20260822-193752-06 (60 via KD negotiations), run-20260822-195034 (50 via the public KD–SD "100-day governance plan"), run-20260822-195728 (75), run-20260822-195344 (80, the ensemble peak). It stayed flat where the cordon sanitaire held firm (run-20260822-194705, run-20260822-193752-04, run-20260822-193752-09).
- **Bearing events.** `pledge_broken` (10 runs, 16 firings) generally marked *Centre Party* realignment toward the left/cross-bloc side — run-20260822-195531 (turn 5), run-20260822-195728 (turn 12), run-20260822-200114 (turn 7) — i.e., it coincided with SD losing relevance rather than gaining seats; the divergence table likewise associates `pledge_broken` with −7.7 on `sd_in_cabinet` at turn 5 (small n). `leader_resigns` (3 runs, 4 firings) identified cases are Liberal leader Mohamsson's resignations (run-20260822-193752-01, run-20260822-193752-03); neither advanced SD.
- **The condition that never materialised.** Conversion to 100 required the Moderates to concede portfolios while retaining Centre tolerance. In every run, M's resistance plus C's veto on organising with SD held, and once the cross-bloc exit opened, SD's leverage evaporated entirely. SD's exclusion is the single most invariant outcome in the ensemble.

### rq_threshold_leverage

**This question cannot be answered from the ensemble as delivered: the statistics record no batch variable for the Liberals' threshold outcome, and the per-run analyses indicate L was outside the chamber in roughly 18 of 20 runs, leaving at most one clear in-chamber case — far too few to estimate a conditional distribution.**

- The one unambiguous in-chamber run is run-20260822-193752-09 ("having cleared the threshold, remained in the chamber"): L played a marginal role and the outcome was the standard cross-bloc government. Run-20260822-193752-08 is ambiguous — its analyst *assumes* L "barely clearing the threshold" from truncated artifacts. Every other analysis describes L as below 4% and acting as a non-voting moral commentator (e.g., run-20260822-193752-01, run-20260822-195034, run-20260822-200226).
- Pooling the runs would violate the question's own design note, so no honest contrast between "honest" and "L-clears-4%" batches is estimable. What can be said is only that in this ensemble L's status made no visible difference to the outcome distribution: right-bloc viability plateaued at ≤75 and L was never a decisive actor in any run, in or out of the chamber.
- To answer the question, the scenario would need to record L's threshold status as a structured run parameter and field balanced batches, comparing `viability_right_bloc` trajectories and `pm_vote_failed` incidence between them.

## Outcome Patterns

Counts below are my tally from the 20 per-run summaries; they are consistent with the ensemble trajectories.

1. **Cross-bloc S-led minority government — 14/20 runs.** S (alone or with MP in cabinet) elected under negative parliamentarism with C abstaining; examples: run-20260822-193752, run-20260822-194705, run-20260822-195728, run-20260822-200114. Formation occurred between turns 8 and 18 (median ~13–14). Three sub-variants: (a) formed with no logged failed vote and no snap date (9 runs, e.g., run-20260822-194705, run-20260822-193752-09, run-20260822-200114); (b) formed only after a snap-election date was announced — the "dated threat" (5 runs: run-20260822-193752, -02, -06, run-20260822-195824, run-20260822-200226), with the deal landing 0–5 turns after announcement; (c) recovered from a logged failed vote (2 runs: run-20260822-193752-06 and run-20260822-200226, both failing at turn 10 and forming later).
2. **Extraordinary election, no government — 6/20 runs.** Examples: run-20260822-193752-01, run-20260822-193752-03, run-20260822-193752-08, run-20260822-195344, run-20260822-195607, run-20260822-195750. Sub-variants: (a) four prime-ministerial votes failed and were *logged* (run-20260822-193752-01; run-20260822-195607 with two logged failures); (b) `snap_election_risk` reached 100 through scheduling collapse with no logged votes (run-20260822-193752-03, run-20260822-193752-08); (c) four failures *narrated but never logged* (run-20260822-195344, run-20260822-195750 — see Caveats).
3. **Right-bloc government — 0/20 runs.** An absence, not a small trend. Closest approaches: run-20260822-193752-01 (right bloc holding a stated 177-seat majority that fractured internally over SD portfolios) and the ensemble-wide `viability_right_bloc` ceiling of 75.
4. **Left-bloc government — 0/20 runs.** Nearest approach: run-20260822-195344, where the left bloc revived to 70 after the cross-bloc collapse, then ran out of constitutionally mandated time.
5. **One-off outcomes (each occurred once):** a snap-election date announced on turn 1, before any precondition was met (run-20260822-193752-01, which ended at turn 4); a 98-viability constellation losing the actual floor vote (run-20260822-195607); a run expiring at the 20-turn cap mid-crisis (run-20260822-195750); the fastest formation, at turn 8, driven by a single security shock (run-20260822-193752-09).

## Recurring Turning Points

1. **Speaker mandate switches (14/20 runs, 28 firings).** The procedural gate: viability cannot exceed 50 without one, and nearly every run's inflection is a switch — to Andersson (run-20260822-193752 turn 3; run-20260822-193752-02 turn 13), to Centre leader Ringqvist (run-20260822-195531 turn 2; run-20260822-200226 turn 4), or, uniquely, to Kristersson, briefly reviving the right (run-20260822-195750 turn 11).
2. **Budget-for-abstention offers (18/20 runs; per-turn counts sum to 56 firings, my sum).** The substantive engine of the cross-bloc deal: run-20260822-194705 (turn 8 acceptance "made the cross-bloc government inevitable"), run-20260822-195034 (five offers culminating in a Framework for Conditional Abstention).
3. **Snap-election-date announcements (11/20 runs).** A genuine fork, not a guaranteed catalyst: in 5 runs it forced a deal within 0–5 turns (run-20260822-193752, -02, -06, run-20260822-195824, run-20260822-200226); in 6 it preceded collapse anyway (all six snap runs). The 2014 "dated threat" precedent encoded in the scenario held only half the time.
4. **Security and national shocks (`security_shock` 8/20 runs, plus seven emergent one-off events).** Shock runs formed governments in 7 of 8 cases (my tally); the shock reframed deadlock as national irresponsibility and gave the Centre Party cover to move (run-20260822-193752-09 turn 2; run-20260822-200114 turn 2; run-20260822-195728 turn 7). Emergent one-offs were often locally decisive where they fired: EU funding pressure (run-20260822-193752-04 turn 10), the energy-regulator alert (run-20260822-193752-06 turn 14), the NATO defence leak (run-20260822-193752 turn 10).
5. **Left Party ultimatum cycles.** V's brinkmanship backfired into marginalisation in most runs, but was the *decisive* cause of collapse in run-20260822-195344 (ultimatum shattered a 95-viability deal) and contributory in run-20260822-195750 and run-20260822-193752-03. V is the main within-pattern switch between the two terminal states.
6. **The Centre Party's final-commitment moment.** Universal last mover: committing to abstention produced a government in all 14 formations; withholding produced deadlock (run-20260822-193752-08) or constitutional paralysis (run-20260822-193752-03).
7. **Right-bloc fracture over SD portfolios.** KD advances portfolio talks, M publicly resists, the bloc splits — present in most runs and explicit in run-20260822-193752-01, run-20260822-193752-02, run-20260822-195728, run-20260822-195824.

## Actor Dynamics

- **Social Democrats (central in 20/20; premiership in 14/20).** Strategic ambiguity between the V-track and C-track in essentially every analysis, pivoting to cross-bloc once V's price proved uns payable. Never broke its SD exclusion; never paid V in cabinet seats.
- **Centre Party (pivot in 20/20).** Dual vetoes held in nearly all runs; instrument was abstention, never membership. Broke its own pre-election pledge toward the left in at least three identified runs (run-20260822-195531, run-20260822-195728, run-20260822-200114) and successfully avoided deadlock blame in most formations.
- **Sweden Democrats (demandeur in 20/20; cabinet in 0/20).** Maximalist cabinet demands, ultimatums, media campaigns; repeatedly assessed by the per-run analysts as alienating potential enablers. Peak proximity 80 (run-20260822-195344); in run-20260822-193752-07 the metric fell to 0 only after the final vote.
- **Moderates (structural loser in 20/20).** Caught between SD dependence and C courtship; reactive in every account; sidelined in formations *and* collapses alike; its only revival came via a Speaker mandate switch (run-20260822-195750).
- **Left Party.** Ultimatum-first posture; marginalised in the 14 formations; the effective veto-holder in 2–3 of the 6 collapses. Never extracted its price; never successfully voted down Andersson alone.
- **Greens.** The quiet winners of the ensemble: acceptable to both S and C, in cabinet in most formed governments (explicitly "S and MP in cabinet" in run-20260822-193752-09), securing climate commitments while avoiding V's maximalism.
- **Christian Democrats.** SD's bridge; their portfolio diplomacy drove every `sd_in_cabinet` rise, but they could never deliver M's consent, and their resistance to SD's "rotating responsibility" model helped fracture the right (run-20260822-195728 turn 16).
- **Liberals.** Outside the chamber in ~18/20 runs (confirmed in-chamber only in run-20260822-193752-09); a purely discursive actor everywhere; leader Mohamsson resigned in the two identified `leader_resigns` runs, both of which collapsed.

## Surprises and Outliers

- **The dated threat failed as often as it worked** — 6 of 11 announcements produced no deal, contradicting the 2014 precedent the scenario explicitly encodes. When it did work, the deal came fast (0–5 turns).
- **Run-20260822-195607** is the ensemble's sharpest lesson: a cross-bloc arrangement at 98 viability lost the actual vote, 176 against — negative parliamentarism is knife-edge arithmetic, not a guarantee.
- **Run-20260822-195344** contains two ensemble extremes at once: the highest SD cabinet proximity (80) and the only left-bloc resurgence (to 70), both ending in nothing.
- **Run-20260822-193752-01** is unique in announcing a snap date on turn 1 — its own analyst flags this as a violation of the event's stated preconditions — compressing the whole crisis into 4 turns.
- **Run-20260822-193752-09** formed in 8 turns off a single security shock, with only one event firing in the entire run; it is also the only confirmed Liberals-in-chamber case.
- **Seven distinct emergent events each fired in exactly one run** (defence leak, defence crisis, energy crisis, energy-crisis alert, EU pressure, rural protests, security alert) — individually rare, collectively present in 7 runs, and frequently the local trigger for resolution or climax.
- **`deadlock_cost` routinely peaks at ~100 at or immediately after formation** (e.g., run-20260822-193752-05, run-20260822-195531) — an artefact discussed under Caveats.

## Simulation Caveats

- **Event-log gaps.** Run-20260822-195344 and run-20260822-195750 narrate four failed prime-ministerial votes with *zero* logged `pm_vote_failed` events; run-20260822-193752-03 and -08 reach risk 100 similarly. Logged firings (5) therefore undercount narrated failures. Run-20260822-193752-01's turn-1 snap date violates the event's own condition (≥2 failed votes or abandoned soundings).
- **Constitution-constraint churn.** Multiple analysts report repeated violations and late corrections: viability raised above 50 without procedural steps (run-20260822-193752-01, run-20260822-195034, run-20260822-193752-07), the left-bloc minimum-60 rule applied only at turn 8 (run-20260822-193752-02), deadlock-cost ceilings breached then corrected. Early-turn metric values should be read with suspicion.
- **Metric artefacts.** `deadlock_cost` peaking at 100 at the moment of resolution inverts its intended logic (pressure should precede the deal); `sd_in_cabinet` shows abrupt unexplained drops (55→25 in run-20260822-200226; to 0 post-vote in run-20260822-193752-07); `snap_election_risk` conflates risk with certainty once four failures make an election mandatory.
- **Possible design funnel.** The Centre Party's double veto plus negative parliamentarism arithmetically admits essentially one government type; all 20 runs share the same structural arc despite high lexical diversity (mean pairwise Jaccard 0.18). The cross-bloc dominance may partly reflect scenario incentives and the model's reluctance to ever have M concede SD portfolios — the one branch that would open right-bloc paths — rather than a discovered empirical tendency. Treat "right and left are unreachable" as a finding about *this simulation configuration*, not about Sweden.
- **Small-n associations.** The largest divergences (turn 18: `deadlock_cost` IQR jump 82, `snap_election_risk` jump 60) rest on n=2-versus-2 contrasts — the two late-forming runs (both security-shocked, run-20260822-195034 and run-20260822-195728) versus the two late-collapsing ones (both date-announced, run-20260822-195344 and run-20260822-195750). Illustrative, not inferential.
- **Batch opacity.** No structured record distinguishes the honest batch from any L-clears-4% conditioning, disabling `rq_threshold_leverage`.
- **Truncation.** Several analysts note condensed/truncated artifacts, limiting verification of early turns and of details like seat counts (run-20260822-195344's arithmetic is flagged as ambiguous by its own analyst).

## Confidence Assessment

- **High confidence:** the terminal-state split (14 cross-bloc governments / 6 extraordinary elections, 0 right-bloc, 0 left-bloc) — directly tallied from 20 complete run analyses and corroborated by the viability trajectories; SD's total exclusion from cabinet (0/20, metric ceiling 80); the Centre Party's universal kingmaker role; the mechanism inventory (mandate switches 14/20, budget deals 18/20).
- **Moderate confidence:** the separators between the formation and collapse branches (six failure cases with heterogeneous causes — V obstruction, C withholding, accumulated vote failures); the security-shock association with resolution (7/8, modest n); the dated-threat efficacy split (5/11 deals).
- **Low confidence:** anything about Liberal threshold effects — the ensemble cannot support the required batch comparison, and the in-chamber sample is one clear run; any quantitative claim resting on the turn-18 divergence associations (n=2 per cell).
- **Structural reservation:** because all 20 runs share one narrative arc inside a scenario whose arithmetic funnels toward a single outcome, the ensemble's most robust-looking regularities should be treated jointly as findings about this scenario-as-simulated, with the cross-bloc monopoly the most likely candidate for a design artefact rather than a world-level result.
