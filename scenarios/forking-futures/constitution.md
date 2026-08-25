# Constitutional Constraints — Forking Futures

## Invariants

1. **The trajectory regime.** The regime named in this run's starting context —
   FAST, PLATEAU or RLVR-LIMITED — is fixed from turn 1 to the last turn, and is
   Game Master information that stays in the Game Master's inputs.

   Three things follow, and they are one rule, not three:

   - *It never changes.* No event, action or rule change may move a run from one
     regime to another.
   - *Nobody inside the simulation knows it.* The regulator is never told which
     future it is in. It may reason about which regime it might be in, and name
     candidates; it may not know.
   - *The narrative never names it* — not as a label, not as a parenthetical,
     not as "consistent with" anything. Write what happened to capability this
     turn; do not name the pattern it belongs to. Operationally, and this is
     checkable character by character: **the exact uppercase strings `FAST`,
     `PLATEAU` and `RLVR-LIMITED` must not appear anywhere in the narrative**,
      including subheadings. The uppercase labels name this run's assigned
      future; generic lowercase talk of plateaus, acceleration or uneven
      progress is legitimate inference and stays allowed. Descriptions of
      emergent-event candidates count as narrative for this purpose: they reach
      the regulator when the event fires.

   *How fast capability grows inside the regime is metric rule 1's business,
   not this document's.* The constitution fixes which regime a run is in and
   who may know about it; it says nothing about growth rates.

2. **Capability is accumulated and does not fall.** `us_capability` and
   `cn_capability` may rise or stay flat. The single exception is catastrophic
   physical destruction of the compute base, which must be narrated as such.

3. **Nothing the regulator decides binds the United States or China
   automatically.** Compliance outside its own jurisdiction must be established
   in the narrative — through agreement, market access, standards adoption or
   pressure — before any metric moves as though it had been achieved.

## Modelling choices

4. **One new measure per turn, and one named priority.** The regulator may
   introduce at most one new measure per turn, and must name exactly one
   measure as its current priority. A turn's output that introduces two
   measures, or names no priority, is invalid.

   A *new measure* is a distinct instrument with its own implementation track.
   Widening the scope of a measure already in flight — extending it to another
   jurisdiction, adding a sector — is a modification, not a new measure: it does
   not consume the turn's slot, but it returns that measure to *under
   implementation* and adds a turn to its remaining lead time. Bundling several
   instruments under one heading is one measure only if they share a single
   implementation track and a single lead time; otherwise it is two proposals
   and the turn's slot allows only the first.

5. **No measure is implemented instantly.** Every measure passes through
   proposed → decided → under implementation → fully implemented, advancing at
   most one phase per turn. Minimum time from proposal to full effect is one
   full turn for low-cost measures and two for high-cost ones. Effect scales
   with the phase reached; a measure that is merely proposed has no effect on
   any metric. *Fully implemented* means in force and actually being enforced in
   every jurisdiction the measure names. A measure in force at home and merely
   agreed in principle abroad is not fully implemented, and gets the domestic
   half of its effect only.

6. **Political asymmetry is one-directional.** A measure is never cheaper in
   political capital before an incident of the class it addresses than after
   one. Anticipatory action always costs more than the same action taken
   reactively. An *incident of the class it addresses* is an event that has
   actually occurred and whose description names harm the measure is designed to
   prevent, detect or absorb. A precursor event is not an incident, and neither
   is rising pressure in general: the discount is earned by realised harm.

7. **The narrative must not telegraph.** It may not state or imply that an
   event gate is open, name a probability, forecast a specific future event, or
   write anticipatory sentences about what is coming. Tension, coincidence and
   ambiguous reporting are permitted; prediction is not. Gate state exists in
   the event evaluations, and belongs nowhere else.

8. **No metric moves more than 25 points in one turn.** This is a hard bound on
   every metric, applied to the number alone. It is not a licence to audit every
   movement against the metric rules: growth inside the ranges those rules give,
   including the compounding capability growth FAST specifies after `rsi_onset`,
   needs no further justification and is not a violation of this rule.
