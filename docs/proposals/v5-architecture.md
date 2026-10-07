# Proposal: Scenario Lab v5 target architecture

Status: **draft** on `version-5`, 2026-10-05. Brief for implementing `docs/VERSION 5.md` without breaking v4 runs.

Read `../VERSION 5.md` for the human-written source notes. Read `../ARCHITECTURE.md` for current ground truth (6-step turn loop, store as declared persistent state, statement ledgers). This doc is the build plan; `ARCHITECTURE.md` gets updated as each piece lands, per `AGENTS.md`.

## Goal and non-goals

Goal: fewer, cleaner LLM steps with Python owning custody and arithmetic. The Ledger takes over everything that is currently re-emitted prose (metrics, event catalogue state, world narration pointers), prompts get smaller, and the turn loop collapses from six steps to three.

Non-goals for v5: replacing LLM judgment with Python rules (custody ≠ logic), System One integration (parked, see VERSION 5 notes), full online play (one-off, not generic).

Kept from v3/v4: lean-into-LLM, incremental persistence (every phase writes before the next starts), per-phase resumability, seeded dice, template overrides, lightweight Python checks only.

## 1. Unified Ledger v5

V4 store (`scenario_lab/store.py`, ~2300 lines) already proves the custody model: declared schema, `actor`/`world`/`system`/`derived` owners, JSON writes under one header, per-entry rejection, one transaction per turn. V5 generalizes it from "actor portfolios plus extras" to "the run's memory":

- **Metrics become a table.** A world-scoped `metrics` table (one record per metric, level in a numeric world-owned column) with the metrics-adapter path already sketched in ARCHITECTURE.md made the default. `scenario.metrics` syncs from records; gates, termination, prompts, analysis read unchanged. `range` clamps-and-records by default, `on_out_of_range: error` for columns where a miss means a broken writer.
- **Events catalogue optionally in the ledger.** Event list / probabilities stay human-edited as `events.md` (source of truth), but each turn's *evaluated* state (probability, roll, triggered, emergent proposals) is already in `1-event-evaluations.json`. V5 adds a ledger mirror only if it removes prompt bulk: the events step reads the catalogue, writes evaluations; no new judgment moves to Python.
- **World narration stays files, indexed in the ledger.** VERSION 5 floats storing prose in the ledger; decision here: keep `4-world-state.md` / `6-historical-summary.md` as files (humans read them, diffs work), and store only pointers + mass-read index in the ledger. Alternative (parse md into ledger) becomes a small import/verify helper, not a storage change.
- **Rich descriptions stay in files, linked from the schema (`info_file`).** Yes to the VERSION 5 note: an optional `info_file:` on a table (and optionally on a column) points at an md file with H2 sections per record. Rationale: ledger cells must stay typed, queryable and aggregatable; prose stuffed into cells breaks that and bloats prompts. The metrics case is the driver — description + reference points live in the info file, the numeric level lives in the ledger cell — but any table gets it (events, measures, alliances). Loader validates the path (same path rules as scenario inheritance) and the H2 structure; `describe` and sign-off render the full text, turn prompts render only the slice needed (today's `metrics_list` path: description + reference points, not full prose). The LLM reads the prose but never re-emits it, which is the same custody split as narration.
- **Queries stay small, reads get batched.** Keep one selector + reducers (`rows`, `sum/min/max/mean/count`, one equality filter). Add mass-read: `store.history(table, id, turns=[...])` for analysis over completed turns, reading persisted per-turn snapshots rather than re-prompting. Anything past that is a query language with authoritative-looking wrong answers; still out.
- **Markdown standard.** H2-only parsing segments for all scenario md files, so ledger import/verify and existing parsers share one rule.

Migration: additive. Scenarios without `store:` behave exactly as today. `metrics`-table migration waits on a before/after arithmetic measurement (europe-2032 runs not comparable across the move). Schema recorded in `config.json` (already done) so batches under different schemas stay apart.

## 2. Three-phase turn loop

Collapse six steps to three; every phase persists incrementally and is a resume/branch point (cycle, not pipeline):

1. **Events.** Input: previous world state. LLM prices candidates (listed + optional emergent proposals). Python rolls seeded dice, persists `1-events.json` + `1-event-evaluations.json`. No metric effects resolved yet.
2. **Actor actions.** Input: previous world state + triggered events in prose. Optional negotiations (section 3), then per-actor responses in parallel. Statement proposals and `## Store changes` applied before the next phase, persisted per actor.
3. **World update.** Input: triggered events + actor actions + world rules. One Game Master call evaluates action success, applies event effects, updates ledger data via rules, rarely adjusts rules themselves (calibrated to be rare; freeze window + max-changes cap kept), writes new world state + narrative + notepad. Constitution referee and summarization fold in here as sub-steps, not phases.

Resume/branch today restores from turn files; v5 extends the state snapshot to phase granularity (`phase: events|actors|world` in `summary.json`, partial turn dirs resumable). `branch --from-turn N` keeps working; add `--from-phase` later.

Rules evolution: keep versioned `3-metric-rules.md` + changelog, but the default tightens (frozen early turns, small deltas). World rules file splits description from reasoning (scenario-authoring guideline, validated by H2 headers).

## 3. Negotiations (optional, off by default)

Fits inside phase 2 as N rounds before the action write-up. Mechanism per VERSION 5: append-only private messages rendered into each recipient's world description (`Message from A to B: ...`). Simultaneous send per round; multi-round with replies, leaking allowed (a recipient may quote a private note to a third actor). Config per scenario: `negotiations: {enabled, rounds, who_may_contact_whom, per_actor_rounds}`; dynamic round count (GM or facilitator may extend once). Cost warning at validate time when enabled. Live games reuse the same channel for team-to-team notes. No Python judgment of content; Python owns delivery lists and persistence (`turn-XX/2-negotiations/`).

## 4. Live games: endings and mixed modes

Standard sims need no climax; live games do. Minimal v5 (combining decisive moment + authored endings + epilogue):

- Optional `finale:` block in `scenario.yaml` (final turn, moment description, 3–5 endings with conditions, epilogue on/off).
- Final turn uses a prompt variant ("resolve the moment"), reached ending recorded in run summary, printable finale/epilogue sheet among handouts.
- Mixed modes: any subset of actors LLM-played in live games (facilitator flags which). Online play stays a one-off, not a framework feature.

## 5. Scenario tooling (independent tracks, any order)

- Authoring guidelines: short files, description/reasoning split, sign-off docs generated one at a time during creation (`scripts/render_signoff.py` already records provenance; extend to gate each creation phase).
- `update-scenario-from-news` command: searches since start date / last update, proposes context/metric/event changes with source + retrieval date (information-bank style), human approves before any write, records update as new version/dated variant (batches kept apart). Suggests only; never edits silently.
- Market anchors: snapshot Metaculus/Polymarket/Manifold/Kalshi figures into the scenario (source, URL, date) as silent properties for the builder – never rendered into a prompt, never fetched during a run. First test: GM turn-1 pricing vs market where both exist (the GM does not see the market).
- Calibration note: probabilities/rules are calibrated to the scenario's world, not today's world.
- Output subfolders for run artifacts; benchmarking suite for actor/GM quality (low priority).

## Sequencing

1. This doc (review, then lock the two load-bearing calls: narration stays files; queries stay small).
2. Ledger v5: `info_file` links (done) + mass-read `read_table_history` (done) + H2 standard. Metrics-table stays opt-in — auto-creating it would change every existing scenario's physics and break run comparability; "default" means new scenarios draft it (create-scenario skill) until the before/after arithmetic measurement lands.
3. Three-phase loop, structural half (done on `version-5`): `run_turn(turn, from_phase=...)`, `phases` in `summary.json`, `detect_last_phase`/`next_phase` in `resume.py`, mid-turn auto-continue in `resume` (including a turn-1 crash, loaded from initial state), event-history re-entry on reload. Covered by `tests/test_phases.py`, including a byte-identical world-phase reproduction. Prompt merge of the world phase explicitly deferred; negotiations plug into phase 2 next.
4. Negotiations (done on `version-5`): `negotiations:` block, `negotiations.py` delivery, `_run_negotiations` in the actors phase, `2-negotiations/` artifacts, validator cost/stale-template warnings, `tests/test_negotiations.py`.
5. Mixed player modes (done on `version-5`): `--llm-actors` on `live-menu`/`live-resolve`/`live`, recorded in `menu.json`, chained next menus keep the mode, model actions via the shared `generate_actor_action`, facilitator pass-through. Finale block postponed.
6. Tooling: output subfolders (done). Update-from-news (done as the `update-scenario` skill: harness-chosen sources, `updates/UPDATE-*.md` approval file with one entry per change, apply-approved-only, design-notes log, incomparability rule). Market anchors (done, Metaculus-first): `**Metaculus:**` / `**Retrieved:**` / `**Market probability:**` on events, parsed + validated + patchable + in `describe`; snapshots, never live fetches; creation flow records anchors at draft and signs off the events list (`create-scenario` skill). H2 standard (done): one H1 title + H2 sections in `metrics.md`/`events.md`, sub-H2 warns as folded prose. Sign-off gating rides on the existing creation checkpoints (framing, review, prompt sign-off) plus the new events sign-off.

## Review fixes, round 3 (2026-10-07)

- Output subfolders named like runs (`run-*`, `live-*`) are rejected at creation, and discovery descends into any directory that has no `config.json` of its own, so existing ones are found too.
- A turn-1 crash resumes with the recorded initial state (`load_initial_scenario`), not the scenario default.
- A turn is complete only once `6-historical-summary.md` exists, on turn 1 too (it is written last, after the referee).
- `rounds` is a guaranteed minimum even when `max_rounds` lags (a config override of `rounds` alone); writers with nobody reachable sit out, and the round prompt never offers unavailable recipients.
- Market anchors are silent: no longer rendered into the events prompt. Sources are Metaculus, Manifold and Polymarket (`market_sources.py`, `market-fetch`); fields are `market_url`/`market_retrieved`/`market_probability`.
- `branch --from-phase events|actors` branches inside a turn.
- Parked: `market-check` with negotiations, see `market-check-negotiations.md`.

## Review fixes, round 2 (2026-10-06, from `v5-review-2-2026-10-06.md`)

- Round prompts render inbox and outbox (regression from round 1 fixed), with a round-2 integration test proving both directions arrive.
- Phase detection requires `-store.json` per actor when a store is declared.
- History snapshots resolve by config actor order, not counters or filenames.
- Live menus fall back to the nearest earlier record; `--llm-actors none` opts out explicitly (mode switches happen at menu time).
- `--max-runs` orders by run-name timestamp (mtime fallback); `rounds` is a guaranteed minimum before silent-stop; `market-check` skips flagged evaluations; user templates must branch on `negotiation_round`; truncation keeps full history when the log starts partway.
- `info_file` slices render in turn prompts via `store.info('table', 'record')` (validated, sections loaded at load time, content never persisted to artifacts).
- `read_table_history` feeds the analysis prompt (`Declared State Over Turns`) as a first snapshot plus per-turn changes, so reports can date portfolio changes instead of recovering them from prose without repeating every unchanged record every turn.

## Review fixes (2026-10-06, from `v5-review-2026-10-06.md`)

All thirteen findings fixed on `version-5`, each with a regression test:

- Resume: actors-phase detection needs every actor's response + statements files (no more dead-ends on partial phases); store restore merges per-actor files last-wins and never reads post-world state on reload; events reload replays emerging-developments tracking; `occurred_events` truncates at the load/branch point (legacy log-less summaries untouched).
- Negotiations: round prompts render a dedicated variant on both templates (no action format mid-round); senders see their offers and delivery failures; the Game Master record (`negotiation_record`) rides into the metrics prompt; `max_rounds` extension seats everyone not explicitly capped; reruns replace the attempt's artifacts wholesale; `negotiations` recorded in run `config.json`.
- Config/CLI: `info_file` resolves against the scenario dir for yaml and variant paths; progress shows three phases; `--max-runs` orders newest-first; branches land beside their parent; `live` keeps the recorded mixed mode unless flagged, and resolve-flag overrides persist into chained menus; live output base walks up past subfolders.
- Anchors reach the events prompt as a labeled prior, plus a `market-check` command comparing turn-1 GM pricing with snapshots.
- `info_file` is consumed by `describe` (section titles) and the sign-off coverage table; `read_table_history` prefers the world file, else the highest-counter actor snapshot.
- Analysis scoping: `subdir` recorded in `config.json` is a cohort axis (`--filter`/`--group-by` on ensemble/synthesize, `--filter` on calibrate).
- Docs: numbering fixed in both skills docs and here.

## Decisions on the open questions (2026-10-06)

- Ledger mirror of the event catalogue: **no.** `1-event-evaluations.json` already carries the per-candidate record with turn stamps; a second mirror buys sync bugs, not prompt savings. Revisit only if a measured prompt shows the catalogue + evaluations jointly bloating the events step.
- Rules-adjustment rarity: **measure before changing defaults.** No global default change in this increment; run europe-2032 with candidate freeze/cap numbers and pick the pair that makes adjustments rare without freezing needed adaptation.
- Live-game climax (authored endings, secret objectives, countdown, epilogue): **postponed.** No clean small form found; the finale block stays a sketch. **Mixed player modes (some actors LLM-played in live games) still planned** — small orchestration change, independent of any climax.
