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

## What the Validation Runs Changed

Four runs of 11-14 turns were used to calibrate this scenario before any batch.
Three findings changed the design, and all three were the same shape: a
constraint that mattered had been written somewhere the model was allowed to
renegotiate.

1. **Invariants moved from `metric-rules.md` to `constitution.md`.** The cap on
   viability, the meaning of the Centre Party's vetoes, the limit on single-turn
   swings and the ceiling on `time_pressure` are not evolving physics – they are
   what the metrics mean and what the parties publicly committed to. In the
   evolvable file the model rewrote the viability cap on *every* unfrozen turn,
   eight turns running, and `viability_cross_bloc` swung 85 to 15 to 75. In the
   constitution the same metric rose smoothly from 20 to 85 across fourteen
   turns, and `time_pressure` stopped saturating halfway through the run.

2. **Rule evolution disabled entirely.** Moving the invariants contained the
   damage but did not stop the behaviour: the model simply rewrote whichever
   rule sat nearest the action instead, again on every single turn.
   `max_changes_per_turn: 1` means "exactly one" in practice. Since the physics
   here is procedure written in law, evolution added cross-run variance without
   insight.

3. **Referee attempts raised from 2 to 3.** The constitution now carries more
   that can be violated. Under the new constraints the referee flagged 4 of 14
   and 9 of 13 turns and corrected all but one – a `viability_right_bloc` move
   from 47 to 52 that crossed the procedural threshold on rhetoric alone. One
   unresolved violation in 27 turns is the accepted residual.

Earlier smoke tests fixed a `pm_vote_failed` condition that was evaluated at 40%
before any vote could have been held, and anchored the viability reference points
to procedural facts rather than sentiment.

## A Conditioned Batch That Did Not Condition

The first `l-crosses` batch is a cautionary case worth keeping. Every draw gave
the Liberals 14–21 seats, and the runs simulated them as a party without seats.

Nothing was wrong with the draw: the seat table showed the number, the
commitments section said they had cleared the threshold. But every *other* signal
in the scenario points the other way — polling at 1.9%, background describing
their worst result since 1967, an actor file whose out-of-chamber branch is the
longer and more vivid of the two. A single row in a table does not overcome a
prior that strong, and the batch silently measured nothing.

The general lesson: **a fact that must override a strong prior has to be stated
as its own sentence, in both directions, saying what follows from it.** Putting
it in a table and trusting the reader to notice is not enough. The sampler now
writes "The Liberals ARE in the chamber… any narrative describing them as outside
parliament is wrong", and the actor file leads with finding that sentence.

This is the same failure that produced the referee ignoring the notepad and the
veto cap being applied to constellations containing neither vetoed party: the
information was present and insufficiently salient.

## Open Question: What Does the Centre Party's Veto Actually Block?

**This is the most consequential unresolved item, and it is a research question
rather than a calibration one.**

The source material states that the Centre Party "will not support any government
**containing** the Left Party". Two readings are available, both defensible, and
they give opposite answers to the scenario's central question:

- **Broad:** any arrangement in which V supports an S-led government is blocked.
  Run with `qwen3-235b-a22b-2507`, this produces an S-led minority government
  carried by Centre abstention in 15 of 20 runs and no V-borne government at all.
- **Narrow:** only V *in cabinet or in formal machinery* is blocked; V voting a
  government through from outside is not. Run with `stealth/ox-alpha` on five
  matched draws, this produces four governments resting on V — the model wrote
  "its veto concerns V in cabinet and formal machinery, not S governing".

The narrow reading is a real distinction in Swedish practice (koalition versus
samarbetsavtal versus passivt stöd) and is arithmetically available: left plus
Centre is 181–191 seats in those draws, comfortably past 175.

**The headline result therefore depends on one word.** Two models read it
differently and both were internally consistent, which means the ambiguity is in
the source material, not in either model.

**To resolve:** find what the Centre Party has actually said during this
campaign, specifically about tolerating an S-led government that V votes for
without entering. Then state it unambiguously in `background/context.md` and in
`source-material/actors.md`, in the same explicit form now used for the Liberals'
threshold status. Until then, treat the 75%/10%/10%/5% distribution as
conditional on the broad reading.

**Resolved 2026-08-23.** The research came back with a third answer: neither
reading is right as a fixed rule.

- Thand Ringqvist's categorical formulation is scope-limited to cabinet: "Vi
  kommer inte att acceptera Vänsterpartiet i en regering och vi kommer heller
  inte stötta en regering som är beroende av Sverigedemokraterna" (SVT). So
  the *veto itself* is narrow — the broad reading is not what C has said.
- But the tolerance path is not open either. On an S-led government carried by
  V from outside, the door is "inte formellt stängd" — conditional on V
  dropping its cabinet demand, and requiring her to "ta tillbaka det till min
  partistyrelse" (TV4). On budget negotiation with V: "den frågan ligger inte
  på bordet".
- V has made cabinet seats an ultimatum for supporting Andersson, so the
  narrow path additionally requires a public V climbdown.

The correct modelling is therefore: **narrow veto, plus a conditional
tolerance path gated by two live uncertainties** (V's climbdown, C's internal
approval) — the same treatment as L's threshold, not a hard constraint either
way. `background/context.md`, `source-material/actors.md` and
`source-material/uncertainties.md` were updated 2026-08-23 to state this.

Consequence: the 75%/10%/10%/5% distribution was conditioned on a broad
reading that C has not actually committed to, and the stealth/ox-alpha runs
assumed a frictionless narrow reading that ignored the ultimatum standoff.
Both arms are superseded; the scenario needs a re-run on the corrected source
material before the 13 September deadline.

## Migration to Adjustable Statements (2026-08-23)

The scenario now uses the framework's statement ledger: each actor holds
tiered statements (`position` / `commitment` / `identity`) that carry forward
verbatim and change only through an explicit, grounded proposal. Tier
assignment came straight out of `constraint-ledger.md` — the four load-bearing
constraints became commitment-tier statements, tactical goals became positions,
and each actor got one identity statement.

**Constitution rules 11 and 12 were rewritten to defer to the ledger.** They
previously encoded the Centre Party's vetoes as fixed metric caps liftable only
by a public attributed statement. With the vetoes now living in C's ledger as
adjustable commitments, two mechanisms owned the same fact and would have
fought: C could change its statement while the constitution went on capping the
metric. Rule 11 now caps what a *standing* veto blocks and rule 12 points at the
actor's ledger as authoritative. The metric behaviour is unchanged; what changed
is which document owns the question.

Note the general principle, since it will recur in other scenarios: the
constitution holds absolutes, the ledger holds what an actor may reconsider. A
constitution clause that *references* a commitment is fine — a metric cap has to
name what it caps. A constitution clause that *owns* what should be adjustable
is a design error.

**What the first runs showed.** A 4-turn and a 14-turn run produced zero
statement changes across 144 actor-turns. That is the right answer rather than a
frozen one: both runs converged toward S–C–MP, which contains neither the Left
Party nor the Sweden Democrats, so no commitment had to break. The ledger is
visibly in the model's reasoning — the world state records "V remains committed
to *cabinet_or_nothing*", and C applies the dependence test in those words.

Because no proposal ever fired, the gate's permissive half was tested separately
in `tests/evals/statement-relevance/`. That eval caught a real laundering
failure — a referee accepting an unrelated SD press motion as grounds for the
Left Party abandoning its cabinet ultimatum — which was fixed prompt-side.

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
