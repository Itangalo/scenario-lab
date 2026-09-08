"""Generate provenance-only initial-state draws for the stats batch.

Each draw carries no metric/context overrides (empty = no-op in
apply_initial_state) and exists only to tag its run: the notes string lands in
the run's config.json under initial_state, which cohorts.py exposes to
--filter/--group-by. Story-block runs carry no initial_state, so
`--filter batch=stats-20260908` isolates exactly this batch.

150 draws -> one batch-run with --variants --repeat 50 (150 jobs).
A separate pilot draw lives next to this script (NOT in initial-states/,
so the batch's sorted draw assignment can never pick it up).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "initial-states"
BATCH = "stats-20260908"
N = 150

OUT.mkdir(parents=True, exist_ok=True)
for i in range(1, N + 1):
    (OUT / f"draw-{i:03d}.json").write_text(
        json.dumps({"notes": f"batch={BATCH}; draw={i:03d}"}, indent=2) + "\n",
        encoding="utf-8",
    )
(HERE / "pilot-draw.json").write_text(
    json.dumps({"notes": f"batch={BATCH}-pilot"}) + "\n", encoding="utf-8"
)
print(f"wrote {N} draws + pilot draw in {HERE}")
