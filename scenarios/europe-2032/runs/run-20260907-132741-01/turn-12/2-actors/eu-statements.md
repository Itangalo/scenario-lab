# Statements: The European Union (turn 12)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (position): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Abandon the current formulation due to de facto institutional paralysis; the Union lacks the political capital to enforce or implement any new measure, and public sentiment has collapsed to a level where even remedial justice is no longer credible without prior restoration of basic functionality and trust.
- `survive_collapse` (commitment): Prevent total disintegration of EU AI governance by maintaining at least one functioning cross-border mechanism, preserving technical capacity in at least two member states, and retaining access to basic incident data across the Union — now expanded to include verified continuity of secure communication between national CERTs and ENISA, tested under live conditions.

## Changes this turn

- **modify** `two_year_commitment` — rejected-structural
  - Tier: commitment
  - Text: Abandon the current formulation due to de facto institutional paralysis; the Union lacks the political capital to enforce or implement any new measure, and public sentiment has collapsed to a level where even remedial justice is no longer credible without prior restoration of basic functionality and trust.
  - Grounds: This commitment was already revised last turn to reflect institutional collapse. It remains valid: we still lack enforcement credibility, fiscal headroom, and member-state cohesion. No development this turn alters that reality — if anything, the continued refusal of Poland and Hungary to join even minimal data-sharing confirms it. We hold this version.
  - Reason: modified text is identical to the current text
- **modify** `survive_collapse` — applied
  - Tier: commitment
  - Text: Prevent total disintegration of EU AI governance by maintaining at least one functioning cross-border mechanism, preserving technical capacity in at least two member states, and retaining access to basic incident data across the Union — now expanded to include verified continuity of secure communication between national CERTs and ENISA, tested under live conditions.
  - Trigger: **capability_plateau_evidence** and **middle_power_coalition**
  - Grounds: The plateau signal changes our threat model: for the first time since 2028, the frontier may have stalled, giving us a narrow window to stabilise rather than merely react. Combined with the emergence of the middle-power coalition — which secures compute access and joint evaluation leverage — we are no longer purely in triage. But legitimacy remains zero. We must now use this breathing room not just to survive, but to demonstrate that something EU-level still works. Thus, we raise the bar: survival now requires not just data flow, but verified, exercised continuity of secure communication. If the data pool delivers visibility but fails under stress, it proves nothing.
  - Evidence quoted: capability_plateau_evidence: A major release underdelivers against its own briefing, and – the stronger signal – the price of top-tier capability falls sharply rather than staying flat, which is what happens when the frontier stops moving and last year's ceiling becomes this year's commodity. It is disputed at once, and the dispute is not resolvable from outside the laboratories.

middle_power_coalition: A coordination framework among the Union and other middle powers holding pieces of the AI supply chain — export-licence alignment, joint bargaining over compute access, shared evaluation capacity. Nobody cedes sovereignty to it, but together its members can withhold things even the great powers need. It counts as securing access on the terms of metric rule 5, and moves `eu_political_capital` on the terms of metric rule 6.
  - Reason: The coalition secures compute access and evaluation leverage, altering the EU's capacity to stabilize governance; the plateau eases pressure, enabling proactive demonstration of functionality.
- **reclassify** `act_under_uncertainty` — applied
  - Tier: position
  - Trigger: **capability_plateau_evidence**, **middle_power_coalition**
  - Grounds: These developments resolve the uncertainty that gave this commitment its meaning. We now have external signals about capability trends and a new coordination vector with real leverage. Acting before clarity was necessary when paralysis was the alternative; now, clarity is within reach. We retain the principle, but as a tactic, not a binding promise. Our next moves will be based on evidence, not anticipation.
  - Evidence quoted: A major release underdelivers against its own briefing, and – the stronger signal – the price of top-tier capability falls sharply rather than staying flat, which is what happens when the frontier stops moving and last year's ceiling becomes this year's commodity. It is disputed at once, and the dispute is not resolvable from outside the laboratories.
  - Reason: The plateau evidence reduces uncertainty about capability trends, directly affecting the rationale for acting before clarity.
