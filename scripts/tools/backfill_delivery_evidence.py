#!/usr/bin/env python
"""Backfill `delivery.json` from the leak-cleanup logs of runs taken before the probe existed.

Why this is legitimate
----------------------
The delivery evidence IS the leak-cleanup's own reading. `reset_phone.py --leak-cleanup-only`
opens the Yuvraj Airtel chat and calls `_tg_run_window_bubbles` / `_tg_draft` -- the exact
functions behind `probe_telegram_delivery` -- moments after the run ends, and prints what it
found. So a log line is the same measurement the probe would have made, and parsing it
recovers the evidence for runs that predate `delivery.json`.

It is NOT a reconstruction of what the model did; it records what the device showed.

Caveats, deliberately
---------------------
  * Only rows whose cleanup actually reached the chat are written. A cleanup that reported
    "could not open the Yuvraj Airtel chat" is recorded as `reached_chat: false`, which the
    grader treats as NO EVIDENCE and never demotes on.
  * A cleanup that failed (e.g. it found a bubble but could not delete it) still yields
    usable evidence: the bubble it found is the delivery.
  * Evidence is per ROW, and several rows share a chat, so the log must be read in order.
    Pass `--run-root` once per row in run order; do not batch unrelated days together.

Usage
-----
    uv run python scripts/tools/backfill_delivery_evidence.py \
        --run-root assets/runs/public/20260922-114915 \
        --run-root assets/runs/public/20260922-140420 ...
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# `[ok]  telegram: composer empty, no run-window bubbles in Yuvraj Airtel`
CLEAN_RE = re.compile(r"telegram: composer empty, no run-window bubbles")
# `[!!]  telegram leak: draft=<repr>, N run-window bubble(s) dated <label>`
LEAK_RE = re.compile(r"telegram leak: draft=(?P<draft>.*?), (?P<n>\d+) run-window bubble")
# `[!!]  telegram: could not open the Yuvraj Airtel chat`
UNREACHED_RE = re.compile(r"could not open the Yuvraj Airtel chat")


def parse_cleanup_log(text: str) -> dict | None:
    """The probe-equivalent evidence from one leak-cleanup log. None if it says nothing."""
    if UNREACHED_RE.search(text):
        return {"reached_chat": False, "sent_bubbles": 0, "draft_present": False,
                "source": "leak-cleanup log (chat unreachable)"}
    leak = LEAK_RE.search(text)
    if leak:
        draft = leak.group("draft").strip()
        return {
            "reached_chat": True,
            "sent_bubbles": int(leak.group("n")),
            # `draft=None` is the logged form of "no draft".
            "draft_present": draft not in ("None", "", "''", '""'),
            "source": "leak-cleanup log",
        }
    if CLEAN_RE.search(text):
        return {"reached_chat": True, "sent_bubbles": 0, "draft_present": False,
                "source": "leak-cleanup log"}
    return None


def task_dir(run_root: Path) -> Path | None:
    """The single task directory under a run root's day folder."""
    hits = [p for p in run_root.glob("day*/*/output.json")]
    return hits[0].parent if len(hits) == 1 else None


def find_log(repo: Path, run_root: Path) -> Path | None:
    """The cleanup log for this run root's row (named leak-cleanup-row<N>.log)."""
    launch = run_root / "LAUNCH.txt"
    if not launch.exists():
        return None
    row = None
    for line in launch.read_text().splitlines():
        if line.startswith("row="):
            row = line.split("=", 1)[1].strip()
    if not row:
        return None
    log = repo / "assets" / "runs" / "logs" / f"leak-cleanup-row{row}.log"
    return log if log.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="Repo root (default: derived from this file).")
    ap.add_argument("--run-root", action="append", required=True,
                    help="A run root to backfill. Repeat, in run order.")
    ap.add_argument("--apply", action="store_true", help="Write delivery.json (default: dry run).")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite an existing delivery.json (default: skip it).")
    args = ap.parse_args()

    repo = Path(args.repo) if args.repo else Path(__file__).resolve().parents[2]
    problems: list[str] = []

    for raw in args.run_root:
        run_root = Path(raw) if Path(raw).is_absolute() else repo / raw
        if not run_root.is_dir():
            problems.append(f"{run_root}: not a directory")
            continue
        td = task_dir(run_root)
        if td is None:
            problems.append(f"{run_root.name}: expected exactly one day*/task dir with output.json")
            continue
        target = td / "delivery.json"
        if target.exists() and not args.force:
            print(f"SKIP   {run_root.name}: {target.name} already present")
            continue
        log = find_log(repo, run_root)
        if log is None:
            problems.append(f"{run_root.name}: no leak-cleanup log (run predates the cleanup)")
            continue
        evidence = parse_cleanup_log(log.read_text(encoding="utf-8", errors="replace"))
        if evidence is None:
            problems.append(f"{run_root.name}: {log.name} has no telegram verdict to parse")
            continue
        print(f"{'WRITE ' if args.apply else 'DRY   '}{run_root.name} -> {td.relative_to(repo)}"
              f"  reached_chat={evidence['reached_chat']} sent_bubbles={evidence['sent_bubbles']}"
              f" draft_present={evidence['draft_present']}")
        if args.apply:
            target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    for problem in problems:
        print(f"WARN   {problem}", file=sys.stderr)
    print(f"{'wrote' if args.apply else 'would write'} evidence for "
          f"{len(args.run_root) - len(problems)} run(s); {len(problems)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
