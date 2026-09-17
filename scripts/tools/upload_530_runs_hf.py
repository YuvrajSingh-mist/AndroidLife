#!/usr/bin/env python3
"""Upload the 530-corpus full-bench run artifacts (days 1-5) to androidlife-530.

Each local full-bench run root holds one day of the 530 schedule; the remote
layout mirrors the corpus day numbering:

    assets/runs/full-bench/<run-id>/dayN  ->  runs/dayN

Run the PII guard over the same directories first — these are real-phone
screenshots and the repo is public. This script does not scan; it only uploads
what it is pointed at.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

REPO = "YuvrajSingh9886/androidlife-530"
ROOT = Path(__file__).resolve().parents[2]
FB = ROOT / "assets" / "runs" / "full-bench"

# local run root -> (day label, run date seen in the day reports)
DAYS = {
    "2026-08-09-153930": "day1",
    "2026-08-10-234158": "day2",
    "2026-08-11-040846": "day3",
    "2026-08-13-011830": "day4",
    "2026-08-14-031816": "day5",
}

os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

RUNS_README = """# 530-corpus run artifacts (days 1-5)

Full run artifacts for the first five days of the 530-task schedule, captured on
a real phone. One directory per day:

| Remote | Local source | Day report |
|---|---|---|
| `runs/day1/` | `assets/runs/full-bench/2026-08-09-153930/day1/` | `reports/day1-run-2026-08-09.md` |
| `runs/day2/` | `assets/runs/full-bench/2026-08-10-234158/day2/` | `reports/day-2.md` |
| `runs/day3/` | `assets/runs/full-bench/2026-08-11-040846/day3/` | `reports/day-3.md` |
| `runs/day4/` | `assets/runs/full-bench/2026-08-13-011830/day4/` | `reports/day-4.md` |
| `runs/day5/` | `assets/runs/full-bench/2026-08-14-031816/day5/` | `reports/day-5.md` |

Each task directory carries `meta.json`, `output.json`, `run_metrics.json`,
`agent.log.txt`, `llm_proxy_metrics.jsonl`, `preflight.json`, `postflight.json`
and a `trajectories/` tree (per-step screenshots + accessibility snapshots).

The 60-task public-preview run artifacts live in
[`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public)
under `runs/`; the trajectory-viewer media for these days lives in
[`YuvrajSingh9886/androidlife-trajectories`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-trajectories)
under `trajectories/dayN/`.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload full-bench days 1-5 to androidlife-530.")
    ap.add_argument("--push", action="store_true", help="Actually upload (default: dry run).")
    ap.add_argument("--days", nargs="*", default=sorted(DAYS.values()),
                    help="Subset of day labels, e.g. --days day1 day2.")
    args = ap.parse_args()

    api = HfApi(token=os.environ.get("HF_TOKEN") or None)
    plan = []
    for run_id, day in DAYS.items():
        if day not in args.days:
            continue
        src = FB / run_id / day
        if not src.is_dir():
            print(f"   [skip] {day}: {src} missing")
            continue
        n = sum(1 for _ in src.rglob("*") if _.is_file())
        sz = sum(p.stat().st_size for p in src.rglob("*") if p.is_file())
        plan.append((day, src, n, sz))
        print(f"   {day}: {n:6} files  {sz / 1e9:.2f} GB  <- {src.relative_to(ROOT)}")

    print(f"\n   total: {sum(p[2] for p in plan):,} files, "
          f"{sum(p[3] for p in plan) / 1e9:.2f} GB -> {REPO}/runs/")

    if not args.push:
        print("\n(dry run — pass --push to upload)")
        return 0

    api.upload_file(path_or_fileobj=str(ROOT / ".cache" / "runs_readme.md"),
                    path_in_repo="runs/README.md", repo_id=REPO, repo_type="dataset")

    for day, src, n, sz in plan:
        print(f"\n   uploading {day} ({n} files, {sz / 1e9:.2f} GB) ...", flush=True)
        api.upload_folder(folder_path=str(src), path_in_repo=f"runs/{day}",
                          repo_id=REPO, repo_type="dataset")
        print(f"   done {day}")
    print(f"\nuploaded {len(plan)} day(s) to {REPO}")
    return 0


if __name__ == "__main__":
    (ROOT / ".cache").mkdir(exist_ok=True)
    (ROOT / ".cache" / "runs_readme.md").write_text(RUNS_README, encoding="utf-8")
    sys.exit(main())
