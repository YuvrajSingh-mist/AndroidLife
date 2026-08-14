#!/bin/bash
# Periodic watcher for a running dailybench batch.
# Sends a macOS notification (via osascript) when the batch process finishes,
# and optionally every N minutes with a progress heartbeat.
#
# Usage:
#   ./scripts/tools/watch_batch.sh --pid <PID> --label "day5-rerun11" [--every 300]
#
# If --pid is omitted, watches the newest dailybench_tasks.py process.
set -u

PID=""
LABEL="dailybench"
EVERY=300
LOG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --pid) PID="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --every) EVERY="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

notify() {
  osascript -e "display notification \"$2\" with title \"$1\" sound name \"Glass\"" >/dev/null 2>&1
}

if [ -z "$PID" ]; then
  PID=$(pgrep -f "dailybench_tasks.py" | head -1)
fi

if [ -z "$PID" ]; then
  echo "No dailybench_tasks.py process found."
  notify "Batch watcher" "No running batch found for '$LABEL'"
  exit 1
fi

echo "Watching PID $PID (label=$LABEL, heartbeat every ${EVERY}s). Ctrl-C to stop."
notify "Batch watcher" "Now watching '$LABEL' (PID $PID)"

START_TS=$(date +%s)
while kill -0 "$PID" 2>/dev/null; do
  sleep "$EVERY"
  if ! kill -0 "$PID" 2>/dev/null; then
    break
  fi
  NOW=$(date +%s)
  MIN=$(( (NOW - START_TS) / 60 ))
  # heartbeat: current task + step from the log tail
  CUR=""
  if [ -n "$LOG" ] && [ -f "$LOG" ]; then
    CUR=$(grep -E "Running MobileAgent|Step [0-9]+/150" "$LOG" | tail -1 | sed 's/^/  /')
  fi
  notify "Batch watcher" "'$LABEL' still running (${MIN} min).$CUR"
done

notify "Batch watcher" "✓ '$LABEL' (PID $PID) has FINISHED."
echo "Done watching PID $PID."
