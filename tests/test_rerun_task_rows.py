"""Tests for the bash launcher ``scripts/run/rerun_task_rows.sh``.

The launcher owns three decisions that are easy to get silently wrong and expensive to get
wrong, because a bad batch burns hours of single-device time:

  * which model a local row is actually served by (a stale ``llama-server`` on the shared
    port answers a readiness probe seen only as "something is listening");
  * whether a run root that produced nothing looks like a scored run; and
  * the preset -> alias map, which has to agree with ``serve_gguf.sh``.

Each helper is extracted from the script by name and exercised in bash, so the tests pin the
shell behaviour itself rather than a Python re-implementation of it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPO_ROOT / "scripts" / "run" / "rerun_task_rows.sh"
SERVE = REPO_ROOT / "scripts" / "llm" / "serve_gguf.sh"


def _fn(name: str) -> str:
    """The text of a top-level ``name() { ... }`` function in the launcher."""
    text = LAUNCHER.read_text()
    m = re.search(rf"^{name}\(\) \{{.*?^\}}$", text, re.DOTALL | re.MULTILINE)
    assert m, f"{name}() not found in {LAUNCHER.name}"
    return m.group(0)


def _run(body: str, *fns: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Source the given launcher functions, then run `body` under bash."""
    prelude = "\n".join(_fn(f) for f in fns)
    # check=False is deliberate: several tests assert on a non-zero exit.
    return subprocess.run(
        ["bash", "-c", prelude + "\n" + body],
        capture_output=True, text=True, cwd=cwd or REPO_ROOT, check=False,
    )


# ---- preset_alias must mirror serve_gguf.sh ---------------------------------


def _serve_gguf_aliases() -> dict[str, str]:
    """preset-pattern -> alias, parsed out of serve_gguf.sh's `case "$SPEC"` block."""
    out: dict[str, str] = {}
    for m in re.finditer(r"^  ([\w.\-|]+)\)\s*\n(.*?)^\s{2,4};;", SERVE.read_text(), re.MULTILINE | re.DOTALL):
        alias = re.search(r'ALIAS="\$\{ALIAS:-([^}]*)\}"', m.group(2))
        if alias:
            for pattern in m.group(1).split("|"):
                out[pattern] = alias.group(1)
    return out


def test_preset_alias_agrees_with_serve_gguf_for_every_preset() -> None:
    """Adding a preset to serve_gguf.sh without updating preset_alias must FAIL here.

    Otherwise that preset's rows silently lose the wrong-model guard, which is the failure
    the guard exists to prevent (measured 2026-09-22: row 13 leaves Bonsai-2-27B on 8088
    while row 12 needs gemma-4-E2B-it).

    Note the output is bracket-wrapped: an unguarded preset prints an EMPTY line, and a
    plain `.split()` drops those, which makes `zip` truncate and the loop skip the very
    rows this test exists to catch.
    """
    aliases = _serve_gguf_aliases()
    assert aliases, "parsed no presets out of serve_gguf.sh - the case block moved"
    body = "\n".join(f'printf "[%s]\\n" "$(preset_alias {p})"' for p in aliases)
    r = _run(body, "preset_alias")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert len(lines) == len(aliases), f"expected one line per preset, got {lines}"
    for (pattern, want), line in zip(aliases.items(), lines):
        assert line == f"[{want}]", (
            f"preset_alias({pattern}) = {line!r}, but serve_gguf.sh advertises {want!r}"
        )


def test_preset_alias_returns_empty_for_an_unknown_preset() -> None:
    """Unknown must mean "guard disabled", never a wrong alias to compare against."""
    r = _run('printf "[%s]\\n" "$(preset_alias totally-unknown)"', "preset_alias")
    assert r.stdout.strip() == "[]"


def test_server_model_is_empty_when_nothing_is_listening() -> None:
    """A free port must not look like a server advertising an empty model name."""
    r = _run(
        'LOCAL_UPSTREAM="http://127.0.0.1:59999"; printf "[%s]\\n" "$(server_model)"',
        "server_model",
    )
    assert r.stdout.strip() == "[]"


# ---- flag_aborted_root ------------------------------------------------------


def test_flag_aborted_root_leaves_a_real_result_alone(tmp_path: Path) -> None:
    """A root with output.json is a model run and must never be renamed."""
    root = tmp_path / "runA"
    (root / "day1" / "task-x").mkdir(parents=True)
    (root / "day1" / "task-x" / "output.json").write_text("{}")
    r = _run(f'flag_aborted_root "{root}" task-x', "flag_aborted_root")
    assert r.returncode == 0, r.stderr
    assert root.is_dir(), "a scored run must keep its name"


def test_flag_aborted_root_marks_a_seed_gate_abort(tmp_path: Path) -> None:
    """No result + SEED_GATE_FAILED -> .aborted-seedgate, diagnostics kept."""
    root = tmp_path / "runB"
    root.mkdir()
    (root / "SEED_GATE_FAILED").write_text("seed gate FAILED")
    r = _run(f'flag_aborted_root "{root}" task-x', "flag_aborted_root")
    assert r.returncode == 0, r.stderr
    assert not root.exists(), "the dead root must no longer look like a run"
    moved = tmp_path / "runB.aborted-seedgate"
    assert moved.is_dir()
    assert (moved / "SEED_GATE_FAILED").exists(), "the diagnostic must survive"


def test_flag_aborted_root_marks_a_harness_death(tmp_path: Path) -> None:
    """No result and no seed-gate file -> .aborted-incomplete (the batch died mid-run)."""
    root = tmp_path / "runC"
    root.mkdir()
    r = _run(f'flag_aborted_root "{root}" task-x', "flag_aborted_root")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "runC.aborted-incomplete").is_dir()


def test_flag_aborted_root_still_flags_when_the_slug_is_unknown(tmp_path: Path) -> None:
    """An abort before the task dir is known must still be flagged, not skipped.

    An empty slug must not make the glob match nothing *and* return early, or the root most
    likely to be debris -- one that never got as far as a task dir -- is the one left behind.
    """
    root = tmp_path / "runD"
    root.mkdir()
    r = _run(f'flag_aborted_root "{root}" ""', "flag_aborted_root")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "runD.aborted-incomplete").is_dir()


def test_flag_aborted_root_does_not_clobber_an_existing_flag(tmp_path: Path) -> None:
    """Re-flagging the same reason must not overwrite the earlier diagnostic."""
    (tmp_path / "runE.aborted-incomplete").mkdir()
    root = tmp_path / "runE"
    root.mkdir()
    r = _run(f'flag_aborted_root "{root}" task-x', "flag_aborted_root")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "runE.aborted-incomplete").is_dir(), "the first diagnostic must survive"
    extras = [p for p in tmp_path.iterdir() if p.name.startswith("runE.aborted-incomplete.")]
    assert extras, "the second flag must go to a distinct name"
