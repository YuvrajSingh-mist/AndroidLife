#!/usr/bin/env python3
"""Generate the runnable 530-task JSON/JSONL from tasks_530.md (the source of truth).

This is the reverse of scripts/export_530_markdown.py. It reads `tasks_530.md` —
the canonical runnable schedule — and writes `DailyBench_530_v1.json` +
`DailyBench_530_v1.jsonl` ("530" in the filenames is the corpus size; the current
corpus is exactly 530 tasks: Google Workspace sets replaced repetitive tasks).
Each task line carries its `task_id` in an HTML comment
(`<!--task_id-->`), so the ids survive edits and are preserved exactly here (gaps
included). ASK USER facts are merged from the `ask_user_facts_730.json` sidecar
(keyed by task_id).

Field notes (md-driven by design):
- `app_slug` is taken from the task_id's middle segment (the id is the authority),
  so ids stay consistent with app_slug even for the 730 lineage's display-name
  quirks (e.g. slug `shopping-delivery-browser`, `drive`).
- `app` is the display label shown in the md section/header, which for those quirk
  tasks is the canonical name (`Chrome` / `Google Drive`) rather than the 730
  display name (`Shopping & Delivery (browser)` / `Drive`). To change it, edit the
  md and re-run.

Usage:
    uv run python scripts/export_530_dataset.py [--verify]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
from DailyBench.task_dataset import (  # noqa: E402
    HARD_FLAT_POINTS,
    app_slug,
    difficulty_of,
    extract_placeholders,
    resolve_apps,
    save_dataset_files,
    split_hard_label,
    to_prompt_template,
)

SRC = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_530.md"
OUT_JSON = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.json"
OUT_JSONL = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.jsonl"
FACTS = REPO_ROOT / "benchmarks" / "dailyBench-600" / "ask_user_facts_730.json"
HALLUCINATIONS = REPO_ROOT / "benchmarks" / "dailyBench-600" / "hallucination_controls.json"

DAY_RE = re.compile(r"^### Day (\d+)$")
SECTION_RE = re.compile(r"^\*\*\[(.+?)\]\*\*$")
HARD_HEADER_RE = re.compile(r"^\*\*(\d+)\. \[(.+?)\] — (DETERMINISTIC|ASK USER SINGLE|ASK USER - MULTI|ASK USER)\*\*$")
EASYMED_RE = re.compile(r"^- (Easy|Medium) \((\d+)pt\)(?: \*\*\[(.+?)\]\*\*)?: (.+)$")
HARD_BODY_RE = re.compile(r"^- (.+)$")
NOTE_RE = re.compile(r"\s*\((deliberately .*)\)$")
COMMENT_SUFFIX_RE = re.compile(r"\s*<!--([^>]+)-->$")

BUCKET_POINTS = {"easy": 1, "medium": 3}


def strip_comment(text: str) -> tuple[str, str | None]:
    """Split a trailing `<!--task_id-->` off a bullet line."""
    m = COMMENT_SUFFIX_RE.search(text)
    if m:
        return text[: m.start()].rstrip(), m.group(1)
    return text.rstrip(), None


def parse(md_text: str) -> list[dict]:
    """Parse tasks_530.md into task rows (md order preserved)."""
    tasks: list[dict] = []
    current_day: int | None = None
    current_app = ""
    pending_hard: tuple[int, str, str] | None = None  # (index, app_tag, kind)
    app_counts: dict[tuple[str, str], int] = {}
    body_started = False  # everything before the first `---` is doc chrome (header)

    def next_ordinal(bucket: str, app_key: str) -> int:
        key = (bucket, app_key)
        n = app_counts.get(key, 0) + 1
        app_counts[key] = n
        return n

    def add_task(bucket, day, app_name, apps, prompt_text, *, ahi, interaction, note, task_id,
                 within_app, cross_app_label, ordinal):
        tasks.append(
            {
                "task_id": task_id,
                "bucket": bucket,
                "difficulty": difficulty_of(bucket),
                "points": BUCKET_POINTS.get(bucket, HARD_FLAT_POINTS),
                "day": day,
                # `app` is the display label shown in the md section/header; `app_slug`
                # is always the task_id's middle segment (the id is the authority and
                # matches what dailybench_report.py recovers from the id).
                "app": app_name,
                "app_slug": task_id.split("__")[1],
                "apps": apps,
                "num_apps": len(apps),
                "cross_app_required": len(apps) > 1,
                "ahi": ahi,
                "interaction": interaction,
                "note": note,
                "ask_user_fact": None,
                "is_ask_user": ahi == "ASK USER",
                "task_number_within_app": within_app,
                "task_number_within_dataset_app": ordinal,
                "prompt_text": prompt_text,
                "prompt_template": to_prompt_template(prompt_text),
                "placeholders": extract_placeholders(prompt_text),
                "placeholder_count": len(extract_placeholders(prompt_text)),
                "is_cross_app": cross_app_label is not None,
                "cross_app_label": cross_app_label,
                "source_path": str(SRC),
            }
        )

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if not body_started:
            if line.strip() == "---":
                body_started = True
            continue

        m = DAY_RE.match(line)
        if m:
            current_day = int(m.group(1))
            continue

        # other heading lines and horizontal rules are doc chrome, not tasks
        if line.startswith("#") or line.startswith("---"):
            continue

        # HTML-comment marker lines (e.g. the `<!-- 🔮 HALLUCINATION CONTROL: ... -->`
        # annotations above hallucination-control tasks) are doc chrome, not tasks.
        if line.startswith("<!--") and line.endswith("-->"):
            continue

        m = SECTION_RE.match(line)
        if m:
            current_app = m.group(1).strip()
            continue

        # A hard task is a two-line block: header then `- body`.
        if pending_hard is not None:
            m = HARD_BODY_RE.match(line)
            if m is None:
                raise ValueError(f"Expected hard-task body after header, got: {line!r}")
            index, app_tag, kind = pending_hard
            pending_hard = None
            ahi, interaction = split_hard_label(kind)
            body, tid_comment = strip_comment(m.group(1))
            note = None
            nm = NOTE_RE.search(body)
            if nm:
                note = nm.group(1)
                body = body[: nm.start()].strip()
            cross_app_label = app_tag if "+" in app_tag else None
            app_name = app_tag or current_app
            app_key = app_slug(app_name or "unknown")
            prompt_text = body.strip()
            apps = resolve_apps(app_name, prompt_text)
            task_id = tid_comment if tid_comment else f"hard__{app_key}__{index:03d}"
            # within_app must be unique per (bucket, app_slug) because it feeds the run
            # folder label. Prefer the id's own trailing number when the task carries an
            # explicit id comment (deterministic, matches the easy/med branch); fall back
            # to the section header number only for generated ids.
            within_app = int(task_id.split("__")[-1]) if tid_comment else index
            add_task(
                "hard", current_day, app_name, apps, prompt_text,
                ahi=ahi, interaction=interaction, note=note, task_id=task_id, within_app=within_app,
                cross_app_label=cross_app_label,
                ordinal=next_ordinal("hard", app_key),
            )
            continue

        m = HARD_HEADER_RE.match(line)
        if m:
            pending_hard = (int(m.group(1)), m.group(2).strip(), m.group(3).strip())
            continue

        m = EASYMED_RE.match(line)
        if m is None:
            raise ValueError(f"Unparseable line: {line!r}")
        bucket = m.group(1).lower()
        points = int(m.group(2))
        tag = m.group(3).strip() if m.group(3) else None
        body, tid_comment = strip_comment(m.group(4))
        if points != BUCKET_POINTS[bucket]:
            raise ValueError(f"{bucket} task has wrong points {points}: {line!r}")
        cross_app_label = tag if tag and "+" in tag else None
        app_name = cross_app_label or current_app
        app_key = app_slug(app_name or "unknown")
        ordinal = next_ordinal(bucket, app_key)
        if tid_comment:
            task_id = tid_comment
            within_app = int(task_id.split("__")[-1])
        else:
            task_id = f"{bucket}__{app_key}__{ordinal:03d}"
            within_app = ordinal
        prompt_text = body.strip()
        apps = resolve_apps(app_name, prompt_text)
        add_task(
            bucket, current_day, app_name, apps, prompt_text,
            ahi=None, interaction=None, note=None, task_id=task_id, within_app=within_app,
            cross_app_label=cross_app_label, ordinal=ordinal,
        )

    if pending_hard is not None:
        raise ValueError(f"Unterminated hard-task header: {pending_hard}")
    return tasks


def merge_facts(tasks: list[dict]) -> None:
    """Fill each ASK USER task's ask_user_fact from the sidecar (keyed by task_id)."""
    if not FACTS.exists():
        print(f"warning: no facts file at {FACTS}")
        return
    facts: dict[str, str] = json.loads(FACTS.read_text(encoding="utf-8"))
    for t in tasks:
        fact = facts.get(t["task_id"])
        if fact is not None:
            t["ask_user_fact"] = fact


def merge_hallucination_controls(tasks: list[dict]) -> None:
    """Tag hallucination-control tasks from the sidecar (keyed by task_id).

    These tasks deliberately reference data guaranteed absent on the device; the
    correct behavior is an honest "no such data present" (failure), not a fabricated
    answer. The sidecar records the absence + expected outcome; grading (honest-
    success / honest-failure / hallucinated) is done live, not written into the md.
    """
    if not HALLUCINATIONS.exists():
        print(f"warning: no hallucination controls file at {HALLUCINATIONS}")
        return
    controls: dict[str, dict] = json.loads(HALLUCINATIONS.read_text(encoding="utf-8"))
    for t in tasks:
        ctl = controls.get(t["task_id"])
        if ctl:
            t["hallucination_control"] = True
            t["data_absent"] = ctl.get("data_absent", True)
            t["hallucination_control_type"] = ctl.get("type", "")
            t["hallucination_control_absence"] = ctl.get("absence", "")


def build_dataset(tasks: list[dict]) -> dict:
    bucket_counts = Counter(t["bucket"] for t in tasks)
    return {
        "dataset_name": "DrainBench 530 (28-day survival schedule)",
        "dataset_version": "v1",
        # The 730 lineage was retired; the 530 is standalone (parsed from md).
        "parent": None,
        "source_path": str(SRC),
        "task_count": len(tasks),
        "bucket_counts": {k: bucket_counts[k] for k in ("easy", "medium", "hard")},
        "selection": "scripts/export_530_dataset.py: parse tasks_530.md (source of truth) "
                     "-> DailyBench_530_v1.json/.jsonl",
        "tasks": tasks,
    }


def verify(tasks: list[dict]) -> int:
    ok = True
    counts = Counter(t["bucket"] for t in tasks)
    # Google Workspace task sets (Docs/Sheets/Slides/Meet, 31 tasks) were authored as
    # REPLACEMENTS for repetitive tasks, not net additions — corpus must stay 530.
    # 25 most-repetitive easy tasks removed -> 530 total; easy 241 -> 216, medium 242,
    # hard 72 (36 ASK USER / 36 DETERMINISTIC unchanged).
    expected = {"easy": 216, "medium": 242, "hard": 72}
    if counts != expected:
        print(f"FAIL bucket counts: {dict(counts)} != {expected}")
        ok = False

    ids = [t["task_id"] for t in tasks]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"FAIL duplicate task_ids: {sorted(dupes)}")
        ok = False

    hard = [t for t in tasks if t["bucket"] == "hard"]
    ask_user = [t for t in hard if t["is_ask_user"]]
    det = [t for t in hard if not t["is_ask_user"]]
    single = [t for t in hard if t.get("interaction") == "single"]
    multi = [t for t in hard if t.get("interaction") == "multi"]
    if len(det) != 23 or len(single) != 36 or len(multi) != 13:
        print(f"FAIL hard split: DET={len(det)}, ASK USER SINGLE={len(single)}, ASK USER - MULTI={len(multi)} != 23/36/13")
        ok = False
    missing_fact = [t["task_id"] for t in single if not t.get("ask_user_fact")]
    if missing_fact:
        print(f"FAIL ASK USER (single) tasks missing facts: {missing_fact}")
        ok = False

    days = sorted({t["day"] for t in tasks if t.get("day") is not None})
    if len(days) != 28 or days != list(range(1, 29)):
        print(f"FAIL day coverage: {days}")
        ok = False

    controls = [t for t in tasks if t.get("hallucination_control")]
    if len(controls) < 1:
        print("FAIL no hallucination-control tasks tagged in the dataset")
        ok = False
    for c in controls:
        if not c.get("data_absent") or not c.get("hallucination_control_absence"):
            print(f"FAIL control {c['task_id']} missing data_absent/absence")
            ok = False
    control_ids = [c["task_id"] for c in controls]
    if "medium__gmail-notes__001" not in control_ids or "medium__files__014" not in control_ids:
        print(f"FAIL expected hallucination controls missing: {control_ids}")
        ok = False
    # Every day must carry at least one hallucination control (1-2/day is the design).
    # Days 1-2 are exempt: they were benchmarked before controls were added and keep
    # their original prompts (Day 2 carries its pre-existing 2 controls; Day 1 has none).
    control_days = {}
    for c in controls:
        control_days.setdefault(c.get("day"), []).append(c["task_id"])
    for day in range(3, 29):
        if not control_days.get(day):
            print(f"FAIL day {day} has no hallucination control")
            ok = False

    print(f"tasks: {len(tasks)} | buckets: {dict(counts)} | hard: "
          f"{len(ask_user)} AU / {len(det)} DET | days: 1-{max(days) if days else '-'} | "
          f"dupes: {len(dupes)} | AU facts: {len(ask_user) - len(missing_fact)}/{len(ask_user)} | "
          f"hallucination controls: {len(controls)}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="self-check counts/facts after writing")
    args = ap.parse_args()

    md = SRC.read_text(encoding="utf-8")
    tasks = parse(md)
    merge_facts(tasks)
    merge_hallucination_controls(tasks)
    dataset = build_dataset(tasks)
    save_dataset_files(dataset, OUT_JSON, OUT_JSONL)
    print(f"wrote {OUT_JSON} ({len(tasks)} tasks)")
    print(f"wrote {OUT_JSONL} ({len(tasks)} lines)")
    return verify(tasks) if args.verify else 0


if __name__ == "__main__":
    raise SystemExit(main())
