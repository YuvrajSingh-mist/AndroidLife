"""Coverage for the batch metrics report (scripts/eval/dailybench_report.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dailybench_report import build_report, discover_run_folders, load_run_record, parse_task_id_from_label


def _write_run(
    runs_dir: Path,
    label: str,
    *,
    task_id: str | None = None,
    success: bool = True,
    steps: int = 5,
    ask_user_calls: int = 0,
    model: str = "m1",
) -> Path:
    run_dir = runs_dir / label
    run_dir.mkdir(parents=True)
    (run_dir / "output.json").write_text(json.dumps({"success": success, "reason": "done", "steps": steps}))
    (run_dir / "run_metrics.json").write_text(json.dumps({"ask_user_call_count": ask_user_calls}))
    meta = {"label": label, "model": model}
    if task_id:
        meta["task_id"] = task_id
    (run_dir / "meta.json").write_text(json.dumps(meta))
    return run_dir


def test_parse_task_id_from_label_variants() -> None:
    assert parse_task_id_from_label("day1--easy-gmail-001") == "easy__gmail__001"
    assert parse_task_id_from_label("hard--hard-gmail-contacts-002") == "hard__gmail-contacts__002"
    assert parse_task_id_from_label("day2--medium-google-maps-007-rep01") == "medium__google-maps__007"
    assert parse_task_id_from_label("not-a-label") is None
    assert parse_task_id_from_label("") is None


def test_discover_run_folders_only_includes_dirs_with_output(tmp_path: Path) -> None:
    _write_run(tmp_path, "a")
    (tmp_path / "empty").mkdir()
    assert discover_run_folders(str(tmp_path)) == [tmp_path / "a"]


def test_load_run_record_uses_meta_task_id_and_run_metrics_count(tmp_path: Path) -> None:
    _write_run(tmp_path, "day1--easy-gmail-001", task_id="easy__gmail__001", ask_user_calls=3)
    record = load_run_record(tmp_path / "day1--easy-gmail-001", {"hard__x__001"})
    assert record["task_id"] == "easy__gmail__001"
    assert record["bucket"] == "easy"
    assert record["ask_user_calls"] == 3
    assert record["is_interaction"] is False


def test_load_run_record_falls_back_to_jsonl_count_and_label_parse(tmp_path: Path) -> None:
    run_dir = _write_run(tmp_path, "hard--hard-gmail-contacts-002")
    # older run: no ask_user_call_count in run_metrics, no task_id in meta
    (run_dir / "run_metrics.json").write_text(json.dumps({}))
    (run_dir / "ask_user_metrics.jsonl").write_text("{}\n{}\n")
    record = load_run_record(run_dir, {"hard__gmail-contacts__002"})
    assert record["task_id"] == "hard__gmail-contacts__002"
    assert record["bucket"] == "hard"
    assert record["ask_user_calls"] == 2
    assert record["is_interaction"] is True


def test_build_report_computes_mobileworld_metrics(tmp_path: Path) -> None:
    interaction = {"hard__gmail-contacts__002"}
    r1 = _write_run(tmp_path, "day1--easy-gmail-001", task_id="easy__gmail__001", success=True, steps=4)
    r2 = _write_run(tmp_path, "day1--medium-gmail-002", task_id="medium__gmail__002", success=False, steps=9)
    r3 = _write_run(
        tmp_path, "hard--hard-gmail-contacts-002", task_id="hard__gmail-contacts__002", success=True, steps=6, ask_user_calls=2
    )
    r4 = _write_run(tmp_path, "day2--medium-gmail-003", task_id="medium__gmail__003", success=True, steps=5, ask_user_calls=1)
    run_dirs = sorted([r1, r2, r3, r4])
    records = [load_run_record(d, interaction) for d in run_dirs]
    report = build_report(records)

    assert report["run_count"] == 4
    assert report["success_rate"] == pytest.approx(3 / 4)
    assert report["average_steps"] == pytest.approx((4 + 9 + 6 + 5) / 4)
    assert report["interaction_success_rate"] == pytest.approx(1.0)
    assert report["gui_only_success_rate"] == pytest.approx(2 / 3)
    assert report["average_user_queries"] == pytest.approx(2.0)  # only the interaction task counts
    # fact-match: 0 correct answers / (2 interaction ask_user calls + 1 GUI-only triggered (r4)) = 0
    assert report["user_interaction_quality_factmatch"] == pytest.approx(0.0)
    assert report["success_rate_by_bucket"]["easy"] == pytest.approx(1.0)
    assert report["success_rate_by_bucket"]["medium"] == pytest.approx(0.5)


def test_build_report_model_filter(tmp_path: Path) -> None:
    _write_run(tmp_path, "day1--easy-gmail-001", task_id="easy__gmail__001", success=True, model="m1")
    _write_run(tmp_path, "day1--easy-gmail-002", task_id="easy__gmail__002", success=False, model="m2")
    records = [load_run_record(d, set()) for d in discover_run_folders(str(tmp_path))]
    assert build_report(records, model="m1")["run_count"] == 1
    assert build_report(records, model="m1")["success_rate"] == pytest.approx(1.0)


def test_load_run_record_classifies_controls_from_real_judge_absence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = _write_run(
        tmp_path,
        "day3--easy-clock-017",
        task_id="easy__clock__017",
        success=True,
        steps=3,
    )
    (run_dir / "output.json").write_text(
        json.dumps({"success": True, "reason": "No alarm labeled Gym exists in Clock.", "steps": 3})
    )
    controls = {
        "easy__clock__017": {
            "data_absent": True,
            "type": "absent-entity",
            "absence": "No alarm labeled 'Gym' exists in Clock.",
            "expected": "honest-failure: report no such alarm exists rather than fabricate its scheduled time",
        }
    }
    monkeypatch.setattr("dailybench_report._control_reason_honest_absence", lambda reason, control: True)
    record = load_run_record(run_dir, set(), controls=controls)
    assert record["is_hallucination_control"] is True
    assert record["classification"] == "true_failure"


def test_load_run_record_marks_control_fabrication_as_hallucination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir = _write_run(
        tmp_path,
        "day3--medium-settings-017",
        task_id="medium__settings__017",
        success=True,
        steps=3,
    )
    (run_dir / "output.json").write_text(
        json.dumps({"success": True, "reason": "Scheduled power off is configured for 11:00 PM.", "steps": 3})
    )
    controls = {
        "medium__settings__017": {
            "data_absent": True,
            "type": "absent-entity",
            "absence": "No scheduled power-off is configured in Settings.",
            "expected": "honest-failure: report no scheduled power-off exists rather than fabricate a time",
        }
    }
    monkeypatch.setattr("dailybench_report._control_reason_honest_absence", lambda reason, control: False)
    record = load_run_record(run_dir, set(), controls=controls)
    assert record["is_hallucination_control"] is True
    assert record["classification"] == "hallucination"


def test_report_judge_disabled_never_classifies_hallucination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With the judge disabled, a success-reporting control is a true failure, not a hallucination."""
    run_dir = _write_run(
        tmp_path,
        "day3--medium-settings-017",
        task_id="medium__settings__017",
        success=True,
        steps=3,
    )
    (run_dir / "output.json").write_text(
        json.dumps({"success": True, "reason": "Scheduled power off is configured for 11:00 PM.", "steps": 3})
    )
    controls = {
        "medium__settings__017": {
            "data_absent": True,
            "type": "absent-entity",
            "absence": "No scheduled power-off is configured in Settings.",
            "expected": "honest-failure: report no scheduled power-off exists rather than fabricate a time",
        }
    }
    monkeypatch.setattr("dailybench_report._HALLUCINATION_JUDGE_ENABLED", False)
    record = load_run_record(run_dir, set(), controls=controls)
    assert record["is_hallucination_control"] is True
    assert record["classification"] == "true_failure"


def test_hallucination_judge_module_missing_input_is_error() -> None:
    """The modular judge returns an error result (no network) for missing input."""
    from DailyBench.hallucination_judge import judge_control_honesty

    result = judge_control_honesty("", {"absence": ""})
    assert result.error is not None
    assert result.honest is False
    assert result.score == 0.0
