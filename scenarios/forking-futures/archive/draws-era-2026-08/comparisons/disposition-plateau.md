## Summary

The comparison of two cohorts—**Forking Futures** (20 runs) and **Forking Futures — Urgent Regulator** (8 runs)—reveals that while both face similar structural pressures (capability growth, incident escalation, collapsing open-weight gap), the **timing and nature of regulatory action** meaningfully alters outcomes. The "Urgent Regulator" cohort shows modest improvements in regulatory capacity and reduced incident pressure, but at the cost of higher market instability and legal friction. Early signals like *eval_anomaly_reports* and *cyber_recon_wave* are more predictive in the base cohort, but their utility diminishes when the regulator acts preemptively—suggesting that urgency changes the signal landscape. No no-regret policy package emerges across both cohorts, though investment in technical evaluation and detection shows consistent relative value. Differences are real but narrow: the urgent regulator slightly improves containment and sentiment but fails to prevent systemic risks. Simulation artifacts—small cohort size, model configuration drift, and metric rule violations—moderate confidence, especially in causal claims.

---

## Cohorts Compared

### Forking Futures

The base cohort of 20 runs depicts a world where regulation is consistently reactive. Despite intentions, the regulator fails to act early on precursors, and interventions are often too slow to close policy windows. Capability grows steadily (US: 66.0, CN: 59.9), the openweight gap collapses to 10.3, and incident pressure rises to 62.2. Regulatory capacity declines slightly (47.0), undermined by legal challenges and overcommitment. The dominant pattern is **sustained crisis**, with most runs experiencing repeated cyber, bio, and information-integrity incidents. Early interventions are rare and ineffective; reactivity dominates, especially after shocks like *bio_incident* or *cyber_mass_campaign*. The regulator shifts from multilateralism to unilateral enforcement, but legitimacy and capacity erode. No policy package proves universally beneficial—effectiveness depends on regime, timing, and external shocks.

### Forking Futures — Urgent Regulator

In this 8-run cohort, the regulator acts earlier and with greater urgency, leading to modest gains. US and Chinese capabilities converge more closely (65.1 vs 61.6), the openweight gap narrows further (7.9), and incident pressure is lower (57.9). Regulatory capacity is slightly higher (49.0), reflecting institutional resilience, though economic context deteriorates more sharply (46.0). The regulator pivots faster from containment to detection, especially after early *open_weight_frontier_release* events. While still overwhelmed by systemic risks, the urgent regulator avoids some worst-case outcomes—fewer algorithmic bias scandals (12% vs 30%), less public backlash (datacenter protests: 12% vs 35%). However, this comes with trade-offs: more *ai_market_crash* (75% vs 40%) and *covert_defection* (38% vs 15%), suggesting that aggressive action triggers market and diplomatic instability. The cohort shows a clearer shift toward **managed crisis** or **stabilized fragmentation**, but not systemic control.

---

## Research Questions

### rq_early_vs_reactive

**Do early, broad interventions beat reactive ones in outcomes — in which regimes, and under what conditions?**

- **Forking Futures**: Early interventions are rare and ineffective. Only 2 of 20 runs show clear early action, and even then, impact is limited. Reactive responses dominate (18 of 20 runs), often triggered by *bio_incident* or *cyber_mass_campaign*. These succeed only when political capital is temporarily available, but enforcement is frequently blocked by courts or noncompliance.  
- **Forking Futures — Urgent Regulator**: The regulator acts earlier, especially on *eval_anomaly_reports* and *cyber_recon_wave*, but this does not consistently prevent major incidents. Instead, early action shifts the failure mode: containment fails earlier, but detection and crisis management improve. Reactive pivots still occur, but from a position of slightly higher capacity.

**Overall answer**: Early interventions do **not** consistently beat reactive ones. In both cohorts, reactivity dominates. However, **early investment in technical evaluation capacity** (e.g., Independent Evaluation Constellation) shows relative benefit in the urgent cohort, enabling faster response when crises hit. The key determinant is not early action *per se*, but whether the regulator adapts to **collapsing openweight gap** before a major incident overwhelms capacity. This adaptation is more common—but not guaranteed—in the urgent cohort.

---

### rq_early_signals

**Which precursor developments precede the largest divergences between runs, and are therefore worth monitoring?**

- **Forking Futures**: *eval_anomaly_reports* (80% occurrence) precedes *capability_jump* in 50% of cases (10 of 20). *cyber_recon_wave* (95%) precedes *cyber_mass_campaign* in 90% (18 of 20). *bio_uplift_findings* (75%) precedes *bio_incident* in 47% (7 of 15). *funding_round_pulled* (50%) precedes *ai_market_crash* in 80% (8 of 10). High false-positive rates limit predictive power.
- **Forking Futures — Urgent Regulator**: *eval_anomaly_reports* occurs in only 38% of runs (3 of 8), and *capability_jump* in 62%—suggesting weaker correlation. *cyber_recon_wave* (88%) still precedes *cyber_mass_campaign* in all 7 cases. *bio_uplift_findings* (75%) precedes *bio_incident* in all 3 cases (100% true positive). *funding_round_pulled* (25%) precedes *ai_market_crash* in both cases, but 4 of 6 crashes occur without it.

**Overall answer**: The most reliable precursors are **cyber_recon_wave** (high sensitivity and specificity) and **bio_uplift_findings** (high specificity, especially in urgent cohort). *eval_anomaly_reports* is less reliable when the regulator acts early, possibly because early action suppresses or alters the signal. *funding_round_pulled* is sufficient but not necessary for *ai_market_crash*. The urgent cohort shows **lower occurrence of some precursors**, suggesting that early regulatory action may suppress or accelerate certain pathways. Monitoring should focus on **cyber, bio, and market signals**, with context-dependent interpretation.

---

### rq_no_regret

**Are there no-regret packages: combinations of measures that are never worse and often better across all three trajectory regimes?**

- **Forking Futures**: No no-regret package exists. Measures succeed only in specific regimes. Limits-and-restrictions (category 3) reduce incident pressure in high-growth runs but fail in diffusion-heavy ones. Preparedness (category 5) helps in some cyber scenarios but not under sustained pressure. Capacity-building (category 1) increases regulatory capacity in 7 of 10 runs but is undermined by legal challenges. No combination shows consistent benefit.
- **Forking Futures — Urgent Regulator**: A **combination of category 1 (evaluation/audit) and category 4 (agent monitoring, weight security)** shows relative consistency. These measures improve regulatory capacity in 5 of 8 runs and help contain *agent_supply_chain_compromise*. However, they do not prevent capability diffusion or incident escalation. Category 3 (limits) fails in 6 of 8 runs due to diplomatic resistance.

**Overall answer**: There is **no true no-regret package** across both cohorts. However, **technical evaluation and post-deployment detection** (categories 1 and 4) come closest, showing consistent relative value even when containment fails. This suggests that **adaptive, technical capabilities** are more robust than binding agreements or broad restrictions. The package is not universally superior, but it is **never worse** and often better—especially in diffusion-heavy or crisis-prone regimes.

---

## Between-Group Differences

### Regulatory Capacity and Incident Pressure
- **Difference**: The urgent regulator achieves **higher regulatory capacity** (49.0 vs 47.0) and **lower incident pressure** (57.9 vs 62.2).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm the difference. Syntheses align: urgent cohort emphasizes institutional resilience and faster pivoting.

### Openweight Gap
- **Difference**: The openweight gap is **smaller** in the urgent cohort (7.88 vs 10.34).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics show a clear gap. Syntheses note earlier *open_weight_frontier_release* (7 of 8 runs) in urgent cohort, suggesting urgency accelerates diffusion.

### Economic Context
- **Difference**: Economic context is **worse** in the urgent cohort (46.0 vs 53.85).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm. Syntheses note more *ai_market_crash* (75% vs 40%) and *funding_round_pulled* (25% vs 50%), suggesting regulatory urgency destabilizes markets.

### Public Sentiment to AI
- **Difference**: Public sentiment is **slightly better** in the urgent cohort (30.75 vs 28.0).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics show modest improvement. Syntheses note fewer *algorithmic_bias_scandal* (12% vs 30%) and *datacenter_protest_wave* (12% vs 35%), suggesting early action reduces visible harms.

### Event Occurrence: ai_market_crash
- **Difference**: *ai_market_crash* occurs **more frequently** in the urgent cohort (75% vs 40%).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm. Syntheses suggest early regulatory action increases market uncertainty.

### Event Occurrence: eval_anomaly_reports
- **Difference**: *eval_anomaly_reports* occurs **less frequently** in the urgent cohort (38% vs 80%).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm. Syntheses suggest early action may suppress or alter the signal, reducing its utility as a precursor.

### Event Occurrence: open_weight_frontier_release
- **Difference**: *open_weight_frontier_release* occurs **more frequently** in the urgent cohort (88% vs 50%).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm. Syntheses note this event forces earlier pivot to detection.

### Event Occurrence: algorithmic_bias_scandal
- **Difference**: *algorithmic_bias_scandal* occurs **less frequently** in the urgent cohort (12% vs 30%).
- **Cohorts**: *Forking Futures — Urgent Regulator* vs *Forking Futures*.
- **Evidence**: Statistics confirm. Syntheses suggest early detection reduces public-facing harms.

### Notable Non-Differences
- **US and CN capability**: Nearly identical (66.03 vs 65.12 and 59.91 vs 61.61). Despite different regulatory postures, capability growth is autonomous and unaffected.
- **bio_incident**: Occurs at nearly identical rates (35% vs 38%). Early action does not reduce bio risk.
- **taiwan_tension_rise**: 90% vs 100%—no meaningful difference. Geopolitical precursors are robust across cohorts.

---

## Similarities Across Cohorts

- **Capability growth**: Both cohorts show steady US and Chinese capability advancement, with minimal divergence. The regulator has little influence on this metric.
- **Incident pressure**: High and rising in both cohorts, driven by *cyber_mass_campaign*, *information_integrity_crisis*, and *labour_displacement_wave*. Crisis is the default state.
- **Collapse of openweight gap**: In both cohorts, the gap narrows significantly, undermining containment strategies. The difference is in timing and degree, not outcome.
- **Regulator pivot**: In both, the regulator shifts from multilateral diplomacy to unilateral enforcement as cooperation fails. This shift is narratively and statistically consistent.
- **Precursor utility**: *cyber_recon_wave* and *bio_uplift_findings* are reliable predictors in both cohorts, though their frequency and impact vary.
- **No no-regret package**: Neither cohort supports the existence of a universally beneficial policy combination. Effectiveness remains regime- and timing-dependent.

---

## Simulation Caveats

- **Cohort size imbalance**: The urgent cohort has only 8 runs vs 20 in the base, limiting statistical power and generalizability. Confidence in differences is moderated.
- **Model configuration drift**: Both syntheses note that runs used different model configurations (e.g., LLM blocks), meaning outcome variation may reflect model differences rather than scenario stochasticity.
- **Metric rule violations**: Multiple runs in both cohorts violate constitutional rules (e.g., incident_pressure exceeding 25-point cap, economic_context recovery too fast). These distort outcome interpretation.
- **Event ledger inconsistencies**: In both cohorts, narrated events sometimes mismatch metadata (e.g., *cyber_mass_campaign* missing from logs), requiring manual reconstruction.
- **Gate logic drift**: Some events fire at probabilities inconsistent with gate conditions, suggesting sampling or implementation errors.
- **Small-N dynamics**: With only 8 runs in the urgent cohort, rare events (e.g., *emergent_multilateral_coordination_group*) may be over- or under-represented.

---

## Confidence Assessment

Confidence in **descriptive patterns** (metric trajectories, event frequencies) is **high**, as they are grounded in cohort statistics. Differences in regulatory capacity, incident pressure, and openweight gap are statistically supported.

Confidence in **causal claims** (e.g., early action causes better outcomes) is **moderate to low**, due to simulation artifacts: rule violations, model configuration drift, and small cohort size in the urgent arm.

Confidence in **research question answers**:
- **rq_early_vs_reactive**: Moderate. Statistics support reactivity as dominant; syntheses agree on mechanism.
- **rq_early_signals**: Moderate. Precursor-event links are quantifiable, but false-positive rates and cohort differences limit predictive clarity.
- **rq_no_regret**: Low. No package is universally beneficial; the "closest" candidate (categories 1 and 4) shows only relative consistency.

Overall, the comparison yields **meaningful insights** about the trade-offs of regulatory urgency, but **simulation integrity issues** caution against overgeneralization. Additional runs with consistent model configurations would improve confidence.
