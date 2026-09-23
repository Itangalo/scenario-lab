# Design notes – Intelligence Rising (Scenario Lab analogue)

## Central question

Under what conditions does a US–China frontier-AI race end in negotiated, verifiably safe RTAI governance vs. preventive attack or loss of control (see `research-question.md`, approved 2026-09-23).

## Key design decisions

- Classic 4-team cast with real IR names (user choice): us_government, china_government, alphabet (US Big Tech pole), tencent (China Big Tech pole). Microsoft/OpenAI and Baidu live in the background, not as actors.
- 8 x 1-year turns from 2026-01: mirrors IR's own turn length and decade arc.
- Capability as two 0–4 metrics mapping the four-level tree; the gap between them (not the levels alone) drives the bad-loser dynamic via event gating and metric rules.
- global_stability opens at 7/10 exactly as in the game; US elections are certain events on the 2028/2032 turns with outcomes resolved in narrative.
- Nationalisation asymmetry, exfiltration-as-race-flipper, and autonomy-assurance as the good-ending condition are all ported as first-class mechanics, not flavour.
- Workshop block included from the start (live-playable); emergent events enabled (the facilitator-shock role); probability_samples 3 for steadier event pricing.
- No Policy Tree (excluded from the analysed games), no middle-power actor (left for a variant), startups as shock events only.

## Assumptions

- Starts (us 1.5 / china 1.2 / safety 20 / tension 45 / agreement 10) are calibrations, not measurements; only stability 7 is sourced.
- Tech-tree node names, R&D costs, victory-condition text, and dice tables are unpublished; abstracted into levels, rules, and termination.
- Election outcomes (continuous vs. disruptive) resolved narratively per turn, not via event_groups; a future iteration could use exactly_one groups for 2028/2032.
- Endgame deployment resolution bands (75/60, 50, below) are our operationalisation of "dice still required even with agreements".
- Cheap default model (qwen3-235b) for drafts; scale up after behaviour looks right.

## Known weak spots

- Two-metric capability may let both blocs hit 4 too easily/fast; watch pacing in smoke tests (expected ~turn 5–7 arrival).
- Election disruption is prose-driven and may be under-applied by the GM; check the 2028 turn explicitly.
- Defection/preventive-strike gating depends on the events model respecting Eligible + Condition; verify firing rates.
- Metric rules are long; per Rule Economy, consolidate if constitutional violations or misapplication appear.

## Deliberately left out

- Policy Tree mechanic; second lab per side (6-team variant idea); international-body/middle-power actor (variant idea); detailed verification-regime design (left to negotiation); post-RTAI world (termination ends the run).

## Smoke test + sign-off (2026-09-23)

- 3-turn smoke run (run-20260923-085344, muse-spark/minimal, $0.013): capabilities +0.2–0.3/turn, safety creeping, stability 7→5 then 2.5 on Taiwan crisis, tension 45→72, agreement flat ~15–18. Taiwan crisis + disruptive 2028 election both fired on schedule; gates held (no exfiltration/strike/defection below thresholds). Alphabet output perfectly in character (compute resilience, race sprint, safety-preaching plus secret weapons work and oversight resistance). Rules carried forward with "No material rule changes"; constitutional check approved, no violations.
- Minor nuance: turn-3 narrative invoked Defense Production Act funds during the blockade – crisis use, acceptable, but watch for DPA normalisation in longer runs (ledger C3).
- Sign-off run (run-20260923-085922) + `render_signoff.py`: all 4 documents. Every coverage-table NO accounted for: other actors' sections (sampled actor only – US gov prompt verified directly from llm-io, correct per-actor interpolation); 5 gated events (Eligible exclusion at low capability/agreement, proven live in the smoke run); metric-rules title line (content rendered); research-question.md (documentation by design, machine-readable via scenario.yaml).
- Known framework limitation for the TSG demo: all actors share one world state – IR's truly private facilitator resolution is narrated secrecy here (constitution invariant 6), not hidden information.
- Signed off 2026-09-23. Regenerate sign-off after any change to templates, overrides, or background files.
