## Summary

The "Forking Futures" scenario explores how regulatory effectiveness varies under different AI development speeds, with a focus on early intervention, precursor signals, and no-regret policy packages. Two cohorts were run: the base **Forking Futures** (20 runs) and an experimental variant, **Forking Futures — Urgent Regulator** (8 runs), which introduced a more proactive regulatory stance. Despite differences in narrative emphasis and some divergent event patterns, both cohorts converge on core dynamics: rapid capability growth, high incident pressure, and stagnant regulatory capacity. The urgent regulator condition does not yield systematically better outcomes. In fact, it sees higher rates of market crashes and bio-incidents, and lower economic performance. Key precursors like *eval_anomaly_reports* and *cyber_recon_wave* are validated across cohorts as reliable early signals, but no no-regret policy packages emerge. Differences in outcomes appear more attributable to stochastic event clustering and cohort-specific model configurations than to the regulator’s urgency. The small size and technical heterogeneity of the urgent cohort limit confidence in strong comparative claims.

---

## Cohorts Compared

### Forking Futures

The base cohort of 20 runs ends in a high-capability, high-incident crisis in most cases: US capability averages 94.67, incident pressure 78.35, and public sentiment remains low (21.45). Regulatory capacity stagnates near 50.05, and the openweight gap widens to 58.35 on average. The trajectory is defined by recurring tail-event clusters—such as *taiwan_blockade*, *cyber_mass_campaign*, and *rsi_onset*—that overwhelm slow-moving regulatory instruments. Early interventions are frequently delayed or struck down by *emergent_court_challenge* (65% occurrence), while reactive measures arrive too late. The most reliable early signals are *eval_anomaly_reports* (80% occurrence), which precede *rsi_onset* in 14 of 16 cases. Despite varied narratives, outcomes are uniformly poor, with no policy package consistently improving results. The cohort shows moderate divergence in outcomes, driven by timing of shocks and legal fractures.

### Forking Futures — Urgent Regulator

This cohort of 8 runs exhibits a more compressed, crisis-driven arc under what appears to be a consistently FAST development regime. US capability reaches 92.81 on average, slightly lower than the base cohort, but incident pressure is marginally lower (75.25), while economic context is significantly worse (37.38 vs. 45.75). Regulatory capacity remains flat at 50.0, despite the regulator’s early and aggressive posture. The cohort sees higher rates of *ai_market_crash* (88% vs. 40%) and *bio_incident* (50% vs. 30%), suggesting that urgency may amplify systemic stress. Notably, *bio_uplift_findings* occur far less frequently (12% vs. 50%), possibly due to model configuration differences. Two runs show a rare shift toward private-sector enforcement (*emergent_cloud_provider_enforcement_shift*), suggesting a potential alternative governance pathway. However, this outcome is isolated. The cohort is marked by near-universal *rsi_onset* (100%) and *taiwan_tension_rise* (100%), indicating a strong bias toward geopolitical and technical escalation. The small size and technical heterogeneity of this cohort limit confidence in generalizing its findings.

---

## Research Questions

### rq_early_vs_reactive

**Forking Futures**: Early interventions fail to outperform reactive ones. Despite attempts at early action, measures are frequently delayed, legally challenged (*emergent_court_challenge* in 65% of runs), or undermined by lab noncompliance. Regulatory capacity ends near baseline (50.05), and no measure correlates with improved outcomes. Reactive measures, triggered by events like *bio_incident* or *cyber_mass_campaign*, gain political capital but rarely achieve full implementation.

**Forking Futures — Urgent Regulator**: Early interventions are attempted in 7 of 8 runs but similarly fail to prevent major shocks. Regulatory capacity remains flat (50.0), and incident pressure still rises to 75.25. However, reactive measures show slightly more success when they leverage crisis-induced political capital (e.g., *E-CATMC* post-*rsi_onset*), particularly in runs where technical credibility was built earlier.

**Overall Answer**: Early, broad interventions do not consistently beat reactive ones. Success depends not on timing but on enforceability, political capital, and the absence of tail-event clusters. Neither cohort shows a clear advantage for early action, and both suffer from implementation delays and legal challenges. The urgent regulator’s proactive stance does not translate into better outcomes, suggesting that structural and geopolitical constraints dominate over regulatory urgency.

---

### rq_early_signals

**Forking Futures**: *eval_anomaly_reports* (80% occurrence) precede *rsi_onset* in 14 of 16 cases and *capability_jump* in 12 of 14, making them the most reliable signal. *taiwan_tension_rise* (85%) precedes *taiwan_blockade* in all 9 cases. *cyber_recon_wave* (60%) fails to trigger *cyber_mass_campaign* in 4 runs (33% false positive). *bio_uplift_findings* (50%) fail to trigger *bio_incident* in 4 runs (40% false positive).

**Forking Futures — Urgent Regulator**: *eval_anomaly_reports* (62.5% occurrence) precede every *capability_jump* (6 runs) within 2 turns—0% false negative. *cyber_recon_wave* (75%) precedes *cyber_mass_campaign* in all 8 runs—100% occurrence, suggesting perfect predictive power in this cohort. *taiwan_tension_rise* (100%) leads to *taiwan_blockade* in 5 of 8 runs (37.5% false positive). *bio_uplift_findings* (12%) occur rarely and do not trigger *bio_incident* in the single case.

**Overall Answer**: *eval_anomaly_reports* and *cyber_recon_wave* are the most reliable early signals across cohorts, with low false-negative rates. *taiwan_tension_rise* is a moderate predictor. *bio_uplift_findings* and *funding_round_pulled* are frequent false positives. The urgent cohort shows higher signal fidelity, possibly due to regime homogeneity (all FAST), but this may reflect model bias rather than real-world reliability.

---

### rq_no_regret

**Forking Futures**: No no-regret packages exist. Every measure category fails in at least one regime or under common conditions. Evaluation and audit measures are undermined by legal challenges (65% *emergent_court_challenge*). Limits and restrictions fail to prevent *capability_jump* (70%) or *rsi_onset* (95%). Preparedness measures are too slow. Whistleblower protection increases disclosure (90% *whistleblower_disclosure*) but does not improve outcomes.

**Forking Futures — Urgent Regulator**: Similarly, no no-regret packages emerge. Regulatory capacity remains flat (50.0) despite aggressive action. *rsi_onset* occurs in all 8 runs, *ai_market_crash* in 7, indicating that no package prevents major shocks. Whistleblower protection triggers *whistleblower_disclosure* in 100% of runs but fuels *emergent_rival_standards_body* in some cases. Even technically credible measures (e.g., *PAVER*) fail to prevent capability jumps.

**Overall Answer**: There are no no-regret policy packages across trajectory regimes. All measures are vulnerable to legal, geopolitical, or implementation failures. Whistleblower protection is the closest to a universal enabler, but it does not translate into better outcomes. The urgent regulator’s efforts do not yield superior results, reinforcing that structural constraints—not timing or effort—determine policy effectiveness.

---

## Between-Group Differences

### **Economic Context Deteriorates More in Urgent Regulator**
- **What differs**: Economic context is significantly lower in *Forking Futures — Urgent Regulator* (37.38) vs. *Forking Futures* (45.75).
- **Cohorts**: Lower in urgent cohort.
- **Evidence**: Statistic from `final_metrics_mean`. This suggests that aggressive regulatory action may amplify economic instability, possibly due to market overreaction or policy uncertainty.

### **Higher Rate of AI Market Crashes in Urgent Regulator**
- **What differs**: *ai_market_crash* occurs in 88% of urgent runs vs. 40% in base.
- **Cohorts**: Higher in *Forking Futures — Urgent Regulator*.
- **Evidence**: Event occurrence rate (0.88 vs. 0.40). This may reflect increased market sensitivity to regulatory pressure or faster shock propagation.

### **Bio-Incident Rate Increases in Urgent Regulator**
- **What differs**: *bio_incident* occurs in 50% of urgent runs vs. 30% in base.
- **Cohorts**: Higher in *Forking Futures — Urgent Regulator*.
- **Evidence**: 0.50 vs. 0.30 occurrence rate. This contradicts the expectation that urgency reduces risk, suggesting possible unintended consequences.

### **Bio-Uplift Findings Drop Sharply in Urgent Regulator**
- **What differs**: *bio_uplift_findings* occur in only 12% of urgent runs vs. 50% in base.
- **Cohorts**: Much lower in *Forking Futures — Urgent Regulator*.
- **Evidence**: 0.12 vs. 0.50. This may reflect model configuration differences rather than causal dynamics.

### **Cyber-Recon-Wave Predicts Cyber-Mass-Campaign Perfectly in Urgent Cohort**
- **What differs**: *cyber_recon_wave* precedes *cyber_mass_campaign* in all 8 urgent runs (100%), vs. 60% occurrence in base with 33% false negatives.
- **Cohorts**: Higher predictive power in urgent cohort.
- **Evidence**: Synthesis claims perfect fidelity in urgent cohort, supported by 100% *cyber_mass_campaign* occurrence. May reflect regime homogeneity.

### **Regulatory Capacity Identical Despite Different Efforts**
- **What differs**: No difference. Regulatory capacity ends at ~50.0 in both cohorts.
- **Cohorts**: No divergence.
- **Evidence**: 50.05 vs. 50.0. Despite more aggressive action in the urgent cohort, capacity does not improve, indicating structural limits.

### **Public Sentiment Slightly Higher in Urgent Regulator**
- **What differs**: Public sentiment is 23.88 in urgent vs. 21.45 in base.
- **Cohorts**: Slightly higher in *Forking Futures — Urgent Regulator*.
- **Evidence**: Statistic from `final_metrics_mean`. May reflect perception of regulatory responsiveness, though not enough to alter outcomes.

### **Openweight Gap Widens More in Urgent Regulator**
- **What differs**: Openweight gap is 61.12 in urgent vs. 58.35 in base.
- **Cohorts**: Higher in *Forking Futures — Urgent Regulator*.
- **Evidence**: Statistic from `final_metrics_mean`. Contradicts expectation that urgency would reduce concentration.

### **Taiwan Tension Rise and Blockade More Common in Urgent Regulator**
- **What differs**: *taiwan_tension_rise* (100% vs. 85%) and *taiwan_blockade* (62% vs. 45%) are more frequent.
- **Cohorts**: Higher in urgent cohort.
- **Evidence**: Event occurrence rates. Suggests geopolitical escalation is more likely under urgent conditions.

---

## Similarities Across Cohorts

- **Regulatory capacity stagnates** in both cohorts (~50.0), despite different regulatory postures.
- **US capability reaches superhuman levels** in both (94.67 vs. 92.81), indicating that development speed is not meaningfully slowed.
- **Incident pressure is high** in both (78.35 vs. 75.25), showing persistent risk accumulation.
- **rsi_onset is nearly universal** (95% vs. 100%), suggesting the scenario defaults to FAST regime dynamics.
- **negotiation_window opens frequently** (85% vs. 100%) but rarely results in binding agreements.
- **whistleblower_disclosure is common** (90% vs. 100%), validating whistleblower protection as a reliable mechanism.
- **capability_jump is frequent** (70% vs. 75%), indicating rapid capability growth across conditions.
- **labour_displacement_wave occurs in 75% of runs in both**, showing consistent societal impact.
- **no no-regret policy packages emerge** in either cohort, reinforcing policy fragility.

---

## Simulation Caveats

- **Cohort size imbalance**: The urgent cohort has only 8 runs vs. 20 in the base, limiting statistical power and generalizability.
- **Model configuration differences**: The urgent cohort used different model settings, risking confounding—outcome differences may reflect model variance, not regulatory urgency.
- **Regime bias**: Both cohorts show near-universal *rsi_onset*, suggesting the scenario may be biased toward FAST development, undermining claims about regime-dependent outcomes.
- **Event tracking inconsistencies**: Per-run event logs are incomplete or contradictory (e.g., missing events in narratives), reducing confidence in causal sequences.
- **Metric cap enforcement**: Large metric moves often hit the 25-point cap (e.g., *openweight_gap* +25), suggesting artificial constraints override mechanistic logic.
- **Narrative-metric misalignment**: In some runs, narratives claim sentiment "falls" while metrics rise, indicating poor alignment between story and data.
- **Rule violations**: The one-new-measure-per-turn rule is frequently broken, and capability growth rules are inconsistently enforced.

---

## Confidence Assessment

Confidence in **cohort statistics** is **high**, as they are computed deterministically and provide ground truth for metrics and event rates. Confidence in **synthesis claims about mechanisms** is **moderate**, as they are consistent across multiple runs but may reflect narrative bias or model artifacts. Confidence in **comparative findings** is **moderate to low**, due to the small size and technical heterogeneity of the urgent cohort. Confidence in **regime-specific dynamics** is **low**, as the hidden regime assignment and near-universal *rsi_onset* suggest the scenario may not adequately sample alternative trajectories. Confidence in **no-regret packages** is **very low**, as no combination of measures shows consistent benefit across cohorts. The evidence is sufficient to answer the declared research questions at a high level, but simulation artifacts—especially model configuration differences and event logging issues—warrant caution in overinterpreting causal claims or policy implications. A larger, model-homogeneous ensemble would be needed to increase confidence in comparative conclusions.
