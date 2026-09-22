#!/usr/bin/env python3
"""Render a `reports/metrics/...-report.md` from its sibling `-report.json`.

The `.md` is a pure function of the `.json` (`androidlife_report.render_markdown`),
so the two must never disagree -- hand-editing the `.md` is what produced the drift
catalogued in redo.md section 7b (row 11 said 14.3% in JSON and 15.6% in MD, row 12
said 29.6% vs 33.3%, and so on).

For the 17 re-run rows the JSON was recomputed by exact arithmetic and the original
run batch is no longer on disk, so `androidlife_report.py` cannot be re-run to
regenerate the MD. This script closes that gap: it feeds the already-recomputed JSON
through the same renderer, so the MD is still derived rather than retyped.

Usage:
    uv run python scripts/tools/render_metrics_md.py reports/metrics/public/ROW-report.json
    uv run python scripts/tools/render_metrics_md.py --all
    uv run python scripts/tools/render_metrics_md.py --check        # drift report only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "eval"))

from androidlife_report import render_markdown  # noqa: E402

METRICS_DIR = REPO / "reports" / "metrics" / "public"


def render_one(json_path: Path, write: bool) -> bool:
    """Render one JSON to its .md. Returns True if the .md changed (or would change)."""
    md_path = json_path.with_suffix(".md")
    report = json.loads(json_path.read_text())
    rendered = render_markdown(report)
    current = md_path.read_text() if md_path.exists() else ""
    if current == rendered:
        return False
    if write:
        md_path.write_text(rendered)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", nargs="*", type=Path, help="report.json file(s) to render")
    ap.add_argument("--all", action="store_true", help=f"render every *-report.json under {METRICS_DIR}")
    ap.add_argument("--check", action="store_true", help="do not write; just report which .md files are stale")
    args = ap.parse_args()

    targets = list(args.json)
    if args.all or not targets:
        targets = sorted(METRICS_DIR.glob("*-report.json"))

    stale = []
    for json_path in targets:
        if render_one(json_path, write=not args.check):
            stale.append(json_path.name)

    if stale:
        verb = "stale" if args.check else "rendered"
        for name in stale:
            print(f"  {verb}: {name}")
        print(f"{len(stale)} file(s) {verb}")
        return 1 if args.check else 0
    print(f"{len(targets)} file(s) already in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
