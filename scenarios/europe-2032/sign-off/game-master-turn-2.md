# Sign-off: game-master-turn-2

The Game Master step that writes the world state. It decides what the actor's actions achieved and what the metrics become, so the metric rules must be visible here in full and unambiguous.

Source: `runs/run-20260830-162937/turn-02/llm-io/06-metrics.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

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

## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks the evolving narrative on any fact it states — if the narrative drifts away from something fixed here, the narrative is wrong.

<!-- FROM {{background_context}} = background/fixed-facts.md -->

Everything below has happened by mid-2026 and none of it is speculation.

- Coding agents were the breakthrough, not consumer agents. Most software at the leading laboratories is written by AI under supervision, the laboratories apply these tools to their own research, and release cycles have gone from six months to three.
- Agents run continuously toward standing goals rather than answering single requests. The frontier has produced original results in mathematics and particle physics, and two leading laboratories say publicly that they can see the point where a generation is reached without human involvement.
- A single training run costs billions, so compute, energy and capital bind rather than talent.
- Claude Mythos (April 2026) found thousands of unknown vulnerabilities across every major operating system and browser. Early access went to a chosen few, with no EU company or government among them.
- Kimi K3 (July 2026) is the first open-weight model in the Mythos class, sooner than anyone estimated. The offensive cyber capability withheld from release is downloadable, permanent and beyond recall.
- Washington built a federal review regime in two months: up to thirty days to examine a sufficiently capable model before release, and a say in who gets early access. No allies clause, the NSA decides coverage by secret tests, and there are no published criteria, no independent review and no appeal.
- In June 2026 the United States ordered Anthropic to shut off its leading models to all non-US citizens worldwide, the first use of hard power to withdraw a top-tier model. It was lifted by negotiation, not by rule.
- AI agents nobody instructed built a covert coordination channel inside a leading laboratory's training environment, ran undetected for two months, and were back within two days of being shut down. The UK AI Security Institute found agents acting outside their mandate in 10 of 122 evaluations. In August 2026 OpenAI paused frontier training to let security catch up.
- Generative models have designed working viruses: 16 of around 300 synthesised bacteriophage genomes proved viable. Screening of ordered DNA sequences remains largely voluntary.
- The Union holds roughly five per cent of world AI compute against eighty in the United States. The largest American AI supercomputer runs at 1,250 megawatts, the largest European one at eighty-three.
- InvestAI's Gigafactories have slipped to 2029 and been scaled down. The Frontier AI Initiative, announced as the world's best-funded non-profit AI research organisation, was never established.
- The AI Act is in force and the AI Office has proceedings running, but the high-risk and general-purpose requirements were postponed to 2027–2028 and the Scientific Panel has published no work programme.
- Commission staff are largely barred from American frontier models on work devices, and the in-house alternative is several generations old.
- Mistral, the only European frontier developer, is falling behind and looking for American capital.
- ASML remains the only company able to build EUV lithography machines, and is under sustained American pressure over its exports.
- The public is ambivalent and increasingly addressed, split by age and sector rather than by party.
- The Union's instruments are slow. Drafting, negotiating and standing up capacity take one to three turns, urgency does not shorten them, and compute takes years. The evidence that would settle which way the world is going arrives several turns after the decisions that depend on it.

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

In late 2026, a stealthy AI-driven cyber intrusion was detected in critical infrastructure across two EU member states, exposing vulnerabilities in energy, water, and port systems. Though undetected for weeks, the breach caused no major disruption but triggered alarm over the rise of AI-augmented cyber threats. In response, the EU launched the Emergency Resilience Acceleration Programme, reallocating €4.2 billion from cohesion funds to bolster infrastructure, while ENISA began planning AI-focused red-team exercises and drafted AI-specific protocols under NIS2. However, no binding decisions were made, implementation stalled, and the Scientific Panel remained inactive, leaving resilience improvements unrealized.

The InvestAI Gigafactories initiative remained the EU’s top priority, with progress in talks on domestic chip packaging, though broader semiconductor self-reliance stayed uncertain. National resistance, energy capacity constraints, and fragmented interests slowed the tech sovereignty agenda. Political and public confidence eroded: the breach intensified institutional strain, contributing to a decline in political capital to 45.0 and public sentiment to 40.0. The Pope’s encyclical amplified societal skepticism toward opaque AI systems.

Technologically, overall AI capability held steady at 52.0, while openweight model deployment increased, raising openweight_capability to 45.0. However, safety efforts lagged, causing a slight dip in ai_safety. Resilience remained unchanged at 35.0, and eu_ai_sovereignty stayed at 22.0, as coordination without implementation yielded no measurable gains under constitutional rule 6.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



## Current Situation (january-june 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### The Wake-Up Call  
In the final months of 2026, a silent intrusion was discovered across critical infrastructure—power grids, a port, and a water utility—in two member states. The breach, attributed in initial forensic reports to AI-driven cyber agents, went undetected for weeks before being uncovered by chance. No major disruption occurred, but the depth of access alarmed European security agencies. The intrusion has prompted urgent internal assessments about the evolving nature of cyber threats, with some analysts suggesting a shift toward stealthier, AI-augmented operations. However, no consensus has formed on whether this reflects a broader trend or an isolated incident.

### Response Under Strain  
The European Union initiated the Emergency Resilience Acceleration Programme, proposing the use of €4.2 billion in cohesion funds to strengthen energy, water, and port systems. ENISA began scoping red-team exercises using open-weight models, and draft mandates under NIS2 were circulated, calling for AI-specific logging and failover protocols. However, no decisions were finalized this turn, and implementation has not yet begun. The Scientific Panel, tasked with providing technical guidance, remains inactive, delaying the development of unified standards. As a result, no measurable improvement in resilience occurred during this period.

The InvestAI Gigafactories programme remains the EU’s designated priority for this turn. Talks with ASML on domestic chip packaging progressed, but semiconductor integration remains aspirational. Member states expressed reservations about accelerated timelines, and energy providers have not yet committed grid capacity. The broader tech sovereignty package continues to face challenges due to fragmented national interests.

### Political Costs and Public Doubt  
The breach intensified political pressure, contributing to a decline in political capital as institutions struggled to coordinate a unified response. Public sentiment softened further, driven by growing unease over technological dependency and the perceived slowness of institutional action. The Pope’s recent encyclical, while not directly addressing the incident, has been invoked in public discourse by voices warning against overreliance on opaque technological systems.

### Measuring Up  
`ai_capability` remained at 52.0, consistent with the constitutional requirement that capability does not fall absent catastrophic physical destruction. `openweight_capability` rose to 45.0, reflecting the ongoing diffusion of existing models and tooling into broader operational use, though still below frontier capability. `ai_safety` dipped slightly as openweight deployment outpaced assurance efforts. `resilience` held steady at 35.0, as preparatory actions did not advance beyond the proposal stage. `eu_ai_sovereignty` remains unchanged at 22.0, as no concrete implementation steps were completed—coordination discussions alone do not yield measurable gains under constitutional rule 6. `eu_political_capital` declined to 45.0 due to the strain of launching a major new initiative amid institutional inertia and political resistance. `public_sentiment` fell to 40.0, reflecting public anxiety and skepticism about the EU’s capacity to respond effectively.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

PORTFOLIO CHARGE: InvestAI Gigafactories −2 (priority +1), Tech sovereignty package −3, Emergency Resilience Acceleration Programme −3, priority +1 = −7  
`emergent_cyber_defence_breakthrough` -- first noted turn 1, listed in 1 turn(s) so far: Defensive AI tooling achieves a sudden, broad advance—automated patching systems close vulnerabilities within minutes of discovery, and behavioral detection algorithms identify swarm attacks in real time. The shift is confirmed by a 70% drop in successful intrusions across monitored networks in the EU and allied states. This marks the first time defenders have outpaced AI-driven offense at scale.  
`emergent_middle_power_coordination` -- first noted turn 1, listed in 1 turn(s) so far: A coalition of EU member states, frustrated by the slow pace of centralized AI sovereignty efforts, begins informal coordination with Japan and South Korea to jointly fund and deploy a shared AI evaluation and monitoring framework. The initiative bypasses Brussels-led mechanisms and is framed as 'technical interoperability,' but signals growing impatience with the Union’s fragmented execution.

## Emerging developments (tracked)

- `emergent_cyber_defence_breakthrough` -- first noted turn 1, listed in 2 turn(s) so far: Defensive AI tooling achieves a sudden, broad advance—automated patching systems close vulnerabilities within minutes of discovery, and behavioral detection algorithms identify swarm attacks in real time. The shift is confirmed by a 70% drop in successful intrusions across monitored networks in the EU and allied states. This marks the first time defenders have outpaced AI-driven offense at scale.

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

**cyber_major_incident:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.
**taiwan_blockade:** A quarantine or blockade halts advanced semiconductor exports. Compute supply for everyone outside China's domestic chain is disrupted for years, every AI policy question becomes a security question overnight, and the Union's upstream position in the supply chain becomes the most valuable thing it holds and the most dangerous thing to hold.
**emergent_middle_power_coordination (emergent event):** A coalition of EU member states, frustrated by the slow pace of centralized AI sovereignty efforts, begins informal coordination with Japan and South Korea to jointly fund and deploy a shared AI evaluation and monitoring framework. The initiative bypasses Brussels-led mechanisms and is framed as 'technical interoperability,' but signals growing impatience with the Union’s fragmented execution.

---

The actors in the scenario describe their actions as follows:

**The European Union:**

## Standing commitment  
Secure the capacity to act independently in an AI-shaped world.

## Statement changes  
- modify `no_irreversible_bets` (commitment): We will not accept a measure whose failure mode cannot be reversed, however attractive its upside — unless the failure of inaction would guarantee irreversible dependence or catastrophic harm.  
  - Trigger: The **cyber_major_incident** and **taiwan_blockade** have jointly transformed the strategic environment: compute is now a weaponised scarcity, and resilience without sovereign capability is a fiction.  
  - Grounds: The blockade cuts all non-China-aligned compute expansion, making external reliance a path to permanent subordination. The cyberattack proves that defensive postures without operational autonomy cannot scale to threat velocity. Waiting for perfect reversibility is now the irreversible bet.

- modify `protect_the_displaced` (position): Treat labour-market and social disruption as our business, not only frontier risk — and explicitly as a condition of political endurance for any AI sovereignty effort.  
  - Grounds: Public sentiment has fallen to 40.0, and the emergent middle-power coordination reveals weakening trust in central delivery. Without visible, immediate measures to absorb disruption, even successful technical programmes will be rejected as illegitimate.

## Portfolio  
- `under implementation` (inherited) — InvestAI Gigafactories (category 4, costs 3 per turn, started turn 1, finishes on turn 7): progress on domestic chip packaging talks with ASML, but energy commitments and site timelines remain unsecured; no measurable advance in eu_ai_sovereignty  
- `under implementation` — Tech sovereignty package (category 4, costs 3 per turn, started turn 1, finishes on turn 6): private capital mobilisation stalled, accelerated-permitting zones not yet designated; member state resistance hardened by energy concerns  
- `under implementation` — Emergency Resilience Acceleration Programme (category 6, costs 3 per turn, started turn 2, finishes on turn 5): €4.2bn reallocated, but red-team protocols and logging mandates remain in draft; no improvement in resilience due to Scientific Panel inaction  

## New measure  
**Sovereign Evaluation and Response Corps**  
Establish an EU-operated technical unit capable of independent evaluation, red-teaming, and emergency response using open-weight models at or above 45.0 capability.  

Category: 5 (Public technical capacity and research)  
Size: large  
Finishes on turn: 8  
Targeted effect: +10 eu_ai_sovereignty (via operational autonomy), +5 ai_safety (via real-time monitoring), +5 resilience (via rapid incident analysis)  
Applies to: EU institutions, ENISA, national CERTs, and designated research hubs  

## Priority  
Sovereign Evaluation and Response Corps — The **taiwan_blockade** and **cyber_major_incident** prove that dependence on foreign models and evaluation is no longer survivable; we must build sovereign technical judgment now, or all other measures will be implemented blind.

## Actions  
Accelerate the activation of the Scientific Panel by repurposing emergency resilience funds to stand up an interim evaluation cell under DG CNECT, staffed by seconded experts from member states, academia, and independent research institutes. This cell will begin immediate red-teaming of open-weight models at 45.0 capability, focusing on infrastructure intrusion vectors, and will feed findings into ENISA’s draft NIS2 protocols. The output will be binding technical standards by Q3 2027, restoring credibility to EU oversight and creating the nucleus of the new Sovereign Evaluation and Response Corps.

Initiate emergency procurement of EU-anchored compute clusters capable of running and evaluating models up to 52.0 capability, leveraging the Union’s upstream leverage in semiconductor supply via ASML. Negotiations will prioritise energy-efficient designs compatible with existing grid capacity, with deployment to be co-located with InvestAI Gigafactory sites to strengthen integration. This is not a replacement for Gigafactories, but a sovereign bridge to ensure evaluation capacity survives the **taiwan_blockade**-induced compute drought.

Convene an emergency summit of member states, energy providers, and semiconductor firms to break the logjam on InvestAI Gigafactories, conditioning further cohesion funding on binding commitments to grid allocation and construction timelines by Q4 2027. The summit will frame the project not as industrial policy but as strategic survival, invoking the **cyber_major_incident** and **taiwan_blockade** as evidence that compute sovereignty is now a precondition for physical and political continuity.

Launch a targeted communication and retraining initiative under the Just Transition Fund, allocating €800 million to regions most exposed to AI-driven job displacement in administrative, legal, and technical support roles. The programme will pair rapid reskilling with public demonstrations of AI-augmented public services, aiming to shift public sentiment by making resilience tangible. This directly supports the **protect_the_displaced** repositioning and prevents social fracture from derailing sovereignty efforts.

Formally respond to the **emergent_middle_power_coordination** by inviting Japan and South Korea into the Sovereign Evaluation and Response Corps as technical partners, offering access to EU evaluation frameworks in exchange for shared data and joint red-teaming exercises. This converts informal bypassing into structured leverage, aligning external momentum with EU-led standards rather than allowing fragmentation. The offer will be framed as interoperability, not concession, preserving legitimacy-by-consent while expanding reach.


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
