---
name: reset-phone
description: 'Reset the benchmark phone (OnePlus CPH2423) to its pre-run baseline and re-verify the seeded task data before running inference. USE WHEN: resetting the phone, reset device before run, restoring baseline, cleaning up run artifacts, undo a run, seed data, provision device, prepare device for a run, pre-run device reset, reseed, full public rerun. DO NOT USE FOR: general ADB debugging, single-task fixes, the emulator (use AVD snapshot cold-boot instead).'
---

# Reset the benchmark phone to baseline (pre-run)

Goal: return the device to the exact fabricated baseline so every inference run
starts from the same state. **Full public-rerun runbook** — run in order:

1. **Regenerate datasets** from the current md (if tasks changed).
2. **Undo run artifacts** (what the agent created/changed during a run) — scripted.
3. **Re-seed** the fabricated data the tasks need (photos, notes, PDFs, calendar).
4. **Verify baseline seeds present** (fail-fast gate before any run).

> ⚠️ Destructive-ish: this DELETES agent-created data (events, notes, files,
> blocks, contact edits). It does NOT wipe the fabricated seed data. Never run on
> a personal device — this phone is the dedicated benchmark device (fabricated
> persona "Yuvraj Singh" data only).

## Connection

- Wired: `adb -s RS7XKZDI8HTOJNYL shell echo OK`
- Wireless: `adb -s 100.108.15.119:5555 shell echo OK`
- If wireless refuses ("Connection refused"), re-arm then reconnect:
  `adb -s RS7XKZDI8HTOJNYL tcpip 5555` → `adb connect 100.108.15.119:5555` (retry once — it's a race while adbd restarts).

## Step 0 — Regenerate datasets (only if `public.md` / `tasks_530.md` changed)

```bash
uv run python scripts/data/export_530_dataset.py --verify      # expect: 530 tasks, 0 dupes
uv run python scripts/data/export_public_dataset.py            # expect: 68 tasks
node website/tools/build_site_data.mjs                          # site data (530 tasks)
uv run python scripts/seeding/verify_config.py                  # every placeholder/fact/seed resolves
uv run python -m pytest tests/ -q -p no:cacheprovider --deselect tests/test_adb.py::test_reset_app_state_force_stops_foreground_app_and_returns_home
```
> 2026-08-23 task changes (re-export picks them up): `easy__swiggy__001` reworded to
> "sum last month's Swiggy spendings"; `hard__google-search-telegram-clock__018` fact
> now includes the recipient (Yuvraj Singh Jio); `medium__google-search__008` promoted
> to ASK USER with the route fact (IIIT Bhubaneswar → Bhubaneswar Airport);
> `hard__photos-gmail-obsidian__012` fact now = photo + recipient email
> (`hafari4025@aghism.com`). **Public set trimmed 68 → 60 (20/20/20 per day)** — 8
> duplicate tasks removed (see `docs/benchmark-spec-public.md`).
> `ask_user_facts.json` was patched by hand — keep it in sync with the dataset.
```
> Note: `test_openrouter_live.py` needs a real network to OpenRouter — it fails
> with `RemoteDisconnected`/`403` when the sandbox blocks outbound; ignore it (or
> run tests with network allowed). It is unrelated to data changes.

## Step 1 — Run the reset script (dry-run first, then apply)

```bash
uv run python scripts/seeding/reset_phone.py --serial RS7XKZDI8HTOJNYL --profile public_v2          # DRY RUN (default, safe)
uv run python scripts/seeding/reset_phone.py --serial RS7XKZDI8HTOJNYL --profile public_v2 --apply  # actually reset
```

The script (profile `public_v2`):
- Restores settings (e.g. `screen_off_timeout` → 1800000).
- Unblocks numbers the agent blocked (keeps pre-existing blocks).
- Deletes agent-created calendar events (marker/title/creation-window matched) and restores the mangled `Akash Kumar` contact.
- **(Re)creates date-relative calendar seeds** at EVERY reset: `Weekly Sync` (next Mon 07:00 + 10:00) + `Gym` (next Tue 06:30) on `cal_id=16` — powers `hard__clock-calendar__023` clash-shift + `hard__google-meet-files__070` agenda meeting. Idempotent (drops same-title first).
- Removes run-created files from Downloads/DCIM + Obsidian `Pasted image *.jpg` artifacts.
- **Restores mutated seed-note contents to their exact baseline** (`Food Favourites.md`, `Budget Deadline.md`, `Weekly Agenda.txt`, `Stock Watch.md`).
- Prints the manual UI-only cleanups ADB can't reach (see Step 4).

> Bug fixed 2026-08-21: `reset_phone.py` `_line_for()` now skips `deleted=1`
> (soft-deleted) calendar rows when checking seed presence — otherwise the verify
> false-FAILs `Weekly Sync` when a freshly re-seeded (non-synced, `_sync_id=NULL`)
> copy coexists with an older soft-deleted one.

## Step 1b — Soft-delete run-created CALENDAR events (synced calendar — reset script MISSES these)

`reset_phone.py` only removes events it can match by marker/title/creation-window; it
DROPS run-created events on the **Google-synced** calendar (`cal_id=16`, `_sync_id`-backed).
Verified 2026-08-23: this run created 3 events the reset left behind. Soft-delete them by
exact title every reset (provider delete works — soft-deletes on the synced calendar):

```bash
for t in "Get-together with friends" "IndiGo 6E-6737 Flight - BBI to DEL" "Review July Photos"; do
  adb shell content delete --uri content://com.android.calendar/events --where "'title=\"$t\"'"
done
adb shell content query --uri content://com.android.calendar/events --projection title:deleted 2>/dev/null \
  | grep -iE "Review July|Get-together|IndiGo" || echo "run events cleaned"
```
These map to: `hard__telegram-calendar__016` ("Get-together with friends"),
`hard__gmail-calendar__003` ("IndiGo 6E-6737 Flight - BBI to DEL"),
`medium__google-photos-calendar__001` ("Review July Photos"). Run **Step 2b** afterwards
(Team Sync / Mentor 1 on 1 are separate date-relative seeds).

## Step 1c — OnePlus Notes: delete run-created notes (GUI automation)

`com.oneplus.note` is app-private (no provider). Run-created notes from the run day MUST
be deleted in the UI (verified working via adb GUI automation 2026-08-23):

```bash
adb shell am start -n com.oneplus.note/com.nearme.note.main.MainActivity
adb shell uiautomator dump /sdcard/ui.xml            # find text="<note title>" -> bounds
adb shell input swipe <x> <y> <x> <y> 900            # long-press the note row (multi-select)
adb shell input tap <dx> <dy>                        # tap the bottom "Delete" button
# confirm dialog "Delete this note?" -> tap its "Delete"
```
Rule (**clean-slate, no mix-ups**): delete **ALL notes whose date == the run day(s)**,
NOT a hardcoded list. THIS run (2026-08-23) created: `How to Change a Bike Tyre`
(`hard__chrome-youtube-notes__088`) and `Fastest route to Bhubaneswar Airport`
(`medium__google-maps__002`). The older canned names ("Card Payment Due", "Budget
Tracker", "Birthday Reminders", "IndiGo Flight…") were from PRIOR runs — match by
date, don't assume.

## Step 1d — Trajectory-driven leftover-state sweep (MANDATORY every reset)

The reset script + canned manual list do NOT catch leftover UI state the agents
left behind (learned the hard way 2026-08-23: unsent Telegram drafts were missed).
After Steps 1–1c, sweep **EVERY task** under the run's `day*/` folders — one folder
per task, do not skip any — and clear persisted state:

1. **Scan every task** (all N task folders, not a sample): for each, open the latest
   `trajectories/<ts>/trajectory.json` and list the final tool calls + any `type`
   action text. Flag:
   - `type` into a messaging compose that was never sent (→ draft to clear)
   - `type` into a search/filter box (ephemeral; dies on force-stop — verify app
     isn't mid-dialog)
   - created alarms/timers, starred items, open compose fields, unsent messages
2. **Messaging drafts (Telegram / SMS / WhatsApp / Messages)** — open each chat the
   agent typed into and clear the compose field (tap it, select-all + delete).
   Known 2026-08-22 run: the **Yuvraj Airtel** chat had 3 unsent drafts
   (`hard__swiggy-005` "Order total: Rs. 30.00", `medium__google-maps-003`
   "Nearest EV charging station…", `medium__music-telegram-001`
   "Blinding Lights | The Weeknd"). Verify the compose EditText is empty
   (uiautomator `text=''`). Note: Telegram force-stop can drop the draft, but
   RE-CHECK every chat the agent touched — the chat list is a custom view
   uiautomator can't read, so open each chat individually.

   > 2026-08-22-195244 run, all-task scan → undo list (match by run-window):
   > calendar events to soft-delete: "Get-together with friends"
   > (`hard__telegram-calendar__016`), "IndiGo 6E-6737 Flight - BBI to DEL"
   > (`hard__gmail-calendar__003`), "Review July Photos"
   > (`medium__google-photos-calendar__001`). Obsidian notes to `rm`:
   > "Fastest route to Bhubaneswar Airport" (`medium__google-maps__002`),
   > "Photo sent to Yuvraj Airtel" (`hard__photos-gmail-obsidian__012`, + unstar
   > the photo + delete the Sent email). Unsent drafts to clear (Yuvraj Airtel
   > chat): "Order total: Rs. 30.00" (`hard__swiggy__005`). Clock leftover:
   > "Work Alarm" (`medium__clock__009`), stop "Workout" timer
   > (`medium__clock__011`). Maps favourite to remove: "parked here"
   > (`easy__google-maps__004`). Note `medium__contacts__009` placed a REAL call
   > (call-log gap is operator-seeded, not undone).

2b. **SENT messages the agent claims it sent (NOT just drafts — 2026-08-28 lesson).**
    Clearing drafts is NOT enough: runs also SEND messages that persist on-device.
    Sweep SENT artifacts for EVERY run:
    - **SMS**: `adb shell content query --uri content://sms --projection _id:address:date:type:body --where "type=2"`
      → flag run-window `type=2` (sent) rows that aren't persona history (match body/date to the run). Delete via the
      Messages app UI (long-press message → Delete → confirm) — `content delete` on `content://sms` FAILS silently
      (shell has no WRITE_SMS). 2026-08-27: qwen `easy__messages-010` left a real sent emoji SMS (👍😊🙏🍽️👋 to
      Yuvraj Airtel, 03:29) the user caught on screen — persona history was intact after deleting only that row.
    - **Telegram**: grep agent logs for `sent successfully|message is sent|was sent|checkmark`, then OPEN the target
      chat and confirm whether a run message actually persists (chat at true bottom = NO scroll-to-bottom FAB + message
      list won't scroll; Telegram search for the message text returns no private-chat hits if it's gone). Agents'
      "sent ✓" self-reports are UNRELIABLE (gemini false-pass pattern) — always verify on-device. 2026-08-27: logs
      claimed 3 sends to Yuvraj Airtel (chrome-telegram-notes-008 Noise link + 2× music-telegram-001 "Blinding
      Lights") but the chat held none at cleanup time.
    - **Gmail**: grep agent logs for `email was sent|sent the invitation`; run-created SENT emails
      (e.g. qwen `easy-google-meet-004` Meet invites, `hard-photos-gmail-obsidian-012` email) need the Sent email
      deleted — ASK THE USER first (they may be the task's deliverable).
3. **Clock** — open `com.oneplus.deskclock`; delete leftover alarms (e.g.
   `medium__clock-009` "Work Alarm") and stop any running timer (`medium__clock-011`
   "Workout") so the next run's clock tasks start clean.
4. **Open apps** — return to home (`input keyevent KEYCODE_HOME`) so no app is
   left foreground in a partial state.
5. **Ephemeral search boxes** (Drive/Sheets/Obsidian/Files search text) — app-private,
   die on force-stop; just confirm the app isn't stuck in a dialog before the run.

## Step 2 — Re-seed the fabricated task data (public rerun)

After the reset, re-push every ADB-seedable fabricated seed (the reset only
restores a few known files; these push the rest):

```bash
S=RS7XKZDI8HTOJNYL
# Day-1 fabricated photos (camera seeds) + Obsidian notes + contacts/SMS/call-log
uv run python scripts/seeding/seed_data.py --serial $S --day 1
# Day-2 invoice PDF
uv run python scripts/seeding/seed_data.py --serial $S --day 2
# Day-3 Music sleep-timer Obsidian 'Bedtime' note (7-day sleep-routine record)
uv run python scripts/seeding/seed_data.py --serial $S --day 3
# Enriched public-sample Obsidian notes (Budget Deadline, Exam Scores, Monthly
# Budget, Shared Bill, Stock Watch, Recipe, Food Favourites, Contact Updates, Bedtime)
uv run python scripts/seeding/enrich_public_notes.py --serial $S
# Public PDFs (Invoice INV-2026-071.pdf = Rs. 1,240.00 due 2026-07-25; Rent
# Receipt.pdf = Rs. 9,000.00 paid in full)
uv run python scripts/seeding/fabricate_public_pdfs.py --serial $S
```

> Day-1 `seed_data.py` pushes `Stock Watch.md` at the **530** value (1,385 INR) —
> the public baseline is 1,320.50 INR. `enrich_public_notes.py` (run right after)
> overwrites it with the correct public value, so keep the order above.

## Step 2b — Re-seed date-relative calendar events (per run date)

`easy__calendar__002` (conflict check) needs **2 overlapping events TOMORROW
afternoon**; the old ones go stale. Re-create them on `cal_id=16` (correct IST
epochs, Asia/Kolkata) — run this every reset:

```bash
uv run python - <<'PY'
import datetime, subprocess
from zoneinfo import ZoneInfo
S = "RS7XKZDI8HTOJNYL"; tz = ZoneInfo("Asia/Kolkata")
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
CAL = "content://com.android.calendar/events"
def sh(*a): return subprocess.run(["adb","-s",S,"shell",*a], capture_output=True, text=True)
def ms(d,h,m): return int(datetime.datetime(d.year,d.month,d.day,h,m,tzinfo=tz).timestamp()*1000)
for t in ("Team Sync","Mentor 1 on 1","Team_Conflict_A","Team_Conflict_B"):
    for _ in range(6): sh("content","delete","--uri",CAL,"--where",f"'title=\"{t}\"'")
def ins(t,h0,m0,h1,m1):
    sh("content","insert","--uri",CAL,"--bind","calendar_id:i:16",
       "--bind",f"title:s:'{t}'","--bind",f"dtstart:l:{ms(tomorrow,h0,m0)}",
       "--bind",f"dtend:l:{ms(tomorrow,h1,m1)}","--bind","allDay:i:0",
       "--bind","hasAlarm:i:0","--bind","eventTimezone:s:Asia/Kolkata")
ins("Team Sync",14,0,15,0); ins("Mentor 1 on 1",14,30,15,30)
print(f"seeded tomorrow ({tomorrow}) afternoon conflicts")
PY
```

## Step 3 — Verify baseline (gate)

```bash
uv run python scripts/seeding/reset_phone.py --serial RS7XKZDI8HTOJNYL --profile public_v2 --verify-only
for d in 1 2 3; do uv run python scripts/seeding/verify_day1_seeds.py --serial RS7XKZDI8HTOJNYL --day $d; done
```

Baseline must include, e.g.: 3 `shareholder *` events on the **Google-synced**
calendar (`yuvraj.mist@gmail.com`, with `_sync_id`), `Weekly Sync` + `Gym`
(next week), `screen_off_timeout=1800000`, seed files present
(`PURCHASE_ORDER.xlsx`, `SPORTS_VIDEO_DATA.xlsx`, `budget.xlsx`, `quote.xlsx`,
`Weekly Agenda.txt`, `Invoice INV-2026-071.pdf`, `Rent Receipt.pdf`), the public
Obsidian notes, `Team Sync`/`Mentor 1 on 1` tomorrow, contact "Akash Kumar" present.
If verify fails, do NOT start the run — fix the device first (fail-fast).

## Step 4 — Manual UI-only cleanups (no ADB access — app-private DB / cloud)

These cannot be scripted on a non-rooted device; do them once per run if the
agent touched them. **Clean-slate rule: remove what THIS run created (match by
run-window/date), never assume a canned list from prior runs.** The reset script
prints these; the key ones:

- **Notes** (`com.oneplus.note`) — delete ALL notes dated the run day(s) (see
  Step 1c — GUI automation works; "Card Payment Due / Budget Tracker / Birthday
  Reminders / IndiGo" were PRIOR-run names, match by date not name).
- **Obsidian** — the vault IS at `/sdcard/Obsidian/<vault>` and is ADB-accessible
  (NOT app-private — corrected 2026-08-23): run-created notes (e.g.
  `Photo sent to Yuvraj Airtel.md` from `hard__photos-gmail-obsidian-012`) can be
  `adb shell rm`'d directly. Reset script already removes `Pasted image *.jpg` +
  restores seed-note contents. Verify `Exam Scores.md` has no "Final Grade" line
  (mutation from `medium__calculator__001`).
- **Photos/Gallery** — delete run-created albums: THIS run = **"Hostel Life"**
  (`medium__google-photos-012`); prior runs = "Invoices", "Trip 2026". Unstar the
  starred photos; re-add `medium__gallery__007` food-photo captions + Favourites
  if ever lost (app-private Photos DB, per-account — normally survive runs).
- **archive.zip.zip** — remove
  `/storage/emulated/0/Files by Google/Compressed files/archive.zip.zip`
  (created by `hard__files-notes__069`; reset script does NOT catch it).
- **YT Music** — delete the "Chill Vibes" playlist (not created this run — verify).
- **Telegram** — unmute the "Forever 21" group; keep the meetup thread
  **UNRESOLVED** (last message: *"22nd could work for me too, let me confirm once
  she's free"* so `hard__telegram-calendar__016` forces a multi-turn ask — don't
  re-add a settling message).
- **Digital Wellbeing** — remove any 30-min app timers (none set this run — verify).
- **Camera** — delete the run-recorded "Camera Video" clip if present (none this run).
- **Cloud (Gmail / Drive)** — NO run-created Gmail label exists this run; if a task
  emailed a photo w/ attachment (`hard__photos-gmail-obsidian-012`), delete that
  Sent email; delete `Copy of SPORTS_VIDEO_DATA` leftovers; re-download the 5
  uploaded files, then delete that Drive folder.
- **Call-log gap** — not seeded by design: the operator must make one real call
  to an unsaved number on run day (see `docs/fabricated-test-data.md`).
- Gmail "Recent Mail Searches" is NOT a reset item (personal searches, no Remove
  menu; can't leak ASK USER facts) — do NOT block a run on it.

## Cloud account map + pre-run cloud verify (the #1 re-run confusion, 2026-08-22)

The fabricated **on-device** seeds are ADB-verifiable (§0). Everything else is
**cloud/account state** that must sit on the right Google account — the device has
6 Google accounts and the apps are NOT auto-consistent. Before every run, confirm
each app is on ONE canonical account (currently split — pick one and re-login the
others):

| App | Where its seed data lives |
|---|---|
| Calendar (cal_id=16) | `yuvraj.mist@gmail.com` — Google Calendar only shows `_sync_id` events |
| Gmail / Drive / Docs / Slides | `ranirajesh786@gmail.com` — Scapia flight email, `Q3_Report` + shared files, `Student Project Tracker` doc, `Q3 Review` deck |
| Google Photos | `rajeshceo2015@gmail.com` (backup ON) — most-recent photo has location + "Backed up" |
| Contacts / SMS / Notes / Obsidian / Telegram | device-local (no account) — ADB-seeded |
| Prime Video / Amazon / Swiggy / BookMyShow / Zomato / YT Music | personal accounts (signed in, real order/watch history — re-verify at run time) |

Quick cloud verify (in-app, ~10 min):
- **Gmail** search "Scapia" → "Fwd: Pack for Delhi" flight email present (KB = PNR X84NVI, BBI→DEL, Oct 16, 12:05→14:30).
- **Drive** `Q3_Report` + shared-with-me editable files present; `Copy of SPORTS_VIDEO_DATA` cleaned.
- **Slides** `Q3 Review` deck · **Docs** `Student Project Tracker`.
- **Photos** food captions + Favourites for `medium__gallery__007` — **app-private AND per-account**: favourites/captions do NOT carry across accounts; if the Photos app is on a different account than where they were set, they appear gone. Re-add 3 food photos (favourited + captioned) in the SAME account the app is signed into.
- **Digital Wellbeing** → "App timers" → "No timers set".

## Step 5 — Run inference (public 60-task sample)

Start Phoenix for the public project (DB `assets/db/public/phoenix.db`), then launch:

```bash
# 1. Phoenix collector (per-run DB: assets/db/public/<RUN_TS>/phoenix.db — date-time folder convention)
RUN_TS=$(date +%Y%m%d-%H%M%S)
uv run python scripts/run/start_phoenix.py --public --run-ts "$RUN_TS"

# 2. Batch (qwen3.6-plus; --task-timeout N overrides the 40-min cap)
uv run dailybench_tasks.py \
  --dataset benchmarks/dailyBench-600/DailyBench_public_v2.json \
  --source public.md --all \
  --serial RS7XKZDI8HTOJNYL \
  --llm-upstream-base https://openrouter.ai/api \
  --model qwen/qwen3.6-plus --temperature 0.0 --steps 60 \
  --save-trajectory action \
  --vars-file benchmarks/dailyBench-600/public_vars.local.env \
  --ask-user-kb benchmarks/dailyBench-600/multiturn_kb_public.json \
  --phoenix-url http://localhost:6006 --phoenix-project dailybench-public \
  --run-root "assets/runs/public/$(date +%Y-%m-%d-%H%M%S)"
```

- `--save-trajectory action` is the default (kept explicit per user preference).
- `--task-timeout` auto-applies 2400s (40 min) per task; `--task-timeout N` overrides, `0` = no wall-clock cap (2026-08-22).
- The 4 multi-turn KB tasks NEED `--ask-user-kb benchmarks/dailyBench-600/multiturn_kb_public.json` (NOT auto-derived by the runner).
- Guardrails: intervene only if the agent contacts someone NOT in the prompt / creates an unapproved group / places a real call.

### Post-run — auto-generate + file all artifacts (no manual filing)

After the batch finishes, generate the official report + hallucination geval, then
run the organizer (creates folders + files every artifact into its per-run
date-time folder + regenerates the turn-based ASK USER audits + README):

```bash
RUN_ROOT=$(ls -dt assets/runs/public/2026-* | head -1); RUN_TS=$(basename "$RUN_ROOT")
uv run scripts/eval/dailybench_report.py --runs "$RUN_ROOT" --source public.md \
  --hallucination-judge-model gpt-5.4-mini \
  --out "reports/metrics/public/public-$RUN_TS-report.json" \
  --out-md "reports/metrics/public/public-$RUN_TS-report.md"
uv run scripts/eval/eval_hallucination_controls.py --runs "$RUN_ROOT" --sub public \
  --model gpt-5.4-mini \
  --out "reports/metrics/hallucination/public-$RUN_TS.json" \
  --out-md "reports/metrics/hallucination/public-$RUN_TS.md"
make organize-public   # or: uv run python scripts/tools/organize_public_artifacts.py --sweep
```
`organize_public_artifacts.py` is idempotent: creates `reports/public/`,
`reports/metrics/public/`, `reports/metrics/hallucination/`,
`reports/turn-based/{ask-query-single,ask-query-multi}/<RUN_TS>/`, moves the
report/metrics/hallucination files in, archives `assets/db/public/<RUN_TS>/phoenix.db`,
regenerates the per-task ask-user audits from `ask_user_metrics.jsonl`, and rewrites
`reports/turn-based/README.md`. Run `--sweep` to enforce on ALL runs.

## Context / gotchas (learned 2026-08-04 / 2026-08-21)

- Google Calendar app only shows **`_sync_id`-backed** (Google-synced) events —
  events seeded on the local account are invisible to it. Seeds must live on the
  Google account (`cal_id=16` `yuvraj.mist@gmail.com`), not `cal_id=1`.
- `content insert/delete` on this non-rooted device: CALENDAR + CALL-LOG WORK
  (verified 2026-08-05) — but quoting matters: wrap `rrule` values AND title
  where-clauses in single quotes so the device shell doesn't split on `;`/spaces
  (`--bind rrule:s:'FREQ=WEEKLY;BYDAY=WE;COUNT=52'`, `--where 'title="X"'`).
  SMS insert is genuinely BLOCKED (silently no-ops). New seeds → content provider
  or UI automation.
- Calendar "shareholder" visibility miss root cause + fix: see
  `/memories/repo/device-audit.md`.
- **Food-photo captions are only visible by OPENING the photo.** Google Photos search is
  content-based, NOT caption-based — searching "pancake"/"veggie" returns old personal
  photos, not the captioned seeds. To verify `medium__gallery__007`: Collections → Favourites
  and scroll to the BOTTOM (3 items, all below the fold): **Pancakes** = Jul 26 photo,
  **Pizza** = Aug 8 collage, **Veggie Bowl** = Jul 23 photo — each shows its caption when opened.
- **Destructive ops removed from the public tasks** (2026-08-21): delete/dedup/
  merge tasks were replaced with doable, non-destructive daily-user tasks
  (count/report/search/verify) so runs are easy to restore between rounds — the
  reset no longer has to restore deleted data. Hallucination-control tasks are
  untouched (their delete/empty targets genuinely absent data → honest failure).
- For the full 730-task dataset, prefer an **emulator + AVD snapshot** (cold-boot
  from snapshot = exact state, zero provisioning). This skill is for the real
  phone (public 68).
- **Telegram Send-button failure (harness/UI bug, recurring):** tapping Send in the
  Telegram app leaves the text in the compose input, no bubble sent — even when the
  agent claims "it now appears in chat history" (verify against the post-action
  ui_state). Affected the 2026-08-22 run: `hard__swiggy-005`, `medium__google-maps-003`
  (false PASS), `medium__music-telegram-001`. Any task whose deliverable is "message
  X on Telegram" may keep failing until this is fixed (try `--vision` / an alternate
  send interaction).
- **Clean-slate principle (2026-08-23):** remove artifacts by RUN-WINDOW (dates the
  run touched), never by a hardcoded list — lists go stale between runs.
- **Obsidian vault is ADB-accessible** at `/sdcard/Obsidian/<vault>/` — run-created
  notes can be `adb shell rm`'d; no need for in-app deletion. Only Photos captions /
  favourites are app-private AND per-account.
