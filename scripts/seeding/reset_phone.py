#!/usr/bin/env python3
"""Reset the DrainBench benchmark phone to its pre-run baseline (non-rooted).

Undoes agent-created run artifacts (settings, blocked numbers, calendar events,
contact edits, run downloads) and verifies the fabricated seed baseline is still
present. Does NOT wipe the seed data.

SAFETY: dry-run by default. Pass --apply to actually make changes. Only run on
the dedicated benchmark device (fabricated persona data), never a personal phone.

Usage:
  uv run python scripts/reset_phone.py --serial 100.108.15.119:5555 --profile public_v2            # dry-run
  uv run python scripts/reset_phone.py --serial 100.108.15.119:5555 --profile public_v2 --apply    # reset
  uv run python scripts/reset_phone.py --serial 100.108.15.119:5555 --profile public_v2 --verify-only
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys

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
        ],
        # Date-relative calendar seeds re-created at EVERY reset (next weekday
        # occurrence, cal_id=16, device-local time) so the clock-calendar clash
        # shift (07:00 -> 07:30) and the meet-files "Weekly Sync 10 AM" meeting
        # are always present for the 3x variance runs.
        "seed_calendar_events": [
            {"title": "Weekly Sync", "weekday": "monday", "start": "07:00", "end": "08:00"},
            {"title": "Weekly Sync", "weekday": "monday", "start": "10:00", "end": "11:00"},
            {"title": "Gym", "weekday": "tuesday", "start": "06:30", "end": "07:30"},
        ],
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


def remove_calendar_events(serial: str, titles: list[str], apply: bool) -> None:
    rows = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:deleted")
    ids: list[str] = []
    for line in rows.splitlines():
        m = re.search(r"_id=(\d+),", line)
        t = re.search(r"title=([^,]*),", line)
        d = re.search(r"deleted=([01])", line)
        if not (m and t and d):
            continue
        if d.group(1) == "1":
            continue  # already deleted
        title = t.group(1).strip()
        if any(title == want for want in titles):
            ids.append(m.group(1))
    if apply and ids:
        where = ",".join(ids)
        sh(serial, f"content delete --uri {CAL_URI} --where \"_id IN ({where})\"", check=True)
        print(f"  [ok]  soft-deleted {len(ids)} run-artifact events: {ids}")
    elif apply:
        print("  [--]  no run-artifact calendar events to delete")
    else:
        print(f"  [dry] soft-delete run-artifact events (matched ids): {ids or 'none'}")


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


def ensure_calendar_events(serial: str, events: list[dict], apply: bool) -> None:
    """(Re)create date-relative calendar seeds so clash/agenda meetings exist at
    every reset (variance-safe for the 3x public runs).

    Removes any existing events with the same titles (idempotent), then inserts
    each event on its next weekday occurrence at the device's local time on
    calendar _id=16 (the Google-synced primary). Used by hard__clock-calendar__023
    (Weekly Sync Mon 07:00 + Gym Tue 06:30 -> clash shift to 07:30) and
    hard__google-meet-files__070 (Weekly Sync Mon 10:00 agenda meeting).
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
    remove_calendar_events(serial, titles, apply)
    if not apply:
        print(f"  [dry] ensure date-relative calendar seeds: {titles}")
        return
    today = datetime.date.today()
    for ev in events:
        target = weekday_index[ev["weekday"]]
        days_ahead = (target - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # next week's occurrence, never today
        d = today + datetime.timedelta(days=days_ahead)

        def epoch(hhmm: str) -> int:
            h, m = map(int, hhmm.split(":"))
            return int(datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=tz).timestamp() * 1000)

        dtstart, dtend = epoch(ev["start"]), epoch(ev["end"])
        cmd = (
            f"content insert --uri {CAL_URI} --bind title:s:{quote(ev['title'])} "
            f"--bind dtstart:l:{dtstart} --bind dtend:l:{dtend} "
            f"--bind calendar_id:i:16 --bind allDay:i:0 "
            f"--bind eventTimezone:s:{quote(tz_name)} --bind hasAlarm:i:0"
        )
        sh(serial, cmd, check=True)
        print(f"  [ok]  seeded calendar event '{ev['title']}' {d} {ev['start']}-{ev['end']} ({tz_name})")


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
        present = title in ev and "deleted=1" not in _line_for(ev, title)
        ok &= present
        synced = bool(re.search(rf"title={re.escape(title)}[^,]*, _sync_id=[^,]", ev))
        print(f"  {'PASS' if present else 'FAIL'} calendar seed '{title}' present (synced={synced})")
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
    for line in haystack.splitlines():
        if title in line and "deleted=1" not in line:
            return line
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset benchmark phone to pre-run baseline (dry-run by default).")
    parser.add_argument("--serial", required=True, help="ADB serial (device id or ip:port)")
    parser.add_argument("--profile", default="public_v2", choices=sorted(PROFILES), help="Profile to use (public_v2 or day_N for the 530 schedule).")
    parser.add_argument("--day", type=int, default=None, help="Shortcut for --profile day_N (e.g. --day 1 cleans Day-1 530 run artifacts).")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default is dry-run)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify baseline; make no changes")
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
        restore_contact(args.serial, prof, args.apply)
        remove_paths(args.serial, prof.get("downloads_to_remove", []), args.apply)
        remove_paths(args.serial, prof.get("device_paths_to_remove", []), args.apply)
        remove_glob(args.serial, prof.get("device_paths_glob", []), args.apply)
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
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
