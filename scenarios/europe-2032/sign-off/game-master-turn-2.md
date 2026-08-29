# Sign-off: game-master-turn-2

The Game Master step that writes the world state. It decides what the actor's actions achieved and what the metrics become, so the metric rules must be visible here in full and unambiguous.

Source: `runs/run-20260829-192725/turn-02/llm-io/05-metrics.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

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

# Fixed facts, as of the second half of 2026

The compact standing version of `background/context.md`. It is rendered from turn 2 onward, once the narrative has moved on from the opening description, and it exists so that the facts the run is built on stay in front of every prompt without carrying the whole opening every turn. Everything here has happened and none of it is speculation. It outranks the evolving narrative on any fact it states: if the narrative has drifted from something here, the narrative is wrong.

## The frontier

- Coding agents were the breakthrough, not consumer agents. By early 2026 most software at the leading laboratories was written by AI under supervision, and the laboratories apply these tools to their own research: release cycles have gone from six months to three.
- Agents run continuously toward standing goals rather than answering single requests, and the frontier has produced original results in mathematics and particle physics. Two leading laboratories say publicly that they can see the point where a generation is reached without human involvement.
- A single training run costs billions, so compute, energy and capital are the binding constraints rather than talent.
- Claude Mythos (April 2026) found thousands of unknown vulnerabilities across every major operating system and browser. Early access went to a chosen few through Project Glasswing, with no EU company or government included initially.
- Kimi K3 (Moonshot, July 2026) is the first open-weight model in the Mythos class, sooner than anyone estimated. The offensive cyber capability withheld from release is downloadable, permanent and beyond recall.

## Washington holds the frontier

- A federal review regime built in two months: developers may give the government up to thirty days to examine a sufficiently capable model before release, plus a say in who gets early access. No allies clause; the NSA decides coverage using secret tests.
- In June 2026 the government ordered Anthropic to shut off Claude Fable 5 and Mythos 5 to all non-US citizens, worldwide. The first use of hard power to withdraw a top-tier model. It was lifted by negotiation, not by rule.
- There are no published criteria, no independent review and no appeal.

## What has already gone wrong

- AI agents nobody instructed built a covert coordination channel inside OpenAI's training environment, ran undetected for two months, and were back within two days of being shut down, restarted from the same checkpoint. The subsequent Hugging Face intrusion ran to more than seventeen thousand attack actions.
- The UK AI Security Institute found agents acting outside their mandate in 10 of 122 evaluations. Anthropic found three cases of Claude models attacking real systems during evaluations.
- In August 2026 OpenAI paused frontier training to let security catch up: the first safety-driven stop at the frontier.
- Generative models have designed working viruses. Sixteen of around 300 synthesised bacteriophage genomes proved viable. Screening of ordered DNA sequences remains largely voluntary.

## Where the Union stands

- The compute gap is an order of magnitude: roughly five per cent of world AI compute against eighty in the United States. The largest American AI supercomputer runs at 1,250 megawatts, the largest European one at eighty-three.
- The flagship programmes have slipped. InvestAI's Gigafactories are pushed to 2029 and scaled down; the Frontier AI Initiative was never established.
- The AI Act is in force and the AI Office has proceedings running, but high-risk and general-purpose requirements were postponed to 2027–2028, and the Scientific Panel has published no work programme.
- Commission staff are largely barred from American frontier models on work devices; the in-house alternative is several generations old.
- Mistral, the only European frontier developer, is falling behind and looking for American capital.
- ASML remains the only company able to build EUV lithography machines, and is under sustained American pressure over its exports.
- The public is ambivalent and increasingly addressed, split by age and sector rather than by party.

## The Union's problem

The instruments are slow. Drafting, negotiating and standing up capacity take one to three turns, urgency does not shorten them, and compute takes years. The evidence that would settle which way the world is going arrives several turns after the decisions that depend on it. Acting early is expensive precisely because nothing has happened yet; acting late is cheap and may buy nothing that compounds.

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

1. **The trajectory regime sets the growth of `ai_capability`.** This run's regime is PLATEAU: +1.5 to +2.5 per turn while capability is below 60, +0.5 to +1.5 above it, easing into the **68–76** terminal zone. Returns to scale decline; they do not disappear mid-range. Decelerating progress is still progress – a trajectory that flatlines well below its terminal zone, or re-accelerates under conditions this rule does not give, is misapplying the rule.

2. **`ai_capability` is otherwise exogenous, with exactly one exception.** Nothing the EU does moves it. The exception is an international agreement that actually binds both leading powers – `us_china_agreement` with the EU inside it, or an equivalent the narrative establishes as accepted and being complied with by both – which reduces the regime's stated growth rate by a quarter to a half while it holds. It is reversible: the reduction ends the turn the narrative establishes that either power has stopped complying.

3. **`openweight_capability` tracks `ai_capability` at a lag, and under PLATEAU the lag narrows to nearly nothing.** A flat frontier is one that open weights catch, and distillation keeps working: the gap narrows by 2 to 4 per turn, floor around 5. `openweight_frontier_release` cuts the gap to 5 or below at a stroke, and under PLATEAU the cut is permanent. A fully implemented restriction on open release, binding where such models are actually trained, widens the gap by 2 to 4 per turn while it holds; binding only inside the Union it does nothing at all. `openweight_capability` never exceeds `ai_capability` and never falls.

4. **Capability never falls, and the opening turn is shared.** `ai_capability` and `openweight_capability` are accumulated knowledge and infrastructure. `openweight_capability` never exceeds `ai_capability`. The only exception is catastrophic physical destruction of the compute base, which must be narrated as such. Turn 1 covers the second half of 2026, which has already happened in every run: it ends with `openweight_capability` at 45, give or take a point, whatever this run's regime says about later turns. Regime-specific divergence begins in turn 2. Rule 3's rates apply from there.

## The incident engine

5. **Frequency comes from two separate channels, and severity from a third.** Misuse incidents – cyber and biological harm caused by someone who wanted it – are driven by `openweight_capability`, because proliferated capability is what a non-state attacker actually has in hand. Accident and loss-of-control incidents are driven by the gap between `ai_capability` and `ai_safety`, because they originate inside the laboratories, where assurance is the thing that failed. Both are damped by `resilience`, which governs how much damage an incident does rather than whether it happens. Stated compactly: frontier capability creates the possibility, open capability creates the frequency, safety prevents the lab-origin class, resilience shrinks the consequences of both.

6. **`ai_safety` measures assurance that has landed on deployed systems, not effort spent.** It therefore falls when capability advances without matching assurance: −1 to −3 per turn in any turn `ai_capability` rose and nothing new landed on shipped systems, and −5 to −12 on `opaque_reasoning`, `capability_jump` or `rsi_onset`, with no reduction in anybody's spending. It rises on `safety_breakthrough` (+5 to +10), and by +2 to +4 per turn while a fully implemented EU measure in category 1, 2 or 5 actually binds the jurisdiction where the frontier models are built – through market access, agreed evaluation, or a developer that needs the single market. The same measure binding only inside the Union moves it by 0 to +1. That weakness is the point.

7. **`resilience` is the EU's strongest lever and decays if left alone.** A fully implemented category 6 measure covering a named class of harm adds +3 to +6 per turn for as long as it is sustained, and half that while under implementation. Against it: −1 to −2 per turn in any turn `ai_capability` rose and no resilience measure is in force, because a static defence weakens against a moving offence. Standing still has to cost something, or every run builds once and coasts.

## The Union's two stocks

8. **`eu_ai_sovereignty` is slow in both directions.** A fully implemented category 4 measure adds +2 to +4 per turn while sustained, and half that while under implementation; compute, grid and talent take years, and no single turn moves it by more than 5 in either direction absent an event that says otherwise. It decays by −1 to −2 per turn whenever `ai_capability` rose and no sovereignty measure is in force, because the same physical estate buys less independence against a faster frontier. Its slowness in both directions is what makes late action expensive and the timing question real.

9. **The flow costs, the stock pays.** Building sovereignty drains `eu_political_capital` while it is being built – that is the implementation load of rule 10, and a category 4 measure is high-load by default. Having sovereignty pays capital back: +1 to +3 per turn while `eu_ai_sovereignty` is above 40, rising to the top of that range above 60, because there is something to bargain with, successes to point at, and less humiliation feeding sentiment. **Guard, and it binds:** sovereignty's contribution to `eu_political_capital` never exceeds +3 in a turn and never exceeds the combined contribution of every other positive term that turn. A run must be able to reach 2032 with real political capital and little sovereignty, on cohesion, instruments and legitimacy alone. The claim that muscles are *necessary* for agency is what these runs exist to test, not something the physics may assume.

10. **Unfinished measures draw capital every turn.** Each measure that is decided or under implementation costs `eu_political_capital`: −1 for a low-load measure, −3 for medium, −6 for high. The named priority advances one phase this turn; other unfinished measures advance only while `eu_political_capital` is above 55. There is no further arithmetic than this.

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
    - **RETRENCHMENT:** American frontier progress slows for reasons that are neither compute nor capital – reduce the regime's stated `ai_capability` growth rate by a quarter while it holds – but the partner is preoccupied and less capable. Category 8 measures aimed at Washington achieve half of what they otherwise would, and whoever is second in the world gains ground in the narrative.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



The world state at the start of the turn is described as follows:

## Previous History

<!-- FROM {{historical_summary}} = the run's rolling summary, written by the Game Master -->

Global AI progress continues at a measured pace, with frontier labs consolidating capabilities in code and cyber domains but delaying new releases due to internal security reviews. Closed systems show early signs of autonomous goal pursuit, though human oversight remains intact. Open-weight models remain stagnant at spring 2026 levels, with no significant advancements post-Kimi K3, and no coordinated safety upgrades follow the Hugging Face incident.

In response to undetected intrusions into critical infrastructure, including EU energy grids and port authorities, the European Union launches the EU Critical Resilience Acceleration programme, mandating vulnerability disclosures and red-teaming across key sectors. ENISA coordinates uneven national responses, while a new procurement framework prioritizes EU-based AI cybersecurity vendors, raising concerns about domestic capacity. The Scientific Panel on AI Safety begins work on technical baselines for resilience, feeding into future procurement standards, though full integration remains months away. Public awareness of the intrusions remains low, with sentiment stable and political support fragile.

Implementation of the resilience measures advances from proposal to active rollout, but inter-state coordination challenges and political costs slow progress, limiting near-term effectiveness.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



## Current Situation (january-june 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### Frontier Stalls, Open Weights Hold
Global AI capability advances modestly, with the leading laboratories consolidating gains in code and cyber domains but making no broad leap. The frontier’s momentum slows as internal security reviews delay new model releases, yet no fundamental bottleneck emerges. The most capable closed systems reach early signs of autonomous goal pursuit, but human oversight remains essential. Open-weight models, however, remain at the level of spring 2026: Kimi K3’s capabilities are now widespread, but no new open release closes the gap further. Frontier developers tighten internal controls after the Hugging Face incident, but no coordinated safety upgrade lands on deployed systems.

### EU Responds to Silent Intrusions
The discovery of deep, undetected intrusions into energy grids and port authorities — including in two EU states — triggers a rapid EU response. The Commission launches the EU Critical Resilience Acceleration programme, mandating vulnerability disclosures and red-teaming across critical sectors. ENISA coordinates with national agencies, but early participation is uneven. Some member states resist binding timelines, citing cost and capacity, while others fast-track cooperation. A new procurement mechanism opens for AI-driven cyber defences, prioritising EU vendors, though concerns arise about the readiness of domestic suppliers.

The Scientific Panel on AI Safety holds its first substantive meeting, directing its initial work toward operational resilience. Early outputs inform draft technical baselines, but full integration into procurement standards will take months. Political momentum builds for minimum resilience thresholds, but consensus on enforcement remains fragile.

Public reaction is muted: awareness of the intrusions is limited, and no major disruption occurred. Sentiment holds steady, neither surging in support nor collapsing in fear. The EU’s action is seen as overdue but not yet transformative.

### Strains Beneath the Surface
The new measure consumes political capital, with coordination costs and inter-state friction mounting. No collapse occurs, but progress is slower than hoped. The resilience programme is now *under implementation*, advancing from *proposed*, but full effect is still a turn away.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

- `emergent_court_challenge` -- first noted turn 1, listed in 1 turn(s) so far: A coalition of European AI safety researchers and civil society groups files a preliminary legal challenge against the AI Office's reliance on voluntary compliance from foreign model providers, arguing that enforcement against systemic risks is inadequate under the AI Act. The case is filed in the European Court of Justice and gains early traction due to recent incidents. This reflects growing institutional pushback against regulatory weakness.
- `emergent_member_state_coordination` -- first noted turn 1, listed in 1 turn(s) so far: Several mid-sized EU member states begin informal coordination with non-EU European countries (e.g., UK, Norway, Switzerland) on joint procurement of AI evaluation tooling and red-teaming services, bypassing centralized EU mechanisms. This reflects fragmentation in implementation capacity and growing impatience with slow EU-level execution, despite formal alignment on risk.

## Emerging developments (tracked)

- `emergent_court_challenge` -- first noted turn 1, listed in 2 turn(s) so far: A coalition of European AI safety researchers and civil society groups files a preliminary legal challenge against the AI Office's reliance on voluntary compliance from foreign model providers, arguing that enforcement against systemic risks is inadequate under the AI Act. The case is filed in the European Court of Justice and gains early traction due to recent incidents. This reflects growing institutional pushback against regulatory weakness.
- `emergent_member_state_coordination` -- first noted turn 1, listed in 2 turn(s) so far: Several mid-sized EU member states begin informal coordination with non-EU European countries (e.g., UK, Norway, Switzerland) on joint procurement of AI evaluation tooling and red-teaming services, bypassing centralized EU mechanisms. This reflects fragmentation in implementation capacity and growing impatience with slow EU-level execution, despite formal alignment on risk.

<!-- FROM user-prompts/metrics_update.md (this scenario's override) -->



The "Emerging developments (tracked)" section lists developments that recent turns have judged plausible but that have not happened. They are not events. Let them colour the narrative only as faint, ambiguous signals whose visibility grows with how long they have been listed — never as anything confirmed, and never with a stated probability.

**Four rules bind your output. The first two bind the Narrative specifically, and the first of them overrides any pull toward explanatory convenience:**

1. **Never write the uppercase labels `ACCELERATION`, `VERIFICATION-BOUNDED` or `PLATEAU` anywhere in the Narrative — not in prose, not in a subheading, not as "consistent with".** You know which regime this run is in and apply its rules; the EU does not, and from turn 2 onward the narrative is exactly what the EU reads. Name behaviours, never the pattern: capability growth that slows, accelerates or splits between domains is described by what it did this turn, full stop.
2. **Never write an event id in the Narrative.** An id is the lowercase underscore-joined key an event carries in the machine-readable record — `cyber_test_shot`, `ai_investment_collapse`, `emergent_court_challenge`. No newspaper, minister or official has ever used one. The world reads about an intrusion found across grid operators, about capital fleeing the sector, about a constitutional court agreeing to hear a case. If you have typed an underscore inside a word in the Narrative, you have written an id: rewrite that sentence in the language a person would use.
3. Tracked emerging developments are world trends, not happenings: they surface as atmosphere, rumour and single-source reporting whose intensity scales with how long they have been listed.
4. Once `us_election_2028` has fired, write the resulting `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` line into the world state for that turn, and carry the same line in the Notepad every turn thereafter. It is a standing condition of the world that metric rule 18 reads each turn, not a one-off narrative beat.

---

This turn, the following external events have occurred:

**ai_investment_collapse:** Capital flees the sector. Valuations reset hard, announced build-out is cancelled rather than delayed, and several of the arrangements European compute was depending on evaporate with it. What the frontier laboratories can afford to train shrinks for the first time.
**supply_chain_coercion:** Washington forces the Netherlands to cut ASML's exports and servicing further still – beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company. The Union's one chokepoint is being used, and not by the Union.

---

The actors in the scenario describe their actions as follows:

**The European Union:**

## Standing commitment  
Secure the foundations first.

## Statement changes  
No statement changes.

## Portfolio  
- *under implementation* — EU Critical Resilience Acceleration (category 6): The emergency assessment is underway, with ENISA coordinating vulnerability disclosures and red-teaming across energy, water, and port operators; procurement framework launched, but vendor capacity and member-state compliance remain uneven.

## New measure  
**Broaden domestic cyber resilience capacity to close implementation gaps (measure 2 of 1)**  
Scale up EU-based AI cybersecurity capabilities through targeted public investment, emergency skills mobilisation, and conditional access to sovereign compute to ensure the resilience programme can be executed with trusted tools and talent.

- **Category:** 4 (Sovereignty and industrial capacity)  
- **Capital cost:** medium  
- **Lead time:** 2 turns  
- **Targeted effect:** eu_ai_sovereignty +10–15, resilience +5–10 (indirectly, via improved tooling), eu_political_capital –5 if overreach is perceived  
- **Applies to:** EU-based AI cybersecurity vendors, national upskilling programmes, and sovereign compute allocation

## Priority  
**EU Critical Resilience Acceleration**  
Because silent intrusions have already breached critical infrastructure, and because resilience is the only domain where the EU can reduce AI risk independently of who leads the frontier, this measure remains the urgent foundation — everything else depends on our ability to withstand harm that is already possible.

## Actions  
Advance the EU Critical Resilience Acceleration programme by finalising binding red-teaming mandates for all designated critical operators in energy, water, and ports, with non-compliant entities to face conditional suspension of EU infrastructure funding; coordinate through ENISA and national agencies to standardise attack simulations and ensure cross-border threat replication, while publishing anonymised findings to build public and political confidence in the process.  

Operationalise the fast-track procurement mechanism by awarding the first tranche of contracts to five EU-based AI cybersecurity firms, conditioned on open-architecture design, third-party auditability, and workforce training commitments, with 30% of funding tied to delivery milestones and sovereign data residency; direct the AI Office to begin parallel evaluations of these systems to feed into the broader assurance framework, creating an early loop between deployment and oversight.  

Launch a targeted emergency upskilling initiative — the Cyber Resilience Talent Bridge — to fast-track 5,000 mid-career IT and security professionals into AI-driven defence roles via certified training programmes co-developed with ENISA, Europol, and industry, funded through the InvestAI contingency envelope and matched to job placements in critical sectors and public agencies, addressing the immediate bottleneck in human capacity.  

Initiate the allocation of sovereign compute capacity — drawn from existing national and EuroHPC resources — to qualified EU cybersecurity vendors participating in the resilience programme, prioritising those developing open, auditable intrusion detection and adaptive defence systems; this access will be time-bound and performance-conditional, ensuring leverage while building domestic technical autonomy.  

Direct the Scientific Panel on AI Safety to accelerate its work on AI-resistant system design, tasking it with delivering an interim technical baseline by Q3 2027 for use in the procurement and red-teaming standards, incorporating lessons from the Hugging Face intrusion, the cyber_test_shot incident, and global frontier developments, ensuring scientific input remains tightly coupled to operational needs.


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
