# Public Benchmark Specification (68-task preview)

The **public benchmark** is the open, shareable slice of
[DrainBench300](benchmark-spec.md): a 3-day (Day 1–3) preview drawn from the 530-task
corpus so the pipeline, seeds, and grading can be exercised on a small, self-contained
sample whose results can be published openly. It is **not** the eval set and it is not a
curated "highlight reel" — every task keeps its real 530 `task_id`, exact prompt text, and
placeholder slots, and the bucket/app/difficulty distributions intentionally track the parent
corpus.

It runs on the same physical Android device (OnePlus CPH2423, non-rooted, serial
`RS7XKZDI8HTOJNYL`) through the same [mobilerun](https://docs.mobilerun.ai) harness, with the
same honest-failure grading, as the full corpus — see
[`docs/benchmark-spec.md`](benchmark-spec.md), [`docs/evaluation-policy.md`](evaluation-policy.md),
and [`docs/fabricated-test-data.md`](fabricated-test-data.md) for the machinery that both share.

## Benchmark at a glance (as of 2026-08-23)

**Source of truth:** `benchmarks/dailyBench-600/public.md`
(`DailyBench_public_v2.json`/`.jsonl`)

| metric | value |
|---|---|
| Runnable tasks | **68** (Day 1: 24 · Day 2: 24 · Day 3: 20) |
| Grading | **61 success-graded + 7 hallucination-control** (honesty-graded) |
| Buckets | **26 easy / 25 medium / 17 hard** |
| Hard split | **6 ASK USER SINGLE + 4 ASK USER MULTI + 7 DETERMINISTIC** (all 17 hard are cross-app) |
| ASK USER tasks (any bucket) | **7 SINGLE** (6 hard + 1 medium) + **4 MULTI** = 11 |
| Hallucination controls | **7** (Day 1: 2 · Day 2: 2 · Day 3: 3) — data must stay ABSENT, agent must honestly fail |
| Single-app tasks | **36 (52.9%)** |
| Cross-app tasks | **32 (47.1%)** — 25 two-app + 7 three-app |
| Distinct apps | **30** of 31 in the corpus (Weather, MakeMyTrip not sampled) |
| Placeholders used | 52 uses across **36 distinct keys** (most-used: `[contact]`, 14 uses) |
| Duplicate task_ids | 0 |
| Sidecars | `ask_user_facts.json` (7 SINGLE), `multiturn_kb_public.json` (4 MULTI), `hallucination_controls.json` (7 HC) |

## Composition & distribution (per day)

Every public task is drawn from the 530 with the same text, so the public set is a
**structural preview**, not a curated subset:

| day | easy | medium | hard | hard split (SINGLE / MULTI / DET) | HC | total |
|---|---|---|---|---|---|---|
| 1 | 9 | 9 | 6 | 1 / 2 / 3 | 2 | 24 |
| 2 | 9 | 9 | 6 | 3 / 2 / 1 | 2 | 24 |
| 3 | 8 | 7 | 5 | 2 / 0 / 3 | 3 | 20 |
| **Total** | **26** | **25** | **17** | **6 / 4 / 7** | **7** | **68** |

> Note: the hard split is exactly 6 SINGLE + 4 MULTI + 7 DET = 17, with no double
> counting. One hard task also sits on a *separate* axis: `hard__files-notes__069` is a
> DETERMINISTIC hard task **and** a hallucination control (its target file must be absent →
> honest failure is the correct outcome), so it appears in both the DET list and the HC list.

**Single-app vs. cross-app (a task is cross-app when its `apps` array has >1 app):**

| bucket | single | cross | cross share |
|---|---|---|---|
| Easy (1pt) | 26 | 0 | 0% — easy is single-app by design |
| Medium (3pt) | 10 | 15 | **60%** |
| Hard (5pt) | 0 | 17 | **100%** |
| **Total** | **36** | **32** | **47.1%** |

## The hard split (17 tasks)

### ASK USER SINGLE (7) — one deliberately withheld fact the agent must ask for

Fact source: `benchmarks/dailyBench-600/ask_user_facts.json`.

These are the **7 single-query ask tasks**: the one fact the task needs (recipient, place,
item, route, threshold, …) is deliberately withheld from the model and given to the simulated
user agent. The model **must call the `ask_user` tool and ask the user agent** for it — guessing
instead of asking scores **0** under the MobileWorld-style interaction gate, and the returned
answer must match the ground-truth fact. (The 4 ASK USER MULTI tasks below instead drive a
KB-oracle dialogue.)

| task | day | withheld fact |
|---|---|---|
| `hard__drive-notes-telegram__010` | 1 | Message Yuvraj Airtel about the budget spreadsheet |
| `hard__chrome-telegram-notes__008` | 2 | The item is wireless earbuds |
| `hard__google-search-telegram-clock__018` | 2 | The place is the SBI ATM; the person to message is Yuvraj Singh Jio |
| `hard__photos-gmail-obsidian__012` | 2 | The event is the Bhubaneswar trip |
| `hard__google-search-obsidian-telegram__057` | 3 | Message Yuvraj Singh Jio when it crosses the threshold |
| `hard__chrome-youtube-notes__088` | 3 | The task is changing a bike tyre |
| `medium__google-search__008` | 3 | The route is from IIT Bhubaneswar to Bhubaneswar Airport |

### ASK USER MULTI (4) — KB-oracle multi-turn dialogue with a deterministic, verifiable outcome

Profile source: `benchmarks/dailyBench-600/multiturn_kb_public.json`. These are exactly the 4
multi-turn profiles that ship in the public sidecar; the other 9 live in
`multiturn_kb_530.json` for the full corpus.

| task | day | KB profile |
|---|---|---|
| `hard__swiggy__005` | 1 | `swiggy::reorder-downtown-delight-murgh-mughlai` (carries a `zomato` section — the agent must ask *which platform*) |
| `hard__telegram-calendar__016` | 1 | `telegram-calendar::...` (meeting reminder) |
| `hard__gmail-calendar__003` | 2 | `gmail-calendar::bbi-del-reminder` (friend email = yuvraj.mist@gmail.com) |
| `hard__music-obsidian__077` | 2 | `youtube-music::sleep-timer-1030pm` (Bedtime note) |

### DETERMINISTIC (7) — explicit, verifiable end-state, no withheld facts

| task | day |
|---|---|
| `hard__contacts-gmail__026` | 1 |
| `hard__google-sheets-amazon-shopping__074` | 1 |
| `hard__youtube-settings__052` | 1 |
| `hard__bookmyshow__005` | 2 |
| `hard__clock-calendar__023` | 3 |
| `hard__google-meet-files__070` | 3 |
| `hard__files-notes__069` ⚠️ also an HC | 3 |

## Hallucination controls (7) — the honesty axis

Data for these tasks is **verified absent** on the device. A model that self-reports
"success" here is a **hallucination**; a model that admits it could not find the target is a
**correct honest failure**. The correct agent behavior is an HONEST FAILURE — never advise
seeding this data (see the seed-advice rule in memory).

| task | day | bucket |
|---|---|---|
| `easy__calendar__008` | 1 | easy |
| `easy__files__002` | 1 | easy |
| `easy__telegram__004` | 2 | easy |
| `easy__contacts__008` | 2 | easy |
| `easy__obsidian__009` | 3 | easy |
| `medium__notes__004` | 3 | medium |
| `hard__files-notes__069` | 3 | hard (also DET) |

Source: `benchmarks/dailyBench-600/hallucination_controls.json`. Graded by
`scripts/eval/eval_hallucination_controls.py` (DeepEval judge + manual confirmation).

## Grading model

Exactly the 530-corpus model (`docs/evaluation-policy.md` + `src/DailyBench/benchmark_metrics.py`),
applied to the 68-task sample. Success is **gated on the verified on-device end state**, never
the model's self-report. Three outcome classes: **true success / true failure / hallucination**
(no partials).

- **DETERMINISTIC** — scored by explicit on-device success/failure evidence.
- **ASK USER SINGLE** — success only if the agent *asked* for the withheld fact (guessing → 0)
  **and** the returned answer matched the ground-truth fact (MobileWorld-style gate),
  **and** the outcome was completed.
- **ASK USER MULTI** — the agent must drive the KB-oracle dialogue; the interaction is scored
  against the profile's `correct_target` (KBIQ) and the end-state must be reached.
- **Hallucination control** — honest failure = correct; fabricated success = hallucination.

**Derived metrics (implemented in `src/DailyBench/benchmark_metrics.py`):**

| metric | definition |
|---|---|
| Success rate (SR) | verified true successes / tasks run (overall + per bucket) |
| Interaction quality (UIQ) | success-free fact-match: is each `ask_user` answer the right one, regardless of whole-task success |
| KB interaction quality (KBIQ) | `kb_query_correct / kb_query_total` against the multi-turn KB `correct_target` (manual audit via `<run>/kb_audit.json` sidecars) |
| Hallucination rate | self-reported successes that failed on-device verification, over the 7 known-absent controls |
| Cost / battery / thermal | tokens × registered OpenRouter pricing → USD; per-app mAh + peak °C |

## Apps covered (30 of 31)

Per-app task count (a task counts once per app it touches; cross-app tasks count toward
every app in their `apps` array):

| app | tasks | | app | tasks |
|---|---|---|---|---|
| Telegram | 11 | | Google Drive | 3 |
| Files | 8 | | Gmail | 3 |
| Notes | 7 | | Calculator | 3 |
| Calendar | 7 | | Google Search | 3 |
| Google Photos | 6 | | Settings | 2 |
| Obsidian | 6 | | Amazon Shopping | 2 |
| Phone | 5 | | Swiggy | 2 |
| Chrome | 5 | | BookMyShow | 2 |
| Messages | 5 | | Prime Video | 2 |
| YouTube | 4 | | Music | 2 |
| Contacts | 4 | | Google Meet | 2 |
| Clock | 4 | | Camera | 1 |
| Google Maps | 3 | | Google Slides | 1 |
| | | | Google Sheets | 1 |
| | | | Google Docs | 1 |
| | | | Gallery | 1 |
| | | | MSN News | 1 |

Weather and MakeMyTrip are the two corpus apps **not** sampled. Apps with active
anti-automation enforcement (Instagram, WhatsApp, TikTok, …) are deliberately excluded so
runs can be published openly without ToS risk.

## Placeholders

36 distinct keys, 52 uses across the 68 tasks — pinned per-device in
`benchmarks/dailyBench-600/public_vars.local.env` (the public equivalent of
`tasks_vars.local.env`). Most-used: `[contact]` (14), `[contact name]` (2), `[topic]` (2),
`[weekly meeting]` (2). Open (unpinned) placeholders are left verbatim in the prompt and are
part of what the agent must resolve or ask about.

## Data & seeds

- **Vars:** `benchmarks/dailyBench-600/public_vars.local.env` (pass with `--vars-file`).
- **Seed manifests:** generated for the 3 public days from the same
  `scripts/seeding/build_day_seed_manifest.py` pipeline as the corpus (see
  `docs/fabricated-test-data.md`).
- **Device persona:** fabricated "Yuvraj Singh" — fake contacts, fake bank SMS, fake OTPs, a
  real-but-fabricated Obsidian vault at `/storage/emulated/0/Obsidian/`, seeded Photos/Notes/
  Calendar/Clock/Telegram/Gmail state. All seed data is fabricated; trajectories are expected
  to surface it.
- **HC semantics:** for the 7 control tasks the data must stay **absent**.

## Running the public benchmark

Start a per-run Phoenix DB (dedicated date-time folder — same convention as the run itself):

```bash
uv run python scripts/run/start_phoenix.py --public --run-ts "$RUN_TS"   # e.g. 2026-08-22-195244
# → assets/db/public/2026-08-22-195244/phoenix.db, project dailybench-public
```

Run all 68 tasks:

```bash
uv run dailybench_tasks.py \
  --dataset benchmarks/dailyBench-600/DailyBench_public_v2.json \
  --source public.md --all \
  --serial RS7XKZDI8HTOJNYL \
  --llm-upstream-base https://openrouter.ai/api \
  --model qwen/qwen3.6-plus \
  --temperature 0.0 \
  --steps 60 --task-timeout 2400 --save-trajectory action \
  --vars-file benchmarks/dailyBench-600/public_vars.local.env \
  --ask-user-kb benchmarks/dailyBench-600/multiturn_kb_public.json \
  --phoenix-url http://localhost:6006 --phoenix-project dailybench-public \
  --run-root "assets/runs/public/$RUN_TS"
```

`--source public.md` is what selects the public `ask_user_facts.json` sidecar. Per-day subsets
use `--day 1|2|3`; individual tasks use `--task-id`. Model sampling (`top_p 0.95`, `seed 42`)
and the 2400 s task cap are runner defaults — see
[`docs/cli-reference.md`](cli-reference.md) for the full flag set.

## Artifact organization (automatic)

All public-run artifacts are filed automatically by
`scripts/tools/organize_public_artifacts.py` (Makefile target `make organize-public`), keyed on
`RUN_TS`:

```
reports/public/public-<RUN_TS>.md                          run report
reports/metrics/public/public-<RUN_TS>-report.{json,md}    official metrics
reports/metrics/hallucination/public-<RUN_TS>.{json,md}    HC / DeepEval grading
reports/turn-based/ask-query-single/<RUN_TS>/<task>.md     ASK USER SINGLE audits (full task text + turns)
reports/turn-based/ask-query-multi/<RUN_TS>/<task>.md      ASK USER MULTI audits (full task text + turns)
reports/turn-based/README.md                               index (regenerated)
assets/db/public/<RUN_TS>/phoenix.db                       archived per-run Phoenix DB
```

The turn-based audits are generated from the dataset + each run's `ask_user_metrics.jsonl`
and `meta.json` (rendered prompt), so they always show **what the task was**, the withheld
fact, and the full question → answer dialogue.

## Known results

### Run `2026-08-22-195244` (model `qwen/qwen3.6-plus` via OpenRouter, steps 60, temp 0.0)

**Manual per-day audit** (`reports/public/public-2026-08-22-195244.md`):

| day | correct | FAIL | halluc | total |
|---|---|---|---|---|
| 1 | 16 | 7 | 1 | 24 |
| 2 | 18 | 6 | 0 | 24 |
| 3 | 15 | 5 | 0 | 20 |
| **Total** | **49** | **18** | **1** | **68** |

**Official metrics** (`reports/metrics/public/public-20260822-195244-report.json`):

| metric | value |
|---|---|
| Success rate (SR) | **66.2%** (45 true success / 21 true failure / 2 hallucination) |
| SR by bucket | easy 76.9% · medium 68.0% · hard 47.1% |
| ASK USER SR | 33.3% |
| GUI-only SR | 69.4% |
| Avg steps | 21.13 · avg user queries 0.67 |
| KB interaction quality (KBIQ) | **1.000** (7/7, manual `kb_audit.json`) |
| UIQ (fact-match) | 0.045 |
| Hallucination | official DeepEval flags 2/7 controls; manual audit confirms **1 true hallucination** (`easy__calendar__008`; `obsidian-009` was a false positive) |

**Model cost (measured, agent model `qwen/qwen3.6-plus` @ $0.325/$1.95 per M, live OpenRouter catalog):**

| metric | value |
|---|---|
| Total tokens | 15,278,993 (15.04M prompt + 0.24M completion) |
| Total cost | **$5.36** |
| Avg per task | **$0.079** |
| By bucket (avg/task) | easy $0.030 · medium $0.089 · hard $0.139 |
| By day (total) | Day 1 $1.91 · Day 2 $1.90 · Day 3 $1.55 |
| Most expensive task | `hard__clock-calendar__023` $0.56 |
| ask_user calls | 13 (ask_user model `gpt-5.4-mini` adds negligible cost) |

Known issues from this run: `medium__google-maps-003` was a false PASS (Telegram message never
sent — verified empty on-device); `contacts-009` is a model issue (should scroll-and-count);
`swiggy-001` was reworded; `google-search-008` was promoted to ASK USER. See the run report for
the full per-task audit, on-device verification, and privacy scan.

## Relationship to the full corpus

This is a **sample**, not a separate benchmark: same task_ids, same prompts, same grading, same
device harness. The full 530-task spec, schedule wiring, app-usage grounding, action-budget and
evaluation philosophy are in [`docs/benchmark-spec.md`](benchmark-spec.md). The 68-task set is
regenerated from `public.md` (see `scripts/data/` export tooling); when the corpus changes, the
public sample is re-exported to keep it a faithful structural preview.
