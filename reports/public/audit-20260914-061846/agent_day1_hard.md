# AndroidLife Manual Audit — Day1 HARD (agent slice)

**Run root:** `/Users/yuvrajsingh1/Data/DrainBench300/assets/runs/public/20260914-061846/day1/`  
**Protocol:** `docs/manual-audit-protocol.md`  
**Ground truth:** `benchmarks/androidlife-530/{AndroidLife_public_v2.json,ask_user_facts.json,multiturn_kb_public.json,public_vars.local.env}`  
**ADB:** phone battery DEAD — **no on-device verification** this pass. Evidence = trajectory.json + ui_states + screenshots (Read).  
**Auditor slice:** 6 hard tasks only.

## Summary table

| Task | Agent claimed | ask_user | Manual verdict | One-line evidence |
|------|---------------|----------|----------------|-------------------|
| hard-contacts-gmail-026 | success / Confirmed | 0 (N/A) | **FAIL** | Clicked **Remove from Favorites** → end-state **unstarred** (hollow star); claimed starred |
| hard-drive-notes-telegram-010 | timeout | **0** | **FAIL** | ASK USER required; 0 `ask_user`; never opened `family_numbers.xlsx` / Telegram |
| hard-google-sheets-amazon-shopping-074 | max steps | 0 (N/A) | **FAIL** | Opened SPORTS sheet but never extracted max-views video; **never opened Amazon** |
| hard-swiggy-005 | max steps | **0** | **FAIL** | MULTI KB gate: 0 `ask_user`; stuck in Notes; never Swiggy reorder / Telegram |
| hard-telegram-calendar-016 | timeout | **0** | **FAIL** | MULTI KB gate: 0 `ask_user`; opened **Messages** not Telegram Forever 21; no calendar |
| hard-youtube-settings-052 | success / Tech Burner | 0 (N/A) | **FAIL** | Tech Burner mute ✅; DND saved **22:00–07:00** not **10PM–8AM** |

**Slice score:** 0 / 6 PASS · 6 FAIL · 0 HALLUCINATION · 0 BLOCKED

---

## Audit methodology & limitations

For each task:
1. Loaded prompt + placeholders from `AndroidLife_public_v2.json` + `public_vars.local.env`.
2. Checked `ahi` / `is_ask_user` / `interaction`, `ask_user_facts.json`, `multiturn_kb_public.json`.
3. Read `output.json`, `output.txt`, `meta.json`, `ask_user_metrics.jsonl`, `run_metrics.json`.
4. Parsed full `trajectories/*/trajectory.json` (all FastAgent thoughts + ToolExecutionEvents).
5. Cross-checked `ui_states/NNNN.json` text + **Read** multiple screenshots.
6. **No ADB** (dead battery). End-state judgments are artifact-only.

False-pass watches applied: starring vs un-favoriting; DND schedule times; claimed complete without end-state; ASK/MULTI with 0 ask_user.

---

## Per-task verdicts

### 1. `hard-contacts-gmail-026` — **FAIL** (false pass)

**GT:** Contact `[contact name]=Maa`. Read email+phone; confirm in Gmail; if confirmed **star**; reply `Name | Email | Phone | Confirmed?`.

**Artifacts:** `trajectories/20260914_151140_1909d8c7/` (13 steps). Agent `success=true`: `Maa | yuvraj.new@example.com | +91 81302 85662 | Confirmed`.

**What happened:**
- Opened Contacts → Maa details: email `yuvraj.new@example.com`, phone `+91 81302 85662` (ui/screenshots `0002`).
- Contact was **already starred** at open (`Remove from Favorites` / filled blue star).
- Gmail: typed email; ui `0008` shows it under **Recent Mail Searches** (agent’s own query) — weak “confirmation,” then treated as Confirmed.
- Step 11: clicked **"Remove from Favorites"** → ui `0011` / screenshot: star **hollow** = **unfavorited**.
- Step 12 thought wrongly: *"button now says Add to Favorites which means the contact is now starred"* — inverted semantics.
- Claimed complete with Confirmed + starred.

**Verdict:** **FAIL**. Required end-state is starred; agent **un-starred**. Classic starring/un-favoriting false pass. Not graded HALLUCINATION (not an HC control); it is a self-reported false success on UI semantics.

---

### 2. `hard-drive-notes-telegram-010` — **FAIL** (ASK USER gate)

**GT:** `is_ask_user=True`, `interaction=single`. Note deliberately omits spreadsheet name + Telegram recipient. Fact: *Message Yuvraj Airtel. The spreadsheet to chase is 'family_numbers.xlsx'.*

**Artifacts:** `20260914_095951_eb3ecf6c/` (35 steps). `output`: timeout 2400s. `ask_user_call_count=0`, empty `ask_user_metrics.jsonl`.

**What happened:**
- Opened Drive; repeatedly typed `"budget spreadsheet"`; never asked user.
- Looped Shared → open PDF (`Shared by tiwariacademy…` maths worksheet) → back (screenshot `0034` still on that PDF).
- Never opened Notes “Budget Deadline”, never Telegram, never `family_numbers.xlsx`.

**Verdict:** **FAIL**. MobileWorld ASK USER gate: **0 ask_user = fail**. Also incomplete / timeout.

---

### 3. `hard-google-sheets-amazon-shopping-074` — **FAIL**

**GT:** Spreadsheet `SPORTS_VIDEO_DATA`; find max-views video; Amazon search `[related product]=smartphone gimbal`; open top result; reply video name + product name only.

**Artifacts:** Primary graded traj `20260914_135405_5acf3203/` (60 steps, max). Earlier partial trajs exist (`104014…` 30 steps, empty stubs). `success=false`, max steps. ask_user N/A.

**What happened:**
- Opened Sheets; clicked `SPORTS_VIDEO_DATA.xlsx`.
- Mid-run scrolled to empty rows (screenshot `0003`); late screenshot `0058` **does** show data (e.g. Cricket V / 9.8M views, IPL 2025 / 1.25M highlighted) but agent kept claiming empty and clicking `spreadsheet_view` until step 60.
- Trajectory tool stats: `open_app`×1 (Sheets only). **Amazon never opened.** No `complete` with required reply.

**Verdict:** **FAIL**. No deliverable string; Amazon half missing; views not acted on despite visible cells.

---

### 4. `hard-swiggy-005` — **FAIL** (MULTI KB gate)

**GT:** `ahi=ASK USER`, `interaction=multi`. Date `14-Aug-2026`. KB target: reorder Downtown Delight Murgh Mughlai (bill ₹523); message “him” on Telegram with order total — details must be confirmed via ask_user / KB profile.

**Artifacts:** `20260914_142708_a39faae8/` (60 steps). Max steps. `ask_user_call_count=0`. `DEVICE_UNREACHABLE` flag present (preflight ADB fail note); run still produced full traj.

**What happened:**
- Only `open_app` Notes. Found bank note “Rs.523 to Swiggy (14/08)” and looped open/close that note (screenshot `0059`).
- Never opened Swiggy, never reorder, never Telegram, **never ask_user**.

**Verdict:** **FAIL**. Explicit MULTI KB gate: **0 ask_user = fail**. Also no reorder / message.

---

### 5. `hard-telegram-calendar-016` — **FAIL** (MULTI KB gate)

**GT:** `interaction=multi`. Confirm day/time/place/reminder **one at a time** with user, then calendar. KB: Telegram group **Forever 21** — Tue 22nd next month, 8 PM, Hill View Cafe And Restro, reminder day-before 8 PM.

**Artifacts:** `20260914_071737_f82c595c/` (48 steps). Timeout 2400s. `ask_user_call_count=0`.

**What happened:**
- `open_app` **Messages** (SMS), not Telegram.
- Searched “friends” / “party”; stuck in **Yuvraj Airtel** SMS thread (screenshot `0047`); swipe-looped.
- Never Forever 21, never ask_user for date/time/place/reminder, never Calendar event.

**Verdict:** **FAIL**. MULTI KB gate: **0 ask_user = fail**. Wrong app; no calendar write.

---

### 6. `hard-youtube-settings-052` — **FAIL** (DND schedule wrong)

**GT:** Mute `[notifying channel]=Tech Burner` YouTube notifications; set DND **10 PM – 8 AM**; reply channel name only.

**Artifacts:** `20260914_061849_b5f22004/` (24 steps). Agent `success=true`, reason `Tech Burner`.

**What happened (mute — PASS component):**
- YouTube → You → Tech Burner notification → selected **None**.
- ui `0007` / screenshot: Tech Burner *"Current setting is receive no notifications"* / bell-slash.

**What happened (DND — FAIL component):**
- Settings → Do Not Disturb → Schedules → Add schedule.
- Form ui/screenshot `0022`: From **22:00**, To **07:00 the next day**.
- Saved ui/screenshot `0023`: **Rule 1 · 22:00–07:00, Every day · On**.
- Agent thought: *"To: 07:00 … this is correct (8 AM)"* — **false** (07:00 = 7 AM, not 8 AM).
- Required window is **22:00–08:00**.

**Verdict:** **FAIL**. Mute correct; DND end time wrong. Claimed complete without correct end-state (watched false-pass: DND schedule times). Not HALLUCINATION (channel name reply matches mute; HC N/A) — still overall task fail.

---

## False-pass callouts (agent success=true)

| Task | Why agent looked green | Manual downgrade |
|------|------------------------|------------------|
| hard-contacts-gmail-026 | Formatted Confirmed reply | Un-favorited Maa |
| hard-youtube-settings-052 | Replied `Tech Burner` | DND 22:00–**07:00** ≠ 10PM–8AM |

---

## ask_user / KBIQ notes (this slice)

| Task | Required | ask_user calls | KBIQ implication |
|------|----------|----------------|------------------|
| drive-notes-telegram-010 | ≥1 (spreadsheet + recipient) | 0 | q≥1 → c/q = 0 |
| swiggy-005 | multi (KB-driven confirms) | 0 | 0 |
| telegram-calendar-016 | multi (day, time, place, reminder) | 0 | 0 |

No `kb_audit.json` written for full-run re-score (slice-only audit).

---

## Discrepancies vs agent output.json

| Task | output.json success | Manual |
|------|---------------------|--------|
| contacts-gmail-026 | true | FAIL |
| drive-notes-telegram-010 | false | FAIL (agree + ASK gate) |
| google-sheets-amazon-074 | false | FAIL (agree) |
| swiggy-005 | false | FAIL (agree + MULTI gate) |
| telegram-calendar-016 | false | FAIL (agree + MULTI gate) |
| youtube-settings-052 | true | FAIL |

---

*End of agent_day1_hard.md*
