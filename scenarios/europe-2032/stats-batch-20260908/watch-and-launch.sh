#!/bin/bash
# Overnight gate: wait for mains power, validate once, then launch caffeinated.
# The harness dies on battery (clamshell sleep cannot be prevented there),
# so launching on 17% battery would burn credits on partial runs.
#
# Start:  nohup bash scenarios/europe-2032/stats-batch-20260908/watch-and-launch.sh >> scenarios/europe-2032/stats-batch-20260908/watcher.log 2>&1 &
set -u
ROOT="/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
HERE="$ROOT/scenarios/europe-2032/stats-batch-20260908"
LOG="$HERE/batch.log"

echo "[$(date '+%F %T')] watcher started (waiting for AC power)"
while ! pmset -g batt 2>/dev/null | grep -q "AC Power"; do sleep 60; done
echo "[$(date '+%F %T')] AC power detected, validating scenario"

cd "$ROOT"
if ! python3 -m scenario_lab.cli validate scenarios/europe-2032 >> "$HERE/watcher.log" 2>&1; then
  echo "[$(date '+%F %T')] VALIDATION FAILED -- batch NOT launched" | tee -a "$HERE/watcher.log"
  exit 1
fi

echo "[$(date '+%F %T')] validation OK, starting monitor + batch"
nohup bash "$HERE/monitor-loop.sh" >> "$HERE/watcher.log" 2>&1 &
caffeinate -dimsu scripts/run-notify.sh "$LOG" -- bash "$HERE/launch-batch.sh"
