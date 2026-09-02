#!/usr/bin/env python3
"""Convert the 5 weather-checking tasks to use the actual Weather app (net.oneplus.weather)."""
from __future__ import annotations

import re
from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

DAY_HEADER = re.compile(r"^### Day (\d+)$")
APP_SECTION = re.compile(r"^\*\*\[(.+?)\]\*\*$")
HARD_HEADER = re.compile(r"^\*\*(\d+)\. \[(.+?)\] — (DETERMINISTIC|ASK USER)\*\*$")

# easy weather tasks: old_id -> (new_id, new prompt)
EASY_WEATHER = {
    "easy__google-search__002": ("easy__weather__001", "What's the weather looking like today? Open the Weather app and give me today's forecast."),
    "easy__chrome__003": ("easy__weather__002", "Can you open the Weather app and check tomorrow's forecast for me?"),
    "easy__google-maps__007": ("easy__weather__003", "Can you check today's weather in the Weather app and tell me if it looks good for my commute?"),
    "easy__google-search__010": ("easy__weather__004", "Check the current temperature outside in the Weather app?"),
}

# hard weather task: old -> new (in place; header tag changes too)
HARD_WEATHER = ("hard__chrome-clock-notes__006", "hard__weather-clock-notes__006")

# slot-freeing moves: (task_id, src_day, dst_day)
MOVES = [
    ("easy__google-docs__002", 5, 18),
    ("easy__youtube__008", 16, 11),
    ("medium__telegram__007", 19, 22),
]


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


def primary_app(lines: list[str], tid: str) -> str:
    i = find_task_line(lines, tid)
    for j in range(i, -1, -1):
        if lines[j] is None:
            continue
        m = APP_SECTION.match(lines[j])
        if m:
            return m.group(1)
    return ""


def ensure_section(lines: list[str], day: int, section: str) -> int:
    ins = find_section_insert(lines, day, section)
    if ins >= 0:
        return ins
    # create section right after the day header
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

    # 1. Hard task: rename in place (body line + preceding hard header).
    hi = find_task_line(lines, HARD_WEATHER[0])
    if hi < 0:
        raise SystemExit(f"ERROR: {HARD_WEATHER[0]} not found")
    lines[hi] = lines[hi].replace(HARD_WEATHER[0], HARD_WEATHER[1])
    j = hi - 1
    while j >= 0 and (lines[j] is None or lines[j].strip() == ""):
        j -= 1
    if j >= 0 and lines[j] and HARD_HEADER.match(lines[j].strip()):
        lines[j] = lines[j].replace("[Chrome+Clock+Notes]", "[Weather+Clock+Notes]")

    # 2. Pull out easy weather tasks + move-out tasks (mark None).
    pulled: dict[str, list[str]] = {}
    prim: dict[str, str] = {}
    src_days: dict[str, int] = {}
    for tid in list(EASY_WEATHER) + [m[0] for m in MOVES]:
        idx = find_task_line(lines, tid)
        if idx < 0:
            raise SystemExit(f"ERROR: {tid} not found")
        pulled[tid] = [lines[idx]]
        prim[tid] = primary_app(lines, tid)
        src_days[tid] = day_of(lines, idx)
        lines[idx] = None

    cleaned = [l for l in lines if l is not None]

    # 3. Re-insert move-out tasks under primary-app section in dest day.
    for tid, _src, dst in MOVES:
        ins = find_section_insert(cleaned, dst, prim[tid])
        if ins < 0:
            raise SystemExit(f"ERROR: day {dst} has no '{prim[tid]}' section for {tid}")
        block = pulled[tid]
        insert = [""] + block if cleaned[ins - 1].strip() != "" else block
        cleaned[ins:ins] = insert

    # 4. Insert renamed easy weather tasks under **[Weather]** in their own days.
    for old, (new, prompt) in EASY_WEATHER.items():
        src_day = src_days[old]
        ins = ensure_section(cleaned, src_day, "Weather")
        new_line = f"- Easy (1pt): {prompt} <!--{new}-->"
        insert = [""] + [new_line] if cleaned[ins - 1].strip() != "" else [new_line]
        cleaned[ins:ins] = insert

    MD.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print("weather conversion + slot-freeing moves applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
