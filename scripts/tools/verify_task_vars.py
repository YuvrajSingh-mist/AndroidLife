#!/usr/bin/env python
"""Render the task vars an agent will actually be handed, and reject known-bad values.

Why this exists
---------------
`task_batch.run()` guards a *missing* placeholder (it raises `SystemExit`), but nothing
guards a *wrong* one. The values come from a precedence chain whose top layer —
`config/user.yaml` — is **gitignored**, so a repository fix never reaches it and it
silently overrides the corrected default in `user_config.py`.

That is not hypothetical. `hard__bookmyshow__005` renders `[cinema]`, and the machine-local
config kept `cinema: INOX Bhubaneswar` — not a real BookMyShow listing — for weeks after the
repo was "fixed in all five places": default in `user_config.py`, `user_config.example`,
`public_vars.local.env`, `tasks_vars.local.env`, and the `hf_release` copies. The missing
fifth place was the gitignored file the runner actually reads, so every run still searched a
cinema that does not exist. One whole 13-row re-run was staged against that value before it
was caught here.

The task's `[placeholder]` slots survive into the goal verbatim and their values are passed
separately ("Your Task Variables"), so *this dict* — not the rendered prompt — is what the
agent is given. Print it, check it, and fail loudly rather than spending hours on a batch
that cannot succeed.

Usage
-----
    uv run python scripts/tools/verify_task_vars.py \
        --dataset benchmarks/androidlife-530/AndroidLife_public_v2.json \
        --task-id hard__bookmyshow__005

Exit 0 if every placeholder resolves and no value is known-bad, else 1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from androidlife.task_dataset import load_dataset, select_tasks
from androidlife.user_config import load_user_config, var_map

# Values that resolve cleanly but are known to be wrong for the task that uses them.
# Keep this list short and evidence-backed: each entry should name what it should be
# instead, so the fix is obvious from the message.
KNOWN_BAD: dict[str, str] = {
    # `hard__bookmyshow__005` — BookMyShow's search only matched the literal string once
    # and returned "Sorry! No result found" (row 12, ui_states/0003); its Bhubaneswar
    # cinemas are `INOX: Symphony Mall`, `INOX: DN Regalia Mall`, `INOX: BMC Bhawani Mall`.
    "cinema": "INOX Bhubaneswar",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, help="Exported public dataset JSON.")
    ap.add_argument("--task-id", required=True, help="Task whose placeholders should be resolved.")
    ap.add_argument("--config", default=None,
                    help="Config to resolve against (default: the runner's own default, config/user.yaml).")
    args = ap.parse_args()

    tasks = select_tasks(load_dataset(Path(args.dataset)), task_ids=[args.task_id])
    if not tasks:
        print(f"FAIL: {args.task_id} is not in {args.dataset}", file=sys.stderr)
        return 1
    task = tasks[0]

    variables = var_map(load_user_config(args.config) if args.config else load_user_config())
    placeholders = task.get("placeholders") or []
    resolved = {ph: variables.get(ph) for ph in placeholders}

    problems: list[str] = []
    for ph, value in resolved.items():
        shown = "<UNRESOLVED>" if value is None else repr(value)
        print(f"  {ph} = {shown}")
        if value is None:
            problems.append(f"{ph!r} has no value (the runner would abort before starting)")
        elif KNOWN_BAD.get(ph) == value:
            problems.append(f"{ph!r} = {value!r} is known-bad - use a real value instead")

    if not placeholders:
        print("  (task has no placeholders)")

    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        print(f"FAIL: {args.task_id} resolved task vars are unusable", file=sys.stderr)
        return 1

    print(f"OK: {args.task_id} task vars resolve cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
