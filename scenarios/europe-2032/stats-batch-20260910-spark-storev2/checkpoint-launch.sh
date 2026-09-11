#!/bin/bash
# Checkpoint chunk of the Muse Spark + store-v2 rerun (rerun-plan.md).
# 21 jobs (7/arm) under batch=stats-20260910-spark-storev2, consuming draws 001-021.
# Audit per the checkpoint section before scaling to the remaining 129 (43/arm).
# After the checkpoint passes, move draws 001-021 aside so the scale-up launch
# takes draws 022-150 (no reuse: resolve_initial_state_files takes the first N).
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
LOG="scenarios/europe-2032/stats-batch-20260910-spark-storev2/checkpoint.log"
nohup caffeinate -i scripts/run-notify.sh "$LOG" -- python3 -m scenario_lab.cli batch-run scenarios/europe-2032 --variants --repeat 7 --max-concurrency 6 --validate --log-llm-io --initial-states scenarios/europe-2032/stats-batch-20260910-spark-storev2/initial-states &
echo "launched, poll with: grep -q RUN_DONE $LOG && echo finished"
