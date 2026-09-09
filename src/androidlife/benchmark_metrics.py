"""MobileWorld-style benchmark metrics (arXiv:2512.19432, MCP metric excluded)"""

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
    """UIQ: mean of per-task ask correctness ratios (see docs/evaluation-policy.md)."""
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
    """KBIQ: UIQ-style mean over multi-turn KB tasks (manual audit; see docs/evaluation-policy.md)."""
    kb = [r for r in records if r.get("is_kb")]
    if not kb:
        return 0.0
    numerator = 0.0
    for record in kb:
        queries = record.get("kb_queries") or 0
        if queries > 0:
            numerator += (record.get("kb_queries_correct") or 0) / queries
    return numerator / len(kb)
