# scripts/ — Command Index

Scripts are grouped into subfolders by function. All are `uv`-managed entrypoints:
`uv run python scripts/<group>/<name>.py ...` (or `./scripts/<group>/<name>.sh`).
Every script carries a module docstring; run any with `--help` for its exact flags.

## Layout

| Folder | Purpose |
|---|---|
| [`setup.py`](setup.py) | **One-command onboarding**: prerequisites → uv sync → scaffold `.env`/config → device check → manifests → day vars → seed → verify |
| [`run/`](run/) | Entrypoints: run a day / the full suite, pre-flight + test runners |
| [`seeding/`](seeding/) | Baseline data: seed manifests, seeding, device reset, verification |
| [`data/`](data/) | Dataset export (`tasks_530.md` → JSON/JSONL + public preview) |
| [`eval/`](eval/) | Metrics, hallucination eval, e2e check |
| [`tools/`](tools/) | Infrastructure: LLM proxy, device health, provider guard, pricing, app audit |

## ▶️ `run/` — entrypoints

| Script | What it does |
|---|---|
| `run_day.py` | **Main launcher.** Run one day (or all 530) from `tasks_530.md`: resolves the per-day vars file, emits one `dailybench_tasks.py` invocation per task, auto-detects the serial. `--dry-run` prints commands. |
| `smoke_test.sh` | Pre-flight: prerequisites, LLM server + real completion, wired/wireless ADB + device health, one real one-step agent run. Run before any benchmark. |
| `run_tests.sh` | Thin `pytest` wrapper for the test suite. |

## 🚀 `setup.py` — one-command onboarding

Turns the whole "new machine + new phone" flow into a single guided command
(each stage is idempotent and safe to re-run):

```bash
uv run python scripts/setup.py                    # full guided flow
uv run python scripts/setup.py prerequisites deps env config device   # pick stages
uv run python scripts/setup.py manifests day-vars                     # no device needed
uv run python scripts/setup.py seed --day 1       # push fabricated seeds to the phone
uv run python scripts/setup.py verify --day 1     # confirm seeds are on-device
uv run python scripts/setup.py --yes --serial <id> all   # non-interactive
```

Stages: `prerequisites` (adb/scrcpy/uv/python) → `deps` (uv sync) → `env`
(scaffold `.env`) → `config` (scaffold `config/user.yaml` + verify) → `device`
(pick serial + audit the 22 required apps) → `manifests` (per-day seed
manifests) → `day-vars` (per-day `tasks_vars/day_N.env`) → `seed`/`verify`
(mutate/check the phone for a day).

## 🌱 `seeding/` — seeding & provisioning

| Script | What it does |
|---|---|
| `build_day_seed_manifest.py` | Generate the per-day seed manifests (`assets/seeds/manifests/day_N/manifest_index.json`) describing every fabricated seed a day's tasks need. |
| `seed_data.py` | Push fabricated seed files to the device (photos, Obsidian note, invoice PDF, calendar events, SMS, call-log) with correct mtimes. `--day N`. Device-specific paths (Obsidian vault, calendar id, persona email) are auto-detected via `device_paths.py`. |
| `device_paths.py` | Auto-detect device-specific seed values (Obsidian vault dir via `find`, Google-synced calendar id, persona contact email), with `config/user.yaml` overrides (`vault path`, `calendar id`, `contact email`). |
| `reset_phone.py` | Undo agent-created run artifacts (settings, blocked numbers, calendar events, downloads, Obsidian run notes) back to the pre-run baseline. Dry-run by default; `--apply` to act. Prints the manual UI items ADB can't reach. |
| `verify_day1_seeds.py` | Verify seeds are actually on-device (config + device halves) before a run. `--day N`. |
| `verify_config.py` | Verify `config/user.yaml` resolves every placeholder / ASK USER fact / seed key the dataset needs. |
| `generate_day_vars.py` | Generate per-day `tasks_vars/day_N.env` files from the shared `tasks_vars.local.env`. |

## 📊 `data/` — dataset export

| Script | What it does |
|---|---|
| `export_530_dataset.py` | Export `tasks_530.md` → `DailyBench_530_v1.json`/`.jsonl` (the runnable dataset; also the shared `parse()` used by `run_day.py`). |
| `export_530_markdown.py` | Regenerate the markdown schedule (tasks_530.md) from the dataset / template. |
| `export_public_dataset.py` | Build the public preview dataset (`DailyBench_public_v2.json`), merging ask_user facts. |

## 📈 `eval/` — metrics, evaluation & reports

| Script | What it does |
|---|---|
| `dailybench_report.py` | Aggregate a batch of run folders into MobileWorld-style metrics (SR, steps, queries, QIS fact-match, outcome split) → `report.json` + `report.md`. |
| `eval_hallucination_controls.py` | Grade HC tasks with DeepEval DAGMetric (full agent log) into an eval report. |
| `e2e_askuser_phoenix.py` | End-to-end check of the ask_user + Phoenix tracing path. |

## 🛠 `tools/` — infrastructure

| Script | What it does |
|---|---|
| `openai_proxy_logger.py` | Local OpenAI-compatible proxy that forwards to `--llm-upstream-base` and logs every completion to JSONL. Spawned per task by the harness (`src/DailyBench/processes.py`). |
| `device_health_check.py` | Battery/thermal/CPU device health snapshot over ADB. |
| `app_audit.py` | **Device-readiness check**: verifies the connected phone has the 22 apps the benchmark targets (label → candidate packages map, OEM-tolerant). `--json` for machine output. |
| `mobilerun_provider_guard.py` | Guard/validation for the mobilerun provider configuration. |
| `register_openrouter_pricing.py` | Register real OpenRouter pricing into the live per-day Phoenix DB (`assets/db/dayN/phoenix.db`) so Phoenix costs LLM spans. |
| `organize_public_artifacts.py` | **Post-run filing.** Sweep/move public reports, metrics, hallucination evals, turn-based ASK audits into the canonical layout (`make organize-public`). |
| `upload_public_runs_hf.py` | Upload finished `assets/runs/public/<id>/` trees (+ reports) to `YuvrajSingh9886/dailybench500-public`. |
| `publish_trajectories.py` | Publish trajectory media to HF and rewrite site URLs (paired with `website/tools/export_trajectories.mjs`). |
| `compact_phoenix_db.py` | Shrink a Phoenix SQLite DB after a run. |

### Website helpers (not under `scripts/`)

| Script | What it does |
|---|---|
| `website/tools/build_public_traj_from_hf.py` | Build/merge `website/assets/data/trajectories/index.json` for public runs (condensed steps local; GIFs on HF). |
| `website/tools/build_site_data.mjs` | Rebuild `website/assets/data/site_data.json` from the datasets + traj index. |
| `website/tools/export_trajectories.mjs` | Local/full-bench trajectory export (also lists public run roots for parity). |

### Removed legacy one-shots

Former migration helpers (`convert_*`, `remove_*`, `watch_and_upload_public.py`,
`patch_reports_hc_usage.py`, etc.) were deleted — use `upload_public_runs_hf.py`
for HF uploads and live eval scripts for HC/reports.