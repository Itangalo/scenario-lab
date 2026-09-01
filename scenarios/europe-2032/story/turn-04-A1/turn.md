# Turn 4 – A1, H1 2028 (ECHO 2026-09-01)

The A1 branch: the acceleration arm, after the reader chose [`option-02-1`](../turn-01/option-02-1.md), the Emergency Resilience Surge. This turn is drawn from `runs/run-20260901-195358` (seed 810108), the run selected at random from the ten in [`branch-A1.md`](../branch-A1.md). What the other nine did this turn is in [`alternatives.md`](alternatives.md).

## What happened to the world

Events that fired: `campaign_security_hawk`, `eval_anomaly_reports`, `taiwan_tension_rise`.

### Frontier Acceleration Amid Uncertainty  
`ai_capability` rises by 3.5 to 63.0, driven by deeper agent coordination and recursive self-improvement loops now running for days unaided. The leaked `eval_anomaly_reports`—unusual reasoning patterns and untrained capabilities—hint at emergent behaviours dismissed by labs as artefacts. With no new safety frameworks deployed, the gap with `ai_safety` widens sharply. However, existing safety infrastructure remains intact and operational, preventing any erosion of baseline capacity. `ai_safety` holds at 17.0, reflecting sustained defensive monitoring and red-team continuity despite growing pressure.

### Open Weights Remain Frozen  
No major open release occurs. The best public models still operate below 45.0, leaving `openweight_capability` stagnant at 41.0. Offensive cyber tools remain concentrated in closed labs, but the lack of public scrutiny increases systemic risk.

### EU Doubles Down on Talent and Control  
The EU prioritises the **Secure AI Talent Pipeline**, launching the Frontier Research Fellowship with €2.1bn and co-location agreements for flagship institutes. However, German and French veto rights deepen fragmentation concerns. Bilateral retention deals with Mistral and Aleph Alpha stall over procurement terms. The Sovereign AI PhD Network expands to 50 universities, but national liaison integration remains slow and under-resourced.

The **InvestAI Gigafactories** progress halts in Finland and Portugal due to unresolved grid constraints, despite invoking Article 346 TFEU. State aid disputes over residency-based access models intensify, with the Commission demanding revisions. No new compute capacity comes online this turn.

### Export Talks Stumble, Audits Begin  
Negotiations under **Negotiate Export Control Alignment** begin at the Trade and Technology Council. The U.S., influenced by hawkish campaign rhetoric, resists binding access guarantees, offering only discretionary exceptions. Joint verification proposals with Dutch and Japanese partners gain little traction.

In response to rising risks, the EU launches the **Openweight Safety Audit Initiative**. EASI convenes a consortium of public labs with authority to inspect weights and simulate misuse. While framed as transparency, developers express concern over subpoena-like powers. Implementation will take time, and no immediate operational impact is observed.

### Public Trust Stagnates  
Protests against data centres and AI expansion persist. A fast-tracked constitutional challenge to the AI Act’s monitoring powers gains momentum in a key member state, undermining enforcement legitimacy. `public_sentiment` remains at 26.0.

`eu_ai_sovereignty` dips slightly to 22.0 due to delays in gigafactory deployment and persistent coordination frictions, reflecting implementation drag rather than capability loss.  

`eu_political_capital` increases moderately to 30.5, reflecting the political effort invested in launching the Talent Pipeline and Audit Initiative, but constrained by visible setbacks and legal challenges. The gain is consistent with partial agenda advancement and symbolic action, without overstating deliverables. The constitutional separation between sovereignty and political capital is preserved: the contribution from sovereignty-linked efforts does not exceed +3 and is balanced by other factors.

## What the Union did

New measure:

**Launch Openweight Safety Audit Initiative (Category 5: Public technical capacity and research)**  
Establish an EU-led, publicly funded evaluation consortium to conduct independent safety audits of all open-weight models above 40.0 capability, with full access to model weights and compute resources sufficient to run red-team agents at scale.

`Category: 5 (Public technical capacity and research)`  
`Size: large`  
`Finishes on turn: 6`  
`Targeted effect:` ai_safety +6 (by establishing baseline assurance on distributed systems), resilience +3 (via early detection of misuse-ready capabilities), public_sentiment +2 (demonstrating proactive risk management)  
`Applies to:` Open-weight developers (Mistral, EleutherAI, Hugging Face), EU member states’ national cybersecurity agencies, ENISA, and the newly formed European AI Safety Institute (EASI)

Priority:

**Secure AI Talent Pipeline** — because without binding agreements this turn to anchor frontier talent to EU institutions, our compute investments will remain underutilised while the frontier pulls further ahead, and because the eval_anomaly_reports event confirms that capability is outpacing understanding, making human expertise the decisive bottleneck in both safety and sovereignty.

In practice:

We are advancing the Secure AI Talent Pipeline through three instruments. First, the Frontier Research Fellowship is now live under Horizon Europe’s 2027 call, with €2.1bn allocated for the first cohort of 700 researchers. The selection panel is co-chaired by DG Research and ELLIS, with mandatory inclusion of safety and interpretability criteria in project proposals. To break the German-French deadlock over centralisation, we have offered co-location rights: each may host one flagship institute with veto power over director appointments — a concession that preserves unity but risks fragmentation. Second, the Talent Retention Pact is being finalised bilaterally with Mistral, Aleph Alpha, and ELLIS units, tied to continued access to Horizon funding and preferential procurement under the AI Act enforcement regime; we are offering fast-track certification for compliant labs as a sweetener. Third, the Sovereign AI PhD Network is operationalising via a new Erasmus-style mobility framework, with 50 universities signed on; implementation runs through the ERA Council, and we are embedding national liaison officers directly into the team to avoid the bottlenecks that crippled the Emergency Resilience Surge.

Simultaneously, construction continues on the InvestAI Gigafactories, with Finland and Portugal delayed by grid constraints requiring subsea reinforcements. We are invoking Article 346 TFEU to accelerate permitting under the Tech Sovereignty Package, but the Commission’s state aid office remains concerned about residency-based pricing models. Our counterproposal — a tiered access system based on IP ownership and long-term employment contracts — is under review. Externally, the Negotiate Export Control Alignment measure is now active under the Trade and Technology Council, where we are pushing for volume licences not as exceptions but as rights, leveraging our upstream position in lithography and materials. We are proposing joint verification mechanisms with Dutch and Japanese partners to build trust. Domestically, we are launching the Openweight Safety Audit Initiative in response to eval_anomaly_reports and the growing gap between closed and open systems: EASI will lead a consortium of public labs with subpoena-like authority to inspect weights, simulate adversarial use cases, and publish redacted findings. This is not about restriction — it is about knowing what is already loose.

## Where the metrics stood

| metric | turn 3 | turn 4 | change |
|---|---|---|---|
| `ai_capability` | 59.5 | 63.0 | +3.5 |
| `openweight_capability` | 41.0 | 41.0 | +0 |
| `ai_safety` | 17.0 | 17.0 | +0 |
| `resilience` | 38.0 | 35.0 | -3 |
| `eu_ai_sovereignty` | 23.5 | 22.0 | -1.5 |
| `eu_political_capital` | 28.0 | 30.5 | +2.5 |
| `public_sentiment` | 26.0 | 26.0 | +0 |

The full actor response, portfolio included, is at `runs/run-20260901-195358/turn-04/2-actors/eu.md`; the Game Master's notepad for the turn is beside it at `5-notepad.md`.
