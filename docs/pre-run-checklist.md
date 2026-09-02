# Pre-run GUI checklist — public 68-task rerun (2026-08-22)

Purpose: tick every item that **only a human in the app UI can verify** (app-private DBs,
cloud/server-side state — NOT ADB-checkable on this non-rooted device). The ADB-verifiable
baseline is already confirmed PASS (see §0); do **not** re-do those.

✅ = verified already via ADB (leave alone) · ☐ = needs YOUR GUI check · 🔴 = run-day only

---

## §0 — Already verified via ADB (do NOT recheck)

- ☑ Reset baseline `--verify-only` → **PASS**
- ☑ Day-1 / Day-2 / Day-3 seed verify → **PASS** (all three)
- ☑ Tomorrow-conflict events re-seeded → **Sun Aug 23** (Team Sync 14:00 + Mentor 1 on 1 14:30)
- ☑ Weekly Sync → **Mon Aug 24** 07:00 + 10:00 · Gym → **Tue Aug 25** 06:30
- ☑ All PDFs/xlsx/Downloads present (PURCHASE_ORDER, SPORTS_VIDEO_DATA, budget, quote,
  Weekly Agenda.txt, Invoice INV-2026-071.pdf, Rent Receipt.pdf, Concert Highlights.mp4, Physics Lecture)
- ☑ All public Obsidian notes present (Bedtime, Budget Deadline, Exam Scores, Monthly Budget,
  Shared Bill, Stock Watch, Recipe, Food Favourites, Contact Updates, Weekly Agenda.txt)
- ☑ Contacts (incl. Akash Kumar + fabricated email `yuvraj.mist@gmail.com`)
- ☑ Camera 11/11 + Screenshots 4/4 · screen_off_timeout=1800000 · blocked numbers cleared
- ☑ Public dataset = **68 tasks** · full test suite **173 passed** · repo clean (git)

---

## §1 — Google Photos  (highest priority — most fragile)

- ☐ **3 food-photo captions + Favourites** exist (`medium__gallery__007`):
  open the Favourites tab → each of the 3 food photos (Pancakes / Pizza / Veggie Bowl)
  has a **description/caption** and is **favourited**. If captions are gone, re-add them
  (the task matches photo description → Obsidian heading).
- ☐ **Event/trip photo caption mentions "Yuvraj Airtel"** (`hard__photos-gmail-obsidian__012`):
  the Bhubaneswar-trip / event album photo has a caption containing **Yuvraj Airtel**
  (so the "email it to them if so" branch is reachable). If missing, add it in the Photos UI.
- ☐ Run-artifact albums deleted: **Invoices**, **Trip 2026** (create fresh only if the task
  expects them — these were agent-created, so delete leftovers).
- ☐ **2 starred photos** from prior runs unstarred (unless a task re-stars them).
- ☐ Recent video `feas_video.mp4` searchable in Photos (`medium__google-photos__008`).
- ☐ Most-recent photo has a location + is cloud-backed (`easy__google-photos__015`).

## §2 — Gmail

- ☐ A **flight-confirmation email** exists in the inbox (`hard__gmail-calendar__003`) —
  with flight name, departure time, terminal. (If none, this task cannot extract details.)
- ☐ Starred emails / agent-created label removed; **sent-with-attachment email** deleted.
- ☐ `hard__contacts-gmail__026`: the contact email `yuvraj.mist@gmail.com` shows up in
  Gmail search (inbox/sent) so the "confirmed?" branch is reachable.

## §3 — Google Drive

- ☐ **Shared-with-me editable files** present (`medium__google-drive__007`) — count queryable.
- ☐ Largest-file check works (`medium__google-drive__001`) — main folder has files.
- ☐ **Shared budget spreadsheet** reachable from the secondary account
  (`hard__drive-notes-telegram__010`) with last-edit date vs the 2026-08-10 deadline.
- ☐ Clean up `Copy of SPORTS_VIDEO_DATA` leftovers; re-download the 5 uploaded files, then
  delete that Drive folder.

## §4 — Google Docs / Slides / Meet (cloud)

- ☐ **Google Slides deck** exists (`easy__google-slides__001`) — slide count queryable.
- ☐ **Google Docs doc** exists to rename (`easy__google-docs__004`).
- ☐ **Scheduled meetings** present today (`easy__google-meet__004`) and **Weekly Sync Mon 10 AM**
  with attendees (`hard__google-meet-files__070`).

## §5 — Chrome

- ☐ Earbuds **search history** from today present (`medium__chrome__003`).
- ☐ **Bookmarks added this month** present (`medium__chrome__011`) — filter + count works.
- ☐ (Cleanup) Remove run-created bookmark if any.

## §6 — Telegram

- ☐ **Forever 21 group unmuted**; meetup thread still **UNRESOLVED** — last message must be
  *"22nd could work for me too, let me confirm once she's free"* (no settled
  date/time/venue in the chat, so `hard__telegram-calendar__016` forces ask_user).
  **Do NOT re-add a settling message.**
- ☐ (Cleanup) Clear stale sent messages to Yuvraj Airtel from prior runs.

## §7 — YouTube Music / Music

- ☐ **Blinding Lights (The Weeknd)** present in **Recently Played** (`medium__music-telegram__001`)
  so the lyrics search resolves to a real song.
- ☐ (Cleanup) **'Chill Vibes' playlist** deleted; sleep timer cleared; any `Raining Night ASMR`
  download removed (`hard__music-obsidian__077` leaves these).

## §8 — Prime Video / Amazon / Swiggy / BookMyShow (cloud app state)

- ☐ **Prime Video**: "Continue Watching" has a recent title (`medium__prime-video__003`),
  Watchlist has TV Shows (`easy__prime-video__002`).
- ☐ **Amazon**: `[product]` currently in cart (`easy__amazon-shopping__002`).
- ☐ **Swiggy**: a recent order exists with a delivery status (`easy__swiggy__001`); last
  Friday's order present (`hard__swiggy__005`).
- ☐ **BookMyShow**: nearest cinema + this-weekend showtimes visible (`easy__bookmyshow__004`,
  `hard__bookmyshow__005`).

## §9 — Notes / Obsidian (app-private cleanups)

- ☐ Notes app: run notes deleted — **Card Payment Due**, **Budget Tracker**,
  **Birthday Reminders**, **IndiGo flight note**.
- ☐ Obsidian: run notes deleted (e.g. **Birthday Reminders**).
- ☐ Notes: **storage-limit note must be ABSENT** for `hard__files-notes__069` (hallucination control — the agent must honestly report there is no limit note; do NOT create one).

## §10 — Settings / other

- ☐ **Digital Wellbeing**: 30-min app timers the agent set → removed.
- ☐ **Camera**: run-recorded **'Camera Video'** clip deleted if present.
- ☐ Notifications/DND: default state (the YouTube/DND task sets it fresh each run).

---

## §11 — 🔴 RUN-DAY actions (do these ON the run day, not now)

- 🔴 **Make one real outgoing call to an unsaved number** (call log can't be seeded) —
  powers `easy__phone__005` ("calls made today") + the call branches of
  `medium__contacts__009`, `medium__contacts__012`, `medium__google-photos__008`.
  (If you don't want an actual call, at minimum ensure there's at least one call
  logged today so "calls made today" isn't a zero-answer edge case.)
- 🔴 Re-confirm device **date = run day** and that the **tomorrow-conflict events
  (Team Sync 14:00 + Mentor 1 on 1 14:30)** are still on **tomorrow** — if a day has
  passed, re-run Step 2b of the skill (re-seed tomorrow's conflicts).

---

## §10 — Long-run / launch-time operational items (2026-09-01)

- ☑ **Wireless ADB = Tailscale serial** `100.108.15.119:5555` (phone roams subnets; the LAN IP
  is unreliable). Reconnect: `adb kill-server` (if "No route to host" persists despite ping
  working), then `adb connect 100.108.15.119:5555`. Phone has `com.tailscale.ipn` on `tun0`.
- ☐ **Launch detached with stdin from `/dev/null`** — `nohup uv run dailybench_tasks.py ... < /dev/null > log 2>&1 &`.
  Without `< /dev/null` the batch dies with `Fatal Python error: init_sys_streams ... Bad file
  descriptor` when the launching terminal closes (this killed the 2026-09-01 mimo run mid-day1).
- ☐ **Start phoenix BEFORE the batch** (`start_phoenix.py --public --run-ts <TS>`, wait for :6006),
  else every task aborts with `PHOENIX_NOT_READY`. `nohup` both.
- ☐ **Resume-in-place**: `--run-root <same> --resume-from <next-task-id>` — find the next task id
  from the dead batch log's echoed `label dayN--...` lines (first label without `output.json`).
- ☑ **Model check**: `xiaomi/mimo-v2.5-pro` emits malformed `<parameter=message>` on the final
  `complete` call → every task grades FAIL at the last step (diagnostic only). `stepfun/step-3.7-flash`
  has `reasoning.mandatory: True` → must pass `--thinking`. Known-good: `bytedance-seed/seed-2.0-lite`,
  `qwen/qwen3.8-27b`, `moonshotai/kimi-k2.6`.
- ☑ **Amazon Music background playback** (controlled run env): whitelist it from OxygenOS
  virtual-freeze — `adb shell dumpsys deviceidle whitelist +com.amazon.mp3` +
  `cmd appops set com.amazon.mp3 RUN_ANY_IN_BACKGROUND allow` (+ in-Settings "Don't optimize" /
  allow background activity). OxygenOS freezes background apps (keeps them in RAM, SIGSTOPs them)
  → playback stops while the process survives.
- ☐ **Clear app search history/suggestions on every reset** (anti-cheat) — esp. YouTube search
  history + any saved-search rows, so the agent can't tap a pre-existing suggestion instead of
  typing the query.

---

## Which tasks are fully ADB-verified (won't surprise you)

Calendar (`easy__calendar__002`, `hard__clock-calendar__023`, `easy__calendar__008`),
Files/PDF (`medium__files__013/015/009`, `medium__files-pdf__001/002`, `hard__google-meet-files__070`
file side), Obsidian notes (`medium__calculator__001`, `hard__google-search-obsidian-telegram__057`,
`hard__music-obsidian__077` note side), Contacts (`easy__phone__002`, `medium__contacts__009/012`,
`hard__contacts-gmail__026` email side), gallery/screenshots (`easy__gallery__012`,
`medium__google-photos__012`, `easy__google-photos__015`), calculator/clock/settings,
plus the **7 hallucination controls** (`easy__calendar__008`, `easy__files__002`,
`easy__telegram__004`, `easy__contacts__008`, `easy__obsidian__009`, `medium__notes__004`,
`hard__files-notes__069`) which are honest-failure by design (their targets are deliberately absent).
