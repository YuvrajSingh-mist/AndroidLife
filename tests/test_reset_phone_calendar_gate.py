"""Regression tests for the calendar-seed gate in reset_phone.verify().

The gate decides whether the device still holds its seeded calendar events. It
false-PASSed twice, which is dangerous because a missing "Weekly Sync" / "Gym"
seed silently breaks hard__clock-calendar__023 and hard__google-meet-files__070
without the pre-run check noticing:

  1. all copies soft-deleted -> `_line_for` returned "" and the caller's
     `"deleted=1" not in ""` evaluated True, so the seed read as present;
  2. substring matching -> the seed "Gym" also matched the live "Old_Gym_Class"
     event, so the gate passed with the real "Gym" seed soft-deleted.

These tests pin the exact-title + live-row behaviour of `_line_for`, which
`verify()` now uses as `present = bool(_line_for(...))`.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "reset_phone.py"

# Shape of `content query --uri .../events --projection _id:title:_sync_id:deleted`
DUMP = """\
Row: 700 _id=4313, title=Old_Gym_Class, _sync_id=aaa, deleted=0
Row: 705 _id=4338, title=Weekly Sync, _sync_id=bbb, deleted=1
Row: 708 _id=4341, title=Weekly Sync, _sync_id=ccc, deleted=0
Row: 709 _id=4342, title=Gym, _sync_id=ddd, deleted=1
"""


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("reset_phone", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reset_phone"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_substring_title_does_not_match(rp):
    """'Gym' must not be satisfied by the live 'Old_Gym_Class' event (hole #2)."""
    assert rp._line_for(DUMP, "Gym") == ""
    assert rp._line_for(DUMP, "Old_Gym_Class") != ""


def test_exact_title_matches_only_its_own_row(rp):
    """An exact live title returns that row, not a longer one containing it."""
    line = rp._line_for(DUMP, "Weekly Sync")
    assert "_id=4341" in line
    assert "_id=4338" not in line  # the soft-deleted copy


def test_soft_deleted_row_is_never_returned(rp):
    """A title with only a deleted=1 copy has no live row."""
    assert rp._line_for(DUMP, "Gym") == ""
    assert rp._line_for("Row: 1 _id=9, title=Gym, _sync_id=x, deleted=1", "Gym") == ""


def test_gate_fails_when_every_copy_is_soft_deleted(rp):
    """The original false PASS: `title in ev and "deleted=1" not in ""` was True."""
    dump = "Row: 1 _id=9, title=Gym, _sync_id=x, deleted=1"

    # the old, buggy expression reported the seed as present
    assert "Gym" in dump and "deleted=1" not in rp._line_for(dump, "Gym")

    # the fixed expression reports it absent
    assert rp._line_for(dump, "Gym") == ""
    assert not bool(rp._line_for(dump, "Gym"))


def test_synced_flag_derives_from_the_live_row(rp):
    """sync-state must come from the live row, not a soft-deleted copy's _sync_id."""
    live = rp._line_for(DUMP, "Weekly Sync")
    assert re.search(r"_sync_id=[^,]", live)

    # a deleted copy still carries an id; deriving from it would wrongly say 'synced'
    only_deleted = "Row: 1 _id=9, title=Gym, _sync_id=x, deleted=1"
    assert not re.search(r"_sync_id=[^,]", rp._line_for(only_deleted, "Gym"))


def test_untitled_and_absent_titles_are_empty(rp):
    """Unknown titles and blank/absent fields yield no match."""
    assert rp._line_for(DUMP, "Nonexistent") == ""
    assert rp._line_for("Row: 1 _id=9, title=, deleted=0", "Gym") == ""
