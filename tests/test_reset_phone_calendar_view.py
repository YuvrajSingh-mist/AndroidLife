"""Regression tests for the Calendar-app view-mode gate in reset_phone.

Why this gate exists (measured 2026-09-21, redo.md 7.2): every provider-level check
reads the *content provider*. The Calendar APP's view mode lives in app state that no
provider query can see, yet it is the agent's first screen. A run whose agent ended on
the Day grid handed the next run a different starting condition than the original
runs, and two easy__calendar_002 re-runs had to be taken again because of it.

The marker is inverted, which is the easy thing to get backwards:

    "<date>, Open Day View"      -> the app is currently in SCHEDULE view
    "<date>, Open Schedule View" -> the app is currently in DAY view

These tests pin that mapping, the in-place repair, and the fact that the check always
hands back a stopped app on the launcher (it runs right before the first task, so
whatever it leaves on screen becomes the agent's start state).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "reset_phone.py"

SCHEDULE_XML = (
    '<hierarchy><node content-desc="Monday 21 September 2026, Open Day View" '
    'bounds="[0,0][1080,100]"/></hierarchy>'
)
DAY_XML = (
    '<hierarchy><node content-desc="Monday 21 September 2026, Open Schedule View" '
    'bounds="[10,20][30,40]"/></hierarchy>'
)
UNCLEAR_XML = "<hierarchy><node text='Search'/></hierarchy>"

CAL_PROFILE = {"seed_calendar_events": True}


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("reset_phone", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reset_phone"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _fast_clock(monkeypatch):
    """Drive the poll loop's clock instead of sleeping.

    Patching only `sleep` leaves the loop busy-waiting against a real 40 s deadline,
    which is exactly the wait these tests must not pay. Advancing a fake clock by the
    requested interval makes each poll take one virtual step.
    """
    import time as _time

    state = {"now": 1_700_000_000.0}

    def _advance(seconds, *a):
        state["now"] += max(seconds, 0.0)

    monkeypatch.setattr(_time, "time", lambda: state["now"])
    monkeypatch.setattr(_time, "sleep", _advance)
    yield state


class FakeDevice:
    """Records adb commands and flips view mode when the affordance is tapped."""

    def __init__(self, mode: str):
        self.mode = mode  # 'schedule' | 'day' | 'unclear'
        self.calls: list[str] = []

    def sh(self, serial, cmd, *a, **k):
        self.calls.append(cmd)
        if "input tap" in cmd:
            self.mode = "schedule"
        return ""

    def pull_ui_dump(self, *a, **k):
        if self.mode == "schedule":
            return SCHEDULE_XML
        if self.mode == "day":
            return DAY_XML
        return UNCLEAR_XML

    def taps(self):
        return [c for c in self.calls if "input tap" in c]


def _install(rp, monkeypatch, mode: str) -> FakeDevice:
    dev = FakeDevice(mode)
    monkeypatch.setattr(rp, "sh", dev.sh)
    monkeypatch.setattr(rp, "_pull_ui_dump", dev.pull_ui_dump)
    return dev


def test_marker_is_inverted(rp, monkeypatch):
    """'Open Day View' means we are IN Schedule -- the mapping that is easy to flip."""
    _install(rp, monkeypatch, "schedule")
    assert rp._calendar_view_mode("s") == "schedule"

    _install(rp, monkeypatch, "day")
    assert rp._calendar_view_mode("s") == "day"


def test_schedule_view_passes_without_tapping(rp, monkeypatch):
    dev = _install(rp, monkeypatch, "schedule")
    assert rp.verify_calendar_view_mode("s", CAL_PROFILE) is True
    assert dev.taps() == [], "a correct view mode must not be touched"


def test_day_view_is_repaired_in_place(rp, monkeypatch):
    """Day view must be FIXED, not merely reported -- the failure mode being
    defended against is exactly 'a human forgets to fix it'."""
    dev = _install(rp, monkeypatch, "day")
    assert rp.verify_calendar_view_mode("s", CAL_PROFILE) is True
    assert len(dev.taps()) == 1
    x, y = dev.taps()[0].split()[-2:]
    assert (x, y) == ("20", "30"), "tap the centre of the 'Open Schedule View' node"


def test_unreadable_ui_fails_closed(rp, monkeypatch):
    _install(rp, monkeypatch, "unclear")
    assert rp.verify_calendar_view_mode("s", CAL_PROFILE) is False


def test_gate_is_skipped_when_the_profile_seeds_no_calendar(rp, monkeypatch):
    dev = _install(rp, monkeypatch, "day")
    assert rp.verify_calendar_view_mode("s", {"seed_calendar_events": False}) is True
    assert dev.calls == [], "must not launch Calendar at all"


@pytest.mark.parametrize("mode", ["schedule", "day", "unclear"])
def test_always_hands_back_a_stopped_app_on_the_launcher(rp, monkeypatch, mode):
    """The gate runs immediately before the first task, so it must never leave
    Calendar in the foreground (same reason verify_meet_agenda had to be fixed)."""
    dev = _install(rp, monkeypatch, mode)
    rp.verify_calendar_view_mode("s", CAL_PROFILE)

    assert dev.calls[-2:] == [f"am force-stop {rp.CAL_PKG}", "input keyevent KEYCODE_HOME"]
