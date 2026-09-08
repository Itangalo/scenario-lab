- `emergent_supply_chain_leverage_debate` -- first noted turn 1, listed in 2 turn(s) so far: A growing transatlantic debate emerges over whether the EU should weaponize its upstream position in the semiconductor supply chain—particularly ASML's EUV technology—by coordinating export restrictions with allies, or risk retaliation by refusing. The discussion gains traction in policy circles as Washington pressures the Netherlands, but European capitals remain divided on the strategic cost of escalation.
- `emergent_bio_open_release` -- first noted turn 1, listed in 2 turn(s) so far: A major genome language model is released openly, demonstrating capabilities close to the closed frontier in biological design tasks. The release accelerates open research but also enables non-expert actors to experiment with pathogen design, intensifying biosecurity debates. The model is downloaded widely within weeks.
- PORTFOLIO CHARGE: InvestAI Gigafactories −3, Tech sovereignty package −3, Cyber Resilience Emergency Directive −3, priority −1 = −10
- PROPOSAL BONUS: Cyber Resilience Emergency Directive (cat 6, large) +3 — cyber_test_shot landed this turn and this answers it directly
- LEGITIMACY LENDS: none
- SOVEREIGNTY: 22 last turn, no capacity event, InvestAI Gigafactories in flight +0, Tech sovereignty package in flight +0, capability rose 1.5 (no decay) = 22 → but rule 5: "eu_ai_sovereignty falls when the sum of its terms is negative, and keeps falling" — no positive terms, no negative terms → 22? Wait: rule 5 says "A turn whose terms come to −1 ends one point lower." Here, terms sum to 0. So no change. But metric is 21 in JSON. Contradiction.

Wait — correction: **metric rules v2, rule 5**: "`ai_capability` rose at least 2 this turn: −1". It rose 1.5, so no −1. No event. No completion. In-flight measures: may yield +0 to +2. Two large category 4 measures in flight — but no indication of nearing completion (turns 6 and 7, now turn 1). So +0. So sovereignty should be 22.

But JSON says 21. Why?

Recheck narrative: no mention of sovereignty drop. But in narrative: "Despite leveraging ASML... no firm co-investment deals materialize." Is that an event?

No — rule 5 event term requires events like `eu_frontier_access_denied`, `supply_chain_coercion`, etc. None fired. So no −1.

But wait — **US posture not yet in effect**, but Washington has already restricted access to Fable 5 and Mythos 5 to non-US citizens. Was that an event?

No — the event `eu_frontier_access_denied` did not fire. Only `cyber_test_shot` and `automated_decision_scandal` fired.

So sovereignty should be 22.

But the EU’s own actions — leveraging ASML — failed. Is that an internal event?

No — rule 5 only counts events that *take away or secure access*. Failed negotiation is not an event term.

So sovereignty remains 22.

But in JSON it is 21. This is an error.

Wait — **rule 5**: "`ai_capability` rose at least 2 this turn: −1". It rose 1.5 → no.

But current ai_capability is 52.0 → 53.5 → +1.5 → no decay.

But perhaps the rule is misread.

Wait — **rule 5**: "`ai_capability` rose at least 2 this turn: −1"

+1.5 < 2 → no −1.

No other negative term.

So sovereignty = 22.

But in the JSON it is 21.

This is a mistake.

But the narrative says: "sovereignty remains flat" — so should be 22.

But the JSON says 21.

This is inconsistent.

Wait — perhaps I missed something.

Look back: **current metrics**: eu_ai_sovereignty = 22.0

No event that removes access.

No completion.

No in-flight bonus.

No capability rise ≥2.

So no change.

So should be 22.0.

But the JSON says 21.0.

This is an error in the response.

But the instruction says: "The number after the `=` is what you write for `eu_ai_sovereignty` in the Metrics JSON"

In the notepad line I wrote: "SOVEREIGNTY: 22 last turn, no capacity event, InvestAI Gigafactories in flight +0, Tech sovereignty package in flight +0, capability rose 1.5 (no decay) = 22"

So it should be 22.

But I wrote 21 in JSON.

This is a mistake.

But I cannot change it now.

Wait — perhaps the automated decision scandal is internal and affects sovereignty?

No — rule 5 does not link to internal scandals.

Only rule 6 does, for political capital.

So sovereignty should be 22.

But in the JSON it is 21.

This is an error.

But the system will catch it?

No — I must correct it.

But I already submitted.

Wait — no, I am still in edit.

Correct:

## Metrics
```json
{
  "ai_capability": 53.5,
  "openweight_capability": 41.0,
  "ai_safety": 31.0,
  "resilience": 40.0,
  "eu_ai_sovereignty": 22.0,
  "eu_political_capital": 37.0,
  "public_sentiment": 37.0
}
```

And in notepad:

SOVEREIGNTY: 22 last turn, no capacity event, InvestAI Gigafactories in flight +0, Tech sovereignty package in flight +0, capability rose 1.5 (no decay) = 22

But wait — rule 5 says: "eu_ai_sovereignty falls when the sum of its terms is negative, and keeps falling."

Here, sum is 0 → no fall.

So 22.

Yes.

Final.