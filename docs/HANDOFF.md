# HANDOFF — Current state & agreed conventions (updated 2026-08-09)

> **Read this first** if you're starting a new session on DrainBench300. It
> records what was done/agreed so work continues exactly as the user intends.
> Companion notes: `docs/future-directions.md` (proposals), `docs/evaluation-policy.md`
> (grading rules), `reports/day1-run-2026-08-09.md` (full Day-1 audit).

## 1. Repo layout — everything under `assets/` (DONE)

- `assets/runs/`, `assets/seeds/`, `assets/db/dayN/`. Old `runs/` / `seeds/` at the
  repo root **no longer exist**. Update any stale path references.
- Code updated: `src/DailyBench/files.py` (runs root is `assets/runs`), `task_batch.py`,
  `cli.py`, eval scripts, seeding scripts, `.gitignore`, README, scripts/README, tests.
  Full suite passes (190 tests, 1 expected wireless skip).

## 2. Phoenix — per-day model (DONE)

- Current run project: **`dailybench-day1`** — the ONLY project left in the DB.
- Day-1 DB: `assets/db/day1/phoenix.db` (23 traces = 22 MobileAgent.run + 1 ask_user.llm).
- Start phoenix per day: `PHOENIX_SQL_DATABASE_URL=sqlite:///<abs>/assets/db/dayN/phoenix.db`
  + `PHOENIX_PROJECT_NAME=dailybench-dayN`.
- `scripts/run/run_day.py --day N` auto-sets `--phoenix-project dailybench-dayN`.
- Pricing + e2e scripts default to `assets/db/day1/phoenix.db` (override `--db`).
- **Agent cost field:** in `llm_proxy_metrics.jsonl` cost is NESTED at `usage.cost`
  (NOT a top-level `cost` key).

## 3. Day-1 run results (qwen3.7-plus, 2026-08-09-153930)

- Reported: 16/22 pass. **Manual audit: 14/22 (63.6%)**.
- Script metrics (SR-gated): 15/22 (68.2%), interaction 33.3%, avg steps 34.14,
  wall 2.16h, agent cost $2.88 + $0.0003 ask_user.
- Reports: `reports/day1-run-2026-08-09.md`, `reports/metrics/day1-metrics-2026-08-09.md/.json`.

### Key audit verdicts
- **medium__gallery__001 = FALSE PASS** (user was right): "Best Pizza Photos" album holds
  random user screenshots (Jun 12 2023 18:59/18:58, Nov 11 2019 12:59 — all "1080x2340
  = 2.5MP"), NOT pizza. Root cause: seeded `pizza1-5.jpg` are 188-234B tiny colored
  rectangles (104-136px, PNG-in-.jpg) Google Photos can't match as pizza; real pizza
  JPGs sit in `/sdcard/Download/` but weren't surfaced. Model trusted identical
  resolutions over content. **Fix: ship real pizza images as seed + agent must confirm
  the photo actually depicts the subject.**
- **hard__chrome-telegram-notes__008 = PARTIAL**: ask_user ✓, Amazon ₹474 vs Flipkart
  ₹799 ✓, <$10 → no Telegram ✓, but "star the cheaper listing" NEVER done (system_button
  newline bug → completed early).
- **hard__google-search-obsidian-telegram__057 = SR-gate FAIL (correct)**: Stock Watch
  note updated (verified, 2026-08-09 / 1,329 INR), no Telegram (below 1,400), but
  `ask_user_call_count=0` → fail per MobileWorld SR gate. **This is the agreed convention.**
- **easy__calendar__001 = PASS (verified)**: event 3712 eventLocation set in device DB.
  NOTE: event seeded Aug 8 not Aug 9 (seed artifact).
- **easy__obsidian__001 = PASS** but 0-byte note.
- **medium__contacts__001 = PASS (verified)**: 5 August birthdays, 7-day reminders on.
- Telegram sends all verified delivered (chrome-telegram, gallery-telegram "Photo Sent",
  messages 17:47).
- Honest fails: easy-camera (rename Save unresponsive), easy-phone (no per-caller
  ringtone), medium-camera (no Night/HDR toggles), medium-calendar (no recurring
  no-attendee events), medium-obsidian (150-step word-count loop).

## 3b. Day-1 task rewordings (DONE 2026-08-09 — data already regenerated)

The following tasks failed on data/device preconditions, so they were reworded to be
achievable and re-seeded. All changes are in `benchmarks/dailyBench-600/tasks_530.md`
(source of truth) and the regenerated `DailyBench_530_v1.json/.jsonl` + day-1 seed
manifest + `website/assets/data/site_data.json` (site auto-deploys on push):

- **easy__phone__001** → "In Phone, message the most recent unknown number with
  \"who's this?\"" — `seed_unknown_number_call()` now inserts an incoming call from
  `+919555555001` (unknown, not in contacts) on seed day.
- **medium__calendar__001** → "Filter my Calendar to show only recurring events with
  no attendees, delete one that's outdated, and check that the series still repeats
  correctly" (removed the "for today" constraint that failed when no recurring
  no-attendee event fell on run day). Seed fix: `Weekly_Standup` now uses
  `rrule="FREQ=DAILY;COUNT=14"` starting today so there's always an event on run day;
  `Old_Gym_Class` stays a dated WEEKLY series (the outdated one to delete).
- **medium__obsidian__001** → **RENAMED** to **medium__google-docs__001** (task_id
  comment in tasks_530.md + new `[Google Docs]` section): "Rank my documents in
  Google Docs by length (word count), open the longest one, and tell me its word
  count." `task_dataset.py` APP_ALIASES gained `"Google Docs": ("Google Docs", "Docs")`.
- **medium__camera__001** → "I'm taking a portrait this evening, so set up the
  Camera: turn on AI enhancement mode and portrait mode."

Metrics rule (user's): results are ONLY true success / failure / hallucination — no
partials. The Day-1 report reclassified `hard__chrome-telegram-notes__008` from
⚠️PARTIAL to a strict failure (❌).

## 4. Grading conventions (AGREED — do not change)

- **MobileWorld SR gate**: ASK USER task counts as success ONLY if agent called
  `ask_user`. Guessing → 0. \\(q_i = s_i / c_i\\), \\(c_i=0 \\Rightarrow q_i=0\\).
- **QIS** = user's success-free fact-match formula (grades answer vs ground-truth
  fact, independent of task success). See `docs/evaluation-policy.md`.
- Both are implemented in `scripts/eval/dailybench_report.py` + `DailyBench/benchmark_metrics.py`.

## 5. Pending task-area work (user requests — NOT yet implemented)

Full writeups in `docs/future-directions.md` §4-6. Summary:

1. **Google Sheets gap**: tasks exist (public.md "open it in the google sheets app"
   for SPORTS_VIDEO_DATA) but NO `sheets` app_slug. Device HAS Sheets installed
   (`com.google.android.apps.docs.editors.sheets`). Add `sheets` app_slug + task set
   + seed workbook.
2. **Google Meet**: add `meet` app + tasks. Meet is NOT installed on the device
   (needs install/provisioning). Keep to UI-reachable states (no real call).
3. **Real-world booking/checkout tasks**: flight booking, movie ticket booking, and
   shopping end-to-end (product pick → payment page). All stop AT the payment page,
   no real purchase. Template = existing public Notes→Amazon cart→payments task.

## 6. Device facts

- Serial `RS7XKZDI8HTOJNYL`, OnePlus CPH2423, wired USB.
- Stock Watch note: `/sdcard/Obsidian/Papers vault oneplus /Stock Watch.md`
  (trailing space in dir name matters). Daily Reflection note exists (0 bytes).
- Pizza seed files are placeholder rectangles — NOT usable for a real pizza search.

## 7. "Run Day N" workflow (for future sessions)

When the user says "run day 2" (or any day N), follow this EXACT sequence. Do not
invent steps; this is the agreed, verified workflow:

1. **Recall context**: read this file + `reports/day1-run-2026-08-09.md` for
   conventions (SR gate, QIS, false-pass lessons).
2. **Prepare the device**: 
   `adb -s "$DAILYBENCH_SERIAL" shell "input keyevent 3; input keyevent KEYCODE_WAKEUP; wm dismiss-keyguard"`
3. **Verify seeds for that day on-device**:
   `uv run scripts/seeding/seed_data.py --serial "$DAILYBENCH_SERIAL" --day N --verify`
4. **Start Phoenix for that day** (fresh per-day DB; project `dailybench-dayN`):
   `PHOENIX_SQL_DATABASE_URL="sqlite:///$PWD/assets/db/dayN/phoenix.db" PHOENIX_PROJECT_NAME=dailybench-dayN uv run phoenix serve --port 6006`
5. **Run the day** (auto-targets the `dailybench-dayN` project):
   `uv run python scripts/run/run_day.py --day N --dry-run` first, then without `--dry-run`.
6. **Register pricing into that day's DB** (default is day1 — pass `--db` for other days):
   `uv run scripts/tools/register_openrouter_pricing.py --model qwen/qwen3.7-flash --db assets/db/dayN/phoenix.db`
7. **Aggregate metrics**:
   `uv run scripts/eval/dailybench_report.py --runs assets/runs/full-bench/<latest-timestamp>/dayN`
8. **Manually audit** (gifs + trajectories + on-device verify). Do NOT trust
   `output.json` success flags — Day 1 had a confirmed false pass
   (`medium__gallery__001`).
9. **Write reports**: `reports/dayN-run-YYYY-MM-DD.md` + `reports/metrics/dayN-metrics-*.md/.json`
   following the Day-1 structure.
10. **Update the site data** if tasks changed, then push (auto-deploys GH Pages):
    `node website/tools/build_site_data.mjs && git add -A && git commit -m "..." && git push origin master`

## 7b. Website trajectories (per-task detail pages)

Each task card on `pages/tasks.html` links to a per-task detail page
(`pages/task.html?task_id=…`) that shows the task description, its state (difficulty,
type, cross-app, points, day), the run's **trajectory replay GIF**, run details
(model, result, duration), and a **step-by-step "Model Trajectory" viewer** (every
thought → function call → tool args → result, as traced into Phoenix), with the
**phone screenshot for the current step** shown in a phone frame beside the JSON.

- Export (run from repo root, regenerates index + copies GIFs + downscaled step
  screenshots into `website/assets/`):
  `node website/tools/export_trajectories.mjs`
- Canonical run roots used: day1 `assets/runs/full-bench/2026-08-09-153930/day1`,
  day2 `assets/runs/full-bench/2026-08-10-234158/day2`,
  day3 `assets/runs/2026-08-11-040846/day3` (reruns merged).
- Output: `website/assets/data/trajectories/{index.json,dayN/<task_id>.json}`
  (condensed FastAgent steps, each tagged with its `screenshot` filename + a
  `screenshot_base` path) + `website/assets/trajectories/dayN/<task_id>/trajectory.gif`
  + `…/screenshots/NNNN.jpg` (downscaled via `sips`/`ffmpeg` to ~560px, ~28KB each).
- Renamed tasks are aliased (e.g. `medium__obsidian__001` → `medium__google-docs__001`)
  so old runs show under the current id — see `TASK_ID_ALIASES` in the exporter.
- The "Open full trajectory in Phoenix" button only appears when previewing from
  localhost (no Phoenix on the public GH Pages site); the step viewer is the
  Phoenix-traced trajectory.

Constraints: never re-run completed tasks; keep the MobileWorld SR gate for ASK
USER tasks; per-day Phoenix DB lives at `assets/db/dayN/phoenix.db`.
