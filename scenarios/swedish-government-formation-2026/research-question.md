# Research Question

Which government constellations are reachable from the Swedish general election
of 13 September 2026, how often does each one occur, and what decides which it
becomes?

## Why This Question

The user wants to know who will govern Sweden, but as a distribution rather
than a single prediction: which outcomes are live, roughly how likely each is,
and which bargaining moves are decisive. Knowing that a particular
constellation is reachable only through a specific concession changes how one
reads the campaign's closing weeks and the negotiation coverage afterwards.

The question also has a hard answer date, which makes it unusually valuable as
a test of the scenario pipeline: the simulation can be scored against reality
within months.

## Frame

- Start: 2026-09-13, election night, results known
- Time scale: 1 week per turn
- Horizon: 20 turns (~4.5 months, covering the 2018 record of 134 days)
- Actors: all eight riksdag parties (S, M, SD, C, V, KD, MP, L), each as its own
  actor. This exceeds the 3-6 guideline and was a deliberate user decision:
  aggregating parties into blocs would destroy the question, since the question
  is precisely which parties end up together. Actors run in parallel, so eight
  costs roughly 8x in tokens but little in wall-clock.
- The Speaker (talmannen) drives procedure rather than an interest, and is
  modelled through metric rules and events rather than as an actor.
- Candidate metrics: viability of each broad constellation (right, left,
  cross-bloc), how close SD is to actual cabinet seats as distinct from a
  support role, snap-election risk, and time pressure. All 0-100.
- Seat distribution is *input*, not simulated: each run starts from its own
  sampled result (see Sampling below).
- Turning points to model as events: a party's threshold outcome confirmed in
  the Wednesday final count, a party leader resigning after a poor result, a
  stated cooperation pledge being broken, a failed prime-ministerial vote (four
  are allowed before a snap election), budget cooperation offered in exchange
  for tolerance, and an external security shock forcing a broad settlement.

## Sampling

Each run draws its own starting world rather than sharing one, because the
decisive uncertainty is arithmetic: small shifts well inside polling error
change which coalitions are possible at all. The draw sets the seat
distribution and a correlated set of pre-election commitments, since a campaign
that produced an unusually strong result for one party is also a campaign that
left different things said out loud.

This required a framework change: Scenario Lab could previously vary event dice
but not starting conditions. Starting-state draws were added for this purpose
(see `docs/SCENARIO_TECHNICAL_REFERENCE.md`).

## Criteria Check

1. **Simulable** – Pass. Government formation is genuine multi-actor bargaining
   with path dependency; 2018 took 134 days.
2. **Bounded in time** – Pass. Starts election night, ends when a prime
   minister is elected or a snap election is triggered.
3. **Paced** – Pass, after splitting. The campaign (slow, weeks) and the
   negotiation (fast, days) were separated: only the negotiation is simulated,
   and campaign uncertainty enters through the draw.
4. **Populated** – Pass, unusually so. Eight actors with a genuinely tight
   constraint graph.
5. **Measurable** – Weak. The answer is categorical (a coalition), encoded as
   continuous viability metrics. This is the most constructed part of the
   design and the first thing to revisit after the smoke test.
6. **Genuinely uncertain** – Pass. The left bloc leads in polling but has no
   easy path, because the Centre Party vetoes both directions.
7. **Open, not leading** – Pass. Reframed from "who will govern" to a
   distribution over reachable outcomes with stated drivers.

## Proposed `research_questions:` Entry

To be copied into `scenario.yaml` by the drafting step, so that `synthesize`
answers these explicitly rather than generically. Metric and event ids are
provisional and must be reconciled with the drafted files.

```yaml
research_questions:
  - id: rq_reachable_constellations
    question: "Which government constellations are reachable from the 2026 election result, and how often does each occur?"
    metrics: [viability_right_bloc, viability_left_bloc, viability_cross_bloc, snap_election_risk]
    events: [final_count_confirmed, pm_vote_failed, pledge_broken]
  - id: rq_sd_in_cabinet
    question: "Under what conditions does SD move from support party into cabinet, rather than being kept outside again?"
    metrics: [sd_in_cabinet, viability_right_bloc]
    events: [pledge_broken, leader_resigns]
  - id: rq_threshold_leverage
    question: "How much does the Liberals' threshold outcome change which government forms?"
    metrics: [viability_right_bloc, viability_left_bloc]
    events: [final_count_confirmed]
```

## Out of Scope

- The election result itself is drawn, not simulated. No campaign turns.
- EU and NATO context held fixed.
- No constitutional change during the formation period.
- Government durability after a prime minister is elected. That is a genuine
  and interesting question, on a different time scale (quarters over four
  years), and is deliberately a separate scenario.

## Approved

2026-08-22. The user approved the recommended question and changed two things
from the proposal: every run samples its own seat distribution rather than
sharing one, and all eight parties are actors rather than five plus three
rule-governed background parties. Both changes were made for realism, at a
known cost in run price and in distance from the usual guidelines.
