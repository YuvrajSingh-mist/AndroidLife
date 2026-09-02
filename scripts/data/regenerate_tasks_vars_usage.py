#!/usr/bin/env python3
"""Regenerate benchmarks/dailyBench-600/tasks_vars_usage.json from the 530 dataset (DailyBench_530_v1.json) and tasks_vars.local.env."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.json"
VARS_LOCAL = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_vars.local.env"
OUT = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_vars_usage.json"


def parse_flat_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    local = parse_flat_env(VARS_LOCAL.read_text(encoding="utf-8"))

    # Collect every placeholder used across tasks, with the tasks+days that use it.
    usage: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for t in tasks:
        for ph in t.get("placeholders") or []:
            usage[ph].append((t["task_id"], t.get("day")))

    # Merge local-env keys that have no dataset placeholder (they may still be
    # referenced at run time from config; keep them as "no task" keys).
    local_keys = set(local)
    dataset_placeholders = set(usage)

    vars_out: dict[str, dict] = {}
    for key in sorted(usage):
        entries = sorted(usage[key], key=lambda e: (e[1] or 0, e[0]))
        vars_out[key] = {
            "configured_in_local_env": key in local_keys,
            "task_count": len(entries),
            "days": sorted({d for _, d in entries if d is not None}),
            "tasks": [tid for tid, _ in entries],
        }

    # Also record local.env keys with no dataset placeholder as empty task entries
    # so the "configured" flag is visible for every local key.
    for key in sorted(local_keys - dataset_placeholders):
        vars_out.setdefault(key, {
            "configured_in_local_env": True,
            "task_count": 0,
            "days": [],
            "tasks": [],
        })

    vars_with_no_config = {k: v for k, v in vars_out.items() if not v["configured_in_local_env"]}
    local_env_keys_with_no_task = sorted(k for k in local_keys if not usage.get(k))

    doc = {
        "file": "Global var->tasks index",
        "description": "For each key in tasks_vars.local.env (and every placeholder in the 530 dataset), the exact tasks that use it.",
        "generated_from": "DailyBench_530_v1.json + tasks_vars.local.env",
        "generated_at": "2026-08-12",
        "var_key_count_in_local_env": len(local_keys),
        "placeholder_key_count_in_dataset": len(dataset_placeholders),
        "vars": dict(sorted(vars_out.items())),
        "vars_with_no_config": dict(sorted(vars_with_no_config.items())),
        "local_env_keys_with_no_task": local_env_keys_with_no_task,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(doc['vars'])} keys)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
