# DailyBench300 — Benchmark Stats & Distribution Report

**What it is:** a 28-day, 530-task mobile-agent benchmark that measures not just *can the agent do the task?* but *what does doing it cost a real phone* — dollars, battery, and heat — across cloud and local models, on everyday tasks in apps people actually use.

**Source of truth:** `benchmarks/dailyBench-600/tasks_530.md` → `DailyBench_530_v1.json` (exported by `scripts/export_530_dataset.py`). All figures below are computed from that JSON.

---

## 1. Snapshot

| Metric | Value |
|---|---|
| Dataset rows | **533** |
| Schedule | 28 days (fixed, one-time-shuffled, reused for every model) |
| Tasks/day | 16–23 (~19 avg) |
| Difficulty split | 230 easy / 231 medium / 72 hard |
| Hard split | 36 ASK USER / 36 DETERMINISTIC |
| Max points | 1,283 (230×1 + 231×3 + 72×5) |
| Apps covered | 21 |
| Cross-app required | 178 / 533 (33.4%) |
| Uniqueness | 533 unique ids · 0 duplicate prompts · 0 empty prompts |

## 2. Distribution by difficulty

| bucket | count | share | points | subgoal (clause) range |
|---|---|---|---|---|
| easy | 230 | 43.1% | 230 | 1–3 (dominant 2) |
| medium | 231 | 43.3% | 693 | 3–8 (dominant 4) |
| hard | 72 | 13.5% | 360 | 1–11 (dominant 5) |

## 3. Hard split — ASK USER vs DETERMINISTIC

- **36 ASK USER** — each hides one load-bearing fact the agent must actively request (all 36 carry an `ask_user_fact`; a single skipped `ask_user` fails the task). 32 have 0 placeholders, 4 have 1–3.
- **36 DETERMINISTIC** — all data on-device, ADB-verifiable end state.
- Interleaved across days: **19/28 days mix both**, 4 days are all-ASK-USER, 5 days are all-DETERMINISTIC.

## 4. Subgoal (clause) distribution

Rough subgoal count = prompt clauses (split on commas/em-dashes/`and`, ignoring app prefixes and parentheticals).

| bucket | clause-count distribution |
|---|---|
| easy | 1×16, 2×197, 3×17 |
| medium | 3×13, 4×157, 5×53, 6×5, 7×1, 8×2 |
| hard | 1×1, 2×3, 3×7, 4×9, 5×35, 6×13, 7×2, 8×1, 11×1 |

## 5. Cross-app requirement

| bucket | cross-app | total | share |
|---|---|---|---|
| medium | 114 | 231 | 49.4% |
| hard | 64 | 72 | 88.9% |
| easy | 0 | 230 | 0% |
| **all** | **178** | **533** | **33.4%** |

## 6. Per-day distribution

| Day | tasks | easy/med/hard | ASK/DET | distinct apps |
|---|---|---|---|---|
| D01 | 22 | 9/10/3 | 3/0 | 11 |
| D02 | 18 | 7/8/3 | 2/1 | 10 |
| D03 | 21 | 9/9/3 | 1/2 | 11 |
| D04 | 19 | 9/7/3 | 0/3 | 10 |
| D05 | 21 | 9/9/3 | 3/0 | 10 |
| D06 | 17 | 7/7/3 | 1/2 | 9 |
| D07 | 17 | 7/7/3 | 1/2 | 12 |
| D08 | 18 | 8/7/3 | 1/2 | 11 |
| D09 | 19 | 8/8/3 | 2/1 | 10 |
| D10 | 20 | 7/10/3 | 0/3 | 11 |
| D11 | 19 | 9/7/3 | 1/2 | 12 |
| D12 | 19 | 9/7/3 | 0/3 | 11 |
| D13 | 23 | 9/11/3 | 2/1 | 13 |
| D14 | 19 | 9/7/3 | 0/3 | 11 |
| D15 | 20 | 9/8/3 | 2/1 | 10 |
| D16 | 18 | 7/8/3 | 0/3 | 12 |
| D17 | 17 | 7/8/2 | 1/1 | 10 |
| D18 | 20 | 7/11/2 | 2/0 | 9 |
| D19 | 18 | 8/8/2 | 2/0 | 10 |
| D20 | 18 | 8/8/2 | 1/1 | 10 |
| D21 | 18 | 8/8/2 | 0/2 | 12 |
| D22 | 19 | 9/8/2 | 1/1 | 11 |
| D23 | 20 | 8/10/2 | 1/1 | 10 |
| D24 | 16 | 7/7/2 | 2/0 | 9 |
| D25 | 18 | 9/7/2 | 2/0 | 10 |
| D26 | 21 | 10/9/2 | 1/1 | 10 |
| D27 | 19 | 8/9/2 | 2/0 | 10 |
| D28 | 19 | 9/8/2 | 2/0 | 12 |

**Schedule notes:** days 1–16 carry 3 hard tasks; days 17–28 carry 2. Every day spans 9–13 distinct apps (min 7, max 11 in the original design; observed 9–13) — no app is on screen every day.

## 7. Per-app coverage

| App | total | easy/med/hard |
|---|---|---|
| Telegram | 71 | 11/36/24 |
| Notes | 71 | 6/44/21 |
| Obsidian | 71 | 7/44/20 |
| Chrome | 49 | 22/21/6 |
| Calendar | 47 | 12/22/13 |
| Clock | 32 | 13/14/5 |
| Files | 30 | 11/13/6 |
| Google Search | 29 | 11/10/8 |
| Gallery | 29 | 12/11/6 |
| Contacts | 27 | 9/11/7 |
| Google Maps | 27 | 10/12/5 |
| Google Drive | 27 | 12/12/3 |
| Gmail | 26 | 9/10/7 |
| YouTube | 26 | 11/10/5 |
| Settings | 26 | 10/10/6 |
| Calculator | 26 | 11/12/3 |
| Camera | 25 | 11/10/4 |
| Phone | 25 | 11/11/3 |
| Google Photos | 25 | 11/12/2 |
| Music | 24 | 9/10/5 |
| Messages | 23 | 11/10/2 |

## 8. Placeholders

44 unique `[placeholders]` in prompts (contact, topic, time, amount, note title, product, song, route, city, sender, meeting title, etc.), resolved from `tasks_vars.local.env` / per-day `tasks_vars/day_N.env` at run time.

## 9. Model / measurement contract

- **Models:** agent = `~deepseek/deepseek-v4-flash-latest` (OpenRouter) · ask_user/judge = `gpt-5.4-mini` · temp 0.0 · top-p 0.95.
- **Core metrics:** success rate, cost (USD), latency, battery/energy drain, thermal drift — captured per step on-device (`dumpsys battery`, `dumpsys thermalservice`), independent of the model under test.
- **Action budget:** 50 steps default (fixed cap, part of the benchmark definition; fairness across buckets).
- **Reference device:** OnePlus CPH2423 (Android 15, non-rooted), wired or wireless ADB; host-side `scrcpy --record` for video artifacts.

## Related reports

- Run reports: `reports/day1-run.md`, `reports/day2-run.md`, `reports/day3-run.md`
- Metric JSON/MD: `reports/metrics/day2-metrics.md`, `reports/metrics/day3-metrics.md`, `hallucination-eval-day2.md`
- Full pipeline spec: `docs/benchmark-spec.md`, `docs/leaderboard-format.md`, `docs/evaluation-policy.md`
- Dataset layout: `benchmarks/dailyBench-600/tasks_530.md` (canonical) + `public.md` (50-task preview)
