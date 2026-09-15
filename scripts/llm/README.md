# Local llama.cpp (Apple Silicon)

Phone stays the DUT. LLM runs on the Mac (Mini M4 16GB) via `llama-server`.

## Fire up any GGUF (model-agnostic)

```bash
export PATH="$HOME/local/bin:/opt/homebrew/bin:$PATH"

# presets under ~/models/androidlife-gguf/
bash scripts/llm/serve_gguf.sh qwen3.5-4b
bash scripts/llm/serve_gguf.sh gemma4-e2b          # auto --mmproj
bash scripts/llm/serve_gguf.sh mai-ui-2b
bash scripts/llm/serve_gguf.sh gui-owl-1.5-2b

# or any weights path / directory
bash scripts/llm/serve_gguf.sh ~/models/foo/bar-Q4_K_M.gguf --alias MyModel
bash scripts/llm/serve_gguf.sh ~/models/androidlife-gguf/qwen3.5-4b

# detached
nohup bash scripts/llm/serve_gguf.sh qwen3.5-4b > /tmp/llama.log 2>&1 &
curl -sS http://127.0.0.1:8088/v1/models
```

`scripts/llm/serve_qwen35_4b.sh` is a thin alias for `serve_gguf.sh qwen3.5-4b`.

### Shared Metal / M4 flags (all presets)

```text
-ngl 99  -fa on  -c 65536  -b 2048  -ub 512
-ctk q8_0  -ctv q8_0  --jinja  -np 1
--host 127.0.0.1  --port 8088
```

| Extra | When |
|-------|------|
| `-a <alias>` | Always — MobileRun `--model` must match |
| `--reasoning off` | Qwen3.5 preset (thinking off for tool use) |
| `--mmproj …` | Auto for Gemma / MAI / Owl (vision) |

### CLI / env overrides

```bash
bash scripts/llm/serve_gguf.sh qwen3.5-4b --port 8090 --ctx 32768 --alias Qwen3.5-4B
LLAMA_PORT=8090 LLAMA_CTX=32768 LLAMA_ALIAS=… LLAMA_MMPROJ=… LLAMA_EXTRA_ARGS="…" \
  bash scripts/llm/serve_gguf.sh gemma4-e2b
```

| Env | Default |
|-----|---------|
| `ANDROIDLIFE_GGUF_ROOT` | `~/models/androidlife-gguf` |
| `LLAMA_SERVER_BIN` | `llama-server` on PATH |
| `LLAMA_HOST` / `LLAMA_PORT` | `127.0.0.1` / `8088` |
| `LLAMA_CTX` | `65536` |
| `LLAMA_ALIAS` | preset default or filename stem |
| `LLAMA_MMPROJ` | auto-detect beside weights |
| `LLAMA_EXTRA_ARGS` | appended raw args |

Download the four stock GGUFs: `bash scripts/llm/download_ggufs.sh`  
Longer model notes: `~/models/androidlife-gguf/README.md`

## Point AndroidLife / MobileRun at it

**No `/v1` on upstream** (the proxy appends `/v1/...`). Context capping was removed.

```bash
# alias must match serve_gguf.sh -a / --alias (printed at startup)
uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-530/AndroidLife_public_v2.json \
  --source public.md --all \
  --serial 100.108.15.119:5555 \
  --llm-upstream-base http://127.0.0.1:8088 \
  --model Qwen3.5-4B \
  --ask-user-model gpt-5.4-mini \
  --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action --no-tracing \
  --vars-file benchmarks/androidlife-530/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-530/multiturn_kb_public.json \
  --run-root "assets/runs/public/$(date +%Y%m%d-%H%M%S)"
# add --vision when serving a mmproj model (gemma / mai / owl)
```

### Preset → `--model` alias

| Preset | Default `--model` | Vision |
|--------|-------------------|--------|
| `qwen3.5-4b` | `Qwen3.5-4B` | no |
| `gemma4-e2b` | `gemma-4-E2B-it` | yes (`--vision`) |
| `mai-ui-2b` | `MAI-UI-2B` | yes |
| `gui-owl-1.5-2b` | `GUI-Owl-1.5-2B` | yes |
