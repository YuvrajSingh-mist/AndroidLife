"""Pytest coverage for the required-delivery gate in the grader.

Background. `hard__bookmyshow__005` ends "message [contact] on Telegram with the plan",
so a delivered message is part of the deliverable -- but the grader used to take the
model's `success` flag as the verdict. Auditing the 2026-09-22 re-run against the device
found three rows that self-reported success while delivering nothing:

  * row 3 left the text in the composer and hit `complete(success=true)`;
  * row 4 never launched Telegram at all (it used the non-existent package
    `org.telegram.messaging`) and reported success anyway;
  * row 10 typed the entire message into Telegram's SEARCH box and never opened the chat.

`success` cannot distinguish any of those from a real send, so the gate reads device-side
evidence recorded by `reset_phone.py --delivery-probe` (a "Sent at" bubble under today's
separator) and demotes a self-reported success when that evidence says nothing was sent.

The gate is deliberately one-directional and conservative: it can only demote, and it
demotes ONLY on definite evidence. A probe that could not reach the chat, or a run that
predates the probe, keeps its own outcome -- failing those would penalise the harness,
not the model.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from androidlife_report import load_run_record

from androidlife.task_dataset import delivery_checks_path

TASK = "hard__bookmyshow__005"

# The real sidecar entry: an unconditional send, unlike hard__drive-notes-telegram__010
# (message only if overdue) or hard__chrome-telegram-notes__008 (only if over $10).
DELIVERY = {"hard__bookmyshow__005": {"channel": "telegram", "requires_send": True}}


def _write_run(
    runs_dir: Path,
    label: str,
    *,
    success: bool,
    delivery: dict | None = None,
    task_id: str = TASK,
    reason: str = "INOX: Symphony Mall, Avengers Endgame: Encore, 07:15 PM",
) -> Path:
    """A minimal run folder; `delivery=None` omits delivery.json entirely."""
    run_dir = runs_dir / label
    run_dir.mkdir(parents=True)
    (run_dir / "output.json").write_text(
        json.dumps({"success": success, "reason": reason, "steps": 5})
    )
    (run_dir / "run_metrics.json").write_text(json.dumps({"ask_user_call_count": 0}))
    (run_dir / "meta.json").write_text(
        json.dumps({"label": label, "model": "m1", "task_id": task_id})
    )
    if delivery is not None:
        (run_dir / "delivery.json").write_text(json.dumps(delivery))
    return run_dir


def _record(run_dir: Path, deliveries: dict | None = DELIVERY) -> dict:
    return load_run_record(run_dir, set(), {}, None, set(), None, deliveries)


def test_path_helper_is_keyed_by_source() -> None:
    assert delivery_checks_path("public.md").endswith("delivery_checks_public.json")
    assert delivery_checks_path("tasks.md").endswith("delivery_checks_530.json")
    with pytest.raises(ValueError):
        delivery_checks_path("something-else.md")


def test_unsent_message_demotes_a_self_reported_pass(tmp_path: Path) -> None:
    """The row-3/row-10 case: reached the chat, found no sent bubble -> FAIL."""
    run_dir = _write_run(tmp_path, "a", success=True,
                         delivery={"reached_chat": True, "sent_bubbles": 0, "draft_present": True})
    rec = _record(run_dir)
    assert rec["success"] is False
    assert rec["delivery_demoted"] is True
    assert rec["delivery_check"] == "not_sent"
    assert rec["delivery_draft_left"] is True
    assert rec["classification"] == "true_failure"


def test_a_real_send_keeps_the_pass(tmp_path: Path) -> None:
    """The row-5 case: a real "Sent at" bubble exists, so the pass stands."""
    run_dir = _write_run(tmp_path, "a", success=True,
                         delivery={"reached_chat": True, "sent_bubbles": 1, "draft_present": False})
    rec = _record(run_dir)
    assert rec["success"] is True
    assert rec["delivery_demoted"] is False
    assert rec["delivery_check"] == "sent"
    assert rec["delivery_sent_bubbles"] == 1


def test_unreachable_chat_is_not_evidence_so_it_does_not_demote(tmp_path: Path) -> None:
    """A chat the probe could not open says nothing about the model. Never fail on it."""
    run_dir = _write_run(tmp_path, "a", success=True,
                         delivery={"reached_chat": False, "sent_bubbles": 0, "draft_present": False})
    rec = _record(run_dir)
    assert rec["success"] is True
    assert rec["delivery_demoted"] is False
    assert rec["delivery_check"] == "unverifiable"


def test_a_run_without_evidence_is_left_alone(tmp_path: Path) -> None:
    """Runs predating the probe (no delivery.json) must not be failed retroactively."""
    run_dir = _write_run(tmp_path, "a", success=True, delivery=None)
    rec = _record(run_dir)
    assert rec["success"] is True
    assert rec["delivery_demoted"] is False
    assert rec["delivery_check"] is None


def test_gate_never_promotes_a_self_reported_failure(tmp_path: Path) -> None:
    """A model that admitted failure stays failed even if a bubble happens to exist."""
    run_dir = _write_run(tmp_path, "a", success=False,
                         delivery={"reached_chat": True, "sent_bubbles": 1})
    rec = _record(run_dir)
    assert rec["success"] is False
    assert rec["delivery_demoted"] is False


def test_a_task_needing_no_delivery_is_untouched(tmp_path: Path) -> None:
    """The gate is opt-in per task; an unlisted task keeps its own outcome."""
    run_dir = _write_run(tmp_path, "a", success=True, task_id="easy__settings__001",
                         delivery={"reached_chat": True, "sent_bubbles": 0})
    rec = _record(run_dir)
    assert rec["success"] is True
    assert rec["delivery_demoted"] is False


def test_a_conditional_send_task_is_not_gated(tmp_path: Path) -> None:
    """hard__drive-notes-telegram__010 may legitimately send nothing, so it must not be
    listed -- and if it is not listed, a no-send run keeps its verdict."""
    run_dir = _write_run(tmp_path, "a", success=True,
                         task_id="hard__drive-notes-telegram__010",
                         delivery={"reached_chat": True, "sent_bubbles": 0})
    rec = _record(run_dir)
    assert rec["success"] is True
    assert rec["delivery_demoted"] is False


def test_real_sidecar_lists_only_unconditional_send_tasks() -> None:
    """The shipped sidecar drives real grading, so pin what it claims.

    Every entry must be a task whose prompt requires the message unconditionally; a
    conditional send ("only if it is overdue", "only if it is over $10") would turn a
    correct decision not to send into a false failure.
    """
    root = Path(__file__).resolve().parents[1]
    sidecar = json.loads((root / "benchmarks/androidlife-530/delivery_checks_public.json").read_text())
    assert "hard__bookmyshow__005" in sidecar
    assert sidecar["hard__bookmyshow__005"]["requires_send"] is True
    # These all have conditional sends in public.md -- gating them would be wrong.
    for conditional in (
        "hard__drive-notes-telegram__010",   # message only if the note is overdue
        "hard__chrome-telegram-notes__008",  # only if the price gap is over $10
        "hard__google-search-obsidian-telegram__057",  # only if the value crossed
    ):
        assert conditional not in sidecar, f"{conditional} has a conditional send"


# --- backfill parser: recovering evidence for runs taken before the probe -------------
#
# The leak cleanup calls the same detection functions moments after a run, so its log is
# the same measurement the probe would have made. These pin the three line shapes it can
# emit, because a mis-parse here would silently rewrite a verdict.


def _parse(text: str):
    """Load the backfill tool and parse one cleanup-log body."""
    tool = Path(__file__).resolve().parents[1] / "scripts" / "tools" / "backfill_delivery_evidence.py"
    spec = importlib.util.spec_from_file_location("bde", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_cleanup_log(text)


def test_parse_clean_chat_means_nothing_was_sent() -> None:
    """Row 4 and row 10 read exactly like this -- clean, because neither ever sent."""
    got = _parse("[ok]  telegram: composer empty, no run-window bubbles in Yuvraj Airtel\n"
                 "PASS telegram: Yuvraj Airtel composer empty, 0 run-window bubble(s) dated September 22")
    assert got is not None
    assert got["reached_chat"] is True
    assert got["sent_bubbles"] == 0
    assert got["draft_present"] is False


def test_parse_draft_left_unsent_is_recorded_as_a_draft() -> None:
    """Row 3: the answer sat in the composer, unsent."""
    got = _parse("  [!!]  telegram leak: draft='INOX: Symphony Mall, Avengers Endgame: Encore, "
                 "07:15 PM', 0 run-window bubble(s) dated September 22")
    assert got is not None
    assert got["sent_bubbles"] == 0
    assert got["draft_present"] is True


def test_parse_a_sent_bubble_is_evidence_of_delivery() -> None:
    """Row 5: a real sent bubble -> the pass must survive the gate."""
    got = _parse("  [!!]  telegram leak: draft=None, 1 run-window bubble(s) dated September 22")
    assert got is not None
    assert got["reached_chat"] is True
    assert got["sent_bubbles"] == 1
    assert got["draft_present"] is False


def test_parse_an_unreachable_chat_is_no_evidence() -> None:
    """Never invent evidence: an unreachable chat must not be read as 'nothing was sent'."""
    got = _parse("  [!!]  telegram: could not open the Yuvraj Airtel chat - clean it by hand")
    assert got is not None
    assert got["reached_chat"] is False


def test_parse_a_log_with_no_telegram_verdict_is_none() -> None:
    assert _parse("== leak cleanup only ==\nWORK IN PROGRESS") is None
