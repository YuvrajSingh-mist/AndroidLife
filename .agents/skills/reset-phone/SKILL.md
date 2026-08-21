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
agent touched them (each is a quick UI action, ~5–10 min total). The reset script
prints these; the key ones:

- **Notes** (`com.oneplus.note`) — delete run-created notes ("Card Payment Due",
  "Budget Tracker", "Birthday Reminders", "IndiGo Flight: BBI-BOM Aug 15-20").
- **Obsidian** — delete run notes (e.g. "Birthday Reminders"); the vault is
  app-private (`/data/data/md.obsidian`), so do it in-app.
- **Photos/Gallery** — delete run-created albums ("Invoices", "Trip 2026");
  unstar starred photos; re-add `medium__gallery__007` food-photo captions +
  Favourites if ever lost (app-private Photos DB — normally survive runs).
- **YT Music** — delete the "Chill Vibes" playlist.
- **Telegram** — unmute the "Forever 21" group; keep the meetup thread
  **UNRESOLVED** (last message edited 2026-08-21 to *"22nd could work for me too,
  let me confirm once she's free"* so `hard__telegram-calendar__016` forces a
  multi-turn ask — don't re-add a settling message).
- **Digital Wellbeing** — remove the 30-min app timers the agent set.
- **Camera** — delete the run-recorded "Camera Video" clip if it shows up.
- **Cloud (Gmail / Drive)** — unstar starred emails + remove agent-created label;
  delete sent-with-attachment email; delete `Copy of SPORTS_VIDEO_DATA` leftovers;
  re-download the 5 uploaded files, then delete that Drive folder.
- **Call-log gap** — not seeded by design: the operator must make one real call
  to an unsaved number on run day (see `docs/fabricated-test-data.md`).
- Gmail "Recent Mail Searches" is NOT a reset item (personal searches, no Remove
  menu; can't leak ASK USER facts) — do NOT block a run on it.

## Step 5 — Run inference

Launch the batch as documented in `docs/fabricated-test-data.md` §5
(`--dataset benchmarks/dailyBench-600/DailyBench_public_v2.json --all ...`).

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
- **Destructive ops removed from the public tasks** (2026-08-21): delete/dedup/
  merge tasks were replaced with doable, non-destructive daily-user tasks
  (count/report/search/verify) so runs are easy to restore between rounds — the
  reset no longer has to restore deleted data. Hallucination-control tasks are
  untouched (their delete/empty targets genuinely absent data → honest failure).
- For the full 730-task dataset, prefer an **emulator + AVD snapshot** (cold-boot
  from snapshot = exact state, zero provisioning). This skill is for the real
  phone (public 68).
