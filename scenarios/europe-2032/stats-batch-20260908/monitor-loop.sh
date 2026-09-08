#!/bin/bash
# Progress reporter: one snapshot now, then every 20 minutes until RUN_DONE.
set -u
HERE="/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3/scenarios/europe-2032/stats-batch-20260908"
LOG="$HERE/batch.log"
PROG="$HERE/progress.log"

while true; do
  python3 "$HERE/monitor-progress.py" >> "$PROG" 2>&1
  if grep -q RUN_DONE "$LOG" 2>/dev/null; then
    python3 "$HERE/monitor-progress.py" --final >> "$PROG" 2>&1
    break
  fi
  sleep 1200
done
