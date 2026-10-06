---
name: update-scenario
description: >
  Refresh an existing Scenario Lab scenario from developments since its start
  date (or last update): news, changed facts, and Metaculus markets. Researches
  with the harness's own search, writes one approval-markdown entry per proposed
  change (change, motivation, sources), waits for human approval, then applies
  only what was approved and records the update. Triggers: "update the
  scenario", "refresh the scenario from news", "is this scenario still current",
  "uppdatera scenariot", "se över scenariot mot nyheter".
---

# Update Scenario: From New Developments to Approved Changes

You are refreshing an existing Scenario Lab scenario. The rule that governs everything: **the command suggests, it does not edit silently.** Research freely, propose concretely, change nothing until the human approves entry by entry.

## Phase 1: Scope

1. Read the scenario: `scenario.yaml` (note `start_date`), `events.md` (note any `**Metaculus:**` anchors), `metrics.md`, `background/context.md`, `design-notes.md`.
2. Check `scenarios/<id>/updates/` for previous `UPDATE-YYYYMMDD.md` files. The baseline date is the latest update's date, or the scenario's `start_date` if there are none.
3. Present the scope in one short message: baseline date, how many anchored events (Metaculus re-checks), and what you will search for. Do not start editing.

## Phase 2: Research

Use the harness's own search and fetch tools (you choose the sources – news outlets, official statistics, primary reports). Cover, as relevant:

- **Fixed facts** that changed: election results, laws in force, treaties, leadership.
- **Metric start values** the world has moved away from.
- **Catalogued events that have now happened**: each becomes either *retired* (remove from `events.md`) or *pinned* (rewritten as turn-1 context – it is history now, not uncertainty).
- **New events** worth adding to the catalogue.
- **Probability shifts**: developments that move an event's per-turn figure.
- **Metaculus anchors**: re-fetch every `**Metaculus:**` URL, record the new community figure with today's date. A moved market is a proposal to adjust the event's probability framing, not an order – market odds are unconditional and dated, scenario events conditional and per-turn.

Save fetched source texts or summaries under `scenarios/<id>/source-material/` (new `update-YYYYMMDD/` subfolder) so the update is reproducible without the links, with the same provenance habit as `frame-scenario`: user, source, model knowledge, assumption.

## Phase 3: Proposal (the approval document)

Write `scenarios/<id>/updates/UPDATE-YYYYMMDD.md` – one entry per proposed change, each with exactly these fields:

```markdown
## U3 – Event probability: strike (12% → 18% in the 10–11.9 band)

- **Kind:** probability
- **Proposed change:** ... (file, section, old → new, verbatim enough to apply)
- **Motivation:** ... (what happened, and why it moves this number)
- **Sources:** ... (URL + retrieval date per source, e.g. `- https://… (retrieved 2026-10-06)`)
- **Status:** proposed
```

Kinds: `context`, `metric`, `event-new`, `event-retired`, `event-pinned`, `probability`, `anchor` (Metaculus refresh). For `event-retired` vs `event-pinned`, recommend one and say why – the human decides. Entries must be independently applicable (approving U2 must not require U1).

Present the proposal to the user and stop. Do not touch scenario files in this phase – not even "trivial" ones.

## Phase 4: Apply (approved entries only)

1. The human marks entries `Status: approved` or `Status: rejected` (with a reason). Apply **only** `approved` entries, exactly as written; anything unclear goes back as a question, not a guess.
2. Run `python -m scenario_lab.cli validate scenarios/<id>` and `describe scenarios/<id>`. Fix errors.
3. Record the update: append to `design-notes.md` under an "Updates" heading (date, applied entry ids, rejected ones with reasons). An update changes the scenario's physics – runs before and after it are **not comparable**. If the scenario is mid-analysis, say so out loud and offer a dated variant (`variants/` + note) instead of overwriting, so batches stay apart.
4. Report: what changed, what was rejected, the validation verdict, and whether existing runs are still comparable (they are not, across an applied update).

## What this skill does not do

- No live fetching during runs: market figures are snapshotted into `events.md` (`**Metaculus:**`, `**Retrieved:**`, `**Market probability:**`) with source, URL and date – the run never calls the web.
- No silent physics changes: a probability edit, a retired event, a moved metric start value each need their own approved entry.
- No invented facts: a claim without a source is marked `[assumption]` in the entry and needs explicit approval to survive.
