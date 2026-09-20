"""Pytest coverage for the pre-launch SEED GATE.

Why this file exists
--------------------
A stale seed does not make a run score *low* -- it makes it score *wrong*. The clearest
recorded case: `easy__calendar__002` passed 5 times because the reset had run the previous
day, so the seeded conflict pair sat on the run day instead of "tomorrow" and the agent
correctly reported no conflicts. A vacuous PASS is indistinguishable from a real one in a
report, so the failure mode is silent, repeated, and corrupts comparability across runs.

The detection already existed (`reset_phone.py --verify-only` -> `verify_calendar_anchors`).
The defect was that nothing FORCED it to run before a scored task. These tests pin that
forcing behaviour, so the gate cannot quietly regress back to an optional manual step.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from androidlife import task_batch


def _fake_run(output: str, returncode: int = 0):
    """Return a subprocess.run stand-in that reports `output` on stdout."""
    def run(command, check=False, **kwargs):
        return SimpleNamespace(returncode=returncode, stdout=output, stderr="")
    return run


def test_gate_off_does_not_shell_out(tmp_path, monkeypatch) -> None:
    """--seed-gate off must not invoke the reset script at all."""
    calls: list[list[str]] = []

    def run(command, check=False, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(task_batch.subprocess, "run", run)
    task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "off", 600.0)
    assert calls == []


def test_gate_passes_on_result_pass(tmp_path, monkeypatch) -> None:
    """A RESULT PASS verdict lets the batch proceed and writes no failure marker."""
    monkeypatch.setattr(task_batch.subprocess, "run",
                        _fake_run("  PASS seed stamp: ran today\nRESULT PASS\n"))
    task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "enforce", 600.0)
    assert not (tmp_path / "SEED_GATE_FAILED").exists()


def test_gate_aborts_on_result_fail(tmp_path, monkeypatch) -> None:
    """enforce mode must stop the batch (exit 5) and leave evidence in the run root."""
    monkeypatch.setattr(task_batch.subprocess, "run", _fake_run(
        "  FAIL seed stamp: last verified --apply was 2026-09-19, today is 2026-09-21\n"
        "RESULT FAIL\n"))
    with pytest.raises(SystemExit) as excinfo:
        task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "enforce", 600.0)
    assert excinfo.value.code == 5
    marker = tmp_path / "SEED_GATE_FAILED"
    assert marker.exists()
    assert "seed gate FAILED" in marker.read_text(encoding="utf-8")


def test_gate_warn_mode_reports_but_continues(tmp_path, monkeypatch) -> None:
    """warn mode is for transport debugging: it prints the verdict and does not abort."""
    monkeypatch.setattr(task_batch.subprocess, "run", _fake_run("RESULT FAIL\n"))
    task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "warn", 600.0)
    assert not (tmp_path / "SEED_GATE_FAILED").exists()


def test_gate_treats_missing_verdict_as_failure(tmp_path, monkeypatch) -> None:
    """A gate that produced no RESULT line (crashed, killed) must FAIL, never silently pass.

    Fail-closed matters more than fail-accurate here: an unverifiable baseline is not a
    usable baseline, and defaulting to 'assume fine' is how a bad run gets recorded.
    """
    monkeypatch.setattr(task_batch.subprocess, "run",
                        _fake_run("Traceback (most recent call last): ...\n"))
    with pytest.raises(SystemExit) as excinfo:
        task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "enforce", 600.0)
    assert excinfo.value.code == 5


def test_gate_aborts_on_timeout(tmp_path, monkeypatch) -> None:
    """A hung gate is a failure: the batch must not start on an unverified device."""
    def run(command, check=False, **kwargs):
        raise subprocess.TimeoutExpired(cmd=command, timeout=600.0)

    monkeypatch.setattr(task_batch.subprocess, "run", run)
    with pytest.raises(SystemExit) as excinfo:
        task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "enforce", 600.0)
    assert excinfo.value.code == 5


def test_gate_tolerates_partial_subprocess_result(tmp_path, monkeypatch) -> None:
    """A stand-in result without `stderr` must FAIL cleanly, not raise AttributeError."""
    monkeypatch.setattr(task_batch.subprocess, "run",
                        lambda command, check=False, **kw: SimpleNamespace(returncode=0, stdout=""))
    with pytest.raises(SystemExit) as excinfo:
        task_batch.run_seed_gate("device-1", tmp_path, "public_v2", "enforce", 600.0)
    assert excinfo.value.code == 5
