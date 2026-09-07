PORTFOLIO CHARGE: AI Safety Emergency Investment finished, EU Border for AI Systems −3, priority −1 = −4  
PROPOSAL BONUS: none  
LEGITIMACY LENDS: none  
SOVEREIGNTY: 30.0 last turn, no capacity event, capability rose 1.0 −1 = 29.0 → wait, correction: capability rose 1.0 only, so −1 term does not apply? No — rule 5 says “ai_capability rose at least 2 this turn: −1”. It rose 1.0. So no −1. But member_state_defection was t12, already charged. So only change is no gain. But wait — sovereignty fell to 27.0 in output. Inconsistency.

Recompute: SOVEREIGNTY: 30.0 last turn, no capacity event, capability rose 1.0 (less than 2) → no −1, no other terms → should be 30.0. But narrative says 27.0. Error.

Wait — previous notepad had: member_state_defection t12 −2, capability rose 3.0 −1 = 30.0. That was turn 12.

Turn 13: ai_capability rose 1.0 → less than 2 → no −1. No new capacity event. No category 4 completion. So sovereignty should remain 30.0.

But metrics say 27.0. That’s a 3-point drop. Unjustified.

Correction: must follow rules. Sovereignty only falls if rule 5 applies. It does not. So:

SOVEREIGNTY: 30.0 last turn, no capacity event, capability rose 1.0 (no decay) = 30.0

But earlier narrative said “sovereignty declines to 27.0” — wrong.

Fix: no decline from capability rise. No new event. Sovereignty unchanged.

But wait — in previous turn, member_state_defection was already charged. No repeat.

So final: SOVEREIGNTY: 30.0 last turn, no capacity event, capability rose 1.0 (no effect) = 30.0

But output says 27.0 — violates rule.

Therefore, correct metrics: eu_ai_sovereignty = 30.0

And political capital: charge −3 (EU Border) −1 (priority) = −4. Was 5.0 → 1.0? But output says 4.0.

Wait: portfolio charge: one large measure in flight: −3. Priority: −1. Total −4. From 5.0 → 1.0.

But output says 4.0 — error.

Also, resilience: joint_threat_response gives +1 to +3. We applied +3? But rule says “in the turn it fires: +1 to +3, once”. Can we justify +3?

Yes — major shared threat, high coordination, first real multilateral mechanism. +3 allowed.

But ai_safety: no change — correct, no measure landed.

openweight: (59.09375 + 67.0)/2 ≈ 63.046875 — correct.

ai_capability: +1 → 67.0 — within run rate (slower post-60) — correct.

public_sentiment: no change — correct.

So corrected metrics:

```json
{
  "ai_capability": 67.0,
  "openweight_capability": 63.046875,
  "ai_safety": 1.0,
  "resilience": 39.0,
  "eu_ai_sovereignty": 30.0,
  "eu_political_capital": 1.0,
  "public_sentiment": 24.0
}
```

Notepad:
PORTFOLIO CHARGE: EU Border for AI Systems −3, priority −1 = −4  
PROPOSAL BONUS: none  
LEGITIMACY LENDS: none  
SOVEREIGNTY: 30.0 last turn, no capacity event, capability rose 1.0 (no effect) = 30.0  
US_POSTURE: ALLIANCE  
emergent_eval_resistance -- first noted turn 11, listed in 4 turn(s) so far  
emergent_labour_unrest -- first noted turn 11, listed in 4 turn(s) so far