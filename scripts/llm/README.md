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

`bonsai2-27b` serves `Ternary-Bonsai-2-27B-PQ2_0.gguf` + `Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf`
(600 MiB, loaded only on image input) from `prism-ml/Ternary-Bonsai-2-27B-gguf` (Bonsai 2 27B, released
2026-09-17), falling back to the smaller `PTQ1_0` pack when `PQ2_0` is not on disk.

### Pack choice: prefer `PQ2_0`, not `PTQ1_0`

The repo ships two packings of the same ternary weights. They are a genuine trade, not a ranking:

| Pack | Stored | Size | Wins on |
|---|---|---|---|
| `PTQ1_0` | dense trits, 1.75 bpw | 5.95 GB | decode where memory bandwidth is binding (Ada-class GPUs, L4); tightest footprint |
| `PQ2_0` | 2-bit slots, 2.13 bpw | 7.21 GB | **prompt processing everywhere**; decode on H100 / A100 / Blackwell |

PrismML's own demo selects them in the order `"*-PQ2_0.gguf *-PTQ1_0.gguf"` — `PQ2_0` first, dense
`PTQ1_0` only as fallback (`Bonsai-demo/scripts/common.sh: select_model_gguf`) — and `PQ2_0` is the pack
its README calls "what this demo downloads by default". `serve_gguf.sh` now follows that order, and as
of 2026-09-20 `PQ2_0` is on disk here so the preset serves it by default.

**This harness is prefill-bound, so the default pack matters more here than the vendor's headline
numbers suggest.** Across the 14 finalized tasks of the 2026-09-20 Bonsai run: 411 requests,
2.69 M prompt tokens against 33 k completion tokens, at a 71.9 % prompt-cache hit rate — i.e.
**~755 k tokens of *fresh* prefill**. At the measured `PTQ1_0` 54 tok/s that is **~3.9 h of pure prompt
processing**, versus **~0.33 h** for the same token volume at Qwen3.5-4B's measured 386 tok/s prefill.
Decode is a rounding error next to that. (Counting every request the batch issued, including the two
tasks that never finalized: 452 requests / 3.17 M prompt / 73.5 % cached.)

Measured on this M4 16 GB (macOS, `prism-b10685`, the *same* `llama-bench` binary for all three rows,
`-ngl 99 -fa 1 -p 512 -n 128 -r 3`, run back-to-back with the server stopped and **both Bonsai packs on
the same build in the same session**):

| Model | Pack | prefill pp512 (tok/s) | decode tg128 (tok/s) |
|---|---|---|---|
| `Qwen3.5-4B` | `Q4_K_M` | **385.95 ± 0.09** | 29.06 ± 0.07 |
| `Ternary-Bonsai-2-27B` | `PTQ1_0` (the old default) | **53.99 ± 0.12** | 10.03 ± 0.01 |
| `Ternary-Bonsai-2-27B` | `PQ2_0` (**now the default**) | **63.12 ± 0.01** | 11.00 ± 0.02 |

**`PQ2_0` measured +16.9 % prefill and +9.7 % decode** over `PTQ1_0` here — a real win, but nothing like
the 1.7–2.2× the vendor reports on CUDA, which is the expected outcome: on this box the ternary kernels
are compute-bound on the 10-core GPU, not starved of memory bandwidth the way the Ada-class cards are.
On the 2026-09-20 workload (755 k fresh prefill tokens) that moves pure prompt processing from
**3.9 h to 3.3 h** — ~35 min saved, not a fix.

**No pack makes a 27B ternary model prefill like a 4B `Q4_K_M` on a base M4.** Even with `PQ2_0`, Bonsai
prefills **6.1×** slower than the 4B Q4_K_M. Most of the gap is the model and the 10-core GPU, not the
packing, so treat the packing as a tuning knob and the model/accelerator as the actual constraint. For
reference, the ternary 27B line on Apple Silicon as published:

| | prefill (tok/s) | decode (tok/s) |
|---|---|---|
| `PQ2_0`, this M4, `llama.cpp` Metal (above) | 63.1 | 11.0 |
| quantized 27B on a base **M4**, MLX 2-bit (community) | 65.2 | 12.7 |
| quantized 27B on **M4 Pro**, `llama.cpp` Metal | 116 | 19.0 |
| quantized 27B on **M5 Max**, `llama.cpp` Metal, `PQ2_0` | 816 | 45.8 |

Re-measure with the command above before trusting any of it on your own box.

### Context size is RAM-tiered upstream, and 65536 is not the 16 GB tier

`Bonsai-demo` sizes `-c` to system RAM rather than using llama.cpp's `-c 0` (which means "full 262 144
training context" and will OOM a constrained machine). Its tiers: **≤11 GB → 8192**, **≤23 GB → 16384**,
≤35 GB → 32768, ≤71 GB → 65536. This box is 16 GB, so the upstream default would be **16384**, not the
`65536` this script defaults to — four times the KV footprint the vendor considers safe here (27B hybrid
attention is ~64 KiB/token FP16).

The 2026-09-20 run never needed the headroom: over its 14 finalized tasks the largest prompt was
**11 794 tokens** (p50 6 611), so a 65536 context bought nothing and only added memory pressure. Keep
65536 only if you actually feed contexts that long; otherwise pass `LLAMA_CTX=32768` (headroom over the
observed max) or `--ctx`.

### Speculative decoding: do not enable it on Apple Silicon

`Bonsai-demo` pairs the 27B with a `dspark` drafter (`BONSAI_SPECULATIVE=1`). That path is worth ~1.8–2.4×
on CUDA code/math, but SPECULATIVE.md says outright it "is not recommended on Apple Silicon": on an M5 Max
it measures 1.19× / 1.17× on code/math and **0.91× / 0.83× on reasoning/chat** (1.03× blended), because
Metal acceptance is too low for the draft overhead to pay off. It also disables cross-request prompt-cache
reuse and forces `-np 1` — which is fatal for a 60-step agentic loop that currently reuses 73.5 % of its
prompt. Leave it off.

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
