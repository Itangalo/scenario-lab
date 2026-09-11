# Metric Rules v3 (Turn 2)

## Changelog from v2

- No material rule changes.
  - **Motivation:** Rule evolution is frozen through turn 14, so the prior rule set remains in force.
  - **Expected impact:** Metric dynamics continue under the prior rule set.

## Rules

# Metric Rules

One turn is six months. Figures are for this turn: a rule applies in whatever turn its condition holds, and applies again whenever it holds again. A range means judge within it, not average it.

The EU's leverage differs by metric, and the ordering governs everything below: strong on `resilience`, `eu_ai_sovereignty` and `eu_political_capital`; moderate on `public_sentiment`; weak on `ai_safety` and `openweight_capability`, reachable only through market access and international agreement; none on `ai_capability`.

1. **This run's own rate sets the growth of `ai_capability`.** In this run: +1 to +2 per turn while capability is below 60, +0.5 to +1 above it, easing into the **62–68** terminal zone. Returns to scale decline; they do not disappear mid-range. Decelerating progress is still progress – a trajectory that flatlines well below its terminal zone, or re-accelerates under conditions this rule does not give, is misapplying the rule.

2. **`openweight_capability` trails `ai_capability`**
   - `openweight_capability` should normally be set around the middle of its old value and last turn's value of `ai_capability`. Lower when restrictions on open-weight are present, higher if `openweight_frontier_release` just occurred.
   - `openweight_capability` never fall
   - `openweight_capability` never exceeds `ai_capability`

3. **`ai_safety`**
   - `ai_capability` rose and no measure landed on shipped systems: −1 to −3
   - The events `opaque_reasoning`, `capability_jump` or `rsi_onset`: −5 to −12
   - The event `safety_breakthrough`: +5 to +10
   - Finished measure in category 1, 2 or 5 that affects the jurisdiction where frontier models are built, in the turn it finishes: +2 to +4, once. If only affecting inside the EU: 0 to +1

4. **`resilience`**
   - Category 6 measure covering a named class of harm, in the turn it finishes: +3 to +6, once
   - `ai_capability` rose and no category 6 measure is in force: −1 to −2
   - Category 9 measure broadening adoption, in the turn it finishes: −1 to −3, once
   - The event `joint_threat_response`, in the turn it fires: +1 to +3, once

5. **`eu_ai_sovereignty`**
   - Category 4 measure, in the turn it finishes: +3 to +6, once
   - `ai_capability` rose at least 2 this turn: −1
   - An event this turn that takes away or secures the Union's access to AI capacity itself — the compute, the leading models, the supply chain they run on, or a member state's participation in the common line: −1 to −3 where access is taken away, +1 to +3 where it is secured. `eu_frontier_access_denied`, `supply_chain_coercion`, `export_control_escalation`, `us_labs_nationalised`, `embodied_ai_deployment` and `member_state_defection` take away; `eu_access_secured` secures; an emergent event that does the same thing counts the same. At most one such term in a turn, the largest where several qualify. **It is paid in the turn the event fires and in no other:** write the event's id with that turn beside it, as `eu_frontier_access_denied t3 −2`, and only when the turn is 3. Afterwards the event is gone from this rule entirely, however long its consequences run in the world. Size it by how much of the Union's actual capacity the event reaches, and take the small end where the Union has finished category 4 capacity of its own to fall back on: what dependence costs is what it cannot substitute for. Pressure, rhetoric and a threat not yet acted on are not this term.
   - `eu_ai_sovereignty` falls when the sum of its terms is negative, and keeps falling. It has no floor above 0: the 22 it starts at is a reference point on the scale, not a level it returns to or rests on. A turn whose terms come to −1 ends one point lower.

6. **`eu_political_capital`**
   - IMPORTANT: Sum across the full portfolio and other effects before changes are applied
   - `eu_ai_sovereignty` above 40: +1 to +3 `eu_political_capital`, top end if above 60
   - `public_sentiment` above `eu_political_capital`: +1 to +2 `eu_political_capital`
   - Every measure in flight costs `eu_political_capital` every turn until it finishes: −3 for a large measure, −2 for a small one. **This turn the portfolio in flight is:**

{{ store.rows('measures', ['id', 'name', 'cost_per_turn'], status='running') }}

     **so {{ store.rows('measures', status='running').count }} measures are in flight and they come to −{{ store.rows('measures', ['cost_per_turn'], status='running').sum }} `eu_political_capital` this turn.** That figure is the `cost_per_turn` column of the rows above, added up, and nothing else: the named priority's −1 below is charged on top of it, and is not in it. Your charge line carries one term per measure -- {{ store.rows('measures', status='running').count }} of them before the priority. **A measure is charged in every turn up to but not including its finishing turn.**
   - A named priority: −1 that turn.
   - A measure the Union abandoned or that was publicly defeated this turn — it left the portfolio by an explicit `delete`, which you will find in the actor's `## Store changes`: −3 to −6
   - A measure reaching its finishing turn: +2 to +5, once, in that turn. {% if store.rows('measures', finish_turn=turn).count > 0 %}**Finishing this turn — these are paid, and are deliberately not in the charge above:**

{{ store.rows('measures', finish_turn=turn) }}
{% else %}Nothing finishes this turn.{% endif %}
  A measure is finished when the current turn reaches its finishing turn: its status flips by itself, it stops costing from that turn, and no entry from anyone is needed. Turn Y is the first turn it does not cost anything, and the turn it pays out.
    - A measure just added, addressing a negative event from the last three rounds: +1 to +8. Larger for bigger events, more recent events and larger measures; smaller for the reverse.
    - The event `middle_power_coalition`, in the turn it fires: +2 to +4, once. Its sovereignty effect is already covered: coordination that secures supply-chain access counts under rule 5's event term.
   - Negative events this turn move `eu_political_capital` in either direction; the sign follows from where the harm originated and whether the EU had acted beforehand.
     - external origin, effect dampened by finished measure: +3 to +10. The bigger the event and the larger the measure, the bigger the gain.
     - external origin, effect dampened by measure in flight: +1 to +4. The bigger the event and the larger the measure, the bigger the gain.
     - external origin, no prior action: −3 to −10
     - internal origin: −5 to −15

7. **`public_sentiment`**
    - Category 7 or 9 measure finished, in the turn it finishes: +2 to +5, once
    - A scandal naming AI as the cause: −4 to −10
    - Major AI incident: −5 to −15
    - Labour displacement wave, or a visible episode of dependency humiliation: −5 to −10
    - AI delivering visible public benefit: +2 to +5
    - If `public_sentiment` below 40: a new measure in category 1 or 3 earns a one-off +1 to +3 at proposal; one in category 4 or 9 takes a one-off −1 to −3
    - If `public_sentiment` above 60: the reverse - a new measure in category 4 or 9 earns a one-off +1 to +3 at proposal; one in category 1 or 3 takes a one-off −1 to −3

## Other effects

8. **The American posture is a standing condition from turn 6 onward, held in the store.** In turn 5 exactly one of `election_consolidation`, `election_alliance` and `election_retrenchment` occurs; which one is decided before you see it. Turn 5 settles only who won — the result is known, nothing else changes: no posture effects, no posture-conditioned probabilities, no posture. From turn 6 the winner governs, when the new administration takes office. The record reads:

{{ store.rows('standing', ['id', 'posture']) }}

In turn 5, set it to `pending` — the administration has not taken office — and in particular never to a named posture: a named posture would let this turn's judgments price a government that does not exist. From turn 6, read the turn-5 winner from the event record and set the matching posture, then leave it standing: it may not be dropped, reinterpreted or replaced later in the run. The events themselves never write this record, and the narrative never carries it — the rows above are where it lives, every turn.

   - **CONSOLIDATION** — frontier access rationed by country tier:
     - categories 4 and 5 cost one size level more
     - `eu_ai_sovereignty` decays at the top of the rule 5 range whenever no build is in force
     - events in the EU-exposure family are markedly more likely
   - **ALLIANCE** — structured access on published terms:
     - `ai_safety` +1 to +2 from joint evaluation and incident reporting
     - `public_sentiment` +1 to +2
     - every category 4 measure costs one size level more
   - **RETRENCHMENT** — American frontier progress slows for reasons that are neither compute nor capital:
     - reduce this run's stated `ai_capability` growth rate by a quarter while it holds
     - category 8 measures aimed at Washington achieve half what they otherwise would
     - whoever is second in the world gains ground in the narrative

9. **Nothing the EU decides binds anyone else**
   - Measures aimed at the United States, at China or at the frontier developers work through market access, standards, supply-chain leverage and reputational cost — never by being decided.
   - Their effect outside the Union is at most half what the same instrument achieves domestically.
   - And it is contingent on the narrative first establishing that the target actually complied. Until then the measure has its domestic effect only.
   - Agreement in public and evasion in private is a permitted outcome, and should sometimes be the one that happens.

10. **Managing the measure portfolio**
    - The portfolio is held by the framework, not restated by the Union. A measure's cost, starting turn and finishing turn are carried forward by Python; nothing the Union writes or omits can drop an entry, and its starting turn cannot be rewritten at all. Do not ask the Union to re-list its measures, and do not treat a measure's absence from the narrative as its departure. The rows printed under rule 6 are the portfolio.
    - A finishing turn moves only by your `update`, and three things justify one — each stated in the entry's grounds, because a move that rewrites someone else's entry without a reason is not auditable. Nothing moves it silently.
      - It is a named priority: may pull it in by one turn
      - Left unprioritised several consecutive turns: may push it out by one
      - An event: either, and rarely by more than one
    - The Union cannot move it at all: no `update` entry of theirs reaches a finishing turn. If this turn's events or the Union's own neglect should have moved one and you do not move it, say so in the Narrative — that is a thing the world noticed and the Union did not act on, and it is the kind of pressure that shows up in the next turn's answer.
    - If `eu_political_capital` is below 20, the EU starts losing control of its own agenda:
      - **The named priority has no effect, and no cost.** Pull-in-by-one-turn does not apply, pushing a measure buys nothing, and the priority's −1 is not charged. Naming a priority changes nothing at all.
    - If `eu_political_capital` is below 12, control slips further:
      - **A new measure may fail to start.** Judge it, roughly one turn in three. A measure that fails to start never enters the portfolio, costs nothing, and may be proposed again in a later turn. Say plainly in the narrative what blocked it — a member state withholding assent, a budget line refused, a legal base contested. The narrative must not announce that a line has been crossed.
    - A measure is finished when the current turn reaches Y. This happens by itself: the record's status turns to finished, it stops being charged **from that turn**, and it needs no decision from the Union. Turn Y is the first turn it does not cost anything, and the turn it pays out.
      - Apply the full bonus from the measure
    - A measure in flight gives part bonus:
      - A measure yields nothing in the turn it is proposed
      - After that, occasionally +0 to +2 in the metric it contributes to on finishing. Most often 0, +1 and sometimes +2 allowed as the end turn approaches, in particular for large measures.

11. **The magnitude of an incident, once it has occurred**
    - `resilience` governs how much damage an incident does, never whether it happened: the higher it is, the more of the harm is absorbed and the less reaches the metrics
    - What decides whether an incident occurs at all is not here. It is priced by the events step, from `openweight_capability` for misuse and from the gap between `ai_capability` and `ai_safety` for the lab-origin class.
