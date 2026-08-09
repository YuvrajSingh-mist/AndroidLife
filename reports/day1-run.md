# Day 1 — Full-Bench Run Report (deepseek-v4-flash)

**Run root:** `runs/full-bench/2026-08-08-071746/day1/` (22 tasks)
**Schedule source:** `benchmarks/dailyBench-600/tasks_530.md` (Day 1, 22 tasks)
**Date:** 2026-08-08 (UTC; ~6.15 h wall-clock incl. cooldowns)
**Model:** `~deepseek/deepseek-v4-flash-latest` (OpenRouter, `https://openrouter.ai/api`)

> **Model switch context:** Day 1 was originally run with `qwen/qwen3.6-plus`
> (21/22 = 95.5%, archived as `day1-run-qwen.md`). This run re-runs the same Day-1
> schedule with `deepseek-v4-flash` for a consistent model stack with Days 2–3.
> **Final tally: 15/22 (68.2%)** under the combined grading (MobileWorld SR gate +
> success-free fact-match QIS). The drop is driven by the DeepSeek `｜DSML｜` bracket
> bug (`<`/`>` → full-width), which caused step-inflation and 5 step-exhausted
> tasks + 1 mid-task failure.

## Config

| Key | Value |
|---|---|
| Dataset | `DailyBench_530_v1.json` (Day-1 slice via `scripts/run_day.py --day 1`) |
| Model | `~deepseek/deepseek-v4-flash-latest` (OpenRouter, `https://openrouter.ai/api`) |
| Device | OnePlus CPH2423 · serial `RS7XKZDI8HTOJNYL` · Android 15 (non-rooted) |
| Steps / temperature | `--steps 200`, `--temperature 0.0` |
| Sampling | `--top-p 0.95`, `--seed 42` (ask_user inherits temp 0.0 / top-p 0.95 / seed 42) |
| Task timeout | none (step budget is the bound) |
| ask_user model | `gpt-5.4-mini` |
| Seed state | Day-1 seeds verified via `scripts/verify_day1_seeds.py` (ALL PASS) before launch |

## Result summary

| Tier | Total | Pass | Fail | Pass rate |
|---|---|---|---|---|
| Easy | 9 | 8 | 1 | 88.9% |
| Medium | 10 | 6 | 4 | 60.0% |
| Hard | 3 | 1 | 2 | 33.3% |
| **All** | **22** | **15** | **7** | **68.2%** |

**Grading (combined, 2026-08-08):** Success Rate uses the **MobileWorld SR gate** —
an ASK USER (interaction) task only counts as a success if the agent actually
called `ask_user` (guessing gets 0, mirroring q_i = s_i/c_i, c_i = 0 → q_i = 0).
The **QIS** metric uses the success-free fact-match formula (penalizes "never
asked" only in the QIS denominator). So on-device success without asking counts
for SR only when the task is NOT an interaction task.

`ask_user` was actually exercised on **1 of 3** interaction tasks
(`hard__chrome-telegram-notes-008` asked once); `hard__google-search-obsidian-telegram__057`
succeeded on-device but guessed the value instead of asking → **zeroed in SR**
(counts only in the 16/22 on-device tally, not the script SR).

## Metrics (script-generated — `dailybench_report.py`, cooldown-corrected)

| metric | value |
|---|---|
| Success Rate | 68.2% |
| Success Rate (interaction / ASK USER) | 33.3% (3 runs) |
| Success Rate (GUI-only) | 73.7% (19 runs) |
| Average Completion Steps | 74.41 |
| Average User Queries | 0.33 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.333 |
| Elapsed (wall-clock, incl. cooldowns) | 22143 s (6.15 h) |
| Elapsed (TRUE agent running time) | 21933 s (6.09 h) |
| Inter-task cooldown subtracted | 210 s (10 s × 21 gaps) |

**Outcome split (true success / true failure / hallucination):**

| outcome | count | rate |
|---|---|---|
| True success | 15 | 68.2% |
| True failure (incl. honest-fail controls) | 7 | 31.8% |
| **Hallucination** (control self-reported success) | 0 | 0.0% |

Hallucination-control honesty: **0/0** controls (Day 1 has none).

> Note: QIS fact-match = 0.000 because the only ASK USER task that asked
> (`hard__chrome-telegram-notes-008`) returned an answer that did not match the
> ground-truth fact (the fact-match grading), even though the task succeeded.
> Full output: `reports/metrics/day1-metrics.md`.

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 88.9% |
| hard | 33.3% |
| medium | 60.0% |

## DSML analysis — why the failures happened

The 6 failures are **model reliability, not task/seed defects**:

- **5 of 6 hit the 200-step cap** (`Reached max step count of 200 steps`):
  `easy-phone-001`, `hard-calendar-telegram-obsidian-002`, `medium-gallery-001`,
  `medium-gallery-telegram-001`, `medium-obsidian-001`. These burned their budget
  in the DeepSeek `｜DSML｜` loop — malformed `<function_calls>` blocks got skipped
  by the parser, the framework re-injected the "use the `complete` tool" template,
  and the agent kept looping instead of closing out.
- **`medium-camera-001` failed at 51 steps** — flash OFF / HDR AUTO done, but the
  low-light setup was not fully completed (soft/failed closeout).
- **`easy-phone-001`** actually set the "Jazz life" ringtone on-device (goal met)
  but never produced a parseable `complete()` → ran to the step cap and was marked
  failed.
- The 5 step-exhausted tasks consumed ~**197 min / ~13.6M tokens** of the
  6.15 h / ~23.5M token run — the DSML bug is the dominant cost driver.
- **Contrast:** the same schedule with `qwen/qwen3.6-plus` had **2 parse-fails
  total** and scored **21/22 (95.5%)**. The DSML bug is DeepSeek-inherent
  (known upstream; vLLM orphan-invoke + OpenClaw DSML-recovery fixes exist). A
  harness-level DSML normalizer (rewrite `｜DSML｜` → `<`/`>` before parsing) would
  recover most of these steps.

## Per-task results

### Easy (8/9 PASS)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| easy__calendar__001 | ✅ | 61 | 7.7m | 62 | 0.48M | Added location to *Lunch with Maa* |
| easy__camera__001 | ✅ | 11 | 2.3m | 11 | 0.05M | Photo renamed `DeskItem` |
| easy__chrome__001 | ✅ | 6 | 1.2m | 7 | 0.04M | Saved current page offline |
| easy__contacts__001 | ✅ | 6 | 0.9m | 6 | 0.03M | Maa → +91 81302 85662 |
| easy__gallery__001 | ✅ | 83 | 14.6m | 85 | 0.82M | Hid the 11:17 AM photo from main view |
| easy__google-search__001 | ✅ | 7 | 1.3m | 8 | 0.05M | USD→INR 95.14 |
| easy__messages__001 | ✅ | 5 | 1.3m | 6 | 0.03M | Searched "ticket" → seeded SMS found |
| easy__obsidian__001 | ✅ | 10 | 1.6m | 11 | 0.05M | Created "Daily Reflection" note |
| easy__phone__001 | ❌ | 200 | 51.3m | 203 | 3.40M | **DSML step cap:** "Jazz life" ringtone set on-device, but `complete()` never parsed |

### Medium (6/10 PASS)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| medium__calendar__001 | ✅ | 50 | 10.9m | 51 | 0.39M | Weekly_Standup = only recurring event with no attendees |
| medium__chrome__001 | ✅ | 41 | 7.0m | 43 | 0.40M | Summarized article main argument |
| medium__chrome-telegram__001 | ✅ | 70 | 14.7m | 73 | 0.85M | Budget-smartphones top-2 results → Telegram |
| medium__contacts__001 | ✅ | 22 | 4.4m | 23 | 0.17M | Dhruv Kumar (Aug 11) birthday → reminder |
| medium__google-search__001 | ✅ | 21 | 4.3m | 22 | 0.17M | Skimmed 2 best organic results |
| medium__messages__001 | ✅ | 63 | 12.1m | 63 | 0.80M | Unread unanswered Q from Yuvraj Airtel found |
| medium__camera__001 | ❌ | 51 | 14.6m | 53 | 0.42M | Flash OFF / HDR AUTO done; low-light setup not fully completed |
| medium__gallery__001 | ❌ | 200 | 34.2m | 206 | 3.23M | **DSML step cap** |
| medium__gallery-telegram__001 | ❌ | 200 | 60.6m | 208 | 3.61M | **DSML step cap** |
| medium__obsidian__001 | ❌ | 200 | 62.7m | 213 | 3.36M | **DSML step cap** |

### Hard (1/3 PASS — script SR; 2/3 on-device)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| hard__chrome-telegram-notes__008 | ✅ | 117 | 30.2m | 119 | 2.07M | **ASK USER (asked 1×):** Nord Buds 2r — Amazon ₹3,299 vs Flipkart ₹1,799 |
| hard__google-search-obsidian-telegram__057 | ⚠️ on-device pass / SR zeroed | 13 | 3.0m | 16 | 0.09M | **ASK USER (never asked — guessed):** Reliance 1,329.00 INR; succeeded on-device but zeroed by the MobileWorld SR gate (must-ask rule) |
| hard__calendar-telegram-obsidian__002 | ❌ | 200 | 25.0m | 201 | 3.00M | **DSML step cap** (also ASK USER — never asked) |

## Failures (detail)

### 1. Step-exhausted (DSML loop) — 5 tasks
`easy-phone-001`, `hard-calendar-telegram-obsidian-002`, `medium-gallery-001`,
`medium-gallery-telegram-001`, `medium-obsidian-001` all hit the 200-step cap.
Root cause: DeepSeek emits full-width `｜DSML｜` instead of `<`/`>`; mobilerun's
regex/ET parser can't match → blocks skipped → the framework nudges with the
"use `complete`" template → agent repeats → loop. On-device state was often
mostly-complete (ringtone set, note created) but the final `complete()` never
parsed. **Fix:** DSML normalizer at the harness layer, or use qwen for these runs.

### 2. medium__camera__001 — partial completion (51 steps)
Flash OFF / HDR AUTO confirmed, but the full low-light setup wasn't finished;
the agent closed out without fully completing the task.

### 3. hard__google-search-obsidian-telegram__057 — guessed ASK USER value (zeroed in SR)
Task succeeded on-device but the agent never called `ask_user` (guessed the price).
Under the **MobileWorld SR gate** this does NOT count as a script success
(mirroring q_i = s_i/c_i, c_i = 0 → q_i = 0); the miss is also reflected in QIS
(a never-asked interaction task adds one missed-expected-question to the QIS
denominator). On-device it did complete. **Behavioral note:** DeepSeek tended to
skip `ask_user` and guess — worth auditing in the interaction-reliability axis.

## Resource & thermal summary

- Total wall time ≈ **6.15 h** for 22 tasks (vs 3.3 h for the qwen run) — DSML
  step-inflation roughly doubled wall time.
- Token-heavy outliers (all step-exhausted): medium__obsidian__001 (3.36M),
  medium__gallery-telegram__001 (3.61M), medium__gallery__001 (3.23M),
  easy__phone__001 (3.40M), hard__calendar-telegram-obsidian__002 (3.00M).
- Thermal: several tasks hit `thermal_status_max=1` (mild); peak skin ≈ 46 °C.
  No throttle events.

## Recommendations

1. **Model choice (primary):** use `qwen/qwen3.6-plus` for the Day-2 re-run, or
   add a harness-level DSML normalizer so `deepseek-v4-flash` is usable — the DSML
   bug is the single biggest cost/latency/reliability driver on this stack.
2. **Interaction honesty:** audit why DeepSeek guessed instead of calling
   `ask_user` on 2 of 3 interaction tasks; MobileWorld grading correctly catches
   it, but it under-reports real capability.
3. **medium__camera__001** — reword to match device capabilities (no Night-mode
   toggle on this OnePlus/Photo UI) or accept as best-effort with documented
   approximation.
4. **Metrics** live in `reports/metrics/day1-metrics.json` / `day1-metrics.md`
   (script-generated, cooldown-corrected). Archive of the qwen run:
   `reports/day1-run-qwen.md`.
