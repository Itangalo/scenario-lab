# Design Notes — Forking Futures

Source: `source-material/design-brief-sv.md` (Johan's working notes, Swedish,
24 August 2026). Those notes settled most of what is below; this file records
what was decided here and what was assumed.

## Central question

Which kinds of regulation and policy hold up in a world where advanced AI may
or may not be arriving fast — and which developments are worth monitoring as
early signals? Not a contest between states: a single policy-maker's decision
problem under uncertainty.

## The three design decisions everything else follows from

**One actor.** The regulator is the only thing whose choices are analysed. Labs
and states are world, expressed through metrics and events. If the trajectory is
set exogenously by the draw, letting labs also "decide" capability would put two
mechanisms on the same quantity. Attribution stays clean: outcomes vary with
(a) the regime and (b) the regulator's choices, which are exactly the two
variables the essay discusses.

**The timeline is an experimental dimension, not a claim.** Three regimes —
FAST, PLATEAU, RLVR-LIMITED — one per run, fixed from turn 1. The essay never
has to take a side in the timeline debate; the scenario asks how outcomes
*differ* between arms.

**Gates, not visible precursors.** A precursor event opens a gate that raises an
escalation's probability for a few turns. It never guarantees it, and the
narrative is forbidden from telegraphing it. If the precursor were as
conspicuous as the escalation there would be no monitoring problem to study;
if it were invisible there would be nothing to monitor. Open gate plus silent
narrative sits between the two, which is what makes the early-signals question
honest.

## Three prompt overrides (built here, not in the brief)

`user-prompts/actor.md`, `user-prompts/events.md` and
`user-prompts/metrics-update.md` are copies of the default templates with small,
documented additions. Overrides *replace* rather than merge, so **all three must
be kept in sync when the defaults change** — the events override in particular
must keep carrying the emergent-events block itself, and the metrics-update
override must keep carrying the regime-label ban. Each file's header comment
says what was changed and why.

## How the regime is kept from the regulator (rewritten 27 August) (ECHO 2026-08-27)

The regime must reach the Game Master and stay away from the regulator, which exists to infer it from what happens. Since the arms became variants this is structural rather than defensive: each variant patches `events` and `metric_rules` with its own figures, and neither resource is ever rendered into the actor prompt. There is no regime text sitting in `background_context` or `world_state` for the actor to see, so there is nothing to truncate.

The `<!-- GM-ONLY -->` marker is retired and must not be used for new work. It solved the draws-era problem: a draw's context reached every prompt including the actor's, so the regime paragraph was placed behind the marker and `user-prompts/actor.md` truncated the actor's view at it. Variants made it unnecessary and it has been removed from the actor override. Verified before removing: no variant's `context` or `world_state` contains the marker, every arm's resolved events and metric rules mention only its own regime label (so the Game Master no longer picks a column and needs no secret), and the rendered actor prompts are byte-identical before and after the removal. `sampler.py` and `draws/` were removed on 2026-08-27, once it was clear they carried nothing else: every draw set `metrics: {}`, and the 20 draws within an arm were identical apart from a `draw=NNN` index in `notes`. Their only jobs were injecting the regime behind the marker and tagging the cohort with `arm=`, and variants do both. They are in git history if a draws-era run ever has to be reproduced, and such a rerun would need the truncation back.

### The channel the marker never covered (found 27 August) (ECHO 2026-08-27)

Moving the arms onto variants opened a leak the marker was structurally unable to catch. `templates/system-prompts/actor.md` renders `The simulation focuses on {{scenario_description}}.`, and this scenario has no `system-prompts/` override. Under draws that was harmless, because the description came from the shared `scenario.yaml` and named no regime. Each variant then acquired its own `description` stating its arm in plain language, and `rlvr-limited-urgent.yaml` spelled out `RLVR-LIMITED`, the exact uppercase string the constitution bans from the narrative. Every run in `runs/` up to and including the 2026-08-26 batch therefore opened by telling the regulator the regime it was meant to infer. The marker guards `background_context` and `world_state`; the description reaches the prompt through neither.

The fix: variants define no `description` at all and inherit the neutral one from `scenario.yaml`, keeping their own wording in a YAML comment. Arm identity still travels by `name`, which is not rendered into the actor prompt, so cohort grouping is unaffected. `tests/test_regime_not_leaked_to_actor.py` asserts both halves, at the source and in the rendered prompt, for every variant.

Two lessons worth keeping. Hiding a fact is a property of every channel into the prompt, not of the one channel that leaked first, so a guard aimed at a specific field ages badly. And a check that renders the real prompt and greps it would have caught both this leak and the original one, which is why the test does that rather than inspecting the YAML alone.

### The third channel: the narrative itself (ECHO 2026-08-27)

Structural separation covers the prompts the regime is configured in, and the description fix covers the scenario blurb, but neither reaches the narrative. From turn 2 onward the narrative *is* the world state the regulator reads, and the Game Master, which legitimately knows the regime, sometimes wrote the label into it. In the first plateau batch (four runs) the uppercase labels leaked into seven turns across three runs; in one run the regulator declared its regime with certainty by turn 9. The referee caught some instances, missed others (approved turns still contained the label), and once ran out of attempts.

Three layers now guard this, because no single one is reliable:

1. **Prevention at the source** — `user-prompts/metrics-update.md` bans the
   three uppercase strings from the Narrative outright.
2. **A checkable constitution clause** — `constitution.md` §1 now states the
   ban as an exact string match (`FAST`, `PLATEAU`, `RLVR-LIMITED` must not
   appear in the narrative; lowercase generic talk of plateaus stays legal),
   which a referee can verify mechanically instead of by feel.
3. **One more retry** — `max_attempts: 4`; observed failures were often the
   last violation competing with metric disputes for the correction budget.

A Jinja-side redaction of the words in the actor prompt was considered and
rejected: a dumb string filter cannot distinguish *confirmation* ("Under the
PLATEAU regime …") from legitimate use of the hypothesis space the regulator is
meant to reason over, so it would blind the inference the scenario exists to
study.

## The regulator's memory (previous_actions)

The framework gives actors two memory substrates — the statement ledger and the
lossy historical summary — but neither holds a measure portfolio. The notepad
is Game-Master-only and unreachable from the actor template by design. In the
plateau batch this was visible as portfolio churn: measures vanished, were
renamed or reinvented between turns while every measure-status mechanic
(capital drain rule 7, recovery rule 8, §4's slot, §5's "fully implemented")
keyed off the unstable record.

Fix: `build_actor_prompt` now supplies `previous_actions` (the actor's own full
response from last turn, already stored on the actor object), and the actor
override renders it under **Your previous response**, declared the authority
that `## Portfolio` must carry forward. Default-template behaviour is unchanged;
the variable is simply available to overrides.

## Emerging developments (emergent events that do not fire are not discarded)

The design intent: at any time a few developments (2–4) should be *emerging* —
leaving faint traces in the narrative for the regulator to act on, each with a
real chance of materialising within 1–3 turns. How many are live, and how fast
they escalate, tracks how fast the world is moving: more in FAST than PLATEAU.

Before the fix this could not happen. An untriggered emergent proposal vanished
completely (nothing carried it into later prompts), and with
`probability_samples: 3` a proposal seen in one sample had its probability
divided by three — 23 proposals across four plateau runs, zero firings. The
mechanism now works in three parts:

1. **Python carries the books** (`orchestrator._update_emerging_developments`,
   opt-in via `emergent_events.track_unfired`, bounded by
   `emergent_events.window_turns`, default 3). A proposal that did not fire is
   tracked with id, description, first/last turn; one that fires occurred and
   leaves the list; one that stops being re-proposed has fizzled. After the
   window's consecutive listed turns without firing, it closes. The list
   persists in `summary.json.emerging_events` and is restored on resume and
   branch.
2. **Prompts carry the semantics.** The tracked list is rendered into the
   notepad all Game-Master steps read (`## Emerging developments (tracked)`),
   regenerated idempotently each turn. The events step must re-list entries
   still plausible at roughly 1.5–2× their previous probability, or omit them;
   because re-listing is mandatory, multi-sample aggregation no longer divides
   them away. The Game Master narrates them only as faint signals whose
   visibility grows with age — they reach the regulator through the narrative,
   never through the notepad itself.
3. **Scenario wiring.** `emergent_events.max_per_turn: 2` so 2–4 can stay live,
   plus `track_unfired: true` and `window_turns: 3`; the events override sets
   the count/ramp expectations per pace-of-progress and forbids descriptions
   naming the regime labels (descriptions reach the actor when an event fires).

This is a framework capability and is documented in `docs/ARCHITECTURE.md`.
It is deliberately opt-in: scenarios that enable emergent events without
`track_unfired` keep the original one-shot proposal semantics, so no other
scenario's physics changed silently (swedish-government-formation-2026 also
runs emergent events and is unaffected).

## Assumptions

- **The starting world is a stylised composite, not a researched fact base.**
  Capability figures (US 45, China 38), the open-weight gap (30), sentiment (42)
  and the economic climate (65) are calibrated to be *interpretable against the
  reference points*, not sourced. They are framework-generated numbers and must
  be reported as such.
- **Starting metrics are identical across all three arms.** Mid-2026 looks the
  same whichever future it becomes; the regime governs growth, not the start.
  Per the brief: keep the arm clean in the first round.
- **Runs within an arm start identically.** They diverge only through the event
  dice and the regulator's choices. Draws carry no jitter.
- **Event probabilities are first guesses.** The regime-specific figures were
  chosen so the arms separate on more than the capability number — note in
  particular that RLVR-LIMITED carries the highest cyber probabilities, which is
  where that regime's capability actually shows up. Calibrate from prototypes.
- **Metric coupling coefficients in `metric-rules.md` are invented physics.**
  They are internally consistent and dimensionally sane; they are not estimates
  of anything.
- **Category numbering** follows *Effective Mitigations for Systemic Risks from
  General-Purpose AI*, widened with category 6 (societal resilience) and
  category 8 (diffusion, adoption and societal effect), which that paper's list
  does not contain. Category 9 is "Other" so that invented measures are still
  taggable, which is what makes cross-run grouping in `synthesize` possible.

## Configuration decisions

- **`requires_initial_state: true`.** Without a draw there is no regime and the
  run answers nothing. Better a hard error than a silently pooled result.
- **`rule_evolution` disabled** (`freeze_until_turn: 19` > `max_turns`). This
  scenario is read as a distribution over ~50 runs; drifting physics is noise in
  exactly the thing being measured. The mechanism is also known to rewrite
  roughly one rule per unfrozen turn regardless of need.
- **`emergent_events.enabled: true`**, per the brief — the scenario exists to
  explore futures nobody listed. `max_per_turn: 2` supports the emerging-
  developments steady state (see that section above).
- **`probability_samples: 3`.** Gate probabilities are the load-bearing numbers
  here; averaging three elicitations is worth the events-step cost. The
  absent-as-zero aggregation is no longer a problem for emergent proposals,
  because the emerging-developments protocol makes re-listing mandatory while an
  entry stays plausible.
- **No `termination` block.** Nothing in this scenario resolves; the horizon is
  the point. Runs go the full 18 turns.
- **Notepad:** Game-Master-owned, as in every scenario: written by the metrics
  step, read by the GM-side steps, never rendered into the actor's prompt. (An
  earlier note here claimed the regulator tracked measures in it — wrong, and
  the portfolio churn it caused is what motivated the previous_actions fix.)
  The actor's own memory of its portfolio is its previous response.

## Deliberately left out

- **A second regulator (US + China).** That is a coordination game between
  jurisdictions, not a decision problem under uncertainty. It would partly
  duplicate `ai-safety-race` and lose the European connection. Candidate for the
  follow-up essay.
- **The believed-threshold mechanic from `ai-safety-race`.** There is no true
  threshold with a fixed value when the timeline itself varies. Early-warning
  value comes from the gate mechanism instead.
- **A welfare metric or objective function.** Fixing one would decide the
  essay's conclusion inside the scenario files. See `constraint-ledger.md` O1.
- **An effort dial per measure.** Concentrate-versus-spread emerges from capital
  scarcity plus the named priority, without extra mechanics to interpret.

## What the prototype runs showed (three runs, 4-5 turns, ~$0.05)

Prototype runs were deleted afterwards so they cannot be pooled with a real
batch by `ensemble` or `synthesize`. What they established:

- **Arms separate sharply and early.** FAST reached `us_capability` 59 by turn
  5; RLVR-LIMITED reached 46.5 by turn 4. That is the separation the design
  requires, visible well inside the prototype.
- **The regime-hiding mechanism holds.** No actor output named this run's
  regime. The regulator did reason about *which* regime it might be in and named
  two candidates — which is the intended behaviour: inference is legitimate,
  foreknowledge is not.
- **The referee earns its place.** It caught a narrative writing "consistent
  with FAST regime dynamics" and corrected it in one extra iteration, and it
  caught the regulator introducing two new measures in one turn. Both were then
  fixed at the source rather than left to the referee.
- **Two defects found and fixed, both in prompts:**
  1. *Gated escalations were never evaluated.* With the gate written as an event
     `Condition`, the model read it as an eligibility test and omitted the event
     — so precursors fired for two turns and no escalation was ever rolled. The
     gate moved into the `Probability` field, and `user-prompts/events.md` now
     names the five always-eligible escalations explicitly. Verified: all five
     appear every turn, at gate-shut probabilities when shut, and
     `capability_jump` fired the turn after its precursor once the gate opened.
     Without this fix precursors would have had a zero false-negative rate,
     which would have made `rq_early_signals` answer a question easier than the
     real one.
  2. *The regulator proposed several new measures per turn and named no
     priority.* Nothing in the output format forced the choice. The actor
     override now requires `## Portfolio` (status plus category tag per measure),
     `## New measure` (at most one, `None this turn.` allowed), and
     `## Priority` (exactly one). This is also what makes measures greppable by
     category, which `rq_no_regret` depends on.

## What the first FAST batch showed (4 runs, 12-16 turns each, stopped early)

Compliance held up over full-length runs: the six escalation events were listed
in 231 of 232 turns, and the regulator produced `## Portfolio`, `## New measure`
and `## Priority` in 57 of 57 turns, never proposing more than one measure. No
run leaked its regime.

One defect and four calibration problems, all visible only at full run length:

- **`rsi_onset` never fired** — the FAST arm's defining mechanism. It was listed
  in 4 of roughly 40 eligible turns and given p=0.0-0.1 rather than 30%, because
  its condition led with "FAST regime only" plus a negative clause and the model
  filtered it out the same way it filtered the gated escalations. Metric rule 1's
  post-RSI branch therefore never activated: FAST reached capability 83-92 purely
  through `capability_jump`, so the arm looked right for the wrong reason. Fixed
  by rewriting the condition positively and adding `rsi_onset` to the
  always-eligible list in `user-prompts/events.md`.
- **`incident_pressure` saturates**, reaching 85-100 by mid-run in three of four
  and pinning there. Decay (-4 to -8) is far too weak against escalation
  increments (+15 to +35); above roughly 60 it never returns.
- **`openweight_gap` is monotone to zero.** -1 to -3 per turn over 18 turns from
  a start of 30 floors it in every run, so it carries no cross-run variance.
- **`public_sentiment_to_ai` is one-directional** (42 down to 8-25 in all four).
  Its recovery clause requires that no harm has landed, which is almost never
  true.
- **`regulatory_capacity` never binds**, staying between 42 and 65 all run. The
  concentrate-or-spread choice is supposed to emerge from capital scarcity, and
  capital never became scarce. The regulator proposed a measure in only 23 of 57
  turns, and about nine of those omitted the `Category:` line that the analysis
  depends on.

**The four calibration problems are not yet actionable.** All four runs were
FAST, the most extreme arm, where a world pinned at high incident pressure and
collapsing sentiment may be the correct answer rather than a miscalibration.
Judging the metric rules off that arm alone would bake the most extreme future
into the physics. They stayed open until PLATEAU had run.

## What the first PLATEAU batch showed (4 runs of draws 001–004, stopped early)

Ten to thirteen turns per run before the batch was interrupted; all four are
the plateau arm. What they established, and what was fixed as a result:

- **The regime leaked through the narrative in three of four runs** — seven
  turns carried an uppercase label, one run's regulator declared its regime by
  turn 9. Fixed with the three layers described under "The leak the marker
  cannot stop".
- **The regulator's portfolio churned**: measures vanished or were renamed
  between turns (a fully implemented pact at turn 4 is gone by turn 8; the
  portfolio at turn 12 shares nothing with turn 4). Fixed with the
  `previous_actions` memory described under "The regulator's memory".
- **`us_capability` stalled flat at 46.5 for ten turns in one run** — the
  PLATEAU branch was read as zero growth ("gains … are negligible"), which rule
  1 never says. The referee cannot see metric rules at all, so nothing pushed
  back. Fixed by hardening rule 1 ("deceleration is not stagnation") and the
  plateau draw text; the other three runs grew slightly below the stated band,
  which is within tolerance.
- **`openweight_gap` pinned near zero in every run**, confirming the FAST-arm
  suspicion with a mechanism attached: `open_weight_frontier_release` fired 9
  times across the four runs because its probability rose when the gap fell
  below 25 while plateau drift guaranteed the gap fell below 25 early — a
  self-feeding loop, capped only by each firing cutting the gap it feeds on.
  Fixed: the event is now non-repeatable, not eligible below gap 12, and its
  probability no longer scales with how narrow the gap already is. Expected
  behaviour now: roughly one release per run at most, at varied timing, with
  some runs never releasing — variance instead of a pin.
- **`incident_pressure` saturated outside FAST too** (97 in run -03), helped by
  `information_integrity_crisis` firing five times in one run despite its
  description describing a singular rupture. Fixed two ways: that event is now
  non-repeatable, and metric rule 5's decay strengthened (−6 to −10, up to −14
  under preparedness) with explicit "pressure breathes" wording.
- **Emergent events never fired** — 23 proposals, zero triggers, probabilities
  visibly divided by the sample count. Fixed by the emerging-developments
  mechanism described above.
- **One turn shipped a capability fall** (48 → 46.5, violating constitution §2)
  and another shipped two new measures in one turn, both in
  `max_attempts_reached` turns accepted under `accept_with_violations`. The
  attempts budget is now 4; prevention (the metrics-update override) reduces
  the competing-violation pressure that exhausted it.

## Coherence pass after the first complete batches (all three arms)

Six full runs (two per arm, 18 turns) exposed two defects that prototype and
partial runs could not show, and the fixes were made as one redesign of how
regime physics are stated rather than as spot patches:

- **`rsi_onset` collapsed to p=0 in elicitation samples even when due.** With
  the threshold met from turn 7, samples returned `[0,0,0]` in nearly every
  turn; one turn gave the correct `[0.3,0.3,0.3]` and the dice beat it by
  0.004. Both FAST runs therefore never entered the compounding branch: one
  reached capability 100 through improvised acceleration (right shape, wrong
  mechanism), the other stalled flat at 48 for seven turns and finished at 72 —
  below the best PLATEAU run. The entry now defines *due-ness* (threshold met
  under FAST → listed every turn) and pins the probability ("exactly 30%,
  identical in every sample, never reduced while the threshold holds"), echoed
  in the override's always-eligible paragraph.
- **PLATEAU and RLVR-LIMITED converged numerically** (ends 59–68.5 vs 62–63).
  Their old ceilings sat next to each other (68 vs 60), plateau drift was
  applied loosely below band while `capability_jump` lifted it (four jumps in
  one run), and nothing anchored where each arm should end.

The redesign, in one move: **metric rule 1 now states each regime as a
per-turn rate plus a terminal zone** — FAST 95–100 (via `rsi_onset`
compounding), PLATEAU 70–78, RLVR-LIMITED 58–64 — with growth tapering into
the zone and rates explicitly floors on motion. Terminal zones give the
models the endpoint anchors they demonstrably follow better than per-turn
prose, separate PLATEAU decisively above RLVR-LIMITED, and replace the
scattered defensive sentences ("deceleration is not stagnation" in two files,
the growth-rate paragraph in the constitution). The constitution now says
explicitly that growth rates belong to rule 1 and not to it — no duplicated,
drift-prone phrasing left. `capability_jump` gained explicit magnitudes
(+3 to +7 general; +1 to +2 under RLVR-LIMITED) so event-driven lift is
physics rather than GM mood.

The eight runs in `../runs/` predate this pass and must be moved to
`calibration-runs/` before any new batch is pooled with anything.

## Catalogue expansion (web-researched, August 2026)

The event list grew from 18 to 33 listed events and the measure anchors were
widened, from a research pass the author commissioned without review. Three
researched institutional reactions — court challenges, member-state
non-compliance, rival standards bodies — were then *moved out of the list into
the emergent lane*: their preconditions live in the regulator's portfolio,
which no metric expression can test, and on a menu they got rolled without
footing in all three validation attempts. The events override now names them
as prime emergent candidates once the portfolio warrants them; ids stay
recognisable (`emergent_court_challenge`, …) for analysis. Sources consulted, and
what they seeded:

- **OECD AI Incidents & Hazards Monitor** (AIM) and its 14 media-themes
  analysis, plus the common reporting framework — used as a coverage
  checklist. Gaps against our list became events: child safety
  (`companion_harm_scandal`), labour/institutional conflict
  (`sector_strike_wave`), AI-enabled warfare (`ai_military_deployment`),
  IP/creator economy (`creator_backlash_campaign`).
- **CSET AI Harm Taxonomy / MIT AI Risk Repository** (via the AI Incident
  Database) — the intangible-harm categories flagged what we lacked entirely:
  differential treatment. `algorithmic_bias_scandal` is the toeslagenaffaire/
  Robodebt pattern, deliberately conditioned on *adoption* measures so that
  diffusion visibly cuts both ways.
- **Datacentre activism reporting** (Ireland's 21%-of-grid moratorium,
  Marseille, Zeewolde, Chile water retreat) — `datacenter_protest_wave`
  (sentiment-gated), `water_use_conflict`, `grid_capacity_crisis`.
- **Agent-safety literature and incidents** (METR's internal-agents risk
  pilot, AISI's unsanctioned-agent-behaviour incident, the Hugging Face agent
  intrusion write-up, RAND's loss-of-control emergency-preparedness report)
  — a new precursor/escalation pair: `agent_misconduct_disclosure` opens an
  agent gate; `agent_supply_chain_compromise` fires behind it (+8..+18 as a
  new medium escalation class in metric rule 5). RLVR-LIMITED weights the
  disclosure higher, which is where its capability actually lives.
- **Human Artistry campaign / Authors Guild suits / SAG-AFTRA strikes** — fed
  `creator_backlash_campaign` and the strike event's conditions.
- Geopolitical economy patterns (export-control escalation cycles, sovereign
  funds after crashes, rival standards bodies, China bundling governance with
  model exports) — informed by general policy reporting rather than one
  source.

Principles applied throughout: **conditional rarity** (most new events are
ineligible most turns — gated on sentiment thresholds, prior events, or
measures actually existing), so per-turn candidate counts stay near what the
calibrated physics expects; **no new always-eligible escalations** (the six
stand); **register discipline** (patterns and mechanisms only, no real
actors named). Metric anchors: only `public_sentiment_to_ai` gained text —
street-level manifestations at 30 and 15, answering "when is this unrest?"
— since sentiment is the agreed proxy for displacement effects too. Seven
metrics remain seven: no unemployment metric, by decision.

## Validation rounds for the expanded catalogue (evening, 24 August)

Three single-run-per-arm rounds under the new catalogue and physics. Two
failed instructively and were archived under
`calibration-runs/aborted-20260824-validation1/`; their findings became two
framework additions and one catalogue restructure:

- **Prose conditions proved unenforceable at list length 36.** The model
  listed ineligible events "just in case" with small probabilities — and
  anything listed gets rolled — so a court challenge fired before any measure
  existed and a grid crisis fired at economic_context 65. Fix:
  **`Eligible:` gates** (`docs/ARCHITECTURE.md`, "Eligibility Gates") — a
  declared boolean expression per event, evaluated by Python against current
  metrics plus regime flags (`is_fast`, `is_plateau`, `is_rlvr_limited`),
  removing gated events from the prompt entirely and rejecting candidates for
  them anyway. Eight events carry gates; `rsi_onset` is one of them
  (`is_fast == 1 and (us_capability >= 65 or cn_capability >= 65)`), which is
  what finally made its probability stick: shown only while due, at a bare
  constant 30%.
- **Portfolio-conditioned reactions cannot be menu items.** Court challenges,
  member-state non-compliance and rival standards bodies depend on what the
  regulator has built, which no metric expression tests. They moved out of
  `events.md` into the emergent lane, where the Game Master sees the books;
  the override names them as prime candidates once warranted.
- **One-shot events were being re-rolled after firing** (rsi fired twice,
  ai_market_crash three times in one run) because the always-eligible contract
  names ids that outlive occurrence. The orchestrator now skips any candidate
  for an occurred non-repeatable event.

The clean round (run-20260824-203039/-42/-45) showed: arms separate (FAST to
100 via an actual `rsi_onset` compounding branch — first time the mechanism
has ever fired; PLATEAU 64.5; RLVR-LIMITED 68.5 flattening), referee approved
54/54 turns with zero regime labels, the emergent lane produced contextual
institutional events (`emergent_court_challenge` only after an alliance bloc
gave it footing), and emerging developments tracked and expired as designed.
Remaining calibration observations, judged from single runs: RLVR-LIMITED
overshot its band mid-run (+2/turn against +0.5..+1.5) before flattening;
incident_pressure still saturates in event-dense runs (97 in FAST with seven
cyber campaigns); PLATEAU's early flatness was crash-adjusted rather than a
stall. All three stay open for the full batch.

## Still uncalibrated

- **Gate-open probabilities came back below their stated figures** (the model
  gave `cyber_mass_campaign` 0.10 where the entry says 22%, applying the
  preparedness halving). Check whether escalations fire often enough across a
  batch to be analysable at all; if not, raise the gate-open figures.
- **Lead times** — see `constraint-ledger.md` O2.
- **Whether the rebalanced decay and the non-repeating integrity crisis leave
  the plateau arm too quiet** — judge from the next full batch, not from these
  partial runs.

## Framework changes made while building this

- `scenario_lab/validator.py` checked event *conditions* against metric ids
  only, while its own comment four lines above states that prose may
  legitimately name events as well as metrics — which rules and actor files
  were already allowed to do. That inconsistency made the precursor/escalation
  gate mechanism unwritable. The check now uses the same `valid_identifiers`
  set the file had already built for that purpose, and the error message names
  both kinds.
- Emerging developments (see the section above): unfired emergent proposals are
  tracked across turns when `emergent_events.track_unfired` is set, rendered
  into the GM-side notepad, restored on resume and branch, and bounded by
  `emergent_events.window_turns`. Opt-in; documented in
  `docs/ARCHITECTURE.md`.
- `build_actor_prompt` supplies `previous_actions` to overrides (default
  templates ignore it), giving an actor a durable record of its own last turn.

## Register discipline (carried from the brief)

- Structural patterns, not policy rankings. "Reactive interventions arrived late
  in X of Y runs", never "the model shows measure Z is best".
- The numbers are framework-generated. This is scenario exploration, not
  evidence synthesis and not calibrated forecasting.

## Populations and variants (updated 26 August)

- The trajectory arms are now **variants**, not draws: `variants/fast.yaml`,
  `plateau.yaml`, `rlvr-limited.yaml`, each carrying its regime's figures as
  resource patches over the shared physics, plus three urgent-disposition
  siblings chained on them (`fast-urgent.yaml` etc.). One
  `batch-run scenarios/forking-futures --variants --repeat N` covers all six.
- Why: an audit of all runs up to 2026-08-26 showed evaluated event
  probabilities *converging* across arms instead of tracking their declared
  per-regime figures (e.g. ai_market_crash evaluated ~4–5% everywhere against
  declared 12/25/18) — the tri-regime prose depended on the events model
  picking the right column every turn, and it mostly didn't. Flat per-arm
  figures remove that failure mode; the old branched text stays in
  `events.md`/`metric-rules.md` as the record of where each patched figure
  came from. `sampler.py` and `draws/` were retired for new runs on
  2026-08-26 and deleted on 2026-08-27; git history keeps them. Note what
  they were not: no draw set any metric, so they never varied the starting
  world and never carried a seed. Seeds are separate and unaffected, each
  run generates its own unless `batch-run --seed` supplies a shared one.
- Two provenance eras, accepted: runs before 2026-08-26 carry `arm=...` in
  `initial_state.notes` and one scenario identity for base + one for the old
  sibling-style urgent batch; runs after carry the arm in their scenario name
  (`Forking Futures — Fast`, `— Plateau (Urgent Regulator)`, …). Group old
  runs by `arm`, new runs by `scenario`.
- `rsi_onset` keeps its id in plateau/rlvr with a permanently-false gate so
  research questions and cross-arm statistics stay comparable.

## Open

See `constraint-ledger.md`: what counts as a good outcome (O1), lead times per measure type (O2), whether the world is too passive with one actor (O3). Runs per arm is now set by how many times the batch repeats each variant, not by `sampler.py --count`: `batch-run` the variant files with `--repeat N`, or list them explicitly when the arms need different counts. At 18 turns a run costs roughly $0.11, so 20 per arm across the six variants is about $13. (ECHO 2026-08-27)
