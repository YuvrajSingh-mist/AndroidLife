"""Regression tests for the Telegram/Notes run-leak cleanup in reset_phone.

Why this exists (redo.md 7.2): the harness reset force-stops an app and returns home,
which resets the app's *screen* but never its *content*. Two leaks were measured across
the 2026-09-21 hard__drive-notes-telegram__010 re-runs:

  * a chase message one run composed and never sent stayed in the Telegram composer, and
    later runs opened the chat to find it already typed (row 9: "The message is already
    composed"; row 11: "I can see the message has been sent!"); and
  * row 12 edited the Budget Deadline note in place, silently moving the graded date and
    flipping the overdue branch the next run takes.

Neither app is debuggable and neither exposes a content provider, so the fix has to drive
the UI -- and the parts worth pinning in a test are the pure decisions around it:

  * what counts as "a draft" (the composer is an EditText, but so is the chat-list SEARCH
    box, whose "Search Chats" hint reads as a leaked draft if position is ignored);
  * which bubbles are run artifacts rather than seeded history; and
  * the Notes fingerprint (`text_count` excludes whitespace, so the tracked seed's
    non-whitespace length is the number the device must match).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seeding" / "reset_phone.py"
NOTE_SEED = REPO_ROOT / "assets" / "seeds" / "public" / "Budget Deadline (OnePlus Notes).txt"

# The device's published `text_count` for the canonical seed: non-whitespace characters
# only. Pinned so a silent edit to the seed file cannot pass unnoticed.
EXPECTED_NOTE_COUNT = 518


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("reset_phone_leaks", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["reset_phone_leaks"] = mod
    spec.loader.exec_module(mod)
    return mod


def _node(text: str, cls: str = "android.widget.TextView", rid: str = "",
          bounds: str = "[0,0][100,100]", desc: str = "") -> str:
    return (f'<node index="0" text="{text}" resource-id="{rid}" class="{cls}" '
            f'package="app" content-desc="{desc}" bounds="{bounds}" />')


def test_note_seed_file_is_tracked_and_matches_the_device_fingerprint(rp):
    assert NOTE_SEED.is_file(), f"tracked note seed missing: {NOTE_SEED}"
    assert rp._non_ws_count(rp._note_seed_text()) == EXPECTED_NOTE_COUNT


def test_non_ws_count_ignores_spaces_and_newlines(rp):
    assert rp._non_ws_count("a b\nc\t d") == 4
    assert rp._non_ws_count("   \n ") == 0


def test_ui_nodes_parses_text_bounds_and_resource_id(rp):
    xml = ("<hierarchy>"
           + _node("Message", cls="android.widget.EditText", bounds="[171,2212][777,2332]")
           + _node("518", rid="com.oneplus.note:id/text_count", bounds="[410,306][469,355]")
           + "</hierarchy>")
    nodes = rp._ui_nodes(xml)
    assert [n["text"] for n in nodes] == ["Message", "518"]
    assert nodes[0]["cx"] == (171 + 777) // 2 and nodes[0]["cy"] == (2212 + 2332) // 2
    assert rp._note_text_count(nodes) == 518


def test_tg_label_reads_content_desc_when_text_is_empty(rp):
    """Telegram's selection toolbar is a row of icon buttons: label in `content-desc`."""
    xml = "".join([
        _node("", desc="Delete", bounds="[921,96][1050,264]"),
        _node("1 Selected", bounds="[225,96][579,264]"),
        _node("Delete", bounds="[799,1403][1008,1523]"),   # the dialog's button
    ])
    nodes = rp._ui_nodes(xml)
    assert rp._tg_label(nodes[0]) == "Delete"   # from desc
    assert rp._tg_label(nodes[1]) == "1 Selected"
    assert rp._tg_label(nodes[2]) == "Delete"   # from text


def test_tg_delete_actions_finds_the_selection_bar_delete(rp):
    """The exact measured long-press menu: this is what the old text-only match missed.

    Reproduced from the device on 2026-09-22: the toolbar Delete is `text='' desc='Delete'`.
    Matching on `text` alone made every cleanup report 'long-press menu did not appear',
    so leaked bubbles were never deleted and aborted every later row at the seed gate.
    """
    xml = "".join([
        _node("1 Selected", bounds="[225,96][579,264]"),
        _node("", desc="Edit", bounds="[579,96][723,264]"),
        _node("", desc="Copy", bounds="[693,96][837,264]"),
        _node("", desc="Delete", bounds="[921,96][1050,264]"),
    ])
    dels = rp._tg_delete_actions(rp._ui_nodes(xml))
    assert len(dels) == 1
    assert dels[0]["cy"] == (96 + 264) // 2


def test_tg_delete_actions_ignores_the_checkbox_and_title(rp):
    """The confirm dialog: only the button is the action; the checkbox would notify the contact."""
    xml = "".join([
        _node("Delete message", bounds="[120,969][549,1050]"),
        _node("Are you sure you want to delete this message?", bounds="[120,1080][960,1202]"),
        _node("Also delete for Yuvraj", bounds="[210,1271][945,1336]"),
        _node("Cancel", bounds="[556,1403][775,1523]"),
        _node("Delete", bounds="[799,1403][1008,1523]"),
    ])
    dels = rp._tg_delete_actions(rp._ui_nodes(xml))
    assert [n["text"] for n in dels] == ["Delete"]


def test_tg_delete_actions_empty_when_the_menu_never_opened(rp):
    """No menu means no Delete: the caller must see this as a failure, not a no-op pass."""
    xml = _node("Movie night this weekend!&#10;Sent at 16:46", bounds="[0,1838][1080,2184]")
    assert rp._tg_delete_actions(rp._ui_nodes(xml)) == []


def test_clear_deletes_a_sent_bubble_end_to_end(rp, monkeypatch):
    """Full deletion sequence against the measured Telegram UI.

    The chat has one run-window bubble (a message a previous run sent). The cleanup must
    long-press it, tap the SELECTION BAR's Delete (label in content-desc), then tap the
    CONFIRM DIALOG's Delete (label in text) -- and never the "Also delete for Yuvraj"
    checkbox. Regression cover for the bug that made every cleanup report "long-press menu
    did not appear" while the menu was in fact on screen.
    """
    bubble = _node("Movie night this weekend!&#10;Sent at 19:02&#10;",
                   bounds="[0,1838][1080,2184]")
    # The detector only counts bubbles BELOW today's date separator.
    sep = _node("September 22", bounds="[0,1747][1080,1838]")
    chat_xml = "<hierarchy>" + sep + bubble + "</hierarchy>"
    menu = "".join([
        _node("1 Selected", bounds="[225,96][579,264]"),
        _node("", desc="Delete", bounds="[921,96][1050,264]"),        # selection bar
        _node("Reply", bounds="[103,2229][442,2313]"),
    ])
    dialog = "".join([
        _node("Delete message", bounds="[120,969][549,1050]"),
        _node("Also delete for Yuvraj", bounds="[210,1271][945,1336]"),
        _node("Cancel", bounds="[556,1403][775,1523]"),
        _node("Delete", bounds="[799,1403][1008,1523]"),              # dialog button
    ])
    dumps = [chat_xml,
             "<hierarchy>" + menu + "</hierarchy>",
             "<hierarchy>" + dialog + "</hierarchy>"]

    calls: list[str] = []
    monkeypatch.setattr(rp, "_tg_today_label", lambda serial: "September 22")
    monkeypatch.setattr(rp, "_pull_ui_dump", lambda serial, remote="/x": dumps.pop(0))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: calls.append(cmd) or "")
    monkeypatch.setattr(rp.time, "sleep", lambda _s: None)
    monkeypatch.setattr(rp, "_tg_open_chat", lambda serial, timeout_s=45.0: rp._ui_nodes(chat_xml))

    assert rp.clear_telegram_run_leaks("S", apply=True) is True
    taps = [c for c in calls if c.startswith("input tap")]
    # 1) the selection bar's Delete (icon button, label in content-desc) ...
    assert taps[0] == "input tap 985 180"
    # 2) ... then the dialog's Delete. Neither is the checkbox at cy 1303.
    assert taps[1] == "input tap 903 1463"
    assert all("1303" not in t for t in taps)
    assert "am force-stop org.telegram.messenger" in calls


def test_clear_reports_failure_when_the_menu_never_appears(rp, monkeypatch):
    """A long-press that produces no Delete must FAIL, not silently pass and leave the leak."""
    bubble = _node("x&#10;Sent at 19:02&#10;", bounds="[0,1838][1080,2184]")
    sep = _node("September 22", bounds="[0,1747][1080,1838]")
    chat_xml = "<hierarchy>" + sep + bubble + "</hierarchy>"
    # 1 chat read + 3 menu reads, all identical: the long-press never opens a menu.
    dumps = [chat_xml] * 4
    calls: list[str] = []
    monkeypatch.setattr(rp, "_tg_today_label", lambda serial: "September 22")
    monkeypatch.setattr(rp, "_pull_ui_dump", lambda serial, remote="/x": dumps.pop(0) if dumps else "<hierarchy/>")
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: calls.append(cmd) or "")
    monkeypatch.setattr(rp.time, "sleep", lambda _s: None)
    monkeypatch.setattr(rp, "_tg_open_chat", lambda serial, timeout_s=45.0: rp._ui_nodes(chat_xml))

    assert rp.clear_telegram_run_leaks("S", apply=True) is False
    assert not [c for c in calls if c.startswith("input tap")]  # never tapped a guess


def test_tg_draft_returns_none_for_the_empty_hint(rp):
    nodes = rp._ui_nodes(_node("Message", cls="android.widget.EditText", bounds="[171,2212][777,2332]"))
    assert rp._tg_draft(nodes) is None


def test_tg_draft_reads_a_real_draft(rp):
    nodes = rp._ui_nodes(
        _node("Hey, just checked our shared budget note", cls="android.widget.EditText",
              bounds="[171,2212][777,2332]")
    )
    assert rp._tg_draft(nodes) == "Hey, just checked our shared budget note"


def test_tg_draft_ignores_the_chat_list_search_box(rp):
    """The search box is an EditText too; its hint must not read as a leaked draft.

    Measured 2026-09-22: after a force-stop Telegram reopens on the chat LIST, and a
    position-blind lookup returned 'Search Chats' as the composer's contents.
    """
    nodes = rp._ui_nodes(_node("Search Chats", cls="android.widget.EditText", bounds="[0,290][1080,370]"))
    assert rp._tg_draft(nodes) is None


def test_tg_run_window_bubbles_only_picks_today_below_its_separator(rp):
    xml = ("<hierarchy>"
           + _node("August 20", bounds="[0,0][100,40]")
           + _node("Seems nice ain't it?&#10;Sent at 16:46, Seen", bounds="[0,1739][100,1789]")
           + _node("August 23", bounds="[0,1975][100,2015]")
           + _node("But need more suggestions pls&#10;Received at 22:18", bounds="[0,2066][100,2116]")
           + _node("September 22", bounds="[0,2180][100,2220]")
           + _node("Hey, just checked budget&#10;Sent at 09:12", bounds="[0,2260][100,2310]")
           + "</hierarchy>")
    nodes = rp._ui_nodes(xml)
    leaks = rp._tg_run_window_bubbles(nodes, "September 22")
    assert len(leaks) == 1
    assert leaks[0]["text"].startswith("Hey, just checked budget")
    # Seeded history (Aug 20/23) is never a candidate, even though it carries a stamp.
    assert all("Seems nice" not in n["text"] for n in leaks)


def test_tg_run_window_bubbles_empty_when_today_absent(rp):
    xml = ("<hierarchy>"
           + _node("August 23", bounds="[0,1975][100,2015]")
           + _node("But need more suggestions pls&#10;Received at 22:18", bounds="[0,2066][100,2116]")
           + "</hierarchy>")
    assert rp._tg_run_window_bubbles(rp._ui_nodes(xml), "September 22") == []


def test_tg_today_label_uses_the_device_clock(rp, monkeypatch):
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "2026-09-22\n")
    assert rp._tg_today_label("S") == "September 22"


def test_tg_today_label_is_blank_when_the_clock_is_unreadable(rp, monkeypatch):
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "not-a-date")
    assert rp._tg_today_label("S") == ""


def test_restore_is_a_noop_when_the_note_already_matches(rp, monkeypatch):
    """A healthy note must cost no typing at all -- the retype path is the risky one."""
    typed: list[str] = []
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: typed.append(cmd) or "")
    monkeypatch.setattr(
        rp, "_note_open",
        lambda serial, timeout_s=40.0: rp._ui_nodes(
            _node(str(EXPECTED_NOTE_COUNT), rid="com.oneplus.note:id/text_count")
        ),
    )
    assert rp.restore_budget_note("S", apply=True) is True
    assert typed == [], f"no adb input should be issued for a matching note, got {typed}"


def test_restore_refuses_to_type_when_the_seed_is_missing(rp, monkeypatch):
    monkeypatch.setattr(rp, "ONEPLUS_NOTE_SEED", Path("/nonexistent/Budget Deadline.txt"))
    assert rp.restore_budget_note("S", apply=True) is False


def test_verify_fails_when_the_note_title_vanished(rp, monkeypatch):
    """A renamed note is the worst case: the oracle names it, so the task is unsolvable."""
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    monkeypatch.setattr(rp, "_note_open", lambda serial, timeout_s=40.0: [])
    assert rp.verify_budget_note("S") is False


# --- --leak-cleanup-only: the between-row repair a batch runner depends on ----------
#
# Without it a batch loses every row after the first that messages: the runner's seed
# gate is verify-only, so a leaked Telegram draft aborts the next row instead of seeding
# it. That is exactly how 2026-09-22's hard__bookmyshow__005 batch lost rows 3-13.


def _wire_leak_only(monkeypatch, rp, *, tg_clean: bool, note_clean: bool,
                    maps_clean: bool = True) -> dict[str, list]:
    """Stub every device touch that --leak-cleanup-only makes, and record the calls."""
    calls: dict[str, list] = {"cleared": [], "restored": [], "maps_notes": [],
                              "maps_recents": [], "verified": [], "full_reset": []}
    monkeypatch.setattr(rp, "connect_ok", lambda serial: True)
    monkeypatch.setattr(rp, "clear_telegram_run_leaks",
                        lambda serial, apply=False: calls["cleared"].append(apply) or True)
    monkeypatch.setattr(rp, "restore_budget_note",
                        lambda serial, apply=False: calls["restored"].append(apply) or True)
    monkeypatch.setattr(rp, "clear_maps_run_notes",
                        lambda serial, apply=False: calls["maps_notes"].append(apply) or True)
    monkeypatch.setattr(rp, "clear_maps_recents",
                        lambda serial, apply=False: calls["maps_recents"].append(apply) or True)
    monkeypatch.setattr(rp, "verify_telegram_chat_clean",
                        lambda serial: calls["verified"].append("telegram") or tg_clean)
    monkeypatch.setattr(rp, "verify_budget_note",
                        lambda serial: calls["verified"].append("note") or note_clean)
    monkeypatch.setattr(rp, "verify_maps_run_notes_clear",
                        lambda serial: calls["verified"].append("maps") or maps_clean)
    monkeypatch.setattr(rp, "verify_maps_recents_clear",
                        lambda serial: calls["verified"].append("maps_recents") or maps_clean)
    # Any full-reset work would mean the mode is not actually narrow.
    monkeypatch.setattr(rp, "reset_settings",
                        lambda *a, **k: calls["full_reset"].append("settings") or True)
    monkeypatch.setattr(rp, "verify_cloud_accounts",
                        lambda *a, **k: calls["full_reset"].append("accounts") or True)
    monkeypatch.setattr(rp, "verify_slides_deck",
                        lambda *a, **k: calls["full_reset"].append("slides") or True)
    return calls


def _run_leak_only(rp, monkeypatch, *extra: str) -> int:
    monkeypatch.setattr(sys, "argv", [
        "reset_phone.py", "--serial", "S", "--profile", "public_v2", "--leak-cleanup-only", *extra,
    ])
    return rp.main()


def test_leak_cleanup_only_repairs_and_returns_zero(rp, monkeypatch, capsys):
    calls = _wire_leak_only(monkeypatch, rp, tg_clean=True, note_clean=True)
    assert _run_leak_only(rp, monkeypatch) == 0
    # Every leak is repaired with apply=True (the caller wants the fix, not a dry run).
    assert calls["cleared"] == [True]
    assert calls["restored"] == [True]
    assert calls["maps_notes"] == [True]
    assert calls["maps_recents"] == [True]
    assert calls["verified"] == ["telegram", "note", "maps", "maps_recents"]
    assert "RESULT PASS" in capsys.readouterr().out


def test_leak_cleanup_only_skips_every_full_reset_step(rp, monkeypatch):
    """It must stay cheap: no calendar anchors, no account sweep, no slides push."""
    calls = _wire_leak_only(monkeypatch, rp, tg_clean=True, note_clean=True)
    _run_leak_only(rp, monkeypatch)
    assert calls["full_reset"] == []


def test_leak_cleanup_only_fails_when_a_leak_survives(rp, monkeypatch, capsys):
    """A surviving draft must be a non-zero exit, so the runner can flag that row."""
    _wire_leak_only(monkeypatch, rp, tg_clean=False, note_clean=True)
    assert _run_leak_only(rp, monkeypatch) == 1
    assert "RESULT FAIL" in capsys.readouterr().out


def test_leak_cleanup_only_still_checks_the_note_when_telegram_is_dirty(rp, monkeypatch):
    """Both verifies always run, so the log names every live leak, not just the first."""
    calls = _wire_leak_only(monkeypatch, rp, tg_clean=False, note_clean=False)
    _run_leak_only(rp, monkeypatch)
    assert calls["verified"] == ["telegram", "note", "maps", "maps_recents"]


def test_leak_cleanup_only_fails_when_a_maps_note_survives(rp, monkeypatch, capsys):
    """A left-over Maps run-note buries the seed and free-hints the next row: non-zero exit."""
    _wire_leak_only(monkeypatch, rp, tg_clean=True, note_clean=True, maps_clean=False)
    assert _run_leak_only(rp, monkeypatch) == 1
    assert "RESULT FAIL" in capsys.readouterr().out


# ---- Maps run-note sweep (the false "seed damaged" abort, 2026-09-23) --------------
#
# medium__google-maps__002 writes a note every row. Seven accumulated on 2026-09-23 and
# pushed the protected `Budget Deadline` seed below the fold, so the seed gate reported
# the seed as missing and aborted rows 8-13. The pure decision worth pinning is what
# counts as a run artifact -- getting that wrong deletes a seed.

MAPS_RUN_TITLES = [
    "Fastest route to Bhubaneswar Airport",
    "Fastest Route to Bhubaneswar Airport",
    "Fastest Travel to Bhubaneswar Airport: Driving (25 min, 12 km)",
    "Bhubaneswar Airport Travel Info: Fastest Option",
    "parked here",
]
NOTE_SEED_TITLES = [
    "Budget Deadline",
    "Daily Reflection",
    "Rent Dues",
    "To Buy",
    "Trip Packing Checklist",
]


@pytest.mark.parametrize("title", MAPS_RUN_TITLES)
def test_maps_run_titles_are_swept(rp, title):
    assert rp._note_is_run_artifact(title) is True


@pytest.mark.parametrize("title", NOTE_SEED_TITLES)
def test_seed_titles_are_never_swept(rp, title):
    assert rp._note_is_run_artifact(title) is False


def test_budget_deadline_is_protected_even_if_it_matched_a_pattern(rp):
    """The seed is excluded by an explicit allow-list, not by hoping no pattern matches."""
    assert rp._note_is_run_artifact(rp.NOTE_TITLE) is False
    assert rp.NOTE_TITLE in rp.NOTE_PROTECTED_TITLES


def test_note_list_rows_only_takes_the_list_area(rp):
    xml = ("<hierarchy>"
           + _node("Fastest Route to Bhubaneswar Airport", rid="com.oneplus.note:id/tv_title",
                   bounds="[95,732][996,797]")
           + _node("Budget Deadline", rid="com.oneplus.note:id/tv_title",
                   bounds="[95,2195][996,2260]")     # under the bottom nav -> not a list row
           + "</hierarchy>")
    rows = rp._note_list_rows(rp._ui_nodes(xml))
    assert [r["text"] for r in rows] == ["Fastest Route to Bhubaneswar Airport"]


def test_ui_nodes_reads_the_checkbox_checked_state(rp):
    """Selection must be driven by `checked`: re-tapping an already-ticked box clears it.

    Measured 2026-09-23: the long-press already checks the pressed row, so a sweep that
    taps every target clears the one it just selected and deletes nothing while printing
    success. The fix reads this attribute.
    """
    def box(y: int, checked: bool) -> str:
        return (f'<node index="0" text="" resource-id="com.oneplus.note:id/cb_list_select" '
                f'class="android.widget.CheckBox" package="app" content-desc="" '
                f'checkable="true" checked="{str(checked).lower()}" bounds="[40,{y}][130,{y + 90}]" />')

    xml = "<hierarchy>" + box(765, True) + box(974, False) + "</hierarchy>"
    boxes = [n for n in rp._ui_nodes(xml) if n["rid"].endswith("id/cb_list_select")]
    assert [b["checked"] for b in boxes] == [True, False]


def test_leak_cleanup_only_rejects_the_contradictory_flag(rp, monkeypatch, capsys):
    calls = _wire_leak_only(monkeypatch, rp, tg_clean=True, note_clean=True)
    assert _run_leak_only(rp, monkeypatch, "--no-leak-cleanup") == 2
    assert "contradicts" in capsys.readouterr().err
    assert calls["cleared"] == []


# ---- draft clearing (the row-11 abort, 2026-09-22) --------------------------

# A real leaked draft: the chase message hard__bookmyshow__005 composes.
LEAKED_DRAFT = "INOX: Symphony Mall, Avengers Endgame: Encore, 07:15 PM"
# What one large DEL flood actually left behind on the device (27 of ~127 chars).
PARTIAL_AFTER_FLOOD = "INOX: Symphony Mall, Avenge"


def _chat_xml(*bodies: str) -> str:
    return "<hierarchy>" + "".join(bodies) + "</hierarchy>"


def _composer(text: str) -> str:
    """The composer: an EditText below the y-guard, so it is not the search box."""
    return _node(text, cls="android.widget.EditText", bounds="[171,2212][777,2332]")


def _wire_draft_clear(monkeypatch, rp, dumps: list[str], calls: list[str]) -> None:
    monkeypatch.setattr(rp, "_tg_today_label", lambda serial: "September 22")
    monkeypatch.setattr(rp, "_pull_ui_dump", lambda serial, remote="/x": dumps.pop(0))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: calls.append(cmd) or "")
    monkeypatch.setattr(rp.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        rp, "_tg_open_chat",
        lambda serial, timeout_s=45.0: rp._ui_nodes(_chat_xml(_composer(LEAKED_DRAFT))))


def test_draft_clear_chunks_deletes_so_a_dropped_press_is_recovered(rp, monkeypatch):
    """One big `input keyevent 67 x N` silently truncates, so the delete must be chunked.

    Measured 2026-09-22: a ~127-char draft survived a single flood as 27 chars, and the
    cleanup then reported a leak it had half-cleared -- row 11 aborted at the seed gate.
    Here the first chunk leaves a partial draft and the second finishes it.
    """
    calls: list[str] = []
    dumps = [_chat_xml(_composer(LEAKED_DRAFT)),      # box found, deleting starts
             _chat_xml(_composer(PARTIAL_AFTER_FLOOD)),  # chunk 1: a press was dropped
             _chat_xml(_composer("Message"))]         # chunk 2: empty (the hint shows)
    _wire_draft_clear(monkeypatch, rp, dumps, calls)

    assert rp.clear_telegram_run_leaks("S", apply=True) is True
    dels = [c for c in calls if c.startswith("input keyevent 67")]
    assert len(dels) >= 2, "a partial read must be deleted again, not accepted"
    # Every DEL is a bounded chunk rather than one unbounded flood.
    assert all(c.split()[2:] == ["67"] * 25 for c in dels)


def test_transiently_missing_composer_is_retried_not_fatal(rp, monkeypatch):
    """A dump without the composer must retry, not abandon the whole clear.

    The old loop `break`-ed on `box is None`, so one transient read ended the cleanup and
    printed "still holds a draft after 3 attempts" having really tried once.
    """
    calls: list[str] = []
    dumps = ["<hierarchy/>",                          # composer absent: must retry
             _chat_xml(_composer(LEAKED_DRAFT)),      # retry finds it and clears
             _chat_xml(_composer("Message"))]
    _wire_draft_clear(monkeypatch, rp, dumps, calls)

    assert rp.clear_telegram_run_leaks("S", apply=True) is True


def test_composer_that_never_appears_still_fails_and_never_guesses(rp, monkeypatch):
    """An unreadable composer is a surviving leak: fail, and never tap blind."""
    calls: list[str] = []
    monkeypatch.setattr(rp, "_tg_today_label", lambda serial: "September 22")
    monkeypatch.setattr(rp, "_pull_ui_dump", lambda serial, remote="/x": "<hierarchy/>")
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: calls.append(cmd) or "")
    monkeypatch.setattr(rp.time, "sleep", lambda _s: None)
    monkeypatch.setattr(
        rp, "_tg_open_chat",
        lambda serial, timeout_s=45.0: rp._ui_nodes(_chat_xml(_composer(LEAKED_DRAFT))))

    assert rp.clear_telegram_run_leaks("S", apply=True) is False
    assert not [c for c in calls if c.startswith("input tap")]
    assert not [c for c in calls if c.startswith("input keyevent 67")]


# ---- Maps Recents gate (the free-hint surface of redo.md section 1) -----------------
#
# With an airport row parked in Recents an agent can satisfy medium__google-maps__002
# without ever typing the query: it taps the pre-existing suggestion and the grader sees
# the right end state. That is how 7 of the 13 original runs passed or were misled, and
# it is why the re-run batch had to clear the list by hand before every row.
#
# The list was cleared on each reset but never *gated*, so a cleanup that silently did
# nothing still printed OK on the full-reset path -- the one that starts a batch. These
# tests pin both halves: what counts as a recent entry, and that an unreadable screen
# fails closed rather than reading as "clean".


def _maps_screen(*nodes: str) -> str:
    return "<hierarchy>" + "".join(nodes) + "</hierarchy>"


def test_maps_recent_rows_needs_the_header(rp):
    """No Recent header means there is no list to read -- not an empty list."""
    xml = _maps_screen(
        _node("Biju Patnaik International Airport", bounds="[40,700][900,760]"),
        _node("Search here", bounds="[40,1200][500,1260]"),
    )
    assert rp._maps_recent_rows(rp._ui_nodes(xml)) == []


def test_maps_recent_rows_takes_entries_below_the_header_only(rp):
    """A place name above the header is the search suggestion, not history."""
    xml = _maps_screen(
        _node("Biju Patnaik International Airport", bounds="[40,200][900,260]"),
        _node("Recent", bounds="[40,600][300,660]"),
        _node("restaurants", bounds="[40,700][900,760]"),
    )
    rows = rp._maps_recent_rows(rp._ui_nodes(xml))
    assert [r["text"] for r in rows] == ["restaurants"]


def test_maps_recent_rows_ignores_the_chips_and_the_omnibox(rp):
    """Home/Work/Favourites sit under the header but are shortcuts, not history."""
    xml = _maps_screen(
        _node("Recent", bounds="[40,600][300,660]"),
        _node("Home", bounds="[40,700][300,760]"),
        _node("Work", bounds="[40,780][300,840]"),
        _node("Favourites", bounds="[40,860][300,920]"),
        _node("Set location", bounds="[40,940][300,1000]"),
        _node("Search here", bounds="[40,1020][500,1080]"),
    )
    assert rp._maps_recent_rows(rp._ui_nodes(xml)) == []


def test_verify_maps_recents_passes_on_a_clean_search_screen(rp, monkeypatch, capsys):
    """The measured clean state: chips + the omnibox hint, and no Recent header."""
    xml = _maps_screen(
        _node("Home", bounds="[40,700][300,760]"),
        _node("Set location", bounds="[40,780][300,840]"),
        _node("Work", bounds="[40,860][300,920]"),
        _node("Favourites", bounds="[40,940][300,1000]"),
        _node("Search here", bounds="[40,1020][500,1080]"),
    )
    monkeypatch.setattr(rp, "_maps_open_recents", lambda serial: (rp._ui_nodes(xml), True))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    assert rp.verify_maps_recents_clear("S") is True
    assert "PASS maps" in capsys.readouterr().out


def test_verify_maps_recents_fails_when_an_entry_survives(rp, monkeypatch, capsys):
    xml = _maps_screen(
        _node("Recent", bounds="[40,600][300,660]"),
        _node("Biju Patnaik International Airport", bounds="[40,700][900,760]"),
    )
    monkeypatch.setattr(rp, "_maps_open_recents", lambda serial: (rp._ui_nodes(xml), True))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    assert rp.verify_maps_recents_clear("S") is False
    out = capsys.readouterr().out
    assert "FAIL maps" in out and "Biju Patnaik International Airport" in out


def test_verify_maps_recents_fails_closed_when_maps_never_opened(rp, monkeypatch, capsys):
    """An unreadable screen must never read as 'clean'.

    A dump taken on the launcher has no Recent header either, so absence of the header is
    not evidence the list is clear -- it is evidence of nothing. Treating it as clean is
    the same shape as the Notes To-dos trap and the plain-tap re-add, both of which
    printed OK while achieving nothing.
    """
    monkeypatch.setattr(rp, "_maps_open_recents",
                        lambda serial: (rp._ui_nodes("<hierarchy/>"), False))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    assert rp.verify_maps_recents_clear("S") is False
    assert "never reached the search screen" in capsys.readouterr().out


def test_clear_maps_recents_reports_failure_when_entries_survive(rp, monkeypatch, capsys):
    """The sweep used to print '[ok] cleared' after its bounded loop whatever it achieved."""
    xml = _maps_screen(
        _node("Recent", bounds="[40,600][300,660]"),
        _node("restaurants", bounds="[40,700][900,760]", rid="android:id/title"),
    )
    monkeypatch.setattr(rp, "_maps_open_recents", lambda serial: (rp._ui_nodes(xml), True))
    monkeypatch.setattr(rp, "_pull_ui_dump", lambda serial, remote="/x": xml)
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    monkeypatch.setattr(rp.time, "sleep", lambda _s: None)
    assert rp.clear_maps_recents("S", apply=True) is False
    out = capsys.readouterr().out
    assert "survived the sweep" in out
    assert "[ok]" not in out


def test_clear_maps_recents_fails_closed_when_maps_never_opened(rp, monkeypatch, capsys):
    monkeypatch.setattr(rp, "_maps_open_recents",
                        lambda serial: (rp._ui_nodes("<hierarchy/>"), False))
    monkeypatch.setattr(rp, "sh", lambda serial, cmd, check=False: "")
    assert rp.clear_maps_recents("S", apply=True) is False
    assert "never reached the search screen" in capsys.readouterr().out


# ---- the full reset path must gate on the Maps leaks too ----------------------------
#
# This is the regression: verify_maps_run_notes_clear existed but was only reachable
# through --leak-cleanup-only, and the Recents list had no gate at all. The full reset is
# what precedes a fresh launch, so a silent cleanup failure there was invisible.


def _wire_full_verify(monkeypatch, rp, *, maps_clean: bool) -> dict[str, list]:
    """Stub every device touch the full --verify-only path makes, recording the gaps."""
    calls: dict[str, list] = {"verified": [], "full_reset": []}
    monkeypatch.setattr(rp, "connect_ok", lambda serial: True)
    for name in ("verify_calendar_view_mode", "verify_cloud_accounts", "verify_slides_deck",
                 "verify_meet_agenda", "assert_anchor_durability"):
        monkeypatch.setattr(rp, name, lambda *a, **k: True)
    monkeypatch.setattr(rp, "verify", lambda *a, **k: True)
    monkeypatch.setattr(rp, "verify_telegram_chat_clean",
                        lambda serial: calls["verified"].append("telegram") or True)
    monkeypatch.setattr(rp, "verify_budget_note",
                        lambda serial: calls["verified"].append("note") or True)
    monkeypatch.setattr(rp, "verify_maps_run_notes_clear",
                        lambda serial: calls["verified"].append("maps") or maps_clean)
    monkeypatch.setattr(rp, "verify_maps_recents_clear",
                        lambda serial: calls["verified"].append("maps_recents") or maps_clean)
    # --verify-only must not repair anything.
    for name in ("reset_settings", "clear_telegram_run_leaks", "clear_maps_run_notes",
                 "clear_maps_recents", "restore_budget_note", "restore_slides_deck"):
        monkeypatch.setattr(rp, name,
                            lambda *a, **k: calls["full_reset"].append(name) or True)
    return calls


def test_full_verify_only_gates_on_both_maps_leaks(rp, monkeypatch, capsys):
    calls = _wire_full_verify(monkeypatch, rp, maps_clean=True)
    monkeypatch.setattr(sys, "argv", [
        "reset_phone.py", "--serial", "S", "--profile", "public_v2", "--verify-only",
    ])
    assert rp.main() == 0
    assert calls["verified"] == ["telegram", "note", "maps", "maps_recents"]
    assert calls["full_reset"] == [], "--verify-only must not repair the phone"
    assert "RESULT PASS" in capsys.readouterr().out


def test_full_verify_only_blocks_on_a_surviving_maps_recents_entry(rp, monkeypatch, capsys):
    """A leaked Recent entry is a gate, not a warning: it aborts the launch."""
    _wire_full_verify(monkeypatch, rp, maps_clean=False)
    monkeypatch.setattr(sys, "argv", [
        "reset_phone.py", "--serial", "S", "--profile", "public_v2", "--verify-only",
    ])
    assert rp.main() == 1
    assert "RESULT FAIL" in capsys.readouterr().out
