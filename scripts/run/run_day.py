#!/usr/bin/env python3
"""Run one day's tasks (or the whole corpus) straight from tasks_530.md in ONE command.

Reads the runnable 530-task schedule — benchmarks/dailyBench-600/tasks_530.md, the
source of truth — extracts a day's task_ids (--day N) or every task (--all), and
hands them to the dataset-backed runner (dailybench_tasks.py) as a single batch.

Fixes the common invocation errors:
  * builds the --task-id argv in Python (no shell word-splitting),
  * loads .env so OPENROUTER_API_KEY / LLM config is available,
  * defaults serial / llm-upstream-base / model from env (or known past values),
    instead of erroring with "Need --serial, --llm-upstream-base, and --model".

Usage:
  uv run python scripts/run_day.py --day 1             # Day-1 tasks (22)
  uv run python scripts/run_day.py --day 3 --dry-run   # preview the commands
  uv run python scripts/run_day.py --all               # the whole 530-task set
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# This file lives in scripts/run/, so the repo root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_530.md"
VARS_DIR = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_vars"

DAY_RE = re.compile(r"^### Day (\d+)$")

# The proxy forwards `upstream_base + "/v1/chat/completions"`, so the base must
# NOT include the /v1 segment (that would double it -> OpenRouter's 404 HTML).
DEFAULT_UPSTREAM = "https://openrouter.ai/api"
# Default agent model (OpenRouter slug). Cheap + XML-reliable for the
# fast-agent XML tool-calling protocol; overridable per run with --model or $MODEL.
DEFAULT_MODEL = "qwen/qwen3.7-flash"


def task_ids_by_day() -> dict[int, list[str]]:
    """Extract {day: [task_id, ...]} from tasks_530.md, preserving schedule order.

    Reuses export_530_dataset.parse() so the ids match the exported JSON exactly,
    including auto-generated ids for comment-less lines (e.g. easy__notes__001) and
    skipping the `<!-- 🔮 ... -->` hallucination-control marker lines.
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
    from export_530_dataset import parse  # noqa: E402

    by_day: dict[int, list[str]] = {}
    for t in parse(SCHEDULE.read_text(encoding="utf-8")):
        by_day.setdefault(t["day"], []).append(t["task_id"])
    return by_day


def detect_serial() -> str | None:
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    for ln in res.stdout.splitlines():
        parts = ln.split("\t")
        if len(parts) == 2 and parts[1] == "device":
            return parts[0]
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run a day (or all 530) from tasks_530.md")
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--day", type=int, metavar="N", help="Day 1-28 to run (its task ids from tasks_530.md)")
    sel.add_argument("--all", action="store_true", help="Run the whole 530-task set")
    ap.add_argument("--serial", default=os.environ.get("DAILYBENCH_SERIAL"),
                    help="ADB serial (default: $DAILYBENCH_SERIAL or auto-detect)")
    ap.add_argument("--llm-upstream-base", default=os.environ.get("LLM_UPSTREAM", DEFAULT_UPSTREAM))
    ap.add_argument("--model", default=os.environ.get("MODEL", DEFAULT_MODEL))
    ap.add_argument("--vars-file", default=None, help="Overrides the auto per-day vars file")
    ap.add_argument("--dry-run", action="store_true", help="Print the runner command without executing")
    # common pass-through flags to the runner
    ap.add_argument("--steps", type=int)
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--top-p", type=float)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--vision", action="store_true")
    ap.add_argument("--screen-record", action="store_true")
    ap.add_argument("--reasoning", action="store_true")
    ap.add_argument("--thinking", action="store_true", help="Leave the model's reasoning/thinking mode ON (default off: harness sends reasoning-off switches).")
    ap.add_argument("--no-debug", action="store_true")
    ap.add_argument("--cooldown-seconds", type=float)
    # pass-through to the runner (save-trajectory + Phoenix tracing are ON by default)
    ap.add_argument("--save-trajectory", choices=["none", "step", "action"])
    ap.add_argument("--no-tracing", action="store_true")
    ap.add_argument("--phoenix-url")
    ap.add_argument("--run-root", default=None,
                    help="Forwarded to the runner: put runs under this root (e.g. assets/runs/full-bench/<ts>) instead of the default assets/runs/<ts>.")
    # Default per-day: running `--day N` auto-targets the `dailybench-dayN` Phoenix
    # project (and its per-day DB under assets/db/dayN/). Override to opt out.
    ap.add_argument("--phoenix-project", default=None,
                    help="Phoenix project name for traces (default: dailybench-day<N> when --day N is given).")
    return ap


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = build_parser().parse_args()

    by_day = task_ids_by_day()
    if args.day is not None:
        if args.day not in by_day:
            print(f"ERROR: tasks_530.md has no Day {args.day} (found days {sorted(by_day)})")
            return 2
        task_ids = by_day[args.day]
        label = f"Day {args.day}"
    else:
        task_ids = [tid for day in sorted(by_day) for tid in by_day[day]]
        label = "all 530"

    serial = args.serial or detect_serial()
    if not serial:
        print("ERROR: no device connected and no --serial given")
        return 2

    vars_file = args.vars_file
    if vars_file is None and args.day is not None:
        candidate = VARS_DIR / f"day_{args.day}.env"
        if candidate.exists():
            vars_file = str(candidate)

    # Per-day Phoenix project: `--day N` targets `dailybench-dayN` by default so traces
    # land in the day's own project + DB (assets/db/dayN/phoenix.db) instead of a shared
    # "dailybench" bucket. An explicit --phoenix-project overrides this.
    phoenix_project = args.phoenix_project
    if phoenix_project is None and args.day is not None:
        phoenix_project = f"dailybench-day{args.day}"

    # Phoenix pre-flight guard: tracing is ON by default, and the mobilerun SDK
    # silently drops traces when `phoenix serve` isn't running (day-4 2026-08-13 lost
    # its entire trace DB this way). Fail the batch up-front instead of silently
    # running untraced. Opt out deliberately with --no-tracing.
    if not args.no_tracing and not args.dry_run:
        phoenix_url = args.phoenix_url or "http://localhost:6006"
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from DailyBench.cli import check_phoenix_ready  # noqa: E402

        if not check_phoenix_ready(phoenix_url, warn_only=False):
            print(
                f"ABORTING {label}: Phoenix collector not reachable at {phoenix_url}.\n"
                "  Start it for this day first, e.g.:\n"
                f"    PHOENIX_SQL_DATABASE_URL=\"sqlite:///{REPO_ROOT}/assets/db/day{args.day}/phoenix.db\" \\\n"
                f"    PHOENIX_PROJECT_NAME={phoenix_project} uv run phoenix serve --port 6006\n"
                "  or pass --no-tracing to skip trace capture deliberately.",
            )
            return 3

    cmd = [sys.executable, str(REPO_ROOT / "dailybench_tasks.py"),
           "--serial", serial,
           "--llm-upstream-base", args.llm_upstream_base,
           "--model", args.model]
    if vars_file:
        cmd += ["--vars-file", vars_file]
    for tid in task_ids:
        cmd += ["--task-id", tid]
    for flag in ("--steps", "--temperature", "--top-p", "--seed", "--repeats", "--cooldown-seconds"):
        val = getattr(args, flag.lstrip("-").replace("-", "_"))
        if val is not None:
            cmd += [flag, str(val)]
    for flag in ("--vision", "--screen-record", "--reasoning", "--thinking", "--no-debug", "--no-tracing"):
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            cmd.append(flag)
    if args.save_trajectory:
        cmd += ["--save-trajectory", args.save_trajectory]
    if args.phoenix_url:
        cmd += ["--phoenix-url", args.phoenix_url]
    if args.run_root:
        cmd += ["--run-root", args.run_root]
    if phoenix_project:
        cmd += ["--phoenix-project", phoenix_project]
    if args.dry_run:
        cmd.append("--dry-run")

    print(f"# {label}: {len(task_ids)} tasks from {SCHEDULE.name}")
    if args.dry_run:
        print("  ".join(f"  {t}" for t in task_ids))
    print("  " + " ".join(cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
