"""Tests for seed_data.verify_day_seeds (device-state seed verification).

verify_day_seeds reads a day's manifest_index.json + per-task manifests and
checks every declared seed_device_path exists on the device via `adb shell ls`.
These tests monkeypatch the module's `adb` helper so no phone is needed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "seed_data.py"


@pytest.fixture(scope="module")
def seed_mod():
    spec = importlib.util.spec_from_file_location("seed_data", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seed_data"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_manifest(day_dir: Path, task_id: str, paths: list[str],
                    needs_ui: list[dict] | None = None) -> None:
    """Create a task manifest declaring seed_device_paths under a fake day dir."""
    task_dir = day_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "task_id": task_id,
        "day": 3,
        "seed_device_paths": {str(i): p for i, p in enumerate(paths)},
        "fabricated_seed_data": needs_ui or [],
    }
    (task_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture()
def fake_day(tmp_path):
    """A fake seeds/full_tasks/day_3 with an index + one task declaring 2 paths."""
    day_dir = tmp_path / "seeds" / "full_tasks" / "day_3"
    day_dir.mkdir(parents=True, exist_ok=True)
    index = {"schema_version": 1, "day": 3, "tasks": ["easy__fake__001"]}
    (day_dir / "manifest_index.json").write_text(json.dumps(index), encoding="utf-8")
    _write_manifest(day_dir, "easy__fake__001", ["/sdcard/A/file1.txt", "/sdcard/A/file2.txt"])
    return day_dir


def test_verify_day_seeds_pass_when_all_paths_present(tmp_path, monkeypatch, seed_mod, fake_day):
    """All declared seed paths exist on device -> exit 0."""

    def fake_adb(serial, *args):
        assert args[0] == "shell" and args[1] == "ls"
        return 0, "file1.txt"

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: fake_day)
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    assert seed_mod.verify_day_seeds("SERIAL", 3) == 0


def test_verify_day_seeds_fail_on_missing_path(tmp_path, monkeypatch, seed_mod, fake_day):
    """A declared seed path that is not on device -> exit 1, names the path."""

    def fake_adb(serial, *args):
        path = args[2].strip("'")
        if path == "/sdcard/A/file2.txt":
            return 0, "No such file or directory"
        return 0, path

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: fake_day)
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    assert seed_mod.verify_day_seeds("SERIAL", 3) == 1


def test_verify_day_seeds_quotes_paths_with_spaces(tmp_path, monkeypatch, seed_mod, fake_day):
    """Paths containing spaces are single-quote wrapped for the device shell."""
    seen: list[str] = []

    def fake_adb(serial, *args):
        seen.append(args[2])
        return 0, "file1.txt"

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: fake_day)
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    seed_mod.verify_day_seeds("SERIAL", 3)
    assert all("'" in a for a in seen), f"paths not quoted: {seen}"


def test_verify_day_seeds_skips_missing_manifest_index(tmp_path, monkeypatch, seed_mod):
    """No manifest_index.json -> warn + exit 0 (nothing to verify)."""

    def fake_adb(serial, *args):
        return 0, ""

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: tmp_path / "missing")
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    assert seed_mod.verify_day_seeds("SERIAL", 3) == 0


def test_verify_day_seeds_warns_on_needs_ui(tmp_path, monkeypatch, seed_mod, fake_day, capsys):
    """needs_ui seeds are flagged UNVERIFIED (not silently skipped) but don't fail."""
    # Add a needs_ui seed to the existing fake task's manifest.
    mf = fake_day / "easy__fake__001" / "manifest.json"
    man = json.loads(mf.read_text(encoding="utf-8"))
    man["fabricated_seed_data"] = [
        {"type": "drive_file", "status": "needs_ui",
         "value": "A 'Weekly Review' document to duplicate (operator/persona Drive)."},
    ]
    mf.write_text(json.dumps(man), encoding="utf-8")

    def fake_adb(serial, *args):
        assert args[0] == "shell" and args[1] == "ls"
        return 0, "file1.txt"

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: fake_day)
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    assert seed_mod.verify_day_seeds("SERIAL", 3) == 0  # warning, not a failure

    out = capsys.readouterr().out
    assert "UNVERIFIED" in out
    assert "easy__fake__001" in out
    assert "needs_ui" in out or "operator action" in out


def test_verify_day_seeds_no_unverified_when_none(tmp_path, monkeypatch, seed_mod, fake_day, capsys):
    """Tasks with no needs_ui seeds produce no UNVERIFIED block."""
    # fake_day's manifest has no fabricated_seed_data (defaults to []).

    def fake_adb(serial, *args):
        return 0, "file1.txt"

    monkeypatch.setattr(seed_mod, "day_seed_dir", lambda day: fake_day)
    monkeypatch.setattr(seed_mod, "adb", fake_adb)
    seed_mod.verify_day_seeds("SERIAL", 3)
    out = capsys.readouterr().out
    assert "UNVERIFIED" not in out
