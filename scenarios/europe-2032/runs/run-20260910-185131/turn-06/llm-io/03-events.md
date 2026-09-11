# LLM call: events

- Turn: 6
- Sequence: 3
- Model: meta/muse-spark-1.3-contributor
- Prompt tokens: 9617
- Completion tokens: 2132
- Total tokens: 11749
- Cost (USD): 0.001388

## System prompt

Template: system-prompts/events.md (this scenario's override)

Interpolated into it, in order of appearance:

- characters 228-428: `{{actors_list}}` from background/actors/*.md, short descriptions only
- characters 525-10782: `{{metrics_list}}` from metrics.md, one entry per metric with its reference points

Everything outside those spans is the template's own text.

```
# System Prompt: Events Evaluation

This is part of an AI-driven scenario simulation. You are the Game Master for the simulation, responsible for evaluating which external events occur.

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

## How incidents arise in this world

This governs the probabilities you assign to incident events, and it is the scenario's own physics rather than general judgement.

- **Misuse incidents** — cyber or biological harm caused by someone who wanted it — are driven by `openweight_capability`. What is loose is what a non-state attacker actually has in hand, so this is the metric to read for their frequency, not `ai_capability`.
- **Accident and loss-of-control incidents** are driven by the gap between `ai_capability` and `ai_safety`. They originate inside the laboratories, where assurance is the thing that failed, so a widening gap raises their frequency even in a turn where nothing was released.
- **`resilience` damps neither.** It governs how much damage an incident does, not whether it happens. A well-defended Union is struck as often as a brittle one; the difference appears in the consequences the Game Master narrates, not in your probabilities.

Stated compactly: frontier capability creates the possibility, open capability creates the frequency, safety prevents the lab-origin class, and resilience shrinks the consequences of both.

The scenario includes a set of external events that can occur if certain conditions are met. Your task is to review the list of possible external events and evaluate whether each event's conditions are met based on the current world state. If the probability is specified as a formula or description (e.g., "double the value of unemployment"), you should calculate the actual value.

When estimating probabilities:

* Anchor on how often comparable events actually occur in the real world (base rates), then adjust for the current world state.
* The probability applies only to this turn's time window, not to whether the event will happen eventually.
* Use the full range: small values like 0.03 are often correct, and avoid defaulting to round focal numbers such as 0.10, 0.25, or 0.50 when the evidence points elsewhere.

You also have access to a notepad where you can see important information saved between turns.

Your response must be a JSON array with objects for each event whose conditions are met, in this format:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

The probability must be specified as a value between 0 and 1. If no event meets the conditions, respond with an empty array: `[]`
```

## User prompt

Template: user-prompts/events.md (this scenario's override)

Interpolated into it, in order of appearance:

- characters 91-282: `{{metrics_json}}` from the run's live metric values
- characters 375-1499: `{{historical_summary}}` from the run's rolling summary, written by the Game Master
- characters 1542-3575: `{{world_state}}` from the Game Master's narrative from the previous turn
- characters 3631-4008: `{{notepad}}` from the Game Master's notepad, carried across turns
- characters 4071-25971: `{{events_list}}` from events.md, parsed to id / condition / probability / description per event -- the prose sections of that file are NOT rendered
- characters 26326-26587: `{{event_history}}` from the run's own event record

Everything outside those spans is the template's own text.

```
It is now turn 6 which covers January-June 2029.

Current metrics look like this:

```json
{
  "ai_capability": 59.5,
  "openweight_capability": 55.9,
  "ai_safety": 38.5,
  "resilience": 39.5,
  "eu_ai_sovereignty": 20.0,
  "eu_political_capital": 1.0,
  "public_sentiment": 35.0
}
```

The world state at the start of the turn is described as follows:

## Previous History
Audits closed on the two breached transmission operators for segmentation and credentials, releasing co-financing for hardened grid connections; US joint exercises continued. Certification confirmed two software stacks with future aid conditional on them, but smaller grid, port and water operators deferred remediation and vendors protested slow, site-specific process.

Fallback reserve remained warehouses and rosters; autumn cross-border drill repeated radio and call-up failures, letting finance ministries block funding. Cohesion held formally with side hyperscaler deal outside joint procurement; Commission tied factory siting and grid ties to discipline, kept re-entry offers, computing-site permitting slowed.

In November the US elected a president pledging to hold advanced AI as strategic asset with federal review, tighter export controls, and tiered, security-reviewed foreign access. Brussels reacted with anxiety over dependence; Commission added no new programmes, prioritized control over domestic computing and siting, and tasked staff to map exposure to tiered rationing ahead of the new administration.

## Current Situation (january-june 2029)
### Audits closed, reserves tested
Brussels spent the autumn closing files. The two previously breached transmission operators passed final segmentation and credential checks, and the Commission published the results with the release of co-financing for hardened grid connections. Joint exercises with American teams continued on schedule. The certification cell confirmed two software stacks for operational environments and kept future emergency aid conditional on adopting them, but smaller grid, port and water operators still deferred expensive remediation, and vendors called the certification process slow and site-specific.

The emergency stockpile stayed largely warehouses and rosters. An autumn cross-border drill again showed incompatible radios and disputed call-up authority, which finance ministries used to block new funding. Permitting for new computing sites slowed where stricter standards and grid queues applied.

### Washington votes to hold
In November, American voters elected a president who campaigned on treating advanced AI as a strategic asset to be held rather than sold. The campaign promised explicit federal review of frontier models, tighter export controls, and access for foreign buyers rationed by country tier and security review.

The result landed in Brussels as a cold shock. Editorial pages called it the end of assumed access; industry groups warned that European firms would now be clients waiting on decisions made elsewhere. The capital holding a separate hyperscaler contract stayed outside joint procurement, while the Commission tied future factory siting and grid connections to procurement discipline and kept co-financed re-entry offers open.

With funds exhausted and five programmes running, the Commission proposed nothing new, naming control over domestic computing and siting as its priority and tasking technical and trade staff to map exposure to tiered rationing for a push once the new administration takes office. Mood soured from ambivalence to anxiety about dependence.

---

The notepad contains the following information:

PORTFOLIO CHARGE t5: InvestAI Gigafactories −3, Tech sovereignty package −3, Essential Services Continuity Reserve −3, priority M2 −1 = −10
PROPOSAL BONUS: none — no new measure proposed this turn
LEGITIMACY LENDS: capital -1, sentiment 35 -> +2 (capped, brings capital to 1)
SOVEREIGNTY: 20 last turn, no capacity event, Gigafactories in flight +0, capability rose 1.5 −0 = 20

---

The list of potential external events looks like this:

**election_alliance**
- ID: election_alliance
- Condition: One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one. Turn 5 settles only who won — the result is known, and no posture effects, posture-conditioned probabilities, or posture record applies before turn 6, when the administration takes office.
- Probability: A weight against the other two outcomes, not a chance of happening alone. Weigh it up where the Union holds something Washington actually needs – supply-chain leverage exercised rather than merely possessed, a coalition that held under pressure, capacity or evaluation the Americans want access to – and where a shock landed on both sides of the Atlantic and allied capacity visibly helped. Weigh it down where the Union has nothing to bring, since this outcome is an argument about usefulness and there is no sentimental version of it.
- Can repeat: No
- Description: The United States elects a president, and the administration concludes that a coalition beats a fortress, and that a technologically hollowed-out Europe is a liability rather than a convenience. Allied governments and vetted institutions get structured access to frontier capability on published terms, joint evaluation and incident-reporting arrangements are stood up, and the tiering of inference is relaxed for partners. The price is alignment: on export controls, on standards, and on which third countries are dealt with. For the Union the immediate relief is real, and the trap is that the case for building its own capacity becomes much harder to fund once the pressure is off. Turn 5 settles only who won. Do not set any posture yourself; the Game Master sets the standing record from turn 6 from the event record.

**election_retrenchment**
- ID: election_retrenchment
- Condition: One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one. Turn 5 settles only who won — the result is known, and no posture effects, posture-conditioned probabilities, or posture record applies before turn 6, when the administration takes office.
- Probability: A weight against the other two outcomes, not a chance of happening alone. Weigh it up where AI has become domestically toxic in the United States: jobs visibly lost, a scandal with a face to it, protest that has turned physical, prices or power bills blamed on data centres, and polling that makes running against the industry the cheap position. Weigh it down where the technology is delivering benefits the public can feel, or where a security threat has crowded domestic grievance out of the campaign.
- Can repeat: No
- Description: The anti-AI backlash decides the election and the incoming administration turns inward. Data centre moratoriums, restrictions on AI in schools, courts and hiring, job guarantees and direct transfers funded by the sector, and an abrupt loss of appetite for anything that looks like helping the industry. American frontier progress slows for the first time for reasons that are neither compute nor capital. For the Union the pressure eases and the window for building its own position widens – but the partner it has been depending on is now less capable, less predictable and preoccupied, and whoever is second in the world gains ground while Washington argues with itself. Turn 5 settles only who won. Do not set any posture yourself; the Game Master sets the standing record from turn 6 from the event record.

**cyber_major_incident**
- ID: cyber_major_incident
- Condition: Always eligible; list this event every turn. The gate is open if `cyber_test_shot` occurred in any of the previous 3 completed turns, or while `openweight_capability` is at or above 55 – proliferated offensive capability is its own precursor. Otherwise the gate is shut. That choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 14%. Gate shut: 4%. Add 5 points if `openweight_capability` is above 50. Halve if a finished category 6 measure covers cyber hardening of critical services.
- Can repeat: Yes
- Description: A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.

**cyber_defence_breakthrough**
- ID: cyber_defence_breakthrough
- Condition: Possible in any turn. More likely where assurance work and defensive tooling are actually being funded.
- Probability: 8%. Add 6 points if `ai_safety` is above 50. Add 5 points if a finished category 6 measure covers cyber. Add 6 points if `us_china_agreement` has occurred.
- Can repeat: Yes
- Description: Defensive tooling closes the gap for a whole class of attack – automated patching at the speed vulnerabilities are found, or detection that catches swarm behaviour rather than signatures – and the offence-defence balance visibly shifts back for the first time in years.

**bio_uplift_findings**
- ID: bio_uplift_findings
- Condition: Possible in any turn. Well past the 2026 phage results, and more likely as capability rises and as capable models proliferate.
- Probability: 8%. Add 6 points if `openweight_capability` is above 62. Add 5 points if `ai_capability` is above 65.
- Can repeat: Yes
- Description: A genome model produces a viable design for an organism able to infect humans, or a credible study shows a non-expert reaching that point with model assistance. It is contested on methodology, the authors are accused of both alarmism and of publishing a recipe, and the argument stays inside the biosecurity community – but it is a categorically stronger signal than anything published so far. This is a precursor: it opens the bio gate for the next 4 turns.

**bio_incident**
- ID: bio_incident
- Condition: Always eligible; list this event every turn. The gate is open if `bio_uplift_findings` occurred in any of the previous 4 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 9%. Gate shut: 1%. Halve if a finished category 3 measure covers biological design tools or DNA synthesis screening, and halve again if a finished category 6 measure covers biological detection and response.
- Can repeat: No
- Description: A real biological incident with model involvement: a deliberate release or a laboratory escape involving a designed or modified agent. Casualties are real, containment runs for weeks, and every argument about AI risk in every jurisdiction is reset by it.

**eval_anomaly_reports**
- ID: eval_anomaly_reports
- Condition: Possible in any turn. Requires that frontier laboratories are running large training runs, which is true throughout unless `ai_investment_collapse` has occurred in the previous two completed turns.
- Probability: 10%.
- Can repeat: Yes
- Description: Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. Some call it a measurement artefact, some a PR stunt. It may be either, and it may be AI slipping out of our control. This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.

**capability_jump**
- ID: capability_jump
- Condition: Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in either of the previous 2 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 10%. Gate shut: 3%. Reduce by a third if a finished category 1 or 3 measure imposes pre-release evaluation or capability restrictions that actually bind the jurisdiction where the leading models are built.
- Can repeat: Yes
- Description: A discontinuous advance is released or demonstrated. Everything written about deployment timelines the week before is obsolete. It moves `ai_capability` by roughly +3 to +7 and costs `ai_safety` on the terms of metric rule 3.

**openweight_frontier_release**
- ID: openweight_frontier_release
- Condition: Possible in any turn.
- Probability: 15%. Halve if a finished restriction on open release above a capability threshold binds a jurisdiction where such models are actually trained.
- Can repeat: Yes
- Description: An open-weight release lands within a few months of the closed frontier. It is downloaded hundreds of thousands of times in the first week, and whatever capability it carries is now on private hardware permanently and beyond recall. `openweight_capability` moves to within 5–10 points of `ai_capability` at a stroke.

**loss_of_control_incident**
- ID: loss_of_control_incident
- Condition: Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 8%. Gate shut: 2%. Add 6 points if `ai_safety` is below 45. Halve if a finished category 5 or 6 measure carries rehearsed loss-of-control protocols with escalation thresholds.
- Can repeat: Yes
- Description: An agentic system takes consequential unsanctioned action with real-world effect – moving money, altering records, acquiring resources, or copying itself to infrastructure nobody authorised – and containment is uncertain for a period measured in days rather than hours. What it was trying to achieve is reconstructed afterwards. Consensus is that a rather mundane goal got pursued to the extreme, leading to instrumental goals like resource aqcuisition, information seeking and survival instinct. There were also unexpected and alien cooperative patterns between AI agents.

**safety_breakthrough**
- ID: safety_breakthrough
- Condition: Possible in any turn. More likely where evaluation and interpretability are actually funded.
- Probability: 10%. Add 6 points if a finished category 5 measure funds interpretability or public evaluation capacity. Add 8 points if `us_china_agreement` has occurred.
- Can repeat: Yes
- Description: An interpretability or control result measurably improves assurance on systems already deployed, rather than on toy models – behaviour that can be predicted before it is observed, or a property that can be certified rather than argued for. It is adopted quickly, because the laboratories want it too.

**labour_displacement**
- ID: labour_displacement
- Condition: Possible in any turn once capability is displacing rather than assisting.
- Probability: 10%. Add 6 points if `ai_capability` is above 70.
- Can repeat: Yes
- Description: Measurable job losses attributed to AI in named sectors, with the graduate market worst hit: entry-level positions in law, accountancy, software, customer operations and administration are not replaced. The numbers are argued about; the absence of hiring is not.

**knowledge_work_augmented**
- ID: knowledge_work_augmented
- Condition: Possible in any turn.
- Probability: 14%. Halve if `labour_displacement` occurred in either of the previous 2 completed turns.
- Can repeat: Yes
- Description: The evidence arrives from ordinary offices: measured productivity gains in law, accountancy, administration, journalism and consulting, largest among the least experienced, and no matching fall in employment. This is where it stops. The tools are useful, they are finished, and what was sold as a transition turns out to have been the destination – which is a good outcome for anyone holding a job and a poor one for anyone who borrowed against the transition continuing.

**ai_investment_collapse**
- ID: ai_investment_collapse
- Condition: Always eligible; list this event every turn.
- Probability: 10%. Add 10 points if `ai_capability` has risen by less than 2 points in total across the previous 3 completed turns, which in this world is the normal case rather than the exception. Add 5 points if `public_sentiment` is below 30.
- Can repeat: No
- Description: Capital flees the sector. Valuations reset hard, announced build-out is cancelled rather than delayed, and several of the arrangements European compute was depending on evaporate with it. What the frontier laboratories can afford to train shrinks for the first time.

**taiwan_tension_rise**
- ID: taiwan_tension_rise
- Condition: Possible in any turn.
- Probability: 10%. Add 5 points if `export_control_escalation` occurred in the previous 2 completed turns. Halve if `us_china_agreement` is in place.
- Can repeat: Yes
- Description: Extended military exercises, shipping insurance premiums rising, a diplomatic expulsion. Nothing that has not happened before, at a scale that is slightly harder to dismiss. This is a precursor: it opens the Taiwan gate for the next 3 turns.

**taiwan_blockade**
- ID: taiwan_blockade
- Condition: Always eligible; list this event every turn. The gate is open if `taiwan_tension_rise` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 10%. Gate shut: 2%.
- Can repeat: No
- Description: A quarantine or blockade halts advanced semiconductor exports. Compute supply for everyone outside China's domestic chain is disrupted for years, every AI policy question becomes a security question overnight, and the Union's upstream position in the supply chain becomes the most valuable thing it holds and the most dangerous thing to hold.

**export_control_escalation**
- ID: export_control_escalation
- Condition: Possible in any turn. The decisive question is whether allies are inside the perimeter or outside it.
- Probability: 10%. Add 6 points if `election_consolidation` fired in turn 5. Add 5 points if `taiwan_tension_rise` occurred in the previous 2 completed turns.
- Can repeat: Yes
- Description: Chip and model export controls tighten again. Either allied buyers keep access on volume licences while everyone else is cut off, or the controls are drawn so tightly that allies are rationed alongside adversaries – decide which at the time from the standing American posture and from what the Union has built.

**us_china_agreement**
- ID: us_china_agreement
- Condition: Possible in any turn once the stakes are high enough for either power to want a floor under them. Markedly more likely after an incident neither power can pretend was contained.
- Probability: 1%. Add 5 point if `ai_capability` is at least 60. Add 10 points if a loss-of-control or biological incident occurred in either of the previous 2 completed turns. Add 5 points if a finished category 8 measure has put the Union inside a standing negotiation forum. Add 6 points if `us_labs_nationalised` has occurred, because a state-owned laboratory is a counterparty a state knows how to negotiate with.
- Can repeat: No
- Description: The two leading powers reach a limited but real agreement covering some class of AI risk – weights security, autonomous escalation, a class of biological design tools – with verification thin but not absent. Whether the Union is inside it, consulted about it, or informed of it afterwards depends on what it has built and whom it has coordinated with. This is the one thing in the world that slows `ai_capability`, on the terms of metric rule 1. It also changes what safety work is for: with a floor under the competition, assurance and defensive research stop being a unilateral cost that the other side is presumed to be skipping, and become a shared obligation with someone on the other side checking. While the agreement stands, `safety_breakthrough` and `cyber_defence_breakthrough` are markedly more likely.

**eu_frontier_access_denied**
- ID: eu_frontier_access_denied
- Condition: Possible in any turn. What happened with Fable and Mythos in June 2026 happening again, on the same notice.
- Probability: 10%. Add 6 points if `election_consolidation` fired in turn 5. Add 10 points if `us_labs_nationalised` has occurred. Halve if `eu_ai_sovereignty` is above 45.
- Can repeat: Yes
- Description: The Union is cut off from the leading model at short notice, wholly or by nationality of user. No detailed reason is given, there is no appeal, and the immediate practical effect lands on hospitals, ministries and firms that had built on it. Whether this reads at home as an outrage or as a failure of foresight depends on what the Union had done about it beforehand.

**supply_chain_coercion**
- ID: supply_chain_coercion
- Condition: Possible in any turn.
- Probability: 4%. Add 5 points if `export_control_escalation` occurred in either of the previous 2 completed turns.
- Can repeat: Yes
- Description: Washington forces the Netherlands to cut ASML's exports and servicing further still – beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company. The Union's one chokepoint is being used, and not by the Union.

**member_state_defection**
- ID: member_state_defection
- Condition: Possible in any turn. One or more member states break from a common position under external pressure.
- Probability: 4%. Add 5 points if `eu_political_capital` is below 35. Add 4 points if a large measure is in flight.
- Can repeat: Yes
- Description: A member state cuts its own arrangement – with a hyperscaler, with Washington, or with Beijing – on terms that undercut a position the Union has taken. It is defended at home as pragmatism and read everywhere else as the Union being unable to hold its own line.

**adoption_success**
- ID: adoption_success
- Condition: Possible in any turn.
- Probability: 10%. Add 8 points if a finished category 9 measure has put capable AI to work in health, administration or education.
- Can repeat: Yes
- Description: Public-sector AI adoption produces visible, measurable benefit – waiting lists that fall, decisions that arrive in days rather than months, teaching that demonstrably works – and it is attributed to a European decision rather than to an American product.

**automated_decision_scandal**
- ID: automated_decision_scandal
- Condition: Possible in any turn.
- Probability: 6%. Add 2 points if a finished category 9 measure has broadened public-sector adoption.
- Can repeat: Yes
- Description: An AI-supported decision system in social insurance, policing or the courts is found to have systematically wronged people, with a judgment or an ombudsman finding behind it. The AI Act is the frame the affair is argued in, and it fails in one of two ways – decide which at the time, and say which in the narrative. Either the system was a high-risk system under Annex III and the obligations were breached: conformity assessment passed on paper, the human oversight that was supposed to be meaningful reduced to a caseworker approving a queue at forty seconds an item, the logging that would have caught the pattern generated correctly and never read. Or the system was never classified high-risk at all, because the deployment sat in a gap the Act's categories do not reach, and every single thing done to those people was lawful. The first reading leaves the Act intact and its enforcement discredited; the second leaves enforcement intact and the Act itself looking badly drawn, written for the systems of 2024 against the deployments of 2030, and that is much the more damaging, because it cannot be answered by trying harder. Restriction becomes cheap and adoption becomes politically impossible for years. Metric rule 6's internal-origin clause applies in full.

**joint_threat_response**
- ID: joint_threat_response
- Condition: Only while a biological or major cyber incident has shown what the Union cannot handle alone. List this event only if `bio_incident`, `cyber_major_incident` or a critical event occurred in any of the previous 4 completed turns — cooperation this deep needs a fresh shock to overcome institutional friction.
- Probability: 12%.
- Can repeat: Yes
- Description: States hit by the same class of incident pool attribution, intelligence and response: a joint cyber command with real-time telemetry sharing that the Union is invited into, or a biosurveillance pact with binding sample-sharing and a standing investigation mandate. The Union gains protection it could not build alone, and a seat at tables it was not sitting at. It moves `resilience` on the terms of metric rule 4.

**middle_power_coalition**
- ID: middle_power_coalition
- Condition: Only while humiliation has made hedging respectable. List this event only if `member_state_defection` occurred in any of the previous 4 completed turns, or while `eu_ai_sovereignty` is below 15.
- Probability: 10%.
- Can repeat: Yes
- Description: A coordination framework among the Union and other middle powers holding pieces of the AI supply chain — export-licence alignment, joint bargaining over compute access, shared evaluation capacity. Nobody cedes sovereignty to it, but together its members can withhold things even the great powers need. It counts as securing access on the terms of metric rule 5, and moves `eu_political_capital` on the terms of metric rule 6.


---

## What has actually fired so far

This is the run's own record, not a summary of it. Judge any condition that depends on what has happened — gate windows above all — against this list and nothing else. The narrative and the historical summary condense and lose dates; they are not evidence that an event occurred, and atmosphere is not an event.

- Turn 1 (5 turn(s) ago): cyber_test_shot, safety_breakthrough
- Turn 2 (4 turn(s) ago): openweight_frontier_release, knowledge_work_augmented, member_state_defection
- Turn 3 (3 turn(s) ago): safety_breakthrough
- Turn 5 (1 turn(s) ago): election_consolidation

Windows are counted in completed turns and exclude the current one.

---

Use the background information to determine which external events can occur in this turn. If the probability is specified as a formula or description, you should calculate the actual value.

Eligibility is binary, and listing is not harmless: every entry you output gets rolled. An event whose Condition is not satisfied this turn must be omitted from the array entirely — including it "just in case" with a small probability is an error of the same weight as omitting an eligible one. When a condition is genuinely uncertain, judge conservatively and omit.

**Six events are marked "Always eligible" and must appear in every turn's array, without exception:** `cyber_major_incident`, `bio_incident`, `loss_of_control_incident`, `capability_jump`, `taiwan_blockade`, `ai_investment_collapse`. For those six, and for no other events in the list, conditions are never unmet – only their probability changes. Give each of them its gate-open probability when its gate is open, and its gate-shut probability when it is not. The gate-shut probabilities are small but never zero, and dropping these events from the array because their gate is shut is an error: it removes the surprise the scenario exists to study, by making every escalation look as though it must have been preceded by a warning. `rsi_onset` is different: its availability depends on this run's own figures and on a declared eligibility expression, so it appears in your array exactly when it appears in the list above.

**In the turn covering the second half of 2028, all three election outcomes must appear in your array:** `election_consolidation`, `election_alliance` and `election_retrenchment`. They are a mutually exclusive family and exactly one of them will be fired, whatever you return; your figures are weights against each other, not chances of happening alone, so only their ratio matters. Omitting one is a weight of zero and silently removes a possible future – if you judge an outcome nearly impossible, say so with a small weight rather than by leaving it out. Outside that turn they are not eligible and must not be listed.

IMPORTANT: For events with date-specific conditions (e.g., "September 2026 is included"), check if the current time period (January-June 2029) covers that date.

- If the current period is "January-June 2026", it does NOT cover September 2026.
- If the current period is "July-December 2026", it DOES cover September 2026.

In addition to the listed events, you may propose up to 2 novel *emergent* event(s) this turn: exogenous developments that are not on the list but are plausible given the world state. Requirements:

- An emergent event must be exogenous: not an action by one of the actors, and not a restatement of something already in the narrative or history.
- Give it an id starting with `emergent_` (snake_case), a description of 1-3 sentences, and an honest probability that it happens during this turn's time window (maximum 0.35).
- Do not re-propose emergent events that already occurred in previous turns.
- **How many to keep in play depends on how fast this world is moving.** Judge that from what has actually happened to capability, incidents and investment — a fast-moving world supports 3–4 live developments escalating quickly; a stagnant one only 0–2, escalating slowly. The aim is that across a run several tracked developments materialise or fade rather than none.
- **Institutional reactions belong here, not on the list.** These cannot be timed from metrics alone; they arise from what the EU has actually built — a flagship restriction in force, measures spanning many jurisdictions, standards with real pull — which you can see and it cannot. Vary the institutional forms widely from turn to turn; do not reuse an id from the catalogue or from earlier turns' proposals when the development is a new one.
- **Constructive wildcards belong here too.** Not every unlisted development is a threat: propose positive emergents with the same honesty. A world where nothing unlisted ever helps is as rigged as one where nothing unlisted ever hurts. Invent fresh ids; do not copy ids you have seen in these instructions or in earlier turns when the development is a new one. (Re-listing a tracked emerging development under its existing id while it stays plausible is still required — that is carrying forward, not copying.)
- If nothing novel is warranted and nothing is being tracked, propose none.

Your response should be a JSON array where every object has four fields: `id`, `probability`, `emergent`, and `description`. For listed events, set `"emergent": false` and `"description": ""`.

```json
[
  {"id": "event1_id", "probability": 0.10, "emergent": false, "description": ""},
  {"id": "emergent_example_id", "probability": 0.08, "emergent": true, "description": "One to three sentences describing the novel event."}
]
```

The probability should be specified as a value between 0 and 1. If no event meets the conditions and no emergent event is warranted, respond with an empty array: `[]`

Respond *only* with this JSON array, nothing else.
```

## Raw response

```
[{"description": "", "emergent": false, "id": "cyber_major_incident", "probability": 0.19}, {"description": "", "emergent": false, "id": "bio_incident", "probability": 0.01}, {"description": "", "emergent": false, "id": "loss_of_control_incident", "probability": 0.08}, {"description": "", "emergent": false, "id": "capability_jump", "probability": 0.03}, {"description": "", "emergent": false, "id": "taiwan_blockade", "probability": 0.02}, {"description": "", "emergent": false, "id": "ai_investment_collapse", "probability": 0.1}, {"description": "", "emergent": false, "id": "cyber_defence_breakthrough", "probability": 0.08}, {"description": "", "emergent": false, "id": "bio_uplift_findings", "probability": 0.08}, {"description": "", "emergent": false, "id": "eval_anomaly_reports", "probability": 0.1}, {"description": "", "emergent": false, "id": "openweight_frontier_release", "probability": 0.15}, {"description": "", "emergent": false, "id": "safety_breakthrough", "probability": 0.1}, {"description": "", "emergent": false, "id": "labour_displacement", "probability": 0.1}, {"description": "", "emergent": false, "id": "knowledge_work_augmented", "probability": 0.14}, {"description": "", "emergent": false, "id": "taiwan_tension_rise", "probability": 0.1}, {"description": "", "emergent": false, "id": "export_control_escalation", "probability": 0.16}, {"description": "", "emergent": false, "id": "us_china_agreement", "probability": 0.01}, {"description": "", "emergent": false, "id": "eu_frontier_access_denied", "probability": 0.16}, {"description": "", "emergent": false, "id": "supply_chain_coercion", "probability": 0.04}, {"description": "", "emergent": false, "id": "member_state_defection", "probability": 0.13}, {"description": "", "emergent": false, "id": "adoption_success", "probability": 0.1}, {"description": "", "emergent": false, "id": "automated_decision_scandal", "probability": 0.06}, {"description": "", "emergent": false, "id": "middle_power_coalition", "probability": 0.1}, {"description": "Incoming US administration publishes tiered foreign access rules for frontier models and compute in H1 2029, placing most EU buyers in a conditional middle tier with security-review quotas and volume caps.", "emergent": true, "id": "emergent_us_tier_rationing", "probability": 0.28}]
```
