# DailyBench300

A benchmark harness that runs **Android agent tasks** against a real phone and a real LLM, capturing
success, cost, battery, thermal, and per-step trajectory traces for every run. It uses the
[mobilerun SDK](https://docs.mobilerun.ai/framework/sdk) to drive the phone over ADB and an
OpenAI-compatible model endpoint (OpenRouter, or a local host) over HTTP.

**Corpus:** a fixed 28-day schedule of **530 runnable tasks** (216 easy / 242 medium / 72 hard,
incl. 36 ASK USER + 36 deterministic) across 31 apps, plus a **61-task public sample** that the
website publishes with trajectory replays. The live site is at
[https://yuvrajsingh-mist.github.io/DrainBench300/](https://yuvrajsingh-mist.github.io/DrainBench300/).

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
# then view pages/tasks.html (530 tasks) or the homepage (public examples) in website/
```

---

## Repo layout

- `dailybench_runner.py` / `dailybench_tasks.py` — CLI entry points
- `src/DailyBench/` — harness package (metrics, dataset, task batch, custom tools)
- `benchmarks/dailyBench-600/` — `tasks_530.md` (source of truth) + `DailyBench_530_v1.json/.jsonl`,
  `public.md` + `DailyBench_public_v2.json`, per-day vars (`tasks_vars/`)
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

## Testing

```bash
make sync          # uv sync --extra dev --extra tracing --extra hf (first time)
make test          # or: ./scripts/run/run_tests.sh
```

## Reports

Per-day full-bench run reports (days 1-5) + the public-sample report live in
[reports/](reports/) (`day-1..5`, `public/`), with structured metrics in `reports/metrics/`.
