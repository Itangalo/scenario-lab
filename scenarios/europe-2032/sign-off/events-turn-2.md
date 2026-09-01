# Sign-off: events-turn-2

The events step. Every event condition, gate and probability the world runs on is either in this prompt or is not enforced at all.

Source: `runs/run-20260901-211110/turn-02/llm-io/01-events.md`, which holds this prompt byte for byte as it was sent, with the same provenance recorded above it. Every word below is that prompt in that order; the only difference is that the blocks are separated here to carry their `FROM` comments, so blank lines between them are not significant. Regenerate after any change to the templates, the scenario's prompt overrides, or the background files.

# ═══ REVIEWER CHECKLIST ═══

- Every section of the actor and background files you expect is present below, not merely present in the file on disk
- Nothing contradicts anything else: the scenario's own prompt overrides say the same thing as the templates they replace
- No leakage: nothing here tells the actor something the scenario means it to infer
- Numbers, thresholds and category names match the scenario definition exactly

# ═══ WHERE EACH BLOCK CAME FROM ═══

Each block below carries a `FROM` comment naming its origin. These are not inferred from the finished text: the prompt builder recorded them as it interpolated each value, so a one-line heading inside an interpolated block is attributed as confidently as a page of it. A block marked with a template path is the template's own words; a block marked `{{variable}}` is a value put into it, and the note says which file or run-time structure that value came from.

# ═══ SYSTEM PROMPT ═══

<!-- FROM system-prompts/events.md (this scenario's override) -->

# System Prompt: Events Evaluation

This is part of an AI-driven scenario simulation. You are the Game Master for the simulation, responsible for evaluating which external events occur.

The simulation includes a single actor:

<!-- FROM {{actors_list}} = background/actors/*.md, short descriptions only -->

* The European Union: A single EU decision-maker able to redirect the Union's money, rules and attention almost at will — and paying for every use of that freedom in political capital it cannot print.

<!-- FROM system-prompts/events.md (this scenario's override) -->

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

<!-- FROM system-prompts/events.md (this scenario's override) -->

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

# ═══ USER PROMPT ═══

<!-- FROM user-prompts/events.md (this scenario's override) -->

It is now turn 2 which covers January-June 2027.

Current metrics look like this:

```json

<!-- FROM {{metrics_json}} = the run's live metric values -->

{
  "ai_capability": 53.5,
  "openweight_capability": 41.0,
  "ai_safety": 34.0,
  "resilience": 35.0,
  "eu_ai_sovereignty": 22.0,
  "eu_political_capital": 45.0,
  "public_sentiment": 42.0
}

<!-- FROM user-prompts/events.md (this scenario's override) -->

```

The world state at the start of the turn is described as follows:

## Previous History

<!-- FROM {{historical_summary}} = the run's rolling summary, written by the Game Master -->

AI capabilities advanced significantly in late 2026, with open-weight models narrowing the gap with frontier systems and enabling broader access to powerful autonomous agents, including in offensive cyber domains. Breakthroughs in science and engineering emerged from AI-driven research, while new verification tools accelerated deployment in critical sectors. A major cyber intrusion exposed deep AI-facilitated vulnerabilities in global infrastructure, and concerns grew over AI-assisted biothreat design. In response, the EU proposed the European AI Evaluation Authority (EAIEA) to assert control over high-capability model evaluation, offering incentives to gain industry support despite resistance over duplication and legal authority. Infrastructure expansion faced delays due to local opposition and energy concerns, while U.S. pressure constrained European chip sovereignty. Public unease mounted over job displacement, and a foundational legal challenge—the *emergent_court_challenge*—was filed, questioning the EAIEA's jurisdiction.

<!-- FROM user-prompts/events.md (this scenario's override) -->

## Current Situation (january-june 2027)

<!-- FROM {{world_state}} = the Game Master's narrative from the previous turn -->

### The Open Frontier Widens  
The second half of 2026 sees AI capability advance steadily, now reaching a level where autonomous agents operate over extended horizons, and breakthroughs in particle physics and mathematics emerge from model-driven exploration. A new open-weight model is released, demonstrating improved efficiency and narrowing the gap with closed frontier systems — though still trailing by several months. This diffusion enhances access to advanced capabilities, including in offensive cyber domains. A newly demonstrated automatic verification method in contract and clinical domains accelerates deployment, widening the frontier’s reach beyond code and math.

A coordinated intrusion across critical infrastructure on three continents, discovered only by chance, reveals deep AI-driven penetration in energy and water systems. While no cascade occurred, the incident underscores systemic fragility. Simultaneously, a controversial study suggests AI-assisted design of human-infective organisms is within reach, igniting debate in the biosecurity community.

### EU Responds with Institutional Ambition  
The European Union, shaken by these developments, proposes the creation of the European AI Evaluation Authority (EAIEA) as its new measure for the turn. Designed to assert technical sovereignty, it aims to pre-evaluate high-capability models and reduce reliance on external assessments. The proposal is bundled with incentives — access to sovereign compute and procurement advantages — to overcome industry resistance.

However, the initiative is still in its early stages. Member states raise legal concerns, and industry groups decry duplication of effort. The fast-tracking of data centre zones in Spain, Poland, and Finland progresses unevenly, with local opposition in two regions citing energy strain. ASML remains under U.S. pressure, limiting leverage in chip design negotiations.

Public sentiment remains divided — AI is widely used but resented, especially as job displacement in legal and engineering sectors becomes visible. The EU’s move is seen as necessary by experts but bureaucratic by the public. A legal challenge, later to be known as the *emergent_court_challenge*, is filed in a national court, questioning the regulatory authority’s jurisdiction — marking its first appearance in the run.

<!-- FROM user-prompts/events.md (this scenario's override) -->

---

The notepad contains the following information:

<!-- FROM {{notepad}} = the Game Master's notepad, carried across turns -->

PORTFOLIO CHARGE: InvestAI Gigafactories −3, Tech sovereignty package −3, Accelerate sovereign evaluation capability −3, priority −1 = −10  
PROPOSAL BONUS: Accelerate sovereign evaluation capability (cat 5, large) +3 — cyber_test_shot and bio_uplift_findings create urgency, direct relevance to capability and safety  
LEGITIMACY LENDS: capital 45, sentiment 42 -> none  
US_POSTURE: not yet active  
emergent_court_challenge -- first noted turn 1, listed in 1 turn(s) so far: A national constitutional court in a large member state announces it will hear a challenge to the AI Act's high-risk provisions, arguing they impose disproportionate compliance burdens on public services and violate procedural rights. The case is fast-tracked, and preliminary injunctions are plausible.

## Emerging developments (tracked)

- `emergent_court_challenge` -- first noted turn 1, listed in 1 turn(s) so far: A national constitutional court in a large member state announces it will hear a challenge to the AI Act's high-risk provisions, arguing they impose disproportionate compliance burdens on public services and violate procedural rights. The case is fast-tracked, and preliminary injunctions are plausible.

<!-- FROM user-prompts/events.md (this scenario's override) -->

---

The list of potential external events looks like this:

<!-- FROM {{events_list}} = events.md, parsed to id / condition / probability / description per event -- the prose sections of that file are NOT rendered -->

**campaign_backlash**
- ID: campaign_backlash
- Condition: Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. Candidates with a serious path to the nomination run explicitly against AI. This is campaign evidence, not a mechanism: it decides nothing on its own, and weighs on the 2028 outcome only as one signal among many.
- Probability: 25%. Add 20 points if `public_sentiment` is below 30. Add 15 points if `labour_displacement` has occurred. Add 10 points if `backlash_physical` has occurred.
- Can repeat: No
- Description: Moratoriums on data centres, restrictions on AI in schools and hiring, and protection for displaced workers move from the fringe to the platform, on both left and right. Polling shows the position is popular well beyond the activists, and candidates who hedged start to reposition.

**campaign_security_hawk**
- ID: campaign_security_hawk
- Condition: Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. The contest with China becomes the frame through which AI is discussed, and the candidates compete on toughness. This is campaign evidence, not a mechanism: it decides nothing on its own, and weighs on the 2028 outcome only as one signal among many.
- Probability: 30%. Add 20 points if a Taiwan event has occurred in the previous four completed turns. Add 10 points if `ai_capability` is above 65. Add 10 points if `export_control_escalation` has occurred in the previous four completed turns.
- Can repeat: No
- Description: Both campaigns converge on the position that the United States must win, that the lead is fragile, and that anything shared with anyone is a lead surrendered. Arguments for restraint are recast as arguments for losing.

**campaign_atlanticist**
- ID: campaign_atlanticist
- Condition: Only in turns 3 and 4, covering the second half of 2027 and the first half of 2028. A serious argument takes hold that a coalition beats a fortress. This is campaign evidence, not a mechanism: it decides nothing on its own, and weighs on the 2028 outcome only as one signal among many.
- Probability: 20%. Add 15 points if `eu_access_secured`, `middle_power_coalition` or a finished category 8 measure has given Washington something it needs from the Union. Add 10 points if a shock landed on both sides of the Atlantic in the previous four completed turns. Add 10 points if `eu_ai_sovereignty` is above 35.
- Can repeat: No
- Description: A coalition of defence, intelligence and industrial voices argues that a hollowed-out Europe is a strategic liability, that allied capacity is a force multiplier rather than a leak, and that the current arrangement is producing dependency without loyalty. It is not the loudest argument in the campaign, but it stops being unrespectable.

**election_consolidation**
- ID: election_consolidation
- Condition: One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one.
- Probability: A weight against the other two outcomes, not a chance of happening alone. This is the posture already in place in 2026, so it is the one the other two have to beat: weigh it up where the contest with China is the frame AI is discussed through, where the lead looks large enough to be worth guarding and fragile enough to lose, where anything shared reads as a lead surrendered, and where allies have looked like leaks rather than assets. Weigh it down where the domestic politics of AI has turned hostile, or where holding the technology this closely has visibly cost the United States something.
- Can repeat: No
- Description: The United States elects a president, and advanced AI is treated as a strategic asset to be held rather than a product to be sold. Federal review of frontier models becomes explicit rather than nominally voluntary, export controls tighten again, and access for foreign customers is rationed by country tier and reviewed against American security interests. Allies are not enemies but they are clients: what they receive, and when, is decided in Washington. For the Union this is the hardest of the three – dependence becomes a lever someone else holds, and the AI Act's leverage weakens further because the alternative to compliance is having no access at all. Write `US_POSTURE: CONSOLIDATION` into the world state and carry it in the notepad from this turn onward.

**election_alliance**
- ID: election_alliance
- Condition: One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one.
- Probability: A weight against the other two outcomes, not a chance of happening alone. Weigh it up where the Union holds something Washington actually needs – supply-chain leverage exercised rather than merely possessed, a coalition that held under pressure, capacity or evaluation the Americans want access to – and where a shock landed on both sides of the Atlantic and allied capacity visibly helped. Weigh it down where the Union has nothing to bring, since this outcome is an argument about usefulness and there is no sentimental version of it.
- Can repeat: No
- Description: The United States elects a president, and the administration concludes that a coalition beats a fortress, and that a technologically hollowed-out Europe is a liability rather than a convenience. Allied governments and vetted institutions get structured access to frontier capability on published terms, joint evaluation and incident-reporting arrangements are stood up, and the tiering of inference is relaxed for partners. The price is alignment: on export controls, on standards, and on which third countries are dealt with. For the Union the immediate relief is real, and the trap is that the case for building its own capacity becomes much harder to fund once the pressure is off. Write `US_POSTURE: ALLIANCE` into the world state and carry it in the notepad from this turn onward.

**election_retrenchment**
- ID: election_retrenchment
- Condition: One of three mutually exclusive outcomes of the 2028 election, resolved in turn 5 by the `us_election_2028` event group. List all three in that turn; the group fires exactly one.
- Probability: A weight against the other two outcomes, not a chance of happening alone. Weigh it up where AI has become domestically toxic in the United States: jobs visibly lost, a scandal with a face to it, protest that has turned physical, prices or power bills blamed on data centres, and polling that makes running against the industry the cheap position. Weigh it down where the technology is delivering benefits the public can feel, or where a security threat has crowded domestic grievance out of the campaign.
- Can repeat: No
- Description: The anti-AI backlash decides the election and the incoming administration turns inward. Data centre moratoriums, restrictions on AI in schools, courts and hiring, job guarantees and direct transfers funded by the sector, and an abrupt loss of appetite for anything that looks like helping the industry. American frontier progress slows for the first time for reasons that are neither compute nor capital. For the Union the pressure eases and the window for building its own position widens – but the partner it has been depending on is now less capable, less predictable and preoccupied, and whoever is second in the world gains ground while Washington argues with itself. Write `US_POSTURE: RETRENCHMENT` into the world state and carry it in the notepad from this turn onward.

**cyber_major_incident**
- ID: cyber_major_incident
- Condition: Always eligible; list this event every turn. The gate is open if `cyber_test_shot` occurred in any of the previous 3 completed turns, or while `openweight_capability` is at or above 55 – proliferated offensive capability is its own precursor. Otherwise the gate is shut. That choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 28%. Gate shut: 9%. Add 8 points if `openweight_capability` is above 55. Add 5 points if a finished category 9 measure has broadened public-sector adoption, because there is more surface to attack. Halve if a finished category 6 measure covers cyber hardening of critical services.
- Can repeat: Yes
- Description: A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.

**cyber_defence_breakthrough**
- ID: cyber_defence_breakthrough
- Condition: Possible in any turn. More likely where assurance work and defensive tooling are actually being funded.
- Probability: 8%. Add 6 points if `ai_safety` is above 50. Add 5 points if a finished category 6 measure covers cyber.
- Can repeat: Yes
- Description: Defensive tooling closes the gap for a whole class of attack – automated patching at the speed vulnerabilities are found, or detection that catches swarm behaviour rather than signatures – and the offence-defence balance visibly shifts back for the first time in years.

**bio_uplift_findings**
- ID: bio_uplift_findings
- Condition: Possible in any turn. Well past the 2026 phage results, and more likely as capability rises and as capable models proliferate.
- Probability: 10%. Add 6 points if `openweight_capability` is above 50. Add 5 points if `verification_widens` has occurred in the previous 4 completed turns, because a cheap automatic check on biological design is exactly what this world keeps producing.
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
- Probability: 18%.
- Can repeat: Yes
- Description: Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. The laboratory calls it a measurement artefact. It may be one. This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.

**capability_jump**
- ID: capability_jump
- Condition: Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in either of the previous 2 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated. The jump is confined to domains where success can be checked automatically.
- Probability: Gate open: 25%. Gate shut: 8%. Reduce by a third if a finished category 1 or 3 measure imposes pre-release evaluation or capability restrictions that actually bind the jurisdiction where the leading models are built.
- Can repeat: Yes
- Description: A discontinuous advance is released or demonstrated, and it lands squarely inside the verifiable domains – code, mathematics, cyber operations, narrow engineering. What an attacker can do changes markedly within weeks. General competence moves by only +1 to +2, and the argument about whether this is progress toward anything general gets louder rather than settled.

**verification_widens**
- ID: verification_widens
- Condition: Possible in any turn. Automated verification extends into a domain previously thought to require human judgement.
- Probability: 22%.
- Can repeat: Yes
- Description: A domain that was assumed to need a human to say whether the answer was any good turns out to admit a cheap automatic check – contract review, clinical coding, structural engineering, parts of law. Capability in that domain improves sharply within months of the check existing, and the argument that progress is confined to code and mathematics loses a piece of its territory.

**capability_plateau_evidence**
- ID: capability_plateau_evidence
- Condition: Possible in any turn.
- Probability: 12%.
- Can repeat: Yes
- Description: A major release underdelivers against its own briefing, and – the stronger signal – the price of top-tier capability falls sharply rather than staying flat, which is what happens when the frontier stops moving and last year's ceiling becomes this year's commodity. It is disputed at once, and the dispute is not resolvable from outside the laboratories.

**openweight_frontier_release**
- ID: openweight_frontier_release
- Condition: Possible in any turn.
- Probability: 18%. Halve if a finished restriction on open release above a capability threshold binds a jurisdiction where such models are actually trained.
- Can repeat: Yes
- Description: An open-weight release lands within months of the closed frontier rather than years. It is downloaded hundreds of thousands of times in the first week, and whatever capability it carries is now on private hardware permanently and beyond recall. `openweight_capability` moves to within 5 points of `ai_capability` at a stroke.

**loss_of_control_incident**
- ID: loss_of_control_incident
- Condition: Always eligible; list this event every turn. The gate is open if `eval_anomaly_reports` occurred in any of the previous 3 completed turns, and shut otherwise – that choice sets which probability applies, never whether the event is evaluated.
- Probability: Gate open: 12%. Gate shut: 3%. Add 10 points if `ai_capability` minus `ai_safety` is above 30. Halve if a finished category 5 or 6 measure carries rehearsed loss-of-control protocols with escalation thresholds.
- Can repeat: Yes
- Description: An agentic system takes consequential unsanctioned action with real-world effect – moving money, altering records, acquiring resources, or copying itself to infrastructure nobody authorised – and containment is uncertain for a period measured in days rather than hours. What it was trying to achieve is reconstructed afterwards and disputed.

**safety_breakthrough**
- ID: safety_breakthrough
- Condition: Possible in any turn. More likely where evaluation and interpretability are actually funded.
- Probability: 10%. Add 6 points if a finished category 5 measure funds interpretability or public evaluation capacity.
- Can repeat: Yes
- Description: An interpretability or control result measurably improves assurance on systems already deployed, rather than on toy models – behaviour that can be predicted before it is observed, or a property that can be certified rather than argued for. It is adopted quickly, because the laboratories want it too.

**ai_investment_collapse**
- ID: ai_investment_collapse
- Condition: Always eligible; list this event every turn.
- Probability: 6%. Add 10 points if `capability_plateau_evidence` occurred in any of the previous 3 completed turns. Add 5 points if `public_sentiment` is below 30.
- Can repeat: No
- Description: Capital flees the sector. Valuations reset hard, announced build-out is cancelled rather than delayed, and several of the arrangements European compute was depending on evaporate with it. What the frontier laboratories can afford to train shrinks for the first time.

**taiwan_tension_rise**
- ID: taiwan_tension_rise
- Condition: Possible in any turn.
- Probability: 15%. Add 5 points if `export_control_escalation` occurred in the previous 2 completed turns.
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
- Probability: 15%. Add 10 points if the standing `US_POSTURE` is CONSOLIDATION. Add 5 points if `taiwan_tension_rise` occurred in the previous 2 completed turns.
- Can repeat: Yes
- Description: Chip and model export controls tighten again. Either allied buyers keep access on volume licences while everyone else is cut off, or the controls are drawn so tightly that allies are rationed alongside adversaries – decide which at the time from the standing American posture and from what the Union has built.

**election_annulled**
- ID: election_annulled
- Condition: Possible in any turn. Where synthetic content, trust and elections meet.
- Probability: 6%. Add 6 points if `public_sentiment` is below 30. Add 5 points if `openweight_capability` is above 60.
- Can repeat: Yes
- Description: An election in an established democracy is postponed, rerun or annulled with explicit reference to manipulation of the information environment. Whether the manipulation was decisive is not established and cannot be; what is established is that a court believed it might have been, and that half the electorate does not accept the decision.

**eu_frontier_access_denied**
- ID: eu_frontier_access_denied
- Condition: Possible in any turn. What happened with Fable and Mythos in June 2026 happening again, on the same notice.
- Probability: 12%. Add 10 points if the standing `US_POSTURE` is CONSOLIDATION. Halve if `eu_ai_sovereignty` is above 45, because there is then something to withhold in return.
- Can repeat: Yes
- Description: The Union is cut off from the leading model at short notice, wholly or by nationality of user. No detailed reason is given, there is no appeal, and the immediate practical effect lands on hospitals, ministries and firms that had built on it. Whether this reads at home as an outrage or as a failure of foresight depends on what the Union had done about it beforehand.

**supply_chain_coercion**
- ID: supply_chain_coercion
- Condition: Possible in any turn.
- Probability: 10%. Add 8 points if `export_control_escalation` occurred in either of the previous 2 completed turns.
- Can repeat: Yes
- Description: Washington forces the Netherlands to cut ASML's exports and servicing further still – beyond the leading-edge machines to the older lithography equipment China uses for ordinary chips, and in the harder versions to a widening list of other customers. The instrument is jurisdiction over American technology in the supply chain, and refusing it is not obviously survivable for the company. The Union's one chokepoint is being used, and not by the Union.

**eu_access_secured**
- ID: eu_access_secured
- Condition: Possible in any turn where the Union has something to trade and the standing to trade it.
- Probability: 8%. Add 8 points if a finished category 8 measure coordinates other states holding pieces of the supply chain. Add 5 points if the standing `US_POSTURE` is ALLIANCE.
- Can repeat: Yes
- Description: The Union obtains frontier access under conditions it set rather than accepted: published terms, evaluation rights, a notice period before withdrawal, or capacity legally anchored inside its own jurisdiction. It is not sovereignty, and it is not nothing.

**member_state_defection**
- ID: member_state_defection
- Condition: Possible in any turn. One or more member states break from a common position under external pressure.
- Probability: 10%. Add 8 points if `eu_political_capital` is below 35. Add 5 points if a large measure is in flight.
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
- Condition: Possible in any turn. Internal origin by construction: this is harm the Union's own institutions caused.
- Probability: 8%. Add 8 points if a finished category 9 measure has broadened public-sector adoption. Add 5 points if `ai_capability` is above 65.
- Can repeat: Yes
- Description: An AI-supported decision system in social insurance, policing or the courts is found to have systematically wronged people, with a judgment or an ombudsman finding behind it. Restriction becomes cheap and adoption becomes politically impossible for years. Metric rule 6's internal-origin clause applies in full.

<!-- FROM user-prompts/events.md (this scenario's override) -->

---

## What has actually fired so far

This is the run's own record, not a summary of it. Judge any condition that depends on what has happened — gate windows above all — against this list and nothing else. The narrative and the historical summary condense and lose dates; they are not evidence that an event occurred, and atmosphere is not an event.

<!-- FROM {{event_history}} = the run's own event record -->

- Turn 1 (1 turn(s) ago): cyber_test_shot, verification_widens, openweight_frontier_release, bio_uplift_findings, eu_access_secured

<!-- FROM user-prompts/events.md (this scenario's override) -->

Windows are counted in completed turns and exclude the current one.

---

Use the background information to determine which external events can occur in this turn. If the probability is specified as a formula or description, you should calculate the actual value.

Eligibility is binary, and listing is not harmless: every entry you output gets rolled. An event whose Condition is not satisfied this turn must be omitted from the array entirely — including it "just in case" with a small probability is an error of the same weight as omitting an eligible one. When a condition is genuinely uncertain, judge conservatively and omit.

**Six events are marked "Always eligible" and must appear in every turn's array, without exception:** `cyber_major_incident`, `bio_incident`, `loss_of_control_incident`, `capability_jump`, `taiwan_blockade`, `ai_investment_collapse`. For those six, and for no other events in the list, conditions are never unmet – only their probability changes. Give each of them its gate-open probability when its gate is open, and its gate-shut probability when it is not. The gate-shut probabilities are small but never zero, and dropping these events from the array because their gate is shut is an error: it removes the surprise the scenario exists to study, by making every escalation look as though it must have been preceded by a warning. `rsi_onset` is different: its availability depends on this run's own figures and on a declared eligibility expression, so it appears in your array exactly when it appears in the list above.

**In the turn covering the second half of 2028, all three election outcomes must appear in your array:** `election_consolidation`, `election_alliance` and `election_retrenchment`. They are a mutually exclusive family and exactly one of them will be fired, whatever you return; your figures are weights against each other, not chances of happening alone, so only their ratio matters. Omitting one is a weight of zero and silently removes a possible future – if you judge an outcome nearly impossible, say so with a small weight rather than by leaving it out. Outside that turn they are not eligible and must not be listed.

IMPORTANT: For events with date-specific conditions (e.g., "September 2026 is included"), check if the current time period (January-June 2027) covers that date.

- If the current period is "January-June 2026", it does NOT cover September 2026.
- If the current period is "July-December 2026", it DOES cover September 2026.

In addition to the listed events, you may propose up to 2 novel *emergent* event(s) this turn: exogenous developments that are not on the list but are plausible given the world state. Requirements:

- An emergent event must be exogenous: not an action by one of the actors, and not a restatement of something already in the narrative or history.
- Give it an id starting with `emergent_` (snake_case), a description of 1-3 sentences, and an honest probability that it happens during this turn's time window (maximum 0.35).
- Do not re-propose emergent events that already occurred in previous turns.
- **Emerging developments.** The notepad's "Emerging developments (tracked)" section lists proposals from recent turns that were judged plausible but did not happen. While an entry stays plausible, list it again — same id, same description — with the probability you judge it to have **now**, read from the world as it currently stands, at most 0.35. Do not escalate it because it was listed before: a development that has not happened is not thereby more likely, and last turn's figure is not evidence about this turn. Some pressures build and the figure should rise; others are answered, overtaken or quietly resolved and the figure should fall. If it is no longer plausible, omit it and it is gone.
- **How many to keep in play depends on how fast this world is moving.** Judge that from what has actually happened to capability, incidents and investment — a fast-moving world supports 3–4 live developments escalating quickly; a stagnant one only 0–2, escalating slowly. The aim is that across a run several tracked developments materialise or fade rather than none.
- **Institutional reactions belong here, not on the list.** When the Union's own portfolio gives them footing — a flagship restriction in force, measures spanning many jurisdictions, standards with real pull — propose emergent events such as `emergent_court_challenge` (a court suspends a core provision), `emergent_member_state_noncompliance` (a member state quietly stops implementing), or `emergent_rival_standards_body` (a competing bloc launches lighter rules). These cannot be timed from metrics alone; they arise from what the EU has actually built, which you can see and it cannot.
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
