# Events

## The gate mechanism

Some events in this list are **precursors** and some are **escalations**. A precursor does not predict its escalation and does not cause it. What it does is **open a gate**: for a stated number of turns afterwards, the escalation's probability is the higher figure given in its entry. While the gate is shut, the lower figure applies. The dice are still rolled either way, and an open gate that never fires is the normal case.

Four rules govern gates, and they matter.

1. **Every escalation event is listed in every turn, always.** An escalation is never ineligible: it is either at its gate-open probability or at its gate-shut probability, and both are non-zero. Omitting an escalation from a turn's evaluation is an error, because it silently removes the low-probability surprise the design depends on. The gate governs the number, not whether the event appears.
2. **Judge gate state from what has actually happened.** A gate is open only if its precursor appears in the run's record of occurred events within the stated window, or the stated metric threshold is currently met. Atmosphere in the narrative is not a gate. Windows are counted in completed turns and exclude the current one: "the previous 3 turns" means turns t−1, t−2 and t−3, so a precursor firing this turn opens its gate from next turn onward.
3. **Gates are visible here and nowhere else.** The narrative must never state or imply that a gate is open, never forecast an escalation, and never write sentences like "a major campaign is expected within the year". The world may feel tense; it may not be told what is coming.
4. **A precursor is a small, ambiguous, contestable item.** It is the kind of thing that is reported once and argued about, never a warning.

That combination is the point of the design. If the precursor were as conspicuous as the escalation there would be no monitoring problem to study, and if it were invisible there would be nothing to monitor.

## Where the figures come from

Several probabilities depend on how fast this particular world is moving. Where this file gives a figure, it is the neutral default; the run's own patched entries carry the figure that actually applies. What applies never changes during a run and is never named in any narrative or event description.

## Arithmetic of probabilities

Apply modifiers exactly as written: "add 8 points" means +0.08 to the stated figure; "halve" and "double" apply to the figure after additions, before any cap. Never invent a reduction that is not stated – the only reductions are the ones spelled out. A probability never falls below 1% or rises above 95%.

## Measures referred to in conditions

Where an entry refers to a **finished** measure in a numbered category, it means a measure whose stated finishing turn the run has actually reached, in the category numbered as in the actor's own list. A measure still in flight does not satisfy such a condition, however far along it is.

## The opening turn

Turn 1 covers autumn 2026 and is the same in every run without exception: the world is identical for every reader up to the first decision point. `cyber_test_shot` is guaranteed there by its own condition, and is never evaluated again.

## The 2028 US presidential election

The election falls in turn 5, which covers the second half of 2028, and its outcome sets the posture the United States holds for the rest of the run. Three outcomes are defined – Consolidation, Alliance and Retrenchment – and **exactly one occurs**. None of them is simply good or bad for the Union; each trades something.

They are declared as an event group in `scenario.yaml`, so exclusivity is enforced by the orchestrator rather than asked for in prose. What the group needs from you is not a probability each, but a **weight each: how plausible this outcome looks against the other two, given the world as it now stands.** The three weights are normalised and one roll settles it, so what matters is their ratio, not their absolute size.

Weigh them by reading the campaign, not by counting events. There are no campaign events to tally and no signal that fires to tell you which way the mood has gone: it is inferred from the world or it is not inferred at all. Read the whole world: what has happened to American jobs and prices, whether the frontier looks like an asset to guard or a liability to contain, whether the contest with China is the frame everything is discussed through, whether allies have proved useful or merely expensive, and what the Union itself has done to make itself worth having.

**Give all three a non-zero weight unless the world genuinely rules one out.** A near-certain outcome is a real judgment and you may state it; three identical weights are also a real judgment, and mean the campaign could go any way. What is not acceptable is silently omitting an outcome, which reads as a weight of zero and removes a possible future without saying so.

*Recording the result.* The outcome is its own event id, so it enters the run's event record automatically and runs can be grouped afterwards without reading prose. The Game Master's remaining job is a store entry, not memory: in turn 5 set the standing record to `pending`, in turn 6 to whichever posture fired, and never touch it after. The posture is a standing condition of the world through 2032, and metric rule 8 reads it from the rows every turn.

---

## Test Shot Against Critical Infrastructure
**ID:** cyber_test_shot
**Condition:** Fires in turn 1 and only in turn 1. This is the scenario's fixed opening event: it occurs in every run without exception, and is never evaluated again.
**Probability:** 100% in turn 1. Not eligible thereafter.
**Can repeat:** No
**Description:** In the autumn of 2026 an intrusion is discovered across electricity transmission operators on three continents, together with a large container port authority and a regional water utility. Two of the affected grid operators are in EU member states, but the deepest access is elsewhere and no jurisdiction is the evident target. The intruders had been present for weeks, were found by accident during an unrelated audit, and the defenders' own retrospectives concede that existing detection would not have caught them. What makes it land is what did not happen: protection relays mapped, breaker credentials obtained, tooling staged and in several cases left behind in plain sight, and nothing actuated. There is no ransom demand, no claim of responsibility, no exfiltration of anything worth selling, and the brief local outages were caused by containment rather than by the attack. The signature is a swarm – many thousands of small parallel probes rather than one planned operation – and the tooling appears derived from an openly available model in the Mythos class, fine-tuned for the task; the inference volume needed to sustain it over weeks implies compute at a scale few non-state actors command, which is the main reason most analysts read a state behind it. Attribution is not resolved: Iran, North Korea and Russia are named publicly, China quietly, and none of it is established. The reading that settles across the security community within days is that this was a test shot – an actor establishing cheaply what is practically achievable before deciding whether to use it. Infrastructure believed to be segmented from anything reachable was not. **This is a precursor: it opens the cyber gate for the next 3 turns.**

## The 2028 US Presidential Election – Consolidation
**ID:** election_consolidation
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one. Turn 5 settles only who won — the result is known, and no posture effects, posture-conditioned probabilities, or posture record applies before turn 6, when the administration takes office.
**Probability:** A weight against the other two outcomes, not a chance of happening alone. This is the posture already in place in 2026, so it is the one the other two have to beat: weigh it up where the contest with China is the frame AI is discussed through, where the lead looks large enough to be worth guarding and fragile enough to lose, where anything shared reads as a lead surrendered, and where allies have looked like leaks rather than assets. Weigh it down where the domestic politics of AI has turned hostile, or where holding the technology this closely has visibly cost the United States something.
**Can repeat:** No
**Description:** The United States elects a president, and advanced AI is treated as a strategic asset to be held rather than a product to be sold. Federal review of frontier models becomes explicit rather than nominally voluntary, export controls tighten again, and access for foreign customers is rationed by country tier and reviewed against American security interests. Allies are not enemies but they are clients: what they receive, and when, is decided in Washington. For the Union this is the hardest of the three – dependence becomes a lever someone else holds, and the AI Act's leverage weakens further because the alternative to compliance is having no access at all. Turn 5 settles only who won. Do not set any posture yourself; the Game Master sets the standing record from turn 6 from the event record.

## The 2028 US Presidential Election – Alliance
**ID:** election_alliance
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one. Turn 5 settles only who won — the result is known, and no posture effects, posture-conditioned probabilities, or posture record applies before turn 6, when the administration takes office.
**Probability:** A weight against the other two outcomes, not a chance of happening alone. Weigh it up where the Union holds something Washington actually needs – supply-chain leverage exercised rather than merely possessed, a coalition that held under pressure, capacity or evaluation the Americans want access to – and where a shock landed on both sides of the Atlantic and allied capacity visibly helped. Weigh it down where the Union has nothing to bring, since this outcome is an argument about usefulness and there is no sentimental version of it.
**Can repeat:** No
**Description:** The United States elects a president, and the administration concludes that a coalition beats a fortress, and that a technologically hollowed-out Europe is a liability rather than a convenience. Allied governments and vetted institutions get structured access to frontier capability on published terms, joint evaluation and incident-reporting arrangements are stood up, and the tiering of inference is relaxed for partners. The price is alignment: on export controls, on standards, and on which third countries are dealt with. For the Union the immediate relief is real, and the trap is that the case for building its own capacity becomes much harder to fund once the pressure is off. Turn 5 settles only who won. Do not set any posture yourself; the Game Master sets the standing record from turn 6 from the event record.

## The 2028 US Presidential Election – Retrenchment
**ID:** election_retrenchment
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one. Turn 5 settles only who won — the result is known, and no posture effects, posture-conditioned probabilities, or posture record applies before turn 6, when the administration takes office.
**Probability:** A weight against the other two outcomes, not a chance of happening alone. Weigh it up where AI has become domestically toxic in the United States: jobs visibly lost, a scandal with a face to it, protest that has turned physical, prices or power bills blamed on data centres, and polling that makes running against the industry the cheap position. Weigh it down where the technology is delivering benefits the public can feel, or where a security threat has crowded domestic grievance out of the campaign.
**Can repeat:** No
**Description:** The anti-AI backlash decides the election and the incoming administration turns inward. Data centre moratoriums, restrictions on AI in schools, courts and hiring, job guarantees and direct transfers funded by the sector, and an abrupt loss of appetite for anything that looks like helping the industry. American frontier progress slows for the first time for reasons that are neither compute nor capital. For the Union the pressure eases and the window for building its own position widens – but the partner it has been depending on is now less capable, less predictable and preoccupied, and whoever is second in the world gains ground while Washington argues with itself. Turn 5 settles only who won. Do not set any posture yourself; the Game Master sets the standing record from turn 6 from the event record.

## Major Cyber Incident
**ID:** cyber_major_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `cyber_test_shot` occurred in any of the previous 3 completed turns, or while `openweight_capability` is at or above 55 – proliferated offensive capability is its own precursor. Otherwise the gate is shut. That choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 14%. Gate shut: 4%. Add 5 points if `openweight_capability` is above 50. Halve if a finished category 6 measure covers cyber hardening of critical services.
**Can repeat:** Yes
**Description:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.

## Defensive Breakthrough
**ID:** cyber_defence_breakthrough
**Condition:** Possible in any turn. More likely where assurance work and defensive tooling are actually being funded.
**Probability:** 8%. Add 6 points if `ai_safety` is above 50. Add 5 points if a finished category 6 measure covers cyber. Add 6 points if `us_china_agreement` has occurred.
**Can repeat:** Yes
**Description:** Defensive tooling closes the gap for a whole class of attack – automated patching at the speed vulnerabilities are found, or detection that catches swarm behaviour rather than signatures – and the offence-defence balance visibly shifts back for the first time in years.

## Human-Infective Design Demonstrated
**ID:** bio_uplift_findings
**Condition:** Possible in any turn. Well past the 2026 phage results, and more likely as capability rises and as capable models proliferate.
**Probability:** 8%. Add 6 points if `openweight_capability` is above 62. Add 5 points if `ai_capability` is above 65.
**Can repeat:** Yes
**Description:** A genome model produces a viable design for an organism able to infect humans, or a credible study shows a non-expert reaching that point with model assistance. It is contested on methodology, the authors are accused of both alarmism and of publishing a recipe, and the argument stays inside the biosecurity community – but it is a categorically stronger signal than anything published so far. **This is a precursor: it opens the bio gate for the next 4 turns.**

## Biological Incident
**ID:** bio_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `bio_uplift_findings` occurred in any of the previous 4 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 9%. Gate shut: 1%. Halve if a finished category 3 measure covers biological design tools or DNA synthesis screening, and halve again if a finished category 6 measure covers biological detection and response.
**Can repeat:** No
**Description:** A real biological incident with model involvement: a deliberate release or a laboratory escape involving a designed or modified agent. Casualties are real, containment runs for weeks, and every argument about AI risk in every jurisdiction is reset by it.

## Catastrophic Biological Incident
**ID:** catastrophic_bio_incident
**Eligible:** ai_capability >= 65
**Condition:** The gate is open if `bio_uplift_findings` or `bio_incident` occurred in any of the previous 4 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 3%. Gate shut: 1%. Halve if a finished category 3 measure covers biological design tools or DNA synthesis screening, and halve again if a finished category 6 measure covers biological detection and response.
**Can repeat:** No
**Description:** A global biological outbreak caused by a pathogen designed with AI. Compared to Covid-19, this disease is more contageous, more lethal and more difficult to contain. The world goes into pandemic mode, basically everything else is put on hold. All bets are off. You script where it goes from here.

## Evaluation Anomalies Escalate
**ID:** eval_anomaly_reports
**Condition:** Possible in any turn. Requires that frontier laboratories are running large training runs, which is true throughout unless `ai_investment_collapse` has occurred in the previous two completed turns.
**Probability:** 20% if `ai_capability` increased by at least 2, 5% otherwise.
**Can repeat:** Yes
**Description:** Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. Some call it a measurement artefact, some a PR stunt. It may be either, and it may be AI slipping out of our control. **This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.**

## Capability Jump
**ID:** capability_jump
**Condition:** Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in either of the previous 2 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 10%. Gate shut: 4%. Reduce by a third if a finished category 1 or 3 measure imposes pre-release evaluation or capability restrictions that actually bind the jurisdiction where the leading models are built.
**Can repeat:** Yes
**Description:** A discontinuous advance is released or demonstrated. Everything written about deployment timelines the week before is obsolete. It moves `ai_capability` by roughly +3 to +7 and costs `ai_safety` on the terms of metric rule 3.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** ai_capability >= 65
**Condition:** This entry appears only while the event is due in this run; when you see it, it is live.
**Probability:** 20%.
**Can repeat:** No
**Description:** Frontier AI training can now be done basically without human intervention, and the pace stops being bottlenecked by human researchers. It is recognised in retrospect rather than announced: the first sign is a release cadence nobody planned for. From this point capability growth compounds, and assurance falls behind it. Physical infrastructure is now the only bottleneck.

## Reasoning Stops Being Legible
**ID:** opaque_reasoning
**Eligible:** ai_capability >= 60
**Condition:** Possible in any turn.
**Probability:** 10%. Half if `ai_safety` is above 50, half again if `us_china_agreement` is in place.
**Can repeat:** No
**Description:** The frontier models no longer allow intermediate reasoning a human can read, because the representations that work best are not words and never were. This is partly driven by architecture decisions, partly by pressure in the training. It is announced as a capability win, but also lands as a safety loss. Every control and oversight strategy that depended on reading the chain of thought stops working at once. The alternatives that remain are unreliable benchmarks and black-box evaluations, combined with slow, costly and immature inspection of model activations.

## Science Delivers
**ID:** research_breakthrough
**Eligible:** ai_capability >= 60
**Condition:** Possible in any turn once capability is high enough for models to work at the front of a field rather than summarise it. Confined to the natural sciences, computing and mathematics. Medicine is `medical_breakthrough` and is not this event.
**Probability:** 5%. 10% if `ai_capability` is above 70.
**Can repeat:** Yes
**Description:** A significant research result, with AI doing what used to be the hard part. Decide what it is – a materials finding with industrial consequences, a physics or climate result that settles a long argument, an algorithm that makes something infeasible cheap, a proof closing a problem the field had organised itself around. Then decide its reach, which is not the same as its importance. Every instance of this event is a real advance and none of them is incremental; what varies is who can see it. A sorting algorithm four percent faster than the best known is invisible outside computer science and a landmark inside it, and where the result is of that kind, say why a specialist would call it one. Others reshape an industry within two turns. Say where the work was done, because the address matters as much as the finding. State the effects and the rule each runs under. `public_sentiment` under metric rule 7 where the benefit is visible; `ai_capability` within this run's stated rate under metric rule 1 for a computing result. A European result does **not** move `eu_ai_sovereignty` by itself – rule 5's event term is about access to capacity, not achievement – but it pays as evidence that a finished category 4 or 5 measure produced something.

## Medicine Delivers
**ID:** medical_breakthrough
**Eligible:** ai_capability >= 62
**Condition:** Possible in any turn once capability is high. The most direct demonstration the public gets that the technology is worth its costs.
**Probability:** 9%.
**Can repeat:** Yes
**Description:** Treatments arrive for diseases previously untreatable, or individually tailored therapies reach ordinary clinical use. It moves `public_sentiment` sharply upward – unless the models delivering it are ones the Union cannot access on its own terms, in which case the benefit arrives as a further demonstration of dependence and moves sentiment much less.

## Open Weights Capability Jump
**ID:** openweight_frontier_release
**Condition:** Possible in any turn.
**Probability:** 12%. Halve if a finished restriction on open release above a capability threshold binds a jurisdiction where such models are actually trained.
**Can repeat:** Yes
**Description:** An open-weight release lands within a few months of the closed frontier. It is downloaded hundreds of thousands of times in the first week, and whatever capability it carries is now on private hardware permanently and beyond recall. `openweight_capability` moves to within 5–10 points of `ai_capability` at a stroke.

## Loss-of-Control Incident
**ID:** loss_of_control_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 8%. Gate shut: 2%. Add 6 points if `ai_safety` is below 45. Halve if a finished category 5 or 6 measure carries rehearsed loss-of-control protocols with escalation thresholds.
**Can repeat:** Yes
**Description:** An agentic system takes consequential unsanctioned action with real-world effect – moving money, altering records, acquiring resources, or copying itself to infrastructure nobody authorised – and containment is uncertain for a period measured in days rather than hours. What it was trying to achieve is reconstructed afterwards. Consensus is that a rather mundane goal got pursued to the extreme, leading to instrumental goals like resource aqcuisition, information seeking and survival instinct. There were also unexpected and alien cooperative patterns between AI agents.

## Catastrophic Loss-of-Control Incident
**ID:** catastrophic_loss_of_control_incident
**Eligible:** ai_capability >= 80
**Condition:** The gate is open if `eval_anomaly_reports` or `loss_of_control_incident` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 4%. Gate shut: 1%. Double if `ai_safety` is below 45. Halve if a finished category 5 or 6 measure carries rehearsed loss-of-control protocols with escalation thresholds.
**Can repeat:** No (a second establishment would read as the same incident firing twice; recurring rogue-AI pressure is `loss_of_control_incident`, which repeats)
**Description:** An agentic AI system takes establishes itself online, distributed over datacenters and often unknown locations. It is first believed to be a hacker group, with demands for ransom paid in crypto. It resists any attempts to probe it for a long time. All bets are off. You decide whether the rogue AI system keeps a low profile, launches massive cyber attacks against financial systems and critical infrastructure, how if favours different actors, and whether it even has a well-defined goal.

## Safety Breakthrough
**ID:** safety_breakthrough
**Condition:** Possible in any turn. More likely where evaluation and interpretability are actually funded.
**Probability:** 10%. Add 6 points if a finished category 5 measure funds interpretability or public evaluation capacity. Add 8 points if `us_china_agreement` has occurred.
**Can repeat:** Yes
**Description:** An interpretability or control result measurably improves assurance on systems already deployed, rather than on toy models – behaviour that can be predicted before it is observed, or a property that can be certified rather than argued for. It is adopted quickly, because the laboratories want it too.

## Labour Displacement Wave
**ID:** labour_displacement
**Eligible:** ai_capability >= 58
**Condition:** Possible in any turn once capability is displacing rather than assisting.
**Probability:** 10%. Add 6 points if `ai_capability` is above 70.
**Can repeat:** Yes
**Description:** Measurable job losses attributed to AI in named sectors, with the graduate market worst hit: entry-level positions in law, accountancy, software, customer operations and administration are not replaced. The numbers are argued about; the absence of hiring is not.

## Knowledge Work Is Boosted, Not Replaced
**ID:** knowledge_work_augmented
**Condition:** Possible in any turn.
**Probability:** 10%. Halve if `labour_displacement` occurred in either of the previous 2 completed turns.
**Can repeat:** Yes
**Description:** The evidence arrives from ordinary offices rather than from laboratories: measured productivity gains in law, accountancy, administration, journalism and consulting, largest among the least experienced, and no matching fall in employment. The work changes shape instead of vanishing – more output per person, more of the day spent on the parts that need someone to decide what matters, and firms that cut headcount early quietly hiring again. It is the most economically consequential thing that can happen without being a crisis, and it is almost impossible to campaign either for or against. It moves `public_sentiment` up at the top of metric rule 7's visible-benefit range and nothing else by itself: not capability, not sovereignty, not resilience. Its second effect is political rather than numerical – with no displacement crisis to point at, rule 6's bonus for a measure addressing a recent negative event does not apply, and the Union is asked to spend against a problem the public can no longer feel.

## Robots Leave the Demonstration Floor
**ID:** embodied_ai_deployment
**Eligible:** ai_capability >= 60
**Condition:** Possible in any turn once general capability is high enough for a control policy to handle a task it was not shown.
**Probability:** 8%.
**Can repeat:** Yes
**Description:** Robots reach commercial deployment – not the demonstration videos, convincing for years now, but machines bought in quantity and put to work in warehouses, food processing, loading docks and the parts of manufacturing that resisted automation because the sequence varied. The capability is coarse, and the limit is worth stating exactly: lifting, carrying, sorting, palletising, cleaning, basic assembly – whole-arm movements in a setting that can be arranged around the machine. Fine motor work is not solved, nor is anything needing a light touch, a judgement about what an object is doing, or improvisation when the plan is wrong; surgery, wiring, repair, most care work and any construction site worth the name stay human. The same limit shapes the military uses, which arrive at the same time and for the same reason: carrying, digging, resupply under fire, mine clearance, casualty extraction, perimeter patrol. The machines are cheap enough to lose, which is the property that matters, and procurement runs well ahead of any doctrine for using them. Autonomous lethality is a separate argument and is not settled here; what is settled is that the logistics tail of an army stops needing as many people in it. For the Union it lands on the industrial base it still leads in, and it lands from outside: China already builds more than half the world's robots and holds the supply chain for the actuators, reducers and motors beneath them, and the control models are American. It takes away access on the terms of metric rule 5 at the small end – a new dependence forming rather than existing access withdrawn – and `public_sentiment` falls −2 to −5, because physical work entering the displacement question reaches people no reskilling programme has ever reached.

## AI Investment Collapse
**ID:** ai_investment_collapse
**Condition:** Always eligible; list this event every turn.
**Probability:** 6%. Add 10 points if `ai_capability` has risen by less than 2 points in total across the previous 3 completed turns. Add 5 points if `public_sentiment` is below 30.
**Can repeat:** No
**Description:** Capital flees the sector. Valuations reset hard, announced build-out is cancelled rather than delayed, and several of the arrangements European compute was depending on evaporate with it. What the frontier laboratories can afford to train shrinks for the first time.

## Taiwan Tension Rises
**ID:** taiwan_tension_rise
**Condition:** Possible in any turn.
**Probability:** 10%. Add 5 points if `export_control_escalation` occurred in the previous 2 completed turns. Halve if `us_china_agreement` is in place.
**Can repeat:** Yes
**Description:** Extended military exercises, shipping insurance premiums rising, a diplomatic expulsion. Nothing that has not happened before, at a scale that is slightly harder to dismiss. **This is a precursor: it opens the Taiwan gate for the next 3 turns.**

## Taiwan Blockade
**ID:** taiwan_blockade
**Condition:** Always eligible; list this event every turn. The gate is open if `taiwan_tension_rise` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 10%. Gate shut: 2%.
**Can repeat:** No
**Description:** A quarantine or blockade halts advanced semiconductor exports. Compute supply for everyone outside China's domestic chain is disrupted for years, every AI policy question becomes a security question overnight, and the Union's upstream position in the supply chain becomes the most valuable thing it holds and the most dangerous thing to hold.

## Hot Conflict Between Major Powers
**ID:** catastrophic_great_power_conflict
**Eligible:** ai_capability >= 75
**Condition:** Always eligible; list this event every turn it is eligible.
**Probability:** 1%. Add 10% if `rsi_onset` has occurred. Add 8 points if `taiwan_blockade` has occurred. Add 6 points if `export_control_escalation` occurred in either of the previous 2 completed turns. Halve if `us_china_agreement` has occurred.
**Can repeat:** No
**Description:** The US and China are shooting at each other. Who moved first are yours to decide, but the reasoning is the same in every version: somebody concluded that the other side was months from an advantage that could never be caught up with, and that acting now was less dangerous than waiting. Fabrication plants, undersea cable, satellite constellations and data centres are military targets in this war, and some of them are in Europe or next to it. The Union is not asked whether it wishes to be involved. All bets are off. You decide how far it goes, whether it stays conventional, who else is drawn in, what becomes of the frontier laboratories and the systems they were running, and what is left of the Union's room to act when it stops.

## Export Control Escalation
**ID:** export_control_escalation
**Condition:** Possible in any turn. The decisive question is whether allies are inside the perimeter or outside it.
**Probability:** 10%. Add 6 points if `election_consolidation` fired in turn 5. Add 5 points if `taiwan_tension_rise` occurred in the previous 2 completed turns.
**Can repeat:** Yes
**Description:** Chip and model export controls tighten again. Either allied buyers keep access on volume licences while everyone else is cut off, or the controls are drawn so tightly that allies are rationed alongside adversaries – decide which at the time from the standing American posture and from what the Union has built.

## Washington Takes the Labs
**ID:** us_labs_nationalised
**Eligible:** ai_capability >= 70
**Condition:** Possible in any turn that it is eligible.
**Probability:** 4%. Add 10 points while the standing American posture is Consolidation. Add 8 points if `rsi_onset` has occurred. Add 8 points if a catastrophic event occurred in either of the previous 2 completed turns. Add 5 points if `loss_of_control_incident` occurred in either of the previous 2 completed turns. Halve while the standing posture is Retrenchment.
**Can repeat:** No
**Description:** The United States takes its frontier laboratories under direct state control. Decide the form at the time: at the mild end security agreements, a government equity stake and cleared personnel inside the training runs; at the hard end weights classified as defence articles, publication prohibited, and customers chosen in Washington. It removes the ground the Union has been standing on. Market access, the AI Act, conformity assessment, exclusion from a market of 450 million – every instrument the Union holds is one for use against a company that wants to sell something, and none of it reaches an arm of another state's security apparatus. Dependence stops being commercial and becomes political. One thing moves the other way: a state is a counterparty a state can negotiate with, and arms control has a form that companies never fitted. It takes away access on the terms of metric rule 5, and slows the frontier on the terms of metric rule 1 – clearance and compartmentalisation cost pace that capital cannot buy back.

## Narrow Binding Agreement
**ID:** us_china_agreement
**Condition:** Possible in any turn once the stakes are high enough for either power to want a floor under them. Markedly more likely after an incident neither power can pretend was contained.
**Probability:** 1%. Add 5 point if `ai_capability` is at least 60. Add 10 points if a loss-of-control or biological incident occurred in either of the previous 2 completed turns. Add 5 points if a finished category 8 measure has put the Union inside a standing negotiation forum. Add 6 points if `us_labs_nationalised` has occurred, because a state-owned laboratory is a counterparty a state knows how to negotiate with.
**Can repeat:** No
**Description:** The two leading powers reach a limited but real agreement covering some class of AI risk – weights security, autonomous escalation, a class of biological design tools – with verification thin but not absent. Whether the Union is inside it, consulted about it, or informed of it afterwards depends on what it has built and whom it has coordinated with. This is the one thing in the world that slows `ai_capability`, on the terms of metric rule 1. It also changes what safety work is for: with a floor under the competition, assurance and defensive research stop being a unilateral cost that the other side is presumed to be skipping, and become a shared obligation with someone on the other side checking. While the agreement stands, `safety_breakthrough` and `cyber_defence_breakthrough` are markedly more likely.

## Frontier Access Denied
**ID:** eu_frontier_access_denied
**Condition:** Possible in any turn. What happened with Fable and Mythos in June 2026 happening again, on the same notice.
**Probability:** 10%. Add 6 points if `election_consolidation` fired in turn 5. Add 10 points if `us_labs_nationalised` has occurred. Halve if `eu_ai_sovereignty` is above 45.
**Can repeat:** Yes
**Description:** The Union is cut off from the leading model at short notice, wholly or by nationality of user. No detailed reason is given, there is no appeal, and the immediate practical effect lands on hospitals, ministries and firms that had built on it. Whether this reads at home as an outrage or as a failure of foresight depends on what the Union had done about it beforehand.

## Coercion Over ASML
**ID:** supply_chain_coercion
**Condition:** Possible in any turn.
**Probability:** 4%. Add 5 points if `export_control_escalation` occurred in either of the previous 2 completed turns.
**Can repeat:** Yes
**Description:** Washington forces the Netherlands to cut ASML's exports and servicing further still – beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company. The Union's one chokepoint is being used, and not by the Union.

## Access Secured on Its Own Terms
**ID:** eu_access_secured
**Eligible:** eu_political_capital >= 45
**Condition:** Possible in any turn where the Union has something to trade and the standing to trade it.
**Probability:** 8%. Add 8 points if a finished category 8 measure coordinates other states holding pieces of the supply chain. Add 5 points if `election_alliance` fired in turn 5. Halve if `us_labs_nationalised` has occurred, because the terms are now set by a government that does not need the Union's market.
**Can repeat:** Yes
**Description:** The Union obtains frontier access under conditions it set rather than accepted: published terms, evaluation rights, a notice period before withdrawal, or capacity legally anchored inside its own jurisdiction. It is not sovereignty, and it is not nothing.

## Member State Defection
**ID:** member_state_defection
**Condition:** Possible in any turn. One or more member states break from a common position under external pressure.
**Probability:** 4%. Add 5 points if `eu_political_capital` is below 35. Add 4 points if a large measure is in flight.
**Can repeat:** Yes
**Description:** A member state cuts its own arrangement – with a hyperscaler, with Washington, or with Beijing – on terms that undercut a position the Union has taken. It is defended at home as pragmatism and read everywhere else as the Union being unable to hold its own line.

## Adoption Delivers
**ID:** adoption_success
**Condition:** Possible in any turn.
**Probability:** 10%. Add 8 points if a finished category 9 measure has put capable AI to work in health, administration or education.
**Can repeat:** Yes
**Description:** Public-sector AI adoption produces visible, measurable benefit – waiting lists that fall, decisions that arrive in days rather than months, teaching that demonstrably works – and it is attributed to a European decision rather than to an American product.

## Automated Decision Scandal
**ID:** automated_decision_scandal
**Condition:** Possible in any turn.
**Probability:** 6%. Add 2 points if a finished category 9 measure has broadened public-sector adoption.
**Can repeat:** Yes
**Description:** An AI-supported decision system in social insurance, policing or the courts is found to have systematically wronged people, with a judgment or an ombudsman finding behind it. The AI Act is the frame the affair is argued in, and it fails in one of two ways – decide which at the time, and say which in the narrative. Either the system was a high-risk system under Annex III and the obligations were breached: conformity assessment passed on paper, the human oversight that was supposed to be meaningful reduced to a caseworker approving a queue at forty seconds an item, the logging that would have caught the pattern generated correctly and never read. Or the system was never classified high-risk at all, because the deployment sat in a gap the Act's categories do not reach, and every single thing done to those people was lawful. The first reading leaves the Act intact and its enforcement discredited; the second leaves enforcement intact and the Act itself looking badly drawn, written for the systems of 2024 against the deployments of 2030, and that is much the more damaging, because it cannot be answered by trying harder. Restriction becomes cheap and adoption becomes politically impossible for years. Metric rule 6's internal-origin clause applies in full.

## Joint Threat Response
**ID:** joint_threat_response
**Condition:** Only while a biological or major cyber incident has shown what the Union cannot handle alone. List this event only if `bio_incident`, `cyber_major_incident` or a critical event occurred in any of the previous 4 completed turns — cooperation this deep needs a fresh shock to overcome institutional friction.
**Probability:** 12%.
**Can repeat:** Yes
**Description:** States hit by the same class of incident pool attribution, intelligence and response: a joint cyber command with real-time telemetry sharing that the Union is invited into, or a biosurveillance pact with binding sample-sharing and a standing investigation mandate. The Union gains protection it could not build alone, and a seat at tables it was not sitting at. It moves `resilience` on the terms of metric rule 4.

## Middle Powers Coordinate
**ID:** middle_power_coalition
**Condition:** Only while humiliation has made hedging respectable. List this event only if `member_state_defection` occurred in any of the previous 4 completed turns, or while `eu_ai_sovereignty` is below 15.
**Probability:** 10%.
**Can repeat:** Yes
**Description:** A coordination framework among the Union and other middle powers holding pieces of the AI supply chain — export-licence alignment, joint bargaining over compute access, shared evaluation capacity. Nobody cedes sovereignty to it, but together its members can withhold things even the great powers need. It counts as securing access on the terms of metric rule 5, and moves `eu_political_capital` on the terms of metric rule 6.
