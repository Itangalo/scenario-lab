## Summary

The two cohorts—**Forking Futures** (20 runs) and **Forking Futures — Urgent Regulator** (8 runs)—simulate the same scenario under different regulatory assumptions: one with a standard regulator, the other with an "urgent" variant presumed to act earlier and more decisively. Despite this design intent, the cohorts show **limited divergence in final outcomes**, with nearly identical levels of US and Chinese capability, incident pressure, and regulatory capacity. However, they diverge sharply in **event dynamics**: the urgent regulator suppresses market and open-weight risks but increases bio-incident likelihood and triggers new legal and institutional backlashes. Syntheses from each cohort suggest differing interpretations—especially on the value of early action—but statistics reveal that **early interventions did not consistently improve outcomes**. Both cohorts suffer from simulation artifacts, including implausible metric jumps and inconsistent event gate logic, which undermine confidence in fine-grained causal claims. The most robust finding is that **precursor events like *eval_anomaly_reports* and *cyber_recon_wave* reliably precede major escalations**, particularly in the urgent cohort.

---

## Cohorts Compared

### Forking Futures

The standard cohort of 20 runs ends in a state of **reactive crisis management**, where regulatory action consistently follows harm rather than preventing it. Despite initial multilateral ambitions, the regulator is overwhelmed by early shocks—especially *ai_market_crash* and *cyber_mass_campaign*—which occur in nearly all runs by turn 2. Interventions are delayed, and when implemented, they fail to halt rising incident pressure or close the openweight gap, which narrows to a mean of 16.32. Regulatory capacity erodes slightly (from 50 to 46.7), and public sentiment to AI remains low (29.1). The synthesis attributes this to systemic inertia and broken precursor chains, with rare early signals like *funding_round_pulled* failing to trigger timely responses. The cohort is marked by **institutional fragmentation**, including court challenges, rival standards bodies, and member-state noncompliance. However, the analysis is undermined by **severe calibration issues**: unexplained capability jumps, cap breaches, and event gate misfires suggest simulation artifacts may distort outcomes.

### Forking Futures — Urgent Regulator

The urgent regulator cohort (8 runs) shows **more proactive intervention**, with earlier measures targeting evaluation, transparency, and coalition-building. This cohort avoids the *ai_market_crash* in 75% of runs (vs. 20% in standard) and suppresses *open_weight_frontier_release* (25% vs. 65%). However, it suffers **more bio_incidents** (50% vs. 20%) and sees **new emergent legal crises**, including *emergent_court_ruling_against_mandate* and *emergent_regulator_crisis_of_legitimacy*, which do not occur in the standard cohort. Despite the "urgent" design, final metrics are nearly identical: US capability (64.25 vs. 64.61), incident pressure (55.25 vs. 56.9), and regulatory capacity (48.0 vs. 46.7). The openweight gap is **worse** (22.0 vs. 16.32), suggesting containment failed more severely. The synthesis interprets early actions as partially effective, especially when narrow and institutionally resilient, but statistics show **no clear net benefit**. The small run count and use of varied model configurations limit confidence in the cohort’s representativeness.

---

## Research Questions

### rq_early_vs_reactive

**Do early, broad interventions beat reactive ones in outcomes — in which regimes, and under what conditions?**

- **Forking Futures**: Early interventions are rare and ineffective. In 19 of 20 runs, major measures follow shocks like *ai_market_crash* or *cyber_mass_campaign*. The synthesis concludes early action fails to improve outcomes, with no correlation between timing and metrics like regulatory capacity or public sentiment.
- **Forking Futures — Urgent Regulator**: Early measures show mixed results. Narrow, coalition-backed interventions (e.g., pre-release evaluations) reduce *capability_jump* likelihood, but broad mandates are struck down in court. Reactive measures post-crisis gain political traction but arrive too late.

**Overall Answer**: **No**, early, broad interventions do not consistently beat reactive ones. The statistics show **no meaningful improvement** in final outcomes: US capability, incident pressure, and regulatory capacity are nearly identical across cohorts. While the urgent regulator avoids *ai_market_crash* (25% vs. 80%) and *open_weight_frontier_release* (25% vs. 65%), it suffers **more bio_incidents** (50% vs. 20%) and **new legal backlashes**. The condition for early success appears to be **narrow scope and institutional resilience**, not timing alone. However, the small size and model variability of the urgent cohort limit confidence in this conclusion.

---

### rq_early_signals

**Which precursor developments precede the largest divergences between runs, and are therefore worth monitoring?**

- **Forking Futures**: *funding_round_pulled* and *cyber_recon_wave* are highlighted as key precursors. *funding_round_pulled* precedes *ai_market_crash* in only 8 of 15 occurrences (47% false positive), and *cyber_recon_wave* precedes *cyber_mass_campaign* in 18 of 19 runs (95% success). However, *bio_uplift_findings* never precedes *bio_incident*, indicating a broken chain.
- **Forking Futures — Urgent Regulator**: *eval_anomaly_reports* precedes *capability_jump* in 6 of 6 cases (100% true positive), *cyber_recon_wave* in 6 of 8 *cyber_mass_campaigns* (75%), and *bio_uplift_findings* in 4 of 4 *bio_incidents* (100% true positive, but 80% false positive rate).

**Overall Answer**: The most reliable precursors are **eval_anomaly_reports** (predicts *capability_jump*), **cyber_recon_wave** (predicts *cyber_mass_campaign*), and **funding_round_pulled** (predicts *ai_market_crash*). *eval_anomaly_reports* has a **100% true positive rate** in the urgent cohort and 65% occurrence overall. *cyber_recon_wave* fires in 95% of standard runs and 75% of urgent runs, preceding *cyber_mass_campaign* in nearly all cases. *funding_round_pulled* has high false positives (47%) but is strongly associated with *ai_market_crash* when it fires. *bio_uplift_findings* is **noisy** (50% occurrence, 80% false positive) but never fails to precede *bio_incident* when it does occur. These precursors are **worth monitoring**, especially *eval_anomaly_reports* and *cyber_recon_wave*, which show high predictive validity.

---

### rq_no_regret

**Are there no-regret packages: combinations of measures that are never worse and often better across all three trajectory regimes?**

- **Forking Futures**: No no-regret packages exist. Every measure category fails in at least one run: evaluation measures trigger constitutional crises, restrictions are circumvented, and adoption measures backfire. The synthesis finds no combination that improves outcomes across regimes.
- **Forking Futures — Urgent Regulator**: No universal no-regret package, but **coalition-building** (e.g., *alliance_bloc_forms*) shows relative resilience, associated with higher US and Chinese capability and no clear downside. However, it only forms in 3 of 8 runs and does not prevent major incidents.

**Overall Answer**: **No**, there are no no-regret policy packages that are **never worse and often better** across all regimes. While **coalition-building** (category 7) shows promise—occurring in 38% of urgent runs vs. 55% of standard, and associated with higher capability and stability—it does not consistently improve other metrics. All other measure categories carry trade-offs: limits reduce capability jumps but trigger evasion, preparedness measures erode capacity under pressure, and transparency efforts invite legal challenges. The statistics confirm **no measure combination dominates across cohorts**, and the small run count prevents identifying robust patterns.

---

## Between-Group Differences

### Event Occurrence: Market and Open-Weight Stability vs. Bio-Risk

- **Difference**: The **urgent regulator** cohort sees **fewer market crashes and open-weight releases** but **more bio_incidents**.
- **Cohorts**: 
  - *ai_market_crash*: 25% in urgent vs. 80% in standard.
  - *open_weight_frontier_release*: 25% vs. 65%.
  - *bio_incident*: 50% vs. 20%.
- **Finding**: The urgent regulator suppresses some risks but **exacerbates others**, suggesting **risk substitution** rather than reduction.

### Emergent Institutional Backlash

- **Difference**: The **urgent regulator** triggers **new legal and legitimacy crises** absent in the standard cohort.
- **Cohorts**: 
  - *emergent_court_ruling_against_mandate*, *emergent_regulator_crisis_of_legitimacy*, *emergent_regulatory_backlash*, and *emergent_staffing_crisis* all occur at **12%** in the urgent cohort (1 run each) and **0%** in standard.
- **Finding**: Proactive regulation increases **institutional friction**, possibly due to overreach or faster implementation.

### Precursor Reliability

- **Difference**: *eval_anomaly_reports* is a **perfect predictor** of *capability_jump* in the urgent cohort but only **65% correlated** in standard.
- **Cohorts**: 
  - *eval_anomaly_reports* → *capability_jump*: 100% true positive in urgent (6/6), but only 7/13 in standard (54%).
- **Finding**: The urgent cohort shows **tighter precursor-event coupling**, possibly due to better gate logic or model configuration.

### Openweight Gap Worsening

- **Difference**: Despite more urgent action, the **openweight gap is wider** in the urgent cohort.
- **Cohorts**: 22.0 (urgent) vs. 16.32 (standard).
- **Finding**: Earlier intervention **did not improve containment**, suggesting diffusion is driven by factors outside regulator control.

### Similarities Examined but Not Found to Differ

- **US and Chinese capability**: Nearly identical (64.61 vs. 64.25 and 61.81 vs. 61.81).
- **Incident pressure**: 56.9 vs. 55.25 — no meaningful difference.
- **Regulatory capacity**: 46.7 vs. 48.0 — slight edge to urgent, but within noise.
- **Public sentiment to AI**: 29.1 vs. 31.75 — modest improvement, not statistically significant given cohort sizes.
- **taiwan_tension_rise**: 95% vs. 75% — higher in standard, but not decisive.

---

## Similarities Across Cohorts

- **High incident pressure**: Both cohorts end with incident pressure above 55, driven by recurring *cyber_mass_campaign* (90% and 100%) and *information_integrity_crisis* (85% and 100%).
- **Regulatory erosion**: Despite different starting assumptions, regulatory capacity remains flat or slightly declines in both (46.7 → 48.0), indicating systemic strain.
- **Capability convergence**: US and Chinese capabilities converge within 3–5 points in both cohorts, reflecting competitive parity.
- **Precursor prevalence**: *cyber_recon_wave*, *whistleblower_disclosure*, and *funding_round_pulled* are common in both, suggesting robust early signals.
- **Failure of multilateralism**: Binding agreements fail in both; *alliance_bloc_forms* occurs but rarely leads to enforcement.
- **Public sentiment decline**: AI sentiment remains below 32 in both, indicating persistent public concern.

---

## Simulation Caveats

- **Calibration failures in standard cohort**: The synthesis reports **12+ instances** of 25-point cap breaches (e.g., *incident_pressure* +35), unexplained *capability_jump* events, and event gate misfires (e.g., *taiwan_blockade* firing at 2% probability). These suggest **broken mechanics**, not scenario dynamics.
- **Small cohort size in urgent regulator**: Only **8 runs**, below the 10+ recommended for stable frequencies. Low-probability events (e.g., *orbital_datacenter_success* at 12%) lack statistical power.
- **Model configuration drift**: The urgent cohort used **different model versions**, risking that differences reflect **model artifacts**, not regulatory urgency.
- **Narrative telegraphing**: Some urgent runs **revealed trajectory regimes** in internal notes, violating the hidden regime rule and potentially biasing outcomes.
- **Unreliable metadata**: *occurred_events* logs omit narrated events, and metric-rule violations (e.g., no decay in *incident_pressure*) suggest **inconsistent simulation logic**.
- **Overinterpretation risk**: Both syntheses attribute outcomes to regulator agency, but statistics show **minimal metric divergence**, suggesting **systemic forces dominate**.

---

## Confidence Assessment

Confidence in the findings is **low to moderate**. The **standard cohort** suffers from **severe calibration issues**—cap breaches, event gate failures, and implausible metric jumps—that undermine trust in its results. The **urgent cohort** has fewer runs (8) and uses **inconsistent model configurations**, limiting comparability. However, **some patterns are robust**: *cyber_mass_campaign* and *eval_anomaly_reports* occur at high rates in both, and *eval_anomaly_reports* perfectly predicts *capability_jump* in the urgent cohort. The **lack of divergence in final metrics** despite different regulatory assumptions suggests **systemic constraints dominate** over policy timing. Confidence is **moderate for rq_early_signals** (precursor reliability is statistically supported) and **low for rq_early_vs_reactive** and **rq_no_regret**, as the cohorts do not show clear, consistent differences in outcomes. A **re-run with fixed mechanics and consistent models** is needed to draw reliable policy conclusions.
