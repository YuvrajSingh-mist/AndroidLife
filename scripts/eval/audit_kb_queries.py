#!/usr/bin/env python3
"""Manual KBIQ audit helper — walk a run batch's KB (multi-turn) ask_user queries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from DailyBench.task_batch import load_json_object
from DailyBench.task_dataset import multiturn_kb_path


def collect_kb_queries(run_dirs: list[Path], kb_ids: set[str]) -> list[tuple[Path, str, list[dict]]]:
    """Return [(run_dir, task_id, [query entries])] for every KB task run that asked."""
    out: list[tuple[Path, str, list[dict]]] = []
    for run_dir in run_dirs:
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        task_id = meta.get("task_id")
        if task_id not in kb_ids:
            continue
        log = run_dir / "ask_user_metrics.jsonl"
        if not log.exists():
            continue
        queries = []
        for line in log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            queries.append({
                "question": (entry.get("request") or {}).get("framework_prompt", "").strip(),
                "answer": (entry.get("response") or "").strip(),
                "turn": entry.get("turn_number"),
            })
        if queries:
            out.append((run_dir, task_id, queries))
    return out


def discover_run_dirs(runs_arg: str) -> list[Path]:
    import glob
    candidates = [Path(p) for p in glob.glob(runs_arg, recursive=True)]
    return sorted(p for p in candidates if p.is_dir() and (p / "output.json").exists())


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual KBIQ audit helper for KB/multi-turn ask_user queries.")
    parser.add_argument("--runs", required=True, help="Glob of run folders, e.g. 'assets/runs/public/<date>/*'.")
    parser.add_argument("--source", choices=("tasks.md", "public.md"), default="public.md",
                        help="Task source the runs came from (selects the multiturn KB sidecar).")
    parser.add_argument("--kb", default=None, help="Override the multiturn KB file path.")
    parser.add_argument("--list", action="store_true", help="Print every KB query for manual judgement (no prompts).")
    parser.add_argument("--interactive", action="store_true", help="Prompt for each query's correctness (y/n).")
    args = parser.parse_args()

    kb_path = args.kb or multiturn_kb_path(args.source)
    kb_ids = set(load_json_object(kb_path))
    run_dirs = discover_run_dirs(args.runs)
    if not run_dirs:
        print(f"No run folders matched {args.runs!r}")
        return 1

    batches = collect_kb_queries(run_dirs, kb_ids)
    if not batches:
        print("No KB (multi-turn) task runs with ask_user queries found.")
        return 0

    total = sum(len(q) for _, _, q in batches)
    print(f"KB profile: {kb_path}  ·  {len(kb_ids)} KB tasks  ·  {len(batches)} runs asked  ·  {total} queries\n")

    for run_dir, task_id, queries in batches:
        print(f"===== {run_dir}  ({task_id}, {len(queries)} query/ies) =====")
        for i, q in enumerate(queries, 1):
            print(f"  [{i}] turn {q['turn']}: {q['question'][:160]}")
            print(f"      -> {q['answer'][:160]}")
            if args.interactive:
                verdict = input("      correct? [Y/n] ").strip().lower()
                q["correct"] = verdict not in ("n", "no")
            elif args.list:
                q["correct"] = None
        if args.interactive:
            audit_path = run_dir / "kb_audit.json"
            audit_path.write_text(json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            right = sum(1 for q in queries if q.get("correct"))
            print(f"  -> wrote {audit_path}  ({right}/{len(queries)} right)\n")
        else:
            print()

    if args.interactive:
        print("Audit complete. Re-run the report with the same --runs to pick up the kb_audit.json files (KBIQ row).")
    else:
        print("Run with --interactive to record correctness (writes <run>/kb_audit.json).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
