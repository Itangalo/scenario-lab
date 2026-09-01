# Branch A1 – turns 2 to 5 (ECHO 2026-09-01)

The first branch of the tree to be built past the fixed opening. A1 is the acceleration arm after the reader chose [`option-02-1`](turn-01/option-02-1.md), the Emergency Resilience Surge: harden critical infrastructure now, and buy time rather than build anything.

Built as a pilot on 2026-09-01, to see whether the pipeline and the rebuilt measure mechanics behave before the other five branches are committed to. The turns are [`turn-02-A1`](turn-02-A1/) through [`turn-05-A1`](turn-05-A1/); each holds `turn.md`, the half-year as the story tells it, and `alternatives.md`, what the other nine runs did with the same half-year.

## How it was made

Turn 1 was pinned afresh rather than reused: the three `run-open-*-base` directories date from 30 August and predate both the turn-1 option split and the metric-rules rewrite of 1 September, so they resolve turn 1 under rules that no longer exist.

```
python scenarios/europe-2032/story/pin-turn-1.py \
    scenarios/europe-2032/variants/acceleration.yaml \
    scenarios/europe-2032/story/turn-01/option-02-1.md 810100 1
# → runs/run-A1-base

python -m scenario_lab.cli branch runs/run-A1-base \
    --from-turn 1 --turns 5 --seed <seed>      # once per seed below
```

Seeds 810101–810110 are unique to this branch and are not to be reused on another branch or arm. The base run holds seed 810100. Ten runs, forty turns, twenty minutes wall clock at ten concurrent, $0.28 in total.

## The runs

| seed | run | `eu_ai_sovereignty` at turn 5 | cost |
|---|---|---|---|
| 810101 | `run-20260901-195330` | 24.0 | $0.0264 |
| 810102 | `run-20260901-195334` | 26.0 | $0.0254 |
| 810103 | `run-20260901-195338` | 26.0 | $0.0325 |
| 810104 | `run-20260901-195342` | 22.0 | $0.0292 |
| 810105 | `run-20260901-195346` | 23.0 | $0.0274 |
| 810106 | `run-20260901-195350` | 29.0 | $0.0258 |
| 810107 | `run-20260901-195354` | 27.0 | $0.0296 |
| 810108 **(the path)** | `run-20260901-195358` | 22.0 | $0.0272 |
| 810109 | `run-20260901-195402` | 32.0 | $0.0250 |
| 810110 | `run-20260901-195406` | 32.0 | $0.0275 |

## How the path was chosen

`random.Random(20260901).choice(range(810101, 810111))`, which draws 810108. The draw seed is the date of the batch, recorded so the choice can be audited rather than argued about. It is a random draw and not a representative one, on the reasoning in [`README.md`](README.md): always taking the median would put every part of the story in the middle of the bell curve.

The draw landed on a bleak run, and one worth knowing is bleak. Sovereignty does not move on it at all – 22.0 at turn 1, 22.0 at turn 5, against a batch that reaches 32 twice. Safety falls from 34 to 15, the steepest fall of the ten. The Union spends the whole two years on a talent programme it never finishes and an export-control negotiation that concludes as a declaration with Japan and the Netherlands after the United States refuses to sign.

## What the batch showed

**Sovereignty moves now, and did not before.** Turn-5 sovereignty spreads 22.0 to 32.0 with a mean of 26.3. The two archived batches of thirty put every road in every arm within three points of the starting 22, at 24.0 to 25.0. That is the open question in [`design-notes.md`](../design-notes.md) answered in the direction the rebuilt measure mechanics were meant to move it: the wall is gone, but the climb is not automatic, and four of the ten runs still end within a point of where they started. Worth re-deriving on a branch that is not A1 before it is treated as settled – A1 opens with a category 6 measure, so it is not the branch most likely to build sovereign capacity.

**The 2028 election fires reliably and is narrated almost never.** Exactly one of the three outcomes fired in all ten runs, which is the repaired mutually-exclusive group behaving, and all three were reachable: five alliance, three retrenchment, two consolidation. Metric rule 8 asks for two things – write the `US_POSTURE:` line into the world state that turn, and carry it in the notepad every turn after. The notepad half was done in 10 runs of 10. The world-state half was done in one, seed 810107. Four world states, the path among them, do not mention the election in any form at all.

The mechanical effect still lands: the path drew retrenchment, and `ai_capability` grows 3.0 in turn 5 against 3.5 in each of the two turns before it, which is the quarter reduction the rule asks for. So this is not the rule being ignored. It is the rule being applied where the machinery reads it and omitted where the reader would. For the story that is the worse half to lose – on the path, the largest scheduled beat of the whole segment is invisible in `turn-05-A1/turn.md`, and a writer working from that file alone would not know the United States had held an election.

Rule 8 is one sentence asking for two things in two places. The handoff's own lesson applies: required, formatted output the model has to write down is reliable, and the notepad line is exactly that while the world-state line is a sentence in a prose instruction. Splitting the two, and making the world-state line as formatted a requirement as the `PORTFOLIO CHARGE` line, is the shape of the fix.

**Events are dropped from the prose more generally.** Five events fired at turn 5 on the path. The world state narrates the loss of control and the frontier advance, and says nothing of `ai_investment_collapse`, `safety_breakthrough` or the election. It also opens by calling the turn's rise "not a discontinuous leap" in a turn where `capability_jump` triggered.

**`Makes the case for:` was not parsed, and has been deleted.** Not a finding of this batch, but found while reading it: the field sat on 31 events, the `Event` model had no attribute for it, and the loader discarded all 31 exactly as it had discarded `Cheapens:` before the rename. Resolved on 2026-09-01 by deletion rather than repair – metric rule 6 already carries the whole mechanic, judged against the event record, and a second source of truth that reaches no prompt is worse than none. The 31 lines, the framing section that explained them, and the sentence in `user-prompts/metrics-update.md` that pointed the Game Master at them are all gone. `validate` now warns when an events file carries a field the parser drops.

This does not invalidate the ten runs. The field was already dead when they ran, so they were resolved under exactly the mechanic that remains: rule 6, judged. The turn-5 notepad on the path shows it working — `PROPOSAL BONUS: ... +4`, with the two events it answers named.
