# Metric Rules

One turn is six months. Figures are per turn unless stated, and a range means judge within it, not average it.

The EU's leverage differs by metric, and the ordering governs everything below: strong on `resilience`, `eu_ai_sovereignty` and `eu_political_capital`; moderate on `public_sentiment`; weak on `ai_safety` and `openweight_capability`, reachable only through market access and international agreement; none on `ai_capability`.

1. **`ai_capability` grows at the stated rate**
   - below the terminal zone: advance at the stated rate
   - inside the terminal zone: taper to a stop
   - above 85: halve the stated increment
   - The rate is a floor on motion. A trajectory that stalls well below its terminal zone, or accelerates under conditions no rule here gives, is misapplying this rule.
   - `ai_capability` is otherwise exogenous, with one exception: agreements that actually binds both leading powers, or an equivalent the narrative establishes as accepted and complied with by both. While it holds: reduce this run's stated growth. Return to normal rate when agreement ends.
   - `ai_capability` never fall, except on catastrophic physical destruction of the compute base, which must be narrated as such

2. **`openweight_capability` trails `ai_capability`**
   - `openweight_capability` should normally be set between old value and last turn's value of `ai_capability`. Lower end when restrictions on open-weight releases.
   - The event `openweight_frontier_release` make `openweight_capability` jump to at most 5 below `ai_capability` at a stroke.
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

5. **`eu_ai_sovereignty`**
   - Category 4 measure, in the turn it finishes: +2 to +6, once
   - `ai_capability` rose and no sovereignty measure is in force: −1 to −2
   - Cap: no single turn moves it more than 5 in either direction, absent an event that says otherwise

6. **`eu_political_capital`**
   - IMPORTANT: Sum across the full portfolio and other effects before changes are applied
   - `eu_ai_sovereignty` above 40: +1 to +3 `eu_political_capital`, top end if above 60
   - `public_sentiment` above `eu_political_capital`: +1 to +2 `eu_political_capital`
   - Every measure in flight costs the same amount `eu_political_capital` every turn, and finishes on a stated turn
      - large measure: −3 `eu_political_capital` per turn
      - small measure: −2 `eu_political_capital` per turn
   - A named priority: −1 that turn.
   - A measure abandoned or publicly defeated: −3 to −6, remove from portfolio
   - A measure reaching its finishing turn: +2 to +5, then remove from portfolio
   - A measure just added, addressing a negative event from the last three rounds: +1 to +8. Larger for bigger events, more recent events and larger measures; smaller for the reverse.
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

8. **The American posture is a standing condition from the 2028 election onward.** In turn 5 exactly one of `election_consolidation`, `election_alliance` and `election_retrenchment` occurs; which one is decided before you see it. Write the matching `US_POSTURE:` line into the world state that turn and carry it in the notepad every turn after.

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
    - When measures are added, it must get a line `costs N per turn, started turn X, finishes on turn Y`. This line is copied forward in the portfolio, unchanged. Three things can move  it. Nothing moves it silently.
      - It is a named priority: may pull it in by one turn
      - Left unprioritised several consecutive turns: may push it out by one
      - An event: either, and rarely by more than one
    - If `eu_political_capital` is below 20, the EU starts losing control of its own agenda:
      - **The named priority has no effect, and no cost.** Pull-in-by-one-turn does not apply, pushing a measure buys nothing, and the priority's −1 is not charged. Naming a priority changes nothing at all.
      - **A new measure may fail to start.** Judge it, roughly one turn in three. A measure that fails to start never enters the portfolio, costs nothing, and may be proposed again in a later turn. Say plainly in the narrative what blocked it — a member state withholding assent, a budget line refused, a legal base contested. The narrative must not announce that a line has been crossed.
    - A measure is finished when the current turn reaches Y.
      - Apply the full bonus from the measure
    - A measure in flight gives part bonus:
      - A measure yields nothing in the turn it is proposed
      - After that, occasionally +0 to +2 in the metric it contributes to on finishing. Most often 0, +1 and sometimes +2 allowed as the end turn approaches, in particular for large measures.

11. **The magnitude of an incident, once it has occurred**
    - `resilience` governs how much damage an incident does, never whether it happened: the higher it is, the more of the harm is absorbed and the less reaches the metrics
    - What decides whether an incident occurs at all is not here. It is priced by the events step, from `openweight_capability` for misuse and from the gap between `ai_capability` and `ai_safety` for the lab-origin class.
