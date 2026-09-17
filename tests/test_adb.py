"""Pytest coverage for ADB output parsing and real ADB command execution (wired and wireless)."""

from __future__ import annotations

import subprocess
import time

import pytest
from conftest import first_adb_device, requires_device, requires_device_drive

from androidlife import adb
from androidlife.adb import adb_cmd, adb_shell, capture_sample, get_foreground_package, parse_battery_output, parse_thermal_output, reset_app_state, should_force_stop

DEVICE_SERIAL = first_adb_device()


def test_parse_battery_output_normalizes_fields() -> None:
    """`dumpsys battery` text is parsed into normalized numeric/bool fields (temps in °C, tenths converted)."""
    text = """
level: 79
temperature: 320
PhoneTemp: 345
Charge counter: 4123456
AC powered: false
USB powered: true
""".strip()
    parsed = parse_battery_output(text)
    assert parsed["level_pct"] == 79
    assert parsed["battery_temp_c"] == 32.0
    assert parsed["vendor_phone_temp_c"] == 34.5
    assert parsed["charge_counter_uah"] == 4123456
    assert parsed["usb_powered"] is True


def test_parse_thermal_output_extracts_hal_temperatures() -> None:
    """`dumpsys thermalservice` text yields a thermal status code plus a per-sensor HAL temperature map."""
    text = """
Thermal Status: 2
Current temperatures from HAL:
Temperature{mValue=41.5, mType=0, mName=CPU, mStatus=0}
Temperature{mValue=36.2, mType=0, mName=BATTERY, mStatus=0}
Current cooling devices from HAL:
""".strip()
    parsed = parse_thermal_output(text)
    assert parsed["thermal_status_code"] == 2
    assert parsed["hal_temperatures_c"]["CPU"]["value_c"] == 41.5
    assert parsed["hal_temperatures_c"]["BATTERY"]["status_code"] == 0


def test_capture_app_battery_maps_uids_to_packages(monkeypatch) -> None:
    """capture_app_battery maps `UID u0a<id>` batterystats entries to packages via `pm list packages -U`."""
    batterystats = """
  Estimated power use (mAh):
    Capacity: 3780, Computed drain: 3074, actual drain: 3062-3100
    Global
      screen: 2537 apps: 2537 duration: 6h 38m 45s
    UID u0a122: 1111 fg: 207 ( screen=891 cpu=97.0 )
    UID u0a150: 690 fg: 4.12 ( screen=681 cpu=8.94 )
    UID u0a209: 51.9 fg: 3.70 ( screen=46.1 cpu=5.21 )
    UID 1000: 443 ( cpu=435 )
    UID 0: 314 ( cpu=313 )
""".strip()
    packages = "\n".join([
        "package:com.google.android.apps.docs uid:10209",
        "package:com.google.android.apps.photos uid:10195",
        "package:org.telegram.messenger uid:10398",
        "package:com.android.systemui uid:1000",
    ])
    monkeypatch.setattr(adb, "adb_shell", lambda serial, command: batterystats if "batterystats" in command else packages)
    result = adb.capture_app_battery("device-1")
    assert result == {"com.google.android.apps.docs": 51.9}


def test_capture_app_battery_returns_empty_on_adb_failure(monkeypatch) -> None:
    """A failing adb call yields an empty dict instead of raising (best-effort metric)."""
    monkeypatch.setattr(adb, "adb_shell", lambda serial, command: (_ for _ in ()).throw(subprocess.CalledProcessError(1, "adb")))
    assert adb.capture_app_battery("device-1") == {}


def test_adb_cmd_passes_through_wired_usb_serial_verbatim() -> None:
    """A wired USB device serial (alphanumeric, no colon) is forwarded as-is to `adb -s`."""
    assert adb_cmd("R58N801XXXX", "shell", "dumpsys battery") == [
        "adb", "-s", "R58N801XXXX", "shell", "dumpsys battery",
    ]


def test_adb_cmd_passes_through_wireless_ip_port_serial_verbatim() -> None:
    """A wireless ADB serial (`ip:port`, e.g. over Tailscale or LAN) is forwarded the same way as a wired one."""
    assert adb_cmd("100.75.134.64:5555", "shell", "dumpsys battery") == [
        "adb", "-s", "100.75.134.64:5555", "shell", "dumpsys battery",
    ]


@requires_device
def test_adb_shell_raises_for_unreachable_serial() -> None:
    """A real `adb` invocation against a serial that doesn't exist fails loudly instead of hanging or returning junk."""
    with pytest.raises(subprocess.CalledProcessError):
        adb_shell("no-such-device:5555", "dumpsys battery")


def test_should_force_stop_excludes_launcher_systemui_and_portal() -> None:
    """The launcher, systemui, and mobilerun's own Portal are never force-stopped, across common OEM package names."""
    assert should_force_stop("com.android.launcher") is False
    assert should_force_stop("com.oneplus.launcher") is False
    assert should_force_stop("com.sec.android.app.launcher") is False
    assert should_force_stop("com.android.systemui") is False
    assert should_force_stop("com.mobilerun.portal") is False


def test_should_force_stop_allows_regular_apps() -> None:
    """An ordinary user-facing app is eligible for the between-task force-stop reset."""
    assert should_force_stop("com.google.android.youtube") is True
    assert should_force_stop("com.google.android.gm") is True


def test_get_foreground_package_parses_mcurrentfocus(monkeypatch) -> None:
    """get_foreground_package extracts the package name from a real `dumpsys window` mCurrentFocus line."""
    dumpsys_output = "  mCurrentFocus=Window{df5fae u0 com.android.launcher/com.android.launcher.Launcher}\n"
    monkeypatch.setattr(adb, "adb_shell", lambda serial, command: dumpsys_output)
    assert get_foreground_package("device-1") == "com.android.launcher"


def test_get_foreground_package_returns_none_when_unparseable(monkeypatch) -> None:
    """A dumpsys output with no recognizable mCurrentFocus line yields None instead of raising."""
    monkeypatch.setattr(adb, "adb_shell", lambda serial, command: "mCurrentFocus=null\n")
    assert get_foreground_package("device-1") is None


@requires_device_drive
def test_reset_app_state_force_stops_foreground_app_and_returns_home() -> None:
    """Against a real device: launch YouTube, confirm it's foreground, then reset_app_state force-stops it and lands on the launcher."""
    assert DEVICE_SERIAL is not None
    subprocess.run(
        ["adb", "-s", DEVICE_SERIAL, "shell", "am", "start", "-n", "com.google.android.youtube/com.google.android.youtube.HomeActivity"],
        capture_output=True, timeout=10, check=False,
    )
    time.sleep(2)
    assert get_foreground_package(DEVICE_SERIAL) == "com.google.android.youtube"

    stopped = reset_app_state(DEVICE_SERIAL)
    assert stopped == "com.google.android.youtube"

    time.sleep(1)
    assert get_foreground_package(DEVICE_SERIAL) != "com.google.android.youtube"



def test_is_tcp_serial_detects_host_port_only() -> None:
    """Only `host:port` serials are treated as reconnectable TCP transports; USB serials are not."""
    assert adb.is_tcp_serial("100.108.15.119:5555") is True
    assert adb.is_tcp_serial("localhost:5555") is True
    assert adb.is_tcp_serial("RS7XKZDI1234") is False
    assert adb.is_tcp_serial("emulator-5554") is False


def test_probe_device_true_only_when_adb_reports_device_state(monkeypatch) -> None:
    """`device offline` (rc=1) is not healthy; only an explicit `device` state is."""
    monkeypatch.setattr(adb.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "device\n", ""))
    assert adb.probe_device("device-1") is True

    monkeypatch.setattr(adb.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 1, "", "error: device offline"))
    assert adb.probe_device("device-1") is False


def test_probe_device_false_when_adb_hangs(monkeypatch) -> None:
    """A frozen transport must fail the probe, not block the caller's retry budget."""

    def _hang(*_args: object, **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired("adb", 5)

    monkeypatch.setattr(adb.subprocess, "run", _hang)
    assert adb.probe_device("device-1") is False


def test_adb_connect_rearms_tcp_serials_only(monkeypatch) -> None:
    """adb_connect issues `adb connect host:port` for TCP serials and is a no-op for USB ones."""
    calls: list[list[str]] = []

    def _run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, f"connected to {cmd[-1]}", "")

    monkeypatch.setattr(adb.subprocess, "run", _run)

    assert adb.adb_connect("RS7XKZDI1234") is False
    assert calls == []

    assert adb.adb_connect("100.108.15.119:5555") is True
    assert calls == [["adb", "connect", "100.108.15.119:5555"]]


def test_wait_for_device_recovers_after_reconnect(monkeypatch) -> None:
    """A drop that comes back after a single `adb connect` is reported healthy (the Tailscale flap)."""
    probes = {"n": 0}

    def _probe(_serial: str, **_kwargs: object) -> bool:
        probes["n"] += 1
        return probes["n"] > 1  # dead on the first probe, alive after the reconnect

    connects: list[str] = []
    monkeypatch.setattr(adb, "probe_device", _probe)
    monkeypatch.setattr(adb, "adb_connect", lambda serial, **_k: bool(connects.append(serial)) or True)
    monkeypatch.setattr(adb.time, "sleep", lambda _seconds: None)

    assert adb.wait_for_device("100.108.15.119:5555", timeout=30.0) is True
    assert connects == ["100.108.15.119:5555"]


def test_wait_for_device_gives_up_once_the_budget_elapses(monkeypatch) -> None:
    """A genuinely dead device returns False after the timeout instead of looping forever."""
    clock = {"t": -100.0}

    def _monotonic() -> float:
        clock["t"] += 100.0
        return clock["t"]

    monkeypatch.setattr(adb, "probe_device", lambda *_a, **_k: False)
    monkeypatch.setattr(adb, "adb_connect", lambda *_a, **_k: False)
    monkeypatch.setattr(adb.time, "monotonic", _monotonic)
    monkeypatch.setattr(adb.time, "sleep", lambda _seconds: None)

    assert adb.wait_for_device("100.108.15.119:5555", timeout=5.0) is False


@requires_device
def test_capture_sample_against_real_attached_device() -> None:
    """capture_sample runs real `adb shell` calls against whatever device is attached and returns sane, parsed values.

    The currently attached test device connects over wireless ADB (an `ip:port` serial), but adb_cmd/adb_shell apply
    no special-casing between connection types, so this same path covers a wired USB serial identically.
    """
    assert DEVICE_SERIAL is not None
    sample = capture_sample(DEVICE_SERIAL)
    assert 0 <= sample["battery"]["level_pct"] <= 100
    assert isinstance(sample["thermal"]["hal_temperatures_c"], dict)
    assert sample["thermal"]["hal_temperatures_c"]
    assert "timestamp_utc" in sample
