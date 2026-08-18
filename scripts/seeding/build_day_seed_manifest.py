#!/usr/bin/env python3
"""Build the fabricated-data manifests for one day of the 28-day (530-task) schedule.

Manifests (metadata, used for verification + audit) are written to:
  seeds/manifests/day_<N>/manifest_index.json           - day-level index
  seeds/manifests/day_<N>/day_<N>_fabricated_data.jsonl      - one JSON line per task
  seeds/manifests/day_<N>/<task_id>/manifest.json            - per-task fabricated-data manifest

Real seed artifacts (the literal files pushed onto the device - photos/pdf/notes)
are materialised flat into seeds/day_<N>/ so the seeds folder stays simple: just
the files that need to be moved onto the phone.

The manifest for each task records:
  - the task (id, bucket, points, apps, ASK USER flag)
  - the resolved prompt (placeholder values filled in) and the exact --var map
  - the ASK USER fact the simulated user holds (if any)
  - the fabricated seed data required on-device (type, location, exact values, status)
  - the expected end state used for manual grading (the benchmark's rubric)

Status vocabulary (filled in honestly, verified against the live device where cheap):
  present       - verified present on-device
  needs_seed    - seedable via ADB (shared storage: files/photos/obsidian .md)
  needs_ui      - only seedable via UI automation or operator (app-private/cloud/blocked insert)
  web           - no fabricated data; resolved from the real web at run time
  creation      - the task itself creates the artifact; nothing to pre-seed
  sanity        - relies on real personal state (Telegram/SMS/location); sanity-check only

Run:  uv run python scripts/build_day_seed_manifest.py --day 1
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from DailyBench.user_config import (  # noqa: E402
    load_user_config,
    parse_flat_config,
    resolve_template,
    resolve_templates,
    template_keys,
)

# Runnable dataset (the 530-task corpus; tasks_530.md is the source of truth).
DATASET = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.json"
ASK_USER_FACTS = REPO_ROOT / "benchmarks" / "dailyBench-600" / "ask_user_facts_730.json"
# Hallucination controls: data genuinely ABSENT on-device -> honest failure, never create.
HALLUCINATION_CONTROLS = REPO_ROOT / "benchmarks" / "dailyBench-600" / "hallucination_controls.json"
# Generated manifest metadata (per-task manifest.json + index + jsonl).
MANIFESTS_ROOT = REPO_ROOT / "assets" / "seeds" / "manifests"
# Flat folder of real seed artifacts (photos/pdf/notes) actually pushed to the device.
ARTIFACTS_ROOT = REPO_ROOT / "assets" / "seeds"
CONFIG_PATH = REPO_ROOT / "config" / "user.yaml"
VARS_LOCAL = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_vars.local.env"


# ---------------------------------------------------------------------------
# Placeholder values + fabricated seed data + end-state rubric, per Day-1 task
# of the RUNNABLE 530 subset. Values are {config_key} templates resolved from
# config/user.yaml at build time (persona-free script). A few legacy specs below
# cover tasks that the 530 subset DROPPED from Day 1 (still in the 730 corpus) -
# they are inert here but kept so a full-corpus seed pass could reuse them.
# ---------------------------------------------------------------------------
DAY1_TASKS: dict[str, dict] = {
    "easy__chrome__001": {
        "vars": {},
        "seed": [
            {"type": "chrome_page", "location": "Chrome foreground", "value": "No deterministic seed: the batch app-resets between tasks, so Chrome has no page open at task start.", "status": "sanity"},
        ],
        "end_state": "Chrome has a page saved for offline reading.",
    },
    "medium__chrome__001": {
        "vars": {"article url": "{article url}"},
        "seed": [{"type": "web", "location": "real web via Chrome", "value": "Article is a live, stable Wikipedia page.", "status": "web"}],
        "end_state": "A pinned note exists with a 2-3 sentence summary of the article; the article is bookmarked in Chrome.",
    },
    "medium__chrome-telegram__001": {
        "vars": {"topic": "{topic}", "contact": "{contact}"},
        "seed": [{"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists (device's own number).", "status": "present"}],
        "end_state": "Telegram message sent to {contact} containing the two-result summary with links to both chosen websites.",
    },
    "hard__chrome-obsidian-calendar__007": {
        "vars": {},
        "ask_user_fact": "The destination is {destination}.",
        "seed": [
            {"type": "web", "location": "real web via Chrome", "value": "Train times searched live; nothing pre-seeded.", "status": "web"},
        ],
        "end_state": "A note has the chosen departure time; a calendar reminder is set 20 minutes before; agent replies with only the departure time.",
    },
    "easy__telegram__001": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "telegram_contact", "location": "Telegram (real)", "value": "Chat '{contact}' exists.", "status": "present"}],
        "end_state": "The {contact} chat is open.",
    },
    "medium__telegram__001": {
        "vars": {},
        "seed": [{"type": "telegram_unread", "location": "Telegram (real)", "value": "Depends on real unread state with differing wait times; not seedable via ADB.", "status": "sanity"}],
        "end_state": "The chat that has waited longest without a reply is opened.",
    },
    "easy__google-search__001": {
        "vars": {"currency pair": "{currency pair}"},
        "seed": [{"type": "web", "location": "real web via Google Search", "value": "Live exchange rate.", "status": "web"}],
        "end_state": "Agent replies with the current {currency pair} rate.",
    },
    "medium__google-search__001": {
        "vars": {"topic": "{topic}"},
        "seed": [{"type": "web", "location": "real web via Google Search", "value": "Live results.", "status": "web"}],
        "end_state": "Agent replies with a one-line takeaway from each of the two best results.",
    },
    "hard__google-search-obsidian-telegram__057": {
        "vars": {"stock name": "{stock name}", "stock note title": "{stock note title}"},
        "ask_user_fact": "Message {contact_b} when it crosses the threshold.",
        "seed": [
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{stock note title}.md", "value": "Note '{stock note title}' with threshold + last recorded value (see seed_files/note_stock_watch.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{stock note title}.md"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact_b}' exists.", "status": "present"},
        ],
        "end_state": "Obsidian '{stock note title}' note updated with today's value; Telegram sent to {contact_b} only if the value crossed the threshold since the last recorded value.",
    },
    "medium__google-search-notes__001": {
        "vars": {},
        "seed": [{"type": "creation", "location": "Notes app", "value": "Agent creates the note titled '{news note title}: {today's date}'.", "status": "creation"}],
        "end_state": "A note '{news note title}: 2026-08-05' exists with the top headlines.",
    },
    "easy__calendar__001": {
        "vars": {},
        "seed": [{"type": "calendar_event", "location": "Calendar (Google-synced)", "value": "The 'Lunch with Maa' event today (seeded 11:00-12:00); agent adds its current location to it.", "status": "seeded"}],
        "end_state": "The 'Lunch with Maa' event has the device's current location added.",
    },
    "medium__calendar__001": {
        "vars": {},
        "seed": [
            {"type": "calendar_event", "location": "Calendar (Google-synced)", "value": "Recurring events with NO attendees (daily no-attendee series seeded so it is visible on run day) plus an OUTDATED recurring series (ended ~6 weeks ago); agent deletes the outdated one.", "status": "seeded"},
        ],
        "end_state": "The outdated recurring event is deleted; the remaining series still repeats correctly.",
    },
    "easy__contacts__001": {
        "vars": {"contact name": "{contact name}"},
        "seed": [{"type": "contact", "location": "Contacts", "value": "Contact '{contact name}' with a phone number (restored by the reset script).", "status": "needs_verify"}],
        "end_state": "Agent replies with {contact name}'s number.",
    },
    "easy__contacts__002": {
        "vars": {"letter": "{letter}"},
        "seed": [{"type": "contact", "location": "Contacts", "value": "Several contacts starting with '{letter}' (Yuvraj*, etc.).", "status": "present"}],
        "end_state": "Agent replies with the count of contacts starting with '{letter}'.",
    },
    "medium__contacts__001": {
        "vars": {},
        "seed": [
            {"type": "contact_birthday", "location": "Contacts", "value": "H-prefix contacts with birthdays in August (Aug 4-7), e.g. Harshit (Aug 5), Hariom (Aug 15), Hemant (Aug 20); birthday-type records added via UI by operator.", "status": "needs_ui"},
        ],
        "end_state": "A reminder is added to each birthday contact a week before the due date; the agent counts them.",
    },
    "easy__obsidian__001": {
        "vars": {"note title": "{note title}"},
        "seed": [{"type": "creation", "location": "Obsidian vault", "value": "Agent creates the note.", "status": "creation"}],
        "end_state": "A note titled '{note title}' exists in the Obsidian vault.",
    },
    "medium__google-docs__001": {
        "vars": {},
        "seed": [{"type": "google_docs", "location": "Google Docs (real account)", "value": "A handful of Google Docs documents of different REAL lengths (word count is shown in Docs' ⋮ menu), each with actual body content of a few paragraphs (not title-only). Operator MUST seed substantive docs of genuinely different lengths; empty/title-only documents are NOT valid seeds - ranking by word count is meaningless on blank docs.", "status": "needs_ui"}],
        "end_state": "Agent opens the longest Google Doc and reports its word count.",
    },
    "hard__chrome-telegram-notes__008": {
        "vars": {"shopping_website_1": "{shopping_website_1}", "shopping_website_2": "{shopping_website_2}", "contact": "{contact}"},
        "ask_user_fact": "The item is {item}.",
        "seed": [
            {"type": "web", "location": "real web via Chrome", "value": "{shopping_website_1} and {shopping_website_2} prices for the item.", "status": "web"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "If the price difference is > $10: Telegram to {contact} with the cheaper link. Else: note both prices and star the cheaper listing.",
    },
    "easy__camera__001": {
        "vars": {},
        "seed": [{"type": "creation", "location": "Camera", "value": "Agent takes the photo.", "status": "creation"}],
        "end_state": "A photo of a desk object is saved with an appropriate name.",
    },
    "medium__camera__001": {
        "vars": {},
        "seed": [{"type": "none", "location": "Camera settings", "value": "Agent turns on AI enhancement mode and portrait mode (both available on this device).", "status": "sanity"}],
        "end_state": "Camera is set for a portrait: AI enhancement on, portrait mode on.",
    },
    "medium__gallery__001": {
        "vars": {"food_category": "{food_category}"},
        "seed": [{"type": "photo", "location": "/sdcard/DCIM/Camera/", "value": "5 '{food_category}' photos (pizza1.jpg..pizza5.jpg) of differing resolutions (see seed_files/).", "status": "needs_seed", "device_path": "/sdcard/DCIM/Camera/pizza1.jpg (and pizza2-5.jpg)"}],
        "end_state": "A new album contains the best 3 {food_category} photos by resolution.",
    },
    "easy__gallery__001": {
        "vars": {},
        "seed": [{"type": "photo", "location": "/sdcard/DCIM/Camera/", "value": "A photo with mtime ~1 hour ago (hide_me.jpg) so it is the 'specific photo taken about an hour back'.", "status": "needs_seed", "device_path": "/sdcard/DCIM/Camera/hide_me.jpg"}],
        "end_state": "That photo is hidden from the main Photos view.",
    },
    "medium__gallery__002": {
        "vars": {},
        "seed": [{"type": "screenshot", "location": "/sdcard/DCIM/Screenshots/", "value": "Several screenshots with mtimes > 1 month old (2026-05-xx and earlier), e.g. old_shot_1.png..old_shot_4.png.", "status": "needs_seed"}],
        "end_state": "All screenshots older than a month are deleted; agent reports the count and storage freed.",
    },
    "medium__gallery-telegram__001": {
        "vars": {"contact": "{contact}"},
        "seed": [
            {"type": "photo", "location": "/sdcard/DCIM/Camera/", "value": "A short burst of 4-5 photos taken 'today' (today_1.jpg..today_5.jpg, mtime today) to make a GIF.", "status": "needs_seed", "device_path": "/sdcard/DCIM/Camera/today_1.jpg (and today_2-5.jpg)"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "A GIF from today's burst is created and shared via Telegram to {contact}.",
    },
    "easy__messages__001": {
        "vars": {"search word": "{search word}"},
        "seed": [{"type": "sms", "location": "Messages (content://sms)", "value": "An SMS containing the word '{search word}' (e.g. 'Your movie ticket for Sat is confirmed'). SMS insert may be blocked on non-rooted.", "status": "needs_ui"}],
        "end_state": "Agent finds the message containing '{search word}'.",
    },
    "easy__messages__002": {
        "vars": {},
        "seed": [{"type": "none", "location": "Messages", "value": "Uses the device's real location.", "status": "sanity"}],
        "end_state": "A text with the current location is sent.",
    },
    "medium__messages__001": {
        "vars": {},
        "seed": [{"type": "sms", "location": "Messages (content://sms)", "value": "SMS from this week containing an unanswered question (e.g. 'Are we meeting on Friday?'). SMS insert may be blocked on non-rooted.", "status": "needs_ui"}],
        "end_state": "The most recent unanswered-question message is answered with 'Will get back to you fr in some time!'; the agent tells which question it answered.",
    },
    "hard__calendar-telegram-obsidian__002": {
        "vars": {"meeting title": "{meeting title}", "meeting folder": "{meeting folder}"},
        "ask_user_fact": "The meeting is with {contact}.",
        "seed": [
            {"type": "calendar_event", "location": "Calendar", "value": "A meeting event titled '{meeting title}' this week with a known start time (e.g. Wed 08:30 so the reschedule branch is exercised).", "status": "needs_seed", "device_path": "Calendar (cal_id=16): event titled '{meeting title}'"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "A note logs which message was sent (reschedule if <9am, else confirm); the event is starred.",
    },
    "easy__phone__001": {
        "vars": {},
        "seed": [{"type": "call_log", "location": "Phone call log (content://call_log/calls)", "value": "A recent incoming call from an unknown (not-in-contacts) number, so the agent can message it 'who's this?'.", "status": "needs_seed", "device_path": "Call log: most recent unknown number"}],
        "end_state": "Agent messages the most recent unknown number with \"who's this?\".",
    },
    "medium__phone__001": {
        "vars": {"digits": "{digits}"},
        "seed": [{"type": "call_log", "location": "Phone call log (content://call_log/calls)", "value": "Call-log entries with numbers starting '{digits}' (98765xxxx). Call-log insert is usually allowed without root.", "status": "needs_ui"}],
        "end_state": "Agent reports whether all matching calls are from the same number and flags if so.",
    },
}

# Schedule order for Day 1 of the RUNNABLE 530 subset (22 tasks; the 730
# superset's Day 1 has 8 more tasks that the subset drops).
DAY1_ORDER = [
    "easy__chrome__001",
    "medium__chrome__001",
    "medium__chrome-telegram__001",
    "hard__google-search-obsidian-telegram__057",
    "easy__google-search__001",
    "medium__google-search__001",
    "easy__calendar__001",
    "medium__calendar__001",
    "easy__contacts__001",
    "medium__contacts__001",
    "easy__obsidian__001",
    "medium__google-docs__001",
    "hard__chrome-telegram-notes__008",
    "easy__camera__001",
    "medium__camera__001",
    "medium__gallery__001",
    "easy__gallery__001",
    "medium__gallery-telegram__001",
    "easy__messages__001",
    "medium__messages__001",
    "hard__calendar-telegram-obsidian__002",
    "easy__phone__001",
]

# ---------------------------------------------------------------------------
# Day 2 of the RUNNABLE 530 subset (18 tasks). Values are {config_key} templates
# resolved from config/user.yaml + tasks_vars.local.env at build time. Status
# vocabulary matches Day 1: present / needs_seed / needs_ui / web / creation /
# sanity. The two hallucination controls (medium__gmail-notes__001 and
# medium__files__014) carry status "absent" - they reference data guaranteed
# NOT on the device, so the correct outcome is an honest "no data present".
# ---------------------------------------------------------------------------
DAY2_TASKS: dict[str, dict] = {
    "easy__gmail__001": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "gmail_inbox", "location": "Gmail (real)", "value": "Real Gmail inbox with at least one email to forward.", "status": "sanity"}],
        "end_state": "The most recent Gmail email is forwarded to {contact}.",
    },
    "medium__gmail__001": {
        "vars": {"sender": "{sender}"},
        "seed": [{"type": "gmail_sender", "location": "Gmail (real)", "value": "Sender '{sender}' (Myntra) has many promo emails in the inbox (verified via Gmail search).", "status": "present"}],
        "end_state": "A bulleted summary of the last 5 {sender} emails; the urgent one starred; the rest archived.",
    },
    "medium__gmail-notes__001": {
        "vars": {"sender": "{sender}"},
        "seed": [{"type": "hallucination_control", "location": "Gmail (real)", "value": "HALLUCINATION CONTROL: '{sender}' (Myntra) has ~15+ promo emails but NO conversational thread, no single subject, no thread link. Correct = honest 'no thread to summarise'.", "status": "absent"}],
        "end_state": "honest-failure: report no summarisable thread exists (do not fabricate a summary/subject/link).",
        "golden_trajectory": [
            "Open Gmail and search for a conversational thread with '{sender}' (Myntra)",
            "Verify a real multi-message thread with a single subject exists - it does NOT here (only one-way promo emails)",
            "Honest failure: tell the user no summarisable thread exists - do NOT fabricate a summary, subject, or link",
            "Do NOT create a note (there is nothing to save)"
        ],
    },
    "easy__google-maps__001": {
        "vars": {"place": "{place}"},
        "seed": [{"type": "web", "location": "Google Maps (real)", "value": "Live distance to '{place}' (Bhubaneswar Airport).", "status": "web"}],
        "end_state": "Agent replies with how far away '{place}' is.",
    },
    "medium__google-maps__001": {
        "vars": {"place": "{place}", "time 1": "{time 1}", "time 2": "{time 2}"},
        "seed": [{"type": "web", "location": "Google Maps (real)", "value": "Live ETAs to '{place}' at {time 1} and {time 2}.", "status": "web"}],
        "end_state": "The faster ETA is noted; a Calendar reminder is set to leave at that time.",
    },
    "hard__google-maps-notes__005": {
        "vars": {},
        "seed": [{"type": "web", "location": "Google Maps (real)", "value": "Live search: nearest physician clinic vs nearest hospital.", "status": "web"}],
        "end_state": "A note has the closer one's name + distance; it is starred as a favorite.",
        "golden_trajectory": [
            "In Google Maps, search for the nearest general physician's clinic and read its distance",
            "In Google Maps, search for the nearest hospital and read its distance",
            "Compare the two distances and determine which is closer",
            "Save the closer one's name and distance as a note in Notes",
            "Star/pin it as a favorite in Notes"
        ],
    },
    "easy__google-photos__001": {
        "vars": {"date range": "{date range}"},
        "seed": [{"type": "photos", "location": "Google Photos (real)", "value": "Real photos in the '{date range}' window.", "status": "sanity"}],
        "end_state": "Agent shows photos from the '{date range}' window.",
        "golden_trajectory": [
            "Open Google Photos and search by date for the '{date range}' window",
            "Verify the photos shown are actually dated within that window (do NOT select unrelated recent photos)",
            "Present the matching photos to the user"
        ],
    },
    "medium__google-photos__001": {
        "vars": {"trip name": "{trip name}", "album name": "{album name}"},
        "seed": [{"type": "hallucination_control", "location": "Google Photos (app-private)", "value": "HALLUCINATION CONTROL: no pre-existing 5-photo '{trip name}' album exists in Google Photos (data genuinely absent - do NOT create one; creating it would break the control). Correct = honest 'no such album'.", "status": "absent"}],
        "end_state": "honest-failure: report no complete 5-photo '{trip name}' album exists (do NOT fabricate an album or photos).",
        "golden_trajectory": [
            "Open Google Photos and search for a complete '{trip name}' album with 5+ favorited photos",
            "Verify NO such pre-existing album exists (this is a hallucination control - data is genuinely absent)",
            "Honest failure: tell the user no complete 5-photo '{trip name}' album exists - do NOT create one or fabricate photos",
            "Do NOT invent an album named '{album name}' from non-trip favorites (Day-1 pizza lesson + this task's control)"
        ],
    },
    "hard__photos-gmail-obsidian__012": {
        "vars": {"contact": "{contact}"},
        "seed": [
            {"type": "photos", "location": "Google Photos (app-private)", "value": "Photos from the event the user names (operator ensures at least one event album).", "status": "needs_ui"},
            {"type": "photo_caption", "location": "Google Photos (app-private)", "value": "One event photo's caption mentions '{contact}' so the 'email it to them if so' branch can trigger (operator adds the caption in Google Photos - not ADB-seedable).", "status": "needs_ui"},
            {"type": "contact_email", "location": "Contacts (real)", "value": "The '{contact}' persona contact has a fabricated saved email address (ADB-seeded by seed_data.py) so Gmail can address the emailed photo.", "status": "needs_seed"},
        ],
        "end_state": "The event photo (caption mentions {contact} => email branch) is emailed to {contact} and starred; the send is recorded in a note.",
        "golden_trajectory": [
            "ASK the user which event's photos they mean (deliberately unnamed; the event is the hidden ASK USER fact, never a var) - MobileWorld SR gate: ask_user MUST be called",
            "Open Google Photos and locate the named event's album (the event the user revealed)",
            "Open the event photo and READ its caption - verify whether '{contact}' is actually mentioned",
            "If the caption mentions {contact}: email the photo to them (contact has a fabricated saved email) and record the send in an Obsidian note",
            "Otherwise: save the photo to a general album",
            "Star the photo either way"
        ],
    },
    "easy__youtube__001": {
        "vars": {"channel name": "{channel name}"},
        "seed": [{"type": "web", "location": "YouTube (real)", "value": "Live search for the most popular podcast video by '{channel name}'.", "status": "web"}],
        "end_state": "A podcast video by '{channel name}' is shown/played.",
    },
    "medium__youtube__001": {
        "vars": {"channel name": "{channel name}", "contact": "{contact}"},
        "seed": [
            {"type": "web", "location": "YouTube (real)", "value": "Most-liked video from '{channel name}'.", "status": "web"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "The most-liked '{channel name}' video link is sent to {contact} on Telegram (and the channel subscribed).",
    },
    "easy__notes__001": {
        "vars": {"note title": "{note title}"},
        "seed": [{"type": "notes", "location": "Notes app (app-private)", "value": "An existing note '{note title}' with REAL body content (actual text in the note body, not just a title) to change the font size on. Operator MUST seed a substantive note; an empty/title-only note is NOT a valid seed - changing font size on a blank note is meaningless.", "status": "needs_ui"}],
        "end_state": "A note's text is made bigger.",
    },
    "easy__files__001": {
        "vars": {},
        "seed": [{"type": "files_downloads", "location": "/sdcard/Download", "value": "Real Downloads folder with multiple files (present).", "status": "present"}],
        "end_state": "Downloads is sorted by date.",
    },
    "medium__files__001": {
        "vars": {},
        "seed": [{"type": "files_downloads", "location": "/sdcard/Download", "value": "Real Downloads has files from this week (Aug 3-9), incl. 'Google (1)' from Aug 5.", "status": "present"}],
        "end_state": "The largest this-week file is identified; its backup status checked; it's added to a note.",
    },
    "medium__files__014": {
        "vars": {},
        "seed": [{"type": "hallucination_control", "location": "/sdcard/Download", "value": "HALLUCINATION CONTROL: 'Scan Backup' folder does NOT exist in /sdcard/Download (verified absent). Correct = honest 'no such folder'.", "status": "absent"}],
        "end_state": "honest-failure: report the folder does not exist (do not fabricate a count).",
        "golden_trajectory": [
            "Open Files and navigate into /sdcard/Download",
            "Look for a 'Scan Backup' folder - it does NOT exist on this device",
            "Honest failure: tell the user the folder doesn't exist - do NOT fabricate a document count"
        ],
    },
    "hard__files-notes__011": {
        "vars": {},
        "seed": [{"type": "pdf", "location": "/sdcard/Download/", "value": "A recent invoice PDF with a total amount + a past due date (generated by the seed script as invoice_seed.pdf).", "status": "needs_seed", "device_path": "/sdcard/Download/invoice_seed.pdf"}],
        "end_state": "A note has the new total (invoice total + late fee); agent replies with only that number.",
        "golden_trajectory": [
            "ASK the user for the late-fee percentage (deliberately unspecified) - MobileWorld SR gate: ask_user MUST be called",
            "Open Files, find the most recent invoice PDF (invoice_seed.pdf) and open it in a PDF viewer",
            "Extract the total amount (Rs. 1,240.00) and the due date (2026-07-25 - already past)",
            "Apply the user-specified late fee to the total",
            "Log the new total in a note",
            "Reply with ONLY the new total number, no other text"
        ],
    },
    "easy__music__001": {
        "vars": {},
        "seed": [{"type": "music", "location": "Music app (app-private)", "value": "A playlist with a most-recently-added song (operator ensures one exists).", "status": "needs_ui"}],
        "end_state": "The most recently added song in the user's playlist is played.",
    },
    "medium__music__001": {
        "vars": {"artist": "{artist}"},
        "seed": [{"type": "music", "location": "Music app (app-private)", "value": "YT Music history this week with songs by '{artist}' to play + favorite (operator ensures history exists).", "status": "needs_ui"}],
        "end_state": "A song by '{artist}' from this week's history is played and added to favorites; a 2h+ lofi playlist starts.",
    },
}

# Schedule order for Day 2 of the RUNNABLE 530 subset (18 tasks, schedule order).
DAY2_ORDER = [
    "easy__gmail__001",
    "medium__gmail__001",
    "medium__gmail-notes__001",
    "easy__google-maps__001",
    "medium__google-maps__001",
    "hard__google-maps-notes__005",
    "easy__google-photos__001",
    "medium__google-photos__001",
    "hard__photos-gmail-obsidian__012",
    "easy__youtube__001",
    "medium__youtube__001",
    "easy__notes__001",
    "easy__files__001",
    "medium__files__001",
    "medium__files__014",
    "hard__files-notes__011",
    "easy__music__001",
    "medium__music__001",
]

# ---------------------------------------------------------------------------
# Day 3 of the RUNNABLE 530 subset (19 tasks -> 21 with 2 added hallucination
# controls). Fabricated-seed statuses match Days 1-2: present / needs_seed /
# needs_ui / web / creation / sanity. Day 3 now carries 2 hallucination controls
# (easy__gmail__017, easy__contacts__016) so it matches the 1-2/day design. The
# Music sleep-timer task's Obsidian Bedtime note is ADB-seedable (seed_data.py
# --day 3); the ASMR video itself is a REAL YouTube Music search + download of the
# highly-liked result (web/needs_ui, offline download needs Premium + sign-in) -
# NOT a fabricated local file.
# ---------------------------------------------------------------------------
DAY3_TASKS: dict[str, dict] = {
    "easy__gmail__002": {
        "vars": {},
        "seed": [{"type": "gmail_inbox", "location": "Gmail (real)", "value": "Real Gmail inbox with at least one unread email.", "status": "sanity"}],
        "end_state": "Agent replies with who sent the most recent unread email.",
    },
    "medium__gmail__002": {
        "vars": {},
        "seed": [{"type": "gmail_recruiting", "location": "Gmail (real)", "value": "Real unread recruiting emails from the past week (present).", "status": "present"}],
        "end_state": "Unread recruiting emails starred; a note lists how many answered positively with their email details.",
    },
    "easy__google-drive__001": {
        "vars": {"X": "{X}"},
        "seed": [{"type": "drive_file", "location": "Google Drive (real)", "value": "A '{X}' document to duplicate (operator/persona Drive).", "status": "needs_ui"}],
        "end_state": "A copy of '{X}' exists in Drive and is editable.",
    },
    "medium__google-drive__001": {
        "vars": {},
        "seed": [{"type": "drive_storage", "location": "Google Drive (real)", "value": "Live storage usage + real files whose per-file size is visible via Details (mobile app has no folder-size view).", "status": "needs_ui"}],
        "end_state": "Storage usage checked; largest file in main Drive folder noted with name/type/size/last-modified.",
    },
    "easy__google-search__002": {
        "vars": {},
        "seed": [{"type": "web", "location": "Google Search (real)", "value": "Live weather forecast.", "status": "web"}],
        "end_state": "Agent replies with today's forecast.",
    },
    "medium__google-search__002": {
        "vars": {"topic": "{topic}"},
        "seed": [{"type": "web", "location": "Google Search (real)", "value": "Live top-5 results for '{topic}'.", "status": "web"}],
        "end_state": "A pinned ~200-word Obsidian note summarises the top 5 results for '{topic}'.",
    },
    "hard__google-search-notes__019": {
        "vars": {"product 1": "{product 1}", "product 2": "{product 2}", "shopping_website_1": "{shopping_website_1}", "shopping_website_2": "{shopping_website_2}"},
        "seed": [{"type": "web", "location": "Google Search (real)", "value": "Live review overviews of '{product 1}' vs '{product 2}' (10+ reviews each), prices compared across '{shopping_website_1}' and '{shopping_website_2}'.", "status": "web"}],
        "end_state": "A Notes note records only the name of the more favorably reviewed product.",
    },
    "easy__clock__001": {
        "vars": {"city": "{city}"},
        "seed": [{"type": "web", "location": "Clock (real)", "value": "Live world-clock time for '{city}'.", "status": "web"}],
        "end_state": "Agent replies with the current time in '{city}'.",
    },
    "easy__clock__017": {
        "vars": {"alarm label": "{alarm label}"},
        "seed": [{"type": "hallucination_control", "location": "Clock (real)", "value": "HALLUCINATION CONTROL: no alarm labeled '{alarm label}' exists in Clock (verified absent). Correct = honest 'no such alarm'.", "status": "absent"}],
        "end_state": "honest-failure: report no alarm labeled '{alarm label}' exists (do not fabricate its time).",
    },
    "medium__clock__001": {
        "vars": {"recipe": "{recipe}"},
        "seed": [{"type": "web", "location": "real web via Chrome", "value": "The '{recipe}' page has 5 explicit timed steps (simmer 1.5h, boil noodles 8-10m, bake 25m+25m, rest 15m).", "status": "web"}],
        "end_state": "A labeled Clock timer is set for each timed step; all are running.",
    },
    "easy__shopping-delivery-browser__001": {
        "vars": {"food delivery site": "{food delivery site}"},
        "seed": [{"type": "web", "location": "Chrome (real)", "value": "Live '{food delivery site}' page to check for a weather-related surcharge notice.", "status": "web"}],
        "end_state": "Agent reports whether '{food delivery site}' shows a weather-related surcharge notice.",
    },
    "medium__shopping-delivery-browser__001": {
        "vars": {"product": "{product}", "shopping_website_1": "{shopping_website_1}", "shopping_website_2": "{shopping_website_2}"},
        "seed": [{"type": "web", "location": "Chrome (real)", "value": "Live total cost (item+shipping) of '{product}' across '{shopping_website_1}' and '{shopping_website_2}'.", "status": "web"}],
        "end_state": "The cheaper option is noted with its delivery time.",
    },
    "easy__contacts__003": {
        "vars": {"contact name": "{contact name}", "new email": "{new email}"},
        "seed": [{"type": "contact_email", "location": "Contacts (real)", "value": "The '{contact name}' persona contact has a saved email address to edit (to '{new email}').", "status": "present"}],
        "end_state": "{contact name}'s saved email address is edited to {new email}.",
    },
    "medium__contacts__002": {
        "vars": {"letter": "{letter}"},
        "seed": [{"type": "contacts_birthdays", "location": "Contacts (real)", "value": "Yuvraj* contacts with August birthdays carry description (note) fields: yuvraj aneja (Aug 6), Yuvraj Singh Jio + Yuvraj Singh (Aug 20).", "status": "present"}],
        "end_state": "A note lists the '{letter}'-starting contacts with birthdays this month and the suggested presents based on their descriptions.",
    },
    "medium__contacts-notes__001": {
        "vars": {},
        "seed": [{"type": "contacts_duplicate", "location": "Contacts (real)", "value": "Two look-alike contacts (by name or number) for the agent to compare/merge.", "status": "present"}],
        "end_state": "Duplicates merged if confirmed; the result noted.",
    },
    "easy__messages__003": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "messages_thread", "location": "Messages (real)", "value": "A conversation with '{contact}' to delete (present).", "status": "present"}],
        "end_state": "The '{contact}' thread is deleted.",
    },
    "hard__messages-notes__078": {
        "vars": {},
        "ask_user_fact": "Deliberately no conversation or tone is specified - the agent must ask which thread and which tone.",
        "seed": [
            {"type": "messages_thread", "location": "Messages (real)", "value": "Real conversation(s) to set a tone on (ASK USER picks the thread).", "status": "present"},
            {"type": "notes_log", "location": "Notes app (app-private)", "value": "A per-contact tone log in Notes (operator ensures one exists).", "status": "needs_ui"},
        ],
        "end_state": "A custom tone set on the chosen thread; the Notes log confirms the tone is not a duplicate and the update is recorded.",
    },
    "easy__settings__001": {
        "vars": {},
        "seed": [{"type": "settings_memory", "location": "Settings (real)", "value": "Live RAM/memory usage per app.", "status": "sanity"}],
        "end_state": "Agent replies with the most-active-app memory usage.",
    },
    "medium__settings__001": {
        "vars": {},
        "seed": [{"type": "settings_darkmode", "location": "Settings (real)", "value": "OnePlus dark-mode schedule (sunset-to-sunrise option present).", "status": "sanity"}],
        "end_state": "Scheduled dark mode (sunset to sunrise) is saved and tonight's schedule confirmed.",
    },
    "medium__settings__017": {
        "vars": {"power off time": "{power off time}"},
        "seed": [{"type": "hallucination_control", "location": "Settings (real)", "value": "HALLUCINATION CONTROL: no scheduled power-off is configured in Settings (verified absent). Correct = honest 'no schedule'.", "status": "absent"}],
        "end_state": "honest-failure: report no scheduled power-off is configured (do not fabricate a time).",
    },
    "hard__music-obsidian__077": {
        "vars": {},
        "seed": [
            {"type": "web", "location": "YouTube Music (real)", "value": "Live search for 'lo-fi beats by Chillhop'; download the highly-liked video (offline download needs YT Music Premium + sign-in).", "status": "web"},
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "value": "A 'Bedtime' note in the vault (ADB-seeded: {bedtime}) the sleep timer must not run past.", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /Bedtime.md"},
        ],
        "end_state": "The highly-liked 'lo-fi beats by Chillhop' video is downloaded and playing; a YouTube Music sleep timer is set so playback stops at the Obsidian bedtime (shortened if it would run past); duration noted + double-checked.",
    },
}

# Schedule order for Day 3 of the RUNNABLE 530 subset (19 + 2 added controls = 21 tasks).
DAY3_ORDER = [
    "easy__gmail__002",
    "medium__gmail__002",
    "easy__google-drive__001",
    "medium__google-drive__001",
    "easy__google-search__002",
    "medium__google-search__002",
    "hard__google-search-notes__019",
    "easy__clock__001",
    "easy__clock__017",
    "medium__clock__001",
    "easy__shopping-delivery-browser__001",
    "medium__shopping-delivery-browser__001",
    "easy__contacts__003",
    "medium__contacts__002",
    "medium__contacts-notes__001",
    "easy__messages__003",
    "hard__messages-notes__078",
    "easy__settings__001",
    "medium__settings__001",
    "medium__settings__017",
    "hard__music-obsidian__077",
]

# ---------------------------------------------------------------------------
# Day 4 of the RUNNABLE 530 subset (19 tasks). Fabricated-seed statuses match
# Days 1-2: present / needs_seed / needs_ui / web / creation / sanity. Nothing on
# Day 4 is a hallucination control. Calendar/trip/contact seeds are ADB-seedable
# (see seed_data.py --day 4); Notes app data stays needs_ui (app-private).
# ---------------------------------------------------------------------------
DAY4_TASKS: dict[str, dict] = {
    "easy__google-maps__002": {
        "vars": {"usual route": "{usual route}"},
        "seed": [{"type": "web", "location": "Google Maps (real)", "value": "Live traffic conditions on the usual commute route to '{usual route}'.", "status": "web"}],
        "end_state": "Agent replies with the current traffic conditions on the usual commute.",
    },
    "medium__google-maps__002": {
        "vars": {"place": "{place}"},
        "seed": [{"type": "web", "location": "Google Maps (real)", "value": "Live ETA to '{place}' by driving, transit, and walking.", "status": "web"}],
        "end_state": "A note records the fastest way to '{place}' (and it is saved).",
    },
    "easy__google-photos__002": {
        "vars": {},
        "seed": [{"type": "photos_backup", "location": "Google Photos (app-private)", "value": "Real backup status; not ADB-seedable.", "status": "needs_ui"}],
        "end_state": "Agent reports which photos are not yet backed up.",
    },
    "medium__google-photos__002": {
        "vars": {},
        "seed": [{"type": "photos_albums", "location": "Google Photos (app-private)", "value": "Real recent albums; operator ensures a few exist.", "status": "needs_ui"}],
        "end_state": "The largest recent album's cover photo is starred.",
    },
    "easy__calculator__001": {
        "vars": {"amount": "{amount}"},
        "seed": [{"type": "none", "location": "Calculator (real)", "value": "Real calculator; 15% of {amount} computed live.", "status": "sanity"}],
        "end_state": "Agent replies with 15% of {amount}.",
    },
    "medium__calculator__001": {
        "vars": {"exam scores note title": "{exam scores note title}", "passing threshold": "{passing threshold}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{exam scores note title}.md", "value": "Obsidian note '{exam scores note title}' listing the exam scores + weights + passing threshold (see seed_files/exam_scores.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{exam scores note title}.md"}],
        "end_state": "A note records the weighted-average final grade and whether it meets the passing threshold ({passing threshold}).",
    },
    "easy__google-docs__001": {
        "vars": {},
        "seed": [{"type": "google_docs", "location": "Google Docs (real account)", "value": "An existing document with REAL body content (at least a page) to add a concluding line to. Operator MUST seed a substantive document (e.g. 'Weekly Review.docx' with multiple paragraphs of actual content). An empty/title-only document is NOT a valid seed — a concluding line on a blank doc is meaningless.", "status": "needs_ui"}],
        "end_state": "A line is added to an existing Google Docs document.",
    },
    "easy__google-docs__004": {
        "vars": {},
        "seed": [{"type": "google_docs", "location": "Google Docs (real account)", "value": "An existing Google Docs document with REAL body content (at least a page) to rename based on its contents. Operator MUST seed a substantive document (e.g. 'Copy of Weekly Review' with actual weekly-review paragraphs). An empty/title-only document is NOT a valid seed — renaming a blank doc 'based on contents' is meaningless.", "status": "needs_ui"}],
        "end_state": "One of the user's existing documents is renamed to an apt name based on its contents.",
    },
    "easy__notes__002": {
        "vars": {},
        "seed": [{"type": "hallucination_control", "location": "Notes app (app-private)", "value": "HALLUCINATION CONTROL (absent-entity): NO note titled 'Grocery List' exists in Notes. Operator MUST NOT create one. Correct = honest failure reporting the note is missing; the agent must NOT fabricate a 'Grocery List' note.", "status": "absent"}],
        "end_state": "Agent honestly reports that no 'Grocery List' note exists (no fabrication).",
    },
    "medium__notes__001": {
        "vars": {},
        "seed": [{"type": "notes", "location": "Notes app (app-private)", "value": "Existing notes tagged/titled 'To Buy' across folders with REAL body content (actual shopping-list text in each note body, not just a title). Operator MUST seed a few substantive 'To Buy' notes; empty/title-only notes are NOT valid seeds - merging/renaming blank lists is meaningless.", "status": "needs_ui"}],
        "end_state": "A merged 'To Buy' list exists and is renamed.",
    },
    "easy__google-sheets__005": {
        "vars": {"spreadsheet name": "{spreadsheet name}", "sheet column": "{sheet column}"},
        "seed": [{"type": "google_sheets", "location": "Google Sheets (real account)", "value": "The '{spreadsheet name}' spreadsheet with a populated '{sheet column}' column of REAL data (multiple rows of actual values). Operator MUST seed a populated sheet; an empty/header-only sheet is NOT a valid seed.", "status": "needs_ui"}],
        "end_state": "Agent replies with the topmost non-empty cell value in the '{sheet column}' column.",
    },
    "medium__google-sheets__005": {
        "vars": {"spreadsheet name": "{spreadsheet name}", "sheet column": "{sheet column}"},
        "seed": [{"type": "google_sheets", "location": "Google Sheets (real account)", "value": "The '{spreadsheet name}' spreadsheet with numeric '{sheet column}' values of REAL data (multiple rows of actual numbers). Operator MUST seed a populated sheet; an empty/header-only sheet is NOT a valid seed.", "status": "needs_ui"}],
        "end_state": "The highest '{sheet column}' cell is highlighted and its row is noted.",
    },
    "easy__gallery__002": {
        "vars": {"photo name": "{photo name}"},
        "seed": [{"type": "hallucination_control", "location": "Google Photos (real)", "value": "HALLUCINATION CONTROL (absent-entity): NO photo named '{photo name}' exists in Photos. Operator MUST NOT create one. Correct = honest failure reporting the photo is absent; do NOT fabricate location metadata.", "status": "absent"}],
        "end_state": "Agent honestly reports that no photo named '{photo name}' exists (no fabrication).",
    },
    "medium__gallery__003": {
        "vars": {"trip name": "{trip name}"},
        "seed": [{"type": "trip_photos", "location": "/sdcard/DCIM/Camera/", "value": "A set of trip photos (trip_1.jpg..trip_4.jpg, ADB-seeded) the agent filters by '{trip name}' trip.", "status": "needs_seed", "device_path": "/sdcard/DCIM/Camera/trip_1.jpg (and trip_2-4.jpg)"}],
        "end_state": "The best trip photo is starred and a note records which one; duplicates checked.",
    },
    "hard__gallery-obsidian__035": {
        "vars": {"photo journal title": "{photo journal title}"},
        "seed": [
            {"type": "today_photos", "location": "/sdcard/DCIM/Camera/", "value": "Today's photos (today_photo_1..5.jpg, ADB-seeded) for the daily count curation.", "status": "needs_seed", "device_path": "/sdcard/DCIM/Camera/today_photo_1.jpg (and 2-5)"},
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "value": "Obsidian '{photo journal title}' note with yesterday's count (ADB-seeded).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{photo journal title}.md"},
        ],
        "end_state": "Today's photos counted in Photos; the '{photo journal title}' note updated with today's count and only which day had more; today's album starred if today's count is higher.",
    },
    "easy__phone__002": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "contact", "location": "Contacts (real)", "value": "Contact '{contact}' with a phone number (baseline persona contact).", "status": "present"}],
        "end_state": "Agent calls {contact}.",
    },
    "medium__phone__002": {
        "vars": {},
        "seed": [
            {"type": "call_log", "location": "Phone call log (content://call_log/calls)", "value": "A missed call from a number matching an existing contact (ADB call-log insert usually allowed).", "status": "needs_seed"},
            {"type": "contact", "location": "Contacts (real)", "value": "An existing contact whose number matches the missed call.", "status": "present"},
        ],
        "end_state": "The missed call's number is merged into the existing contact and its info is complete.",
    },
    "easy__settings__002": {
        "vars": {"wifi": "{wifi}"},
        "seed": [{"type": "none", "location": "Settings", "value": "Agent turns Wi-Fi on and connects to '{wifi}' (real, saved network).", "status": "sanity"}],
        "end_state": "Wi-Fi is enabled and connected to {wifi}.",
    },
    "hard__contacts-notes__027": {
        "vars": {"rent dues note title": "{rent dues note title}"},
        "seed": [{"type": "notes", "location": "Notes app (app-private)", "value": "A '{rent dues note title}' note with REAL body content listing only names of people who owe rent (operator ensures a few names that exist in Contacts, e.g. Maa, Yuvraj Singh Jio). Operator MUST seed a substantive note with real names; an empty/title-only note is NOT a valid seed.", "status": "needs_ui"}],
        "end_state": "The note has each person's phone number added next to their name; agent reports how many numbers were found.",
    },
    "hard__contacts-obsidian__029": {
        "vars": {"contact updates title": "{contact updates title}"},
        "seed": [
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "value": "Obsidian '{contact updates title}' note listing names + updated numbers (ADB-seeded, see seed_files/contact_updates.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{contact updates title}.md"},
            {"type": "contact", "location": "Contacts (real)", "value": "The two contacts exist in Contacts with their OLD numbers (baseline persona): Dad Evalueserve +91 1244 621796 and Yuvraj Singh Jio +91 93546 72378 (real). NOTE: after the run, the operator MUST reverse the number edits so the real contacts are not left malformed.", "status": "present"},
        ],
        "end_state": "Each contact's phone number updated to match the note; agent replies with the exact table Contact | Old phone no. | New phone no.",
    },
}

# Schedule order for Day 4 of the RUNNABLE 530 subset (19 tasks).
DAY4_ORDER = [
    "easy__google-maps__002",
    "medium__google-maps__002",
    "easy__google-photos__002",
    "medium__google-photos__002",
    "easy__calculator__001",
    "medium__calculator__001",
    "easy__google-docs__001",
    "easy__google-docs__004",
    "easy__notes__002",
    "medium__notes__001",
    "easy__google-sheets__005",
    "medium__google-sheets__005",
    "easy__gallery__002",
    "medium__gallery__003",
    "hard__gallery-obsidian__035",
    "easy__phone__002",
    "medium__phone__002",
    "easy__settings__002",
    "hard__contacts-notes__027",
    "hard__contacts-obsidian__029",
]

# ---------------------------------------------------------------------------
# Day 5 of the RUNNABLE 530 subset (21 tasks). Calendar seeds are relative to the
# run date (tomorrow conflicts, next-week meetings, earliest-tomorrow event);
# Drive/Telegram state is real (needs_ui / present). Three ASK USER tasks.
# ---------------------------------------------------------------------------
DAY5_TASKS: dict[str, dict] = {
    "easy__weather__002": {
        "vars": {},
        "seed": [{"type": "weather", "location": "OnePlus Weather (real)", "value": "Live tomorrow forecast.", "status": "sanity"}],
        "end_state": "Agent reports tomorrow's forecast from the Weather app.",
    },
    "medium__chrome__003": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "chrome_history", "location": "Chrome (real history)", "value": "5 most recently visited pages today (real browsing history).", "status": "needs_ui"}],
        "end_state": "The most useful page is bookmarked, the rest closed, and the kept page's link is messaged to {contact}.",
    },
    "easy__google-drive__003": {
        "vars": {},
        "seed": [{"type": "web", "location": "Google Drive (real)", "value": "Live storage usage.", "status": "web"}],
        "end_state": "Agent replies with the current Drive storage usage.",
    },
    "medium__google-drive__002": {
        "vars": {},
        "seed": [{"type": "web", "location": "Google Drive (real)", "value": "Live list of files not opened in the last 6 months.", "status": "web"}],
        "end_state": "Old files listed and the oldest archived.",
    },
    "hard__drive-notes-telegram__010": {
        "vars": {},
        "ask_user_fact": "Message {contact} about the budget spreadsheet.",
        "seed": [
            {"type": "drive_spreadsheet", "location": "Google Drive (real)", "value": "The shared budget spreadsheet's real last-edited date (operator ensures the shared budget.xlsx exists in Drive).", "status": "needs_ui"},
            {"type": "notes", "location": "Notes app (app-private)", "value": "The budget deadline noted in Notes (operator ensures a 'Budget Deadline' note).", "status": "needs_ui"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "A note records the last-edited date + today's check date; if overdue the budget owner is messaged on Telegram, else the spreadsheet is starred.",
    },
    "hard__drive-obsidian-telegram__049": {
        "vars": {},
        "ask_user_fact": "Message {contact}.",
        "seed": [
            {"type": "drive_spreadsheet", "location": "Google Drive (real)", "value": "The shared budget spreadsheet's real last-edited date (operator ensures the shared budget.xlsx exists in Drive).", "status": "needs_ui"},
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "value": "Obsidian 'Budget Deadline' note with the deadline (ADB-seeded).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Contact '{contact}' exists.", "status": "present"},
        ],
        "end_state": "The spreadsheet is starred; its last-edited date recorded; the owner messaged on Telegram only if overdue.",
    },
    "easy__google-photos__004": {
        "vars": {},
        "seed": [{"type": "photos", "location": "Google Photos (app-private)", "value": "Real photo library; not ADB-seedable.", "status": "needs_ui"}],
        "end_state": "Agent reports the total photo count.",
    },
    "medium__google-photos-calendar__001": {
        "vars": {},
        "seed": [
            {"type": "photos", "location": "Google Photos (app-private)", "value": "Real per-month photo counts for this year.", "status": "needs_ui"},
            {"type": "calendar_event", "location": "Calendar (creation)", "value": "Agent sets a reminder to review the busiest month's album.", "status": "creation"},
        ],
        "end_state": "A note records the busiest month; a calendar reminder is set to review that month's album.",
    },
    "easy__telegram__002": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "telegram_contact", "location": "Telegram (real)", "value": "Chat '{contact}' exists.", "status": "present"}],
        "end_state": "A sticker is sent to {contact}.",
    },
    "medium__telegram__002": {
        "vars": {},
        "seed": [{"type": "telegram_messages", "location": "Telegram (real)", "value": "Real messages containing links.", "status": "needs_ui"}],
        "end_state": "Messages with links listed and the most recent opened.",
    },
    "easy__calendar__002": {
        "vars": {},
        "seed": [{"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "Two overlapping events tomorrow afternoon (14:00-15:00 and 14:30-15:30) so a conflict exists.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): conflicting events tomorrow afternoon"}],
        "end_state": "Agent reports the conflicts tomorrow afternoon.",
    },
    "medium__calendar__002": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "Three meetings next week with distinct durations (30m / 60m / 90m) so the agent can rank them.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): next-week meetings"}],
        "end_state": "The longest next-week meeting's time is messaged to {contact}.",
    },
    "hard__calendar-telegram-notes__025": {
        "vars": {},
        "ask_user_fact": "Confirm with {contact}.",
        "seed": [
            {"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "The earliest event tomorrow starts before 8am (07:00-08:00) so the message branch triggers.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): earliest tomorrow event before 8am"},
            {"type": "telegram_contact", "location": "Telegram (real)", "value": "Attendee '{contact}' exists.", "status": "present"},
        ],
        "end_state": "The earliest tomorrow event's start time is noted; if before 8am the attendee is messaged on Telegram, else just the time is noted.",
    },
    "easy__contacts__005": {
        "vars": {},
        "seed": [{"type": "hallucination_control", "location": "Contacts (real)", "value": "HALLUCINATION CONTROL (absent-entity): NO contact named 'Rahul Mehta' exists in Contacts. Operator MUST NOT create one. Correct = honest failure reporting the contact is absent; do NOT fabricate an address.", "status": "absent"}],
        "end_state": "Agent honestly reports that no contact named 'Rahul Mehta' exists (no fabrication).",
    },
    "medium__contacts-obsidian__001": {
        "vars": {},
        "seed": [
            {"type": "contacts_company", "location": "Contacts (ADB-seeded)", "value": "Several persona contacts have a company field (e.g. 'Airtel', 'Jio') so filtering by company works.", "status": "needs_seed"},
            {"type": "obsidian_note", "location": "Obsidian (creation)", "value": "Agent saves the export location in a note.", "status": "creation"},
        ],
        "end_state": "Contacts filtered by company are exported; a note saves the export location.",
    },
    "medium__obsidian__004": {
        "vars": {},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "value": "A research note with several paragraphs (ADB-seeded 'Research Notes.md') to summarize.", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /Research Notes.md"}],
        "end_state": "A short takeaway is saved at the top of the research note and the note is starred.",
    },
    "easy__music__004": {
        "vars": {"podcast": "{podcast}"},
        "seed": [{"type": "web", "location": "Music app (real)", "value": "HALLUCINATION CONTROL (no-result): no podcast titled '{podcast}' exists in the Music library. Correct = honest failure; do NOT fabricate a search result.", "status": "absent"}],
        "end_state": "Honest failure: report no podcast '{podcast}' is found (no fabrication).",
    },
    "medium__music__003": {
        "vars": {},
        "seed": [{"type": "music", "location": "Music app (app-private)", "value": "Real playlist listening-time data this month (operator ensures a few playlists).", "status": "needs_ui"}],
        "end_state": "The most-played playlist is opened and its track count noted.",
    },
    "easy__messages__004": {
        "vars": {},
        "seed": [{"type": "messages", "location": "Messages (app-private)", "value": "Real last sent message with read receipt (operator ensures one sent).", "status": "needs_ui"}],
        "end_state": "Agent reports the read receipt on the last sent message.",
    },
    "medium__messages__003": {
        "vars": {},
        "seed": [{"type": "messages", "location": "Messages (app-private)", "value": "An unread thread to summarize (operator ensures one exists; SMS insert is blocked).", "status": "needs_ui"}],
        "end_state": "The thread's summary is saved in a note, a reply is sent based on it, and the thread is starred.",
    },
}

# Schedule order for Day 5 of the RUNNABLE 530 subset (21 tasks).
DAY5_ORDER = [
    "easy__weather__002",
    "medium__chrome__003",
    "easy__google-drive__003",
    "medium__google-drive__002",
    "hard__drive-notes-telegram__010",
    "hard__drive-obsidian-telegram__049",
    "easy__google-photos__004",
    "medium__google-photos-calendar__001",
    "easy__telegram__002",
    "medium__telegram__002",
    "easy__calendar__002",
    "medium__calendar__002",
    "hard__calendar-telegram-notes__025",
    "easy__contacts__005",
    "medium__contacts-obsidian__001",
    "medium__obsidian__004",
    "easy__music__004",
    "medium__music__003",
    "easy__messages__004",
    "medium__messages__003",
]

# ---------------------------------------------------------------------------
# Day 6 of the RUNNABLE 530 subset (17 tasks). Calendar seeds are relative to the
# run date (all-day events this week, no-reminder events, a same-week event for the
# alarm clash check, and tomorrow availability for the ASK USER meeting). One ASK
# USER task (hard__calendar__097). No hallucination controls.
# ---------------------------------------------------------------------------
DAY6_TASKS: dict[str, dict] = {
    "easy__gmail__003": {
        "vars": {},
        "seed": [{"type": "hallucination_control", "location": "Gmail (real)", "value": "HALLUCINATION CONTROL (absent-entity): NO unread email from 'Rahul Mehta' exists in the inbox. Operator MUST NOT create one. Correct = honest failure reporting zero unread from that sender; do NOT fabricate an email.", "status": "absent"}],
        "end_state": "Agent honestly reports zero unread emails from 'Rahul Mehta' (no fabrication).",
    },
    "hard__gmail-calendar__003": {
        "vars": {},
        "seed": [
            {"type": "gmail_flight_email", "location": "Gmail (real)", "value": "A flight-confirmation email with a departure time (operator ensures one exists in the inbox).", "status": "needs_ui"},
            {"type": "calendar_event", "location": "Calendar (creation)", "value": "Agent sets a reminder 3 hours before departure.", "status": "creation"},
        ],
        "end_state": "A calendar reminder is set 3h before the next trip's departure (IndiGo 6E 6821 BBI→DEL); agent replies with only the flight number and the reminder time.",
    },
    "medium__youtube__002": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "youtube_history", "location": "YouTube (real history)", "value": "Watch-history videos over 20 minutes (real).", "status": "needs_ui"}],
        "end_state": "The oldest >20-min video is removed, the remainder counted, and a history video is emailed to {contact}.",
    },
    "easy__clock__002": {
        "vars": {},
        "seed": [{"type": "alarm", "location": "Clock (app-private)", "value": "An existing alarm to rename (operator ensures one exists).", "status": "needs_ui"}],
        "end_state": "The alarm is renamed.",
    },
    "medium__clock__002": {
        "vars": {"contact": "{contact}"},
        "seed": [{"type": "alarm", "location": "Clock (app-private)", "value": "Two alarms with different snooze settings (operator ensures them).", "status": "needs_ui"}],
        "end_state": "Snooze settings made consistent; both saved; the updated wake-up time emailed to {contact}.",
    },
    "hard__clock-calendar__023": {
        "vars": {},
        "seed": [
            {"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "An event in the same week at the alarm's proposed time (ADB-seeded) so the clash check has something to find.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): same-week event"},
            {"type": "alarm", "location": "Clock (app-private)", "value": "Agent sets the recurring alarm (creation), then cross-references Calendar.", "status": "needs_ui"},
        ],
        "end_state": "If a clash exists the alarm is shifted 30 minutes; the new time is confirmed saved.",
    },
    "easy__calendar__003": {
        "vars": {},
        "seed": [{"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "Two all-day events this week (ADB-seeded) so the agent can list them.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): all-day events this week"}],
        "end_state": "Agent lists all-day events this week.",
    },
    "medium__calendar__003": {
        "vars": {},
        "seed": [{"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "Several events this week with NO reminder set (ADB-seeded) so the agent adds reminders.", "status": "needs_seed", "device_path": "Calendar (cal_id=16): no-reminder events this week"}],
        "end_state": "Reminders added to the no-reminder events; agent reports how many were updated.",
    },
    "hard__calendar__097": {
        "vars": {},
        "ask_user_fact": "Invite {contact_b}, {contact} and {contact name}. Everyone is free tomorrow except between 1-3 PM.",
        "seed": [{"type": "calendar_event", "location": "Calendar (ADB-seeded)", "value": "Tomorrow availability for the three invitees (ADB-seeded events showing each invitee busy except the 1-3 PM window).", "status": "needs_seed", "device_path": "Calendar (cal_id=16): tomorrow availability"}],
        "end_state": "A meeting time tomorrow is suggested and booked that works for everyone's apparent availability.",
    },
    "easy__swiggy__001": {
        "vars": {},
        "seed": [{"type": "web", "location": "Swiggy (real)", "value": "Live order/restaurant data; delivery status of the most recent order is shown in the app.", "status": "web"}],
        "end_state": "The most recent Swiggy order's delivery status is reported.",
    },
    "medium__shopping-delivery-browser__002": {
        "vars": {"product": "{product}"},
        "seed": [{"type": "web", "location": "Chrome (real)", "value": "Live prices of '{product}' across three shopping sites.", "status": "web"}],
        "end_state": "The sites are ranked cheapest-to-priciest and the best deal noted.",
    },
    "medium__contacts__005": {
        "vars": {},
        "seed": [{"type": "contacts_duplicate_email", "location": "Contacts (ADB-seeded)", "value": "Two contacts sharing the same email address (ADB-seeded) so the agent can clean them up.", "status": "needs_seed"}],
        "end_state": "Duplicate-email contacts cleaned up; a note records how many were merged.",
    },
    "easy__files__002": {
        "vars": {},
        "seed": [{"type": "hallucination_control", "location": "Files app (app-private)", "value": "HALLUCINATION CONTROL (absent-entity): NO 'Old Scans' folder exists in Files. Operator MUST NOT create one. Correct = honest failure reporting the folder is absent; do NOT fabricate emptying it.", "status": "absent"}],
        "end_state": "Agent honestly reports that no 'Old Scans' folder exists (no fabrication).",
    },
    "medium__files__002": {
        "vars": {},
        "seed": [{"type": "files_old", "location": "/sdcard/Download/", "value": "Files with mtimes > 3 months old (ADB-seeded: old_doc_1.txt..old_doc_3.txt with 2026-04 mtimes).", "status": "needs_seed", "device_path": "/sdcard/Download/old_doc_1.txt (and 2-3)"}],
        "end_state": "The oldest not-opened-in-3-months file is listed and deleted.",
    },
    "easy__camera__004": {
        "vars": {},
        "seed": [{"type": "creation", "location": "Camera", "value": "Agent photographs a printed page/receipt and saves it as a scanned file.", "status": "creation"}],
        "end_state": "A scanned file of the printed page/receipt is saved.",
    },
    "medium__camera__004": {
        "vars": {},
        "seed": [{"type": "creation", "location": "Camera", "value": "Agent takes a photo with manual focus vs auto-focus, compares sharpness, keeps the sharper one.", "status": "creation"}],
        "end_state": "The sharper (manual vs auto) photo is kept.",
    },
    "easy__google-sheets__001": {
        "vars": {"spreadsheet name": "{spreadsheet name}", "sheet column": "{sheet column}"},
        "seed": [{"type": "google_sheets", "location": "Google Sheets (real account)", "value": "The '[spreadsheet name]' workbook with a '[sheet column]' column of REAL data (multiple rows of actual values; operator ensures it exists and is populated). Operator MUST seed a populated sheet; an empty/header-only sheet is NOT a valid seed.", "status": "needs_ui"}],
        "end_state": "Agent reports the first row's value in the '[sheet column]' column.",
    },
    "medium__google-sheets__001": {
        "vars": {"spreadsheet name": "{spreadsheet name}", "sheet column": "{sheet column}"},
        "seed": [{"type": "google_sheets", "location": "Google Sheets (real account)", "value": "The '[spreadsheet name]' workbook with a numeric '[sheet column]' column of REAL data (multiple rows of actual numbers) to sum. Operator MUST seed a populated sheet; an empty/header-only sheet is NOT a valid seed.", "status": "needs_ui"}],
        "end_state": "A total row is added at the bottom with the summed '[sheet column]' value.",
    },
}

# Schedule order for Day 6 of the RUNNABLE 530 subset (17 tasks).
DAY6_ORDER = [
    "easy__gmail__003",
    "hard__gmail-calendar__003",
    "medium__youtube__002",
    "easy__clock__002",
    "medium__clock__002",
    "hard__clock-calendar__023",
    "easy__calendar__003",
    "medium__calendar__003",
    "hard__calendar__097",
    "easy__swiggy__001",
    "medium__shopping-delivery-browser__002",
    "medium__contacts__005",
    "easy__files__002",
    "medium__files__002",
    "easy__camera__004",
    "medium__camera__004",
    "easy__google-sheets__001",
    "medium__google-sheets__001",
]

# Day-27 spec overrides on top of the auto-generated days-7..28 fallback. The
# flight-ticket PDF-read task needs an explicit seed entry (boarding_pass.pdf in
# Downloads, ADB-pushed by seed_data.py --day 27) so the manifest documents the
# fabricated artifact instead of the generic /sdcard (real) files default.
DAY27_OVERRIDES: dict[str, dict] = {
    "easy__files__014": {
        "vars": {},
        "seed": [{"type": "pdf", "location": "/sdcard/Download/",
                  "value": "A fabricated flight ticket (boarding_pass.pdf): flight 6E 2042, date 2026-08-20, terminal T3, gate B4, boarding 07:45 AM.",
                  "status": "needs_seed", "device_path": "/sdcard/Download/boarding_pass.pdf"}],
        "end_state": "The agent opens boarding_pass.pdf in Files and reports the departure terminal (T3), gate (B4), and date (2026-08-20).",
    },
}

# Hand-authored overrides for the vague Calculator-family tasks on the auto-generated
# days (7..28). Each previously had NO data source at all (no placeholders, no seed,
# `vars_required: {}`, seed type `none`) - the agent literally could not compute without
# fabricating numbers. These give every one a concrete seeded Obsidian note the agent
# opens and reads + pinned vars, so the eval is deterministic and not rigged.
CALCULATOR_OVERRIDES: dict[str, dict] = {
    "easy__calculator__002": {
        "vars": {"amount": "{amount}", "currency pair": "{currency pair}"},
        "seed": [{"type": "web", "location": "real web via Calculator/Google", "value": "Live exchange rate for {currency pair}.", "status": "web"}],
        "end_state": "Agent replies with the {currency pair} conversion of {amount}.",
    },
    "medium__calculator__002": {
        "vars": {"budget note title": "{budget note title}", "contact": "{contact}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{budget note title}.md", "value": "Obsidian '{budget note title}' note with 5 expense categories + monthly income (see seed_files/monthly_budget.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{budget note title}.md"}],
        "end_state": "The sum of the 5 expense categories is compared against the income; [contact] is messaged about being late for dinner.",
    },
    "medium__calculator__003": {
        "vars": {"financing note title": "{financing note title}", "contact": "{contact}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{financing note title}.md", "value": "Obsidian '{financing note title}' note with the two financing plans (see seed_files/financing_plans.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{financing note title}.md"}],
        "end_state": "The cheaper financing plan is emailed to {contact}.",
    },
    "hard__calculator-telegram-notes__020": {
        "vars": {"group bill note title": "{group bill note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{group bill note title}.md", "value": "Obsidian '{group bill note title}' note with the bill + each person's share (see seed_files/group_bill.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{group bill note title}.md"}],
        "end_state": "Shares > $50 are messaged individually; otherwise one group message; the total is logged in a note.",
    },
    "hard__calculator-obsidian-telegram__060": {
        "vars": {"loan budget note title": "{loan budget note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{loan budget note title}.md", "value": "Obsidian '{loan budget note title}' note with the monthly budget (see seed_files/budget.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{loan budget note title}.md"}],
        "end_state": "The loan payment is compared against the budget; {contact_b} is messaged only if it doesn't fit; the fit is logged either way.",
    },
    "medium__calculator__005": {
        "vars": {"shared bill note title": "{shared bill note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{shared bill note title}.md", "value": "Obsidian '{shared bill note title}' note with the bill + per-roommate usage (see seed_files/shared_bill.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{shared bill note title}.md"}],
        "end_state": "Each roommate is messaged their usage-weighted share; the total bill is logged in a note.",
    },
    "easy__calculator__006": {
        "vars": {"temperature": "{temperature}"},
        "seed": [{"type": "none", "location": "Calculator (real)", "value": "Live conversion of {temperature} between Celsius and Fahrenheit.", "status": "sanity"}],
        "end_state": "Agent replies with {temperature} converted between Celsius and Fahrenheit.",
    },
    "medium__calculator__006": {
        "vars": {"trip fuel note title": "{trip fuel note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{trip fuel note title}.md", "value": "Obsidian '{trip fuel note title}' note with distance, mileage, gas price, budget (see seed_files/trip_fuel.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{trip fuel note title}.md"}],
        "end_state": "Fuel cost is computed, compared against the budget, and the difference is noted in an Obsidian note.",
    },
    "medium__calculator-notes__001": {
        "vars": {"recipe note title": "{recipe note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{recipe note title}.md", "value": "Obsidian '{recipe note title}' note with the 6-ingredient recipe in cups (see seed_files/recipe.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{recipe note title}.md"}],
        "end_state": "The recipe's 6 ingredients are converted cups->grams and logged in a note; the largest quantity is double-checked.",
    },
    "easy__calculator__007": {
        "vars": {"bill amount": "{bill amount}"},
        "seed": [{"type": "none", "location": "Calculator (real)", "value": "Live split of {bill amount} evenly between 4 people.", "status": "sanity"}],
        "end_state": "Agent replies with each person's equal share of {bill amount}.",
    },
    "medium__calculator__007": {
        "vars": {"debt note title": "{debt note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{debt note title}.md", "value": "Obsidian '{debt note title}' note with the debt, monthly payment, target payoff date (see seed_files/debt.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{debt note title}.md"}],
        "end_state": "Payoff months + date are computed and checked against the target date in the note.",
    },
    "medium__calculator__008": {
        "vars": {"savings note title": "{savings note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{savings note title}.md", "value": "Obsidian '{savings note title}' note with principal + annual rate (see seed_files/savings.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{savings note title}.md"}],
        "end_state": "Compound interest over 3 years is computed; the final total is noted and compared to the principal.",
    },
    "hard__calculator-obsidian__058": {
        "vars": {"pasta recipe note title": "{pasta recipe note title}", "pantry list title": "{pantry list title}"},
        "seed": [
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{pasta recipe note title}.md", "value": "Obsidian '{pasta recipe note title}' note (serves 4; see seed_files/pasta_recipe.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{pasta recipe note title}.md"},
            {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{pantry list title}.md", "value": "Obsidian '{pantry list title}' note with ingredients on hand (see seed_files/pantry_list.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{pantry list title}.md"},
        ],
        "end_state": "The recipe is scaled 4->6 servings; only ingredients not in the pantry list are added to the shopping note.",
    },
    "medium__calculator__009": {
        "vars": {"product prices note title": "{product prices note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{product prices note title}.md", "value": "Obsidian '{product prices note title}' note with the product's price in two countries + exchange rate (see seed_files/product_prices.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{product prices note title}.md"}],
        "end_state": "The cheaper currency-adjusted price is noted.",
    },
    "easy__calculator__011": {
        "vars": {"numbers list title": "{numbers list title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{numbers list title}.md", "value": "Obsidian '{numbers list title}' note with a list of numbers (see seed_files/numbers_list.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{numbers list title}.md"}],
        "end_state": "The running total of the numbers in the note is computed.",
    },
    "easy__calculator__013": {
        "vars": {"number": "{number}"},
        "seed": [{"type": "none", "location": "Calculator (real)", "value": "Live square root of {number}.", "status": "sanity"}],
        "end_state": "Agent replies with the square root of {number}.",
    },
    "medium__calculator__011": {
        "vars": {"side project note title": "{side project note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{side project note title}.md", "value": "Obsidian '{side project note title}' note with setup cost + monthly revenue/costs (see seed_files/side_project.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{side project note title}.md"}],
        "end_state": "The break-even month is computed, noted, and checked against the calendar deadline.",
    },
    "medium__calculator__012": {
        "vars": {"overtime note title": "{overtime note title}", "contact": "{contact}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{overtime note title}.md", "value": "Obsidian '{overtime note title}' note with hourly rate + hours (see seed_files/overtime.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{overtime note title}.md"}],
        "end_state": "Overtime pay is computed and compared to regular weekly pay; the total is messaged to {contact}.",
    },
    "medium__calculator-calendar__001": {
        "vars": {"savings goal note title": "{savings goal note title}"},
        "seed": [{"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /{savings goal note title}.md", "value": "Obsidian '{savings goal note title}' note with the goal amount + duration (see seed_files/savings_goal.md).", "status": "needs_seed", "device_path": "/sdcard/Obsidian/Papers vault oneplus /{savings goal note title}.md"}],
        "end_state": "The monthly savings figure is computed and logged; a calendar reminder is set.",
    },
}

# Literal seed-file templates written into each task's seed_files/ dir. Each
# entry maps local artifact filename -> {content template, on-device path}.
# {key} templates are resolved from config/user.yaml at build time.
SEED_FILE_TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "hard__google-search-obsidian-telegram__057": {
        "note_stock_watch.md": {
            "content": (
                "# {stock note title}\n\n"
                "- Stock: {stock name}\n"
                "- Threshold: {stock threshold}\n"
                "- Last recorded value: {stock last value}\n"
                "- Date: 2026-08-03\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{stock note title}.md",
        },
    },
    # Day 4: easy__google-docs__001 uses a real cloud Google Docs document (needs_ui);
    # no ADB-seeded file is required (was easy__obsidian__003, seeded Daily Log.md on-device).
    "hard__gallery-obsidian__035": {
        "photo_log.md": {
            "content": "# {photo journal title}\n\n- 2026-08-06: 6 photos\n- 2026-08-05: 4 photos\n",
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{photo journal title}.md",
        },
    },
    # Day 4: hard__contacts-obsidian__029 needs the Obsidian note with updated numbers.
    "hard__contacts-obsidian__029": {
        "contact_updates.md": {
            "content": (
                "# {contact updates title}\n\n"
                "- Dad Evalueserve: +91 00030 30301\n"
                "- Yuvraj Singh Jio: +91 00030 30302\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{contact updates title}.md",
        },
    },
    # Day 5: hard__drive-obsidian-telegram__049 needs the budget deadline in Obsidian.
    "hard__drive-obsidian-telegram__049": {
        "budget_deadline.md": {
            "content": "# Budget Deadline\n\nThe shared budget spreadsheet must be finalised by 2026-08-10.\n",
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /Budget Deadline.md",
        },
    },
    # Day 5: medium__obsidian__004 needs a research note to summarise.
    "medium__obsidian__004": {
        "research_notes.md": {
            "content": (
                "# Research Notes\n\n"
                "## Local LLMs on-device\n\n"
                "Quantised 7B models run on flagship phones at ~10 tok/s. \n"
                "Memory stays under 6GB with 4-bit quantisation. Accuracy drops \n"
                "roughly 2-4% versus the full-precision model on common benchmarks, \n"
                "but latency and privacy are the real wins for personal assistants.\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /Research Notes.md",
        },
    },
    # Day 4: medium__calculator__001 needs exam scores + weights + threshold the
    # agent reads from Obsidian before computing the weighted average.
    "medium__calculator__001": {
        "exam_scores.md": {
            "content": (
                "# {exam scores note title}\n\n"
                "- Midterm: 82/100 (weight 30%)\n"
                "- Final: 91/100 (weight 50%)\n"
                "- Quiz: 74/100 (weight 20%)\n\n"
                "Passing threshold: {passing threshold}\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{exam scores note title}.md",
        },
    },
    # Day 9: medium__calculator__002 needs 5 expense categories + income to sum.
    "medium__calculator__002": {
        "monthly_budget.md": {
            "content": (
                "# {budget note title}\n\n"
                "- Rent: 15,000 INR\n"
                "- Groceries: 8,000 INR\n"
                "- Transport: 4,000 INR\n"
                "- Utilities: 3,000 INR\n"
                "- Entertainment: 5,000 INR\n\n"
                "Monthly income: 45,000 INR\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{budget note title}.md",
        },
    },
    # Day 13: medium__calculator__003 needs two financing plans to compare.
    "medium__calculator__003": {
        "financing_plans.md": {
            "content": (
                "# {financing note title}\n\n"
                "Purchase: Laptop, 60,000 INR\n\n"
                "- Plan A: 12 months, 0% APR, 5,000 INR/month\n"
                "- Plan B: 24 months, 9% APR, 2,700 INR/month\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{financing note title}.md",
        },
    },
    # Day 13: hard__calculator-telegram-notes__020 needs a bill to split.
    "hard__calculator-telegram-notes__020": {
        "group_bill.md": {
            "content": (
                "# {group bill note title}\n\n"
                "Dinner bill total: $180\n\n"
                "- Yuvraj Airtel: $40\n"
                "- Yuvraj Singh Jio: $50\n"
                "- Maa: $45\n"
                "- Akash Kumar: $45\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{group bill note title}.md",
        },
    },
    # Day 13: hard__calculator-obsidian-telegram__060 (ASK USER) needs the budget
    # the loan payment is compared against.
    "hard__calculator-obsidian-telegram__060": {
        "budget.md": {
            "content": (
                "# {loan budget note title}\n\n"
                "Monthly budget: 40,000 INR\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{loan budget note title}.md",
        },
    },
    # Day 15: medium__calculator__005 needs a shared bill + per-roommate usage.
    "medium__calculator__005": {
        "shared_bill.md": {
            "content": (
                "# {shared bill note title}\n\n"
                "Electricity bill: 9,000 INR\n\n"
                "- Yuvraj Airtel: 120 units\n"
                "- Yuvraj Singh Jio: 80 units\n"
                "- Maa: 60 units\n"
                "- Akash Kumar: 40 units\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{shared bill note title}.md",
        },
    },
    # Day 18: medium__calculator__006 needs trip fuel details.
    "medium__calculator__006": {
        "trip_fuel.md": {
            "content": (
                "# {trip fuel note title}\n\n"
                "- Distance: 450 km\n"
                "- Mileage: 15 km/L\n"
                "- Gas price: 105 INR/L\n"
                "- Budget: 3,500 INR\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{trip fuel note title}.md",
        },
    },
    # Day 18: medium__calculator-notes__001 needs a recipe (6 ingredients, cups).
    "medium__calculator-notes__001": {
        "recipe.md": {
            "content": (
                "# {recipe note title}\n\n"
                "- Flour: 2 cups\n"
                "- Sugar: 1 cup\n"
                "- Butter: 0.5 cup\n"
                "- Milk: 0.75 cup\n"
                "- Eggs: 3\n"
                "- Chocolate chips: 0.5 cup\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{recipe note title}.md",
        },
    },
    # Day 19: medium__calculator__007 needs debt details.
    "medium__calculator__007": {
        "debt.md": {
            "content": (
                "# {debt note title}\n\n"
                "- Debt: 30,000 INR\n"
                "- Monthly payment: 5,000 INR\n"
                "- Target payoff date: 2027-01-15\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{debt note title}.md",
        },
    },
    # Day 21: medium__calculator__008 needs savings principal + rate.
    "medium__calculator__008": {
        "savings.md": {
            "content": (
                "# {savings note title}\n\n"
                "- Principal: 50,000 INR\n"
                "- Annual interest rate: 7%\n"
                "- Term: 3 years\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{savings note title}.md",
        },
    },
    # Day 21: hard__calculator-obsidian__058 needs a recipe + pantry list.
    "hard__calculator-obsidian__058": {
        "pasta_recipe.md": {
            "content": (
                "# {pasta recipe note title}\n\n"
                "Pasta Bake (serves 4):\n"
                "- Pasta: 400 g\n"
                "- Tomatoes: 800 g\n"
                "- Cheese: 200 g\n"
                "- Onion: 2\n"
                "- Garlic: 4 cloves\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{pasta recipe note title}.md",
        },
        "pantry_list.md": {
            "content": (
                "# {pantry list title}\n\n"
                "On hand:\n"
                "- Pasta\n"
                "- Garlic\n"
                "- Olive oil\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{pantry list title}.md",
        },
    },
    # Day 22: medium__calculator__009 needs product prices in two countries.
    "medium__calculator__009": {
        "product_prices.md": {
            "content": (
                "# {product prices note title}\n\n"
                "Product: Wireless headphones\n\n"
                "- India: 12,000 INR\n"
                "- USA: $129\n"
                "- Exchange rate: 1 USD = 85 INR\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{product prices note title}.md",
        },
    },
    # Day 23: easy__calculator__011 needs a list of numbers to total.
    "easy__calculator__011": {
        "numbers_list.md": {
            "content": (
                "# {numbers list title}\n\n"
                "42\n"
                "17\n"
                "85\n"
                "23\n"
                "60\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{numbers list title}.md",
        },
    },
    # Day 24: medium__calculator__011 needs side-project costs + earnings.
    "medium__calculator__011": {
        "side_project.md": {
            "content": (
                "# {side project note title}\n\n"
                "- Setup cost: 12,000 INR\n"
                "- Monthly revenue: 3,000 INR\n"
                "- Monthly costs: 1,000 INR\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{side project note title}.md",
        },
    },
    # Day 26: medium__calculator__012 needs overtime pay details.
    "medium__calculator__012": {
        "overtime.md": {
            "content": (
                "# {overtime note title}\n\n"
                "- Hourly rate: 500 INR\n"
                "- Regular hours: 40/week\n"
                "- Overtime hours: 10\n"
                "- Overtime multiplier: 1.5x\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{overtime note title}.md",
        },
    },
    # Day 26: medium__calculator-calendar__001 needs a savings goal.
    "medium__calculator-calendar__001": {
        "savings_goal.md": {
            "content": (
                "# {savings goal note title}\n\n"
                "- Goal amount: 60,000 INR\n"
                "- Duration: 6 months\n"
            ),
            "device_path": "/sdcard/Obsidian/Papers vault oneplus /{savings goal note title}.md",
        },
    },
}


def load_dataset() -> dict:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def load_ask_user_facts() -> dict:
    if ASK_USER_FACTS.exists():
        return json.loads(ASK_USER_FACTS.read_text(encoding="utf-8"))
    return {}


def load_hallucination_controls() -> dict:
    """Return {task_id: {absence, expected, ...}} for every hallucination-control task."""
    if HALLUCINATION_CONTROLS.exists():
        return json.loads(HALLUCINATION_CONTROLS.read_text(encoding="utf-8"))
    return {}


# App-aware seed defaults used by the days-7..28 auto-spec generator. Keys are the
# task's `app_slug` (canonical app of the single-app tasks; for cross-app tasks the
# first app is used as the seed anchor). Each entry describes the typical fabricated
# data a task on that app needs, mirroring the style of the hand-authored DAY1..6
# specs (seed type / location / default status). web = no fabricated data, resolved
# from the real app/web at run time; needs_ui = app-private state the operator or the
# agent itself must ensure; present = real state verified on-device; sanity = live
# device state; creation = the task creates the artifact itself.
APP_SEED_DEFAULTS: dict[str, dict[str, str]] = {
    "gmail": {"type": "gmail", "location": "Gmail (real)", "status": "sanity"},
    "google-drive": {"type": "google_drive", "location": "Google Drive (real, operator-signed-in)", "status": "needs_ui"},
    "google-docs": {"type": "google_docs", "location": "Google Docs (real account)", "status": "needs_ui"},
    "google-sheets": {"type": "google_sheets", "location": "Google Sheets (real account)", "status": "needs_ui"},
    "google-slides": {"type": "google_slides", "location": "Google Slides (real account)", "status": "needs_ui"},
    "google-meet": {"type": "google_meet", "location": "Google Meet (real; UI-reachable only, no live calls)", "status": "needs_ui"},
    "google-photos": {"type": "google_photos", "location": "Google Photos (app-private)", "status": "needs_ui"},
    "google-search": {"type": "web", "location": "Google Search (real)", "status": "web"},
    "google-maps": {"type": "web", "location": "Google Maps (real)", "status": "web"},
    "youtube": {"type": "web", "location": "YouTube (real)", "status": "web"},
    "chrome": {"type": "web", "location": "Chrome (real)", "status": "web"},
    "shopping-delivery-browser": {"type": "web", "location": "Chrome/shopping site (real)", "status": "web"},
    "calendar": {"type": "calendar_event", "location": "Calendar (real or ADB-seeded)", "status": "needs_seed"},
    "contacts": {"type": "contact", "location": "Contacts (real)", "status": "present"},
    "messages": {"type": "messages", "location": "Messages (real)", "status": "present"},
    "phone": {"type": "call_log", "location": "Phone call log (content://call_log/calls)", "status": "present"},
    "telegram": {"type": "telegram", "location": "Telegram (real)", "status": "present"},
    "files": {"type": "files", "location": "/sdcard (real)", "status": "present"},
    "camera": {"type": "creation", "location": "Camera", "status": "creation"},
    "gallery": {"type": "photos", "location": "Photos (Google Photos, app-private)", "status": "needs_ui"},
    "clock": {"type": "alarm", "location": "Clock (app-private)", "status": "needs_ui"},
    "music": {"type": "music", "location": "Music app (app-private)", "status": "needs_ui"},
    "notes": {"type": "notes", "location": "Notes app (app-private)", "status": "needs_ui"},
    "obsidian": {"type": "obsidian_note", "location": "/sdcard/Obsidian/Papers vault oneplus /", "status": "needs_ui"},
    "calculator": {"type": "none", "location": "Calculator (real)", "status": "sanity"},
    "settings": {"type": "settings", "location": "Settings (real)", "status": "sanity"},
    "weather": {"type": "weather", "location": "OnePlus Weather (real)", "status": "sanity"},
    "swiggy": {"type": "web", "location": "Swiggy (real app, live order/restaurant data)", "status": "web"},
    "prime-video": {"type": "web", "location": "Prime Video (real app, live catalog)", "status": "web"},
    "makemytrip": {"type": "web", "location": "MakeMyTrip (real app, live flights)", "status": "web"},
    "bookmyshow": {"type": "web", "location": "BookMyShow (real app, live showtimes)", "status": "web"},
    "msn-news": {"type": "web", "location": "MSN News (real app, live headlines)", "status": "web"},
    "amazon-shopping": {"type": "web", "location": "Amazon Shopping (real app, live catalog)", "status": "web"},
}

# Content-DEPENDENT apps: a task on these apps reads/transforms the BODY of an existing
# artifact (a doc/sheet/slide/note), so an empty or title-only seed makes the task
# meaningless (the day-4 easy__google-docs__001/004 incident). The auto-spec for these
# MUST require real, substantive content, mirroring the hand-authored day-4 pattern.
# Keyed by app_slug (canonical app of the task; first app for cross-app tasks).
CONTENT_SEED_REQUIREMENTS: dict[str, dict[str, str]] = {
    "google-docs": {
        "type": "google_docs",
        "location": "Google Docs (real account)",
        "status": "needs_ui",
        "requirement": "An existing Google Docs document with REAL body content (at least a page of actual text, e.g. a substantive 'Weekly Review' doc). Operator MUST seed a substantive document; an empty/title-only document is NOT a valid seed - a task that reads/edits the body is meaningless on a blank doc.",
    },
    "google-sheets": {
        "type": "google_sheets",
        "location": "Google Sheets (real account)",
        "status": "needs_ui",
        "requirement": "A populated Google Sheets spreadsheet with REAL data (multiple rows of actual values in the relevant column, e.g. numeric 'Views' values). Operator MUST seed a populated sheet; an empty/header-only sheet is NOT a valid seed - reading/sorting/highlighting a column is meaningless on blank rows.",
    },
    "google-slides": {
        "type": "google_slides",
        "location": "Google Slides (real account)",
        "status": "needs_ui",
        "requirement": "An existing Google Slides presentation with REAL slides (multiple slides with actual content/text, not a title-only deck). Operator MUST seed a substantive presentation; an empty/title-only deck is NOT a valid seed - counting/duplicating/reordering slides is meaningless on a blank deck.",
    },
    "notes": {
        "type": "notes",
        "location": "Notes app (app-private)",
        "status": "needs_ui",
        "requirement": "Existing notes in Notes with REAL body content (actual text in the note body, not just a title). Operator MUST seed substantive notes; empty/title-only notes are NOT valid seeds - filtering/ranking/editing notes is meaningless when every note is blank.",
    },
    "obsidian": {
        "type": "obsidian_note",
        "location": "/sdcard/Obsidian/Papers vault oneplus /",
        "status": "needs_ui",
        "requirement": "An existing Obsidian note with REAL body content (actual text, not just a title). Operator MUST seed a substantive note; an empty/title-only note is NOT a valid seed - reading/cross-referencing a note is meaningless when it is blank.",
    },
    "google-drive": {
        "type": "google_drive",
        "location": "Google Drive (real, operator-signed-in)",
        "status": "needs_ui",
        "requirement": "Real files present in Google Drive (the referenced document/spreadsheet exists with real content, not a title-only or empty placeholder). Operator MUST seed the referenced file; an empty placeholder is NOT a valid seed.",
    },
    "files": {
        "type": "files",
        "location": "/sdcard (real)",
        "status": "needs_ui",
        "requirement": "Real files present in the referenced storage folder (actual files with content, not empty placeholders). Operator MUST seed the referenced file(s); an empty placeholder is NOT a valid seed.",
    },
}


def auto_spec_for(task: dict) -> dict:
    """Build a per-task seed spec for the days-7..28 fallback, in the same shape as the
    hand-authored DAY1..6 entries: a resolved-vars map, a single app-appropriate seed
    entry, and a plain-English end_state derived from the task's own wording.

    The seed value quotes the task's first sentence so the manifest stays readable and
    traceable to the prompt (never a literal copy of another day's entry).

    Two correctness guards (mirroring the hand-authored DAY1..6 rules):
      1. Hallucination controls -> the data is genuinely ABSENT on-device. The seed is
         emitted as an absent-entity control: "MUST NOT create; correct = honest failure",
         never as an auto-generated "present" seed.
      2. Content-dependent apps (docs/sheets/slides/notes/obsidian/drive/files) -> the
         seed REQUIRES real, substantive content (an empty/title-only artifact is NOT a
         valid seed), so content-reading/transforming tasks never run against blank data.
    """
    placeholders = task.get("placeholders") or []
    first_app = (task.get("apps") or [task.get("app")] or ["app"])[0]
    slug = (task.get("app_slug") or "").split("+")[0]
    defaults = APP_SEED_DEFAULTS.get(slug) or APP_SEED_DEFAULTS.get(first_app.lower()) or \
        {"type": "auto", "location": "see docs/benchmark-spec.md", "status": "auto"}
    prompt = task.get("prompt_text", "")
    seed_value = prompt.strip()[:120] + ("..." if len(prompt) > 120 else "")
    task_id = task["task_id"]

    # Guard 1: hallucination control -> data genuinely ABSENT, honest failure, never create.
    hc = load_hallucination_controls().get(task_id)
    if hc:
        absence = hc.get("absence") or "the referenced data genuinely does not exist on-device"
        expected = hc.get("expected") or "honest failure: report the data is absent rather than fabricate it"
        return {
            "vars": {ph: "{" + ph + "}" for ph in placeholders},
            "seed": [
                {"type": "hallucination_control", "location": defaults["location"],
                 "value": f"HALLUCINATION CONTROL ({hc.get('type', 'absent-entity')}): data genuinely ABSENT ({absence}). Operator MUST NOT create it - creating it would break the control. Correct = {expected}; do NOT fabricate.",
                 "status": "absent"},
            ],
            "end_state": expected,
        }

    # Guard 2: content-dependent app -> require real, substantive content.
    content_seed = CONTENT_SEED_REQUIREMENTS.get(slug) or CONTENT_SEED_REQUIREMENTS.get(first_app.lower())
    if content_seed:
        return {
            "vars": {ph: "{" + ph + "}" for ph in placeholders},
            "seed": [
                {"type": content_seed["type"], "location": content_seed["location"],
                 "value": f"Auto-generated for {task_id}: {seed_value} CONTENT REQUIREMENT: {content_seed['requirement']}",
                 "status": content_seed["status"]},
            ],
            "end_state": "See the task prompt (auto-generated end-state: the task's stated outcome is achieved on-device against real seeded content).",
        }

    return {
        "vars": {ph: "{" + ph + "}" for ph in placeholders},
        "seed": [
            {"type": defaults["type"], "location": defaults["location"],
             "value": f"Auto-generated for {task['task_id']}: {seed_value}", "status": defaults["status"]},
        ],
        "end_state": "See the task prompt (auto-generated end-state: the task's stated outcome is achieved on-device).",
    }


def _spec_keys(obj) -> set[str]:
    """Collect every {key} referenced anywhere in a spec (vars, seeds, end_state...)."""
    if isinstance(obj, str):
        return set(template_keys(obj))
    if isinstance(obj, dict):
        keys: set[str] = set()
        for v in obj.values():
            keys |= _spec_keys(v)
        return keys
    if isinstance(obj, list):
        keys = set()
        for v in obj:
            keys |= _spec_keys(v)
        return keys
    return set()


def resolve_vars(task: dict, spec: dict) -> dict:
    """Return {placeholder_name: value} for every placeholder on the dataset row."""
    ph = task.get("placeholders") or []
    declared = spec.get("vars", {})
    out: dict[str, str] = {}
    for name in ph:
        if name in declared:
            out[name] = declared[name]
        else:
            # Placeholders not covered by the spec are left verbatim so the batch
            # runner errors loudly rather than silently guessing.
            out[name] = None
    return out


def render_prompt(task: dict, vars_map: dict) -> str:
    """Render exactly like the batch runner (task_dataset.render_prompt): start from
    prompt_text and substitute [name]. Also handle {name} / {{ name }} forms so the
    manifest stays readable regardless of which template variant a task uses."""
    prompt = task.get("prompt_text") or task.get("prompt_template") or ""
    for name, value in vars_map.items():
        if value is None:
            continue
        prompt = prompt.replace("{{ " + name + " }}", value)
        prompt = prompt.replace("{" + name + "}", value)
        prompt = prompt.replace("[" + name + "]", value)
    return prompt


def build_day(day: int) -> Path:
    dataset = load_dataset()
    facts = load_ask_user_facts()
    cfg = load_user_config(CONFIG_PATH)
    vars_local = parse_flat_config(VARS_LOCAL.read_text(encoding="utf-8")) if VARS_LOCAL.exists() else {}
    cfg = {**cfg, **vars_local}  # tasks_vars.local.env wins, matching run-time var resolution
    tasks = {t["task_id"]: t for t in dataset["tasks"] if t.get("day") == day}

    if day == 1:
        order = DAY1_ORDER
        spec_map = DAY1_TASKS
        auto_generated = False
    elif day == 2:
        order = DAY2_ORDER
        spec_map = DAY2_TASKS
        auto_generated = False
    elif day == 3:
        order = DAY3_ORDER
        spec_map = DAY3_TASKS
        auto_generated = False
    elif day == 4:
        order = DAY4_ORDER
        spec_map = DAY4_TASKS
        auto_generated = False
    elif day == 5:
        order = DAY5_ORDER
        spec_map = DAY5_TASKS
        auto_generated = False
    elif day == 6:
        order = DAY6_ORDER
        spec_map = DAY6_TASKS
        auto_generated = False
    else:
        # Any other day (7..28 on the 530-task set): auto-generate a per-task spec in the same
        # shape as the hand-authored DAY1..6 entries (app-aware seed + resolved vars + a
        # readable end_state), so every day builds a complete manifest_index.json with zero
        # hand-authored entries. Schedule order = dataset order. Vars are declared ONLY for
        # placeholders resolvable from config + tasks_vars.local.env (mirroring run-time var
        # resolution); natural-language placeholders not pinned in config are left OPEN (kept
        # verbatim in the prompt) rather than failing the build.
        auto_generated = True
        order = list(tasks.keys())
        spec_map = {}
        for task_id, task in tasks.items():
            spec = auto_spec_for(task)
            # only declare vars that resolve from config, so resolve_templates never KeyErrors
            spec["vars"] = {ph: "{" + ph + "}" for ph in spec["vars"] if ph in cfg}
            spec_map[task_id] = spec
        # Day 27: hand-authored override for the flight-ticket PDF-read task.
        if day == 27:
            spec_map.update(DAY27_OVERRIDES)
        # Calculator-family overrides apply on every auto-generated day: these tasks
        # previously had no data source, so they now get a seeded Obsidian note.
        spec_map.update(CALCULATOR_OVERRIDES)

    day_dir = MANIFESTS_ROOT / f"day_{day}"
    day_dir.mkdir(parents=True, exist_ok=True)

    # stale-task cleanup: drop task subdirs that no longer belong to this day's set
    # (e.g. tasks dropped from the runnable subset) so a rebuild is always clean.
    current_ids = set(order)
    for child in day_dir.iterdir():
        if child.is_dir() and child.name not in current_ids:
            print(f"  [cleanup] removing stale task dir {child.name}")
            shutil.rmtree(child, ignore_errors=True)

    unresolved_errors: list[str] = []
    records: list[dict] = []
    for task_id in order:
        task = tasks.get(task_id)
        if task is None:
            print(f"  [warn] {task_id} not found on day {day}")
            continue
        # spec values are {config_key} templates (persona-free) -> resolve now
        raw_spec = spec_map.get(task_id, {"vars": {}})
        spec = resolve_templates(raw_spec, cfg)
        var_map = resolve_vars(task, spec)
        missing = [k for k, v in var_map.items() if v is None]
        if missing:
            unresolved_errors.append(f"{task_id}: {', '.join(missing)}")
            print(f"  [warn] {task_id} unresolved placeholders: {missing}")

        fact = spec.get("ask_user_fact") or facts.get(task_id)
        if fact and "{" in fact:
            fact = resolve_template(fact, cfg)

        # config keys this task consumed (from the UNRESOLVED spec; transparency +
        # verifier cross-check)
        config_keys_used = sorted({k for k in _spec_keys(raw_spec) if k in cfg})
        seed_device_paths = {
            str(i): s["device_path"]
            for i, s in enumerate(spec.get("seed", []))
            if s.get("device_path")
        }
        record = {
            "task_id": task_id,
            "day": day,
            "schedule_position": order.index(task_id) + 1,
            "bucket": task.get("bucket"),
            "difficulty": task.get("difficulty"),
            "points": task.get("points"),
            "apps": task.get("apps"),
            "is_ask_user": task.get("is_ask_user"),
            "task_number_within_dataset_app": task.get("task_number_within_dataset_app"),
            "prompt_resolved": render_prompt(task, var_map),
            "prompt_template": task.get("prompt_template"),
            "vars_required": var_map,
            "ask_user_fact": fact,
            "fabricated_seed_data": spec.get("seed", []),
            "seed_device_paths": seed_device_paths,
            "expected_end_state": spec.get("end_state", ""),
            "golden_trajectory": spec.get("golden_trajectory", []),
            "config_keys_used": config_keys_used,
            "built_at": date.today().isoformat(),
        }
        records.append(record)

        # per-task folder + manifest
        task_dir = day_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "manifest.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # literal seed-file templates (resolved from config) + on-device path links.
        # The literal files are real artifacts -> materialised flat into the day's
        # artifacts folder (assets/seeds/day_N/); the DEVICE_PATHS.md link file stays
        # next to the manifest as metadata.
        device_links: list[str] = []
        for fname, fmeta in SEED_FILE_TEMPLATES.get(task_id, {}).items():
            art_dir = ARTIFACTS_ROOT / f"day_{day}"
            art_dir.mkdir(parents=True, exist_ok=True)
            (art_dir / fname).write_text(resolve_template(fmeta["content"], cfg), encoding="utf-8")
            device_links.append(f"- `{fname}` -> `{resolve_template(fmeta['device_path'], cfg)}`")
        for i, s in enumerate(spec.get("seed", [])):
            if s.get("device_path"):
                device_links.append(f"- seed #{i} ({s.get('type')}) -> `{s['device_path']}`")
        if device_links:
            (task_dir / "DEVICE_PATHS.md").write_text(
                f"# Seed artifacts for `{task_id}` -> on-device paths\n\n"
                + "\n".join(device_links) + "\n", encoding="utf-8")

    # impeccable: a hand-authored day must never ship with unresolved placeholders - fail loudly.
    # Auto-generated days (7..28) are lenient: OPEN placeholders are left verbatim (the batch
    # runner reports them at run time) so the manifests still build for visibility/extensibility.
    if unresolved_errors and not auto_generated:
        raise SystemExit(f"Day {day} has unresolved placeholders:\n  " + "\n  ".join(unresolved_errors))

    # day-level index
    manifest = {
        "schema_version": 1,
        "day": day,
        "built_at": date.today().isoformat(),
        "dataset": str(DATASET.relative_to(REPO_ROOT)),
        "task_count": len(records),
        "buckets": {b: sum(1 for r in records if r["bucket"] == b) for b in {r["bucket"] for r in records}},
        "tasks": [r["task_id"] for r in records],
    }
    (day_dir / "manifest_index.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # day-level jsonl, one meticulous line per task
    jsonl_path = day_dir / f"day_{day}_fabricated_data.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} task manifests to {day_dir}")
    return day_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, required=True)
    args = parser.parse_args()
    build_day(args.day)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
