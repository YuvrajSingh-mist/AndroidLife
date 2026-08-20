"""MobileWorld-style benchmark metrics (arXiv:2512.19432, MCP metric excluded).

Implements the Success Rate, Average Completion Steps, Average User Queries, and
User Interaction Quality (UIQ) metrics from MobileWorld Section 4.2, operating on
per-run records produced by the DailyBench harness. The paper's Average MCP Tool
Calls metric is deliberately excluded.

A "record" is a dict with at least these fields (produced by
``scripts/eval/dailybench_report.py``):

    success: bool          # s_i in the paper: 1 if the task fully completed
    steps: int             # t_i: number of action steps in the trajectory
    ask_user_calls: int    # c_i: number of ask_user invocations
    is_interaction: bool   # True for ASK USER (agent-user interaction) tasks

Formulas (Section 4.2):

    SR            = (1/N) * sum(s_i)
    Ave. Steps    = (1/N) * sum(t_i)
    Ave. Queries  = (1/|I_interact|) * sum_{i in I_interact}(c_i)

User Interaction Quality (UIQ) is the **success-free fact-match** formula
(``user_interaction_quality_factmatch``): each interaction task contributes its
own ``c_i / q_i`` correctness ratio (fraction of its ``ask_user`` answers that
were the right question; 0 if it never asked), averaged over interaction tasks
plus GUI-only tasks that asked unnecessarily — so every interaction task is
weighted equally regardless of how many times it asked, and whole-task success
is deliberately ignored.
"""

from __future__ import annotations

from typing import Any, Iterable

Record = dict[str, Any]


def _mean(values: Iterable[float]) -> float:
    """Mean of a sequence; 0.0 when empty or all-None."""
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else 0.0


def _record_success(record: Record) -> bool:
    """Raw success flag, or classification-based success when present.

    When a record carries a ``classification`` (``true_success`` / ``true_failure``
    / ``hallucination``), only ``true_success`` counts as a success. This makes
    every rate classification-aware: hallucinated controls (self-reported
    success) and honest control failures never inflate Success Rate.
    """
    classification = record.get("classification")
    if classification is not None:
        return classification == "true_success"
    return bool(record["success"])


def success_rate(records: Iterable[Record]) -> float:
    """Success Rate: the proportion of tasks fully completed (formula 1).

    Classification-aware: hallucinated controls and honest control failures are
    not counted as successes (see :func:`_record_success`).
    """
    return _mean(1.0 if _record_success(record) else 0.0 for record in records)


def avg_steps(records: Iterable[Record]) -> float:
    """Average Completion Steps across all trajectories (formula 3)."""
    return _mean(record.get("steps", 0) for record in records)


def avg_user_queries(records: Iterable[Record]) -> float:
    """Average User Queries over interaction tasks only (formula 4).

    Non-interaction tasks are excluded from the denominator, matching the paper.
    """
    interaction = [record for record in records if record["is_interaction"]]
    return _mean(record.get("ask_user_calls", 0) for record in interaction)


def user_interaction_quality_factmatch(records: Iterable[Record]) -> float:
    """Success-free UIQ based on fact retrieval (not task success).

    A call is a "right question" if the simulated user's returned answer matched
    the task's ground-truth fact (``ask_user_correct``). Task completion is
    deliberately ignored: asking the right question counts even when the overall
    task failed for unrelated reasons (e.g. an alarm UI bug).

    Each interaction task contributes its **own** correctness ratio ``c_i / q_i``
    (the fraction of its ask_user calls that were the right question; 0 when it
    never asked), so every ASK USER task is weighted equally regardless of how
    many times it asked. The average is taken over interaction tasks plus
    GUI-only tasks that needlessly invoked ask_user.

        UIQ = sum_{i in I} (c_i / q_i) / (|I| + |T|)    # c_i/q_i := 0 if q_i = 0

    A never-asked interaction task contributes 0 to the numerator yet stays in
    the denominator, so skipping the ask is still penalized.
    """
    interaction = [record for record in records if record["is_interaction"]]
    numerator = 0.0
    for record in interaction:
        calls = record.get("ask_user_calls") or 0
        if calls > 0:
            numerator += (record.get("ask_user_correct") or 0) / calls
    triggered = sum(
        1
        for record in records
        if not record["is_interaction"] and (record.get("ask_user_calls") or 0) > 0
    )
    denominator = len(interaction) + triggered
    return (numerator / denominator) if denominator else 0.0


def kb_interaction_quality(records: Iterable[Record]) -> float:
    """KB Interaction Quality (KBIQ): the fraction of KB/multi-turn ask_user
    queries that returned the RIGHT answer according to the KB profile.

    A run's ``ask_user_metrics.jsonl`` records every KB query (question + oracle
    answer). Whether each answer was *right* is a manual judgement (the KB oracle
    is the source of truth, so "right" = the answer matches what the profile
    actually holds), audited after the run — each record carries ``kb_queries``
    (total KB queries asked) and ``kb_queries_correct`` (the audited count).

        KBIQ = sum_i(kb_queries_correct_i) / sum_i(kb_queries_i)   over KB tasks

    A task that never asked contributes 0 to the numerator but its queries are
    already 0, so it drops out; until a run is audited ``kb_queries_correct`` is
    0 and KBIQ reads 0 (not-audited).
    """
    total = sum(record.get("kb_queries") or 0 for record in records)
    correct = sum(record.get("kb_queries_correct") or 0 for record in records)
    return (correct / total) if total else 0.0
