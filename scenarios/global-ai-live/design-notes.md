# Design Notes – Global AI Live

Central question: in a 90-minute live workshop game for German politicians (non-experts), do participants feel that advanced AI is real and grasp its larger consequences over 2026–2029 – both the benefits (science, medicine, democratic support, drudgery lifted, robots) and the risks (jobs, disruption, information decay, EU dependence on the US, engineered pandemics, loss of control, US-China hot conflict)?

## What changed and why (2026-09-17 redesign)

- **Purpose rewritten:** was a generic capability-vs-governance race game; now a politician-facing game where every metric and event maps to a named risk or benefit in the brief.
- **Time horizon stretched:** `time_scale` was "6 months per turn" (18 months); now "1 year per turn" (2026–2029) so structural consequences (displacement waves, dependence, conflict spiral) have room to bite in 3 turns. Metric-rules growth steps raised accordingly (+8 to +18 capability per turn instead of +5 to +12).
- **Metrics replaced (4 → 8):** kept `frontier_capability`, `public_trust`, `governance_strength`; dropped `us_china_cooperation` (replaced by worse-upward `us_china_tension` – note the reversal when comparing to old runs); added `scientific_progress`, `labor_displacement`, `information_integrity`, `eu_us_dependence`. The three worse-upward metrics (`labor_displacement`, `eu_us_dependence`, `us_china_tension`) are flagged in-metrics.md so the room reads direction correctly.
- **Events rewritten (6 → 8):** all strictly exogenous – no actor actions (no blockades ordered, no controls imposed, no accords signed). Added `jobs_shock`, `information_crisis`, `science_windfall`, `bio_misuse_scare`, `control_scare`, `strait_clash` (an accident nobody ordered, so the hot-conflict risk stays exogenous); kept capability-leap and compute-bottleneck ideas. Probabilities 10–20% per turn so 1–3 events typically fire per 3-turn game.
- **Actors retuned, ids unchanged** (`us-gov`, `us-labs`, `china`, `eu`): descriptions rewritten for the new theme; statements kept at 3 each with position/commitment/identity mix; EU bridge-mediation replaced by sovereign-capacity (dependence theme), US added jobs framing, China added crisis-aversion.
- **Background rewritten:** compact mid-2026 world state aimed at non-experts (AI as infrastructure, where the lead sits, what daily life already shows). Original text, shorter than europe-2032's; read europe-2032's background and events for tone/scale first.
- **Workshop block retuned:** audience is now German politicians without AI background; tone vivid but never sensationalist. `output_language` stays default (English) – the facilitator switches per event with --override.
- **Unchanged by brief:** max_turns 3, no `store:` block, no constitution, rules frozen all turns, cheap LLM config (muse-spark on OpenRouter + minimal reasoning + qwen referee).
- **Spendable purses (8 → 12 metrics):** each actor owns one pool (`us_gov_capital`, `us_labs_resources`, `china_resources`, `eu_capital`; HIGH = more left). Deliberately metrics, not store tables: teams spend in prose, the GM deducts per the price bands in rule 9, pools refill +8 to +12 per turn. No paper JSON needed.

## Assumptions

- Start July 2026 mirrors the europe-2032 opening consensus at a coarser grain (no new research; live-play legibility over precision).
- 0–100 index scales throughout; worse-upward directions documented in `metrics.md` and the rules header.
- Event probabilities are first-guess values tuned for a 3-turn game (visible action likely each run without chaos).
- `rule_evolution.freeze_until_turn: 3` keeps rules fixed for the whole run; physics must not shift mid-workshop.
- No prompt overrides – templates apply.

## History note

- `runs/` holds old test runs that simulated the previous 4-metric setup. They are kept as history but are NOT comparable to runs under the new 8-metric physics.

## Weak spots

- Starting values are judgment calls, not calibrated.
- EU sovereign-capacity dynamics are stylized; real market-access and supply-chain play is richer.
- `strait_clash` compresses many escalation paths into one accidental-clash form; deliberate-attack paths are left to actor play and narrative.
