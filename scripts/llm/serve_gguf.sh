#!/usr/bin/env bash
# Model-agnostic llama-server launcher for AndroidLife GGUFs (Apple Silicon / Metal).
#
# Usage:
#   scripts/llm/serve_gguf.sh qwen3.5-4b
#   scripts/llm/serve_gguf.sh gemma4-e2b
#   scripts/llm/serve_gguf.sh bonsai2-27b
#   scripts/llm/serve_gguf.sh lfm2.5-2.6b
#   scripts/llm/serve_gguf.sh lfm2.5-vl-3b
#   scripts/llm/serve_gguf.sh /path/to/model.gguf [--alias NAME] [--mmproj PATH]
#   LLAMA_PORT=8090 LLAMA_CTX=32768 scripts/llm/serve_gguf.sh qwen3.5-4b
#
# Env:
#   ANDROIDLIFE_GGUF_ROOT  default ~/models/androidlife-gguf
#   LLAMA_SERVER_BIN       default: llama-server on PATH
#   LLAMA_PORT             default 8088
#   LLAMA_CTX              default 65536
#   LLAMA_ALIAS            override -a alias (MobileRun --model must match)
#   LLAMA_MMPROJ           force mmproj path (or auto-detect beside weights)
#   LLAMA_N_PREDICT        max generated tokens per response (default 2048; 0/-1 = uncapped)
#   LLAMA_EXTRA_ARGS       extra raw args appended to llama-server
set -euo pipefail

ROOT="${ANDROIDLIFE_GGUF_ROOT:-$HOME/models/androidlife-gguf}"
PORT="${LLAMA_PORT:-8088}"
CTX="${LLAMA_CTX:-65536}"
N_PREDICT="${LLAMA_N_PREDICT:-2048}"
BIN="${LLAMA_SERVER_BIN:-$(command -v llama-server || true)}"
HOST="${LLAMA_HOST:-127.0.0.1}"

# PrismML's fork of llama.cpp, needed ONLY for Ternary Bonsai 2 (PTQ1_0/PQ2_0).
# Those are PrismML's own ternary packings; stock upstream refuses them with
# "tensor 'output.weight' has invalid ggml type 143". Side-by-side install so the
# Gemma/Qwen/LFM presets keep using the stock binary untouched.
prism_bin() {
  local c
  for c in "${LLAMA_PRISM_SERVER_BIN:-}" \
           "$HOME"/local/llama-prism-*/*/llama-server; do
    [[ -n "$c" && -x "$c" ]] && { printf '%s\n' "$c"; return 0; }
  done
  return 1
}

usage() {
  cat <<'EOF' >&2
Usage: serve_gguf.sh <preset|path-to.gguf> [--alias NAME] [--mmproj PATH] [--port N] [--ctx N] [--n-predict N]

Presets (under $ANDROIDLIFE_GGUF_ROOT):
  qwen3.5-4b       Qwen3.5-4B-Q4_K_M.gguf          alias Qwen3.5-4B
  gemma4-e2b       gemma-4-E2B-it-Q4_K_M.gguf      + mmproj-BF16.gguf
  bonsai2-27b      Ternary-Bonsai-2-27B-PTQ1_0.gguf + mmproj-Q8_0 (general, ternary, vision)
  lfm2.5-2.6b      LFM2.5-2.6B-Q4_K_M.gguf         (general, text)
  lfm2.5-vl-3b     LFM2.5-VL-3B-Q4_K_M.gguf        + mmproj-Q8_0 (general, vision)

Examples:
  bash scripts/llm/serve_gguf.sh qwen3.5-4b
  bash scripts/llm/serve_gguf.sh gemma4-e2b
  bash scripts/llm/serve_gguf.sh ~/models/foo.gguf --alias MyModel
EOF
  exit 2
}

if [[ $# -lt 1 ]]; then
  usage
fi

SPEC="$1"
shift

ALIAS="${LLAMA_ALIAS:-}"
MMPROJ="${LLAMA_MMPROJ:-}"
REASONING_OFF=0

# Resolve preset → weights (+ default alias / mmproj / reasoning).
case "$SPEC" in
  -h|--help) usage ;;
  qwen3.5-4b|qwen|qwen35|qwen3.5)
    MODEL="$ROOT/qwen3.5-4b/Qwen3.5-4B-Q4_K_M.gguf"
    ALIAS="${ALIAS:-Qwen3.5-4B}"
    REASONING_OFF=1
    ;;
  gemma4-e2b|gemma|gemma4|e2b)
    MODEL="$ROOT/gemma4-e2b/gemma-4-E2B-it-Q4_K_M.gguf"
    ALIAS="${ALIAS:-gemma-4-E2B-it}"
    MMPROJ="${MMPROJ:-$ROOT/gemma4-e2b/mmproj-BF16.gguf}"
    ;;
  bonsai2-27b|bonsai2|bonsai|bonsai-2-27b|ternary-bonsai-2|bonsai-2)
    MODEL="$ROOT/bonsai2-27b/Ternary-Bonsai-2-27B-PTQ1_0.gguf"
    ALIAS="${ALIAS:-Bonsai-2-27B}"
    # Ternary Bonsai 2 only loads on the PrismML fork, not upstream llama.cpp.
    # An explicit LLAMA_SERVER_BIN still wins (needed for dry-runs/tests).
    if [[ -z "${LLAMA_SERVER_BIN:-}" ]]; then
      if ! BIN="$(prism_bin)"; then
        cat >&2 <<'EOF'
bonsai2-27b needs PrismML's llama.cpp fork — stock upstream refuses PTQ1_0
("invalid ggml type 143"). Install it side-by-side:

  curl -sSL -o /tmp/llama-prism.tar.gz \
    https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b10685-7dffb15/llama-prism-b10685-7dffb15-bin-macos-arm64.tar.gz
  mkdir -p ~/local/llama-prism-b10685 && tar -xzf /tmp/llama-prism.tar.gz -C ~/local/llama-prism-b10685

...or point LLAMA_PRISM_SERVER_BIN at an existing prism llama-server.
EOF
        exit 1
      fi
    fi
    # Bonsai 2 27B is a ternary multimodal model (Qwen3.8-27B base). The
    # mmproj pack is optional and only loaded for image input.
    if [[ -z "$MMPROJ" ]]; then
      for c in "$ROOT/bonsai2-27b"/Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf \
               "$ROOT/bonsai2-27b"/*mmproj*.gguf; do
        [[ -f "$c" ]] && MMPROJ="$c" && break
      done
    fi
    # Bonsai 2 reasons by default at 'xhigh' effort. The chat template honours
    # enable_thinking=false, which --reasoning off drives, so this genuinely
    # disables thinking (verified: reasoning_content comes back empty).
    # Note: 'low' effort is unsupported upstream and behaves like 'xhigh';
    # only 'medium' and 'xhigh' are real. Override with --no-reasoning-off.
    REASONING_OFF=1
    ;;
  lfm2.5-2.6b|lfm2.6b|lfm-text|lfm2.5-text|lfm26)
    MODEL="$ROOT/lfm2.5-2.6b/LFM2.5-2.6B-Q4_K_M.gguf"
    ALIAS="${ALIAS:-LFM2.5-2.6B}"
    ;;
  lfm2.5-vl-3b|lfm|lfm2|lfm2.5|lfm-vl|lfm2-vl|lfm3b)
    MODEL="$ROOT/lfm2.5-vl-3b/LFM2.5-VL-3B-Q4_K_M.gguf"
    ALIAS="${ALIAS:-LFM2.5-VL-3B}"
    if [[ -z "$MMPROJ" ]]; then
      for c in "$ROOT/lfm2.5-vl-3b"/mmproj-LFM2.5-VL-3B-Q8_0.gguf \
               "$ROOT/lfm2.5-vl-3b"/*mmproj*.gguf; do
        [[ -f "$c" ]] && MMPROJ="$c" && break
      done
    fi
    ;;
  *.gguf)
    MODEL="$SPEC"
    ;;
  *)
    # Treat as directory under ROOT or absolute/relative path to a .gguf / dir.
    if [[ -f "$SPEC" ]]; then
      MODEL="$SPEC"
    elif [[ -f "$ROOT/$SPEC" ]]; then
      MODEL="$ROOT/$SPEC"
    elif [[ -d "$SPEC" ]] || [[ -d "$ROOT/$SPEC" ]]; then
      DIR="$SPEC"
      [[ -d "$ROOT/$SPEC" ]] && DIR="$ROOT/$SPEC"
      # Prefer *Q4_K_M*.gguf, else first non-mmproj gguf.
      MODEL=""
      for c in "$DIR"/*Q4_K_M*.gguf "$DIR"/*.gguf; do
        [[ -f "$c" ]] || continue
        base="$(basename "$c")"
        [[ "$base" == *mmproj* ]] && continue
        MODEL="$c"
        break
      done
      if [[ -z "$MODEL" ]]; then
        echo "No weights GGUF in $DIR" >&2
        exit 1
      fi
      if [[ -z "$MMPROJ" ]]; then
        for c in "$DIR"/*mmproj*.gguf "$DIR"/mmproj*.gguf; do
          [[ -f "$c" ]] && MMPROJ="$c" && break
        done
      fi
    else
      echo "Unknown preset or path: $SPEC" >&2
      usage
    fi
    ;;
esac

# Optional CLI overrides after the preset/path.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --alias) ALIAS="$2"; shift 2 ;;
    --mmproj) MMPROJ="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --ctx) CTX="$2"; shift 2 ;;
    --n-predict) N_PREDICT="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --reasoning-off) REASONING_OFF=1; shift ;;
    --no-reasoning-off) REASONING_OFF=0; shift ;;
    -h|--help) usage ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      ;;
  esac
done

if [[ ! -f "$MODEL" ]]; then
  echo "Missing weights: $MODEL — run scripts/llm/download_ggufs.sh or pass a .gguf path" >&2
  exit 1
fi
if [[ -z "$BIN" ]]; then
  echo "llama-server not on PATH (set LLAMA_SERVER_BIN)" >&2
  exit 1
fi

# Default alias from filename stem if still unset.
if [[ -z "$ALIAS" ]]; then
  base="$(basename "$MODEL")"
  ALIAS="${base%.gguf}"
  ALIAS="${ALIAS%.Q4_K_M}"
  ALIAS="${ALIAS%-Q4_K_M}"
fi

if [[ -n "$MMPROJ" && ! -f "$MMPROJ" ]]; then
  echo "Missing mmproj: $MMPROJ" >&2
  exit 1
fi

# Auto-pick mmproj next to weights if not set and one exists.
if [[ -z "$MMPROJ" ]]; then
  DIR="$(dirname "$MODEL")"
  for c in "$DIR"/*mmproj*.gguf "$DIR"/mmproj*.gguf; do
    [[ -f "$c" ]] && MMPROJ="$c" && break
  done
fi

cmd=(
  "$BIN"
  -m "$MODEL"
  -a "$ALIAS"
  --host "$HOST"
  --port "$PORT"
  -ngl 99
  -fa on
  -c "$CTX"
  -b 2048
  -ub 512
  -ctk q8_0
  -ctv q8_0
  --jinja
  -np 1
)

# Cap generation PER RESPONSE. Without this, llama-server defaults to -n -1
# (infinity), so a model that fails to emit EOS in a degenerate loop generates
# until the context window fills — ~20 min at ~30 tok/s, far past the LLM
# client's 300s timeout -> APITimeoutError, and with -np 1 it blocks the single
# slot for every later request too. That was the 2026-09-17 runaway.
#
# 2048 is scoped to THIS server. The flag governs only the local GGUF models
# (Qwen3.5-4B, gemma-4-E2B-it); OpenRouter-hosted models are unaffected by it.
# Across every logged local completion, neither has come close: n=1650 with a
# max of 965 tokens (Qwen3.5-4B n=948 max 907; gemma-4-E2B-it n=702 max 965).
# So 2048 has never truncated a local response, and a runaway now ends in
# ~1.5 min instead of ~20.
#
# Corrected 2026-09-18: an earlier note here claimed "5804 completions, max
# 2016", which conflated local and OpenRouter traffic. Over the full public
# corpus (21,493 completions) there are 6 over 2048 — but every one is
# moonshotai/kimi-k2.6 on OpenRouter, four of them 65536-token runaways with
# finish_reason=length. Those are a remote-backend problem this flag cannot
# reach, and they are excluded from the local evidence above. Pass 0 or -1 to
# opt back out.
if [[ "$N_PREDICT" != "0" && "$N_PREDICT" != "-1" ]]; then
  cmd+=(-n "$N_PREDICT")
fi

if [[ "$REASONING_OFF" -eq 1 ]]; then
  cmd+=(--reasoning off)
fi
if [[ -n "$MMPROJ" ]]; then
  cmd+=(--mmproj "$MMPROJ")
fi

# shellcheck disable=SC2206
if [[ -n "${LLAMA_EXTRA_ARGS:-}" ]]; then
  # intentional word-split for extra CLI tokens
  extra=( ${LLAMA_EXTRA_ARGS} )
  cmd+=("${extra[@]}")
fi

echo "Serving $MODEL"
echo "  alias:  $ALIAS   (use --model $ALIAS with MobileRun)"
echo "  listen: http://${HOST}:${PORT}"
echo "  ctx:    $CTX"
if [[ "$N_PREDICT" != "0" && "$N_PREDICT" != "-1" ]]; then
  echo "  n_predict: $N_PREDICT tokens/response (cap; set LLAMA_N_PREDICT=-1 to disable)"
else
  echo "  n_predict: UNCAPPED (-n -1) - a degenerate generation loop will run until the context fills"
fi
[[ -n "$MMPROJ" ]] && echo "  mmproj: $MMPROJ"
[[ "$REASONING_OFF" -eq 1 ]] && echo "  reasoning: off"
echo "  tip:    --llm-upstream-base http://${HOST}:${PORT}   # no /v1"

exec "${cmd[@]}"
