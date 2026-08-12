#!/usr/bin/env python3
"""Move 14 tasks between days in tasks_530.md to cap every day 4-28 at <=11 apps.

Only edits tasks_530.md. Each task moves to a destination day that ALREADY has the
task's primary-app section (verified), so the destination app union is unchanged and
the source day loses that app (single-task, non-HC app). No tasks deleted, no HC
tasks moved, no task_id changed, no Google set's own days broken.

Usage: python3 scripts/tools/apply_day_cap_moves.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

# (task_id, src_day, dst_day)  -- dst day verified to already contain the task's
# primary-app section (so destination union is unchanged and stays <=11).
MOVES = [
    ("easy__calendar__004", 7, 17),
    ("medium__gmail__004", 7, 17),
    ("medium__messages__006", 10, 8),
    ("medium__google-maps__004", 11, 18),
    ("easy__shopping-delivery-browser__005", 12, 7),
    ("medium__notes__003", 13, 17),
    ("medium__files-telegram__001", 13, 25),
    ("easy__google-docs__004", 13, 4),
    ("hard__files-notes__069", 14, 24),
    ("medium__clock__005", 16, 6),
    ("easy__gallery__007", 16, 11),
    ("easy__camera__012", 21, 7),
    ("easy__google-docs__007", 21, 16),
    ("easy__gallery__015", 28, 24),
]

HARD_HEADER = re.compile(r"^\*\*\d+\. \[.+\] — (DETERMINISTIC|ASK USER)\*\*$")
TASK_ID = re.compile(r"<!--([^>]+)-->")
DAY_HEADER = re.compile(r"^### Day (\d+)$")
APP_SECTION = re.compile(r"^\*\*\[(.+?)\]\*\*$")


def day_of(lines: list[str], idx: int) -> int:
    for j in range(idx, -1, -1):
        if lines[j] is None:
            continue
        m = DAY_HEADER.match(lines[j])
        if m:
            return int(m.group(1))
    return 0


def find_task_block(lines: list[str], tid: str, day: int) -> tuple[int, int] | None:
    """Return (start, end) inclusive of the task's block on `day`.

    A block is the body line carrying <!--tid--> plus, for hard tasks, the preceding
    `**N. [App+App] — KIND**` header line.
    """
    for i, l in enumerate(lines):
        if l is None:
            continue
        if f"<!--{tid}-->" in l and day_of(lines, i) == day:
            start = i
            j = i - 1
            while j >= 0 and (lines[j] is None or lines[j].strip() == ""):
                j -= 1
            if j >= 0 and lines[j] is not None and HARD_HEADER.match(lines[j].strip()):
                start = j
            return start, i
    return None


def find_insert_point(lines: list[str], day: int, primary_app: str) -> int | None:
    """Return the line index right after the `**[primary_app]**` header in `day`."""
    in_day = False
    for i, l in enumerate(lines):
        if DAY_HEADER.match(l):
            d = int(DAY_HEADER.match(l).group(1))
            in_day = d == day
            if d > day:
                break
        if in_day and APP_SECTION.match(l):
            if APP_SECTION.match(l).group(1) == primary_app:
                return i + 1
    return None


def primary_app_of_task(lines: list[str], tid: str) -> str:
    """Primary app = the app section the task currently sits under (its first app)."""
    for i, l in enumerate(lines):
        if l is None:
            continue
        if f"<!--{tid}-->" in l:
            for j in range(i, -1, -1):
                if lines[j] is None:
                    continue
                m = APP_SECTION.match(lines[j])
                if m:
                    return m.group(1)
    raise SystemExit(f"could not find primary app for {tid}")


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 1. Capture every block + its primary app, in original order.
    blocks: list[tuple[str, int, int, str, list[str]]] = []  # (tid, src, dst, primary, block)
    for tid, src, dst in MOVES:
        blk = find_task_block(lines, tid, src)
        if blk is None:
            print(f"ERROR: {tid} not found on day {src}")
            return 1
        s, e = blk
        primary = primary_app_of_task(lines, tid)
        block_lines = lines[s : e + 1]
        blocks.append((tid, src, dst, primary, block_lines))
        # mark the block lines as consumed
        for k in range(s, e + 1):
            lines[k] = None

    # 2. Remove consumed lines (keep structure: collapse the gaps).
    cleaned = [l for l in lines if l is not None]

    # 3. Pre-verify every destination still has its primary-app section in `cleaned`.
    for tid, src, dst, primary, _blk in blocks:
        if find_insert_point(cleaned, dst, primary) is None:
            print(f"ERROR: day {dst} has no '{primary}' section for {tid}")
            return 1

    # 4. Insert each block into its destination day under the primary-app section.
    for tid, src, dst, primary, block_lines in blocks:
        ins = find_insert_point(cleaned, dst, primary)
        if ins is None:
            print(f"ERROR: day {dst} lost '{primary}' section for {tid}")
            return 1
        # ensure a blank line separates the section header from the inserted task
        insert = [""] + block_lines if cleaned[ins - 1].strip() != "" else block_lines
        cleaned[ins:ins] = insert

    # 5. Write back.
    MD.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print(f"moved {len(blocks)} tasks in {MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
