# Constitutional Constraints

Hard rules of Swedish parliamentary procedure. These are law, not tendencies,
and no narrative may contradict them.

1. **The riksdag has exactly 349 seats.** An absolute majority is 175. Seat
   counts stated in any turn must match the election result given at the start
   of the run, and must sum to 349.

2. **The seat distribution never changes.** It was settled by the election. No
   event, negotiation, or narrative development may reallocate seats, add a
   party to the chamber, or remove one from it. A party that did not clear four
   percent holds zero seats for the entire run.

3. **Negative parliamentarism governs the prime-ministerial vote.** A candidate
   proposed by the Speaker is elected unless **at least 175 members vote
   against**. A candidate supported by a minority is elected if the opposition
   to them is divided. Never require a majority in favour.

4. **Abstention is not opposition.** Members who abstain do not count toward the
   175 needed to reject a candidate.

5. **Four failures force an extraordinary election.** If the Speaker's proposal
   is rejected four times, an extraordinary election is called. The count of
   failed votes may never exceed four without that consequence following.

6. **The Speaker proposes; the chamber decides.** The Speaker cannot appoint a
   prime minister, cannot refuse to hold a vote indefinitely, and cannot rule a
   party out of consideration.

7. **A party cannot cast more votes than it holds seats.** Support, opposition
   and abstention are all bounded by the party's actual seat count.

8. **Parties outside the chamber have no votes.** A party below four percent may
   speak publicly but cannot vote, cannot be counted toward 175, cannot receive
   cabinet seats, and cannot be part of a governing arrangement.

9. **The prime minister must be a person, from a party in the chamber.** Cabinet
   posts likewise go to parties holding seats.

The following constrain how the viability and pressure metrics may move. They
encode what the metrics *mean* and what the parties have publicly committed to,
not evolving physics, and may not be reinterpreted, softened or qualified by any
metric rule.

10. **Viability above 50 requires a procedural step that has actually occurred.**
    A viability metric may exceed 50 only once the narrative has recorded, **at
    any point in the run**, that the Speaker gave an exploratory mandate covering
    that constellation, or that formal negotiations between its parties began, or
    that parties holding enough seats publicly declared how they will vote.
    Statements of openness, policy annexes, private talks, listening sessions,
    working groups and media campaigns are **not** procedural steps.

    **This is a persistent state, not a per-turn test.** Once such a step has
    occurred for a constellation, the threshold stays unlocked for it for the
    rest of the run. Do not require a fresh procedural step each turn, and do not
    push a metric back down to 50 because nothing procedural happened this week.
    A constellation whose talks are under way keeps whatever viability it has
    earned; it rises or falls on what the parties do, not on the calendar.

    **The notepad is the authoritative record of which steps have occurred.**
    Consult it before concluding that no procedural step has taken place. A
    mandate granted in turn 7 still counts in turn 14 even if this turn's
    narrative does not mention it. Record every procedural milestone in the
    notepad when it happens, naming the constellation it covers.

11. **A veto in an actor's ledger caps what it actually blocks.** Some actors
    hold commitment-tier statements that rule out a constellation. While such a
    commitment stands, cap at 40 any constellation it blocks.

    Concretely, for the Centre Party's two commitments: cap at 40 any
    constellation that requires Centre Party support and places the Left Party
    in cabinet, and any that requires organised Centre Party cooperation with
    the Sweden Democrats, or that depends on the Sweden Democrats while
    requiring Centre Party support.

    **Name the member parties before applying this cap.** The notepad records
    which parties each arrangement contains. An S–C–MP government contains
    neither the Left Party nor the Sweden Democrats, so neither veto touches it,
    regardless of how those parties are behaving elsewhere. Opposition from a
    party is not membership in the arrangement it opposes.

12. **The actor's own ledger decides whether a veto still stands.** These
    commitments are not absolutes and are not owned by this document. They live
    in the actor's statement ledger, and they change only through the statement
    mechanism: the actor proposes the change, names the development that caused
    it, and the change is recorded. Do not infer that a veto has been abandoned
    from mood, pressure, or another party's behaviour, and do not treat one as
    permanent either. **Read the actor's current statements; they are
    authoritative.** If a veto commitment has been changed or retired there, the
    cap above no longer applies and the narrative should reflect what the
    reversal cost the actor.

13. **No viability may move more than 25 points in a single turn** unless the
    narrative names a specific, attributed act that caused it – a party
    withdrawing, a vote failing, a pledge publicly broken. Gradual shifts in
    sentiment do not justify large jumps in either direction.

    **A movement of 25 points or fewer needs no special justification.** This
    constraint is a ceiling on the size of a single step, not a requirement that
    every step be attributed. Do not report a move of 25 or less as a violation
    of this constraint — count the difference before objecting. In particular, a
    rise to 100 that is within the ceiling is a government being formed, and
    blocking it on this constraint prevents the run from ever concluding.

14. **`deadlock_cost` may rise at most 12 points per turn**, and may only rise
    when the narrative names what is being lost – a missed decision, an
    approaching deadline, a failed vote, or an extraordinary election becoming
    more concrete. It may not rise merely because a week has passed, and may not
    fall while no government has been formed.

15. **A constellation holding 175 or more seats cannot be blocked from outside.**
    Under negative parliamentarism no one can assemble 175 votes against a
    constellation that already holds 175 itself. For such a constellation:

    - Constraint 11 does not apply. It needs no outside party's support, so no
      outside party's veto touches it. The Centre Party's vetoes are irrelevant
      to a bloc that does not need the Centre Party.
    - Constraint 10's ceiling is satisfied by the arithmetic. It does not need a
      procedural step to be *possible*; it needs one only to be *enacted*.
    - Its viability starts at no less than 60 and moves on whether its own member
      parties agree with each other — over portfolios, policy and the premiership
      — not on what anyone outside it does.

    Check the seat table in the starting context before deciding any
    constellation's viability. Arithmetic outranks atmosphere: a bloc with a
    majority that fails to govern must fail because its own parties fell out, and
    the narrative must say which ones and over what.

    **Never explain such a constellation's movement by "lack of external
    support", "no outside backing", or another party's veto.** Those reasons are
    unavailable by definition — it has the seats and needs nobody. If its
    viability falls, name the member party that balked and what it balked at. A
    narrative that describes an internal split and then blames an outside veto
    has cited a cause this constraint forbids.
