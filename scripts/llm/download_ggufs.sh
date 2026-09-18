#!/usr/bin/env bash
# Download the AndroidLife SLM GGUFs for llama.cpp (Apple Silicon).
set -euo pipefail
ROOT="${ANDROIDLIFE_GGUF_ROOT:-$HOME/models/androidlife-gguf}"
export PATH="${PATH}:$(cd "$(dirname "$0")/../.." && pwd)/.venv/bin"
mkdir -p "$ROOT"
export HF_XET_HIGH_PERFORMANCE=1

echo "Root: $ROOT"

echo "==> Qwen3.5-4B Q4_K_M"
hf download unsloth/Qwen3.5-4B-GGUF \
  --include "Qwen3.5-4B-Q4_K_M.gguf" \
  --local-dir "$ROOT/qwen3.5-4b"

echo "==> Gemma 4 E2B-it Q4_K_M + mmproj-BF16"
hf download unsloth/gemma-4-E2B-it-GGUF \
  --include "gemma-4-E2B-it-Q4_K_M.gguf" \
  --include "mmproj-BF16.gguf" \
  --local-dir "$ROOT/gemma4-e2b"

echo "==> MAI-UI-2B Q4_K_M + mmproj-f16"
hf download mradermacher/MAI-UI-2B-GGUF \
  --include "*Q4_K_M*" \
  --include "*mmproj*f16*" \
  --local-dir "$ROOT/mai-ui-2b"

echo "==> GUI-Owl-1.5-2B-Instruct Q4_K_M + mmproj-f16"
hf download mradermacher/GUI-Owl-1.5-2B-Instruct-GGUF \
  --include "*Q4_K_M*" \
  --include "*mmproj*f16*" \
  --local-dir "$ROOT/gui-owl-1.5-2b"

echo "==> Ternary-Bonsai-2-27B PTQ1_0 + mmproj-Q8_0"
hf download prism-ml/Ternary-Bonsai-2-27B-gguf \
  --include "Ternary-Bonsai-2-27B-PTQ1_0.gguf" \
  --include "Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf" \
  --local-dir "$ROOT/bonsai2-27b"

echo "Done. Tree:"
find "$ROOT" -name '*.gguf' -exec ls -lh {} \;
