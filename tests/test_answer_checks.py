"""Ground-truth answer checks: grade the reply, not the model's opinion of it.

easy__google-slides__001 asks "how many slides does this deck have?". The official
grader scored it purely on `output["success"]` -- the model's own flag -- so the
recorded history contains replies of `1`, `3` and `8` and all three scored PASS
(redo.md 5). An answer check is a {task_id: known answer} sidecar that lets the grader
DEMOTE a self-reported pass whose reply does not state the right answer.

The check is one-directional by design: it can turn a pass into a failure but never the
reverse, so enabling it for a task can only ever make a score more honest.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest

from androidlife.task_dataset import answer_checks_path, merge_answer_checks
from androidlife_report import _reply_matches_check, load_run_record

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_8 = {"kind": "numeric_reply", "expected": 8}


def _write_run(runs_dir: Path, label: str, *, task_id: str, success: bool, reason: str) -> Path:
    run_dir = runs_dir / label
    run_dir.mkdir(parents=True)
    (run_dir / "output.json").write_text(
        json.dumps({"success": success, "reason": reason, "steps": 3})
    )
    (run_dir / "run_metrics.json").write_text(json.dumps({"ask_user_call_count": 0}))
    (run_dir / "meta.json").write_text(
        json.dumps({"label": label, "model": "m1", "task_id": task_id})
    )
    return run_dir


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("8", True),
        ("8 slides.", True),
        ("The deck has 8 slides", True),
        ("There are 8", True),
        ("Slide 8 of 8", True),
        ("1", False),
        ("3", False),
        ("seven", False),
        ("", False),
        ("I could not open the deck", False),
        ("18", False),  # a substring test would wrongly accept this
    ],
)
def test_numeric_reply_takes_the_first_integer(reply: str, expected: bool) -> None:
    assert _reply_matches_check(CHECK_8, reply) is expected


def test_no_applicable_check_returns_none_not_false() -> None:
    """None means "not checked"; only False is allowed to change a verdict."""
    assert _reply_matches_check(None, "1") is None
    assert _reply_matches_check({}, "1") is None
    assert _reply_matches_check({"kind": "some_future_kind"}, "1") is None


def test_answer_checks_path_is_keyed_by_source() -> None:
    assert answer_checks_path("public.md").endswith("answer_checks_public.json")
    assert answer_checks_path("tasks.md").endswith("answer_checks_530.json")
    with pytest.raises(ValueError):
        answer_checks_path("something-else.md")


def test_merge_answer_checks_sets_matching_rows_only(tmp_path: Path) -> None:
    dataset = {"tasks": [{"task_id": "easy__google-slides__001"}, {"task_id": "easy__other__001"}]}
    sidecar = tmp_path / "checks.json"
    sidecar.write_text(json.dumps({"easy__google-slides__001": CHECK_8}))
    merge_answer_checks(dataset, sidecar)
    assert dataset["tasks"][0]["answer_check"] == CHECK_8
    # Non-matching rows are left untouched, so they keep whatever the parser set (None).
    assert dataset["tasks"][1].get("answer_check") is None


def test_merge_answer_checks_is_a_no_op_for_a_missing_file(tmp_path: Path) -> None:
    dataset = {"tasks": [{"task_id": "easy__google-slides__001"}]}
    merge_answer_checks(dataset, tmp_path / "does-not-exist.json")
    assert dataset["tasks"][0].get("answer_check") is None


def test_wrong_reply_demotes_a_self_reported_pass(tmp_path: Path) -> None:
    """The exact failure mode the check exists for: PASS on the stray 1-slide deck."""
    run_dir = _write_run(
        tmp_path, "day1--easy-google-slides-001",
        task_id="easy__google-slides__001", success=True, reason="1",
    )
    record = load_run_record(run_dir, set(), checks={"easy__google-slides__001": CHECK_8})
    assert record["success"] is False
    assert record["classification"] == "true_failure"
    assert record["answer_check"] == "failed"
    assert record["answer_check_demoted"] is True


def test_correct_reply_keeps_the_pass(tmp_path: Path) -> None:
    run_dir = _write_run(
        tmp_path, "day1--easy-google-slides-001",
        task_id="easy__google-slides__001", success=True, reason="8",
    )
    record = load_run_record(run_dir, set(), checks={"easy__google-slides__001": CHECK_8})
    assert record["success"] is True
    assert record["classification"] == "true_success"
    assert record["answer_check"] == "passed"
    assert record["answer_check_demoted"] is False


def test_check_never_promotes_a_self_reported_failure(tmp_path: Path) -> None:
    """A model that reports failure still fails, even if its reply looks right."""
    run_dir = _write_run(
        tmp_path, "day1--easy-google-slides-001",
        task_id="easy__google-slides__001", success=False, reason="8",
    )
    record = load_run_record(run_dir, set(), checks={"easy__google-slides__001": CHECK_8})
    assert record["success"] is False
    assert record["answer_check"] == "passed"  # the reply itself was fine ...
    assert record["answer_check_demoted"] is False  # ... but nothing was promoted


def test_unchecked_task_is_left_alone(tmp_path: Path) -> None:
    run_dir = _write_run(
        tmp_path, "day2--medium-other-002",
        task_id="medium__other__002", success=True, reason="anything",
    )
    record = load_run_record(run_dir, set(), checks={"easy__google-slides__001": CHECK_8})
    assert record["success"] is True
    assert record["answer_check"] is None
    assert record["answer_check_demoted"] is False


def test_real_sidecar_agrees_with_the_real_seed_deck() -> None:
    """The grader's ground truth and the seeding fixture must be the same number.

    This is what ties the two halves of the fix together: reset_phone.py asserts the
    DEVICE deck has `expected_slides`, and this sidecar asserts the REPLY states the same
    count. If someone rebuilds the deck with a different number of slides this fails,
    instead of quietly re-scoring every historical run against a moved target.
    """
    sidecar = json.loads((REPO_ROOT / answer_checks_path("public.md")).read_text(encoding="utf-8"))
    check = sidecar["easy__google-slides__001"]
    assert check["kind"] == "numeric_reply"

    deck = REPO_ROOT / "assets/seeds/public/Q3_Review.pptx"
    assert deck.is_file(), f"the ground-truth deck is missing from the repo: {deck}"
    with zipfile.ZipFile(deck) as zf:
        slides = sum(1 for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))

    assert slides == check["expected"], (
        f"deck has {slides} slide(s) but the grader expects {check['expected']} -- "
        "the ground truth and the fixture have drifted apart"
    )
