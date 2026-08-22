# Information Bank Index

Built 2026-08-22 for the research question in `../research-question.md`. The
user supplied no material, so everything here is web research or model
knowledge. There is no `[user]`-tagged content anywhere in this bank.

## Files

### `world-state.md`
The situation at election night: the date, the 349/175 arithmetic, the outgoing
Tidö arrangement, and the formation procedure under negative parliamentarism.

- Provenance: mostly `[source]` (regeringen.se, Regeringsformen ch. 6), some
  `[model]` for pacing and the final-count mechanic.
- Trust: high on procedure, which is constitutional and stable.
- Does **not** cover: the Speaker election mechanics in detail, or what happens
  procedurally if a snap election is triggered.

### `quantities.md`
Polling from three institutes, the 2022 baseline, the threshold mechanic, seat
allocation, and how far Swedish polls historically miss.

- Provenance: `[source]` for all figures (Wikipedia poll aggregation, GU
  Rapport 2022:8); `[assumption]` for the sampler calibration derived from them.
- Trust: high on the numbers, moderate on the derived sigma values, which are
  my inference rather than a published figure.
- Does **not** cover: constituency-level data, or per-institute house effects
  beyond noting that the institutes disagree.

### `actors.md`
The eight parties, and — more importantly — the constraint graph of who has
ruled out whom.

- Provenance: `[source]` for the four stated constraints and three leader
  names; `[model]` and `[assumption]` for strategic reasoning.
- Trust: high on the stated constraints, which are the load-bearing facts.
  Lower on inferred motivations.
- Does **not** cover: five of eight party leaders (see Known Gaps), internal
  party divisions, or the parties' actual policy platforms beyond the
  cooperation question.

### `uncertainties.md`
The turning points, with reasoning about how likely each is.

- Provenance: mixed; the L threshold analysis rests on `[source]` figures with
  `[assumption]` inference on top.
- Trust: moderate. These are the judgement calls most likely to need revision.
- Does **not** cover: base rates for most events, which are informed guesses.

## Known Gaps

1. ~~Five party leaders unverified.~~ **Resolved 2026-08-22.** All eight are
   now sourced and listed in `actors.md`. Two details carry into drafting: MP
   has two co-spokespersons rather than one leader, and L's leader took over in
   June 2025 and now faces the party's worst polling in decades.

2. **Constituency-level seat data not gathered.** *Handle as:* an assumption in
   design-notes — a national Sainte-Laguë approximation, accurate to a seat or
   two, which is well inside the uncertainty the draw already carries.

3. **Sampler sigma is inferred, not published.** The 1.1-point average
   deviation is sourced; converting it to per-party standard deviations and a
   correlation structure is my own work. *Handle as:* an explicit assumption,
   with the sampler's parameters written down where they can be criticised.

4. **L's crossing probability is low** — low single digits to under ten
   percent of runs. **Resolved 2026-08-22: stratified design**, chosen by the
   user. Two batches: one drawn from the honest distribution, one conditioned on
   L clearing the threshold. They are reported separately and never pooled — the
   conditioned batch answers "what would L's entry mean", not "how likely is
   it". The sampler must therefore support a conditioning flag, and the draws'
   `notes` field must record which batch a draw belongs to so runs cannot be
   mixed up afterwards.

5. **Event base rates are guesses.** Leader resignations and broken pledges have
   no clean base rate. *Handle as:* stated assumptions, with `probability_samples`
   raised so the model's own estimates are averaged rather than taken once.

6. **Campaign commitments gathered only partially.** The four load-bearing
   constraints are sourced (C's double veto, S ruling out SD, S refusing to
   commit). The fuller set of what each party has said during this campaign is
   not. *Handle as:* a limitation recorded in design-notes, and a candidate for
   a further research pass if the smoke test shows actors reasoning from
   commitments the bank does not contain.
