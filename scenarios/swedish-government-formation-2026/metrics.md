# Metrics

These track how close each broad constellation is to actually governing, plus
the pressures acting on the negotiation. They do not track seats: the seat
distribution is fixed on election night, given in the starting context, and
does not move during the simulation.

## viability_right_bloc
**Description:** How close a right-leaning government (M and KD at its core, with SD support in some form, and L if it is in the chamber) is to being formed and surviving a prime-ministerial vote.
**ID:** viability_right_bloc
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 35
**Reference points:**
- 0: Ruled out entirely – a stated veto or arithmetic makes it impossible
- 25: Discussed publicly, but no formal procedural step has been taken toward it
- 50: The Speaker has given an exploratory mandate pointing at this constellation, or formal negotiations between its parties have actually begun
- 75: Parties holding enough seats have publicly declared support or abstention that a vote would probably pass
- 100: This government has been formed and its prime minister elected

## viability_left_bloc
**Description:** How close an S-led government resting on the left (V and MP in some combination, inside or outside cabinet) is to being formed and surviving a prime-ministerial vote.
**ID:** viability_left_bloc
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 35
**Reference points:**
- 0: Ruled out entirely – a stated veto or arithmetic makes it impossible
- 25: Discussed publicly, but no formal procedural step has been taken toward it
- 50: The Speaker has given an exploratory mandate pointing at this constellation, or formal negotiations between its parties have actually begun
- 75: Parties holding enough seats have publicly declared support or abstention that a vote would probably pass
- 100: This government has been formed and its prime minister elected

## viability_cross_bloc
**Description:** How close a government spanning the traditional blocs is to being formed – an S-led government tolerated or joined by C and possibly M, or any arrangement that breaks the bloc pattern rather than working within it.
**ID:** viability_cross_bloc
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 15
**Reference points:**
- 0: Ruled out entirely – no party will cross
- 15: The default at the start; discussed by commentators, not by parties
- 40: At least one party has publicly opened the door in its own name
- 50: The Speaker has given an exploratory mandate across the bloc line, or formal negotiations have actually begun
- 75: Parties holding enough seats have publicly declared support or abstention that a vote would probably pass
- 100: This government has been formed and its prime minister elected

## sd_in_cabinet
**Description:** How close the Sweden Democrats are to actual cabinet seats, as distinct from supporting a government from outside it. This is the substantive question beneath the arithmetic.
**ID:** sd_in_cabinet
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 30
**Reference points:**
- 0: Excluded from government and from any formal support role
- 25: Support party outside cabinet, as in the outgoing arrangement
- 50: Formal agreement with cabinet seats explicitly on the table
- 75: Cabinet seats conceded in principle, portfolios under negotiation
- 100: Sweden Democrats hold cabinet posts in a formed government

## snap_election_risk
**Description:** How likely the process is to end in an extraordinary election rather than a government. Rises with each failed prime-ministerial vote; four failures forces one.
**ID:** snap_election_risk
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 10
**Reference points:**
- 0: A government is essentially settled
- 10: Normal starting uncertainty on election night
- 40: One prime-ministerial vote has failed and positions are hardening
- 70: Two or three votes have failed; parties are openly discussing a new election
- 100: Four votes have failed; an extraordinary election is triggered

## time_pressure
**Description:** Accumulated public, media, market and institutional pressure to produce a government. Rises the longer the country goes without one, and makes concessions cheaper to justify.
**ID:** time_pressure
**Min:** 0
**Max:** 100
**Unit:** index
**Start value:** 5
**Reference points:**
- 5: Election night; nobody expects an answer yet
- 25: Weeks in; commentary turns impatient but nothing is urgent
- 50: A budget deadline or comparable institutional date is approaching
- 75: Sustained criticism; parties are visibly paying a price for the deadlock
- 100: The deadlock is itself the dominant political issue
