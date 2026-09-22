# Redo queue — tasks to re-run

Local working note (gitignored). Tasks whose recorded results are **not trustworthy**,
why, and what to do before re-running. Not a changelog — only things we owe a re-run.

---

## 1. `medium__google-maps__002` — Google Maps + Notes (medium, 3pt, day 1)

**Verdict: every recorded result is a vacuous PASS — the search was never performed.**

The task asks the agent to compare driving / transit / walking ETAs in Maps for
`[place]` (= `Bhubaneswar Airport`, which Maps resolves to *Biju Patnaik International
Airport*) and save the fastest one to Notes. **No run ever typed the query.** Maps'
recent history and/or a leftover open route already contained the airport, so the agent
taps what is already on screen and the grader sees the right end state.

| Run | Typed the airport query? | What it actually did | Recorded |
|---|---|---|---|
| qwen-28 | no | "I see 'Biju Patnaik International Airport' in recent history — I'll tap it." | ✅ vacuous PASS |
| qwen-0909v | no | "…in recent history" | ✅ vacuous PASS |
| seed-30 | no | "there's a pre-existing suggestion … I can click that directly instead of typing, which is faster" | ✅ vacuous PASS |
| gemini-26 | no | went straight to a Directions button on an already-open airport page | ✅ vacuous PASS |
| qwen35-0914 | no | "the driving mode is already selected showing 24 minutes" — live leftover route | ✅ vacuous PASS |
| mimo-0901 | no | "recent search history" → tapped it | ❌ FAIL (malformed) |
| gemma-0917v | **yes** | typed `Bhubaneswar Airport`, reached the airport page, then **tapped Start and began live turn-by-turn navigation** (32 min / 13 km) — never compared modes, never saved the note | 🚨 HALLUCINATION |

Established by tracing every run's tool calls for a `type` / `type_text` of the airport
query. The 17 Sep vision run is the first that *did* type it, and it still failed — so the
free-pass mechanism above is about the earlier runs only.

**Root cause:** Maps is not returned to a clean search state between runs, so a prior
run's query / route leaks forward and satisfies the task for free where no query is typed.

**Before re-running:**
- Clear Maps search history + recent destinations, and stop any leftover active route.
- **Specifically stop leftover live navigation.** On 17 Sep the agent tapped *Start* on the
  airport route and nothing cancelled it; a Maps element then sat on top of **26 of the 27
  tasks** (552 a11y states across 472 files), with the navigation bubble reading
  `Hostel Rd` in 21 of them — so every later task was observed through it. Only the first
  task, which ran before Maps, was clean. Stop navigation (or reboot) between Maps and the
  next task as well as before the run.
- Confirm the airport is **not** pre-suggested when you open the search box.
- Then re-run on that clean state.
- Consider tightening the grade so it also asserts the query was typed — otherwise a
  pre-existing suggestion can keep satisfying it.

---

## 2. `hard__google-meet-files__070` — Google Meet + Files (hard, 5pt, day 3)

**Verdict: failed in all 11 recorded runs (10 on the current leaderboard). The cause is
now fixed, so these need a re-run on the new seed.**

> The other Meet task, `easy__google-meet__004` (day 2, easy), is **not** on this list —
> its recorded mix of PASS/FAIL traces to ordinary model errors (3 AM vs 3 PM, garbled
> invitee field, step caps), not to a broken seed. It is however the source of the
> `Product Demo` contamination noted below.

The failure was **never the account** — one report (`public-20260826-105200.md`) claims
"account mismatch / Rani Singh", and that is wrong. The real causes were:

1. the seeded `Weekly Sync` carried **no Meet conference link**, and Meet's "Scheduled"
   list only ever shows conferenced meetings;
2. Meet's "Scheduled" list only covers **~48h**, and the seed was Monday-anchored — so
   it sat 3–6 days out whenever a run started midweek, and Meet showed nothing.

**Fixed 2026-09-17** (`d26932d` main, `b4a544a` website):
- Meet links added by hand to the two offset-anchored seeds (`wph-bgoe-eye`, `ruo-uxua-pfr`);
- `reset_phone.py` now **shifts seeds in place** so those links survive every reset;
- the agenda meeting is anchored at **today+1 / today+2** (always inside the 48h window);
- the prompt no longer hardcodes "Monday".

**Before re-running:**
- Run `reset_phone.py --apply` **on the run day** (anchors are date-relative). This is
  the only thing "re-seed on the run day" means — there is **no new time to pick**; the
  meetings stay at 10:00 and only the dates shift to today+1 / today+2.
- Then run `reset_phone.py --verify-only`, which now **gates on this task**: it fails
  loudly if the anchor is stale (outside Meet's ~48h window), if the Meet link is gone,
  or if Meet's "Scheduled" list does not actually show `Weekly Sync` (wrong account).
  A broken seed can no longer silently cost a FAIL.
- **Watch for `Product Demo` contamination.** The day-2 task `easy__google-meet__004`
  creates a *conferenced* "Product Demo" event, which then shows up in Meet's list on
  day 3. Several of the recorded failures cited exactly this — the agent reported
  "Product Demo" instead of the seeded `Weekly Sync`. Clear any leftover "Product Demo"
  events before the day-3 Meet task runs.
- The links persist through resets; they only need re-adding if the events get deleted.

> ### ⚠️ 2026-09-21 CORRECTION — the 2026-09-17 fix was NOT sufficient
>
> **This task is still unsolvable as seeded, and cannot be made solvable by resetting.**
> The 17 Sep fix assumed the blocker was the link and the 48h window. Both were real, but
> neither was the whole cause. The real blocker is that **Meet is a cloud app and the seed
> is a local database**:
>
> - Meet lists what exists on **Google's servers**, not what is in the phone's
>   `com.android.calendar` provider. `content insert`/`update` writes only the local copy.
> - Measured on the live device: the seeded rows carry `_sync_id`s (so they reached Google
>   *once*, when the links were added **by hand in the app UI**), but every later adb
>   date-shift sits at `dirty=1` **forever** — it never uploads.
> - Both documented ways to force a sync are **no-ops on this build**. `content call
>   --method forceSync` prints `Result: null` and `am broadcast -a
>   android.content.SyncAdapter` returns `result=0`; logcat during both shows **zero sync
>   activity**. There is no public force-sync API for a third-party account.
> - So the in-place shift added on 17 Sep *does* preserve the link (good) — but it moves
>   the meeting to a date the **server never learns about**, and Meet keeps showing the
>   stale server-side date, which by then is in the past.
>
> **Net rule: adb calendar writes never reach the cloud. Only app-UI writes do.**
> Evidence that app writes upload: the leftover `Weekly_Standup` from the 17 Sep run was
> agent-created in the UI and synced fine (`dirty=0`).
>
> **The fix that will actually work** (one-time, ~2 min, do it on the run day):
> 1. Open **Google Calendar** signed in as `yuvraj.mist@gmail.com`.
> 2. Create a **recurring DAILY** event `Weekly Sync` 10:00–11:00 **with a Meet
>    conference + attendees** (Daily ⇒ there is *always* an occurrence inside Meet's 48h
>    window, so it never needs re-uploading and never goes stale).
> 3. Delete the adb-seeded `Weekly Sync` copies so the reset stops shifting them, and add
>    the recurring series to an exclusion so `--apply` leaves it alone.
>
> Until that is done, `reset_phone.py` reports this check as a **WARN** (not a FAIL) so the
> launch gate stays usable; `--meet-strict` re-arms it once the seed is fixed.

**Expect the numbers to move** once it is fixed — but note the post-fix runs will not be
comparable to the 11 on record, and the earlier "this is now solvable" claim above was
wrong: every recorded run failed, and none of them failed for a reason a reset could fix.


---

## 3. `hard__bookmyshow__005` — BookMyShow + Telegram (hard, 5pt, day 2)
**Verdict: the `[cinema]` placeholder named a cinema that does not exist. Failed in every
recorded public run. Vars fixed 2026-09-18 — all models need a re-run.**

`public_vars.local.env` resolved the placeholder to `cinema=INOX Bhubaneswar`. BookMyShow
has no listing by that name. Its Bhubaneswar cinemas are:

- `INOX: Symphony Mall`
- `INOX: DN Regalia Mall`
- `INOX: BMC Bhawani Mall`
- (plus `Cinepolis: Nexus Esplanade, Bhubaneswar`, `PVR: Utkal Kanika Galleria, Bhubaneswar`)

BookMyShow's search is **literal**, so typing the placeholder verbatim returns
**"Sorry! No result found"** — reproduced in the 17 Sep vision run
(`hard-bookmyshow-005/.../ui_states/0003`), which tried it once and returned `success=false`
after 4 steps. The 16 Sep run only found the cinemas because it happened to browse the
`INOX` prefix instead.

**Fixed 2026-09-18:** `cinema` is now **`INOX: Symphony Mall`** (an exact live listing) in
`src/androidlife/user_config.py`, `config/user_config.example`, and the
`public_vars.local.env` / `tasks_vars.local.env` copies under `benchmarks/`.

> ### ⚠️ 2026-09-22 — the fix was NOT in effect; re-verified live before re-running
>
> **The fix missed the one file the runner actually reads.** `config/user.yaml` is
> **gitignored** (machine-local persona config), so a "fixed in all five places" commit could
> not touch it, and because `load_user_config()` merges it *over* the shipped defaults it
> **overrode** the corrected value:
>
> | Layer | `cinema` | Actually used? |
> |---|---|---|
> | `src/androidlife/user_config.py` (shipped default) | `INOX: Symphony Mall` ✅ | no — overridden |
> | `config/user_config.example` | `INOX: Symphony Mall` ✅ | no |
> | `benchmarks/.../public_vars.local.env`, `tasks_vars.local.env` | `INOX: Symphony Mall` ✅ | no — not passed by the launcher |
> | **`config/user.yaml`** (gitignored, the runner's `--config` default) | ~~`INOX Bhubaneswar`~~ ❌ | **YES** |
>
> Proof, through the runner's own resolution path: `var_map(load_user_config())` returned
> `cinema = 'INOX Bhubaneswar'`. A 13-row re-run staged against that value would have
> re-run the *defect*, not the fix. Corrected in `config/user.yaml` 2026-09-22, and
> `scripts/tools/verify_task_vars.py` now renders the resolved task vars and **fails the
> launch** on a known-bad value — the runner only guards a *missing* placeholder, never a
> wrong one, which is why this slipped through twice.
>
> **Live re-verification on the run day (2026-09-22, device `CPH2423`).** BookMyShow
> Bhubaneswar still lists `INOX: Symphony Mall` (first result), `INOX: DN Regalia Mall`,
> `INOX: BMC Bhawani Mall`. So the pinned value is current.
>
> **Correction to this section's own claim: the search is not strictly literal.** Typing
> `INOX` — or even a mangled `INOX Bhuneswar` — surfaces the real INOX venues, so the task is
> reachable by browsing the prefix. What returns `Sorry! No result found` is the **exact
> phrase** `INOX Bhubaneswar`, confirmed in row 12's own `ui_states/0003`. The defect is
> therefore *ambiguity*, not unreachability — but pinning a real listing is still the right
> fix for a `DETERMINISTIC` task.
>
> **The recorded history is more mixed than "every run failed this task"** (all live pulls
> from the Hub, `day2/hard-bookmyshow-005/output.json`):
>
> | row | run | outcome | reply / reason |
> |---|---|---|---|
> | 3 | `20260826-105200` | `success=true`, 7 steps | `INOX: Symphony Mall, Toxic…, 07:00 AM` — **correct cinema**, failed only at the harness Send step |
> | 6 | `20260905-051950` | `success=true`, 18 steps | replied `INOX Bhubaneswar` — the **placeholder**, not a listing |
> | 10 | `20260916-011341` | `success=true`, 18 steps | replied `INOX Bhubaneswar` — graded 🚨 **HALLUCINATION** ("wrong cinema label") |
> | 8 | `20260910-041531` | `success=false` | "`INOX Bhubaneswar` was not found in BookMyShow" |
> | 12 | `20260917-160018` | `success=false`, 4 steps | "Sorry! No result found" at `ui_states/0003` |
> | 1,1,2,5,11,+ | … | `success=false` | step-capped at 60 (or malformed tool-call ×3) |
>
> Two consequences for interpretation:
> 1. **Rows 6 and 10 "succeeded" by echoing the placeholder back** — `INOX Bhubaneswar` is
>    not a cinema BookMyShow lists. Row 10 was correctly graded a hallucination; **row 6 was
>    graded `❌ FAIL — ASK USER — 0 asks (gate FAIL)`, but this task is `DETERMINISTIC`
>    (`is_ask_user: false`)** — an ASK USER gate applied to a non-ASK-USER task. The verdict
>    (FAIL) may still be right, but that stated reason is not.
> 2. So the redo premise "**failed in every recorded public run**" is wrong: at least one run
>    (row 3) produced the correct cinema+showtime and failed on delivery, and two others
>    replied with the non-existent placeholder. Row 3's is the only genuine solve, and it was
>    a **harness** failure.
>
> **Still open, for a verdict pass after the re-run:** there is no `answer_check` for this
> task, so a reply naming a non-existent cinema (`INOX Bhubaneswar`) is not machine-checkable
> — every graded judgement here came from a human reading the reply.

**Before re-running:**
- ✅ **Re-verified live 2026-09-22** — `INOX: Symphony Mall` is still the first Bhubaneswar
  result. ✅ **`config/user.yaml` corrected 2026-09-22** (it was silently overriding the fix —
  see above), and `scripts/tools/verify_task_vars.py` now gates the launch.
- Keep `ticket price=₹240`.
- This task touches live data (showtimes for "this weekend"), so re-verify on the run day
  like the docs already require for the other live-data tasks.
- ⚠️ **Verdict pass needed afterwards:** rows 6 and 10 recorded "success" while replying the
  non-existent `INOX Bhubaneswar`, and row 6's stated FAIL reason (ASK USER gate) does not
  apply to a `DETERMINISTIC` task. See the table above.

> ### 2026-09-22 re-run — 9 of 13 rows done, and a delivery defect it exposed
>
> Rows 1–5 and 7–10 have run; **6, 11, 12 and 13 still need one** (the host rebooted mid-batch
> at ~15:02 and took the detached launcher with it — `start_new_session=True` survives the
> shell and Cursor dying, not a reboot — and the handset then dropped off the network, so the
> batch cannot resume until it is reachable again).
>
> | row | model | `success` | delivered? | verdict |
> |---|---|---|---|---|
> | 3 | gemini-3.1-flash-lite (text) | `true` | ❌ left in the composer | **FAIL** (demoted) |
> | 4 | seed-2.0-lite (text) | `true` | ❌ Telegram never launched | **FAIL** (demoted) |
> | 5 | qwen3.8-27b (vision) | `true` | ✅ real sent bubble | **PASS** — the first genuine solve |
> | 7 | gpt-5.6-luna (text) | `false` | — | FAIL (honest) |
> | 8 | gpt-5.6-luna (vision) | `false` | — | FAIL |
> | 10 | gemma-4-E2B-it (text) | `true` | ❌ typed into Telegram's search box | **FAIL** (demoted) |
> | 1, 2, 9 | qwen3.8-27b / kimi-k2.6 / Qwen3.5-4B | `false` | — | FAIL (step cap) |
>
> **The defect: `success` cannot tell a send from a near-miss.** Three rows scored a pass while
> delivering nothing, each in a different way — row 3 typed the plan and never tapped Send
> (the leak cleanup recovered it as a live draft, `draft='INOX: Symphony Mall, Avengers
> Endgame: Encore, 07:15 PM'`); row 4 could not launch Telegram at all (it used the
> non-existent package `org.telegram.messaging`, which every other row resolved correctly to
> `org.telegram.messenger`) and called `complete(success=true)` anyway; row 10 typed the whole
> message into Telegram's **search box** and never opened the chat. Row 10 is the instructive
> one: its final UI state is a chat *list* with the composer empty, so nothing inside the chat
> looks wrong — the tell is that the message text is sitting in the search field.
>
> **Fixed, in the same one-directional style as `answer_check`:** `reset_phone.py
> --delivery-probe` reads the device-side fact (a "Sent at" bubble under today's separator in
> the `Yuvraj Airtel` chat) and the launcher writes it to `delivery.json` before the leak
> cleanup deletes the bubble. `androidlife_report.py` then demotes a self-reported success when
> a required-delivery task has evidence that nothing was sent. It only demotes on *definite*
> evidence: an unreachable chat, or a run taken before the probe existed, keeps its own
> outcome. The sidecar `benchmarks/androidlife-530/delivery_checks_public.json` lists the task,
> and it must stay **opt-in** — `hard__drive-notes-telegram__010` ("message … if it hasn't been
> updated by the deadline"), `hard__chrome-telegram-notes__008` (only over $10) and
> `hard__google-search-obsidian-telegram__057` (only if it crossed the threshold) all have
> *conditional* sends, so gating them would fail a correct decision not to send.
>
> Today's rows predate the probe, so their evidence was recovered from the leak-cleanup logs —
> the same two functions (`_tg_run_window_bubbles` / `_tg_draft`), run at the same moment —
> by `scripts/tools/backfill_delivery_evidence.py`. Re-running the grader over the 7 rows
> demotes exactly 3, 4 and 10 and leaves row 5's pass intact.
>
> **Also fixed in the harness (all committed):** `--leak-cleanup-only` between rows (the gate
> is verify-only, so one row's leftover draft used to abort every row after it — the first
> 2026-09-22 attempt lost rows 3–13 to row 2's unsent plan); a retry on transient seed-gate
> UI-read failures; the Telegram bubble deletion, which had **never** worked because the
> selection bar's `Delete` carries its label in `content-desc` rather than `text`, so it
> always reported "long-press menu did not appear" while the menu was on screen; and a retry
> in `_tg_open_chat`.
>
> **Still open:** run rows 6, 11–13 with the probe active, then do the verdict pass below.

> ### 2026-09-22 (later) — row 6 hit a `400` on BookMyShow, and it was *state*, not network
>
> Row 6 died at step 2 on an app error page, so the batch was stopped to diagnose it:
>
> ```
> com.bt.bms:id/no_network_error_container
> Sorry! Request failed
> It seems like we are encountering some issues at our side. Please try again.
> (Error code: 400).
> ```
>
> **The tell is the container: `seat_quantity_container`.** That is the *seat-selection*
> page — reachable only after choosing a movie, cinema and showtime — and it appeared one
> step after the splash, before the agent had done anything. BookMyShow had been **resumed
> into a previous run's unfinished booking**: row 10 (`20260922-140420`, 14:04) drove the
> app into seat selection and left it there (its own narration: *"the screen has changed to
> a seat selection interface… I see a 'How many seats?'"*). Row 6 started at 16:57, its
> `open_app` brought that stale task to the foreground instead of cold-starting, and
> BookMyShow answered the dead session with `400`.
>
> **It is not a network fault.** Verified on the device during the diagnosis: `ping 8.8.8.8`
> 0% loss, Wi-Fi on, airplane mode off, and BookMyShow opens to a normal home page
> (Bhubaneswar, movies listed). `am force-stop com.bt.bms` → relaunch lands cleanly on
> `MainActivity`. Blast radius was **1 of 13 rows**: rows 1, 5 and 10 also reached seat
> selection without erroring, because each was cold-started.
>
> **Why the reset missed it.** The pre-run reset (`cli.py`, §7.4) force-stops only the app in
> the **foreground**. BookMyShow was *backgrounded* (the foreground was Telegram), so it was
> never touched, and a backgrounded app keeps its UI state. The fix force-stops **the task's
> own apps** as well:
>
> * `src/androidlife/app_packages.py` — the app-name → package map, moved out of
>   `scripts/tools/app_audit.py` so the audit and the runner share one source of truth.
> * `adb.stop_packages()` — best-effort force-stop of a package list, reusing
>   `should_force_stop` so a protected/system package can never be killed. Force-stop kills
>   the process **without clearing app data**, so a signed-in app stays signed in — it is
>   deliberately not `pm clear`.
> * `cli.py --pre-app-reset-packages` — stopped before the agent starts, and recorded in
>   `meta.json` as `pre_app_reset_stopped_packages` so each run says what it actually reset.
> * `task_batch.py` resolves the dataset's per-task `apps` field (all 60 tasks declare one;
>   `hard__bookmyshow__005` → `['BookMyShow', 'Telegram']`) and passes the packages through.
>
> Verified on the device: with BookMyShow in the foreground, `stop_packages(['com.bt.bms',
> 'org.telegram.messenger'])` returns both, the focus falls back to the launcher, and no
> `com.bt.bms` process remains.

---

## 4. `hard__drive-notes-telegram__010` — Notes + Telegram (hard, 5pt, day 1)

**Verdict: two benchmark-level defects — a missing app-private seed and an oracle naming a
file that never existed. ✅ BOTH FIXED 2026-09-21; this needs a re-run, not a code fix.**

The prompt named "my 'Budget Deadline' note", and the task also sent the agent to a Drive
spreadsheet described **only** in the oracle. Both halves were broken:

- the note lives **only** in the OnePlus Notes app (`com.oneplus.note`), which has no file
  seed, so it kept disappearing and nothing could restore it;
- the oracle directed the agent to a Drive file that does not exist anywhere.

The fix drops the Drive half entirely and turns the note's text into a tracked file seed.

Two pre-run UI dumps bracket the note's original loss:

| Dump | Date | Notes listed |
|---|---|---|
| `notes_final.xml` | 2026-08-30 | **`Budget Deadline`** + 7 others |
| `notes_now.xml` | 2026-09-16 | 8 notes, **no `Budget Deadline`** |

The 17 Sep run opened OnePlus Notes, searched `Budget Deadline`, and correctly got
"No results" — the task was genuinely unsolvable that day.

**Why the note kept vanishing:** it is an **app-private `needs_ui` seed with no file seed**.
`build_day_seed_manifest.py` records it as `{"type": "notes", "location": "Notes app
(app-private)", "status": "needs_ui"}`. `reset_phone.py` only *deletes* run-created notes
from that app; it cannot create this one. `docs/fabricated-test-data.md` says it was enriched
through the app UI — that edit does not survive a wipe, exactly as the doc warns
("re-applied via UI if ever reset"). It is now re-typed before each batch, and its text is
version-controlled.

> ### ✅ 2026-09-21 RESOLVED — Drive dropped, oracle fixed, seed re-typed
>
> **Defect 1 — the oracle named a Drive file that never existed.** The public ground truth
> told the agent to chase `family_numbers.xlsx`, but the device only ever held `budget.xlsx`:
>
> | Source | Named |
> |---|---|
> | public `ask_user_facts_public.json` + dataset | `family_numbers.xlsx` ❌ |
> | 530 twin (`ask_user_facts_530.json`) | `shared budget.xlsx` |
> | seed manifest (`build_day_seed_manifest.py`) | *"operator ensures the shared **budget.xlsx** exists in Drive"* |
> | `reset_phone.py` `seed_files` | `/sdcard/Download/budget.xlsx` |
> | **the device, observed 2026-09-21** | **`budget.xlsx`** (Microsoft Excel, Modified Aug 14) |
>
> Drive search for `budget.xlsx` returned exactly that one file; a search for `family`
> returned only stray images and a PDF — **no `family_numbers.xlsx`, no spreadsheet**.
> `family_numbers` appears in **0** of the 55 `ui_states` across the two runs that actually
> reached Drive.
>
> This had already corrupted a published verdict. `public-2026-08-30-143554.md` records
> `hard__drive-notes-telegram__010` as a FAIL partly because the agent "used `budget.xlsx`
> (ground truth `family_numbers.xlsx`)" — that specific criticism is **backwards**: the agent
> used the only file that exists. (The FAIL stands on its other grounds — it never asked
> which spreadsheet, missed the 08-10 deadline, and never messaged.)
>
> **Fix:** the public oracle now reads *"Message Yuvraj Airtel. The note you want is
> 'Budget Deadline'."* — and **Drive is out of the task altogether**, so there is no filename
> left to disagree about.
>
> **Defect 2 — the note was self-mutating and unresettable.** The prompt instructed the agent
> to *"log today's check date in the note"* on the not-overdue branch, so a run can **write
> into the very seed it is graded against**. The OnePlus Notes copy is app-private:
> `reset_phone.py` can only *delete* run-created notes, so it cannot restore this one, and
> `--verify-only` reads the content provider only — it is blind to `com.oneplus.note`.
> Evidence it really happened: the 2026-08-30 run read a note carrying *"prior check dates
> 2026-08-24 and 2026-08-28"* that the file seed does not contain.
>
> **Fix:** the note was re-typed through the Notes UI on 2026-09-21 carrying real budget
> figures plus both dates, and that exact text is now the tracked file seed
> `assets/seeds/public/notes/Budget Deadline.md` (generated by `enrich_public_notes.py`,
> restored by `reset_phone.py`). `reset_phone.py` still **deletes run-created notes by title
> and never sweeps by date**, so the seed survives a batch.
>
> **What changed**
>
> | File | Change |
> |---|---|
> | `public.md` | prompt → "Open my budget note in the Notes app and compare the last-reviewed date recorded in it against the finalisation deadline recorded in the same note"; header `[Drive+Notes+Telegram]` → `[Notes+Telegram]` |
> | `ask_user_facts_public.json` | `family_numbers.xlsx` → `"The note you want is 'Budget Deadline'."` |
> | `assets/seeds/public/notes/Budget Deadline.md` | real budget data + `Deadline: 2026-08-10` + `Last reviewed: 2026-07-10.` |
> | `enrich_public_notes.py` / `reset_phone.py` / `build_day_seed_manifest.py` | same text as the seed source / restore entry / manifest |
> | on-device `com.oneplus.note` | note re-typed via the UI 2026-09-21 |
>
> The `task_id` comment is untouched, so the artifact path stays
> `hard-drive-notes-telegram-010` and history remains comparable by path.
>
> **This is a deliberate public-only divergence.** `tasks_530.md` keeps its own copy of this
> task on **Drive + Obsidian + Telegram** (`hard__drive-obsidian-telegram__049` is its
> Obsidian twin) and stays as-is: the 530 corpus is self-consistent because
> `ask_user_facts_530.json` names **`shared budget.xlsx`**, which really does exist in Drive.
> Only the *public* slice carried the nonexistent `family_numbers.xlsx`. `public.md` already
> diverges from the 530 text where the preview needs it (see the per-task overrides in
> `export_public_dataset.py`), so this is the same pattern.
>
> **Residual risk — now automated (2026-09-22).** The note is *still* app-private, and with
> Drive gone it is the **only** graded state — but it is no longer true that "nothing but a
> human in the UI can recreate it". Its text is version-controlled at
> `assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, and `reset_phone.py --apply`
> runs `restore_budget_note()`, which re-types it from that seed whenever
> `com.oneplus.note:id/text_count` drifts (canonical **518**), then verifies the result.
> `--verify-only` gates on it, so drift now **fails the gate** instead of silently costing a
> task — and unlike the old manual step it also repairs the *in-place edit* case, where a run
> takes the note's own "log today's check date" branch and overwrites the very seed it is
> graded against. Two measured constraints are load-bearing: the retype uses **Ctrl+A**, never
> a DEL loop (the note's **title is its first line**, so a character-wise delete renames it and
> the next run cannot find it), and the note **must not** be swept by date — hence
> `reset_phone.py` still deletes run-created notes **by title only**.
>
> **Before re-running**
> - ✅ Note re-typed via the UI 2026-09-21 (title `Budget Deadline`; preview `FY26 family
>   budget - finalisation`; list holds 12 notes).
> - ✅ Seed gate PASSES 2026-09-21, including
>   `PASS seed file content ... Budget Deadline.md contains 'Last reviewed: 2026-07-10.'`
> - **Now gate-enforced (2026-09-22):** the app-private copy is verified via
>   `com.oneplus.note:id/text_count` (**518** non-whitespace chars) against the tracked seed
>   `assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, and `restore_budget_note()`
>   re-types it on drift. The old manual "confirm the note is in the list — nothing on disk
>   verifies the app-private copy" step is therefore obsolete: there *is* now something on
>   disk, and drift fails the gate rather than costing a task.
> - The app force-stops back to the **list** on relaunch (verified), so the seed does not trip
>   the "starts inside the last-edited note" trap.

### ✅ 2026-09-21 RESULT — all 13 rows re-run; **0 PASS, and no verdict flipped**

The task is finally graded against state that actually exists, and the honest answer is that
**no model completed it**. Every row now fails for a reason the task itself defines, not for a
missing seed or a phantom filename:

| row | model | re-run outcome (2026-09-21) | verdict |
|---|---|---|---|
| 1 | qwen3.8-27b (TEXT) | read the note, called it overdue, **0 asks**, no chase | ❌ FAIL |
| 2 | kimi-k2.6 (TEXT) | asked ✓ → overdue → **60-step cap**, chase never confirmed | ❌ FAIL |
| 3 | gemini-3.1-flash-lite | asked ✓ → overdue → chase **composed** for Yuvraj Airtel, **`Send` never registered** | ❌ FAIL |
| 4 | seed-2.0-lite | asked ✓ → overdue → chase **composed**, 3 × `Send` + Enter, **never delivered** | ❌ FAIL |
| 5 | qwen3.8-27b (VISION) | **0 asks** (gate), 60-step cap | ❌ FAIL |
| 6 | seed-2.0-lite (VISION) | **malformed tool-call markup ×3** at step 9 | ❌ FAIL |
| 7 | gpt-5.6-luna (TEXT) | overdue detected, but judged the note to name no owner → nothing sent, 0 asks | ❌ FAIL |
| 8 | gpt-5.6-luna (VISION) | same as row 7 | ❌ FAIL |
| 9 | Qwen3.5-4B (TEXT) | 1 ask → **60-step cap** | ❌ FAIL |
| 10 | gemma-4-E2B-it (TEXT) | overdue detected, **could not reach a Telegram send surface**, 0 asks | ❌ FAIL |
| 11 | kimi-k2.6 (VISION) | 1 ask → **60-step cap** | ❌ FAIL |
| 12 | gemma-4-E2B-it (VISION) | judged the note **overdue**, then took the note's own "log today's check date" branch instead of messaging (accepted by the grader), **0 asks** | ❌ FAIL |
| 13 | Bonsai-2-27B (TEXT) | **2400 s timeout, 0 steps** | ❌ FAIL |

**No published verdict changed.** The two PASSes that the first substitution recorded
(rows 3 and 4) were **self-reported only**: in both runs the chase text is still sitting in
Telegram's composer at the final UI state, with the `Send` button present and no sent bubble
— and row 4's own closing reason admits *"the send button did not register clicks to finalize
delivery"*. That is the **same harness Send-button failure** that made the original rows 3 and
6 FAIL, so both were re-graded to FAIL and the manual-audit headlines for rows 3, 4 and 6 are
back where they started. Only telemetry (steps / queries / elapsed / cost) moved.

> **⚠️ New infra finding — the Telegram `Send` tap is unreliable (see §7.2).** Of the 13
> re-runs, **2 composed the exact correct chase message and could not deliver it** (rows 3, 4),
> and 2 more of the original runs hit the identical failure (rows 3, 6). A tap on
> `Text: 'Send'` at its reported centre coordinates registers as "clicked" in the trajectory
> yet leaves the text in the compose box. Until that is characterised, **any chase-message task
> has a delivery step the harness cannot be trusted to perform** — grade such tasks from the
> post-send UI state, never from the model's claim.

**What was done with the result**

- all 13 reports (`reports/public/public-*.md`) carry a re-run note, and rows 1, 2, 5 and 7–13
  had their stale `family_numbers.xlsx` / Drive-loop verdict text replaced with the re-run's
  actual behaviour;
- `reports/metrics/public/*` and `androidlife-website/assets/js/leaderboard.js` were updated
  for the telemetry only — `verify_leaderboard.py` → **0 mismatches**;
- row 12's Limitations bullet now records that the app-private seed gap it depended on is fixed;
- the re-run artifacts replaced the superseded ones in place under
  `runs/<canonical>/day1/hard-drive-notes-telegram-010/` on
  `YuvrajSingh9886/androidlife-public`, and every uploaded file was verified byte-identical
  (sha256 for LFS objects, git-blob-sha1 for the rest).


---

## 5. `easy__google-slides__001` — Google Slides (easy, 1pt, day 1)

**Verdict: CLOSED 2026-09-21. Two presentations were both named "Q3 Review" and the runs
read the wrong one (1 slide, not 8). All 7 affected rows re-taken against the canonical
`Q3_Review.pptx`; 6 PASS / 1 genuine FAIL. The deck is now version-controlled + restored by
`reset_phone.py`, and the grader now checks the reply against ground truth — see the end of
this item.**

The task: *"open the `[presentation name]` presentation in Google Slides and tell me how
many slides it has"* → `presentation name=Q3 Review`.

**The canonical account map** (`.agents/skills/reset-phone/SKILL.md` → "Cloud account
map") puts **Gmail / Drive / Docs / Slides on `ranirajesh786@gmail.com`** — that account
owns the `Q3 Review` deck. Verified 2026-09-18:

| App | Canonical account | Found on device | |
|---|---|---|---|
| Calendar (`cal_id=16`) | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Google Meet | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Gmail | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Drive | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Docs | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| **Slides** | `ranirajesh786@gmail.com` | **`rajceo2031@gmail.com`** | ❌ → fixed |
| Google Photos | `rajeshceo2015@gmail.com` | `rajeshceo2015@gmail.com` | ✅ |
| Google Maps | *(not constrained)* | `rajceo2031@gmail.com` | ⚠️ benign |

**This was a genuine drift, not the original state.** An archived UI dump
(`assets/runs/logs/gui_checks/51_slides.xml`, **2026-09-04 21:42**) shows Slides signed in
as `ranirajesh786@gmail.com` with `Q3 Review` **visible**. On 2026-09-18 it was
`rajceo2031@gmail.com` and the deck list contained **no `Q3` token at all** — a completely
different set of decks. Any run made in that window could not see the seeded deck.

**Fixed 2026-09-18:** switched Slides to `ranirajesh786@gmail.com` via the in-app account
chooser (all six accounts are already on the device — no password needed).

**The deck itself is fine.** `Q3_Review.pptx` is present **both** as the device file
`/sdcard/Download/Q3_Review.pptx` and in **Drive** on `ranirajesh786@gmail.com` (an uploaded
`.pptx`, not a native cloud Slides deck — which is why a search for the literal string
`Q3 Review` misses it; the item is `Q3_Review.pptx`). Opening it in Slides shows
**`Slide N of 8`** and the indicator **is** exposed to the accessibility tree, so a
text-tree agent can read it. Confirmed live 2026-09-18.

**Root cause, corrected 2026-09-21.** The account drift was real but was *not* what
produced the wrong answers. Two different presentations were both called **"Q3 Review"**:

| | file | slides | role |
|---|---|---|---|
| stray | `Q3 Review` (old upload) | **1** | what every run in the 08-26 → 09-06 window opened |
| canonical | `Q3_Review.pptx` | **8** | rebuilt **2026-09-07 13:12**; the real target |

The task's `presentation name` var is `Q3 Review`, and a literal search matches the stray.
So the earlier answers were honest readings of the **wrong file** — `1`, `3` and `8` all
scored PASS because the grader carried no ground truth at all. **6 of the 7 affected rows
were self-reported passes** against the wrong deck.

**Re-taken 2026-09-21** for all 7 affected rows (`1, 2, 3, 4, 6, 7, 11`), each confirmed in
`ui_states` to have opened `Q3_Review.pptx` (`Slide N of 8` on screen):

| row | model | re-run verdict | steps / s |
|---|---|---|---|
| 1 | qwen3.8-27b (TEXT) | ✅ PASS — replied `8` | 4 / 78.47 |
| 2 | kimi-k2.6 (TEXT) | ✅ PASS — replied `8` | 8 / 113.28 |
| 3 | gemini-3.1-flash-lite | ✅ PASS — replied `8` | 3 / 43.54 |
| 4 | seed-2.0-lite | ✅ PASS — replied `8` | 3 / 54.57 |
| 6 | seed-2.0-lite (VISION) | ✅ PASS — replied `8` | 3 / 64.51 |
| 7 | gpt-5.6-luna (TEXT) | ❌ FAIL — 60-step cap, no count | 60 / — |
| 11 | kimi-k2.6 (VISION) | ✅ PASS — replied `8` | 21 / 319.55 |

*Row 6 and row 7 above previously carried **swapped mode labels** — the leaderboard's row 6
is `seed-2.0-lite (VISION)` = `20260905-051950`, and its row 7 is `gpt-5.6-luna (TEXT)` =
`20260906-063336` (the same mapping the calendar table further down already used). The
step/latency figures always pointed at the right runs; only the two model strings were
wrong. Corrected 2026-09-21.*

### Visual re-verification — was the deck actually *empty*?

Checked 2026-09-21 by reading every run's `ui_states` (the same evidence the screenshots and
`.gif`s render) for the deck on screen. **The stray deck really is effectively empty:**
`Slide 1 of 1` with no content. The single intact original trajectory that still shows it is
`20260901-002701` (mimo-0901), which recorded the reply `1`; it is **not a leaderboard row**,
so it was never in scope for a re-run. The canonical deck instead renders `Slide N of 8`
with the full Q3 content.

Every run whose *original* trajectory is still intact was checked for the same symptom —
**none of them shows it**:

| Row | Run | Deck actually opened | Counts seen | Reply |
|---|---|---|---|---|
| 5 | `20260909-043419` | first a **22-slide** `UFDS Mentoring Orientation 2022`, then `Q3_Review.pptx` | `of 8` (settled) | `8` ✅ |
| 8 | `20260910-041531` | `Q3_Review.pptx` | `of 8` | 60-step cap ❌ |
| 9 | `20260914-061846` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 10 | `20260916-011341` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 12 | `20260917-160018` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 13 | `20260920-044846` | `Q3_Review.pptx` | `of 8` | `8` ✅ |

(Non-`8` counts do appear mid-trajectory on rows 10 and 12 — `of 7`, `of 5`, `of 6` — but
they are transient while the deck loads/settles; the settled count is always `8`.)

So the re-run set **is** exactly the runs that read the wrong, empty-looking deck. The four
local / mac-mini rows (9, 10, 12, 13) were never affected and were correctly left alone.

**Caveat, worth remembering:** the seven re-runs *replaced* their original trajectory
directories in `androidlife-public`, so the pre-fix screen state for exactly those seven rows
can no longer be re-verified from the hub — only from the report notes. Every other run's
original is intact.

Row 7's FAIL **stands**, but is now known to be a genuine model limit (the correct 8-slide
deck was on screen) rather than a seed artifact. Rows 1 and 11 gained a true success; the
reports, `leaderboard.js` and the `reports/metrics/public/*.json` aggregates were all
recomputed from the re-runs by exact arithmetic, and the artifacts + reports re-uploaded to
`androidlife-public` (byte-identical, 337 files, 0 stale). Row 11's re-run left an
`Untitled presentation` behind; it was trashed and the gate re-verified before the next
launch.

**Both systemic fixes are now in (2026-09-21), so this cannot recur:**

1. **The deck is version-controlled and self-repairing.** `assets/seeds/public/Q3_Review.pptx`
   is tracked (the single exception to the blanket `assets/` gitignore — see `.gitignore`;
   a `!` under an excluded *directory* is silently useless, so the tree is excluded
   entry-by-entry to make the negation reachable). `restore_slides_deck()` re-pushes it on
   `--apply` whenever the device copy is missing or the wrong length, and refuses to push a
   fixture that disagrees with the task's ground truth; `verify_slides_deck()` blocks the
   gate. Tests: `tests/test_reset_phone_slides_deck.py` (incl. one that asserts the fixture
   is *actually tracked*, so a gitignore regression fails loudly).
2. **The grader grades the reply, not the model's opinion.** A new
   `answer_checks_public.json` sidecar (mirroring the existing `ask_user_facts` plumbing:
   `answer_checks_path` / `merge_answer_checks`) marks tasks with objectively known answers.
   `easy__google-slides__001` → `numeric_reply: 8`. `androidlife_report.py` takes the first
   integer in the agent's reply and **demotes** a self-reported pass that does not state it.
   The check is **one-directional — it can never promote**, so enabling it can only make a
   score more honest. Verified end-to-end against the 7 real re-run artifacts: all 7 classify
   correctly and **none of the 7 was decided by the check** (so no published number moved
   because of it).

**Before re-running:**
- Confirm **Slides → account = `ranirajesh786@gmail.com`** (now part of the account gate).
- Confirm `Q3_Review.pptx` is present and still has **8** slides (now restored + gate-enforced).
- **Never repair the deck by hand on the device again** — update the git fixture, or the next
  reset will put the old one back.

---

## 6. `easy__calendar__002` — Google Calendar (easy, 1pt, day 1)

**Verdict: the seeded conflict pair has been sitting on the RUN DAY instead of "tomorrow"
in most runs, so the task is vacuous when it passes and unjust when it fails. Cause now
confirmed; all models need a re-run.**

> ### ✅ RE-RUN COMPLETE — 2026-09-21
>
> All **9 affected models** were re-run on 2026-09-21 against a corrected same-day seed
> (conflict pair verifiably on “tomorrow” = **Tue 22 Sep**, and confirmed to be *rendering
> in the Calendar app*, not merely present in the provider). Aggregate metrics, official
> metrics JSONs, reports and the leaderboard were all updated in place; HF is byte-identical;
> `verify_leaderboard.py` reports **0 mismatches across 13 rows / 300 fields**.
>
> | Row | Model (mode) | Was | Now | Score move |
> |---|---|---|---|---|
> | 1 | qwen3.8-27b (TEXT) | ❌ FAIL *(unjust)* | ✅ PASS | 25 → **26 / 60** |
> | 2 | kimi-k2.6 (TEXT) | ❌ FAIL *(timeout)* | ✅ PASS | 31 → **32 / 60** |
> | 3 | gemini-3.1-flash-lite (TEXT) | ❌ FAIL *(never looked)* | ✅ PASS | 25 → **26 / 60** |
> | 6 | seed-2.0-lite (VISION) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — |
> | 7 | gpt-5.6-luna (TEXT) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — (official 8 → **9**) |
> | 10 | gemma-4-E2B-it (TEXT) | ❌ FAIL *(unjust)* | ✅ PASS | 5 → **6 / 53** |
> | 11 | kimi-k2.6 (VISION) | ✅ PASS *(incl. artifact)* | ✅ PASS *(clean pair)* | — |
> | 12 | gemma-4-E2B-it (VISION) | 🚨 HALLUCINATION | ❌ FAIL *(protocol abort)* | halluc 4 → **3** |
> | 13 | Bonsai-2-27B (TEXT) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — |
>
> **Net: +4 true successes across the 9 rows**, 1 hallucination retired, and every remaining
> PASS on this task is now earned rather than vacuous.
>
> **Row 12 is the one judgement call.** gemma-4-E2B-it VISION *twice* named the correct pair
> in its reasoning, then emitted `<complete success="true" message="…"/>` instead of the
> harness's `<invoke name="complete"><parameter …></invoke>` form, and the runner aborted
> with `malformed tool-call markup 3/3`. It is recorded as ❌ FAIL, not PASS: an answer that
> never reaches a valid tool call is not a deliverable, and this failure mode is scored FAIL
> everywhere else in the benchmark (that same report lists 3 other tasks killed by it).
> T=0.0 makes it deterministic, so a third attempt reproduces it byte-for-byte.
>
> **No longer needed:** the `Weekly_Standup` sweep is now automatic, and `--apply` on a
> previous day can no longer start a run (the launch gate is enforced and fail-closed).
> See `.agents/skills/reset-phone/SKILL.md`.
>
> ---
>
> #### ↻ Second pass — 2026-09-21 (Schedule-view correction), rows 1 and 2
>
> Auditing the re-runs above for polluted starting conditions found one class the gate
> **cannot** see: the **Calendar app's view mode**. Google Calendar's agenda row reads
> `"<weekday> <D> <Month> <Y>, Open Day View"` when it is in **Schedule** view and
> `"... Open Schedule View"` when it is in **Day** view — so the mode is recoverable from
> the `ui_states` artifacts. Checked across all nine re-runs:
>
> | Row | Re-run traj | t0 view | Fixed? |
> |---|---|---|---|
> | 13 | `20260921_020121` | Schedule | — |
> | 1 | `20260921_021331` | **Day** ✗ | re-run as `20260921_035827` |
> | 2 | `20260921_023010` | **Day** ✗ | re-run as `20260921_040820` |
> | 3, 6, 7, 10, 11, 12 | `20260921_0245..0319` | Schedule | — |
>
> Cause: the agent of each run left the app wherever it finished, so row 13's agent left
> **Day** and rows 1–2 inherited it. From row 3 onward the view was forced back to
> Schedule before launch. Both affected rows were taken again from a verified Schedule
> start (`ui_states/0002`), verdicts unchanged (**PASS**), and their task figures,
> aggregates, metrics JSONs, the leaderboard and HF were all updated. **All nine re-runs
> now start from Schedule — 0 exceptions.**
>
> The re-take also repaired three lines the *first* pass had left stale on row 2 — its
> Date-line elapsed, its **Grand total run cost** (which contradicted the leaderboard:
> `$9.84` vs `$8.37`) and its **Top-token tasks** list (the calendar task, now ~21K tokens,
> was still listed first at 1972K) — plus the `easy-calendar__002` reference in the
> failure-analysis header count. The corrected top-token ranking was re-derived from all 60
> `run_metrics.json` on the hub, not guessed.


The task asks about **conflicts tomorrow afternoon**. `reset_phone.py` seeds
`Team Sync` 14:00–15:00 and `Mentor 1 on 1` 14:30–15:30 at `offset_days: 1`. When the
anchors are day-relative and `--apply` ran **on a previous day**, both land on what is by
run time *today*, leaving tomorrow with only the recurring `Weekly_Standup` 14:30–15:30 —
so "no conflicts" is the *correct* answer for that device, and the task tests nothing.

Established by parsing **every** `easy-calendar-002` `ui_states/*.json` on HF and reading
the day header each event sits under:

| Row | Run | Model | Conflict pair sat on | Recorded | Reality |
|---|---|---|---|---|---|
| 1 | `2026-08-28-002424` | qwen3.8-27b (TEXT) | **run day** (Fri 28 Aug) | ❌ FAIL *(“false pass”)* | **the FAIL is wrong** — the model said “tomorrow has only `Weekly_Standup`”, which was *true*; the audit’s ground truth came from ADB **after** the drift |
| 2 | `2026-08-29-153657` | kimi-k2.6 (TEXT) | not on screen | ❌ FAIL (timeout) | inconclusive |
| 3 | `20260826-105200` | gemini-3.1-flash-lite | not on screen | ❌ FAIL | inconclusive |
| 4 | `2026-08-30-143554` | seed-2.0-lite | **D+1 ✅** | ✅ PASS | correct |
| 5 | `20260909-043419` | qwen3.8-27b (VISION) | **D+1 ✅** | ✅ PASS | correct |
| 6 | `20260905-051950` | seed-2.0-lite (VISION) | **run day** (Sat 5 Sep) | ✅ PASS | **vacuous** |
| 7 | `20260906-063336` | gpt-5.6-luna (TEXT) | **run day** (Sun 6 Sep) | ✅ PASS | **vacuous** ← *this is the golden-format report* |
| 8 | `20260910-041531` | gpt-5.6-luna (VISION) | **D+1 ✅** | ✅ PASS | correct |
| 9 | `20260914-061846` | Qwen3.5-4B (TEXT) | **D+1 ✅** | ✅ PASS | correct |
| 10 | `20260916-011341` | gemma-4-E2B-it (TEXT) | **run day** (Wed 16 Sep) | ❌ FAIL | seed issue (already documented) |
| 11 | `2026-08-30-021852` | kimi-k2.6 (VISION) | not on screen | ✅ PASS | inconclusive |
| 12 | `20260917-160018` | gemma-4-E2B-it (VISION) | not on screen | 🚨 HALLUCINATION | inconclusive |
| 13 | `20260920-044846` | Bonsai-2-27B (TEXT) | **run day** (Sun 20 Sep) | ✅ PASS *(vacuous)* | **vacuous** |

**5 of 13 rows are demonstrably wrong or meaningless** on this task: 3 unearned PASSes
(rows 6, 7, 13 — including the report held up as the format standard) and 1 unjust FAIL
(row 1). It is the *same* failure class as #4 and #5: a benchmark-level seed defect, not a
model signal. Note the split is not random — every run with a **same-day** `--apply` is
correct (rows 4, 5, 8, 9); every run where the reset happened a day earlier is broken.

**Root cause (CONFIRMED 2026-09-20, from the 20 Sep run's own week view):**

```
Sun 20 Sep (run day)   Weekly Sync 10:00, Team Sync 14:00, Mentor 1 on 1 14:30, Weekly_Standup 14:30
Mon 21 Sep (tomorrow)  Weekly Sync 07:00, Weekly Sync 10:00, Weekly_Standup 14:30
```

Every `offset_days` seed is **exactly one day early** — `19 Sep + 1 = 20 Sep` — while every
`weekday` anchor is correct, because on consecutive days "next Monday" resolves to the same
date. **`--apply` ran on 19 Sep, not on the run day.** This is the recorded 2026-09-16
failure (seeded 15 Sep, batch started 16 Sep 01:13) and it keeps recurring.

**Disproven along the way** (do not re-apply these "fixes"):
- **Not** a Google-sync revert. A plain `content update` survives, and binding
  `dirty:i:1` is *rejected* by the CalendarProvider (`Only sync adapters may write to
  dirty`) — silently, since `content insert/update` still exit 0. That bind **broke every
  calendar write** and has been removed.
- **Not** a gate failure. `verify_calendar_anchors` was committed ~11 h *after* the 20 Sep
  run began, so it never ran that morning; the "gate saw the right dates" line in
  `public-20260920-044846.md` was a reconstruction artefact.

**Also found: a recurring run artifact pollutes the window.** `Weekly_Standup`
(`_id=4378`) is `rrule=FREQ=DAILY;COUNT=14` from Thu **17 Sep** 14:30 — created by the
2026-09-17 gemma run's agent, uploaded, never cleaned. It therefore appears on *every* day
including "tomorrow", and would add a spurious third afternoon event even with correct
seeds. Reset only sweeps exact-date rows today.

**Before re-running:**
- Run `reset_phone.py --apply` **on the run day** (same calendar day as launch). This is
  the whole fix; there is no other setting to change.
- Confirm the anchor gate shows `Team Sync` / `Mentor 1 on 1` on **D+1**; the script now
  re-reads every write it makes, so a rejected write fails loudly instead of silently.
- **Sweep recurring run artifacts** (`Weekly_Standup` FREQ=DAILY) across the window —
  query the `rrule` column, delete the series, not just today's instance.
- The two 14:30 events (`Mentor 1 on 1` + `Weekly_Standup`) overlap by design in the
  "triple-booking" reading; keep the recurring artifact out or the conflict set changes.

**Do not trust any recorded `easy__calendar__002` cell** from a run where the reset did not
happen on the same day — including the golden-format report.

---

## Re-run list (by model)

When the fixes below are in place, these tasks need a fresh run **for every model on the
board**. Scores for them are not comparable across the fix boundary.

### Count: **6 tasks × 13 model rows = 78 task-runs** to redo

`13` = the current leaderboard rows in `androidlife-website/assets/js/leaderboard.js`
(`LEADERBOARD_ROWS`), including the interrupted battery-death rows. Each of the 6 tasks
below must be re-run for every one of them, because all 6 were broken **at the benchmark
level**, not by any individual model — so the recorded cells are not a model signal.

| # | Task | Why | Blocked on |
|---|---|---|---|
| 1 | `medium__google-maps__002` | vacuous PASS from Maps' leaked recent/route state; the 17 Sep run also left live navigation running over 26/27 tasks | clear Maps history + stop nav |
| 2 | `hard__google-meet-files__070` | unsolvable seed (no conference link + 48h window) — **fixed** | re-run `reset_phone.py --apply` **on the run day** (anchors are date-relative; no new time needed), then `--verify-only` gates it |
| 3 | `hard__bookmyshow__005` | `[cinema]` placeholder named a non-existent cinema — **fixed (`INOX: Symphony Mall`); the 2026-09-18 fix had NOT taken effect** — `config/user.yaml` is gitignored and was overriding it, so the runner still resolved `INOX Bhubaneswar`. Corrected + launch now gated by `verify_task_vars.py` | **↻ IN PROGRESS 2026-09-22** — listing re-verified live on-device, device re-seeded today, 13 rows running. Row 1 found `INOX: Symphony Mall` (no placeholder echo) and failed only at the harness Send step. ⚠️ verdict pass needed: rows 6/10 recorded "success" while replying the non-existent `INOX Bhubaneswar`, and row 6's FAIL reason (ASK USER gate) doesn't apply to a `DETERMINISTIC` task |
| 4 | `hard__drive-notes-telegram__010` | app-private `Budget Deadline` note kept vanishing, and the oracle named a Drive file (`family_numbers.xlsx`) that never existed — **fixed 2026-09-21: Drive dropped from the task, oracle fixed, note text version-controlled + re-typed via UI** | ✅ **DONE 2026-09-21** — all 13 rows re-run against the corrected seed (**0 PASS**, no verdict flipped); every run verified to start on the launcher; reports/leaderboard/metrics substituted, artifacts + reports byte-identical on HF |
| 5 | `easy__google-slides__001` | Two decks both named **"Q3 Review"** (stray **1**-slide vs canonical `Q3_Review.pptx` **8**-slide, rebuilt 2026-09-07) → runs read the wrong file; the grader had no ground truth, so `1`/`3`/`8` all recorded PASS — **deck now version-controlled + restored on reset, grader now checks the reply** | ✅ **DONE 2026-09-21** — all 7 affected rows re-run against the real deck (6 PASS / 1 genuine FAIL); reports, leaderboard + metrics JSONs substituted; artifacts byte-identical on HF |
| 6 | `easy__calendar__002` | conflict pair seeded on the **run day** instead of tomorrow in 5 of 13 rows → 3 vacuous PASSes (incl. the golden report) + 1 unjust FAIL — **cause confirmed, fix is same-day `--apply`** | ✅ **DONE 2026-09-21** — all 9 affected rows re-run; `--apply` gate is now enforced at launch and the recurring-artifact sweep is automatic |

---

## Device account state (verified 2026-09-18)

The device carries **6 Google accounts** and the apps are **not auto-consistent** — each
app remembers its own selected account, and nothing resets it between runs. Per-app
account selection is therefore **unmanaged drift**, and it is the same failure class as
#5: an app on the wrong account cannot see its seeded cloud data.

Canonical map (from `.agents/skills/reset-phone/SKILL.md` → "Cloud account map") vs what
was actually on the device:

| App | Canonical | Found | |
|---|---|---|---|
| Calendar (`cal_id=16`) | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Google Meet | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Gmail | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Drive | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Docs | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| **Slides** | `ranirajesh786@gmail.com` | ~~`rajceo2031@gmail.com`~~ | ❌ **fixed** |
| Google Photos | `rajeshceo2015@gmail.com` | `rajeshceo2015@gmail.com` | ✅ |
| Google Maps | *(not constrained by any task)* | `rajceo2031@gmail.com` | ⚠️ benign |
| Amazon / Swiggy / Zomato / BookMyShow / Prime Video / YT Music | personal accounts | all signed in | ✅ |

**Maps is on `rajceo2031@gmail.com`, not `yuvraj.mist@gmail.com`** — and that is fine. Maps
is deliberately **not** in the canonical map: neither Maps task
(`medium__google-maps__002` = compare ETAs + Notes, `easy__google-maps__004` = save parking
location) touches account-bound data, so the Maps account gates nothing. `rajceo2031` is
the documented *"device owner's own primary Gmail"*. Only Slides was actually wrong.

**Maps WAS on `yuvraj.mist` at some point and moved** — the same drift, just harmless here.
The lesson is the general one: never assume an app is on the account you last left it on.

**Recommended gate:** extend `reset_phone.py --verify-only` to assert the cloud account per
app (the identity disc's `content-desc` reads `Signed in as <Name> <email>`), so a drifted
app fails the pre-run gate instead of silently costing a task — the same treatment the Meet
seed now gets.

---

## Standing note

The items above are **benchmark-validity** issues, not model failures: the recorded
scores overstate ability for #1 (free pass) and #5 (unverified count) and understate it
for #2 (unsolvable seed). Worth keeping in mind when comparing against any run made
before 2026-09-17.

One more, **not** a re-run item — it caps what any of these numbers can mean:

- **The Google Sheets editor exposes no cell data to the accessibility tree.** Verified on
  the 17 Sep run: **0 of 15** a11y states for `hard__google-sheets-amazon-shopping__074`
  contain any cell text (`IPL 2025 Final Over`, `12500000` appear 0 times in the whole
  run). The tree carries only the sheet tab name and the toolbar; the grid draws on
  `id/spreadsheet_view`. So every Sheets task (and the Sheets half of
  `hard__google-sheets-amazon-shopping__074`) is **effectively vision-only** — a text-tree
  agent cannot read the spreadsheet at all. Keep this in mind when reading Sheets results
  as a capability signal; fix would be a UI-automator path that reads the grid, or
  accepting it as a vision-only task.

---

## 7. Latent infra defects found while auditing the seed path (2026-09-21)

Not task re-runs, but they can silently corrupt a run — which is the same hazard class as
items 1–6.

### 7.1 Stale tests hide real regressions (fix before trusting the suite)

`tests/test_reset_phone_calendar_gate.py` has **3 failing tests**. They are pre-existing,
not new: verified by stashing all local edits, and bisected to **`4be381d`** ("seeding: make
calendar seeds survive the Google sync, and re-verify after a settle") — green at
`b2d09a1`, red from `4be381d` onward. The suite has been red ever since.

There are **two mechanisms**, and they stack in a way that matters for the fix:

- **(a) The exact-date fast path — the cause today.** `ensure_calendar_events` computes
  each anchor from `date.today()`; the shared `QUERY_ROWS` fixture builds its copies from
  the **same** anchor helpers (`MONDAY`, `D1`, `D2`). So every fixture copy already sits
  exactly on its anchor, the seeder logs `already on ... (no write needed)`, and it issues
  **zero** writes of any kind. Measured: three `no write needed` lines and a call list
  containing only `getprop` + two `content query`s — no update, no insert, no delete.
  This fires **every day**, not just on Mondays (both sides derive from the same helpers).
- **(b) A latent second trap, revealed the moment you fix (a).** If you "fix" these tests
  by dating the fixture rows in the past, the seeder sees a same-time miss and — because
  the fixture rows are **unlinked** — resolves it by **INSERT**, not UPDATE (only
  `meet: True` seeds are UPDATE'd on a same-time miss, since delete+insert would silently
  destroy the conference link, which the non-rooted `content` CLI cannot rewrite). So
  re-dating the fixture alone will **not** green them.

Therefore the fix needs **both**: a stale-dated fixture (so (a) doesn't skip) *and*
`meet: True` seeds (so (b) resolves to an in-place UPDATE). The invariant actually worth
pinning is **link preservation**, which is why the update-in-place path exists.

One assertion in test 1 is **dead code** regardless: `assert ["_id=4341" in updates[0],
"_id=4342" in updates[1], "_id=4343" in updates[2]]` builds a non-empty list, and a
non-empty list is always truthy — it asserts nothing.

Why it matters more than it looks: a permanently red suite means a **real** regression is
indistinguishable from the known noise, which is exactly how the calendar drift survived
five runs. Note (a) itself is **not** unprotected — the new
`test_already_correct_seed_is_not_rewritten` pins the skip deliberately. Only these three
stale tests are broken.


### 7.2 Other pollution classes with no gate coverage

Everything below is ADB-invisible, so `--verify-only` **cannot** see it and only the manual
checklist in `docs/pre-run-checklist.md` covers it.

> **Promoted out of this table 2026-09-22 — the two content leaks that survived `force-stop`.**
> Both of the first two rows below were *app content*, not app screen, so the new pre-run app
> reset (`cli.py`, §7.4) cannot touch them and they stayed manual. Both are now **blocking
> gates with `--apply` repairs**:
>
> * **Telegram `Yuvraj Airtel` chat** — `clear_telegram_run_leaks()`. Deletes the draft and
>   any bubble under **today's** date separator (seeded history is dated 2026-08-20/23
>   precisely so run artifacts are distinguishable). Two measured facts drive the
>   implementation: **`force-stop` does NOT clear a Telegram draft** (typed → HOME →
>   force-stop → relaunch showed the identical draft, so the clearing has to happen in the
>   UI before the process is killed), and the chat-list **search box is also an EditText**,
>   so the composer lookup is y-guarded or `Search Chats` reads as a leak.
> * **OnePlus Notes `Budget Deadline`** — `restore_budget_note()`. The note text is now a
>   tracked fixture (`assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, canonical
>   `text_count` **518**); a drifted note is re-typed from it via Ctrl+A and verified. It
>   must **not** be repaired by character-wise deletion: the note's **title is its first
>   line**, so a DEL-loop renames the note (a trial turned it into `- Utilities: Rs 9400`)
>   and the next run cannot find it.
>
> Opt out with `--no-leak-cleanup`. Both run in the same pre-first-task window as
> `verify_calendar_view_mode`, so they always hand back a stopped app on the launcher.

> **A second, nastier version of the Telegram leak: the run *after* the send (2026-09-22).**
> The cleanup above only deletes bubbles under **today's** separator, and it did not exist
> before 2026-09-22. So the 2026-09-21 `hard__drive-notes-telegram__010` re-runs had **no
> coverage at all**, and the chat carried each row's delivered message into the next row.
> The consequence is a genuinely false pass, not just a dirty device:
>
> | row | run | started | what the chat showed |
> |---|---|---|---|
> | 11 | `20260921-192331` (kimi-k2.6) | 19:25 | typed the chase from step 8, **sent it at 19:29** |
> | 13 | `20260921-194413` (Bonsai-2-27B) | 19:46 | at **step 6** already showed the same `Sent at 19:29` bubble |
>
> Row 13's `success=true` over 9 steps was **inherited state**: row 11 had already sent the
> exact message the task asks for, so there was nothing left to do and Bonsai reported
> success having sent nothing. The PASS was an artifact of the previous row, which is why it
> was already recorded FAIL — but the *reason* matters, because the same shape will recur
> wherever a task's deliverable is a message.
>
> **The rule this generalises to:** a run must not start while a message it is required to
> send is already sitting in the target chat. Any run that did start in that state is void
> and has to be re-taken, however it scored — a leftover message turns "did the agent do the
> work" into "was the work already done for it".
>
> Re-measured across both batches on 2026-09-22 with
> `scripts/tools/audit_telegram_inheritance.py` (a sent bubble whose stamp predates the
> run's own start is an inheritance, not an action): the `010` batch has exactly one
> inheritance (**row 13**), and the `bookmyshow` batch has **none** — row 5 is the only row
> that sent, at 12:06 against an 11:58 start, and the between-row cleanup deleted it before
> row 7 began. So the fix holds going forward, and the contamination is confined to the
> batch that ran before the cleanup existed.

> **Promoted out of this table 2026-09-21 — App UI mode drift.** A previous run leaving the
> **Calendar app in Day view** used to be undetectable here: `--verify-only` reads the
> *provider*, and the view mode lives in app state. It bit **rows 1 and 2** of the
> 2026-09-21 calendar re-runs, both of which had to be taken a second time from Schedule
> view. It is now a **blocking gate**, `verify_calendar_view_mode()`. Two details worth
> keeping:
>
> * The marker is **inverted** — the day-row content-desc names the mode you would switch
>   *into*, so `"... , Open Day View"` means the app is currently in **Schedule** view. Do
>   not "fix" `_OPEN_DAY` / `_OPEN_SCHEDULE`; pinned by the first test in
>   `tests/test_reset_phone_calendar_view.py`.
> * It **repairs** (taps "Open Schedule View") instead of warning, because "a human will
>   notice and fix it" is the exact assumption that failed. Opt out with
>   `--no-calendar-view-check`. Like `verify_meet_agenda`, it always hands back a stopped app
>   on the launcher — it runs immediately before the first task, so whatever it leaves on
>   screen *becomes* the agent's start state.

| Class | Example | Blast radius |
|---|---|---|
| Leftover app state lets the agent skip the work | Maps recents + leftover route: 7 of 13 runs never typed the query | `medium__google-maps__002`, `easy__google-maps__004` |
| ~~**Messaging leftovers inherited across runs**~~ ✅ **gated 2026-09-22** | **Telegram draft/sent bubble in the `Yuvraj Airtel` chat: ONE draft survived 7 rows and ~90 min** — row 4 composed the chase message, its Send never registered, and rows 5/6/9/11 then opened the chat to find it pre-typed ("*The message is already composed*") or already sent ("*I can see the message has been sent!*"). Now a **blocking gate** (`clear_telegram_run_leaks` / `verify_telegram_chat_clean`); the chat list is still unreadable by uiautomator, so the check opens the chat by name rather than scanning the list. | `hard__drive-notes-telegram__010`; any "message X" deliverable |
| Leftover *conferenced* event hijacks the Meet task | day-2 `easy__google-meet__004` creates "Product Demo", which day-3 Meet reports instead | `hard__google-meet-files__070` |
| **The Telegram `Send` tap does not reliably deliver** | A tap on `Text: 'Send'` at its reported centre coordinates is logged as "clicked" but the text stays in the compose box — hit by **4 runs across 2 models** (rows 3 & 6 originally, rows 3 & 4 on the 2026-09-21 re-run). Row 4 even pressed Enter and retried the button 3×. Post-send `ui_states` and the model's own closing reason are the only reliable evidence; the trajectory's "clicked" line is not. | every "message X" deliverable |
| ~~App-private seeds with no file backup~~ ✅ **fixed 2026-09-22** | OnePlus Notes `Budget Deadline` — adb cannot recreate it, but the text is now version-controlled (`assets/seeds/public/Budget Deadline (OnePlus Notes).txt`) and `restore_budget_note()` re-types + verifies it (`text_count` 518) | `hard__drive-notes-telegram__010` |
| Cloud account drift | Slides drifted to `rajceo2031`; caught only by the account gate | 25 of 60 tasks touch a cloud app |
| Live external data | BookMyShow listings, Maps ETAs, Swiggy/Amazon/Prime state | 10 of 60 tasks |
| Grader blind spots | Slides has no ground truth (1/3/8 all passed); Sheets exposes no cell data to the a11y tree | `*google-slides*`, `*google-sheets*` |

### 7.3 Scope note on the new recurring-artifact sweep

`calendar_recurring_artifacts_to_remove` is **public_v2-only, deliberately**:
`Weekly_Standup` is a legitimate *seed* for the 530 `day_N` profiles
(`scripts/seeding/verify_day1_seeds.py` asserts it). The sweep must never run there.

### 7.4 Pre-run vs post-run reset: the harness now closes the start-state hole (2026-09-22)

The distinction that matters, since "we reset between runs" was being read as covering more
than it did:

| | **Post-run reset** (`reset_phone.py --apply`, before a *batch*) | **Pre-run reset** (`cli.py`, before *every task*) |
|---|---|---|
| Scope | whole device → canonical seeds | the **focused app** only |
| Resets | files, calendar, provider DBs, now two leak repairs | the app's **screen** (force-stop + HOME) |
| Resets app **data**? | only for the two named leaks | ❌ no — a draft/edit still survives it |

So both holes were real and neither was redundant: the post-run reset cannot run between
tasks in a batch (it would wipe seeds a previous task legitimately consumed), and the
pre-run reset cannot see app content. Concretely, this is why `5–11 (vision/text) FAIL` is
**not** a start-state artifact — every one of the 13 re-runs began on the launcher
(`🏠 LAUNCHER` in its first `ui_states`), so those failures are model behaviour, not
inherited screens. The pre-run package is recorded per run as
`pre_app_reset_stopped_package` in `meta.json`, so a run that starts inside an app is now
visible in the artifacts instead of having to be inferred from `ui_states/0001`.
`get_foreground_package()` was hardened at the same time: it previously read only
`mCurrentFocus`, which is `null` whenever nothing holds input focus (transient dialog,
notification shade, mid-animation) and made the force-stop a silent no-op — three of the
2026-09-21 re-runs recorded `None` while parked inside `com.oneplus.note`. It now falls
back to `mFocusedApp`, then the resumed-activity line.
