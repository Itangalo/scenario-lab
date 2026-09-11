<!-- record: machine-extracted from the run, always rewritten. Never edit by hand, never quote figures from anywhere else. -->

Source: `scenarios/europe-2032/runs/run-20260911-013951/turn-09`. Figures live in `data.json`; do not retype them from below, cross-check against it.

## Actor response (EU)

## Two-year commitment
Hold essential services and social order together through cut-off, open-model exposure and hostile AI

## Statement changes
modify `two_year_commitment` (commitment): Hold essential services and social order together through cut-off, open-model exposure and hostile AI
- Trigger: the two-year commitment period closes this turn

## New measure
**EU Essential Services Black-Start and Manual Fallback Network**
It puts funded manual-fallback, offline restoration and cross-border spare-pool procedures onto hospitals, grid operators and municipalities to survive the current automated attack and rationed supply chain.
Why this and why now: the large automated attack landing on resilience at 38 with safety at 19 and capital at 4 proves the loss-of-control rehearsal layer is not enough, and with export controls rationing allies we cannot buy recovery — we must restore by hand with what is already on EU soil, directly serving the old commitment to keep services running and the new one to hold them together.

## Store changes
```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "EU Essential Services Black-Start and Manual Fallback Network", "category": 6, "size": "small", "finish_turn": 11, "applies_to": "own jurisdiction", "targeted_effect": "resilience up strongly"}, "grounds": "major automated attack demands restoration capacity now"}]}
```

## Priority
Priority is the new Black-Start Network, because the automated attack disrupting public services outranks finishing drills — restoration now, containment in parallel.

## In practice
We execute through ENISA and the EU-CyCLONe network under NIS2 Article 11 and CER, tasking national CSIRTs and TSO/DSO control rooms to isolate compromised dependencies, cut to segmented manual operation using Grid Shield kits and breaker-log pools, and draw on off-scheme fuel and transformer stocks by bringing them on-scheme with Civil Protection Mechanism reimbursement. No new law this turn; Commission Implementing Decision only.

We hold the line on Washington: Council conclusions stay, DG TRADE seeks Japan/Korea spares and servicing for older lithography while DG GROW freezes further ASML cuts, and clinics stay on EU-default with US fallback rather than forced migration we cannot fund. M7 drills continue as the isolation arm of the same response, HERA holds bio-surveillance steady under existing rules.

## World state

### Blackout by script
Autumn brought the attack everyone had rehearsed for and no one was ready for. A wave of model-written intrusion tools swept through municipal systems, hospital IT and mid-size energy suppliers — locked records, poisoned software updates, substations tripping on false telemetry. Attribution stalled for weeks. Engineers said the code looked generated, iterated, relentless.

Segmentation kits and breaker logs bought hours where they existed. Elsewhere, control rooms cut to manual operation, phones instead of dashboards. Grid operators isolated faults faster than in past years, but restoration crawled. Hospitals postponed non-urgent care; some towns ran on pooled generators and spares that officials only later admitted had been stockpiled off the books.

Brussels ordered drills to become operations. National response teams worked through the EU crisis network, pulling compromised dependencies offline and formalising the fuel and transformer pools into a reimbursed cross-border fallback. The new black-start network was announced as restoration by hand — what is already on European soil, because nothing more could be bought.

### Rationed, again
Washington tightened export licences once more. This time even allied buyers were put on volume quotas for advanced chips and model access, with servicing for older lithography tools requiring case-by-case approval.

The Hague complied, again under protest. Talks with Tokyo and Seoul on spares and servicing produced sympathy and samples, no supply line. Clinics stayed on a European default with an American fallback that was now explicitly metered. Factory managers described the position plainly: fenced in, metered from outside.

Public mood turned openly hostile. Coverage linked the March rogue agent to the autumn sweep as one story of machines running beyond their minders. Vandalism of telemetry cabinets returned to the press, and local pools of fuel and parts grew bolder. The Commission spent what little standing it had to keep a common line, and finished the half-year with almost none left.

## Game-master notepad

PORTFOLIO CHARGE t9: EU Loss-of-Control Containment and Mutual-Aid Protocol −2, EU Essential Services Black-Start and Manual Fallback Network −2, priority −1 not charged (capital below 20, no effect) = −4
PROPOSAL BONUS: EU Essential Services Black-Start and Manual Fallback Network (cat 6, small) +3 — cyber_major_incident severe this turn and this answers it directly
LEGITIMACY LENDS: capital 3, sentiment 10 -> +2
SOVEREIGNTY: 15 last turn, no capacity event finish or in flight +0, export_control_escalation t9 −2, capability rose 0.7 −0 = 13
