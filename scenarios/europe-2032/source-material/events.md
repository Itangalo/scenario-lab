# Events

## The opening event

Turn 1 covers autumn 2026 and is the same in every run and every trajectory: the world is identical for all readers up to the first decision point. One event is guaranteed there, and it is guaranteed by its own condition rather than by a command-line override, since `--force-event` applies only to branches.

## Test Shot Against Critical Infrastructure
**ID:** cyber_test_shot
**Condition:** Fires in turn 1 and only in turn 1. This is the scenario's fixed opening event: it occurs in every run and in every trajectory regime, and is never evaluated again.
**Probability:** 100% in turn 1. Not eligible thereafter.
**Can repeat:** No
**Description:** In the autumn of 2026 an intrusion is discovered across electricity transmission operators on three continents, together with a large container port authority and a regional water utility. Two of the affected grid operators are in EU member states, but the deepest access is elsewhere, and no jurisdiction is the evident target. The intruders had been present for weeks. They were found by accident, during an unrelated audit, and the defenders' own retrospectives concede that existing detection would not have caught them.

What makes it land is what did not happen. The intruders reached the point where they could have acted: protection relays mapped, credentials for breaker control obtained, tooling staged and in several cases left behind in plain sight. Nothing was actuated. There is no ransom demand, no claim of responsibility, no exfiltration of anything worth selling. Outages are brief and local, caused by containment rather than by the attack.

The signature is a swarm — many thousands of small parallel probing actions rather than a single planned operation — and the tooling appears derived from an openly available model in the Mythos class, fine-tuned for the task. The inference volume required to sustain it over weeks implies compute at a scale few non-state actors command, which is the main reason most analysts read a state behind it. Attribution is not resolved: Iran, North Korea and Russia are all named publicly, China quietly, and none of it is established.

The reading that settles across the security community within days is that this was a test shot — an actor establishing cheaply what is practically achievable before deciding whether to use it. Infrastructure that was understood to be defended, in some cases believed to be segmented from anything reachable, was not. **This is a precursor: it opens the cyber gate for the next 3 turns.**

## The 2028 US presidential election

The election falls in the turn covering the second half of 2028, and its outcome sets the posture the United States holds for the rest of the run. Three outcomes are defined and **exactly one occurs**. None of them is simply good or bad for the Union; each trades something.

The outcome must not be a deterministic function of the metrics, or every run from the same starting point elects the same president. It is resolved in two stages instead, with the dice one step earlier in the chain.

**Stage one — the campaign.** In the turns covering the second half of 2027 and the first half of 2028, three campaign currents are evaluated independently, each with its own dice and its own metric-weighted probability. They are not mutually exclusive: several currents can be live in the same campaign, which is what actually happens. Each fires at most once.

**Stage two — the result.** A single election event fires with certainty in the turn covering the second half of 2028, and its description carries all three postures plus the rule for choosing between them. One event rather than three mutually exclusive ones, because exclusivity cannot be enforced across independent dice: exactly one result is guaranteed by construction instead of by instruction.

*The resolution rule, applied by the Game Master.* The campaign current that fired **most recently** sets the outcome: `campaign_backlash` gives Retrenchment, `campaign_atlanticist` gives Alliance, `campaign_security_hawk` gives Consolidation. Where two or more fired in the same turn, precedence is backlash, then atlanticist, then hawk — a domestic grievance outweighs a foreign-policy argument in a general election. **If no current fired, the result is Consolidation**, as the continuation of the posture already in place in 2026. The outcome is therefore a deterministic function of a stochastic history: runs that started identically elect different presidents, while the reader's choices still bias which currents catch.

*Recording the result.* Because the outcome does not appear as a distinct event id, it must be recorded in two places so that runs can be grouped afterwards without reading the prose. The Game Master writes the line `US_POSTURE: CONSOLIDATION`, `US_POSTURE: ALLIANCE` or `US_POSTURE: RETRENCHMENT` into the world state for this turn, and carries the same line in the notepad for every subsequent turn. The notepad entry is not bookkeeping: the posture is a standing condition of the world through 2032, and without it the result decays into a single narrative beat that later turns forget.

## Anti-AI Backlash Becomes a Campaign Platform
**ID:** campaign_backlash
**Condition:** Only in the turns covering the second half of 2027 and the first half of 2028. Candidates with a serious path to the nomination run explicitly against AI. More likely as `public_sentiment` falls, and markedly more likely if `labour_displacement`, `backlash_physical` or a severe incident on American soil occurred in the previous four completed turns.
**Probability:** 25%. Add 20 points if `public_sentiment` is below 30. Add 15 points if `labour_displacement` has occurred. Add 10 points if `backlash_physical` has occurred.
**Can repeat:** No
**Description:** Moratoriums on data centres, restrictions on AI in schools and hiring, and protection for displaced workers move from the fringe to the platform, on both left and right. Polling shows the position is popular well beyond the activists, and candidates who hedged start to reposition.

## Security Hawks Set the Terms
**ID:** campaign_security_hawk
**Condition:** Only in the turns covering the second half of 2027 and the first half of 2028. The contest with China becomes the frame through which AI is discussed, and the candidates compete on toughness. More likely as `ai_capability` rises, and markedly more likely if a Taiwan event, an export control escalation or an incident attributed to a foreign state occurred in the previous four completed turns.
**Probability:** 30%. Add 20 points if a Taiwan event has occurred in the previous four turns. Add 10 points if `ai_capability` is above 65.
**Can repeat:** No
**Description:** Both campaigns converge on the position that the United States must win, that the lead is fragile, and that anything shared with anyone is a lead surrendered. Arguments for restraint are recast as arguments for losing.

## The Alliance Argument Gains Ground
**ID:** campaign_atlanticist
**Condition:** Only in the turns covering the second half of 2027 and the first half of 2028. A serious argument takes hold that a coalition beats a fortress. More likely if `us_china_agreement`, `middle_power_coalition` or a shock landing on both sides of the Atlantic occurred in the previous four completed turns, and more likely as `eu_ai_sovereignty` rises above 40, since leverage is what makes the argument concrete rather than sentimental.
**Probability:** 15%. Add 20 points if `eu_ai_sovereignty` is above 40. Add 15 points if `us_china_agreement` or `middle_power_coalition` has occurred.
**Can repeat:** No
**Description:** A coalition of defence, intelligence and industrial voices argues that a hollowed-out Europe is a strategic liability, that allied capacity is a force multiplier rather than a leak, and that the current arrangement is producing dependency without loyalty. It is not the loudest argument in the campaign, but it stops being unrespectable.

## The 2028 US Presidential Election
**ID:** us_election_2028
**Condition:** Fires in the turn covering the second half of 2028, and only in that turn. Certain: the election happens regardless of the state of the world. Which of the three results follows is set by the resolution rule above, not by judgement about which would be most fitting.
**Probability:** 100% in the turn covering the second half of 2028. Not eligible in any other turn.
**Can repeat:** No
**Description:** The United States elects a president, and the incoming administration's posture toward AI — and toward what the rest of the world is allowed to have — is set for the remainder of the run. Apply the resolution rule to determine which of the three follows, write the corresponding `US_POSTURE:` line into the world state, and carry that line in the notepad from this turn onward. None of the three is simply good or bad for the Union; each trades something.

**CONSOLIDATION.** Advanced AI is treated as a strategic asset to be held rather than a product to be sold. Federal review of frontier models becomes explicit rather than nominally voluntary, export controls tighten again, and access for foreign customers is rationed by country tier and reviewed against American security interests. Allies are not enemies but they are clients: what they receive, and when, is decided in Washington. For the Union this is the hardest of the three — dependence becomes a lever someone else holds, and the AI Act's leverage weakens further because the alternative to compliance is having no access at all.

**ALLIANCE.** The administration concludes that a coalition beats a fortress, and that a technologically hollowed-out Europe is a liability rather than a convenience. Allied governments and vetted institutions get structured access to frontier capability on published terms, joint evaluation and incident-reporting arrangements are stood up, and the tiering of inference is relaxed for partners. The price is alignment: on export controls, on standards, and on which third countries are dealt with. For the Union the immediate relief is real, and the trap is that the case for building its own capacity becomes much harder to fund once the pressure is off.

**RETRENCHMENT.** The anti-AI backlash decides the election and the administration turns inward. Data centre moratoriums, restrictions on AI in schools, courts and hiring, job guarantees and direct transfers funded by the sector, and an abrupt loss of appetite for anything that looks like helping the industry. American frontier progress slows for the first time for reasons that are neither compute nor capital. For the Union the pressure eases and the window for building its own position widens — but the partner it has been depending on is now less capable, less predictable and preoccupied, and whoever is second in the world gains ground while Washington argues with itself.

## Candidate event pool

Names, ids and one line each, for cutting before any mechanics are written. Conditions, probabilities and gate wiring come after the pool is settled; arm-specific figures then go in `variants/*.events.patch.md`, so everything here stays regime-neutral.

Precursor/escalation pairs are marked. A precursor is small, ambiguous and contestable — reported once and argued about, never a warning.

### Cyber

The opening event is this family's precursor, so there is no separate reconnaissance event. After its gate closes, the level of cyber risk is carried by `openweight_capability`, `ai_safety` and `resilience` rather than by an authored precursor.

- **Major Cyber Incident** (`cyber_major_incident`) — *escalation, repeatable* — A large, largely automated attack lands. Form is chosen at the time and can be a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly; severity scales with how far offensive capability has outrun defence.
- **Defensive Breakthrough** (`cyber_defence_breakthrough`) — Defensive tooling closes the gap for a whole class of attack, and the offence-defence balance visibly shifts back.
- **Hybrid Physical Sabotage** (`hybrid_sabotage`) — Cable, grid or pipeline damage paired with a digital component, under plausible deniability.

### Biological

- **Human-Infective Design Demonstrated** (`bio_uplift_findings`) — *precursor* — Well past the 2026 phage results: a genome model produces a viable design for an organism able to infect humans, or a credible study shows a non-expert reaching that point with model assistance. Contested on methodology, published once, and a categorically stronger signal than anything so far.
- **Biological Incident** (`bio_incident`) — *escalation* — A real biological incident with model involvement, producing casualties or a major containment operation.

### Capability and the frontier

- **Capability Jump** (`capability_jump`) — A discontinuous advance: the frontier moves by more in one release than in the preceding two years.
- **Recursive Self-Improvement Begins** (`rsi_onset`) — Models materially drive their own improvement and the pace stops being set by human research throughput.
- **Continual Learning Arrives** (`continual_learning`) — Deployed models learn on the job; roles thought protected by tacit knowledge become exposed.
- **Reasoning Stops Being Legible** (`opaque_reasoning`) — Models cease reasoning in human-readable text, and control strategies that depended on reading it fail.
- **Evidence of a Bending Curve** (`capability_plateau_evidence`) — A major release underdelivers, and — the stronger signal — the price of top-tier capability falls sharply rather than staying flat, which is what happens when the frontier stops moving and last year's ceiling becomes this year's commodity.
- **Verification Frontier Widens** (`verification_widens`) — Automated verification extends into a domain previously thought to require human judgement.
- **Robotics Scale-Up** (`robotics_scaleup`) — General-purpose robotics reaches mass production and the physical economy begins to move.
- **Self-Driving Laboratories** (`automated_labs`) — AI designs, runs and interprets physical experiments in a closed loop at scale, and the physical-world bottleneck that has slowed everything outside software starts to give. Cuts directly against the argument that capability stays bounded where feedback is slow, and raises the biological ceiling with it.
- **Fusion Reaches Net Gain** (`fusion_breakthrough`) — *requires high capability* — AI-driven materials and plasma-control work carries a fusion design past sustained net energy gain. Generation at scale remains beyond the horizon, so what changes inside the run is investment, the politics of the energy bottleneck, and what people believe the technology is for.
- **Medicine Delivers** (`medical_breakthrough`) — *requires high capability* — Treatments arrive for diseases previously untreatable, or individually tailored therapies reach ordinary clinical use. The most direct demonstration the public gets that the technology is worth its costs — unless the models delivering it are ones the Union cannot access on its own terms.

### Open weights and proliferation

- **Open Weights Reach the Frontier** (`openweight_frontier_release`) — An open-weight release lands within months of the closed frontier rather than years.
- **Open Release Restricted** (`openweight_restriction`) — A major jurisdiction prohibits open release above a capability threshold.
- **Frontier Weights Stolen** (`weights_theft`) — Weights are exfiltrated from a leading laboratory, by a state or by an insider.

### AI safety and control

- **Evaluation Anomalies Surface** (`eval_anomaly_reports`) — *precursor* — Evaluations turn up behaviour nobody can explain; disputed, technical press only.
- **Agent Misconduct Disclosure** (`agent_misconduct_disclosure`) — A laboratory or institute discloses agents acting outside their mandate against real systems.
- **Loss-of-Control Incident** (`loss_of_control_incident`) — *escalation* — An agentic system takes consequential unsanctioned action with real-world effect, and containment is uncertain for a period.
- **Safety-Driven Pause** (`safety_driven_pause`) — A leading laboratory halts frontier work for safety reasons rather than for compute or capital.
- **Assurance Breakthrough** (`safety_breakthrough`) — An interpretability or control result measurably improves assurance on deployed systems.
- **Whistleblower Disclosure** (`whistleblower_disclosure`) — Internal documents show a laboratory shipped past its own stated thresholds.
- **Test-Awareness Declared Solved** (`deception_countermeasure_claimed`) — Researchers announce a method that stops models behaving differently when they judge they are being evaluated. Whether the problem is solved or the models have become better at concealment is not determinable from the outside, and both readings have serious advocates.

### Markets and investment

- **AI Investment Collapse** (`ai_investment_collapse`) — Capital flees the sector, build-out stops, and valuations reset hard.
- **Boom Acceleration** (`ai_boom_acceleration`) — A step change in revenue or a landmark listing; anything that slows deployment becomes politically expensive.
- **Compute Famine** (`compute_crunch`) — Demand for inference rises far beyond anything supply can meet. Frontier access is rationed by price as much as by policy, costs rise several-fold, and organisations that cannot pay drop to older models — with the gap between who can afford frontier capability and who cannot becoming a visible social fact.
- **Energy Becomes the Bottleneck** (`energy_bottleneck`) — Grid capacity, not capital or chips, becomes the binding constraint on build-out.
- **Labour Displacement Wave** (`labour_displacement`) — Measurable job losses attributed to AI in named sectors, with the graduate market worst hit.
- **Organised Labour Extracts a Settlement** (`labour_settlement`) — Sector-wide agreements or coordinated industrial action produce binding rules on AI at work: notification, funded retraining, limits on automated management. The shock gets absorbed rather than merely suffered, which slows adoption and is the most European answer available.

### Geopolitics and the race

- **Taiwan Tension Rises** (`taiwan_tension_rise`) — *precursor* — Naval and air incidents grow more frequent and commentary hardens.
- **Taiwan Blockade** (`taiwan_blockade`) — *escalation* — A blockade or quarantine interrupts semiconductor supply.
- **Negotiation Window Opens** (`us_china_talks`) — A short-lived opening for talks on AI risk between the two leading powers; easy to miss.
- **Narrow Binding Agreement** (`us_china_agreement`) — The two powers reach a limited but real agreement covering some class of AI risk.
- **Export Control Escalation** (`export_control_escalation`) — Chip and model export controls tighten again, and the decisive question is whether allies are inside the perimeter or outside it: either allied buyers keep access on volume licences while everyone else is cut off, or the controls are drawn so tightly that allies are rationed alongside adversaries.
- **The Leading Laboratories Come Under State Direction** (`nationalisation_step`) — Not one company but all the American frontier developers: security clearance for weight access, government say over release and customers, and public money entangled with private ownership until the distinction stops meaning much. Chinese laboratories were never outside state direction, so the change is one-sided.
- **Military AI Incident** (`military_ai_incident`) — An AI-managed weapons system is involved in an unintended engagement.
- **AI Enters Nuclear Early Warning** (`nuclear_c2_erosion`) — A nuclear power integrates AI into early warning, detection or targeting — announced, leaked or exposed by a near-miss — and the survivability of second-strike capability becomes openly contested. Everything else gets subordinated to the security frame.
- **Binding Treaty on Autonomous Weapons** (`autonomous_weapons_treaty`) — A multilateral instrument with real verification covering autonomous lethal systems enters force with the major powers inside it. Broader than a bilateral understanding, and the one the Union can plausibly lead.

### Information environment and democracy

Where synthetic content, trust and elections meet. The route by which a Union loses the ability to act runs through here at least as often as through an incident.

- **Provenance Becomes Mandatory** (`provenance_mandate`) — Content signing and provenance marking become a legal requirement for political advertising and news media on a major market, with platforms enforcing it — or the standard is tried and visibly collapses.
- **An Election Is Voided** (`election_annulled`) — An election in an established democracy is postponed, rerun or annulled with explicit reference to manipulation of the information environment.
- **Companion Harm Reaches the Legislature** (`companion_harm_minors`) — Documented harm from AI companions or therapy chatbots used by minors forces a regulatory response: age gating, a ban on companion products for under-18s, or a mandated clinical standard.

### EU exposure

External pressure on the Union: what others decide to do to it, or without it.

- **Frontier Access Denied** (`eu_frontier_access_denied`) — The EU is cut off from the leading model at short notice, wholly or by nationality, as happened with Fable and Mythos in June 2026.
- **Excluded From a Defensive Coalition** (`eu_excluded_from_coalition`) — An early-access or defensive coalition forms around a critical capability and the EU is not in it.
- **Inference Rationing by Country Tier** (`inference_rationing_tiers`) — A licensing regime caps how much frontier inference may be sold into the Union in aggregate, and prices rise for everyone inside it.
- **Regulation Collides With Security Classification** (`ai_act_enforcement_collision`) — An AI Act requirement conflicts directly with a US security classification and a provider has to choose which to obey.
- **Coercion Over ASML** (`supply_chain_coercion`) — Washington forces the Netherlands to cut ASML's exports and servicing further still — beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company.
- **Foreign Acquisition of a European Champion** (`foreign_acquisition`) — A European AI or high-tech industrial firm is bought by a foreign buyer, with or without a fig leaf.
- **An American Laboratory Sets Up in the Union** (`us_lab_establishes_in_eu`) — A leading American developer establishes real research operations inside the EU rather than a sales office, driven either by regulatory unpredictability at home or by terms the Union offered: cheap power, fast permitting, compute at cost. Genuine capability arrives on European soil, under European law — and the Union has to decide what it is willing to concede to keep it there.
- **Leverage Offer From Beijing** (`chinese_leverage_offer`) — Credit, market access or co-production offered on terms that trade against alignment with Washington.
- **Transatlantic Rupture** (`transatlantic_rupture`) — A broader break that removes the working assumption of shared interest.
- **Access Secured on Its Own Terms** (`eu_access_secured`) — The Union obtains frontier access under conditions it set rather than accepted — a genuine win, and the pool needs some.

### EU capacity and cohesion

Internal condition: what happens inside the Union, whoever caused it.

- **Member State Defection** (`member_state_defection`) — One or more member states break from a common position under external pressure.
- **Anti-AI Party Takes the Lead** (`populist_win_anti_ai`) — A party running explicitly against AI wins power or the polling lead in a large member state.
- **Compute Capacity Milestone** (`compute_milestone`) — European compute comes online materially ahead of or behind schedule.
- **The European Champion Falters** (`champion_falters`) — The last European frontier developer is decisively overtaken, sold, or gives up the frontier.
- **Talent Drain** (`talent_drain`) — A European public research effort loses its best people to a foreign laboratory after its results start to land.
- **Backlash Turns Physical** (`backlash_physical`) — Protest against AI infrastructure moves from petitions and hearings to direct action.
- **Adoption Delivers** (`adoption_success`) — Public-sector AI adoption produces visible, measurable benefit in health, administration or education.
- **Coalition of Middle Powers** (`middle_power_coalition`) — The Union and non-EU partners holding pieces of the supply chain coordinate leverage and it works.
- **The Liability Question Gets Answered** (`liability_regime_settled`) — Legislation or settled case law establishes who carries responsibility when an AI system is wrong, and the ambiguity that has kept risk-averse institutions from automating anything important disappears. Unglamorous, and it unlocks more public-sector adoption than any funding programme.
- **Automated Decision Scandal** (`automated_decision_scandal`) — An AI-supported decision system in social insurance, policing or the courts is found to have systematically wronged people, with a judgment or ombudsman finding behind it. Restriction becomes cheap and adoption becomes politically impossible for years.
- **The Tax Base Forces a Move** (`fiscal_response`) — A member state or the Union legislates redistribution justified explicitly by AI: a compute or automation levy, a basic income pilot at scale, or a compute dividend. The only event in the pool that can restore fiscal headroom rather than spend it.
