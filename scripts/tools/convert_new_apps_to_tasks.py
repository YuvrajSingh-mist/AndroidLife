#!/usr/bin/env python3
"""Diversify the 530-task corpus with 7 newly-installed apps by REPLACING easy tasks.

User directive: "installed zomato, prime, make my trip, book my show and msn for
news ... use this in the existing tasks and diversify pls not changing the dist"
+ "we have pdf opening tasks too right? since its something that people use a lot".

Note: the installed food-delivery app is SWIGGY (in.swiggy.android), not Zomato —
no com.application.zomato package exists on the device, so Swiggy is used.

New apps (7) -> app_slug (task_id middle segment = app_slug, so ids change):
  Swiggy          -> swiggy
  Prime Video     -> prime-video
  MakeMyTrip      -> makemytrip
  BookMyShow      -> bookmyshow
  MSN News        -> msn-news
  Amazon Shopping -> amazon-shopping
  Adobe Scan      -> adobe-scan   (PDF open + scan -> first-class PDF tasks)

Each swap replaces an EASY single-app task on a 10-app "slack" day whose app still
has >=2 touches that day, so the destination day goes 10->11 apps (within the
days-4-28 <=11 cap) and the source app stays in the union. Buckets stay 216/242/72,
HC stays 55, AU/DET stay 36/36, total stays 530 — nothing is added, only swapped.

Usage: python3 scripts/tools/convert_new_apps_to_tasks.py
"""
from __future__ import annotations

import re
from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

DAY_HEADER = re.compile(r"^### Day (\d+)$")
APP_SECTION = re.compile(r"^\*\*\[(.+?)\]\*\*$")

# old_id -> (new_id, new_section_header, new_prompt)
CONVERSIONS = {
    "easy__shopping-delivery-browser__002": (
        "easy__swiggy__001", "Swiggy",
        "Can you open Swiggy and check the delivery status of my most recent order?",
    ),
    "easy__shopping-delivery-browser__005": (
        "easy__prime-video__001", "Prime Video",
        "Can you open Prime Video and tell me what's in my Continue Watching list?",
    ),
    "easy__youtube__008": (
        "easy__makemytrip__001", "MakeMyTrip",
        "Can you open MakeMyTrip and check the cheapest flight from [city] to [place] for next week?",
    ),
    "easy__google-search__006": (
        "easy__bookmyshow__001", "BookMyShow",
        "Can you open BookMyShow and tell me which movies are playing at the nearest cinema today?",
    ),
    "easy__files__010": (
        "easy__msn-news__001", "MSN News",
        "Can you open MSN News and tell me today's top headline?",
    ),
    "easy__google-maps__010": (
        "easy__amazon-shopping__001", "Amazon Shopping",
        "Can you open Amazon Shopping and check the price of '[product]'?",
    ),
    "easy__google-search__012": (
        "easy__adobe-scan__001", "Adobe Scan",
        "Can you open the PDF 'Q3_Report.pdf' in Adobe Scan and tell me how many pages it has?",
    ),
    "easy__shopping-delivery-browser__013": (
        "easy__adobe-scan__002", "Adobe Scan",
        "Can you use Adobe Scan to scan this printed page and save it as a PDF?",
    ),
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
    """Index right after the `**[section]**` header in `day`; -1 if section absent."""
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


def ensure_section(lines: list[str], day: int, section: str) -> int:
    ins = find_section_insert(lines, day, section)
    if ins >= 0:
        return ins
    for i, l in enumerate(lines):
        if l is None:
            continue
        m = DAY_HEADER.match(l)
        if m and int(m.group(1)) == day:
            lines.insert(i + 1, f"**[{section}]**")
            return i + 2
    raise SystemExit(f"ERROR: day {day} header not found")


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 1. Capture source days, then mark every converted line None.
    src_days: dict[str, int] = {}
    for old in CONVERSIONS:
        idx = find_task_line(lines, old)
        if idx < 0:
            raise SystemExit(f"ERROR: {old} not found")
        src_days[old] = day_of(lines, idx)
        lines[idx] = None

    cleaned = [l for l in lines if l is not None]

    # 2. Insert each new task under its new app's section in the SAME day.
    for old, (new, section, prompt) in CONVERSIONS.items():
        src_day = src_days[old]
        ins = ensure_section(cleaned, src_day, section)
        new_line = f"- Easy (1pt): {prompt} <!--{new}-->"
        insert = [""] + [new_line] if cleaned[ins - 1].strip() != "" else [new_line]
        cleaned[ins:ins] = insert

    MD.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    for old, (new, section, _) in CONVERSIONS.items():
        print(f"{old:42s} -> {new:28s} [{section}] day {src_days[old]}")
    print("7 new apps woven into existing easy tasks (replace-only, dist unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
