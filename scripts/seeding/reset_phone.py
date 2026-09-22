#!/usr/bin/env python3
"""Reset the AndroidLife benchmark phone to its pre-run baseline (non-rooted)."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

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

# --- seed stamp: the launch gate's ground truth --------------------------------
# `--apply` records the calendar day it ran. EVERY calendar anchor is a delta from that
# day, so a reset performed on D-1 leaves each `offset_days` seed sitting on what is by
# then the run day: `easy__calendar__002` asks about a "tomorrow" that holds no conflict,
# and its PASS is vacuous. Confirmed in 5 of 13 recorded runs (see redo.md #6).
#
# The gate already knew how to detect this (`verify_calendar_anchors` asserts the pair is
# on D+1), but nothing ran the gate at launch, so a missed manual step silently ruined the
# run. This stamp turns "did the reset happen on the run day?" into a check the launch
# path can ENFORCE, instead of something an operator has to remember.
REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_STATE_PATH = REPO_ROOT / ".seed_state.json"

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
        # Recurring (rrule != NULL) run-artifact SERIES to delete on every reset, matched
        # by title on ANY date. A date-exact sweep cannot catch these: the parent row's
        # dtstart is in the past, yet the recurrence lands on EVERY day of the run window
        # -- including "tomorrow". `Weekly_Standup` (FREQ=DAILY;COUNT=14, from the
        # 2026-09-17 run's agent) did exactly that and silently changed the conflict set
        # `easy__calendar__002` sees, on both the run day and the day after.
        "calendar_recurring_artifacts_to_remove": ["Weekly_Standup"],
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
        # that lives as a device file (and in Drive on ranirajesh786@gmail.com).
        #
        # `sources` is the host-side canonical copy, in preference order. It IS
        # version-controlled (see .gitignore's one-line assets/ exception), because an
        # uncommitted deck is exactly what rotted: two presentations both named
        # "Q3 Review" existed, the device kept the 1-slide one, and six runs in
        # Aug/Sep 2026 self-reported a PASS against the wrong file. restore_slides_deck()
        # now re-pushes it whenever the device copy is missing or the wrong length, so
        # the deck cannot drift again; verify_slides_deck() still asserts the result.
        #
        # NOTE the name is `Q3_Review.pptx` (underscore), not the `Q3 Review` var value.
        "slides_deck": {
            "path": "/sdcard/Download/Q3_Review.pptx",
            "expected_slides": 8,
            "sources": [
                "assets/seeds/public/Q3_Review.pptx",  # tracked canonical fixture
            ],
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
                "## FY26 family budget - finalisation\n\n"
                "Deadline: 2026-08-10\n"
                "Last reviewed: 2026-07-10.\n\n"
                "### Income per month\n"
                "- Salary: Rs 78000\n"
                "- Flat 2B rent: Rs 14000\n"
                "- Total income: Rs 92000\n\n"
                "### Spends per month\n"
                "- Rent: Rs 24000\n"
                "- Groceries: Rs 11500\n"
                "- Utilities: Rs 9400\n"
                "- Transport: Rs 6900\n"
                "- School fees: Rs 19000\n"
                "- Medical: Rs 3200\n"
                "- Misc: Rs 8600\n"
                "- Total spends: Rs 82600\n\n"
                "Left over: Rs 9400\n"
                "- Move Rs 5000 to savings, keep Rs 4400 as buffer.\n\n"
                "## To do before finalising\n"
                "- Add June and July spends to the tracker.\n"
                "- Categorise the 7 uncategorised rows in misc.\n"
                "- Cross-check rent and utilities against last month.\n"
                "- Export a PDF copy once locked.\n"
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
            "Notes (com.oneplus.note): delete run-CREATED notes ONLY, by title (Card Payment Due, Budget Tracker, Birthday Reminders, IndiGo flight note). NEVER sweep by date: PROTECT the 'Budget Deadline' SEED - hard__drive-notes-telegram__010 reads it and its prompt says 'otherwise just log today's check date in the note', so a run can make the note LOOK run-dated and a date-based sweep deletes the seed. That is the likely cause of it vanishing between 2026-08-30 and 2026-09-16 (re-seeded via UI 2026-09-18). The app is app-private with no file seed, so reset_phone.py cannot recreate it - losing it makes the task unsolvable.",
            "Obsidian: delete run notes (e.g. Birthday Reminders)",
            "Photos/Gallery: delete run albums (Invoices, Trip 2026); unstar the 2 starred photos",
            "YT Music: delete the 'Chill Vibes' playlist",
            "Telegram: unmute the 'Forever 21' group; keep the meetup thread UNRESOLVED (edited 2026-08-21: last message is \"22nd could work for me too, let me confirm once she's free\" — no settled date/time/venue in the chat, so hard__telegram-calendar__016 forces ask_user; do NOT re-add a settling message)",
            "Telegram: CLEAR run messages/drafts in the 'Yuvraj Airtel' chat - every hard__drive-notes-telegram__010 run messages the budget owner there. A draft left behind is INHERITED by the next run (2026-09-21: row 4 composed a chase message, its Send never registered, and rows 5/6/9/11 then opened the chat to find it already typed - row 9 said 'The message is already composed', row 11 said 'I can see the message has been sent!'). A run that SENDS leaves a bubble the next run reads as done, so delete both drafts and sent bubbles. uiautomator CANNOT read the chat list - open the chat and confirm the compose box is empty and no run-window (today-dated) bubble remains. Measured 2026-09-21: one draft survived ~90 minutes and 7 rows.",
            "Digital Wellbeing: remove the 30-min app timers the agent set",
            "Camera: delete the run-recorded 'Camera Video' clip if present",
            "YouTube: RESTORE the notifying channel's notification bell to 'All'. hard__youtube-settings__052 has the agent turn it OFF ('None'), and it is app-private (no provider, no ADB), so nothing resets it. The public prompt does NOT name the channel - the agent must find whichever channel is notifying (normally 'Tech Burner', see config/user_config.example -> notifying channel), so check the Subscription list for any channel left on 'None'. If left off, the NEXT run's agent finds notifications already disabled and the task becomes a free pass.",
            "Settings: confirm Do Not Disturb shows 'No schedules' (hard__youtube-settings__052 also creates a 22:00-08:00 schedule rule). TRUST THE UI, NOT dumpsys: a stale ZenRule named 'Rule 1' (22:00-07:00) has survived deletion in `dumpsys notification` while Settings reads 'No schedules' - verified 2026-09-19, the zombie dated from the 17 Sep run. An ADB-only check can therefore report a DND rule that no agent can actually see.",
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
            "Notes app: the two Maps run-notes 'parked here' (easy__google-maps__004) and 'Fastest Route to Bhubaneswar Airport' (medium__google-maps__002) are now AUTOMATED - `clear_maps_run_notes` deletes every note whose title matches 'Bhubaneswar Airport' or 'parked here' on each reset and between rows (via --leak-cleanup-only), and never touches the protected 'Budget Deadline' seed. Still MANUAL: remove the home-screen Notes widget those runs add. NOTE: the app reopens the last-edited note on launch, so a leftover note makes the next agent start INSIDE a note - confirmed 2026-09-16 it burned all 60 steps for qwen-26 + kimi-30v and let gemini-26 pass on the pre-existing note. 2026-09-23: a 13-row batch left 7 such notes, which pushed the 'Budget Deadline' seed below the fold and aborted rows 8-13 on the seed gate.",
            "Google Maps: the search box's *Recent* list (medium__google-maps__002) is now AUTOMATED - `clear_maps_recents` long-presses each recent row -> 'Delete suggested search?' -> Delete on each reset and between rows. NEVER a plain tap: that opens the place page AND re-adds the row to history (happened 16 Sep with 'Treebo Aasma Downtown'). Leftover rows let agents skip typing the destination entirely (7 of 13 runs on 2026-09-16, incl. 3 that PASSED on the leftover). It force-stops Maps afterwards so the app reopens on the home/search state, not a leftover route/place page.",
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


def remove_recurring_calendar_artifacts(serial: str, titles: list[str], apply: bool) -> int:
    """Delete recurring (rrule != NULL) run-artifact SERIES by title, on ANY date.

    A date-exact sweep structurally cannot catch these. The series' parent row carries a
    `dtstart` in the PAST (the day a previous run created it), so it never matches a
    today/tomorrow lookup -- but its recurrence still lands on every day of the current
    window, including "tomorrow". `Weekly_Standup` (`FREQ=DAILY;COUNT=14;WKST=MO` from
    Thu 2026-09-17, created by that day's agent and uploaded so it can never be
    re-derived from a seed file) did exactly this on the 2026-09-20 run: it appeared on
    BOTH the run day and the day after, silently changing the conflict set
    `easy__calendar__002` sees.

    Deleting the parent row removes the whole series (the provider cascades).
    """
    if not titles:
        return 0
    rows = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:rrule:deleted")
    found: list[tuple[str, str]] = []  # (title, _id)
    for line in rows.splitlines():
        m = re.search(r"_id=(\d+),", line)
        t = re.search(r"title=([^,]*),", line)
        r = re.search(r"rrule=([^,]*)", line)
        if not (m and t and r):
            continue
        if _is_deleted(line):
            continue  # already tombstoned -- not live
        if not r.group(1).strip() or r.group(1).strip().lower() == "null":
            continue  # not recurring
        if t.group(1).strip() in titles:
            found.append((t.group(1).strip(), m.group(1)))
    if not found:
        print(f"  [--]  no recurring run-artifact series present (checked {titles})")
        return 0
    if apply:
        for title, eid in found:
            sh(serial, f"content delete --uri {CAL_URI} --where \"_id={eid}\"", check=True)
            print(f"  [ok]  deleted recurring run-artifact series '{title}' (_id={eid}, any date)")
    else:
        for title, eid in found:
            print(f"  [dry] would delete recurring run-artifact series '{title}' (_id={eid})")
    return len(found)


def verify_no_recurring_artifacts(serial: str, prof: dict) -> bool:
    """FAIL while any recurring run-artifact series is still live in the window."""
    titles = prof.get("calendar_recurring_artifacts_to_remove") or []
    if not titles:
        return True
    rows = sh(serial, f"content query --uri {CAL_URI} --projection _id:title:rrule:deleted")
    live = []
    for line in rows.splitlines():
        m = re.search(r"_id=(\d+),", line)
        t = re.search(r"title=([^,]*),", line)
        r = re.search(r"rrule=([^,]*)", line)
        if not (m and t and r):
            continue
        if _is_deleted(line):
            continue  # tombstone is the SUCCESS state: deleting the series must leave a
                      # `deleted=1` row so the deletion can propagate to the server.
        if not r.group(1).strip() or r.group(1).strip().lower() == "null":
            continue
        if t.group(1).strip() in titles:
            live.append(f"{t.group(1).strip()} (_id={m.group(1)})")
    if live:
        print(f"  FAIL no recurring run artifacts: still live {live} — these land on "
              f"'tomorrow' too and change the conflict set; re-run --apply")
        return False
    print(f"  PASS no recurring run artifacts live in the window ({titles})")
    return True


def write_seed_state(serial: str, profile_name: str) -> None:
    """Stamp the day a full, VERIFIED `--apply` completed. Never called on failure."""
    import datetime
    state = {
        "seeded_on": datetime.date.today().isoformat(),
        "seeded_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "serial": serial,
        "profile": profile_name,
    }
    try:
        SEED_STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print(f"  [ok]  seed stamp: {SEED_STATE_PATH.name} seeded_on={state['seeded_on']} "
              f"profile={profile_name}")
    except OSError as exc:
        print(f"  [warn] could not write {SEED_STATE_PATH}: {exc}")


def verify_seed_freshness(profile_name: str) -> bool:
    """FAIL unless a verified `--apply` ran TODAY (the day-relative anchor trap).

    This is the check that would have caught the 2026-09-20 run: `--apply` was last run
    on 19 Sep, so every `offset_days` seed sat on the run day and `easy__calendar__002`
    passed vacuously. It is deliberately strict -- a stale stamp means the calendar seeds
    are on the wrong day, and there is no way to serve a valid calendar result from that
    state.
    """
    import datetime
    today = datetime.date.today().isoformat()
    if not SEED_STATE_PATH.exists():
        print(f"  FAIL seed stamp: {SEED_STATE_PATH.name} missing — no verified `--apply` "
              f"has stamped this tree")
        print(f"        Fix: reset_phone.py --profile {profile_name} --apply  (on the RUN day)")
        return False
    try:
        state = json.loads(SEED_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  FAIL seed stamp: unreadable ({exc})")
        return False
    seeded_on = state.get("seeded_on")
    if seeded_on != today:
        print(f"  FAIL seed stamp: last verified --apply was {seeded_on}, today is {today}")
        print("        Every calendar anchor is relative to the day --apply ran, so the "
              "conflict pair sits on the WRONG day and easy__calendar__002 is vacuous.")
        print(f"        Fix: reset_phone.py --profile {profile_name} --apply  (TODAY)")
        return False
    if state.get("profile") != profile_name:
        print(f"  FAIL seed stamp: stamped for profile {state.get('profile')!r}, "
              f"verifying {profile_name!r}")
        return False
    print(f"  PASS seed stamp: verified --apply ran today ({today}, "
          f"profile={profile_name}, serial={state.get('serial')})")
    return True


def verify_device_clock(serial: str) -> bool:
    """FAIL if the DEVICE date != host date.

    Anchors are computed from `date.today()` on the HOST, but the UI the agent reads is
    rendered from the DEVICE clock. If they disagree (stale RTC after a battery death),
    every calendar anchor is silently off by a day even though the writes landed.
    """
    import datetime
    out = sh(serial, "date +%Y-%m-%d").strip().splitlines()
    dev = out[0].strip() if out else ""
    host = datetime.date.today().isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", dev):
        print(f"  WARN device clock: could not parse device date ({dev!r}); skipping")
        return True
    if dev != host:
        print(f"  FAIL device clock: device={dev} host={host} — anchors are computed on "
              f"the host but rendered on the device; fix the clock before running")
        return False
    print(f"  PASS device clock matches host ({host})")
    return True


def _force_calendar_sync(serial: str, account: str = "") -> bool:
    """Best-effort nudge for the Google calendar sync adapter. True if one landed.

    There is no public force-sync API for a third-party account (`ContentResolver
    .requestSync` is signature-protected), so this tries the provider `call()`
    hooks that some builds expose and reports honestly instead of pretending.

    This is a PROBE, not a fix. It reports honestly instead of pretending, because
    on this build both nudges return success without starting a sync.

    What was actually proven on device (2026-09-20) is narrower than an earlier
    revision of this file claimed: the CalendarProvider marks any local write
    `dirty=1` by itself, so local edits are already queued for upload, and binding
    `dirty` from adb is REJECTED ("Only sync adapters may write to dirty"). The
    cause of the 2026-09-20 one-day revert was therefore NOT a missing dirty flag.
    A direct probe (insert Sep-25, update Sep-26) held its update across a sync
    nudge and a 150 s settle, but with `dirty` still 1 -- i.e. the upload had not
    completed, so that run did not exercise the revert either way.
    """
    for cmd in (
        f"content call --uri {CAL_URI} --method forceSync",
        "cmd sync --help",
    ):
        out = sh(serial, cmd)
        low = out.lower()
        if out.strip() and "error" not in low and "exception" not in low and "unknown" not in low:
            print(f"  [ok]  calendar sync nudged ({cmd.split()[0]} {cmd.split()[1]})")
            return True
    if account:
        # Fallback: an explicit sync-adapter broadcast. Usually ignored on Android
        # 15, but harmless to try before giving up.
        out = sh(serial, f"am broadcast -a android.content.SyncAdapter "
                         f"--es account_name {account} --es account_type com.google")
        if "Broadcast completed" in out:
            print("  [ok]  calendar sync nudged (broadcast)")
            return True
    print("  [warn] could not force a calendar sync on this build -- the settle "
          "re-check below is therefore a lower bound, not a guarantee")
    return False


def assert_anchor_durability(serial: str, prof: dict, settle_s: float,
                             account: str = "") -> bool:
    """Re-run the anchor gate after a settle window so a silent revert is visible.

    Why this exists: on 2026-09-20 the anchors verified correct at 03:46 and had
    already reverted by the time `easy__calendar__002` ran at 09:31, which is what
    made that task vacuous. A gate that only samples the instant after the write
    cannot see a revert, however well it checks the date.

    Caveat, and it matters: Google schedules account sync opportunistically, so a
    short window may not pull a revert into the open. Measured 2026-09-20: neither
    `content call --method forceSync` nor the SyncAdapter broadcast actually starts
    a sync on this build, so the window is whatever Android chooses. A PASS here is
    reassurance, not proof.
    """
    import time
    if settle_s <= 0:
        return True
    print(f"== calendar durability re-check (sync nudge + {settle_s:.0f}s settle) ==")
    _force_calendar_sync(serial, account)
    time.sleep(settle_s)
    ok = verify_calendar_anchors(serial, prof)
    if ok:
        print("  [ok]  anchors still correct after the settle window")
    else:
        print("  [FAIL] anchors MOVED after the settle window -- the synced "
              "calendar reverted the write. Do NOT benchmark: the calendar tasks "
              "will run against the wrong dates.")
    return ok


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


WEEKDAY_INDEX = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                 "friday": 4, "saturday": 5, "sunday": 6}


def _anchor_date(ev: dict, today) -> "object":
    """Resolve a `seed_calendar_events` entry's anchor to a concrete date.

    An entry is anchored either by `offset_days` (today + N) or by `weekday` (the
    NEXT occurrence -- never today, so a `"monday"` seed is always in the future).

    This helper is shared by BOTH the writer (`ensure_calendar_events`) and the gate
    (`verify_calendar_anchors`). That sharing is the point: the gate can only assert
    the right date if it derives the date the same way the writer does, and a
    duplicated copy of this arithmetic is exactly how a half-applied reset (which
    shifted the Weekly Sync seeds but not Team Sync / Mentor 1 on 1) slipped past the
    old presence-only gate on 2026-09-20.
    """
    import datetime
    if "offset_days" in ev:
        return today + datetime.timedelta(days=int(ev["offset_days"]))
    days_ahead = (WEEKDAY_INDEX[ev["weekday"]] - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7  # next week's occurrence, never today
    return today + datetime.timedelta(days=days_ahead)


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
    # (title, dtstart_ms) of seeds written via INSERT this run. Tracked so the
    # stale-copy sweep can be gated on the inserts having actually landed.
    _inserted: list[tuple[str, int]] = []
    # (title, _id, dtstart_ms) of rows moved in place via UPDATE. Tracked for the
    # same reason: `content update` reports success even when the provider rejects
    # it, so an unconfirmed move would be indistinguishable from a good one.
    _moved: list[tuple[str, str, int]] = []
    for ev in events:
        d = _anchor_date(ev, today)

        def epoch(hhmm_str: str) -> int:
            h, m = map(int, hhmm_str.split(":"))
            return int(datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=tz).timestamp() * 1000)

        dtstart, dtend = epoch(ev["start"]), epoch(ev["end"])
        # Match on title + time-of-day. An exact-date hit means "this seed is already
        # where it belongs" and issues no write at all (see the durability note
        # below). A same-time miss must be resolved by INSERT for unlinked seeds and
        # by an in-place UPDATE only for Meet seeds -- the link is what makes the
        # meeting visible in Meet, and a delete+insert silently DESTROYS it, because
        # the non-rooted `content` CLI cannot write the conferencing column (bind
        # values reject ':' and a Meet URL always contains '://').
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
        #
        # 2026-09-20 DURABILITY -- read before changing the branch structure.
        #
        # The 2026-09-20 run's `easy__calendar__002` was vacuous because every
        # `offset_days` seed sat one day early at run time (Team Sync / Mentor 1 on
        # 1 on the run day; both Weekly Sync 10:00 copies on D+1/D+2) -- i.e. the
        # dates a reset run the PREVIOUS day would compute. The `weekday` anchors
        # looked correct only because Sep-19's and Sep-20's "next Monday/Tuesday"
        # coincide.
        #
        # An earlier revision of this code blamed that on a missing `dirty` flag and
        # bound `dirty:i:1` on both writes. THAT WAS WRONG, and it was worse than
        # useless -- the CalendarProvider rejects it outright:
        #
        #     IllegalArgumentException: Only sync adapters may write to dirty
        #
        # and the failure is SILENT, because `content update/insert` still exits 0
        # through `adb shell`. Measured on device 2026-09-20: with the bind, the row
        # did not move at all; without it, the write lands AND the provider marks the
        # row `dirty=1` by itself. So local edits are already flagged for upload --
        # nothing here should ever bind `dirty`.
        #
        # What the code DOES hold to, and why:
        #   1. if a copy already sits on the exact target date+time, issue NO write;
        #   2. if the seed needs a Meet link, it MUST be moved in place (a
        #      delete+insert would drop the conferencing block, which the non-rooted
        #      `content` CLI cannot rewrite) -- so update that row;
        #   3. otherwise INSERT a fresh copy on the target date and let the leftover
        #      sweep below remove the stale same-time row.
        # Every write is then CONFIRMED by re-reading the row, because a rejected
        # write costs nothing to miss otherwise (see the silent-exit-0 note above).
        already = (_pick(exact_date=True, prefer_link=True) if (ev.get("meet") and linked)
                   else _pick(exact_date=True, prefer_link=False))
        if already:
            used.add(already)
            print(f"  [ok]  calendar event '{ev['title']}' already on {d} "
                  f"{ev['start']}-{ev['end']} (_id={already}, no write needed)")
            continue

        match = None
        if ev.get("meet") and linked:
            match = (_pick(exact_date=False, prefer_link=True)
                     or _pick(exact_date=False, prefer_link=False))
        if match:
            # No `dirty` bind: the provider sets it, and binding it is rejected
            # outright (see the note above -- it broke every calendar write).
            sh(serial, f"content update --uri {CAL_URI} "
                       f"--bind dtstart:l:{dtstart} --bind dtend:l:{dtend} "
                       f"--where \"_id={match}\"", check=True)
            used.add(match)
            _moved.append((ev["title"], match, dtstart))
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
            # The stale same-time copy (if any) is deliberately NOT added to `used`:
            # it becomes a leftover and is swept below. But only after the insert is
            # CONFIRMED -- otherwise a failed insert plus the sweep would leave the
            # device with no seed at all.
            _inserted.append((ev["title"], dtstart))
            print(f"  [ok]  seeded calendar event '{ev['title']}' {d} "
                  f"{ev['start']}-{ev['end']} ({tz_name})")

    # Confirm every freshly INSERTed anchor actually landed before we delete anything.
    # A rejected write is silent (adb exits 0 through a provider exception), so the
    # only trustworthy signal is re-reading the row.
    if _inserted:
        live_after = _live_calendar_events(serial, sorted({t for t, _ in _inserted}))
        missing = []
        for title, want_ms in _inserted:
            if not any(t == title and s is not None and abs(s - want_ms) <= 60_000
                       for _i, t, s in live_after):
                missing.append(title)
        if missing:
            print(f"  [FAIL] calendar insert did not land for: {sorted(set(missing))}")
            print("  [FAIL] skipping the stale-copy sweep so no seed is lost; "
                  "re-run --apply before benchmarking.")
            return
        print(f"  [ok]  confirmed {len(_inserted)} freshly inserted calendar anchor(s)")

    # Same confirmation for rows moved in place. These are the Meet-linked seeds, so
    # a silent rejection here loses the link's slot and takes
    # hard__google-meet-files__070 down with it.
    if _moved:
        moved_missing = []
        for title, eid, want_ms in _moved:
            row = sh(serial, f"content query --uri {CAL_URI} "
                             f"--projection _id:dtstart --where \"_id={eid}\"")
            m = re.search(r"dtstart=(\d+)", row)
            if not m or abs(int(m.group(1)) - want_ms) > 60_000:
                moved_missing.append(f"{title} (_id={eid})")
        if moved_missing:
            print(f"  [FAIL] calendar in-place move did not land for: {moved_missing}")
            print("  [FAIL] re-run --apply before benchmarking.")
            return
        print(f"  [ok]  confirmed {len(_moved)} in-place calendar move(s)")

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


def verify_calendar_anchors(serial: str, prof: dict) -> bool:
    """Assert every date-relative seed sits on its EXPECTED date AND start time.

    `verify()` below only checks that a seed title EXISTS on the calendar; it never
    checked *where* it was anchored. That gap let a half-applied reset pass the gate
    with `Team Sync` on the run day instead of tomorrow -- and since
    `easy__calendar__002` asks for "tomorrow afternoon" conflicts, the task would
    fail while the gate said PASS. Observed 2026-09-20: a `nohup`-backgrounded
    `--apply` was torn down after it had shifted the Weekly Sync seeds but before it
    reached Team Sync / Mentor 1 on 1 (and before the call log, which has its own
    check). The same gap silently makes `hard__clock-calendar__023` (Weekly Sync
    Mon 07:00) and `hard__google-meet-files__070` (10:00 agenda in Meet's 48h window)
    unsolvable when an anchor goes stale.

    Cheap and device-local -- one `content query` for all titles, no UI launches --
    so it always runs and has no `--no-*` skip flag, unlike the UI-probe gates.

    Matching is per (title, expected date, expected start) with each live copy
    consumed once, because duplicate titles are legitimate here (Weekly Sync exists
    at Mon 07:00, D+1 10:00 and D+2 10:00).
    """
    events = prof.get("seed_calendar_events") or []
    if not events:
        return True
    import datetime
    from zoneinfo import ZoneInfo

    tz_name = sh(serial, "getprop persist.sys.timezone").strip() or "Asia/Kolkata"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    today = datetime.date.today()
    titles = sorted({e["title"] for e in events})
    live = _live_calendar_events(serial, titles)
    linked = _calendar_ids_with_meet_link(serial) if any(e.get("meet") for e in events) else set()

    print("== calendar anchor verify (each seed must be on the RIGHT date) ==")
    ok = True
    used: set[str] = set()
    for ev in events:
        want = _anchor_date(ev, today)
        h, m = map(int, ev["start"].split(":"))
        want_ms = int(datetime.datetime(want.year, want.month, want.day, h, m,
                                        tzinfo=tz).timestamp() * 1000)
        hit = None
        for eid, etitle, eds in live:
            if eid in used or etitle != ev["title"] or eds is None:
                continue
            if abs(eds - want_ms) <= 60_000:  # <=1 min slack for provider rounding
                hit = eid
                break
        if hit:
            used.add(hit)
        ok &= hit is not None
        note = ""
        if hit and ev.get("meet") and linked:
            # Informational only -- verify_meet_agenda() owns the conferencing-link
            # verdict, and failing here too would just double-report the same fault.
            note = (" (link present)" if hit in linked
                    else " (no link on THIS copy -- see meet gate)")
        print(f"  {'PASS' if hit else 'FAIL'} anchor '{ev['title']}' "
              f"{want} {ev['start']} (today{(want - today).days:+d}d){note}")
    for eid, etitle, eds in live:
        if eid in used or eds is None:
            continue
        # Unconsumed live copy of a seeded title = a stale duplicate the writer
        # should have deleted. Not fatal, but it is how a wrong-date copy lingers.
        got = datetime.datetime.fromtimestamp(eds / 1000, tz=tz)
        print(f"  WARN  stale '{etitle}' at {got} (today{(got.date() - today).days:+d}d) "
              f"was not claimed by any seed")
    return ok


CAL_PKG = "com.google.android.calendar"

# Google Calendar's day-row content-desc advertises the mode you would switch INTO, so
# it names the CURRENT mode:
#   "<weekday> <D> <Month> <Y>, Open Day View"      -> currently in SCHEDULE view
#   "<weekday> <D> <Month> <Y>, Open Schedule View" -> currently in DAY view
_OPEN_DAY = "Open Day View"
_OPEN_SCHEDULE = "Open Schedule View"


def _calendar_view_mode(serial: str, timeout_s: float = 40.0) -> str:
    """'schedule' | 'day' | 'unknown' -- the mode the Calendar APP is showing now.

    Always leaves the app stopped and the device on the launcher. That matters here
    for the same reason it does in verify_meet_agenda(): the gate runs right before
    the first task, so whatever it leaves on screen BECOMES the agent's start state.
    """
    import time

    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"am force-stop {CAL_PKG}")
    sh(serial, f"monkey -p {CAL_PKG} -c android.intent.category.LAUNCHER 1")
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(4)
            xml = _pull_ui_dump(serial)
            # _OPEN_DAY first: the marker for "we are in Schedule" must win if both
            # strings ever appear in one dump.
            if _OPEN_DAY in xml:
                return "schedule"
            if _OPEN_SCHEDULE in xml:
                return "day"
        return "unknown"
    finally:
        sh(serial, f"am force-stop {CAL_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")


def _switch_calendar_to_schedule(serial: str, timeout_s: float = 25.0) -> bool:
    """Tap the 'Open Schedule View' affordance, then confirm the mode flipped."""
    import time

    sh(serial, f"monkey -p {CAL_PKG} -c android.intent.category.LAUNCHER 1")
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(4)
            xml = _pull_ui_dump(serial)
            if _OPEN_DAY in xml:
                return True
            for pat in (
                r'content-desc="[^"]*Open Schedule View[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*content-desc="[^"]*Open Schedule View',
            ):
                m = re.search(pat, xml)
                if m:
                    x1, y1, x2, y2 = (int(g) for g in m.groups())
                    sh(serial, f"input tap {(x1 + x2) // 2} {(y1 + y2) // 2}")
                    time.sleep(5)
                    return _calendar_view_mode(serial, timeout_s=20.0) == "schedule"
        return False
    finally:
        sh(serial, f"am force-stop {CAL_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")


def verify_calendar_view_mode(serial: str, prof: dict) -> bool:
    """The Calendar APP must be in Schedule view -- the mode the original runs began in.

    Measured 2026-09-21 (redo.md 7.2): a run's agent leaves the app wherever it
    finished, so a completed run can hand the next one a **Day**-view calendar. None of
    the provider checks above can see that -- they query the content provider, not the
    app -- and it silently changes the agent's starting screen. It bit rows 1 and 2 of
    the easy__calendar_002 re-runs, which had to be run a second time.

    Repaired in place rather than merely reported: this is UI mode, not seed data, and
    the failure mode being defended against is precisely "a manual fix gets skipped".
    Always exits to the launcher.
    """
    if not (prof.get("seed_calendar_events") or prof.get("seed_calendar_titles")):
        return True
    mode = _calendar_view_mode(serial)
    if mode == "schedule":
        print("  PASS calendar app view mode: Schedule (matches the original runs)")
        return True
    if mode == "day":
        print("  WARN calendar app view mode: Day (a previous run left it there) -- restoring")
        if _switch_calendar_to_schedule(serial):
            print("  PASS calendar app view mode: restored to Schedule")
            return True
        print("  FAIL calendar app view mode: still Day -- the Calendar UI would not switch")
        return False
    print("  FAIL calendar app view mode: could not read the Calendar UI (no "
          "'Open Day View' / 'Open Schedule View' marker in the dump)")
    return False


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
    # Presence is not enough: the seed must be on the DATE the task expects. This is
    # what catches a half-applied reset (see verify_calendar_anchors docstring).
    ok &= verify_calendar_anchors(serial, prof)
    # A recurring run artifact lands on every day of the window, so it survives the
    # date-exact checks above while still changing what the agent sees.
    ok &= verify_no_recurring_artifacts(serial, prof)
    return ok


def _is_deleted(line: str) -> bool:
    """True when a `content query` result line is a tombstone (`deleted=1`).

    Deleting a calendar row does not remove it: the provider keeps a `deleted=1` row so
    the deletion can propagate to the server. Any presence check that ignores this reads
    a successful delete as a still-present event -- which is exactly how the recurring
    sweep first reported success and then failed its own verification.
    """
    m = re.search(r"deleted=(\d+)", line)
    return bool(m and m.group(1) == "1")


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
    # From here on Meet is on screen, so EVERY exit path must put the device back.
    # This matters because the gate now runs automatically right before the first task,
    # while the harness only resets the foreground app AFTER a task (cli.py) and never
    # before the first one. So whatever this leaves on screen BECOMES the first task's
    # starting state. Verified regression: a re-run of easy__calendar__002 began with
    # Meet in the foreground (`com.google.android.apps.tachyon` HomeActivity) where the
    # original run began on the launcher -- an avoidable difference in starting
    # conditions, caused by automating a step an operator used to finish by hand.
    # Mirrors verify_cloud_accounts(), which already force-stops + goes home.
    try:
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
    finally:
        sh(serial, f"am force-stop {pkg}")
        sh(serial, "input keyevent KEYCODE_HOME")


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


def _slide_count_in_pptx(path: Path) -> int:
    """Count slides in a local .pptx (one slide == one `ppt/slides/slideN.xml` part).

    Deliberately host-side and shared by the canonical fixture AND the device pull, so
    the two are scored by the same rule and a disagreement is reported rather than
    rounded away.
    """
    with zipfile.ZipFile(path) as zf:
        return sum(1 for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))


def _device_slide_count(serial: str, remote: str) -> int | None:
    """Slide count of the deck currently on the device; None when it can't be read."""
    import tempfile

    fd, tmp = tempfile.mkstemp(prefix="androidlife_deck_", suffix=".pptx")
    os.close(fd)
    try:
        pulled = subprocess.run(["adb", "-s", serial, "pull", remote, tmp],
                                capture_output=True, text=True, timeout=60)
        if pulled.returncode != 0:
            return None
        return _slide_count_in_pptx(Path(tmp))
    except Exception:  # noqa: BLE001 - any failure means "cannot read"
        return None
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _deck_source(deck: dict) -> Path | None:
    """The first existing host-side canonical deck, or None if no candidate exists."""
    for rel in deck.get("sources", []):
        p = REPO_ROOT / rel
        if p.is_file():
            return p
    return None


def restore_slides_deck(serial: str, prof: dict, apply: bool) -> bool:
    """Re-push the canonical Q3_Review.pptx when the device copy is missing or wrong.

    This is what makes the version-controlled fixture load-bearing. The deck has no
    generator -- it is a hand-built ground-truth artifact -- so before this existed it
    was repaired by hand and silently rotted back to a stray 1-slide presentation also
    named "Q3 Review", which re-scored easy__google-slides__001 against the wrong file
    for six runs (redo.md 5).

    A no-op when the device already holds the right deck, so it costs no ADB traffic on
    a healthy reset. Returns False only when a restore was needed and could not be done.
    """
    deck = prof.get("slides_deck")
    if not deck:
        return True
    want = int(deck["expected_slides"])
    remote = deck["path"]

    got = _device_slide_count(serial, remote)
    if got == want:
        print(f"  [ok]  slides deck already correct: {remote} ({got} slides, not re-pushed)")
        return True

    src = _deck_source(deck)
    if src is None:
        print(f"  [!!]  slides deck source missing (looked for {deck.get('sources')} "
              f"under {REPO_ROOT}) — cannot restore")
        return False

    src_slides = _slide_count_in_pptx(src)
    if src_slides != want:
        print(f"  [!!]  canonical {src} has {src_slides} slide(s), expected {want} — "
              "refusing to push a deck that does not match the task's ground truth")
        return False

    state = f"{got} slide(s)" if got is not None else "missing/unreadable"
    if not apply:
        print(f"  [dry] restore slides deck: {src} -> {remote} (device has {state})")
        return True

    pushed = subprocess.run(["adb", "-s", serial, "push", str(src), remote],
                            capture_output=True, text=True, timeout=120)
    if pushed.returncode != 0:
        print(f"  [!!]  slides deck push failed for {remote}: {pushed.stderr.strip()[:200]}")
        return False
    print(f"  [ok]  restored slides deck: {src.name} -> {remote} "
          f"(device had {state}; now {src_slides} slides)")
    return True


def verify_slides_deck(serial: str, prof: dict) -> bool:
    """Assert the seeded Slides deck exists and still has the expected slide count.

    easy__google-slides__001 asks "how many slides does the [presentation name] deck
    have?". The answer is ground-truthed twice, on purpose:

      * here -- the DEVICE deck is byte-for-byte the version-controlled fixture, so the
        task cannot be run against the wrong presentation at all; and
      * in the grader (`answer_checks_public.json`) -- the agent's REPLY has to contain
        the expected count, so a model cannot self-report a pass it did not earn.

    Before either existed the recorded history contained `1`, `3` and `8`, and every one
    of them scored PASS, because the official grader rode entirely on the model's own
    success flag.

    restore_slides_deck() has already tried to re-push the file, so a failure here means
    the push itself failed rather than the deck having quietly rotted.
    """
    deck = prof.get("slides_deck")
    if not deck:
        return True
    path, want = deck["path"], int(deck["expected_slides"])

    src = _deck_source(deck)
    if src is None:
        print(f"  FAIL slides: no canonical deck on the host (looked for "
              f"{deck.get('sources')} under {REPO_ROOT}) — the ground-truth fixture is "
              "missing")
        return False
    src_slides = _slide_count_in_pptx(src)
    if src_slides != want:
        print(f"  FAIL slides: canonical {src.name} has {src_slides} slide(s), want {want}")
        return False

    got = _device_slide_count(serial, path)
    if got is None:
        print(f"  FAIL slides: {path} is missing or unreadable")
        return False

    good = got == want
    print(f"  {'PASS' if good else 'FAIL'} slides: {path.split('/')[-1]} has {got} slide(s) "
          f"(want {want}; canonical {src.name} has {src_slides})")
    return good


# ---------------------------------------------------------------------------
# Run-leak cleanup: the Telegram chat and the OnePlus Notes seed
#
# Force-stopping an app (below, and in the harness) resets its *screen*, never its
# *content*. A Telegram draft composed by one run is still sitting in the composer
# when the next run opens the chat, and a run's edit to the Notes seed stays in the
# note -- both measured leaking across rows on 2026-09-21 (redo.md 7.2: one draft
# survived ~90 minutes and 7 rows; row 12 rewrote the "Last reviewed" line in place).
#
# Neither app is debuggable and neither exposes a content provider (`run-as` fails on
# both; `dumpsys package com.oneplus.note` lists widget providers only), so `pm clear`
# is the only non-UI route -- and it destroys the seed (Telegram's login, every note).
# Driving the UI is therefore the only viable mechanism, which is what these helpers
# do. Both are *verifiable* rather than best-effort, and that is what makes them safe
# to gate on:
#
#   * Notes publishes `com.oneplus.note:id/text_count`, which measurement shows is the
#     character count EXCLUDING whitespace -- a stable fingerprint of the whole note.
#     The canonical seed is 518 on that scale.
#   * Telegram's a11y tree exposes the composer (an empty one reads as the literal hint
#     `Message`) and every bubble with its `Sent at`/`Received at` stamp under a date
#     separator, which is how run-window bubbles are told apart from seeded history.
# ---------------------------------------------------------------------------

TG_PKG = "org.telegram.messenger"
TG_CHAT_NAME = "Yuvraj Airtel"
TG_COMPOSE_HINT = "Message"

NOTE_PKG = "com.oneplus.note"
NOTE_TITLE = "Budget Deadline"
NOTE_TEXT_COUNT_ID = "com.oneplus.note:id/text_count"
# Notes that must NEVER be deleted by a leak sweep: they are seeds, not run artifacts.
NOTE_PROTECTED_TITLES = (NOTE_TITLE,)

# Tracked plain-text seed for the OnePlus Notes app. This is NOT the same artifact as
# assets/seeds/public/notes/Budget Deadline.md -- that one is a markdown note pushed
# into the Obsidian vault, which happens to share the title. This file is the exact
# plain text the app holds.
ONEPLUS_NOTE_SEED = REPO_ROOT / "assets/seeds/public/Budget Deadline (OnePlus Notes).txt"

_UI_NODE_RE = re.compile(r"<node\b[^>]*>")
_UI_ATTR_RE = re.compile(r'(\w[\w-]*)="([^"]*)"')
_UI_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def _ui_nodes(xml: str) -> list[dict]:
    """Parse a `uiautomator dump` into a flat list of {text, desc, cls, rid, bounds, cx, cy}."""
    nodes = []
    for tag in _UI_NODE_RE.findall(xml):
        attrs = dict(_UI_ATTR_RE.findall(tag))
        b = _UI_BOUNDS_RE.search(attrs.get("bounds", ""))
        if not b:
            continue
        x1, y1, x2, y2 = (int(g) for g in b.groups())
        nodes.append({
            "text": attrs.get("text", ""),
            "desc": attrs.get("content-desc", ""),
            "cls": attrs.get("class", ""),
            "rid": attrs.get("resource-id", ""),
            "bounds": (x1, y1, x2, y2),
            "checked": attrs.get("checked") == "true",
            "cy": (y1 + y2) // 2,
            "cx": (x1 + x2) // 2,
        })
    return nodes


def _ui_tap(serial: str, node: dict) -> None:
    sh(serial, f"input tap {node['cx']} {node['cy']}")


def _ui_wait(serial: str, predicate, timeout_s: float = 30.0, interval_s: float = 2.0) -> tuple[str, list[dict]]:
    """Poll the a11y dump until `predicate(nodes)` is truthy. Returns (xml, nodes) -- possibly stale on timeout."""
    deadline = time.time() + timeout_s
    xml, nodes = "", []
    while time.time() < deadline:
        xml = _pull_ui_dump(serial)
        nodes = _ui_nodes(xml)
        if predicate(nodes):
            return xml, nodes
        time.sleep(interval_s)
    return xml, nodes


def _non_ws_count(text: str) -> int:
    """Count characters the way `com.oneplus.note:id/text_count` does (whitespace excluded)."""
    return len(re.sub(r"\s", "", text))


def _note_seed_text() -> str | None:
    """The canonical OnePlus note body, or None when the tracked seed is missing."""
    if not ONEPLUS_NOTE_SEED.is_file():
        return None
    return ONEPLUS_NOTE_SEED.read_text(encoding="utf-8").rstrip("\n")


def _note_find_title(serial: str, timeout_s: float = 40.0) -> list[dict]:
    """Wait for NOTE_TITLE to appear in the note list, repairing the two ways it hides.

    The OnePlus Notes app reopens on whichever bottom tab it was last left on, and the
    **To-dos** tab does not list notes at all — so a run that ends on To-dos makes the
    note look missing. Measured 2026-09-23: a Maps run left the app on To-dos, `_note_open`
    then returned [] for every remaining row, and the seed gate aborted rows 8-13 of the
    re-run. The note was never actually damaged.

    A long list is the second way: run artifacts accumulate at the TOP of the list
    (7 new "Fastest route to Bhubaneswar Airport" notes pushed the seed down on
    2026-09-23), so the title can sit below the fold. We therefore scroll a bounded
    number of times rather than assuming the first screenful is the whole list.
    """
    _, nodes = _ui_wait(serial, lambda ns: any(n["text"] == NOTE_TITLE for n in ns),
                        timeout_s, interval_s=1.5)
    if any(n["text"] == NOTE_TITLE for n in nodes):
        return nodes

    # Repair the wrong-tab case: tap the bottom-nav "Notes" item (the nav item is the
    # bottom-most node carrying that content-desc; the screen's own header is not tappable).
    tab = next((n for n in sorted((n for n in nodes if n["desc"] == "Notes"),
                                  key=lambda n: n["cy"], reverse=True)), None)
    if tab is not None:
        _ui_tap(serial, tab)
        _, nodes = _ui_wait(serial, lambda ns: any(n["text"] == NOTE_TITLE for n in ns),
                            15.0, interval_s=1.5)
        if any(n["text"] == NOTE_TITLE for n in nodes):
            return nodes

    # Repair the below-the-fold case: scroll the list down, re-dumping after each swipe.
    for _ in range(6):
        sh(serial, "input swipe 540 1800 540 700 300")
        time.sleep(1.5)
        nodes = _ui_nodes(_pull_ui_dump(serial))
        if any(n["text"] == NOTE_TITLE for n in nodes):
            return nodes
    return nodes


def _note_open(serial: str, timeout_s: float = 40.0) -> list[dict]:
    """Force-stop Notes, launch it, open NOTE_TITLE and return the editor's a11y nodes."""
    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, f"monkey -p {NOTE_PKG} -c android.intent.category.LAUNCHER 1")
    nodes = _note_find_title(serial, timeout_s)
    target = next((n for n in nodes if n["text"] == NOTE_TITLE), None)
    if target is None:
        return []
    # Tap below the title text: the row title sits at the top of its card, and tapping
    # the card body is what opens the note (tapping the title itself can start a rename).
    sh(serial, f"input tap 540 {target['cy'] + 45}")
    _xml, nodes = _ui_wait(serial, lambda ns: any(n["rid"] == NOTE_TEXT_COUNT_ID for n in ns), timeout_s)
    return nodes


def _note_text_count(nodes: list[dict]) -> int | None:
    """The note's published `text_count`, or None when the editor is not on screen."""
    for n in nodes:
        if n["rid"] == NOTE_TEXT_COUNT_ID:
            try:
                return int(n["text"])
            except ValueError:
                return None
    return None


def restore_budget_note(serial: str, apply: bool) -> bool:
    """Rewrite the Budget Deadline note from the tracked seed when a run has drifted it.

    Verified by `text_count` before and after, so a partial retype is reported rather
    than silently leaving the task unsolvable. This is the only repair path: the note
    lives in app-private storage with no file seed, so it cannot be pushed back.
    """
    seed = _note_seed_text()
    if seed is None:
        print(f"  [!!]  note seed missing ({ONEPLUS_NOTE_SEED}) — cannot restore the Budget Deadline note")
        return False
    want = _non_ws_count(seed)

    nodes = _note_open(serial)
    got = _note_text_count(nodes)
    if got is None:
        print(f"  [!!]  note: no note titled '{NOTE_TITLE}' with a readable body — missing "
              "or renamed (the title IS the note's first line)")
        return False
    if got == want:
        print(f"  [ok]  note already matches the seed (text_count {got}, not re-typed)")
        return True

    print(f"  [!!]  Budget Deadline drift: text_count {got}, seed {want} "
          f"({'run added text' if got > want else 'run removed/edited text'})")
    if not apply:
        print("  [dry] restore Budget Deadline note from the tracked seed")
        return True

    # The retype is verified and retried rather than done once: `input text` occasionally
    # drops characters against this editor's live rich-text formatting (measured
    # 2026-09-22: a first pass landed 492/518), and a partially restored seed is worse
    # than a known-dirty one because it silently changes the overdue arithmetic. Each
    # attempt re-opens the note, so a retry starts from a clean editor.
    after = got
    for attempt in range(1, 4):
        nodes = _note_open(serial) if attempt > 1 else nodes
        editor = next((n for n in nodes if n["rid"].endswith("id/richEditor")), None)
        if editor is None:
            print("  [!!]  note: no editor node — cannot enter edit mode")
            return False
        # Enter edit mode by tapping the note BODY. Tapping the `Insert` toolbar button
        # does not do it (measured 2026-09-22: the toolbar layout is unchanged afterwards
        # and typing goes nowhere); tapping inside `richEditor` places the cursor and
        # switches the toolbar into its edit variant.
        _ui_tap(serial, editor)
        time.sleep(4)

        # Ctrl+A selects the whole body and the retype replaces it. Deliberately NOT a
        # character-wise DEL loop: deleting from the end eats the note's FIRST LINE, and
        # the app treats that line as the note TITLE -- a 2026-09-22 trial renamed the
        # seed to "- Utilities: Rs 9400", making the task unresolvable (the oracle names
        # the note "Budget Deadline") until the title was typed back.
        sh(serial, "input keycombination 113 29")
        time.sleep(3)

        lines = seed.split("\n")
        for i, line in enumerate(lines):
            # `input text` needs literal spaces as %s; the seed is deliberately ASCII
            # (no `Rs`-vs-rupee ambiguity) so no other escaping is required.
            sh(serial, "input text " + line.replace(" ", "%s"))
            if i < len(lines) - 1:
                sh(serial, "input keyevent 66")     # Enter -> new line
            time.sleep(0.35)
        time.sleep(3)
        sh(serial, "input keyevent KEYCODE_BACK")
        time.sleep(5)

        nodes = _note_open(serial)
        after = _note_text_count(nodes)
        if after == want:
            print(f"  [ok]  note restored from the tracked seed: text_count {after} "
                  f"(attempt {attempt})")
            sh(serial, f"am force-stop {NOTE_PKG}")
            sh(serial, "input keyevent KEYCODE_HOME")
            return True
        print(f"  [!!]  note re-type attempt {attempt} landed text_count {after} (want {want})")

    print(f"  [!!]  note: seed NOT restored (text_count {after}, want {want}) — restore by hand")
    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    return False


def verify_budget_note(serial: str) -> bool:
    """Gate: the one-plus Notes seed must be byte-equivalent to the tracked seed.

    `text_count` excludes whitespace, so it pins the *content* without needing to read
    the (unreadable) note body. It catches the row-12 failure mode -- an agent editing a
    line in place rather than appending -- which changes the count and silently flips
    the overdue branch the NEXT run takes.
    """
    seed = _note_seed_text()
    if seed is None:
        print(f"  FAIL note: seed missing ({ONEPLUS_NOTE_SEED})")
        return False
    want = _non_ws_count(seed)
    nodes = _note_open(serial)
    got = _note_text_count(nodes)
    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    if got is None:
        print(f"  FAIL note: no note titled '{NOTE_TITLE}' with a readable body — missing or "
              "renamed (the title IS the note's first line)")
        return False
    good = got == want
    print(f"  {'PASS' if good else 'FAIL'} note: Budget Deadline text_count {got} (want {want})")
    return good


_TG_DATE_SEP_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(,\s*\d{4})?$"
)


def _tg_open_chat(serial: str, timeout_s: float = 45.0) -> list[dict]:
    """Launch Telegram, search for TG_CHAT_NAME and open it. Returns the chat's a11y nodes.

    The chat LIST is not exposed to uiautomator (documented, and re-confirmed here), so
    search is the only route in. Returns [] if the chat could not be reached.

    Retried once: `clear_telegram_run_leaks` treats [] as a hard failure (it must never
    report a clean chat it never saw), and this sequence has several ways to come up empty
    on a slow handset -- a cold start that outlasts the search wait, a tap that lands
    before the list is laid out. One retry covers those; a genuinely unreachable chat fails
    both times and still reports the failure.
    """
    for attempt in range(2):
        nodes = _tg_open_chat_once(serial, timeout_s)
        if nodes:
            return nodes
        if not attempt:
            sh(serial, f"am force-stop {TG_PKG}")
            time.sleep(3)
    return []


def _tg_open_chat_once(serial: str, timeout_s: float) -> list[dict]:
    """One attempt at Telegram -> search -> TG_CHAT_NAME. [] if any step does not land."""
    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"am force-stop {TG_PKG}")
    sh(serial, f"monkey -p {TG_PKG} -c android.intent.category.LAUNCHER 1")
    _, nodes = _ui_wait(
        serial,
        lambda ns: any("search" in (n["desc"] or n["text"]).lower() for n in ns),
        timeout_s,
    )
    search = next((n for n in nodes if "search" in (n["desc"] or n["text"]).lower()), None)
    if search is None:
        return []
    _ui_tap(serial, search)
    time.sleep(4)
    sh(serial, "input text " + TG_CHAT_NAME.replace(" ", "%s"))
    # The result row is the one carrying the live "last seen" status; the bare-name row
    # above it is the search box echo, and the rows below are unrelated contacts.
    _, nodes = _ui_wait(
        serial,
        lambda ns: any(n["text"].startswith(TG_CHAT_NAME + ",") for n in ns),
        timeout_s,
    )
    row = next((n for n in nodes if n["text"].startswith(TG_CHAT_NAME + ",")), None)
    if row is None:
        return []
    sh(serial, f"input tap 540 {row['cy']}")
    _, nodes = _ui_wait(
        serial,
        lambda ns: any(n["text"].strip() == TG_COMPOSE_HINT for n in ns)
        or any(_TG_DATE_SEP_RE.match(n["text"].strip()) for n in ns),
        timeout_s,
    )
    return nodes


def _tg_label(node: dict) -> str:
    """A node's human label, from `text` or `content-desc`.

    Telegram's *selection toolbar* exposes its actions as ICON buttons whose label lives
    only in `content-desc` (`text` is empty), while the confirm *dialog* puts the same
    words in `text`. Matching on `text` alone therefore never sees the toolbar's Delete,
    which is exactly how `clear_telegram_run_leaks` failed: the long-press worked, the
    selection bar appeared, and the cleanup reported "long-press menu did not appear"
    (measured 2026-09-22). Never match on `text` alone here.
    """
    return node["text"].strip() or (node.get("desc") or "").strip()


def _tg_delete_actions(nodes: list[dict]) -> list[dict]:
    """The Delete entries in a Telegram long-press menu or confirm dialog.

    An EXACT match on the label, not a substring: the confirm dialog also contains a
    "Delete message" title and an "Also delete for Yuvraj" checkbox, and tapping either
    would be wrong (the checkbox would notify the real contact).
    """
    return [n for n in nodes if _tg_label(n) == "Delete"]


def _tg_draft(nodes: list[dict]) -> str | None:
    """The composer's text when a draft is present, else None (an empty box shows the hint).

    Only the composer counts, and it is identified by position: the chat-list SEARCH box
    is an EditText too, so when Telegram opens on the list rather than in the chat its
    hint ("Search Chats") otherwise reads as a leaked draft. That false positive is what
    the y-guard below prevents.
    """
    box = next((n for n in nodes if "EditText" in n["cls"] and n["cy"] > 1500), None)
    if box is None:
        return None
    text = box["text"].strip()
    return text if text and text != TG_COMPOSE_HINT else None


def _tg_run_window_bubbles(nodes: list[dict], today_label: str) -> list[dict]:
    """Bubbles below a date separator for TODAY -- i.e. written by a run, not seeded.

    Seeded history in this chat is dated 2026-08-20/23, so anything under today's
    separator is a run artifact (a chase message that was sent, or a failed send the
    model left behind) and must go before the next run reads it as already handled.
    """
    stamps = [n for n in nodes if _TG_DATE_SEP_RE.match(n["text"].strip())]
    today_seps = [n for n in stamps if n["text"].strip() == today_label]
    if not today_seps:
        return []
    cutoff = max(n["cy"] for n in today_seps)
    return [
        n for n in nodes
        if n["cy"] > cutoff and ("Sent at" in n["text"] or "Received at" in n["text"])
    ]


def probe_telegram_delivery(serial: str) -> dict:
    """Evidence that THIS run actually delivered a message to TG_CHAT_NAME.

    A task whose deliverable is a message cannot be graded on `success` alone: measured
    2026-09-22 in the hard__bookmyshow__005 re-run, three rows self-reported success
    without delivering anything -- one left the text in the composer, one never launched
    Telegram at all, and one typed the whole message into Telegram's SEARCH box. All three
    would score as passes. The run-window bubble is the device-side fact: a message that
    reached the chat carries a "Sent at" stamp under today's separator, and nothing else
    can produce one.

    Read-only, and it must run BEFORE the leak cleanup deletes the bubble. Returns
    `reached_chat: False` when the chat could not be opened, which callers must treat as
    "no evidence" rather than as "nothing was sent" -- the two are different verdicts and
    only the second is safe to fail a run on.
    """
    today = _tg_today_label(serial)
    nodes = _tg_open_chat(serial)
    if not nodes:
        return {"reached_chat": False, "today": today, "sent_bubbles": 0,
                "draft_present": False, "sent_texts": []}
    bubbles = _tg_run_window_bubbles(nodes, today)
    draft = _tg_draft(nodes)
    return {
        "reached_chat": True,
        "today": today,
        "sent_bubbles": len(bubbles),
        # A live draft is the signature of the "typed it but never sent it" failure.
        "draft_present": draft is not None,
        "draft_text": draft or "",
        "sent_texts": [" ".join(b["text"].split())[:400] for b in bubbles],
    }


def _tg_today_label(serial: str) -> str:
    """Telegram's date-separator spelling for today, read from the device clock."""
    raw = sh(serial, "date +%Y-%m-%d").strip()
    try:
        _y, m, d = (int(x) for x in raw.split("-"))
    except ValueError:
        return ""
    import calendar as _calendar

    return f"{_calendar.month_name[m]} {d}"


def clear_telegram_run_leaks(serial: str, apply: bool) -> bool:
    """Clear a leaked draft and any run-window bubbles in the Yuvraj Airtel chat.

    The failure this prevents is specific and measured: row 4's chase message never left
    the composer, and rows 5/6/9/11 then opened the chat to find it already typed -- row
    9 reported "The message is already composed" and row 11 "I can see the message has
    been sent!". A run that DOES send leaves a bubble the next one reads as done.
    """
    today = _tg_today_label(serial)
    nodes = _tg_open_chat(serial)
    if not nodes:
        print("  [!!]  telegram: could not open the Yuvraj Airtel chat — clean it by hand")
        return False

    draft = _tg_draft(nodes)
    leaks = _tg_run_window_bubbles(nodes, today)
    if draft is None and not leaks:
        print("  [ok]  telegram: composer empty, no run-window bubbles in Yuvraj Airtel")
        sh(serial, f"am force-stop {TG_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    print(f"  [!!]  telegram leak: draft={draft!r}, {len(leaks)} run-window bubble(s) dated {today}")
    if not apply:
        print("  [dry] clear the draft and delete the run-window bubbles")
        sh(serial, f"am force-stop {TG_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    if draft is not None:
        # Ctrl+A does NOT work in Telegram's composer (measured 2026-09-22: the selection
        # is ignored and the draft survives). Move to the end and delete character-wise
        # instead -- then re-read the composer and retry, because a tap that misses focus
        # silently clears nothing.
        #
        # Two further failure modes, both measured 2026-09-22 and both of which burned a
        # row (row 11 aborted at the seed gate) before they were handled:
        #   * One large `input keyevent 67 x N` drops presses. On a ~127-char draft it
        #     left 'INOX: Symphony Mall, Avenge' (27 chars) behind -- so the delete has to
        #     be chunked with a read between chunks, not fired once.
        #   * A dump that transiently lacks the composer used to `break` the loop, which
        #     then printed "still holds a draft after 3 attempts" having really tried once.
        #     A missing box is a reason to retry, never to give up.
        ok_draft = False
        for _ in range(6):
            fresh = _ui_nodes(_pull_ui_dump(serial))
            box = next((n for n in fresh if "EditText" in n["cls"] and n["cy"] > 1500), None)
            if box is None:
                time.sleep(2)  # transient: the composer comes back; retry, don't bail
                continue
            _ui_tap(serial, box)
            time.sleep(2)
            sh(serial, "input keyevent 123")  # KEYCODE_MOVE_END
            time.sleep(1)
            # Chunked, with a read after each chunk: a single flood silently truncates.
            for _ in range(len(draft) // 25 + 3):
                sh(serial, "input keyevent " + " ".join(["67"] * 25))  # DEL x25
                time.sleep(1)
                draft = _tg_draft(_ui_nodes(_pull_ui_dump(serial)))
                if draft is None:
                    break
            if draft is None:
                ok_draft = True
                break
        if not ok_draft:
            print(f"  [!!]  telegram: composer still holds a draft after 6 attempts ({draft!r})")
    else:
        ok_draft = True

    # Delete bottom-up: the a11y coordinates shift as bubbles disappear, so re-dumping
    # each round is required (and doubling as the loop guard against a stuck menu).
    ok = True
    for _ in range(len(leaks)):
        dels: list[dict] = []
        # A long-press does not always register: measured 2026-09-22 as "long-press menu
        # did not appear" on a real sent bubble. A missed press leaves the message
        # resident -- which is the exact contamination this cleanup exists to prevent, and
        # it then aborts every later row at the seed gate -- so retry with a longer hold
        # before giving up.
        for hold in (900, 1400, 1400):
            targets = _tg_run_window_bubbles(_ui_nodes(_pull_ui_dump(serial)), today)
            if not targets:
                break
            victim = max(targets, key=lambda n: n["cy"])
            sh(serial, f"input swipe {victim['cx']} {victim['cy']} "
                       f"{victim['cx']} {victim['cy']} {hold}")
            time.sleep(3)
            menu = _ui_nodes(_pull_ui_dump(serial))
            # The selection bar's `Delete` is the topmost one; the dialog's is lower.
            # Its label is in `content-desc` (icon button) -- see _tg_label.
            dels = _tg_delete_actions(menu)
            if dels:
                break
        if not dels:
            print("  [!!]  telegram: long-press menu did not appear after 3 attempts — stopping")
            ok = False
            break
        _ui_tap(serial, min(dels, key=lambda n: n["cy"]))
        time.sleep(3)
        dialog = _ui_nodes(_pull_ui_dump(serial))
        # Leave "Also delete for Yuvraj" UNCHECKED: this is device-side cleanup, and
        # ticking it would notify the real contact that the message was deleted. Note this
        # must be an EXACT "Delete": the dialog also has a "Delete message" title and an
        # "Also delete for Yuvraj" row, both of which a substring match would hit.
        confirm = _tg_delete_actions(dialog)
        if not confirm:
            print("  [!!]  telegram: delete confirmation did not appear — stopping")
            ok = False
            break
        _ui_tap(serial, max(confirm, key=lambda n: n["cy"]))  # the dialog's Delete
        time.sleep(4)

    # Deleting a draft in the composer is not enough on its own: Telegram persists the
    # *editor contents* when the app is backgrounded, so force-stopping too soon lets it
    # restore the stale on-disk draft on the next launch (measured 2026-09-22 -- clearing
    # then killing within ~2s brought the draft straight back, while clearing, going HOME
    # and waiting before the kill made it stick). Park the app first, give it time to
    # flush the now-empty draft, then stop it.
    sh(serial, "input keyevent KEYCODE_HOME")
    time.sleep(10)
    sh(serial, f"am force-stop {TG_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    return ok and ok_draft


def verify_telegram_chat_clean(serial: str) -> bool:
    """Gate: the Yuvraj Airtel composer is empty and no run-window bubble remains."""
    today = _tg_today_label(serial)
    nodes = _tg_open_chat(serial)
    if not nodes:
        print("  FAIL telegram: could not read the Yuvraj Airtel chat")
        return False
    draft = _tg_draft(nodes)
    leaks = _tg_run_window_bubbles(nodes, today)
    sh(serial, f"am force-stop {TG_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    good = draft is None and not leaks
    detail = (f"composer {'empty' if draft is None else 'HOLDS A DRAFT'}, "
              f"{len(leaks)} run-window bubble(s) dated {today}")
    print(f"  {'PASS' if good else 'FAIL'} telegram: Yuvraj Airtel {detail}")
    return good


# --- Google Maps run-leak cleanup -----------------------------------------------------
# The Maps tasks (medium__google-maps__002, easy__google-maps__004) leak in two ways that
# a force-stop cannot clear, because both live in app-private state:
#
#   1. The search box's *Recent* list keeps "Biju Patnaik International Airport". A later
#      run then taps the suggestion instead of typing the query and the grader sees the
#      right end state for free -- the "vacuous PASS" of redo.md section 1 (7 of 13 runs).
#   2. The task WRITES a note ("Fastest Route to Bhubaneswar Airport" and model-specific
#      variants), one per run. Left alone they accumulate in the OnePlus Notes list, where
#      they (a) are the same free-hint surface and (b) push the protected `Budget Deadline`
#      seed below the fold, so `_note_find_title` cannot see it and the seed gate aborts
#      every later row. Measured 2026-09-23: a 13-row batch left 7 such notes, the seed
#      looked missing, and rows 8-13 aborted.
#
# Both are UI-only: Maps has no public API for recent history, and the notes are
# app-private. `parked here` is easy__google-maps__004's artifact.
MAPS_PKG = "com.google.android.apps.maps"
MAPS_RECENTS_BUTTON = (391, 192)  # the "Search here" omnibox on the Maps home screen
MAPS_RUN_NOTE_PATTERNS = ("Bhubaneswar Airport", "parked here")


def _note_list_rows(nodes: list[dict]) -> list[dict]:
    """Note rows in the scrollable list area (above the bottom nav bar)."""
    return [n for n in nodes if n["rid"].endswith("tv_title") and 200 < n["bounds"][1] < 2190]


def _note_is_run_artifact(title: str) -> bool:
    """True for a run-created Maps note. Never matches a protected seed."""
    if title in NOTE_PROTECTED_TITLES:
        return False
    return any(p in title for p in MAPS_RUN_NOTE_PATTERNS)


def _note_list_open(serial: str) -> list[dict]:
    """Force-stop Notes, launch it and land on the *Notes* tab's list.

    The app reopens on whichever bottom tab was last used, and the **To-dos** tab does not
    list notes -- so a run that ends on To-dos makes every note look missing.
    """
    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, f"monkey -p {NOTE_PKG} -c android.intent.category.LAUNCHER 1")
    time.sleep(7)
    nodes = _ui_nodes(_pull_ui_dump(serial))
    tab = next((n for n in sorted((n for n in nodes if n["rid"].endswith("id/note_tab")),
                                  key=lambda n: n["cy"], reverse=True)), None)
    if tab is not None:
        _ui_tap(serial, tab)
        time.sleep(4)
        nodes = _ui_nodes(_pull_ui_dump(serial))
    return nodes


def clear_maps_run_notes(serial: str, apply: bool) -> bool:
    """Delete the run-created Maps notes, keeping the protected `Budget Deadline` seed."""
    nodes = _note_list_open(serial)
    targets = [r for r in _note_list_rows(nodes) if _note_is_run_artifact(r["text"])]

    if not targets:
        # They may sit below the fold, so scan before concluding there are none.
        for _ in range(8):
            sh(serial, "input swipe 540 1700 540 800 300")
            time.sleep(1.4)
            nodes = _ui_nodes(_pull_ui_dump(serial))
            targets = [r for r in _note_list_rows(nodes) if _note_is_run_artifact(r["text"])]
            if targets:
                break
    if not targets:
        print("  [ok]  notes: no Maps run-notes")
        sh(serial, f"am force-stop {NOTE_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    print(f"  [!!]  notes: {len(targets)} Maps run-note(s) - e.g. {targets[0]['text'][:48]!r}")
    if not apply:
        print("  [dry] delete the Maps run-notes (multi-select, never 'Select all')")
        sh(serial, f"am force-stop {NOTE_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    removed = 0
    for _ in range(12):
        nodes = _ui_nodes(_pull_ui_dump(serial))
        targets = [r for r in _note_list_rows(nodes) if _note_is_run_artifact(r["text"])]
        if not targets:
            break

        if not any(n["rid"].endswith("id/select_all") for n in nodes):
            # Long-press enters multi-select AND checks the pressed row.
            t = targets[0]
            sh(serial, f"input swipe {t['cx']} {t['cy']} {t['cx']} {t['cy']} 1200")
            time.sleep(2.5)
            nodes = _ui_nodes(_pull_ui_dump(serial))
            if not any(n["rid"].endswith("id/select_all") for n in nodes):
                print("  [!!]  notes: multi-select did not open - delete these by hand")
                break

        # Tick only the targets whose checkbox is still clear. Tapping an already-checked
        # row DESELECTS it, and the long-press has already checked the row it pressed:
        # 2026-09-23's first attempt tapped every target, cleared the one it had just
        # selected, and then deleted nothing while still reporting success.
        boxes = [n for n in nodes if n["rid"].endswith("id/cb_list_select")]
        for row in _note_list_rows(nodes):
            if not _note_is_run_artifact(row["text"]):
                continue
            box = min(boxes, key=lambda b: abs(b["cy"] - row["cy"]), default=None)
            if box is None or box["checked"]:
                continue
            _ui_tap(serial, row)
            time.sleep(0.7)

        nodes = _ui_nodes(_pull_ui_dump(serial))
        sel = next((n["text"] for n in nodes if n["rid"].endswith("id/main_title")), "")
        m = re.search(r"(\d+)\s+selected", sel)
        n_sel = int(m.group(1)) if m else 0
        if n_sel == 0:
            print("  [!!]  notes: nothing stayed selected - aborting this sweep")
            sh(serial, "input keyevent 4")
            time.sleep(1.5)
            break

        dele = next((n for n in nodes if n["rid"].endswith("id/note_delete")), None)
        if dele is None:
            print("  [!!]  notes: no delete action - backing out")
            sh(serial, "input keyevent 4")
            time.sleep(1.5)
            break
        _ui_tap(serial, dele)
        time.sleep(2.5)
        # Confirmation dialog, when the build shows one.
        nodes = _ui_nodes(_pull_ui_dump(serial))
        confirm = next((n for n in nodes
                        if n["text"] in ("Delete", "OK", "Confirm") and n["bounds"][1] > 900), None)
        if confirm is not None:
            _ui_tap(serial, confirm)
            time.sleep(2.5)
        removed += n_sel
        time.sleep(1.5)

    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    print(f"  [ok]  notes: deleted {removed} Maps run-note(s)")
    return True


def verify_maps_run_notes_clear(serial: str) -> bool:
    """Gate: no Maps run-note is left in the Notes list."""
    nodes = _note_list_open(serial)
    for _ in range(8):
        left = [r["text"] for r in _note_list_rows(nodes) if _note_is_run_artifact(r["text"])]
        if left:
            break
        sh(serial, "input swipe 540 1700 540 800 300")
        time.sleep(1.4)
        nodes = _ui_nodes(_pull_ui_dump(serial))
    else:
        left = [r["text"] for r in _note_list_rows(nodes) if _note_is_run_artifact(r["text"])]
    sh(serial, f"am force-stop {NOTE_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    print(f"  {'PASS' if not left else 'FAIL'} notes: {len(left)} Maps run-note(s) left"
          + (f" - {left[0][:48]!r}" if left else ""))
    return not left


def clear_maps_recents(serial: str, apply: bool) -> bool:
    """Clear the Maps search box's *Recent* list (the redo.md section 1 free hint).

    Long-press each recent row -> "Delete suggested search?" -> Delete. Never a plain tap:
    that opens the place page AND re-adds the row to history (measured 2026-09-16).
    """
    sh(serial, "input keyevent KEYCODE_WAKEUP")
    sh(serial, f"am force-stop {MAPS_PKG}")
    sh(serial, f"monkey -p {MAPS_PKG} -c android.intent.category.LAUNCHER 1")
    time.sleep(8)
    sh(serial, f"input tap {MAPS_RECENTS_BUTTON[0]} {MAPS_RECENTS_BUTTON[1]}")
    time.sleep(5)
    nodes = _ui_nodes(_pull_ui_dump(serial))

    def recent_rows(ns: list[dict]) -> list[dict]:
        # The Recent section starts under the "Recent" header; rows there are tappable
        # place/query entries, not the Home/Work/Favourites chips above it.
        hdr = next((n for n in ns if n["text"] == "Recent"), None)
        if hdr is None:
            return []
        chip_labels = ("Home", "Work", "Favourites", "Set location")
        out = []
        for n in ns:
            if (n["bounds"][1] > hdr["bounds"][1] and n["text"].strip()
                    and n["text"] not in chip_labels
                    and not n["text"].startswith("Search here")
                    and n["text"] != "Recent"):
                out.append(n)
        return out

    rows = recent_rows(nodes)
    if not rows:
        print("  [ok]  maps: recent list empty")
        sh(serial, f"am force-stop {MAPS_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    print(f"  [!!]  maps: {len(rows)} entry/entries in the recent list")
    if not apply:
        print("  [dry] clear the Maps recent list")
        sh(serial, f"am force-stop {MAPS_PKG}")
        sh(serial, "input keyevent KEYCODE_HOME")
        return True

    for _ in range(12):
        nodes = _ui_nodes(_pull_ui_dump(serial))
        rows = recent_rows(nodes)
        if not rows:
            break
        t = rows[0]
        sh(serial, f"input swipe {t['cx']} {t['cy']} {t['cx']} {t['cy']} 1200")
        time.sleep(3)
        dlg = _ui_nodes(_pull_ui_dump(serial))
        if not any(n["text"] == "Delete suggested search?" for n in dlg):
            # Not a deletable suggestion (e.g. a "More from recent history" row): skip it
            # by scrolling rather than tapping, which would re-add it to history.
            sh(serial, "input keyevent 4")
            time.sleep(1)
            sh(serial, "input swipe 540 1200 540 700 300")
            time.sleep(1.5)
            continue
        dele = next((n for n in dlg if n["text"] == "Delete"), None)
        if dele is None:
            sh(serial, "input keyevent 4")
            continue
        _ui_tap(serial, dele)
        time.sleep(3)

    sh(serial, f"am force-stop {MAPS_PKG}")
    sh(serial, "input keyevent KEYCODE_HOME")
    print("  [ok]  maps: recent list cleared")
    return True


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
    parser.add_argument("--no-calendar-view-check", action="store_true",
                        help="Skip the Calendar-app view-mode gate. Schedule view is the "
                             "starting state the original runs began from; an agent can "
                             "leave the app in Day view (redo.md 7.2), which no provider "
                             "query can detect. Auto-restores rather than only warning.")
    parser.add_argument("--meet-strict", action="store_true",
                        help="Treat a failing Meet agenda check as a hard FAIL. Default is "
                             "WARN, because the seed is known-unsolvable until the meeting "
                             "exists server-side (redo.md #2).")
    parser.add_argument("--no-account-check", action="store_true",
                        help="Skip the canonical-cloud-account gate (~40s: launches Gmail, "
                             "Drive, Docs, Slides, Calendar, Meet and Photos to read each "
                             "app's selected Google account)")
    parser.add_argument("--no-slides-check", action="store_true",
                        help="Skip the Slides deck gate AND its restore (restore re-pushes "
                             "the version-controlled Q3_Review.pptx when the device copy is "
                             "missing or has the wrong slide count; the gate then asserts it)")
    parser.add_argument("--settle-recheck", type=float, default=0.0, metavar="SECONDS",
                        help="After --apply, nudge the calendar sync, wait SECONDS, then "
                             "re-assert the date anchors. Catches a silent revert of the "
                             "synced-calendar seeds (2026-09-20 root cause). 0 = off.")
    parser.add_argument("--no-leak-cleanup", action="store_true",
                        help="Skip the Telegram + OnePlus-Notes run-leak cleanup and its "
                             "gate. Both drive the UI (~40-90s). Force-stopping an app "
                             "resets its screen, never its content: a leaked second-hand "
                             "Telegram draft misled 4 rows, and an in-place edit to the "
                             "Budget Deadline note (row 12) flips the overdue branch the "
                             "next run takes. See redo.md 7.2.")
    parser.add_argument("--leak-cleanup-only", action="store_true",
                        help="Do ONLY the Telegram + OnePlus-Notes run-leak cleanup and its "
                             "gate, then exit -- the cheap (~60-90s) between-row repair for "
                             "a batch runner. Implies --apply. A batch that re-runs one task "
                             "across all rows hits this on EVERY row for any task that "
                             "messages: 2026-09-22's hard__bookmyshow__005 batch lost rows "
                             "3-13 because row 2 composed a Telegram plan and left the draft "
                             "behind, and the (correct) verify-only gate then aborted each "
                             "remaining row rather than seed it contaminated.")
    parser.add_argument("--delivery-probe", action="store_true",
                        help="Read-only: report whether the Yuvraj Airtel chat holds a "
                             "message sent TODAY (a run-window bubble), plus any live "
                             "draft. Prints one `DELIVERY {json}` line and exits. The "
                             "evidence a message-delivering task needs: three rows of the "
                             "2026-09-22 hard__bookmyshow__005 re-run self-reported "
                             "success without delivering anything, and `success` alone "
                             "cannot tell that from a real send. Run it BEFORE the leak "
                             "cleanup, which deletes the bubble it looks for.")
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

    # Read-only delivery evidence, for the grader of a message-delivering task.
    if args.delivery_probe:
        print("DELIVERY " + json.dumps(probe_telegram_delivery(args.serial)))
        return 0

    # Between-row repair for a batch runner: only the content leaks, then its gate.
    # Deliberately narrow so it can run on every row without paying for the calendar
    # anchors, account sweep or slides push. `--apply` is implied: the caller wants the
    # repair done, not a dry-run of it.
    if args.leak_cleanup_only:
        if args.no_leak_cleanup:
            print("ERROR: --leak-cleanup-only contradicts --no-leak-cleanup", file=sys.stderr)
            return 2
        print("== leak cleanup only (Telegram draft/bubbles + Budget Deadline note + Maps) ==")
        clear_telegram_run_leaks(args.serial, apply=True)
        restore_budget_note(args.serial, apply=True)
        clear_maps_run_notes(args.serial, apply=True)
        clear_maps_recents(args.serial, apply=True)
        # All verifies always run (`&=` does not short-circuit), so the log names every
        # leak that is still live rather than only the first.
        ok_only = verify_telegram_chat_clean(args.serial)
        ok_only &= verify_budget_note(args.serial)
        ok_only &= verify_maps_run_notes_clear(args.serial)
        print("RESULT " + ("PASS" if ok_only else "FAIL"))
        return 0 if ok_only else 1

    if not args.verify_only:
        print(f"== reset (profile={profile_name}, apply={args.apply}) ==")
        reset_settings(args.serial, prof.get("settings", {}), args.apply)
        unblock_numbers(args.serial, prof.get("blocked_numbers_to_remove", []), args.apply)
        remove_calendar_events(args.serial, prof.get("calendar_titles_to_remove", []), args.apply)
        remove_calendar_by_ids(args.serial, prof.get("calendar_ids_to_remove", []), args.apply)
        remove_recurring_calendar_artifacts(
            args.serial, prof.get("calendar_recurring_artifacts_to_remove", []), args.apply)
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
        # Ground-truth fixture with no generator: re-push the deck so it cannot rot back
        # to the stray 1-slide "Q3 Review" that re-scored easy__google-slides__001
        # against the wrong file for six runs (redo.md 5). Cheap no-op when correct.
        if not args.no_slides_check:
            restore_slides_deck(args.serial, prof, args.apply)
        if not args.no_leak_cleanup:
            # Content leaks, which no force-stop can clear (see the section header above).
            # Both report rather than raise, so a cleanup failure cannot abort a reset.
            clear_telegram_run_leaks(args.serial, apply=args.apply)
            restore_budget_note(args.serial, apply=args.apply)
            clear_maps_run_notes(args.serial, apply=args.apply)
            clear_maps_recents(args.serial, apply=args.apply)
        manual = prof.get("manual_ui_cleanup") or []
        if manual:
            print("== CANNOT auto-reset (app-private; do by hand in the UI) ==")
            for item in manual:
                print(f"  - {item}")
        print("== UI-only manual cleanups (no ADB) — see scripts/seeding/SKILL.md ==")

    ok = verify(args.serial, prof)
    # Not part of verify(): like the account/slides checks it drives an app, and it is
    # gated by its own flag. It DOES block -- an agent that starts on the wrong Calendar
    # screen is not running the task that was benchmarked.
    if not args.no_calendar_view_check:
        ok &= verify_calendar_view_mode(args.serial, prof)
    if args.settle_recheck and args.apply and not args.verify_only:
        ok &= assert_anchor_durability(args.serial, prof, args.settle_recheck,
                                       prof.get("calendar_account", ""))
    if not args.no_account_check:
        ok &= verify_cloud_accounts(args.serial, prof)
    if not args.no_slides_check:
        ok &= verify_slides_deck(args.serial, prof)
    if not args.no_leak_cleanup:
        # Both are gates, not warnings: a run that starts against a leaked draft or an
        # edited note is not running the benchmarked task.
        ok &= verify_telegram_chat_clean(args.serial)
        ok &= verify_budget_note(args.serial)
    # The Meet agenda check is verified but -- by default -- does NOT block. It cannot
    # pass today for a reason that is not a seeding mistake: the meeting has to exist in
    # Google's CLOUD for Meet to list it, and an adb-written calendar row never uploads
    # (measured: both force-sync nudges are no-ops). See redo.md #2. Downgrading it to a
    # WARN keeps the launch gate usable without hiding the fault -- it is printed loudly,
    # recorded in the seed stamp, and re-armed with --meet-strict.
    meet_ok = verify_meet_agenda(args.serial, prof) if not args.no_meet_check else True
    if not meet_ok and not args.meet_strict:
        print("  WARN meet: KNOWN-UNSOLVABLE SEED (redo.md #2) — not a seeding regression, "
              "and NOT blocking. hard__google-meet-files__070 cannot pass until the "
              "meeting exists server-side (create it in the Calendar app UI, which does "
              "upload). Pass --meet-strict to block on this.")
    ok &= meet_ok or not args.meet_strict
    # Clock + freshness are checked LAST and only in verify-only mode:
    #   * `--apply` is the thing that MAKES the seed fresh, so failing it mid-apply for
    #     being stale would be self-defeating -- it stamps itself below instead;
    #   * `--verify-only` is what the launch gate runs, and a stale stamp there is exactly
    #     the condition that must block a run.
    ok &= verify_device_clock(args.serial)
    if args.verify_only:
        ok &= verify_seed_freshness(profile_name)
    if args.apply and not args.verify_only and ok:
        write_seed_state(args.serial, profile_name)
    print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
