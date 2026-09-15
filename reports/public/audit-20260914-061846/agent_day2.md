# AndroidLife Manual Audit — day2 (`20260914-061846`)

**Model:** Qwen3.5-4B  
**Run root:** `/Users/yuvrajsingh1/Data/DrainBench300/assets/runs/public/20260914-061846/day2/`  
**Auditor note:** Phone battery DEAD — **no ADB on-device verification**. Evidence = `meta` / `output` / `run_metrics` / `ask_user_metrics` + full `trajectory.json` + multiple screenshots (Read) + `ui_states`.  
**Do not grade** `_stale_resume_*` copies as primary (noted only for orphan narrative where the live folder was overwritten by a resume).

**Ground truth sources:** `AndroidLife_public_v2.json`, `ask_user_facts_public.json`, `multiturn_kb_public.json`, `public_vars.local.env`, `public.md`.

---

## Headline

| Bucket | Count |
|--------|------:|
| PASS | 0 |
| FAIL | 5 |
| HALLUCINATION | 0 |
| INTERRUPTED (orphans) | 2 |
| Graded finalized | 5 |

Manual graded rate: **0/5 PASS (0%)**.

---

## Finalized grades

| Task | AHI | Agent `success` | Manual | One-line reason |
|------|-----|-----------------|--------|-----------------|
| `hard-chrome-telegram-notes-008` | ASK USER SINGLE | false (timeout 2400s) | **FAIL** | Asked correctly (wireless earbuds); compared Amazon/Flipkart prices but never opened Telegram / never sent cheaper link; stuck looping on Flipkart PDP |
| `hard-gmail-calendar-003` | MULTI KB | false (timeout 2400s) | **FAIL** | `ask_user_call_count=0` — guessed instead of multi-ask; never found Scapia BBI→DEL; opened wrong X email; never forward / Calendar |
| `medium-calculator-002` | — | false (max 60 steps) | **FAIL** | Read Monthly Budget correctly; botched Calculator entry; never finished sum / reply-only-total; never messaged Yuvraj Airtel |
| `medium-chrome-003` | — | false (timeout 2400s) | **FAIL** | Saw earbuds in Chrome history but looped Chrome↔WhatsApp; wrong channel (WhatsApp not Messages); no links sent |
| `medium-files-009` | — | false (malformed tool-call ×3) | **FAIL** | Found ~140 screenshots; did not delete oldest 10 or report new folder size; died on malformed `type` markup |

---

## Orphans (not graded PASS/FAIL)

| Task | Verdict | Where it died |
|------|---------|---------------|
| `hard-bookmyshow-005` | **INTERRUPTED** | `meta.command_exit_code=null`. Live `day2/` folder is a thin resume (~2 shots, open BookMyShow then stalled). Prior interrupted attempt (artifacts under `_stale_resume_20260915-033445/`, **not graded as primary**) reached INOX search → DN Regalia → *Dahaan* 09:00 AM seat map, then `device offline` on a click; no Telegram plan message |
| `easy-settings-014` | **INTERRUPTED** | Only `DEVICE_UNREACHABLE` + `meta` (`exit=null`). Preflight ADB failed: `device offline`. No trajectory / screenshots |

---

## Per-task deep evidence

### 1. `hard-chrome-telegram-notes-008` — FAIL

**Prompt (resolved):** Compare wireless-earbuds prices on `amazon.in` vs `flipkart.com`; if difference > $10, Telegram cheaper link to `Yuvraj Airtel`; else note + star cheaper listing. Item must be asked (`ask_user_facts`: “The item is wireless earbuds.”).

| Artifact | Evidence |
|----------|----------|
| `ask_user_metrics.jsonl` | 1 call: “What specific item…?” → **“The item is wireless earbuds.”** (`ask_user_call_count=1`) |
| Trajectory | `ask_user` → Chrome → Amazon search (app) prices ₹1,499 / ₹2,299 → Flipkart search **“wireless earbuds under 200”** → PDP iCallMart ₹198 → endless click loop on product title; **no `open_app Telegram`**, no Send |
| Screenshots | `0010.png` Amazon wireless earbuds; `0016.png` Flipkart query; `0028.png` Flipkart PDP ₹198 still on product (end state) |
| `ui_states/0029` | Still Flipkart PDP (`Go to cart` / `Buy now` ₹198) |
| `output.json` | `success: false` — timeout 2400s |

**Verdict FAIL:** ASK USER gate passed, but deliverable (Telegram cheaper link given Δ ≫ $10) never executed. No Send to verify.

---

### 2. `hard-gmail-calendar-003` — FAIL (MULTI KB)

**KB (`multiturn_kb_public.json`):** BBI→DEL Scapia PNR X84NVI, depart 12:05 Oct 16 2026, Terminal 1; account `rajceo2031@gmail.com`; friend `yuvraj.mist@gmail.com`.  
**Intended asks:** which trip / which Gmail account / friend’s email.

| Artifact | Evidence |
|----------|----------|
| `run_metrics` / `ask_user_metrics` | **`ask_user_call_count: 0`**, empty jsonl |
| Trajectory | Immediate `open_app Gmail` → type `flight confirmation` → opens X/Kapil Sibal “Flying…” email → long click/back loop on thread list; never Calendar; never forward |
| Screenshots | `0003.png` search “flight confirmation”; `0006.png` wrong Twitter email; `0055.png` still non-flight results / garbled search |
| `output.json` | timeout 2400s, `success: false` |

**Verdict FAIL:** MobileWorld multi-ask gate failed (guessed). Correct flight email never opened; no forward; no 3h-before Calendar reminder. (Not HALLUCINATION — agent did not claim success.)

---

### 3. `medium-calculator-002` — FAIL

**Resolved:** Obsidian note `Monthly Budget`; sum 5 expenses; compare to income in Calculator; reply **only** final total; message `Yuvraj Airtel` “late for dinner”.

| Artifact | Evidence |
|----------|----------|
| `ui_states/0001` + `screenshots/0001.png` | Note visible: income ₹25,000; Rent 8k + Food 6k + Transport 2.5k + Shopping 2k + Bills 1.5k = **₹20,000** |
| Trajectory | Obsidian → Calculator only (`open_app` never Messages). Digits mangled (`8000+6000+2005` etc.) |
| Screenshots | `0015.png` shows `8,000+6,000` → 14,000; `0059.png` end: `8,000+6,000+2,005` → 16,005 (not 20,000) |
| `output` | Reached max 60 steps, `success: false` |
| UI scan | **0** ui_states mention Messages / “late for dinner” |

**Verdict FAIL:** Partial Obsidian read OK; Calculator incomplete/wrong; no SMS; no reply-only total.

---

### 4. `medium-chrome-003` — FAIL

**Resolved:** From Chrome history, send earbuds shopping links to `Yuvraj Airtel` via **Messages** (apps: Chrome + Messages).

| Artifact | Evidence |
|----------|----------|
| Trajectory | Chrome History ↔ home ↔ **WhatsApp** contact picker loop (`open_app Chrome` ×9); never Messages; never `type` of URLs into compose |
| Screenshots | `0005.png` Social folder → WhatsApp; `0010.png` / `0035.png` WhatsApp “Select contact”; `0020.png` Flipkart earbuds page + Chrome menu (History visible) |
| `output` | timeout 2400s |

**Verdict FAIL:** Wrong messenger; no message sent (no compose clear / sent bubble). History had relevant earbuds URLs but unused for delivery.

---

### 5. `medium-files-009` — FAIL

**Prompt:** Find screenshots across folders, **delete oldest 10**, check folder’s **new total size**.

| Artifact | Evidence |
|----------|----------|
| Trajectory / shots | My Files search `screenshot` → **“140 items in total”** (`0006.png`); some mid-list taps; left to home (`0010.png`); later Files-by-Google with **invoice** recent (`0018.png`) |
| End | Three consecutive malformed tool calls: `<parameter name="text">screenshot", "clear": true}` → harness stop |
| `output.json` | malformed tool-call markup ×3; `success: false` |

**Verdict FAIL:** Discovery partial; delete oldest-10 + size check not done. No ADB to confirm deletions (phone dead).

---

### Orphan A. `hard-bookmyshow-005` — INTERRUPTED

- **Live primary folder:** resume traj `20260915_033458_49faf62c` — ~2 screenshots, opened BookMyShow, `exit=null`, no `output.json`.
- **Prior interrupted attempt** (sidelined to `_stale_resume_20260915-033445/…/20260915_023750_0999f66d`, not graded): BookMyShow → search INOX → DN Regalia Mall → *Dahaan: The Evil Within* 09:00 AM seat layout (`0059.png`); last tool `click` → **Failed: device offline**. Never Telegram’d plan; never final cinema/movie/showtime reply.

### Orphan B. `easy-settings-014` — INTERRUPTED

- `DEVICE_UNREACHABLE`: `adb … dumpsys battery` → `device offline`.
- No trajectories; task never started UI work.

---

## Audit methodology & limitations

1. Ground truth from public dataset JSON + ask_user facts + multiturn KB + `public_vars.local.env`.
2. Per finalized task: `meta.json`, `output.json`/`output.txt`, `run_metrics.json`, `ask_user_metrics.jsonl`, full `trajectory.json` tool timeline + thoughts, sampled `ui_states`, **≥6 screenshots via Read** per finalized task.
3. **ADB skipped** — battery dead / device offline. Cannot verify Calendar events, Messages DB, file deletes, or Telegram send state on device.
4. Telegram/Messages “sent” claims would require post-Send ui_state (compose empty + bubble); none of these tasks reached a credible Send.
5. `_stale_resume_*` used only to narrate orphan bookmyshow progress; not used as a graded primary run.

---

## Discrepancies vs agent self-report

All five finalized tasks already have `success: false` in `output.json` — manual audit **agrees** they failed; no false-PASS downgrades needed. Primary value-add: documenting *why* (ask_user miss on MULTI KB; wrong app on chrome-003; Telegram never opened on chrome-tg; calc digit thrash; files malformed stop) and classifying orphans as INTERRUPTED.
