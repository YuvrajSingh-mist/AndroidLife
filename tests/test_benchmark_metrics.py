"""Coverage for MobileWorld-style benchmark metrics (arXiv:2512.19432, MCP excluded)."""

from __future__ import annotations

import pytest

from DailyBench.benchmark_metrics import (
    avg_steps,
    avg_user_queries,
    kb_interaction_quality,
    success_rate,
    user_interaction_quality_factmatch,
)


def _rec(success: bool, steps: int = 0, ask_user_calls: int = 0, is_interaction: bool = False, ask_user_correct: int = 0, is_kb: bool = False, kb_queries: int = 0, kb_queries_correct: int = 0) -> dict:
    return {
        "success": success,
        "steps": steps,
        "ask_user_calls": ask_user_calls,
        "ask_user_correct": ask_user_correct,
        "is_interaction": is_interaction,
        "is_kb": is_kb,
        "kb_queries": kb_queries,
        "kb_queries_correct": kb_queries_correct,
    }


def test_success_rate_overall_and_empty() -> None:
    assert success_rate([_rec(True), _rec(False), _rec(True)]) == pytest.approx(2 / 3)
    assert success_rate([]) == 0.0


def test_avg_steps_overall_and_empty() -> None:
    assert avg_steps([_rec(True, 10), _rec(False, 4), _rec(True, 1)]) == pytest.approx(5.0)
    assert avg_steps([]) == 0.0


def test_avg_user_queries_counts_interaction_tasks_only() -> None:
    records = [
        _rec(True, ask_user_calls=2, is_interaction=True),
        _rec(True, ask_user_calls=1, is_interaction=True),
        _rec(True, ask_user_calls=5, is_interaction=False),  # excluded from denominator
    ]
    assert avg_user_queries(records) == pytest.approx(1.5)
    assert avg_user_queries([]) == 0.0


def test_factmatch_uiq_counts_right_question_even_when_task_failed() -> None:
    # Task asked the right question (answer matched ground truth) but still failed.
    records = [
        _rec(False, ask_user_calls=1, ask_user_correct=1, is_interaction=True),
    ]
    assert user_interaction_quality_factmatch(records) == pytest.approx(1.0)


def test_factmatch_uiq_penalizes_never_asked() -> None:
    # 1 right answer / (1 call + 1 never-asked interaction task) = 0.5
    records = [
        _rec(False, ask_user_calls=1, ask_user_correct=1, is_interaction=True),
        _rec(True, ask_user_calls=0, ask_user_correct=0, is_interaction=True),
    ]
    assert user_interaction_quality_factmatch(records) == pytest.approx(1 / 2)


def test_factmatch_uiq_counts_each_right_answer_and_penalizes_gui_triggered() -> None:
    # interaction asks twice, both right: per-task ratio = 2/2 = 1
    # denominator = 1 interaction + 1 GUI-only triggered = 2
    records = [
        _rec(False, ask_user_calls=2, ask_user_correct=2, is_interaction=True),
        _rec(True, ask_user_calls=1, ask_user_correct=0, is_interaction=False),
    ]
    assert user_interaction_quality_factmatch(records) == pytest.approx(1 / 2)


def test_factmatch_uiq_wrong_answers_and_empty() -> None:
    assert user_interaction_quality_factmatch([_rec(True, ask_user_calls=1, ask_user_correct=0, is_interaction=True)]) == pytest.approx(0.0)
    assert user_interaction_quality_factmatch([]) == 0.0


def test_kbiq_pooled_correct_over_total_kb_queries() -> None:
    # KB queries: 2 of 3 audited right across two KB tasks -> 2/3.
    records = [
        _rec(False, is_kb=True, kb_queries=2, kb_queries_correct=1),
        _rec(True, is_kb=True, kb_queries=1, kb_queries_correct=1),
        _rec(True, is_kb=False, kb_queries=0, kb_queries_correct=0),  # non-KB ignored
    ]
    assert kb_interaction_quality(records) == pytest.approx(2 / 3)


def test_kbiq_unaudited_and_empty() -> None:
    # Not audited yet -> correct stays 0 -> KBIQ 0 (never inflates).
    assert kb_interaction_quality([_rec(True, is_kb=True, kb_queries=2, kb_queries_correct=0)]) == pytest.approx(0.0)
    assert kb_interaction_quality([]) == 0.0
    assert kb_interaction_quality([_rec(True, is_kb=True, kb_queries=0, kb_queries_correct=0)]) == pytest.approx(0.0)


def test_factmatch_uiq_weights_each_task_equally_not_by_call_volume() -> None:
    # Per-task ratios: task A = 1/1 = 1.0, task B = 1/9 ≈ 0.111
    # UIQ = (1.0 + 1/9) / 2 ≈ 0.556 — the chatty task does NOT dominate.
    records = [
        _rec(False, ask_user_calls=1, ask_user_correct=1, is_interaction=True),
        _rec(False, ask_user_calls=9, ask_user_correct=1, is_interaction=True),
    ]
    assert user_interaction_quality_factmatch(records) == pytest.approx((1.0 + 1 / 9) / 2)
