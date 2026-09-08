#!/bin/bash
# Full 50x3 stats batch for europe-2032 (all arms, same two-year commitments
# as the story runs). Invoked via scripts/run-notify.sh, which owns the log
# and appends the RUN_DONE marker + desktop notification.
#
# Separation: every job gets one provenance-only draw from initial-states/
# (notes: "batch=stats-20260908; draw=NNN"), recorded in its config.json.
# Isolate with:  synthesize ... --filter batch=stats-20260908
# Arms split with: --group-by scenario
set -u
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/kodprojekt/Scenario Lab 3"
python3 -m scenario_lab.cli batch-run scenarios/europe-2032 --variants --repeat 50 \
  --initial-states scenarios/europe-2032/stats-batch-20260908/initial-states \
  --max-concurrency 10
