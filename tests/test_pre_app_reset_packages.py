"""Pre-run force-stop of a task's own apps (the BookMyShow 400 fix).

The runner already force-stopped whatever was in the FOREGROUND before a task began, which
is enough only when the app that task needs happened to be on screen last. When it was
BACKGROUNDED it was never touched, and the task's `open_app` then *resumed* its stale
screen instead of cold-starting it.

Measured 2026-09-22 on `hard__bookmyshow__005`: row 10 left BookMyShow on the seat-selection
page, and row 6's `open_app` three hours later resumed that dead booking, which the app
answered with "Sorry! Request failed ... (Error code: 400)" at step 2 -- before the agent
had done anything. The fix force-stops the task's own apps (the dataset's `apps` field,
resolved to packages) before the agent starts.

These tests pin the pure logic: name -> package resolution, the best-effort stop contract,
and that the batch runner actually passes the resolved packages through.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from androidlife import adb, task_batch
from androidlife.app_packages import BENCHMARK_APPS, packages_for


def test_packages_for_resolves_a_tasks_apps_in_order() -> None:
    assert packages_for(["BookMyShow", "Telegram"]) == ["com.bt.bms", "org.telegram.messenger"]


def test_packages_for_de_duplicates_shared_packages() -> None:
    """Google Slides/Docs/Sheets/Meet all include com.google.android.apps.docs."""
    got = packages_for(["Google Docs", "Google Sheets"])
    assert got.count("com.google.android.apps.docs") == 1
    assert got[0] == "com.google.android.apps.docs.editors.docs"


def test_packages_for_skips_unknown_names_rather_than_raising() -> None:
    """A typo in the hand-authored dataset must not break a run."""
    assert packages_for(["Not An App", "Telegram"]) == ["org.telegram.messenger"]
    assert packages_for([]) == []


def test_every_benchmark_app_resolves() -> None:
    """Each declared app must map to at least one package, or its tasks get no reset."""
    for app in BENCHMARK_APPS:
        assert packages_for([app]), f"{app} has no packages"


def test_app_audit_and_the_runner_share_one_map() -> None:
    """Two copies of this map would drift; the audit imports the shared one."""
    import importlib.util

    tool = Path(__file__).resolve().parents[1] / "scripts" / "tools" / "app_audit.py"
    spec = importlib.util.spec_from_file_location("app_audit", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.BENCHMARK_APPS is BENCHMARK_APPS


# --- stop_packages: best-effort, and never stops something protected ----------------


def test_stop_packages_skips_protected_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    """A system package must never be force-stopped, even if a task named it."""
    stopped_calls: list[str] = []
    monkeypatch.setattr(adb, "force_stop_app", lambda _s, pkg: stopped_calls.append(pkg))
    # com.android.systemui is excluded by adb.should_force_stop.
    got = adb.stop_packages("S", ["com.android.systemui", "com.bt.bms"])
    assert got == ["com.bt.bms"]
    assert stopped_calls == ["com.bt.bms"]


def test_stop_packages_is_best_effort_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """An uninstalled candidate must not abort the run; the rest still get stopped."""
    def fake(_serial: str, package: str) -> None:
        if package == "in.swiggy.android":
            raise RuntimeError("package not found")

    monkeypatch.setattr(adb, "force_stop_app", fake)
    got = adb.stop_packages("S", ["in.swiggy.android", "com.bt.bms"])
    assert got == ["com.bt.bms"]


def test_stop_packages_handles_empty_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb, "force_stop_app", lambda _s, _p: None)
    assert adb.stop_packages("S", []) == []
    assert adb.stop_packages("S", None) == []


def test_stop_packages_reports_exactly_what_it_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb, "force_stop_app", lambda _s, _p: None)
    got = adb.stop_packages("S", ["com.bt.bms", "org.telegram.messenger"])
    assert got == ["com.bt.bms", "org.telegram.messenger"]


# --- the batch runner must actually pass them through -------------------------------


def _args():
    """The real parsed namespace, so no attribute can go missing."""
    return task_batch.build_parser().parse_args([
        "--serial", "S",
        "--llm-upstream-base", "http://localhost:1234/v1",
        "--model", "m",
    ])


def _real_task(task_id: str) -> dict:
    """A real dataset task, so the command builder gets every field it expects."""
    root = Path(__file__).resolve().parents[1]
    dataset = task_batch.load_json_object(
        str(root / "benchmarks" / "androidlife-530" / "AndroidLife_public_v2.json")
    )
    return next(t for t in dataset["tasks"] if t["task_id"] == task_id)


def _command_for(task: dict) -> list[str]:
    command, _label = task_batch.build_run_command(
        _args(), task, "do the thing", 9999,
        repeat_index=0, repeats_total=1, cfg={}, task_vars={},
    )
    return command


def test_run_command_passes_the_task_apps_for_force_stop() -> None:
    """The real BookMyShow task must hand the runner com.bt.bms to force-stop."""
    cmd = _command_for(_real_task("hard__bookmyshow__005"))
    assert "--pre-app-reset-packages" in cmd
    assert cmd[cmd.index("--pre-app-reset-packages") + 1] == "com.bt.bms,org.telegram.messenger"


def test_run_command_omits_the_flag_when_a_task_names_no_apps() -> None:
    """No apps -> nothing to force-stop; the flag must be omitted, not passed empty."""
    task = dict(_real_task("hard__bookmyshow__005"))
    task.pop("apps", None)
    cmd = _command_for(task)
    assert "--pre-app-reset-packages" not in cmd


def test_run_command_omits_the_flag_for_only_unknown_apps() -> None:
    task = dict(_real_task("hard__bookmyshow__005"))
    task["apps"] = ["Totally Unknown"]
    cmd = _command_for(task)
    assert "--pre-app-reset-packages" not in cmd


def test_every_public_task_passes_a_resolvable_package() -> None:
    """Every task declares apps, so every task's run must carry the force-stop list."""
    root = Path(__file__).resolve().parents[1]
    tasks = task_batch.load_json_object(
        str(root / "benchmarks" / "androidlife-530" / "AndroidLife_public_v2.json")
    )["tasks"]
    assert tasks, "dataset unexpectedly empty"
    for task in tasks:
        packages = packages_for(task.get("apps") or [])
        assert packages, f"{task['task_id']} declares {task.get('apps')} but resolves no package"
