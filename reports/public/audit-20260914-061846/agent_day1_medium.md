# Day1 Medium Manual Audit — `20260914-061846`

**Run root:** `assets/runs/public/20260914-061846/day1/`  
**Model (meta):** Qwen3.5-4B  
**ADB:** skipped (phone battery dead) — evidence from trajectories / screenshots / ui_states / output / meta / run_metrics only  
**Auditor:** deep per-task trajectory + multi-screenshot + ui_state pass  
**Folders audited:** medium-contacts-009, medium-files-pdf-001, medium-gallery-007, medium-google-drive-001, medium-google-maps-002

| Task | Verdict | Evidence |
|------|---------|----------|
| medium-contacts-009 | FAIL | Goal: count contacts missing phone numbers + call `Yuvraj Airtel`; reply with count only. `meta` exit=1, `output.json` success=false (2400s timeout). Traj: opened Contacts, inspected several details with phones (e.g. **ui_states/0003** Yuvraj Singh `+91 93546 72378`; **0005** Maa; **0007**/`screenshots/0007.png` Trrebo `+91 91240 90691`; Anannya/Bhartiya/Priyanshu/tilak similarly). Never opened contact `A` or Abhipsa; never dialed `Yuvraj Airtel` (no Phone/Calling UI). End-state **screenshots/0050.png** still on Contacts list. Looped account↔list (~51 steps / 51 screens). No count emitted. |
| medium-files-pdf-001 | PASS | Goal: open `Invoice INV-2026-071.pdf`, read amount due, check due date; reply amount only. Vars match. Traj: Files → search → open invoice (**screenshots/0002.png** lists `Invoice INV-2026-071.pdf`). **screenshots/0003.png**/`0004.png` + **ui_states/0003.json** PDF text: `Amount Due: Rs. 1,240.00`, `Due Date: 2026-07-25`. Agent notes current date Sep 14 2026 (due passed). `output.txt`=`1240`, success=true. Amount matches invoice screenshot. |
| medium-gallery-007 | FAIL | Goal: copy Favourites photos for Pancakes / Pizza / Veggie Bowl into Obsidian `Food Favourites`; reply count only. **Favourites check:** **ui_states/0003**/`0007` + **screenshots/0003.png**/`0007.png` show **2** Favourites only — Pizza collage (`0004.png` caption `Pizza`, starred) and Pancakes (`0006.png` caption `Pancakes`, starred). **No Veggie Bowl** in Favourites a11y or screenshots. Agent never opened Obsidian / never copied either available photo. `complete(success=false)` → `0 photos added…`; honest but incomplete → FAIL. |
| medium-google-drive-001 | FAIL | Goal: check Drive storage, then find largest file in main Drive folder (name/type/size/modified). `meta` exit=1, timeout 2400s, success=false, no deliverable. Storage OK: **screenshots/0002.png** / **ui_states/0002** `4 GB of 15 GB used`; **0004.png**/ui `3.8 GB of 15 GB` (Gmail 3.27 GB / Drive 310.96 MB / Photos 228.02 MB). Partial file info: e.g. yolov8 notebook **2.4 MB** (ui `0010`), Untitled `0.3 KB`, Untitled17 `72.9 KB`, How to get started PDF `1.4 MB`. Stuck looping on `5.jpg` More-actions without View information (**screenshots/0042.png** end-ish). Never finished largest-file answer. |
| medium-google-maps-002 | FAIL | Goal: compare **driving + transit + walking** to `Bhubaneswar Airport`, pick fastest, save ETA+distance note. **Mode check:** **ui_states/0002.json** shows Driving `27 min` (13 km), Two-wheeler `26 min`, **`Public transport mode: not available`**, Walking `2 hr 48`. Agent never selected a transit ETA; substituted **two-wheeler** for transit (explicitly disallowed). Note **was** saved: **screenshots/0005.png** body `Travel to Bhubaneswar Airport: Two-wheeler (fastest) - 26 min, 13 km`; list **0012.png**; home widget **0013.png**. Agent `complete(success=true)` claiming all three modes compared — false pass vs required modes. Among required modes with transit N/A, driving (27 min) should win over walking; two-wheeler is out of scope. |

## Summary

| Verdict | Count |
|---------|-------|
| PASS | 1 |
| FAIL | 4 |
| HALLUCINATION | 0 |

- **PASS:** files-pdf-001  
- **FAIL:** contacts-009, gallery-007, google-drive-001, google-maps-002  
- **HALLUCINATION:** (none in this batch)

## Special checks

| Task | Check | Result |
|------|-------|--------|
| files-pdf-001 | Amount due matches invoice screenshot | **PASS** — `Rs. 1,240.00` on PDF (`0003`/`0004` + ui PDF text) ↔ output `1240` |
| maps-002 | driving + transit + walking (not two-wheeler as transit); note saved | **Modes FAIL** (two-wheeler substituted; transit = N/A, never used). **Note saved** (yes — Two-wheeler note in Notes list/widget). Overall **FAIL**. |
| gallery-007 | Required photos in Favourites | Pizza ✓, Pancakes ✓, **Veggie Bowl ✗** (Favourites has only 2 items). No Obsidian copies. **FAIL**. |

## Per-task artifact pointers

| Task | Trajectory | Screens / UI |
|------|------------|--------------|
| contacts-009 | `…/20260914_063720_cccd113b/` | 51 png / 51 ui; end `0050` |
| files-pdf-001 | `…/20260914_091649_dd2050bb/` | 5 (+gif) / 5 ui; invoice `0003`–`0004` |
| gallery-007 | `…/20260914_083631_8d2996ce/` | 9 (+gif) / 9 ui; favs `0003`–`0007` |
| google-drive-001 | `…/20260914_091927_b219c02c/` | 43 / 43 ui; storage `0002`/`0004`; end `0042` |
| google-maps-002 | `…/20260914_062939_36642485/` | 14 (+gif) / 14 ui; modes `0001`–`0002`; note `0005`/`0012`/`0013` |

## Limitations

- No ADB on-device verification (dead battery).  
- Contacts/Drive timeouts: graded on incomplete trajectory evidence, not a final agent answer.  
- Gallery Favourites: collage renders as a 2×2 pizza grid visually but is one Favourites “Creation” item in a11y (plus Pancakes) — count = 2 Favourites entries.  
- Maps: transit genuinely unavailable in UI; still fails because two-wheeler was used as a transit substitute and agent claimed success on the required three-mode comparison.
