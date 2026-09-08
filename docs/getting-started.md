# Getting started — study this repo

**AndroidLife** measures Android agents on a real phone (OnePlus CPH2423) — open-weight LLMs via API and a path to on-device SLMs, driven by MobileRun (Droidrun)
over everyday apps. Read this page first, then dive into the linked docs.

## What to learn (in order)

1. **[README.md](../README.md)** — what the harness is, quick start, public vs 530.
2. **This page** — mental model + where artifacts live.
3. **[docs/benchmark-spec-public.md](benchmark-spec-public.md)** — the **60-task public**
   sample (what the website leaderboard uses).
4. **[docs/evaluation-policy.md](evaluation-policy.md)** — how PASS / FAIL / hallucination
   are graded (manual audit is ground truth).
5. **[docs/fabricated-test-data.md](fabricated-test-data.md)** — why seeds exist and what
   ADB can vs cannot plant.
6. **[`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md)** —
   the full pre-run reset + reseed + manual UI checklist (operators).
7. **[docs/cli-reference.md](cli-reference.md)** — every CLI flag, detach/resume, model notes.
8. **[docs/HANDOFF.md](HANDOFF.md)** — current run state / conventions for maintainers
   (can be stale mid-session; trust the latest public report if they conflict).

## Two corpora

| Tier | Size | Source | Runs land in |
|---|---|---|---|
| **Public benchmark** | 60 tasks (3 days × 20) | `benchmarks/dailyBench-600/DailyBench_public_v2.json` + `public.md` | `assets/runs/public/<RUN_TS>/` |
| **Full dataset** | 530 tasks (28-day schedule) | `DailyBench_530_v1.json` + `tasks_530.md` | `assets/runs/full-bench/…` or dated roots |

The website leaderboard and trajectory browser are built from **public** runs only.

## TEXT vs VISION

- **TEXT** (default): accessibility tree only — no `--vision`.
- **VISION**: `--vision` adds a screenshot every step (a11y + image).

Same dataset either way; treat them as separate leaderboard rows.

## Lifecycle of a public run

```text
reset_phone.py --profile public_v2 --apply
  → seed_data.py --day {1,2,3} + enrich_public_notes + fabricate_public_pdfs
  → tomorrow Team Sync / Mentor conflicts
  → verify (baseline + day seeds PASS)
  → operator manual seeds (Chrome history, Photos favourites, Gmail Scapia, …)
  → start Phoenix (per-run DB) then dailybench_tasks.py --source public.md --all
  → dailybench_report.py + eval_hallucination_controls.py
  → make organize-public
  → manual audit → reports/public/public-<RUN_TS>.md
  → website: build_public_traj_from_hf.py + build_site_data.mjs + leaderboard.js row
```

Detached launch (survives Cursor/terminal exit):

```bash
# Prefer Popen(start_new_session=True, stdin=DEVNULL) — see README — or:
nohup … < /dev/null > batch-$RUN_TS.log 2>&1 &
```

Resume mid-batch with the **same** `--run-root` and either `--resume-from <task_id>` or
an explicit remaining `--task-id` list. Do not re-run folders that already have
`run_metrics.json` + `meta.command_exit_code`.

## Where results live

| Artifact | Path |
|---|---|
| Per-task trajectories / metrics | `assets/runs/public/<RUN_TS>/day{1,2,3}/<task>/` |
| Narrative report (manual audit GT) | `reports/public/public-<RUN_TS>.md` |
| Official self-report metrics | `reports/metrics/public/public-<RUN_TS>-report.{json,md}` |
| DeepEval DAGMetric HC | `reports/metrics/hallucination/public-<RUN_TS>.{json,md}` |
| ASK-USER turn audits | `reports/turn-based/public/ask-query-{single,multi}/<RUN_TS>/` |
| Site leaderboard | `website/assets/js/leaderboard.js` |
| Site trajectories index | `website/assets/data/trajectories/index.json` (media on Hugging Face) |

Public HF dataset: [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public).

## Scripts that matter (vs one-shots)

Canonical entrypoints are listed in [`scripts/README.md`](../scripts/README.md).

**Prefer these:** `setup.py`, `run/start_phoenix.py`, `run/run_day.py`, `seeding/reset_phone.py`,
`seeding/seed_data.py`, `seeding/enrich_public_notes.py`, `seeding/fabricate_public_pdfs.py`,
`seeding/verify_day1_seeds.py`, `eval/dailybench_report.py`, `eval/eval_hallucination_controls.py`,
`tools/organize_public_artifacts.py`, `tools/upload_public_runs_hf.py`,
`website/tools/build_public_traj_from_hf.py`, `website/tools/build_site_data.mjs`.

One-shot migration/upload helpers under `scripts/tools/` (convert_*, remove_*, recover_*,
send_coupon_*, etc.) are **not** part of the steady-state path — keep them only if you
still need that migration; do not treat them as required reading.
