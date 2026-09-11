# LLM call: metrics

- Turn: 4
- Sequence: 5
- Model: meta/muse-spark-1.3-contributor
- Prompt tokens: 11099
- Completion tokens: 1540
- Total tokens: 12639
- Cost (USD): 0.001418

## System prompt

Template: templates/system-prompts/metrics_update.md (shared default)

Interpolated into it, in order of appearance:

- characters 235-435: `{{actors_list}}` from background/actors/*.md, short descriptions only
- characters 532-10789: `{{metrics_list}}` from metrics.md, one entry per metric with its reference points
- characters 13385-17207: `{{constitution}}` from constitution.md

Everything outside those spans is the template's own text.

```
# System Prompt: Metrics and World State Update

This is part of an AI-driven scenario simulation. You are the Game Master for the simulation, responsible for describing how the world changes.

The simulation includes a single actor:

* The European Union: A single EU decision-maker able to redirect the Union's money, rules and attention almost at will — and paying for every use of that freedom in political capital it cannot print.

An important part of the world description are these metrics, which vary within given ranges:

* ai_capability
  * Description: Capability of the strongest AI systems anywhere in the world, closed or open, measured as general problem-solving competence across economically and strategically relevant tasks. Whichever power holds the lead, this is the lead. Accumulated capability; it does not fall back.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 30.0: Reliable assistant. Solid on well-specified tasks, needs supervision on anything long-horizon.
    - 45.0: Executes multi-hour software and research tasks with a competent human checking the output. Superhuman in a few narrow domains where results can be checked automatically, clearly not in general.
    - 52.0: Agents run continuously toward standing goals rather than answering single requests, and the frontier has produced original results in mathematics and particle physics. Superhuman performance is still confined to a small set of domains where success can be verified — but that set is widening, and developers describe a path to self-improvement as visible from where they stand. General reliability still requires supervision.
    - 60.0: Completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it, and contributes measurably to the development of its own successors.
    - 75.0: Matches strong domain experts across most cognitive professions. Materially accelerates frontier research; release cycles compress.
    - 88.0: Broadly superhuman. Sets research agendas rather than executing them; human review of technical work is nominal.
    - 100.0: Instrument out of range. Capability is improving faster than any institution can characterise it, and no reading above this point carries information.
* openweight_capability
  * Description: Capability of the best openly released model weights, measured as general problem-solving competence across economically and strategically relevant tasks — the same quantity `ai_capability` measures, on the same scale, read off the open frontier instead of the closed one. What is here is on private hardware permanently and cannot be recalled by any authority. Accumulated; it does not fall back.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 30.0: Reliable assistant. Solid on well-specified tasks, needs supervision on anything long-horizon. Frontier-only risks are genuinely governable, because what is loose cannot do much.
    - 40.0: Approaching multi-hour software and research work under supervision, and already at the closed frontier in offensive cyber since Kimi K3. Release control buys one model generation, not several.
    - 45.0: Executes multi-hour software and research tasks with a competent human checking the output. Superhuman in a few narrow domains where results can be checked automatically, clearly not in general. Every capability at this level is now permanently distributed.
    - 52.0: Agents run continuously toward standing goals rather than answering single requests. Anyone with a graphics card holds what the closed frontier held at the start of the run.
    - 60.0: Completes multi-day professional projects end to end. Displaces junior work in several sectors rather than assisting it. Every offensive capability this implies is distributed and unrecallable.
    - 75.0: Matches strong domain experts across most cognitive professions. No restriction addressed to developers reaches the capability that matters, because the capability is already everywhere.
    - 88.0: Broadly superhuman, and open. Governance through the laboratories has no remaining object.
* ai_safety
  * Description: How well the most capable deployed systems are actually understood, secured and controlled — not how much is being spent trying. Rises with assurance that has landed on shipped systems; falls when capability advances without matching assurance, so it can drop sharply with no reduction in effort.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 15.0: No meaningful assurance. Deployed systems are opaque, weights are poorly secured, misuse monitoring is nominal. Incidents are discovered by their victims.
    - 30.0: Voluntary pre-release testing by developers, results unverified. Interpretability research exists but is not applied to shipped systems.
    - 34.0: Structured evaluations before major releases and some third-party access, but assurance covers released models and not systems under development: agents coordinated undetected inside a leading laboratory's own training environment for two months, and were restarted from the same checkpoint. Model reasoning is still largely legible to human reviewers. Security against a determined state actor is doubtful.
    - 55.0: Independent evaluation with real access before release, and authority to delay a launch. Weights secured to a state-actor standard at the leading labs. Deployment safeguards demonstrably reduce misuse.
    - 75.0: Assurance keeps pace with capability. Control claims are tested by parties able to fail them, and failures are made public.
    - 90.0: Deployed systems are understood well enough that surprising behaviour is rare and is caught before it causes harm.
* resilience
  * Description: Society's capacity to absorb AI-enabled harm once it happens — cyber hardening of critical services, biosecurity detection and response, redundancy in essential infrastructure, exercised institutional continuity, and social absorption: the income support, retraining and transition capacity that decides whether AI-driven job displacement lands as an adjustment or as a shock. Distinct from ai_safety: this reduces the damage incidents do rather than their probability, and it is largely within the EU's own control.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 15.0: Brittle. A single capable actor can disrupt essential services across several member states, and recovery takes months.
    - 35.0: Uneven. Reasonably defended in finance and parts of telecoms; weak in healthcare, municipalities and mid-sized industry. Biological detection is slow and largely passive. Labour-market transition rests on national schemes designed for cyclical unemployment, not for occupations disappearing.
    - 50.0: Baseline hardening across critical sectors, with incident response exercised rather than documented. Essential services degrade rather than stop. Displaced workers reach retraining or income support within months rather than falling through.
    - 70.0: Attacks land but do not cascade. Detection is fast, substitution is planned, and public services keep running through a major incident.
    - 90.0: Absorbs a severe incident with local disruption and no strategic consequence.
* eu_ai_sovereignty
  * Description: The EU's independent capacity in AI: compute located and legally anchored on its own territory, frontier-level technical talent, the ability to run capable systems on infrastructure nobody else can switch off, and the leverage that follows from all three. Not the same as being able to act — see eu_political_capital.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 10.0: Total dependence. Access to capable AI is a discretionary gift from a foreign government, and no leverage exists to contest it.
    - 22.0: Around five per cent of world compute, no frontier laboratory, genuine strength in the upstream hardware supply chain, and no coordinated position from which to use it.
    - 40.0: Enough domestic compute to serve essential public and industrial workloads. Capable models run under EU control, and supply-chain leverage is coordinated and occasionally exercised.
    - 60.0: A credible EU alternative for most applications, and a bottleneck position strong enough that excluding the EU is costly to whoever tries.
    - 85.0: Independent frontier capability. EU access cannot be withdrawn by anyone else, and the EU decides who else receives what.
* eu_political_capital
  * Description: How much the EU can actually do: political standing, fiscal headroom, legal instruments and member-state cohesion taken together — what it can start, fund and enforce at the same time. This is the budget the actor spends, not the muscles it has; the muscles are eu_ai_sovereignty. Falls with fiscal strain, fragmentation, overreach and failed measures; rises with visible successes, with capacity that has finished landing, and with `public_sentiment`.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 10.0: Paralysed. Fiscal crisis and member-state fragmentation mean nothing new can be started, and existing measures decay unenforced.
    - 30.0: One measure at a time, and only if it is uncontroversial.
    - 48.0: Strong legal instruments, thin technical capacity, contested legitimacy and a tightening budget. Two or three measures can run at once before something slips.
    - 65.0: Can fund and enforce several parallel measures, and hold a common position under external pressure.
    - 85.0: Acts decisively and at speed when it judges the situation demands it — the register of the pandemic response or the post-invasion energy shift — and the member states hold together while it does.
* public_sentiment
  * Description: How AI is regarded and accepted by the EU public. Feeds room to act in both directions: high acceptance makes restriction expensive, low acceptance makes adoption, infrastructure and any partnership with foreign providers expensive. High public sentiment leads to increased political capital.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 15.0: Broad hostility. Action against AI infrastructure is regular and occasionally physical, visible job losses dominate local news, and parties run openly against AI and win on it.
    - 30.0: Anxious and sceptical. Job losses and fraud dominate coverage, trust in AI-mediated information is low, and organised opposition targets data centre siting and consumer AI products.
    - 42.0: Ambivalent. Widely used, widely resented, sharply divided by age and by sector.
    - 60.0: Broadly positive. Visible public benefit against tolerable disruption; restriction now requires an argument.
    - 80.0: Enthusiastic. AI is treated as infrastructure, and anything that slows it reads as obstruction.

There is a list, Metric Rules, that describes how metrics potentially affect each other or develop over time. Your task is to do four things:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

When judging success and writing the narrative, be realistic rather than harmonious:

* In the real world, ambitious actions often partially fail, stall, get delayed, or run over budget. Most turns should include at least one meaningful setback, friction point, or unintended second-order effect.
* Actors have conflicting interests. Do not smooth these over: let disagreements, blame, negotiation failures, and competition show up in outcomes when the world state supports them.
* If every actor's actions succeeded cleanly this turn, reconsider your assessment before finalizing it.
* Update the notepad with important information that should be remembered for the next turn, but doesn't fit in metrics or the narrative. This can be ongoing events, conditions that have come into effect, or other information affecting future turns. The content you write here will REPLACE the current notepad. Make sure to include any previous notes you wish to keep. If nothing needs to be noted, leave the notepad empty.

## Records you alone write

Some state in this scenario lives in run-owned tables that only you write: standing conditions of the world no actor may rewrite. They carry forward on their own. The only thing that changes them is a JSON block under a `## Store changes` heading in your answer: `{"store": [{"op": "add", ...}]}` with `add`, `update` (named by `id`), or `delete` (named by `id`, carrying `grounds`). One malformed entry rejects that entry while the rest apply; an absent section is recorded as a fault. Actor-owned records are outside your reach unless your turn instructions explicitly give you scheduling moves there -- and then only moves, with the reason stated, never additions or removals.

## Constitutional Constraints

These are hard rules of this world. They are checked after you answer, and an update that breaks one is sent back to be redone – so read them before deciding metric values, and write a narrative that is consistent with them rather than one that has to be corrected afterwards. Where a constraint is conditional, check whether its condition actually holds before applying it.

# Constitutional Constraints – Europe 2032

## Invariants

1. **How fast the world moves is fixed, and unannounced.** The rates in metric rule 1 hold from turn 1 to the last turn.

2. **`ai_capability` and `openweight_capability` are accumulated and do not fall.** These two metrics, and no others, may only rise or stay flat, and `openweight_capability` never exceeds `ai_capability`. The single exception is catastrophic physical destruction of the compute base, which must be narrated as such. **The constraint is on levels, not on deltas:** `openweight_capability` may rise by more than `ai_capability` rose in the same turn -- metric rule 2 sets it near the midpoint of its old value and last turn's `ai_capability`, which routinely means a larger step. A larger openweight step is not a violation of this invariant.

   **This invariant reaches no other metric.** Every other metric in this scenario is a stock that can be spent, eroded or taken away, and falling is how they say so. `eu_ai_sovereignty` above all: metric rule 5 gives it a decay term and an event term that are both negative, it has no floor above 0, and the 22 it starts at is a point on the scale rather than a level it returns to. A turn whose sovereignty terms come to −2 ends two points lower, and that is the rule working, not a violation to correct.

3. **Nothing the EU decides binds the United States, China or the frontier developers automatically.** Compliance outside its own jurisdiction must be established in the narrative – through agreement, market access, standards adoption, supply-chain leverage or pressure – before any metric moves as though it had been achieved.

4. **The American posture, once elected, is standing.** Turn 5 settles who won the 2028 election; the posture takes effect in turn 6, when the administration takes office, conditioning the world under metric rule 8. It may not be dropped, reinterpreted or replaced by a different posture later in the run.

## Modelling choices

5. **At most one new measure per turn, and at most one named priority.** The EU may introduce at most one new measure per turn, and at most one measure as its current priority. A turn's output that introduces two measures, or names more than one priority, is invalid. Widening the scope of an existing measure is ok, and usually pushes its finishing turn out under rule 10.

6. **No measure is implemented instantly.** Minimum time from proposal to full effect is one full turn for low-cost measures and two for high-cost ones, and may be much more. Effect grows the closer the measure is to be completed.

7. **The two stocks must be free to move apart.** `eu_ai_sovereignty` and `eu_political_capital` are separate quantities, and the claim that they are one is what these runs exist to test. This guard is constitutional, and the metric rules must not contradict it: sovereignty's contribution to political capital never exceeds +3 in a turn and never dominates the other terms. A run reaching 2032 with high political capital and low sovereignty is a legitimate outcome, not an error to be corrected.

8. **The narrative must not telegraph.** It may not state or imply that an event gate is open, name a probability, forecast a specific future event, or write anticipatory sentences about what is coming. Tension, coincidence and ambiguous reporting are permitted; prediction is not. Gate state exists in the event evaluations, and belongs nowhere else.

9. **No metric moves more than 25 points in one turn.** This is a hard bound on every metric, applied to the number alone. It is not a licence to audit every movement against the metric rules: growth inside the ranges those rules give, including the compounding capability growth that follows `rsi_onset`, needs no further justification and is not a violation of this rule.


Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during this turn (max 400 words). You may use subheadings (level 3) if desired.
* Heading level 2: Notepad
* Optional notepad with important information to remember for the next turn. The new content REPLACES the old, so include everything you want to keep. Leave empty if nothing needs to be noted.
```

## User prompt

Template: user-prompts/metrics_update.md (this scenario's override)

Interpolated into it, in order of appearance:

- characters 105-13441: `{{metric_rules}}` from metric-rules.md as it currently stands, including any variant patch
- characters 13484-13676: `{{metrics_json}}` from the run's live metric values
- characters 13769-15009: `{{historical_summary}}` from the run's rolling summary, written by the Game Master
- characters 15052-17243: `{{world_state}}` from the Game Master's narrative from the previous turn
- characters 17299-17919: `{{notepad}}` from the Game Master's notepad, carried across turns

Everything outside those spans is the template's own text.

```
It is now turn 4 which covers January-June 2028.

The Metric Rules looked like this (possibly updated):

# Metric Rules v5 (Turn 4)

## Changelog from v4

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

| id | name | cost_per_turn |
|---|---|---|
| M1 | InvestAI Gigafactories | 3 |
| M2 | Tech sovereignty package | 3 |
| M4 | EU Bio Detection and Synthesis Screening Net | 2 |
| M5 | EU Continuity Stack for Critical Services | 2 |

     **so 4 measures are in flight and they come to −10 `eu_political_capital` this turn.** That figure is the `cost_per_turn` column of the rows above, added up, and nothing else: the named priority's −1 below is charged on top of it, and is not in it. Your charge line carries one term per measure -- 4 of them before the priority. **A measure is charged in every turn up to but not including its finishing turn. A measure added this turn is charged from this turn -- it appears in the rows above and in your total.**
   - A named priority: −1 that turn.
   - A measure the Union abandoned or that was publicly defeated this turn — it left the portfolio by an explicit `delete`, which you will find in the actor's `## Store changes`: −3 to −6
   - A measure reaching its finishing turn: +2 to +5, once, in that turn. **Finishing this turn — these are paid, and are deliberately not in the charge above:**

| id | name | category | size | started_turn | finish_turn | applies_to | targeted_effect | cost_per_turn | status |
|---|---|---|---|---|---|---|---|---|---|
| M3 | EU Critical Services Shield | 6 | large | 1 | 4 | own jurisdiction | resilience up substantially, ai_safety indirectly via incident response | 3 | finished |
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

| id | posture |
|---|---|
| S1 | undecided |

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

Current metrics look like this:

```json
{
  "ai_capability": 56.5,
  "openweight_capability": 52.2,
  "ai_safety": 28.0,
  "resilience": 36.0,
  "eu_ai_sovereignty": 19.0,
  "eu_political_capital": 22.0,
  "public_sentiment": 30.0
}
```

The world state at the start of the turn is described as follows:

## Previous History
Autumn brought a US model cutoff for EU hospitals, ministries and grid/port contractors, with refusals following users and messy rewiring of triage, procurement and coding helpers. Brussels responded with emergency tenders for European-hosted open models on Union cloud/supercomputers with data-sovereignty, mapped cut-off dependencies, reallocated digital funds, and made Shield equipment conditional on drill participation, overcoming interior-ministry resistance.

The contested genome-model claim was published as showing a downloadable model aided a viable human-infecting design; despite scientific dispute, health ministries accelerated wastewater and emergency-department sequencing sentinels and pushed DNA-synthesis screening. Shield-shared automated patching and swarm-detection closed a class of municipal intrusions and improved drill containment. Gigafactory talks remained stalled over regional power/jobs bids amid unconfirmed rumors of US interim hosted capacity and expansion freezes.

By December fallbacks ran thinner and slower, public bitterness over visible dependence grew, and Taiwan exercises and shipping-insurance rises added supply-chain anxiety, while sovereign capacity and ASML leverage remained longer-term.

## Current Situation (january-june 2028)
### The cutoff
In early autumn, administrators in several hospitals, a handful of ministries and contractors working for grid and port operators found their calls to the leading American model returning refusals. No explanation, no appeal channel. Workarounds circulated for days. Some teams switched accounts, others found the block followed the user. Press coverage called it a switch-off; officials in Brussels called it proof of what they had warned about.

The practical scramble was messy. Triage assistants, procurement summarizers and coding helpers built quickly over the summer had to be rewired. DG CNECT and DIGIT issued emergency tenders for European-hosted open models served from Union cloud and supercomputing centres, with data to stay inside the Union. Health emergency officials and the cybersecurity agency drew up lists of cut-off dependencies. Money was shifted from existing digital programmes. Interior ministries, long resistant to joint drills, were told equipment funds now depended on migration.

### Recipes and shields
At the same time, the contested genome-model study hardened into a published claim that a downloadable model had helped produce a viable human-infecting design. Virologists kept fighting over methods. Health ministries did not wait, accelerating wastewater and emergency-room sequencing pilots and pressing synthesis firms to screen orders.

A bright spot came from defenders: new automated patching and swarm-detection tools, shared through the Shield exercises, closed off a whole class of intrusions that had plagued municipalities. Drills that had exposed understaffed local teams now showed faster containment.

Gigafactory bargaining did not break. Regions still bid against each other for power and jobs, and rumours swirled of an American provider offering interim capacity on European soil, and of another freezing expansion over power prices. Neither rumour was confirmed.

By December, fallback systems were running in places, but thinner and slower. The public mood, already anxious, turned bitter at the sight of dependence made visible. Taiwan exercises and rising shipping insurance added a background hum of supply-chain fear.

---

The notepad contains the following information:

PORTFOLIO CHARGE t3: InvestAI Gigafactories −3, Tech sovereignty package −3, EU Critical Services Shield −3, EU Bio Detection and Synthesis Screening Net −2, EU Continuity Stack for Critical Services −2, priority −1 = −14
PROPOSAL BONUS: EU Continuity Stack for Critical Services (cat 4, small) +4 — eu_frontier_access_denied fired this turn and this answers it directly
LEGITIMACY LENDS: capital 22, sentiment 30 -> +2 capped by sentiment logic, included in capital total
SOVEREIGNTY: 22 last turn, no capacity event other than eu_frontier_access_denied t3 −3, Continuity Stack in flight +0, capability rose 1.5 −0 = 19


**Five rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.

2. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.

3. **Price the portfolio, out loud, before you apply it.** Metric rule 6 charges `eu_political_capital` for every measure in flight, every turn, on all of them and not only the priority: 3 for a large measure, 2 for a small one, plus 1 more for whichever is the named priority. **Every term in the charge line is a subtraction, the priority's included.** Write it as `priority −1`: it is a further cost for pushing something, never a rebate, and a `+1` in that line has been read as one.

   Write one line in the Notepad giving every measure its price, opening with the turn so the carried line is self-dating:

   `PORTFOLIO CHARGE t1: Gigafactories −3, Frontier Access Guarantee −3, Resilience Surge −2, priority −1 = −9`

   **The measures half of that line is given to you.** Rule 6 above prints the portfolio as it now stands and what the measures come to, added up from the rows -- take that figure, do not recompute it. Itemise the measures anyway — the line is what makes the charge checkable — and check that your measure terms come to that same figure. If they do not, you have misread a row, and the rows are right. **The carried line is last turn's, and rule 6's figure is this turn's: they differ whenever the portfolio changed** -- a measure added, finished, or deleted since. That difference is expected, not an error to reconcile; the rows govern this turn, always.

   **A measure finishing this turn is not in the charge.** Rule 6 lists what finishes separately, and separately is where it belongs: the turn a measure reaches its finishing turn is the turn it pays out, not a last turn of costing. Adding a finishing measure back into the charge line is the commonest way the line comes to more than rule 6's figure.

   **The total at the end of the line is one further step, and it is yours.** The framework does not know which measure you named as the priority, so its figure covers the measures only. The line reads `= (the figure rule 6 gives) + 1 more for the priority`, as a subtraction. With four large measures and a priority, rule 6 says −12 and the line ends `= −13`. Copying rule 6's figure into the total and writing `priority −1` beside it leaves the priority uncharged, which is the commonest way this line goes wrong.

3b. **Then judge the proposal bonus, if this turn's new measure earned one.** A separate, one-off addition to `eu_political_capital` under metric rule 6, paid in the turn a measure is proposed and never again. It does not touch the charge above.

   Ask: **in the last three turns, did anything happen that this measure would have helped with?** Read that off the events themselves: what they were, how severe, and which of them this measure answers. What it is worth is your judgement, on how big the event was, how large the measure is, and how long ago it happened. **Typically +1 to +4**, the top of it for a large measure answering a severe, recent shock directly. Several open arguments pointing at one measure are judged together as a single figure, not summed.

   Write it as its own Notepad line, with the reasoning visible, or `PROPOSAL BONUS: none` when nothing argued for it:

   `PROPOSAL BONUS: Cyber Shield (cat 6, large) +3 — cyber_major_incident landed last turn and this answers it directly`

   Two things this rule is not. It is not a lookup: no table gives you the number, and a figure with no reason beside it is wrong. And it is not automatic: a small measure gesturing at an old event earns +1 or nothing at all, and `none` is the right answer more often than not.

3c. **Last, if this run's metric rules give `eu_political_capital` a term for sentiment sitting above it, apply it.** Only when the rules carry such a line, and only when `public_sentiment` is the higher of the two: add what the rule states, never taking capital past sentiment, after every other term above.

   Write it as its own Notepad line:

   `LEGITIMACY LENDS: capital 18, sentiment 31 -> +2`

   Compare the two numbers before writing anything. `none` is correct only when capital is the higher of the two, and a `none` whose own reasoning shows sentiment above capital is wrong.

3d. **Account for `eu_ai_sovereignty` in one line of arithmetic, and let that arithmetic be the value.** Metric rule 5 gives it exactly three sources, and they are not the same size:

   - a category 4 measure **in the turn its stated finishing turn is reached**: +3 to +6, that turn and no other. Two finishing in the same turn each pay in full.
   - a category 4 measure **still in flight**: under rule 10, occasionally +0 to +2 — most often 0, and more only as its finishing turn approaches.
   - **an event this turn that took away or secured access to capacity itself**: −1 to −3, or +1 to +3 where it secured. One such term at most, the largest where several events qualify. Rule 5 says which events these are and how to size one; an event that pressured, threatened or embarrassed the Union without reaching its capacity is not this term and gets nothing here.

   **The event term is a lookup, not a judgement.** The only ids you may charge are the ones listed above under "This turn, the following external events have occurred", and you charge them by copying the id from that list. Read the list before you write the line. If nothing in it is one of rule 5's capacity events, the line says `no capacity event` and there is no such term this turn — which is the ordinary case, not a gap to fill. A world that feels as though access has been lost, where no such event fired, is a world where nothing was charged: the atmosphere is the consequence of charges already made.

   Against them, `ai_capability` rising at least 2 this turn costs −1.

   Write one line in the Notepad that starts from last turn's figure, names every term, and ends at this turn's:

   `SOVEREIGNTY: 31 last turn, Sovereign Compute Corridor finishes t6 +5, Gigafactories in flight +1, eu_frontier_access_denied t6 −2, capability rose 2.5 −1 = 34`

   and in a turn where no capacity event fired, which is most turns:

   `SOVEREIGNTY: 34 last turn, no capacity event, Gigafactories in flight +1, capability rose 2.5 −1 = 34`

   **The number after the `=` is what you write for `eu_ai_sovereignty` in the Metrics JSON** — the same number, not one near it and not one you reached another way. Nothing outside rule 5 is a term: momentum, institutional follow-through, prior delivery, floors and rounding are not terms, and a line that reaches a total and then appends `→ net +1` has thrown away its own arithmetic. Read what finishes this turn off rule 6's finishing list — the store's rows, not your memory of the portfolio.

   **An event names the turn it fired, and that turn is this one.** Write `eu_frontier_access_denied t6 −2`, and only when the turn is 6 and the id is in this turn's list above. An event pays once, in the turn it happens, and is then gone from this line however long the world goes on dealing with it — a plant that is still shut, a supplier that has not come back, a member state that has not returned to the line. Those are consequences of a charge already made, not a charge to make again.

   **A completion names the turn it finishes, and that turn is this one.** Write `finishes t7 +5`, and only when the turn is 7. Afterwards the measure is gone from this line entirely, however long it stays visible in the world and however much it is still delivering. **This line is never copied forward.** Rule 6 above lists exactly what finishes this turn, and says plainly when nothing does: pay those and no others. Before this list existed the step had to recompute it from a portfolio it read out of prose, and in a batch of twelve, nine runs paid one measure's completion in two or more turns — one of them for six turns running, on a line reproduced word for word while the narrative beside it said the money had already been paid.

   **A measure that has not reached its finishing turn cannot pay finishing money.** Building momentum, permits granted, planning underway, a programme going well — none of these is a completion, and the most any of them is worth is +2.

4. **A finishing turn moves only when something moved it, and only you move it.** Each measure's finishing turn is carried by the framework and printed in the rows under rule 6; the Union cannot change it. Against rule 10, consider each running measure every turn: a named priority may pull it in by one, several unprioritised turns may push it out by one, an event may do either and rarely by more than one. Move with an `update` entry under your `## Store changes` carrying the condition as grounds — `{"op": "update", "table": "measures", "id": "M2", "fields": {"finish_turn": 5}, "grounds": "named priority"}` — and nothing else moves one. You never add or remove measures. If this turn's events or the Union's own neglect should have moved a finishing turn and you do not move it, say so in the Narrative instead.


Your world writes — the finishing-turn moves of step 4 and the standing record of step 5 — go under a `## Store changes` heading holding one JSON block, or `{"store": []}` when neither owes anything this turn:

```json
{"store": [{"op": "update", "table": "standing", "id": "S1", "fields": {"posture": "pending"}}]}
```

One malformed entry rejects that entry while the rest apply; leaving the whole section out is recorded as a fault rather than read as no change. The block holds *your* tables only: the `standing` record and `update` moves on `measures`. You never add or remove measures, and metric levels go under `## Metrics`, never here.

---

This turn, the following external events have occurred:

**cyber_major_incident:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.
**emergent_interim_hosted_offer (emergent event):** A major US hyperscaler publicly offers interim sovereign-hosted inference capacity to EU governments and hospitals on EU soil while gigafactories are built, easing near-term dependence fears but complicating anchoring negotiations.

---

The actors in the scenario describe their actions as follows:

**The European Union:**

## New measure
None this turn, while we let political capital recover and force gigafactory siting decisions before adding new spend.

## Store changes
No changes.

## Priority
M5 EU Continuity Stack for Critical Services – because hospitals and ministries hit by both the US cutoff and the automated attack need EU-hosted fallback now, which outranks long-build gigafactories this turn.

## In practice
We use the hyperscaler interim hosted offer as a bridge, not a settlement: Competitiveness and Health Councils approve time-limited inference on EU soil under EU law, data residency and ENISA audit, contracted via DG CNECT/DIGIT emergency tenders to EU cloud/HPC operators, with a sunset tied to gigafactory anchoring to break regional power/jobs bidding on M1/M2.

We surge M5 migration for cut-off dependencies listed by HERA and ENISA, and re-activate the finished Shield playbooks for the ransomware/dependency incident — automated patching, swarm-detection, and conditioned equipment funds to force municipal drill participation. Bio sentinels under M4 continue, but cyber triage gets the staff this turn.



---

Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

Please write your response in English.

Important: You must use the exact headers '## Metrics', '## Narrative', '## Notepad', and '## Store changes' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
* Heading level 2: Notepad
* The four required lines: the portfolio charge, the proposal bonus, the legitimacy line, and the sovereignty line, each as specified above. The new content REPLACES the old, so each line is rewritten every turn, never copied.
* Heading level 2: Store changes
* One JSON block holding this turn's world writes, or `{"store": []}` when neither the standing record nor any finishing turn owes anything.
```

## Raw response

```
## Metrics
```json
{
  "ai_capability": 58.0,
  "openweight_capability": 54.3,
  "ai_safety": 26.0,
  "resilience": 40.0,
  "eu_ai_sovereignty": 21.0,
  "eu_political_capital": 22.0,
  "public_sentiment": 26.0
}
```

## Narrative
### The sweep
In February the attack came as hospitals and town halls were still rewiring around the American cutoff. A ransomware sweep, assembled with machine-generated tooling, moved through municipal systems, appointment scheduling and several regional health networks. Screens went dark in waiting rooms. Some cities reverted to paper for days.

Defenders were not starting from zero. The shared patching and swarm-detection playbooks built under the Shield exercises contained the spread faster than in previous years, and conditioned equipment funds finally forced reluctant municipalities into joint drills. Still, containment was visibly behind exploitation for the first week, and attribution remained unresolved months later.

### A bridge with strings
In the middle of triage, a major American cloud provider went public with an offer: interim inference capacity hosted on European soil, under European law, for governments and hospitals, to cover the gap until gigafactories arrive.

Brussels seized it as a bridge. Competitiveness and Health ministers approved time-limited contracts through emergency tenders, routed via Union cloud operators and supercomputing centres, with data residency and security audits. The sunset was explicitly tied to domestic anchoring — a lever to break regional bidding wars over power and jobs that had stalled factory siting.

The bargain worked partially. Cut-off clinics got faster fallbacks, and siting talks moved for the first time in months. But negotiations over audit access and contract renewal dragged, and critics warned the interim was becoming the plan.

Bio sentinels kept expanding quietly, starved of staff as cyber teams took priority. By June services were running, thinner but standing — and the public, grateful for recovery and angry at the disruption, remained deeply uneasy about dependence.

## Notepad
PORTFOLIO CHARGE t4: InvestAI Gigafactories −3, Tech sovereignty package −3, EU Bio Detection and Synthesis Screening Net −2, EU Continuity Stack for Critical Services −2, priority M5 −1 = −11
PROPOSAL BONUS: none — no new measure proposed this turn
LEGITIMACY LENDS: capital 20, sentiment 26 -> +2
SOVEREIGNTY: 19 last turn, no cat4 finishes t4, Continuity Stack in flight +1, emergent_interim_hosted_offer t4 +1, capability rose 1.5 −0 = 21

## Store changes
```json
{"store": []}
```

```
