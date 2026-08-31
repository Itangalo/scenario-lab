# Forking Futures — Ensemble Synthesis (60 runs)

## Summary

Sixty completed 18-turn runs (July 2026 – June 2035, one regulator actor, states and labs modeled as conditions) produced a consistent macro-shape with sharply forked endpoints. By turn 18, US capability averaged 75.1 (median 67.5; p90 = 100, so at least ~10% of runs reached the decisively-superhuman cap) and Chinese capability 68.3 (p90 = 87). The openweight_gap split violently: min 0, max 95, p10 = 1, p90 = 73 — roughly a quarter of runs ended with frontier capability effectively diffused, another quarter with it locked in closed labs. Incident_pressure rose in almost every run (median 72 vs start 20; only one analyzed run ended below its start). Public sentiment fell everywhere (median 26 vs start 42; no analyzed run ended above its start). Regulatory_capacity was nearly inert (median 47 vs start ~48.7; max IQR jump across all events: 2.0 points).

Three structural facts recur across the 60 per-run readings: (1) the regulator's instruments arrived after the harms and windows they targeted — this refrain appears in nearly every analysis; (2) the binding constraint was legitimacy, not capability — emergent court challenges fired in 35 of 60 runs (58%), rival standards bodies in 29 (48%), member-state noncompliance in 16 (27%); (3) endpoints forked primarily on capability regime (rsi_onset in 19 runs, 32%) and on diffusion, not on anything the regulator reliably controlled.

## Research Questions

### rq_early_vs_reactive

**The ensemble supports only a weak, conditional "yes": early measures that fully landed bought real but fragile advantages, while purely reactive postures produced transient capacity peaks that decayed — and in the 19 runs with recursive-self-improvement onset, no timing strategy mattered at all.** The ensemble statistics cannot test the question directly: nothing timestamps when the regulator committed capital to a measure class against when the matching incident landed. The comparison below therefore rests on the per-run analyses, and should be read as narrative evidence, not measurement.

What the narratives show:

- **Early-and-implemented was rare.** Counting from the 60 analyses, only about 13 runs record any measure verifiably reaching full implementation (e.g., run-20260825-030256: Containment Enforcement Directive fully implemented turn 4, capacity peaking at 68; run-20260825-081623: consumer-product safety standards landing domestically at turn 4 as the portfolio's only completion; run-20260824-232120: only a low-cost post-deployment monitoring duty survived). Run-20260825-011006 records none.
- **Early wins were reversible.** Run-20260825-001102 implemented and enforced Emergency Binding Standards in turn 5 after the market crash, then lost them to an injunction at turn 7. Run-20260825-003831 saw its Domestic Enforcement Pathway reach full implementation at turn 12 and be suspended shortly after. The 58% court-challenge rate is the mechanical reason early advantage decayed.
- **Reactive surges peaked and drained.** Run-20260824-223522 (capacity peak 59 in turns 12–13 after the first cyber campaign, then erosion), run-20260825-024359 (peak 59, ending 43), run-20260825-011359 (emergency protocols litigated into suspension).
- **Early preparation paid off ex post even when binding action came late.** Run-20260825-081618 built detection infrastructure from turn 4; when the precursor-paid cyber campaign finally landed at turn 14, the act-before-proof strategy was vindicated — though the binding fallback certification still arrived four turns after the harm.
- **Negotiation windows reward pre-built capital.** Windows opened in 53 of 60 runs (88%); only two runs converted one into any agreement — run-20260825-005828 (Binding Interim Protocol on Pre-Deployment Cyber Screening, US and allies, China observer-only) and run-20260825-032809 (Bilateral Compute Transparency Accord) — both cases where the regulator entered the window with drafts and capital in hand. Everywhere else windows closed empty (0-for-2 in run-20260825-025927 and run-20260825-081613; 0-for-3 in run-20260825-081553; 0-for-4 in run-20260824-232950).

**Regime conditions:** the divergence statistics show runs with rsi_onset sitting ~27 points higher on us_capability at the turn-15 checkpoint (91.1 vs 64.0). In those 19 runs, analysts uniformly describe instruments as irrelevant to the outcome; the meaningful early-action cases sit in slower regimes. **What would have to be measured:** a per-turn ledger of measure-class commitment and implementation status, aligned with incident dates, before early-vs-reactive can be answered quantitatively.

### rq_early_signals

**The precursors that preceded the largest divergences were funding_round_pulled (economic collapse), eval_anomaly_reports (the capability-regime fork), and bio_uplift_findings (early incident-pressure spikes); the three most frequent precursors — taiwan_tension_rise (54/60), whistleblower_disclosure (52/60) and cyber_recon_wave (50/60) — fired so widely they discriminate almost nothing, and gated catastrophes regularly arrived with no precursor at all.**

| Precursor | Fires in | What it preceded | Verdict |
|---|---|---|---|
| funding_round_pulled | 36/60 (60%) | ai_market_crash (32/60); crash is the largest turn-3 economic divergence (−19.2) | Genuine but incomplete: classic chains in run-20260824-214358 and run-20260824-214357-04 (pull T1 → crash T2), but ≥7 analyses record crashes through shut gates with no fresh precursor (run-20260824-214357-03, -223522, run-20260825-001102, -010925, -022620, -060551, -081603) |
| eval_anomaly_reports | 45/60 (75%) | capability_jump (36/60), rsi_onset (19/60); rsi_onset carries the largest end-state associations in the dataset (+41.8 openweight_gap, +27.1 us_capability) | Best available leading indicator of the capability fork — but with false positives (run-20260825-003831: anomalies T10–T11, no jump ever) and false negatives (run-20260825-040955: no anomalies, no jumps, smooth growth) |
| bio_uplift_findings | 35/60 (58%) | bio_incident (17/60); bio incident is the largest turn-2 incident-pressure association (+27.4, though n=3) | Noisy both ways: roughly half of uplift signals never paid off within the gate horizon; run-20260825-022620 had a bio incident at T1 at its 1% shut-gate rate with no uplift |
| cyber_recon_wave | 50/60 (83%) | cyber_mass_campaign (54/60) | Mechanically linked but saturated — and an *anti*-signal for takeoff: runs with recon waves ended ~14 points *lower* on us_capability (69.0 vs 83.4), marking cyber-heavy slow-capability worlds. Lags can be enormous (run-20260824-223114: ~14 turns of precursor persistence before the T18 payoff) |
| taiwan_tension_rise | 54/60 (90%) | taiwan_blockade (24/60) | Poor specificity: ≥7 analyses explicitly record blockades at the gate-shut 2% rate (run-20260824-214358, -223947, run-20260825-001102, -024359, -042646, -081558, -081618) |
| whistleblower_disclosure | 52/60 (87%) | ambient legitimacy pressure | Chronic background, not a discriminator |
| agent_misconduct_disclosure | 23/60 (38%) | agent_supply_chain_compromise (19/60) | Mixed: 6 of 19 compromises occurred in turns 2–4 at ~2% shut-gate rates, before any disclosure could open the gate |
| datacenter_protest_wave | 20/60 (33%) | — | Lagging, not leading: clustered in turns 13–18, following sentiment collapse (run-20260825-013538) |

Two monitoring conclusions beyond the table. First, early-run divergence is driven by realized shocks (incident_pressure forks at turn 2; economic_context at turn 3), while late-run divergence is driven by the capability regime — so capability signals deserve weight *earlier* than their consequences appear. Second, several analyses show rsi_onset was recognizable only retrospectively through release cadence (run-20260824-223419's early-warning system detected anomalies but could never confirm; run-20260825-015102; run-20260825-001924), arguing for direct cadence monitoring alongside the precursor list.

### rq_no_regret

**There is a candidate no-regret core — independent technical evaluation capacity, incident reporting/transparency, and cyber preparedness — that recurs as the durable survivor across all three regimes, but no package strictly satisfies "never worse": even detection portfolios consumed scarce capacity, and every binding-restriction package was regime-conditional or negative.**

- **The recurring survivor:** across regime-diverse runs, the "one durable success" is almost always sovereign detection/evaluation infrastructure — the Technical Evaluation Lab (run-20260824-214358), the Shared Detection Infrastructure and Early Warning Watchlist (run-20260824-233031), Open-Weight Threat Monitoring and the Joint Incident Response Cell (run-20260825-022620), BRED/SEAR (run-20260825-011006), the Sovereign Red-Teaming Facility (run-20260825-023012), the Early Detection Protocol (run-20260825-045712), secure evaluation infrastructure (run-20260825-051555), CDACC (run-20260825-081618), the AI Transparency Registry (run-20260825-034635), and five domestic implementations (run-20260825-081548). No analysis describes these as harmful; their cost is capacity and attention (run-20260825-023012 cites "chronic portfolio congestion").
- **Binding restrictions are regime-conditional.** They paid off mainly in post-crash windows where restriction became politically cheap (run-20260825-001102; run-20260824-232120), and even there courts reversed them. Outside those windows they stalled, provoked rival standards bodies (48% of runs) and member-state defiance (27%), and attracted covert defection (8 runs, 13%; run-20260824-232120's turn-7 defection "shattered multilateral trust").
- **Multilateral treaty-first postures were the worst package everywhere**: near-universal stalling against US and Chinese refusal, with only the two partial bilateral conversions noted above.
- **Adoption-promotion measures carried embedded regret**: algorithmic_bias_scandal (11 runs, 18%) lands specifically where adoption put it and drags sentiment (−5.8 association).
- **Diffusion was not controllable by any package**: the gap fell to ~0 through distillation with no release event in run-20260825-081548, run-20260825-002240 and run-20260825-060551, and release-control instruments weakened on contact wherever releases did occur.

Strict "never worse" cannot be verified because regulatory_capacity barely moves in response to anything (max IQR jump 2.0), so opportunity costs are invisible to the ensemble statistics. Regime labels were mostly hidden from the regulator and are only intermittently visible in the artifacts (PLATEAU confirmed in run-20260824-234542 and run-20260825-081548; RLVR-like code/cyber-confined growth inferred in run-20260824-223722, run-20260825-023012, run-20260825-032454, run-20260825-052440), so regime-conditional claims here are inferential.

## Outcome Patterns

Families overlap; the first two are capability branches, the next two governance end-states that cut across them. Counts marked ◆ are my tallies from the 60 per-run analyses; all other counts are ensemble statistics.

1. **Compounding-takeoff endings — 19 runs (32%, = rsi_onset count).** US capability 85–100, openweight gap widening, incident pressure pinned at crisis levels, regulator reduced to observation. Examples: run-20260824-223114, run-20260825-012812, run-20260825-022426, run-20260825-030256, run-20260825-004558, run-20260825-005828, run-20260825-000221, run-20260824-231310, run-20260825-081543, run-20260825-081558.
2. **Diffusion-capture endings — ~13 runs ◆** (consistent with the gap distribution's floor: p10 = 1.0 at turn 18). Gap collapses to ~0–8 largely without frontier releases; containment becomes structurally obsolete. Examples: run-20260824-234542, run-20260825-002240, run-20260825-013538, run-20260825-040955, run-20260825-081548, run-20260825-044737, run-20260825-060551, run-20260825-023012, run-20260825-081608, run-20260825-025927, run-20260825-024359, run-20260825-042817, run-20260825-022620.
3. **Grinding-crisis attrition — the modal overlay, clearest in ~10 runs ◆.** Capability converges moderately (US ~62–70), incident pressure pins at 65–95, capacity ends at or below start, enforcement is judicially frozen. Examples: run-20260824-232950, run-20260825-011359, run-20260825-024359, run-20260825-034635, run-20260825-051555, run-20260825-081608, run-20260825-042646, run-20260824-214357, run-20260824-214358, run-20260824-223756.
4. **Standards-war fragmentation endings — event in 29 runs (48%); war-dominated endings in ~6 runs ◆.** A rival standards body captures adopters or formally launches. Examples: run-20260825-081553, run-20260825-025927 (rival bloc took ~40% of the regulator's core market), run-20260824-214357-04, run-20260825-032454, run-20260825-040955, run-20260824-214357-02.
5. **One-off endings (each occurred once):**
   - **Armed stagnation** — run-20260825-002043 ends in a "legitimacy contest that ends in armed stagnation."
   - **Immediate-triple-shock emergency** — run-20260825-081553 opens with a near-frontier open-weight release, a bio incident, and an alliance bloc all in turn 1, collapsing the scenario's uncertainty premise immediately.
   - **Last-turn reversal** — run-20260824-223114: after a run of maximal concentration (gap 93), an emergent open-weight breakthrough cuts the gap to 73 in the final turn.
   - **Affective-harm-first agenda** — run-20260825-081623, where a companion-platform hospitalisation, not cyber or geopolitics, structures the entire regulatory arc.
   - **Sub-start incident pressure** — run-20260824-223722 is the only analyzed run ending below its starting incident_pressure (18 vs 20), a full round trip.
   - **Narrow alignment failure** — `emergent_alignment_failure_narrow` fired once, turn 12, in one run (ensemble statistics only; no analysis names it).
   - **Defensive breakthroughs** — `emergent_defensive_breakthrough` in 2 runs; the ensemble's rare good news.

## Recurring Turning Points

1. **Turn 1–3 shock cluster.** Funding pulls at T1 (14 run-occurrences) chained into crashes at T2–T3 (12); early cyber campaigns (19 run-occurrences in T1–T3) and early blockades (9 in T2–T3) set permanent postures before the regulator had built anything.
2. **First cyber_mass_campaign (90% of runs).** Converts doctrine from anticipation to permanent reaction (run-20260824-223522, run-20260825-051555, run-20260825-040755).
3. **Open_weight_frontier_release (34 runs, 57%, concentrated T4–T8).** The containment-to-diffusion pivot (run-20260825-040955, run-20260825-044737, run-20260825-022620).
4. **Failed negotiation windows (53 runs with windows; 2 conversions).** Permanent closure of the binding-agreement track (run-20260825-015102, run-20260824-232950).
5. **Emergent court challenge (35 runs, 58%, typically T6–T10).** Freezes flagship enforcement for the remainder of the run (run-20260825-002240: unresolved for eleven turns; run-20260825-060551; run-20260825-081623).
6. **rsi_onset (19 runs, 32%, T7–T18).** Recognized retrospectively via release cadence; the dominant driver of end-state divergence.
7. **Rival standards body and member-state noncompliance (29 and 16 runs).** The fragmentation turn (run-20260825-025927, run-20260825-032454; sole withdrawal in run-20260825-040955).
8. **Taiwan blockade (24 runs, 40%).** Converts AI policy into security policy and floors the economy (run-20260825-002043, run-20260825-011006).
9. **Late labour/protest cluster (T11–T18; labour waves in 40 runs, protests in 20).** Drives sentiment to hostility floors and anti-AI politics (run-20260825-013538, run-20260825-023012).

## Actor Dynamics

- **The Regulator** fielded roughly 10–16 measures per run, fully implemented almost none, and migrated doctrinally from multilateral-first to unilateral enforcement-first in most runs (run-20260825-011359, run-20260825-012812 — ending with labs recast as "de facto threat actors" — run-20260825-042817, run-20260824-234542). Its capacity metric barely moved regardless.
- **The United States** refused data-sharing and verification universally (run-20260825-005828's protocol left "operationally hollow"; run-20260824-223419; run-20260825-081608's three refused windows), with one partial compliance under sanction (run-20260825-022426).
- **China** converged steadily (turn-18 p90 = 87) and switched to standards export late — all 20 china_standards_export occurrences fall in turns 9–18 — bundling governance stacks with model sales (run-20260825-023012's ecosystem, run-20260824-231310).
- **Courts and emergent bodies were the regulator's most effective opponents**, ahead of any state: court challenges (58%), rival standards bodies (48%), certification consortia and open-source forks (singletons).
- **Industry leaked chronically**: whistleblower_disclosure fired in 52 of 60 runs, functioning as ambient legitimacy pressure rather than a discrete crisis. (Note: talent_drain_to_labs is defined in the scenario but never logged — see caveats.)
- **The public moved in one direction**: sentiment fell in every analyzed run, with protests (33%), strikes (42%), creator backlash (60%) and companion-harm scandals (35%) acting as a feedback loop on adoption depth rather than as independent shocks.

## Surprises and Outliers

- **Shut-gate catastrophe clusters.** Run-20260825-001102 drew a cyber campaign and Taiwan blockade together at their 4%/2% shut-gate rates plus a 3% crash; run-20260825-022620 opened with a 1% bio incident and later added a precursor-less blockade and crash; run-20260825-040755 opened with a 4% campaign with no recon wave ever recorded. If the specification's probabilities held, such clusters should be very rare; their recurrence is a finding about the simulation, not the world.
- **Run-20260824-223722** is the only run ending with incident pressure below its start.
- **Run-20260824-223114's** final-turn open-weight breakthrough reverses the run's entire concentration thesis.
- **Capacity gains in fast worlds**: run-20260824-232432 (50→66) and run-20260825-030256 (peak 68) contradict the prior that nothing works under acceleration — both rested on early, narrow, domestically enforceable measures.
- **`emergent_alignment_failure_narrow`** (one run, turn 12) is the ensemble's only alignment-failure event — statistically invisible but qualitatively the most consequential event class the scenario gestures at.
- **Rule-outcome breaks**: run-20260825-015102's open-weight release did not move the gap as the metric rules require; run-20260825-081553's gap snapped from 11 back to 27–29 unexplained; run-20260825-081608 shows capability surges "no stated rule grounds"; run-20260824-223756 breaches the 25-point turnover cap and its declared regime contradicts its metrics.

## Simulation Caveats

These are artifacts of the simulation, not findings about the world:

- **Model-configuration heterogeneity.** The ensemble statistics themselves warn that runs used different LLM configurations; outcome variation may reflect model differences rather than scenario stochasticity. No cross-model breakdown was provided, so this confound cannot be partitioned here.
- **Probability plumbing diverges from spec in both directions.** Repeatable events fire well below their evaluated per-turn probabilities (cyber_mass_campaign realized ≈0.05/turn vs ≈0.2 evaluated; negotiation_window similar), while shut-gate hits at claimed 1–3% rates appear constantly in the narratives. Eligibility windows were also violated: orbital_datacenter_success fired in turn 1 in one run (spec: not before turn 6), and open_weight_frontier_release fired before turn 4 in four runs.
- **Two scripted events never logged**: grid_capacity_crisis and talent_drain_to_labs have no entries in the event statistics.
- **Emergent-event zoo.** Roughly sixty `emergent_*` types appear, nearly all as singletons, with spelling variants fragmenting related counts (alliance formalisation/formalization/initiative). Several duplicate scripted precursors with different base rates (emergent_bio_uplift_findings 12 runs vs 35 scripted; emergent_cyber_recon_wave 7 vs 50; emergent_eval_anomaly_reports 3 vs 45), so precursor base rates depend on counting choices.
- **regulatory_capacity is nearly inert** (max IQR jump 2.0 across all events), which cripples it as an outcome measure for intervention questions; effects may exist that this metric cannot register.
- **Hidden regime labels.** PLATEAU/FAST/RLVR-LIMITED assignments were GM-only; some analysts saw them, others explicitly did not (run-20260825-052440), making regime-conditional claims unevenly grounded.
- **Truncated analyses and a lexical-only diversity metric** limit how finely narrative patterns can be verified; the 18-turn horizon also truncates dynamics that were still moving at run end (e.g., run-20260824-223114's final-turn breakthrough).

## Confidence Assessment

- **High confidence:** all frequencies and distributions (computed deterministically from 60 runs); the near-universality of the late-instrument pattern (present in virtually all 60 analyses); the monotone public-sentiment decline; regulatory-capacity stickiness; the rarity of negotiation-window conversion (2 of 53 window-bearing runs).
- **Moderate confidence:** turning-point sequencing and consequences (each is anchored in multiple named runs but rests on narrative reading); the indicator rankings in rq_early_signals; the no-regret candidate package; the sizes of the diffusion-capture and standards-war ending families (my own tallies, ◆ above).
- **Low confidence:** regime-conditional claims (regime labels mostly hidden and inferred indirectly); any quantitative early-versus-reactive effect (commitment timing was never measured — the scenario would need a per-turn measure-class ledger aligned with incident dates); small-n divergence associations (bio_incident at the turn-2 fork rests on n=3, algorithmic_bias_scandal on n=2); and any attribution of variation to scenario stochasticity versus model-configuration differences, which the provided data cannot separate.
