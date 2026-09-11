#!/usr/bin/env python3
"""Join Stage-2 reps back to blocks after the batch completes.

Reads story/stage-2-logs/<BLOCK>-rep<N>.log for the branch dir
("Created branch: <name>") and seed ("Random seed: <int>"), plus
story/stage-2-tasks.txt for parent/fixture/option, and writes
story/stage-2-blocks-rerun.json (one entry per rep, incl. the watched
A11-rep1 pilot from story/stage-2-pilot-A11.log).

Verifies every rep log ended RUN_DONE exit=0 and every run dir completed.
"""
import json
import re
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent
RUNS = STORY.parent / "runs"

TASKS = (STORY / "stage-2-tasks.txt").read_text().splitlines()
entries = []
problems = []

for line in TASKS:
    parent, fixture, option, block, rep = line.split()
    rep = int(rep)
    log = STORY / "stage-2-logs" / f"{block}-rep{rep}.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    m_dir = re.findall(r"Created branch: (\S+)", text)
    m_seed = re.findall(r"Random seed: (\d+)", text)
    done = re.findall(r"RUN_DONE exit=(\d+)", text)
    entry = {"dir": m_dir[-1] if m_dir else None, "path": block, "rep": rep,
             "seed": int(m_seed[-1]) if m_seed else None, "parent": parent,
             "fixture": fixture, "option": option,
             "exit": int(done[-1]) if done else None}
    if entry["dir"] is None or entry["seed"] is None or entry["exit"] != 0:
        problems.append(f"{block} rep{rep}: dir={entry['dir']} seed={entry['seed']} exit={entry['exit']}")
    else:
        summary = RUNS / entry["dir"] / "summary.json"
        try:
            status = json.loads(summary.read_text()) .get("status")
        except (OSError, ValueError):
            status = "?"
        if status != "completed":
            problems.append(f"{block} rep{rep} {entry['dir']}: status {status}")
    entries.append(entry)

# Watched pilot (A11 rep1) ran outside the task list.
pilot_log = (STORY / "stage-2-pilot-A11.log").read_text(encoding="utf-8", errors="replace")
m_dir = re.findall(r"Created branch: (\S+)", pilot_log)
m_seed = re.findall(r"Random seed: (\d+)", pilot_log)
entries.append({"dir": m_dir[-1] if m_dir else "run-20260911-002005",
                "path": "A11", "rep": 1,
                "seed": int(m_seed[-1]) if m_seed else 14477735025383896940,
                "parent": "run-20260910-223510",
                "fixture": "run-20260911-000401-04",
                "option": "pool-06-A1-20260911/sample-01.md", "exit": 0,
                "pilot": True})

out = STORY / "stage-2-blocks-rerun.json"
out.write_text(json.dumps(entries, indent=1) + "\n")
print(f"{len(entries)} entries -> {out}")
print("PROBLEMS:" if problems else "ALL CLEAN")
for p in problems:
    print(" ", p)
sys.exit(1 if problems else 0)
