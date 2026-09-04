#!/bin/bash
# Run a long command, then notify unmissably when it ends (or fails).
#
# Polling for completion with sleep+pgrep has missed endings repeatedly:
# overbroad patterns, dead sleeps, killed watchers. This inverts it: the
# wrapper owns the child PID, waits on it directly, and then (a) appends a
# stable RUN_DONE marker line to the log, and (b) fires a macOS notification
# with sound. Poll for the marker with grep, never with pgrep.
#
# Usage:
#   nohup scripts/run-notify.sh /tmp/my-run.log -- python3 -m scenario_lab.cli batch-run ... &
#   # ...later, reliably:
#   grep -q RUN_DONE /tmp/my-run.log && echo finished
#
# The marker line looks like:
#   RUN_DONE exit=0 at 2026-09-04T10:30:00
set -u

if [ "$#" -lt 3 ] || [ "$2" != "--" ]; then
  echo "usage: run-notify.sh LOGFILE -- <command...>" >&2
  exit 2
fi

LOGFILE="$1"
shift 2

echo "RUN_START at $(date +%Y-%m-%dT%H:%M:%S) :: $*" >> "$LOGFILE"
"$@" >> "$LOGFILE" 2>&1
CODE=$?
echo "RUN_DONE exit=${CODE} at $(date +%Y-%m-%dT%H:%M:%S)" >> "$LOGFILE"

if [ "$CODE" -eq 0 ]; then
  TITLE="Simulation finished"
  BODY="$(basename "$1") exited 0 — $(date +%H:%M)"
else
  TITLE="Simulation FAILED (exit ${CODE})"
  BODY="$(basename "$1") — check ${LOGFILE}"
fi

# Desktop notification (no-op if osascript is unavailable, e.g. over plain ssh).
if command -v osascript >/dev/null 2>&1; then
  osascript -e "display notification \"${BODY}\" with title \"${TITLE}\" sound name \"Glass\"" 2>/dev/null || true
fi
# Terminal bell for any attached session watching the log.
printf '\a'

exit "$CODE"
