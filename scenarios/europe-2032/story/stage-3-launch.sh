#!/bin/bash
# Stage-3 rerun: 24 blocks x 10 reps (turns 10-13) via story/pin-turn.py.
# A111-rep1 ran separately as the watched pilot (war fixture); the 239 lines
# below are the rest. Each line: "<parent-run> <fixture-run> <option-sample>
# <block> <rep>". 6-wide xargs; per-rep logs in story/stage-3-logs/. Seeds are
# drawn inside pin-turn.py and recorded in config.json; join back afterwards
# via "Created branch" + "Random seed" lines in the logs.
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
S="scenarios/europe-2032/story"
mkdir -p "$S/stage-3-logs"
cat "$S/stage-3-tasks.txt" | xargs -P 6 -n 5 bash -c '
  parent="$0"; fixture="$1"; option="$2"; block="$3"; rep="$4"
  log="scenarios/europe-2032/story/stage-3-logs/$block-rep$rep.log"
  caffeinate -i scripts/run-notify.sh "$log" -- python3 -u scenarios/europe-2032/story/pin-turn.py \
    "scenarios/europe-2032/runs/$parent" 9 10 \
    "scenarios/europe-2032/runs/$fixture/turn-10/1-event-evaluations.json" \
    "scenarios/europe-2032/story/$option" 13 >> "$log" 2>&1
'
echo "ALL STAGE-3 JOBS DONE"
