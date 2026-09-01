# Turn 2 – A1, H1 2027 (ECHO 2026-09-01)

The A1 branch: the acceleration arm, after the reader chose [`option-02-1`](../turn-01/option-02-1.md), the Emergency Resilience Surge. This turn is drawn from `runs/run-20260901-195358` (seed 810108), the run selected at random from the ten in [`branch-A1.md`](../branch-A1.md). What the other nine did this turn is in [`alternatives.md`](alternatives.md).

## What happened to the world

Events that fired: `capability_jump`, `backlash_physical`.

### Frontier Advances Steadily

Leading labs demonstrate progress in agent coordination and recursive self-improvement research, building on trends observed in the previous half-year. These developments contribute to a measured rise in `ai_capability` to 56.0, consistent with the ongoing trajectory established since Turn 1. While the advancements are significant, they represent a continuation rather than a rupture in the rate of progress. The new architectures outpace existing evaluation frameworks, and no safeguards are ready to interpret or constrain their internal reasoning processes. As a result, oversight gaps widen and `ai_safety` falls sharply to 22.0, reflecting growing opacity in frontier systems.

### Open Weights Stagnate

No new open-weight release matches the capabilities of the latest closed models. Existing open models, including Kimi K3 derivatives, remain in circulation but show limited adaptation to emerging agent-based paradigms. `openweight_capability` holds at 41.0, highlighting the widening gap between open and closed development paths.

### EU Concludes Resilience Surge

The Emergency Resilience Surge formally concludes. ENISA reports partial success: AI-augmented detection systems are now mandated across most critical operators, and red-teaming exercises have exposed previously unknown vulnerabilities. The measure delivers a +3 boost to `resilience`, raising it to 38.0. However, only 40% of allocated funds reached deployment due to slow national absorption, revealing persistent bottlenecks in translating EU mandates into operational defences.

### Talent Pipeline Announced, Implementation Delayed

The EU announces the Secure AI Talent Pipeline as its new priority, pledging future investment to train and recruit 10,000 frontier researchers over the coming years. While the ambition signals long-term commitment, no funding source is yet secured — the proposed €18bn expenditure lacks parliamentary approval, borrowing authorization, or reallocation from existing programmes. France and Germany object to centralized governance, and implementation is stalled pending intergovernmental negotiations. Construction begins on two regional training hubs, but hiring remains minimal.

As a result, `eu_ai_sovereignty` sees only a modest increase to 22.5, reflecting early symbolic progress and infrastructure groundwork. The political cost of the priority is immediate: the portfolio charge rises by −1, and public backlash intensifies. A protest in Bavaria turns physical as activists disrupt a data centre expansion linked to the InvestAI Gigafactories, part of a broader wave of `backlash_physical`. Public sentiment declines to 28.0. Despite the +3 proposal bonus from concluding the Resilience Surge, `eu_political_capital` drops by one point to 39.0 due to high cost and low near-term payoff.

## What the Union did

New measure:

**Secure AI Talent Pipeline (Category 4: Sovereignty and industrial capacity)**  
Establish a pan-European recruitment, retention, and training programme to secure 10,000 frontier AI researchers and engineers within five years, with immediate deployment incentives and long-term academic-industrial integration.

`Category: 4 (Sovereignty and industrial capacity)`  
`Size: large`  
`Finishes on turn: 6`  
`Targeted effect:` eu_ai_sovereignty +15, public_sentiment +5 (via visible investment in high-skill jobs), indirect support to future measures in evaluation and research  
`Applies to:` EU member states, research institutions, and private AI labs operating in the Union

Priority:

**Secure AI Talent Pipeline** — because the capability_jump this turn confirms that the race is now defined by human capital as much as compute, and without sovereign access to frontier talent, our compute investments will run idle.

In practice:

We are launching the Secure AI Talent Pipeline to close the most critical gap in our sovereignty: people. The Gigafactories and Tech Sovereignty Package deliver silicon and sites, but they are useless without the minds to run them. The capability_jump — a discontinuous leap in agent coordination and self-improvement pathways — was not driven by hardware, but by tightly integrated research-engineering teams in a handful of closed labs. We do not have enough of these teams on EU soil, and the mobility of talent means we are losing them faster than we replace them.

This measure mobilises €18bn in combined public and private funding: €8bn from Horizon Europe and the Digital Europe Programme, matched by €10bn from national governments and industry partners like SAP, ASML, and the Max Planck Institutes. The core instruments are threefold: a *Frontier Research Fellowship* offering €250k packages (salary, lab budget, relocation) for 2,000 top-tier researchers over three years; a *Talent Retention Pact* with binding golden handcuffs and equity-sharing mandates for EU-based AI engineers; and a *Sovereign AI PhD Network* integrating 50 universities into a coordinated training pipeline focused on safety, resilience, and open-weight stewardship. Legal implementation runs through the European Research Area Council and the Internal Market Council, with conditionality tied to Horizon funding access. Resistance is expected from member states with strong national programmes — Germany and France — who fear brain drain *within* the Union; we are countering with co-location rights and shared governance on the fellowship board.

At the same time, we are concluding the Emergency Resilience Surge. ENISA has delivered baseline AI-augmented detection mandates to 87% of essential operators, and red-teaming exercises have been completed in 18 member states. The €12bn fund is being disbursed, but only 40% has reached implementation due to slow national absorption — a warning that resilience cannot be mandated from above without local capacity. The Gigafactories are now in detailed site negotiation, with two locations shortlisted (Finland and Portugal), but grid connection timelines remain at risk. The Tech Sovereignty Package is facing legal scrutiny over state aid rules; we are preparing a derogation argument based on strategic autonomy under Article 346 TFEU.

## Where the metrics stood

| metric | turn 1 | turn 2 | change |
|---|---|---|---|
| `ai_capability` | 54.5 | 56.0 | +1.5 |
| `openweight_capability` | 41.0 | 41.0 | +0 |
| `ai_safety` | 34.0 | 22.0 | -12 |
| `resilience` | 35.0 | 38.0 | +3 |
| `eu_ai_sovereignty` | 22.0 | 22.5 | +0.5 |
| `eu_political_capital` | 40.0 | 39.0 | -1 |
| `public_sentiment` | 30.0 | 28.0 | -2 |

The full actor response, portfolio included, is at `runs/run-20260901-195358/turn-02/2-actors/eu.md`; the Game Master's notepad for the turn is beside it at `5-notepad.md`.
