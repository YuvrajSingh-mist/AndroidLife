#!/usr/bin/env bash
# Re-run one public task for every model row on the leaderboard.
#
# A redo row in redo.md is usually a *benchmark-level* defect, so its recorded
# score is not a model signal and every model has to be re-taken on the fixed
# seed. This drives that: one `androidlife-tasks` invocation per leaderboard row,
# each into its own timestamped run root with a LAUNCH.txt + batch.log, exactly
# like the ad-hoc re-runs.
#
# Usage:
#   bash scripts/run/rerun_task_rows.sh <task_id> <tag> [row ...]
#
#   bash scripts/run/rerun_task_rows.sh hard__drive-notes-telegram__010 rerun-010
#   bash scripts/run/rerun_task_rows.sh easy__google-slides__001 rerun-slides 1 5
#   ROWS_FILTER=text bash scripts/run/rerun_task_rows.sh <task> <tag>   # skip vision rows
#   LEAK_CLEANUP=0 bash scripts/run/rerun_task_rows.sh <task> <tag>      # no between-row repair
#   STEPS=40 LOCAL_AUTOSERVE=1 bash scripts/run/rerun_task_rows.sh <task> <tag>
#
# Between rows the script repairs the Telegram/Notes content leaks (LEAK_CLEANUP=1,
# default). Necessary for any task that messages: a row can leave a draft or a sent
# bubble, and the runner's verify-only seed gate then correctly ABORTS every remaining
# row. See --leak-cleanup-only in reset_phone.py.
#
# Rows (from LEADERBOARD_ROWS in androidlife-website/assets/js/leaderboard.js):
#    1 qwen3.8-27b TEXT        2 kimi-k2.6 TEXT        3 gemini-3.1-flash-lite
#    4 seed-2.0-lite TEXT      5 qwen3.8-27b VISION    6 seed-2.0-lite VISION
#    7 gpt-5.6-luna TEXT       8 gpt-5.6-luna VISION   9 Qwen3.5-4B TEXT        (local)
#   10 gemma-4-E2B-it TEXT    11 kimi-k2.6 VISION     12 gemma-4-E2B-it VISION  (local)
#   13 Bonsai-2-27B TEXT                                                       (local)
#
# Local rows (9, 10, 12, 13) need a llama-server on $LOCAL_UPSTREAM (default
# 127.0.0.1:8088) already serving that row's pack; they are skipped with a loud
# message unless the server answers, because a half-started batch wastes hours.
#
# Prereqs, checked up front: adb device reachable, .env present, and the seed gate
# passing *today* (date-relative calendar anchors make a stale --apply useless).
set -uo pipefail

TASK_ID="${1:-}"
# The run directory is the task_id in slug form: hard__bookmyshow__005 -> hard-bookmyshow-005.
# (SLUG is the *model* slug, so it cannot be used for this.)
TASK_DIR_SLUG="${TASK_ID//__/-}"
TAG="${2:-}"
shift 2 2>/dev/null || true
WANT_ROWS=("$@")

if [[ -z "$TASK_ID" || -z "$TAG" ]]; then
  echo "usage: $0 <task_id> <tag> [row ...]" >&2
  exit 2
fi

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
REPO="$PWD"
PUBLIC_ROOT="$REPO/assets/runs/public"
SERIAL="${ANDROIDLIFE_SERIAL:-100.108.15.119:5555}"
LOCAL_UPSTREAM="${LOCAL_UPSTREAM:-http://127.0.0.1:8088}"
OPENROUTER="https://openrouter.ai/api"
PHOENIX_URL="${PHOENIX_URL:-http://localhost:6006}"
DATASET="benchmarks/androidlife-530/AndroidLife_public_v2.json"
STEPS="${STEPS:-60}"
ROWS_FILTER="${ROWS_FILTER:-all}"
LOGDIR="$REPO/assets/runs/logs"
mkdir -p "$LOGDIR"

# row | model slug | mode | upstream (empty = local) | serve_gguf.sh preset (local only)
ROW_TABLE=(
  "1|qwen/qwen3.8-27b|text|$OPENROUTER|"
  "2|moonshotai/kimi-k2.6|text|$OPENROUTER|"
  "3|google/gemini-3.1-flash-lite|text|$OPENROUTER|"
  "4|bytedance-seed/seed-2.0-lite|text|$OPENROUTER|"
  "5|qwen/qwen3.8-27b|vision|$OPENROUTER|"
  "6|bytedance-seed/seed-2.0-lite|vision|$OPENROUTER|"
  "7|openai/gpt-5.6-luna|text|$OPENROUTER|"
  "8|openai/gpt-5.6-luna|vision|$OPENROUTER|"
  "9|Qwen3.5-4B|text||qwen3.5-4b"
  "10|gemma-4-E2B-it|text||gemma4-e2b"
  "11|moonshotai/kimi-k2.6|vision|$OPENROUTER|"
  "12|gemma-4-E2B-it|vision||gemma4-e2b"
  "13|Bonsai-2-27B|text||bonsai2-27b"
)

# LOCAL_AUTOSERVE=1 starts the row's llama-server, waits for it, runs the row, then
# stops it — one server at a time, since they all want $LOCAL_UPSTREAM's port.
LOCAL_AUTOSERVE="${LOCAL_AUTOSERVE:-0}"
# Between-row Telegram/Notes content-leak repair. On by default: any task that messages
# can leave a draft or a sent bubble, and the runner's verify-only gate then aborts every
# remaining row. Set LEAK_CLEANUP=0 to disable (e.g. for a task that cannot leak).
LEAK_CLEANUP="${LEAK_CLEANUP:-1}"
SEED_GATE_PROFILE="${SEED_GATE_PROFILE:-public_v2}"
SERVED_PID=""

stop_server() {
  [[ -n "$SERVED_PID" ]] || return 0
  kill "$SERVED_PID" 2>/dev/null
  for _ in $(seq 1 30); do kill -0 "$SERVED_PID" 2>/dev/null || break; sleep 1; done
  kill -9 "$SERVED_PID" 2>/dev/null
  SERVED_PID=""
}

start_server() {
  local preset="$1" log="$2"
  echo "   starting llama-server ($preset) ..."
  bash scripts/llm/serve_gguf.sh "$preset" >"$log" 2>&1 &
  SERVED_PID=$!
  local i
  for i in $(seq 1 180); do
    if curl -sf -m 3 "$LOCAL_UPSTREAM/v1/models" >/dev/null 2>&1; then
      echo "   server up after ${i}s (pid $SERVED_PID)"
      return 0
    fi
    kill -0 "$SERVED_PID" 2>/dev/null || { echo "   server died - see $log"; return 1; }
    sleep 2
  done
  echo "   server did not become ready in 360s - see $log"
  stop_server
  return 1
}

# Never orphan a llama-server if the batch is interrupted.
trap 'stop_server' EXIT INT TERM

wanted() {
  local r="$1"
  [[ ${#WANT_ROWS[@]} -eq 0 ]] && return 0
  local w; for w in "${WANT_ROWS[@]}"; do [[ "$w" == "$r" ]] && return 0; done
  return 1
}

# ---- preflight ------------------------------------------------------------
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "FAIL: OPENROUTER_API_KEY not set (put it in .env)" >&2; exit 1
fi
if ! adb -s "$SERIAL" get-state >/dev/null 2>&1; then
  echo "FAIL: adb device $SERIAL not reachable (adb connect $SERIAL)" >&2; exit 1
fi
# Without the collector the runner ABORTS every task (it refuses to silently drop
# trace data), so a batch would burn through all rows failing identically.
if ! curl -sf -m 5 -o /dev/null "$PHOENIX_URL" 2>/dev/null; then
  echo "FAIL: Phoenix collector not reachable at $PHOENIX_URL" >&2
  echo "      start it:  uv run python scripts/run/start_phoenix.py --public --no-open" >&2
  exit 1
fi
if [[ "$LOCAL_AUTOSERVE" == "1" ]] && ! command -v llama-server >/dev/null 2>&1 \
   && ! ls "$HOME"/local/llama-*/**/llama-server >/dev/null 2>&1; then
  echo "WARN: no llama-server found; local rows 9/10/12/13 will be skipped" >&2
fi
echo "== phoenix collector: $PHOENIX_URL reachable =="
# The runner guards a *missing* placeholder (SystemExit) but not a *wrong* one, so a
# drifted machine-local config/user.yaml resolves silently and invalidates the whole
# batch. That is not hypothetical: `cinema: INOX Bhubaneswar` (not a real BookMyShow
# listing) survived the "fixed in all five places" commit precisely because
# config/user.yaml is gitignored, so it overrides the corrected shipped default in
# user_config.py. Render the values the agent will actually be given, and refuse to
# burn a batch on a known-bad one.
echo "== resolved task vars (what the agent will be told) =="
if ! uv run python scripts/tools/verify_task_vars.py --dataset "$DATASET" --task-id "$TASK_ID"; then
  echo "FAIL: resolved task vars look wrong - fix config/user.yaml (or pass --config) first" >&2
  exit 1
fi
echo "== seed gate (must pass TODAY; anchors are date-relative) =="
# Deliberately NO --no-account-check / --no-meet-check: the runner runs the full
# gate internally and aborts the task on failure, so a weaker preflight here just
# means we discover a bad seed AFTER burning a row. Run the same check the runner
# will run (see run_seed_gate in androidlife/n.py).
if ! uv run python scripts/seeding/reset_phone.py --serial "$SERIAL" --profile "$SEED_GATE_PROFILE" \
      --verify-only 2>&1 | tail -3 | tee /dev/stderr | grep -q "RESULT PASS"; then
  echo "FAIL: seed gate did not pass - run reset_phone.py --apply first" >&2; exit 1
fi
echo

# ---- run each row ---------------------------------------------------------
FAILED=()
for SPEC in "${ROW_TABLE[@]}"; do
  IFS='|' read -r ROW SLUG MODE UP PRESET <<<"$SPEC"
  wanted "$ROW" || continue
  if [[ "$ROWS_FILTER" != "all" && "$MODE" != "$ROWS_FILTER" ]]; then
    echo "-- row $ROW ($SLUG $MODE): skipped (ROWS_FILTER=$ROWS_FILTER)"; continue
  fi
  if [[ -z "$UP" ]]; then
    if ! curl -sf -m 5 "$LOCAL_UPSTREAM/v1/models" >/dev/null 2>&1; then
      if [[ "$LOCAL_AUTOSERVE" == "1" && -n "$PRESET" ]]; then
        SRVLOG="$LOGDIR/llama-server-row$ROW.log"
        if ! start_server "$PRESET" "$SRVLOG"; then
          echo "-- row $ROW ($SLUG $MODE): SKIPPED - could not start $PRESET"
          FAILED+=("$ROW(local-serve-failed)"); continue
        fi
      else
        echo "-- row $ROW ($SLUG $MODE): SKIPPED - no llama-server on $LOCAL_UPSTREAM"
        echo "   start it (scripts/llm/serve_gguf.sh $PRESET) or set LOCAL_AUTOSERVE=1,"
        echo "   then re-run: $0 $TASK_ID $TAG $ROW"
        FAILED+=("$ROW(local-no-server)"); continue
      fi
    fi
    UP="$LOCAL_UPSTREAM"
  fi

  TS="$(date +%Y%m%d-%H%M%S)"
  ROOT="$PUBLIC_ROOT/$TS"
  MODETAG="$MODE"
  mkdir -p "$ROOT"
  cat > "$ROOT/LAUNCH.txt" <<EOF
run_ts=$TS
tag=$TAG
redo_task=$TASK_ID
row=$ROW
model=$SLUG
mode=$MODE
llm_upstream_base=$UP
serial=$SERIAL
run_root=$ROOT
batch_log=$ROOT/batch.log
EOF

  echo "== row $ROW/13  $SLUG ($MODE) -> $ROOT"
  ARGS=(--dataset "$DATASET" --source public.md --task-id "$TASK_ID"
        --run-root "$ROOT" --serial "$SERIAL" --model "$SLUG"
        --llm-upstream-base "$UP" --steps "$STEPS"
        --temperature 0.0 --save-trajectory action
        --ask-user-model gpt-5.4-mini
        --phoenix-url http://localhost:6006 --phoenix-project androidlife-public
        --seed-gate enforce)
  [[ "$MODE" == "vision" ]] && ARGS+=(--vision)

  if uv run androidlife-tasks "${ARGS[@]}" >"$ROOT/batch.log" 2>&1; then
    echo "   done: $(grep -c 'Step ' "$ROOT/batch.log" 2>/dev/null || echo 0) step lines"
  else
    echo "   FAILED - see $ROOT/batch.log"
    FAILED+=("$ROW($SLUG)")
  fi

  # Free the port before the next local row wants it.
  [[ -n "$SERVED_PID" ]] && stop_server

  # Delivery evidence, read BEFORE the cleanup below deletes the bubble it looks for.
  # A task whose deliverable is a message cannot be graded on the model's own `success`:
  # three rows of the 2026-09-22 hard__bookmyshow__005 re-run reported success having sent
  # nothing (draft left in the composer / Telegram never launched / message typed into the
  # search box). Writing the device-side fact here lets scripts/eval/androidlife_report.py
  # demote those. The grader only demotes on definite evidence, so a probe that cannot
  # reach the chat is recorded honestly rather than guessed at.
  if [[ -n "$TASK_DIR_SLUG" ]] && ls "$ROOT"/day*/"$TASK_DIR_SLUG"/output.json >/dev/null 2>&1; then
    TASK_DIR="$(ls -d "$ROOT"/day*/"$TASK_DIR_SLUG")"
    if PROBE="$(uv run python scripts/seeding/reset_phone.py --serial "$SERIAL" \
          --profile "$SEED_GATE_PROFILE" --delivery-probe 2>/dev/null | grep '^DELIVERY ' | head -1)"; then
      if [[ -n "$PROBE" ]]; then
        printf '%s\n' "${PROBE#DELIVERY }" >"$TASK_DIR/delivery.json"
        echo "   delivery: $(grep -o '"sent_bubbles": [0-9]*' "$TASK_DIR/delivery.json" | head -1)"
      else
        echo "   delivery: probe produced no verdict (left unrecorded - grader will not demote)"
      fi
    else
      echo "   delivery: probe failed (left unrecorded - grader will not demote)"
    fi
  fi

  # Between-row content-leak repair, BEFORE the next row's gate looks at the device.
  # Force-stop resets an app's screen, never its content, and this task messages on
  # Telegram -- so nearly every row leaves either a sent bubble or (when the harness
  # Send tap misses) a live draft. The runner's gate is verify-only and correctly
  # ABORTS on that, which without this step costs every remaining row: the first
  # 2026-09-22 attempt lost rows 3-13 because row 2 left its movie-night plan in the
  # Yuvraj Airtel composer. Cheap (~60-90s) next to a row.
  if [[ "$LEAK_CLEANUP" == "1" ]]; then
    if uv run python scripts/seeding/reset_phone.py --serial "$SERIAL" --profile "$SEED_GATE_PROFILE" \
         --leak-cleanup-only 2>&1 | tee "$LOGDIR/leak-cleanup-row$ROW.log" | grep -q "RESULT PASS"; then
      echo "   leak cleanup: PASS"
    else
      echo "   leak cleanup: FAIL - next row will abort on the seed gate (see $LOGDIR/leak-cleanup-row$ROW.log)"
      FAILED+=("$ROW(leak-cleanup)")
    fi
  fi

  # Per-task post-row drift check. Only the app-private OnePlus-Notes seed needs one:
  # a run can rewrite the note it is graded against, and the rewrite would contaminate
  # the next row. Other tasks have nothing app-private that a run can silently mutate.
  if [[ "$TASK_ID" == "hard__drive-notes-telegram__010" ]] \
     && ! adb -s "$SERIAL" shell "cat '/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md'" 2>/dev/null \
       | grep -q "Last reviewed: 2026-07-10."; then
    echo "   WARN: Obsidian 'Budget Deadline.md' lost its 'Last reviewed:' line - restore it"
    FAILED+=("$ROW(seed-drift)")
  fi
done

echo
if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo "BATCH COMPLETE - all requested rows ran"
else
  echo "BATCH FINISHED WITH PROBLEMS: ${FAILED[*]}"
fi
