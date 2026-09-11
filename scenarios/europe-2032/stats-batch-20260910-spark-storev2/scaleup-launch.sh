#!/bin/bash
# Scale-up of the Muse Spark + store-v2 stats rerun (rerun-plan.md).
# Checkpoint (21 runs, draws 001-021) passed 2026-09-10; this adds the
# remaining 43/arm = 129 jobs on draws 022-150, per-arm dirs so no draw
# is reused across arms. Batch tag throughout: stats-20260910-spark-storev2.
# Three parallel batch-runs at concurrency 4 each (12 total, within the
# previously used range). One log + RUN_DONE marker per arm; poll with:
#   grep -q RUN_DONE <log> && echo finished   (all three logs)
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
BASE="scenarios/europe-2032/stats-batch-20260910-spark-storev2"
nohup caffeinate -i scripts/run-notify.sh "$BASE/scaleup-A.log" -- python3 -u -m scenario_lab.cli batch-run scenarios/europe-2032/variants/acceleration.yaml --repeat 43 --max-concurrency 4 --validate --log-llm-io --initial-states "$BASE/initial-states/per-arm-A" >> "$BASE/scaleup-A.log" 2>&1 &
nohup caffeinate -i scripts/run-notify.sh "$BASE/scaleup-V.log" -- python3 -u -m scenario_lab.cli batch-run scenarios/europe-2032/variants/verification-bounded.yaml --repeat 43 --max-concurrency 4 --validate --log-llm-io --initial-states "$BASE/initial-states/per-arm-V" >> "$BASE/scaleup-V.log" 2>&1 &
nohup caffeinate -i scripts/run-notify.sh "$BASE/scaleup-P.log" -- python3 -u -m scenario_lab.cli batch-run scenarios/europe-2032/variants/plateau.yaml --repeat 43 --max-concurrency 4 --validate --log-llm-io --initial-states "$BASE/initial-states/per-arm-P" >> "$BASE/scaleup-P.log" 2>&1 &
echo "launched 3 arms; poll with: for f in A V P; do grep -q RUN_DONE $BASE/scaleup-\$f.log && echo \$f-done; done"
