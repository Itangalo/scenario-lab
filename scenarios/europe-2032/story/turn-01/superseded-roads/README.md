# The three roads that used to fork at turn 1

These are the pinned turn-1 responses for roads A, B and C, kept because they are the provenance of the two archived batches in `runs/archive/pre-priority-bias-2026-08/`. Nothing runs from them any more.

They were retired on 2026-08-30, when the fork moved from turn 1 to turn 2 and turn 1 became a single fixed opening. Three things had gone wrong with them, and the third is why re-drawing was not enough on its own:

- They open `## Portfolio` with `Nothing in flight.`, from a prompt that told the actor the inherited programmes belonged in its reasoning and never in the list. The prompt now seeds two of them into the portfolio directly.
- They declare `Capital cost:` and `Lead time:`, which the rebuilt measure mechanics do not read. A measure now states `Size:` and `Finishes on turn:`, judged once when it is first written down.
- Road A launches a compute programme alongside the inherited InvestAI Gigafactories. The prompt now names that specific move as the one the Union cannot credibly make, so road A could not be re-drawn: 20 fresh draws under the current prompt returned no category 4 measure at all.

The wider finding from that re-draw is in the story README. In short, the spread the three roads were selected from no longer exists – 16 of 20 draws chose category 6 and the remaining 4 category 5 – which is what moved the fork to turn 2.
