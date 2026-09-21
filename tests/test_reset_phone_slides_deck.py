"""Regression tests for the Q3_Review.pptx restore + gate in reset_phone.

Why this exists (redo.md 5): the deck for easy__google-slides__001 is a hand-built
ground-truth fixture with no generator, and it lived only as a device file plus an
uncommitted copy. Two presentations both named "Q3 Review" were in circulation, the
device kept the 1-slide one, and six runs in Aug/Sep 2026 self-reported a PASS against
it. The fix has two halves, and these tests only cover the first:

  * reset_phone.py re-pushes the version-controlled deck whenever the device copy is
    missing or the wrong length, then asserts it (this file); and
  * the grader checks the agent's REPLY against the same expected count
    (tests/test_answer_checks.py).

The fake ADB below is a tiny device model: a pull renders the deck the "device" holds,
a push overwrites it. That is enough to pin the behaviour that matters -- a wrong deck
gets replaced, a right one is left alone, and a broken canonical fixture is never
pushed over a working device.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "reset_phone.py"

DECK_REL = "assets/seeds/public/Q3_Review.pptx"
DECK_REMOTE = "/sdcard/Download/Q3_Review.pptx"


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("reset_phone", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reset_phone"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_pptx(path: Path, slides: int) -> Path:
    """A minimal but structurally real .pptx: slide count == ppt/slides/slideN.xml parts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        for i in range(1, slides + 1):
            zf.writestr(f"ppt/slides/slide{i}.xml", "<sld/>")
    return path


class FakeAdb:
    """Stands in for `subprocess.run(["adb", ...])` with a one-file device model."""

    def __init__(self, device_slides: int | None) -> None:
        self.device_slides = device_slides
        self.pulls: list[str] = []
        self.pushes: list[tuple[str, str]] = []

    def __call__(self, argv, **kwargs):  # noqa: ANN001 - mirrors subprocess.run
        assert argv[0] == "adb", argv
        verb = argv[3]
        if verb == "pull":
            remote, dest = argv[4], argv[5]
            self.pulls.append(remote)
            if self.device_slides is None:
                return subprocess.CompletedProcess(
                    argv, 1, "", "adb: error: failed to stat remote object"
                )
            _make_pptx(Path(dest), self.device_slides)
            return subprocess.CompletedProcess(argv, 0, "1 file pulled", "")
        if verb == "push":
            src, remote = argv[4], argv[5]
            self.pushes.append((src, remote))
            with zipfile.ZipFile(src) as zf:
                self.device_slides = sum(
                    1 for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
                )
            return subprocess.CompletedProcess(argv, 0, "1 file pushed", "")
        raise AssertionError(f"unexpected adb verb: {argv}")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rp):
    """Point the module's REPO_ROOT at a scratch tree so `sources` resolve there."""
    monkeypatch.setattr(rp, "REPO_ROOT", tmp_path)
    return tmp_path


def _profile(slides: int = 8) -> dict:
    return {"slides_deck": {"path": DECK_REMOTE, "expected_slides": slides, "sources": [DECK_REL]}}


def test_slide_count_reads_pptx_parts(rp, tmp_path: Path) -> None:
    assert rp._slide_count_in_pptx(_make_pptx(tmp_path / "a.pptx", 8)) == 8
    assert rp._slide_count_in_pptx(_make_pptx(tmp_path / "b.pptx", 1)) == 1


def test_deck_source_prefers_the_first_existing_candidate(rp, repo: Path) -> None:
    deck = {"sources": ["missing/first.pptx", DECK_REL]}
    assert rp._deck_source(deck) is None
    _make_pptx(repo / DECK_REL, 8)
    assert rp._deck_source(deck) == repo / DECK_REL


def test_restore_is_a_no_op_when_the_device_deck_is_already_correct(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    adb = FakeAdb(device_slides=8)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=True) is True
    assert adb.pushes == [], "a correct deck must not be re-pushed (it is a cheap no-op)"


def test_restore_replaces_the_stray_single_slide_deck(rp, repo: Path, monkeypatch) -> None:
    """The actual 2026-08/09 rot: device held a 1-slide deck named the same thing."""
    _make_pptx(repo / DECK_REL, 8)
    adb = FakeAdb(device_slides=1)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=True) is True
    assert adb.pushes == [(str(repo / DECK_REL), DECK_REMOTE)]
    assert adb.device_slides == 8


def test_restore_pushes_when_the_device_copy_is_missing(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    adb = FakeAdb(device_slides=None)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=True) is True
    assert len(adb.pushes) == 1
    assert adb.device_slides == 8


def test_restore_dry_run_never_pushes(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    adb = FakeAdb(device_slides=1)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=False) is True
    assert adb.pushes == []
    assert adb.device_slides == 1


def test_restore_refuses_a_fixture_that_contradicts_the_task_ground_truth(rp, repo: Path, monkeypatch) -> None:
    """Never push a deck whose slide count disagrees with the check -- fail loudly."""
    _make_pptx(repo / DECK_REL, 7)
    adb = FakeAdb(device_slides=1)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=True) is False
    assert adb.pushes == []
    assert adb.device_slides == 1


def test_restore_reports_failure_when_no_fixture_exists(rp, repo: Path, monkeypatch) -> None:
    adb = FakeAdb(device_slides=1)
    monkeypatch.setattr(rp.subprocess, "run", adb)

    assert rp.restore_slides_deck("s", _profile(), apply=True) is False
    assert adb.pushes == []


def test_verify_passes_when_device_matches_the_canonical_deck(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    monkeypatch.setattr(rp.subprocess, "run", FakeAdb(device_slides=8))
    assert rp.verify_slides_deck("s", _profile()) is True


def test_verify_fails_when_the_device_deck_is_missing(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    monkeypatch.setattr(rp.subprocess, "run", FakeAdb(device_slides=None))
    assert rp.verify_slides_deck("s", _profile()) is False


def test_verify_fails_when_the_device_deck_is_the_wrong_length(rp, repo: Path, monkeypatch) -> None:
    _make_pptx(repo / DECK_REL, 8)
    monkeypatch.setattr(rp.subprocess, "run", FakeAdb(device_slides=3))
    assert rp.verify_slides_deck("s", _profile()) is False


def test_verify_fails_when_the_canonical_fixture_is_missing(rp, repo: Path, monkeypatch) -> None:
    """The gate must not pass by trusting the device when the fixture itself is gone."""
    monkeypatch.setattr(rp.subprocess, "run", FakeAdb(device_slides=8))
    assert rp.verify_slides_deck("s", _profile()) is False


def test_no_slides_deck_profile_is_a_no_op(rp, repo: Path) -> None:
    assert rp.restore_slides_deck("s", {}, apply=True) is True
    assert rp.verify_slides_deck("s", {}) is True


def test_the_ground_truth_deck_is_version_controlled() -> None:
    """The one assets/ file that must never become untracked again.

    .gitignore excludes all of assets/ and re-includes just this deck. Git's negation
    rules are easy to get wrong -- a `!` under an excluded DIRECTORY is silently
    useless -- and if that regresses the fixture goes back to being uncommitted, which
    is exactly the state that let it rot to a 1-slide deck. So assert it directly
    rather than trusting the pattern.
    """
    deck = REPO_ROOT / "assets/seeds/public/Q3_Review.pptx"
    assert deck.is_file(), f"canonical deck missing: {deck}"
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("not a git checkout")

    rel = deck.relative_to(REPO_ROOT).as_posix()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                             cwd=REPO_ROOT, capture_output=True, text=True)
    assert tracked.returncode == 0, (
        f"{rel} is not tracked by git -- the .gitignore assets/ exception has regressed"
    )
    ignored = subprocess.run(["git", "check-ignore", rel],
                             cwd=REPO_ROOT, capture_output=True, text=True)
    assert ignored.returncode != 0, (
        f"{rel} is tracked but still matched by a .gitignore rule, so edits to the "
        f"fixture could not be staged: {ignored.stdout.strip()}"
    )
