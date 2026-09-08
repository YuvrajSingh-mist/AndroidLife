# AndroidLife

A **real-phone** Android agent benchmark: everyday tasks on a live device, with success **and**
phone cost (battery, thermal, dollars, steps). Agents run through
[MobileRun](https://docs.mobilerun.ai/framework/sdk) (by [Droidrun](https://www.droidrun.ai/)) over ADB.

**Models:** not on-device-only. AndroidLife evaluates **open-weight** models across sizes —
frontier / mid-size LLMs via API today, with a **heavy future focus on SLMs deployed on the phone**.
Same harness either way (OpenRouter, local OpenAI-compatible server, or on-device runtime).

Live site: [https://yuvrajsingh-mist.github.io/AndroidLife/](https://yuvrajsingh-mist.github.io/AndroidLife/) ·
Code: [github.com/YuvrajSingh-mist/AndroidLife](https://github.com/YuvrajSingh-mist/AndroidLife) ·
Public run artifacts: [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public)
(old `dailybench500-public` redirects here).

**Two tiers**, as presented on the website:

- **60-task public benchmark** - the fully-run preview. Every one of the 60 tasks has been executed
  on a real Android phone (OnePlus CPH2423) by real LLMs; each carries its **full agent trajectory**
  (model thoughts, tool calls, per-step screenshots, screen-replay GIF), run telemetry (cost /
  battery / thermal / steps), and a manual-audit verdict, all browsable on the site's leaderboard
  and per-task pages. Source: `benchmarks/dailyBench-600/DailyBench_public_v2.json` (with `public.md`,
  `public_vars.local.env`, `multiturn_kb_public.json`).

- **530-task dataset** - the complete benchmark corpus: **530 runnable tasks** (216 easy / 242
  medium / 72 hard; 49 ASK USER = 36 single-turn + 13 multi-turn KB, 23 deterministic) on a fixed
  28-day schedule across **31 apps**, from which the public 60 are sampled. The 28 days model one
  simulated month of everyday use (~10 apps/day - a real person never touches all 31 in a day); they
  are the dataset's structure, *not* a run length - actual runs are short, bounded sessions
  (the 60-task public run takes ~2-9 h and can even be cut short by the phone's battery dying, as the
  run reports record). Still being benchmarked - more days' runs and their trajectories are added as
  they complete. Source: `benchmarks/dailyBench-600/DailyBench_530_v1.json` (with `tasks_530.md`).

---

## Quick start

Everything is `uv`-managed — no bare `pip`/`python3`.

```bash
# 1. Install + guided onboarding (checks prereqs, device, apps, config, seeds)
uv run python scripts/setup.py            # or: make setup

# 2. Seed the device for the day you'll run, then verify it actually landed
uv run python scripts/setup.py seed --day 1 --serial <device-id>
uv run python scripts/setup.py verify --day 1 --serial <device-id>
```

Prerequisites (system tools): `adb`, `scrcpy`, Python 3.11–3.13.

Copy `.env.example` → `.env` and fill in your API keys (`OPENROUTER_API_KEY` for the agent LLM,
`OPENAI_API_KEY` for the `ask_user` simulated user on ASK USER tasks — each is independently optional).

### Run a full day

```bash
export DAILYBENCH_SERIAL=<device-id>                       # e.g. 192.168.1.23:5555 or USB serial
export LLM_UPSTREAM=https://openrouter.ai/api
export MODEL=qwen/qwen3.7-flash                            # default agent model (cheap + reliable)

# 1. Start Phoenix tracing for that day (per-day SQLite DB + project dailybench-dayN)
uv run python scripts/run/start_phoenix.py --day 3

# 2. Run the day (drops into assets/runs/<timestamp>/day3/...)
uv run dailybench_tasks.py --serial "$DAILYBENCH_SERIAL" \
  --llm-upstream-base "$LLM_UPSTREAM" --model "$MODEL" \
  --day 3 --vars-file benchmarks/dailyBench-600/tasks_vars/day_3.env
```

`--day N` works for any day 1..28; combine with `--bucket`/`--app`/`--task-id`, and add `--dry-run`
or `--list` first to inspect. A full CLI + flag reference is in
[docs/cli-reference.md](docs/cli-reference.md).

### Public 3-day sample (60 tasks) — detached launch + resume

The public sample (`benchmarks/dailyBench-600/DailyBench_public_v2.json` + `public.md` +
`public_vars.local.env` + `multiturn_kb_public.json`) is the current benchmark. Launch it
**detached** — a plain `nohup ... &` dies with `init_sys_streams: Bad file descriptor` when the
launching terminal closes, so **always redirect stdin from `/dev/null`**:

```bash
RUN_TS=$(date +%Y%m%d-%H%M%S)
nohup uv run python scripts/run/start_phoenix.py --public --run-ts "$RUN_TS" > "assets/db/public/phoenix-$RUN_TS.log" 2>&1 &   # start phoenix FIRST
# wait for :6006, then:
nohup uv run dailybench_tasks.py --dataset benchmarks/dailyBench-600/DailyBench_public_v2.json \
  --source public.md --all --serial 100.108.15.119:5555 \
  --llm-upstream-base https://openrouter.ai/api --model <model> \
  --ask-user-model gpt-5.4-mini --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action --vars-file benchmarks/dailyBench-600/public_vars.local.env \
  --ask-user-kb benchmarks/dailyBench-600/multiturn_kb_public.json \
  --phoenix-url http://localhost:6006 --phoenix-project dailybench-public \
  --run-root "assets/runs/public/$RUN_TS" \
  < /dev/null > "assets/runs/public/batch-$RUN_TS.log" 2>&1 &
```

If it dies mid-run, **resume in place** with `--run-root <same> --resume-from <next-task-id>`
(no re-runs of completed tasks). Wireless ADB is via **Tailscale** (`100.108.15.119:5555`) —
the phone roams subnets, so the Tailscale IP is the stable serial. Model compatibility notes
(mandatory-reasoning models, malformed-complete-XML gotcha) live in
[docs/cli-reference.md](docs/cli-reference.md#model-compatibility-notes-2026-09-01).

### Inspect results

```bash
# Aggregate a run into MobileWorld metrics (SR, avg steps, UIQ, KBIQ, cost…)
uv run scripts/eval/dailybench_report.py --runs assets/runs/<timestamp>

# Manual KBIQ audit of KB/multi-turn ask_user queries (writes <run>/kb_audit.json,
# which the report's KBIQ row reads)
uv run scripts/eval/audit_kb_queries.py --runs 'assets/runs/<timestamp>/*' --source public.md --interactive

# Rebuild the site's trajectory assets (GIFs + step screenshots + condensed traces)
node website/tools/export_trajectories.mjs
```

### Website — local preview (important)

The site is **static HTML/JS** under `website/` (same tree GitHub Pages deploys). Open it
via a local HTTP server — **do not** open `index.html` as a `file://` URL (relative
assets / fetch of `assets/data/*.json` will break).

```bash
# From the repo root (leave this running while you edit):
cd website
python3 -m http.server 8000
# then open http://localhost:8000/
#   leaderboard:  http://localhost:8000/   (homepage)
#   all tasks:    http://localhost:8000/pages/tasks.html
```

**Seeing your edits:** the server reads files from disk on every request — no rebuild
step for HTML/CSS/JS. After saving, **hard-refresh the browser** (`Cmd+Shift+R` /
`Ctrl+Shift+R`) so cached JS/CSS don't stick.

| What you changed | What to do |
|---|---|
| `website/index.html`, `pages/*.html`, `assets/css/*`, `assets/js/*` (e.g. `leaderboard.js`) | Save → hard-refresh browser |
| Task corpus / labels that feed `site_data.json` | `node website/tools/build_site_data.mjs` → hard-refresh |
| Public traj picker / GIF links in `trajectories/index.json` | `uv run python website/tools/build_public_traj_from_hf.py` → hard-refresh |
| Local trajectory screenshots/GIFs (full-bench export) | `node website/tools/export_trajectories.mjs` → hard-refresh |

You do **not** need to restart `python3 -m http.server` after edits.

Production deploy is automatic on push to `master` → GitHub Pages at
[https://yuvrajsingh-mist.github.io/AndroidLife/](https://yuvrajsingh-mist.github.io/AndroidLife/).
Trajectory **media** lives on Hugging Face (`YuvrajSingh9886/androidlife-public`);
raw `assets/runs/` stay local/HF and are gitignored.

---

## Repo layout

- `dailybench_runner.py` / `dailybench_tasks.py` — CLI entry points
- `src/DailyBench/` — harness package (metrics, dataset, task batch, custom tools)
- `benchmarks/dailyBench-600/` — task data: the **530-task dataset** (`tasks_530.md`,
  `DailyBench_530_v1.json/.jsonl`, per-day `tasks_vars/`) and the **60-task public benchmark**
  (`public.md`, `DailyBench_public_v2.json`, `public_vars.local.env`, `multiturn_kb_public.json`)
- `config/` — `user_config.example` → copy to `user.yaml` (persona placeholders, gitignored)
- `scripts/` — setup, seeding, run helpers, eval, tools
- `assets/` — generated data: `runs/` (artifacts), `seeds/`, `db/dayN/phoenix.db`
- `website/` — static site (GitHub Pages), including the trajectory viewer
- `reports/` — run reports + per-day metrics
- `tests/` — pytest suite

## Documentation

- [docs/cli-reference.md](docs/cli-reference.md) — flags, app-reset fairness, step-budget policy
- [docs/benchmark-spec.md](docs/benchmark-spec.md) — task corpus design, apps, schedule
- [docs/evaluation-policy.md](docs/evaluation-policy.md) — success/hallucination/partial rules, metrics
- [docs/multiturn-public-flow.md](docs/multiturn-public-flow.md) — multi-turn KB dialogues, rolling memory, KBIQ
- [docs/app-usage-grounding.md](docs/app-usage-grounding.md) — how tasks map to real app usage
- [docs/fabricated-test-data.md](docs/fabricated-test-data.md) — seed data philosophy + controls
- [docs/future-directions.md](docs/future-directions.md) — planned task areas
- [docs/HANDOFF.md](docs/HANDOFF.md) — internal run workflow + conventions (per-day reset, metrics)
- README § **Website — local preview** — `cd website && python3 -m http.server 8000` → http://localhost:8000/

## Testing

```bash
make sync          # uv sync --extra dev --extra tracing --extra hf (first time)
make test          # or: ./scripts/run/run_tests.sh
```

## Reports

Per-day full-bench run reports (days 1-5) + the public-sample report live in
[reports/](reports/) (`day-1..5`, `public/`), with structured metrics in `reports/metrics/`.
