#!/usr/bin/env bash
# Back-compat wrapper → model-agnostic serve_gguf.sh (Qwen3.5-4B preset).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$DIR/serve_gguf.sh" qwen3.5-4b "$@"
