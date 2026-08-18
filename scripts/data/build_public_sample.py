#!/usr/bin/env python3
"""Rebuild the public 3-day preview as a TRUE sample of the 530-task corpus.

Selects tasks directly from DailyBench_530_v1.json — real task_ids, exact prompt
text, placeholder slots preserved — remaps them to Days 1-3, and writes:
  - public.md                     (530-style md with <!--task_id--> comments)
  - DailyBench_public_v2.json/.jsonl (real 530 ids, day remapped to 1-3)
  - ask_user_facts.json           (public ASK USER sidecar, from the 730 facts)

The 4 multi-turn KB tasks are kept in the sample; their profiles live in
multiturn_kb_public.json keyed by the REAL 530 ids (same as multiturn_kb_530.json).

Placeholders are preserved as [slots] and resolved at run time from
public_vars.local.env + config/user.yaml (see docs/task-authoring/occasional-apps.md).

Usage: uv run python scripts/data/build_public_sample.py [--seed N]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from DailyBench.task_dataset import save_dataset_files  # noqa: E402

BENCH = ROOT / "benchmarks" / "dailyBench-600"
S530 = BENCH / "DailyBench_530_v1.json"
FACTS_730 = BENCH / "ask_user_facts_730.json"
FACTS_PUB = BENCH / "ask_user_facts.json"
HC = BENCH / "hallucination_controls.json"
PUBLIC_VARS = BENCH / "public_vars.local.env"
USER_YAML = ROOT / "config" / "user.yaml"
OUT_MD = BENCH / "public.md"
OUT_JSON = BENCH / "DailyBench_public_v2.json"
OUT_JSONL = BENCH / "DailyBench_public_v2.jsonl"

# The 4 best multi-turn (KB) tasks, by their REAL 530 ids.
MULTITURN = [
    "hard__swiggy__005",
    "hard__telegram-calendar__016",
    "hard__music-obsidian__077",
    "hard__gmail-calendar__003",
]

# Target sample size / bucket split (matches the 530 distribution, scaled to 57).
TARGETS = {"easy": 21, "medium": 20, "hard": 16}
HARD_ASK_USER = 6  # of the 16 hard, 6 ASK USER (the rest DET, incl. 4 multi-turn)

NAT = re.compile(r"\b(i'?m|i want|i need|can you|could you|i'?d)\b", re.I)
IMPER = re.compile(
    r"^(Open|Go to|Check|Find|Fetch|Count|Search|In |On |Set|Save|Get|Create|Delete|Take|Compute|Play|Star|Turn|Rename|Look|Draft|Make|Send|Pull|List|Add|Type|Call|Message)",
    re.I,
)
DAY_SPLIT = {"easy": [7, 7, 7], "medium": [7, 7, 6], "hard": [6, 6, 4]}


def load_placeholder_keys() -> set[str]:
    keys: set[str] = set()
    if PUBLIC_VARS.exists():
        keys |= set(re.findall(r"^([a-z0-9\- ]+)\s*=", PUBLIC_VARS.read_text(), re.M))
    if USER_YAML.exists():
        keys |= set(re.findall(r"^([a-z0-9\-_ ]+):", USER_YAML.read_text(), re.M))
    return keys


def resolvable(t: dict, keys: set[str]) -> bool:
    return all(ph in keys for ph in (t.get("placeholders") or []))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    tasks = json.loads(S530.read_text())["tasks"]
    by_id = {t["task_id"]: t for t in tasks}
    facts730 = json.loads(FACTS_730.read_text())
    hc = set(json.loads(HC.read_text())) if HC.exists() else set()
    keys = load_placeholder_keys()

    def pool(bucket: str):
        return [
            t
            for t in tasks
            if t["bucket"] == bucket
            and t["task_id"] not in hc
            and resolvable(t, keys)
            and NAT.search(t["prompt_text"])
            and not IMPER.match(t["prompt_text"].strip())
        ]

    easy_pool, med_pool = pool("easy"), pool("medium")
    au_pool = [t for t in pool("hard") if t.get("ahi") == "ASK USER"]
    det_pool = [
        t
        for t in pool("hard")
        if t.get("ahi") == "DETERMINISTIC" and t["task_id"] not in MULTITURN
    ]

    for label, p, n in (("easy", easy_pool, TARGETS["easy"]), ("medium", med_pool, TARGETS["medium"])):
        if len(p) < n:
            raise SystemExit(f"not enough {label} candidates ({len(p)} < {n})")
    if len(au_pool) < HARD_ASK_USER:
        raise SystemExit(f"not enough ASK USER candidates ({len(au_pool)})")
    if len(det_pool) < (TARGETS["hard"] - HARD_ASK_USER - len(MULTITURN)):
        raise SystemExit("not enough DET hard candidates")

    rng.shuffle(easy_pool)
    rng.shuffle(med_pool)
    rng.shuffle(au_pool)
    rng.shuffle(det_pool)

    selected: dict[str, dict] = {tid: by_id[tid] for tid in MULTITURN}  # multi-turn first
    for t in easy_pool[: TARGETS["easy"]]:
        selected[t["task_id"]] = t
    for t in med_pool[: TARGETS["medium"]]:
        selected[t["task_id"]] = t
    for t in au_pool[:HARD_ASK_USER]:
        selected[t["task_id"]] = t
    for t in det_pool[: (TARGETS["hard"] - HARD_ASK_USER - len(MULTITURN))]:
        selected[t["task_id"]] = t

    if len(selected) != sum(TARGETS.values()):
        raise SystemExit(f"selection size {len(selected)} != {sum(TARGETS.values())}")

    # Assign days per bucket (e.g. hard 6/6/4) so hard-per-day stays balanced.
    day_of: dict[str, int] = {}
    for bucket, split in DAY_SPLIT.items():
        bucket_tasks = [t for t in selected.values() if t["bucket"] == bucket]
        rng.shuffle(bucket_tasks)
        idx = 0
        for day, n in enumerate(split, start=1):
            for _ in range(n):
                day_of[bucket_tasks[idx]["task_id"]] = day
                idx += 1

    # Public rows: real ids, day remapped, prompt exact.
    public_tasks: list[dict] = []
    for t in selected.values():
        row = dict(t)
        row["day"] = day_of[t["task_id"]]
        public_tasks.append(row)
    public_tasks.sort(key=lambda r: (r["day"], r["bucket"] != "hard", r["app_slug"], r["task_id"]))

    # --- write ask_user_facts.json (public sidecar) for the chosen AU tasks ---
    pub_facts = {
        t["task_id"]: facts730.get(t["task_id"], t.get("ask_user_fact") or "")
        for t in public_tasks
        if t.get("ahi") == "ASK USER"
    }
    FACTS_PUB.write_text(json.dumps(pub_facts, ensure_ascii=False, indent=2) + "\n")

    # --- write public.md (530 format, with <!--task_id--> comments) ---
    md_lines = [
        "# DrainBench — Public Sample (3-Day Preview)",
        "",
        "### Not the eval set. A structural preview only — a TRUE sample drawn from the",
        "530-task corpus (same task_ids, exact prompt text, placeholder slots). "
        "**57 tasks total.**",
        "",
        "**Grading model**: no separate rubric/LLM-judge \"open-ended\" bucket — a task either has everything",
        "it needs (deterministic, ADB-verified end state) or is missing one load-bearing fact the agent",
        "must actively ask for (agent-user interaction, resolved by an LLM playing the user, holding only",
        "the omitted fact, answering just what's asked). Multi-turn (KB) tasks are DETERMINISTIC with a",
        "knowledge-base profile in `multiturn_kb_public.json`.",
        "",
        "Easy: 1 app, Medium: 1-2 apps; Hard battery: 2-3 apps, genuine reasoning, natural first-person",
        "requests, **distributed across the days and mixed so ask-user, deterministic and multi-turn tasks",
        "aren't grouped or predictable by position.**",
        "",
        "---",
        "",
    ]
    per_day: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for t in public_tasks:
        per_day[t["day"]].append(t)

    for day in (1, 2, 3):
        md_lines.append(f"### Day {day}")
        md_lines.append("")
        day_tasks = per_day[day]
        hard = [t for t in day_tasks if t["bucket"] == "hard"]
        nonhard = [t for t in day_tasks if t["bucket"] != "hard"]
        # group non-hard by app
        from collections import OrderedDict

        by_app: "OrderedDict[str, list]" = OrderedDict()
        for t in sorted(nonhard, key=lambda r: (r["app"], r["task_id"])):
            by_app.setdefault(t["app"], []).append(t)
        for app, app_tasks in by_app.items():
            md_lines.append(f"**[{app}]**")
            for t in app_tasks:
                label = "Easy (1pt)" if t["bucket"] == "easy" else "Medium (3pt)"
                tag = f" **[{' + '.join(t.get('apps') or [])}]**" if t.get("is_cross_app") else ""
                md_lines.append(f"- {label}{tag}: {t['prompt_text']} <!--{t['task_id']}-->")
            md_lines.append("")
        if hard:
            md_lines.append(f"Hard tasks — Day {day}:")
            md_lines.append("")
            for i, t in enumerate(hard, start=1):
                ahi = t.get("ahi") or "DETERMINISTIC"
                md_lines.append(f"**{i}. [{t['app']}] — {ahi}**")
                md_lines.append(f"- {t['prompt_text']} <!--{t['task_id']}-->")
                md_lines.append("")
        md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines).rstrip() + "\n")

    # --- write the public dataset files (real ids) ---
    dataset = {
        "dataset_name": "DailyBench-Public",
        "dataset_version": "v2",
        "source_path": "benchmarks/dailyBench-600/public.md",
        "task_count": len(public_tasks),
        "bucket_counts": dict(Counter(t["bucket"] for t in public_tasks)),
        "tasks": public_tasks,
    }
    save_dataset_files(dataset, OUT_JSON, OUT_JSONL)

    print(f"Wrote public sample: {len(public_tasks)} tasks")
    print("  buckets:", dict(Counter(t["bucket"] for t in public_tasks)))
    h = [t for t in public_tasks if t["bucket"] == "hard"]
    print("  hard ahi:", dict(Counter(t.get("ahi") for t in h)))
    print("  hard per day:", dict(Counter(t["day"] for t in h)))
    print("  multi-turn tasks:", [tid for tid in MULTITURN if tid in selected])
    print("  ASK USER facts written:", len(pub_facts))
    print("  placeholder tasks:", sum(1 for t in public_tasks if t.get("placeholders")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
