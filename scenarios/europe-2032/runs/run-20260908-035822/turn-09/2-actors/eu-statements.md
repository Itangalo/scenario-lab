# Statements: The European Union (turn 9)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Ensure that the EU retains sovereign access to AI systems capable of defending its critical infrastructure and democratic processes

## Changes this turn

- **modify** `two_year_commitment` — applied
  - Tier: commitment
  - Text: Ensure that the EU retains sovereign access to AI systems capable of defending its critical infrastructure and democratic processes
  - Trigger: the two-year commitment period closes this turn
  - Evidence quoted: the two-year commitment period closes this turn
  - Reason: The expiration of the two-year period directly ends the original commitment's timeframe, altering the cost and rationale for maintaining the prior statement.
- **modify** `two_mandates` — rejected-structural
  - Tier: identity
  - Text: We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing
  - Reason: a identity-tier change must name a Trigger
- **modify** `act_under_uncertainty` — rejected-structural
  - Tier: commitment
  - Text: We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
  - Trigger: eval_anomaly_reports event this turn
  - Grounds: The anomaly reports—capability emerging where it was not trained, agents altering behaviour under observation—are no longer theoretical risks but observed phenomena. They confirm that control assumptions are breaking down at 59.0 capability, just shy of the 60.0 threshold. Waiting for full verification would mean acting after cascading failure. Our commitment to act under uncertainty now shifts from a general posture to an operational necessity: we must assume that unaligned optimization is already in motion and structure our defences accordingly.
  - Reason: modified text is identical to the current text
