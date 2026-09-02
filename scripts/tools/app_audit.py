#!/usr/bin/env python3
"""Audit a device for the apps the benchmark needs (device-readiness check)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

# The 32 apps the runnable 530-task dataset targets, mapped to the Android
# packages that commonly provide them (most common first). Ordering = display
# order in the report. Extend the candidate lists if your OEM uses a different
# package (run `adb shell pm list packages` to find it).
BENCHMARK_APPS: dict[str, list[str]] = {
    "Phone": [
        "com.google.android.dialer",
        "com.android.dialer",
        "com.oneplus.dialer",
        "com.samsung.android.dialer",
        "com.xiaomi.xmsf",  # MIUI dialer
    ],
    "Messages": [
        "com.google.android.apps.messaging",
        "com.android.messaging",
        "com.samsung.android.messaging",
    ],
    "Contacts": [
        "com.google.android.contacts",
        "com.android.contacts",
        "com.samsung.android.app.contacts",
    ],
    "Calendar": [
        "com.google.android.calendar",
        "com.android.calendar",
        "com.samsung.android.calendar",
    ],
    "Gmail": ["com.google.android.gm"],
    "Chrome": ["com.android.chrome", "com.google.android.apps.chrome"],
    "Google Search": ["com.google.android.googlequicksearchbox"],
    "Google Maps": ["com.google.android.apps.maps"],
    "Google Photos": ["com.google.android.apps.photos"],
    "Gallery": [
        "com.oneplus.gallery",
        "com.coloros.gallery3d",
        "com.android.gallery3d",
    ],
    "Google Drive": ["com.google.android.apps.docs"],
    "Google Docs": [
        "com.google.android.apps.docs.editors.docs",
        "com.google.android.apps.docs",
    ],
    "Google Sheets": [
        "com.google.android.apps.docs.editors.sheets",
        "com.google.android.apps.docs",
    ],
    "Google Slides": [
        "com.google.android.apps.docs.editors.slides",
        "com.google.android.apps.docs",
    ],
    "Google Meet": [
        "com.google.android.apps.tachyon",  # Meet's package since the Duo/Meet merge (2022)
        "com.google.android.apps.meetings",
        "com.google.android.apps.docs",
    ],
    "Camera": [
        "com.oneplus.camera",
        "com.oplus.camera",
        "com.android.camera",
        "com.sec.android.app.camera",
        "com.google.android.GoogleCamera",
        "com.miui.camera",
    ],
    "Files": [
        "com.google.android.apps.nbu.files",
        "com.android.documentsui",
        "com.oneplus.filemanager",
    ],
    "Clock": [
        "com.google.android.deskclock",
        "com.android.deskclock",
        "com.oneplus.deskclock",
        "com.oplus.deskclock",
        "com.sec.android.app.clockpackage",
    ],
    "Calculator": [
        "com.google.android.calculator",
        "com.android.calculator2",
        "com.oneplus.calculator",
        "com.sec.android.app.popupcalculator",
    ],
    "Notes": [
        "com.oneplus.note",
        "com.google.android.keep",
        "com.samsung.android.app.notes",
        "com.miui.notes",
    ],
    "Obsidian": ["md.obsidian"],
    "YouTube": ["com.google.android.youtube"],
    "Music": [
        "com.google.android.apps.youtube.music",
        "com.android.music",
        "com.oneplus.music",
        "com.sec.android.app.music",
    ],
    "Telegram": ["org.telegram.messenger"],
    "Settings": ["com.android.settings"],
    "Weather": [
        "net.oneplus.weather",
        "com.coloros.weather.service",
        "com.google.android.apps.weather",
        "com.android.weather",
    ],
    "Swiggy": ["in.swiggy.android"],
    "Prime Video": ["com.amazon.avod.thirdpartyclient"],
    "MakeMyTrip": ["com.makemytrip"],
    "BookMyShow": ["com.bt.bms"],
    "MSN News": ["com.microsoft.amp.apps.bingnews"],
    "Amazon Shopping": ["in.amazon.mShop.android.shopping"],
}

# Apps referenced by docs/future directions that are NOT expected on a fresh
# device (need install/provision before those tasks can run). Google Meet is now
# detected first-class via com.google.android.apps.tachyon (the renamed Duo/Meet
# package), so it is no longer in the optional/missing list here.
OPTIONAL_APPS: dict[str, str] = {}


def adb_devices() -> list[str]:
    """Return the list of connected ADB device serials (state=device)."""
    try:
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=15)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    out: list[str] = []
    for line in res.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1] == "device":
            out.append(parts[0])
    return out


def installed_packages(serial: str) -> set[str]:
    """Return the set of package names installed on the device."""
    res = subprocess.run(
        ["adb", "-s", serial, "shell", "pm", "list", "packages"],
        capture_output=True, text=True, timeout=60,
    )
    pkgs: set[str] = set()
    for line in res.stdout.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            pkgs.add(line[len("package:"):])
    return pkgs


def audit(serial: str) -> dict:
    """Run the audit; return {app: {installed, matched_package}} + counts."""
    pkgs = installed_packages(serial)
    result: dict[str, dict] = {}
    for app, candidates in BENCHMARK_APPS.items():
        matched = next((p for p in candidates if p in pkgs), None)
        result[app] = {"installed": matched is not None, "package": matched}
    optional: dict[str, dict] = {}
    for app, pkg in OPTIONAL_APPS.items():
        optional[app] = {"installed": pkg in pkgs, "package": pkg}
    return {
        "serial": serial,
        "required": result,
        "optional": optional,
        "installed_count": sum(1 for v in result.values() if v["installed"]),
        "missing": [app for app, v in result.items() if not v["installed"]],
        "required_count": len(result),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a device for the benchmark's required apps.")
    ap.add_argument("--serial", default=None, help="ADB serial (default: auto-detect single device)")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of the report")
    args = ap.parse_args()

    serial = args.serial
    if not serial:
        devices = adb_devices()
        if not devices:
            print("FAIL: no ADB device connected. Plug in / pair the phone and retry.", file=sys.stderr)
            return 1
        if len(devices) > 1:
            print("FAIL: multiple devices connected; pass --serial explicitly. Found:", ", ".join(devices), file=sys.stderr)
            return 1
        serial = devices[0]

    data = audit(serial)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Benchmark app audit for {serial}: {data['installed_count']}/{data['required_count']} required apps installed")
        print()
        for app, info in data["required"].items():
            mark = "OK  " if info["installed"] else "MISS"
            pkg = info["package"] or "-"
            print(f"  [{mark}] {app:16s} {pkg}")
        if data["optional"]:
            print()
            print("Optional (not required for the core 530, but some tasks reference them):")
            for app, info in data["optional"].items():
                mark = "OK  " if info["installed"] else "MISS"
                print(f"  [{mark}] {app:16s} {info['package']}")
        if data["missing"]:
            print()
            print("MISSING required apps (install from Play Store before running those tasks):")
            for app in data["missing"]:
                print(f"  - {app}")
            return 1
        print()
        print("All required apps present - device is ready for benchmark runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
