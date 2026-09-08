"""One progress snapshot for the stats-20260908 batch (see monitor-loop.sh).

Identifies batch runs by config.json initial_state.notes pair
batch=stats-20260908 (exact match; the pilot used batch=...-pilot and the
story-block runs carry no initial_state, so neither is counted).
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3")
HERE = ROOT / "scenarios/europe-2032/stats-batch-20260908"
RUNS = ROOT / "scenarios/europe-2032/runs"
BATCH = "stats-20260908"
TOTAL_RUNS = 150
TOTAL_TURNS = 1950  # 150 runs x 13 turns

_PAIR_RE = re.compile(r"(\w+)\s*=\s*([^;,]+)")


def main() -> None:
    final = "--final" in sys.argv
    now = datetime.now().astimezone()
    start = None
    try:
        m = re.search(
            r"RUN_START at (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            (HERE / "batch.log").read_text(encoding="utf-8"),
        )
        if m:
            start = datetime.fromisoformat(m.group(1)).astimezone()
    except OSError:
        pass

    runs = completed = turns = 0
    arms: dict[str, int] = {}
    for run_dir in RUNS.iterdir():
        if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
            continue
        try:
            cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        notes = (cfg.get("initial_state") or {}).get("notes", "")
        pairs = {k: v.strip() for k, v in _PAIR_RE.findall(notes)}
        if pairs.get("batch") != BATCH:
            continue
        runs += 1
        try:
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            summary = {}
        if isinstance(summary, dict) and summary.get("status") == "completed":
            completed += 1
            name = str(cfg.get("name", "?")).replace("Europe 2032 \u2014 ", "")
            arms[name] = arms.get(name, 0) + 1
        else:
            turns += sum(
                1
                for t in run_dir.iterdir()
                if t.is_dir()
                and t.name.startswith("turn-")
                and (t / "4-metrics.json").exists()
            )

    done_turns = completed * 13 + turns
    line = (
        f"[{now:%F %T}] runs {completed}/{TOTAL_RUNS} completed "
        f"({runs} batch dirs on disk), ~{done_turns}/{TOTAL_TURNS} turn-executions"
    )
    if start and done_turns > 0:
        elapsed = max((now - start).total_seconds() / 60, 0.1)
        rate = done_turns / elapsed
        eta_min = (TOTAL_TURNS - done_turns) / rate if rate > 0 else float("inf")
        line += f", {rate:.1f} turns/min, ETA ~{eta_min / 60:.1f}h"
    print(line, flush=True)
    if final:
        print(f"[{now:%F %T}] per-arm completed: {arms or 'n/a'}", flush=True)


if __name__ == "__main__":
    main()
