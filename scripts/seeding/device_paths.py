#!/usr/bin/env python3
"""Device-specific path/ID auto-detection for seeding + verification.

The seed scripts used to hardcode this phone's layout (Obsidian vault path with
a trailing space, the Google-synced calendar id "16", the fabricated persona
email). That made the benchmark single-device: a different phone with a
differently-named vault, a different calendar account, or a different persona
would silently seed into the wrong place.

This module centralises those values and resolves them in priority order:

  1. an explicit config/user.yaml override (keys below),
  2. auto-detection from the live device (best-effort ADB query),
  3. the historical default (so the current device keeps working untouched).

Resolution is cached per process. Every function takes a ``serial`` and shells
out to ``adb`` only when needed (no device -> falls straight back to default).
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

# Config keys (see src/DailyBench/user_config.py SCHEMA) that override
# auto-detection for a non-default device / persona.
CFG_KEY_VAULT = "vault path"
CFG_KEY_CALENDAR_ID = "calendar id"
CFG_KEY_CONTACT_EMAIL = "contact email"

# Historical defaults for the original benchmark device (OnePlus CPH2423,
# persona "Yuvraj Singh"). Kept as the final fallback so nothing breaks.
DEFAULT_VAULT = "/sdcard/Obsidian/Papers vault oneplus "  # NB: trailing space is real
DEFAULT_CALENDAR_ID = "16"
DEFAULT_CONTACT_EMAIL = "yuvraj.airtel@example.com"

# Camera / Screenshots are stable Android paths (no trailing-space quirk).
CAMERA = "/sdcard/DCIM/Camera"
SCREENSHOTS = "/sdcard/DCIM/Screenshots"


def adb(serial: str, *args: str) -> tuple[int, str]:
    try:
        res = subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True, timeout=30)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""
    return res.returncode, (res.stdout + res.stderr).strip()


def vault_path(serial: str, cfg: dict[str, str] | None = None) -> str:
    """Resolve the Obsidian vault directory on the device.

    Priority: config `vault path` -> auto-detect the /sdcard/Obsidian subdir that
    actually contains .md files (the vault, vs. empty/Obsidian-config dirs) ->
    DEFAULT_VAULT.

    Detection uses `find` (not `ls`): the device's ls display strips a trailing
    space from a vault name (the original device's vault is literally
    'Papers vault oneplus '), which made a ls-based probe return a path that
    doesn't exist. `find ... -name '*.md'` locates the real vault dir directly.
    """
    if cfg and cfg.get(CFG_KEY_VAULT):
        return cfg[CFG_KEY_VAULT]
    # find the first .md under /sdcard/Obsidian (the vault holds the notes).
    rc, out = adb(serial, "shell", "find", "/sdcard/Obsidian", "-maxdepth", "3",
                  "-name", "*.md", "-print", "-quit")
    if rc == 0 and out.strip():
        first_md = out.strip().splitlines()[0].strip()
        md_path = Path(first_md)
        # Return the TOP-LEVEL vault dir (the direct child of /sdcard/Obsidian),
        # not the nested folder that happens to hold the first .md (e.g.
        # 'Excalidraw'). 'Papers vault oneplus ' has a trailing space - kept.
        try:
            obsidian_idx = md_path.parts.index("Obsidian")
            top = Path(*md_path.parts[: obsidian_idx + 2])  # .../Obsidian/<vault>
            if str(top).startswith("/sdcard/Obsidian"):
                return str(top)
        except ValueError:
            pass
        vault = str(md_path.parent)
        if vault.startswith("/sdcard/Obsidian"):
            return vault
    return DEFAULT_VAULT


def calendar_id(serial: str, cfg: dict[str, str] | None = None) -> str:
    """Resolve the Google-synced calendar id used for seeded events.

    Priority: config `calendar id` -> the visible Google calendar's _id
    (content://com.android.calendar/calendars) -> DEFAULT_CALENDAR_ID.
    """
    if cfg and cfg.get(CFG_KEY_CALENDAR_ID):
        return cfg[CFG_KEY_CALENDAR_ID]
    rc, out = adb(
        serial, "shell",
        "content", "query", "--uri", "content://com.android.calendar/calendars",
        "--projection", "_id:account_name:calendar_displayName:visible",
    )
    if rc == 0 and out:
        # content query rows look like: Row: 0 _id=16, account_name=x@gmail.com, ...
        best = None
        for line in out.splitlines():
            if "Row:" not in line or "_id=" not in line:
                continue
            rid = _field(line, "_id")
            account = _field(line, "account_name")
            visible = _field(line, "visible")
            if not rid:
                continue
            if "gmail.com" in (account or "") or "google.com" in (account or ""):
                return rid  # prefer the Google account calendar
            if visible in ("1", "true") and best is None:
                best = rid
        if best:
            return best
        first = _first_id(out)
        if first:
            return first
    return DEFAULT_CALENDAR_ID


def contact_email(cfg: dict[str, str] | None = None) -> str:
    """Resolve the fabricated persona contact email (config override only)."""
    if cfg and cfg.get(CFG_KEY_CONTACT_EMAIL):
        return cfg[CFG_KEY_CONTACT_EMAIL]
    return DEFAULT_CONTACT_EMAIL


def _field(row: str, name: str) -> str | None:
    """Pull `name=value` out of a `content query` Row line (comma-separated)."""
    for part in row.split(","):
        part = part.strip()
        if part.startswith(name + "="):
            return part[len(name) + 1:].strip()
    return None


def _first_id(out: str) -> str | None:
    for line in out.splitlines():
        if "_id=" in line:
            rid = _field(line, "_id")
            if rid:
                return rid
    return None


@lru_cache(maxsize=None)
def _cached_vault(serial: str, cfg_tuple: tuple | None) -> str:
    return vault_path(serial, dict(cfg_tuple) if cfg_tuple else None)


@lru_cache(maxsize=None)
def _cached_calendar(serial: str, cfg_tuple: tuple | None) -> str:
    return calendar_id(serial, dict(cfg_tuple) if cfg_tuple else None)
