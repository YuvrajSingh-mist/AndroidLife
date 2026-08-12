#!/usr/bin/env python3
"""Remove 25 repetitive easy tasks from tasks_530.md to land the corpus at 530.

The Google Workspace task sets (Docs/Sheets/Slides/Meet) were intended as REPLACEMENTS
for repetitive tasks, not net additions — so the corpus must stay at 530 tasks.

This removes the 25 most-repetitive non-Google, non-HC easy tasks (single-line blocks,
verified: every removed task is `bucket==easy`, `app_slug` not in the Google set, and
NOT a hallucination control). Resulting corpus: 530 tasks, 216 easy / 242 medium /
72 hard, 36 ASK USER / 36 DETERMINISTIC, 55 hallucination controls, all 26 apps still
present, per-day distinct apps still 10-12.

Usage: python3 scripts/tools/remove_repetitive_tasks.py
"""
from __future__ import annotations

from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

REMOVE = [
    "easy__clock__004",
    "easy__clock__009",
    "easy__gallery__005",
    "easy__gallery__015",
    "easy__camera__007",
    "easy__camera__013",
    "easy__settings__007",
    "easy__settings__015",
    "easy__youtube__006",
    "easy__calculator__008",
    "easy__calculator__014",
    "easy__gallery__003",
    "easy__settings__009",
    "easy__calculator__003",
    "easy__calculator__009",
    "easy__youtube__002",
    "easy__telegram__007",
    "easy__calendar__004",
    "easy__telegram__011",
    "easy__music__006",
    "easy__clock__003",
    "easy__music__011",
    "easy__clock__011",
    "easy__settings__008",
    "easy__clock__013",
]


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    removed: list[str] = []
    kept: list[str] = []
    for line in lines:
        tid = None
        for candidate in REMOVE:
            if f"<!--{candidate}-->" in line:
                tid = candidate
                break
        if tid is not None:
            removed.append(tid)
            # drop one adjacent blank line above to avoid double-blank gaps
            if kept and kept[-1].strip() == "":
                kept.pop()
        else:
            kept.append(line)

    missing = [t for t in REMOVE if t not in removed]
    if missing:
        print(f"ERROR: not found in md: {missing}")
        return 1

    MD.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"removed {len(removed)} tasks; remaining lines: {len(kept)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
