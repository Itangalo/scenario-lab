#!/bin/bash
# Stage-1 rerun remainder: 59 branches (turns 2-5) after the watched A1-rep1 pilot.
# Reads tasks from story/stage-1-blocks-rerun.json (rep 1 of A1 already launched
# by hand as the pilot). Each line: "<parent> <seed> <path> <rep>".
# 6-wide xargs; per-job logs in story/stage-1-logs/. After all RUN_DONE,
# fill "dir" fields in the manifest from each job log's "Results saved to".
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
mkdir -p scenarios/europe-2032/story/stage-1-logs
python3 -c "
import json
tasks=json.load(open('scenarios/europe-2032/story/stage-1-blocks-rerun.json'))
skip={('A1',1)}
for t in tasks:
    if (t['path'],t['rep']) in skip: continue
    print(f\"scenarios/europe-2032/runs/{t['parent']} {t['seed']} {t['path']} {t['rep']}\")
" > scenarios/europe-2032/story/stage-1-tasks.txt
wc -l scenarios/europe-2032/story/stage-1-tasks.txt
cat scenarios/europe-2032/story/stage-1-tasks.txt | xargs -P 6 -n 4 bash -c '
  parent="$0"; seed="$1"; path="$2"; rep="$3"
  log="scenarios/europe-2032/story/stage-1-logs/${path}-rep${rep}.log"
  caffeinate -i scripts/run-notify.sh "$log" -- python3 -u -m scenario_lab.cli branch "$parent" --from-turn 1 --turns 5 --seed "$seed" --log-llm-io >> "$log" 2>&1
'
echo "ALL STAGE-1 JOBS DONE"
