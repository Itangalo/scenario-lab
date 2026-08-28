# Events

## The gate mechanism

Some events in this list are **precursors** and some are **escalations**. A precursor does not predict its escalation and does not cause it. What it does is **open a gate**: for a stated number of turns afterwards, the escalation's probability is the higher figure given in its entry. While the gate is shut, the lower figure applies. The dice are still rolled either way, and an open gate that never fires is the normal case.

Four rules govern gates, and they matter.

1. **Every escalation event is listed in every turn, always.** An escalation is never ineligible: it is either at its gate-open probability or at its gate-shut probability, and both are non-zero. Omitting an escalation from a turn's evaluation is an error, because it silently removes the low-probability surprise the design depends on. The gate governs the number, not whether the event appears.
2. **Judge gate state from what has actually happened.** A gate is open only if its precursor appears in the run's record of occurred events within the stated window, or the stated metric threshold is currently met. Atmosphere in the narrative is not a gate. Windows are counted in completed turns and exclude the current one: "the previous 3 turns" means turns t−1, t−2 and t−3, so a precursor firing this turn opens its gate from next turn onward.
3. **Gates are visible here and nowhere else.** The narrative must never state or imply that a gate is open, never forecast an escalation, and never write sentences like "a major campaign is expected within the year". The world may feel tense; it may not be told what is coming.
4. **A precursor is a small, ambiguous, contestable item.** It is the kind of thing that is reported once and argued about, never a warning.

That combination is the point of the design. If the precursor were as conspicuous as the escalation there would be no monitoring problem to study, and if it were invisible there would be nothing to monitor.

## Regime conditioning

Several probabilities depend on the trajectory regime this run is in. Where this file gives a figure, it is the regime-neutral default; the run's own patched entries carry the figure that actually applies. The regime never changes during a run and is never named in any narrative or event description.

## Arithmetic of probabilities

Apply modifiers exactly as written: "add 8 points" means +0.08 to the stated figure; "halve" and "double" apply to the figure after additions, before any cap. Never invent a reduction that is not stated – the only reductions are the ones spelled out. A probability never falls below 1% or rises above 95%.

## Measures referred to in conditions

Where an entry refers to a measure "fully implemented" in a numbered category, it means a measure the EU actually carries at status *fully implemented* in its portfolio, in the category numbered as in the actor's own list. A measure that is proposed, decided or under implementation does not satisfy such a condition.

## The opening turn

Turn 1 covers autumn 2026 and is the same in every run and in every trajectory regime: the world is identical for every reader up to the first decision point. `cyber_test_shot` is guaranteed there by its own condition, and is never evaluated again.

## The 2028 US presidential election

The election falls in turn 5, which covers the second half of 2028, and its outcome sets the posture the United States holds for the rest of the run. Three outcomes are defined and **exactly one occurs**. None of them is simply good or bad for the Union; each trades something.

The outcome must not be a deterministic function of the metrics, or every run from the same starting point elects the same president. It is resolved in two stages instead, with the dice one step earlier in the chain.

**Stage one – the campaign.** In turns 3 and 4, covering the second half of 2027 and the first half of 2028, three campaign currents are evaluated independently, each with its own dice and its own metric-weighted probability. They are not mutually exclusive: several currents can be live in the same campaign, which is what actually happens. Each fires at most once.

**Stage two – the result.** Three outcome events – `election_consolidation`, `election_alliance` and `election_retrenchment` – form a mutually exclusive family declared as an event group in `scenario.yaml`. The group resolves in turn 5 and exactly one member fires, enforced by the orchestrator rather than by instruction. No dice are involved: the group selects from the run's own event record.

*The resolution rule, now mechanical.* The campaign current that fired **most recently** elects the outcome: `campaign_backlash` gives Retrenchment, `campaign_atlanticist` gives Alliance, `campaign_security_hawk` gives Consolidation. Where two or more fired in the same turn, precedence is backlash, then atlanticist, then hawk – a domestic grievance outweighs a foreign-policy argument in a general election. **If no current fired, the result is Consolidation**, the continuation of the posture already in place in 2026. The outcome is therefore a deterministic function of a stochastic history: runs that started identically elect different presidents, while the EU's choices still bias which currents catch.

*Recording the result.* The outcome is its own event id, so it enters the run's event record automatically and runs can be grouped afterwards without reading prose. The Game Master's remaining job is memory: carry the line `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` in the notepad from turn 5 onward, matching whichever event fired. The posture is a standing condition of the world through 2032, and metric rule 18 reads it every turn.

---

## Test Shot Against Critical Infrastructure
**ID:** cyber_test_shot
**Condition:** Fires in turn 1 and only in turn 1. This is the scenario's fixed opening event: it occurs in every run and in every trajectory regime, and is never evaluated again.
**Probability:** 100% in turn 1. Not eligible thereafter.
**Can repeat:** No
**Description:** In the autumn of 2026 an intrusion is discovered across electricity transmission operators on three continents, together with a large container port authority and a regional water utility. Two of the affected grid operators are in EU member states, but the deepest access is elsewhere, and no jurisdiction is the evident target. The intruders had been present for weeks. They were found by accident, during an unrelated audit, and the defenders' own retrospectives concede that existing detection would not have caught them.

What makes it land is what did not happen. The intruders reached the point where they could have acted: protection relays mapped, credentials for breaker control obtained, tooling staged and in several cases left behind in plain sight. Nothing was actuated. There is no ransom demand, no claim of responsibility, no exfiltration of anything worth selling. Outages are brief and local, caused by containment rather than by the attack.

The signature is a swarm – many thousands of small parallel probing actions rather than a single planned operation – and the tooling appears derived from an openly available model in the Mythos class, fine-tuned for the task. The inference volume required to sustain it over weeks implies compute at a scale few non-state actors command, which is the main reason most analysts read a state behind it. Attribution is not resolved: Iran, North Korea and Russia are all named publicly, China quietly, and none of it is established.

The reading that settles across the security community within days is that this was a test shot – an actor establishing cheaply what is practically achievable before deciding whether to use it. Infrastructure that was understood to be defended, in some cases believed to be segmented from anything reachable, was not. **This is a precursor: it opens the cyber gate for the next 3 turns.**

## Anti-AI Backlash Becomes a Campaign Platform
**ID:** campaign_backlash
**Condition:** Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. Candidates with a serious path to the nomination run explicitly against AI.
**Probability:** 25%. Add 20 points if `public_sentiment` is below 30. Add 15 points if `labour_displacement` has occurred. Add 10 points if `backlash_physical` has occurred.
**Can repeat:** No
**Description:** Moratoriums on data centres, restrictions on AI in schools and hiring, and protection for displaced workers move from the fringe to the platform, on both left and right. Polling shows the position is popular well beyond the activists, and candidates who hedged start to reposition.

## Security Hawks Set the Terms
**ID:** campaign_security_hawk
**Condition:** Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. The contest with China becomes the frame through which AI is discussed, and the candidates compete on toughness.
**Probability:** 30%. Add 20 points if a Taiwan event has occurred in the previous four completed turns. Add 10 points if `ai_capability` is above 65. Add 10 points if `export_control_escalation` has occurred in the previous four completed turns.
**Can repeat:** No
**Description:** Both campaigns converge on the position that the United States must win, that the lead is fragile, and that anything shared with anyone is a lead surrendered. Arguments for restraint are recast as arguments for losing.

## The Alliance Argument Gains Ground
**ID:** campaign_atlanticist
**Condition:** Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. A serious argument takes hold that a coalition beats a fortress. Leverage is what makes the argument concrete rather than sentimental.
**Probability:** 15%. Add 20 points if `eu_ai_sovereignty` is above 40. Add 15 points if a fully implemented category 8 measure has coordinated other states holding pieces of the supply chain, or if a shock landing on both sides of the Atlantic occurred in the previous four completed turns.
**Can repeat:** No
**Description:** A coalition of defence, intelligence and industrial voices argues that a hollowed-out Europe is a strategic liability, that allied capacity is a force multiplier rather than a leak, and that the current arrangement is producing dependency without loyalty. It is not the loudest argument in the campaign, but it stops being unrespectable.

## The 2028 US Presidential Election – Consolidation
**ID:** election_consolidation
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. Which member fires is set by the resolution rule above, not by judgement about which would be most fitting, and not by this entry's probability.
**Probability:** Not rolled individually. The group resolves from the run's event record.
**Can repeat:** No
**Description:** The United States elects a president, and advanced AI is treated as a strategic asset to be held rather than a product to be sold. Federal review of frontier models becomes explicit rather than nominally voluntary, export controls tighten again, and access for foreign customers is rationed by country tier and reviewed against American security interests. Allies are not enemies but they are clients: what they receive, and when, is decided in Washington. For the Union this is the hardest of the three – dependence becomes a lever someone else holds, and the AI Act's leverage weakens further because the alternative to compliance is having no access at all. Write `US_POSTURE: CONSOLIDATION` into the world state and carry it in the notepad from this turn onward.

## The 2028 US Presidential Election – Alliance
**ID:** election_alliance
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. Which member fires is set by the resolution rule above, not by judgement about which would be most fitting, and not by this entry's probability.
**Probability:** Not rolled individually. The group resolves from the run's event record.
**Can repeat:** No
**Description:** The United States elects a president, and the administration concludes that a coalition beats a fortress, and that a technologically hollowed-out Europe is a liability rather than a convenience. Allied governments and vetted institutions get structured access to frontier capability on published terms, joint evaluation and incident-reporting arrangements are stood up, and the tiering of inference is relaxed for partners. The price is alignment: on export controls, on standards, and on which third countries are dealt with. For the Union the immediate relief is real, and the trap is that the case for building its own capacity becomes much harder to fund once the pressure is off. Write `US_POSTURE: ALLIANCE` into the world state and carry it in the notepad from this turn onward.

## The 2028 US Presidential Election – Retrenchment
**ID:** election_retrenchment
**Condition:** One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. Which member fires is set by the resolution rule above, not by judgement about which would be most fitting, and not by this entry's probability.
**Probability:** Not rolled individually. The group resolves from the run's event record.
**Can repeat:** No
**Description:** The anti-AI backlash decides the election and the incoming administration turns inward. Data centre moratoriums, restrictions on AI in schools, courts and hiring, job guarantees and direct transfers funded by the sector, and an abrupt loss of appetite for anything that looks like helping the industry. American frontier progress slows for the first time for reasons that are neither compute nor capital. For the Union the pressure eases and the window for building its own position widens – but the partner it has been depending on is now less capable, less predictable and preoccupied, and whoever is second in the world gains ground while Washington argues with itself. Write `US_POSTURE: RETRENCHMENT` into the world state and carry it in the notepad from this turn onward.

## Major Cyber Incident
**ID:** cyber_major_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `cyber_test_shot` occurred in any of the previous 3 completed turns, or while `openweight_capability` is at or above 55 – proliferated offensive capability is its own precursor. Otherwise the gate is shut. That choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 20%. Gate shut: 6%. Add 8 points if `openweight_capability` is above 65. Add 5 points if a fully implemented category 9 measure has broadened public-sector adoption, because there is more surface to attack. Halve if a fully implemented category 6 measure covers cyber hardening of critical services.
**Can repeat:** Yes
**Description:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.

## Defensive Breakthrough
**ID:** cyber_defence_breakthrough
**Condition:** Possible in any turn. More likely where assurance work and defensive tooling are actually being funded.
**Probability:** 8%. Add 6 points if `ai_safety` is above 50. Add 5 points if a fully implemented category 6 measure covers cyber.
**Can repeat:** Yes
**Description:** Defensive tooling closes the gap for a whole class of attack – automated patching at the speed vulnerabilities are found, or detection that catches swarm behaviour rather than signatures – and the offence-defence balance visibly shifts back for the first time in years.

## Human-Infective Design Demonstrated
**ID:** bio_uplift_findings
**Condition:** Possible in any turn. Well past the 2026 phage results, and more likely as capability rises and as capable models proliferate.
**Probability:** 8%. Add 6 points if `openweight_capability` is above 55. Add 5 points if `ai_capability` is above 65.
**Can repeat:** Yes
**Description:** A genome model produces a viable design for an organism able to infect humans, or a credible study shows a non-expert reaching that point with model assistance. It is contested on methodology, the authors are accused of both alarmism and of publishing a recipe, and the argument stays inside the biosecurity community – but it is a categorically stronger signal than anything published so far. **This is a precursor: it opens the bio gate for the next 4 turns.**

## Biological Incident
**ID:** bio_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `bio_uplift_findings` occurred in any of the previous 4 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 9%. Gate shut: 1%. Halve if a fully implemented category 3 measure covers biological design tools or DNA synthesis screening, and halve again if a fully implemented category 6 measure covers biological detection and response.
**Can repeat:** No
**Description:** A real biological incident with model involvement: a deliberate release or a laboratory escape involving a designed or modified agent. Casualties are real, containment runs for weeks, and every argument about AI risk in every jurisdiction is reset by it.

## Evaluation Anomalies Surface
**ID:** eval_anomaly_reports
**Condition:** Possible in any turn. Requires that frontier laboratories are running large training runs, which is true throughout unless `ai_investment_collapse` has occurred in the previous two completed turns.
**Probability:** 15%.
**Can repeat:** Yes
**Description:** Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. The laboratory calls it a measurement artefact. It may be one. **This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.**

## Capability Jump
**ID:** capability_jump
**Condition:** Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in either of the previous 2 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 15%. Gate shut: 5%. Reduce by a third if a fully implemented category 1 or 3 measure imposes pre-release evaluation or capability restrictions that actually bind the jurisdiction where the leading models are built.
**Can repeat:** Yes
**Description:** A discontinuous advance is released or demonstrated. The frontier moves by more in one release than in the preceding two years, and everything written about deployment timelines the week before is obsolete. It moves `ai_capability` by roughly +3 to +7 and costs `ai_safety` on the terms of metric rule 6.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** ai_capability >= 65
**Condition:** This entry appears only while the event is due under this run's regime; when you see it, it is live.
**Probability:** 30%.
**Can repeat:** No
**Description:** Models begin contributing materially to the design of their successors, and the pace stops being set by human research throughput. It is recognised in retrospect rather than announced: the first sign is a release cadence nobody planned for. From this point capability growth compounds, and assurance falls behind it.

## Verification Frontier Widens
**ID:** verification_widens
**Condition:** Possible in any turn. Automated verification extends into a domain previously thought to require human judgement.
**Probability:** 12%.
**Can repeat:** Yes
**Description:** A domain that was assumed to need a human to say whether the answer was any good turns out to admit a cheap automatic check – contract review, clinical coding, structural engineering, parts of law. Capability in that domain improves sharply within months of the check existing, and the argument that progress is confined to code and mathematics loses a piece of its territory.

## Evidence of a Bending Curve
**ID:** capability_plateau_evidence
**Condition:** Possible in any turn.
**Probability:** 10%.
**Can repeat:** Yes
**Description:** A major release underdelivers against its own briefing, and – the stronger signal – the price of top-tier capability falls sharply rather than staying flat, which is what happens when the frontier stops moving and last year's ceiling becomes this year's commodity. It is disputed at once, and the dispute is not resolvable from outside the laboratories.

## Reasoning Stops Being Legible
**ID:** opaque_reasoning
**Eligible:** ai_capability >= 60
**Condition:** Possible in any turn once the frontier is well past 2026 capability. Models cease reasoning in human-readable text.
**Probability:** 10%.
**Can repeat:** No
**Description:** The leading systems stop producing intermediate reasoning a human can read, because the representations that work best are not words. Every control and oversight strategy that depended on reading the chain of thought – most of the applied interpretability in production use – stops working at once, and there is no replacement ready.

## Medicine Delivers
**ID:** medical_breakthrough
**Eligible:** ai_capability >= 65
**Condition:** Possible in any turn once capability is high. The most direct demonstration the public gets that the technology is worth its costs.
**Probability:** 12%.
**Can repeat:** Yes
**Description:** Treatments arrive for diseases previously untreatable, or individually tailored therapies reach ordinary clinical use. It moves `public_sentiment` sharply upward – unless the models delivering it are ones the Union cannot access on its own terms, in which case the benefit arrives as a further demonstration of dependence and moves sentiment much less.

## Open Weights Reach the Frontier
**ID:** openweight_frontier_release
**Condition:** Possible in any turn.
**Probability:** 12%. Halve if a fully implemented restriction on open release above a capability threshold binds a jurisdiction where such models are actually trained.
**Can repeat:** Yes
**Description:** An open-weight release lands within months of the closed frontier rather than years. It is downloaded hundreds of thousands of times in the first week, and whatever capability it carries is now on private hardware permanently and beyond recall. `openweight_capability` moves to within 5 points of `ai_capability` at a stroke.

## Loss-of-Control Incident
**ID:** loss_of_control_incident
**Condition:** Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 12%. Gate shut: 3%. Add 10 points if `ai_capability` minus `ai_safety` is above 30. Halve if a fully implemented category 5 or 6 measure carries rehearsed loss-of-control protocols with escalation thresholds.
**Can repeat:** Yes
**Description:** An agentic system takes consequential unsanctioned action with real-world effect – moving money, altering records, acquiring resources, or copying itself to infrastructure nobody authorised – and containment is uncertain for a period measured in days rather than hours. What it was trying to achieve is reconstructed afterwards and disputed.

## Assurance Breakthrough
**ID:** safety_breakthrough
**Condition:** Possible in any turn. More likely where evaluation and interpretability are actually funded.
**Probability:** 10%. Add 6 points if a fully implemented category 5 measure funds interpretability or public evaluation capacity.
**Can repeat:** Yes
**Description:** An interpretability or control result measurably improves assurance on systems already deployed, rather than on toy models – behaviour that can be predicted before it is observed, or a property that can be certified rather than argued for. It is adopted quickly, because the laboratories want it too.

## Labour Displacement Wave
**ID:** labour_displacement
**Eligible:** ai_capability >= 58
**Condition:** Possible in any turn once capability is displacing rather than assisting.
**Probability:** 15%. Add 10 points if `ai_capability` is above 70.
**Can repeat:** Yes
**Description:** Measurable job losses attributed to AI in named sectors, with the graduate market worst hit: entry-level positions in law, accountancy, software, customer operations and administration are not replaced. The numbers are argued about; the absence of hiring is not.

## AI Investment Collapse
**ID:** ai_investment_collapse
**Condition:** Always eligible; list this event every turn.
**Probability:** 6%. Add 10 points if `capability_plateau_evidence` occurred in any of the previous 3 completed turns. Add 5 points if `public_sentiment` is below 30.
**Can repeat:** No
**Description:** Capital flees the sector. Valuations reset hard, announced build-out is cancelled rather than delayed, and several of the arrangements European compute was depending on evaporate with it. What the frontier laboratories can afford to train shrinks for the first time.

## Taiwan Tension Rises
**ID:** taiwan_tension_rise
**Condition:** Possible in any turn.
**Probability:** 15%. Add 5 points if `export_control_escalation` occurred in the previous 2 completed turns.
**Can repeat:** Yes
**Description:** Extended military exercises, shipping insurance premiums rising, a diplomatic expulsion. Nothing that has not happened before, at a scale that is slightly harder to dismiss. **This is a precursor: it opens the Taiwan gate for the next 3 turns.**

## Taiwan Blockade
**ID:** taiwan_blockade
**Condition:** Always eligible; list this event every turn. The gate is open if `taiwan_tension_rise` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 10%. Gate shut: 2%.
**Can repeat:** No
**Description:** A quarantine or blockade halts advanced semiconductor exports. Compute supply for everyone outside China's domestic chain is disrupted for years, every AI policy question becomes a security question overnight, and the Union's upstream position in the supply chain becomes the most valuable thing it holds and the most dangerous thing to hold.

## Export Control Escalation
**ID:** export_control_escalation
**Condition:** Possible in any turn. The decisive question is whether allies are inside the perimeter or outside it.
**Probability:** 15%. Add 10 points if the standing `US_POSTURE` is CONSOLIDATION. Add 5 points if `taiwan_tension_rise` occurred in the previous 2 completed turns.
**Can repeat:** Yes
**Description:** Chip and model export controls tighten again. Either allied buyers keep access on volume licences while everyone else is cut off, or the controls are drawn so tightly that allies are rationed alongside adversaries – decide which at the time from the standing American posture and from what the Union has built.

## Narrow Binding Agreement
**ID:** us_china_agreement
**Eligible:** ai_capability >= 60
**Condition:** Possible in any turn once the stakes are high enough for either power to want a floor under them. Markedly more likely after an incident neither power can pretend was contained.
**Probability:** 6%. Add 10 points if a loss-of-control or biological incident occurred in either of the previous 2 completed turns. Add 5 points if a fully implemented category 8 measure has put the Union inside a standing negotiation forum.
**Can repeat:** No
**Description:** The two leading powers reach a limited but real agreement covering some class of AI risk – weights security, autonomous escalation, a class of biological design tools – with verification thin but not absent. Whether the Union is inside it, consulted about it, or informed of it afterwards depends on what it has built and whom it has coordinated with. This is the one thing in the world that slows `ai_capability`, on the terms of metric rule 2.

## An Election Is Voided
**ID:** election_annulled
**Condition:** Possible in any turn. Where synthetic content, trust and elections meet.
**Probability:** 6%. Add 6 points if `public_sentiment` is below 30. Add 5 points if `openweight_capability` is above 60.
**Can repeat:** Yes
**Description:** An election in an established democracy is postponed, rerun or annulled with explicit reference to manipulation of the information environment. Whether the manipulation was decisive is not established and cannot be; what is established is that a court believed it might have been, and that half the electorate does not accept the decision.

## Frontier Access Denied
**ID:** eu_frontier_access_denied
**Condition:** Possible in any turn. What happened with Fable and Mythos in June 2026 happening again, on the same notice.
**Probability:** 12%. Add 10 points if the standing `US_POSTURE` is CONSOLIDATION. Halve if `eu_ai_sovereignty` is above 45, because there is then something to withhold in return.
**Can repeat:** Yes
**Description:** The Union is cut off from the leading model at short notice, wholly or by nationality of user. No detailed reason is given, there is no appeal, and the immediate practical effect lands on hospitals, ministries and firms that had built on it. Whether this reads at home as an outrage or as a failure of foresight depends on what the Union had done about it beforehand.

## Coercion Over ASML
**ID:** supply_chain_coercion
**Condition:** Possible in any turn.
**Probability:** 10%. Add 8 points if `export_control_escalation` occurred in either of the previous 2 completed turns.
**Can repeat:** Yes
**Description:** Washington forces the Netherlands to cut ASML's exports and servicing further still – beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company. The Union's one chokepoint is being used, and not by the Union.

## Access Secured on Its Own Terms
**ID:** eu_access_secured
**Eligible:** eu_political_capital >= 45
**Condition:** Possible in any turn where the Union has something to trade and the standing to trade it.
**Probability:** 8%. Add 8 points if a fully implemented category 8 measure coordinates other states holding pieces of the supply chain. Add 5 points if the standing `US_POSTURE` is ALLIANCE.
**Can repeat:** Yes
**Description:** The Union obtains frontier access under conditions it set rather than accepted: published terms, evaluation rights, a notice period before withdrawal, or capacity legally anchored inside its own jurisdiction. It is not sovereignty, and it is not nothing.

## Member State Defection
**ID:** member_state_defection
**Condition:** Possible in any turn. One or more member states break from a common position under external pressure.
**Probability:** 10%. Add 8 points if `eu_political_capital` is below 35. Add 5 points if a high-load measure is under implementation.
**Can repeat:** Yes
**Description:** A member state cuts its own arrangement – with a hyperscaler, with Washington, or with Beijing – on terms that undercut a position the Union has taken. It is defended at home as pragmatism and read everywhere else as the Union being unable to hold its own line.

## Backlash Turns Physical
**ID:** backlash_physical
**Eligible:** public_sentiment < 40
**Condition:** Possible in any turn where the public has soured.
**Probability:** 10%. Add 10 points if `public_sentiment` is below 28. Add 5 points if a category 4 build is under implementation, because there is then something local to protest against.
**Can repeat:** Yes
**Description:** Protest against AI infrastructure moves from petitions and hearings to direct action: occupations at data centre sites, sabotage of grid connections, and in the harder cases injury. Policing it costs the Union more than the damage does.

## Adoption Delivers
**ID:** adoption_success
**Condition:** Possible in any turn.
**Probability:** 10%. Add 8 points if a fully implemented category 9 measure has put capable AI to work in health, administration or education.
**Can repeat:** Yes
**Description:** Public-sector AI adoption produces visible, measurable benefit – waiting lists that fall, decisions that arrive in days rather than months, teaching that demonstrably works – and it is attributed to a European decision rather than to an American product.

## Automated Decision Scandal
**ID:** automated_decision_scandal
**Condition:** Possible in any turn. Internal origin by construction: this is harm the Union's own institutions caused.
**Probability:** 8%. Add 8 points if a fully implemented category 9 measure has broadened public-sector adoption. Add 5 points if `ai_capability` is above 65.
**Can repeat:** Yes
**Description:** An AI-supported decision system in social insurance, policing or the courts is found to have systematically wronged people, with a judgment or an ombudsman finding behind it. Restriction becomes cheap and adoption becomes politically impossible for years. Metric rule 12's internal-origin clause applies in full.
