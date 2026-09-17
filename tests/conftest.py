"""Shared pytest helpers for AndroidLife tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
# Script modules were reorganized into subfolders (2026-08-08): eval/ holds the
# report + eval modules, tools/ holds the proxy + provider/pricing helpers.
SCRIPT_SUBDIRS = [SCRIPTS / "eval", SCRIPTS / "tools"]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
for _d in ([SCRIPTS] + SCRIPT_SUBDIRS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def _adb_device_serials() -> list[str]:
    """Return serials of every attached ADB device whose state is exactly 'device'."""
    if shutil.which("adb") is None:
        return []
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5, check=False)
    except OSError:
        return []
    serials = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def first_adb_device() -> str | None:
    """Return the serial of the first attached ADB device (wired or wireless), or None if none is reachable."""
    serials = _adb_device_serials()
    return serials[0] if serials else None


def first_wired_adb_device() -> str | None:
    """Return the serial of the first attached wired (non ip:port) ADB device, or None if there isn't one."""
    for serial in _adb_device_serials():
        if ":" not in serial:
            return serial
    return None


def first_wireless_adb_device() -> str | None:
    """Return the serial of the first attached wireless (ip:port) ADB device, or None if there isn't one."""
    for serial in _adb_device_serials():
        if ":" in serial:
            return serial
    return None


def device_tests_enabled() -> bool:
    """Whether tests that touch the real handset are allowed to run (opt-in).

    Enabled by ANDROIDLIFE_DEVICE_TESTS=1. A bare `pytest` must never drive the
    phone: a benchmark batch is usually mid-run against it, and launching or
    force-stopping apps steals the foreground from the task in flight. That
    corrupts the run *and* then presents as a mysteriously flaky test rather than
    the interference it actually is.
    """
    return os.environ.get("ANDROIDLIFE_DEVICE_TESTS") == "1"


# For tests that only read from the device: run whenever one is attached.
requires_device = pytest.mark.skipif(
    first_adb_device() is None,
    reason="No ADB device attached (wired or wireless)",
)

# For tests that drive the phone (launch/force-stop apps, send key events).
requires_device_drive = pytest.mark.skipif(
    first_adb_device() is None or not device_tests_enabled(),
    reason="Drives the handset: needs an attached device AND ANDROIDLIFE_DEVICE_TESTS=1 "
           "(never run these while a benchmark batch is running)",
)
