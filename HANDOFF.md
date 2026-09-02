# Handoff – sessions of 2026-08-28/30, 2026-08-31/09-01, and 2026-09-02

## Read these first

- `scenarios/europe-2032/design-notes.md` – the scenario's own record, including "Calibrating political capital"
- `scenarios/europe-2032/sign-off/` – the four prompts as they are actually sent, regenerated 2026-09-01
- `scenarios/europe-2032/metric-rules.md` – rewritten this session, organised by metric
- `.claude/skills/create-scenario/SKILL.md`, section "Writing metric-rules.md" – the form, and why

## Where the scenario stands

`metric-rules.md` is now one rule per metric, gathering every term that moves it, with cross-cutting mechanics after. Eleven rules. The preamble is load-bearing: **"Figures are for this turn: a rule applies in whatever turn its condition holds, and applies again whenever it holds again. Nothing carries itself forward."** It used to say "per turn unless stated", which made a bare number an annuity and produced the largest physics bug of the session – one finished category 4 measure paid forever, so a run that built once ended level with a run that built six times.

The three trajectory arms separate cleanly on capability: acceleration ends near 86–92, verification-bounded near 67–73, plateau near 63–67. That was in doubt until 2026-09-01 and is now settled over 36 runs plus two batches of 12.

Turn 1 of the story is built and unaffected by any of the physics work: `story/turn-01/` holds the shared frame plus two options, verbatim draws from a pool of 30.

## What was fixed, and what it cost to learn

**Timing became a one-off.** Events carried `Cheapens: category N by X for Y turns`, a per-turn discount on the portfolio charge. It was applied in 6 of 166 opportunities – the Game Master will not re-derive a four-way lookup every turn. It is now `Makes the case for:` and pays a one-off bonus at proposal, judged rather than looked up. Working.

**Required output lines fixed three mechanics.** The portfolio charge, the proposal bonus and the legitimacy loan were each unreliable until the Game Master had to write them into the notepad, and reliable afterwards. This became the house pattern.

**The pattern then failed on the fourth attempt, and the reason is the useful part.** Sovereignty was inflating: eight of twelve runs moved it +6 or more in a single turn, against a legal maximum of +2 for anything short of a completion. A `SOVEREIGNTY:` line was added on the same principle. It is now written in **156 of 156 turns** – and the inflation is unchanged, still 8 of 12 runs, with the largest jump growing from +10 to +12.

The diagnosis: **the stated total matches the applied change in only 16 of 70 turns (23%)**. The charge line worked because it *is* the computation – the Game Master must total it to apply it. The sovereignty line is written *beside* a value decided elsewhere, and nothing reconciles the two. Sample lines show the failure modes plainly: a measure credited as finishing twice, two turns apart; a category 6 measure credited to sovereignty as `in flight +5`; totals stated as +4 and applied as +6.

**Writing it down only works when the writing is the mechanism.** That is the correction to the pattern, and it is the most transferable thing this session produced.

## Open, in the order I would take them

1. **Sovereignty accounting does not bind.** See above. Options: make the metrics step emit sovereignty as a computed sum rather than a judged value; or narrow rule 5 so there is nothing to judge (a completion is worth exactly +4, no range); or accept the drift and stop reporting sovereignty as a result.
2. **The agency floor is uncalibrated, and the batch that would calibrate it is contaminated.** `scenario.yaml` says thresholds are first guesses to be set against the first full batch. Final political capital across the latest 12: `9 12 17 20 26 30 33 35 41 42 42 56`, median 32, and 4 of 12 clear the current floor of 40. At >=30 it would be 7 of 12, at >=25, 8. But sovereignty inflation feeds capital through rule 6's dividend above 40, so calibrate only after item 1.
3. **`r` between category 4 measures and final sovereignty is not yet a result.** Reported as +0.61 mid-session; recomputed over the same runs it is +0.41, and the newest batch gives +0.23. The mid-session figure was computed while runs were still finalising and should be disregarded. None of the three is trustworthy while item 1 stands.
4. **The story tree is 168 turn pieces and 42 options** across three arms, each built from ten or more simulations. Turn 1 is done. Nothing beyond it should be built until item 1 is settled, because turns 2–5 depend on the physics.
5. **`load_actor` still truncates.** Everything below the first `###` in an actor file is dropped. Worked around in europe-2032 by moving what mattered into the turn prompt; five actor files in three scenarios still lose content silently.

## Things that will bite you if nobody says them

- **Silent failure is this codebase's characteristic bug.** Truncated actor background, event fields that reached no prompt, statement proposals lost to a code-span wrapper, an arithmetic total copied forward while the portfolio grew. None of them errored. `validate` passes through all of it.
- **Variant patches bind by rule number** and replace the rule wholesale. Renumbering `metric-rules.md` silently repoints them: mid-session the three arms were overwriting `ai_safety` with open-weight text because rule 3 had moved. Renumber patches and cross-references in the same commit, and check `events.md`, `constitution.md`, `scenario.yaml` and the prompt overrides, which all cite rules by number.
- **Seeds must be unique per run.** Blocks used so far: 5101–5330, 5401–5834, 6101–6302, 7101–7312, 7401–7604, 7701–7904.
- **The harness kills background tasks at about 30 minutes.** Long batches belong in a terminal tab, or detached with `nohup`. The scratchpad holds self-resuming drivers that survive it.
- **`caffeinate -s` is ignored on battery**, and no flag prevents clamshell sleep on battery. Overnight batches need mains power.
- **Sign-off documents are the check that the prompts say what you think.** Regenerate after any prompt change: run 2 turns with `--log-llm-io`, then `python scripts/render_signoff.py <run-dir>`. A regeneration is what caught the defect in the then-`Cheapens:` field.

## Untracked and deliberate

`runs/` and `actor-samples/` are gitignored. 117 run directories exist locally; the analysis that matters is in `design-notes.md`, because the directories are not backed up and were cleared once already this session.
