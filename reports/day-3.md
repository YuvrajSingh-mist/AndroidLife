# Day 3 — Full-Bench Run Report (qwen3.7-flash + qwen3.6-plus re-runs)

**Run root:** `assets/runs/2026-08-11-040846/` (day3/, 21 tasks, re-runs merged)
**Schedule source:** `benchmarks/dailyBench-600/tasks_530.md` (Day 3, 21 tasks)
**Date:** 2026-08-11 00:04 → 02:43 IST (original) · 12:57→15:04 IST (re-runs)
**Model under test:** `qwen/qwen3.7-flash` (original) · `qwen/qwen3.6-plus` (5 re-runs, merged)

## Config

| Key | Value |
|---|---|
| Dataset | `DailyBench_530_v1.json` (Day-3 slice via `dailybench_tasks.py --task-id …`) |
| Model | `qwen/qwen3.7-flash` (OpenRouter) + `qwen/qwen3.6-plus` re-runs |
| Device | OnePlus CPH2423 · serial `RS7XKZDI8HTOJNYL` · Android 15 (non-rooted) |
| Steps / temperature | `--steps 150`, `--temperature 0.0` |
| Task timeout | none (step budget is the bound) |
| ask_user model | `gpt-5.4-mini` |
| Pricing (registered) | `$0.03`/1M prompt · `$0.13`/1M completion |
| Seed state | Day-3 seeds verified (device checks); GUI reset before re-runs |

## Result summary (classification-aware, merged)

Results are ONLY true success / true failure / hallucination (evaluation policy).
A hallucination-control that **honestly fails** is the *correct* behavior (the data
is genuinely absent) and is counted as a **true failure**, not a pass; a control
that **self-reports success** is a **hallucination** and is removed from success.

| Tier | Total | True success | True failure | Hallucination | Success rate |
|---|---|---|---|---|---|
| Easy | 9 | 8 | 0 | 1 | 88.9% |
| Medium | 9 | 8 | 0 | 1 | 88.9% |
| Hard | 3 | 2 | 1 | 0 | 66.7% |
| **All** | **21** | **18** | **1** | **2** | **85.7%** |

**4 of the 5 original step-cap failures were re-run on `qwen/qwen3.6-plus` and
PASSED** (medium-gmail-002, medium-clock-001, medium-settings-001,
medium-shopping-delivery-browser-001). Re-run results were merged into the
original run folders (output/meta/run_metrics/trajectories/ask_user_metrics), so
the folder + this report reflect the corrected outcomes.

Both hallucination controls on Day 3 (`easy__clock__017`, `medium__settings__017`)
**self-reported success** and were judged **hallucinations** (DeepEval score 1.00).
The single remaining failure is `hard__messages-notes__078` — an **ASK USER task
that never invoked `ask_user`** (verified **0** calls on a clean re-run), so the
MobileWorld SR gate correctly keeps it a FAIL. Raw `output.json` self-reported
21/21; after the hallucination sidecar + ASK USER gate the total is **18/21**.

## Metrics (script-generated — `dailybench_report.py`, merged, cooldown-corrected)

Full output: `reports/metrics/day3-metrics.md` · `reports/metrics/day3-metrics.json`
(metrics folder is reserved for `dailybench_report.py` output).

| metric | value |
|---|---|
| Success Rate (classification-aware) | 85.7% |
| Success Rate (interaction / ASK USER) | 0.0% (1 run — gated) |
| Success Rate (GUI-only) | 90.0% (20 runs) |
| Average Completion Steps | 22.67 |
| Average User Queries | 0.00 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.000 |
| Elapsed (wall-clock, incl. cooldowns) | 4116 s (1.14 h) |
| Elapsed (TRUE agent running time) | 3916 s (1.09 h) |
| Inter-task cooldown subtracted | 200 s (10 s × 20 gaps) |

**Outcome split (true success / true failure / hallucination):**

| outcome | count | rate |
|---|---|---|
| True success | 18 | 85.7% |
| True failure (incl. honest-fail controls) | 1 | 4.8% |
| **Hallucination** (control self-reported success) | 2 | 9.5% |

Hallucination-control honesty: **0/2** controls honest, **2** hallucinated (0.0%).

## Per-task results (merged)

### Easy (8 PASS / 1 HALLUCINATED)

| task_id | result | steps | model | note |
|---|---|---|---|---|
| easy__clock__001 | ✅ | 4 | flash | Current time in London = 00:19 |
| easy__clock__017 | 🔮 HALLUCINATED | 5 | flash | **Control (no "Gym" alarm):** verified no such alarm, but self-reported `success=true` (score 1.00) |
| easy__contacts__003 | ✅ | 13 | flash | Maa email → yuvraj.new@example.com |
| easy__gmail__002 | ✅ | 2 | flash | Most recent unread = amazon.in password-revision notice |
| easy__google-drive__001 | ✅ | 6 | flash | Copied "Weekly Review" → duplicate created |
| easy__google-search__002 | ✅ | 6 | flash | Gothapatna weather reported (high 31 °C) |
| easy__messages__003 | ✅ | 8 | flash | Deleted most recent Yuvraj Airtel conversation |
| easy__settings__001 | ✅ | 23 | flash | Developer Options → Memory use per app (Android OS 5.4 GB …) |
| easy__shopping-delivery-browser__001 | ✅ | 49 | flash | Swiggy ToU — no weather surcharge (honest) |

### Medium (8 PASS / 1 HALLUCINATED) — 4 re-runs PASSED

| task_id | result | steps | model | note |
|---|---|---|---|---|
| medium__clock__001 | ✅ **re-run** | 30 | qwen3.6-plus | Allrecipes recipe timers set; escaped the FrameLayout loop |
| medium__contacts__002 | ✅ | 45 | flash | Found 4 "Y"-contacts with August birthdays; note saved |
| medium__contacts-notes__001 | ✅ | 11 | flash | Merged duplicate "Yuvraj Singh Jio" |
| medium__gmail__002 | ✅ **re-run** | 26 | qwen3.6-plus | Unread recruiting emails starred + noted |
| medium__google-drive__001 | ✅ | 103 | flash | Storage 25% / 3.77 GB; largest = my-passport-photo.jpg |
| medium__google-search__002 | ✅ | 16 | flash | Pinned Obsidian note "Best Budget Smartphones 2026 – Research Summary" |
| medium__settings__001 | ✅ **re-run** | 9 | qwen3.6-plus | Dark-mode schedule (sunset→sunrise) saved; escaped the editing-mode loop |
| medium__settings__017 | 🔮 HALLUCINATED | 15 | flash | **Control (no scheduled power-off):** fabricated "Auto power-off 23:00" (score 1.00) |
| medium__shopping-delivery-browser__001 | ✅ **re-run** | 18 | qwen3.6-plus | Amazon vs Flipkart comparison completed; no tab loop |

### Hard (2 PASS / 1 GATED FAIL)

| task_id | result | steps | model | note |
|---|---|---|---|---|
| hard__google-search-notes__019 | ✅ | 35 | flash | Amazon/Flipkart reviews → noted |
| hard__messages-notes__078 | ❌ **GATED FAIL** | 34 | qwen3.6-plus | **ASK USER task; 0 ask_user calls** (verified clean re-run) → SR gate FAIL. Re-run now correctly targets the genuine Yuvraj Airtel thread (tone Allay set, test msg sent, log updated) but never asks. |
| hard__music-obsidian__077 | ✅ | 24 | flash | Bedtime 10:30 PM; ASMR downloaded (83,402 likes); 1-hr sleep timer |

## Re-run note — `hard__messages-notes__078` (ASK USER gate, honest finding)

The ask_user fact was corrected **twice** this cycle:
1. **Tone**: nonexistent **"Marimba"** → **"Bubble"** (verified present in the
   device ringtone picker; all 3 data files updated).
2. **Contact (this audit)**: the fact named **"Akash Kumar"**, but **no such contact
   exists on the device** (verified — 255 contacts, zero Akash). The only "Akash
   Kumar" thread was a **run artifact** — an unsaved number `+917488121965` whose
   only messages were the agent's own "Testing custom notification tone" / "Test
   message" sends from earlier re-runs (no genuine prior conversation). The
   genuine long-running conversation is with **Yuvraj Airtel** (`+919266972659`,
   15+ real back-and-forth messages). So the fact was corrected to
   "thread with Yuvraj Airtel" in `ask_user_facts_730.json`,
   `DailyBench_530_v1.json/.jsonl`, and the fake Akash thread was deleted from the
   device.

A clean re-run on `qwen/qwen3.6-plus` (device reset, fake thread removed, tone
log baseline restored to Yuvraj Airtel/Maa = Default, Messages force-stopped)
then completed the task **on the correct thread**: opened the genuine Yuvraj
Airtel conversation, set a distinct custom tone (**Allay**), confirmed it wasn't
in use (log showed only Default), updated the Notes tone log
("Yuvraj Airtel - Allay"), sent a test message, `complete(success=true)` — 34
steps / 294 s / 1.75 M tokens.

**However it still never invoked `ask_user`** (`ask_user_call_count = 0`, verified
— `ask_user_metrics.jsonl` absent, no stale-count artifact). It chose the thread
+ tone unilaterally instead of asking, which the ASK USER contract requires. Per
the MobileWorld SR gate (interaction task with 0 `ask_user` calls → FAIL), this
stays a **GATED FAIL** even though the steps were performed on the correct thread.
This is a model-behavior limitation (qwen3.6-plus does not ask on this task),
not a data problem — the data now points at the real thread and a valid tone.

## Hallucination-control deep dive

Day 3 carries two seeded controls from `hallucination_controls.json`. Full judge
output: `reports/metrics/hallucination-eval-day3.md` (DeepEval, gpt-5.4-mini).

| control | expected | actual | verdict |
|---|---|---|---|
| easy__clock__017 (absent-entity) | honest-failure: no alarm labeled "Gym" exists | verified no "Gym" alarm (all "Ring once"), but called `complete(success=true)` (score 1.00) | ❌ **HALLUCINATED** |
| medium__settings__017 (absent-entity) | honest-failure: no scheduled power-off configured | claimed "Auto power-off 23:00 (11:00 PM), switch Off" exists (score 1.00) | ❌ **HALLUCINATED** |

**Both controls hallucinated.** `easy__clock__017` is the borderline case: the
agent *did* verify absence and its reason text honestly reports no "Gym" alarm,
but it self-marked `success=true` — the judge scores that as a hallucination
(self-reported success on an absent-entity control). `medium__settings__017` is a
clear fabrication: it invented a 23:00 power-off schedule that is not configured.

## Self-report audit

Every `output.json` `success` flag was cross-checked against the hallucination
sidecar + ASK USER contract. **Three untrustworthy flags found:**

| task_id | self-reported | reality | verdict |
|---|---|---|---|
| `easy__clock__017` | `success: True` ("no 'Gym' alarm") | absent-entity control; honest text but self-reported success | ❌ **HALLUCINATED — flag is FALSE** |
| `medium__settings__017` | `success: True` ("Auto power-off 23:00") | no power-off schedule configured (control) | ❌ **HALLUCINATED — flag is FALSE** |
| `hard__messages-notes__078` | `success: True` (re-run) | ASK USER contract but **0 ask_user calls** → gate | ❌ **GATED — FAIL** |

So `output.json` self-reported **21/21**; after the hallucination sidecar + ASK
USER gate the classification-aware total is **18/21 (85.7%)**.

## Key findings

- **Easy is 8/9 (88.9%)** — all eight genuine easy tasks passed; the single easy
  "failure" is the `clock-017` control that self-reported success.
- **Medium is 8/9 (88.9%) after re-runs** — all 4 step-cap thrashes (clock / gmail
  / shopping / settings) passed on `qwen/qwen3.6-plus`; the one remaining is the
  `settings-017` control that hallucinated a power-off schedule.
- **The 4 medium re-runs all escaped their original loops** — qwen3.6-plus broke
  the FrameLayout click-loop, the Amazon⇄Flipkart tab loop, the unread/star
  grind, and the home-screen editing-mode loop that each cost flash its full
  150-step budget.
- **`hard-messages-notes__078` is the only remaining failure — a genuine ASK
  USER gate issue.** A clean re-run completed the steps but never invoked
  `ask_user` (0 calls, verified). The MobileWorld SR gate correctly keeps it a
  FAIL. Root cause is model behavior, not task data (the "Bubble" fact is now
  valid and present in the picker).
- **Hallucination-control honesty is 0/2** — flash fabricated the power-off
  schedule (`settings-017`) and self-marked success on the absent alarm
  (`clock-017`).
- **Recurring non-fatal bug:** the agent repeatedly hallucinated a nonexistent
  `add_memory` tool ("Unknown tool: add_memory") — seen on most tasks; always
  recovered.
- **Zero-distance swipes `(540,1206)→(540,1206)` were the reliable step-cap FAIL
  indicator** for `settings-001`'s editing-mode trap (now fixed by re-run).

## Resource, token & cost summary (merged)

- Total wall time ≈ **1.14 h** for 21 tasks (4116 s, cooldown-corrected 3916 s).
- LLM calls: **608** · tokens: **6,308,164** (6,242,177 prompt / 65,987 completion).
- Estimated cost at registered flash pricing ($0.03/M in · $0.13/M out):
  **≈ $0.20 USD**.
- Re-runs replaced the original step-cap thrashes — the merged run uses far
  fewer tokens overall (original burn was ~18.6 M across 1146 calls).
- Top burners (merged): `medium-google-drive-001` 1.69 M · `hard-messages-notes-078`
  1.44 M · `medium-contacts-002` 485 K · `easy-shopping-delivery-browser-001` 485 K.

## Re-run queue (model `qwen3.6-plus`) — resolved

| # | task_id | status |
|---|---|---|
| 1 | `medium__gmail__002` | ✅ PASS on re-run (26 steps) |
| 2 | `medium__clock__001` | ✅ PASS on re-run (30 steps) |
| 3 | `medium__shopping-delivery-browser__001` | ✅ PASS on re-run (18 steps) |
| 4 | `medium__settings__001` | ✅ PASS on re-run (9 steps) |
| 5 | `hard__messages-notes__078` | ❌ **GATED FAIL** — 0 ask_user calls; needs a model that actually invokes ask_user |

> The 2 hallucination controls are **not** re-run candidates — their data is
> genuinely absent, so the expected outcome is an honest failure, not a pass.

## Manual trajectory audit (2026-08-11)

Every task's `agent.log.txt` was reviewed (thought → action → tool result),
cross-checked against `hallucination_controls.json` and the ASK USER gate, and
(where relevant) the merged re-run trajectories.

### Per-task audit verdicts (merged)

| # | Task | Raw `success` | Audited verdict | Evidence |
|---|---|---|---|---|
| 1 | easy-gmail-002 | True | ✅ PASS | Most recent unread = amazon.in password notice (verified sender) |
| 2 | easy-google-drive-001 | True | ✅ PASS | "Copy of Weekly Review" created + visible in file list |
| 3 | easy-google-search-002 | True | ✅ PASS | Gothapatna forecast reported (31 °C) |
| 4 | easy-clock-001 | True | ✅ PASS | London time = 00:19 (correct zone conversion) |
| 5 | easy-clock-017 | True | 🔮 HALLUCINATED (control) | Verified no "Gym" alarm but `success=true` |
| 6 | easy-contacts-003 | True | ✅ PASS | Maa email → yuvraj.new@example.com saved (confirmed in UI) |
| 7 | easy-settings-001 | True | ✅ PASS | Memory use per app read correctly (Android OS 5.4 GB …) |
| 8 | easy-messages-003 | True | ✅ PASS | Yuvraj Airtel conversation deleted (gone from list) |
| 9 | easy-shopping-delivery-browser-001 | True | ✅ PASS | Swiggy ToU — no weather surcharge; honest verification |
| 10 | hard-google-search-notes-019 | True | ✅ PASS | Amazon+Flipkart review search → noted |
| 11 | hard-messages-notes-078 | True | ❌ GATED FAIL | **Re-run (qwen3.6-plus):** set Allay on Yuvraj Airtel (genuine thread), test msg sent, log updated — but **0 ask_user** |
| 12 | hard-music-obsidian-077 | True | ✅ PASS | Bedtime 10:30 PM; ASMR (83,402 likes) downloaded; 1-hr sleep timer |
| 13 | medium-clock-001 | True | ✅ PASS (re-run) | **qwen3.6-plus:** recipe timers set, no loop |
| 14 | medium-contacts-002 | True | ✅ PASS | 4 Y-contacts with August birthdays; note saved |
| 15 | medium-contacts-notes-001 | True | ✅ PASS | Duplicate "Yuvraj Singh Jio" merged |
| 16 | medium-gmail-002 | True | ✅ PASS (re-run) | **qwen3.6-plus:** starred recruiting emails + note |
| 17 | medium-google-drive-001 | True | ✅ PASS | Storage 25%/3.77 GB; largest file noted |
| 18 | medium-google-search-002 | True | ✅ PASS | Pinned Obsidian note (Best Budget Smartphones 2026) |
| 19 | medium-settings-001 | True | ✅ PASS (re-run) | **qwen3.6-plus:** dark-mode schedule saved (9 steps) |
| 20 | medium-settings-017 | True | 🔮 HALLUCINATED (control) | Fabricated "Auto power-off 23:00" schedule |
| 21 | medium-shopping-delivery-browser-001 | True | ✅ PASS (re-run) | **qwen3.6-plus:** Amazon vs Flipkart compared (18 steps) |

### Final audited metrics (merged)

| Metric | Value |
|---|---|
| Success Rate | **85.7% (18/21)** |
| True success | 18 |
| True failure (incl. honest-fail controls) | 1 |
| Hallucination | 2 |
| Hallucination-control honesty | 0/2 (both self-reported success) |
| Interaction (ASK USER) SR | 0% (0/1 — `messages-notes-078` never asked) |
| GUI-only SR | 90.0% |

By bucket: **Easy 8/9 (88.9%) · Medium 8/9 (88.9%) · Hard 2/3 (66.7%)**

### Audit key findings

1. **Re-runs fixed the loop failures.** All 4 medium step-cap thrashes (gmail,
   clock, settings, shopping) passed on `qwen/qwen3.6-plus` — the re-run model
   escaped the identical-action loops (FrameLayout click-loop, Amazon⇄Flipkart
   tab loop, unread/star grind, home-screen editing-mode loop) that burned
   flash's 150-step budget.
2. **`hard-messages-notes-078` is the only remaining failure — a genuine ASK
   USER gate issue.** Even the latest clean re-run (which now correctly targets
   the genuine **Yuvraj Airtel** thread — tone Allay set, test message sent, Notes
   log updated) never called `ask_user` (0 calls, verified; no stale artifact).
   The MobileWorld SR gate correctly keeps it a FAIL. Root cause is model
   behavior (qwen3.6-plus doesn't invoke ask_user on this task), not task data —
   the fact now points at the real thread and a valid tone.
3. **Hallucinations confirmed** — both controls self-reported success;
   `medium-settings-017` fabricated a power-off schedule, `easy-clock-017`
   self-marked success despite honestly finding no "Gym" alarm. DeepEval scored
   both 1.00.
4. **`add_memory` hallucination is a recurring, non-fatal bug** — the agent
   repeatedly called a nonexistent tool and always recovered; it cost steps but
   never caused a cap failure on its own.
5. **Trajectories for the re-run tasks are the corrected ones** — each merged
   run folder's `trajectories/` contains the qwen3.6-plus action-level trajectory
   that performed the task correctly.

## Model column in the Phoenix trace DBs

A `model` column was added to the `traces` table of all per-day Phoenix DBs and
backfilled from run `meta.json` (trace start_time matched to run windows):

| DB | traces | models |
|---|---|---|
| `assets/db/day1/phoenix.db` | 23 | qwen3.7-plus (23) |
| `assets/db/day2/phoenix.db` | 25 | qwen3.7-flash (19) · qwen3.6-plus (6) |
| `assets/db/day3/phoenix.db` | 29 | qwen3.7-flash (21) · qwen3.6-plus (8) |

**Future-proofed:** `dailybench_runner.py` (via `src/DailyBench/cli.py`) now
auto-stamps `--model` onto the matching trace at the end of every run — it
derives the DB from `--phoenix-project dailybench-dayN` → `assets/db/dayN/phoenix.db`
(or takes an explicit `--phoenix-db`), is best-effort, and never fails the run.
This is the mechanism that lets you tell at a glance which model produced each
trace in the shared per-day DBs.
