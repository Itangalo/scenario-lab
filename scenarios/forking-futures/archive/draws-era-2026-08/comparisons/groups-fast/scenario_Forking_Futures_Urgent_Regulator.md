## Summary

The ensemble of eight runs in the "Forking Futures" scenario consistently depicts a trajectory of rapid AI capability growth under a de facto FAST regime, with US and Chinese systems advancing from mid-tier to broadly superhuman levels by the end of the 18-turn horizon. Despite the regulator’s persistent efforts, governance capacity erodes or stagnates, and incident pressure rises to crisis levels in all runs. Early interventions are frequently undermined by legal challenges, geopolitical friction, and systemic delays, while reactive measures struggle to contain cascading risks. The openweight gap widens significantly in most runs, indicating dangerous concentration of frontier capabilities. A recurring pattern is the regulator’s pivot from multilateralism to coalition-based or unilateral enforcement as global cooperation fractures. Key precursors like eval_anomaly_reports and cyber_recon_wave reliably precede major capability jumps and cyber incidents, validating their role as early signals. No no-regret policy packages emerge across all three hypothetical regimes, as effectiveness is highly regime-dependent and often offset by implementation costs.

## Research Questions

### rq_early_vs_reactive

Early, broad interventions do not consistently outperform reactive ones across the ensemble, and their success depends heavily on regime-specific conditions and the timing of major shocks. In 7 of 8 runs, early measures (e.g., IEC, RAVF) were introduced in the first 3 turns but failed to prevent capability jumps, cyber_mass_campaigns, or bio_incidents due to legal challenges, covert defection, or lack of enforcement capacity. Reactive measures, triggered after events like rsi_onset or cyber_mass_campaign (e.g., E-CATMC, MVDP), were more effective in reducing incident pressure in 5 runs (run-20260825-145356, run-20260825-145408, run-20260825-202323, run-20260825-202323-02, run-20260825-212404), but only when they leveraged crisis-induced political capital. For example, in run-20260825-202323-02, the emergent_cloud_provider_enforcement_shift in turn 18 succeeded because it followed years of technical credibility-building during earlier reactive phases. However, in runs where early capital was squandered (e.g., run-20260825-145420), reactive measures were too late to matter. The bearing metrics show that regulatory_capacity remained flat (mean 50.0 at turn 18) despite high incident_pressure (mean 75.25), indicating that neither early nor reactive strategies reliably built sustained capacity. Early interventions succeeded only when they were narrowly focused and implemented before the first major shock (turn 5), as seen in the partial success of EEM in run-20260825-202323 after the turn 2 ai_market_crash.

### rq_early_signals

The most reliable precursors to large divergences are eval_anomaly_reports and cyber_recon_wave, which precede capability jumps and cyber_mass_campaigns with high fidelity, while bio_uplift_findings and funding_round_pulled are frequent false positives. eval_anomaly_reports occurred in 5 of 8 runs and preceded every capability_jump (6 occurrences), with a mean evaluated probability of 0.25 in turn 1 and declining thereafter. In all 5 runs where it fired (run-20260825-145356, run-20260825-145420, run-20260825-202323, run-20260825-202323-03, run-20260825-212404), it was followed within 2 turns by a capability_jump, confirming its role as a high-sensitivity, low-false-positive signal. cyber_recon_wave occurred in 6 runs and opened the gate for cyber_mass_campaign in all 8 runs (100% occurrence), with a mean probability rising from 0.18 in turn 1 to 0.27 in turn 10. In contrast, bio_uplift_findings occurred only once (run-20260825-145408) despite a high base probability, and funding_round_pulled occurred in 5 runs but led to ai_market_crash in only 4, yielding a 20% false-positive rate. taiwan_tension_rise occurred in all 8 runs but led to taiwan_blockade in only 5, a 37.5% false-positive rate. The ensemble divergence analysis shows that incident_pressure diverged most sharply in turn 2, associated with eval_anomaly_reports (mean difference +17.53) and cyber_mass_campaign (mean difference +26.83), confirming their predictive power.

### rq_no_regret

There are no no-regret policy packages across the three hypothetical trajectory regimes, as all measure combinations show trade-offs that make them regime-specific or offset by implementation costs. The ensemble statistics show that regulatory_capacity remained near baseline (mean 50.0 at turn 18, std 8.96), while incident_pressure rose to crisis levels (mean 75.25) and openweight_gap widened (mean 61.12), indicating that no portfolio of measures consistently improved outcomes. Per-run analyses confirm this: in run-20260825-202323, the regulator’s “portfolio of measures” strategy led to chronic strain and emergent_member_state_noncompliance. Measures grouped by category—such as evaluation capacity (category 1), incident reporting (category 2), and limits (category 3)—showed no consistent benefit. For example, category 1 measures like IEC and PAVER built technical credibility but failed to prevent capability_jump in 6 runs. Category 3 measures like MWTC were often blocked by courts (run-20260825-145420). The only measure with broad utility was whistleblower protection (category 2), which triggered whistleblower_disclosure in all 8 runs and provided critical evidence for enforcement, but even this came at a cost: in run-20260825-202323-01, it fueled emergent_rival_standards_body. The bearing events show that rsi_onset occurred in all 8 runs and ai_market_crash in 7, indicating that no package prevented the most consequential regime-specific shocks.

## Outcome Patterns

The runs ended in three distinct patterns:

1. **Regulatory Erosion and Crisis Governance (5 runs)**: The regulator loses enforcement authority due to legal defeats and geopolitical resistance, shifting to reactive crisis management. Incident pressure remains high (85–95), public sentiment collapses (18–24), and the openweight gap widens (65–77). Examples: run-20260825-145420, run-20260825-145408, run-20260825-202323, run-20260825-202323-01, run-20260825-202323-03. In these runs, measures like ECCO or MTP are struck down, and the regulator pivots to minimal-viability detection.

2. **Technical Credibility and Private Enforcement (2 runs)**: The regulator fails to achieve binding international agreements but gains de facto influence through technical credibility and private-sector alignment. Regulatory capacity stabilizes or rises (58–66), and enforcement shifts to market mechanisms. Example: run-20260825-202323-02, where emergent_cloud_provider_enforcement_shift in turn 18 enables telemetry adoption; run-20260825-212404, where DSSN provides sovereign verification.

3. **Geopolitical Lock-In and Compute Scarcity (1 run)**: The taiwan_blockade in turn 4 permanently reshapes the trajectory, freezing compute expansion and shifting focus to efficiency and resilience. Capability growth continues but slows, and economic context remains low (38). Example: run-20260825-145356. This outcome is unique in its early divergence and sustained focus on supply-chain security.

## Recurring Turning Points

- **Turn 2–3: Early Shocks Define Trajectory**  
  In 6 runs, a dual shock (e.g., ai_market_crash + cyber_mass_campaign in run-20260825-202323) collapses economic_context and spikes incident_pressure, forcing the regulator into crisis mode. This early divergence (turn 2 max IQR jump: 22.0 in incident_pressure) sets the tone for reactive governance.

- **Turn 5–6: Missed Diplomacy and Escalation**  
  In 5 runs, a negotiation_window opens but is missed due to lack of prepared proposals or geopolitical friction (e.g., run-20260825-145356). This failure to secure binding agreements leads to a shift toward unilateral enforcement.

- **Turn 9–10: rsi_onset and Capability Lock-In**  
  rsi_onset occurs in all 8 runs (mean turn 10.5), confirming the FAST regime and triggering compounding growth. In 6 runs, it coincides with a cyber_mass_campaign or capability_jump, marking the point where regulatory timelines become obsolete.

- **Turn 13–14: Legal or Geopolitical Fracture**  
  In 5 runs, a court challenge (e.g., emergent_court_challenge in run-20260825-145420) or taiwan_blockade (5 runs) severs a key governance pathway, forcing a pivot to coalition-based or technical enforcement.

- **Turn 18: Private-Sector Breakthrough (2 runs)**  
  In run-20260825-202323-02 and run-20260825-212404, late alignment with private actors (cloud providers, labs) provides a narrow path to influence, suggesting a potential long-term shift in enforcement leverage.

## Actor Dynamics

The regulator consistently attempts to build multilateral consensus and technical capacity but is repeatedly undermined by external actors. In all 8 runs, US and Chinese labs resist binding commitments, with covert_defection occurring in 2 runs and chip_export_escalation in 7. The regulator’s strategy evolves from international cooperation (e.g., IEC) to coalition-of-the-willing enforcement (e.g., E-CATMC) and finally to sovereign technical systems (e.g., DSSN, fail-safe telemetry). Whistleblower_disclosure occurs in all 8 runs, providing critical evidence but also exposing internal lab resistance. The emergence of rival institutions—emergent_rival_standards_body in 5 runs—reflects a broader fragmentation of governance authority. In 2 runs, private actors (cloud providers) become decisive enforcement partners, suggesting a shift from state-led to market-mediated governance. The regulator’s identity as an independent rule-maker is preserved, but its effectiveness depends on its ability to generate technical credibility through red-teaming and independent evaluation.

## Surprises and Outliers

- **run-20260825-145356** is an outlier in its early taiwan_blockade (turn 4), which froze compute expansion and shifted the entire trajectory toward efficiency and resilience, unlike other runs where scaling continued. This led to a unique focus on E-CATMC and defensive coordination.

- **run-20260825-202323-02** is the only run where private enforcement (emergent_cloud_provider_enforcement_shift) provided a decisive breakthrough, elevating regulatory_capacity to 58.0. This outcome, occurring in the final turn, suggests a low-probability but high-impact pathway.

- **run-20260825-145408** is notable for the bio_incident in turn 18, which had a muted impact on metrics despite its narrative significance, indicating a potential disconnect between event severity and metric response.

- The consistent occurrence of rsi_onset in all 8 runs, despite the scenario’s design for three possible regimes, suggests the ensemble may be biased toward the FAST trajectory, possibly due to model configuration differences noted in the caveats.

## Simulation Caveats

- Only 8 runs were completed, below the recommended 10+ for robust ensemble analysis, limiting statistical confidence, especially for low-frequency events.
- The runs used different model configurations (as noted in the caveats), meaning outcome variation may reflect model differences rather than scenario stochasticity. This undermines claims about causal patterns.
- Several constitutional constraints were repeatedly violated: the FAST regime was telegraphed in narratives (e.g., explicit mentions of "recursive self-improvement"), metric movements approached or hit the 25-point cap (e.g., openweight_gap +48.0 in run-20260825-202323-03), and the one-new-measure-per-turn rule was frequently broken.
- The regulatory_capacity metric showed surprising resilience (mean 50.0 at turn 18) despite numerous legal defeats and crises, suggesting it may not fully capture erosion of soft power or legitimacy.
- The narrative diversity analysis (mean Jaccard similarity 0.11) indicates high divergence, but the most similar pair (run-20260825-202323-01 and -02) suggests clustering around certain trajectories, possibly due to shared model settings.

## Confidence Assessment

Confidence in the ensemble findings is **moderate**. The small run count (8) and use of different model configurations limit generalizability. However, the consistency of key patterns—rapid capability growth, rsi_onset in all runs, high incident_pressure, and regulatory erosion—across diverse narratives suggests robust emergent behavior. The bearing metrics and event statistics are authoritative and support the central claims. Confidence is higher for patterns observed in 6+ runs (e.g., eval_anomaly_reports as a precursor, failure of early interventions) and lower for outlier-dependent claims (e.g., private enforcement as a solution). The declared research questions are answerable with the available data, but the regime bias toward FAST limits insights into alternative trajectories. A larger, model-homogeneous ensemble would be needed to increase confidence in no-regret packages or early-vs-reactive comparisons.
