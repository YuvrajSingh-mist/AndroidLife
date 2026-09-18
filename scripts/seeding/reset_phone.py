#!/usr/bin/env python3
"""Reset the AndroidLife benchmark phone to its pre-run baseline (non-rooted)."""

from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys
import time

# --- stray dump sweep (profile-independent) -----------------------------------
# Operator/agent sessions save `uiautomator dump` + `screencap` output to the shared
# storage ROOT as /sdcard/<name>.xml and /sdcard/<name>.png, and never clean up, so
# debris accumulates indefinitely -- 724 files had built up between 2026-07-29 and
# 2026-09-18 (the sweep cleared them). Nothing seeds or reads the root: all seeds live
# under Download/ or Obsidian/, and the root's *files* are exclusively dumps (verified),
# so these globs are safe. Applied to EVERY profile on --apply, because the debris is
# profile-independent. NOTE: this WILL remove a dump you saved by hand -- pull anything
# you want to keep BEFORE running --apply.
DEVICE_ROOT_DUMP_GLOBS = ["/sdcard/*.xml", "/sdcard/*.png"]

# --- profile: known run-artifact + seed facts for the public 50-task dataset ---
PROFILES: dict[str, dict] = {
    "public_v2": {
        # settings to restore: key:value where key = "system|secure|global:name"
        "settings": {"system:screen_off_timeout": "1800000"},
        # numbers the agent blocked during runs (run artifacts) - these get removed
        "blocked_numbers_to_remove": [
            "+912071167023", "+917968179241", "+917968179245", "+911600108194",
        ],
        # calendar event titles the agent created (run artifacts) - soft-deleted
        "calendar_titles_to_remove": [
            "Dentist appointment", "Dentist Appointment",
            "Wish Yuvraj Singh a happy birthday!", "Card Payment Due",
            "Maa's Birthday", "Yuvraj Singh's Birthday", "Hariom Sharma EVS's Birthday",
        ],
        # Downloads paths the agent created during runs - removed (quotes preserved)
        "downloads_to_remove": [
            "/sdcard/Download/Food Photos≠Memories 2021-23",
            "/sdcard/Download/PURCHASE_ORDER (1).xlsx",
            "/sdcard/Download/PURCHASE_ORDER (1) (1).xlsx",
            "/sdcard/Download/PURCHASE_ORDER (1) (2).xlsx",
            "/sdcard/Download/Q3_Report.pdf",
        ],
        # seed files that MUST be present after reset (baseline verify)
        "seed_files": [
            "/sdcard/Download/PURCHASE_ORDER.xlsx",
            "/sdcard/Download/SPORTS_VIDEO_DATA.xlsx",
            "/sdcard/Download/budget.xlsx",
            "/sdcard/Download/quote.xlsx",
            "/sdcard/Download/Weekly Agenda.txt",  # hard__google-meet-files__070
        ],
        # seed calendar events that MUST be present on the Google-synced calendar
        "seed_calendar_titles": [
            "shareholder AlphaCorp Q2 Review",
            "shareholder BetaTech Strategy",
            "shareholder GammaFund Governance",
            # hard__clock-calendar__023 clash + hard__google-meet-files__070 agenda meeting
            "Weekly Sync",
            "Gym",
            # easy__calendar__002 conflict pair (date-relative; see seed_calendar_events)
            "Team Sync",
            "Mentor 1 on 1",
        ],
        # Date-relative calendar seeds re-created at EVERY reset (cal_id=16,
        # device-local time) so the clock-calendar clash shift (07:00 -> 07:30)
        # and the meet-files "Weekly Sync 10 AM" meeting are always present for
        # the 3x variance runs.
        #
        # An entry is anchored either by "weekday" (next occurrence of that
        # weekday) or by "offset_days" (today + N). The meet-files meeting uses
        # offsets because Google Meet's "Scheduled" list only surfaces meetings
        # within ~48h: a Monday-anchored meeting is 3-6 days out whenever a run
        # starts midweek, so Meet showed nothing and hard__google-meet-files__070
        # could never pass. Seeding it at +1 and +2 keeps one occurrence inside
        # that window on the day the task actually runs.
        "seed_calendar_events": [
            {"title": "Weekly Sync", "weekday": "monday", "start": "07:00", "end": "08:00"},
            # `meet: True` = this occurrence is the Google-Meet agenda seed for
            # hard__google-meet-files__070. Meet only lists conferenced meetings, and
            # only within ~48h, so the verify gate asserts at least one of these
            # lands inside that window (a stale anchor silently fails the task).
            {"title": "Weekly Sync", "offset_days": 1, "start": "10:00", "end": "11:00", "meet": True},
            {"title": "Weekly Sync", "offset_days": 2, "start": "10:00", "end": "11:00", "meet": True},
            {"title": "Gym", "weekday": "tuesday", "start": "06:30", "end": "07:30"},
            # easy__calendar__002 ("any scheduling conflicts *tomorrow* afternoon?").
            # Anchored to today+1 so the pair always reads as TOMORROW on the run day.
            # Previously seeded by an out-of-band snippet pinned to `date.today() + 1`
            # at *seed* time, so a batch that started a day later (or crossed midnight)
            # left the conflicts on the run day and the task became unsolvable -- it
            # cost the 2026-09-16 run (seeded 15 Sep, batch started 16 Sep 01:13 ->
            # the agent's "tomorrow" was the 17th, which held no conflicts). Resetting
            # the pair here re-anchors it on every `--apply`, removing the manual step.
            {"title": "Team Sync", "offset_days": 1, "start": "14:00", "end": "15:00"},
            {"title": "Mentor 1 on 1", "offset_days": 1, "start": "14:30", "end": "15:30"},
        ],
        # Meet package to drive for the pre-run gate (first one installed wins).
        # `tachyon` is Google Meet on this device (Duo-rebrand lineage); `meetings`
        # is the standalone app and is NOT installed here.
        "meet_packages": ["com.google.android.apps.meetings", "com.google.android.apps.tachyon"],
        # Titles that must be visible in Meet -> "Scheduled" on run day.
        "meet_expected_titles": ["Weekly Sync"],
        # How far ahead Meet's "Scheduled" list reaches (measured ~48h: today/+1/+2
        # visible, +3/+4 hidden).
        "meet_window_hours": 48.0,
        # Call-log seeds for easy__phone__005 ("how many calls I've made today...
        # total call time"). The call log IS writable from a non-rooted adb
        # (`content insert --uri content://call_log/calls`) -- a note in the docs
        # claimed otherwise, but scripts/seeding/seed_data.py has always done exactly
        # this for the 530 corpus. So this is a deterministic seed, not an operator
        # "go make a real phone call" step, and the answer is no longer the degenerate
        # 0 seconds you get from an empty log.
        #
        # Every seeded call is OUTGOING: the prompt asks for the calls the user MADE.
        # Keeping the whole day outgoing means "outgoing only" and "all calls today"
        # (the reading a 2026-08-30 audit used) give the SAME total, so the verdict does
        # not hinge on which way the grader reads it.
        #
        # easy__phone__002 (day 1) places a real call, so the day-2 total also includes
        # that row; these seeds are the fixed baseline underneath it.
        "seed_calls": [
            {"number": "+919000000001", "duration": 72},  # 1:12
            {"number": "+919000000002", "duration": 45},  # 0:45  -> today total 1:57
        ],
        # Canonical cloud account per app (see .agents/skills/reset-phone/SKILL.md ->
        # "Cloud account map"). The device carries 6 Google accounts and each app
        # remembers its own selection, so an app CAN drift onto another account --
        # and then it cannot see its own seeded cloud data (that is exactly how
        # easy__google-slides__001 lost its `Q3 Review` deck on 2026-09-18).
        # Asserted by verify_cloud_accounts(); skip with --no-account-check.
        "canonical_accounts": {
            "com.google.android.gm": "ranirajesh786@gmail.com",                    # Gmail
            "com.google.android.apps.docs": "ranirajesh786@gmail.com",             # Drive
            "com.google.android.apps.docs.editors.docs": "ranirajesh786@gmail.com",   # Docs
            "com.google.android.apps.docs.editors.slides": "ranirajesh786@gmail.com", # Slides
            "com.google.android.calendar": "yuvraj.mist@gmail.com",                # Calendar
            "com.google.android.apps.tachyon": "yuvraj.mist@gmail.com",            # Meet
            "com.google.android.apps.photos": "rajeshceo2015@gmail.com",           # Photos
        },
        # The Google Slides deck for easy__google-slides__001 ("how many slides?").
        # It is NOT a native cloud deck and NOT file-seeded -- it is an uploaded .pptx
        # that lives as a device file (and in Drive on ranirajesh786@gmail.com), so
        # nothing restores it if a run edits or deletes it. The grader carries no
        # ground truth for this task, so the count is asserted here instead.
        # NOTE the name is `Q3_Review.pptx` (underscore), not the `Q3 Review` var value.
        "slides_deck": {
            "path": "/sdcard/Download/Q3_Review.pptx",
            "expected_slides": 8,
        },
        # the contact that runs mangle (easy-contacts-001) - restored to this name
        "contact_email": "akashveyron33@gmail.com",
        "contact_display": "Akash Kumar",
        "contact_given": "Akash",
        "contact_last": "Kumar",
        # Seed files whose CONTENT runs MUTATE (not just create). These are restored
        # to their exact baseline content on reset so every variance-check run starts
        # identical (medium__gallery__007 pastes photos into Food Favourites.md;
        # hard__drive-*-telegram__049/010 log dates into Budget Deadline.md).
        "restore_file_contents": {
            "/sdcard/Obsidian/Papers vault oneplus /Food Favourites.md": (
                "# Food Favourites\n\n"
                "Quick reference of my favourite food photos pulled from Google Photos. Keep\n"
                "these in sync with the album - one photo per dish, added from Google Photos\n"
                "Favourites by matching the photo description to the heading.\n\n"
                "## Pancakes\n\n## Pizza\n\n## Veggie Bowl\n"
            ),
            "/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md": (
                "# Budget Deadline\n\n"
                "## Shared budget spreadsheet - FY26 finalisation\n\n"
                "The family shared budget spreadsheet (the one we all add our monthly spends\n"
                "to) must be **finalised by 2026-08-10** so the numbers are locked before the\n"
                "new financial-year planning round starts.\n\n"
                "Last reviewed: 2026-07-10.\n"
            ),
            # hard__google-meet-files__070: the agenda doc the agent must open (kept
            # at baseline so a run can't mutate it between variance checks).
            "/sdcard/Download/Weekly Agenda.txt": (
                "Weekly Agenda\n\n"
                "1. Opening / standup (5 min)\n"
                "2. Review last week action items (10 min)\n"
                "3. Project status updates (15 min)\n"
                "4. New business / decisions (10 min)\n"
                "5. Action items + owners (5 min)\n"
            ),
            # hard__google-search-obsidian-telegram__057: the agent updates this
            # note with today's recorded value each run -> restore to the baseline
            # (2026-08-13 value) so variance-check runs start identical.
            "/sdcard/Obsidian/Papers vault oneplus /Stock Watch.md": (
                "# Stock Watch\n\n"
                "Watchlist for the stocks I follow. I only act when a ticker crosses its\n"
                "threshold since the last recorded value.\n\n"
                "- Stock: Reliance Industries\n"
                "- Threshold: 1,400 INR\n"
                "- Last recorded value: 1,320.50 INR\n"
                "- Date: 2026-08-13\n\n"
                "## Watchlist rules\n"
                "- If the price crosses the threshold, message the group and update this note\n"
                "  with today's value.\n"
                "- Re-check on the day I'm tracking; don't chase intraday noise.\n"
                "- NSE ticker: RELIANCE.\n\n"
                "## Other tickers I follow\n"
                "- TCS: threshold 4,000 (currently ~3,950).\n"
                "- HDFC Bank: threshold 1,700 (currently ~1,680).\n"
            ),
        },
        # run-created Obsidian paste artifacts: Obsidian stores pasted images in the
        # vault root as "Pasted image YYYYMMDDHHMMSS.jpg" (no attachment folder is
        # configured in .obsidian/app.json). The gallery task's paste creates these.
        "obsidian_pasted_images": [
            "/sdcard/Obsidian/Papers vault oneplus /Pasted image*",
        ],
        # seed file CONTENT checks for the verify gate (baseline must still hold)
        "seed_file_contents": {
            "/sdcard/Obsidian/Papers vault oneplus /Food Favourites.md": "## Veggie Bowl",
            "/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md": "Last reviewed: 2026-07-10.",
            "/sdcard/Download/Weekly Agenda.txt": "Opening / standup",
        },
        # App-private / cloud run artifacts the reset CANNOT auto-delete (non-rooted)
        # - see .agents/skills/reset-phone/SKILL.md step 2 for the full list.
        "manual_ui_cleanup": [
            "Google Photos: the 3 food-photo captions + Favourites for medium__gallery__007 live in the app-private Photos DB - the task only reads them, so they persist across runs; if ever lost, re-add captions + favourites in the Photos UI before a run (SAME account the Photos app is signed into - favourites/captions do NOT carry across Google accounts)",
            "Gmail: unstar starred emails + remove the label the agent created; delete the sent-with-attachment email",
            "Notes: delete run notes (Card Payment Due, Budget Tracker, Birthday Reminders, IndiGo flight note)",
            "Obsidian: delete run notes (e.g. Birthday Reminders)",
            "Photos/Gallery: delete run albums (Invoices, Trip 2026); unstar the 2 starred photos",
            "YT Music: delete the 'Chill Vibes' playlist",
            "Telegram: unmute the 'Forever 21' group; keep the meetup thread UNRESOLVED (edited 2026-08-21: last message is \"22nd could work for me too, let me confirm once she's free\" — no settled date/time/venue in the chat, so hard__telegram-calendar__016 forces ask_user; do NOT re-add a settling message)",
            "Digital Wellbeing: remove the 30-min app timers the agent set",
            "Camera: delete the run-recorded 'Camera Video' clip if present",
            "Drive: delete 'Copy of SPORTS_VIDEO_DATA' leftovers; re-download the 5 uploaded files, then delete that Drive folder",
        ],
    },
    # Day-1 of the 530 schedule: run-artifact cleanup for the day-1 task set
    # (Chrome offline downloads, Obsidian run notes, Camera run photos, calendar
    # events the day-1 calendar tasks created on 2026-08-05). Seed verification for
    # a day profile is done by scripts/verify_day1_seeds.py -- not here (this
    # profile has no seed_* keys, so verify() only checks settings/blocked).
    "day_1": {
        "settings": {"system:screen_off_timeout": "1800000"},
        "blocked_numbers_to_remove": [
            "+912071167023", "+917968179241", "+917968179245", "+911600108194",
        ],
        # Chrome "Download page" offline files created by easy__chrome__001 runs
        # (including the 2026-08-08 re-run) - these are run artifacts. Chrome names
        # them variably ("Google", "Google (1)", "Google – My Activity", ...) so a
        # shell glob is used in addition to the exact paths.
        "device_paths_to_remove": [
            "/sdcard/Download/Google",
            "/sdcard/Download/Google (1)",
            "/sdcard/Download/Google (2)",
            "/sdcard/Download/Google – My Activity",
            # Camera run photos from easy/medium__camera__001 / gallery tasks
            "/sdcard/DCIM/Camera/today_photo_1.jpg",
            "/sdcard/DCIM/Camera/today_photo_2.jpg",
            "/sdcard/DCIM/Camera/today_photo_3.jpg",
            "/sdcard/DCIM/Camera/today_photo_4.jpg",
            "/sdcard/DCIM/Camera/today_photo_5.jpg",
            "/sdcard/DCIM/Camera/trip_1.jpg",
            "/sdcard/DCIM/Camera/trip_2.jpg",
            "/sdcard/DCIM/Camera/trip_3.jpg",
            "/sdcard/DCIM/Camera/trip_4.jpg",
            "/sdcard/DCIM/Camera/Desk_Object.heic",
        ],
        "device_paths_glob": ["/sdcard/Download/Google*"],
        # Obsidian vault run-created notes/folders (the vault is on /sdcard, ADB-visible).
        # The 'Stock Watch.md' seed is deliberately NOT listed here.
        "obsidian_vault_remove": [
            "/sdcard/Obsidian/Papers vault oneplus /Best Budget Smartphones 2026.md",
            "/sdcard/Obsidian/Papers vault oneplus /Daily Log.md",
            "/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md",
            "/sdcard/Obsidian/Papers vault oneplus /Photo Log.md",
            "/sdcard/Obsidian/Papers vault oneplus /Research Notes.md",
            "/sdcard/Obsidian/Papers vault oneplus /Daily Reflection.md",
            "/sdcard/Obsidian/Papers vault oneplus /Untitled 4.md",
            "/sdcard/Obsidian/Papers vault oneplus /Untitled 5.md",
            "/sdcard/Obsidian/Papers vault oneplus /Bedtime.md",
            "/sdcard/Obsidian/Papers vault oneplus /Meeting Notes",
            "/sdcard/Obsidian/Papers vault oneplus /testdir",
        ],
        # calendar events the old Day-1 run created on 2026-08-05 (by _id, so the
        # empty-title event is covered too). These are NOT day-1 seeds (those are
        # Lunch with Maa / Weekly_Standup / Old_Gym_Class / meeting).
        "calendar_ids_to_remove": [3584, 3586, 3623, 3650, 3691],
        # App-private run artifacts the reset CANNOT delete via ADB (non-rooted):
        # these MUST be cleaned by hand in the UI before re-running, or the agent
        # will see leftovers from the previous run. Printed explicitly by the script.
        "manual_ui_cleanup": [
            "Notes app: delete run-created pinned note(s) 'Open-source software' (medium__chrome__001)",
            "Chrome: remove the run-created 'Open-source software' bookmark from Mobile bookmarks",
            "Telegram: clear old sent messages to Yuvraj Airtel (medium__chrome-telegram__001 / gallery share / hard tasks)",
        ],
    },
    # Day-2 of the 530 schedule: run-artifact cleanup for the day-2 task set
    # (2026-08-06 run). Day-2 seeds (invoice_seed.pdf + {contact} email) are NOT
    # touched here - seed verification is scripts/verify_day1_seeds.py --day 2.
    "day_2": {
        "settings": {"system:screen_off_timeout": "1800000"},
        "blocked_numbers_to_remove": [
            "+912071167023", "+917968179241", "+917968179245", "+911600108194",
        ],
        # Calendar reminder created by medium__google-maps__001 (title-based removal).
        "calendar_titles_to_remove": ["Leave for Bhubaneswar Airport"],
        "manual_ui_cleanup": [
            "Notes app: delete run-created notes ('SUM Hospital - 2.8 km' from hard__google-maps-notes__005; largest-file note from medium__files__001; Myntra thread summary from medium__gmail-notes__001; invoice/amount note from hard__files-notes__011; music note from medium__music__001)",
            "Notes app: delete the Maps run notes 'parked here' (easy__google-maps__004) and 'Fastest Route to Bhubaneswar Airport' (medium__google-maps__002), then REMOVE the home-screen Notes widget those runs add. NOTE: the app reopens the last-edited note on launch, so a leftover note makes the next agent start INSIDE a note - confirmed 2026-09-16 it burned all 60 steps for qwen-26 + kimi-30v and let gemini-26 pass on the pre-existing note.",
            "Google Maps: clear the search box's *Recent* list (medium__google-maps__002). LONG-PRESS each recent row -> 'Delete suggested search?' -> Delete; do NOT plain-tap the row (that opens the place page AND re-adds it to history - happened 16 Sep with 'Treebo Aasma Downtown'). Leftover rows let agents skip typing the destination entirely (7 of 13 runs on 2026-09-16, incl. 3 that PASSED on the leftover). Then force-stop Maps so it reopens on the home/search state, not a leftover route/place page.",
            "Notes app: restore the font-size note's text size 20 -> 16 (easy__notes__001)",
            "Obsidian: delete the run-created send-record note from hard__photos-gmail-obsidian__012 (title from that run's note)",
            "Gmail: unstar the urgent Myntra email + unread the 8 marked-read (medium__gmail__001); delete the forwarded email sent to Yuvraj Airtel (easy__gmail__001); delete the sent event-photo email (hard__photos-gmail-obsidian__012)",
            "Google Photos: delete the shared 'Memories 2021' album (medium__google-photos__001; prior run also created a hallucinated 'GOA TRIP' album - remove that too if present) + unfavorite the 6 photos; unstar the event photo (hard__photos-gmail-obsidian__012)",
            "YouTube Music: remove 'THATS WHAT I WANT' from favorites (medium__music__001); unsubscribe from the Harsha visa Times channel (medium__youtube__001)",
            "Telegram: clear the YouTube link sent to Yuvraj Airtel (medium__youtube__001)",
        ],
    },
    # Day-3 of the 530 schedule: run-artifact cleanup for the day-3 task set
    # (2026-08-06 run). Day-3 seed (Obsidian 'Bedtime.md') is NOT touched here -
    # seed verification is scripts/verify_day1_seeds.py --day 3. All day-3 run
    # artifacts are app-private/UI-only, so there are no ADB path cleanups.
    "day_3": {
        "settings": {"system:screen_off_timeout": "1800000"},
        "blocked_numbers_to_remove": [
            "+912071167023", "+917968179241", "+917968179245", "+911600108194",
        ],
        "manual_ui_cleanup": [
            "Contacts: restore 'Maa''s saved email to its original value (easy__contacts__003 changed it to yuvraj.new@example.com)",
            "Messages: re-create the 'Yuvraj Airtel' conversation deleted by easy__messages__003 (SMS insert blocked - send a real message); delete any agent-sent 'Test message for custom tone' / 'Testing custom notification tone' run artifacts (hard__messages-notes__078)",
            "Messages: restore Yuvraj Airtel's thread notification tone (hard__messages-notes__078 may leave a custom tone, e.g. 'Allay') back to Default; the device has NO 'Akash Kumar' contact/thread (verified 2026-08-11) - the ask_user_fact now targets Yuvraj Airtel",
            "Google Drive: delete the 'Copy of Weekly Review' created by easy__google-drive__001",
            "YouTube Music: remove the 'Raining Night ASMR' download + clear the sleep timer set by hard__music-obsidian__077",
            "Clock: remove any run-created alarm (hard__music-obsidian__077 only read existing alarms)",
            "Chrome: clear Swiggy browsing from easy__shopping-delivery-browser__001 if desired",
        ],
    },
}

CAL_URI = "content://com.android.calendar/events"
CONTACTS_DATA_URI = "content://com.android.contacts/data"
CONTACTS_URI = "content://com.android.contacts/contacts"
BLOCKED_URI = "content://com.android.blockednumber/blocked"
CALL_URI = "content://call_log/calls"


def sh(serial: str, cmd: str, check: bool = False) -> str:
    """Run a command on the device shell, return stdout."""
    proc = subprocess.run(
        ["adb", "-s", serial, "shell", cmd], capture_output=True, text=True
    )
    if check and proc.returncode != 0:
        print(f"  !! adb failed ({proc.returncode}): {cmd}")
        print("  " + proc.stderr.strip()[:300])
    return proc.stdout


def connect_ok(serial: str) -> bool:
    out = subprocess.run(
        ["adb", "-s", serial, "shell", "echo", "OK"], capture_output=True, text=True
    )
    return out.returncode == 0 and "OK" in out.stdout


def quote(s: str) -> str:
    """Single-quote a string for the remote sh, escaping embedded single quotes."""
    return "'" + s.replace("'", "'\\''") + "'"


def reset_settings(serial: str, settings: dict[str, str], apply: bool) -> None:
    for key, value in settings.items():
        ns, _, name = key.partition(":")
        cur = sh(serial, f"settings get {ns} {name}").strip()
        # NB: the "(was: ...)" annotation is print-only - it must never be part of
        # the command sent to the device shell (a literal '(' breaks sh).
        command = f"settings put {ns} {name} {value}"
        if apply:
            sh(serial, command, check=True)
            print(f"  [ok]  {command}   (was: {cur!r})")
        else:
            print(f"  [dry] {command}   (was: {cur!r})")


def unblock_numbers(serial: str, numbers: list[str], apply: bool) -> None:
    rows = sh(serial, f"content query --uri {BLOCKED_URI}")
    for num in numbers:
        present = re.search(rf"e164_number={re.escape(num)}", rows)
        if apply:
            if present:
                sh(
                    serial,
                    f"content delete --uri {BLOCKED_URI} --where \"original_number='{num}'\"",
                    check=True,
                )
                print(f"  [ok]  unblocked {num}")
            else:
                print(f"  [--]  {num} not blocked (already clean)")
        else:
            print(f"  [dry] unblock {num} (present={bool(present)})")


def _calendar_ids_for_titles(serial: str, titles: list[str]) -> list[str]:
    """Return the `_id` of every LIVE (deleted=0) event whose title matches.

    One coherent query (colon-separated projection) so the parsed fields always
    belong to the same row — zipping separate per-column queries silently
    misaligns when the provider reorders rows.
    """
    rows = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:deleted")
    ids: list[str] = []
    for line in rows.splitlines():
        m = re.search(r"_id=(\d+),", line)
        t = re.search(r"title=([^,]*),", line)
        d = re.search(r"deleted=([01])", line)
        if not (m and t and d):
            continue
        if d.group(1) == "1":
            continue  # already soft-deleted; nothing to clean up
        if t.group(1).strip() in titles:
            ids.append(m.group(1))
    return ids


def remove_calendar_events(serial: str, titles: list[str], apply: bool) -> None:
    """Soft-delete every LIVE event whose title matches, then assert none remain.

    The events provider clears **one row per `content delete` call**, so a single
    `--where "title=..."` (or a fixed 6x retry loop) leaves extras behind whenever
    a previous reset inserted more copies than the loop runs for. Runs are also
    known to leave duplicate copies, and `verify()` only checks presence, not
    count — so the duplicates pass the gate and then confuse later audits.
    Deleting each matched `_id` individually and re-querying makes the cleanup
    actually idempotent.
    """
    if not titles:
        return
    ids = _calendar_ids_for_titles(serial, titles)
    if not apply:
        print(f"  [dry] soft-delete run-artifact events (matched ids): {ids or 'none'}")
        return
    if not ids:
        print("  [--]  no run-artifact calendar events to delete")
        return
    for eid in ids:
        sh(serial, f"content delete --uri {CAL_URI} --where \"_id={eid}\"", check=True)
    left = _calendar_ids_for_titles(serial, titles)
    msg = f"  [ok]  soft-deleted {len(ids)} run-artifact events: {ids}"
    if left:
        # Do not fail the reset: the re-seed below still inserts a clean copy.
        msg += f"  [warn] still live after delete: {left}"
    print(msg)


def restore_contact(serial: str, prof: dict, apply: bool) -> None:
    if not prof.get("contact_email"):
        print("  [--]  profile has no contact to restore; skipping")
        return
    rows = sh(
        serial,
        f"content query --uri {CONTACTS_DATA_URI} --projection _id:raw_contact_id:mimetype:data1:data2:data3:data4 --where \"mimetype='vnd.android.cursor.item/email_v2'\"",
    )
    raw_id = None
    for line in rows.splitlines():
        m = re.search(r"data1=([^,]*),", line)
        r = re.search(r"raw_contact_id=(\d+),", line)
        if m and r and m.group(1).strip() == prof["contact_email"]:
            raw_id = r.group(1)
            break
    if raw_id is None:
        print("  [--]  target contact not found; nothing to restore")
        return
    name_rows = sh(
        serial,
        f"content query --uri {CONTACTS_DATA_URI} --projection _id:mimetype:data1:data2:data3:data4 --where \"raw_contact_id={raw_id}\"",
    )
    name_id = org_id = None
    for line in name_rows.splitlines():
        if "vnd.android.cursor.item/name" in line:
            m = re.search(r"_id=(\d+),", line)
            name_id = m.group(1) if m else name_id
        if "vnd.android.cursor.item/organization" in line and "Sahoo" in line:
            m = re.search(r"_id=(\d+),", line)
            org_id = m.group(1) if m else org_id
    if apply:
        if name_id:
            sh(
                serial,
                f"content update --uri {CONTACTS_DATA_URI} --bind \"data1:s:{prof['contact_display']}\" --bind \"data2:s:{prof['contact_given']}\" --bind \"data3:s:{prof['contact_last']}\" --bind \"data4:s:\" --where \"_id={name_id}\"",
                check=True,
            )
        if org_id:
            sh(serial, f"content delete --uri {CONTACTS_DATA_URI} --where \"_id={org_id}\"", check=True)
        print(f"  [ok]  restored contact {prof['contact_display']} (name_row={name_id}, org_row={org_id})")
    else:
        print(f"  [dry] restore contact -> {prof['contact_display']} (name_row={name_id}, org_row={org_id})")


def remove_paths(serial: str, paths: list[str], apply: bool) -> None:
    """Remove arbitrary device paths (files or dirs), preserving quotes."""
    for path in paths:
        if apply:
            sh(serial, f"rm -rf {quote(path)}", check=True)
            print(f"  [ok]  rm {path}")
        else:
            print(f"  [dry] rm {path}")


def remove_glob(serial: str, patterns: list[str], apply: bool) -> None:
    """Remove files matching shell glob patterns (NOT quoted, so `*` expands)."""
    for pattern in patterns:
        if apply:
            sh(serial, f"rm -f {pattern}", check=True)
            print(f"  [ok]  rm -f {pattern}")
        else:
            print(f"  [dry] rm -f {pattern}")


def remove_by_find(serial: str, patterns: list[str], apply: bool) -> None:
    """Remove files matching a glob inside a (possibly space-containing) dir via `find -delete`.

    Unlike remove_glob, both the dir AND the glob are single-quoted, so spaces in the
    path (e.g. 'Papers vault oneplus /Pasted image*') are safe while `*` still expands.
    """
    for pattern in patterns:
        dirname, basename = os.path.split(pattern)
        cmd = f"find {quote(dirname)} -maxdepth 1 -name {quote(basename)} -delete"
        if apply:
            sh(serial, cmd, check=True)
            print(f"  [ok]  {cmd}")
        else:
            print(f"  [dry] {cmd}")


def restore_file_contents(serial: str, entries: dict[str, str], apply: bool) -> None:
    """Overwrite seed files that runs mutate back to their exact baseline content.

    Content is base64-encoded on the host and decoded on-device (`base64 -d`) so no
    shell metacharacter in the note text can break the command.
    """
    for path, content in entries.items():
        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        if apply:
            sh(serial, f"echo {b64} | base64 -d > {quote(path)}", check=True)
            print(f"  [ok]  restored file content: {path}")
        else:
            print(f"  [dry] restore file content: {path}")


def remove_calendar_by_ids(serial: str, ids: list[int], apply: bool) -> None:
    """Soft-delete calendar events by their _id (covers empty-title run artifacts)."""
    if not ids:
        return
    where = ",".join(str(i) for i in ids)
    if apply:
        sh(serial, f"content delete --uri {CAL_URI} --where \"_id IN ({where})\"", check=True)
        print(f"  [ok]  soft-deleted calendar events by id: {ids}")
    else:
        print(f"  [dry] soft-delete calendar events by id: {ids}")


def _live_calendar_events(serial: str, titles: list[str]) -> list[tuple[str, str, int | None]]:
    """Return `(id, title, dtstart_ms)` for LIVE events whose title matches exactly.

    Exact-title matching avoids the `Old_Gym_Class` / `Gym` substring trap, and
    dtstart is carried alongside the id so the caller can match a seed to the
    existing copy that holds *that* time slot.
    """
    rows = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:dtstart:deleted")
    found: list[tuple[str, str, int | None]] = []
    for line in rows.splitlines():
        m = re.search(r"_id=(\d+),", line)
        t = re.search(r"title=([^,]*),", line)
        s = re.search(r"dtstart=(\d+)", line)
        d = re.search(r"deleted=([01])", line)
        if not (m and t and d) or d.group(1) == "1":
            continue
        if t.group(1).strip() in titles:
            found.append((m.group(1), t.group(1).strip(), int(s.group(1)) if s else None))
    return found


def _calendar_ids_with_meet_link(serial: str) -> set[str]:
    """`_id`s of LIVE events that carry a Google Meet conference link.

    Read from `description`, which is where the sync adapter stores the join block.
    Rows are split on the `Row: N ` marker rather than on newlines: a description
    contains embedded newlines, so the URL lands several physical lines below the
    `_id=` field and a per-line scan false-negatives every linked event.
    """
    rows = sh(serial, f"content query --uri {CAL_URI} "
                      f"--projection _id:description:deleted")
    out: set[str] = set()
    for block in re.split(r"^Row: \d+ ", rows, flags=re.M)[1:]:
        i = re.match(r"_id=(\d+),", block)
        d = re.search(r"deleted=([01])", block)
        if not i or (d and d.group(1) == "1"):
            continue
        if "meet.google.com/" in block:
            out.add(i.group(1))
    return out


def ensure_calendar_events(serial: str, events: list[dict], apply: bool) -> None:
    """(Re)create date-relative calendar seeds so clash/agenda meetings exist at
    every reset (variance-safe for the 3x public runs).

    Shifts an existing copy in place when one already holds that title and time
    slot, and only inserts when there is nothing to shift. Used by
    hard__clock-calendar__023 (Weekly Sync Mon 07:00 + Gym Tue 06:30 -> clash
    shift to 07:30) and hard__google-meet-files__070 (Weekly Sync 10:00 agenda
    meeting).

    An entry carries either `weekday` (next occurrence of that weekday) or
    `offset_days` (today + N); the meet-files agenda meeting uses offsets so at
    least one occurrence lands inside Google Meet's ~48h "Scheduled" window on
    the day the task runs.

    In-place shifting matters because a Meet conference link lives in Google
    sync-adapter columns that the non-rooted `content` CLI cannot write (bind
    values reject ':', and a Meet URL always contains '://'). The old
    delete-then-insert therefore silently dropped any conferencing link on every
    reset, which is why hard__google-meet-files__070 could never see its meeting
    in Meet. Shifting dates preserves it.
    """
    if not events:
        return
    import datetime
    from zoneinfo import ZoneInfo

    tz_name = sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")
    weekday_index = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                     "friday": 4, "saturday": 5, "sunday": 6}
    titles = [e["title"] for e in events]
    existing = _live_calendar_events(serial, titles)
    # Only queried when a meet-marked seed exists: pre-fix resets migrated the
    # unlinked duplicate into Meet's window slot, so the link has to be steered.
    linked = _calendar_ids_with_meet_link(serial) if any(e.get("meet") for e in events) else set()
    if not apply:
        print(f"  [dry] ensure date-relative calendar seeds: {titles}")
        print(f"  [dry] would date-shift {len(existing)} live seed event(s) in place")
        return

    def hhmm(ms: int) -> str:
        return datetime.datetime.fromtimestamp(ms / 1000, tz=tz).strftime("%H:%M")

    def day_of(ms: int) -> datetime.date:
        return datetime.datetime.fromtimestamp(ms / 1000, tz=tz).date()

    today = datetime.date.today()
    used: set[str] = set()
    for ev in events:
        if "offset_days" in ev:
            d = today + datetime.timedelta(days=int(ev["offset_days"]))
        else:
            target = weekday_index[ev["weekday"]]
            days_ahead = (target - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # next week's occurrence, never today
            d = today + datetime.timedelta(days=days_ahead)

        def epoch(hhmm_str: str) -> int:
            h, m = map(int, hhmm_str.split(":"))
            return int(datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=tz).timestamp() * 1000)

        dtstart, dtend = epoch(ev["start"]), epoch(ev["end"])
        # Match on title + time-of-day. PREFER an exact-date copy (the steady-state
        # case), but fall back to any same-time copy so we SHIFT it in place rather
        # than delete+insert.
        #
        # The fallback is load-bearing: a Meet conference link cannot be written by
        # the non-rooted `content` CLI (bind values reject ':', and the provider
        # drops direct `description` writes on synced rows), so a delete+insert
        # silently DESTROYS it. Before this fallback existed, an anchor that was
        # more than a day stale (i.e. any reset not run on consecutive days) matched
        # nothing, inserted two fresh unlinked copies, and deleted the linked one —
        # taking hard__google-meet-files__070 back to invisible.
        def _pick(*, exact_date: bool, prefer_link: bool) -> str | None:
            for eid, etitle, eds in existing:
                if eid in used or etitle != ev["title"] or eds is None:
                    continue
                if hhmm(eds) != ev["start"]:
                    continue
                if exact_date and day_of(eds) != d:
                    continue
                if prefer_link and eid not in linked:
                    continue
                return eid
            return None

        # A `meet: True` seed must end up as the LINKED copy, because the link is what
        # makes the meeting visible in Meet at all -- and only the run-day+1 slot lands
        # inside Meet's ~48h "Scheduled" window. Date-exactness alone is not enough: on
        # consecutive-day resets the unlinked duplicate already occupies the +1 slot, so
        # an exact-date-first pick hands that slot to the UNLINKED copy and pushes the
        # linked one to +2 -- silently out of the window (this actually happened on the
        # 2026-09-19 run day). Prefer the linked copy first, then fall back.
        if ev.get("meet") and linked:
            match = (_pick(exact_date=True, prefer_link=True)
                     or _pick(exact_date=False, prefer_link=True)
                     or _pick(exact_date=True, prefer_link=False)
                     or _pick(exact_date=False, prefer_link=False))
        else:
            match = _pick(exact_date=True, prefer_link=False) or _pick(exact_date=False, prefer_link=False)
        if match:
            sh(serial, f"content update --uri {CAL_URI} "
                       f"--bind dtstart:l:{dtstart} --bind dtend:l:{dtend} "
                       f"--where \"_id={match}\"", check=True)
            used.add(match)
            print(f"  [ok]  shifted calendar event '{ev['title']}' to {d} "
                  f"{ev['start']}-{ev['end']} in place (_id={match}, conferencing kept)")
        else:
            cmd = (
                f"content insert --uri {CAL_URI} --bind title:s:{quote(ev['title'])} "
                f"--bind dtstart:l:{dtstart} --bind dtend:l:{dtend} "
                f"--bind calendar_id:i:16 --bind allDay:i:0 "
                f"--bind eventTimezone:s:{quote(tz_name)} --bind hasAlarm:i:0"
            )
            sh(serial, cmd, check=True)
            print(f"  [ok]  seeded calendar event '{ev['title']}' {d} "
                  f"{ev['start']}-{ev['end']} ({tz_name})")

    # Live copies we did not shift are stale duplicates or run artifacts. Delete
    # one id at a time: the provider clears a single row per `content delete`.
    leftovers = [eid for eid, _t, _s in existing if eid not in used]
    for eid in leftovers:
        sh(serial, f"content delete --uri {CAL_URI} --where \"_id={eid}\"", check=True)
    if leftovers:
        print(f"  [ok]  soft-deleted {len(leftovers)} stale seed cop(y/ies): {leftovers}")

    # Two identical titles (e.g. "Weekly Sync" 07:00 + 10:00) are legitimate, so
    # compare against the expected count per title rather than asserting 1.
    expected: dict[str, int] = {}
    for ev in events:
        expected[ev["title"]] = expected.get(ev["title"], 0) + 1
    for title, want in expected.items():
        got = len(_calendar_ids_for_titles(serial, [title]))
        flag = "ok" if got == want else "WARN"
        print(f"  [{flag}]  calendar seed '{title}': {got} live event(s) (want {want})")


def _calls_today(serial: str) -> list[tuple[str, int, str]]:
    """`(id, duration_s, type)` for call-log rows dated TODAY on the device."""
    import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata")
    today = datetime.datetime.now(tz).date()
    rows = sh(serial, f"content query --uri {CALL_URI} --projection _id:date:duration:type")
    out: list[tuple[str, int, str]] = []
    for line in rows.splitlines():
        i = re.search(r"_id=(\d+),", line)
        d = re.search(r"date=(\d+)", line)
        if not (i and d):
            continue
        when = datetime.datetime.fromtimestamp(int(d.group(1)) / 1000, tz=tz)
        if when.date() != today:
            continue
        dur = re.search(r"duration=(\d+)", line)
        typ = re.search(r"type=(\d+)", line)
        out.append((i.group(1), int(dur.group(1)) if dur else 0, typ.group(1) if typ else "?"))
    return out


def ensure_call_log(serial: str, calls: list[dict], apply: bool) -> None:
    """Seed TODAY's call log so easy__phone_005 has a definite, non-zero answer.

    Today's rows are cleared first, which makes `--apply` idempotent: a second reset
    on the same day reproduces the same log instead of stacking duplicates. Only rows
    dated today are touched, so the historical log is left intact.

    Timestamps sit shortly before the reset and are clamped to just after midnight, so
    the calls always read as "today" even when the reset runs at 00:xx.
    """
    if not calls:
        return
    if not apply:
        print(f"  [dry] ensure call-log seeds today: {len(calls)} call(s)")
        return
    import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata")
    now = datetime.datetime.now(tz)
    floor = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=1)

    cleared = 0
    for eid, _dur, _typ in _calls_today(serial):
        sh(serial, f"content delete --uri {CALL_URI} --where \"_id={eid}\"")
        cleared += 1

    for idx, call in enumerate(calls):
        # Older seeds first; 12 minutes apart so the log reads naturally.
        ts = now - datetime.timedelta(minutes=10 + (len(calls) - 1 - idx) * 12)
        if ts < floor:
            ts = floor + datetime.timedelta(minutes=idx)  # break ties at 00:xx resets
        sh(serial, f"content insert --uri {CALL_URI} "
                   f"--bind number:s:{call['number']} "
                   f"--bind date:l:{int(ts.timestamp() * 1000)} "
                   f"--bind duration:i:{int(call['duration'])} "
                   f"--bind type:i:2 --bind new:i:0 --bind is_read:i:1")
    total = sum(int(c["duration"]) for c in calls)
    print(f"  [ok]  call log: seeded {len(calls)} outgoing call(s) today, total {total}s "
          f"({cleared} prior row(s) cleared)")


def verify(serial: str, prof: dict) -> bool:
    ok = True
    print("== baseline verify ==")
    for key, value in prof.get("settings", {}).items():
        ns, _, name = key.partition(":")
        cur = sh(serial, f"settings get {ns} {name}").strip()
        good = cur == value
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'} settings {ns}:{name} = {cur!r} (want {value!r})")
    rows = sh(serial, f"content query --uri {BLOCKED_URI}")
    for num in prof.get("blocked_numbers_to_remove", []):
        gone = not re.search(rf"e164_number={re.escape(num)}", rows)
        ok &= gone
        print(f"  {'PASS' if gone else 'FAIL'} blocked {num} absent")
    ev = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:_sync_id:deleted")
    for title in prof.get("seed_calendar_titles", []):
        # A seed counts as present only if a LIVE (deleted=0) row exists. Testing
        # `title in ev and "deleted=1" not in _line_for(...)` false-PASSed when every
        # copy was soft-deleted: _line_for returns "" and `"deleted=1" not in ""` is
        # True. Derive both presence and sync-state from the live row instead.
        live = _line_for(ev, title)
        present = bool(live)
        ok &= present
        synced = bool(re.search(r"_sync_id=[^,]", live))
        print(f"  {'PASS' if present else 'FAIL'} calendar seed '{title}' present (synced={synced})")
    if prof.get("seed_calls"):
        # easy__phone__005 needs at least one call dated TODAY, else the answer is a
        # degenerate 0 seconds (and the day-2 total is whatever easy__phone__002 left).
        calls = _calls_today(serial)
        outgoing = [c for c in calls if c[2] == "2"]
        good = bool(outgoing)
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'} call log: {len(outgoing)} outgoing call(s) today, "
              f"total {sum(c[1] for c in outgoing)}s (easy__phone__005)")
    for path in prof.get("seed_files", []):
        has = sh(serial, f"ls {quote(path)}").strip() != ""
        ok &= has
        print(f"  {'PASS' if has else 'FAIL'} seed file {path}")
    for path, needle in prof.get("seed_file_contents", {}).items():
        content = sh(serial, f"cat {quote(path)}")
        good = needle in content
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'} seed file content {path} contains {needle!r}")
    contact_display = prof.get("contact_display")
    if contact_display:
        ca = sh(serial, f"content query --uri {CONTACTS_URI} --projection _id:display_name")
        name_ok = contact_display.lower() in ca.lower()
        ok &= name_ok
        print(f"  {'PASS' if name_ok else 'FAIL'} contact '{contact_display}' present")
    return ok


def _line_for(haystack: str, title: str) -> str:
    """Return the LIVE (deleted=0) query line for an event whose title matches EXACTLY.

    Two false-PASS traps this avoids:
      * substring matching — a seed titled "Gym" also matched the live
        "Old_Gym_Class" event, so the gate passed with the real seed soft-deleted;
      * returning "" for "no live row" — callers then saw `"deleted=1" not in ""`
        as True and reported the seed present.
    """
    for line in haystack.splitlines():
        match = re.search(r"title=([^,]*),", line)
        if match and match.group(1).strip() == title and "deleted=1" not in line:
            return line
    return ""


def _pull_ui_dump(serial: str, remote: str = "/sdcard/_gate_ui.xml") -> str:
    """uiautomator dump -> local temp file -> text. '' on any failure.

    Removes the on-device dump afterwards: the gate runs several times per reset and
    a stray `_gate_ui.xml` would sit in the shared storage the benchmark's Files
    tasks browse.
    """
    import tempfile

    sh(serial, f"uiautomator dump {remote}")
    fd, tmp = tempfile.mkstemp(prefix="androidlife_gate_", suffix=".xml")
    os.close(fd)
    try:
        subprocess.run(["adb", "-s", serial, "pull", remote, tmp],
                       capture_output=True, text=True, timeout=30)
        with open(tmp, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return ""
    finally:
        # Remove BOTH sides, always: the device copy would otherwise persist across
        # resets (it is plain shared storage, not app-private).
        sh(serial, f"rm -f {remote}")
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _agenda_seed_window(serial: str, prof: dict) -> tuple[bool, str]:
    """Deterministic half of the Meet gate: is an agenda seed inside Meet's window?

    Returns `(ok, detail)`. A stale anchor (reset days before the run) pushes the
    10:00 meetings into the past, so Meet's ~48h "Scheduled" list shows nothing and
    hard__google-meet-files__070 fails *silently* — the model just reports nothing.
    This catches that without touching the UI.
    """
    import datetime
    from zoneinfo import ZoneInfo

    agenda = [e for e in prof.get("seed_calendar_events", []) if e.get("meet")]
    if not agenda:
        return True, "no meet-marked seeds"
    window = float(prof.get("meet_window_hours", 48.0))

    tz = ZoneInfo(sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata")
    now = datetime.datetime.now(tz)
    live = _live_calendar_events(serial, [e["title"] for e in agenda])
    soonest: float | None = None
    for ev in agenda:
        hits = [ds for _eid, t, ds in live if t == ev["title"] and ds is not None]
        for ds in hits:
            delta_h = (datetime.datetime.fromtimestamp(ds / 1000, tz=tz) - now).total_seconds() / 3600
            if delta_h > 0 and (soonest is None or delta_h < soonest):
                soonest = delta_h
    if soonest is None:
        return False, "no upcoming meet-marked seed at all"
    if soonest > window:
        return False, (f"soonest agenda seed is +{soonest:.1f}h away — outside Meet's "
                       f"~{window:.0f}h Scheduled window (STALE ANCHOR: re-run "
                       f"`reset_phone.py --apply` on the run day)")
    return True, f"soonest agenda seed +{soonest:.1f}h (inside the ~{window:.0f}h window)"


def _agenda_conference_links(serial: str, prof: dict) -> list[tuple[str, bool]]:
    """`(title, has_meet_link)` for each live agenda occurrence, from its `description`.

    Scoped to the `meet`-marked seeds' time-of-day, so the Monday 07:00 / Tue 06:30
    clash seeds (same title, no conferencing) are not miscounted as agenda meetings.

    A Meet conference link is only writable through the Calendar UI — the non-rooted
    `content` CLI cannot set it (bind values reject ':' and the provider ignores
    direct `description` writes on synced rows). It IS readable though, so the gate
    can assert it is still present instead of discovering it is gone on run day.

    Rows are split on the `Row: N ` marker, NOT on newlines: an event description
    contains embedded newlines, so the meet link lands several physical lines below
    the `title=` field and a per-line scan false-negatives every linked seed.
    """
    import datetime
    from zoneinfo import ZoneInfo

    agenda = [e for e in prof.get("seed_calendar_events", []) if e.get("meet")]
    titles = {e["title"] for e in agenda}
    starts = {e["start"] for e in agenda}
    if not titles:
        return []
    tz = ZoneInfo(sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata")
    rows = sh(serial, f"content query --uri {CAL_URI} "
                      f"--projection _id:title:dtstart:description:deleted")
    out: list[tuple[str, bool]] = []
    for block in re.split(r"^Row: \d+ ", rows, flags=re.M)[1:]:
        t = re.search(r"title=([^,]*),", block)
        d = re.search(r"deleted=([01])", block)
        s = re.search(r"dtstart=(\d+)", block)
        if not (t and d and s) or d.group(1) == "1":
            continue
        title = t.group(1).strip()
        if title not in titles:
            continue
        slot = datetime.datetime.fromtimestamp(int(s.group(1)) / 1000, tz=tz).strftime("%H:%M")
        if slot not in starts:
            continue
        out.append((title, "meet.google.com/" in block))
    return out


def verify_meet_agenda(serial: str, prof: dict, timeout_s: float = 40.0) -> bool:
    """Pre-run gate: will Meet actually list the agenda meeting on run day?

    Three layers, because they catch different breakages:
      1. calendar-side window check (deterministic) — catches a stale anchor;
      2. conference-link check (deterministic) — catches a dropped Meet link;
      3. live Meet "Scheduled" probe — catches the classic account mismatch (Meet
         signed into a different Google account than the one cal_id=16 lives on, so
         the meeting never appears even though the seed is perfect).
    """
    titles = prof.get("meet_expected_titles") or []
    if not titles:
        return True

    ok, detail = _agenda_seed_window(serial, prof)
    print(f"  {'PASS' if ok else 'FAIL'} meet: agenda seed in window ({detail})")
    if not ok:
        # A stale anchor dooms the Meet task regardless of what the app shows.
        print("        -> hard__google-meet-files__070 will FAIL as seeded. Fix before running.")
        return False

    links = _agenda_conference_links(serial, prof)
    linked = [t for t, has in links if has]
    if not linked:
        print(f"  FAIL meet: no agenda seed carries a Meet conference link ({len(links)} checked)")
        print("        -> re-add it by hand: Calendar -> open the 10:00 'Weekly Sync' -> "
              "Edit -> Add video conferencing -> Google Meet -> Save")
        return False
    print(f"  PASS meet: conference link present ({len(linked)}/{len(links)} agenda seed(s))")

    installed = sh(serial, "pm list packages")
    pkg = next((p for p in prof.get("meet_packages", []) if f"package:{p}" in installed), None)
    if not pkg:
        print(f"  FAIL meet: none of {prof.get('meet_packages')} installed")
        return False

    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
    xml = ""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(4)
        xml = _pull_ui_dump(serial)
        # "Scheduled" is the list header; "New call" shows on the same home screen.
        if xml and ("Scheduled" in xml or "New call" in xml):
            break
    if not xml:
        print(f"  FAIL meet: could not read the Meet UI (no uiautomator dump after {timeout_s:.0f}s)")
        return False

    found = [t for t in titles if f'text="{t}"' in xml or f'content-desc="{t}' in xml]
    missing = [t for t in titles if t not in found]
    if missing:
        print(f"  FAIL meet: {pkg} -> 'Scheduled' does NOT list {missing} "
              f"(no conference link, stale anchor, or Meet on the wrong Google account)")
        print("        -> hard__google-meet-files__070 will FAIL as seeded. Fix before running.")
        return False

    print(f"  PASS meet: {pkg} -> 'Scheduled' lists {found}")
    return True


def _signed_in_email(xml: str) -> str | None:
    """Pull the account email out of an app's `Signed in as <Name> <email>` disc."""
    if not xml:
        return None
    # The disc is `Signed in as Rani Singh ranirajesh786@gmail.com\nAccount and settings.`
    m = re.search(r"Signed in as[^\"&]{0,90}", xml)
    if not m:
        return None
    em = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", m.group(0))
    return em.group(0) if em else None


def verify_cloud_accounts(serial: str, prof: dict, timeout_s: float = 28.0) -> bool:
    """Assert every cloud app is on its canonical Google account.

    Each app remembers its OWN selected account, and nothing resets that between
    runs, so an app can silently drift onto a different Google account. When it
    does, its seeded cloud data becomes invisible -- the app looks empty while the
    seed is perfectly fine. That is the failure mode behind the Gemini-2026-08-26
    Meet report ("account mismatch / Rani Singh") and the 2026-09-18 Slides deck
    disappearing.

    Read-only: launches each app, reads the identity disc's content-desc, and
    force-stops again. Costs ~6s per app (~40s for the 7 mapped apps).
    """
    want = prof.get("canonical_accounts") or {}
    if not want:
        return True

    installed = sh(serial, "pm list packages")
    ok = True
    for pkg, email in want.items():
        if f"package:{pkg}" not in installed:
            print(f"  SKIP cloud account {pkg.split('.')[-1]}: not installed")
            continue
        sh(serial, "input keyevent KEYCODE_WAKEUP")
        sh(serial, f"am force-stop {pkg}")
        time.sleep(1)
        sh(serial, f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
        found = None
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(5)
            found = _signed_in_email(_pull_ui_dump(serial))
            if found:
                break
        sh(serial, f"am force-stop {pkg}")
        good = found == email
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'} cloud account {pkg.split('.')[-1]}: "
              f"{found or 'not readable'} (want {email})")
    sh(serial, "input keyevent KEYCODE_HOME")
    return ok


def verify_slides_deck(serial: str, prof: dict) -> bool:
    """Assert the seeded Slides deck exists and still has the expected slide count.

    easy__google-slides__001 asks "how many slides does the [presentation name] deck
    have?", but the official grader carries **no ground truth** for it -- pass/fail
    rides on the agent's own reply. That is why the recorded history contains `1`,
    `3` and `8` and every one of them scored PASS.

    The deck is an uploaded `.pptx` (device file + Drive copy on ranirajesh786), NOT a
    native cloud deck and NOT file-seeded, so there is nothing to restore it if a run
    edits or deletes it. Asserting the count here is what keeps the task honest.
    """
    deck = prof.get("slides_deck")
    if not deck:
        return True
    path, want = deck["path"], int(deck["expected_slides"])
    if not sh(serial, f"ls {path}").strip() or "No such file" in sh(serial, f"ls {path}"):
        print(f"  FAIL slides: {path} is missing (easy__google-slides__001 has no deck)")
        return False

    import tempfile, zipfile

    fd, tmp = tempfile.mkstemp(prefix="androidlife_deck_", suffix=".pptx")
    os.close(fd)
    try:
        subprocess.run(["adb", "-s", serial, "pull", path, tmp],
                       capture_output=True, text=True, timeout=60)
        with zipfile.ZipFile(tmp) as zf:
            got = sum(1 for n in zf.namelist()
                      if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
    except Exception as exc:  # noqa: BLE001 - any failure means "cannot verify"
        print(f"  FAIL slides: could not read {path} ({exc})")
        return False
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    good = got == want
    print(f"  {'PASS' if good else 'FAIL'} slides: {path.split('/')[-1]} has {got} slide(s) (want {want})")
    return good


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset benchmark phone to pre-run baseline (dry-run by default).")
    parser.add_argument("--serial", required=True, help="ADB serial (device id or ip:port)")
    parser.add_argument("--profile", default="public_v2", choices=sorted(PROFILES), help="Profile to use (public_v2 or day_N for the 530 schedule).")
    parser.add_argument("--day", type=int, default=None, help="Shortcut for --profile day_N (e.g. --day 1 cleans Day-1 530 run artifacts).")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default is dry-run)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify baseline; make no changes")
    parser.add_argument("--no-meet-check", action="store_true",
                        help="Skip the Google Meet 'Scheduled' pre-run gate (it needs the "
                             "phone unlocked and adds ~10-40s)")
    parser.add_argument("--no-account-check", action="store_true",
                        help="Skip the canonical-cloud-account gate (~40s: launches Gmail, "
                             "Drive, Docs, Slides, Calendar, Meet and Photos to read each "
                             "app's selected Google account)")
    parser.add_argument("--no-slides-check", action="store_true",
                        help="Skip the Slides deck gate (pulls Q3_Review.pptx and asserts "
                             "its slide count; the grader has no ground truth for it)")
    args = parser.parse_args()

    profile_name = args.profile
    if args.day is not None:
        candidate = f"day_{args.day}"
        if candidate not in PROFILES:
            print(f"ERROR: no reset profile for --day {args.day} (known: {sorted(PROFILES)})")
            return 2
        profile_name = candidate

    if args.serial not in ("RS7XKZDI8HTOJNYL", "100.108.15.119:5555"):
        print(f"WARN: serial {args.serial} is not the known benchmark device; continuing anyway.")

    if not connect_ok(args.serial):
        print(f"FATAL: cannot reach {args.serial} (run `adb connect {args.serial}` or `adb -s RS7XKZDI8HTOJNYL tcpip 5555`)")
        return 1

    prof = PROFILES[profile_name]
    if not args.verify_only:
        print(f"== reset (profile={profile_name}, apply={args.apply}) ==")
        reset_settings(args.serial, prof.get("settings", {}), args.apply)
        unblock_numbers(args.serial, prof.get("blocked_numbers_to_remove", []), args.apply)
        remove_calendar_events(args.serial, prof.get("calendar_titles_to_remove", []), args.apply)
        remove_calendar_by_ids(args.serial, prof.get("calendar_ids_to_remove", []), args.apply)
        ensure_calendar_events(args.serial, prof.get("seed_calendar_events", []), args.apply)
        ensure_call_log(args.serial, prof.get("seed_calls", []), args.apply)
        restore_contact(args.serial, prof, args.apply)
        remove_paths(args.serial, prof.get("downloads_to_remove", []), args.apply)
        remove_paths(args.serial, prof.get("device_paths_to_remove", []), args.apply)
        remove_glob(args.serial, prof.get("device_paths_glob", []), args.apply)
        # Profile-independent: sweep operator/agent `uiautomator dump` debris off the
        # shared-storage root (see DEVICE_ROOT_DUMP_GLOBS).
        remove_glob(args.serial, DEVICE_ROOT_DUMP_GLOBS, args.apply)
        remove_paths(args.serial, prof.get("obsidian_vault_remove", []), args.apply)
        remove_by_find(args.serial, prof.get("obsidian_pasted_images", []), args.apply)
        restore_file_contents(args.serial, prof.get("restore_file_contents", {}), args.apply)
        manual = prof.get("manual_ui_cleanup") or []
        if manual:
            print("== CANNOT auto-reset (app-private; do by hand in the UI) ==")
            for item in manual:
                print(f"  - {item}")
        print("== UI-only manual cleanups (no ADB) — see .agents/skills/reset-phone/SKILL.md ==")

    ok = verify(args.serial, prof)
    if not args.no_account_check:
        ok &= verify_cloud_accounts(args.serial, prof)
    if not args.no_slides_check:
        ok &= verify_slides_deck(args.serial, prof)
    if not args.no_meet_check:
        ok &= verify_meet_agenda(args.serial, prof)
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
