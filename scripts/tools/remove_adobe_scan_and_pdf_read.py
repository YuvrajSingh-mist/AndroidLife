#!/usr/bin/env python3
"""Remove Adobe Scan and strengthen PDF open+read coverage (REPLACE-only, dist unchanged)."""
from __future__ import annotations

import re
from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

DAY_HEADER = re.compile(r"^### Day (\d+)$")
APP_SECTION = re.compile(r"^\*\*\[(.+?)\]\*\*$")

# old Adobe id -> (restored id, restored section, restored prompt)
RESTORE = {
    "easy__adobe-scan__001": (
        "easy__google-search__012", "Google Search",
        "Can you check today's top news headline for [topic] on Google Search?",
    ),
    "easy__adobe-scan__002": (
        "easy__shopping-delivery-browser__013", "Chrome",
        "Can you search for '[product]' on a shopping site in Chrome and check its current price?",
    ),
}

# PDF open+read conversion: (old id, new prompt) — task_id and app stay the same
PDF_READ = {
    "easy__files__014": "Can you open the PDF 'invoice_seed.pdf' in Files and tell me the total amount shown on it?",
}


def day_of(lines: list[str], idx: int) -> int:
    for j in range(idx, -1, -1):
        m = DAY_HEADER.match(lines[j] or "")
        if m:
            return int(m.group(1))
    return 0


def find_task_line(lines: list[str], tid: str) -> int:
    for i, l in enumerate(lines):
        if l is not None and f"<!--{tid}-->" in l:
            return i
    return -1


def find_section_insert(lines: list[str], day: int, section: str) -> int:
    in_day = False
    for i, l in enumerate(lines):
        if l is None:
            continue
        m = DAY_HEADER.match(l)
        if m:
            d = int(m.group(1))
            in_day = d == day
            if d > day:
                break
            continue
        if in_day and APP_SECTION.match(l):
            if APP_SECTION.match(l).group(1) == section:
                return i + 1
    return -1


def remove_section_if_empty(lines: list[str], day: int, section: str) -> None:
    """Drop a `**[section]**` header that now has no task lines beneath it in `day`."""
    in_day = False
    for i, l in enumerate(lines):
        if l is None:
            continue
        m = DAY_HEADER.match(l)
        if m:
            d = int(m.group(1))
            in_day = d == day
            if d > day:
                break
            continue
        if in_day and APP_SECTION.match(l):
            if APP_SECTION.match(l).group(1) != section:
                continue
            # walk forward until the next section/day; if only blanks remain, drop it
            j = i + 1
            saw_task = False
            while j < len(lines):
                nxt = lines[j]
                if nxt is None:
                    j += 1
                    continue
                if APP_SECTION.match(nxt) or DAY_HEADER.match(nxt):
                    break
                if nxt.strip():
                    saw_task = True
                    break
                j += 1
            if not saw_task:
                lines[i] = None


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 1. Capture Adobe task days, remove them, and remove their (now-empty) sections.
    src_days: dict[str, int] = {}
    for old in RESTORE:
        idx = find_task_line(lines, old)
        if idx < 0:
            raise SystemExit(f"ERROR: {old} not found")
        src_days[old] = day_of(lines, idx)
        lines[idx] = None

    cleaned = [l for l in lines if l is not None]
    for old, (_new, _section, _prompt) in RESTORE.items():
        remove_section_if_empty(cleaned, src_days[old], "Adobe Scan")
    cleaned = [l for l in cleaned if l is not None]

    # 2. Insert restored tasks under their original sections in the same day.
    for old, (new, section, prompt) in RESTORE.items():
        src_day = src_days[old]
        ins = find_section_insert(cleaned, src_day, section)
        if ins < 0:
            raise SystemExit(f"ERROR: day {src_day} has no '{section}' section for {new}")
        new_line = f"- Easy (1pt): {prompt} <!--{new}-->"
        insert = [""] + [new_line] if cleaned[ins - 1].strip() != "" else [new_line]
        cleaned[ins:ins] = insert

    # 3. PDF open+read conversion (in place).
    for old, prompt in PDF_READ.items():
        idx = find_task_line(cleaned, old)
        if idx < 0:
            raise SystemExit(f"ERROR: {old} not found")
        cleaned[idx] = f"- Easy (1pt): {prompt} <!--{old}-->"

    MD.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    for old, (new, section, _) in RESTORE.items():
        print(f"{old:34s} -> {new:38s} [{section}] day {src_days[old]}")
    for old, prompt in PDF_READ.items():
        print(f"{old:34s} -> PDF open+read task (same id/app/day)")
    print("Adobe Scan removed; easy-tier PDF open+read task added (dist unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
