# **What 150 simulations of Europe 2032 show**

The interactive story Europe 2032 is a showcase for LLM-powered scenario gaming: storytelling built on branching simulations, not an analysis of the Europe 2032 worlds.

In parallel to the simulations for the stories, though, there are 150 start-to-end simulations of the Europe 2032 worlds – 50 for each of the three underlying worlds:

- **Acceleration** (A), where recursively self-improving AI and artificial general intelligence are likely within 5–10 years.
- **Verification-bounded** (V), where AI becomes superhuman only in math, coding and other areas with "verifiable rewards".
- **Plateau** (P), where AI progress stalls.

Here is an analysis of what those simulations tell us. The analysis focuses mainly on what leads to or prevents catastrophic events, but also how events and actions that the LLMs themselves invented affected the world.

One corpus note: the comparison popups in the published story are built from 160 runs, not 150 – including ten pilot runs. A reader who opens them will see numbers slightly diluted next to the ones here.

## For catastrophic events, the scripted mechanics dominate

The short story: **To the first order, the world is explained by the mechanics written into the scenario.**

32 of 150 runs (21%) suffer at least one catastrophe. The occurrence is almost completely explained by AI acceleration: 29 of the runs with catastrophic events are found in the A worlds, 2 in the V worlds and 1 in the P worlds.

These catastrophic events were written to only be possible at AI capability above 80 (catastrophic loss of control), 75 (war) and 65 (catastrophic bio incident). The underlying mechanics make AI capabilities reach 86–100 in A while V and P top out at around 70. Which worlds have catastrophic events is thus basically an effect of how the scenario was written from the start.

There are more clearly visible effects of the conditions written into the scenario's DNA:

- War was scripted to be more likely when recursively self-improving AI was triggered (the case for 19 of 20 wars), and also more likely after Taiwan blockades (8 of 20) and increased export controls (7 of 20).
- Catastrophic loss of control was scripted to be more likely after evaluation anomalies or loss-of-control incidents (present in 13 of 15), and the risk is doubled if AI safety is below 45. That condition held in all 15 cases, but it tells us little: AI safety falls below 45 in every A world.
- Catastrophic bio incidents were scripted to be more likely after bio uplift findings or bio incidents (present in 10 of 14).

Single-event precursors are weak predictors on their own, though. It is the combination of high capability *and* probability-raising events that kills.

One thing decreases the probability of catastrophic events: An AI agreement between the US and China should halve the probability of war, according to the scenario rules. In the A worlds with such agreements, the war rate was 1/3 instead of 1/2 (11 of 32 runs with an agreement, against 9 of 18 without – small numbers, so hold lightly, and a smaller drop than the "halve" in the rules).

### Actions by the EU don't matter much

- Some mitigating measures from the EU halve some catastrophic probabilities, but the measures are rarely finished (e.g. only ~2 finished category-3 restrictions on bio-capable AI in 150 runs) and the aggressive dynamics of the A worlds dominate. A fair summary is that after 2030 or so, nothing the EU builds keeps catastrophes away in the A worlds. There are some signs that early measures mitigating bio risks actually prevent catastrophic bio incidents, though. (Of the 19 runs holding some kind of bio screening – mostly finished category-6 detection, and 14 of the 19 on the V and P arms where bio catastrophes barely occur – none overlap with the 14 runs with catastrophic bio incidents. Within the A worlds alone the comparison is 0 of 5 holders against 11 of 45, too thin to carry the claim.)
- EU diplomacy efforts increase the likelihood of an agreement between the US and China, which in turn reduces the catastrophic risks. But the effect is very modest.

**In all, these findings are reassuring since they say that the built-in mechanics work. But they aren't that interesting: they reflect starting points, not conclusions.**

## The emergent dynamics

Across the 150 runs (1950 turns), the game master LLM invented 331 different ids for emergent events, firing 387 times. What do they look like?

### Data centre protests

Protests at sites for data centres or other AI infrastructure are the biggest category, appearing in 97 of 1950 turns. They appear in turns where public sentiment drops more than average (−3.62 vs −2.30), while AI sovereignty (−0.62 vs −0.58) and AI capabilities (+1.72 vs +1.83) are basically unaffected.

There are 18 turns with sabotage against infrastructure sites, which correlates with loss of AI sovereignty (−1.94 vs −0.59 on average).

In Scenario Lab the events are determined before the metrics are updated, so the game master seems to treat these events as causes of the metric drops. Whether they are causes in any stronger sense is harder to say: the same model writes the events and then scores the metrics.

### Unscripted early warnings

Some emergent events cluster *before* catastrophes in the A worlds, although the numbers are small (eight runs). Pre-catastrophe and catastrophe-free turns alike counted in the A worlds only:

- Raised or repriced insurance is 4.3 times as common in the turns leading up to catastrophes, compared to catastrophe-free turns.
- Leaks or coverup revelations are 3.2 times as common.

"Insurance retreat predicts doom" is nowhere in the scenario rules, but the AI game master seems to reach for market and revelation language when a world is coming apart.

There is also a mirror image: Protest events only appear at roughly a third of the frequency in the turns leading up to catastrophes. A plausible reading is that local politics drops out of the story once larger histories take over: siting fights fire at the same rate before catastrophes as in clean worlds, then thin out afterwards, when there is only fallout left to narrate.

## What have I learned?

The Europe 2032 scenario may be too tightly scripted. The strength of LLM-powered scenario simulations is to use LLMs for judgement and creativity, instead of writing extensive rules and formulas. Where to draw the line is difficult, and the line will shift as (cheap and fast) LLMs become more powerful.

After a first version of the story was completed, I rebuilt parts of the scenario with a much more capable model, Muse Spark 1.3 Contributor, instead of Qwen (qwen3-235b-a22b-2507). It is likely that the scaffolding could have been loosened up more.

I still think it makes sense to have explicit percentages for events – not least because it forces the scenario writer to consider probabilities. But my guess is that things modifying the percentages should be kept much more open for the LLM to interpret. "Cooperation around AI safety decreases the risk" instead of "AI safety agreement between the US and China halves the risk". It would be interesting to build a parallel scenario where the rules are looser, and see where the worlds end up.
