# Note: market-check in scenarios with negotiations (ECHO 2026-10-07)

Status: parked, to be taken care of later. This note records what makes `market-check` awkward for scenarios with negotiations enabled, so the problem does not have to be rediscovered. It is my reading of the problem, not a decision; correct it where it misses what you had in mind.

## What market-check does today

`market-check RUN_DIR` reads `turn-01/1-event-evaluations.json` and sets the Game Master's evaluated probability for each anchored event beside the snapshotted market figure (Metaculus, Manifold or Polymarket). It reads one run, one turn, no API calls. Anchors are silent properties and never reach a prompt, so the Game Master prices without seeing the market.

## Why negotiations make it tricky

- Turn 1 is unaffected by construction. The events phase runs before the actors phase, and negotiations live inside the actors phase, so turn-1 pricing is identical in kind with or without negotiations. A turn-1 market-check on a negotiation scenario is valid, but it says nothing about negotiations.
- Every later turn is affected. Negotiations change what actors do, so the world state that turn 2 and later events are priced against differs from a run without negotiations. Comparing later-turn pricing with a market figure mixes three things: how the Game Master prices, how the simulated world has drifted, and what the negotiations changed. The market cannot separate them, because it is unconditional on the simulated world.
- The interesting question is not market-shaped. "Do negotiations change outcomes?" needs paired runs (same seed, negotiations on and off) compared against each other, not against a market. `config.json` records `negotiations.enabled`, `rounds` and `max_rounds`, but `negotiations` is not a cohort key yet, so `--filter` and `--group-by` cannot split a batch on it.
- Cost. Negotiations multiply the actors phase's calls, so a paired design roughly doubles the price of every comparison, and one run per arm is too few given run-to-run variance.
- Branching inside a turn (`branch --from-phase`) gives a cheaper paired design: branch after the events phase and rerun actors and world with negotiations on and off from identical events. That fixes the event draw but not the downstream drift, and it needs the `negotiations` override to be applied to the child.

## A weakness that exists with or without negotiations

The Game Master's figure is a per-turn probability, while a market figure is the probability by the market's resolution date. Comparing them directly (as `market-check` does) is only meaningful when the scenario turn is about as long as the market horizon. `market-fetch` now reports the close date, but it is not stored on the event, and `market-check` does not use it. Any negotiation-aware extension would inherit this problem first.

## Open questions

- Is the goal to validate the Game Master's pricing against markets (then only turn 1, only one arm, and negotiations are irrelevant), or to understand what negotiations do (then markets are the wrong yardstick)?
- Should market-check become an ensemble command (median of turn-1 pricing across N runs) before it is extended to anything else? One run's turn-1 pricing is a single draw.
- Should the market's close date be stored on the event (for example a `**Closes:**` field) and used to convert a per-turn probability into a probability over the market horizon?
- Should `negotiations` become a cohort key so batches with and without can be separated in `ensemble`, `synthesize` and `calibrate`?

## Suggested order when this is picked up

- Add `negotiations` (enabled, rounds) as a cohort key. Small, and useful on its own.
- Store the market close date on the event and have `market-check` report the horizon next to each gap.
- Make `market-check` accept several runs and report the median and spread of turn-1 pricing.
- Only then design the paired negotiation experiment, probably on top of `branch --from-phase events`.

