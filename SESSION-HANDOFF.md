# Session handoff — DrainBench300 (read this first in a new chat)

**Written:** 2026-09-25 ~12:57 IST  
**Repo:** `/Users/yuvrajsingh1/Data/DrainBench300`  
**Purpose:** Untracked continuity doc so a new agent session can resume without rediscovering context.  
**Do not commit this file** unless the owner asks.

**Durable per-row meet ledger (also untracked / outside git):**  
`~/Library/Application Support/Cursor/AgentStores/cursor_agent_stores/f316233a-6e29-464f-be27-6ab54c462457/files/meet_rerun_ledger.md`  
(Previously lived in `/tmp/meet_rerun_ledger.md` and got wiped — do not put state only in `/tmp`.)

---

## 1. What we are trying to do (objective)

**Benchmark:** AndroidLife public 60-task sample; leaderboard has **13 model rows**.

**Redo queue** (`redo.md`): six tasks were broken at the *benchmark* level (seed / vars / leaks), so recorded scores are not model signal. Each must be re-run for all 13 rows, hand-reviewed, then **merged in place** into the canonical run roots — **artifacts + reports/metrics/leaderboard** — and **both** must be **uploaded to HuggingFace** (`YuvrajSingh9886/androidlife-public`). No new run roots on HF. No fake `review.json` on HF.

| # | Task | Status |
|---|---|---|
| 1 | `medium__google-maps__002` | ✅ Done (published) |
| 2 | `hard__google-meet-files__070` | 🔄 **IN PROGRESS** — rows 1–7 reviewed; **8–13 left** |
| 3 | `hard__bookmyshow__005` | ✅ Done |
| 4 | `hard__drive-notes-telegram__010` | ✅ Done |
| 5 | `easy__google-slides__001` | ✅ Done |
| 6 | `easy__calendar__002` | ✅ Done |

**Immediate objective:** finish §2 (`hard__google-meet-files__070`) for all 13 rows with the manual-review pipeline, then publish.

---

## 2. Results so far — meet re-run (§2)

**Task:** open Meet → find next scheduled `Weekly Sync` → note title/time/attendees → open Files → open agenda `Weekly Agenda` → reply with **only** meeting title + agenda file name.  
**Ground truth:** `weekly meeting = Weekly Sync`, `agenda file = Weekly Agenda` (`/sdcard/Download/Weekly Agenda.txt`).  
**No `answer_check`** — `success: true` alone proves nothing; verdicts come from trajectories.

### Owner decisions (binding)

1. **Guests seeded once via Calendar GUI** (2026-09-24): `rajceo2031@gmail.com`, `ranirajesh786@gmail.com`. Gate: `meet_expected_attendees` in `reset_phone.py` / `verify_meet_agenda`.
2. **Meet never shows a scheduled attendee count** (measured). Only Calendar does. `No one is in the call yet` = live participants.
3. **Keep the “number of attendees” clause in the prompt.** Green-room loops = **genuine model failure** (how the model handles an unanswerable sub-goal). Do **not** amend the prompt mid-batch.
4. **No `review.json` on HF** for these reviews. Hand-review only; `REVIEW_GATE=0` on the batch script.
5. **Battery for charge-night re-runs = N/A**, not a median proxy (see §5).

### Row table (authoritative)

| row | model | mode | run root | steps | verdict |
|---|---|---|---|---|---|
| 1 | qwen3.8-27b | text | `20260924-102208` | 13 | **PASS** |
| 2 | kimi-k2.6 | text | `20260924-103804` | 17 | **PASS** (supersedes old 60-cap FAIL `20260924-065148`) |
| 3 | gemini-3.1-flash-lite | text | `20260924-105601` | 5 | **PASS** (batched click→home→complete; prove open via `macro.json` final `pre_state`) |
| 4 | seed-2.0-lite | text | `20260924-111349` | 12 | **PASS** — reply label-wrapped (`Meeting title: …`) |
| 5 | qwen3.8-27b | vision | `20260924-113115` | 9 | **PASS** |
| 6 | seed-2.0-lite | vision | `20260924-114614` | 7 | **PASS** — same label-wrap habit |
| 7 | gpt-5.6-luna | text | `20260924-132821` | 60 | **FAIL** — task done by ~step 20; then 40 bare `Weekly Sync — Weekly Agenda` with **no `complete` tool call** |
| ~~7-void~~ | | | `20260924-120024.aborted-incomplete` | | VOID (adb dropped; no device tools) |
| ~~8-void~~ | | | `20260924-164311.aborted-incomplete` | | VOID (empty root; phone unreachable) |
| **8–13** | | | | | **NOT RUN YET** |

**Corpus note so far:** no row has hit the attendee thrash trap post-seed. Failures seen: luna’s fail-to-terminate (row 7), and (historical) kimi’s 56-swipe loop pre-rerun.

**Label-wrap caveat:** rows 4 & 6 (`seed-2.0-lite`). Graded PASS; if owner enforces “no other text” literally, only those two fail.

---

## 3. What’s left (exact next steps)

### A. Before any meet row (today is 2026-09-25)

Seed stamp is still **`seeded_on: 2026-09-24`** (`.seed_state.json`) → **stale**.

```bash
cd /Users/yuvrajsingh1/Data/DrainBench300
adb connect 100.108.15.119:5555
# Phoenix must be up (prefer detached start_new_session so it survives the shell):
#   python3 -c 'import subprocess; subprocess.Popen(["uv","run","python","scripts/run/start_phoenix.py","--public","--no-open"], start_new_session=True, ...)'
uv run python scripts/seeding/reset_phone.py --serial 100.108.15.119:5555 --profile public_v2 --apply
uv run python scripts/seeding/reset_phone.py --serial 100.108.15.119:5555 --profile public_v2 --verify-only
# Expect RESULT PASS including: meet guests present
```

### B. Resume meet batch at row 8

```bash
LOCAL_AUTOSERVE=1 REVIEW_GATE=0 bash scripts/run/rerun_task_rows.sh hard__google-meet-files__070 rerun-meet 8
# then hand-review; then 9, 10, 11, 12, 13 one at a time
```

Rows:  
8 `gpt-5.6-luna` VISION · 9 `Qwen3.5-4B` TEXT local · 10 `gemma-4-E2B-it` TEXT local ·  
11 `kimi-k2.6` VISION · 12 `gemma-4-E2B-it` VISION local · 13 `Bonsai-2-27B` TEXT local  

`LOCAL_AUTOSERVE=1` swaps llama packs. At last check **8088 was serving `Bonsai-2-27B`** (fine for row 13; autoserve handles 9/10/12).

### C. After all 13 reviewed — **merge in place + upload to HF** (mandatory)

Same rule as every other redo task (Maps, BookMyShow, Notes, Slides, Calendar). **Never** publish a re-run as its own run root on HF.

**1. Merge artifacts in place (local + HF)**  
- Each row’s re-run dir under `assets/runs/public/20260924-…/day3/hard-google-meet-files-070/` **replaces** that task’s directory **inside the canonical day-3 root** for that leaderboard row (the original `public-YYYY…` run root).  
- Root identity stays the same (e.g. qwen TEXT stays `2026-08-28-002424`).  
- Then **upload those replaced task dirs to HuggingFace** dataset `YuvrajSingh9886/androidlife-public` under `runs/<canonical-root>/…` so HF is byte-updated (viewer / trajectories / metrics read HF).  
- Working re-run roots (`20260924-*`) are staging only — not published as new roots.

**2. Merge reports / metrics / leaderboard in place**  
- Write the new verdict + `↻` note into that row’s existing `reports/public/public-….md` (exact row for `hard__google-meet-files__070`).  
- Recompute that report’s headline counts / aggregates from the new verdict (exact arithmetic, not a full corpus regen).  
- Update `reports/metrics/public/*-report.json` (+ render `.md` if that’s the row’s convention).  
- Update `androidlife-website/assets/js/leaderboard.js` for any score/bucket/cost fields that moved.  
- Run `verify_leaderboard.py` → 0 mismatches.

**3. Upload reports to HF too**  
- `uv run python scripts/tools/sync_reports_hf.py --push` so `reports/` on HF matches local.  
- Artifacts and reports are **both** required on HF; local-only is incomplete.

**4. Docs**  
- Update `redo.md` §2 + owed table (still wrongly says BLOCKED on recurring DAILY seed — guests+gate already exist). Mark ✅ when published.

**5. Website (if trajectories changed)**  
- Rebuild public traj index against HF + media gate so GIFs/step viewer aren’t stale.

### D. Uncommitted work to commit when owner asks

**Main repo (`master`):**
- `redo.md` (§8 battery N/A rewrite)
- 13× `reports/public/public-*.md` (battery aggregates + N/A notes)

**Website nested repo (`androidlife-website` `main`):**
- `assets/js/leaderboard.js` (`batteryDrain` reverted to pre-median sums)

**Already on HF (no local commit required for these):**
- 13 report markdowns synced  
- 42 `run_metrics.json` median fills restored to `0`

**Leave untracked:** this file, `website/marketing/`, `website/pages/` (other session’s marketing work).

---

## 4. Validation pipeline (do this every meet row)

1. One row per `rerun_task_rows.sh` invocation; **`REVIEW_GATE=0`**; **`LOCAL_AUTOSERVE=1`**.
2. **Hand-review from that row’s own artifacts** before launching the next. Criteria:
   - Meet: `Weekly Sync` from Scheduled (no `Product Demo`)
   - Files: doc **opened** — need `view_pager` + `file_path` …/`Download/Weekly Agenda.txt` (prefer `macro.json` `pre_state` of the action *after* the tap if ui_states miss it)
   - Reply: title + agenda name; under 60 steps; terminated with `complete` (row 7 is the counterexample)
3. Record in the durable ledger (path above). **Never write `review.json` for publication.**
4. Between rows: leak cleanup is on by default in the script (Telegram/Notes).

---

## 5. Battery policy (settled 2026-09-25)

Charge-night re-runs recorded `battery_level_delta_pct = 0`. A **same-category median proxy was tried and withdrawn**.

**Current rule:**
- Report those cells as **N/A** (not proxied).
- Artifacts keep honest **0**.
- Run aggregate / leaderboard `batteryDrain` = sum of **untouched tasks only** (pre-median “published” column: −69/−90/−21/−29/−79/−51/−85/−88/−96/−81/−94/−93/−92).
- **Thermals never touched.**

`verify_leaderboard.py`: 0 mismatches after the leaderboard edit (warnings on steps/UIQ axes are pre-existing).

---

## 6. Dos and don’ts

### Do

- Read `redo.md` §2 + this file + the durable meet ledger before acting.
- `--apply` on the **run calendar day**; trust the seed stamp gate.
- One meet row at a time; hand-review before the next.
- Merge re-runs **in place** into the canonical root, then upload **artifacts and `reports/`** to HF — local-only is incomplete.
- Prefer detached Phoenix (`start_new_session=True`) so it doesn’t die with the shell.
- Flag empty/incomplete roots as `.aborted-*` (never score them).
- Restore stripped working-tree files from `HEAD` if another session deletes gate/reset code again.
- Keep new commits free of `Co-authored-by: Cursor` trailers.
- Only commit / push when the owner asks.

### Don’t

- Don’t amend the meet prompt’s attendee clause mid-batch.
- Don’t publish a re-run as its own HF/local run root (always in-place replace inside the canonical root).
- Don’t leave publication local-only — HF must get the replaced task dirs **and** updated `reports/`.
- Don’t publish `review.json` / debug sidecars to HF for these hand reviews.
- Don’t re-introduce median battery fills.
- Don’t touch thermals when fixing battery.
- Don’t batch all 13 meet rows without review.
- Don’t treat `success: true` as PASS without trajectory proof of the file preview.
- Don’t put critical state only in `/tmp`.
- Don’t force-push / skip hooks / amend others’ commits.
- Don’t confuse **local** row-13 maps (`-6`, original) with **HF** in-place re-run (on-charge → 0).

---

## 7. Infra cheat sheet

| Item | Value |
|---|---|
| Phone serial | `100.108.15.119:5555` (Tailscale wireless adb) |
| Seed profile | `public_v2` |
| Seed stamp file | `.seed_state.json` (must be **today**) |
| Phoenix | `http://localhost:6006` |
| Local llama | `http://127.0.0.1:8088` (`serve_gguf.sh` presets) |
| Dataset | `benchmarks/androidlife-530/AndroidLife_public_v2.json` |
| Rerun driver | `scripts/run/rerun_task_rows.sh` |
| Seed/reset | `scripts/seeding/reset_phone.py` |
| HF dataset | `YuvrajSingh9886/androidlife-public` |
| Report sync | `uv run python scripts/tools/sync_reports_hf.py --push` |
| Leaderboard check | `uv run python scripts/tools/verify_leaderboard.py` |

Meet guests (gate): `rajceo2031@gmail.com`, `ranirajesh786@gmail.com` on the 10:00 `Weekly Sync` (GUI-only; `--apply` date-shifts in place).

---

## 8. Other session interference (2026-09-25 ~12:06)

Uncommitted WT deletions (~388 lines) stripped seed-gate / pre-app-reset / serve_gguf notes / checklist prose from:

`docs/pre-run-checklist.md`, `scripts/llm/README.md`, `scripts/llm/serve_gguf.sh`,  
`src/androidlife/{adb,cli,task_batch}.py`, `tests/test_task_batch.py`

**Restored from HEAD** in the previous session. Meet attendee gate in `reset_phone.py` was never removed from commits. If WT looks gutted again, `git checkout HEAD -- <those files>` — do not assume HEAD is wrong.

Also present untracked (leave alone unless asked): `website/marketing/`, `website/pages/`.

---

## 9. Already done outside the meet batch (context)

- Website trajectory GIFs / `index.json` rebuild against HF + media gate (`verify_traj_media.py`); empty/missing GIF backfill.
- Maps / BookMyShow / Notes / Slides / Calendar redo sections published in place.
- Battery median fill applied then **withdrawn** in favor of N/A (reports + leaderboard local uncommitted; HF artifacts+reports updated).

## 9a. Battery commits landed + local re-run roots pruned (2026-09-25 ~20:00)

**Committed (not pushed), trailer-clean** — a Cursor co-author line was auto-injected on both
and was stripped with `--amend`:

- main repo `master` **`634d7db`** — `redo.md` §8 + the 13 `reports/public/public-*.md`
- `androidlife-website` `main` **`53260aa`** — `assets/js/leaderboard.js` `batteryDrain`
  back to the untouched-tasks-only sums (−69/−90/−21/−29/−79/−51/−85/−88/−96/−81/−94/−93/−92)

`verify_leaderboard.py`: 13 rows / 300 fields → **0 mismatches** (7 pre-existing
steps/UIQ warnings). Nothing pushed; HF untouched by these commits.

**Local re-run roots deleted — 55 of them, `assets/runs/public` 2.4 GB → 769 MB.**
Published runs upload only a single *task directory* into a canonical root, so the local
working roots were pure duplicates once merged. Verified **before** deleting, by diffing
`output.json` against each canonical HF row:

```
§1 maps 13/13 · §3 bookmyshow 13/13 · §4 drive-notes 13/13 · §5 slides 7/7 · §6 calendar 9/9
= 55 roots, all byte-identical on the Hub, 0 differing, 0 missing
```

(Full file-set comparison too: `local_only=[]` for every sampled row, so **no junk** is in the
uploads. The only non-artifact files — `batch-*.log`, `LATEST_*_RUN.txt`, `.active_*`,
`phoenix.log`, `DEVICE_UNREACHABLE` — sit at the run-root level, which is never uploaded.
`delivery.json` is a genuine artifact for tasks with a delivery check.)

**Deliberately KEPT:** the 12 meet roots (§2 is not published), the canonical root
`20260920-044846` (row 13 — its local maps data still differs from HF: original `-6` vs re-run
`0`), `assets/runs/_rerun_backups/` (45 MB, displaced originals), and the six
`20260923-*.aborted-seedgate` diagnostics (72 KB, they are the evidence for the Maps rows 8-13
abort). **Do not re-create a redo root and assume it is the only copy** — if a section is ever
re-run, its new root is the source until it is merged into the canonical root on HF.

> Quick check if you ever suspect the prune was wrong: the artifacts also live on HF at
> `runs/<canonical_root>/dayN/<task-slug>/`, so a deleted local root is recoverable from the Hub.

---

## 10. First message checklist for the new session

1. Read this file end-to-end.  
2. `adb devices` + Phoenix + `.seed_state.json` date.  
3. If stamp ≠ today → `--apply` then `--verify-only`.  
4. Confirm owner wants to **continue meet at row 8** (and whether to **commit** battery/leaderboard diffs first).  
5. Launch **only row 8**, hand-review, update durable ledger, then proceed 9→13.  
6. Do not “helpfully” rewrite the prompt or re-median battery.

**Left off:** battery N/A fix completed (HF live; local commits pending). Meet **paused before row 8** pending `--apply` for 2026-09-25 and owner go-ahead.
