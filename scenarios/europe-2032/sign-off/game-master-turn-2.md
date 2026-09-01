# Sign-off: game-master-turn-2

The Game Master step that writes the world state. It decides what the actor's actions achieved and what the metrics become, so the metric rules must be visible here in full and unambiguous.

Source: `runs/run-20260901-211110/turn-02/llm-io/05-metrics.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

# ═══ REVIEWER CHECKLIST ═══

- Every section of the actor and background files you expect is present below, not merely present in the file on disk
- Nothing contradicts anything else: the scenario's own prompt overrides say the same thing as the templates they replace
- No leakage: nothing here tells the actor something the scenario means it to infer
- Numbers, thresholds and category names match the scenario definition exactly

# ═══ WHERE EACH BLOCK CAME FROM ═══

Each block below carries a `FROM` comment naming its origin. These are not inferred from the finished text: the prompt builder recorded them as it interpolated each value, so a one-line heading inside an interpolated block is attributed as confidently as a page of it. A block marked with a template path is the template's own words; a block marked `{{variable}}` is a value put into it, and the note says which file or run-time structure that value came from.

# ═══ SYSTEM PROMPT ═══

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

# System Prompt: Metrics and World State Update

This is part of an AI-driven scenario simulation. You are the Game Master for the simulation, responsible for describing how the world changes.

The simulation includes a single actor:

<!-- FROM {{actors_list}} = background/actors/*.md, short descriptions only -->

* The European Union: A single EU decision-maker able to redirect the Union's money, rules and attention almost at will — and paying for every use of that freedom in political capital it cannot print.

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

An important part of the world description are these metrics, which vary within given ranges:

<!-- FROM {{metrics_list}} = metrics.md, one entry per metric with its reference points -->

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

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

There is a list, Metric Rules, that describes how metrics potentially affect each other or develop over time. Your task is to do four things:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

When judging success and writing the narrative, be realistic rather than harmonious:

* In the real world, ambitious actions often partially fail, stall, get delayed, or run over budget. Most turns should include at least one meaningful setback, friction point, or unintended second-order effect.
* Actors have conflicting interests. Do not smooth these over: let disagreements, blame, negotiation failures, and competition show up in outcomes when the world state supports them.
* If every actor's actions succeeded cleanly this turn, reconsider your assessment before finalizing it.
* Update the notepad with important information that should be remembered for the next turn, but doesn't fit in metrics or the narrative. This can be ongoing events, conditions that have come into effect, or other information affecting future turns. The content you write here will REPLACE the current notepad. Make sure to include any previous notes you wish to keep. If nothing needs to be noted, leave the notepad empty.

## Constitutional Constraints

These are hard rules of this world. They are checked after you answer, and an update that breaks one is sent back to be redone – so read them before deciding metric values, and write a narrative that is consistent with them rather than one that has to be corrected afterwards. Where a constraint is conditional, check whether its condition actually holds before applying it.

<!-- FROM {{constitution}} = constitution.md -->

# Constitutional Constraints – Europe 2032

## Invariants

1. **How fast the world moves is fixed, and unannounced.** The rates in metric rule 1 hold from turn 1 to the last turn.

2. **Capability is accumulated and does not fall.** `ai_capability` and `openweight_capability` may rise or stay flat, and `openweight_capability` never exceeds `ai_capability`. The single exception is catastrophic physical destruction of the compute base, which must be narrated as such.

3. **Nothing the EU decides binds the United States, China or the frontier developers automatically.** Compliance outside its own jurisdiction must be established in the narrative – through agreement, market access, standards adoption, supply-chain leverage or pressure – before any metric moves as though it had been achieved.

4. **The American posture, once elected, is standing.** From the turn `us_election_2028` fires, the `US_POSTURE:` line is carried in the notepad every subsequent turn and conditions the world under metric rule 8. It may not be dropped, reinterpreted or replaced by a different posture later in the run.

## Modelling choices

5. **At most one new measure per turn, and at most one named priority.** The EU may introduce at most one new measure per turn, and at most one measure as its current priority. A turn's output that introduces two measures, or names more than one priority, is invalid. Widening the scope of an existing measure is ok, and usually moves the finishing date further out.

6. **No measure is implemented instantly.** Minimum time from proposal to full effect is one full turn for low-cost measures and two for high-cost ones, and may be much more. Effect grows the closer the measure is to be completed.

7. **The two stocks must be free to move apart.** `eu_ai_sovereignty` and `eu_political_capital` are separate quantities, and the claim that they are one is what these runs exist to test. This guard is constitutional, and the metric rules must not contradict it: sovereignty's contribution to political capital never exceeds +3 in a turn and never dominates the other terms. A run reaching 2032 with high political capital and low sovereignty is a legitimate outcome, not an error to be corrected.

8. **The narrative must not telegraph.** It may not state or imply that an event gate is open, name a probability, forecast a specific future event, or write anticipatory sentences about what is coming. Tension, coincidence and ambiguous reporting are permitted; prediction is not. Gate state exists in the event evaluations, and belongs nowhere else.

9. **No metric moves more than 25 points in one turn.** This is a hard bound on every metric, applied to the number alone. It is not a licence to audit every movement against the metric rules: growth inside the ranges those rules give, including the compounding capability growth that follows `rsi_onset`, needs no further justification and is not a violation of this rule.

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during this turn (max 400 words). You may use subheadings (level 3) if desired.
* Heading level 2: Notepad
* Optional notepad with important information to remember for the next turn. The new content REPLACES the old, so include everything you want to keep. Leave empty if nothing needs to be noted.

# ═══ USER PROMPT ═══

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->

It is now turn 2 which covers January-June 2027.

The Metric Rules looked like this (possibly updated):

<!-- FROM {{metric_rules}} = metric-rules.md as it currently stands, including any variant patch -->

# Metric Rules v3 (Turn 2)

## Changelog from v2

- No material rule changes.
  - **Motivation:** Rule evolution is frozen through turn 14, so the prior rule set remains in force.
  - **Expected impact:** Metric dynamics continue under the prior rule set.

## Rules

# Metric Rules

One turn is six months. Figures are per turn unless stated, and a range means judge within it, not average it.

The EU's leverage differs by metric, and the ordering governs everything below: strong on `resilience`, `eu_ai_sovereignty` and `eu_political_capital`; moderate on `public_sentiment`; weak on `ai_safety` and `openweight_capability`, reachable only through market access and international agreement; none on `ai_capability`.

1. **This run's own rate sets the growth of `ai_capability`.** In this run: +1.5 to +2.5 per turn while capability is below 60, +0.5 to +1.5 above it, easing into the **68–74** terminal zone. Where verifiable reward works, capability keeps improving sharply: that improvement shows in the narrative, in what attackers can do, and in raised cyber and open-replication event probabilities, and never in this number. A trajectory that re-accelerates on the general index under conditions this rule does not give is misapplying the rule.

2. **`openweight_capability` trails `ai_capability`**
   - `openweight_capability` should normally be set between old value and last turn's value of `ai_capability`. Lower end when restrictions on open-weight releases.
   - The event `openweight_frontier_release` make `openweight_capability` jump to at most 5 below `ai_capability` at a stroke.
   - `openweight_capability` never fall
   - `openweight_capability` never exceeds `ai_capability`

3. **`ai_safety`**
   - `ai_capability` rose and no measure landed on shipped systems: −1 to −3
   - The events `opaque_reasoning`, `capability_jump` or `rsi_onset`: −5 to −12
   - The event `safety_breakthrough`: +5 to +10
   - Finished measure in category 1, 2 or 5 that affects the jurisdiction where frontier models are built: +2 to +4. If only affecting inside the EU: 0 to +1

4. **`resilience`**
   - Finished category 6 measure covering a named class of harm: +3 to +6
   - `ai_capability` rose and no category 6 measure is in force: −1 to −2
   - Finished category 9 measure broadening adoption: −1 to −3

5. **`eu_ai_sovereignty`**
   - Finished category 4 measure: +2 to +6
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
    - Category 7 or 9 measure finished: +2 to +5
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
      - After that, a share of the per-turn figure its category rule gives it, judged from how far it has come between X and Y — at most half that figure until it finishes. Judge the share; do not compute it to a decimal.

11. **The magnitude of an incident, once it has occurred**
    - `resilience` governs how much damage an incident does, never whether it happened: the higher it is, the more of the harm is absorbed and the less reaches the metrics
    - What decides whether an incident occurs at all is not here. It is priced by the events step, from `openweight_capability` for misuse and from the gap between `ai_capability` and `ai_safety` for the lab-origin class.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->

The world state at the start of the turn is described as follows:

## Previous History

<!-- FROM {{historical_summary}} = the run's rolling summary, written by the Game Master -->

AI capabilities advanced significantly in late 2026, with open-weight models narrowing the gap with frontier systems and enabling broader access to powerful autonomous agents, including in offensive cyber domains. Breakthroughs in science and engineering emerged from AI-driven research, while new verification tools accelerated deployment in critical sectors. A major cyber intrusion exposed deep AI-facilitated vulnerabilities in global infrastructure, and concerns grew over AI-assisted biothreat design. In response, the EU proposed the European AI Evaluation Authority (EAIEA) to assert control over high-capability model evaluation, offering incentives to gain industry support despite resistance over duplication and legal authority. Infrastructure expansion faced delays due to local opposition and energy concerns, while U.S. pressure constrained European chip sovereignty. Public unease mounted over job displacement, and a foundational legal challenge—the *emergent_court_challenge*—was filed, questioning the EAIEA's jurisdiction.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->

## Current Situation (january-june 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### The Open Frontier Widens  
The second half of 2026 sees AI capability advance steadily, now reaching a level where autonomous agents operate over extended horizons, and breakthroughs in particle physics and mathematics emerge from model-driven exploration. A new open-weight model is released, demonstrating improved efficiency and narrowing the gap with closed frontier systems — though still trailing by several months. This diffusion enhances access to advanced capabilities, including in offensive cyber domains. A newly demonstrated automatic verification method in contract and clinical domains accelerates deployment, widening the frontier’s reach beyond code and math.

A coordinated intrusion across critical infrastructure on three continents, discovered only by chance, reveals deep AI-driven penetration in energy and water systems. While no cascade occurred, the incident underscores systemic fragility. Simultaneously, a controversial study suggests AI-assisted design of human-infective organisms is within reach, igniting debate in the biosecurity community.

### EU Responds with Institutional Ambition  
The European Union, shaken by these developments, proposes the creation of the European AI Evaluation Authority (EAIEA) as its new measure for the turn. Designed to assert technical sovereignty, it aims to pre-evaluate high-capability models and reduce reliance on external assessments. The proposal is bundled with incentives — access to sovereign compute and procurement advantages — to overcome industry resistance.

However, the initiative is still in its early stages. Member states raise legal concerns, and industry groups decry duplication of effort. The fast-tracking of data centre zones in Spain, Poland, and Finland progresses unevenly, with local opposition in two regions citing energy strain. ASML remains under U.S. pressure, limiting leverage in chip design negotiations.

Public sentiment remains divided — AI is widely used but resented, especially as job displacement in legal and engineering sectors becomes visible. The EU’s move is seen as necessary by experts but bureaucratic by the public. A legal challenge, later to be known as the *emergent_court_challenge*, is filed in a national court, questioning the regulatory authority’s jurisdiction — marking its first appearance in the run.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->

---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

PORTFOLIO CHARGE: InvestAI Gigafactories −3, Tech sovereignty package −3, Accelerate sovereign evaluation capability −3, priority −1 = −10  
PROPOSAL BONUS: Accelerate sovereign evaluation capability (cat 5, large) +3 — cyber_test_shot and bio_uplift_findings create urgency, direct relevance to capability and safety  
LEGITIMACY LENDS: capital 45, sentiment 42 -> none  
US_POSTURE: not yet active  
emergent_court_challenge -- first noted turn 1, listed in 1 turn(s) so far: A national constitutional court in a large member state announces it will hear a challenge to the AI Act's high-risk provisions, arguing they impose disproportionate compliance burdens on public services and violate procedural rights. The case is fast-tracked, and preliminary injunctions are plausible.

## Emerging developments (tracked)

- `emergent_court_challenge` -- first noted turn 1, listed in 2 turn(s) so far: A national constitutional court in a large member state announces it will hear a challenge to the AI Act's high-risk provisions, arguing they impose disproportionate compliance burdens on public services and violate procedural rights. The case is fast-tracked, and preliminary injunctions are plausible.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->

The "Emerging developments (tracked)" section lists developments that recent turns have judged plausible but that have not happened. They are not events. Let them colour the narrative only as faint, ambiguous signals whose visibility grows with how long they have been listed — never as anything confirmed, and never with a stated probability.

**Five rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.

2. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.

3. **Price the portfolio, out loud, before you apply it.** Metric rule 6 charges `eu_political_capital` for every measure in flight, every turn, on all of them and not only the priority: 3 for a large measure, 2 for a small one, plus 1 more for whichever is the named priority. **Every term in the charge line is a subtraction, the priority's included.** Write it as `priority −1`: it is a further cost for pushing something, never a rebate, and a `+1` in that line has been read as one.

   Write one line in the Notepad giving every measure its price:

   `PORTFOLIO CHARGE: Gigafactories −3, Frontier Access Guarantee −3, Resilience Surge −2, priority −1 = −9`

   Recompute that total every turn from the portfolio as it now stands. It changes when a measure is added and when one finishes, and a total carried forward unchanged while the portfolio grew is this rule being skipped.

3b. **Then judge the proposal bonus, if this turn's new measure earned one.** A separate, one-off addition to `eu_political_capital` under metric rule 6, paid in the turn a measure is proposed and never again. It does not touch the charge above.

   Ask: **in the last three turns, did anything happen that this measure would have helped with?** Read that off the events themselves: what they were, how severe, and which of them this measure answers. What it is worth is your judgement, on how big the event was, how large the measure is, and how long ago it happened. **Typically +1 to +4**, the top of it for a large measure answering a severe, recent shock directly. Several open arguments pointing at one measure are judged together as a single figure, not summed.

   Write it as its own Notepad line, with the reasoning visible, or `PROPOSAL BONUS: none` when nothing argued for it:

   `PROPOSAL BONUS: Cyber Shield (cat 6, large) +3 — cyber_major_incident landed last turn and this answers it directly`

   Two things this rule is not. It is not a lookup: no table gives you the number, and a figure with no reason beside it is wrong. And it is not automatic: a small measure gesturing at an old event earns +1 or nothing at all, and `none` is the right answer more often than not.

3c. **Last, if this run's metric rules give `eu_political_capital` a term for sentiment sitting above it, apply it.** Only when the rules carry such a line, and only when `public_sentiment` is the higher of the two: add what the rule states, never taking capital past sentiment, after every other term above.

   Write it as its own Notepad line:

   `LEGITIMACY LENDS: capital 18, sentiment 31 -> +2`

   Compare the two numbers before writing anything. `none` is correct only when capital is the higher of the two, and a `none` whose own reasoning shows sentiment above capital is wrong.

4. **A finishing turn moves only when something moved it.** The portfolio carries a stated finishing turn per measure, set when the measure was proposed. Copy them forward as they stand. If a measure's finishing turn should change — pushed by being the priority, slipping through neglect, delayed or accelerated by an event — say so in the Narrative in the same breath as the reason, and write the new turn. A finishing turn that drifts with no reason given is an error.

5. Once `us_election_2028` has fired, write the resulting `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` line into the world state for that turn, and carry the same line in the Notepad every turn thereafter. It is a standing condition of the world that metric rule 8 reads each turn, not a one-off narrative beat.

---

This turn, the following external events have occurred:

**cyber_major_incident:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.
**capability_jump:** A discontinuous advance is released or demonstrated, and it lands squarely inside the verifiable domains – code, mathematics, cyber operations, narrow engineering. What an attacker can do changes markedly within weeks. General competence moves by only +1 to +2, and the argument about whether this is progress toward anything general gets louder rather than settled.

---

The actors in the scenario describe their actions as follows:

**The European Union:**

## Statement changes
No statement changes.

## Portfolio
- ``InvestAI Gigafactories (category 4, costs 3 per turn, started turn 1, finishes on turn 7): €200bn fund for four to five sites``
- ``Tech sovereignty package (category 4, costs 3 per turn, started turn 1, finishes on turn 6): Targets €200bn of private capital for AI data centres by 2036 and proposes accelerated-permitting zones``
- ``Accelerate sovereign evaluation capability (category 5, costs 3 per turn, started turn 1, finishes on turn 5): Establish a permanent EU evaluation agency with pre-deployment testing authority over all general-purpose models above threshold capability``

## New measure
**Cyber Shield Initiative**  
Launch a coordinated, cross-sector hardening programme for essential public services against AI-powered cyber threats, with mandatory red-teaming and live-fire exercises.

`Category: 6 (Preparedness and resilience)`  
`Size: large`  
`Finishes on turn: 6`  
`Targeted effect:` Increases resilience (+15), reduces vulnerability to automated attacks exploiting AI-generated exploits; begins closing the gap between offensive capability and defensive readiness  
`Applies to:` EU jurisdiction, targeting national and municipal digital infrastructure, energy grids, water systems, and emergency response networks

## Priority
**Cyber Shield Initiative** — because the *cyber_major_incident* has landed with visible damage across public services, proving that offensive AI tools are now operational at scale, and we cannot rely on evaluation alone when the attack surface is already being exploited.

## In practice
We are activating the Cyber Shield Initiative in direct response to the recent major incident, which demonstrated how AI-generated exploits can bypass traditional defences through speed, novelty, and coordination. The initiative will be led by ENISA in coordination with national CSIRTs, under a new mandate from the Council’s Telecommunications Working Party. We are allocating €8.2bn from the Digital Europe Programme and cohesion funds to finance rapid upgrades in intrusion detection, zero-trust architecture, and automatic patch generation systems. Every member state must submit a national implementation plan by Q3 2027, with binding targets for red-teaming frequency and system recovery time. The first live-fire exercise — simulating an AI-driven supply chain compromise — will be conducted in September across ten critical nodes in Germany, France, and Estonia.

At the same time, we are advancing the Accelerate sovereign evaluation capability measure by finalising the EAIEA’s legal framework under Article 114 TFEU, despite the emerging *emergent_court_challenge*. To strengthen legitimacy, we are expanding the pilot phase to include not only red-team contracts but also joint evaluations with Japan and Canada, building early alignment with trusted third parties. On the industrial front, the InvestAI Gigafactories continue to progress, though Spain and Finland report delays due to local opposition over power allocation. We are responding by offering regional incentives — including priority access to cooling infrastructure and grid rebalancing subsidies — to secure buy-in. The Tech sovereignty package remains on track, but we are beginning to see strain: ASML continues to face U.S. pressure, and without a breakthrough in export coordination, our chip design leverage risks remaining symbolic rather than strategic.


---

Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

Please write your response in English.

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
