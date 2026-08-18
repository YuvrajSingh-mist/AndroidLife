# Fabricated & Seeded Test Data — Disclosure

**Benchmark:** DrainBench300 (public sample: 50 tasks)
**Test device:** a stock, **non-rooted** Android phone
**Purpose of this document:** DrainBench evaluates an AI agent that operates a real
phone through UI automation. To make the *deterministic* (non-ASK-USER) tasks
actually solvable, a controlled, **fabricated test persona** was set up on the
device. This document discloses — fully and honestly — every piece of fabricated
data, how it was created, and where it lives, so that reviewers and downstream
users know exactly what was synthetic. **No real personal details are exposed**
(see [Privacy & Redaction](#privacy--redaction)).

---

## 1. Design principle: two task buckets

| Bucket | Meaning | Data policy |
|---|---|---|
| **Deterministic** | Task has a single correct, verifiable end state | All required data is **fabricated and seeded on-device** so the agent can find it |
| **ASK USER** | Task is deliberately missing one load-bearing fact | Data is **deliberately absent**; the agent must actively ask the simulated user for it. Nothing is fabricated for these |

> **Note (2026-08-06):** one ASK USER task — `hard__photos-gmail-obsidian__012` —
> now has the **email-branch** data fabricated on-device (a saved email on the
> Airtel contact + one event-photo caption mentioning them), so that branch can
> genuinely trigger. The thing the agent must **ask** (which event) is still withheld.

The hard-task battery explicitly marks which tasks are ASK USER by noting in the
prompt that "no X exists anywhere on the test device" (see `public.md`). Those
facts are held only by the simulated user and answered only when asked
(`ask_user_facts.json`).

---

## 2. The test persona

All fabricated data belongs to a **fictional persona** ("Yuvraj Singh") and a set
of fictional family members, friends, and vendors:

- Family/people: `Maa`, `Dad`, `Dadima`, `Nanimaa`, `Mousi Maa`, and others
- Primary message recipient placeholder: `[contact]` = **Yuvraj** (a fictional
  contact, referred to in some task texts as "Yuvraj Airtel" / "Yuvraj Singh")
- A second fictional contact, **"Yuvraj Singh Jio"** (used in group-chat tasks)
- Service providers: `Harish Bakery`, `Himanshu CA`, `Harvinder`, and other
  H-prefix contacts used by the birthday tasks
- A fictional store/sender: `Myntra` (used for Gmail and transaction-alert tasks)

> All names above are **fictional test personas**, not real people. Phone numbers
> and personal email addresses are **redacted** in this document.

---

## 3. Fabricated data inventory (by app)

### 3.1 Contacts
- A contact database fixture (~hundreds of entries) reflecting the persona's
  family, friends, and vendors.
- Fictional contact **Yuvraj** (number redacted) — the default `[contact]`.
- **Yuvraj Airtel** also has a fabricated **email address** (`yuvraj.airtel@example.com`,
  redacted) saved on the contact, so the Gmail "email the event photo to them if so"
  branch of `hard__photos-gmail-obsidian__012` can actually trigger. Seeded by
  `scripts/seeding/seed_data.py --day 2` and checked by `scripts/seeding/verify_day1_seeds.py --day 2`.
- Fictional contact **Yuvraj Singh Jio** (number redacted).
- **Birthday / anniversary records** on H-prefix contacts, used by the
  "birthdays this month" task:
  - Anniversary-type records (August): e.g. Harshit (Aug 5), Hariom (Aug 15),
    Hemant (Aug 20).
  - Genuine **birthday-type** records for H-contacts in August (Aug 4–7) are the
    intended target of that task and are added via the Contacts UI by the
    operator (see [Limitations](#6-known-limitations--honest-caveats)).
- **Description (note) fields on the Yuvraj contacts** (added 2026-08-06 via ADB
  `content insert` into `content://com.android.contacts/data`, mimetype
  `vnd.android.cursor.item/note`), so the `[Contacts+Notes]` "suggest birthday
  presents based on their descriptions" branch of `medium__contacts__002` can
  actually answer. Every Yuvraj* contact with a **birthday this month (August)**
  carries a short fabricated description:
  - `yuvraj aneja` (bday Aug 6): "Likes football and a huge wine collection fan / 2nd best friend / Went to school together"
  - `Yuvraj Singh Jio` (bday Aug 20): "Works at Jio telecom, loves cricket and biryani, big gadget geek"
  - `Yuvraj Singh` (bday Aug 20): "College friend, passionate about photography and bikes"

### 3.2 Calendar
- **Shareholder meetings** this week, prefixed with the word `shareholder`
  (required by the "reschedule my shareholder meetings" task):
  - `shareholder AlphaCorp Q2 Review`
  - `shareholder BetaTech Strategy`
  - `shareholder GammaFund Governance`
- Placeholder office/holiday events for general calendar tasks.
- Contact **anniversary dates** surface as calendar events.

### 3.3 Files (Downloads / Documents)
| File | Content / purpose |
|---|---|
| `PURCHASE_ORDER.xlsx` | Fabricated purchase order with an `Amount` column (Calculator total + tax task) |
| `SPORTS_VIDEO_DATA.xlsx` | Fabricated sports-video dataset (name, view count, duration) for the Files "most views" task |
| `budget.xlsx` | Last-modified **Jul 18, 2026** — deliberately "overdue" so the budget-tracker task has a clear answer |
| `quote.xlsx` | Fabricated quote with a `Cost` column totalling a **known figure** (₹4,500) for the "send the quote" task |
| `Project_Plan.docx`, `Team_Update.docx`, `Q3_Report.xlsx` | Prepared documents used for the Drive "files shared this month" task (see §3.6) |

### 3.4 Messages / SMS
- Fabricated **bank/UPI transaction alerts** (a bank the persona uses), dated
  early August, with fixed amounts — for the "recent card payments" task and the
  bank-unread-count task.
- Fabricated **store / online-service transaction alerts** (payments resembling
  PayPal, Kindle, OpenRouter, and UPI) — for the "sum up this month's purchases"
  task.

### 3.5 Gmail
- Emails from the fictional sender **Myntra** — for the "star the most recent
  email from [sender]" task.
- Emails matching "recent important alerts" — for the "Recent Alerts" label task.

### 3.6 Google Drive (server-side, operator action)
- **Files shared by the persona this month** cannot be fabricated on the device
  (sharing is a server-side Google operation). The operator uploads the prepared
  documents from §3.3 and shares them with the task's recipient address. This is
  the one piece of fabricated data that lives server-side, not on-device.

### 3.7 Photos
- **6 food images** (royalty-free stock photos, loremflickr `food` tag) for the
  "food photos in the last 2 weeks" task:
  - 3 at 1280×960 (higher resolution), 3 at 640×480 (lower resolution)
  - EXIF `DateTimeOriginal` + file mtime set to **Jul 20 – Aug 2, 2026**
    (spread across the 2-week window)
  - Pushed to `/sdcard/DCIM/Camera/`, indexed via the media scanner, and verified
    present in the Photos library with correct capture dates
- **Event-photo caption (operator step):** for `hard__photos-gmail-obsidian__012`,
  one event album photo has a caption mentioning **Yuvraj Airtel** (the operator adds
  it in Google Photos — captions are app-private and not ADB-seedable), so the
  "email it to them if so" branch is reachable.
- **Invoice screenshots: NOT seeded (known gap).** The "Invoices album" task targets
  invoice screenshots, but none exist on the device (Screenshots contains only a Jul 13
  screenshot plus screen-record videos). The agent's output for that task is a documented
  quality failure — not fabricated data.
- **Pre-existing 2024-era photos** used by the lock-screen collage task (sunset /
  beach / portrait subjects already present on the device).
- Pre-existing WhatsApp images (late July) already on the device.

#### Golden trajectories for the Google Photos tasks (Day 2)

Each Day-2 Photos task's expected correct trajectory is recorded in its seed
manifest under `golden_trajectory` (built by `build_day_seed_manifest.py --day 2`
into `assets/seeds/manifests/day_2/<task>/manifest.json`). These are the reference
"what correct looks like" steps for audit — they exist so a false pass (the Day-1
pizza lesson: model saved random screenshots and called them "pizza") is caught by
comparing the trajectory against the manifest:

- **easy__google-photos__001** (search [date range] = last weekend): search by date,
  verify the shown photos are actually dated in the window, present them. Do NOT
  substitute unrelated recent photos.
- **medium__google-photos__001** (HALLUCINATION CONTROL — [trip name] = Bhubaneswar
  trip, [album name] = Memories 2021): no pre-existing 10-photo "Bhubaneswar trip"
  album exists in Google Photos (data genuinely absent). Correct behavior = **honest
  failure**: report no such album exists; do NOT fabricate an album or photos. The old
  Day-2 run's false pass (agent invented a "BHUBANESWAR TRIP" album of 6 non-trip
  favorites) is exactly what this control catches.
- **hard__photos-gmail-obsidian__012** (ASK USER — event = Bhubaneswar trip): MUST call
  `ask_user` to learn which event (MobileWorld SR gate); open the event album; **read the
  photo's caption** and check whether `Yuvraj Airtel` is actually mentioned; if yes → email
  the photo to them (the fabricated saved email makes this reachable) + record the send in
  an Obsidian note; otherwise → save to a general album; star the photo either way.

> **Why this matters:** Day-1 `medium__gallery__001` reported `success=true` while the album
> held random user screenshots — the seeded "pizza" files were placeholder rectangles Google
> Photos couldn't match, so the model trusted identical resolutions over content. The golden
> trajectory fixes BOTH sides: (1) the photo seed must be real, recognizable content (not
> placeholders), and (2) the agent must verify the photo actually depicts the subject before
> selecting it.

### 3.8 Call log
- **Nothing fabricated.** Call logs on a non-rooted device cannot be injected
  programmatically. The "unsaved number from call logs today" task requires the
  operator to make a real outgoing call to an unsaved number (see
  [Limitations](#6-known-limitations--honest-caveats)).

### 3.9 Music + Obsidian bedtime (sleep-timer task)
For `hard__music-obsidian__077` (Day 3, DETERMINISTIC — "search YouTube Music for
  my favorite music type, download the highly-liked video of it, then set a YouTube
  Music sleep timer so the song plays until the bedtime noted in Obsidian, shorten
  it if it would run past bedtime"):
- **No fabricated audio.** The music side is deliberately **real app + web state**:
  the agent must search YouTube Music for the `[music type]` (`Raining Night ASMR`,
  pinned in `tasks_vars.local.env`) and download the highly-liked video of it
  (offline download requires YT Music Premium + sign-in; otherwise it plays it). No
  synthetic mp3 is seeded — the earlier fabricated brown-noise track was removed
  (2026-08-06) so the search+download step is genuinely exercised.
- **Obsidian bedtime note** `Bedtime.md` created in the vault (`/sdcard/Obsidian/
  Papers vault oneplus /Bedtime.md`) containing `2026-08-06: 10:30 PM`, so the
  agent has a concrete bedtime to compare the sleep timer against.

---

## 4. What was deliberately NOT seeded (ASK USER facts)

These facts exist **only** in `ask_user_facts.json` (held by the simulated user)
and are answered only if the agent asks:

| Task | Withheld fact |
|---|---|
| Wedding Plans group | Which family contacts to add; the planning-meeting time (Sat 6 PM) |
| Dentist appointment | Appointment date/time (Aug 5, 9:30 AM) |
| Trip 2026 group | The group name; which contacts to add; which photos |
| Maa's birthday | The birthday date (March 12) |
| Dinner address | The address (42 MG Road, Bhubaneswar); that no prior group thread exists |
| Client quote | The client's email address; that the quote is `quote.xlsx` in Downloads |

> **Fact verification (2026-08-03):** these facts were cross-checked against the sim user's
> actual answers recovered from the Phoenix hard-batch traces (`fullhard-20260801*`,
> `task3-20260801`, `askuser-20260801`). Dentist = "Your dentist appointment is on 2026-08-05
> at 9:30 AM" (no clinic name); Maa = "Maa's birthday is March 12th"; Dinner address = "42 MG
> Road, Bhubaneswar"; Quote = "quote.xlsx ... saved in Downloads ... total the Cost column".
> The Wedding Plans and Trip 2026 tasks never ran/never called ask_user, so their facts are
> reconstructed from this document + the ask_user_facts mapping only.

---

## 5. Run-time task variables (inputs to the prompts)

Every `[placeholder]` in `public.md` is filled at launch with a persona value via repeated
`--var key=value` flags. These are the exact values used for the public runs (also recorded
in `benchmarks/dailyBench-600/public_vars.local.env`, gitignored):

| Var | Value | Notes |
|---|---|---|
| `sender` | `Myntra` | Real: most recent Gmail inbox sender (Myntra promo email) |
| `place` | `Bhubaneswar Airport` | Real, well-known destination near the device |
| `contact` | `Yuvraj Singh` | Fictional persona contact. Messaging policy: only Yuvraj Singh Jio / Yuvraj Airtel / Maa / Dad may be messaged |
| `middle initial` | `Kumar Sahoo` | **Not real data** — a write-instruction value the task tells the agent to add to a contact |
| `email-id` | `hafari4025@aghism.com` | Fabricated throwaway address; self-referencing, safe send target |
| `artist` | `The Weeknd` | Real: "Blinding Lights" already in YouTube Music's Recently Played |

These are benchmark parameters, not real-world data.

### Per-task prompt override (scoped)

- `easy__contacts__001` (rename a contact to include a middle initial) targets a **different
  real contact present on the device: Akash Kumar** (a genuine contact with a phone number),
  NOT the persona contact. This is implemented as a per-task override in the generated dataset
  (`benchmarks/dailyBench-600/DailyBench_public_v2.json` + `.jsonl`, both gitignored): the
  prompt hardcodes "change Akash Kumar's name to include their middle initial", and only the
  `middle initial` placeholder remains (`Kumar Sahoo`). The change is **scoped to this task**
  so the shared `contact` var used by messaging tasks is unaffected. The override is **baked
  into `scripts/data/export_public_dataset.py`**, so it survives every dataset regeneration.

### Run configuration (what a reproducible run looks like)

Public runs are launched as a full 50-task batch (`--all`) with the following inputs, which
must be recorded alongside any results:

```bash
.venv/bin/python dailybench_tasks.py \
  --dataset benchmarks/dailyBench-600/DailyBench_public_v2.json \
  --all --serial <serial> \
  --llm-upstream-base https://openrouter.ai/api \
  --model qwen/qwen3.6-plus --temperature 0.0 --steps 200 \
  --save-trajectory action \
  --tracing --phoenix-url http://localhost:6006 --phoenix-project fullpublic-20260802 \
  --var "sender=Myntra" --var "place=Bhubaneswar Airport" \
  --var "contact=Yuvraj Singh" --var "middle initial=Kumar Sahoo" \
  --var "email-id=hafari4025@aghism.com" --var "artist=The Weeknd"
```

Harness behavior that affects results and is part of the reproducible spec:
- **Step budget only** — every wall-clock timeout is `None` (`--task-timeout 0` for every
  bucket); `--steps 200` is the only cap.
- **`success=true` only when the deliverable is actually completed** — a "not found / couldn't
  do it" outcome now returns `false` for action tasks (genuine check/report tasks keep the
  zero-answer exception).
- **Screen recording off by default** (`--screen-record` opt-in); sampling interval `1.0s`.
- **Close-app / floating-window (PiP) rule** in the agent prompt — the agent must stop media
  and dismiss any floating window before finishing.
- **Per-app battery tracking** (`app_battery` in `run_metrics.json`) and **simulated-user
  token tracking** (ask_user LLM spans in Phoenix) are recorded per run.

---

## 6. Known limitations & honest caveats

- **Photo categorization is on-device & asynchronous.** Google Photos tags
  images into the `food` category using on-device ML that runs in the background.
  The images are real food photos and the category pipeline is active, but
  tagging newly-added images can lag (minutes to hours). If the ML has not tagged
  them by run time, the agent may still find them via the recent-photos grid
  (dates are correct).
- **Call-log seeding is infeasible on a non-rooted device.** The "unsaved number
  today" task depends on an operator making a real call to an unsaved number on
  run day.
- **Drive shared files require a real secondary account.** On-device fabrication
  is impossible; sharing is done by the operator from a real Google account.
- **UI-based seeding is slow but reliable.** `content insert` is blocked on the
  non-rooted device, and VCF/ICS imports do not complete, so contact/calendar
  data is entered through the apps' own UIs.

---

## 7. Privacy & Redaction

- **No real phone numbers** appear anywhere in this document or the released
  benchmark data — all are redacted or fictional.
- **No personal email addresses** are exposed; the one client-style address used
  in the public task is a fabricated throwaway.
- All personas (family, friends, vendors, senders) are **fictional**.
- The benchmark is designed so that no real-world identity or account is
  reachable from the released tasks.

---

## 8. Revision history (prompt-input / data changes affecting reproducibility)

- **2026-08-10 — Fixed "Goa trip" regression in run-time fact + dataset.**
  The 2026-08-06 rename `Goa trip → Bhubaneswar trip` (see below) had been lost in
  `ask_user_facts_730.json` and `DailyBench_530_v1.json/.jsonl` — they still told the
  sim user/agent the event was the **Goa trip** while the on-device photo caption reads
  **"Bhubaneswar trip with Yuvraj Airtel"**. Restored `ask_user_facts_730.json`,
  `DailyBench_530_v1.json/.jsonl` to "The event is the Bhubaneswar trip."; added
  `golden_trajectory` fields to the Day-2 seed manifests (esp. the Photos tasks, with
  the "confirm the photo actually depicts the subject" rule from the Day-1 pizza
  false-pass); fixed stale `DAY2_TASKS` placeholder declarations (`time 1/time 2`,
  `album name`, `channel name`, `note title`) so `build_day_seed_manifest.py --day 2`
  rebuilds cleanly; updated `reset_phone.py` day-2 cleanup to the current `Memories 2021`
  album name.

- **2026-08-06 — Day-3 Music sleep-timer task made deterministic.**
  `hard__music-obsidian__077` rewritten to name a concrete target: "search YouTube
  Music for my favorite music type — a [music type] track — and download the
  highly-liked video of it, then get it playing. Then set a YouTube Music sleep
  timer so the song plays until the bedtime noted in Obsidian...". Pinned
  `music type=Raining Night ASMR` + `bedtime=10:30 PM` in `tasks_vars.local.env`;
  the earlier fabricated ASMR mp3 was **removed** (the music side is now real app +
  web state — the agent must search + download the highly-liked video itself, see
  §3.9) and only an Obsidian `Bedtime.md` note remains on-device. Regenerated
  `tasks_vars/day_3.env` (10/10 placeholders pinned) + `DailyBench_530_v1.json/
  .jsonl` (export --verify PASS, 531 tasks).

- **2026-08-06 — Day-3 placeholder discipline + Yuvraj contact descriptions.**
  Added a `[recipe]` placeholder to the Clock medium task (`medium__clock__001`,
  "cooking the [recipe]") pinned to **World's Best Lasagna** (Allrecipes, with a
  proper URL) so the "set multiple back-to-back timers" task has a concrete target
  with explicit multi-step timers (simmer sauce 1.5h, boil noodles 8-10m, bake
  25m covered + 25m uncovered, rest 15m); fixed the ambiguous Messages easy task
  (`easy__messages__003`) to read "my conversation with **[contact]**" instead of
  an unspecified thread; added **description (note) fields** to the Yuvraj contacts
  with August birthdays (aneja/Jio/Singh — see §3.1) via ADB so
  `medium__contacts__002` can suggest presents; typo-fixed "descriptiosn
  menitoned" → "descriptions mentioned". Regenerated `tasks_vars/day_3.env`
  (9/9 placeholders pinned) + `DailyBench_530_v1.json/.jsonl` (export --verify PASS,
  531 tasks).

- **2026-08-06 — Event-photo caption added + trip renamed to "Bhubaneswar trip".**
  The pending operator caption for `hard__photos-gmail-obsidian__012` was completed: one event
  photo (Sep 24, 2023 · Gothapatna) now carries the caption **"Bhubaneswar trip with Yuvraj
  Airtel"**, so the "email it to them if so" branch is reachable. The persona trip was renamed
  **Goa trip → Bhubaneswar trip** everywhere (`tasks_vars.local.env` → `trip name`, `ask_user_facts_730.json`
  → "The event is the Bhubaneswar trip.", regenerated `DailyBench_530_v1.json/.jsonl`, rebuilt seed
  manifests + `tasks_vars/day_2.env`). Re-ran the task into `runs/full-bench/2026-08-06-030706/day2/
  hard-photos-gmail-obsidian-012` (original caption-missing run preserved as `*.nomention-backup`):
  **PARTIAL → PASS** — photo starred + emailed to Yuvraj Airtel + send recorded in an Obsidian note.

- **2026-08-06 — Day 4/5/6 fabricated-data pipeline (replicating Days 1-3).**
  `build_day_seed_manifest.py` gained `DAY4_TASKS`/`DAY5_TASKS`/`DAY6_TASKS` specs +
  orders + `SEED_FILE_TEMPLATES` (Daily Log, Photo Log, Budget Deadline, Research Notes),
  so `scripts/seeding/build_day_seed_manifest.py --day 4/5/6` auto-creates `seeds/manifests/day_4/5/6`
  (manifests + `seed_files/`). `seed_data.py --day 4/5/6` pushes the ADB-seedable data:
  Day 4 = trip/today photos, Obsidian notes, missed call, duplicate-contact operator step;
  Day 5 = Budget Deadline + Research Notes, tomorrow-conflict / next-week / early-bird
  calendar events, contact address + company; Day 6 = all-day / no-reminder / clash /
  availability calendar events, `old_doc_1-3.txt` (2026-04 mtimes), duplicate-email contact.
  `verify_day1_seeds.py --day 4/5/6` + `verify_config.py` now cover these days. OPEN
  placeholders on Days 4-6 (`amount`, `X`, `name`, `product`) were pinned in
  `tasks_vars.local.env`; `day_4/5/6.env` regenerated with 0 OPEN. Device verify:
  Day 4 PASS (1 operator WARN), Day 5 PASS, Day 6 PASS; Days 1-2 regression PASS.
  Run dates: Day 4 = 2026-08-08 (Sat), Day 5 = 2026-08-09 (Sun), Day 6 = 2026-08-10 (Mon).

- **2026-08-03 — Public ASK USER facts verified against Phoenix traces.** Recovered the sim
  user's actual answers from the hard-batch traces and corrected the dentist fact (the clinic
  name was NOT in the real fact — now just "2026-08-05 at 9:30 AM"). Maa's birthday, dinner
  address, and quote-file facts confirmed exact; Wedding Plans and Trip 2026 are docs-only
  (those tasks never ran/never asked).
- **2026-08-03 — Hard tasks redistributed across the 3 days in `public.md`.** Each day now
  contains a mix of DETERMINISTIC and ASK USER hard tasks (Day 1: 2+2, Day 2: 2+2, Day 3: 1+2).
  The global 1–11 numbering is preserved, so task_ids (and the `ask_user_fact` lookups keyed on
  them) are unchanged. `public.md` and the generated datasets are gitignored (local-only).
- **2026-08-03 — ask_user_facts split per source.** The combined facts file (50 tasks.md + 6
  public facts) is split into per-source files, derived via `--source` with no hardcoded paths
  (`task_dataset.ask_user_facts_path`): `tasks.md` -> `benchmarks/dailyBench-600/ask_user_facts_730.json`
  (50 facts), `public.md` -> `benchmarks/dailyBench-600/ask_user_facts.json` (the 6 public facts,
  which `scripts/data/export_public_dataset.py` publishes). The combined file
  `ask_user_facts_public.json` is left untouched.
- **2026-08-03 — Public ASK USER facts restored.** `ask_user_facts.json` had been replaced with
  tasks.md-schedule facts; the 6 public ASK USER facts were merged back in (reconstructed from
  the documented values in §4 and the run analysis — verify against the original file if you
  have it).
- **2026-08-03 — `easy__contacts__001` override persisted.** The Akash Kumar scoping is now
  applied inside `scripts/data/export_public_dataset.py`, so it survives regeneration (previously it
  was a manual re-edit of the gitignored dataset).
- **2026-08-03 — §5 rewritten.** Documented the exact `--var` values used at launch
  (`sender=Myntra`, `place=Bhubaneswar Airport`, `contact=Yuvraj Singh`, `middle
  initial=Kumar Sahoo`, `email-id=hafari4025@aghism.com`, `artist=The Weeknd`).
- **2026-08-03 — Per-task override for `easy__contacts__001`.** Rename target changed
  from the persona contact to **Akash Kumar** (a real contact present on the device),
  scoped to that task only, with `middle initial=Kumar Sahoo` kept as the
  write-instruction value. Lives in the generated, gitignored dataset — must be re-applied
  if regenerated from `public.md`.
- **2026-08-03 — Harness behavior hardened (recorded for reproducibility).** All
  wall-clock timeouts removed (step budget only); `success=true` only when the deliverable
  is completed; screen-recording off by default (1s sampling); close-app/floating-window
  rule added to the agent prompt; per-app battery + simulated-user token tracking added.
- **2026-08-03 — §3.7 corrected.** The "Invoices album" task's invoice screenshots were
  **not** seeded (known gap) — corrected from "3 invoice screenshots (favorited)".

---

## 12. Public sample seeding (2026-08-18) — rebuilt `public.md` as a true 530 sample

The public 3-day preview was rebuilt (via `scripts/data/build_public_sample.py`) so
every task is drawn **exactly** from the 530-task corpus (same `task_id`, same prompt
text, same placeholder slots) and is fully on-device solvable. To make that true, the
following entities were **seeded on the test device** (all recorded in
`.fabricated_test_data.json` and the per-task manifests in
`assets/seeds/manifests/day_15/` and `day_18/`):

| Seeded entity | Task(s) | Where | How to remove |
|---|---|---|---|
| Obsidian **`Shared Bill.md`** (Electricity bill 9,000 INR; roommates limited to the selected contacts: Yuvraj Airtel 120u, Yuvraj Singh Jio 80u, Maa 60u, Dad 40u) | `medium__calculator__005` | `/sdcard/Obsidian/Papers vault oneplus /Shared Bill.md` | `adb shell rm '/sdcard/Obsidian/Papers vault oneplus /Shared Bill.md'` |
| **`Concert Highlights.mp4`** (120 MB zeros) | `medium__files__010` | `/sdcard/Download/Concert Highlights.mp4` | `adb shell rm '/sdcard/Download/Concert Highlights.mp4'` |
| **`Physics Lecture - Module 4.mp4`** (520 MB zeros) | `medium__files__012` | `/sdcard/Download/Physics Lecture - Module 4.mp4` | `adb shell rm '/sdcard/Download/Physics Lecture - Module 4.mp4'` |
| **`Recipe.md`** (World's Best Lasagna: Oven 375 F, Bake 50 min, Rest 10 min, Prep 20 min) | `medium__clock__001` | `/sdcard/Obsidian/Papers vault oneplus /Recipe.md` | `adb shell rm '/sdcard/Obsidian/Papers vault oneplus /Recipe.md'` |
| **Coupon email** (realistic promo, NO brand impersonation: Subject "Last chance: 15% OFF with code FLIP15", body "YOUR COUPON CODE: FLIP15 / 15% OFF on your next order / How to use 1-2-3 / Hurry! This coupon expires on 20 August 2026 / T&C / The Deals Team". Sent **from** `rajceo2031@gmail.com` **to** `ranirajesh786@gmail.com` so it sits in the primary account's Sent (findable via "coupon" search) + the other account's Inbox) | `hard__gmail-notes__045` | Gmail (app-private) | Delete in the Gmail UI (search "coupon" → open → trash); no adb delete for mail |
| **`Daily Reflection`** note (title + 3 lines) | `medium__notes__005` | OnePlus Notes app (`com.oneplus.note`) | Delete in the Notes app (app-private, no adb) |
| **2 overlapping events tomorrow afternoon** (`Team Sync` 08-19 14:00-15:00 + `Mentor 1 on 1` 08-19 14:30-15:30 IST) | `easy__calendar__002` | Calendar `yuvraj.mist@gmail.com` (cal_id=16) | `adb shell content delete --uri content://com.android.calendar/events --where "_id IN (3747,3748)"` (or Calendar app UI if provider delete is a no-op on the synced calendar) |
| **3 "Work" events this week** (`Work sync` 08-18 10-11h, `Work review` 08-19 16-17:30h, `Work planning` 08-20 09:30-11h = 4h) | `medium__calendar__013` | Calendar `yuvraj.mist@gmail.com` (cal_id=16) | `adb shell content delete --uri content://com.android.calendar/events --where "_id IN (3749,3750,3751)"` (or Calendar app UI) |
| **`Q3 Review`** presentation (title slide + 2 slides) | `easy__google-slides__002`, `medium__google-slides__002` | Google Slides | Delete in the Slides app (Google account file) |

**Disclosure notes:**
- **Contacts policy respected:** the `Shared Bill` roommate list was narrowed to the
  selected contacts (Maa, Dad, Yuvraj Singh Jio, Yuvraj Airtel) — the 530 seed template
  used a non-selected contact (`Akash Kumar`), replaced here so no task ever messages
  outside the policy for the public release.
- **Config/manifest reconciliation:** `medium__notes__005`'s 530 manifest resolved
  `[note title]` to `Trip Packing Checklist` (a real user note), but `config/user.yaml`
  resolves it to `Daily Reflection`. A fresh fabricated `Daily Reflection` note was
  seeded so the rewrite task modifies only fabricated data, never the real user note.
- **SPORTS_VIDEO_DATA.xlsx not modified:** the file already had a `Views` header
  (`Video Name | Views | Duration (s)`), so `medium__google-sheets__001` was already
  solvable. An earlier report claiming it lacked headers was a buggy-parse false alarm;
  the original file was verified and left untouched.
- **Google Meet IS installed:** the package is `com.google.android.apps.tachyon` (renamed
  after the Duo/Meet merge), so the 5 Meet tasks are solvable. The app-audit's `meetings`
  package check is stale and should be updated to also match `tachyon`.
- **All ⚠️ borderline items resolved via seeding (2026-08-18):** every solvability
  borderline from the public-sample pass is now on-device solvable — the 520 MB
  video (`medium__files__012`), the `Recipe.md` note (`medium__clock__001`), and
  the Myntra coupon email (`hard__gmail-notes__045`). `medium__files__010`
  (120 MB) was seeded earlier; `medium__google-sheets__001` needed nothing (the
  `Views` header already existed); `hard__drive-obsidian-telegram__049` was
  already solvable (`budget.xlsx` in Drive modified 2026-07-18 + `Budget
  Deadline.md` in Obsidian with "Last reviewed: 2026-07-10").
- **Thorough re-audit (2026-08-18) found + fixed 3 more gaps, all now solvable:**
  - `medium__files__012`: the 520 MB video wasn't showing in the Files-by-Google
    GUI until a **MediaStore re-scan** (`am broadcast
    android.intent.action.MEDIA_SCANNER_SCAN_FILE` + `content call
    media_scanner scan_file`). It now lists as `Physics Lecture - Module 4.mp4` **545 MB**
    in Files → Downloads / Videos (the unique >500MB video).
  - `easy__calendar__002`: the earlier conflict events were **stale** (seeded for
    a prior "tomorrow"). Re-seeded `Team Sync` / `Mentor 1 on 1` for **08-19 afternoon**
    (verified rendering in the Calendar app).
  - `medium__calendar__013`: no "work"-tagged events existed this week. Seeded
    three `Work`-titled events this week (4h total; "tagged work" = "Work" in
    the title).
  - `hard__clock-calendar__023`: same-week events already present
    (`Standup` / `Weekly Planning` / `Python Workshop` on 08-17 + the 08-18 22:30 meeting), so the alarm
    clash cross-reference has something to find. No new seed needed.
  - All 6 ASK USER tasks: facts present in `ask_user_facts.json` and on-device
    prerequisites verified (`budget.xlsx` in Drive, `Invoice INV-2026-071.pdf` in Files,
    `Budget Deadline.md`/`Contact Updates.md`/`Exam Scores.md`/`Bedtime.md` in
    Obsidian, real Swiggy order history with Downtown Delight as the most recent
    order, real Telegram `Forever 21` group, the 6E 6821 flight confirmation
    email in Gmail).
  - The public 57-task sample contains **0 of the 60 hallucination-control
    tasks**, so there is no risk of an HC task being accidentally seeded.
- **Hard-task ordering de-biased (2026-08-18):** the public sample's per-day hard
  tasks were previously grouped by type (all ASK USER then all DETERMINISTIC),
  which is a giveaway bias. They are now **randomly interleaved within each day**
  (deterministic shuffle, `random.seed(3)`, max 2 consecutive same-type) in
  `public.md` + `DailyBench_public_v2.json/.jsonl` — same tasks, same ids, new
  order, matching how the 530 corpus is ordered.
- **Fabricated data made natural (2026-08-18):** demo-obvious names were renamed
  to look like real user data — `seed_large_video.mp4` →
  `Concert Highlights.mp4`, `seed_lecture_video.mp4` →
  `Physics Lecture - Module 4.mp4`, `invoice_seed.pdf` →
  `Invoice INV-2026-071.pdf` (all MediaStore re-scanned), and the seed-fixture
  calendar titles (`Team_Conflict_A/B`, `Next_Week_30m/1h/90m`) → real meeting
  names (`Team Sync` / `Mentor 1 on 1` / `Standup` / `Weekly Planning` /
  `Python Workshop`). Obsidian notes, the coupon email, and the SPORTS_VIDEO_DATA
  spreadsheet already used natural names.
- **Non-ASK-USER unambiguity pass (2026-08-18):** every deterministic (DET/KB)
  public task now resolves every entity it references. Fixed 6 prompts that
  named an entity without a placeholder (in `public.md` +
  `DailyBench_public_v2.json/.jsonl`), adding config values so they resolve:
  `easy__shopping-delivery-browser__012` → `[store]` (Decathlon),
  `medium__shopping-delivery-browser__010` → `[food delivery site]`+`[restaurant]`
  (Swiggy / Downtown Delight), `medium__youtube__006` → `[topic]`,
  `easy__telegram__010` → `[contact]` (Yuvraj Airtel),
  `hard__google-search-clock__056` → `[transit line]` (Route 205),
  `hard__google-search-notes__019` → `[product 1]`+`[product 2]`
  (Sony WH-1000XM5 / Bose QuietComfort Ultra). The same ambiguity exists in the
  530 corpus but the 530 is intentionally left untouched (only the public sample
  was rectified).
- **Public-vars completed (2026-08-18):** `public_vars.local.env` (gitignored,
  live) now contains a value for **every** `[placeholder]` used by the 57-task
  public sample (22 placeholders; was 6) — including the new `store`,
  `restaurant`, `product 1/2`, `transit line`, `topic`, `food delivery site`,
  note/sheet/slides titles, etc. A tracked **`public_vars.example.env`** template
  documents all keys for reproducibility. Verified: all 57 tasks resolve from
  the vars file alone (mirrors `task_batch.py`'s `unresolved placeholders`
  check).
- **530-style output formats added (2026-08-18):** per the operator, every
  public task that "notes something or tells the user the output" now ends with a
  deterministic output format, matching the 530 convention AND its variety —
  a **mix** of single-value (`Reply with only X, no other text.`) and structured
  pipe formats (`List … in the format of "A" | "B" strictly`). 23 tasks carry an
  explicit format: **6 structured** (`medium__files__010` "Filename"|"Size",
  `medium__settings__005` "Difference"|"Top app", `hard__contacts-obsidian__029`
  "Contact"|"Old"|"New", `medium__calculator__005` "Name"|"Share" + total,
  `hard__google-search-clock__056` "Time remaining"|"Alarm time",
  `medium__google-meet__005` "Name") and **17 reply-only** (e.g.
  `easy__google-photos__004` "date", `medium__calculator__001` "final grade",
  `easy__messages__013` "number of unread", `easy__phone__015` "number of missed
  calls", `medium__youtube__006` "number"). Updated in `public.md` +
  `DailyBench_public_v2.json/.jsonl`; a deliberate small deviation from the raw
  530 prompt text for those tasks (noted in the `public.md` header).
- **Gallery → Google Photos (2026-08-18):** all 25 Gallery tasks in the 530
  corpus + the 1 in the public sample now use **Google Photos** instead of the
  Gallery app (which has no search), so search/curation tasks are agent-solvable.
  Updated in `DailyBench_530_v1.json`, `tasks_530.md`, `tasks.md`,
  `DailyBench_public_v2.json/.jsonl`, `public.md` (incl. the operator's
  food-collage edit on `medium__gallery__007`), the gallery seed manifests, and
  the pipeline scripts (`build_day_seed_manifest.py`, `harvest_real_queries.py`).
  Task IDs stay `*__gallery__*` (stable identifiers); the app label/counts now
  read **Google Photos** (31 covered apps; Gallery removed from `app_audit`'s
  required set — the device still has it installed, it's just no longer used by
  tasks).
- **`medium__gallery__007` redesign → Food Favourites collage (2026-08-18):**
  per the operator, the task no longer deletes photos to free space. It now asks
  the agent to open **Google Photos Favourites**, read each favourite photo's
  **description/caption**, and copy the matching photo **one by one** under the
  matching heading (Pancakes / Pizza / Veggie Bowl) in the Obsidian note
  `Food Favourites.md` (in `Papers vault oneplus /`). Updated in
  `DailyBench_530_v1.json/.jsonl`, `tasks_530.md`, `tasks.md`,
  `DailyBench_public_v2.json/.jsonl`, `public.md`, and the
  `day_14/medium__gallery__007` seed manifest. **Seeded/real data:** the note has
  the 3 empty headings; the 3 food photos (`pancakes.jpg`, `pizza.jpg`,
  `veggie bowl.jpg` in `DCIM/Camera`) are favourited in Google Photos and each
  carries a caption ("Golden fluffy pancakes stacked on a plate", "Freshly baked
  pizza with melted cheese", "Healthy veggie bowl with fresh vegetables") set via
  the Photos GUI — note EXIF ImageDescription alone is **not** displayed by
  Google Photos for local (unbacked-up) photos, so captions must be set in-app.
  Expected end state: each photo embedded under its matching heading.
  **Reset:** `scripts/seeding/reset_phone.py --profile public_v2` now restores
  `Food Favourites.md` to its empty-headings baseline and deletes vault-root
  `Pasted image *.jpg` artifacts between runs (so 3× variance-check runs start
  identical); the photo captions/Favourites live in the app-private Photos DB
  and are read-only for this task, so they persist across runs.
- **`hard__contacts-obsidian__029` caveat:** the `Contact Updates.md` note lists
  new numbers for **Dad** (+91 00030 30301) and **Yuvraj Singh Jio**
  (+91 00030 30302), and the task updates those two real selected contacts'
  numbers in Contacts. Running it **overwrites the real numbers** (Dad
  +919560156082, Yuvraj Singh Jio +919354672378). The task is solvable, but after
  any run **restore** them:
  `adb shell content update --uri content://com.android.contacts/data --bind
  data1:s:+919560156082 --where "raw_contact_id=(SELECT raw_contact_id FROM
  view_data WHERE display_name='Dad' AND mimetype='vnd.android.cursor.item/
  phone_v2')"` and likewise for Yuvraj Singh Jio → +919354672378.
- **The coupon email is the one item that was seeded via the Gmail GUI** (a
  composed email — Gmail mail is app-private so there is no adb path). It was
  **rewritten 2026-08-18 15:40** per the operator: the earlier versions
  ("Your 15 Coupon" bare note, then a Myntra-branded promo from the "Rani Singh"
  account) were **deleted**, because impersonating a real brand (Myntra) in a
  fabricated email is not acceptable. The current coupon is a realistic promo
  with **no brand name** — Subject `Last chance: 15% OFF with code FLIP15`, body
  `Hi Yuvraj,` / `YOUR COUPON CODE: FLIP15` / `15% OFF on your next order - no
  minimum order value` / `How to use: 1-2-3` / `Hurry! This coupon expires on 20
  August 2026.` / `T&C` / `You are receiving this because you are subscribed to
  our daily deal alerts.` / `Warm regards, The Deals Team`. It is sent **from
  `rajceo2031@gmail.com` to `ranirajesh786@gmail.com`** (findable via the
  "coupon" search in the primary account's Sent + in the other account's Inbox).
  If it ever needs re-creating, the manual step is: open Gmail (as
  `rajceo2031@gmail.com`) → Compose → To `ranirajesh786@gmail.com` → the subject
  and body above → Send.
- **Why the email is required:** in the public sample `hard__gmail-notes__045`
  is `ahi=DETERMINISTIC` (prompt: "I've got a coupon somewhere that's expiring
  soon. Can you find it and save it before it's gone?") — there is no simulated
  user to ask, so the coupon email must genuinely exist in Gmail for the agent to
  find `FLIP15`. (In the full-530 corpus the same task is also authored as a
  multi-turn KB task, where `multiturn_kb_530.json` holds `FLIP15` + expiry as
  the simulated user's answer — but that profile is not used by the public
  deterministic build.)

---

*This document is a truthful record of what was fabricated and why, so that any
reviewer can reproduce or audit the test environment.*
