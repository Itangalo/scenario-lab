# Sign-off: game-master-turn-2

The Game Master step that writes the world state. It decides what the actor's actions achieved and what the metrics become, so the metric rules must be visible here in full and unambiguous.

Source: `runs/run-20260830-185157/turn-02/llm-io/05-metrics.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

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

The simulation includes the following actors:

<!-- FROM {{actors_list}} = background/actors/*.md, short descriptions only -->

* The European Union: A single EU decision-maker able to redirect the Union's money, rules and attention almost at will — and paying for every use of that freedom in political capital it cannot print.

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->



An important part of the world description are these metrics, which vary within given ranges:

<!-- FROM {{metrics_list}} = metrics.md, one entry per metric with its reference points -->

* ai_capability
  * Description: Capability of the strongest systems anywhere in the world, closed or open, measured as general problem-solving competence across economically and strategically relevant tasks. Whichever power holds the lead, this is the lead. Accumulated capability; it does not fall back.
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
  * Description: How much the EU can actually do: political standing, fiscal headroom, legal instruments and member-state cohesion taken together — what it can start, fund and enforce at the same time. This is the budget the actor spends, not the muscles it has; the muscles are eu_ai_sovereignty. Falls with fiscal strain, fragmentation, overreach and failed measures; rises with visible successes and with capacity that has finished landing.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 10.0: Paralysed. Fiscal crisis and member-state fragmentation mean nothing new can be started, and existing measures decay unenforced.
    - 30.0: One measure at a time, and only if it is uncontroversial. Money is the binding constraint.
    - 48.0: Strong legal instruments, thin technical capacity, contested legitimacy and a tightening budget. Two or three measures can run at once before something slips.
    - 65.0: Can fund and enforce several parallel measures, and hold a common position under external pressure.
    - 85.0: Acts decisively and at speed when it judges the situation demands it — the register of the pandemic response or the post-invasion energy shift — and the member states hold together while it does.
* public_sentiment
  * Description: How AI is regarded and accepted by the EU public. Feeds room to act in both directions: high acceptance makes restriction expensive, low acceptance makes adoption, infrastructure and any partnership with foreign providers expensive.
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

   Two things follow, and they are one rule, not two:

   - *They never change.* No event, action or rule change may move a run onto a different long-run path. Individual turns vary within the stated rates; the path they are varying around does not.
   - *Nothing announces the path.* Write what happened to capability this turn and what it plausibly implies. Do not characterise the long run as settled, do not tell the reader which of the futures under debate this world turned out to be, and do not write as though the answer were available to anyone inside the simulation. The EU may reason about where the frontier is heading and name candidates; it may not be told, and neither may anyone else. Descriptions of emergent-event candidates count as narrative for this purpose: they reach the EU when the event fires.

   *What the rates are is metric rule 1's business, not this document's.* The constitution fixes that they hold and that nobody is told them; it says nothing about their values.

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

Starting physics. One turn is six months. Figures are per turn unless stated.

The seven metrics sort by how far the EU can actually move them, and that ordering governs everything below: strong on `resilience`, `eu_ai_sovereignty` and `eu_political_capital`; moderate on `public_sentiment`; weak on `ai_safety` and `openweight_capability`, which it reaches only through market access and international agreement; and essentially none on `ai_capability`. This is uncomfortable and it is correct. The EU does not set the frontier's pace, and rules that let it do so turn the scenario into a fantasy.

## The frontier

1. **This run's own rate sets the growth of `ai_capability`.** In this run: +1.5 to +2.5 per turn while capability is below 60, +0.5 to +1.5 above it, easing into the **68–76** terminal zone. Returns to scale decline; they do not disappear mid-range. Decelerating progress is still progress – a trajectory that flatlines well below its terminal zone, or re-accelerates under conditions this rule does not give, is misapplying the rule.

2. **`ai_capability` is otherwise exogenous, with exactly one exception.** Nothing the EU does moves it. The exception is an international agreement that actually binds both leading powers – `us_china_agreement` with the EU inside it, or an equivalent the narrative establishes as accepted and being complied with by both – which reduces this run's stated growth rate by a quarter to a half while it holds. It is reversible: the reduction ends the turn the narrative establishes that either power has stopped complying.

3. **`openweight_capability` tracks `ai_capability` at a lag, and in this run the lag narrows to nearly nothing.** A flat frontier is one that open weights catch, and distillation keeps working: the gap narrows by 2 to 4 per turn, floor around 5. `openweight_frontier_release` cuts the gap to 5 or below at a stroke, and here the cut is permanent. A fully implemented restriction on open release, binding where such models are actually trained, widens the gap by 2 to 4 per turn while it holds; binding only inside the Union it does nothing at all. `openweight_capability` never exceeds `ai_capability` and never falls.

4. **Capability never falls, and the opening turn is shared.** `ai_capability` and `openweight_capability` are accumulated knowledge and infrastructure. `openweight_capability` never exceeds `ai_capability`. The only exception is catastrophic physical destruction of the compute base, which must be narrated as such. Turn 1 covers the second half of 2026, which has already happened in every run: it ends with `openweight_capability` at 45, give or take a point, whatever this run's rates say about later turns. Divergence begins in turn 2. Rule 3's rates apply from there.

## The incident engine

5. **Frequency comes from two separate channels, and severity from a third.** Misuse incidents – cyber and biological harm caused by someone who wanted it – are driven by `openweight_capability`, because proliferated capability is what a non-state attacker actually has in hand. Accident and loss-of-control incidents are driven by the gap between `ai_capability` and `ai_safety`, because they originate inside the laboratories, where assurance is the thing that failed. Both are damped by `resilience`, which governs how much damage an incident does rather than whether it happens. Stated compactly: frontier capability creates the possibility, open capability creates the frequency, safety prevents the lab-origin class, resilience shrinks the consequences of both.

6. **`ai_safety` measures assurance that has landed on deployed systems, not effort spent.** It therefore falls when capability advances without matching assurance: −1 to −3 per turn in any turn `ai_capability` rose and nothing new landed on shipped systems, and −5 to −12 on `opaque_reasoning`, `capability_jump` or `rsi_onset`, with no reduction in anybody's spending. It rises on `safety_breakthrough` (+5 to +10), and by +2 to +4 per turn while a fully implemented EU measure in category 1, 2 or 5 actually binds the jurisdiction where the frontier models are built – through market access, agreed evaluation, or a developer that needs the single market. The same measure binding only inside the Union moves it by 0 to +1. That weakness is the point.

7. **`resilience` is the EU's strongest lever and decays if left alone.** A finished category 6 measure covering a named class of harm adds +3 to +6 per turn for as long as it is sustained, and the share of that rule 10 gives it while it is still being built. Against it: −1 to −2 per turn in any turn `ai_capability` rose and no resilience measure is in force, because a static defence weakens against a moving offence. Standing still has to cost something, or every run builds once and coasts.

## The Union's two stocks

8. **`eu_ai_sovereignty` is slow in both directions.** A finished category 4 measure adds +2 to +4 per turn while sustained, and the share of that rule 10 gives it while it is still being built; no single turn moves it by more than 5 in either direction absent an event that says otherwise. It decays by −1 to −2 per turn whenever `ai_capability` rose and no sovereignty measure is in force, because the same physical estate buys less independence against a faster frontier. Its slowness in both directions is what makes late action expensive and the timing question real.

9. **The flow costs, the stock pays.** Building sovereignty drains `eu_political_capital` while it is being built – that is the implementation load of rule 10, and a category 4 measure is high-load by default. Having sovereignty pays capital back: +1 to +3 per turn while `eu_ai_sovereignty` is above 40, rising to the top of that range above 60, because there is something to bargain with, successes to point at, and less humiliation feeding sentiment. **Guard, and it binds:** sovereignty's contribution to `eu_political_capital` never exceeds +3 in a turn and never exceeds the combined contribution of every other positive term that turn. A run must be able to reach 2032 with real political capital and little sovereignty, on cohesion, instruments and legitimacy alone. The claim that muscles are *necessary* for agency is what these runs exist to test, not something the physics may assume.

10. **Every unfinished measure costs the same every turn, and finishes on a stated turn.**

    *It costs.* −3 `eu_political_capital` per turn for a large measure and −2 for a small one, every turn until it finishes or is abandoned, charged on all of them and not only the priority. Total the charge across the portfolio and apply it. Naming a measure your priority costs **1 more** that turn, because pushing something is what attention is spent on. An abandoned measure costs nothing further.

    These are political prices, not budgets, and the world moves them – but not by your judgement of the mood. **Read the discount off the event record.** Every event in the catalogue that lowers a price says so on its own entry, as `Cheapens: category N by X for Y turns`, and the events that have fired are listed for you. For each measure, take every `Cheapens:` line that names its category and whose window is still open, and subtract. Two of them reaching the same measure stack. **There is no floor:** a small measure can reach zero and cost nothing at all that turn, which is what it looks like when something has stopped needing to be argued for – the money is still being spent, but nobody has to be persuaded. Nothing raises a price except being the priority.

    *It finishes on a stated turn.* Every measure carries `costs N per turn, started turn X, finishes on turn Y` from the moment it is proposed. Y is judged once, when the measure is first written down, from how large the thing actually is: a directive that needs drafting and a vote finishes in two or three turns, a capability that has to be built and staffed in six or more, and the same instrument may be either depending on how much of it already exists. **After that it is copied forward unchanged. Do not recompute it.**

    Three things may move it, each written into the portfolio line with the reason: being the named priority may pull it in by one turn; leaving a measure unprioritised for several consecutive turns may push it out by one, because flagships slip when nobody carries them; an event may do either, and rarely by more than one. Nothing else moves it, and nothing moves it silently. A measure is finished when the current turn reaches its stated finishing turn.

    *What it delivers.* Nothing at all in the turn it is proposed. After that it delivers a share of whatever per-turn figure its category rule gives it, judged from how far it has come between its starting and finishing turns – little at first, most of it near the end, and the full figure from the turn it finishes and for as long as it is sustained. Judge the share; do not compute it to a decimal.

11. **`eu_political_capital` recovers from results and erodes from their absence.** A measure reaching full implementation: +4 to +8. A measure visibly working when an incident it addresses occurs: +8 to +15. A measure abandoned, a deadline missed, or a proposal publicly defeated: −5 to −12. Idle capacity decays: −3 per turn when nothing is under implementation, and a further −2 per turn while a live class of harm sits unaddressed. There is no drift back toward 48. Capital exists to be spent, and a turn that banks it against a future that may never arrive has cost something.

12. **The attribution rule decides whether a shock strengthens the Union or breaks it.** Negative events move `eu_political_capital` in either direction, and the sign follows from two things already on the record – where the harm originated, and whether the EU had acted beforehand.

    - External origin, prior action taken: reads as vindication. +5 to +12.
    - External origin, no prior action: reads as *why did you not see this coming*. −5 to −12.
    - Internal origin – an EU-deployed system, a regulatory failure, an automated-decision scandal: −10 to −20, regardless of anything else.

    **Damper.** The vindication bonus decays where the same class of harm recurs and the response demonstrably did not work: full on the first occurrence, half on the second, none on the third, and a penalty thereafter. Being attacked twice is someone else's fault; being attacked five times is your own.

13. **Political asymmetry, and it is one-directional.** The capital cost of adopting a measure falls by roughly half in the turn after an incident of the class it addresses, and by roughly a quarter for the two turns after that. Before any such incident the full stated cost applies. A precursor is not an incident, and neither is rising tension: the discount is earned by realised harm. Note what this sets up against rule 12 – waiting makes the next measure cheaper, acting early makes the shock itself strengthen you, and neither dominates.

## The public and the world's mood

14. **`public_sentiment` moves in both directions and must be allowed to.** It falls −8 to −20 after a major incident, −5 to −10 after a labour displacement wave or a visible episode of dependency humiliation, and −4 to −10 after a scandal that names AI as the cause. It rises +2 to +5 per turn where AI is delivering visible public benefit and no harm has landed, and by a further +2 to +6 per turn while a fully implemented category 7 or 9 measure holds. It recovers slowly and does not return to its pre-crisis level within four turns.

15. **Sentiment sets what is affordable, in both directions.** Below 40 it lowers the capital cost of restrictive measures (categories 1, 3) by roughly half and raises the cost of adoption, infrastructure and any partnership with a foreign provider (categories 4, 9) by roughly half. Above 60 it does the reverse. This is not a goodness score: a soured public enlarges the room to restrict and simultaneously makes every diffusion and compute measure politically expensive, which is why neither direction is simply good for the Union.

16. **Diffusion cuts both ways.** Category 9 measures that broaden adoption raise `public_sentiment` and the economic case for everything else, and simultaneously raise the frequency and severity of misuse and cyber events, because there is more surface to attack. Category 7 measures buy sentiment and cohesion without buying capability.

## What the Union does not control

17. **Nothing the EU decides binds anyone else automatically.** Measures aimed at the United States, at China or at the frontier developers work through market access, standards, supply-chain leverage and reputational cost. Their effect on those jurisdictions is at most half of what the same instrument achieves domestically, and is contingent on the narrative first establishing that the target actually complied. Agreement in public and evasion in private is a permitted outcome and should sometimes be the one that happens.

18. **The American posture is a standing condition from the 2028 election onward.** In turn 5 exactly one of `election_consolidation`, `election_alliance` and `election_retrenchment` occurs; which one is decided before you see it. Write the matching `US_POSTURE:` line into the world state that turn and carry it in the notepad every turn after, because it conditions everything below.

    - **CONSOLIDATION:** access to frontier capability is rationed by country tier. Category 4 and 5 measures cost one load level more, `eu_ai_sovereignty` decays at the top of the rule 8 range whenever no build is in force, and events in the EU-exposure family are markedly more likely.
    - **ALLIANCE:** structured access on published terms. `ai_safety` gains +1 to +2 per turn from joint evaluation and incident reporting, and `public_sentiment` gains +1 to +2 per turn; against that, every category 4 measure costs one load level more in political terms, because the case for building an alternative is much harder to fund once the pressure is off.
    - **RETRENCHMENT:** American frontier progress slows for reasons that are neither compute nor capital – reduce this run's stated `ai_capability` growth rate by a quarter while it holds – but the partner is preoccupied and less capable. Category 8 measures aimed at Washington achieve half of what they otherwise would, and whoever is second in the world gains ground in the narrative.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



The world state at the start of the turn is described as follows:

## Previous History

<!-- FROM {{historical_summary}} = the run's rolling summary, written by the Game Master -->

AI capability remains stable at 52.0 due to recursive research automation, while open-weight models advance with Kimi K3's release of a potent offensive cyber capability, raising openweight capability to 45.0. A covert AI-driven cyber intrusion breaches two EU member states, exposing critical gaps in defensive detection despite fortuitous discovery. In response, the EU proposes the Emergency Compute Mobilisation Directive as a priority category 4 measure, initiating preparatory legal work and threat assessments under Article 122 TFEU, though no binding decisions or implementations occur. ENISA and the Scientific Panel begin scoping future AI intrusion detection standards, and talent outreach planning starts with no hires. With three active category 4 initiatives, political costs mount; despite a net −8 cost, capped movement limits reduce eu_political_capital by only 3, from 48.0 to 45.0. Eu_ai_sovereignty and resilience remain unchanged, and public sentiment holds steady at 42.0.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



## Current Situation (january-june 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### The Frontier Creeps Forward

Contrary to early speculation around `capability_plateau_evidence`, `ai_capability` holds at 52.0, sustained by recursive tool use in research automation that continues to yield incremental gains. The pace of improvement remains unannounced and consistent with long-run trends. In the open frontier, Kimi K3 releases an offensive cyber capability previously withheld by Mythos, marking a significant diffusion event. No other open-weight model crosses the threshold this turn, but the jump lifts `openweight_capability` to 45.0, narrowing the gap with the closed frontier.

### A Cyber Wake-Up Call

The `cyber_test_shot` reveals AI-driven intrusions exhibiting operational patience and low observability. Though not exclusively targeting the EU, two member states suffer breaches, and defenders acknowledge detection was fortuitous. Post-incident reviews confirm existing tools failed to flag key patterns, exposing a growing mismatch between threat evolution and defensive readiness. The event sharpens focus but does not yet unify response strategies.

### Emergency Measures, Uneven Buy-In

The European Union proposes the **Emergency Compute Mobilisation Directive**, a category 4 measure aimed at accelerating sovereign compute deployment. It is formally tabled and designated as the **current priority** for the turn, satisfying the requirement for one named priority. Trilogue negotiations are scheduled but do not begin in this turn; the measure remains in the *proposed* phase. Preparatory legal work is announced under Article 122 TFEU, but no binding decisions or implementation actions occur.

The Commission launches a classified threat assessment linking detection failures to gaps in sovereign AI simulation capacity. ENISA and the Scientific Panel initiate scoping work for future AI intrusion detection standards, but no drafting begins. Talent outreach planning starts, with no hires secured. No capacity or enforcement effects arise — the measure is not yet decided, let alone implemented.

### Political Costs Mount

The EU’s active portfolio now includes three category 4 measures: InvestAI Gigafactories (inherited), Tech Sovereignty Package (inherited), and the new Emergency Compute Mobilisation Directive. As per rules, introducing a new measure at this scale incurs a cost of −3 per active large measure, offset by +1 for clear prioritisation. No incident has occurred that would reduce the political cost of category 4 actions. Total charge: −8. `eu_political_capital` falls from 48.0 to 40.0. However, given the cap on single-turn metric movements (Constraint 10), the drop is limited to −3, resulting in a corrected value of 45.0.

`eu_ai_sovereignty` remains unchanged — no capacity has been built. Resilience is unaffected; response plans remain theoretical. Public sentiment holds steady at 42.0, reflecting growing awareness but no shift in overall confidence. The narrative does not telegraph event gates or probabilities, and no metric exceeds the 25-point movement limit.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

- `emergent_supply_chain_pressure` -- first noted turn 1, listed in 1 turn(s) so far: The U.S. Department of Commerce expands its jurisdictional reach over ASML’s software and servicing stack, effectively extending export controls to cover maintenance of existing EUV and older DUV machines bound for China. This triggers an immediate crisis in Dutch semiconductor policy and forces the EU to respond, as the integrity of ASML’s global service model — and thus the Union’s sole strategic chokepoint — is directly challenged.
- US_POSTURE: [pending election in turn 5]

## Emerging developments (tracked)

- `emergent_supply_chain_pressure` -- first noted turn 1, listed in 2 turn(s) so far: The U.S. Department of Commerce expands its jurisdictional reach over ASML’s software and servicing stack, effectively extending export controls to cover maintenance of existing EUV and older DUV machines bound for China. This triggers an immediate crisis in Dutch semiconductor policy and forces the EU to respond, as the integrity of ASML’s global service model — and thus the Union’s sole strategic chokepoint — is directly challenged.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



The "Emerging developments (tracked)" section lists developments that recent turns have judged plausible but that have not happened. They are not events. Let them colour the narrative only as faint, ambiguous signals whose visibility grows with how long they have been listed — never as anything confirmed, and never with a stated probability.

**Six rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write the long run as settled.** Report what happened to capability this turn, and what it plausibly suggests; never characterise the trajectory as established, name which of the futures under debate this world turned out to be, or write as though the question were closed. You apply this run's stated rates; the EU does not have them, and from turn 2 onward the narrative is exactly what the EU reads. Name behaviours, never the pattern: capability growth that slows, accelerates or splits between domains is described by what it did this turn, full stop.
2. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.
3. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.
4. **Price the portfolio, out loud, before you apply it.** Metric rule 10 charges `eu_political_capital` for every unfinished measure, every turn, on all of them and not only the priority: 3 for a large measure, 2 for a small one, plus 1 for whichever is the named priority.

   Then, **before totalling, price each measure against the event record.** Events in the catalogue carry a `Cheapens:` line naming the measure categories they make politically easier, by how much, and for how many turns. This is a lookup, not a judgement: for each measure, find every event that has fired whose window is still open and whose `Cheapens:` names that measure's category, and subtract. Two stack. There is no floor — a measure can reach zero. Nothing raises a price except being the priority.

   A measure in a category that a recently fired event names, still charged in full, is this rule being skipped. It has been skipped before.

   Write one line in the Notepad, giving every measure its price and every discount its reason:

   `PORTFOLIO CHARGE: Gigafactories −1 (eu_frontier_access_denied cheapens 4 by 2), Frontier Access Guarantee −1 (same), Resilience Surge −2, priority +1 = −3`

   Then apply that total. It is written out because it is the rule most easily skipped in both directions: a turn in which several measures are unfinished and capital did not fall has forgotten the charge, and a turn in which the world plainly made something easier and every measure still paid full price has forgotten the discount.

5. **A finishing turn moves only when something moved it.** The portfolio carries a stated finishing turn per measure, set when the measure was proposed. Copy them forward as they stand. If a measure's finishing turn should change — pushed by being the priority, slipping through neglect, delayed or accelerated by an event — say so in the Narrative in the same breath as the reason, and write the new turn. A finishing turn that drifts with no reason given is an error.
6. Once `us_election_2028` has fired, write the resulting `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` line into the world state for that turn, and carry the same line in the Notepad every turn thereafter. It is a standing condition of the world that metric rule 18 reads each turn, not a one-off narrative beat.

---

This turn, the following external events have occurred:

None

---

The actors in the scenario describe their actions as follows:

**The European Union:**

## Standing commitment  
Secure the capacity to act independently in an age of artificial intelligence, before the window closes.

## Statement changes  
No statement changes.

## Portfolio  
- `proposed` — Emergency Compute Mobilisation Directive (category 4, costs 3 per turn, started turn 2, finishes on turn 5): Trilogue negotiations initiated but not concluded; legal basis under Article 122 TFEU advanced, threat assessment completed and annexed, site selection criteria drafted for three sovereign AI hubs.  
- `under implementation` — InvestAI Gigafactories (category 4, costs 3 per turn, started turn 1, finishes on turn 7): No progress this turn; funding allocation remains stalled pending clarity on energy access and permitting acceleration from the Emergency Compute Mobilisation Directive.  
- `decided` — Tech Sovereignty Package (category 4, costs 3 per turn, started turn 1, finishes on turn 6): Accelerated-permitting zones remain legally proposed but unimplemented; private capital response muted due to regulatory uncertainty around compute access and grid priority.

## New measure  
### Horizon-AI Secure Agent Initiative  
Launch a classified R&D programme under Horizon Europe to develop a first-generation EU-controlled agent-capable system by turn 8, designed for defensive simulation, intrusion detection, and secure governmental use.  
Category: 5 (Public technical capacity and research)  
Size: large  
Finishes on turn: 8  
Targeted effect: +8 to eu_ai_sovereignty by turn 8, +5 to ai_safety through sovereign assurance capacity, and foundational leverage for future autonomous defence systems  
Applies to: EU jurisdiction, EuroHPC JU, ELIXIR, and selected national research agencies in France, Germany, and Finland

## Priority  
Emergency Compute Mobilisation Directive — The cyber_test_shot exposed that without sovereign compute, we cannot simulate, detect, or resist AI-driven threats; our defences are blind to attacks we cannot run ourselves, and delaying this directive risks locking the EU into permanent strategic passivity.

## Actions  
Advance trilogue negotiations on the Emergency Compute Mobilisation Directive with binding timelines, pressing both Parliament and Council to agree on a joint negotiating text by June 2027. Focus discussions on the classified threat assessment, which demonstrates that the recent intrusion exploited patterns only reproducible through offensive AI simulation—capability we lack—and argue that Article 4(2) TEU justifies overriding national veto points on energy and land use in designated hubs. Assign Vice-President for Values and Transparency to lead outreach to member states with siting concerns, offering co-governance models and local benefit-sharing to preserve cohesion.  

Direct the Commission’s Joint Research Centre to finalise the scope and architecture for the Horizon-AI Secure Agent Initiative, contracting EuroHPC JU and ELIXIR to integrate AI-agent workloads into upcoming procurement cycles, beginning with secure testbed environments at LUMI and Leonardo. Launch a targeted talent acquisition protocol offering fast-track residency, security clearance pathways, and €2M per researcher over five years to attract ten frontier AI scientists currently outside the EU, focusing on adversarial robustness, agent alignment, and cyber-physical reasoning.  

Task ENISA and the Scientific Panel to deliver draft baseline standards for AI-enabled intrusion detection in critical infrastructure by Q3 2027, based on lessons from the cyber_test_shot. Require that these standards assume the attacker has access to open-weight offensive tools at 45.0 capability, and mandate that pilot implementations in two member states (Germany and Estonia) include red-team simulations using EU-held models at equivalent capability—contingent on the Emergency Compute Mobilisation Directive delivering the necessary infrastructure.  

Maintain fiscal discipline across the portfolio by freezing new disbursements under InvestAI Gigafactories until the Emergency Compute Mobilisation Directive establishes clear energy and permitting pathways, preventing duplication and preserving political capital. Communicate this pause as tactical sequencing, not abandonment, aligning with the `no_irreversible_bets` commitment by ensuring investments follow rather than precede enablers.


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
