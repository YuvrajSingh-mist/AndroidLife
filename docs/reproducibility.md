# Reproducibility (public 60-task)

AndroidLife is a **real-device** benchmark. You can re-run the same public protocol —
same tasks, same reset/seed pipeline, same grading — but you cannot expect a
**bit-identical** trajectory or identical battery/thermal/latency numbers. That is
by design: the phone, the apps, and the network are the real world.

This page describes what *is* fixed (the reproducibility set), how to bring the
device back to a known baseline, and why true identical runs are impossible.

## What the reproducibility set is

The **public 60-task benchmark** is the open evaluation protocol people re-run and
publish against. It is **not** “just a random subset of the 530” in the sense of a
throwaway sample — it is its own publishable evaluation set (3 days × 20 tasks),
sharing the same MobileRun harness, fabricated-seed philosophy, and grading policy
as the larger 530-task corpus.

| Piece | Where | Role |
|---|---|---|
| Task definitions | `benchmarks/androidlife-600/public.md` + `AndroidLife_public_v2.json` | Fixed prompts, placeholders, buckets |
| Vars / persona | `public_vars.local.env` | Device-pinned placeholder values |
| ASK USER / multi-turn | `ask_user_facts.json`, `multiturn_kb_public.json` | Withheld facts + KB profiles |
| Hallucination controls | `hallucination_controls.json` | Known-absent targets (honest fail) |
| Reset profile | `reset_phone.py --profile public_v2` | Undo agent side-effects → baseline |
| Seeds | `seed_data.py --day 1..3` + enrich / PDF helpers | Fabricated notes, files, calendar, etc. |
| Verify gates | `--verify-only` + `verify_day1_seeds.py --day N` | Do not launch on FAIL |
| Harness | MobileRun (Droidrun) over ADB | Same agent loop every run |
| Metrics | `run_metrics.json`, trajectories, reports | SR, steps, cost, battery, thermal, latency |

Operator walkthrough (commands): [`device-reset-and-seed.md`](device-reset-and-seed.md).  
Skill with edge cases: [`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md).

## Reset → seed → verify (before every public run)

1. **Connect** the OnePlus CPH2423 over ADB (canonical Tailscale serial in the reset doc).
2. **Reset** with `public_v2` so prior agent writes (calendar junk, drafts, etc.) are cleared.
3. **Seed** days 1–3 fabricated data, then public Notes enrich + PDFs, plus date-relative calendar conflicts as needed.
4. **Verify** baseline + each day — expect **RESULT PASS** before launching a batch.
5. **Run** the 60-task batch; grade with the same report / manual-audit path as published leaderboard rows.

Anyone following that checklist is on the same *protocol*. That is what “reproducible”
means here — not that two runs will print the same screenshots.

## Why it can never be a true identical run

The benchmark is **grounded in live phones and live apps**. Even with identical prompts
and a fresh seed, runs diverge because:

- **App and OS drift** — Play updates, WebView changes, notification copy, A/B layouts.
- **Network and cloud** — Gmail, Drive, Maps, Chrome content, search rankings, CDN timing.
- **Device physics** — battery level, thermal state, charging, background killers, a11y lag.
- **Non-deterministic agents** — sampling temperature, tool-order choices, retries, timeouts.
- **Human-shaped interrupts** — notifications, calls, and system dialogs that appear mid-task.
- **Time** — “tomorrow” calendar seeds, relative dates, and “today” UI all move with the clock.

So: **protocol reproducibility, not bitwise replay.** Two honest runs of the same model
can differ in steps, dollars, mAh, °C, and wall-clock while still being valid AndroidLife
results. Compare models under the same reset/seed/verify gate; do not expect pixel-identical
trajectories.

## What *is* comparable across runs

- Same task ids and grading rules (on-device end-state + honesty for HC tasks).
- Same seed *schema* (fabricated persona data — privacy-preserving, not scraped real user data).
- Same metric definitions (SR, efficiency, latency / `elapsed_seconds`, USD cost, battery/thermal).
- Published rows should state device model, mode (text/vision), and whether the run was interrupted (e.g. battery to 0).

For the full corpus shape and public composition tables, see
[`benchmark-spec.md`](benchmark-spec.md) and [`benchmark-spec-public.md`](benchmark-spec-public.md).
