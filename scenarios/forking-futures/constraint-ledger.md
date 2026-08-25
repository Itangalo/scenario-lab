# Constraint Ledger — Forking Futures

## Why this ledger reads differently from the others

In `swedish-government-formation-2026` the ledger adjudicates against reality:
each ruling is settled by what a real party leader actually said, and expert
sign-off is a gate before runs are paid for. **This scenario has no real-world
referent.** The regulator is a deliberate composite — "the direction an EU-,
UN- or OECD-like body pushes AI policy in" — so there is no source to quote and
nothing an expert could contradict at the level of fact.

The load-bearing constraints here are therefore *mechanism* constraints, not
commitments, and the honest verdict category is **settled by design**: the text
was sharpened until one reading remained, and the sharpened wording was folded
back into `constitution.md` and `events.md`. Two-track LLM interrogation was
not run, because divergence between tracks would only have told me the text was
vague — which is a defect I can fix directly rather than adjudicate.

What remains genuinely open is listed at the end and is handled as a limitation,
not silently resolved.

---

## C1 — One new measure per turn

**Operational statement:** The regulator may introduce at most one new measure
per turn and must name exactly one priority. (`constitution.md` §4,
`background/actors/regulator.md`.)

| Edge case | Ruling | Status |
|---|---|---|
| A "package" heading covering three instruments with different lead times | Two or more measures. Only the first is admitted this turn. | settled by design |
| Extending a measure already in flight to a new jurisdiction | Modification, not a new measure. Does not consume the slot; returns the measure to *under implementation* and adds one turn of lead time. | settled by design |
| Abandoning a measure and proposing a replacement in the same turn | The replacement is a new measure and consumes the slot. Abandonment costs capital (metric rule 8). | settled by design |
| Naming two priorities, or none | Invalid turn; the referee must reject it. | settled by design |

## C2 — Fully implemented

**Operational statement:** A measure's effect scales with the phase reached;
*fully implemented* means in force and actually being enforced in every
jurisdiction the measure names. (`constitution.md` §5.)

| Edge case | Ruling | Status |
|---|---|---|
| In force domestically, agreed in principle by the US | Not fully implemented. Domestic half-effect only (metric rule 14). | settled by design |
| In force everywhere named but with no enforcement capacity behind it | Not fully implemented. Enforcement is part of the definition. | settled by design |
| Fully implemented, then a party covertly defects (`covert_defection`) | Remains fully implemented; the defection removes the effect in that jurisdiction and costs capital when discovered. | settled by design |

## C3 — Political asymmetry

**Operational statement:** A measure is never cheaper before an incident of the
class it addresses than after one. (`constitution.md` §6, metric rule 9.)

| Edge case | Ruling | Status |
|---|---|---|
| `cyber_recon_wave` fires; does a cyber measure get the discount? | No. A precursor is not an incident. This is the constraint that makes anticipation genuinely expensive. | settled by design |
| A whistleblower discloses a dangerous capability that was never exercised | No discount. No realised harm. It may still move sentiment and capacity. | settled by design |
| `bio_incident` fires; does the discount extend to a cyber measure? | No. The discount is class-specific: the measure must prevent, detect or absorb the harm the event's description names. | settled by design |
| `bio_incident` fires; does it discount a category 4 evaluation-capacity measure? | Yes, if the narrative connects that capacity to detecting this class of harm. This is the one place the ruling depends on narrative judgment. | settled by design, judgment-dependent |

## C4 — Gate windows

**Operational statement:** A gate is open if its precursor occurred within the
stated number of completed turns, excluding the current one. (`events.md`,
gate rule 1.)

| Edge case | Ruling | Status |
|---|---|---|
| Precursor fires this turn — is the gate open this turn? | No. It opens next turn. Otherwise precursor and escalation could land together, which would destroy the monitoring question. | settled by design |
| Precursor fires twice inside one window | The window runs from the most recent occurrence. | settled by design |
| Escalation fires while the gate is shut | Legitimate — the shut-gate probability is non-zero on purpose. False negatives are part of what the monitoring question measures. | settled by design |

## C5 — Nothing binds the US or China automatically

**Operational statement:** Compliance outside the regulator's jurisdiction must
be established in the narrative before any metric moves as though it had been
achieved. (`constitution.md` §3, metric rule 14.)

| Edge case | Ruling | Status |
|---|---|---|
| A US-headquartered lab complies in order to keep selling into the regulator's market | Compliance established, for that lab and that product line only. Its domestic training runs are untouched. | settled by design |
| The regulator's standard is voluntarily adopted by a US standards body | Compliance established at half effect, and reversible. | settled by design |
| Capability growth falls after a measure the US never accepted | Not permitted. Metric rule 6 requires the measure to bind the leading jurisdiction. | settled by design |

## C6 — The regulator's staked statements

`no_safety_for_competitiveness_trade` and `act_before_proof` are the two
commitment-tier statements that can actually be broken under pressure, which is
what makes them worth having.

| Edge case | Ruling | Status |
|---|---|---|
| Delaying a measure for economic reasons without weakening its content | Not a breach of `no_safety_for_competitiveness_trade`. Delay is not dilution — but the delay is visible and the world may price it anyway. | settled by design |
| Narrowing a measure's scope to win agreement | Breach, if the narrowing removes a safety requirement. A statement change must be proposed and will be priced. | settled by design |
| Acting with no indication at all, purely pre-emptively | Consistent with `act_before_proof` — the statement sets a floor on evidence, not a ceiling. The cost is paid in capital, not in credibility. | settled by design |

---

## Open

**O1 — What counts as a good outcome.** The scenario declares no objective
function and no termination condition, so "which measures pay off" is settled at
analysis time by reading metric trajectories, not by anything inside a run. This
is deliberate: fixing a welfare function would decide the essay's conclusion in
the scenario files. It does mean `synthesize` must be given an explicit basis
for comparison, and that different bases could give different answers. **Handled
as an explicit limitation, and it belongs in the register discipline of any text
built on these runs.**

**O2 — Lead times per measure type.** The constitution fixes minimum lead times
(1 turn low-cost, 2 turns high-cost) but the realistic figure differs sharply
between, say, an incident-reporting duty and an energy build-out. **To be
calibrated from the prototype runs**; until then the Game Master judges it, and
that judgment varies between runs.

**O3 — Whether the world feels too passive.** With one actor, labs and states
respond only through metric rules and events. Design brief: upgrade to a second
actor only if prototype runs show the world reacting implausibly little.
**Open until prototype runs are read.** First partial answer from the plateau
batch: the emerging-developments mechanism (see `design-notes.md`) now gives
unfired developments narrative presence across turns, which addresses the
"world only twitches through discrete events" half of the concern; whether that
suffices waits on a full batch.
