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
**Probability:** time_pressure / 250
**Can repeat:** Yes
**Description:** A party publicly abandons a pre-election commitment about who it will or will not work with. This unlocks arrangements that were previously blocked, at a cost in credibility that other parties will exploit.

## Budget Cooperation Offered
**ID:** budget_deal_offered
**Condition:** A party seeking to form a government needs tolerance rather than support, and has something to trade in the budget.
**Probability:** time_pressure / 200
**Can repeat:** Yes
**Description:** A formal offer of budget cooperation is made in exchange for abstention in the prime-ministerial vote. This is the classic Swedish mechanism for buying tolerance without conceding cabinet seats.

## Speaker Shifts the Mandate
**ID:** speaker_switches_mandate
**Condition:** The current sounding has visibly stalled, and another party leader has a plausible claim to try instead.
**Probability:** snap_election_risk / 300
**Can repeat:** Yes
**Description:** The Speaker passes the exploratory mandate to a different party leader. This resets the negotiation around a new centre of gravity and can rescue a process that had settled into deadlock.

## External Security Shock
**ID:** security_shock
**Condition:** May occur at any point; not dependent on the state of the negotiation.
**Probability:** 5%
**Can repeat:** No
**Description:** A serious external security event places sudden pressure on the parties to produce a functioning government quickly. Arguments about national responsibility become available to whoever can use them, and narrow party positions become harder to defend publicly.
