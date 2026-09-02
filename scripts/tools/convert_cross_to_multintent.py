#!/usr/bin/env python3
"""Convert 36 note-anchored cross-app tasks (day 5+) into UNRELATED multi-intent composites."""
from __future__ import annotations

from pathlib import Path

MD = Path("benchmarks/dailyBench-600/tasks_530.md")

# task_id -> (new **[App+App]** tag, new prompt text)
CONVERSIONS: dict[str, tuple[str, str]] = {
    "medium__calculator__002": (
        "[Calculator+Messages]",
        "Could you add up 5 expense categories into a monthly budget and compare it to my income in Calculator? Also, message [contact] that I'll be late for dinner tonight.",
    ),
    "medium__google-photos__005": (
        "[Google Photos+Gmail]",
        "Could you list albums I haven't viewed recently and delete the least-used one in Google Photos? Also, email [contact] the photo from the [trip name] trip.",
    ),
    "medium__calculator__003": (
        "[Calculator+Gmail]",
        "Could you compute the total cost of two financing plans for the same purchase and compare them in Calculator? Also, email [contact] the cheaper plan.",
    ),
    "medium__google-maps__005": (
        "[Google Maps+Gmail]",
        "Could you find the cheapest parking option near [place] and check its distance from [place] in Google Maps? Also, email [contact] the address so we can meet there.",
    ),
    "medium__google-search__008": (
        "[Google Search+Gmail]",
        "Could you compare public transit options for a specific route and tell me the fastest in Google Search? Also, email [contact] the fastest route for tomorrow.",
    ),
    "medium__calendar__008": (
        "[Calendar+Gmail]",
        "Could you list the 5 busiest days this month and tell me the busiest one in Calendar? Also, email [contact] that I'm free on [date range].",
    ),
    "medium__google-maps__013": (
        "[Google Maps+Messages]",
        "Could you summarize the reviews for [place] into pros and cons in Google Maps? Also, message [contact] the address so they can find it.",
    ),
    "medium__calculator__012": (
        "[Calculator+Messages]",
        "Could you compute overtime pay given an hourly rate and extra hours across a week and compare it to the regular weekly pay in Calculator? Also, message [contact] the total for the week.",
    ),
    "medium__google-search__013": (
        "[Google Search+Gmail]",
        "Could you filter results to only official or government sites, open the most relevant one, and bookmark it in Google Search? Also, email [contact] the link.",
    ),
    "medium__contacts__013": (
        "[Contacts+Gmail]",
        "Could you find contacts with an outdated area code and update the most recent one in Contacts? Also, email [contact] to confirm their new number.",
    ),
    "medium__chrome__003": (
        "[Chrome+Messages]",
        "Could you list the 5 pages I visited most recently today in Chrome, bookmark the most useful one, and close the rest? Also, message [contact] the link to the page you kept.",
    ),
    "medium__calendar__002": (
        "[Calendar+Messages]",
        "Could you rank next week's meetings by how long they run and check how many people are invited to the longest one in Calendar? Also, message [contact] the time of the longest meeting.",
    ),
    "medium__google-search__004": (
        "[Google Search+Gmail]",
        "Could you compare the visa requirements for two destinations and tell me which one is simpler in Google Search? Also, email [contact] the simpler destination.",
    ),
    "medium__music__004": (
        "[Music+Gmail]",
        "Could you find songs I downloaded for offline listening that I haven't played in months and remove them in Music? Also, email [contact] how much storage that freed up.",
    ),
    "medium__chrome__004": (
        "[Chrome+Gmail]",
        "Could you find the top 3 search results for [topic], open the one that seems most reliable in Chrome? Also, email [contact] the link to the one you opened.",
    ),
    "medium__google-maps__003": (
        "[Google Maps+Gmail]",
        "Could you filter EV charging stations near the route by connector type and check the nearest one's availability in Google Maps? Also, email [contact] the address of the nearest station.",
    ),
    "medium__telegram__003": (
        "[Telegram+Messages]",
        "Could you rank chats by how many unread messages they have, open the top one, and reply to the most recent message in Telegram? Also, send [contact] a text asking them to call me.",
    ),
    "medium__music__006": (
        "[Music+Gmail]",
        "Could you find songs I added to a playlist but never played and remove them in Music? Also, email [contact] the playlist link.",
    ),
    "medium__youtube__005": (
        "[YouTube+Gmail]",
        "Could you compare the view counts across three videos on the same topic and save the most popular one in YouTube? Also, email [contact] the link to the most popular video.",
    ),
    "medium__contacts__008": (
        "[Contacts+Gmail]",
        "Could you filter contacts to only ones added this month, star the most recent, and check whether any are missing a phone number in Contacts? Also, email [contact] the list of contacts missing a number.",
    ),
    "medium__telegram__005": (
        "[Telegram+Gmail]",
        "Could you find the 5 most active group chats this week and mute the least relevant one in Telegram? Also, email [contact] which chat you muted.",
    ),
    "medium__google-photos__008": (
        "[Google Photos+Phone]",
        "Could you filter the library to only videos over 1 minute long, delete the longest if it's unneeded, and count what's left in Google Photos? Also, call [contact] to confirm the plan for tonight.",
    ),
    "medium__contacts__012": (
        "[Contacts+Phone]",
        "Could you merge duplicate contacts sharing the same phone number, confirm only one remains, and check its info is complete in Contacts? Also, call [contact] to confirm their address.",
    ),
    "medium__google-photos__010": (
        "[Google Photos+Phone]",
        "Could you filter screenshots older than a month, count them, and delete them in bulk in Google Photos? Also, call [contact] to tell them I'm on my way.",
    ),
    "medium__chrome__011": (
        "[Chrome+Messages]",
        "Could you filter my bookmarks to only ones added this month, delete any duplicates, and count what's left in Chrome? Also, message [contact] the count.",
    ),
    "medium__google-drive__010": (
        "[Google Drive+Messages]",
        "Could you compare two versions of the same document and keep the latest in Google Drive? Also, message [contact] what changed between the versions.",
    ),
    "medium__google-drive__011": (
        "[Google Drive+Gmail]",
        "Could you filter to only files shared with me, check which ones I can edit vs view-only, and star the most recent editable one in Google Drive? Also, email [contact] the link to the starred file.",
    ),
    "medium__calendar__011": (
        "[Calendar+Gmail]",
        "Could you find a free 30-minute slot tomorrow, book it as 'Focus time', and set a reminder for it in Calendar? Also, email [contact] the time of the slot.",
    ),
    "medium__google-photos__012": (
        "[Google Photos+Messages]",
        "Could you find and remove duplicate photos in Google Photos? Also, message [contact] how much storage was freed.",
    ),
    "medium__clock__012": (
        "[Clock+Messages]",
        "Could you rank the currently running timers by time remaining and cancel the longest if it's not needed in Clock? Also, message [contact] the time the last timer will finish.",
    ),
    "medium__youtube__002": (
        "[YouTube+Gmail]",
        "Could you filter my watch history to just videos over 20 minutes, remove the oldest one, and count what's left in YouTube? Also, email [contact] a video from the history they'd like.",
    ),
    "medium__clock__002": (
        "[Clock+Gmail]",
        "Could you compare the snooze settings across two alarms, make them consistent, and confirm both saved in Clock? Also, email [contact] the updated wake-up time.",
    ),
    "medium__gmail__007": (
        "[Gmail+Telegram]",
        "Could you find every email mentioning 'invoice' this month and add up the amounts in Gmail? Also, send [contact] the total on Telegram.",
    ),
    "medium__calendar__006": (
        "[Calendar+Phone]",
        "Could you list this month's events missing a location field and add one to the nearest event in Calendar? Also, call [contact] to confirm the venue.",
    ),
    "medium__contacts__009": (
        "[Contacts+Phone]",
        "Could you find all contacts missing a phone number, list them, and delete the ones with no other info in Contacts? Also, call [contact] to confirm their number.",
    ),
    "medium__chrome__007": (
        "[Chrome+Phone]",
        "Could you find yesterday's page about [topic] in my browsing history, summarize what it said, and reopen it in Chrome? Also, call [contact] to tell them about it.",
    ),
}

LINE_RE = {tid: f"<!--{tid}-->" for tid in CONVERSIONS}


def main() -> int:
    text = MD.read_text(encoding="utf-8")
    lines = text.split("\n")
    updated = 0
    for i, line in enumerate(lines):
        for tid, (tag, prompt) in CONVERSIONS.items():
            if f"<!--{tid}-->" in line:
                # Rebuild the single-line medium bullet with the new tag + prompt.
                new_line = f"- Medium (3pt) **{tag}**: {prompt} <!--{tid}-->"
                lines[i] = new_line
                updated += 1
                break
    missing = [t for t in CONVERSIONS if not any(f"<!--{t}-->" in l for l in lines)]
    if missing:
        print(f"ERROR: not found: {missing}")
        return 1
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"converted {updated}/{len(CONVERSIONS)} tasks in {MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
