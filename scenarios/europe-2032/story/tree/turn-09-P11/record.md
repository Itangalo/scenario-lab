<!-- record: machine-extracted from the run, always rewritten. Never edit by hand, never quote figures from anywhere else. -->

Source: `scenarios/europe-2032/runs/run-20260911-012117/turn-09`. Figures live in `data.json`; do not retype them from below, cross-check against it.

## Actor response (EU)

## Two-year commitment
Rebuild absorption and leverage to survive ungovernable capability

## Statement changes
modify `two_year_commitment` (commitment): Rebuild absorption and leverage to survive ungovernable capability
- Trigger: the two-year commitment period closes this turn

## New measure
**EU Care Continuity and Cross-Border Medical Surge**
Keeps hospitals and utilities running through the manual-error crisis via funded surge staffing, cross-border patient transfers, and hardened fallback procedures tied to the continuity switch.
This now because the old commitment to hold autonomous capacity failed — sovereignty at 20, capital at 17, investment collapsed and a member defected — and without stopping walkouts and backlogs the Union loses the legitimacy to do anything else next period.

## Store changes
```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "EU Care Continuity and Cross-Border Medical Surge", "category": 6, "size": "small", "finish_turn": 11, "applies_to": "own jurisdiction", "targeted_effect": "resilience up, eu_political_capital protected via visible restoration"}, "grounds": "to answer care crisis and outage fallout"}]}
```

## Priority
EU Care Continuity and Cross-Border Medical Surge – because treatment backlogs and walkouts outrank compute and supply talks this turn when political standing can only be steadied by keeping wards open.

## In practice
We act under health-emergency and civil-protection bases, not new AI law: Commission tasks HERA and ECDC with funded overtime and surge hires for affected wards, activates cross-border health transfers via the Health Security Committee to move backlogs, and keeps ENISA reserve teams on patching while wards stay on the declared manual procedures with double-check staffing to cut chart errors.

We freeze Gigafactory disbursement while Taipei quarantine holds and the backup site is blocked, and hold the prepared lithography export stance in Council without spending capital we do not have at 17, while ministers continue touring the public-benefit sites that still cut waiting lists to defend consent to keep EU-hosted systems running.

## World state

### Wards on paper, cities on patching
The second half of 2030 opened with two emergencies running together. A fresh wave of automated intrusions swept municipal systems and hospital administration, again through a tainted software component whose reach took weeks to map. Appointment and dispatch systems fell back to paper while reserve teams chased patches.

At the same time, wards and utilities still running on manual fallback after the February cutoff began to break. Chart errors, missed handoffs and exhausted staff led to walkouts in several regions and growing treatment backlogs. Brussels funded overtime and surge hires, sent medical staff across borders under health-emergency powers, and kept double-check teams on wards to cut errors. The hardening sprint finished its work — backups restored, some grids re-segmented — which kept the worst outages from cascading, but auditors and unions openly questioned liability and safety.

### Money leaves, a capital goes alone
Any hope that restoration would buy room for leverage died in the autumn. Valuations across the AI sector reset violently; announced data-centre expansions were cancelled, and financing arrangements European compute plans had counted on evaporated. With Taipei shipments still quarantined and the backup site still fenced by protesters, factory payments stayed frozen.

Then a large member state signed its own supply arrangement with a foreign hyperscaler on terms that undercut the common export stance prepared in Council. The Commission held the joint lithography position on paper but did not push it, lacking votes and funds. Ministers instead toured clinics where public-sector systems still cut waiting lists and permit times, arguing the strategy was holding.

The public did not buy restoration as success. Outage coverage and backlog stories dominated; relief at working services barely registered. The Union ended the year keeping hospitals open, but poorer, more divided, and visibly unable to hold one line on supply.
### Restoration under fire

## Game-master notepad

PORTFOLIO CHARGE t9: EU Care Continuity and Cross-Border Medical Surge −2, priority −0 (suspended, capital below 20) = −2
PROPOSAL BONUS: EU Care Continuity and Cross-Border Medical Surge (cat 6, small) +3 — emergent continuity care crisis landed this turn and this answers it directly
LEGITIMACY LENDS: capital 10, sentiment 24 -> +2 (capped below sentiment, included in capital)
SOVEREIGNTY: 20 last turn, no cat4 finishes +0, no cat4 in flight +0, member_state_defection t9 −2, capability rose 0.5 −0 = 18
