# AndroidLife

Real-phone Android agent benchmark: everyday tasks on a live device, scoring **task success** and **phone cost** (battery, thermals, $$, steps). Agents are driven by [MobileRun](https://docs.mobilerun.ai/framework/sdk) (Droidrun) over ADB.

Built for **open-weight** models — OpenRouter / any OpenAI-compatible API today, with **on-device SLMs** as the long-term focus. Same harness either way.

| | |
|---|---|
| **Leaderboard / site** | [androidlife-website.vercel.app](https://androidlife-website.vercel.app/) |
| **Code** | [github.com/YuvrajSingh-mist/AndroidLife](https://github.com/YuvrajSingh-mist/AndroidLife) |
| **Public run artifacts** | [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public) |
| **530-task corpus** | [`YuvrajSingh9886/androidlife-530`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-530) |

## What you get

- **60-task public benchmark** — fully executed on a OnePlus CPH2423. Each task ships trajectory, screenshots/GIF, telemetry, and a **manual-audit** verdict (ground truth for the leaderboard).  
  Sources: `benchmarks/androidlife-600/AndroidLife_public_v2.json`, `public.md`, `public_vars.local.env`, `multiturn_kb_public.json`.

- **530-task dataset** — 216 easy / 242 medium / 72 hard on a fixed **28-day** schedule across **31 apps**. The schedule is dataset shape (≈10 apps/day), not wall-clock run length. Public 60 is sampled from this set.  
  Sources: `AndroidLife_530_v1.json`, `tasks_530.md`. Spec: [docs/benchmark-spec.md](docs/benchmark-spec.md).

**TEXT** (default) = accessibility tree only. **VISION** = add `--vision` (a11y + screenshot each step). Report them as separate rows.

## Requirements

- macOS or Linux host with **Python 3.11–3.13** and [`uv`](https://docs.astral.sh/uv/)
- `adb` (Android platform-tools); `scrcpy` recommended
- A dedicated Android phone with USB or wireless debugging (this project’s device: OnePlus CPH2423)
- API keys as needed:
  - `OPENROUTER_API_KEY` — agent via OpenRouter
  - `OPENAI_API_KEY` — simulated `ask_user` (ASK USER / multi-turn KB tasks)
  - omit OpenRouter key if you point `--llm-upstream-base` at a **local** OpenAI-compatible server (e.g. llama.cpp)

## Setup

```bash
git clone https://github.com/YuvrajSingh-mist/AndroidLife.git
cd AndroidLife

# install deps + scaffold .env / config (or: make setup)
uv run python scripts/setup.py
# equivalent: make sync && make setup

cp .env.example .env   # if setup did not already create .env
# edit .env → OPENROUTER_API_KEY / OPENAI_API_KEY as needed
```

Sanity checks:

```bash
make test-fast          # unit smoke
make app-audit          # phone has the expected apps
make smoke-test         # LLM + ADB + one real task (optional)
```

### Connect the phone

```bash
adb devices -l
# USB: use the device serial from `adb devices`
# Wireless (example Tailscale IP — your port changes after re-pair):
adb pair <phone-ip>:<pairing-port>   # one-time, with the 6-digit code
adb connect <phone-ip>:<connect-port>
S=<phone-ip>:<connect-port>          # export or paste into commands below
adb -s "$S" shell echo OK
```

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

uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-600/AndroidLife_public_v2.json \
  --source public.md --all \
  --serial "$S" \
  --llm-upstream-base https://openrouter.ai/api \
  --model qwen/qwen3.6-plus \
  --ask-user-model gpt-5.4-mini \
  --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action \
  --vars-file benchmarks/androidlife-600/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-600/multiturn_kb_public.json \
  --run-root "$RUN_ROOT"
  # add --vision for VISION mode
  # add --phoenix-url http://localhost:6006 --phoenix-project androidlife-public if Phoenix is up
  # add --no-tracing to skip tracing entirely
```

**Local llama.cpp** (OpenAI-compatible server on `:8088`):

```bash
# example helper (64k ctx on Apple Silicon — adjust as needed)
bash scripts/llm/serve_qwen35_4b.sh   # or your own llama-server flags

uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-600/AndroidLife_public_v2.json \
  --source public.md --all \
  --serial "$S" \
  --llm-upstream-base http://127.0.0.1:8088 \
  --model Qwen3.5-4B \
  --ask-user-model gpt-5.4-mini \
  --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action --no-tracing \
  --vars-file benchmarks/androidlife-600/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-600/multiturn_kb_public.json \
  --run-root "assets/runs/public/$(date +%Y%m%d-%H%M%S)"
```

Detach so the run survives terminal close (macOS-friendly):

```bash
RUN_TS=$(date +%Y%m%d-%H%M%S)
nohup uv run androidlife_tasks.py ... --run-root "assets/runs/public/$RUN_TS" \
  < /dev/null > "assets/runs/public/batch-$RUN_TS.log" 2>&1 &
# or double-fork / start_new_session from a launcher script
```

Resume an interrupted batch with the **same** `--run-root` and `--resume-from <task_id>` (or an explicit remaining `--task-id` list).  
Flags: [docs/cli-reference.md](docs/cli-reference.md). (`dailybench_tasks.py` remains a supported alias — [docs/naming.md](docs/naming.md).)

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
uv run androidlife_tasks.py --serial "$S" \
  --llm-upstream-base https://openrouter.ai/api --model "$MODEL" \
  --day 3 --vars-file benchmarks/androidlife-600/tasks_vars/day_3.env
```

## Repository layout

| Path | Role |
|---|---|
| `androidlife_runner.py` / `androidlife_tasks.py` | CLI entrypoints (`dailybench_*` aliases) |
| `src/androidlife/` | Harness |
| `benchmarks/androidlife-600/` | Public 60 + 530 datasets, vars, KB |
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

## Fuel the benches

Perf benchmarking burns wall-clock, watts, and a lot of coffee. If these numbers helped you pick a board or a model, fuel the next run:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/YuvrajSingh-mist)
[![Support me on Ko-fi](https://storage.ko-fi.com/cdn/kofi2.png?v=3)](https://ko-fi.com/O7W120DR8R)
