"""Pytest coverage for scripts/tools/verify_task_vars.py.

Real subprocesses, no mocks — the tool is the launch-time guard that stands between a
drifted machine-local `config/user.yaml` and a whole batch re-running a known-bad value,
so it is exercised the way the launcher runs it.

Background: `hard__bookmyshow__005` renders `[cinema]`. Its fix landed in the shipped
default, `user_config.example` and both vars files, but the one file the runner actually
reads — `config/user.yaml` — is gitignored, so it kept `cinema: INOX Bhubaneswar` (not a
real BookMyShow listing) and silently overrode the corrected default. The runner guards a
*missing* placeholder but never a *wrong* one, so nothing caught it. Hence this tool.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "tools" / "verify_task_vars.py"
DATASET = REPO / "benchmarks" / "androidlife-530" / "AndroidLife_public_v2.json"
TASK = "hard__bookmyshow__005"


def run_tool(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--dataset", str(DATASET), "--task-id", TASK, *extra],
        capture_output=True, text=True, check=False, cwd=REPO,
    )


def test_passes_with_the_real_config() -> None:
    """The shipped/host config must resolve cleanly — otherwise every batch would refuse to start."""
    result = run_tool()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
    # The value the agent is actually handed must not be the placeholder that names a
    # cinema BookMyShow does not list.
    assert "INOX Bhubaneswar" not in result.stdout


def test_lists_every_placeholder_so_the_launch_log_is_auditable() -> None:
    result = run_tool()
    assert result.returncode == 0, result.stderr
    for placeholder in ("cinema", "ticket price", "contact"):
        assert f"{placeholder} =" in result.stdout


def test_fails_on_a_known_bad_value(tmp_path: Path) -> None:
    """Reproduces the exact regression: a config that resolves, but to the wrong cinema."""
    bad = tmp_path / "user.yaml"
    bad.write_text("cinema: INOX Bhubaneswar\n", encoding="utf-8")
    result = run_tool("--config", str(bad))
    assert result.returncode == 1
    assert "known-bad" in result.stderr
    assert "INOX Bhubaneswar" in result.stderr


def test_ignores_an_unrelated_known_bad_key(tmp_path: Path) -> None:
    """Only the *task's* placeholders are judged — a stray key elsewhere must not fail the launch."""
    cfg = tmp_path / "user.yaml"
    cfg.write_text("cinema: INOX: Symphony Mall\nsize threshold: INOX Bhubaneswar\n", encoding="utf-8")
    result = run_tool("--config", str(cfg))
    assert result.returncode == 0, result.stdout + result.stderr


def test_unknown_task_id_fails() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--dataset", str(DATASET), "--task-id", "not__a__task"],
        capture_output=True, text=True, check=False, cwd=REPO,
    )
    assert result.returncode == 1
    assert "not in" in result.stderr
