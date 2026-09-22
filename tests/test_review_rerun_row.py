"""Tests for the re-run manual-review gate (scripts/tools/review_rerun_row.py).

The gate exists because `output.json` is not publishable for a redo row. Three failures
look identical to `success: true`:

  * a vacuous PASS -- Maps' leaked recent list let the agent reach the right end state
    without typing the query (7 of 13 runs on 2026-09-16);
  * a wrong-answer PASS -- 2026-09-23 row 9 typed the query and wrote a well-formed note,
    but named **Two-wheeler** fastest when the task asks about driving/transit/walking; and
  * a step-cap exit, which is an honest FAIL rather than a harness error.

Both PASS and FAIL cases are pinned, including a regression for a false positive this
reviewer originally had (see `test_single_mode_note_passes`).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "tools" / "review_rerun_row.py"


@pytest.fixture(scope="module")
def rr():
    spec = importlib.util.spec_from_file_location("review_rerun_row", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["review_rerun_row"] = mod
    spec.loader.exec_module(mod)
    return mod


def _traj(*calls: tuple[str, str]) -> str:
    """Build a trajectory.json body from (tool_name, text) pairs."""
    events = []
    for name, text in calls:
        events.append({
            "type": "FastAgentResponseEvent",
            "code": (f'<function_calls>\n<invoke name="{name}">\n'
                     f'<parameter name="text">{text}</parameter>\n</invoke>\n</function_calls>'),
        })
    return json.dumps(events)


def _row(tmp_path: Path, *, success: bool, steps: int, calls: list[tuple[str, str]]) -> Path:
    task = tmp_path / "day1" / "medium-google-maps-002"
    (task / "trajectories" / "t1").mkdir(parents=True)
    (task / "output.json").write_text(json.dumps({"success": success, "steps": steps}))
    (task / "trajectories" / "t1" / "trajectory.json").write_text(_traj(*calls))
    return task


QUERY = ("type", "Bhubaneswar Airport")
# The real note from 2026-09-23 row 8: correct -- all three compared, driving fastest.
NOTE_OK = ("type", (
    "Fastest route to Bhubaneswar Airport\\n\\nDriving: 32 minutes, 13 km\\n"
    "Transit: unavailable\\nWalking: 2 hours 50 minutes\\n\\nFastest option: Driving"))
# The real note from 2026-09-23 row 9: well-formed, but answers a different question.
NOTE_OFF = ("type", "Travel to Bhubaneswar Airport - Fastest Option: Two-wheeler (33 min, 12 km)")
# The real note from row 3: only the fastest option, which is what the task asks for.
NOTE_SINGLE = ("type", "Fastest Route to Bhubaneswar Airport\\nDriving: 26 minutes, 13 km")


def test_good_row_passes(rr, tmp_path):
    task = _row(tmp_path, success=True, steps=54, calls=[QUERY, NOTE_OK])
    res = rr.review_maps(task)
    assert res["verdict"] == "PASS", res["reasons"]
    assert res["evidence"]["typed_query"] is True
    assert res["evidence"]["compared_all_three"] is True


def test_off_mode_note_fails_even_though_it_looks_clean(rr, tmp_path):
    """Row 9, 2026-09-23: typed the query AND wrote a note, but named Two-wheeler fastest."""
    task = _row(tmp_path, success=False, steps=60, calls=[QUERY, NOTE_OFF])
    res = rr.review_maps(task)
    assert res["verdict"] == "FAIL"
    assert any("two-wheeler" in x for x in res["reasons"])
    assert any("different question" in x for x in res["reasons"])


def test_single_mode_note_passes(rr, tmp_path):
    """Regression: the task says save only the FASTEST option, so one mode in the note is fine.

    The first version of this reviewer required all three modes in the NOTE and therefore
    false-FAILed row 3 (`Fastest Route to Bhubaneswar Airport / Driving: 26 minutes, 13 km`),
    which is a correct answer. The comparison happens on the Maps screen, not in the note.
    """
    task = _row(tmp_path, success=True, steps=9, calls=[QUERY, NOTE_SINGLE])
    res = rr.review_maps(task)
    assert res["verdict"] == "PASS", res["reasons"]
    assert res["evidence"]["modes_in_note"] == ["driving"]


def test_no_typed_query_is_vacuous(rr, tmp_path):
    """The redo.md section 1 mechanism: taps a leftover suggestion, never types."""
    task = _row(tmp_path, success=True, steps=12,
                calls=[("click", "Biju Patnaik International Airport"), NOTE_OK])
    res = rr.review_maps(task)
    assert res["verdict"] == "FAIL"
    assert any("never typed the airport query" in x for x in res["reasons"])


def test_step_cap_is_a_fail(rr, tmp_path):
    task = _row(tmp_path, success=False, steps=60, calls=[QUERY, NOTE_OK])
    res = rr.review_maps(task)
    assert res["verdict"] == "FAIL"
    assert any("step cap" in x for x in res["reasons"])


def test_missing_note_is_a_fail(rr, tmp_path):
    task = _row(tmp_path, success=True, steps=20, calls=[QUERY])
    res = rr.review_maps(task)
    assert res["verdict"] == "FAIL"
    assert any("no comparison note" in x for x in res["reasons"])


def test_no_output_json_is_void_not_fail(rr, tmp_path):
    """An aborted row has nothing to review; VOID keeps it out of the pass/fail tally."""
    task = tmp_path / "day1" / "medium-google-maps-002"
    task.mkdir(parents=True)
    assert rr.review_maps(task)["verdict"] == "VOID"


def test_no_trajectory_is_void(rr, tmp_path):
    task = tmp_path / "day1" / "medium-google-maps-002"
    task.mkdir(parents=True)
    (task / "output.json").write_text(json.dumps({"success": True, "steps": 5}))
    assert rr.review_maps(task)["verdict"] == "VOID"


def test_out_of_question_note_that_names_no_required_mode_fails(rr, tmp_path):
    task = _row(tmp_path, success=True, steps=10,
                calls=[QUERY, ("type", "Fastest option: cab, 20 minutes")])
    res = rr.review_maps(task)
    assert res["verdict"] == "FAIL"
    assert any("cab" in x for x in res["reasons"])
