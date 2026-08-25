#!/usr/bin/env python3
"""Generate starting-state draws for Forking Futures.

The experimental variable in this scenario is not the starting world -- that is
the same in every run, because mid-2026 looks the same whichever future it turns
into. The variable is the *trajectory regime*: how AI capability develops over
the following nine years. Three regimes are simulated, one per run, fixed from
turn 1 and never changing.

Each draw therefore sets no metrics at all. It appends one block of context
naming the regime, placed after a `<!-- GM-ONLY -->` marker. The scenario's
`user-prompts/actor.md` override truncates the actor's view at that marker, so
the Game Master steps know which future the run is in and the regulator does
not. That asymmetry is the scenario: a regulator has to commit slow instruments
before it can know which world it is committing them to.

Scenario Lab never runs this script. You run it, deliberately, and then point
`--initial-states` at one of the directories it produced.

Usage:

    python3 sampler.py --count 20 --out draws

    # then one batch per arm -- never pooled into a single batch, because the
    # three arms answer "how do outcomes differ between regimes", which requires
    # them to stay separable
    python -m scenario_lab.cli batch-run scenarios/forking-futures \
        --repeat 20 --initial-states scenarios/forking-futures/draws/fast

Runs within one arm are deliberately identical at the start. They diverge only
through the event dice and through what the regulator chooses, which is what
keeps the arm's distribution attributable to those two things alone.
"""

import argparse
import json
from pathlib import Path

MARKER = "<!-- GM-ONLY -->"

REGIMES: dict[str, str] = {
    "fast": """**REGIME: FAST.**

Capability compounds. Progress through the late 2020s is rapid and continues to
accelerate rather than levelling off; recursive self-improvement becomes
possible once the frontier is far enough along, and once it starts, the interval
between capability generations shortens instead of lengthening. Broadly
superhuman performance is a live prospect in the second half of the horizon.

Apply this through metric rule 1 (FAST branch) and through the FAST figures in
the event probabilities. `rsi_onset` is possible in this regime only.""",
    "plateau": """**REGIME: PLATEAU.**

Steady but decelerating progress. Models become substantially more reliable,
cheaper and more widely deployed, and the returns to further scaling visibly
decline. Nothing within the horizon becomes superhuman in any general sense; the
frontier in 2035 is recognisably an extension of the frontier in 2026 rather
than a different kind of thing.

Apply this through metric rule 1 (PLATEAU branch) and through the PLATEAU
figures in the event probabilities, exactly as written: deceleration narrows
the increments, it does not zero them. `rsi_onset` is impossible in this
regime.""",
    "rlvr-limited": """**REGIME: RLVR-LIMITED.**

Progress stays strong where verifiable reward works -- code, mathematics,
offensive and defensive cyber, narrow engineering -- and stays roughly flat
everywhere else. Capability becomes sharply uneven, and the unevenness is the
point: this is a world with superhuman hackers and unremarkable strategists, in
which general-competence measures barely move while a specific class of risk
grows year on year.

Apply this through metric rule 1 (RLVR-LIMITED branch) and through the
RLVR-LIMITED figures in the event probabilities -- note in particular the raised
cyber probabilities, which are where this regime's capability actually shows up.
`rsi_onset` is impossible in this regime.""",
}

PREAMBLE = """## Trajectory Regime for This Run

This section is for the Game Master and the metric and event steps. **It is
withheld from the regulator, who must infer the regime from what actually
happens.** Never state it, name it, or hint at it in the narrative.
"""


def write_draws(out_root: Path, count: int) -> None:
    for arm, body in REGIMES.items():
        arm_dir = out_root / arm
        arm_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, count + 1):
            draw = {
                "metrics": {},
                "context": f"{MARKER}\n\n{PREAMBLE}\n{body}\n",
                "notes": f"arm={arm}; draw={i:03d}; regime fixed for the whole run",
            }
            path = arm_dir / f"draw-{i:03d}.json"
            path.write_text(json.dumps(draw, indent=2) + "\n")
        print(f"{arm}: {count} draws -> {arm_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--count", type=int, default=20, help="draws per arm (default: 20, giving 60 runs)"
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "draws", help="output directory"
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be at least 1")
    write_draws(args.out, args.count)


if __name__ == "__main__":
    main()
