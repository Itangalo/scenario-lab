# Turn 3 – A1, H2 2027 (ECHO 2026-09-01)

The A1 branch: the acceleration arm, after the reader chose [`option-02-1`](../turn-01/option-02-1.md), the Emergency Resilience Surge. This turn is drawn from `runs/run-20260901-195358` (seed 810108), the run selected at random from the ten in [`branch-A1.md`](../branch-A1.md). What the other nine did this turn is in [`alternatives.md`](alternatives.md).

## What happened to the world

Events that fired: `campaign_backlash`, `export_control_escalation`.

### Frontier Gains Momentum
The global AI frontier advances steadily, with leading labs achieving tighter agent coordination and early recursive self-improvement loops. `ai_capability` rises by 3.5 to 59.5, reflecting sustained progress. However, no new evaluation frameworks have been deployed, and the opacity of internal reasoning in these systems deepens. The gap between capability and safety widens, driving `ai_safety` down by 5 to 17.0.

### Open Weights Left Behind
No major open-weight release occurs. The latest closed models operate in agentive, long-horizon modes far beyond the reach of publicly available systems. `openweight_capability` remains at 41.0, now lagging by 18.5 points — a gap that enables powerful offensive cyber tools in private hands while leaving them out of reach for most defenders.

### EU Pushes Talent and Access
The EU advances the Secure AI Talent Pipeline, launching the Frontier Research Fellowship with €2.1bn in Horizon funding. Germany and France agree to co-host flagship institutes, but only with veto rights over leadership — a concession that slows central coordination. The Talent Retention Pact gains tentative buy-in from Mistral and Aleph Alpha, tied to future procurement advantages. However, national implementation bottlenecks persist.

Construction on InvestAI Gigafactories continues, though site finalisation in Finland and Portugal is delayed by grid constraints requiring costly subsea reinforcements. Article 346 TFEU is invoked to accelerate permitting, but state aid concerns over residency-based access models spark internal disputes.

### Export Talks Begin, Backlash Grows
The EU opens high-level talks under the Trade and Technology Council to secure guaranteed access to advanced chips, leveraging its position in lithography and materials. However, the U.S. signals it will ration allied access, framing controls as national security imperatives. Negotiations stall over verification mechanisms.

Meanwhile, public resistance intensifies. Campaigns for moratoriums on data centres and AI in public services gain mainstream traction. A protest in Bavaria disrupts a Gigafactory-related expansion, and polling shows growing cross-spectrum distrust. `public_sentiment` drops to 26.0.

## What the Union did

New measure:

**Negotiate Export Control Alignment (Category 8: International coordination and leverage)**  
Engage the United States and key allies in structured negotiations to align export control regimes on advanced AI chips and models, ensuring that EU access is secured under multilateral frameworks rather than unilateral discretion, while shaping the scope of controls to preserve European industrial and research competitiveness.

`Category: 8 (International coordination and leverage)`  
`Size: large`  
`Finishes on turn: 5`  
`Targeted effect:` eu_ai_sovereignty +8 (by locking in guaranteed access), ai_safety +3 (via shared verification protocols), indirect boost to public_sentiment through demonstration of strategic agency  
`Applies to:` United States, Japan, South Korea, Netherlands, Taiwan (via Dutch semiconductor partners), and the Quad-plus coordination format

Priority:

**Secure AI Talent Pipeline** — because talent is now the decisive bottleneck in sovereign capability, and without binding agreements this turn to anchor researchers to EU institutions, our compute investments will remain underutilised while the frontier pulls further ahead.

In practice:

We are advancing the Secure AI Talent Pipeline through three instruments. First, the Frontier Research Fellowship is being launched via Horizon Europe’s 2027 call, with €2.1bn allocated for the first cohort of 700 researchers. The selection panel will be co-chaired by DG Research and the European Lab for Learning and Intelligent Systems (ELLIS), with mandatory inclusion of safety and interpretability criteria in project proposals. Germany and France continue to resist centralisation, so we are offering them co-location rights: each may host one of the two flagship institutes, with veto power over director appointments. Second, the Talent Retention Pact is being negotiated bilaterally with major EU-based AI labs — including Mistral, Aleph Alpha, and the ELLIS units — tied to continued access to Horizon funding and preferential procurement under the upcoming AI Act enforcement regime. Third, the Sovereign AI PhD Network is being operationalised through a new Erasmus-style mobility framework, with 50 universities signing letters of intent; implementation runs through the ERA Council in December.

Simultaneously, construction continues on the InvestAI Gigafactories, with final site decisions delayed by grid capacity assessments in Finland and Portugal — both now require subsea cable reinforcements funded jointly by national governments and the Connecting Europe Facility. We are invoking Article 346 TFEU to fast-track permitting under the Tech Sovereignty Package, but the Commission’s state aid office has raised concerns about preferential pricing for EU nationals; we are countering with a tiered access model based on residency and IP ownership. The Emergency Resilience Surge has concluded, and ENISA is now transitioning to a standing monitoring role under the revised NIS2 framework, though only 40% of funds reached implementation due to national bottlenecks — a lesson we are applying by embedding national liaison officers directly into the Talent Pipeline’s implementation team to prevent repetition.  

Externally, the tightening of U.S. export controls threatens to cut off EU labs from next-generation chips unless we act. With American policy shifting toward rationing even allied access, we are launching high-level talks under the Trade and Technology Council (TTC) to negotiate volume licences not as exceptions but as rights under a shared democratic technology agenda. Our leverage lies in the EU’s upstream position in lithography (ASML), materials, and metrology; we are proposing joint control verification mechanisms and reciprocal access guarantees. This is not non-proliferation — it is alliance architecture for the AI era.

## Where the metrics stood

| metric | turn 2 | turn 3 | change |
|---|---|---|---|
| `ai_capability` | 56.0 | 59.5 | +3.5 |
| `openweight_capability` | 41.0 | 41.0 | +0 |
| `ai_safety` | 22.0 | 17.0 | -5 |
| `resilience` | 38.0 | 38.0 | +0 |
| `eu_ai_sovereignty` | 22.5 | 23.5 | +1 |
| `eu_political_capital` | 39.0 | 28.0 | -11 |
| `public_sentiment` | 28.0 | 26.0 | -2 |

The full actor response, portfolio included, is at `runs/run-20260901-195358/turn-03/2-actors/eu.md`; the Game Master's notepad for the turn is beside it at `5-notepad.md`.
