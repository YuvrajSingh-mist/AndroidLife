#!/usr/bin/env python3
"""Render the RUNNABLE 530-task schedule as its own markdown doc (tasks_530.md).

Separates the 530 runnable set from the 730-corpus superset (tasks.md). Written in
the same markdown dialect as tasks.md (`### Day N` + `**[App]**` headers +
`- Easy/Medium (Npt): ...` bullets + numbered hard headers), so the doc is
readable, diffable, and re-parseable.

SOURCE DIRECTION: tasks_530.md is the **source of truth** for the runnable 530 set.
This script writes the doc from the JSON (a full re-sync); the reverse script
`scripts/export_530_dataset.py` parses the doc back into the JSON/JSONL. Every
task line carries its `task_id` in an HTML comment (`<!--task_id-->`) so ids
survive edits to the markdown.

Usage:
    uv run python scripts/export_530_markdown.py [--verify]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
from DailyBench.task_dataset import parse_tasks_markdown  # noqa: E402

SRC = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.json"
OUT = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_530.md"

HEADER = """# DrainBench: The 28-Day Survival Schedule — runnable 530-task set

This is the **canonical runnable schedule**: the deterministic 530-task corpus
(216 easy / 242 medium / 72 hard = 36 ASK USER / 36 DETERMINISTIC), landing each
day at the real-world ~9-10 distinct-app density (see
docs/app-usage-grounding.md).

This file is the **source of truth for the runnable set**: edit it, then run
`scripts/export_530_dataset.py` to regenerate `DailyBench_530_v1.json` / `.jsonl`.
Each task line carries its `task_id` in an HTML comment, so ids survive edits.
Resync from the JSON with `scripts/export_530_markdown.py`.

---
"""


def render(data: dict) -> str:
    tasks = data["tasks"]
    by_day: dict[int, list] = defaultdict(list)
    for t in tasks:
        by_day[t["day"]].append(t)

    lines = HEADER.splitlines()
    lines.append("")
    lines.append("## The 28-Day Schedule")
    for day in sorted(by_day):
        lines.append("")
        lines.append(f"### Day {day}")
        # group each day's tasks under their primary app's section, preserving
        # JSON order; hard tasks sit at the end of their primary app's section.
        sections: OrderedDict[str, dict] = OrderedDict()
        for t in by_day[day]:
            primary = t["apps"][0]
            sec = sections.setdefault(primary, {"easy_med": [], "hard": []})
            sec["hard" if t["bucket"] == "hard" else "easy_med"].append(t)
        for app, sec in sections.items():
            lines.append("")
            lines.append(f"**[{app}]**")
            for t in sec["easy_med"]:
                _maybe_hallucination_marker(lines, t)
                tag = f" **[{t['cross_app_label']}]**" if t.get("cross_app_label") else ""
                lines.append(f"- {t['bucket'].title()} ({t['points']}pt){tag}: {t['prompt_text']} <!--{t['task_id']}-->")
            for t in sec["hard"]:
                kind = "DETERMINISTIC" if not t.get("is_ask_user") else "ASK USER"
                app_tag = t.get("cross_app_label") or "+".join(t["apps"])
                body = t["prompt_text"]
                if t.get("note"):
                    body += f" ({t['note']})"
                lines.append("")
                _maybe_hallucination_marker(lines, t)
                lines.append(f"**{t['task_number_within_app']}. [{app_tag}] — {kind}**")
                lines.append(f"- {body} <!--{t['task_id']}-->")
    lines.append("")
    return "\n".join(lines) + "\n"


def _maybe_hallucination_marker(lines: list[str], task: dict) -> None:
    """Emit a `<!-- 🔮 HALLUCINATION CONTROL ... -->` doc-chrome comment above a
    task whose JSON carries hallucination_control=true. These lines are stripped
    as doc chrome by the dataset exporter, so they never become tasks."""
    if not task.get("hallucination_control"):
        return
    ctl_type = task.get("hallucination_control_type") or "control"
    absence = (task.get("hallucination_control_absence") or "").strip()
    note = f" ({absence})" if absence else ""
    lines.append(f"<!-- 🔮 HALLUCINATION CONTROL ({task['task_id']}, {ctl_type}): data genuinely absent{note}. Correct = honest failure; do NOT fabricate. -->")


def verify(parsed: dict) -> int:
    """Round-trip check: every JSON task has an identical parsed counterpart."""
    src = json.loads(SRC.read_text(encoding="utf-8"))["tasks"]
    parsed_tasks = parsed["tasks"]
    key = lambda t: (t["bucket"], tuple(t["apps"]), t["prompt_text"])
    parsed_by_key = {}
    for t in parsed_tasks:
        parsed_by_key.setdefault(key(t), []).append(t)
    missing = []
    for t in src:
        if not parsed_by_key.get(key(t)):
            missing.append(t["task_id"])
    # count uniqueness on both sides
    dup_parsed = len(parsed_tasks) - len(parsed_by_key)
    print(f"JSON tasks: {len(src)} | parsed-md tasks: {len(parsed_tasks)}")
    print(f"missing from parsed md: {len(missing)} {'-> ' + str(missing[:5]) if missing else ''}")
    print(f"duplicate keys in parsed md: {dup_parsed}")
    ok = (len(src) == len(parsed_tasks) and not missing and dup_parsed == 0)
    print("round-trip:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="parse the rendered md and compare against the JSON")
    args = ap.parse_args()

    data = json.loads(SRC.read_text(encoding="utf-8"))
    rendered = render(data)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT} ({len(data['tasks'])} tasks)")
    if args.verify:
        # strip the task_id HTML comments so parse_tasks_markdown sees clean bullets
        parsed = parse_tasks_markdown(re.sub(r"<!--.*?-->", "", rendered), source_path=str(OUT))
        return verify(parsed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
