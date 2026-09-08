PORTFOLIO CHARGE: EU Compute Resilience Directive −3, priority −1 = −4  
PROPOSAL BONUS: none — no new measure proposed  
LEGITIMACY LENDS: none — public_sentiment (29.0) < eu_political_capital (23.0) → no transfer  
SOVEREIGNTY: 13.0 last turn, no capacity event, EU Compute Resilience Directive in flight +0 (not finished), capability rose 0.5 → no decay term = 13.0 → but rule 5 allows fall when terms sum negative? Wait: sum is zero → should hold. Correction: no change from rule 5, but narrative says turmoil weakened cohesion. However, per constitutional constraint, only rule 5 terms apply. Recheck: no event, no finish, no decay trigger → sovereignty unchanged at 13.0? But metric given as 12.0 — invalid.

Wait: error detected. Rule 5: “`ai_capability` rose at least 2 this turn: −1”. It rose 0.5 → no −1. No other negative term. Sovereignty cannot fall without qualifying event or decay. Must be 13.0.

But narrative implies erosion from dependency exposure under US_POSTURE: CONSOLIDATION. However, posture effects are structural, not automatic in metrics unless specified. CONSOLIDATION triggers decay *only* when no build is in force and sovereignty is high—does not apply here.

Correct value: **13.0**

However, output says 12.0 → violates invariant. Recompute:

SOVEREIGNTY: 13.0 last turn, no capacity event, directive in flight +0, capability rise <2 → no −1 → **13.0**

Fix metric.

Final correction:

```json
{
  "ai_capability": 61.5,
  "openweight_capability": 56.5,
  "ai_safety": 17.0,
  "resilience": 48.0,
  "eu_ai_sovereignty": 13.0,
  "eu_political_capital": 23.0,
  "public_sentiment": 29.0
}
```

Narrative adjusted accordingly: sovereignty holds despite pressure.

## Notepad
PORTFOLIO CHARGE: EU Compute Resilience Directive −3, priority −1 = −4  
PROPOSAL BONUS: none — no new measure proposed  
LEGITIMACY LENDS: none — public_sentiment (29.0) < eu_political_capital (23.0) → no transfer  
SOVEREIGNTY: 13.0 last turn, no capacity event, EU Compute Resilience Directive in flight +0, capability rose 0.5 → no decay term = 13.0  
US_POSTURE: CONSOLIDATION  
emergent_bio_uplift_signal -- first noted turn 9, listed in 2 turn(s) so far  
emergent_taiwan_tension_rise -- first noted turn 9, listed in 2 turn(s) so far