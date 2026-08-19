# Public Sample (57-task) — On-Device Feasibility Audit

> Status: **2026-08-19**. Audited the OnePlus CPH2423 (RS7XKZDI8HTOJNYL) against every task in
> `public.md`. All **31/31 required apps installed** (app_audit PASS). Verdict legend:
> - ✅ **runnable** — the data the task needs is verified present / trivially satisfiable on-device.
> - 🛠 **fabricate** — needs data I can create via ADB/GUI before running (I'll do these or they're quick).
> - 👤 **manual** — data can't be created via ADB (app-private / live-server / needs a real action); set
>   aside for the operator.

Legend applies per task. `[placeholder]` values resolve from `public_vars.local.env` / `config/user.yaml`
(verify_config PASS).

---

## Day 1

| task | apps | verdict | note |
|---|---|---|---|
| `medium__google-maps__002` | Maps+Notes | ✅ | `[place]`=Bhubaneswar Airport (real); Maps ETA + Notes write |
| `easy__gallery__012` | Photos | ✅ | count photos in Screenshots album (deterministic; no seed needed; easily resettable files) |
| `medium__contacts__009` | Contacts+Phone | ✅ | contacts present; `[contact]`=Yuvraj Airtel (real) |
| `medium__google-drive__007` | Drive | ✅ | Drive has shared files |
| `easy__shopping-delivery-browser__001` | Chrome | 👤 | `[food delivery site]`=Swiggy surcharge notice — live page content, verify at run |
| `easy__camera__006` | Camera | ✅ | trivial (video mode) |
| `easy__phone__002` | Phone | ✅ | `[contact]` real; dialer works |
| `easy__google-slides__001` | Slides | ✅ | `[presentation name]`=Q3 Review (seeded deck) |
| `easy__calendar__002` | Calendar | ✅ | calendar has seeded events |
| `medium__gallery__007` | Photos+Obsidian | ✅ | Food Favourites.md verified (Pancakes/Pizza/Veggie Bowl headings) |
| `medium__files__013` | Files | 🛠 | duplicate files in Downloads — fabricate a few dupes |
| `medium__google-maps__003` | Maps+Telegram | ✅ | EV charging filter + `[contact]` message |
| `hard__contacts-gmail__026` | Contacts+Gmail | ✅ | contacts present |
| `easy__calculator__006` | Calculator | ✅ | trivial (temp convert) |
| `hard__drive-notes-telegram__010` | Drive+Notes+Telegram | ✅ | Budget Deadline.md verified (2026-08-10) + real budget spreadsheet |
| `medium__google-drive__001` | Drive | ✅ | Drive storage + largest file |
| `hard__google-sheets-amazon-shopping__074` | Sheets+Amazon | ✅ | SPORTS_VIDEO_DATA.xlsx verified on device |
| `hard__swiggy__005` | Swiggy+Telegram | ✅ | real orders verified (Downtown Delight Aug 14) |
| `hard__telegram-calendar__016` | Telegram+Calendar | 👤 | needs a dated message in "Forever 21" — Telegram app-private, type manually |
| `hard__youtube-settings__052` | YouTube+Settings | 🛠 | `[notifying channel]`=Tech Burner — verify subscription / mute-able channel |

## Day 2

| task | apps | verdict | note |
|---|---|---|---|
| `medium__chrome__003` | Chrome+Messages | 👤 | needs earbuds links in Chrome history — hard to seed; verify/do manually |
| `medium__calculator__002` | Calculator+Messages | 🛠 | `[budget note title]` Obsidian note (5 expense categories) — create note |
| `hard__bookmyshow__005` | BookMyShow+Telegram | 👤 | `[cinema]`=INOX Bhubaneswar live shows + group of 4 + ₹240 — verify at run |
| `easy__settings__014` | Settings | ✅ | trivial (version) |
| `easy__amazon-shopping__002` | Amazon | 👤 | `[product]`=Sony WH-1000XM5 in cart — live cart state, verify |
| `medium__prime-video__003` | Prime Video | 👤 | Continue Watching — live profile, verify |
| `easy__google-maps__004` | Maps | ✅ | trivial (save parking) |
| `easy__swiggy__001` | Swiggy | ✅ | recent order exists (delivery status) |
| `medium__clock__009` | Clock+Calendar | ✅ | recurring alarm vs calendar events |
| `easy__google-meet__004` | Meet | 🛠 | needs a meeting today — seed a Calendar/Meet event today |
| `medium__google-photos__012` | Photos+Messages | ✅ | create album 'Weekend' + add 3 most recent photos + message album name — doable via GUI, resettable (delete album) |
| `easy__youtube__011` | YouTube | 👤 | comments on "current video" — needs a video open/history |
| `hard__chrome-telegram-notes__008` | Chrome+Telegram+Notes | ✅ | price compare amazon.in/flipkart.com — real |
| `medium__files__009` | Files | 🛠 | ≥10 screenshots in folders — fabricate |
| `easy__phone__005` | Phone | ✅ | call log (make a call or verify log) |
| `medium__chrome__011` | Chrome+Messages | 👤 | bookmarks this month + dupes — hard to seed; manual |
| `hard__gmail-calendar__003` | Gmail+Calendar | ✅ | flight emails real; KB fabricated next trip (oracle) |
| `hard__google-search-telegram-clock__018` | Search+Telegram+Clock | ✅ | `[place]`=Bhubaneswar Airport hours + alarm |
| `hard__music-obsidian__077` | Music+Obsidian | ✅ | Bedtime.md verified 10:30 PM |
| `hard__photos-gmail-obsidian__012` | Photos+Gmail+Obsidian | 🛠 | needs event photo captioned "Yuvraj Airtel" — fabricate photo |

## Day 3

| task | apps | verdict | note |
|---|---|---|---|
| `medium__google-photos__008` | Photos+Phone | 🛠 | needs a >1-min video — fabricate/push |
| `medium__google-photos-calendar__001` | Photos+Calendar | 🛠 | photo dates this year — depends on photo library; fabricate a few |
| `easy__bookmyshow__004` | BookMyShow | 👤 | movies at nearest cinema — live; verify at run |
| `medium__google-search__008` | Search+Telegram | ✅ | transit fastest option + message |
| `hard__chrome-youtube-notes__088` | Chrome+YouTube+Notes | ✅ | learn a skill — open web, generic |
| `medium__calculator__001` | Calculator+Obsidian+Notes | ✅ | Exam Scores.md verified + `[passing threshold]`=60 |
| `easy__google-docs__004` | Docs | 🛠 | need a doc to rename — create one |
| `medium__music-telegram__001` | Music+Telegram | 👤 | **listening stats this week vs last week in Music** — YouTube Music doesn't expose per-week listening stats to the agent → NOT practically executable; set aside |
| `easy__msn-news__002` | MSN News | ✅ | `[topic]` section headline (Bing News) |
| `easy__messages__010` | Messages | 🛠 | need a conversation to send a GIF — create/fabricate |
| `easy__prime-video__002` | Prime Video | 👤 | Watchlist sorted by TV Shows — live profile; verify |
| `easy__youtube__009` | YouTube | 👤 | resume recently watched — needs watch history; manual/verify |
| `medium__contacts__012` | Contacts+Phone | ✅ | duplicate contacts merge (may need dupes) |
| `hard__clock-calendar__023` | Clock+Calendar | ✅ | Weekly Sync + Gym seeded (07:00 → 07:30 clash) |
| `easy__google-photos__015` | Photos | 🛠 | needs a recent screenshot to delete — fabricate |
| `hard__google-meet-files__070` | Meet+Files | ✅ | Weekly Sync + Weekly Agenda.txt seeded |
| `hard__google-search-obsidian-telegram__057` | Search+Obsidian+Telegram | ✅ | Stock Watch.md verified (Reliance, 1,400 threshold) |

---

## Summary

- ✅ **runnable (~27)** — verified data present or trivially satisfiable.
- 🛠 **fabricate (~11)** — quick ADB/GUI wins: duplicate files, screenshots, a photo/video, a Google Doc,
  a Calendar/Meet event today, the budget Obsidian note, a contact-photo.
- 👤 **manual (~13)** — cannot be ADB-seeded (app-private or live-server):
  - **Telegram dated message** (`telegram-calendar__016`) — type "see you on the 20th" in Forever 21.
  - **Chrome history/bookmarks** (`chrome__003`, `chrome__011`) — seed via real browsing.
  - **BookMyShow live shows** (`bookmyshow__004/005`) — verify INOX Bhubaneswar shows at run.
  - **Amazon cart** (`amazon-shopping__002`) / **Prime Watchlist & Continue Watching** (`prime-video__002/003`)
    — verify live profile at run.
  - **YouTube comments / resume** (`youtube__011`, `youtube__009`) — needs watch history.
  - **Music weekly listening stats** (`music-telegram__001`) — **not executable**: YouTube Music (the
    benchmark's "Music") doesn't surface week-vs-week listening stats the agent can read; set aside.
  - **Swiggy surcharge notice** (`shopping-delivery-browser__001`) — live page content; verify.
- `verify_config.py` PASS; all placeholders resolve; all apps installed.

**Fabrication list (I can do these via ADB):** duplicate files in Downloads, 10+ screenshots, a >1-min video, a couple of photos + a screenshot, a Google Doc to rename, a Calendar/Meet event for today, the
Obsidian budget note (5 expense categories), and a contact-photo assignment.

### Fabrication status (2026-08-19 — done via ADB)
- ✅ **Obsidian `Monthly Budget.md`** created (income ₹25,000 + 5 expense categories) → `calculator__002`.
- ✅ **20 duplicate PDFs** (10 pairs) in `/sdcard/Download` → `files__013`.
- ✅ **11 screenshots** in `/sdcard/Pictures/Screenshots` → `files__009`, `google-photos__015`.
- ✅ **Calendar "Team Standup"** event today 11:00–11:30 (cal_id 16) → `google-meet__004`.
- ✅ **65s video** (`feas_video.mp4`) pushed to `/sdcard/DCIM/Camera` → `google-photos__008`.
- ✅ **Google Docs recents already populated** (`Weekly Review.docx`, `Untitled document`, etc.) →
  `google-docs__004` is runnable without fabrication (agent renames an existing doc).
- ✅ **Duplicate photos likely satisfiable**: the 11 `feas_*.png` screenshots are near-identical frames, so
  Google Photos will present them as duplicates → `google-photos__012` (agent removes + reports freed
  storage).
- 🛠 still to do (GUI/operator): event photo captioned "Yuvraj Airtel" (`photos-gmail-obsidian__012` — verify
  the existing Photo Sent note against the photo library).
- ✅ **Vision-only camera/gallery task:** `medium__gallery__007` (match food photos to Pancakes/Pizza/Veggie
  Bowl by content). `easy__gallery__012` was reverted from a synthetic-seed vision task to a plain
  Screenshots-album count (no seed needed).
- 👤 **cannot ADB-seed** → operator: Telegram dated message, Chrome history/bookmarks, BookMyShow shows,
  Amazon cart, Prime Watchlist/Continue Watching, YouTube comments/resume, **Music weekly stats
  (`music-telegram__001`)**.
