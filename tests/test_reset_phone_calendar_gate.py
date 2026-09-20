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

import datetime
import importlib.util
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

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


# --- ensure_calendar_events: shift in place instead of delete+insert ---------
# A Meet conference link lives in Google sync-adapter columns the non-rooted
# `content` CLI cannot write, so delete+insert silently dropped it every reset.
# These tests pin the shift-in-place behaviour that keeps it. Fixtures are built
# relative to *today* because the seeder anchors to the real current date and a
# hardcoded epoch would go stale overnight.

TZ = ZoneInfo("Asia/Kolkata")
TODAY = datetime.date.today()


def _ms(day: datetime.date, hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return int(datetime.datetime(day.year, day.month, day.day, h, m, tzinfo=TZ).timestamp() * 1000)


def _next_weekday(weekday: int) -> datetime.date:
    """Next occurrence of `weekday` (0=Mon), never today -- mirrors the seeder."""
    days = (weekday - TODAY.weekday()) % 7 or 7
    return TODAY + datetime.timedelta(days=days)


MONDAY, TUESDAY = _next_weekday(0), _next_weekday(1)
D1, D2 = TODAY + datetime.timedelta(days=1), TODAY + datetime.timedelta(days=2)


def _rows(*specs) -> str:
    return "\n".join(f"Row: {i} _id={i}, title={t}, dtstart={ms}, deleted={d}"
                     for i, t, ms, d in specs)


# One May-ish copy of each seed, plus an unrelated live event whose title merely
# contains "Gym".
#
# KNOWN STALE (predates the meet-link rework in ensure_calendar_events): these copies are
# built from the CURRENT anchors, so the seeder's exact-date fast path treats them as
# already-correct and issues no write -- while the three shift tests below still assert
# three UPDATEs. That combination can only hold for `meet: True` seeds, where a same-time
# miss is resolved by an in-place UPDATE to preserve the conference link. These fixtures
# are unlinked, so a same-time miss now INSERTs by design. See redo.md.
QUERY_ROWS = _rows(
    (4313, "Old_Gym_Class", _ms(TODAY, "07:00"), 0),
    (4341, "Weekly Sync", _ms(MONDAY, "07:00"), 0),
    (4342, "Weekly Sync", _ms(D1, "10:00"), 0),
    (4343, "Weekly Sync", _ms(D2, "10:00"), 0),
    (4344, "Gym", _ms(TUESDAY, "06:30"), 0),
)


def _fake_sh(rows: str, calls: list[str]):
    def sh(serial, cmd, check=False):
        calls.append(cmd)
        if "getprop" in cmd:
            return "Asia/Kolkata"
        return rows
    return sh


def _seed(title="Weekly Sync", start="07:00", end="08:00", weekday="monday"):
    """Weekday-anchored seed (the clash-shift / Gym style)."""
    return {"title": title, "weekday": weekday, "start": start, "end": end}


def _seed_off(days=1, title="Weekly Sync", start="10:00", end="11:00"):
    """Offset-anchored seed (the Meet agenda-meeting style)."""
    return {"title": title, "offset_days": days, "start": start, "end": end}


def test_live_events_match_exact_titles_and_skip_deleted(rp, monkeypatch):
    """Only live rows with exactly-matching titles come back."""
    monkeypatch.setattr(rp, "sh", _fake_sh(QUERY_ROWS, []))
    got = rp._live_calendar_events("S", ["Weekly Sync", "Gym"])
    assert [g[0] for g in got] == ["4341", "4342", "4343", "4344"]
    assert "4313" not in [g[0] for g in got]  # Old_Gym_Class must not match "Gym"

    deleted = _rows((9, "Gym", _ms(TODAY, "07:00"), 1))
    monkeypatch.setattr(rp, "sh", _fake_sh(deleted, []))
    assert rp._live_calendar_events("S", ["Gym"]) == []


def test_existing_seeds_are_shifted_in_place(rp, monkeypatch):
    """Matched seeds are UPDATE'd, never deleted and re-inserted."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(QUERY_ROWS, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    # the full public_v2 declaration: clash seed + both agenda-meeting offsets
    rp.ensure_calendar_events("S", [_seed(start="07:00", end="08:00"),
                                    _seed_off(days=1), _seed_off(days=2)], apply=True)

    updates = [c for c in calls if "content update" in c]
    inserts = [c for c in calls if "content insert" in c]
    deletes = [c for c in calls if "content delete" in c]
    assert len(updates) == 3, f"expected in-place shifts, got: {calls}"
    assert ["_id=4341" in updates[0], "_id=4342" in updates[1], "_id=4343" in updates[2]]
    assert not inserts, "a matched seed must not be re-inserted"
    assert not deletes, "a matched seed must not be deleted"
    # Gym is not in the declared seed list, so it must not be touched either.
    assert not any("_id=4344" in c for c in calls)


def test_same_time_on_consecutive_days_both_survive(rp, monkeypatch):
    """The two 10:00 agenda seeds differ only by date; neither may be treated as
    a stale duplicate of the other (time-of-day matching alone would delete one)."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(QUERY_ROWS, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed(start="07:00", end="08:00"),
                                    _seed_off(days=1), _seed_off(days=2)], apply=True)

    updates = [c for c in calls if "content update" in c]
    deletes = [c for c in calls if "content delete" in c]
    assert len(updates) == 3, f"one copy was wrongly dropped: {calls}"
    assert "_id=4342" in updates[1] and "_id=4343" in updates[2]
    assert not deletes, f"a declared seed was deleted as stale: {deletes}"


def test_time_of_day_disambiguates_duplicate_titles(rp, monkeypatch):
    """The 10:00 agenda seed must not match the 07:00 Monday copy."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(QUERY_ROWS, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed(start="07:00", end="08:00")], apply=True)

    updates = [c for c in calls if "content update" in c]
    assert len(updates) == 1
    assert "_id=4341" in updates[0], f"matched the wrong Weekly Sync copy: {updates[0]}"


def test_already_correct_seed_is_not_rewritten(rp, monkeypatch):
    """A seed already sitting on its anchor is left alone (no pointless write).

    This skip is what silently invalidated the three shift tests above when their fixture
    was built from the current anchors -- so it gets its own explicit test rather than
    being an unasserted side effect of them.
    """
    calls: list[str] = []
    rows = _rows((4341, "Weekly Sync", _ms(_next_weekday(0), "07:00"), 0))
    monkeypatch.setattr(rp, "sh", _fake_sh(rows, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed(start="07:00", end="08:00")], apply=True)

    assert not [c for c in calls if "content update" in c], f"rewrote an up-to-date seed: {calls}"
    assert not [c for c in calls if "content insert" in c], "duplicated an existing seed"


def test_missing_seed_is_inserted(rp, monkeypatch):
    """No existing copy for that slot -> insert (first-time seeding)."""
    rows = _rows((4341, "Weekly Sync", _ms(MONDAY, "07:00"), 0))
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(rows, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed_off(days=1)], apply=True)

    assert len([c for c in calls if "content insert" in c]) == 1
    assert not [c for c in calls if "content update" in c]


def test_unmatched_stale_copy_is_deleted_but_matched_one_is_kept(rp, monkeypatch):
    """A duplicate in a non-matching slot is stale; the matched copy survives."""
    stale = _ms(TODAY, "15:00")  # right title, wrong slot
    rows = _rows((4341, "Weekly Sync", _ms(MONDAY, "07:00"), 0),
                 (9999, "Weekly Sync", stale, 0))
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(rows, calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed(start="07:00")], apply=True)

    deletes = [c for c in calls if "content delete" in c]
    assert any("_id=9999" in c for c in deletes), f"stale copy not removed: {calls}"
    assert not any("_id=4341" in c for c in deletes), "matched copy must survive"


def test_offset_days_anchors_to_today_plus_n(rp, monkeypatch):
    """offset_days seeds land on today+N, even when today is that weekday."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh("", calls))
    monkeypatch.setattr(rp, "quote", lambda s: f"'{s}'")

    rp.ensure_calendar_events("S", [_seed_off(days=1), _seed_off(days=2)], apply=True)

    starts = [int(re.search(r"dtstart:l:(\d+)", c).group(1))
              for c in calls if "content insert" in c]
    assert starts == [_ms(D1, "10:00"), _ms(D2, "10:00")], starts


def test_dry_run_makes_no_changes(rp, monkeypatch):
    """apply=False must plan only -- no update, insert or delete."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "sh", _fake_sh(QUERY_ROWS, calls))

    rp.ensure_calendar_events("S", [_seed(), _seed_off(days=1)], apply=False)

    assert not [c for c in calls if "content update" in c or "content insert" in c
                or "content delete" in c], f"dry run wrote: {calls}"
