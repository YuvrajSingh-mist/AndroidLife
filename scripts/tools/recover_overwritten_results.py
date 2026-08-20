#!/usr/bin/env python3
"""Recover per-task result JSONs for tasks whose run-folder files were overwritten.

The public run `assets/runs/public/2026-08-20-003030` used a dataset where two task pairs
shared the same `task_number_within_app` (the bug fixed in scripts/data/
export_public_dataset.py). Because the batch runner names each run folder from
that field, the later task of each pair overwrote the earlier task's top-level
result files (output.json / meta.json / run_metrics.json) inside the same folder.
The earlier tasks' full trajectories survived in the folder's `trajectories/`
subdirs, so their results are recoverable.

This script rebuilds a proper standalone run folder for each overwritten task
under `recovered/<task_id>/`, reading the final outcome (success/reason/steps)
from the surviving trajectory's FastAgentEndEvent and the timing from the
trajectory folder name + macro.json timestamp. The recovered folders carry the
same result-file layout (output.json / meta.json / run_metrics.json) so the
report generator discovers them alongside the 59 intact run folders -> 61 total.

Overwritten tasks:
  - medium__google-maps__002  (traj 20260820_003854_159b478e; folder was reused
    by medium__google-maps__003)
  - medium__clock__009         (traj 20260820_032626_b83d8636; folder was reused
    by medium__clock__011)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "assets" / "runs" / "public" / "2026-08-20-003030"
DATASET = ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_public_v2.json"
VARS_FILE = ROOT / "benchmarks" / "dailyBench-600" / "public_vars.local.env"

IST = timezone(timedelta(hours=5, minutes=30))

# (task_id, collided_run_dir, surviving_traj_subdir_name)
RECOVER = [
    (
        "medium__google-maps__002",
        RUN_ROOT / "day1" / "medium-google-maps-001",
        "20260820_003854_159b478e",
    ),
    (
        "medium__clock__009",
        RUN_ROOT / "day2" / "medium-clock-001",
        "20260820_032626_b83d8636",
    ),
]

MODEL = "qwen/qwen3.6-plus"
SERIAL = "100.108.15.119:5555"


def load_vars() -> dict[str, str]:
    """Parse the vars file (KEY=value with inline comments) into a dict."""
    out: dict[str, str] = {}
    for line in VARS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def vars_for_task(task: dict, all_vars: dict[str, str]) -> dict[str, str]:
    """Fill the task's placeholders from the vars file (matching the batch runner)."""
    filled: dict[str, str] = {}
    for ph in task.get("placeholders") or []:
        key = ph.strip().lower().replace(" ", "_").replace("-", "_")
        value = all_vars.get(ph) or all_vars.get(key) or all_vars.get(ph.lower())
        if value is not None:
            filled[ph] = value
    return filled


def parse_dir_start(dirname: str) -> datetime:
    """Parse the trajectory folder name's leading YYYYMMDD_HHMMSS (IST) -> aware UTC."""
    stamp = dirname.split("_", 2)
    assert len(stamp) >= 2, dirname
    dt_ist = datetime.strptime(f"{stamp[0]}_{stamp[1]}", "%Y%m%d_%H%M%S").replace(tzinfo=IST)
    return dt_ist.astimezone(timezone.utc)


def parse_macro_end(stamp: str) -> datetime:
    """Parse macro.json's timestamp (YYYYMMDD_HHMMSS, IST) -> aware UTC."""
    dt_ist = datetime.strptime(stamp, "%Y%m%d_%H%M%S").replace(tzinfo=IST)
    return dt_ist.astimezone(timezone.utc)


def recover_task(task_id: str, run_dir: Path, traj_name: str) -> Path:
    """Rebuild a standalone recovered run folder for one overwritten task."""
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    task = next(t for t in dataset["tasks"] if t["task_id"] == task_id)

    traj_dir = run_dir / "trajectories" / traj_name
    trajectory = json.loads((traj_dir / "trajectory.json").read_text(encoding="utf-8"))
    macro = json.loads((traj_dir / "macro.json").read_text(encoding="utf-8"))

    end_events = [e for e in trajectory if e.get("type") == "FastAgentEndEvent"]
    if not end_events:
        raise SystemExit(f"no FastAgentEndEvent in {traj_dir}")
    end = end_events[-1]
    success = bool(end.get("success"))
    reason = end.get("reason") or ""
    steps = int(end.get("tool_call_count") or 0)
    command_exit_code = 0 if success else 1

    started_at = parse_dir_start(traj_name)
    ended_at = parse_macro_end(macro.get("timestamp", ""))
    elapsed_seconds = (ended_at - started_at).total_seconds()

    all_vars = load_vars()
    variables = vars_for_task(task, all_vars)
    goal = task["prompt_text"]
    bucket, app_slug, within = task_id.split("__")
    run_id = f"{bucket}-{app_slug}-{int(within):03d}"
    day = task.get("day")
    label = f"day{day}--{run_id}"

    out_dir = RUN_ROOT / "recovered" / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    output = {"reason": reason, "steps": steps, "success": success}
    (out_dir / "output.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )

    meta = {
        "app_reset_stopped_package": task.get("app_reset_stopped_package"),
        "command_exit_code": command_exit_code,
        "elapsed_seconds": elapsed_seconds,
        "ended_at_utc": ended_at.isoformat(),
        "goal": goal,
        "label": label,
        "model": MODEL,
        "run_id": run_id,
        "serial": SERIAL,
        "started_at_utc": started_at.isoformat(),
        "steps": steps,
        "task_id": task_id,
        "task_timeout_seconds": 2400,
        "temperature": 0.0,
        "top_p": 0.95,
        "variables": variables,
        # Recovery provenance: which surviving trajectory this was rebuilt from,
        # and why (the original top-level result files were overwritten by the
        # later task sharing the same task_number_within_app in the pre-fix dataset).
        "recovered_from": {
            "reason": (
                "top-level result files (output.json/meta.json/run_metrics.json) "
                "were overwritten by the later task sharing the same "
                "task_number_within_app in the pre-fix dataset"
            ),
            "surviving_trajectory": str(traj_dir.relative_to(RUN_ROOT)),
            "dataset_fix": "scripts/data/export_public_dataset.py",
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    run_metrics = {
        "ask_user_call_count": 0,
        "command_exit_code": command_exit_code,
        "elapsed_seconds": elapsed_seconds,
        "ended_at_utc": ended_at.isoformat(),
        "label": label,
        "run_id": run_id,
        "started_at_utc": started_at.isoformat(),
    }
    (out_dir / "run_metrics.json").write_text(
        json.dumps(run_metrics, indent=2) + "\n", encoding="utf-8"
    )

    # A short note so the folder is self-documenting.
    (out_dir / "RECOVERED.txt").write_text(
        (
            f"Recovered result files for {task_id}\n"
            f"  success={success} steps={steps} elapsed={elapsed_seconds:.1f}s\n"
            f"  rebuilt from {traj_dir.relative_to(RUN_ROOT)}\n"
            "  The original top-level result files were overwritten by the later task\n"
            "  sharing the same task_number_within_app in the pre-fix dataset.\n"
        ),
        encoding="utf-8",
    )

    print(f"recovered {task_id}: success={success} steps={steps} elapsed={elapsed_seconds:.1f}s -> {out_dir.relative_to(ROOT)}")
    return out_dir


def main() -> int:
    for task_id, run_dir, traj_name in RECOVER:
        recover_task(task_id, run_dir, traj_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
