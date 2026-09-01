# Metric rules patch — paralysis plus upward-only drift

Replaces rule 11 and appends rule 19. Everything else is inherited from the verification-bounded arm.

11. **`eu_political_capital` recovers from results, erodes from their absence, and can be lent back by the public.**
    - a measure reaching its finishing turn: +4 to +8
    - a measure in flight or finished that visibly blunts an incident when it lands: +1 to +7, judged the same way as rule 13 — the bigger the event and the larger the measure, the bigger the gain. This is the mirror of rule 13: that one pays for acting after the harm, this one for having already acted.
    - a measure abandoned, a deadline missed, a proposal publicly defeated: −3 to −6
    - nothing in flight: −3
    - `public_sentiment` above `eu_political_capital`: +1 to +2, never past sentiment

19. **Below 20, the Union is no longer in control of its own agenda.** Political capital is a budget, and running out of it has to bite.

    While `eu_political_capital` is below 20, and only while it is:
    - **the named priority has no effect, and no cost.** Rule 10's pull-in-by-one-turn does not apply, pushing a measure buys nothing, and the priority's −1 is not charged. Naming one changes nothing at all.
    - **a new measure may fail to start.** Judge it, roughly one turn in three. A measure that fails to start never enters the portfolio, costs nothing, and may be proposed again in a later turn. Say plainly in the narrative what blocked it — a member state withholding assent, a budget line refused, a legal base contested — and never that capital was low.
    - the threshold is not a cliff the actor is told about. It is not named in any prompt the Union reads, and the narrative must not announce that a line has been crossed.

    This is not a penalty stacked on the charge. It is what a Union without standing looks like from the inside: it can still decide things, and the deciding stops carrying.
