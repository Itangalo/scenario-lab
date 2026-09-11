<!-- record: machine-extracted from the run, always rewritten. Never edit by hand, never quote figures from anywhere else. -->

Source: `scenarios/europe-2032/runs/run-20260911-084331/turn-10`. Figures live in `data.json`; do not retype them from below, cross-check against it.

## Actor response (EU)

## Two-year commitment
modify `two_year_commitment` (commitment): Hold the Union together through AI shocks by hardening critical services against automated attacks and cushioning displaced workers
- Trigger: the two-year commitment period closes this turn

## Statement changes
- modify `two_year_commitment` (commitment): Hold the Union together through AI shocks by hardening critical services against automated attacks and cushioning displaced workers
- Trigger: the two-year commitment period closes this turn
- Grounds: Keeping essentials alive through blackouts was met narrowly but legitimacy collapsed — political capital 10, sentiment 2 — while the next shocks are an automated cyber sweep, verifiable-domain capability jump, and entry-level white-collar displacement under tighter export controls. The next two years must answer disruption and jobs, not just power.

## New measure
**EU Critical Services Cyber Recovery Corps and Dependency Patching Pact**
Puts joint ENISA/CERT-EU teams, pre-funded vendor patch contracts and offline fallback procedures into municipalities, hospitals and grid operators hit by the automated attack wave.
This and now because the major model-generated incident lands on brittle systems with resilience 37 and safety 24, and without a visible defender-ahead response the last capital and trust evaporate; it is category 6 Preparedness and resilience, small and executable under CER/NIS2 and Civil Protection within one turn.

## Store changes
```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "EU Critical Services Cyber Recovery Corps and Dependency Patching Pact", "category": 6, "size": "small", "finish_turn": 12, "applies_to": "own jurisdiction", "targeted_effect": "resilience up moderately, eu_political_capital up slightly if recovery visible"}, "grounds": "automated cyber sweep demands immediate containment"}]}
```

## Priority
EU Critical Services Cyber Recovery Corps and Dependency Patching Pact, because it is the only in-flight measure and the cyber incident plus second blackout winter will decide whether any next commitment is credible.

## In practice
We run this as a NIS2 Article 11/12 operation: ENISA and CERT-EU stand up three mobile recovery corps drawn from national CSIRTs and contracted vendors, deployed first to the ransomware-hit public services and compromised-dependency users, with EU-CyCLONe coordinating daily patch and isolation notes. Funding comes from reshuffled Digital Europe and cohesion emergency envelopes — no new vote, ECOFIN written procedure only.

We pair it with the finished islanding kits: TSOs keep the compute-first curtailment order, hospitals and water stay islanded, and mayors get a single claims window for both energy relief and cyber recovery to counter the relabelled-money charge. We ask US volume-licence channels for expedited patch tooling while quietly sourcing open-weight assistance already on municipal hardware, since recall is impossible.

## World state

### The sweep
In February the attack came as warned: not a single intrusion but a wave of machine-written ransomware and a poisoned software library spreading through municipal IT, clinic booking systems and two grid operators. Screens froze, backups were wiped, patch notes arrived faster than staff could read them.

The new joint recovery teams were still hiring when it hit. Three mobile corps drawn from national response units and contractors deployed to the worst-hit cities, isolating servers, pushing vendor patches pre-paid from emergency funds, and falling back to the paper procedures and offline folders left from the winter blackouts. Where they arrived, water and hospitals stayed up. Where they had not yet arrived, services stayed down for days.

Brussels published daily technical notes and opened a single claims window for energy relief and cyber repair. Mayors said the money was the same envelope renamed twice. Data-centre operators curtailed for the grid in winter were now asked to lend clean capacity for recovery.

### Smarter tools, fewer jobs
At the same time an American laboratory demonstrated systems that write and break code, prove theorems and plan intrusions markedly better than before. Specialists argued about whether this was general progress; security teams felt the difference within weeks.

Tighter American chip and model controls followed, with allies kept on volume licences while others were cut off. European buyers kept access on paper, at higher prices and with new conditions.

By spring, graduate hiring in routine coding, analysis and support collapsed. Firms said entry-level drafts were now machine-made and checked by seniors. Unions called it a white-collar freeze; ministers called it transition.

Voters saw rationed power, ransomed town halls and vanishing first jobs, and blamed the machines. Trust fell to nothing.

## Game-master notepad

PORTFOLIO CHARGE t10: EU Critical Services Cyber Recovery Corps and Dependency Patching Pact −2, priority −1 = −3
PROPOSAL BONUS: EU Critical Services Cyber Recovery Corps and Dependency Patching Pact (cat 6, small) +3 — cyber_major_incident landed this turn and this answers it directly
LEGITIMACY LENDS: capital 5, sentiment 0 -> none, capital higher
SOVEREIGNTY: 17 last turn, no capacity event finishing, no category 4 in flight, export_control_escalation t10 −2, capability rose 1.0 no charge = 15
