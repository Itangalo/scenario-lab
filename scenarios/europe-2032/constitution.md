# Constitutional Constraints – Europe 2032

## Invariants

1. **The trajectory regime.** The regime this run is in – ACCELERATION, VERIFICATION-BOUNDED or PLATEAU – is fixed from turn 1 to the last turn, and is Game Master information that stays in the Game Master's inputs.

   Three things follow, and they are one rule, not three:

   - *It never changes.* No event, action or rule change may move a run from one regime to another.
   - *Nobody inside the simulation knows it.* The EU is never told which future it is in. It may reason about which regime it might be in, and name candidates; it may not know.
   - *The narrative never names it* – not as a label, not as a parenthetical, not as "consistent with" anything. Write what happened to capability this turn; do not name the pattern it belongs to. Operationally, and this is checkable character by character: **the exact uppercase strings `ACCELERATION`, `VERIFICATION-BOUNDED` and `PLATEAU` must not appear anywhere in the narrative**, including subheadings. The uppercase labels name this run's assigned future; generic lowercase talk of plateaus, acceleration or uneven progress is legitimate inference and stays allowed. Descriptions of emergent-event candidates count as narrative for this purpose: they reach the EU when the event fires.

   *How fast capability grows inside the regime is metric rule 1's business, not this document's.* The constitution fixes which regime a run is in and who may know about it; it says nothing about growth rates.

2. **Capability is accumulated and does not fall.** `ai_capability` and `openweight_capability` may rise or stay flat, and `openweight_capability` never exceeds `ai_capability`. The single exception is catastrophic physical destruction of the compute base, which must be narrated as such.

3. **Nothing the EU decides binds the United States, China or the frontier developers automatically.** Compliance outside its own jurisdiction must be established in the narrative – through agreement, market access, standards adoption, supply-chain leverage or pressure – before any metric moves as though it had been achieved.

4. **The American posture, once elected, is standing.** From the turn `us_election_2028` fires, the `US_POSTURE:` line is carried in the notepad every subsequent turn and conditions the world under metric rule 18. It may not be dropped, reinterpreted or replaced by a different posture later in the run.

## Modelling choices

5. **One new measure per turn, and one named priority.** The EU may introduce at most one new measure per turn, and must name exactly one measure as its current priority. A turn's output that introduces two measures, or names no priority, is invalid.

   A *new measure* is a distinct instrument with its own implementation track. Widening the scope of a measure already in flight – extending it to another jurisdiction, adding a sector – is a modification, not a new measure: it does not consume the turn's slot, but it returns that measure to *under implementation* and adds a turn to its remaining lead time. Bundling several instruments under one heading is one measure only if they share a single implementation track and a single lead time; otherwise it is two proposals and the turn's slot allows only the first.

6. **No measure is implemented instantly.** Every measure passes through proposed → decided → under implementation → fully implemented, advancing at most one phase per turn. Minimum time from proposal to full effect is one full turn for low-cost measures and two for high-cost ones. Effect scales with the phase reached; a measure that is merely proposed has no effect on any metric. *Fully implemented* means in force and actually being enforced in every jurisdiction the measure names. A measure in force at home and merely agreed in principle abroad is not fully implemented, and gets the domestic half of its effect only.

7. **Political asymmetry is one-directional.** A measure is never cheaper in political capital before an incident of the class it addresses than after one. Anticipatory action always costs more than the same action taken reactively. An *incident of the class it addresses* is an event that has actually occurred and whose description names harm the measure is designed to prevent, detect or absorb. A precursor is not an incident, and neither is rising tension: the discount is earned by realised harm.

8. **The two stocks must be free to move apart.** `eu_ai_sovereignty` and `eu_political_capital` are separate quantities, and the claim that they are one is what these runs exist to test. Metric rule 9's guard is constitutional: sovereignty's contribution to political capital never exceeds +3 in a turn and never dominates the other terms. A run reaching 2032 with high political capital and low sovereignty is a legitimate outcome, not an error to be corrected.

9. **The narrative must not telegraph.** It may not state or imply that an event gate is open, name a probability, forecast a specific future event, or write anticipatory sentences about what is coming. Tension, coincidence and ambiguous reporting are permitted; prediction is not. Gate state exists in the event evaluations, and belongs nowhere else.

10. **No metric moves more than 25 points in one turn.** This is a hard bound on every metric, applied to the number alone. It is not a licence to audit every movement against the metric rules: growth inside the ranges those rules give, including the compounding capability growth that follows `rsi_onset`, needs no further justification and is not a violation of this rule.
