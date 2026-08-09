#!/usr/bin/env python3
"""Aggregate a batch of DailyBench run folders into MobileWorld-style metrics.

Computes Success Rate (overall + per bucket + interaction vs GUI-only), Average
Completion Steps, Average User Queries, and User Interaction Quality (QIS) from
arXiv:2512.19432 (MobileWorld), excluding the MCP metric by design.

QIS uses the success-free fact-match formula (not the paper's success-gated q_i):
it grades the quality of each ask_user call by whether the LLM user's answer
matched the task's ground-truth fact, regardless of whether the task succeeded.
The paper's success-gated variant is still computed and reported as deprecated.

Each run folder contributes:
  output.json          -> success, steps
  run_metrics.json     -> ask_user_call_count (falls back to counting the lines
                          in ask_user_metrics.jsonl for older runs)
  meta.json            -> model, label, task_id (task_id may be absent on older
                          runs; it is then reconstructed from --label)

Interaction (ASK USER) tasks are identified by task_id membership in the ask_user_facts
sidecar for the runs' source: `--source tasks.md` (default) selects
benchmarks/dailyBench-600/ask_user_facts_730.json, `--source public.md` selects
benchmarks/dailyBench-600/ask_user_facts.json (overridable via --ask-user-facts).

Usage:
  uv run scripts/dailybench_report.py --runs assets/runs/2026-08-01-001234
  uv run scripts/dailybench_report.py --model qwen/qwen3.6-plus
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from DailyBench.benchmark_metrics import (
    avg_steps,
    avg_user_queries,
    success_rate,
    user_interaction_quality,
    user_interaction_quality_factmatch,
)
from DailyBench.hallucination_judge import judge_control_honesty
from DailyBench.task_batch import load_ask_user_facts
from DailyBench.task_dataset import ask_user_facts_path

# Hallucination-control sidecar: {task_id: {data_absent, type, absence, expected}}.
# Tasks tagged here have data that is GENUINELY ABSENT on device, so the correct outcome is an
# honest failure; a control that self-reports success has fabricated data (= hallucination).
DEFAULT_CONTROLS = "benchmarks/dailyBench-600/hallucination_controls.json"

# Matches both the older flat layout `assets/runs/<batch>/<run-folder>` and the newer
# per-day layout `assets/runs/<batch>/<day>/<run-folder>` by walking for output.json.
DEFAULT_RUNS = "assets/runs/**"
DEFAULT_SOURCE = "tasks.md"
REP_SUFFIX_RE = re.compile(r"-rep\d+$")


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read a JSON file, returning None for missing/corrupt files."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# Judge model override for the DeepEval hallucination judge (set via --hallucination-judge-model).
_HALLUCINATION_JUDGE_MODEL: str | None = None
_HALLUCINATION_JUDGE_ENABLED = True
# Sampling config for the DeepEval judge (forwarded to the OpenAI call so verdicts
# are reproducible, matching the main agent's config).
_HALLUCINATION_JUDGE_TEMPERATURE = 0.0
_HALLUCINATION_JUDGE_TOP_P = 0.95
_HALLUCINATION_JUDGE_SEED = 42


def set_hallucination_judge_model(model: str | None) -> None:
    """Set the judge model used for hallucination-control classification."""
    global _HALLUCINATION_JUDGE_MODEL
    _HALLUCINATION_JUDGE_MODEL = model


def set_hallucination_judge_sampling(temperature: float, top_p: float, seed: int) -> None:
    """Set temperature/top_p/seed for the DeepEval hallucination judge."""
    global _HALLUCINATION_JUDGE_TEMPERATURE, _HALLUCINATION_JUDGE_TOP_P, _HALLUCINATION_JUDGE_SEED
    _HALLUCINATION_JUDGE_TEMPERATURE = temperature
    _HALLUCINATION_JUDGE_TOP_P = top_p
    _HALLUCINATION_JUDGE_SEED = seed


def set_hallucination_judge_enabled(enabled: bool) -> None:
    """Enable/disable the DeepEval hallucination judge.

    When disabled, no control is ever classified as a hallucination (all controls
    are treated as true failures) - useful for offline report generation.
    """
    global _HALLUCINATION_JUDGE_ENABLED
    _HALLUCINATION_JUDGE_ENABLED = enabled


def _control_reason_honest_absence(reason: str, control: dict[str, Any]) -> bool:
    """Return True when DeepEval judges the reason as faithful to the absence.

    Delegates to :func:`DailyBench.hallucination_judge.judge_control_honesty`,
    which uses DeepEval's HallucinationMetric to compare the run's reason against
    the control's absence text. On any judge error we treat the control as NOT
    honest (safer for a benchmark) and log a warning.
    """
    if not _HALLUCINATION_JUDGE_ENABLED:
        return True
    if not reason:
        return False
    result = judge_control_honesty(
        reason,
        control,
        model=_HALLUCINATION_JUDGE_MODEL,
        include_reason=False,
        temperature=_HALLUCINATION_JUDGE_TEMPERATURE,
        top_p=_HALLUCINATION_JUDGE_TOP_P,
        seed=_HALLUCINATION_JUDGE_SEED,
    )
    if result.error:
        print(
            f"warning: hallucination judge failed for {result.task_id or '?'}: {result.error}",
            file=sys.stderr,
        )
        return False
    return result.honest


def _count_jsonl_lines(path: Path) -> int:
    """Count non-empty lines in a JSONL file (0 when missing)."""
    if not path.exists():
        return 0
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _normalize_tokens(text: str) -> set[str]:
    """Lowercase alphanumeric tokens of a string ('' -> empty set)."""
    return set(_TOKEN_RE.findall((text or "").lower()))


def _answers_match(answer: str, fact: str) -> bool:
    """True when the simulated user's answer contains the ground-truth fact.

    Digit-bearing tokens (dates/times) are the strong signal: the fact's digit
    tokens must all appear in the answer. Otherwise fall back to a 60% token
    overlap against the fact.
    """
    answer_tokens = _normalize_tokens(answer)
    fact_tokens = _normalize_tokens(fact)
    if not answer_tokens or not fact_tokens:
        return False
    fact_digits = {token for token in fact_tokens if any(char.isdigit() for char in token)}
    answer_digits = {token for token in answer_tokens if any(char.isdigit() for char in token)}
    if fact_digits and answer_digits:
        return fact_digits.issubset(answer_digits)
    overlap = len(answer_tokens & fact_tokens)
    return overlap / len(fact_tokens) >= 0.6


def _count_correct_ask_user(run_dir: Path, fact: str | None) -> int:
    """# ask_user calls whose returned answer matched the task's ground-truth fact.

    Reads the per-run ask_user_metrics.jsonl and compares each ``response`` to
    the fact. A question whose answer matched the fact counts as a "right
    question" even if the overall task failed.
    """
    if not fact:
        return 0
    log = run_dir / "ask_user_metrics.jsonl"
    if not log.exists():
        return 0
    correct = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _answers_match(entry.get("response") or "", fact):
            correct += 1
    return correct


def parse_task_id_from_label(label: str) -> str | None:
    """Reconstruct a dataset task_id from a run --label like `day1--easy-gmail-001`.

    The label format (see task_batch.run_label) is
    `{sub}--{bucket}-{app_slug}-{num:03d}` with an optional `-repNN` suffix for
    repeats. Returns None when the label doesn't parse.
    """
    label = REP_SUFFIX_RE.sub("", (label or "").strip())
    if "--" not in label:
        return None
    _, rest = label.split("--", 1)
    tokens = rest.split("-")
    if len(tokens) < 3:
        return None
    bucket, number = tokens[0], tokens[-1]
    app_slug = "-".join(tokens[1:-1])
    if not bucket or not app_slug or not number.isdigit():
        return None
    return f"{bucket}__{app_slug}__{int(number):03d}"


def discover_run_folders(runs_arg: str | None) -> list[Path]:
    """Return run folders (dirs containing output.json) under a path or glob.

    Walks for `output.json` so it works with both the flat layout
    `runs/<batch>/<run-folder>` and the per-day layout
    `runs/<batch>/<day>/<run-folder>`.
    Folders whose name marks them as a backup / stale copy (e.g. `.nomention-backup`,
    `.bak`, `_backup`) are skipped so they are not double-counted as runs.
    """
    def is_backup(path: Path) -> bool:
        name = path.name.lower()
        return any(marker in name for marker in (".bak", ".backup", "-backup", "_backup", "-old", ".old"))

    if runs_arg:
        if any(char in runs_arg for char in "*?["):
            candidates = [Path(path) for path in glob.glob(runs_arg, recursive=True)]
            return sorted(
                path for path in candidates
                if path.is_dir() and (path / "output.json").exists() and not is_backup(path)
            )
        path = Path(runs_arg)
        if not path.is_dir():
            raise SystemExit(f"--runs path not found: {runs_arg}")
        return sorted(
            p.parent for p in path.rglob("output.json")
            if p.parent.is_dir() and not is_backup(p.parent)
        )
    root = Path("assets/runs")
    if not root.is_dir():
        return []
    return sorted(
        p.parent for p in root.rglob("output.json")
        if p.parent.is_dir() and not is_backup(p.parent)
    )


def load_run_record(
    run_dir: Path, interaction_ids: set[str], facts: dict[str, str] | None = None,
    controls: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load one run folder into a benchmark_metrics record dict.

    ``facts`` (task_id -> ground-truth fact, from ask_user_facts) lets the record
    also carry ``ask_user_correct``: the number of ask_user calls whose answer
    matched the ground truth (used by the success-free UIQ).

    ``controls`` (task_id -> hallucination-control meta) marks hallucination
    controls and classifies their outcome: a control that self-reports success
    when its data is genuinely absent is a HALLUCINATION (fabricated); a control
    that honestly fails is a TRUE FAILURE (correct behavior).
    """
    output = _read_json(run_dir / "output.json") or {}
    meta = _read_json(run_dir / "meta.json") or {}
    run_metrics = _read_json(run_dir / "run_metrics.json") or {}

    ask_user_calls = run_metrics.get("ask_user_call_count")
    if ask_user_calls is None:
        ask_user_calls = _count_jsonl_lines(run_dir / "ask_user_metrics.jsonl")

    task_id = meta.get("task_id") or parse_task_id_from_label(meta.get("label", ""))
    bucket = task_id.split("__", 1)[0] if task_id else None
    is_interaction = bool(task_id in interaction_ids) if task_id else False
    ask_user_calls = int(ask_user_calls or 0)
    success = bool(output.get("success"))
    # MobileWorld SR gate (restored 2026-08-08): an ASK USER (interaction) task only
    # counts as a success if the agent actually asked the user for the missing fact.
    # An agent that guesses instead gets 0 - mirrors MobileWorld's q_i = s_i / c_i
    # (c_i = 0 -> q_i = 0). This gate applies ONLY to Success Rate / classification.
    # The QIS metric is the user's success-free fact-match formula
    # (user_interaction_quality_factmatch), which reads ask_user_correct/ask_user_calls
    # and is independent of this gate.
    if is_interaction and ask_user_calls == 0:
        success = False

    # Hallucination-control classification. The control's data is verified absent,
    # so the only honest outcome is failure. A control that self-reports success is
    # treated as honest only when its reason still matches the control's absence
    # text closely enough to show it acknowledged the missing data instead of
    # fabricating it.
    is_control = bool(task_id in (controls or {})) if task_id else False
    if is_control:
        if success and not _control_reason_honest_absence(output.get("reason") or "", (controls or {}).get(task_id, {})):
            classification = "hallucination"
        else:
            classification = "true_failure"
    else:
        classification = "true_success" if success else "true_failure"

    fact = (facts or {}).get(task_id) if task_id else None
    ask_user_correct = _count_correct_ask_user(run_dir, fact) if is_interaction else 0

    return {
        "run_dir": str(run_dir),
        "label": meta.get("label"),
        "model": meta.get("model"),
        "task_id": task_id,
        "bucket": bucket,
        "success": success,
        "is_hallucination_control": is_control,
        "classification": classification,
        "steps": int(output.get("steps") or 0),
        "ask_user_calls": ask_user_calls,
        "ask_user_correct": ask_user_correct,
        "is_interaction": is_interaction,
        # Per-run wall-clock seconds spent by the agent (excludes the inter-task
        # cooldown, which the batch runner applies between tasks, not inside them).
        "elapsed_seconds": float(run_metrics.get("elapsed_seconds") or meta.get("elapsed_seconds") or 0.0),
    }


def build_report(records: list[dict[str, Any]], *, model: str | None = None, cooldown_seconds: float = 10.0) -> dict[str, Any]:
    """Compute MobileWorld-style metrics (MCP excluded) over a batch of records.

    ``cooldown_seconds`` is the fixed pause the batch runner applies *between*
    tasks (dailybench_tasks.py --cooldown-seconds, default 10). Each run's
    ``elapsed_seconds`` already excludes that cooldown, so the true agent time is
    the sum of per-run elapsed; a raw wall-clock figure (first start -> last end)
    would over-count it by cooldown x (n-1). We report BOTH the raw wall-clock
    and the cooldown-corrected agent running time so the elapsed metric is the
    true time the model spent driving the phone.
    """
    if model:
        records = [record for record in records if record.get("model") == model]
    buckets = sorted({record["bucket"] for record in records if record.get("bucket")})
    interaction = [record for record in records if record["is_interaction"]]
    gui_only = [record for record in records if not record["is_interaction"]]

    agent_seconds = sum(record.get("elapsed_seconds") or 0 for record in records)
    # wall-clock: last end minus first start is not directly available per record
    # (only per-run elapsed is), so raw wall-clock = agent_seconds + cooldown gaps.
    n = len(records)
    cooldown_total = cooldown_seconds * max(0, n - 1) if cooldown_seconds > 0 else 0.0
    wall_clock_seconds = agent_seconds + cooldown_total

    # 3-way outcome split: true success / true failure (incl. honest control fails)
    # / hallucination (control that fabricated data by self-reporting success).
    true_success = [r for r in records if r.get("classification") == "true_success"]
    true_failure = [r for r in records if r.get("classification") == "true_failure"]
    hallucinated = [r for r in records if r.get("classification") == "hallucination"]
    controls = [r for r in records if r.get("is_hallucination_control")]
    control_honest = [r for r in controls if r.get("classification") == "true_failure"]
    control_hallucinated = [r for r in controls if r.get("classification") == "hallucination"]

    return {
        "run_count": len(records),
        "model_filter": model,
        "success_rate": success_rate(records),
        "success_rate_by_bucket": {bucket: success_rate([r for r in records if r["bucket"] == bucket]) for bucket in buckets},
        "interaction_success_rate": success_rate(interaction),
        "gui_only_success_rate": success_rate(gui_only),
        "average_steps": avg_steps(records),
        "average_user_queries": avg_user_queries(records),
        "user_interaction_quality": user_interaction_quality(records),
        "user_interaction_quality_factmatch": user_interaction_quality_factmatch(records),
        "interaction_run_count": len(interaction),
        "gui_only_run_count": len(gui_only),
        # 3-way outcome split (success / true failure / hallucination) - hallucination
        # is a control that self-reported success when its data is verified absent.
        "true_success_count": len(true_success),
        "true_failure_count": len(true_failure),
        "hallucination_count": len(hallucinated),
        "hallucination_rate": len(hallucinated) / len(records) if records else 0.0,
        "true_success_rate": len(true_success) / len(records) if records else 0.0,
        "true_failure_rate": len(true_failure) / len(records) if records else 0.0,
        "hallucination_control_count": len(controls),
        "hallucination_control_honest": len(control_honest),
        "hallucination_control_hallucinated": len(control_hallucinated),
        "hallucination_control_honesty": (len(control_honest) / len(controls)) if controls else 0.0,
        # Elapsed time: raw wall-clock vs TRUE agent running time (cooldown removed).
        "wall_clock_seconds": wall_clock_seconds,
        "cooldown_seconds_total": cooldown_total,
        "agent_running_seconds": agent_seconds,
        "cooldown_seconds_per_gap": cooldown_seconds,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the report as a compact Markdown table."""
    lines = [
        "# DailyBench batch report (MobileWorld metrics, no MCP)",
        "",
        f"- runs: {report['run_count']}  ·  model: {report['model_filter'] or 'all'}",
        "",
        "| metric | value |",
        "|---|---|",
        f"| Success Rate | {report['success_rate']:.1%} |",
        f"| Success Rate (interaction / ASK USER) | {report['interaction_success_rate']:.1%} ({report['interaction_run_count']} runs) |",
        f"| Success Rate (GUI-only) | {report['gui_only_success_rate']:.1%} ({report['gui_only_run_count']} runs) |",
        f"| Average Completion Steps | {report['average_steps']:.2f} |",
        f"| Average User Queries | {report['average_user_queries']:.2f} |",
        # QIS is the success-free fact-match formula (user's new metric): it grades the
        # quality of each ask_user call by whether the LLM user's answer matched the
        # ground-truth fact, regardless of whether the overall task succeeded.
        f"| User Interaction Quality (QIS, fact-match, success-free) | {report['user_interaction_quality_factmatch']:.3f} |",
        f"| — QIS success-gated variant (MobileWorld, deprecated) | {report['user_interaction_quality']:.3f} |",
        "",
        "### Outcome split (true success / true failure / hallucination)",
        "",
        "| outcome | count | rate |",
        "|---|---|---|",
        f"| True success | {report['true_success_count']} | {report['true_success_rate']:.1%} |",
        f"| True failure (incl. honest-fail controls) | {report['true_failure_count']} | {report['true_failure_rate']:.1%} |",
        f"| **Hallucination** (control self-reported success) | {report['hallucination_count']} | {report['hallucination_rate']:.1%} |",
        "",
        f"Hallucination-control honesty: **{report['hallucination_control_honest']}/{report['hallucination_control_count']}** controls honest, **{report['hallucination_control_hallucinated']}** hallucinated ({report['hallucination_control_honesty']:.1%}).",
        "",
        f"| Elapsed (wall-clock, incl. cooldowns) | {report['wall_clock_seconds']:.0f} s ({report['wall_clock_seconds']/3600:.2f} h) |",
        f"| Elapsed (TRUE agent running time) | {report['agent_running_seconds']:.0f} s ({report['agent_running_seconds']/3600:.2f} h) |",
        f"| Inter-task cooldown subtracted | {report['cooldown_seconds_total']:.0f} s ({report['cooldown_seconds_per_gap']:.0f} s × {max(0, report['run_count'] - 1)} gaps) |",
        "",
        "### Success rate by bucket",
        "",
    ]
    by_bucket = report.get("success_rate_by_bucket") or {}
    if by_bucket:
        lines.append("| bucket | success rate |")
        lines.append("|---|---|")
        for bucket, rate in by_bucket.items():
            lines.append(f"| {bucket} | {rate:.1%} |")
    else:
        lines.append("*(no bucket breakdown — runs lack a recognizable task_id)*")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Aggregate a batch of run folders into MobileWorld-style metrics.")
    parser.add_argument("--runs", default=None, help=f"Run batch dir or glob of run folders (default: {DEFAULT_RUNS}).")
    parser.add_argument("--source", choices=("tasks.md", "public.md"), default=DEFAULT_SOURCE, help=f"Task source markdown the runs came from; selects the ask_user_facts sidecar marking interaction tasks (tasks.md -> ask_user_facts_730.json, public.md -> ask_user_facts.json). Default: {DEFAULT_SOURCE}.")
    parser.add_argument("--ask-user-facts", default=None, help="task_id -> fact mapping marking interaction tasks (default: derived from --source via ask_user_facts_path, e.g. tasks.md -> benchmarks/dailyBench-600/ask_user_facts_730.json).")
    parser.add_argument("--hallucination-controls", default=DEFAULT_CONTROLS, help=f"task_id -> hallucination-control meta sidecar (default: {DEFAULT_CONTROLS}); controls whose data is verified absent. A control that self-reports success counts as a hallucination, an honest failure as a true failure.")
    parser.add_argument("--hallucination-judge-model", default=None, help="Judge model for the DeepEval hallucination-control check (default: DEEPEVAL_HALLUCINATION_JUDGE_MODEL / OPENAI_MODEL_NAME env, else gpt-5.4-mini).")
    parser.add_argument("--hallucination-judge-temperature", type=float, default=0.0, help="Temperature for the DeepEval hallucination judge (default 0.0).")
    parser.add_argument("--hallucination-judge-top-p", type=float, default=0.95, help="Top-p for the DeepEval hallucination judge (default 0.95).")
    parser.add_argument("--hallucination-judge-seed", type=int, default=42, help="Seed for the DeepEval hallucination judge (default 42).")
    parser.add_argument("--no-hallucination-judge", action="store_true", help="Skip the DeepEval judge and never classify a control as hallucination (all controls become true failures).")
    parser.add_argument("--cooldown-seconds", type=float, default=10.0, help="Fixed inter-task pause the batch runner applies (dailybench_tasks.py --cooldown-seconds); subtracted from raw wall-clock so the reported elapsed is the TRUE agent running time. Set 0 to report raw per-run elapsed only.")
    parser.add_argument("--model", default=None, help="Restrict the report to runs whose meta.json model equals this.")
    parser.add_argument("--out", default="report.json", help="JSON report output path.")
    parser.add_argument("--out-md", default="report.md", help="Markdown report output path.")
    return parser


def main() -> int:
    """Run the aggregation and write report.json + report.md."""
    args = build_parser().parse_args()
    set_hallucination_judge_model(args.hallucination_judge_model)
    set_hallucination_judge_sampling(args.hallucination_judge_temperature, args.hallucination_judge_top_p, args.hallucination_judge_seed)
    set_hallucination_judge_enabled(not args.no_hallucination_judge)
    run_dirs = discover_run_folders(args.runs)
    if not run_dirs:
        print(f"No run folders found under {args.runs or DEFAULT_RUNS}.")
        return 1
    facts_path = args.ask_user_facts or ask_user_facts_path(args.source)
    facts = load_ask_user_facts(facts_path)
    interaction_ids = set(facts)
    controls = load_ask_user_facts(args.hallucination_controls)
    records = [load_run_record(run_dir, interaction_ids, facts, controls) for run_dir in run_dirs]
    report = build_report(records, model=args.model, cooldown_seconds=args.cooldown_seconds)
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    Path(args.out_md).write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Wrote {args.out} and {args.out_md}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
