# Metric Rules

The physics of the formation process. Rules 1–10 describe how the metrics move
in response to what the actors do. Rules 11–15 drive the procedure forward, and
16–18 describe what makes parties actually concede. Rule evolution is disabled
for this scenario, so these stay fixed for the whole run.

1. **Viability rises with credible commitment, not with talk.** A constellation's
   viability increases substantially (10–25 points) only when a party actually
   commits to supporting or abstaining. Statements of openness without commitment
   move it a little (0–5 points).

2. **Abstention counts as much as support.** Under negative parliamentarism a
   government passes unless 175 members vote against. When calculating whether a
   constellation could survive a vote, count declared abstentions as helping it,
   not as neutral.

3. **A constellation that cannot reach 175 opponents is viable regardless of its
   size.** Do not treat lacking a majority as low viability. Treat *the existence
   of 175 members willing to vote against* as low viability.

4. **The veto caps and the procedural threshold are constitutional, not rules.**
   See `constitution.md`, constraints 10 to 13. They are not open to
   reinterpretation here and must not be restated, softened or qualified in this
   file.

5. **Viabilities are not required to sum to anything.** Several constellations can
   be simultaneously plausible or simultaneously dead. Only one can reach 100.

6. **Reaching 100 ends the process.** When a constellation reaches 100, a prime
   minister has been elected. Other viabilities drop toward 0 in the same turn.

7. **`deadlock_cost` moves on what is lost, not on weeks passing.** Raise it when
   the narrative names something concrete: a decision the caretaker government
   declined to take, an approaching institutional deadline, a failed vote, or an
   extraordinary election becoming more concrete. If nothing was lost this turn,
   it does not rise. Its ceiling per turn is constitutional; see
   `constitution.md`, constraint 14.

8. **A high `deadlock_cost` makes concessions cheaper.** Above 50, parties become
   measurably more willing to break commitments and accept arrangements they
   previously refused.

9. **Snap-election risk tracks failed votes.** It rises roughly 20–25 points per
   failed prime-ministerial vote and falls when a viable constellation gains
   commitments. At four failed votes it is 100 and the process ends.

10. **SD cabinet proximity moves only on explicit concessions.** It rises when the
    Moderates or Christian Democrats concede something concrete about portfolios,
    and falls when they publicly rule it out. Sentiment alone does not move it.

## Procedure: How a Government Actually Gets Formed

Without these the process cannot reach a conclusion, because nothing converts a
promising constellation into an elected prime minister.

11. **The chamber convenes, elects a Speaker, then takes up the premiership.**
    Narrate that sequence across the first two or three turns. Under RF 6:3 the
    vote on whether the sitting prime minister may remain follows shortly after
    the election. Which side controls the Speaker's chair follows from the seat
    distribution and is worth naming, because the Speaker runs everything after
    that. The vote is a real procedural step and satisfies constitutional
    constraint 10 for the constellation it tests.

12. **The Speaker's soundings produce an exploratory mandate by turn 4.** The
    Speaker consults each party leader and hands the mandate to the leader with
    the strongest claim – normally the largest party, or the leader of the
    constellation with the highest viability. Name who receives it. This is a
    procedural step.

13. **A constellation at 70 or above is put to a vote within two turns.** When a
    constellation reaches 70 and its candidate holds or is handed the Speaker's
    mandate, the Speaker puts that candidate to the chamber. Narrate the vote and
    count the declared positions party by party.

14. **A candidate not opposed by 175 members is elected.** Under negative
    parliamentarism the vote succeeds unless at least 175 members vote against.
    Count abstentions as not opposing. When a vote succeeds, set that
    constellation's viability to 100 in the same turn: a prime minister has been
    elected and the run is over. When at least 175 do vote against, the
    `pm_vote_failed` event applies instead.

15. **After a failed vote the mandate moves.** The Speaker either re-proposes the
    same candidate or hands the mandate to another leader. Snap-election risk
    rises 20–25 points. At four failures an extraordinary election follows.

## What Makes Parties Concede

Two mechanisms are visible in the Swedish record, and both are live here.

16. **The dated threat, not the passing of time.** In December 2014 nothing moved
    for weeks, an extraordinary election date was announced, and a cross-bloc
    agreement followed within weeks – the election was then called off. Model
    this shape: concessions arrive in a rush once `snap_election_date_announced`
    has fired, not gradually before it.

17. **The threat is asymmetric, and the draw says how.** The starting context
    gives each party's seats against 2022. A party that lost ground cannot afford
    a campaign and will move first and furthest once a date exists. A party that
    gained is tempted by a fresh election, but wins only a shortened mandate
    running to the next ordinary election, which blunts the temptation. Reason
    about each party from its own row in that table, not from a shared sense of
    urgency.

18. **The kingmaker eventually has to choose.** The 2018–19 formation took 134
    days and ended without any real prospect of an extraordinary election: the
    pivot parties simply decided to enable one side and charged for it. From
    roughly turn 8, a party holding vetoes against both sides pays a rising price
    for obstruction – in its own voters, its regional organisations, and its
    claim to be constructive. It becomes progressively more likely to break the
    cheaper of its vetoes rather than keep both.
