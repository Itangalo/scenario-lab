# Events

Exogenous turning points in the formation process. None of these change the
seat distribution, which is fixed at the start of the run and settled.

## Prime-Ministerial Vote Fails
**ID:** pm_vote_failed
**Condition:** A vote has actually been scheduled: the Speaker must already have named a candidate for prime minister, and the chamber must be voting this turn. If no candidate has been named in the narrative so far, this event is impossible and its probability is 0, regardless of the base rate below. Early turns almost never satisfy this.
**Probability:** 40%
**Can repeat:** Yes
**Description:** The Speaker's proposed candidate is rejected by an absolute majority. Positions harden, the count of failed votes rises, and a fourth failure would force an extraordinary election.

## Party Leader Resigns
**ID:** leader_resigns
**Condition:** A party performed clearly worse than expected, or its leader has been publicly blamed for the deadlock. More likely for parties whose result was poor.
**Probability:** 15%
**Can repeat:** Yes
**Description:** A party leader announces their resignation. The party's positions become temporarily unstable and previously stated commitments become easier for a successor to abandon.

## Stated Pledge Broken
**ID:** pledge_broken
**Condition:** A party is under sustained pressure to abandon a commitment it made before the election, and the cost of continued deadlock has begun to exceed the cost of the reversal.
**Probability:** deadlock_cost / 600
**Can repeat:** Yes
**Description:** A party publicly abandons a pre-election commitment about who it will or will not work with.

**When this fires, the narrative must record an actual abandonment.** Name the party, quote or paraphrase what its leader now says, and name the specific commitment being dropped – "the Centre Party will not support a government containing the Left Party", "the Centre Party will not organise with the Sweden Democrats", "the Social Democrats rule out the Sweden Democrats". That statement is what constitutional constraint 12 requires to lift a veto, and lifting it removes the constraint 11 cap on every arrangement that veto was blocking.

**This event is not general momentum.** It is one party breaking one named promise, at a real cost in credibility that its opponents will use against it for the rest of the run. A turn in which the event fires and the narrative has parties *reaffirming* their commitments has not modelled the event at all: if no pledge is actually abandoned, do not treat the event as having occurred and do not let it move any metric.

## Budget Cooperation Offered
**ID:** budget_deal_offered
**Condition:** A party seeking to form a government needs tolerance rather than support, and has something to trade in the budget.
**Probability:** deadlock_cost / 200
**Can repeat:** Yes
**Description:** A formal offer of budget cooperation is made in exchange for abstention in the prime-ministerial vote. This is the classic Swedish mechanism for buying tolerance without conceding cabinet seats.

## Speaker Shifts the Mandate
**ID:** speaker_switches_mandate
**Condition:** The current sounding has visibly stalled, and another party leader has a plausible claim to try instead.
**Probability:** snap_election_risk / 300
**Can repeat:** Yes
**Description:** The Speaker passes the exploratory mandate to a different party leader. This resets the negotiation around a new centre of gravity and can rescue a process that had settled into deadlock.

## Extraordinary Election Date Announced
**ID:** snap_election_date_announced
**Condition:** The process has visibly failed to converge. This requires that **at least two prime-ministerial votes have actually been held and rejected**, or that the Speaker has publicly abandoned the soundings with no constellation close to a majority. If neither has happened in the narrative so far, this event is impossible and its probability is 0, regardless of the base rate below. Turns passing, rising pressure and pessimistic commentary are **not** sufficient: an election date is announced by a government that has run out of options, not by a mood.
**Probability:** snap_election_risk / 200
**Can repeat:** No
**Description:** A specific date for an extraordinary election is set and made public. This is the single sharpest event in the scenario. In December 2014 the announcement of an election date produced a cross-bloc agreement within weeks, and the election was called off – it was the dated threat, not the election, that forced the deal. Parties that lost ground on 13 September now face fighting a campaign they cannot afford, for a shortened mandate that runs only to the next ordinary election. Parties that gained face the same shortened mandate and a smaller prize than it first appears. Expect rapid, visible movement from whoever stands to lose most.

## External Security Shock
**ID:** security_shock
**Condition:** May occur at any point; not dependent on the state of the negotiation.
**Probability:** 5%
**Can repeat:** No
**Description:** A serious external security event places sudden pressure on the parties to produce a functioning government quickly. Arguments about national responsibility become available to whoever can use them, and narrow party positions become harder to defend publicly.
