## Summary

The ensemble of 20 runs of "Forking Futures" reveals a world where AI governance is consistently reactive, not anticipatory. Despite the regulator’s intent to act early, instruments are chronically too slow to hit their policy windows. Capability grows steadily across all runs, with US systems reaching 61.8–75.0 and Chinese systems 51.0–66.0 by the end. The open-weight gap collapses from 30.0 to a median of 6.0, eroding the feasibility of containment. Incident pressure rises sharply, peaking in sustained crisis (median 58.0, max 95.0), driven by cyber, bio, and information-integrity events. Regulatory capacity ends slightly lower (median 47.0) than it began, undermined by legal challenges, coalition fragmentation, and overcommitment. Early interventions are rare and often ineffective; reactive responses dominate, especially after shocks like negotiation windows or mass incidents. Precursors like eval_anomaly_reports and cyber_recon_wave are common but inconsistently acted upon. No no-regret policy package emerges—measures succeed only in specific regimes or under specific conditions, and their benefits are fragile.

---

## Research Questions

### rq_early_vs_reactive

Early, broad interventions do not consistently beat reactive ones; in fact, reactive responses are more common and often more effective, especially after major shocks. Across 20 runs, only 2 (run-20260824-214357, run-20260825-081618) show clear early action on precursors (e.g., cyber_recon_wave or eval_anomaly_reports), and even then, the impact is limited. In 18 runs, the regulator responds only after a major incident (e.g., cyber_mass_campaign, bio_incident, or information_integrity_crisis), when political capital is temporarily cheaper (per rule 9). For example, in run-20260824-232950, the bio_incident at turn 2 triggers a surge in incident_pressure to 65, enabling the launch of AIRC-NET, but the measure never reaches full implementation. In run-20260825-032809, the regulator seizes a negotiation_window at turn 4 to pass the Bilateral Compute Transparency Accord, but covert_defection undermines it by turn 17. Early action fails when precursors are ignored (e.g., eval_anomaly_reports in run-20260825-022620) or when measures are too slow (e.g., the International Evaluation Network in run-20260824-234542 takes 6 turns to implement). Reactive action succeeds only when it aligns with a temporary political opening, but even then, enforcement is often blocked by courts or noncompliance. Thus, early interventions are neither more effective nor more common; reactivity is the dominant pattern.

### rq_early_signals

The most reliable precursors are eval_anomaly_reports, cyber_recon_wave, and bio_uplift_findings, but they have high false-positive rates. eval_anomaly_reports fires in 16 of 20 runs (80%), and in 10 of those, it precedes a capability_jump (50% true positive rate). However, in 6 runs (e.g., run-20260825-003831), eval_anomaly_reports fires but no jump occurs. cyber_recon_wave fires in 19 of 20 runs (95%), and in 18, it precedes a cyber_mass_campaign (90% true positive rate), but in 1 run (run-20260825-032809), it fires without a campaign. bio_uplift_findings fires in 15 of 20 runs (75%), but only 7 lead to a bio_incident (47% true positive rate). Other precursors like funding_round_pulled (50% occurrence) and taiwan_tension_rise (90% occurrence) are common but less predictive: funding_round_pulled leads to ai_market_crash in only 8 of 10 cases (80% true positive), and taiwan_tension_rise leads to taiwan_blockade in only 8 of 18 cases (44% true positive). The false-positive rate is high because precursors are probabilistic and often ignored by the regulator. For example, in run-20260825-022620, bio_uplift_findings fires at turn 1 but is ignored, and bio_incident fires at turn 1 without the gate being open. Thus, while these precursors are worth monitoring, their predictive power is limited by implementation delays and stochastic event resolution.

### rq_no_regret

There are no no-regret policy packages—no combination of measures consistently improves outcomes across all three trajectory regimes. Measures that work in one regime fail in others. For example, limits-and-restrictions (category 3) reduce incident_pressure in runs with high capability growth (e.g., run-20260825-025927), but they fail in diffusion-heavy runs (e.g., run-20260825-044737) where openweight_gap is already low. Preparedness and response (category 5) measures like cyber_resilience_stress_testing reduce cyber_mass_campaign impact in 6 of 8 runs where they are implemented (e.g., run-20260825-060551), but they are ineffective in runs with sustained incident_pressure (e.g., run-20260825-002240). Capacity-building (category 1) measures like build_own_evaluation_capacity increase regulatory_capacity in 7 of 10 runs (e.g., run-20260825-081548), but they are undermined by emergent_court_challenge in 5 runs (e.g., run-20260825-032809). No package of measures—such as combining category 1, 3, and 5—shows consistent benefits. For instance, in run-20260824-214357, the regulator implements multiple measures, but regulatory_capacity still declines to 46.0. In run-20260825-040955, detection-and-disruption measures succeed temporarily, but judicial rulings suspend them by the end. Thus, no combination of measures is universally beneficial; effectiveness depends on regime, timing, and external shocks.

---

## Outcome Patterns

1. **Sustained Crisis (12 runs)**: Incident pressure remains above 60 for most of the run, driven by repeated cyber_mass_campaigns, bio_incidents, or information_integrity_crisis. Regulatory capacity erodes due to overcommitment and legal challenges. Examples: run-20260825-025927 (incident_pressure peaks at 95.0), run-20260825-040955 (pinned at 85.0), run-20260825-002240 (ends at 44.0 after decay).  
2. **Diffusion-Driven Collapse (5 runs)**: The open-weight gap collapses early (by turn 6–8), making containment impossible. The regulator shifts to detection and monitoring, but enforcement fails. Examples: run-20260825-044737 (gap to 5.0), run-20260825-081548 (to 0.0), run-20260825-003831 (to 19.0).  
3. **Boom-and-Bust Regulation (3 runs)**: An ai_market_crash or taiwan_blockade disrupts the economic context, making restriction cheaper but irrelevant. Capability growth slows, but regulatory capacity does not recover. Examples: run-20260824-223947 (crash at turn 13), run-20260825-060551 (crash at turn 11), run-20260825-081603 (crash at turn 6).  
4. **Diplomatic Failure (1 run)**: A negotiation_window opens but is missed due to lack of prepared proposal. The regulator pivots to unilateral action, but legitimacy suffers. Example: run-20260825-013538 (window at turn 3 missed).  
5. **Judicial Paralysis (1 run)**: An emergent_court_challenge suspends enforcement of key measures, rendering the regulator powerless despite high capacity. Example: run-20260825-060551 (challenge from turn 8 onward).  

---

## Recurring Turning Points

- **Precursor Ignored, Harm Follows**: In 15 runs, a precursor (e.g., eval_anomaly_reports, cyber_recon_wave) fires but is not acted upon, followed by a major incident. For example, in run-20260825-022620, eval_anomaly_reports fires at turn 1, but no action is taken, and bio_incident fires at turn 1. In run-20260825-003831, cyber_recon_wave at turn 1 is ignored, and cyber_mass_campaign fires at turn 2.  
- **Shock Triggers Reactive Pivot**: In 18 runs, a major incident (e.g., cyber_mass_campaign, bio_incident) causes the regulator to abandon multilateralism and adopt unilateral or coalition-based action. For example, in run-20260824-232950, the bio_incident at turn 2 leads to the launch of AIRC-NET and a doctrinal shift. In run-20260825-051555, the first cyber_mass_campaign at turn 2 breaks the diplomacy-first doctrine.  
- **Negotiation Window Missed**: In 14 runs, a negotiation_window opens but closes without agreement, often because the regulator lacks a draft proposal. For example, in run-20260825-013538, the window at turn 3 is missed due to resource reallocation. In run-20260825-025927, the window at turn 6 closes with no engagement.  
- **Open-Weight Release Ends Containment**: In 10 runs, open_weight_frontier_release fires, collapsing the openweight_gap and forcing a shift to detection. For example, in run-20260824-223756, the release at turn 6 invalidates the Bio-Risk Early Monitoring Framework. In run-20260825-044737, the release at turn 4 sets the causal spine of the run.  
- **Legal Challenge Freezes Enforcement**: In 8 runs, an emergent_court_challenge suspends key measures. For example, in run-20260825-002240, the challenge at turn 8 freezes the emergency toolkit. In run-20260825-060551, the challenge from turn 8 onward paralyzes red-teaming mandates.  

---

## Actor Dynamics

The regulator is the sole actor, but its effectiveness is shaped by systemic forces: markets, labs, states, and the public. The regulator consistently overcommits, launching 10–16 measures across 18 turns, but few reach full implementation due to lead times and capital costs. In 12 runs, the regulator’s capacity is drained by concurrent measures, leading to a median end capacity of 47.0. The US and China are modeled as external forces: their capability growth is autonomous, and they rarely bind themselves to agreements. For example, in run-20260825-032809, the Bilateral Compute Transparency Accord is undermined by covert_defection. Labs act through disclosures: whistleblower_disclosure fires in 18 runs, often confirming safety overrides (e.g., run-20260825-044737). The public responds to harm: public_sentiment_to_ai falls below 30 in 14 runs after incidents, but rebounds only in 2 (e.g., run-20260825-081603, due to rule-violating recovery). Markets react to shocks: ai_market_crash occurs in 8 runs, but economic_context often recovers unrealistically (e.g., +25.0 in run-20260825-081603). The regulator’s identity shifts from multilateral convenor to unilateral enforcer, but this shift is not matched by real authority.

---

## Surprises and Outliers

- **Gate-Shut Shocks**: In 6 runs, major events fire through closed gates: bio_incident at 1% probability in run-20260825-022620 (turn 1), taiwan_blockade at 2% in run-20260825-011006 (turn 3), ai_market_crash at 3% in run-20260825-081603 (turn 6). These tail events keep the regulator reactive.  
- **Unexplained Capability Jumps**: In run-20260825-011006, us_capability jumps +11.0 at turn 8 with no capability_jump event or narrative cause. In run-20260825-081603, +9.0/+8.0 jumps occur with no mechanism.  
- **Metric Cap Violations**: In 8 runs, incident_pressure moves exceed the 25-point cap (e.g., +36.0 in run-20260825-002240), and in 5, economic_context recovers by +25.0 (e.g., run-20260825-081603), violating rule 12. These are often unflagged by the referee.  
- **One-Off Event**: emergent_bio_framework_leak in run-20260824-223756 (turn 9) reveals internal suppression, damaging credibility. This emergent event fires only once.  
- **End-State Anomaly**: In run-20260825-081603, economic_context ends at 78.0, above its start of 65.0, despite a market crash—undermining the scenario’s premise that shocks cheapen restriction.  

---

## Simulation Caveats

- **Event Ledger Inconsistencies**: In 12 runs, the occurred_events metadata list omits clearly narrated events (e.g., cyber_mass_campaign in run-20260825-025927) or includes unverified ones (e.g., taiwan_blockade in run-20260825-044737). Event history should be reconstructed from turn artifacts.  
- **Metric Rule Violations**: Multiple runs violate core rules: incident_pressure exceeds 25-point cap (8 runs), economic_context recovery exceeds +6 per turn (5 runs), capability stalls below floor rates (6 runs). The constitutional referee often fails to flag these.  
- **Gate Logic Drift**: In 5 runs, event probabilities do not match stated gate conditions (e.g., cyber_mass_campaign at gate-shut rates despite active recon_wave). This suggests sampling or implementation errors.  
- **Regime Signal Confusion**: In run-20260825-051555, regime signals conflict: eval_anomaly_reports rate matches PLATEAU, but cyber_recon_wave rate matches RLVR-LIMITED. This may reflect model configuration differences.  
- **Measure Phase Freezing**: In 4 runs, measures like the International AI Red-Teaming Accord (run-20260825-044737) remain at “lead time: 1 turn” for 15+ turns, suggesting bookkeeping defects.  
- **Model Configuration Differences**: The ensemble caveat notes that runs use different model configurations, which may explain outcome variation beyond scenario stochasticity.  

---

## Confidence Assessment

Confidence is **moderate** in the overall patterns due to consistent metric trajectories (e.g., rising incident_pressure, falling openweight_gap) and high-frequency events (e.g., 90% cyber_mass_campaign). However, confidence is **low** in causal claims due to widespread data quality issues: event ledger mismatches, metric cap violations, and gate logic drift. The per-run analyses are valuable for narrative detail but often contradict the ensemble statistics (e.g., on event timing or measure implementation). The declared research questions can be answered with moderate confidence for rq_early_vs_reactive and rq_early_signals, as they align with observable event sequences. rq_no_regret is answerable with low confidence due to the lack of consistent measure success. The simulation’s integrity is compromised by unflagged rule violations and inconsistent refereeing, which may distort outcomes. A dedicated model-sensitivity analysis is needed to disentangle scenario effects from model differences.
