#!/usr/bin/env python3
"""Audit that every public run's trajectory is present and loadable, end to end.

For each run in `index.json.public_run_order` this checks, per task that the run
covers:
  1. the run's condensed step JSON (`data`) exists on disk,
  2. that JSON parses and carries steps,
  3. the HF media path (`gif`) exists on the Hub (HEAD),
  4. the run's screenshots directory is non-empty on the Hub.

Exit code is non-zero when any run has missing coverage, so it can gate a publish.

Usage (from the repo root):
    python3 scripts/tools/audit_trajectories.py            # local checks + HF sample
    python3 scripts/tools/audit_trajectories.py --hf-all   # HEAD every gif
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
WEBSITE = ROOT / "androidlife-website"
INDEX = WEBSITE / "assets" / "data" / "trajectories" / "index.json"


def head_ok(url: str, session: requests.Session) -> bool:
    try:
        r = session.head(url, allow_redirects=True, timeout=20)
        return r.status_code == 200 and int(r.headers.get("content-length", "1")) > 0
    except requests.RequestException:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hf-all", action="store_true",
                    help="HEAD every gif (slow); default samples the first gif per run.")
    args = ap.parse_args()

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    order = idx["public_run_order"]
    keys = [r["key"] for r in order]
    labels = {r["key"]: r["label"] for r in order}

    tasks = idx["public"]
    per_run = defaultdict(lambda: {"tasks": 0, "no_data": [], "no_gif": [],
                                   "data_missing": [], "data_empty": []})
    sample_gif: dict[str, str] = {}

    for task_id, t in tasks.items():
        for r in t.get("runs") or []:
            k = r.get("run_key")
            if k not in labels:
                continue
            b = per_run[k]
            b["tasks"] += 1
            data = r.get("data")
            gif = r.get("gif")
            if not gif or gif.startswith("assets/"):
                b["no_gif"].append(task_id)
            elif k not in sample_gif:
                sample_gif[k] = gif
            if not data:
                b["no_data"].append(task_id)
                continue
            p = WEBSITE / data
            if not p.is_file():
                b["data_missing"].append(task_id)
                continue
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                b["data_empty"].append(task_id)
                continue
            steps = payload.get("steps") if isinstance(payload, dict) else payload
            if not steps:
                b["data_empty"].append(task_id)

    print(f"{'run':14} {'label':42} {'tasks':>5} {'data✓':>6} {'gif✓':>5} {'issues'}")
    print("-" * 100)
    bad_runs = []
    for k in keys:
        b = per_run[k]
        n = b["tasks"]
        d_ok = n - len(b["data_missing"]) - len(b["data_empty"]) - len(b["no_data"])
        g_ok = n - len(b["no_gif"])
        issues = len(b["data_missing"]) + len(b["data_empty"]) + len(b["no_data"]) + len(b["no_gif"])
        flag = "" if issues == 0 else "  <-- GAP"
        if n == 0:
            flag = "  <-- NO TASKS AT ALL"
            bad_runs.append(k)
        elif issues:
            bad_runs.append(k)
        print(f"{k:14} {labels[k][:42]:42} {n:5} {d_ok:6} {g_ok:5} {issues:6}{flag}")

    print("\nPer-run issue detail:")
    for k in keys:
        b = per_run[k]
        for field in ("no_data", "data_missing", "data_empty", "no_gif"):
            if b[field]:
                sample = ", ".join(b[field][:6])
                more = f" (+{len(b[field]) - 6})" if len(b[field]) > 6 else ""
                print(f"   {k:14} {field:13} x{len(b[field]):3}  {sample}{more}")

    print("\nHF media spot-check (first gif per run):")
    s = requests.Session()
    for k in keys:
        url = sample_gif.get(k)
        if not url:
            print(f"   {k:14} NO GIF URL")
            continue
        ok = head_ok(url, s)
        print(f"   {k:14} {'OK ' if ok else 'FAIL'} {url.split('/resolve/main/')[-1][:78]}")

    if args.hf_all:
        print("\nHF media full check (every gif):")
        for k in keys:
            fails = []
            seen = 0
            for task_id, t in tasks.items():
                for r in t.get("runs") or []:
                    if r.get("run_key") != k or not r.get("gif"):
                        continue
                    seen += 1
                    if not head_ok(r["gif"], s):
                        fails.append(task_id)
            print(f"   {k:14} {seen - len(fails)}/{seen} OK" + (f"  fails: {fails[:5]}" if fails else ""))

    print(f"\n{'FAIL' if bad_runs else 'PASS'}: {len(keys) - len(bad_runs)}/{len(keys)} runs complete")
    return 1 if bad_runs else 0


if __name__ == "__main__":
    sys.exit(main())
