#!/usr/bin/env python3
"""Compare the benchmark cohorts on cost, time and output quality.

Reads every run carrying the benchmark tag and groups by model. Because the two
cohorts share dice seeds, a pair sees identical events and any difference is the
model. Quality is scored on the axes `docs/MODEL_TESTING.md` already uses --
constitutional violations, unresolved turns, dropped metrics, parse failures --
plus the physics checks Phase 1 of the roadmap declares, since a model that is
cheap and fast but produces a world that does not behave is not a saving.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

TAG = "batch=benchmark-muse-20260909"
RUNS = Path(__file__).resolve().parent.parent / "runs"

# Metrics that may only rise, per constitutional invariant 2.
ACCUMULATED = ("ai_capability", "openweight_capability")
ELECTION = {"election_consolidation", "election_alliance", "election_retrenchment"}


def model_of(config: dict) -> str:
    blob = json.dumps(config.get("llm", {}).get("events", ""))
    return "muse" if "muse" in blob else "qwen"


def load_runs() -> list[dict]:
    out = []
    for cfg_path in sorted(RUNS.glob("run-*/config.json")):
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            continue
        notes = (cfg.get("initial_state") or {}).get("notes") or ""
        if TAG not in notes:
            continue
        out.append({"dir": cfg_path.parent, "config": cfg})
    return out


def score(run: dict) -> dict:
    d: Path = run["dir"]
    cfg = run["config"]
    turns = sorted(d.glob("turn-*"))

    r = {
        "run": d.name,
        "model": model_of(cfg),
        "effort": cfg.get("llm", {}).get("reasoning_effort"),
        "seed": cfg.get("random_seed"),
        "turns": 0,
        "violation_turns": 0,
        "unresolved": 0,
        "iterations": 0,
        "dropped_metrics": 0,
        "accum_falls": 0,
        "election_turn5": None,
        "events_total": 0,
        "cost": None,
        "tokens": None,
        "completion": 0,
        "seconds": None,
        "sec_per_turn": None,
    }

    prev: dict[str, float] = {}
    for t in turns:
        metrics_file = t / "4-metrics.json"
        if not metrics_file.is_file():
            continue  # partial turn; not completed
        r["turns"] += 1

        check = t / "5-constitutional-check.json"
        if check.is_file():
            c = json.loads(check.read_text())
            if c.get("violations_found"):
                r["violation_turns"] += 1
            if c.get("status") not in ("approved", "corrected_and_approved"):
                r["unresolved"] += 1
            r["iterations"] += int(c.get("iterations") or 0)

        meta = t / "4-metrics-metadata.json"
        if meta.is_file():
            r["dropped_metrics"] += len(
                json.loads(meta.read_text()).get("missing_metrics") or []
            )

        vals = json.loads(metrics_file.read_text())
        if isinstance(vals, dict):
            for key in ACCUMULATED:
                now, before = vals.get(key), prev.get(key)
                if isinstance(now, (int, float)) and isinstance(before, (int, float)):
                    if now < before - 1e-9:
                        r["accum_falls"] += 1
            prev = {k: v for k, v in vals.items() if isinstance(v, (int, float))}

        ev_file = t / "1-events.json"
        if ev_file.is_file():
            try:
                ev = json.loads(ev_file.read_text())
                ids = [e.get("id") for e in ev] if isinstance(ev, list) else []
                r["events_total"] += len(ids)
                if t.name == "turn-05":
                    r["election_turn5"] = sum(1 for i in ids if i in ELECTION)
            except Exception:
                pass

    costs = d / "costs.json"
    if costs.is_file():
        c = json.loads(costs.read_text())
        r["cost"] = c.get("total_cost_usd")
        r["tokens"] = c.get("total_tokens")
        # Completion tokens are the direct proxy for reasoning spend: a
        # reasoning model bills its thinking here, so this is where a change of
        # effort level shows up rather than in the prompt side.
        r["completion"] = sum(
            t.get("completion_tokens") or 0 for t in (c.get("by_turn") or [])
        )

    # costs.json carries no timing, so wall clock is measured from the artefacts.
    # The start time comes from the run directory name, not config.json: that
    # file is rewritten every turn, so its mtime tracks the latest turn and
    # reports a run that has been going an hour as four minutes old.
    last = max(
        (t / "4-metrics.json" for t in turns if (t / "4-metrics.json").is_file()),
        key=lambda f: f.stat().st_mtime,
        default=None,
    )
    started = None
    stamp = d.name.split("run-", 1)[-1][:15]
    try:
        started = datetime.strptime(stamp, "%Y%m%d-%H%M%S").timestamp()
    except ValueError:
        pass
    if started is not None and last is not None:
        r["seconds"] = last.stat().st_mtime - started
        if r["turns"]:
            r["sec_per_turn"] = r["seconds"] / r["turns"]
    return r


def main() -> int:
    runs = load_runs()
    if not runs:
        print(f"No runs found carrying {TAG!r}")
        return 1

    rows = [score(r) for r in runs]
    rows.sort(key=lambda r: (r["model"], r["seed"]))

    print(f"{len(rows)} tagged runs\n")
    hdr = (f"{'run':<26} {'model':<5} {'effort':<8} {'seed':<8} {'turns':>5} "
           f"{'viol':>5} {'unres':>6} {'iters':>6} {'drop':>5} {'fall':>5} "
           f"{'t5el':>5} {'evts':>5} {'compl':>8} {'cost':>9} {'s/turn':>7}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        cost = f"${r['cost']:.4f}" if isinstance(r["cost"], (int, float)) else "-"
        secs = f"{r['sec_per_turn']:.0f}" if isinstance(r["sec_per_turn"], (int, float)) else "-"
        print(f"{r['run']:<26} {r['model']:<5} {str(r['effort']):<8} {r['seed']:<8} "
              f"{r['turns']:>5} {r['violation_turns']:>5} {r['unresolved']:>6} "
              f"{r['iterations']:>6} {r['dropped_metrics']:>5} {r['accum_falls']:>5} "
              f"{str(r['election_turn5']):>5} {r['events_total']:>5} {r['completion']:>8} {cost:>9} {secs:>7}")

    print("\nper model (means over completed runs)")
    for model in ("qwen", "muse"):
        sel = [r for r in rows if r["model"] == model and r["turns"]]
        if not sel:
            continue
        n = len(sel)
        avg = lambda k: sum(r[k] for r in sel) / n  # noqa: E731
        costs = [r["cost"] for r in sel if isinstance(r["cost"], (int, float))]
        secs = [r["sec_per_turn"] for r in sel if isinstance(r["sec_per_turn"], (int, float))]
        print(f"  {model}: turns {avg('turns'):.1f}  completion-tok {avg('completion'):.0f}  violation-turns {avg('violation_turns'):.1f}  "
              f"unresolved {avg('unresolved'):.1f}  referee-iters {avg('iterations'):.1f}  "
              f"dropped-metrics {avg('dropped_metrics'):.1f}  accum-falls {avg('accum_falls'):.1f}  "
              f"events {avg('events_total'):.1f}")
        if costs:
            print(f"         cost ${sum(costs)/len(costs):.4f}/run", end="")
        if secs:
            print(f"   {sum(secs)/len(secs):.0f}s/turn", end="")
        print()

    print("\ncolumns: viol=turns where the referee raised something; unres=turns it could not "
          "resolve; iters=total referee iterations; drop=metrics missing from a turn's JSON; "
          "fall=accumulated metric went down (invariant 2); t5el=election outcomes at turn 5 "
          "(contract says exactly 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
