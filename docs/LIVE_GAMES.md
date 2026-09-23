# Live Workshop Games

Run a Scenario Lab scenario as a facilitated workshop game: human teams play the actors, choosing from a short menu of LLM-generated options each turn. One computer (the facilitator's), printed handouts, no laptops for the teams.

## Facilitator web UI (no terminal)

```bash
scenario-lab-facilitate   # then open http://127.0.0.1:8000/
```

The page covers the whole loop: pick a scenario, start a new game or open an existing one, prepare menus, tick the teams' picks (radio buttons or free text), resolve with a confirm step, and print the briefing plus one sheet per team. Long model calls run in the background with a visible log. It writes exactly the same `turn-NN/live/` artifacts as the CLI below, so you can mix the two freely on one game – the UI and the terminal stay interoperable. The server binds localhost only and needs no new dependencies.

## The loop

One command starts or resumes a game – it finds the live-ready scenario, asks new-or-resume when there is anything to ask, and prepares the menus:

```bash
python -m scenario_lab.cli live --skip-model-checks
```

(With a single live-ready scenario and no previous games, it asks nothing at all. Pass a scenario or run directory to skip the questions: `live scenarios/global-ai-live` starts a new game, `live <run-dir>` continues one at its next unfinished turn.)

Then the whole workshop runs on that one command, repeated:

- `live` with fresh menus → print handouts, teams deliberate.
- `live` again → enters the picks through the picker (headers in the terminal, details on paper; `back` revisits, final summary with per-team redo), resolves the turn, and prepares the next turn's menus on the spot.

```bash
python -m scenario_lab.cli live --skip-model-checks   # menus (or picks, if menus are ready)
# print turn-NN/live/*, teams deliberate, repeat
```

`live-resolve` remains for direct use (and `--actor-action` flags for scripting), and `live-menu` for starting a game or regenerating a turn's menus. `live` with a pending turn and `--actor-action` flags resolves non-interactively.

`live-menu` is only needed to start a game (or to regenerate a turn's menus, or with `--no-auto-menu` on the resolve). It rolls the turn's events first (same seeded dice as a simulated turn), so the menus already reflect this turn's shocks. Re-running it reuses the recorded events and overwrites the menus – the teams' situation never changes under a regenerated menu.

`live-resolve` shows each team's option headers in the terminal (descriptions stay on the printed sheets); answer with a number (`3`, `option 3`) or free text for an off-menu move. `back` revisits the previous team, and a final summary lets you redo any team by number or name before confirming. Every team must pick exactly one option. For scripting or tests, pass picks non-interactively instead:

```bash
python -m scenario_lab.cli live-resolve <run> --turn 1 \
  --actor-action us-gov=2 --actor-action us-labs=1 \
  --actor-action china="we propose a joint safety summit" --actor-action eu=4
```

## Finding the files

Live games live under `scenarios/<name>/runs/live-YYYYMMDD-HHMMSS/` (instead of `run-*`). Per turn, `turn-NN/live/` holds `briefing.md` (world summary, metrics, events – present or print for everyone), one `menu-<actor>.md` per team, and `menu.json` (machine-readable, for shorthand resolution). Everything else in the turn folder is the standard artifact layout, so `costs`, `check-run-integrity`, `resume`, and `branch` all work on live runs unchanged. Note: while teams deliberate, the newest turn holds menus but no resolution yet – `check-run-integrity` reports that honestly as "menus generated, awaiting resolve (pending live turn)" with a warning, not an error.

## Tuning the generated language

To tune what Scenario Lab itself writes – menu options and turn narratives fitted to the room – declare a `workshop:` block in scenario.yaml:

```yaml
workshop:
  audience: "professional colleagues with no AI background"
  tone: "plain, jargon-free, brisk"
```

It renders into the menu and narrative prompts (as `workshop_guidance`, overridable per prompt type like any template). For a non-English group, use `output_language` (e.g. `--override output_language=German`) – menus and briefing content follow. The workshop leader knows the audience and picks the voice herself; there is deliberately no leader-facing notes file.

## 90-minute checklist

- **Use a short scenario.** `global-ai-live` (4 teams, 3 turns) is built for this. Fewer actors = less facilitation load.
- **Freeze rule evolution** (`rule_evolution.freeze_until_turn` covering all turns) so turns resolve fast and the world stays legible.
- **Use cheap models.** Menus cost one call per team per turn; the default `global-ai-live` config runs on the free contributor tier, so a full 3-turn game costs nothing marginal (cost reports show $0.00 for it).
- **Budget ~25 minutes per turn:** 5 min briefing, 10 min team deliberation + cross-team negotiation, 5 min picks + resolution, 5 min presenting the new world state. 3 turns + intro/debrief fits 90 minutes.
- **Decide the end in advance.** Tell the teams how many turns you will play; the leader can stop after any resolved turn – the run is complete as a record wherever it stops.
- **Dry-run the full game** with `--actor-action` flags before the workshop to check timing and handout readability.

## Options and limitations

- `--max-options N` caps the menu length (default 6). No "do nothing" option is added by default; restraint appears only when the model judges it a genuine move.
- `--strategy sample-distill --samples N` draws N free-form drafts per actor first, then distills them into a menu. More faithful to what the simulation would do, but slower and pricier – `direct` (default) is right for a live clock.
- Teams cannot rewrite statement ledgers or persistent store tables from paper; picks resolve as actions only. Prefer storeless scenarios for live play.
- A live run can be continued with `resume` (the LLM takes over the actors) or forked with `branch` for what-if counterfactuals – handy for a debrief ("what if China had picked option 2?").
