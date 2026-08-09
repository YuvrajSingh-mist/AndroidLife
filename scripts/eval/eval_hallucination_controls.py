#!/usr/bin/env python3
"""Run the DeepEval/GEval hallucination-control judge over run folders.

Every control in ``hallucination_controls.json`` whose run folder exists under
``--runs`` is judged with DeepEval's ``HallucinationMetric``: the run's reason
is compared against the control's ``absence`` text, producing a score, an
honest/not-honest verdict, and a judge explanation. This makes the per-control
hallucination audit reproducible by anyone (no reading report internals).

Classification follows the report convention:
  - run reports success  AND judge says reason is NOT faithful  -> hallucination
  - otherwise                                                  -> true_failure

Usage:
  uv run scripts/eval_hallucination_controls.py \\
      --runs assets/runs/full-bench/2026-08-06-030706/day2 \\
      --hallucination-controls benchmarks/dailyBench-600/hallucination_controls.json \\
      --model gpt-5.4-mini \\
      --out reports/metrics/hallucination-eval.json \\
      --out-md reports/metrics/hallucination-eval.md

Exit code 0 on success, 1 if no control runs were found or any judge call failed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from DailyBench.hallucination_judge import DEFAULT_JUDGE_MODEL, JudgeResult, judge_control_honesty
from dailybench_report import discover_run_folders, parse_task_id_from_label

DEFAULT_CONTROLS = ROOT / "benchmarks" / "dailyBench-600" / "hallucination_controls.json"


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _collect_control_runs(runs_arg: str, controls: dict) -> list[dict]:
    """Map each control task_id to its run folder + output, when a run exists."""
    items: list[dict] = []
    for run_dir in discover_run_folders(runs_arg):
        meta = _read_json(run_dir / "meta.json") or {}
        output = _read_json(run_dir / "output.json") or {}
        task_id = meta.get("task_id") or parse_task_id_from_label(meta.get("label", ""))
        if not task_id or task_id not in controls:
            continue
        items.append(
            {
                "task_id": task_id,
                "run_dir": str(run_dir),
                "success": bool(output.get("success")),
                "reason": output.get("reason") or "",
                "control": controls[task_id],
            }
        )
    return items


def _classify(run_success: bool, judge: JudgeResult) -> str:
    if judge.error or judge.honest is False and run_success:
        return "hallucination" if run_success else "true_failure"
    return "true_failure" if not run_success else "true_success"


def _render_markdown(items: list[dict]) -> str:
    lines = [
        "# Hallucination-control judge report (DeepEval HallucinationMetric)",
        "",
        f"- controls judged: {len(items)}  ·  judge model: {items[0]['judge'].model if items else '-'}",
        "",
        "| task_id | success flag | score | honest | classification | judge reason |",
        "|---|---|---|---|---|---|",
    ]
    for item in items:
        judge = item["judge"]
        reason = (judge.reason or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {item['task_id']} | {item['success']} | {judge.score:.2f} | {judge.honest} "
            f"| {item['classification']} | {reason} |"
        )
    lines.append("")
    lines.append("Notes: score is DeepEval's hallucination score (0 = no contradiction, 1 = full).")
    lines.append("`honest=True` means the reason faithfully acknowledges the absence.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DeepEval hallucination-control judge over run folders.")
    parser.add_argument("--runs", default=None, help="Run batch dir or glob of run folders (default: walks assets/runs/).")
    parser.add_argument("--hallucination-controls", default=str(DEFAULT_CONTROLS), help="task_id -> control meta sidecar.")
    parser.add_argument("--model", default=None, help=f"Judge model (default: env DEEPEVAL_HALLUCINATION_JUDGE_MODEL / OPENAI_MODEL_NAME, else {DEFAULT_JUDGE_MODEL}).")
    parser.add_argument("--out", default="reports/metrics/hallucination-eval.json", help="JSON output path.")
    parser.add_argument("--out-md", default="reports/metrics/hallucination-eval.md", help="Markdown output path.")
    args = parser.parse_args()

    controls = _read_json(Path(args.hallucination_controls)) or {}
    if not controls:
        print(f"No controls found in {args.hallucination_controls}.", file=sys.stderr)
        return 1

    items = _collect_control_runs(args.runs, controls)
    if not items:
        print("No run folders matched any hallucination control. Check --runs.", file=sys.stderr)
        return 1

    had_error = False
    for item in items:
        judge = judge_control_honesty(
            item["reason"],
            item["control"],
            model=args.model,
            include_reason=True,
        )
        item["judge"] = judge
        item["classification"] = _classify(item["success"], judge)
        if judge.error:
            had_error = True
            print(f"warning: judge failed for {item['task_id']}: {judge.error}", file=sys.stderr)

    out_payload = {
        "model": items[0]["judge"].model,
        "count": len(items),
        "controls": [
            {
                "task_id": item["task_id"],
                "run_dir": item["run_dir"],
                "success_flag": item["success"],
                "score": item["judge"].score,
                "honest": item["judge"].honest,
                "classification": item["classification"],
                "judge_reason": item["judge"].reason,
                "run_reason": item["reason"],
            }
            for item in items
        ],
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(_render_markdown(items), encoding="utf-8")
    print(_render_markdown(items))
    print(f"Wrote {args.out} and {args.out_md}.")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
