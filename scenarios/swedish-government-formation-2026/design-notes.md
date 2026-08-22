# Design Notes

## Central Question

Which government constellations are reachable from the Swedish general election
of 13 September 2026, how often does each occur, and what decides which it
becomes? The full framing, including the criteria check, is in
`research-question.md`.

## Key Design Decisions

**The election is input, not simulation.** Each run starts from its own sampled
seat distribution, produced by `sampler.py` and supplied as a starting-state
draw. The campaign is not simulated: mixing a slow process (opinion over weeks)
with a fast one (bargaining over days) would violate the pacing criterion, and
the user's own framing – "polls today, which can shift a little but not much" –
describes a distribution rather than a process worth simulating.

**Seats are context, not metrics.** The seat distribution never moves during a
run, and a metric that cannot change is background rather than a metric. It is
therefore delivered in the draw's `context` field and stated as fact, with a
machine-readable summary in `notes` so runs can be grouped afterwards. The six
metrics are all genuinely dynamic.

**The draw is final.** An early "final count" event that reallocated seats was
drafted and then removed: it would have invited the model to invent seat numbers,
and fabricated metric values are a documented failure mode in this project. The
constitution now states explicitly that seats never change.

**The answer is categorical, encoded as continuous viabilities.** This is the
most constructed part of the design. Three constellation viabilities plus
`sd_in_cabinet` stand in for what is really a discrete outcome. Rule 6 makes the
encoding legible: reaching 100 means that government was formed. This is the
first thing to revisit if the smoke test looks wrong.

**Eight actors, against the 3–6 guideline.** A deliberate user decision.
Aggregating parties into blocs would destroy the question, which is precisely
about which parties end up together. Actors run in parallel, so the cost is
roughly 8x in tokens and little in wall-clock.

**The scenario refuses to run without a draw.** `scenario.yaml` sets
`requires_initial_state: true`. Without a draw there is no election result and
the simulation is incoherent, but nothing would have said so – the run would
simply have produced confident nonsense, and a batch of twenty would have cost
real money before anyone noticed. The flag was added to the framework for this
scenario and makes the omission a hard error.

**The Speaker is rules and events, not an actor.** The Speaker drives procedure
rather than pursuing an interest. Their power appears through the constitution
and through `speaker_switches_mandate`.

## Assumptions

Carried from the provenance tags in `source-material/`, where every claim is
marked `[source]`, `[model]` or `[assumption]`.

1. **Sampler calibration is inferred, not published.** The 1.1-point average
   deviation per party in 2022 is sourced (GU Rapport 2022:8). Converting it
   into per-party standard deviations and a correlation structure is my own
   inference. Parameters are written explicitly at the top of `sampler.py` so
   they can be criticised and changed.
2. **National-level Sainte-Laguë approximation.** Constituency-level data was
   not gathered. The approximation is accurate to a seat or two, well inside the
   uncertainty the draw already carries.
3. **Metric starting values are judgement calls.** Both bloc viabilities start
   at 35 and cross-bloc at 15, reflecting that on election night the blocs are
   the default frame and crossing is commentary rather than policy. These are
   not derived from anything.
4. **Event probabilities are informed guesses.** Leader resignations and broken
   pledges have no clean base rate. `probability_samples: 3` is set so the
   model's own estimates are averaged rather than taken once.
5. **Party motivations beyond stated commitments are inferred.** The four
   load-bearing constraints are sourced. Reasoning about what each party
   *wants* is `[model]` or `[assumption]` and should be read as plausible
   characterisation, not as reporting.
6. **Time pressure has no empirical anchor.** The 3–8 points per turn in rule 7
   was chosen so that pressure becomes decisive somewhere around turn 8–12,
   which is where historical formations have tended to break.

## Known Gaps

1. **Campaign commitments gathered only partially.** The four constraints that
   shape the problem are sourced; the fuller set of what each party has said
   during this campaign is not. If the smoke test shows actors reasoning from
   commitments the bank does not contain, this needs a further research pass.
2. **Internal party divisions are not modelled.** Each party acts as a unitary
   actor. Real formation crises often turn on internal revolts, and this
   scenario cannot represent that except through `leader_resigns`.
3. **No empirical base rates for the events.** See assumption 4.
4. **Correlation between seats and commitments is asserted, not implemented in
   full.** The sampler draws commitments conditioned on the result, but the
   conditioning is a simple rule rather than anything empirically grounded.

## Weak Spots

- The viability encoding may prove too coarse. "Right bloc" covers several
  genuinely different governments, and only `sd_in_cabinet` distinguishes them.
- Eight actors in a twenty-turn run is a lot of text per turn. If narratives
  become repetitive, reducing `max_turns` is preferable to dropping actors,
  since the actor set is what the user asked for.
- `viability_cross_bloc` may sit dead at 15 for entire runs. If so, that is a
  finding rather than a fault – but it should be checked rather than assumed.

## Study Design

The Liberals' threshold outcome is the largest single swing factor and is also
rare: at 1.9–2.4 percent, clearing 4 percent is roughly a three-sigma move,
softened by tactical vote-lending to an estimated few percent up to under ten
percent of runs.

A single batch would therefore contain almost no runs where the Liberals enter,
which cannot support analysis. The user chose a **stratified design**:

- one batch drawn from the honest distribution, which answers what is likely
- one batch conditioned on the Liberals clearing the threshold, which answers
  what their entry would mean

The two are reported separately and **never pooled**. The conditioned batch
carries no information about how likely that world is; only the honest batch
does. Each draw records its batch in `notes` so the two cannot be confused.

## Deliberately Left Out

- Government durability after a prime minister is elected. A genuine question,
  on a different time scale, and a separate scenario.
- The campaign itself.
- Constitutional change during the formation period.
- Regional and municipal elections held the same day.
