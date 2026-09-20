"""Pytest coverage for the seed-stamp and recurring-artifact gates in reset_phone.py.

Both checks exist because of the same class of bug: a seed that LOOKS present but is not
the seed the task expects.

  * seed stamp -- every calendar anchor is a delta from the day `--apply` ran, so a reset
    performed the previous day leaves the pair on the run day. `easy__calendar__002` then
    asks about a "tomorrow" with no conflict and passes vacuously. Recorded in 5 of 13
    runs; see redo.md #6.
  * recurring artifacts -- a leftover daily series (Weekly_Standup, FREQ=DAILY;COUNT=14
    from the 2026-09-17 run) lands on every day of the window, including "tomorrow", so it
    survives every date-exact check while still changing what the agent sees.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "reset_phone.py"

# Shape of `content query --uri .../events --projection _id:title:rrule:deleted`
RECURRING_DUMP = """\
Row: 0 _id=3592, title=shareholder AlphaCorp Q2 Review, rrule=NULL, deleted=0
Row: 0 _id=4378, title=Weekly_Standup, rrule=FREQ=DAILY;COUNT=14;WKST=MO, deleted=0
Row: 0 _id=4379, title=Weekly_Standup, rrule=FREQ=DAILY;COUNT=14;WKST=MO, deleted=1
Row: 0 _id=4435, title=Team Sync, rrule=NULL, deleted=0
Row: 0 _id=4440, title=Daily Standup, rrule=FREQ=DAILY, deleted=0
"""

TOMBSTONE_DUMP = """\
Row: 0 _id=4378, title=Weekly_Standup, rrule=FREQ=DAILY;COUNT=14;WKST=MO, deleted=1
"""


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("reset_phone", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reset_phone"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_is_deleted_detects_tombstone(rp):
    """A soft-deleted row is a tombstone, not a live event.

    Deleting a calendar row leaves `deleted=1` behind so the deletion can reach the
    server. A presence check that ignores it reads a SUCCESSFUL delete as 'still
    present' -- which is exactly how the recurring sweep first passed then failed.
    """
    assert rp._is_deleted(TOMBSTONE_DUMP.strip()) is True
    assert rp._is_deleted("Row: 0 _id=4435, title=Team Sync, deleted=0") is False
    assert rp._is_deleted("Row: 0 _id=4435, title=Team Sync") is False  # no column


def test_recurring_sweep_ignores_tombstones_and_other_series(rp, monkeypatch):
    """Only the live parent of a configured series is swept.

    The tombstone (`deleted=1`) must not be re-deleted, and an unconfigured recurring
    series (`Daily Standup`) must be left alone -- it is not a run artifact.
    """
    deleted: list[str] = []
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: (
        deleted.append(cmd) or "" if cmd.startswith("content delete") else RECURRING_DUMP))
    rp.remove_recurring_calendar_artifacts("device-1", ["Weekly_Standup"], apply=True)
    assert len(deleted) == 1
    assert "_id=4378" in deleted[0]
    assert "4379" not in deleted[0]  # the tombstone


def test_recurring_gate_fails_while_series_is_live(rp, monkeypatch):
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: RECURRING_DUMP)
    assert rp.verify_no_recurring_artifacts("device-1",
                                            {"calendar_recurring_artifacts_to_remove": ["Weekly_Standup"]}) is False


def test_recurring_gate_passes_once_only_tombstone_remains(rp, monkeypatch):
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: TOMBSTONE_DUMP)
    assert rp.verify_no_recurring_artifacts("device-1",
                                            {"calendar_recurring_artifacts_to_remove": ["Weekly_Standup"]}) is True


def test_recurring_gate_is_noop_without_config(rp):
    """Day profiles must not sweep: Weekly_Standup is a real day-1 seed there."""
    assert rp.verify_no_recurring_artifacts("device-1", {}) is True


def _stamp(rp, monkeypatch, tmp_path, payload):
    path = tmp_path / ".seed_state.json"
    if payload is not None:
        path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(rp, "SEED_STATE_PATH", path)
    return path


def test_seed_freshness_passes_when_applied_today(rp, monkeypatch, tmp_path):
    today = datetime.date.today().isoformat()
    _stamp(rp, monkeypatch, tmp_path, {"seeded_on": today, "profile": "public_v2"})
    assert rp.verify_seed_freshness("public_v2") is True


def test_seed_freshness_fails_when_applied_yesterday(rp, monkeypatch, tmp_path):
    """The exact 2026-09-20 condition: seeded Sep 19, run Sep 20 -> vacuous calendar pass."""
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    _stamp(rp, monkeypatch, tmp_path, {"seeded_on": yesterday, "profile": "public_v2"})
    assert rp.verify_seed_freshness("public_v2") is False


def test_seed_freshness_fails_when_stamp_missing(rp, monkeypatch, tmp_path):
    _stamp(rp, monkeypatch, tmp_path, None)
    assert rp.verify_seed_freshness("public_v2") is False


def test_seed_freshness_fails_on_profile_mismatch(rp, monkeypatch, tmp_path):
    """A stamp from a different profile has different seeds, so it proves nothing."""
    today = datetime.date.today().isoformat()
    _stamp(rp, monkeypatch, tmp_path, {"seeded_on": today, "profile": "day_1"})
    assert rp.verify_seed_freshness("public_v2") is False


def test_seed_freshness_fails_on_corrupt_stamp(rp, monkeypatch, tmp_path):
    path = tmp_path / ".seed_state.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(rp, "SEED_STATE_PATH", path)
    assert rp.verify_seed_freshness("public_v2") is False
