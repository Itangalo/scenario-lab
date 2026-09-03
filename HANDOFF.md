# Handoff – sessions through 2026-09-02

## Read these first

- `scenarios/europe-2032/design-notes.md` – the scenario's own record. The two newest sections cover why the sovereignty line did not bind and what the constitutional referee is actually doing.
- `scenarios/europe-2032/sign-off/` – the four prompts as they are actually sent, regenerated 2026-09-02 from `run-20260902-201003`
- `scenarios/europe-2032/metric-rules.md` – one rule per metric, cross-cutting mechanics after
- `scripts/check_sovereignty.py` – reads a run's notepad accounting against the metric it applied. `--split` compares the current line form against the one it replaced.

## Where the scenario stands

The three trajectory arms separate cleanly on capability: acceleration ends near 86–92, verification-bounded near 67–73, plateau near 63–67. Settled over 36 runs plus three batches of 12.

Turn 1 of the story is built: `story/turn-01/` holds the shared frame plus two options, verbatim draws from a pool of 30. Nothing beyond it is built.

**Sovereignty accounting now binds in two turns of three, against one in three before.** Twelve runs each side, four per arm, thirteen turns. The full table is in the design notes; the short version is that the stated total equals the applied change in 68% of turns against 33%, the line starts from the value the metric actually held in 137 of 138 turns, repeat payment of a completion fell from 13 cases in 9 runs to 9 in 6 with the longest streak cut from six turns to three, and illegal moves above +2 fell from 7 turns to 1.

Three changes did that, and the third was the root cause:

- The line runs from last turn's figure to this turn's, and the number it ends at *is* the metrics JSON value. It used to end at a delta while the JSON carried a level, so nothing joined the two ends.
- Every completion carries the turn it finishes and may be paid only in that turn, which makes a copied line visibly wrong rather than locally plausible.
- **`metrics_json` now reaches the metrics prompt.** It always reached the events and actor prompts. The one step whose output is the next set of metric values was the only one that could not see the current ones, and had to recover them from narrative prose.

## Open, in the order I would take them

1. **Two named causes remain for the third of turns that still do not bind.** An `→ adjusted to N` clause appended after a total is reached — the same escape the old `→ net +1` was — and, separately, the decay term being written in turns where its condition does not hold and then correctly not charged, which is why the line's internal arithmetic fell from 70% to 51% even as binding doubled. The second is a one-clause fix: do not write a term you are not applying. Both were left alone deliberately so the batch measured one change.
2. **The agency floor is uncalibrated, and can now be calibrated.** `scenario.yaml` says the thresholds are first guesses to be set against the first full batch. The contamination that blocked this is largely gone — sovereignty can no longer jump +6 to +12 unnoticed into rule 6's dividend gate at 40 — so run the numbers off the 8101–8304 batch or a fresh one, and not off anything earlier.
3. **`r` between category 4 measures and final sovereignty is still not a result.** Reported as +0.61 mid-session, +0.41 recomputed, +0.23 on the next batch. All three predate the fix and none should be quoted. Recompute on post-fix runs only.
4. **The constitutional referee is not the backstop it looks like.** It raised at least one violation in 117 of 156 baseline turns (75%), naming `eu_ai_sovereignty` in 76, mean 2.13 iterations against a maximum of 4 — and then approved. On `run-20260902-155512` turn 5 it described this session's exact defect correctly ("the notepad shows only +1 from prior momentum, with no justification for an additional +12") and let the turn through. A check that fires on three quarters of turns carries no information in any one of them. Its output sits in `turn-XX/5-constitutional-check.json` and no analysis path opens the file.
5. **`openweight_frontier_release` no longer functions as an event.** Rule 2's trailing clause is fixed — see the design notes — and open-weight capability now tracks the frontier at a stable ~20-point separation instead of flatlining at 45, which reopens the proliferation-keyed event gates at 55, 60 and 65 that had been reached once in 36 runs. The event itself was never obeyed under any wording tried: 39 firings across three versions, zero landing in the stated band, and it now moves the metric 1.2x an ordinary turn. The untested candidate is a destination rather than a direction, inside the clause that already moves.

6. **The story tree is 168 turn pieces and 42 options** across three arms, each built from ten or more simulations. Turns 2–5 depend on the physics, which is now in better shape than it was; item 1 is small enough that it need not block this.
7. **`load_actor` still truncates, but no longer silently.** `validate` now names every heading whose text it drops: six actor files across four scenarios, one more than the five known by hand. It reports rather than repairs, because folding the text back would change what those scenarios send mid-calibration and would duplicate content that prompt overrides have since restated. Which files to fix, and how, is a judgement per file.

## Things that will bite you if nobody says them

- **A metric can go missing from a turn and nothing notices.** In one run of 2026-09-03 the Game Master omitted `openweight_capability` from turn 1's JSON entirely; the previous value was carried forward, the run completed, and only an analysis script that indexed the key found it. Metric completeness is not checked anywhere.
- **Silent failure is this codebase's characteristic bug.** Truncated actor background, event fields that reached no prompt, statement proposals lost to a code-span wrapper, an arithmetic total copied forward while the portfolio grew, and the metrics step never being shown the metrics. None of them errored. `validate` passes through nearly all of it.
- **A measurement can be wrong in the same silent way.** `check_sovereignty.py` first reported 21% binding before and 59% after; both were artefacts of resolving every stated total as a change when the Game Master mixes levels and changes freely. The corrected figures are 33% and 68%. The six shapes are pinned in `tests/test_check_sovereignty.py` — extend that table before trusting a new number out of the script.
- **Variant patches bind by rule number** and replace the rule wholesale. Renumbering `metric-rules.md` silently repoints them. Only rule 1 is patched today, in all three arms. Check `events.md`, `constitution.md`, `scenario.yaml` and the prompt overrides, which all cite rules by number.
- **Seeds must be unique per run.** Blocks used so far: 5101–5330, 5401–5834, 6101–6302, 7101–7312, 7401–7604, 7701–7904, 8001–8002, 8101–8504, 9101–9312, 9401–9504.
- **The harness kills background tasks at about 30 minutes.** Long batches belong in a terminal tab, or detached with `nohup`. Twelve 13-turn runs cost about $1.10 and take roughly 80 minutes at eight concurrent, faster at four.
- **`caffeinate -s` is ignored on battery**, and no flag prevents clamshell sleep on battery. Overnight batches need mains power.
- **Sign-off documents are the check that the prompts say what you think.** Regenerate after any prompt change: run 2 turns with `--log-llm-io`, then `python scripts/render_signoff.py <run-dir>`. Coverage is sampled from two turns of one run, so a heading flipping to **NO** may only mean its gate was shut in those turns.

## Untracked and deliberate

`runs/` and `actor-samples/` are gitignored. The analysis that matters lives in `design-notes.md`, because the directories are not backed up and were cleared once already.
