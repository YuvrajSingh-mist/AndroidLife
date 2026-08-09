"""Tests for scripts/seeding/device_paths.py (device-specific seed value resolution).

Covers the portability contract: config overrides win, and without a config key
the function falls back to auto-detection (which on a device-less test env falls
back to the historical default). No real device is required.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "seeding"))

import device_paths  # noqa: E402


def test_config_override_wins_for_vault_path() -> None:
    """An explicit `vault path` config key beats auto-detection/default."""
    cfg = {"vault path": "/sdcard/Obsidian/My Vault"}
    assert device_paths.vault_path("no-such-device", cfg) == "/sdcard/Obsidian/My Vault"


def test_vault_path_falls_back_to_default_without_device() -> None:
    """No config key + no reachable device -> the historical default (the original
    device's vault, trailing space preserved)."""
    got = device_paths.vault_path("no-such-device")
    assert got == device_paths.DEFAULT_VAULT
    assert got.endswith(" ")


def test_calendar_id_config_override() -> None:
    """An explicit `calendar id` config key is used verbatim."""
    cfg = {"calendar id": "7"}
    assert device_paths.calendar_id("no-such-device", cfg) == "7"


def test_calendar_id_default_without_device() -> None:
    """No config + no device -> historical default id."""
    assert device_paths.calendar_id("no-such-device") == device_paths.DEFAULT_CALENDAR_ID


def test_contact_email_config_override_and_default() -> None:
    """`contact email` config override, else the persona default."""
    assert device_paths.contact_email({"contact email": "me@example.com"}) == "me@example.com"
    assert device_paths.contact_email() == device_paths.DEFAULT_CONTACT_EMAIL


def test_camera_screenshots_are_stable_paths() -> None:
    """Camera/Screenshots are standard Android paths (no per-device variation)."""
    assert device_paths.CAMERA == "/sdcard/DCIM/Camera"
    assert device_paths.SCREENSHOTS == "/sdcard/DCIM/Screenshots"
