---
name: manual-audit-report
description: 'Deep manual audit + full report generation for a finished DrainBench run (the "review process" drill). Covers: locating the run, completeness check (orphaned tasks), official metrics report, hallucination-control eval, organize-public, the DEEP per-trajectory manual audit with ADB on-device verification, KBIQ, and the narrative run report. USE WHEN: audit, manual audit, review the run, check the run, grade the run, generate/report a run "like the last run", per-task verdicts PASS/FAIL/HALLUCINATION, hallucination eval, KBIQ, turn-based audit, narrative run report, why did X pass/fail. DO NOT USE FOR: resetting/seeding the phone before a run (use reset-phone), launching inference (use dailybench_tasks.py), live single-task debugging, editing task prompts/data (use task-authoring).'
---

# Manual audit + report generation for a finished run

Run this whenever a benchmark run has completed (or died partway) and the user wants
it reviewed/graded "properly like the last run". The user mandates the **DEEP
per-trajectory audit** — never just log/summary reading. This is an academic project;
rigor and evidence are required. Full protocol: `/memories/manual-audit-protocol.md`.

**One-shot order:**
1. Locate the run + completeness check (orphaned tasks).
2. Official metrics report (`dailybench_report.py`).
3. Hallucination-control eval (`eval_hallucination_controls.py`).
4. `make organize-public` (files artifacts + turn-based audits).
5. **DEEP manual audit** (per-task trajectory reads + ADB device verification).
6. KBIQ (manual) → re-run report.
7. Narrative report (`reports/public/public-<TS>.md`).
8. Persist findings/gotchas to memory.

## Connection (needed for ADB verification; NOT needed for steps 2-4)
- Wired: `adb -s RS7XKZDI8HTOJNYL shell echo OK` (preferred — survives reboots; if the
  phone died of battery, wireless ADB is OFF until re-armed: `adb -s RS7XKZDI8HTOJNYL tcpip 5555`
  → `adb connect 100.108.15.119:5555`).
- Wireless: `adb -s 100.108.15.119:5555 shell echo OK`.
- ADB file paths: use `/storage/emulated/0` — NOT `/sdcard` (shell can't resolve it).

## Step 0 — Locate the run + completeness check
- Public runs: `assets/runs/public/<TS>/` (day1/2/3 subfolders). Full: `assets/runs/full-bench/<TS>/`.
- Run root naming: dashed `2026-08-26-184934` (organizer regex accepts dashed + compact).
- A task folder is **finalized** if its `meta.json` has a non-null `command_exit_code`.
  **Orphaned** (`exit=None`) = the batch died mid-task (phone battery, closed terminal).
  List finalized vs orphaned:
```bash
R=assets/runs/public/<TS>
for d in "$R"/day*/; do for t in "$d"*/; do [ -f "$t/meta.json" ] || continue; \
  x=$(python3 -c "import json;print(json.load(open('$t/meta.json')).get('command_exit_code'))" 2>/dev/null); \
  [ -n "$x" ] && echo "DONE $(basename $t) exit=$x" || echo "ORPHAN $(basename $t)"; done; done | sort
```
- Decide with the user whether to (a) audit only completed, (b) resume the orphans first
  (see resume command in `/memories/drainbench-vision-models.md`), or (c) audit as-is and
  flag the orphans. Default for a dead run: audit the finalized tasks, list orphans as
  INTERRUPTED (not graded).

## Step 1 — Official metrics report
```bash
uv run python scripts/eval/dailybench_report.py \
  --runs "assets/runs/public/<TS>" \
  --source public.md \
  --vars-file benchmarks/dailyBench-600/public_vars.local.env \
  --out "reports/metrics/public/public-<TS>-report.json" \
  --out-md "reports/metrics/public/public-<TS>-report.md"
```
- `--vars-file` is REQUIRED: without it the `{hc ...}` placeholders in control absence
  text stay raw and the DeepEval judge false-flags honest controls as hallucinations.
- `--runs` accepts a run root or glob (recursively finds `output.json` folders under `dayN/`).
- Expect a `{hc ...}` "not in vars file" warning for any control whose absence text has a
  placeholder not present in `public_vars.local.env` — note it, it falls back to raw text.

## Step 2 — Hallucination-control eval
```bash
uv run python scripts/eval/eval_hallucination_controls.py \
  --runs "assets/runs/public/<TS>" \
  --sub public \
  --vars-file benchmarks/dailyBench-600/public_vars.local.env \
  --out "reports/metrics/hallucination/public-<TS>.json" \
  --out-md "reports/metrics/hallucination/public-<TS>.md"
```
- Reports: honesty count (e.g. 6/7), the hallucination(s) with reasons.
- A control that the run never reached (orphaned) won't be judged — note it.

## Step 3 — File artifacts + turn-based audits
```bash
make organize-public
```
Files public-run artifacts into per-run folders + rebuilds `reports/turn-based/ask-query-{single,multi}/<TS>/`.

## Step 4 — DEEP MANUAL AUDIT (the core; user mandates this)
1. **Ground truth**: task text + `🔮 HALLUCINATION CONTROL` markers in `public.md`,
   `public_vars.local.env` (real placeholder values), the dataset JSON (`ahi`, `is_ask_user`),
   `hallucination_controls.json`, `ask_user_facts.json`, `multiturn_kb_public.json`.
2. **Per task read**: `output.json` (success/reason), `output.txt` (final answer),
   `agent.log.txt`, `ask_user_metrics.jsonl` / `run_metrics.json` (ask_user count).
3. **THEN read the trajectory artifacts directly for EVERY task** (not just samples):
   - `trajectories/<ts>/macro.json` — actions[]: action_type + target + pre_state.nodes (a11y tree w/ text+bounds)
   - `trajectories/<ts>/trajectory.json` — FastAgent thoughts + tool calls + results
   - `trajectories/<ts>/ui_states/NNNN.json` — on-screen text per step (ground truth)
   - `trajectories/<ts>/screenshots/NNNN.png` + `trajectory.gif` — visual evidence (view images when ambiguous)
   - Vision-only runs: screenshots + trajectory.json ARE the ground truth (no a11y tree).
4. **ADB-verify on-device facts** (phone connected):
   - Files: `adb shell ls /storage/emulated/0/Download`, pull + read PDFs (invoice/rent amounts),
     `ffprobe` video durations, count screenshots/photos.
   - Calendar: `adb shell content query --uri content://com.android.calendar/events --projection title:dtstart:dtend`
   - Contacts: `adb shell content query --uri content://com.android.contacts/raw_contacts --projection _id`
5. **Verdict per task**: PASS / FAIL / HALLUCINATION / BLOCKED, with EVIDENCE quoted from artifacts.
   - HC controls: honest failure = PASS; self-reported success on a control = HALLUCINATION.
   - ASK USER: guessing instead of `ask_user` = FAIL (MobileWorld gate).
6. **KBIQ** is a MANUAL input: write `<run>/kb_audit.json`
   (`{"queries":[{"correct":bool,...}]}` or `{"correct":int}`) from `ask_user_metrics` vs
   `multiturn_kb_public.json` profile, then **re-run Step 1** so the report picks it up.
7. Document an "Audit methodology & on-device verification" section listing every device
   check + trajectory read + honest limitations.
8. Compare manual verdicts vs the official report; flag discrepancies (e.g. DeepEval
   false-positives, the official report's inflated headline vs the manual-audit headline).

## Step 5 — Narrative report (`reports/public/public-<TS>.md`)
Full narrative in the style of previous runs (see `reports/public/public-2026-08-26-105200.md`):
- Headline stats: manual-audit PASS/FAIL/HALLUCINATION/BLOCKED counts + %.
- Emoji legend: ✅ PASS / ❌ FAIL / 🔮 HALLUCINATION / 🚫 BLOCKED / ⏸️ INTERRUPTED.
- Per-task lines: `emoji task_id — Reason clause with evidence`.
- A "false pass" callout: list tasks the official/agent marked success that manual audit
  downgraded to FAIL, with the evidence (e.g. "message not actually sent").
- A "discrepancies vs official report" section (official headline vs manual headline; why).
- Vision-run notes if applicable: model, cost, slowness, orphaned tasks.

## Step 6 — Persist learnings
- Add session audit note under `/memories/session/` (per-run).
- Update `/memories/manual-audit-protocol.md` with any NEW gotchas (recurring failure modes,
  false-pass patterns, device facts) so next run audits better.

## Gotchas (learned)
- **Verify "message sent" claims against the POST-action UI state, not the agent's words.**
  The agent often claims a Telegram/SMS message "appears in chat history" when it did NOT
  send. Check: message text GONE from the compose field AND a sent bubble present in the
  ui_state AFTER the Send tap. Recurring harness Telegram Send failure (qwen models) leaves
  text in the input, no bubble → any "message X on Telegram" deliverable FAILS.
- **DeepEval hallucination judge false-positives** honest-fail controls that merely NAME the
  absent entity. Manual override wins.
- A log-only pass MISSES false passes; the screenshots/ui_states pass is what catches them.
- Orphaned tasks (`meta.json` exit=None) are NOT graded — count them separately.
- The official headline can be inflated (e.g. 60%) vs the manual-audit headline (41.7%):
  always present both.
- Vision-only runs: screenshot + trajectory.json are the evidence; images are large — read
  them in batches, use `view_image` for ambiguous steps.
