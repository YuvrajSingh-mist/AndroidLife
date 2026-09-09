# AndroidLife

Real-phone Android agent benchmark: everyday tasks on a live device, scoring **success** and
**phone cost** (battery, thermal, dollars, steps). Agents use
[MobileRun](https://docs.mobilerun.ai/framework/sdk) (Droidrun) over ADB.

Evaluates **open-weight** models (API today; **on-device SLMs** as the long-term focus). Same
harness for OpenRouter, a local OpenAI-compatible server, or on-device runtime.

Live site: [yuvrajsingh-mist.github.io/AndroidLife](https://yuvrajsingh-mist.github.io/AndroidLife/) ·
Code: [github.com/YuvrajSingh-mist/AndroidLife](https://github.com/YuvrajSingh-mist/AndroidLife) ·
Public artifacts: [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public) ·
530 corpus: [`YuvrajSingh9886/androidlife-530`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-530)

## Two tiers

- **60-task public benchmark** — fully run on-device (OnePlus CPH2423); each task has trajectory,
  screenshots/GIF, telemetry, manual-audit verdict. Source:
  `benchmarks/androidlife-600/AndroidLife_public_v2.json` (+ `public.md`, `public_vars.local.env`,
  `multiturn_kb_public.json`).

- **530-task dataset\*** — full corpus (216 easy / 242 medium / 72 hard) on a fixed **28-day**
  schedule across **31 apps** (distinct Android apps in the corpus — Telegram, Notes, Chrome,
  Gmail, …; see [docs/benchmark-spec.md](docs/benchmark-spec.md#app-coverage--sector-distribution)).
  The 28 days are the *dataset shape* (≈10 apps/day like a real user), **not** run length; actual
  runs are short sessions. Public 60 is sampled from this set. \*Only **5 of 28** days have been
  fully run on-device so far; the rest roll out on the same harness. Source:
  `AndroidLife_530_v1.json` (+ `tasks_530.md`).

## Quick start

```bash
uv run python scripts/setup.py            # or: make setup
cp .env.example .env                      # OPENROUTER_API_KEY, OPENAI_API_KEY for ask_user
```

Needs `adb`, `scrcpy`, Python 3.11–3.13 (`uv`-managed).

### Reset + seed (before every public run)

Full command sequence: **[docs/device-reset-and-seed.md](docs/device-reset-and-seed.md)**.

```bash
S=100.108.15.119:5555   # Tailscale serial
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --apply
uv run python scripts/seeding/seed_data.py --serial "$S" --day 1   # also --day 2, --day 3
uv run python scripts/seeding/enrich_public_notes.py --serial "$S"
uv run python scripts/seeding/fabricate_public_pdfs.py --serial "$S"
# then tomorrow Team Sync/Mentor + verify — see device-reset-and-seed.md
```

### Public 60-task batch (detached)

```bash
RUN_TS=$(date +%Y%m%d-%H%M%S)
# Phoenix first (per-run DB under assets/db/public/$RUN_TS/), then:
nohup uv run androidlife_tasks.py \
  --dataset benchmarks/androidlife-600/AndroidLife_public_v2.json \
  --source public.md --all --serial 100.108.15.119:5555 \
  --llm-upstream-base https://openrouter.ai/api --model <model> \
  --ask-user-model gpt-5.4-mini --temperature 0.0 --steps 60 --task-timeout 2400 \
  --save-trajectory action --vars-file benchmarks/androidlife-600/public_vars.local.env \
  --ask-user-kb benchmarks/androidlife-600/multiturn_kb_public.json \
  --phoenix-url http://localhost:6006 --phoenix-project androidlife-public \
  --run-root "assets/runs/public/$RUN_TS" \
  < /dev/null > "assets/runs/public/batch-$RUN_TS.log" 2>&1 &
```

(`dailybench_tasks.py` is still a supported alias — see [docs/naming.md](docs/naming.md).)
Prefer `Popen(..., start_new_session=True, stdin=DEVNULL)` over bare `nohup` when launching from
Cursor. Resume: same `--run-root` + `--resume-from <task_id>`. Add `--vision` for VISION mode.
Flags: [docs/cli-reference.md](docs/cli-reference.md).

### Single day (530 schedule)

```bash
uv run python scripts/run/start_phoenix.py --day 3
uv run androidlife_tasks.py --serial "$S" --llm-upstream-base https://openrouter.ai/api \
  --model "$MODEL" --day 3 --vars-file benchmarks/androidlife-600/tasks_vars/day_3.env
```

### Results

```bash
uv run scripts/eval/androidlife_report.py --runs assets/runs/public/<RUN_TS>
uv run scripts/eval/audit_kb_queries.py --runs 'assets/runs/public/<RUN_TS>/*' --source public.md --interactive
```
### Website (local)

```bash
cd website && npx --yes live-server --port=8000 --host=127.0.0.1
# or: python3 -m http.server 8000
```

Hard-refresh after HTML/JS/CSS edits. Rebuild `site_data.json` with
`node website/tools/build_site_data.mjs` if the task corpus changed.

## Layout

| Path | Role |
|---|---|
| `androidlife_runner.py` / `androidlife_tasks.py` | CLI entrypoints (`dailybench_*` aliases) |
| `src/androidlife/` | Harness (compat shim: `src/DailyBench/`) |
| `benchmarks/androidlife-600/` | 530 + public datasets |
| `scripts/seeding/` | Reset / seed / verify |
| `assets/` | Runs, seeds, Phoenix DBs (gitignored) |
| `website/` | GitHub Pages site |
| `reports/` | Audits + metrics |

## Docs

- [docs/device-reset-and-seed.md](docs/device-reset-and-seed.md) — **reset + seed commands**
- [docs/getting-started.md](docs/getting-started.md) — mental model + artifact paths
- [docs/cli-reference.md](docs/cli-reference.md) — flags, detach/resume, model notes
- [docs/benchmark-spec.md](docs/benchmark-spec.md) — 530 corpus / 31 apps / schedule
- [docs/benchmark-spec-public.md](docs/benchmark-spec-public.md) — public 60
- [docs/evaluation-policy.md](docs/evaluation-policy.md) — grading
- [docs/app-usage-grounding.md](docs/app-usage-grounding.md) — why ~10 apps/day
- [docs/pre-run-checklist.md](docs/pre-run-checklist.md) — UI/cloud seeds ADB cannot plant
- [docs/HANDOFF.md](docs/HANDOFF.md) — current run state (maintainers)

## Tests

```bash
make sync && make test
```
