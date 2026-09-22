"""Pytest coverage for scripts/tools/audit_telegram_inheritance.py.

The detector decides whether a run is VOID (it scored using a message the previous run had
already sent), so a false negative hides a fake pass and a false positive voids a good run.
Both directions are pinned here against synthetic run folders, plus the real measured case.

Background: the between-row Telegram cleanup did not exist before 2026-09-22, so the
2026-09-21 hard__drive-notes-telegram__010 re-runs carried each delivered message into the
next row. Row 11 sent at 19:29; row 13 started at 19:46, saw that same bubble at step 6, and
reported success in 9 steps having sent nothing.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "scripts" / "tools" / "audit_telegram_inheritance.py"


def _mod():
    spec = importlib.util.spec_from_file_location("ati", TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TASK = "hard__drive-notes-telegram__010"
KEYWORDS = ("FY26 family budget", "overdue")
BUDGET_MSG = "Hey, just checked the FY26 family budget note. The deadline was Aug 10"


def _run(tmp_path: Path, *, started_utc: str, states: dict[str, str]) -> Path:
    """A synthetic run: meta.json start time + ui_states/<name>.json UI trees."""
    tdir = tmp_path / "day2" / TASK.replace("__", "-")
    ui = tdir / "trajectories" / "t1" / "ui_states"
    ui.mkdir(parents=True)
    (tdir / "meta.json").write_text(json.dumps({"started_at_utc": started_utc}))
    for name, text in states.items():
        (ui / name).write_text(json.dumps({"text": text}))
    return tdir


def test_a_bubble_stamped_before_the_start_is_an_inheritance(tmp_path: Path) -> None:
    """The measured case: started 19:46 IST, bubble stamped 19:29."""
    tdir = _run(tmp_path, started_utc="2026-09-21T14:16:00Z",   # 19:46 IST
                states={"0006.json": f"{BUDGET_MSG} Sent at 19:29, Seen"})
    hits = _mod().inherited_sends(tdir, KEYWORDS)
    assert len(hits) == 1
    assert hits[0]["sent_at"] == "19:29"
    assert hits[0]["started"] == "19:46"


def test_a_bubble_stamped_after_the_start_belongs_to_the_run(tmp_path: Path) -> None:
    """Row 11: started 19:25 and sent at 19:29 -- that is the run's own work."""
    tdir = _run(tmp_path, started_utc="2026-09-21T13:55:00Z",   # 19:25 IST
                states={"0017.json": f"{BUDGET_MSG} Sent at 19:29, Seen"})
    assert _mod().inherited_sends(tdir, KEYWORDS) == []


def test_seeded_history_is_never_counted(tmp_path: Path) -> None:
    """The seeded chat is shared by every run and must not flag any of them."""
    tdir = _run(tmp_path, started_utc="2026-09-21T14:16:00Z",
                states={"0002.json": "Seems nice ain't it? Sent at 16:46, Seen"})
    assert _mod().inherited_sends(tdir, ("overdue", "budget", "Seems nice")) == []


def test_a_received_bubble_is_not_a_send(tmp_path: Path) -> None:
    """Only our own sends matter -- an inbound message says nothing about the run."""
    tdir = _run(tmp_path, started_utc="2026-09-21T14:16:00Z",
                states={"0002.json": f"{BUDGET_MSG} Received at 19:29"})
    assert _mod().inherited_sends(tdir, KEYWORDS) == []


def test_an_unsent_draft_is_not_a_send(tmp_path: Path) -> None:
    """A draft in the composer has no stamp, so it can never read as a delivery."""
    tdir = _run(tmp_path, started_utc="2026-09-21T14:16:00Z",
                states={"0002.json": BUDGET_MSG})
    assert _mod().inherited_sends(tdir, KEYWORDS) == []


def test_keywords_scope_the_match_to_the_task_tmp_path(tmp_path: Path) -> None:
    """A run for a different message must not be judged on this task's leftovers."""
    tdir = _run(tmp_path, started_utc="2026-09-21T14:16:00Z",
                states={"0002.json": "Unrelated news Sent at 09:00"})
    assert _mod().inherited_sends(tdir, KEYWORDS) == []


def test_a_missing_or_malformed_meta_is_skipped_not_crashed(tmp_path: Path) -> None:
    """A whole-corpus scan must survive one broken run folder."""
    tdir = tmp_path / "day2" / TASK.replace("__", "-")
    tdir.mkdir(parents=True)
    (tdir / "meta.json").write_text("{not json")
    assert _mod().run_started_at(tdir) is None
    assert _mod().inherited_sends(tdir, KEYWORDS) == []


def test_keyword_table_covers_every_task_with_a_required_send() -> None:
    """Keep the detector and the delivery gate pointed at the same tasks."""
    m = _mod()
    root = Path(__file__).resolve().parents[1]
    sidecar = json.loads((root / "benchmarks/androidlife-530/delivery_checks_public.json").read_text())
    for task_id in sidecar:
        assert task_id in m.TASK_MESSAGE_KEYWORDS, (
            f"{task_id} has a required send but no keywords, so inheritance would go unchecked"
        )
