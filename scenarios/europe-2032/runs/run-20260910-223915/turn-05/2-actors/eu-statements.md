# Statements: The European Union (turn 5)

## Ledger

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will impose verifiable checks and delay power before assurance catches up, even at the cost of access and adoption speed
- `two_year_commitment` (commitment): Hold sovereign capacity and resilience while making frontier systems legible and controllable again

## Changes this turn

- **modify** `two_year_commitment` — applied
  - Tier: commitment
  - Text: Hold sovereign capacity and resilience while making frontier systems legible and controllable again
  - Trigger: the two-year commitment period closes this turn
  - Grounds: The first period built narrow compute and a Shield that degraded rather than stopped, but eval anomalies plus opaque reasoning mean capability at 64 with safety at 26 can no longer be absorbed by resilience alone; the next period must keep the sovereignty-resilience base while adding control.
  - Evidence quoted: the two-year commitment period closes this turn
  - Reason: The closure of the commitment period directly ends the timeframe for the original pledge, necessitating a revised statement of intent for the next phase.
- **modify** `act_under_uncertainty` — applied
  - Tier: commitment
  - Text: We will impose verifiable checks and delay power before assurance catches up, even at the cost of access and adoption speed
  - Trigger: eval_anomaly_reports and opaque_reasoning this turn remove chain-of-thought oversight
  - Grounds: When reasoning is no longer human-readable and evals saturate early, waiting for clarity means ceding control; precautionary evaluation authority is now the price of both mandates.
  - Evidence quoted: eval_anomaly_reports: Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. It may be either, and it may be AI slipping out of our control. This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.

opaque_reasoning: The frontier models no longer allow intermediate reasoning a human can read, because the representations that work best are not words and never were. This is partly driven by architecture decisions, partly by pressure in the training. It is announced as a capability win, but also lands as a safety loss. Every control and oversight strategy that depended on reading the chain of thought stops working at once. The alternatives that remain are unreliable benchmarks and black-box evaluations, combined with slow, costly and immature inspection of model activations.
  - Reason: Opaque reasoning removes chain-of-thought oversight; eval anomalies show unexplained capability jumps—both directly undermine the basis for acting under uncertainty by eroding visibility and control.
