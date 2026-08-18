# DailyBench300

A benchmark harness that runs Android agent tasks (via the [mobilerun SDK](https://docs.mobilerun.ai/framework/sdk)) against a real phone and a real LLM, and captures phone + model performance metrics for every run.

## Architecture

- **Phone**: agent execution only.
- **mini2** (or any model host): serves the LLM over an OpenAI-compatible endpoint.
- **This repo**: benchmark harness, dataset, and run artifacts — drives the phone over ADB and the model over HTTP.

That split is the most stable setup found for repeatable runs. The harness talks to the phone entirely through the `mobilerun` Python SDK (`AndroidDriver`/`MobileAgent`), in-process — there's no external `mobilerun` CLI binary involved anywhere.

## Prerequisites

Installed locally (system tools, not `uv`-managed):

- `adb`
- `scrcpy`
- Python 3.11–3.13 (required by the `mobilerun` package)

## Setup

This repo is `uv`-managed end to end: no bare `pip`/`python3` — every install and every script/test run goes through `uv`.

### One-command onboarding (recommended)

Plug in / pair your phone, then run the guided setup. It checks prerequisites,
installs deps, scaffolds `.env` + `config/user.yaml`, picks your device, audits
that the 22 benchmark apps are installed, and builds the per-day seed manifests
and vars:

```bash
uv run python scripts/setup.py            # or: make setup
```

Then seed the device for the day you're about to run and verify:

```bash
uv run python scripts/setup.py seed --day 1 --serial <id>   # push fabricated seeds
uv run python scripts/setup.py verify --day 1 --serial <id> # confirm on-device
```

The device-specific seed values (Obsidian vault path, Google calendar id,
persona contact email) are **auto-detected** from your phone — no manual path
editing. Override any of them in `config/user.yaml` (`vault path`, `calendar id`,
`contact email`) if your device is unusual. Run `uv run python scripts/tools/app_audit.py`
(or `make app-audit`) any time to check the phone has the apps the tasks need.

> New to the benchmark / setting up a fresh phone? See
> [docs/new-device-setup.md](docs/new-device-setup.md) for the full step-by-step
> (install apps → scaffold config → build manifests → seed → verify → run → reset).

### Manual setup (the individual steps)

```bash
uv sync --extra dev --extra tracing --extra hf
```

- `dev` — `pytest`, for `make test`
- `tracing` — `arize-phoenix`, only needed for `--tracing` (see [docs/advanced-features.md](docs/advanced-features.md))
- `hf` — `huggingface_hub`, only needed for pushing dataset exports to Hugging Face

Then set up your API keys - copy the template and fill in your own values:

```bash
cp .env.example .env
```

```dotenv
# .env
OPENAI_API_KEY=sk-...      # only needed for the ask_user tool (Hard/ASK USER tasks)
OPENROUTER_API_KEY=...     # only needed if using OpenRouter instead of a local model host
HF_TOKEN=hf_...            # only needed for pushing dataset exports to Hugging Face
```

`.env` is gitignored and loaded automatically by both entrypoints (`dailybench_runner.py`/`dailybench_tasks.py`) via `python-dotenv` — no `export`, no `--env-file`, nothing else to configure. Leave any line blank if you don't need that feature yet; each one is independently optional (see the comments in `.env.example`).

> **Note:** The `ask_user` simulated user (`--ask-user-model`, default `gpt-5.4-mini`) only supports **OpenAI-hosted models** — the `ask_user` tool calls the OpenAI API directly, and its per-1M-token cost table covers OpenAI models. It is a separate service from the agent's LLM (`--model`), which can be any model your LLM host (e.g. OpenRouter) serves.

## Tracing (Phoenix)

[Arize Phoenix](https://github.com/Arize-ai/phoenix) captures every LLM call, tool execution, and agent step as OpenTelemetry traces — essential for debugging runs, comparing model behavior, and auditing token usage. The `mobilerun` SDK auto-instruments traces when it detects a Phoenix server running locally.

### Start the Phoenix server

Phoenix DBs are **per-day**: each day's run writes into its own SQLite DB at
`assets/db/dayN/phoenix.db` (project `dailybench-dayN`). Point the server at the day
you're running:

```bash
uv run python scripts/run/start_phoenix.py --day 4   # helper: creates assets/db/day4/phoenix.db, project dailybench-day4
```

or, equivalently (raw command, for custom ports/hosts):

```bash
PHOENIX_SQL_DATABASE_URL="sqlite:///$PWD/assets/db/day1/phoenix.db" \
PHOENIX_PROJECT_NAME=dailybench-day1 \
uv run phoenix serve --port 6006
```

This must be running **before** you start any benchmark run. The server's web UI will be at [http://localhost:6006](http://localhost:6006).

> **Note:** `run_day.py --day N` auto-targets the `dailybench-dayN` project, so a day's
traces land in that day's own project + DB. Query a day's spans directly with `sqlite3`
against `assets/db/dayN/phoenix.db`, or use the Phoenix UI to explore span trees, token
counts, and latency.
>
> **Guard (added 2026-08-13):** `run_day.py` and the per-task runner now **fail fast
> when tracing is ON but the Phoenix collector isn't reachable** — a silent miss like
> day-4 (2026-08-13, no `day4/phoenix.db` because `phoenix serve` was never started)
> can't happen again. Pass `--no-tracing` only to deliberately skip trace capture.

### How traces flow

1. `phoenix serve` starts a gRPC (port 4317) and HTTP (port 6006/v1/traces) collector
2. `dailybench_runner.py` / `dailybench_tasks.py` set `PHOENIX_HOST=localhost` and `PHOENIX_PORT=4317` automatically when they detect the server — no `--tracing` flag needed
3. The `mobilerun` SDK sends every step (LLM chat, tool call, app launch, etc.) as spans to Phoenix
4. View the full trace tree at [http://localhost:6006](http://localhost:6006)

### Cost tracking (OpenRouter pricing)

Phoenix prices LLM spans by matching `llm.model_name` against a built-in model catalog (OpenAI/Anthropic/Gemini/…). OpenRouter slugs like `qwen/qwen3.6-plus` aren't in that catalog, so their cost shows as **$0.00** even though token counts are recorded. Register real OpenRouter pricing so new spans get costed:

```bash
uv run scripts/tools/register_openrouter_pricing.py --model qwen/qwen3.7-flash
```

This fetches live per-token prices from OpenRouter's model API and upserts them into the live per-day DB (`assets/db/dayN/phoenix.db`; override with `--db`) as user-defined models; Phoenix's cost daemon picks them up within ~5 seconds. Options:

- `--all` — register every model in OpenRouter's catalog
- `--model A --model B` — register specific slugs (repeatable)
- `--prompt-price-per-m 0.15 --completion-price-per-m 0.60` — set prices manually (USD per 1M tokens) without calling the API

Existing spans are not retroactively repriced — run the script once, and new spans for those models carry real cost.


The main tables are `traces`, `spans`, `projects`, and `span_annotations`. See [docs/advanced-features.md](docs/advanced-features.md) for more tracing configuration.

## MobileWorld-style batch metrics

After a batch, aggregate the run folders into the [MobileWorld](https://arxiv.org/abs/2512.19432) metrics (arXiv:2512.19432) — Success Rate (overall + per bucket + interaction/GUI-only split), Average Completion Steps, Average User Queries, and User Interaction Quality (UIQ) — excluding the MCP metric:

```bash
uv run scripts/eval/dailybench_report.py --runs assets/runs/2026-08-01-001234   # default scans assets/runs/*/*
uv run scripts/eval/dailybench_report.py --runs 'assets/runs/2026-08-01-001234/day3/*' --cooldown-seconds 10
```

`--cooldown-seconds` (default `10.0`) is the fixed inter-task pause the batch runner
applies between tasks (`dailybench_tasks.py --cooldown-seconds`). The report subtracts
`cooldown_seconds × (n_tasks − 1)` from the summed per-run wall-clock so the reported
elapsed time is the **TRUE agent running time** (set `0` to report raw per-run elapsed).
Pass it only when the batch was run with the same non-default value.

This writes `report.json` + `report.md` in the current directory. Interaction (ASK USER) tasks are identified via the ask_user_facts sidecar for the runs' source: `--source tasks.md` (default) selects `benchmarks/dailyBench-600/ask_user_facts_730.json`, `--source public.md` selects `benchmarks/dailyBench-600/ask_user_facts.json` (overridable with `--ask-user-facts`). Each run's `meta.json` records its `task_id` (batch runner passes `--task-id`), and `run_metrics.json` records `ask_user_call_count`. See [docs/leaderboard-format.md](docs/leaderboard-format.md).

## Quick start

```bash
cd /Users/yuvrajsingh9886/Desktop/DrainBench300
export DAILYBENCH_SERIAL=172.24.2.66:5555
export LLM_UPSTREAM=http://100.75.134.64:8081/v1  # mini2 over Tailscale; LAN IP drifts
export MODEL='bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF:Q4_K_M'
```

Prefer a hosted model over running your own? Point `LLM_UPSTREAM`/`MODEL` at [OpenRouter](https://openrouter.ai) instead of a local host — no model server to manage:

```bash
export LLM_UPSTREAM=https://openrouter.ai/api
export MODEL='qwen/qwen3.7-flash'
```

`qwen/qwen3.7-flash` is the default agent model (see `scripts/run/run_day.py`): it's cheap
($0.03/$0.13 per 1M tokens), open-source, and XML-reliable for mobilerun's tool-calling
protocol. Override per run with `--model` or `$MODEL`.

This needs `OPENROUTER_API_KEY` set in `.env`. See [docs/advanced-features.md](docs/advanced-features.md) for the full setup.

Confirm the phone and model server are reachable:

```bash
adb devices -l
curl -s "$LLM_UPSTREAM/models"
```

Then run the pre-flight check before any real benchmark run (or after changing phones/model hosts):

```bash
./scripts/run/smoke_test.sh
```

It checks, in order: local prerequisites (`adb`/`curl`/`uv`/the `mobilerun` SDK import), the LLM server (`GET /models` + a real chat completion, auto-selecting the first listed model if `--model` isn't given), wired ADB + a device health check on a USB device, wireless ADB + the same check over TCP/IP (bootstrapping with `adb tcpip`/`adb connect` from a USB device if no wireless serial is given), and finally one real one-step agent run through `dailybench_runner.py` itself. Every target is a flag or env var — nothing is hardcoded to one phone or model host. Naming exactly one of `--usb-serial`/`--wireless-serial` automatically skips the other transport's check:

```bash
./scripts/run/smoke_test.sh --llm-url http://192.168.1.50:8080/v1 --model my-model
./scripts/run/smoke_test.sh --skip-llm --skip-agent-run --wireless-serial 192.168.1.23:5555
./scripts/run/smoke_test.sh --help   # full flag/env var reference
```

The device health check itself is pure SDK: [scripts/tools/device_health_check.py](scripts/tools/device_health_check.py) connects with `mobilerun.AndroidDriver` and exercises `get_date()`/`screenshot()` for real, mirroring [docs.mobilerun.ai/framework/sdk/adb-tools](https://docs.mobilerun.ai/framework/sdk/adb-tools).

### Known-good target (last verified working configuration)

- phone: OnePlus `CPH2423`, Android `15`, SoC `MT6895`
- model host: `mini2` at `http://100.75.134.64:8081/v1`
- model: `bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF:Q4_K_M`

## Wireless ADB

Connect once over USB, then run:

```bash
adb devices -l
PHONE_IP=$(adb shell "ip -f inet addr show wlan0 | sed -n 's/.*inet \\([0-9.]*\\)\\/.*/\\1/p' | head -1" | tr -d '\r')
adb tcpip 5555
adb connect ${PHONE_IP}:5555
adb devices -l
export DAILYBENCH_SERIAL="${PHONE_IP}:5555"
```

Use wireless ADB for real battery / thermal runs so the USB cable does not skew results.

## Running a benchmark

List a task slice from the dataset:

```bash
uv run dailybench_tasks.py --bucket easy --app gmail --list
```

`config/user.yaml` is loaded automatically, so `[placeholder]` values come from there (no `--var` needed for a configured persona); use `--var` to override a single run, `--vars-file` to override a whole day.

Dry-run it first to see the exact commands that would execute:

```bash
uv run dailybench_tasks.py \
  --bucket easy --app gmail \
  --skip-unresolved \
  --serial "$DAILYBENCH_SERIAL" \
  --llm-upstream-base "$LLM_UPSTREAM" \
  --model "$MODEL" \
  --dry-run
```

Then run it for real (drop `--dry-run`):

```bash
uv run dailybench_tasks.py \
  --bucket easy --app gmail \
  --skip-unresolved \
  --serial "$DAILYBENCH_SERIAL" \
  --llm-upstream-base "$LLM_UPSTREAM" \
  --model "$MODEL"
```

Or run a single one-off task with full harness artifacts:

```bash
uv run dailybench_runner.py \
  --serial "$DAILYBENCH_SERIAL" \
  --label gmail-unread-count \
  --sample-interval 0.1 \
  --llm-upstream-base "$LLM_UPSTREAM" \
  --llm-proxy-port 8090 \
  --model "$MODEL" \
  --temperature 0 \
  --steps 50 \
  --goal "Check how many unread emails are in the inbox"
```

All runs land under `assets/runs/<date-time>/<label>/` automatically — no need to specify an output directory.

Stop interrupted runs:

```bash
pkill -f "dailybench_tasks.py" || true
pkill -f "dailybench_runner.py" || true
pkill -f "scripts/tools/openai_proxy_logger.py" || true
pkill -f "scrcpy" || true
```

Full flag reference for both entry points, including the app-reset fairness behavior, repeats caveat, and step-budget policy: [docs/cli-reference.md](docs/cli-reference.md).

## Task dataset

The benchmark is a **28-day schedule of 530 runnable tasks** (530 dataset rows: 216 easy / 242 medium / 72 hard, of which 36 ASK USER + 36 DETERMINISTIC hard; 31 apps, ~10-12 apps/day (mean ~10.8), max 1302 pts). It ships as `tasks_530.md` + `DailyBench_530_v1.json`/`.jsonl` (the dataset the runner reads by default). The corpus is **exactly 530 tasks** — the Google Workspace task sets (Docs/Sheets/Slides/Meet), the Weather app, and 6 newly-installed real apps (Swiggy, Prime Video, MakeMyTrip, BookMyShow, MSN News, Amazon Shopping) replaced repetitive tasks rather than adding to the count (see `docs/benchmark-spec.md` → "Benchmark at a glance" for the full stats).

- **`benchmarks/dailyBench-600/tasks_530.md`** — the source of truth. Edit it and regenerate the JSON/JSONL with `scripts/data/export_530_dataset.py`; each task line carries its `task_id` in an HTML comment so ids survive edits.
- **`benchmarks/dailyBench-600/public.md`** — the public 50-task preview (same structure, a curated sample you can publish/share).
- **`config/user.yaml`** — supplies the persona values for every `[placeholder]` automatically (override per run with `--var`, per day with `--vars-file`).

### Prep the dataset (from scratch)

```bash
# 1. Regenerate the runnable dataset from tasks_530.md (the source of truth):
uv run scripts/data/export_530_dataset.py

# 2. One-time resync: render tasks_530.md from the JSON (embeds task_ids, round-trips itself):
uv run scripts/data/export_530_markdown.py --verify

# 3. Point config/user.yaml at your persona (first time only; ships with defaults):
cp config/user_config.example config/user.yaml   # then edit values

# 4. Verify config resolves every placeholder, ASK USER fact, and seed:
uv run scripts/seeding/verify_config.py

# 5. Generate per-day vars files (tasks_vars/day_N.env) from config + tasks_vars.local.env:
uv run scripts/seeding/generate_day_vars.py --all

# 6. Build a day's fabricated-data seed manifests (any day 1..28 on the set;
#    days 1-6 have hand-authored specs; days 7-28 are auto-generated per-task):
uv run scripts/seeding/build_day_seed_manifest.py --day 1

# 7. Materialise the day's seed artifacts (images/docs) and push to the device:
uv run scripts/seeding/seed_data.py --serial "$DAILYBENCH_SERIAL" --no-push   # dry: only materialise into assets/seeds/
uv run scripts/seeding/seed_data.py --serial "$DAILYBENCH_SERIAL"             # real: push onto the phone
uv run scripts/seeding/seed_data.py --serial "$DAILYBENCH_SERIAL" --day 3 --verify   # device-state check: every declared seed path actually on the phone
```

`--verify` (any `--day`) is the check that catches "the manifest says the seed exists but it was never pushed" — it runs `adb shell ls` on every `seed_device_path` a day's tasks declare and exits 1 if any is missing. Run it before a batch so you never start a run on half-seeded data.

The `.jsonl` is the easiest artifact to push to Hugging Face datasets (`uv sync --extra hf` first).

### Run a day

The runnable set is the default `--dataset`; `config/user.yaml` supplies the persona values and the per-day vars file supplies that day's overrides. **The runner takes any schedule day directly** — no need to hand-list task ids:

**Prepare the device before any run** — wake it, dismiss the lock screen, and return to the
home screen so the first task's agent starts from a clean launcher (not a lock screen / stale
foreground app, which would poison its first screenshot and UI dump):

```bash
adb -s "$DAILYBENCH_SERIAL" shell "input keyevent 3; input keyevent KEYCODE_WAKEUP; wm dismiss-keyguard"
```

```bash
uv run dailybench_tasks.py \
  --serial "$DAILYBENCH_SERIAL" \
  --llm-upstream-base "$LLM_UPSTREAM" \
  --model "$MODEL" \
  --day 3 \
  --vars-file benchmarks/dailyBench-600/tasks_vars/day_3.env
```

`--day N` is a selector on its own (works for any day 1..28) and combines with `--bucket`/`--app`/`--task-id`; add `--dry-run` first to inspect the exact per-task commands, or `--list` to print the day's task ids. Each one carries the **raw goal** (placeholders kept) plus the task's resolved `--var` variables (rendered into the agent's system prompt), and — for ASK USER tasks — the hidden ground-truth fact only via `--ask-user-context` (never as a variable).

Every run lands under `assets/runs/<batch>/day<N>/...` automatically (see [Run artifacts](#run-artifacts)), and every day's fabricated-data manifests are generated under `assets/seeds/manifests/day_<N>/` (per-task `manifest.json` + `manifest_index.json` + `day_<N>_fabricated_data.jsonl`), with the real seed files (photos/pdf/notes) materialised flat under `assets/seeds/day_<N>/`, so the benchmark is fully inspectable and extensible day by day — see [docs/benchmark-spec.md](docs/benchmark-spec.md).

## Run artifacts

Run folders are grouped under `assets/runs/<date-time>/...` automatically, and contain phone/model metrics, logs, and the task's final result. Full contents and metric definitions: [docs/run-artifacts.md](docs/run-artifacts.md).

## Repo layout

- [dailybench_runner.py](dailybench_runner.py): thin CLI wrapper
- [dailybench_tasks.py](dailybench_tasks.py): dataset-backed segmented runner
- [.env.example](.env.example): API key template - copy to `.env` (gitignored) and fill in your own keys
- [src/DailyBench](src/DailyBench): harness package
- [pyproject.toml](pyproject.toml): package metadata
- [Makefile](Makefile): common test commands
- [scripts/tools/openai_proxy_logger.py](scripts/tools/openai_proxy_logger.py): per-run proxy/logger
- [scripts/data/export_530_dataset.py](scripts/data/export_530_dataset.py): tasks_530.md -> DailyBench_530_v1.json/.jsonl exporter
- [scripts/run/smoke_test.sh](scripts/run/smoke_test.sh): pre-flight check for the LLM server, wired/wireless ADB + mobilerun, and one real end-to-end task
- [scripts/tools/device_health_check.py](scripts/tools/device_health_check.py): SDK-only device health check used by `smoke_test.sh`
- [benchmarks/dailyBench-600](benchmarks/dailyBench-600): the 28-day schedule (`tasks_530.md` = the source of truth for the 530-task corpus, `public.md` = public 50-task preview), exported datasets (`.json`/`.jsonl`), and per-day vars (`tasks_vars/`)
- [config](config): the user config — `user_config.example` is the committed, documented persona template; copy to `user.yaml` (gitignored) and edit
- [assets](assets): everything generated — `assets/runs/` (run artifacts), `assets/seeds/` (per-day real seed files + generated manifests with on-device paths), `assets/db/dayN/phoenix.db` (per-day Phoenix DBs)
- [docs](docs): CLI reference, advanced features, run artifacts, methodology, and task authoring notes
- [reports](reports): benchmark reports and notes
- [tests](tests): pytest coverage for CLI, parsing, helpers, and process wiring

## Testing

Run `uv sync --extra dev` once first (or `make sync` for every extra). All of these use the `.venv` uv manages:

```bash
make test
make test-fast
make test-cli
./scripts/run/run_tests.sh
```

## Further documentation

- [docs/cli-reference.md](docs/cli-reference.md) — full flag tables, app-reset fairness, repeats caveat, step-budget policy
- [docs/advanced-features.md](docs/advanced-features.md) — starting the mini2 model server, tracing, trajectory recording
- [docs/run-artifacts.md](docs/run-artifacts.md) — run folder contents and metric definitions
- [docs/benchmark-spec.md](docs/benchmark-spec.md), [docs/evaluation-policy.md](docs/evaluation-policy.md), [docs/task-authoring.md](docs/task-authoring.md), [docs/leaderboard-format.md](docs/leaderboard-format.md)
- [reports/day1-run-2026-08-09.md](reports/day1-run-2026-08-09.md) — Day-1 run report
- [reports/day-2.md](reports/day-2.md) — Day-2 run report
- [reports/metrics/](reports/metrics/) — per-day metric JSON/MD and hallucination-control evals
