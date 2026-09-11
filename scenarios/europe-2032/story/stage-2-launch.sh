#!/bin/bash
# Stage-2 rerun: 12 blocks x 10 reps (turns 6-9) via story/pin-turn.py.
# A11-rep1 ran separately as the watched pilot; the 119 lines below are the rest.
# Each line: "<parent-run> <fixture-evaluations> <option-sample> <block> <rep>".
# 6-wide xargs; per-rep logs in story/stage-2-logs/. Seeds are drawn inside
# pin-turn.py and recorded in each run's config.json; stage-2-fill-manifest.py
# joins them back to blocks afterwards.
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
S="scenarios/europe-2032/story"
R="scenarios/europe-2032/runs"
mkdir -p "$S/stage-2-logs"
cat "$S/stage-2-tasks.txt" | xargs -P 6 -n 5 bash -c '
  parent="$0"; fixture="$1"; option="$2"; block="$3"; rep="$4"
  log="scenarios/europe-2032/story/stage-2-logs/$block-rep$rep.log"
  caffeinate -i scripts/run-notify.sh "$log" -- python3 -u scenarios/europe-2032/story/pin-turn.py \
    "scenarios/europe-2032/runs/$parent" 5 6 \
    "scenarios/europe-2032/runs/$fixture/turn-06/1-event-evaluations.json" \
    "scenarios/europe-2032/story/$option" 9 >> "$log" 2>&1
'
echo "ALL STAGE-2 JOBS DONE"
