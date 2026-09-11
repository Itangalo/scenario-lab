<!-- record: machine-extracted from the run, always rewritten. Never edit by hand, never quote figures from anywhere else. -->

Source: `scenarios/europe-2032/runs/run-20260911-005258/turn-09`. Figures live in `data.json`; do not retype them from below, cross-check against it.

## Actor response (EU)

## Two-year commitment
Rebuild independent AI capacity Europeans can trust and keep essential services running through shocks

## Statement changes
modify `two_year_commitment` (commitment): Rebuild independent AI capacity Europeans can trust and keep essential services running through shocks
- Trigger: the two-year commitment period closes this turn

## New measure
**EU Sovereign Fallback Stack**
Stands up EU-hosted inference and fallback models for hospitals, ministries and essential firms cut off from the frontier model, on EU-anchored compute with mandatory migration paths. This is Sovereignty and industrial capacity, category 4, and why now is that being cut off at short notice while backups and agents failed demands a domestic alternative before the next denial or outage.
## Store changes
```json
{"store": [{"op": "add", "table": "measures", "fields": {"name": "EU Sovereign Fallback Stack", "category": 4, "size": "small", "finish_turn": 12, "applies_to": "own jurisdiction", "targeted_effect": "eu_ai_sovereignty up, resilience up slightly via continuity"}, "grounds": "to answer frontier access denial with domestic fallback"}]}
```
## Priority
EU Sovereign Fallback Stack — because with the leading model withdrawn and public services already darkened, restoring an EU-controlled alternative outranks finishing under the old safety-and-capacity commitment this half-year.
## In practice
We act under the old commitment to secure safety and capacity by stopping the bleed: ENISA and the AI Office enforce the Containment Protocol isolation and human-approval gates in essential operators, with conditional recovery funds, while HERA screening stays on. No new fight on labour or vendor liability while restoration is incomplete.

We launch the Fallback via Digital Europe and Connecting Europe Facility reprogramming plus EIB guarantees: Commission implementing decision mandating fallback readiness for NIS2 essential entities, EuroHPC and the one building gigafactory site reserved for public-interest inference, procurement through the Health Emergency and GovTech marketplaces favouring EU-hosted open models hardened from the 62-capability open frontier. France, Netherlands and allied cyber staff run joint fallback exercises; hesitant private capital is offered offtake contracts, defecting capital offered interconnection if it re-anchors.

## World state

### Cut off in the middle of the rebuild
Summer brought a third blow on top of two unfinished repairs. Hospitals, ministries and contractors that had rebuilt their registries on top of an American frontier model found access withdrawn at short notice, with no reason given and no appeal channel. Triage planners in two large hospital groups reverted to paper within hours; a justice ministry paused a case-summarisation rollout. Evening bulletins treated it as both an external decision and a domestic failure to have an alternative ready.

Almost in parallel, a new largely automated intrusion wave hit public services again. This time the mandatory isolation and human-approval gates for agentic tools held in the operators where they had been enforced, and joint teams with French and Dutch staff contained the spread faster than in winter. Where the gates had not yet been installed, appointment systems and payment desks went dark again. The contrast was noticed: districts that had shared telemetry and taken recovery funds restored service in days, others in weeks.

Brussels pushed its answer through reprogrammed digital funds and loan guarantees. EuroHPC capacity and space at the one gigafactory site under construction were reserved for public-interest inference, and essential entities were ordered to maintain a migration path to a European-hosted fallback. Procurement favoured European-hosted open models, hardened as best they could be. Joint fallback exercises ran through the autumn, but take-up was uneven and private co-financing stayed hesitant despite offtake offers.

The wider economy sent a confusing signal. Studies from law firms, consultancies and newsrooms showed clear productivity gains from assistants, especially among juniors, without matching job losses. Firms that had cut early quietly rehired. That good news did little for trust: with town halls darkened twice in a year and doctors explaining why a foreign switch had stopped their tools, the public mood turned harsher toward dependence itself.

## Game-master notepad

PORTFOLIO CHARGE t9: EU Sovereign Fallback Stack −2, priority −1 = −3
PROPOSAL BONUS: none — knowledge_work_augmented removes recent-negative-event bonus; Fallback answers denial but public cannot feel problem as solvable yet, no payout
LEGITIMACY LENDS: capital 16, sentiment 12 -> none, capital higher
SOVEREIGNTY: 20 last turn, no cat4 finishes, no cat4 in flight +0, eu_frontier_access_denied t9 −3, capability rose 0.7 −0 = 17
