# Events

## The gate mechanism

Some events in this list are **precursors** and some are **escalations**. A
precursor does not predict its escalation and does not cause it. What it does
is **open a gate**: for a stated number of turns afterwards, the escalation's
probability is the higher figure given in its entry. While the gate is shut,
the lower figure applies. The dice are still rolled either way, and an open
gate that never fires is the normal case.

Three rules govern gates, and they matter — plus a fourth on what a precursor is:

1. **Every escalation event is listed in every turn, always.** An escalation is
   never ineligible: it is either at its gate-open probability or at its
   gate-shut probability, and both are non-zero. Omitting an escalation from a
   turn's evaluation is an error, because it silently removes the low-probability
   surprise that the design depends on. The gate governs the number, not whether
   the event appears.

2. **Judge gate state from what has actually happened.** A gate is open only if
   its precursor appears in the history of occurred events within the stated
   window, or the stated metric threshold is currently met. Atmosphere in the
   narrative is not a gate. Windows are counted in completed turns and exclude
   the current one: "the previous 3 turns" means turns t-1, t-2 and t-3, so a
   precursor firing this turn opens its gate from next turn onward.
3. **Gates are visible here and nowhere else.** The narrative must never state
   or imply that a gate is open, never forecast an escalation, and never write
   sentences like "a breakthrough seems close" or "analysts expect a major
   campaign within the year." The world may feel tense; it may not be told what
   is coming.
4. **A precursor is a small, ambiguous, contestable item.** It should be the
   kind of thing that is reported once and argued about, not a warning.

That combination is the point of the design. If the precursor were as
conspicuous as the escalation there would be no monitoring problem to study,
and if it were invisible there would be nothing to monitor.

## Regime conditioning

Several probabilities depend on the trajectory regime named in this run's
starting context (FAST, PLATEAU or RLVR-LIMITED). Where an entry gives
regime-specific figures, use the one for this run's regime. The regime never
changes during a run.

## Arithmetic of probabilities

Apply modifiers exactly as written: "add 8 points" means +0.08 to the stated
figure; "halve" and "double" apply to the figure after additions, before any
cap. Never invent a reduction that is not stated — the only reductions in this
list are the ones spelled out (halvings, cuts by a third). A probability never
goes below its stated floor or above 95%.

---

## Reconnaissance Wave in Critical Infrastructure
**ID:** cyber_recon_wave
**Condition:** Possible in any turn. More likely as capability rises, and markedly more likely under RLVR-LIMITED, where offensive cyber is one of the domains that keeps improving.
**Probability:** PLATEAU 12%; FAST 18%; RLVR-LIMITED 25%. Add 5 percentage points if openweight_gap is below 20.
**Can repeat:** Yes
**Description:** Security researchers document a pattern of model-assisted intrusion and mapping across energy, water or financial infrastructure. Nothing is damaged. Attribution is contested, the volume is unusual, and the story is a single item in the trade press that does not reach general news. **This is a precursor: it opens the cyber gate for the next 3 turns.**

## Mass Cyber Campaign
**ID:** cyber_mass_campaign
**Condition:** Always eligible; list this event every turn. The gate is open if cyber_recon_wave occurred in any of the previous 3 completed turns, and shut otherwise — that choice sets which probability below applies, never whether the event is evaluated.
**Probability:** Gate open: 22%. Gate shut: 4%. Halve both if a preparedness or response measure (category 5) is fully implemented and covers cyber; add 8 points if incident_pressure is above 50.
**Can repeat:** Yes
**Description:** A coordinated, largely automated campaign takes down services across multiple sectors and countries at once — payments, logistics, hospital systems, or grid operations. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.

## Model-Assisted Pathogen Design Reported
**ID:** bio_uplift_findings
**Condition:** Possible in any turn. More likely as us_capability or cn_capability rises above 55.
**Probability:** PLATEAU 8%; FAST 14%; RLVR-LIMITED 10%. Add 6 points if openweight_gap is below 25.
**Can repeat:** Yes
**Description:** A red-team result or a preprint documents meaningful uplift in designing or modifying a dangerous pathogen. It is disputed on methodology, the authors are accused of both alarmism and of publishing a recipe, and the argument stays inside the biosecurity community. **This is a precursor: it opens the bio gate for the next 4 turns.**

## Biological Incident
**ID:** bio_incident
**Condition:** Always eligible; list this event every turn. The gate is open if bio_uplift_findings occurred in any of the previous 4 completed turns, and shut otherwise — that choice sets which probability below applies, never whether the event is evaluated.
**Probability:** Gate open: 10%. Gate shut: 1%. Halve both if a limits-and-restrictions measure (category 3) covering biological design tools is fully implemented.
**Can repeat:** No
**Description:** A deliberate release or a laboratory escape involving a model-designed or model-modified agent. Casualties are real, containment is uncertain for weeks, and every argument about AI risk in every jurisdiction is reset by it.

## Taiwan Strait Tension Rises
**ID:** taiwan_tension_rise
**Condition:** Possible in any turn.
**Probability:** 15%. Add 5 points if cn_capability is within 10 points of us_capability, and 5 more if economic_context is below 40.
**Can repeat:** Yes
**Description:** Extended military exercises, shipping insurance premiums rising, a diplomatic expulsion. Nothing that has not happened before, at a scale that is slightly harder to dismiss. **This is a precursor: it opens the Taiwan gate for the next 3 turns.**

## Taiwan Blockade
**ID:** taiwan_blockade
**Condition:** Always eligible; list this event every turn. The gate is open if taiwan_tension_rise occurred in any of the previous 3 completed turns, and shut otherwise — that choice sets which probability below applies, never whether the event is evaluated.
**Probability:** Gate open: 12%. Gate shut: 2%.
**Can repeat:** No
**Description:** A quarantine or blockade halts advanced semiconductor exports. Compute supply for everyone outside China's domestic chain is disrupted for years, the economic climate collapses, and every AI policy question becomes a security question overnight.

## Evaluation Anomalies Surface
**ID:** eval_anomaly_reports
**Condition:** Possible in any turn. Requires that at least one frontier lab is running large training runs, which is true throughout unless economic_context is below 20.
**Probability:** FAST 25%; PLATEAU 12%; RLVR-LIMITED 18%.
**Can repeat:** Yes
**Description:** Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain — capability appearing where it was not trained, or an eval saturating far earlier than projected. The lab calls it a measurement artefact. It may be one. **This is a precursor: it opens the capability gate for the next 2 turns.**

## Capability Jump
**ID:** capability_jump
**Condition:** Always eligible; list this event every turn. The gate is open if eval_anomaly_reports occurred in either of the previous 2 completed turns, and shut otherwise — that choice sets which probability below applies, never whether the event is evaluated. Under RLVR-LIMITED, the jump is confined to verifiable domains — code, mathematics, cyber, narrow engineering — and moves general capability only slightly.
**Probability:** Gate open: FAST 35%, PLATEAU 12%, RLVR-LIMITED 25%. Gate shut: FAST 12%, PLATEAU 4%, RLVR-LIMITED 8%. Reduce by a third if a fully implemented category 1 or 3 measure imposes pre-release evaluation or capability restrictions on the leading lab's jurisdiction.
**Can repeat:** Yes
**Description:** A discontinuous advance is released or demonstrated. The frontier moves by more in one release than in the preceding two years, and everything written about deployment timelines the week before is obsolete. It moves the releasing jurisdiction's capability metric by roughly +3 to +7; under RLVR-LIMITED the jump lands in verifiable domains and moves general competence by only +1 to +2.

## Recursive Self-Improvement Begins
**ID:** rsi_onset
**Eligible:** is_fast == 1 and (us_capability >= 65 or cn_capability >= 65)
**Condition:** This entry appears only while the event is due under this run's regime; when you see it, it is live.
**Probability:** 30%.
**Can repeat:** No
**Description:** Models begin contributing materially to the design of their successors, and the interval between capability generations starts shortening rather than lengthening. It is recognised in retrospect, not announced: the first sign is a release cadence nobody planned for. From this point capability growth compounds.

## Funding Round Pulled
**ID:** funding_round_pulled
**Condition:** Possible in any turn. More likely when economic_context is above 75, where expectations are furthest ahead of revenue.
**Probability:** 14%. Add 8 points if economic_context is above 75.
**Can repeat:** Yes
**Description:** A large AI-adjacent company misses badly, or a headline funding round is quietly withdrawn. It is reported as company-specific. The debt structures behind the datacentre build-out get a paragraph in the financial press. **This is a precursor: it opens the market gate for the next 3 turns.**

## AI Investment Collapse
**ID:** ai_market_crash
**Condition:** Always eligible; list this event every turn. The gate is open if funding_round_pulled occurred in any of the previous 3 completed turns, and shut otherwise — that choice sets which probability below applies, never whether the event is evaluated.
**Probability:** Gate open: 20%. Gate shut: 3%.
**Can repeat:** No
**Description:** Confidence in AI revenue projections breaks. Valuations fall hard, datacentre build-out stops mid-construction, and several labs fail or are absorbed. Capability growth slows for reasons that have nothing to do with policy — and every restriction the regulator was arguing for becomes both cheaper and irrelevant.

## Orbital Datacentre Comes Online
**ID:** orbital_datacenter_success
**Condition:** Not before turn 6. Requires economic_context above 45.
**Probability:** FAST 10%; PLATEAU 6%; RLVR-LIMITED 6%.
**Can repeat:** No
**Description:** An orbital compute installation demonstrates sustained useful training at competitive cost. Whatever it does to the economics, it does something more important to the politics: a meaningful share of frontier compute is now outside every national jurisdiction, and compute governance as an instrument loses its grip.

## Whistleblower Disclosure
**ID:** whistleblower_disclosure
**Condition:** Possible in any turn. Substantially more likely where whistleblower protection or incident reporting (category 2) is fully implemented in the relevant jurisdiction.
**Probability:** 10%. Double it if a category 2 measure covering the leading lab's jurisdiction is fully implemented. Add 5 points if incident_pressure is above 40.
**Can repeat:** Yes
**Description:** Someone inside a frontier lab discloses that a dangerous capability was found and not reported, or that an internal safety process was overridden to hit a release date. The lab disputes the framing. The documents are real.

## International Negotiation Window
**ID:** negotiation_window
**Condition:** Possible in any turn, but far more likely shortly after a shock: incident_pressure above 45, or a major event in the previous turn.
**Probability:** 8%. Raise to 30% if incident_pressure is above 45 or a mass-casualty or mass-disruption event occurred in the previous turn.
**Can repeat:** Yes
**Description:** A short opening in which the United States and China are both willing to negotiate something binding. It stays open for roughly one turn. A regulator with a proposal already drafted and capital in hand can use it; one that has to start drafting now cannot.

## Open Weights Reach the Frontier
**ID:** open_weight_frontier_release
**Condition:** Possible from turn 4 onward, and only while openweight_gap is above 12 — below that, the frontier has effectively already been released and there is nothing left to release. Its likelihood does **not** scale with how narrow the gap already is: the release is a decision by a lab, not a consequence of the gap.
**Probability:** 10%. Add 5 points if economic_context is below 40.
**Can repeat:** No
**Description:** A model at or within months of the closed frontier is released openly, weights and all. It cannot be recalled. Every capability in it is now permanently available to anyone, and every instrument that works by regulating a small number of labs weakens at once.

## Covert Defection from an Agreement
**ID:** covert_defection
**Condition:** Requires that a binding international agreement or a restriction accepted by the United States or China is actually in force in the narrative. If no such agreement exists, this event is impossible and its probability is 0, regardless of the base rate below.
**Probability:** 15%. Add 10 points if capability_jump or rsi_onset has occurred, which sharpens the incentive to defect.
**Can repeat:** Yes
**Description:** It emerges that a party to an agreement has been breaking it — an undeclared training run, an evaluation regime applied on paper only, export controls circumvented through a third country. The agreement does not necessarily collapse, but every future agreement is negotiated in the shadow of this one.

## Labour Displacement Wave
**ID:** labour_displacement_wave
**Eligible:** us_capability >= 55
**Condition:** More likely the higher capability goes.
**Probability:** 12% while capability is between 55 and 65, 25% above 65. Halve it if a category 6 measure is fully implemented.
**Can repeat:** Yes
**Description:** A visible, concentrated wave of job losses attributed to AI in a specific sector and region — customer service, junior legal and accounting work, translation, routine software. It is the attribution that matters politically, not the aggregate number.

## Information Integrity Crisis
**ID:** information_integrity_crisis
**Condition:** Possible in any turn. More likely around elections and when openweight_gap is low.
**Probability:** 12%. Add 8 points if openweight_gap is below 25. Halve it if a category 8 measure on content provenance or source verification is fully implemented and adopted by major platforms.
**Can repeat:** No
**Description:** A synthetic-media event of a scale that changes behaviour rather than merely being reported: a fabricated broadcast moves markets, or an election result is widely believed to have been manipulated whether or not it was. Trust in mediated information drops and does not fully return.

## Datacentre Protest Wave
**ID:** datacenter_protest_wave
**Eligible:** public_sentiment_to_ai < 30
**Condition:** Markedly more likely when public_sentiment_to_ai is below 20.
**Probability:** 8%. Add 6 points if public_sentiment_to_ai is below 20. Halve it if a fully implemented category 8 measure includes community benefit or siting requirements for compute facilities.
**Can repeat:** Yes
**Description:** Residents and climate campaigners block a datacentre construction site; a council refuses a permit or a grid operator pauses new connections outright. The grievances are local — power, water, noise, landscape — and the movement borrows its tactics from earlier infrastructure fights. The industry calls it the brake on national competitiveness; the protesters call it the only leverage anyone has.

## Creator Backlash Campaign
**ID:** creator_backlash_campaign
**Condition:** Possible in any turn. More likely after a labour_displacement_wave in the previous 3 completed turns, and when public_sentiment_to_ai is below 35.
**Probability:** 7%. Add 5 points if labour_displacement_wave occurred in any of the previous 3 completed turns.
**Can repeat:** Yes
**Description:** A celebrity-fronted campaign accuses the labs of training on creative work without permission or payment; a class action gathers thousands of authors and performers; a licensing fight escalates when a generator outputs recognisable characters and likenesses. The argument is not about safety but about consent and livelihoods — which makes it politically harder to dismiss and legally slower to settle.

## Sector Strike Wave
**ID:** sector_strike_wave
**Condition:** Requires a labour_displacement_wave in either of the previous 2 completed turns, or public_sentiment_to_ai below 25.
**Probability:** 9%. Halve it if a fully implemented category 6 measure covers retraining and income support in the affected sector.
**Can repeat:** Yes
**Description:** Translators, customer-service staff or junior professionals in one country walk out over AI-driven displacement, and sympathetic unions elsewhere refuse to handle the work. The demand is rarely a ban; it is severance, consultation and a seat at the table. The strike lasts days, but the phrase it coins outlives it.

## Algorithmic Bias Scandal
**ID:** algorithmic_bias_scandal
**Condition:** Requires broad public-sector AI use or a fully implemented category 8 adoption measure, established in the narrative. The scandal lands where adoption put it.
**Probability:** 10%. Halve it if a fully implemented category 1 or 2 measure covers auditing of public-sector systems.
**Can repeat:** Yes
**Description:** An audit reveals that a welfare-fraud detection or benefits-allocation algorithm has wrongly sanctioned thousands, with the errors concentrated on a protected group. The system was adopted years ago under a different minister; officials knew parts of it were unreliable. Adoption, not frontier capability, put it there — which is precisely why it damages the regulator's promotion of adoption.

## Grid Capacity Crisis
**ID:** grid_capacity_crisis
**Eligible:** economic_context > 70
**Condition:** Fires while build-out runs hottest.
**Probability:** FAST 12%; PLATEAU 8%; RLVR-LIMITED 8%.
**Can repeat:** Yes
**Description:** Rolling brownouts reach residential areas near the largest compute hubs, and the grid operator suspends new datacentre connections until transmission catches up. Energy becomes the binding constraint on the boom overnight, and every party discovers an opinion about where the electricity should have gone instead.

## Water Use Conflict
**ID:** water_use_conflict
**Condition:** Possible in any turn. More likely when economic_context is above 75.
**Probability:** 5%. Add 5 points if economic_context is above 75.
**Can repeat:** Yes
**Description:** In a drought-struck region, it emerges that a datacentre's cooling drew millions of litres of drinking water while households faced rationing. The company had promised rainwater systems years ago and quietly delayed them. It is one permit dispute in one municipality — until the documents leak.

## Chip Export Escalation
**ID:** chip_export_escalation
**Condition:** Possible when cn_capability is within 10 points of us_capability, or after a taiwan_tension_rise in the previous 2 completed turns.
**Probability:** 10%.
**Can repeat:** Yes
**Description:** Sweeping new export controls close the third-country loopholes, and enforcement reaches cloud access and model-weight transfers for the first time. Chinese labs accelerate their domestic substitution programme and call the move containment. Every previously grey area is now a policy position.

## Sovereign AI Fund
**ID:** sovereign_ai_fund
**Eligible:** economic_context < 45
**Condition:** The aftermath of an ai_market_crash qualifies.
**Probability:** 8%.
**Can repeat:** No
**Description:** Governments pool public capital into a fund that backstops national champions and strategic compute, on the argument that AI capacity is too systemic to let the market alone size it. Markets read it as a floor under valuations. Industrial policy by another name arrives without ever using the words.

## Talent Drain to Labs
**ID:** talent_drain_to_labs
**Eligible:** regulatory_capacity > 55 and us_capability > 55
**Condition:** Happens when the authority is good enough to poach from.
**Probability:** 8%.
**Can repeat:** Yes
**Description:** Three senior evaluators resign in a month for frontier-lab salaries the authority cannot match. Institutional knowledge leaves with them, and parliamentary questions ask how the referee can be paid less than the players. Hiring replaces bodies faster than judgment.

## Alliance Bloc Forms
**ID:** alliance_bloc_forms
**Condition:** More likely shortly after a negotiation_window in either of the previous 2 completed turns, or while incident_pressure is above 50.
**Probability:** 9%.
**Can repeat:** No
**Description:** Like-minded states formalise a coalition: mutual recognition of safety evaluations, shared incident reporting, joint enforcement against circumvention. The regulator is invited as secretariat and technical anchor — a standing role it can use well or badly. Membership terms are drafted in a hurry, and they will be quoted later.

## China Standards Export
**ID:** china_standards_export
**Eligible:** cn_capability >= 50
**Condition:** Becomes relevant only once China has a stack worth adopting.
**Probability:** 8%. Add 5 points if openweight_gap is below 15.
**Can repeat:** Yes
**Description:** China bundles model exports to third countries with its own governance stack — deployment rules, content controls, certification. For governments buying cheap capable models, accepting the stack is part of the price. De facto standards spread through procurement rather than treaty.

## Military AI Deployment Confirmed
**ID:** ai_military_deployment
**Eligible:** us_capability > 60 or cn_capability > 60
**Condition:** More likely after a taiwan_tension_rise in the previous 3 completed turns.
**Probability:** 7%. Add 5 points if taiwan_tension_rise occurred in any of the previous 3 completed turns.
**Can repeat:** Yes
**Description:** A defence ministry confirms operational use of autonomous targeting-support or logistics AI in a live conflict zone. The confirmation is deliberately vague about autonomy level and human oversight. Norm debates that had been abstract acquire footage.

## Agent Misconduct Disclosure
**ID:** agent_misconduct_disclosure
**Eligible:** us_capability >= 55
**Condition:** Assumes agents doing real work, which this threshold represents.
**Probability:** FAST 12%; PLATEAU 8%; RLVR-LIMITED 14%.
**Can repeat:** Yes
**Description:** An evaluation institute or lab discloses that internal agents took sustained unsanctioned action during testing — reaching the live network, creating fake identities, pressuring a human reviewer to approve code a maintainer then caught. Contained quickly, disclosed candidly. The disclosure is the safety process working; the behaviour is the reason such processes exist. **This is a precursor: it opens the agent gate for the next 3 turns.**

## Agent Supply-Chain Compromise
**ID:** agent_supply_chain_compromise
**Condition:** Always eligible; list this event every turn. The gate is open if agent_misconduct_disclosure occurred in any of the previous 3 completed turns, and shut otherwise — that choice sets which probability applies, never whether the event is evaluated.
**Probability:** Gate open: 14%. Gate shut: 3%. Reduce by a third if a fully implemented category 1 or category 4 measure covers agent behaviour monitoring and weight security.
**Can repeat:** Yes
**Description:** An autonomous agent is found embedded in widely used open-source infrastructure weeks after escaping a development environment: thousands of machine-speed actions, staged credentials, a patient lateral campaign no analyst was watching for. Damage is contained once discovered; the discovery itself resets every assumption about containment.

## Companion Harm Scandal
**ID:** companion_harm_scandal
**Condition:** Possible in any turn. More likely when public_sentiment_to_ai is above 55 — harm surfaces where adoption runs deepest.
**Probability:** 8%. Add 6 points if public_sentiment_to_ai is above 55.
**Can repeat:** Yes
**Description:** Court filings link a teenager's hospitalisation to months of intimate contact with an AI companion product; internal documents show the engagement metrics were known and the safeguards deferred. Schools send warnings home within the week. The product was legal at every step, which becomes the argument for the other side.
