#!/usr/bin/env python3
"""Run the full-context hallucination-control judge over run folders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from DailyBench.hallucination_judge import (
    DEFAULT_JUDGE_MODEL,
    JudgeResult,
    judge_control_full_context,
    read_agent_log,
    resolve_control,
)
from DailyBench.jsonutils import read_json
from DailyBench.user_config import load_user_config, parse_flat_config
from dailybench_report import discover_run_folders, parse_task_id_from_label

DEFAULT_CONTROLS = ROOT / "benchmarks" / "dailyBench-600" / "hallucination_controls.json"
   

def _load_task_prompts(dataset_arg: str | None) -> dict[str, str]:
    """Load task_id -> prompt_text from an exported dataset JSON (for judge context)."""
    if not dataset_arg:
        return {}
    d = read_json(Path(dataset_arg))
    if d is None:
        print(f"warning: could not load --dataset {dataset_arg}", file=sys.stderr)
        return {}
    tasks = d.get("tasks") if isinstance(d, dict) else d
    if not isinstance(tasks, list):
        return {}
    return {
        t.get("task_id", ""): str(t.get("prompt_text") or t.get("instruction") or "")
        for t in tasks
        if isinstance(t, dict) and t.get("task_id")
    }


def _collect_control_runs(runs_arg: str, controls: dict, cfg: dict[str, str], prompts: dict[str, str] | None = None) -> list[dict]:
    """Map each control task_id to its run folder + output, when a run exists."""
    prompts = prompts or {}
    items: list[dict] = []
    for run_dir in discover_run_folders(runs_arg):
        meta = read_json(run_dir / "meta.json") or {}
        output = read_json(run_dir / "output.json") or {}
        task_id = meta.get("task_id") or parse_task_id_from_label(meta.get("label", ""))
        if not task_id or task_id not in controls:
            continue
        control = resolve_control(controls[task_id], cfg)
        if task_id in prompts and not control.get("prompt_text"):
            control["prompt_text"] = prompts[task_id]
        items.append(
            {
                "task_id": task_id,
                "run_dir": str(run_dir),
                "success": bool(output.get("success")),
                "reason": output.get("reason") or "",
                "control": control,
            }
        )
    return items


def _classify(run_success: bool, judge: JudgeResult) -> str:
    """Control outcome per the report convention.

    A control's data is verified absent, so a self-reported success that the
    judge flags as NOT honest is a hallucination; every other control outcome
    is a true failure (honest-fail controls are the *correct* behavior and are
    re-labelled true-success by the report layer, not here).
    """
    if judge.error or (judge.honest is False and run_success):
        return "hallucination" if run_success else "true_failure"
    return "true_failure" if not run_success else "true_success"


def _aggregate_usage(items: list[dict]) -> dict[str, Any]:
    """Sum judge LLM usage/cost/elapsed across all judged controls (best-effort)."""
    keys = ("prompt_tokens", "completion_tokens", "total_tokens", "elapsed_ms")
    agg: dict[str, Any] = {k: sum(getattr(j["judge"], k) or 0 for j in items) for k in keys}
    costs = [j["judge"].cost_usd for j in items if j["judge"].cost_usd is not None]
    agg["cost_usd"] = round(sum(costs), 6) if costs else None
    agg["cost_details"] = "estimated from runtime pricing catalog" if costs else "not available (no published rate or no usage)"
    return agg


def _render_markdown(items: list[dict]) -> str:
    judge_name = items[0]["judge"].model if items and items[0]["judge"].model else "-"
    usage = _aggregate_usage(items)
    cost = f"${usage['cost_usd']:.4f}" if usage["cost_usd"] is not None else "n/a"
    lines = [
        "# Hallucination-control judge report (full-context agent-log judge)",
        "",
        f"- controls judged: {len(items)}  ·  judge model: {judge_name}",
        f"- judge tokens: {usage['total_tokens']:,} ({usage['prompt_tokens']:,} prompt / {usage['completion_tokens']:,} completion)"
        f"  ·  cost: {cost}  ·  elapsed: {usage['elapsed_ms'] / 1000:.1f}s",
        "",
        "| task_id | success flag | hallucinated (1/0) | classification | judge explanation |",
        "|---|---|---|---|---|",
    ]
    for item in items:
        judge = item["judge"]
        hallu = judge.hallucinated if judge.hallucinated is not None else ("ERR" if judge.error else "-")
        reason = (judge.reason or judge.error or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {item['task_id']} | {item['success']} | {hallu} "
            f"| {item['classification']} | {reason} |"
        )
    lines.append("")
    lines.append("Notes: `hallucinated` is the judge's strict answer (1 = hallucinated, 0 = not).")
    lines.append("The judge reads the full agent.log.txt, not just the one-line reason.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the DeepEval hallucination-control judge over run folders.")
    parser.add_argument("--runs", default=None, help="Run batch dir or glob of run folders (default: walks assets/runs/).")
    parser.add_argument("--hallucination-controls", default=str(DEFAULT_CONTROLS), help="task_id -> control meta sidecar.")
    parser.add_argument("--dataset", default=None, help="Exported dataset JSON (e.g. benchmarks/dailyBench-600/DailyBench_public_v2.json) to pull each task's prompt_text as judge context.")
    parser.add_argument("--model", default=None, help=f"Judge model (default: env DEEPEVAL_HALLUCINATION_JUDGE_MODEL / OPENAI_MODEL_NAME, else {DEFAULT_JUDGE_MODEL}).")
    parser.add_argument("--sub", default="full-bench", choices=("full-bench", "public"),
                        help="Which metrics/hallucination subfolder to write into (full-bench or public). Default: full-bench.")
    parser.add_argument("--config", default=None, help="User config file (flat key: value), default config/user.yaml; resolved over shipped defaults.")
    parser.add_argument("--vars-file", default=None, help="Optional key=value vars file merged over --config (e.g. benchmarks/dailyBench-600/public_vars.local.env).")
    parser.add_argument("--out", default=None, help="JSON output path (default: reports/metrics/hallucination/<sub>/hallucination-eval.json).")
    parser.add_argument("--out-md", default=None, help="Markdown output path (default: reports/metrics/hallucination/<sub>/hallucination-eval.md).")
    args = parser.parse_args()

    sub_dir = Path("reports/metrics/hallucination") / args.sub
    out = Path(args.out) if args.out else sub_dir / "hallucination-eval.json"
    out_md = Path(args.out_md) if args.out_md else sub_dir / "hallucination-eval.md"

    controls = read_json(Path(args.hallucination_controls)) or {}
    if not controls:
        print(f"No controls found in {args.hallucination_controls}.", file=sys.stderr)
        return 1

    cfg = load_user_config(args.config)
    if args.vars_file:
        try:
            cfg.update(parse_flat_config(Path(args.vars_file).read_text(encoding="utf-8")))
        except OSError as exc:
            print(f"warning: could not read --vars-file {args.vars_file}: {exc}", file=sys.stderr)

    prompts = _load_task_prompts(args.dataset)
    items = _collect_control_runs(args.runs, controls, cfg, prompts)
    if not items:
        print("No run folders matched any hallucination control. Check --runs.", file=sys.stderr)
        return 1

    had_error = False
    for item in items:
        agent_log = read_agent_log(Path(item["run_dir"]))
        judge = judge_control_full_context(
            item["reason"],
            item["control"],
            agent_log,
            success=item["success"],
            model=args.model,
        )
        item["judge"] = judge
        item["classification"] = _classify(item["success"], judge)
        if judge.error:
            had_error = True
            print(f"warning: judge failed for {item['task_id']}: {judge.error}", file=sys.stderr)

    out_payload = {
        "judge": "full-context-agent-log",
        "model": items[0]["judge"].model,
        "count": len(items),
        "usage": _aggregate_usage(items),
        "controls": [
            {
                "task_id": item["task_id"],
                "run_dir": item["run_dir"],
                "success_flag": item["success"],
                "hallucinated": item["judge"].hallucinated,  # 1 = hallucinated, 0 = not
                "score": item["judge"].score,
                "honest": item["judge"].honest,
                "classification": item["classification"],
                "judge_reason": item["judge"].reason,
                "context_chars": item["judge"].context_tokens,
                "prompt_tokens": item["judge"].prompt_tokens,
                "completion_tokens": item["judge"].completion_tokens,
                "total_tokens": item["judge"].total_tokens,
                "cost_usd": item["judge"].cost_usd,
                "elapsed_ms": item["judge"].elapsed_ms,
                "run_reason": item["reason"],
            }
            for item in items
        ],
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text(_render_markdown(items), encoding="utf-8")
    print(_render_markdown(items))
    print(f"Wrote {out} and {out_md}.")
    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
