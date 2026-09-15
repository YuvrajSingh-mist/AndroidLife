#!/usr/bin/env bash
# Model-agnostic llama-server launcher for AndroidLife GGUFs (Apple Silicon / Metal).
#
# Usage:
#   scripts/llm/serve_gguf.sh qwen3.5-4b
#   scripts/llm/serve_gguf.sh gemma4-e2b
#   scripts/llm/serve_gguf.sh mai-ui-2b
#   scripts/llm/serve_gguf.sh gui-owl-1.5-2b
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
#   LLAMA_EXTRA_ARGS       extra raw args appended to llama-server
set -euo pipefail

ROOT="${ANDROIDLIFE_GGUF_ROOT:-$HOME/models/androidlife-gguf}"
PORT="${LLAMA_PORT:-8088}"
CTX="${LLAMA_CTX:-65536}"
BIN="${LLAMA_SERVER_BIN:-$(command -v llama-server || true)}"
HOST="${LLAMA_HOST:-127.0.0.1}"

usage() {
  cat <<'EOF' >&2
Usage: serve_gguf.sh <preset|path-to.gguf> [--alias NAME] [--mmproj PATH] [--port N] [--ctx N]

Presets (under $ANDROIDLIFE_GGUF_ROOT):
  qwen3.5-4b       Qwen3.5-4B-Q4_K_M.gguf          alias Qwen3.5-4B
  gemma4-e2b       gemma-4-E2B-it-Q4_K_M.gguf      + mmproj-BF16.gguf
  mai-ui-2b        MAI-UI-2B.Q4_K_M.gguf           + mmproj-f16
  gui-owl-1.5-2b   GUI-Owl-1.5-2B-Instruct.Q4_K_M  + mmproj-f16

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
  mai-ui-2b|mai|mai-ui)
    MODEL="$ROOT/mai-ui-2b/MAI-UI-2B.Q4_K_M.gguf"
    ALIAS="${ALIAS:-MAI-UI-2B}"
    # Prefer f16 mmproj if present.
    if [[ -z "$MMPROJ" ]]; then
      for c in "$ROOT/mai-ui-2b"/MAI-UI-2B.mmproj-f16.gguf \
               "$ROOT/mai-ui-2b"/*mmproj*f16*.gguf \
               "$ROOT/mai-ui-2b"/mmproj*.gguf; do
        [[ -f "$c" ]] && MMPROJ="$c" && break
      done
    fi
    ;;
  gui-owl-1.5-2b|gui-owl|owl)
    MODEL="$ROOT/gui-owl-1.5-2b/GUI-Owl-1.5-2B-Instruct.Q4_K_M.gguf"
    ALIAS="${ALIAS:-GUI-Owl-1.5-2B}"
    if [[ -z "$MMPROJ" ]]; then
      for c in "$ROOT/gui-owl-1.5-2b"/GUI-Owl-1.5-2B-Instruct.mmproj-f16.gguf \
               "$ROOT/gui-owl-1.5-2b"/*mmproj*f16*.gguf \
               "$ROOT/gui-owl-1.5-2b"/mmproj*.gguf; do
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
[[ -n "$MMPROJ" ]] && echo "  mmproj: $MMPROJ"
[[ "$REASONING_OFF" -eq 1 ]] && echo "  reasoning: off"
echo "  tip:    --llm-upstream-base http://${HOST}:${PORT}   # no /v1"

exec "${cmd[@]}"
