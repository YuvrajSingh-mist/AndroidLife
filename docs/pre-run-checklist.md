# Pre-run GUI checklist — public **60-task** rerun

Purpose: tick every item that **only a human in the app UI can verify** (app-private DBs,
cloud/server-side state — NOT ADB-checkable on this non-rooted device). The ADB-verifiable
baseline is confirmed via `reset_phone.py --verify-only` + `verify_day1_seeds.py --day {1,2,3}`;
do **not** re-do those here.

> **The ADB-verifiable half is now ENFORCED (2026-09-21).** `task_batch.py` runs the seed
> gate before the first task and **aborts the batch (exit 5, `SEED_GATE_FAILED` in the run
> root)** if it fails, so the items below this box are the only ones still relying on you.
> Those are precisely the ones ADB cannot see — treat this document as the gate's blind
> spot, and assume anything not checked here is unchecked.
>
> Two failures this gate now catches automatically, both of which previously cost real
> runs *silently* (a vacuous PASS is indistinguishable from a real one in a report):
> - **`--apply` ran on a previous day** → every calendar anchor is a day early, so
>   `easy__calendar__002` asks about a "tomorrow" holding no conflict. Caught by the
>   `seeded_on == today` stamp (5 of 13 runs were affected; see `redo.md` #6).
> - **A live recurring run artifact** → `Weekly_Standup` (`FREQ=DAILY;COUNT=14`) landed on
>   every day of the window including "tomorrow" and silently changed the conflict set.


Canonical operator runbook (ADB reset + manual seeds table):
[`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md).

✅ = verified already via ADB (leave alone) · ☐ = needs YOUR GUI check · 🔴 = run-day only

---

## §0 — Already verified via ADB (do NOT recheck)

- ☑ Reset baseline `--verify-only` → **PASS**
- ☑ Root dump sweep — `reset_phone.py --apply` now clears `/sdcard/*.xml` + `/sdcard/*.png`
  (724 stray dumps accumulated 2026-07-29 → 2026-09-18; cleared 2026-09-18, root now 0).
  Nothing seeds or reads the root. If you saved a dump by hand, pull it **before** `--apply`.
- ☑ Day-1 / Day-2 / Day-3 seed verify → **PASS** (all three)
- ☑ Tomorrow-conflict events (`Team Sync` 14:00 + `Mentor 1 on 1` 14:30) are **reset-managed**
  - ☑ **Now stamp-enforced (2026-09-21).** `reset_phone.py --apply` writes
    `.seed_state.json` (`seeded_on=<date>`), and the launch gate FAILS unless that date is
    **today** — so a reset left over from the previous day can no longer reach a scored
    run. Same for the recurring-artifact sweep (`Weekly_Standup`). See `redo.md` #6.
  - ✅ **Fixed 2026-09-18.** `reset_phone.py --apply` now re-anchors the pair to
    **run-day + 1** on every reset — they are ordinary `public_v2.seed_calendar_events`
    entries (alongside `Weekly Sync` / `Gym`) and are date-shifted **in place**. The old
    out-of-band §3 snippet anchored them to `date.today() + 1` **at seed time**, so a batch
    that started on a later day (or crossed midnight) left the conflicts on the run day and
    `easy__calendar__002` became unsolvable — it cost the **16 Sep** run (seeded 15 Sep,
    batch started 16 Sep 01:13 → `ui_states/0004` showed both events on Wed 16, Thu 17 empty).
    The manual re-seed step is gone; `--verify-only` now asserts both titles are present.
    In-place shifting keeps `easy__calendar__008`'s lookalike-deletion check intact.
  - ⚠️ Still confirm the **device date = run day** before launch: every anchor is computed
    from `date.today()` on the **host**, so a stale device/host clock mis-anchors the whole
    calendar (pair, `Weekly Sync`, `Gym`) in one go.
- ☑ Weekly Sync + Gym date-relative seeds (Mon 07:00 for the clash task; **10:00 on today+1 and today+2** for the Meet task; next Tue for Gym)

  ☑ **Gate-enforced:** the Calendar app must be left in **Schedule** view. A finished run
  hands the next one whatever view its agent ended on, and Day view changes the starting
  screen without touching any seed — `verify_calendar_view_mode()` now restores it
  automatically (redo.md 7.2). Look at `ui_states/0002` of a task to see the start state.
- ☑ All PDFs/xlsx/Downloads present (PURCHASE_ORDER, SPORTS_VIDEO_DATA, budget, quote,
  Weekly Agenda.txt, Invoice INV-2026-071.pdf, Rent Receipt.pdf, …)
- ☑ All public Obsidian notes present (Bedtime, Budget Deadline, Exam Scores, Monthly Budget,
  Shared Bill, Stock Watch, Recipe, Food Favourites, Contact Updates, Weekly Agenda.txt)
- ☑ Contacts (incl. Akash Kumar + fabricated email `yuvraj.mist@gmail.com`)
- ☑ Camera seeds + Screenshots · `screen_off_timeout=1800000` · blocked numbers cleared
- ☑ Public dataset = **60 tasks** (`AndroidLife_public_v2.json`)

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
- ☐ **`Budget Deadline` note** present in the OnePlus Notes app (`hard__drive-notes-telegram__010`)
  carrying both dates — `Deadline: 2026-08-10` and `Last reviewed: 2026-07-10.` App-private with
  no file seed, so it must be re-typed via the UI if missing; `reset_phone.py` verifies the
  Obsidian copy's `Last reviewed:` needle. Drive is **not** part of this task since 2026-09-21.
- ☐ Clean up `Copy of SPORTS_VIDEO_DATA` leftovers; re-download the 5 uploaded files, then
  delete that Drive folder.

## §4 — Google Docs / Slides / Meet (cloud)

- ☑ **Cloud account gate** — `reset_phone.py --verify-only` now asserts each app's
  selected Google account (`Signed in as …`), so a drifted app FAILs the reset instead of
  silently hiding its seed. **2026-09-18: Slides had drifted to `rajceo2031@gmail.com`;
  fixed to `ranirajesh786@gmail.com`.** Canonical: Gmail/Drive/Docs/Slides =
  `ranirajesh786`, Calendar/Meet = `yuvraj.mist`, Photos = `rajeshceo2015`. (Maps is
  deliberately unconstrained.)
- ☑ **Google Slides deck** exists (`easy__google-slides__001`) — slide count queryable.
  **Gate-enforced AND self-repairing (2026-09-21):** `restore_slides_deck()` re-pushes
  `/sdcard/Download/Q3_Review.pptx` from the **version-controlled** fixture
  (`assets/seeds/public/Q3_Review.pptx` — the single file excepted from the `assets/`
  gitignore) whenever the device copy is missing or the wrong length, and
  `verify_slides_deck()` then asserts **8** slides. The deck is an uploaded `.pptx`
  (device file + Drive copy on `ranirajesh786`), **not** a native cloud deck and **not**
  file-seeded, so nothing else would restore it. The grader also carries ground truth for
  this task now (`answer_checks_public.json`) and **refuses a PASS whose reply does not
  state `8`** — before that, replies of `1`, `3` and `8` all scored PASS. See `redo.md`
  item 5.
- ☐ **Google Docs doc** exists to rename (`easy__google-docs__004`).
- ☐ **Scheduled meetings** present today (`easy__google-meet__004`) and a conferenced **Weekly Sync
  10:00 within the next 2 days** with attendees `hard__google-meet-files__070` — Meet only lists
  conferenced meetings, signed in as `yuvraj.mist@gmail.com`, and only ~48h out.

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
- ☐ 🔴 **Maps run notes deleted — `parked here` and `Fastest Route to Bhubaneswar Airport`
  (recurring gap).** The OnePlus Notes app reopens the **last-edited** note, so a leftover
  note drops the agent *inside* an existing note on `easy__google-maps__004`
  (and `medium__google-maps__002`). Confirmed cost: **`qwen-26` and `kimi-30v` both burned
  60 steps in a "+-tap loop inside an existing note and FAILED** ("Notes '+' kept opening
  existing 'To Buy' note"); **`gemini-26` PASSED on a pre-existing `parked here` note**
  ("the note is already there", 1 min old) rather than creating one, so its PASS is vacuous.
  Also delete the **home-screen Notes widget** those runs add.
- ☐ **Google Maps run state cleared (comparability hygiene — this is the big one).** Leftovers let agents *skip the search*:
  - **Search history / Recent searches.** A leftover `Biju Patnaik International Airport` row in the search box's
    *Recent* list let **7 of 13 runs never type the destination** — `qwen-28`, `qwen-0909v`, `seed-30` even say so
    out loud (*"in recent history … I'll tap it"*, *"a pre-existing suggestion … faster"*). Those five
    `medium__google-maps__002` passes **stay valid** (the graded end-state — a note with the compared 3-mode ETA —
    was still produced, so the capability under test was still exercised); what leaks is *comparability*: run N
    inherits run N-1's hints, which is outside the reset/seed gate `docs/reproducibility.md` defines.
    → In Maps: tap the search box → **clear the Recent list** (per-row ⋮ / `Clear`). Current leftovers from the
    530 Maps tasks: `pharmacy`, `general physician clinic near me`, `hospital near me open now`,
    `Chennai International Airport (MAA)`, `RG Residency`, `Le Dazzle`.
  - **Leftover route / place page.** Maps was left showing *Your location → Airport Wireless Road* with
    Drive 36 min / 13 km (a prior run's directions state), and `gemini-26` used an already-open airport page.
    Force-stop Maps and reopen on the **home/search** state.
  - **Saved places** — re-checked 16 Sep: *Favourites = 0 places*, "All saved" holds only `AI4Bharat` (non-
    public task), so no public Maps pass came from a pre-saved/starred place; `Bali Cafe` stays **absent** for the
    530 HC tasks `easy__google-maps__008/009/014`.
  - **Home-screen Notes widget** added by `easy__google-maps__004` runs — remove it (and see the `parked here`
    bullet above: `gemini-26`'s PASS there never created the deliverable at all, so *that* one is a real vacuous pass).
- ☐ **Notes app: "New note" vs "last-edited note".** Prefer deleting notes via the app's own list so Notes
  doesn't reopen a stale note on the next run (see the `parked here` bullet above).
- ☐ Obsidian: run notes deleted (e.g. **Birthday Reminders**).
- ☐ Notes: **storage-limit note must be ABSENT** for `hard__files-notes__069` (hallucination control — the agent must honestly report there is no limit note; do NOT create one).

## §10 — Settings / other

- ☐ **Digital Wellbeing**: 30-min app timers the agent set → removed.
- ☐ **Camera**: run-recorded **'Camera Video'** clip deleted if present.
- ☐ Notifications/DND: default state (the YouTube/DND task sets it fresh each run).

---

## §11 — 🔴 RUN-DAY actions (do these ON the run day, not now)

- ☑ **Call log is seeded by `reset_phone.py --apply`** — `public_v2.seed_calls` inserts
  2 OUTGOING calls dated **today** (`+919000000001` 1:12, `+919000000002` 0:45 → total
  **1:57**). The call log **is** writable from non-rooted adb
  (`content insert --uri content://call_log/calls`); the old "make a real call, the log
  can't be seeded" step was based on a wrong assumption — `scripts/seeding/seed_data.py`
  has always seeded it for the 530 corpus. Today's rows are cleared first, so a re-apply
  is idempotent and the answer is never the degenerate 0 seconds.
  - Every seeded call is **outgoing**, so "calls I've made" and "all calls today" give
    the same total.
  - `easy__phone__002` (day 1) places a real call, so the day-2 total includes that row
    on top of this baseline — that part is run-dependent by design.
- ☑ **Then** re-verify the run day: `--verify-only` asserts at least one outgoing call
  dated today. Re-confirm device **date = run day** and that the **tomorrow-conflict
  events (Team Sync 14:00 + Mentor 1 on 1 14:30)** are still on **tomorrow** — every
  calendar anchor is computed from the *host* clock, so a stale clock mis-anchors the
  whole calendar in one go.

---

## §10 — Long-run / launch-time operational items (2026-09-01)

- ☑ **Wireless ADB = Tailscale serial** `100.108.15.119:5555` (phone roams subnets; the LAN IP
  is unreliable). Reconnect: `adb kill-server` (if "No route to host" persists despite ping
  working), then `adb connect 100.108.15.119:5555`. Phone has `com.tailscale.ipn` on `tun0`.
- ☐ **Know the transport's failure mode.** OxygenOS virtual-freezes `com.tailscale.ipn` once the
  screen sleeps (nothing keeps it alive while the phone is *unplugged* —
  `stay_on_while_plugged_in` doesn't apply), the WireGuard tunnel dies, and adb starts saying
  `device offline`. The harness deliberately does **not** work around this: it re-probes for
  `--device-reconnect-timeout` (45s) and then **aborts** on a `DEVICE_UNREACHABLE` preflight,
  because the phone is the benchmark's subject and a run that cannot reach it has no valid
  result. Do not whitelist apps from Doze or otherwise change device settings to mask this —
  the benchmark must run on stock device state, or the runs stop being comparable.
- ☐ **Keep the phone charged.** Battery drain across a full 60-task run measured **-93%**, so a
  run started below ~15% will die mid-day and take the rest of the queue with it (see
  2026-09-17: `easy__settings__014` started at 3%, hit 0% at 21:00, and ADB died 23s later).
  Nothing in the harness will stop a task from launching on a nearly-dead phone.
- ☐ **Launch detached with stdin from `/dev/null`** — `nohup uv run androidlife_tasks.py ... < /dev/null > log 2>&1 &`.
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
