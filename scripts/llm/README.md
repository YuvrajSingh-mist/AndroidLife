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
bash scripts/llm/serve_gguf.sh bonsai2-27b         # ternary (Bonsai 2), vision

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
-n 2048  --host 127.0.0.1  --port 8088
```

| Extra | When |
|-------|------|
| `-a <alias>` | Always — MobileRun `--model` must match |
| `-n 2048` | Always — **generation cap**. See below. |
| `--reasoning off` | Qwen3.5 preset (thinking off for tool use) |
| `--mmproj …` | Auto for Gemma / MAI / Owl (vision) |

### `-n` / `--n-predict` (generation cap) — do not remove

`llama-server` defaults to `-n -1`, i.e. **unlimited tokens per response**. There is no
cap on the harness side either (the proxy only *logs* `max_tokens`; the OpenAI client
sends none). So a model that fails to emit EOS in a degenerate loop — Gemma 4 E2B does
this after a failed action — keeps generating until the context window fills: ~20 min at
~30 tok/s, well past the LLM client's 300s timeout, which surfaces as `APITimeoutError`.
With `-np 1` (single slot) that also blocks every later request behind it, so retries
pile up and time out too.

`-n 2048` is scoped to **this server only** — the flag governs the local GGUF models
(`Qwen3.5-4B`, `gemma-4-E2B-it`). OpenRouter-hosted models are unaffected by it.
Across every logged **local** completion, neither has come close to the cap:

| Local model | completions | p50 | p99 | max |
|---|---|---|---|---|
| `Qwen3.5-4B` | 948 | 81 | 256 | **907** |
| `gemma-4-E2B-it` | 702 | 107 | 507 | **965** |
| combined | 1,650 | — | — | **965** |

So `-n 2048` (≈2.1× the highest local response on record) has never truncated a local
GUI-agent response, while a runaway now ends in ~1.5 min instead of ~20.

> **Corrected 2026-09-18.** An earlier version of this note cited "5,804 logged
> completions … max ever 2,016", which conflated local and OpenRouter traffic. Over the
> **full public corpus** (21,493 completions across 718 proxy logs) there are in fact
> **6 completions over 2048** — but every one is `moonshotai/kimi-k2.6` on OpenRouter,
> four of them 65,536-token runaways with `finish_reason=length` (and only 2 of the 6
> ended normally: 9,874 and 3,219 tokens). Those are a **remote-backend** problem that
> `-n` cannot reach, and they are excluded from the local table above. If you ever serve
> kimi-class models from this script, revisit the cap.

Override with `--n-predict N` or `LLAMA_N_PREDICT=N`; `-1`/`0` opts back out.

> **`--context-shift` is NOT the culprit** (corrected 2026-09-17). On this build
> (`version 1 (8c146a836)`) it already defaults to **disabled**, and `serve_gguf.sh`
> never passed it. Context shift was never enabled — the runaway was purely `n_predict=-1`.
> (Disabling it does mean a runaway self-limits at `-c` rather than looping forever, but
> 32k tokens of generation is still ~20 min, so it is not a substitute for `-n`.)

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
| `bonsai2-27b` | `Bonsai-2-27B` | yes (`--vision`) |

`bonsai2-27b` serves `Ternary-Bonsai-2-27B-PTQ1_0.gguf` (5.54 GiB) + `Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf`
(600 MiB, loaded only on image input) from `prism-ml/Ternary-Bonsai-2-27B-gguf` (Bonsai 2 27B, released
2026-09-17).

### `bonsai2-27b` needs PrismML's llama.cpp fork

`PTQ1_0` / `PQ2_0` are PrismML's own ternary packings. **Stock upstream llama.cpp refuses them:**

```text
E gguf_init_from_reader: tensor 'output.weight' has invalid ggml type 143. should be in [0, 42)
E llama_server: exiting due to model loading error
```

Bonsai **1**'s `Q1_0` *is* merged upstream, so it runs on the stock binary — Bonsai **2** does not. The
preset installs side-by-side and only `bonsai2-27b` uses it, so the other presets are unaffected:

```bash
curl -sSL -o /tmp/llama-prism.tar.gz \
  https://github.com/PrismML-Eng/llama.cpp/releases/download/prism-b10685-7dffb15/llama-prism-b10685-7dffb15-bin-macos-arm64.tar.gz
mkdir -p ~/local/llama-prism-b10685 && tar -xzf /tmp/llama-prism.tar.gz -C ~/local/llama-prism-b10685
```

`serve_gguf.sh` auto-discovers `~/local/llama-prism-*/*/llama-server`; override with
`LLAMA_PRISM_SERVER_BIN`. An explicit `LLAMA_SERVER_BIN` still wins (used for dry-runs).

> Do not "fix" a load failure by switching to a `Q2_0` file on a stock build — PrismML documents that
> those **load silently and output gibberish** rather than erroring.

### Bonsai 2 reasoning is on by default, and genuinely disableable

It thinks at `xhigh` effort by default. The preset passes `--reasoning off`, which the chat template
honours via `enable_thinking=false` — verified: `reasoning_content` comes back empty. Other levers:
`--reasoning-budget 0`, `--chat-template-kwargs '{"enable_thinking":false}'`, or per-request
`thinking_budget_tokens: 0` (`-1` = unlimited). Use `--no-reasoning-off` to keep thinking on.

`reasoning_effort` accepts only `medium` and `xhigh` — PrismML states `low` is unsupported and behaves
close to `xhigh`, so it is not a middle option. Non-thinking sampling is t=0.7 / top_p=0.80 /
presence_penalty=1.5; thinking mode is t=1.0 / top_p=0.95.

Measured on the M4 16 GB: loads in ~4 s, **7.69 GB RSS** at `-c 32768`; text returns clean and vision
correctly read a test image ("A red square with the word 'HELLO' and a blue circle.").
