# AndroidLife

Real-phone Android agent benchmark: everyday tasks on a live device, scoring **task success** and **phone cost** (battery, thermals, $$, steps). Agents are driven by [MobileRun](https://docs.mobilerun.ai/framework/sdk) / Droidrun over ADB — **pinned to `mobilerun==0.6.15`** (see `pyproject.toml` + `uv.lock`) for reproducible harness behavior.

Built for **open-weight** models — OpenRouter / any OpenAI-compatible API today, with **on-device SLMs** as the long-term focus. Same harness either way.

| | |
|---|---|
| **Leaderboard / site** | [androidlife-website.vercel.app](https://androidlife-website.vercel.app/) |
| **Code** | [github.com/YuvrajSingh-mist/AndroidLife](https://github.com/YuvrajSingh-mist/AndroidLife) |
| **Public run artifacts** | [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public) |
| **530-task corpus** | [`YuvrajSingh9886/androidlife-530`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-530) |

## What you get

- **60-task public benchmark** — fully executed on a OnePlus CPH2423. Each task ships trajectory, screenshots/GIF, telemetry, and a **manual-audit** verdict (ground truth for the leaderboard).  
  Sources: `benchmarks/androidlife-530/AndroidLife_public_v2.json`, `public.md`, `public_vars.local.env`, `multiturn_kb_public.json`.

- **530-task dataset** — 216 easy / 242 medium / 72 hard on a fixed **28-day** schedule across **31 apps**. The schedule is dataset shape (≈10 apps/day), not wall-clock run length. Public 60 is sampled from this set.  
  Sources: `AndroidLife_530_v1.json`, `tasks_530.md`. Spec: [docs/benchmark-spec.md](docs/benchmark-spec.md).

**TEXT** (default) = accessibility tree only. **VISION** = add `--vision` (a11y + screenshot each step). Report them as separate rows.

## Requirements

- macOS or Linux host with **Python 3.11–3.13** and [`uv`](https://docs.astral.sh/uv/)
- `adb` (Android platform-tools)
- A dedicated Android phone with USB or wireless debugging (reference device: OnePlus CPH2423)
- **MobileRun / Droidrun `0.6.15`** — exact pin (`mobilerun==0.6.15`); do not float to a newer wheel unless you intentionally re-lock and re-validate
- API keys as needed:
  - `OPENROUTER_API_KEY` — agent via OpenRouter
  - `OPENAI_API_KEY` — simulated `ask_user` (ASK USER / multi-turn KB tasks)
  - omit OpenRouter key if you point `--llm-upstream-base` at a **local** OpenAI-compatible server (e.g. llama.cpp)

### Tested hosts

Harness install + public runs have been exercised on:

| Host | Notes |
|---|---|
| **MacBook Air (M1, 2020)** | Apple Silicon, local + cloud LLM |
| **Mac mini (M4, 2025, 16 GB)** | Apple Silicon, local llama.cpp (e.g. Qwen3.5-4B) + cloud LLM |

Paths below are **repo-relative** — run every command from the cloned `AndroidLife/` root. The only machine-specific value is your ADB serial (`$S`).

## Setup

Everything is **`uv` + `pyproject.toml` + `uv.lock`** — no `pip install -r`, no Poetry.
Run commands from the repo root so console scripts and relative paths resolve.

```bash
git clone https://github.com/YuvrajSingh-mist/AndroidLife.git
cd AndroidLife   # ← stay here for all later commands

# creates .venv from uv.lock (pins MobileRun 0.6.15 + transitive deps)
uv sync --extra dev --extra tracing --extra hf   # or: make sync
uv run python scripts/setup.py                   # or: make setup  (scaffolds .env / config)

cp -n .env.example .env                          # skip if .env already exists
# edit .env → OPENROUTER_API_KEY / OPENAI_API_KEY as needed

# confirm the harness pin from the lockfile env
uv run python -c "import importlib.metadata as m; print(m.version('mobilerun'))"
# → 0.6.15
```

Preferred entrypoints (defined in `pyproject.toml` `[project.scripts]`):

```bash
uv run androidlife-tasks --help
uv run androidlife-runner --help
# thin wrappers also work:  uv run androidlife_tasks.py …
```

Sanity checks:

```bash
make test-fast          # unit smoke
make app-audit          # phone has the expected apps
make smoke-test         # LLM + ADB + one real task (optional)
```

`make test-fast` never touches the handset. Tests that *drive* it — launching or
force-stopping apps, or anything that reaches `reset_app_state` — are skipped
unless you opt in:

```bash
ANDROIDLIFE_DEVICE_TESTS=1 make test-fast   # only when no benchmark batch is running
```

That default exists because the phone is exclusive to the run: a stray
`am force-stop` / `input keyevent HOME` steals the foreground from the task in
flight, corrupting the benchmark and looking like a flaky test rather than the
interference it is.

### Connect the phone

```bash
adb devices -l
# USB: enable debugging, plug in, accept the RSA prompt
# Wireless: Developer options → Wireless debugging → Pair / Connect
#   adb pair <phone-ip>:<pairing-port>     # 6-digit code (pairing port)
#   adb connect <phone-ip>:<connect-port>  # different port from the IP & port line

# pick the first online device (works on any machine)
export S="$(adb devices | awk '/\tdevice$/{print $1; exit}')"
test -n "$S" || { echo "No adb device in 'device' state"; exit 1; }
echo "Using serial: $S"
adb -s "$S" shell echo OK
```

Keep `$S` exported in that shell (or paste the serial into `--serial` flags).

## Run the public 60 (operator path)

Full reset/seed runbook: **[docs/device-reset-and-seed.md](docs/device-reset-and-seed.md)**.  
GUI-only seeds (Chrome history, Photos captions, Gmail, …): **[docs/pre-run-checklist.md](docs/pre-run-checklist.md)**.

### 1. Reset + seed

```bash
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --apply

uv run python scripts/seeding/seed_data.py --serial "$S" --day 1
uv run python scripts/seeding/seed_data.py --serial "$S" --day 2
uv run python scripts/seeding/seed_data.py --serial "$S" --day 3
uv run python scripts/seeding/enrich_public_notes.py --serial "$S"
uv run python scripts/seeding/fabricate_public_pdfs.py --serial "$S"

# re-seed tomorrow afternoon conflicts (Team Sync / Mentor 1 on 1) — see device-reset-and-seed.md

uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --verify-only
for d in 1 2 3; do
  uv run python scripts/seeding/verify_day1_seeds.py --serial "$S" --day "$d"
done
```

Do **not** start a scored run if verify fails. Finish the pre-run checklist in the UI next.

### 2. Launch the batch

**OpenRouter (cloud) example** — Phoenix optional for tracing:

```bash
RUN_TS=$(date +%Y%m%d-%H%M%S)
RUN_ROOT="assets/runs/public/$RUN_TS"

# optional tracing
# uv run python scripts/run/start_phoenix.py --public --run-ts "$RUN_TS"

uv run androidlife-tasks \
  --dataset benchmarks/androidlife-530/AndroidLife_public_v2.json \
  --source public.md --all \
  --serial "$S" \
  --llm-upstream-base https://openrouter.ai/api \
  --model qwen/qwen3.6-plus \
  --ask-user-model gpt-5.4-mini \
  --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action \
  --vars-file benchmarks/androidlife-530/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-530/multiturn_kb_public.json \
  --run-root "$RUN_ROOT"
  # add --vision for VISION mode
  # add --phoenix-url http://localhost:6006 --phoenix-project androidlife-public if Phoenix is up
  # add --no-tracing to skip tracing entirely
```

**Local llama.cpp** (OpenAI-compatible server on `:8088`):

Model-agnostic launcher + flag table: [`scripts/llm/README.md`](scripts/llm/README.md).

```bash
export PATH="$HOME/local/bin:/opt/homebrew/bin:$PATH"
# any preset: qwen3.5-4b | gemma4-e2b | mai-ui-2b | gui-owl-1.5-2b
# or: bash scripts/llm/serve_gguf.sh /path/to/model.gguf --alias MyModel
bash scripts/llm/serve_gguf.sh qwen3.5-4b
# shared Metal args: -ngl 99 -fa on -c 65536 -b 2048 -ub 512 -ctk/-ctv q8_0 --jinja -np 1
# Qwen also gets --reasoning off; vision presets auto-attach --mmproj
# back-compat: bash scripts/llm/serve_qwen35_4b.sh

uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-530/AndroidLife_public_v2.json \
  --source public.md --all \
  --serial "$S" \
  --llm-upstream-base http://127.0.0.1:8088 \
  --model Qwen3.5-4B \
  --ask-user-model gpt-5.4-mini \
  --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action --no-tracing \
  --vars-file benchmarks/androidlife-530/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-530/multiturn_kb_public.json \
  --run-root "assets/runs/public/$(date +%Y%m%d-%H%M%S)"
# --model must match the server -a alias; add --vision for mmproj models
```

#### Public 60-task batch (detached)

Detach so the run survives terminal close (from repo root). Prefer `androidlife-tasks`; `androidlife_tasks.py` is an equivalent alias.

```bash
RUN_TS=$(date +%Y%m%d-%H%M%S)
nohup uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-530/AndroidLife_public_v2.json \
  --source public.md --all --serial "$S" \
  --llm-upstream-base https://openrouter.ai/api --model <model> \
  --ask-user-model gpt-5.4-mini --temperature 0.0 \
  --steps 60 --task-timeout 2400 \
  --save-trajectory action \
  --vars-file benchmarks/androidlife-530/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-530/multiturn_kb_public.json \
  --run-root "assets/runs/public/$RUN_TS" \
  < /dev/null > "assets/runs/public/batch-$RUN_TS.log" 2>&1 &
tail -f "assets/runs/public/batch-$RUN_TS.log"

# optional: add --vision for screenshot-driven runs
# resume: same --run-root + --resume-from <task_id>
```

Resume an interrupted batch with the **same** `--run-root` and `--resume-from <task_id>` (or an explicit remaining `--task-id` list).  
Flags: [docs/cli-reference.md](docs/cli-reference.md). (`uv run dailybench-tasks` / `androidlife-tasks` remain supported aliases — [docs/naming.md](docs/naming.md).)

### 3. Score + file artifacts

```bash
RUN_ROOT=assets/runs/public/<RUN_TS>

uv run scripts/eval/androidlife_report.py --runs "$RUN_ROOT" --source public.md \
  --hallucination-judge-model gpt-5.4-mini \
  --out "reports/metrics/public/public-<RUN_TS>-report.json" \
  --out-md "reports/metrics/public/public-<RUN_TS>-report.md"

uv run scripts/eval/eval_hallucination_controls.py --runs "$RUN_ROOT" --sub public \
  --model gpt-5.4-mini \
  --out "reports/metrics/hallucination/public-<RUN_TS>.json" \
  --out-md "reports/metrics/hallucination/public-<RUN_TS>.md"

make organize-public
```

Then write the narrative manual audit under `reports/public/public-<RUN_TS>.md`. Manual audit is the leaderboard ground truth — official self-report tables are inflated.

## 530-day schedule (optional)

```bash
uv run python scripts/run/start_phoenix.py --day 3
uv run androidlife-tasks --serial "$S" \
  --llm-upstream-base https://openrouter.ai/api --model "$MODEL" \
  --day 3 --vars-file benchmarks/androidlife-530/tasks_vars/day_3.env
```

## Repository layout

| Path | Role |
|---|---|
| `androidlife-tasks` / `androidlife-runner` | Console scripts from `pyproject.toml` (`dailybench-*` aliases) |
| `src/androidlife/` | Harness |
| `benchmarks/androidlife-530/` | Public 60 + 530 datasets, vars, KB |
| `scripts/seeding/` | Reset / seed / verify |
| `scripts/eval/` | Reports, HC judge, KB audit |
| `scripts/llm/` | Local GGUF download / serve helpers |
| `assets/` | Runs, seeds, DBs (gitignored) |
| `reports/` | Metrics + narrative audits |
| `website/` | GitHub Pages redirect → Vercel |
| `androidlife-website/` | Local clone of private site repo (gitignored) |

## Docs

- [docs/getting-started.md](docs/getting-started.md) — mental model + artifact map  
- [docs/device-reset-and-seed.md](docs/device-reset-and-seed.md) — reset + seed commands  
- [docs/pre-run-checklist.md](docs/pre-run-checklist.md) — UI/cloud seeds ADB cannot plant  
- [docs/cli-reference.md](docs/cli-reference.md) — flags, detach / resume  
- [docs/benchmark-spec-public.md](docs/benchmark-spec-public.md) — public 60  
- [docs/benchmark-spec.md](docs/benchmark-spec.md) — 530 corpus  
- [docs/evaluation-policy.md](docs/evaluation-policy.md) — grading  
- [docs/reproducibility.md](docs/reproducibility.md) — what “reproducible” means here  

## Website

Canonical: https://androidlife-website.vercel.app/  
(GitHub Pages redirects: https://yuvrajsingh-mist.github.io/AndroidLife/)

Site source is the private repo [`androidlife-website`](https://github.com/YuvrajSingh-mist/androidlife-website). Keep a local checkout at `androidlife-website/` (gitignored) and push from there.

## Citation

If you use AndroidLife — the benchmark, leaderboard, tasks, or results — please credit this work and cite it as:

```bibtex
@misc{singh2026androidlife,
      title={AndroidLife: Real-Phone Android Agent Benchmark for Open-Weight Models and On-Device SLMs},
      author={Yuvraj Singh},
      year={2026},
      howpublished={\url{https://github.com/YuvrajSingh-mist/AndroidLife}},
}
```

Also see [`CITATION.cff`](CITATION.cff).

## License

- **Code / harness** (`src/`, scripts, tooling): [Apache License 2.0](LICENSE) — keep the copyright notice and `NOTICE` when you redistribute.
- **Benchmark datasets & task content** (task definitions, schedules, published evaluation artifacts): [CC BY 4.0](LICENSE-DATASET) — free to use and adapt, including commercially, **with attribution** to Yuvraj Singh (name + link; indicate changes if you modify).

Academic paper citation is a community norm (use the BibTeX above); CC BY is what legally requires credit when the dataset or task content is shared or adapted.

## Fuel the benches

Perf benchmarking burns wall-clock, watts, and a lot of coffee. If these numbers helped you pick a board or a model, fuel the next run:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/YuvrajSingh-mist)
[![Support me on Ko-fi](https://storage.ko-fi.com/cdn/kofi2.png?v=3)](https://ko-fi.com/O7W120DR8R)
