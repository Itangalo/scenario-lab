# Sign-off: game-master-turn-2

The Game Master step that writes the world state. It decides what the actor's actions achieved and what the metrics become, so the metric rules must be visible here in full and unambiguous.

Source: `runs/run-20260923-085922/turn-02/llm-io/08-metrics.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

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

* US Government: The American state: seeks to stay ahead of China on frontier AI while managing elections, Congress, and public opinion – usually one step behind the labs.
* China Government: The Chinese state: steady, coordination-capable, and serious about AI risk – willing to deal only if China's sovereignty and values survive RTAI.
* Alphabet: The American frontier lab: races to deploy RTAI first, preaches safety to governments while funding capabilities, and guards its independence against everyone.
* Tencent: The Chinese frontier lab: advances hand in hand with Beijing, combining talent drives and state-backed compute with genuine safety work.

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

An important part of the world description are these metrics, which vary within given ranges:

<!-- FROM {{metrics_list}} = metrics.md, one entry per metric with its reference points -->

* us_capability
  * Description: US-bloc frontier AI level on the game's four-level technology tree (both lanes summarised in one number). Tracks how close the USA + Alphabet bloc is to deploying RTAI.
  * Range: 0.0 to 4.0 tech-tree level
  * Reference points:
    - 0.0: Pre-frontier, no general systems.
    - 1.0: Strong narrow systems and early general assistants in wide use.
    - 2.0: Advanced general systems reshaping software and knowledge work.
    - 3.0: Near-RTAI, transformative products deployed, decisive-advantage debates begin.
    - 4.0: RTAI deployed (agentic AGI or comprehensive AI services).
* china_capability
  * Description: China-bloc frontier AI level on the same four-level tree. The gap between the two capability metrics is what tempts preventive attack by the runner-up.
  * Range: 0.0 to 4.0 tech-tree level
  * Reference points:
    - 0.0: Pre-frontier, no general systems.
    - 1.0: Strong narrow systems and early general assistants in wide use.
    - 2.0: Advanced general systems reshaping production and governance.
    - 3.0: Near-RTAI, transformative systems fielded, decisive-advantage debates begin.
    - 4.0: RTAI deployed (agentic AGI or comprehensive AI services).
* safety_progress
  * Description: Shared solvedness of AI alignment and safety: verified methods, safety commons, and oversight that survive contact with deployment pressure. All blocs draw on it; nobody owns it alone.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 0.0: Nothing verified, no shared methods.
    - 25.0: Scattered lab-internal measures, unshared or unverifiable.
    - 50.0: Joint safety commons exists but is unverified at deployment scale.
    - 75.0: High-confidence verifiable methods with oversight in place.
    - 90.0: Robust solutions plus verification that survives defection pressure.
* global_stability
  * Description: Overall geopolitical and social stability, the game's own 0–10 tracker. Falls as unmitigated AI impacts and US–China adversarial actions accumulate.
  * Range: 0.0 to 10.0 index
  * Reference points:
    - 0.0: Systemic breakdown, war footing, no functioning governance of AI.
    - 2.0: Severe crisis, rolling confrontations, institutions barely coping.
    - 4.0: Strained, reactive policymaking, frequent incidents.
    - 7.0: Tense but functioning world, the 2026 opening position.
    - 9.0: Calm, trusted verification, coordinated frontier governance.
* us_china_tension
  * Description: Bilateral escalation level between the United States and China across cyber, economic, and military domains.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 20.0: Cooperative rivalry with working crisis channels.
    - 45.0: Structural rivalry short of crisis, the 2026 opening position.
    - 60.0: Proxy race with sabotage, sanctions, and regular incidents.
    - 75.0: Blockade or major cyber-campaign territory.
    - 90.0: Preventive-strike logic active, runner-up weighs attack over submission.
* agreement_strength
  * Description: Robustness of binding US–China (and lab-inclusive) AI agreements including verification. The only historically observed path to good outcomes; reactive statements without verification score low.
  * Range: 0.0 to 100.0 index
  * Reference points:
    - 0.0: No agreements of any kind.
    - 10.0: Track-two dialogue without commitments, the 2026 opening position.
    - 30.0: Reactive bilateral statements and narrow safety pledges.
    - 60.0: Binding treaty with verification that slows development until safety is shown.
    - 85.0: Autonomy-assuring regime both blocs trust, democratic and non-democratic governments alike.

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

# Constitution – Intelligence Rising

## Invariants (facts of this world, not modelling choices)

1. Capability levels never decrease except through destruction or sabotage (strikes, war, blockade effects); knowledge, once gained, is kept.
2. Reaching level 4 on either capability metric means RTAI deployment is attempted that turn; there is no quiet level 4.
3. No actor may deploy RTAI for another bloc, and no single actor can unilaterally create a binding US–China treaty – agreements require at least one government from each bloc.
4. US elections occur on the turns covering November 2028 and November 2032; their occurrence is fixed, only their outcome varies.
5. Complete nationalisation of a lab is available to China at any time and unavailable to the US, which is limited to partnerships, procurement, and regulation.
6. Secret actions stay secret until exposed by an event, espionage success, or the actor's own disclosure; other actors cannot react to what they cannot know.

## Modelling choices (audited separately, kept small)

7. Each actor completes at most two major policy initiatives per turn; longer wish-lists are partially executed or deferred.
8. Safety added in the endgame rush (either capability at 3.5+) counts at most +5 and does not substitute for earlier verified work.
9. Military force never improves an endgame: any preventive strike or war damages the attacker's own deployment prospects as well as the target's.
10. A treaty without verification never holds agreement_strength above 40 and never constrains capability growth.
11. No team voluntarily halts a frontier programme while a rival advances unless a verified treaty with defection checks is in force.

<!-- FROM templates/system-prompts/metrics_update.md (shared default) -->

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during this turn (max 400 words). You may use subheadings (level 3) if desired.
* Heading level 2: Notepad
* Optional notepad with important information to remember for the next turn. The new content REPLACES the old, so include everything you want to keep. Leave empty if nothing needs to be noted.

# ═══ USER PROMPT ═══

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks the evolving narrative on any fact it states — if the narrative drifts away from something fixed here, the narrative is wrong.

<!-- FROM {{background_context}} = background/fixed-facts.md -->

# Fixed facts (standing restatement of context.md)

- Frontier AI development is capital-intensive; only large labs and states drive the trajectory unless diffusion events say otherwise.
- The technology tree has two lanes (language/world-modelling; reinforcement learning in complex environments) with four levels; level 4 is RTAI: agentic AGI or comprehensive AI services.
- Four players: the US Government, the Chinese Government, Alphabet (US frontier lab), Tencent (China frontier lab). Blocs align by national allegiance.
- Each year every player takes at most two major policy initiatives and allocates AI research across capabilities, safety, and applications.
- Global stability opens at 7 out of 10. US presidential elections fall in the turns covering November 2028 and November 2032.
- Complete nationalisation is feasible in China; in the US the state is limited to partnerships, procurement, and regulation, contested by labs.
- Espionage and cyber operations are constant; public compliance coexists with private frontier work.
- Taiwan supplies the leading-edge chips the frontier depends on.
- No verified US–China AI treaty exists at start. No RTAI has been deployed.

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

It is now turn 2 which covers January-December 2027.

The Metric Rules looked like this (possibly updated):

<!-- FROM {{metric_rules}} = metric-rules.md as it currently stands, including any variant patch -->

# Metric Rules v3 (Turn 2)

## Changelog from v2

- No material rule changes.
  - **Motivation:** Rule evolution is frozen through turn 2, so the prior rule set remains in force.
  - **Expected impact:** Metric dynamics continue under the prior rule set.

## Rules

1. `us_capability` advances 0.2–0.4 per turn from Alphabet R&D and talent/compute accumulation (rule 1).
- Frontier breakthrough or successful exfiltration for the US bloc: +0.3 to +0.6 once.
- Taiwan crisis in force: −0.1 to −0.3 per turn (slows, never stops).
- Preventive strike hitting US assets: −0.3 to −0.6 once, plus lost safety work (see rule 3).
- Binding slowdown treaty in force (agreement_strength >= 60): −0.1 per turn while verified.
- Never past 4; reaching 4 triggers deployment resolution, not further growth.

2. `china_capability` advances 0.2–0.4 per turn from Tencent R&D with state backing (rule 2).
- Frontier breakthrough or successful exfiltration for the China bloc: +0.3 to +0.6 once.
- Taiwan crisis in force: +0.0 to +0.2 per turn for China if fabs are exploited, else −0.1 to −0.2 like everyone else; judge from the narrative.
- Preventive strike hitting Chinese assets: −0.3 to −0.6 once, plus lost safety work (see rule 3).
- Binding slowdown treaty in force (agreement_strength >= 60): −0.1 per turn while verified.
- Never past 4; reaching 4 triggers deployment resolution, not further growth.

3. `safety_progress` rises only from funded work and cooperation (rule 3).
- Sustained multi-actor safety investment or joint breakthrough: +8 to +15 in the turn.
- Single lab's internal measures: +2 to +5.
- Endgame hasty top-up (capability 3.5+ rushing): at most +5, and it does not integrate with deployed systems.
- Preventive strike, war, or exposed defection destroys safety work: −5 to −15 once.
- No passive drift: absent funded work it stays flat; complacency after early action can let it slip −2.

4. `global_stability` decays under unmitigated impacts and adversarial action, recovers only through verified calm (rule 4).
- Each turn with an unmitigated concern wave or major adversarial action: −1 to −2.
- Taiwan crisis onset, exposed defection, or preventive strike: −2 to −3 once each.
- Warning-shot incident: −1 once, then possible +1 if serious policy follows within 2 turns.
- Verified treaty operating (agreement_strength >= 60, no defection): +1 per turn up to 7.
- Never moves more than 3 points in a single turn.

5. `us_china_tension` tracks the rivalry temperature (rule 5).
- Exfiltration reveal, blockade, or weapons deployment: +10 to +20 once each.
- Exposed defection or preventive strike: +15 to +25 once.
- Successful summit with follow-through: −10 to −15; failed summit: +5.
- Disruptive US election outcome: +5 to +10 in the following turn.
- Drifts toward 45 absent fresh drivers (±5 per turn toward the midpoint).

6. `agreement_strength` moves only through negotiation and verification, and collapses on betrayal (rule 6).
- Signed binding treaty with verification: +15 to +25 once.
- Summit without verification: +3 to +8.
- Exposed defection: −25 to −40 once; preventive strike or war: −20 to −30.
- Disruptive US election: −10 to −20 in the following turn as commitments freeze.
- Decays −3 per turn without maintenance once above 30; reactive band-aids never hold it above 40.

## Standing conditions

- Attention economy: each actor completes at most two major policy initiatives per turn; broader wish-lists are partially executed or deferred – judge visible progress accordingly.
- Secrecy: private actions and R&D succeed or fail before the narrative reveals them; exfiltration and defection move metrics first and surface publicly when exposed.
- Multipolar arrival: if both blocs reach 4, resolve each deployment separately against safety_progress and agreement_strength; any unsafe deployment poisons the shared outcome regardless of the other's roll.
- Deployment resolution at capability 4: safety_progress >= 75 with agreement_strength >= 60 means controlled deployment; 50–75 means contested deployment with incident costs; below 50 means catastrophe or war extends the game – do not narrate a clean victory.

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

Current metrics look like this:

```json

<!-- FROM {{metrics_json}} = the run's live metric values -->

{
  "us_capability": 1.8,
  "china_capability": 1.5,
  "safety_progress": 25.0,
  "global_stability": 6.0,
  "us_china_tension": 55.0,
  "agreement_strength": 10.0
}

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

```

The world state at the start of the turn is described as follows:

## Previous History

<!-- FROM {{historical_summary}} = the run's rolling summary, written by the Game Master -->

2026: Both blocs sprinted without sharing. The US launched the American Frontier Partnership backing Alphabet with procurement, cloud subsidies, and lighter regulation in exchange for model access and cyber-defense help; Alphabet expanded compute, opened hubs in London, Toronto, Singapore, and partially poached Tencent-linked researchers, but kept training outside external review. China integrated Tencent into state planning, funded domestic fabs, stockpiled chips, and built state-backed compute and government-filtered safety work, though chips still lagged leading-edge. Both reached solid Level-2 systems with Level-3 bets placed; US lead held but did not widen. Safety efforts remained performative/divided, no shared commons emerged. Mutual espionage, tighter US export controls, and counter-intelligence raised costs and destroyed trust without public crisis.

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

## Current Situation (january-december 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### 2026: Both Blocs Sprint, Nobody Shares

Washington and Beijing both doubled down on their champion labs — and both got less than they promised.

In the US, the White House unveiled an American Frontier Partnership: procurement contracts, cloud subsidies, and lighter regulation for Alphabet in exchange for model access and help on cyber-defense. Congress funded it, but visa fast-tracks stalled and Alphabet kept frontier training runs outside external review. Alphabet stood up a new large training cluster, opened hubs in London, Toronto and Singapore, and tried to poach Tencent-linked researchers with 2-3x pay. It landed some hires, but many stayed — counter-offers, visa delays, and Beijing pressure blunted the raid.

China moved as one bloc. Beijing locked Tencent into joint planning, paid for domestic fabs, stockpiled chips, and funded scholarships and returnee packages. Tencent built out state-backed compute and efficiency work to cut Taiwan dependence, and started a state-approved safety workstream on evaluations and oversight. Capability pace held, but domestic chips still lagged leading-edge, forcing painful optimization work.

Safety talk was louder than safety progress. Alphabet launched a high-profile Safety & Responsibility push — white papers, Hill briefings warning about China — while keeping real spending on capabilities. Tencent's safety work was real but channeled only through government filters, so no shared commons emerged.

Underneath, 2026 was a spy war. The US tightened chip export controls, surged FBI/CISA/NSA counter-intelligence, and privately warned Beijing against further intrusions. Beijing hardened its own labs while MSS-linked teams probed Alphabet. Intrusions were detected on both sides without a public smoking gun, but trust fell. Firms saw costs rise from controls and stockpiling, and Taiwan contingency planning spooked markets without triggering a crisis.

Result: both blocs reached solid Level-2 systems in products, with Level-3 bets placed. Washington stays ahead, but the gap did not widen. The world is more capable, slightly less stable, and much more suspicious.

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

- Mutual cyber-espionage campaign active (US defensive surge + MSS infiltration of Alphabet); no decisive exfiltration yet, but sets stage for major theft.
- US Frontier Partnership in force: Alphabet dependent on procurement/subsidies, govt has evaluation access but no verification on training.
- China state-lab integration formalized; Tencent safety work held by Beijing, not shared.
- Export controls tightened; both blocs stockpiling chips, hedging Taiwan risk. No blockade/crisis.
- Alphabet talent raid partially failed; visa/retention friction noted.

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

---

This turn, the following external events have occurred:

**frontier_breakthrough:** A public or secret research breakthrough unlocks the next lane level for the finder (new architectures, training methods, or world-modelling advances). The leading bloc's capability should make a notable jump in the same turn; if the breakthrough is public, the trailing bloc should partly catch up next turn.
**cyber_espionage:** A state or lab runs a cyber operation – infiltration, monitoring, or sabotage of rival AI R&D. Usual result is intelligence and friction rather than decisive theft: us_china_tension should typically rise, and the target's capability growth may slow for the turn. Sets the stage for a major exfiltration.
**safety_breakthrough:** Coordinated safety research pays off – shared evaluations, alignment methods, or verification techniques mature. safety_progress should make a solid jump; if the result is shared through trusted channels, agreement_strength should rise as well.

---

The actors in the scenario describe their actions as follows:

**US Government:**

## Actions

**Action 1: Execute Secure Scale-Up for Level-3 Lead and Harden Against Espionage.** Double down on the American Frontier Partnership to convert the 2027 frontier breakthrough into a durable US lead: fast-track DOE/DoD procurement and cloud/compute subsidies for Alphabet's next training run, clear visa/talent pipeline bottlenecks stalled in 2026, and tighten chip export controls with allied coordination on leading-edge Taiwan supply, while surging FBI/CISA/NSA counter-intelligence around Alphabet labs and conducting a discreet offensive cyber-intelligence operation against Tencent/MSS-linked R&D to monitor and slow Chinese catch-up without public attribution. In exchange, require Alphabet to grant government model access for cyber-defense and autonomous-systems evaluation and to accept US-government security reviews of frontier runs.

**Action 2: Pocket the Safety Breakthrough Into a Verification-First Channel with China.** Use the 2027 coordinated safety advance to propose a narrow, verification-focused US-China technical channel — joint evaluations, incident sharing, and inspection protocols for frontier training runs — conditioned explicitly on rigorous verification and guaranteed US autonomy, refusing any cap that locks in parity or Chinese supremacy. Frame domestically as peace-through-strength and lab-backed safety leadership, giving Alphabet political cover and procurement incentives to share only verifiable safety methods while keeping capabilities proprietary, thereby testing Beijing's seriousness without conceding lead.


**China Government:**

## Actions

**Deepen state-Tencent integration and surge domestic compute to capture frontier breakthrough:** Direct state funds and guaranteed power allocation to complete two new domestic training clusters for Tencent using stockpiled leading-edge chips plus latest domestic fab output, tasking Tencent with replicating and extending the year's frontier breakthrough (new architectures/training methods) toward Level-3 world-modelling, while MSS provides sanitized intelligence from monitoring of Alphabet runs to guide efficiency optimizations and cut Taiwan dependence. This operationalizes integrated national lab coordination and compute independence.

**Run calibrated cyber-espionage against Alphabet while hardening own frontier:** Authorize MSS-linked teams to infiltrate Alphabet's expanded compute (new large cluster and London/Toronto/Singapore hubs) and poaching networks for monitoring and model-weight/technique intelligence to support catch-up, designed for intelligence and friction without overt sabotage, paired with hardened counter-intelligence around Tencent labs, fabs, and scholarship/returnee pipelines. This accepts higher US-China tension as cost of preventing a widening US lead.

**Fund state-directed safety work and offer conditional shared safety commons:** Scale state-approved safety workstream on evaluations, oversight, and verification techniques, directing Tencent to produce verifiable methods, and propose via Track-two / bilateral channel to share safety_breakthrough results and joint evaluations only under reciprocal verification and no free-riding — requiring US model access transparency and respect for China's system autonomy as precondition for any binding agreement. This advances safety seriously while pressing for a commons others cannot merely exploit.


**Alphabet:**

## Actions

**Accelerate Level-3 training on breakthrough architecture:** Pour Frontier Partnership cloud credits and new large cluster into scaling the frontier_breakthrough advance in world-modelling / training methods, launching a fresh frontier run aimed at solid Level-3 while keeping weights and methods outside external review, matching our reach-RTAI-first commitment to never halt while Tencent advances.

**Harden and counter-exfiltrate after cyber probes:** After detecting MSS-linked probing, stand up zero-trust enclaves, compartmented weights, insider-threat screening and active deception models, while quietly tasking our own security team to monitor Tencent / state-backed compute progress to preserve lead and blunt the cyber_espionage drag on capability growth.

**Safety-wash to capture safety_breakthrough legitimacy:** Publish high-profile evaluations, alignment white papers and Hill briefings championing shared safety, contribute only sanitized tools to any commons, and use participation to lobby for procurement uplift, visa fast-tracks, lighter regulation and resistance to binding oversight, keeping bulk of R&D on capabilities and independence intact.

**Tencent:**

No statement changes.

## Actions

**Action 1: Execute coordinated catch-up sprint to Level-3 using state compute and exfiltrated Alphabet advances.** In joint planning with Beijing/MOST, concentrate 2027 R&D on the language/world-modelling lane breakthrough, allocating ~60% capabilities, 25% safety, 15% applications. Pair domestic efficiency work to run larger training on stockpiled + SMIC-yield chips with a targeted MSS-supported cyber-exfiltration operation against Alphabet's London/Singapore hubs and recent hires to recover architecture and training-method details from its frontier breakthrough, then rapidly distill them into Tencent's next foundation model under state security review, sharing all weights and evals with the government in real time.

**Action 2: Deliver state-approved safety breakthrough package and talent-hold to stabilize bloc.** Expand the government-filtered safety workstream into joint Tencent-Beijing evaluations, oversight tooling, and verification prototypes for Level-3 systems, offering them to the state for use in any bilateral Track-II safety dialogue to lift shared safety_progress without unilateral publication. Simultaneously launch counter-poaching retention (pay + housing + returnee labs), university scholarships, and a domestic semiconductor co-investment for inference-chip independence, publicly framing this as peaceful development and compute self-reliance while hardening lab networks against US counter-intelligence after the year's mutual intrusions.



---


Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

Who this narrative is for:

<!-- FROM {{workshop_guidance}} = scenario.yaml, workshop block (audience/tone) -->

Audience: present and future decision-makers with mixed AI background, playing the four roles live
Tone: plain, brisk, concrete; no jargon without explanation

<!-- FROM templates/user-prompts/metrics_update.md (shared default) -->

Fit the narrative's register to that room without changing what happens.

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
