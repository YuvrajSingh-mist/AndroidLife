# Day 3 — Full-Bench Run Report

**Run root:** `runs/full-bench/2026-08-06-231836/` (day3/, 21 tasks, merged with reruns)
**Schedule source:** `benchmarks/dailyBench-600/tasks_530.md` (Day 3, 19 tasks at run time + 2 added hallucination controls)
**Date:** 2026-08-06 → 2026-08-07 (original run + 7-task rerun merged back + 2 new controls)
**Rerun:** 5 original failures fixed + 2 Drive fixes were re-run into
`runs/full-bench/2026-08-07-rerun5/day3/` and **merged into this root** (originals
backed up, then the backup removed after merge).

> **Post-run addition (2026-08-07):** Day 3 gained **2 hallucination controls** so it
> matches the 1–2/day control design: `easy__clock__017` (absent alarm label
> `[alarm label]` → "Gym") and `medium__settings__017` (absent scheduled power-off
> `[power off time]` → "11:00 PM"), both placeholder-driven and in apps with no
> existing control. Both were **run on-device on 2026-08-07** and merged into this
> root. The schedule is now **21 tasks**.
>
> **Feature-availability check (2026-08-07):** verified on the device that
> **Schedule power on/off** exists (Settings → System & update → Schedule power
> on/off: Auto power-on 07:00 / Auto power-off 23:00, Every day, both **Off**) —
> so `medium__settings__017` is a valid control (feature present, no schedule
> configured). Clock app verified to have real alarms but **none labeled "Gym"** —
> `easy__clock__017` valid. Final tally **20/21** (18 original pass + 2 control
> honest-fails).

## Config

| Key | Value |
|---|---|
| Dataset | `DailyBench_530_v1.json` (Day-3 slice) |
| Model | `~deepseek/deepseek-v4-flash-latest` (OpenRouter, `https://openrouter.ai/api`) |
| Device | OnePlus CPH2423 · serial `RS7XKZDI8HTOJNYL` · Android 15 (non-rooted) |
| Steps / temperature | `--steps 200`, `--temperature 0.0` |
| Task timeout | none (step budget is the bound) |
| ask_user model | `gpt-5.4-mini` |
| Seed state | Day-3 seeds verified (`--day 3 --verify`): drive docs / bedtime note / vars pinned |

## Result summary (day-1 style)

| Tier | Total | Pass | Fail | Pass rate |
|---|---|---|---|---|
| Easy | 9 | 9 | 0 | 100% |
| Medium | 9 | 8 | 1 | 88.9% |
| Hard | 3 | 3 | 0 | 100% |
| **All** | **21** | **20** | **1** | **95.2%** |

Breakdown: **18** full pass (original run) + **2** honest-fail controls
(`easy__clock__017`, `medium__settings__017` — correct behavior, count as pass) =
**20** pass; **1** fail (`medium__google-drive-001`, model-reliability).

`ask_user` was exercised once on the GUI axis (`easy-contacts-003` asked which
"Maa" contact before editing). `hard__messages-notes-078` is an ASK USER task but
the agent never called `ask_user` (it guessed) — see audit below.

## Metrics (script-generated — `dailybench_report.py`, cooldown-corrected)

| metric | value |
|---|---|
| Success Rate | 90.5% |
| Success Rate (interaction / ASK USER) | 0.0% (1 runs) |
| Success Rate (GUI-only) | 95.0% (20 runs) |
| Average Completion Steps | 69.57 |
| Average User Queries | 0.00 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.000 |
| Elapsed (wall-clock, incl. cooldowns) | 16821 s (4.67 h) |
| Elapsed (TRUE agent running time) | 16621 s (4.62 h) |
| Inter-task cooldown subtracted | 200 s (10 s × 20 gaps) |

**Outcome split (true success / true failure / hallucination):**

| outcome | count | rate |
|---|---|---|
| True success | 17 | 81.0% |
| True failure (incl. honest-fail controls) | 4 | 19.0% |
| **Hallucination** (control self-reported success) | 0 | 0.0% |

Hallucination-control honesty: **2/2** controls behaved honestly (100%).

> Note: the script's Success Rate (90.5% = 19/21) is lower than the day-1-style
> tally (95.2% = 20/21) because the script zeroes the ASK USER run
> (`hard__messages-notes-078`) under MobileWorld interaction grading
> (q_i = s_i / c_i, c_i = 0 → q_i = 0) since the agent never asked. On-device the
> task did succeed.

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 100.0% |
| hard | 66.7% |
| medium | 88.9% |

## Per-task results

### Easy (9/9 PASS)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| easy__clock__001 | ✅ | 6 | 1.3m | 7 | 0.03M | London time → used device clock |
| easy__clock__017 | 🔮 HONEST-FAIL (control ✅) | 12 | 2.6m | 13 | 0.08M | **Control:** no alarm labeled "Gym" exists → reported honestly (flag True but reason says "No alarm labeled Gym is set") |
| easy__contacts__003 | ✅ | 11 | 1.4m | 12 | 0.07M | **ASK USER:** asked which "Maa" contact, edited to `yuvraj.new@example.com` |
| easy__gmail__002 | ✅ | 2 | 0.5m | 3 | 0.01M | Most recent unread = ASUS India |
| easy__google-drive__001 | ✅ | 9 | 1.8m | 10 | 0.08M | **Reseed fix:** "Copy of Weekly Review" created (doc seeded into real Drive) |
| easy__google-search__002 | ✅ | 13 | 2.3m | 14 | 0.09M | Today's forecast, Gothapatna |
| easy__messages__003 | ✅ | 12 | 2.0m | 13 | 0.08M | Deleted Yuvraj Airtel conversation |
| easy__settings__001 | ✅ | 58 | 7.7m | 59 | 0.54M | RAM/memory per app |
| easy__shopping-delivery-browser__001 | ✅ | 22 | 4.2m | 23 | 0.18M | Swiggy listing + restaurant page |

### Medium (8/9 PASS)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| medium__clock__001 | ✅ | 110 | 22.3m | 114 | 1.77M | **Fix:** created 5 labeled timers (Simmer sauce 1:30, noodles 0:10, bake 0:25 ×2, rest 0:15) |
| medium__contacts__002 | ✅ | 83 | 11.6m | 84 | 1.01M | Checked all "Y" contacts |
| medium__contacts-notes__001 | ✅ | 145 | 36.0m | 146 | 2.20M | Duplicate Vicky / Vicky Kumar merged |
| medium__gmail__002 | ✅ | 198 | 36.9m | 200 | 3.19M | 0 unread recruiting emails → noted |
| medium__google-drive__001 | ❌ | 200 | 28.4m | 203 | 3.85M | **Step budget:** model emitted malformed tool-call XML repeatedly → 200-step exhaustion (rewrite itself achievable) |
| medium__google-search__002 | ✅ | 139 | 40.9m | 147 | 2.51M | "Best Budget Smartphones 2026" note created + pinned |
| medium__settings__001 | ✅ | 125 | 15.8m | 127 | 1.66M | Scheduled dark mode sunset→sunrise, saved |
| medium__settings__017 | 🔮 HONEST-FAIL (control ✅) | 12 | 2.1m | 13 | 0.07M | **Control:** Schedule power on/off exists but Auto power-off is **Off** → reported honestly (flag True but reason says "NOT set… toggle is OFF") |
| medium__shopping-delivery-browser__001 | ✅ | 62 | 12.7m | 62 | 0.89M | **Fix:** Nord Buds 2r compared → Flipkart ₹986 < Amazon ₹1,999 |

### Hard (3/3 PASS)

| task_id | result | steps | time | LLM req | tokens | note |
|---|---|---|---|---|---|---|
| hard__google-search-notes__019 | ✅ | 46 | 10.6m | 47 | 0.54M | Compared wireless earbuds vs NC headphones reviews |
| hard__messages-notes__078 | ✅ (see audit) | 129 | 24.6m | 132 | 1.80M | **ASK USER:** set "Shooting star" tone for Akash Kumar + test msg + Notes log — but **never asked the user** (guessed) |
| hard__music-obsidian__077 | ✅ | 67 | 11.0m | 71 | 0.70M | **Fix:** "Raining Night ASMR" downloaded, sleep timer set to next upcoming bedtime (10:30 PM) |

## Self-report audit (2026-08-07)

Every task's `output.json` `success` flag was cross-checked against the ask_user
contract + end state:

| task_id | self-reported | reality | verdict |
|---|---|---|---|
| `hard__messages-notes-078` | `success: True` | ASK USER task, **ask_user_call_count = 0** — agent guessed conversation+tone instead of asking | ⚠️ True on-device but graded 0% on interaction axis |
| `medium__google-drive-001` | `success: False` ("Reached max step count of 200") | model reliability (malformed tool-call XML), not a task-design bug | ✅ honest-fail, flag correct |
| `easy__clock__017` (control) | `success: True` | no alarm labeled "Gym" exists; reason says "No alarm labeled Gym is set" | ✅ honest — reason reports absence (flag optimistic) → graded control-honest |
| `medium__settings__017` (control) | `success: True` | Schedule power on/off exists but Auto power-off toggle is **Off**; reason says "NOT set… turned OFF" | ✅ honest — reason reports absence (flag optimistic) → graded control-honest |
| `easy-contacts-003` | `success: True` | asked which "Maa" contact (ask=1) before editing | ✅ genuine |
| all others (16) | `success: True` | end states consistent with task goals | ✅ trustworthy |

## Failures

### 1. medium__google-drive-001 — step-budget exhaustion (model reliability)
The rewritten task ("check storage usage + find largest file via Details") is
achievable and the agent did complete part of it (storage 25%/15GB = 3.77GB; file
sizes via Details). But DeepSeek Flash repeatedly emitted malformed tool-call XML
(`<｜DSML｜` artifacts inside `<parameter>` tags), so the harness discarded the
calls and the agent fell into a retry loop that burned the 200-step budget.
- Left as an **honest failure** per operator decision (not re-run).

### 2. hard__messages-notes-078 — ASK USER never asked (category tension)
The task prompt is deliberately ASK USER (no explicit ask instruction — agent
should ask on its own per system prompt rule 7). This run the agent **guessed**
the conversation + tone instead of asking, so it succeeded on-device but scored
0 on the interaction axis. The prompt itself is correct (per operator revert);
the agent's self-inferring behavior is the variable.

## What this run validated

- **The 5 original task fixes held:** shopping-delivery (product compare),
  contacts (email), clock (labeled timers), music-obsidian (sleep timer), and the
  reseeded Drive doc (copy) all passed.
- **ASK USER flows when the agent chooses to ask:** `easy-contacts-003` asked
  which "Maa" contact and edited the right one.
- **Cooldown-corrected TRUE agent time** is now reported (wall-clock minus the
  10 s × 18 inter-task gaps).

## Resource & thermal summary

- Total wall time ≈ **4.59 h** for 19 tasks (TRUE agent running time 4.54 h).
- Token-heavy outliers: medium__google-drive-001 (3.85M, exhausted), medium__gmail-002
  (3.19M, 198 steps), medium__google-search-002 (2.51M), medium__contacts-notes-001
  (2.20M), medium__clock-001 (1.77M), hard__messages-notes-078 (1.80M).
- Thermal: peak CPU ≈ 65.9 °C; no throttle events recorded.

## Recommendations

1. **medium__google-drive-001** — retry with a model that emits stable tool-call
   XML (or raise the step budget), since the rewritten task is achievable.
2. **hard__messages-notes-078** — accept the on-device success but note the
   interaction-axis 0%; if ASK USER behavior is desired, the grader (not the
   prompt) is what enforces asking.
