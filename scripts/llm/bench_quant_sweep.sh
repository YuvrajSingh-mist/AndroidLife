#!/usr/bin/env bash
# llama-bench sweep across context length and generation length, for comparing
# two GGUF packings of the same model on the same box.
#
# Why: the AndroidLife harness is prefill-bound (long agentic prompts, high
# prompt-cache reuse) but also runs real decode, so a single pp512/tg128 number
# is not enough to predict end-to-end cost. This sweeps both axes so the
# prefill/decode crossover and any degradation with context are visible.
#
# Flags mirror the production server exactly (see serve_gguf.sh): -ngl 99,
# -fa on, -ctk/-ctv q8_0, -b 2048, -ub 512. Reps are reduced on the largest
# sizes because prefill at 16k dominates the wall-clock (llama-bench still runs
# a warmup pass in addition to -r).
#
# Usage:
#   bash scripts/llm/bench_quant_sweep.sh            # both packs, default dir
#   MODELS_DIR=~/models/androidlife-gguf/bonsai2-27b bash scripts/llm/bench_quant_sweep.sh
set -uo pipefail

MODELS_DIR="${MODELS_DIR:-$HOME/models/androidlife-gguf/bonsai2-27b}"
BIN="${LLAMA_BENCH_BIN:-$HOME/local/llama-prism-b10685/llama-prism-b10685-7dffb15/llama-bench}"
COMMON=(-ngl 99 -fa on -ctk q8_0 -ctv q8_0 -b 2048 -ub 512)

if [[ ! -x "$BIN" ]]; then
  echo "llama-bench not found at $BIN (set LLAMA_BENCH_BIN)" >&2
  exit 1
fi

run() {
  # $1 = label, $2 = model, rest = llama-bench args
  local label="$1" model="$2"; shift 2
  echo "--- $label"
  "$BIN" -m "$model" "${COMMON[@]}" "$@" 2>/dev/null | grep -E 'pp[0-9]+|tg[0-9]+' || echo "  (no result)"
}

for pack in PTQ1_0 PQ2_0; do
  MODEL="$MODELS_DIR/Ternary-Bonsai-2-27B-$pack.gguf"
  echo
  echo "################################################################"
  echo "### PACK: $pack   ($(basename "$MODEL"))"
  echo "################################################################"
  if [[ ! -f "$MODEL" ]]; then echo "MISSING: $MODEL"; continue; fi

  echo
  echo "===== PREFILL (prompt processing) ====="
  run "pp512      r=3" "$MODEL" -p 512   -n 0 -r 3
  run "pp4096     r=3" "$MODEL" -p 4096  -n 0 -r 3
  run "pp8192     r=2" "$MODEL" -p 8192  -n 0 -r 2
  run "pp16384    r=1" "$MODEL" -p 16384 -n 0 -r 1

  echo
  echo "===== DECODE (token generation, zero prompt depth) ====="
  run "tg128      r=3" "$MODEL" -p 0 -n 128  -r 3
  run "tg512      r=3" "$MODEL" -p 0 -n 512  -r 3
  run "tg1024     r=2" "$MODEL" -p 0 -n 1024 -r 2

  echo
  echo "===== DECODE AT REALISTIC DEPTH (8k-token prompt) ====="
  run "pp8192+tg256 r=1" "$MODEL" -p 8192 -n 256 -r 1
done

echo
echo "SWEEP COMPLETE"
