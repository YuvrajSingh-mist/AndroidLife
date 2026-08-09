# Benchmark Specification

DailyBench300 is a mobile-agent benchmark focused on Droidrun / Mobilerun style execution on a real Android device.

## Scope

- platform: Android phone
- control mode: primarily no-vision, accessibility/state-driven
- model serving: external OpenAI-compatible endpoint
- measurement:
  - end-to-end task latency
  - phone battery and thermal data
  - model token data

## Benchmark unit

One benchmark unit is one task run through the harness into one timestamped run folder under [runs](/Users/yuvrajsingh9886/Desktop/DrainBench300/runs).

## Days, seeds, and manifests — how the 28-day schedule is wired

The 530-task schedule spans **28 days** (`day` field on every dataset row, ~16-23 tasks/day). Three artifacts make any day runnable, inspectable, and extensible:

1. **Runs** — `runs/<batch>/day<N>/<task-id>/...` (each task's run nests under its day, auto-created by `day_subfolder` in `src/DailyBench/task_batch.py`).
2. **Seed manifests** — `scripts/seeding/build_day_seed_manifest.py --day N` generates `seeds/full_tasks/day_<N>/` for **any** day 1..28:
   - `manifest_index.json` — day-level index (task ids, buckets, count)
   - `<task_id>/manifest.json` — per-task fabricated-data spec (resolved prompt, `--var` map, ASK USER fact, seed list, expected end state)
   - `day_<N>_fabricated_data.jsonl` — one meticulous JSON line per task
   - Days 1–6 use **hand-authored specs** (`DAY1..DAY6_TASKS`); days 7–28 are **auto-generated** from the dataset (placeholders resolved from config + `tasks_vars.local.env`, OPEN ones left verbatim, seed marked `auto`). Hand-author a `DAY<N>_TASKS` entry to document a day's fabricated seeds.
3. **Per-day vars** — `scripts/seeding/generate_day_vars.py --all` writes `tasks_vars/day_N.env` for every day (13/13 pinned on day 3 etc.), passed to the runner with `--vars-file`.

## Running any day

```bash
uv run dailybench_tasks.py --serial "$DAILYBENCH_SERIAL" --llm-upstream-base "$LLM_UPSTREAM" \
  --model "$MODEL" --day 3 --vars-file benchmarks/dailyBench-600/tasks_vars/day_3.env
```

`--day N` (any 1..28) is a first-class selector and combines with `--bucket`/`--app`/`--task-id`. See [cli-reference.md](cli-reference.md) and the README.

## Canonical task families

- easy
- medium
- hard-deterministic
- open-ended

The canonical runnable task list lives in [benchmarks/dailyBench-600/tasks_530.md](../benchmarks/dailyBench-600/tasks_530.md) — the deterministic 530-task subset (533 dataset rows: 230 easy / 231 medium / 72 hard = 36 ASK USER / 36 DETERMINISTIC), laid out as a 28-day schedule. The public preview is `benchmarks/dailyBench-600/public.md` (50 curated tasks). `tasks_530.md` is the source of truth: edit it and regenerate `DailyBench_530_v1.json`/`.jsonl` with `scripts/data/export_530_dataset.py`.

## Days, seeds, and manifests

The benchmark is organised day-by-day so it is fully inspectable and extensible:

- **Run any day** with the batch runner: `uv run dailybench_tasks.py --day 3 ...` (a `--day N` selector for any day 1..28, see [README](../README.md#run-a-day-530)). Runs land under `runs/<batch>/day<N>/...`.
- **Seed manifests** are generated per day under `seeds/full_tasks/day_<N>/`:
  - `manifest_index.json` — day-level index (task ids in schedule order, bucket counts)
  - `<task_id>/manifest.json` — per-task fabricated-data manifest (resolved prompt, `--var` map, ASK USER fact, required seed data + status, expected end state, config keys used)
  - `day_<N>_fabricated_data.jsonl` — one meticulous JSON line per task
  - `<task_id>/seed_files/` — literal seed-file templates + `DEVICE_PATHS.md` (on-device paths)
- **Days 1–6** have hand-authored specs (`DAY1..6_TASKS` in `scripts/seeding/build_day_seed_manifest.py`) that document each task's exact fabricated data.
- **Days 7–28** are auto-generated per-task from the dataset (same manifest shape): each task gets an app-appropriate seed entry (web / needs_ui / needs_seed / present / sanity / creation) and a resolved-vars map. To document a specific day's fabricated seeds by hand, add a `DAY<N>_TASKS` block to `scripts/seeding/build_day_seed_manifest.py` and wire it into `build_day()` — the generator then uses your spec instead of the auto one.
- Rebuild all days at once: `for d in $(seq 1 28); do uv run python scripts/seeding/build_day_seed_manifest.py --day $d; done`.

This keeps the fabricated data, the run schedule, and the per-day vars (`tasks_vars/day_N.env`) all derived from `tasks_530.md` + `config/user.yaml`, so nothing is hidden in ad-hoc files.

## Required run artifacts

Each valid run should contain:

- `meta.json`
- `preflight.json`
- `postflight.json`
- `samples.ndjson`
- `run_metrics.json`
- `agent.log.txt`
- `output.txt`
- `output.json`

Optional artifacts:

- `screen.mp4`
- `llm_proxy_metrics.jsonl`
- `llm_metrics.json`

## Required summary metrics

- `elapsed_seconds`
- `command_exit_code`
- `llm_prompt_tokens_sum`
- `llm_completion_tokens_sum`
- `llm_total_tokens_sum`

## Action-budget policy

- all benchmark tasks use the same default `50`-step action budget
- this fixed cap is part of the benchmark definition and is meant to preserve fairness across buckets

## Evaluation philosophy

- deterministic tasks should be scored by explicit success/failure evidence
- open-ended tasks should be scored separately with rubric-based evaluation
- benchmark maintenance must preserve comparability across runs and dates
