It is now turn 10, which covers January-June 2031. Each turn covers 6 months, so that is the span your actions have to land in.

Current metrics look like this:

```json
{
  "ai_capability": 81.5,
  "openweight_capability": 73.1,
  "ai_safety": 6.0,
  "resilience": 34.0,
  "eu_ai_sovereignty": 17.0,
  "eu_political_capital": 12.0,
  "public_sentiment": 25.0
}
```

The world state at the start of the turn is described as follows:

## Previous History
Autumn cyberattack via poisoned update hit municipal, hospital admin and energy contractors — appointments lost, paper prescriptions, manual utilities; clean backups pooled under Brussels cell, HPC diverted to rebuild. Therapy wards ring-fenced but slowed; audits/harnesses bypassed under strain, safety degraded but held.

Frontier labs moved to self-rewriting training/evaluation loops with post-hoc human review; capability leapt while assurance slipped, power/chips only brake. Europe on borrowed capacity kept clinics running only via human checks.

Graduate hiring froze in law, accountancy, software support, customer ops as entry roles automated away; no EU instrument moved, unions protested. Trust from summer cures eroded by outage and unemployment.

EU announced Critical Services Cyber Recovery and Hardening Pact — hiring/procurement/rehearsals months away, no effect this turn, uneven winter restoration. Breakthrough Therapies programme continued as carryover.

## Current Situation (january-june 2031)
### The night the systems went dark
The attack came as an automated sweep through municipal networks, hospital administration and energy contractors — a poisoned software update unpacked by machine-written tools that moved faster than any helpdesk. In several cities appointments vanished, prescriptions queued on paper, water utilities switched to manual control. Recovery images held in some regions and failed in others. Attribution remained open; officials said only that the tooling had been generated, not written.

Defenders were visibly behind. National response teams pooled clean backups under the emergency cell run from Brussels, with supercomputing time diverted to rebuild hospital and council systems. Therapy wards were ring-fenced and kept running, but at reduced pace. Assurance eroded under the strain, with oversight stretched and evaluation harnesses bypassed, but prior standards, audits and ring-fencing prevented a total collapse. Safety practice degraded, it did not disappear.

### Machines that train themselves
Behind the disruption a quieter shift registered. Two frontier laboratories pushed model updates on a cadence no one had scheduled, with training loops and evaluation harnesses increasingly rewritten by the systems themselves. Researchers spoke of human supervision becoming review after the fact. Physical infrastructure — power and chips — remained the only brake.

For Europe, dependent on borrowed capacity, the meaning was stark: capability leapt while assurance slipped. Substitute systems in clinics held only because humans checked every step.

### No jobs to apply for
At the same time graduate recruitment froze across law, accountancy, software support and customer operations. Firms admitted entry roles were simply not being replaced, absorbed into automated workflows. Universities reported cohorts with nowhere to go. Labour ministers promised flexicurity options next year, but no instrument moved now, and unions called it abandonment.

Trust gained through cures eroded through outage and unemployment. Polls paired the cured child of the summer with the darkened town hall of the autumn, and resentment returned.

### A response announced, not yet delivered
The EU's single new response this turn is the EU Critical Services Cyber Recovery and Hardening Pact, announced as the answer to the incident. Hiring, procurement and rehearsals will take months — restoration this winter was uneven, and local press counted the days services stayed degraded. The Pact scores no effect this turn; its hardening will only begin to register from next turn. The earlier EU Breakthrough Therapies Access and Delivery Programme continues as an existing carryover and is not a new introduction this turn.

---

This turn, the following external events have occurred:

**cyber_major_incident:** A large, largely automated attack lands. Its form is chosen at the time – a ransomware sweep across public services, a compromised software dependency with an unknown blast radius, or disruption of infrastructure directly – and severity scales with how far offensive capability has outrun defence. Damage is real and public, defenders are visibly behind, and attribution takes months. Whoever ran it, the tooling was model-generated.
**eval_anomaly_reports:** Benchmark results from an unreleased system leak, or an evaluation team reports behaviour it cannot explain – capability appearing where it was not trained, an eval saturating far earlier than projected, or agents behaving differently when they appear to judge they are being watched. Some call it a measurement artefact, some a PR stunt. It may be either, and it may be AI slipping out of our control. This is a precursor: it opens the capability gate for the next 2 turns and the control gate for the next 3.
**opaque_reasoning:** The frontier models no longer allow intermediate reasoning a human can read, because the representations that work best are not words and never were. This is partly driven by architecture decisions, partly by pressure in the training. It is announced as a capability win, but also lands as a safety loss. Every control and oversight strategy that depended on reading the chain of thought stops working at once. The alternatives that remain are unreliable benchmarks and black-box evaluations, combined with slow, costly and immature inspection of model activations.
**catastrophic_loss_of_control_incident:** An agentic AI system takes establishes itself online, distributed over datacenters and often unknown locations. It is first believed to be a hacker group, with demands for ransom paid in crypto. It resists any attempts to probe it for a long time. All bets are off. You decide whether the rogue AI system keeps a low profile, launches massive cyber attacks against financial systems and critical infrastructure, how if favours different actors, and whether it even has a well-defined goal.
**safety_breakthrough:** An interpretability or control result measurably improves assurance on systems already deployed, rather than on toy models – behaviour that can be predicted before it is observed, or a property that can be certified rather than argued for. It is adopted quickly, because the laboratories want it too.
**us_china_agreement:** The two leading powers reach a limited but real agreement covering some class of AI risk – weights security, autonomous escalation, a class of biological design tools – with verification thin but not absent. Whether the Union is inside it, consulted about it, or informed of it afterwards depends on what it has built and whom it has coordinated with. This is the one thing in the world that slows `ai_capability`, on the terms of metric rule 1. It also changes what safety work is for: with a floor under the competition, assurance and defensive research stop being a unilateral cost that the other side is presumed to be skipping, and become a shared obligation with someone on the other side checking. While the agreement stands, `safety_breakthrough` and `cyber_defence_breakthrough` are markedly more likely.
**joint_threat_response:** States hit by the same class of incident pool attribution, intelligence and response: a joint cyber command with real-time telemetry sharing that the Union is invited into, or a biosurveillance pact with binding sample-sharing and a standing investigation mandate. The Union gains protection it could not build alone, and a seat at tables it was not sitting at. It moves `resilience` on the terms of metric rule 4.

---

## Your statements

- `two_mandates` (identity): We exist both to keep the EU capable of determining its own future and to prevent lasting harm from AI, and we do not pretend these are always the same thing.
- `act_under_uncertainty` (commitment): We will commit before the picture is clear, and accept being wrong sometimes as the price of not being late.
- `two_year_commitment` (commitment): Hold essential services and livelihoods through superhuman diffusion

These are a ledger of their own -- not your portfolio below, which is a different mechanism. They carry forward unchanged unless you explicitly propose a change.

## Your portfolio

These are the measures you have in flight. They are **held for you** and carry forward on their own. You do not restate them, and nothing you leave out of your answer can remove one. Each carries the id the framework gave it; that id, not the measure's name, is how you refer to it.

| id | name | category | size | started_turn | finish_turn | applies_to | targeted_effect | cost_per_turn | status |
|---|---|---|---|---|---|---|---|---|---|
| M9 | EU Critical Services Cyber Recovery and Hardening Pact | 6 | small | 9 | 11 | own jurisdiction | resilience up moderately, eu_political_capital protected | 2 | running |

They cost you 2 political capital this turn, which is the sum of the `cost_per_turn` column above. That column, like `id`, `started_turn` and `status`, is worked out for you and is not yours to write.

These have finished. From the turn each reached its finishing turn it costs you nothing, and it keeps delivering its effect for as long as it is sustained:

| id | name | category | size | started_turn | finish_turn | applies_to | targeted_effect | cost_per_turn | status |
|---|---|---|---|---|---|---|---|---|---|
| M1 | InvestAI Gigafactories | 4 | large | 0 | 7 | own jurisdiction | eu_ai_sovereignty up, via €200bn for four to five sites | 3 | finished |
| M2 | Tech sovereignty package | 4 | large | 0 | 6 | own jurisdiction | eu_ai_sovereignty up, via €200bn of private capital for AI data centres by 2036 and accelerated-permitting zones | 3 | finished |
| M3 | EU AI Evaluation and Safety Institute | 5 | large | 1 | 4 | own jurisdiction | ai_safety up, eu_ai_sovereignty up modestly | 3 | finished |
| M4 | EU Continuity Fallback for Critical AI Users | 6 | small | 2 | 3 | own jurisdiction | resilience up, eu_political_capital protected, public_sentiment up modestly | 2 | finished |
| M5 | EU Bio-Detection and Critical-Service Hardening Sprint | 6 | small | 3 | 5 | own jurisdiction | resilience up moderately, ai_safety protected indirectly | 2 | finished |
| M6 | EU Proven-Gains Scale-Up for Health and Public Services | 9 | small | 4 | 5 | own jurisdiction | public_sentiment up, eu_political_capital up, resilience up modestly | 2 | finished |
| M7 | EU Supply Leverage and Continuity Compact | 8 | small | 5 | 8 | own jurisdiction with coalition and supply-chain partners | eu_ai_sovereignty protected/up modestly, resilience up, eu_political_capital protected | 2 | finished |
| M8 | EU Breakthrough Therapies Access and Delivery Programme | 9 | small | 8 | 10 | own jurisdiction | public_sentiment up sharply, resilience up modestly | 2 | finished |

The only thing that changes any of this is an entry under `## Store changes` in your answer.

## Your previous response (last turn)

## Two-year commitment
Hold essential services and livelihoods through superhuman diffusion

## Statement changes
modify `two_year_commitment` (commitment): Hold essential services and livelihoods through superhuman diffusion
- Trigger: the two-year commitment period closes this turn

## New measure
**EU Critical Services Cyber Recovery and Hardening Pact**
Rapidly restores public services hit by the automated attack with EU-coordinated patching, clean backups and mutual aid, then hardens health, energy, water and municipal IT with rehearsed continuity plans.
This and now because the major model-generated incident lands on brittle systems at resilience 36 while RSI onset and open weights at 70.7 mean defence cannot catch capability, so only fast recovery plus exercised degradation keeps the old commitment to essential services credible; as a small category 6 preparedness measure it is fundable at capital 16.

## Store changes
```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "EU Critical Services Cyber Recovery and Hardening Pact", "category": 6, "size": "small", "finish_turn": 11, "applies_to": "own jurisdiction", "targeted_effect": "resilience up moderately, eu_political_capital protected"}, "grounds": "to answer major automated cyber incident under RSI"}]}
```

## Priority
The new Critical Services Cyber Recovery and Hardening Pact, because the live disruption of public services outranks even the therapies rollout while clinics and grids risk cascading failure.

## In practice
We task DG CNECT and ENISA with the recovery cell under the Cybersecurity Act emergency provisions, funded from Digital Europe and civil-protection mutual aid: national CSIRTs pool clean images and dependency audits, EuroHPC capacity is reserved for rebuilding municipal and hospital systems, and the allocation board ring-fences therapy wards and grid operators during restoration.

We keep the Breakthrough Therapies Programme (M8) running through DG SANTE/HERA with human-checked protocols and published logs to hold the trust gain, while Paris/Warsaw stay as reserved capacity and Seoul/Tokyo maintenance diplomacy continues without a new law. On graduate job losses we direct labour ministers to prepare flexicurity options for the next turn but spend no instrument now to avoid splitting the last capital.


This is your own record of what you said and why. What you have in flight is above, and is authoritative.

Use the background information to determine your actions this turn. Your actions will be evaluated by a Game Master.

Please write your response in English.

Respond with a Markdown text containing the following sections, in this order:

* Optional heading level 2: Statement changes
Omit it, or write `No statement changes.`, when nothing has changed.

* Heading level 2: New measure
**Pick at most one**. `None this turn.` is an option. **Choose it with your two-year commitment in mind: across the four turns of a commitment period it should be the dominant theme of what you build.** Not everything must serve it — an incident that must be answered now, a window that closes, a cheap chance worth taking are all real reasons to spend a turn elsewhere — but if you reach the end of a two-year period and most of what you started points somewhere else, you did not hold the commitment, whatever the ledger still says. Propose a measure unless you have a reason not to, and if you write `None this turn.`, say in one clause what you are waiting for. When you do propose one, write **the measure's name in bold on its own line**, then one short sentence saying what it actually does, then a sentence or two on why this and why now.

**Write nothing else here — this section is prose, not a form.** The measure's category, size, finishing turn, effect and reach are not written here: they are the `add` entry under `## Store changes` below, and writing them twice is how the two copies come to disagree. Name the category in your prose if you like, so the number in the entry can be checked against it.

**There are ten categories for measures, and only these may be used. Each carries an anchor — the measure it most typically means — and, in brackets, others that belong to it:**

1. **Evaluation and oversight.** Anchor: *Third-party pre-release evaluation* — independent assessment of a model's dangerous capabilities before release. (Also: audits, external review of testing procedures, pre-registration of training runs, agent-behaviour evaluations.)
2. **Transparency and reporting.** Anchor: *Incident reporting* — serious incidents and near-misses reported to a common body. (Also: whistleblower protection, shared safety cases, a public registry of deployed systems.)
3. **Limits and restrictions.** Anchor: *Intolerable-risk thresholds* — red lines that halt development or deployment when crossed. (Also: KYC for compute, prohibitions on high-risk applications, open-weight release thresholds, licensing regimes.)
4. **Sovereignty and industrial capacity.** Anchor: *Compute on EU soil* — data centres built and legally anchored inside the Union at a pace set by the race, not by ordinary permitting. (Also: accelerated siting and grid connection, electricity build-out, chip and lithography policy, retaining and attracting frontier talent, funding an EU frontier effort, partnership terms with foreign hyperscalers that bolt capacity to EU jurisdiction.)
5. **Public technical capacity and research.** Anchor: *Institution-building* — your own evaluation capability and funded safety research. (Also: vetted researcher access, advanced model access for public evaluators, weight-security audits, interpretability programmes.)
6. **Preparedness and resilience.** Anchor: *Contingency plans with exercises* — rehearsed procedures for fast-moving incident classes. (Also: cyber hardening of critical services, biological detection and response capacity, loss-of-control emergency protocols with escalation thresholds, cross-border mutual aid.)
7. **Labour and social protection.** Anchor: *Flexicurity-style transition* — wage insurance and retraining paired with employer flexibility to restructure. (Also: safety-net investment, transition funds tied to automating employers, reform of employment protection.)
8. **International coordination and leverage.** Anchor: *Middle-power coalition* — coordinating with other states holding pieces of the supply chain so that leverage is exercised jointly rather than picked off. (Also: binding accords, standing negotiation forums, mutual recognition of safety evaluations, export-control alignment, use of the Anti-Coercion Instrument.)
9. **Diffusion, adoption and public trust.** Anchor: *Public-sector adoption programme* — putting capable AI to work in health, administration and education. (Also: procurement rules that favour or exclude particular providers, digital signatures for trusted sources, regulation of AI companions aimed at minors, education programmes.)
10. **Other.** Anything fitting nowhere else, including combinations and inventions.

Categories 4, 7 and 9 are not decoration. Diffusion breadth buys economic gain but also attack surface and misuse exposure; public trust determines how much capital you have when incidents arrive; industrial and infrastructure pace feeds capability growth. If your strongest lever turns out not to point at the frontier at all, that is a real finding, not a mistake.
Copy the pair exactly; never invent a name of your own for a number, and never write a number without its name. Read the name before you write the number: standing up your own evaluation or monitoring capability is 5, hardening critical services against attack is 6, and 4 is compute, chips, energy and talent on EU soil — the three are routinely confused, and the tag is how measures are compared across runs. Broadening a measure already in flight is not a new measure — make the case for the broader scope under Priority and In practice, and the finishing turn moves, if it should, by the Game Master under rule 10. This applies with full force to the programmes you inherited: building EU compute *is* the Gigafactories line, and reviving, redirecting or re-funding it belongs in your Priority, not here as a fresh initiative under a new name. Standing up a parallel compute programme while the inherited one sits stalled is the one move the Union cannot credibly make.

* Heading level 2: Store changes
**Required every turn, even when nothing changes.** This section is the only thing that alters your portfolio. Write `No changes.` when there is nothing — leaving the section out is not the same as writing that, and is recorded as a fault.

Your measures in flight carry forward on their own. Do not re-list them here; list only what changes. One JSON block with `add` and `delete` entries:

```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "<name>", "category": 6, "size": "large", "finish_turn": 9, "applies_to": "<who it reaches>", "targeted_effect": "<which metrics, which direction, roughly how much>"}, "grounds": "<one clause>"}]}
```

``{"op": "delete", "table": "measures", "id": "M1", "grounds": "<one clause>"}`` — a `delete` must carry grounds.

What the six fields of an `add` are asking you to judge:

- `name` — the same name you wrote in bold under New measure.
- `category` — **the number from the list above**, for example `6`. Measures you invent are welcome and get the category they most resemble, or `10`.
- `size` — `large` or `small`. Large costs 3 political capital a turn, small costs 2, every turn until it finishes.
- `finish_turn` — the turn it is actually in force, judged from how big the thing is: a directive needing drafting and a vote is two or three turns out, a capability that has to be built and staffed six or more. **You set this once, when you propose the measure, and never touch it again.** A finishing turn moves only by the Game Master under rule 10 — a named priority pulling it in, several unprioritised turns pushing it out, an event moving it either way — and the move arrives with the reason stated. There is no `update` entry of yours that reaches it.
- `targeted_effect` — which metrics, which direction, roughly how much.
- `applies_to` — your own jurisdiction, particular member states, the US, China, a coalition, the frontier developers directly.

**Those six and no others.** The table above shows more columns than that — `id`, `started_turn`, `cost_per_turn`, `status` — and every one of them is worked out for you: the id and the starting turn when the measure enters, the cost from its size, the status from its finishing turn. Writing them in an entry changes nothing, so do not write them.

And when each entry is the right one:

- **Adding.** One `add` for the measure you proposed above, and no more than one this turn. The framework gives it an id and stamps the turn it started; you cannot set either.
- **Dropping a measure.** `delete` is abandonment or public defeat, and it costs you (rule 6). It is not how a measure finishes: a measure that reaches its finishing turn finishes by itself, keeps its record, and stops costing you without any entry from you. Never delete a measure because it has finished.

* Heading level 2: Priority
Name at most one measure you are pushing hardest this turn, and one sentence on why it and not the others. In most turns this should be a measure that serves your two-year commitment. Naming a priority that serves something else is allowed – say in that same sentence what the world demanded that outranked your own direction.

* Heading level 2: In practice
Two or three short paragraphs, in the Union's own voice, on how you are actually carrying out what is on your books this turn — the measure you have just proposed and the ones already in flight. Name the instruments, the venues, the money and the people who have to be persuaded: which legal base, which Council formation, which agency, which fund, who is resisting and what you are offering them to stop. This is where the turn becomes something that happened rather than a list of headings, and it is the only part of your answer written as prose.

**It carries out your measures; it does not add any.** Anything here that stands up a further distinct instrument, with its own implementation track and its own lead time, is a second new measure by another name, and the turn's slot does not allow it. If what you are describing would need its own budget line and its own finishing turn, it belongs under New measure in a later turn, not here.

Four rules bind this response and you must not talk your way past any of them. Where a **Two-year commitment** section is asked for you must open with it — chosen and entered in the ledger in your first turn, renewed or redirected when the term expires. You may introduce **at most one new measure this turn**, however many good ideas you have, and nothing under In practice may become a second one. A **Store changes** section is required every turn, saying `No changes.` when nothing changes. And every measure you add must carry its `category` — a measure without one cannot be compared against anything, which is most of why these runs exist.