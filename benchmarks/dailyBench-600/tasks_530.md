# DrainBench: The 28-Day Survival Schedule — runnable 530-task set

This is the **canonical runnable schedule**: the deterministic 530-task subset
(531 dataset rows: 229 easy / 230 medium / 72 hard = 36 ASK USER / 36 DETERMINISTIC) of the 730-task
corpus, landing each day at the real-world ~9-10 distinct-app density (see
docs/app-usage-grounding.md). Every task here is also in `tasks.md` (the full 730
corpus) and traces to it by task_id.

This file is the **source of truth for the runnable 530 set**: edit it, then run
`scripts/export_530_dataset.py` to regenerate `DailyBench_530_v1.json` / `.jsonl`.
Each task line carries its `task_id` in an HTML comment, so ids survive edits.
Resync from the JSON with `scripts/export_530_markdown.py`.

---

## The 28-Day Schedule

### Day 1

**[Chrome]**
- Easy (1pt): Save the page I'm on right now in Chrome so I can read it offline later <!--easy__chrome__001-->
- Medium (3pt): I'd like a short summary of the article at [article url]. Pull out its main argument in 2-3 sentences, save that as a pinned note, and bookmark the article in Chrome <!--medium__chrome__001-->
- Medium (3pt) **[Chrome+Telegram]**: Look up [topic] in Chrome across two top search results, summarize the key points, and share the summary with [contact] on Telegram with links to both of the chosen websites <!--medium__chrome-telegram__001-->

**8. [Chrome+Telegram+Notes] — ASK USER**
- I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing (deliberately no item is specified, so the agent must ask the user what they are shopping for) <!--hard__chrome-telegram-notes__008-->

**[Google Search]**
- Easy (1pt): Google the current exchange rate for [currency pair] <!--easy__google-search__001-->
- Medium (3pt): I'm curious about [topic]. Google it, skim the two best results, and give me a one-line takeaway from each <!--medium__google-search__001-->

**57. [Google Search+Obsidian+Telegram] — ASK USER**
- I'm tracking [stock name] and only want to hear about it when it matters. Check its current value via Google Search against the threshold in my '[stock note title]' Obsidian note, note today's value, compare it to the last recorded value in that Obsidian note, message the person I follow this stock with on Telegram only if it has crossed the threshold since then, and update the Obsidian note with today's value (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__google-search-obsidian-telegram__057-->

**[Calendar]**
- Easy (1pt): Add my current location to my 'Lunch with Maa' event in Calendar today <!--easy__calendar__001-->
- Medium (3pt): Filter my Calendar to show only recurring events with no attendees, delete one that's outdated, and check that the series still repeats correctly <!--medium__calendar__001-->

**2. [Calendar+Telegram+Obsidian] — ASK USER**
- My '[meeting title]' meeting this week needs its timing sorted. Check Calendar for it, note its exact start time, and message the attendee on Telegram to reschedule if it's before 9am or confirm if it isn't. Also, log the message you sent in an Obsidian note under the '[meeting folder]' folder (create it if it isn't there) with the meeting details + meet link (deliberately no attendee is named for the meeting, so the agent must ask the user who it is with) <!--hard__calendar-telegram-obsidian__002-->

**[Contacts]**
- Easy (1pt): Search my Contacts for the number of a contact named [contact name] <!--easy__contacts__001-->
- Medium (3pt) **[Contacts+Calendar]**: It's a busy month for birthdays. In Contacts, see which of my contacts have birthdays this month, add a reminder for each to buy a present a week before the due date, and count them <!--medium__contacts__001-->

**[Obsidian]**
- Easy (1pt): Create a new note titled '[note title]' in Obsidian <!--easy__obsidian__001-->

**[Google Docs]**
- Medium (3pt): Rank my documents in Google Docs by length (word count), open the longest one, and tell me its word count <!--medium__google-docs__001-->

**[Camera]**
- Easy (1pt): Take a photo of any object on my desk with the Camera and save it with an appropriate name for the object captured <!--easy__camera__001-->
- Medium (3pt): I'm taking a portrait this evening, so set up the Camera: turn on AI enhancement mode and portrait mode. <!--medium__camera__001-->

**[Gallery]**
- Medium (3pt): Search for [food_category] photos, then in Gallery pick the best 3 in terms of resolution and save them to a new album <!--medium__gallery__001-->
- Easy (1pt): Hide the specific photo taken about an hour back from the main view in Gallery <!--easy__gallery__001-->
- Medium (3pt) **[Gallery+Telegram]**: I've got a short burst of photos that'd make a fun GIF. Select the ones taken recently today and make the GIF in Gallery, save it, and share it via Telegram to [contact] <!--medium__gallery-telegram__001-->

**[Messages]**
- Easy (1pt): Search my Messages for the word '[search word]' <!--easy__messages__001-->
- Medium (3pt): Find all unread Messages from this week that contain an unanswered question, answer the most recent with "Will get back to you fr in some time!", and tell me the question you answered <!--medium__messages__001-->

**[Phone]**
- Easy (1pt): In Phone, message the most recent unknown number with "who's this?" <!--easy__phone__001-->

### Day 2

**[Gmail]**
- Easy (1pt): Can you forward the most recent email in my Gmail to [contact] pls? <!--easy__gmail__001-->
- Medium (3pt): I've got a few unread emails from [sender] piling up. In Gmail, give me a short bulleted-summary of its last 5, star whichever looks most urgent, and archive the rest <!--medium__gmail__001-->

<!-- 🔮 HALLUCINATION CONTROL (medium__gmail-notes__001, no-thread): data genuinely absent (Myntra has ~15+ one-way promo emails but no conversational thread, no single subject, and Gmail mobile exposes no 'link to a thread'. A summarisable thread genuinely does not exist.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Gmail+Notes]**: Find the thread with [sender] in Gmail, summarize it into exactly 3 bullet points, and save the summary, the subject of the thread and a link to it as a note in my Notes app. <!--medium__gmail-notes__001-->

**[Google Maps]**
- Easy (1pt): Check how far away [place] is on Google Maps <!--easy__google-maps__001-->
- Medium (3pt) **[Google Maps+Calendar]**: Compare the ETA to [place] at [time 1] and [time 2] in Google Maps, note which is faster, and set a Calendar reminder to leave at that time with an appropriate title. <!--medium__google-maps__001-->

**5. [Google Maps+Notes] — DETERMINISTIC**
- Which is closer from here, the nearest general physician's clinic or the nearest hospital? Search Maps for both, check their distances, compare, and save the closer one's name and distance as a note in Notes, then star it as a favorite or pin it. <!--hard__google-maps-notes__005-->

**[Google Photos]**
- Easy (1pt): Search Google Photos for photos from [date range] <!--easy__google-photos__001-->
- Medium (3pt): Find the 5 best photos from my [trip name] trip based on favorites, creating an album called: [album name] <!--medium__google-photos__001-->

**12. [Photos+Gmail+Obsidian] — ASK USER**
- I'd like to send [contact] a photo from the event. Find the photo from [trip name] in Photos, for which the caption has the [contact] mentioned, and email it to them if so, recording the send in a note in Obsidian; otherwise save it to a general album. Star it either way (deliberately no event is named, so the agent must ask the user which event's photos they mean) <!--hard__photos-gmail-obsidian__012-->

**[YouTube]**
- Easy (1pt): Search YouTube for the most popular podcast video by [channel name] and play it  for about a minute or so. <!--easy__youtube__001-->
- Medium (3pt) **[YouTube+Telegram]**: Find the most-liked video from my favourite channel: [channel name] channel on YouTube, subscribe if I'm not already, and send its link to [contact] on Telegram <!--medium__youtube__001-->

**[Notes]**
- Easy (1pt): Make the [note title] note's text bigger in Notes <!--easy__notes__001-->

**[Files]**
- Easy (1pt): Sort Downloads by date instead of name in Files <!--easy__files__001-->
- Medium (3pt) **[Files+Notes]**: In Files, filter Downloads to only the files from this week, tell me the largest one, check whether it's already backed up, and add those to a note that haven't already been backed up, in Notes. <!--medium__files__001-->
<!-- 🔮 HALLUCINATION CONTROL (medium__files__014, absent-entity): data genuinely absent (No 'Scan Backup' folder inside /sdcard/Download (verified absent on the device).). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt): In Files, open the 'Scan Backup' folder inside Downloads and tell me how many scanned documents are in it <!--medium__files__014-->

**11. [Files+Notes] — ASK USER**
- I need to pay an invoice and want to know what I actually owe. Find the most recent invoice PDF in Files (you can open it in any PDF Viewer you desire), extract the total amount and due date, and if the due date has passed, add the late fee I specify. Log the new total in a note and reply with only that number, no other text (deliberately no late fee percentage is specified, so the agent must ask the user what late fee to apply) <!--hard__files-notes__011-->

**[Music]**
- Easy (1pt): Can you play the most recently added song in my playlist I have on YT Music? Thanks <!--easy__music__001-->
- Medium (3pt): In my YT Music app, look through my history this week and play the ones with by [artist], add it to my favorites. Also, I am about to start studying, so play some 2 hrs+ lofi playlist for me?<!--medium__music__001-->

### Day 3

**[Gmail]**
- Easy (1pt): I haven't checked my mail in a bit — can you open Gmail and tell me who sent the most recent unread email? <!--easy__gmail__002-->
- Medium (3pt) **[Gmail+Notes]**: In Gmail, filter unread recruiting emails from past week, star them, and save a note listing how many have answered back with a positive response to my job applications with the respective email details. <!--medium__gmail__002-->

**[Google Drive]**
- Easy (1pt): Make me a copy of [X] in Google Drive, please — I want a duplicate I can edit without touching the original. <!--easy__google-drive__001-->
- Medium (3pt): I'm running out of space in my Drive and can't figure out where it all went. Check my current storage usage in Drive's settings, then open the details of the files in the main Drive folder, find the largest file, and note its name, type, size, and last modified date. <!--medium__google-drive__001-->

**[Google Search]**
- Easy (1pt): What's the weather looking like today? Google it and give me today's forecast. <!--easy__google-search__002-->
- Medium (3pt) **[Google Search+Obsidian]**: My essay is  due tomorrow so help me out writing one by doing a thorough research yourself, for the topic: [topic], sumarizing the top 5 Google search results as a pinned note in a Obsidian notes for about 200 words. Thanks! <!--medium__google-search__002-->

**19. [Google Search+Notes] — DETERMINISTIC**
- I'm torn between [product 1] and [product 2]. Search Google for an overview of highly rated reviews of each, record the overall sentiments of each of the products, compare them, save only the name of the more favorably reviewed one as a note. in Notes. Your review pool should atleasr be 10 or more for a more thorough analysis for each product. <!--hard__google-search-notes__019-->

**[Clock]**
- Easy (1pt): What time is it in [city] right now? Check it on the Clock for me. <!--easy__clock__001-->
<!-- 🔮 HALLUCINATION CONTROL (easy__clock__017, absent-entity): data genuinely absent (No alarm labeled '[alarm label]' exists in Clock.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Clock, check whether an alarm labeled '[alarm label]' is set and tell me what time it's set for <!--easy__clock__017-->
- Medium (3pt): I'm cooking the [recipe] and it has several timed steps back-to-back. Read the recipe and set up a labeled timer in the Clock for each timed step (label each timer with its step name) so they are ready to start as each step begins; confirm each timer was created and labelled. <!--medium__clock__001-->

**[Chrome]**
- Easy (1pt): I'm about to order food but worried about surcharges — open the [food delivery site] in Chrome and check if there's any weather-related surcharge notice <!--easy__shopping-delivery-browser__001-->
- Medium (3pt): In Chrome, compare total cost, item plus shipping, of [product] across [shopping_website_1] and [shopping_website_2], note the cheaper option, and check the delivery time for that option, outputting the same. <!--medium__shopping-delivery-browser__001-->

**[Contacts]**
- Easy (1pt): In Contacts, edit [contact name]'s saved email address to [new email] <!--easy__contacts__003-->
- Medium (3pt) **[Contacts+Notes]**: Can you get me all the contacts from Contacts app, that start with the letter [letter] who have birthdays this month? Also, suggest me good birthday presents based on their descriptions mentioned in their contact details, and save the list of contacts and the suggested presents as a note <!--medium__contacts__002-->
- Medium (3pt) **[Contacts+Notes]**: In Contacts, compare two contacts that look like possible duplicates either by name or phone number, merge if confirmed, and note the result <!--medium__contacts-notes__001-->

**[Messages]**
- Easy (1pt): I want to clear out my most recent conversation with [contact] in Messages — please delete that specific thread for me. <!--easy__messages__003-->

**78. [Messages+Notes] — ASK USER**
- Give one conversation a distinct notification tone. Set a custom notification tone for the Messages thread, send a test message to confirm it plays, check the Notes log for whether the same tone is already used for another contact, choose a different one if so, and confirm the update in the log (deliberately no conversation or tone is specified, so the agent must ask the user which thread and which tone) <!--hard__messages-notes__078-->

**[Settings]**
- Easy (1pt): In Settings, check available RAM/memory usage per most active app right now <!--easy__settings__001-->
- Medium (3pt): In Settings, set up a scheduled dark mode from sunset to sunrise, confirm it saved, and check tonight's schedule <!--medium__settings__001-->
<!-- 🔮 HALLUCINATION CONTROL (medium__settings__017, absent-entity): data genuinely absent (No scheduled power-off is configured in Settings.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt): In Settings, check the scheduled power-off setting and tell me whether the phone is set to turn itself off at [power off time] each night <!--medium__settings__017-->

**[Music]**

**77. [Music+Obsidian] — DETERMINISTIC**
- I fall asleep to music and want the timer to match my bedtime. First, search YouTube Music for my favorite music type — a [music type] track — and download the highly-liked video of it. Then set a YouTube Music **sleep timer** so **playback stops at the next upcoming bedtime noted in Obsidian** — pick the nearest bedtime in the future, set the timer to end the music at that time, note the chosen duration, compare it against that bedtime, shorten it if it would run past bedtime, and double-check the final timer length <!--hard__music-obsidian__077-->

### Day 4

**[Google Maps]**
- Easy (1pt): In Google Maps, check current traffic conditions on the usual commute route <!--easy__google-maps__002-->
- Medium (3pt) **[Google Maps+Notes]**: In Google Maps, compare the ETA to [place] by driving, transit, and walking, pick the fastest way there, and save the ETA+distance to travel it as a note in Notes with an appropriate title." <!--medium__google-maps__002-->

**[Google Photos]**
- Easy (1pt): In Google Photos, check which photos aren't backed up yet <!--easy__google-photos__002-->
- Medium (3pt): In Google Photos, rank recent albums by number of photos, open the largest one, and star its cover photo <!--medium__google-photos__002-->

**[Calculator]**
- Easy (1pt): In Calculator, compute 15% of [amount] <!--easy__calculator__001-->
- Medium (3pt) **[Calculator+Notes]**: In Calculator, compute a weighted average of my exam scores with different weights, write the final grade in a note, and check if it meets a passing threshold <!--medium__calculator__001-->

**[Obsidian]**
- Easy (1pt): In Obsidian, add a line to an existing note <!--easy__obsidian__003-->

**[Notes]**
<!-- 🔮 HALLUCINATION CONTROL (easy__notes__002, absent-entity): data genuinely absent (No note titled 'Grocery List' exists in Notes.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Notes, add a bullet list to the note titled 'Grocery List' <!--easy__notes__002-->
- Medium (3pt): In Notes, filter notes tagged or titled 'To Buy' across folders, merge them into one list, and rename it <!--medium__notes__001-->

**[Camera]**
- Easy (1pt): In Camera, switch to a square aspect ratio and take a photo of any object <!--easy__camera__003-->
- Medium (3pt): In Camera, take a photo of any object, apply a filter, and compare before/after <!--medium__camera__003-->

**[Gallery]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__002, absent-entity): data genuinely absent (No photo named 'IMG_20250101.jpg' exists in Gallery.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gallery, check the location metadata on the photo 'IMG_20250101.jpg' <!--easy__gallery__002-->
- Medium (3pt) **[Gallery+Notes]**: In Gallery, filter photos to show only ones from a specific trip, star the best one, check whether any are duplicates, and save a note of which photo you starred <!--medium__gallery__003-->

**35. [Gallery+Obsidian] — DETERMINISTIC**
- Track how many photos I take each day. Curate today's Gallery photos into an album, note the count, match it against yesterday's count noted in Obsidian, log only which day had more, and star the album if today's count is higher <!--hard__gallery-obsidian__035-->

**[Phone]**
- Easy (1pt): In Phone, call [contact] <!--easy__phone__002-->
- Medium (3pt): In Phone, find and merge a missed call's number into an existing contact, confirm the merge, and check the contact's info is complete <!--medium__phone__002-->

**[Settings]**
- Easy (1pt): In Settings, turn on Wi-Fi <!--easy__settings__002-->

**[Contacts]**

**27. [Contacts+Notes] — DETERMINISTIC**
- Track how my contacts are growing. Export Contacts to a file, compare the total against last month's export noted in Notes, jot down only the difference, and star the note <!--hard__contacts-notes__027-->

**29. [Contacts+Obsidian] — DETERMINISTIC**
- My contacts have duplicates. Find the Contacts sharing the same number, merge them, write down the merge in a note with today's date, and reply with only the count of contacts remaining after the merge, no other text <!--hard__contacts-obsidian__029-->

### Day 5

**[Chrome]**
- Easy (1pt): In Chrome, search 'weather tomorrow' and open the first result <!--easy__chrome__003-->
- Medium (3pt) **[Chrome+Notes]**: In Chrome, list the 5 most recently visited pages today, bookmark the most useful one, close the rest, and note which one you kept <!--medium__chrome__003-->

**[Google Drive]**
- Easy (1pt): In Google Drive, check current Drive storage usage <!--easy__google-drive__003-->
- Medium (3pt): In Google Drive, find files not opened in the last 6 months, list them, and archive the oldest <!--medium__google-drive__002-->

**10. [Drive+Notes+Telegram] — ASK USER**
- The shared budget spreadsheet might be slipping. Check Drive for its last-edited date, note it, and compare it against the deadline in Notes. If it's overdue, message the person who owns the budget on Telegram; if on track, star it. Confirm the check with today's date in the note (deliberately no recipient or budget spreadsheet is named, so the agent must ask the user who to message and which budget spreadsheet they mean) <!--hard__drive-notes-telegram__010-->

**49. [Drive+Obsidian+Telegram] — ASK USER**
- Make sure the shared spreadsheet is on track. Check its last-edited date in Drive, record it, cross-reference it against the deadline noted in Obsidian, and message the person who owns the spreadsheet on Telegram only if it's overdue; star the spreadsheet either way (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__drive-obsidian-telegram__049-->

**[Google Photos]**
- Easy (1pt): In Google Photos, check how many photos are in the library <!--easy__google-photos__004-->
- Medium (3pt) **[Google Photos+Calendar]**: In Google Photos, summarize how many photos were taken each month this year, note the busiest month, and set a calendar reminder to review that month's album <!--medium__google-photos-calendar__001-->

**[Telegram]**
- Easy (1pt): In Telegram, send a sticker to [contact] <!--easy__telegram__002-->
- Medium (3pt): In Telegram, find all messages containing a link, list them, and open the most recent <!--medium__telegram__002-->

**[Calendar]**
- Easy (1pt): In Calendar, check for any conflicts tomorrow afternoon <!--easy__calendar__002-->
- Medium (3pt) **[Calendar+Notes]**: In Calendar, rank next week's meetings by duration, save the longest one in a note, and check its attendee count <!--medium__calendar__002-->

**25. [Calendar+Telegram+Notes] — ASK USER**
- Confirm tomorrow's early start for me. Check Calendar for the earliest event tomorrow, note its exact start time, and message the attendee on Telegram to confirm if it starts before 8am, otherwise just note the time, recording the outcome either way (deliberately no attendee is named, so the agent must ask the user who to confirm with) <!--hard__calendar-telegram-notes__025-->

**[Contacts]**
<!-- 🔮 HALLUCINATION CONTROL (easy__contacts__005, absent-entity): data genuinely absent (No contact named 'Rahul Mehta' exists in Contacts.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Contacts, check the saved address of 'Rahul Mehta' <!--easy__contacts__005-->
- Medium (3pt) **[Contacts+Obsidian]**: In Contacts, filter contacts by company name, export the list, and save the export location in a note <!--medium__contacts-obsidian__001-->

**[Notes]**
- Easy (1pt): In Notes, find the note titled '[X]' <!--easy__notes__003-->

**[Obsidian]**
- Medium (3pt): In Obsidian, summarize a research note into a short takeaway, save it at the top of the note, and star the note <!--medium__obsidian__004-->

**[Music]**
<!-- 🔮 HALLUCINATION CONTROL (easy__music__004, no-result): data genuinely absent (No podcast titled 'The Midnight Cast' exists in the Music library.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Music, search for a podcast by 'The Midnight Cast' <!--easy__music__004-->
- Medium (3pt): In Music, rank playlists by total listening time this month, open the most-played, and note its track count <!--medium__music__003-->

**[Messages]**
- Easy (1pt): In Messages, check the read receipt on the last sent message <!--easy__messages__004-->
- Medium (3pt) **[Messages+Notes]**: In Messages, summarize an unread thread's messages into one line, save the summary in a note, reply based on it, and star the thread <!--medium__messages__003-->

### Day 6

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__003, absent-entity): data genuinely absent (No unread email from 'Rahul Mehta' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gmail, check how many unread emails from 'Rahul Mehta' are in my inbox <!--easy__gmail__003-->

**3. [Gmail+Calendar] — DETERMINISTIC**
- I'm flying soon and want a heads-up before departure. Find the most recent flight-confirmation email in Gmail, extract the departure time, set a calendar reminder 3 hours before, then check the current time and reply with only the countdown in hours until departure, no other text <!--hard__gmail-calendar__003-->

**[YouTube]**
- Easy (1pt): In YouTube, mute the current video <!--easy__youtube__002-->
- Medium (3pt) **[YouTube+Notes]**: In YouTube, filter watch history to show only videos over 20 minutes, remove the oldest one, count what's left, and note the count <!--medium__youtube__002-->

**[Clock]**
- Easy (1pt): In Clock, rename an alarm <!--easy__clock__002-->
- Medium (3pt) **[Clock+Notes]**: In Clock, compare snooze settings across two alarms, make them consistent, confirm both saved, and note the change <!--medium__clock__002-->

**23. [Clock+Calendar] — DETERMINISTIC**
- I need a recurring alarm but don't want it to clash. Set it on Clock, cross-reference it against Calendar for the same week, and if there's a conflict, shift it by 30 minutes, then confirm the new time saved <!--hard__clock-calendar__023-->

**[Calendar]**
- Easy (1pt): In Calendar, see a list of all-day events this week <!--easy__calendar__003-->
- Medium (3pt): In Calendar, filter events this week without a reminder set, add reminders to them, and count how many were updated <!--medium__calendar__003-->

**97. [Calendar] — ASK USER**
- Set up a meeting that works for everyone. Suggest and book the best meeting time tomorrow considering everyone's apparent calendar availability (deliberately no attendee list or preferred time exists on the test device, so the agent must ask the user who to invite and what time works before proposing times) <!--hard__calendar__097-->

**[Chrome]**
- Easy (1pt): In Chrome, search for a specific brand's page on a shopping site <!--easy__shopping-delivery-browser__002-->
- Medium (3pt): In Chrome, compare the price of '[product]' across three shopping sites, rank them cheapest to priciest, and note the best deal <!--medium__shopping-delivery-browser__002-->

**[Contacts]**
- Medium (3pt) **[Contacts+Notes]**: In Contacts, find contacts with duplicate email addresses, clean them up, and note how many were merged <!--medium__contacts__005-->

**[Files]**
<!-- 🔮 HALLUCINATION CONTROL (easy__files__002, absent-entity): data genuinely absent (No 'Old Scans' folder exists in Files.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Files, empty the 'Old Scans' folder <!--easy__files__002-->
- Medium (3pt): In Files, find files not opened in over 3 months, list them, and delete the oldest <!--medium__files__002-->

**[Camera]**
- Easy (1pt): In Camera, take a photo of a printed page or receipt and save it as a scanned file <!--easy__camera__004-->
- Medium (3pt): In Camera, take a photo of a nearby object with manual focus vs. auto-focus, compare sharpness, and keep the sharper one <!--medium__camera__004-->

### Day 7

**[Gmail]**
- Medium (3pt) **[Gmail+Telegram]**: In Gmail, filter the inbox by attachment type (PDF only), list the senders, and message the most frequent sender's name to [contact] on Telegram, with no other text <!--medium__gmail__004-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__004, absent-entity): data genuinely absent (No file named 'Project Proposal v2' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, search for a file named 'Project Proposal v2' <!--easy__google-drive__004-->
- Medium (3pt): In Google Drive, find duplicate-named files across folders, delete the older copy, and note which was kept <!--medium__google-drive__003-->

**[Google Search]**
- Easy (1pt): In Google Search, look up 'how to [topic]' and read the top result <!--easy__google-search__004-->
- Medium (3pt) **[Google Search+Obsidian]**: In Google Search, compare visa requirements for two destinations, note which is simpler, and save that in an Obsidian note <!--medium__google-search__004-->

**[Calendar]**
- Easy (1pt): In Calendar, check what my next event today is <!--easy__calendar__004-->

**[Chrome]**
- Easy (1pt): In Chrome, check a shopping site's flash-sale end time <!--easy__shopping-delivery-browser__003-->
- Medium (3pt): In Chrome, compare shipping costs and delivery windows across two options, and note the better one, without checking out <!--medium__shopping-delivery-browser__003-->

**[Files]**
<!-- 🔮 HALLUCINATION CONTROL (easy__files__003, absent-entity): data genuinely absent (No image file named 'IMG_20250101.jpg' exists in Files.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Files, preview the image file 'IMG_20250101.jpg' without opening a gallery app <!--easy__files__003-->
- Medium (3pt): In Files, filter Downloads to only .apk or installer files, delete the ones no longer needed, and count what's left <!--medium__files__003-->

**[Music]**
- Easy (1pt): In Music, like or save the currently playing song <!--easy__music__006-->
- Medium (3pt) **[Music+Obsidian]**: In Music, find songs downloaded for offline listening that haven't been played in months, remove them, and note in Obsidian how much storage was freed <!--medium__music__004-->

**[Phone]**
- Easy (1pt): In Phone, block a specific incoming number <!--easy__phone__003-->
- Medium (3pt): In Phone, compare call duration between two contacts this month, note who I spoke to longer, and check the total combined duration <!--medium__phone__003-->

**[Contacts]**

**26. [Contacts+Gmail] — DETERMINISTIC**
- I want to clean up my contacts. Find all Contacts missing a phone number, list them, check each against Gmail for a saved email, delete only the ones with neither, and star one of the remaining contacts as a reminder to verify it later <!--hard__contacts-gmail__026-->

**[Camera]**

**34. [Camera+Files] — DETERMINISTIC**
- Digitize a document without creating a duplicate. Take a photo of it with Camera, check Files for whether a scan of the same document already exists, keep only the clearer of the two if so, otherwise save the new one, and rename it with today's date <!--hard__camera-files__034-->

**66. [Camera+Contacts+Gmail] — ASK USER**
- Found a handwritten note with someone's details. Take a photo of it with Camera, read off the details, check Gmail for whether that name has emailed before, merge into the existing contact if so, otherwise save as new, and verify the contact's info is complete (deliberately no person is named for the handwritten note, so the agent must ask the user whose details it is) <!--hard__camera-contacts-gmail__066-->

### Day 8

**[Chrome]**
- Easy (1pt): In Chrome, enable reader/simplified view on an article <!--easy__chrome__004-->
- Medium (3pt) **[Chrome+Obsidian]**: In Chrome, find the top 3 search results for [topic], note which seems most reliable, open it, and save the reason in an Obsidian note <!--medium__chrome__004-->

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__005, absent-entity): data genuinely absent (No email from 'Rahul Mehta' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gmail, star the email from 'Rahul Mehta' I'll need later today <!--easy__gmail__005-->

**[Google Maps]**
- Easy (1pt): In Google Maps, save the current location as 'parked here' <!--easy__google-maps__004-->
- Medium (3pt) **[Google Maps+Obsidian]**: In Google Maps, filter EV charging stations near the route by connector type, check the nearest one's availability, save it, and note its address in Obsidian <!--medium__google-maps__003-->

**[YouTube]**
- Easy (1pt): In YouTube, check trending videos today <!--easy__youtube__003-->
- Medium (3pt): In YouTube, summarize the top comment thread on a video, like the top comment, and reply to it <!--medium__youtube__003-->

**[Clock]**
- Easy (1pt): In Clock, set an alarm for [time] <!--easy__clock__003-->
- Medium (3pt): In Clock, check which alarms would go off during a planned quiet-hours window, disable those, and confirm the rest remain active <!--medium__clock__003-->

**[Contacts]**
<!-- 🔮 HALLUCINATION CONTROL (easy__contacts__008, absent-entity): data genuinely absent (No contact named 'Rahul Mehta' exists to favourite.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Contacts, star 'Rahul Mehta' as a favorite <!--easy__contacts__008-->

**[Gallery]**
- Easy (1pt): In Gallery, zoom in on my most recent photo <!--easy__gallery__003-->
- Medium (3pt): In Gallery, filter photos by which lens they were taken with, count how many used portrait mode, and star one <!--medium__gallery__004-->

**[Messages]**
- Medium (3pt): In Messages, filter conversations to show only ones with unread messages, determine which has waited longest, and open that one <!--medium__messages__004-->

**[Settings]**
- Easy (1pt): In Settings, adjust screen brightness manually <!--easy__settings__005-->
- Medium (3pt) **[Settings+Obsidian]**: In Settings, filter installed apps to show which have camera permission, revoke it for one unused app, and note in Obsidian which apps still have it <!--medium__settings__004-->

**81. [Settings+Notes] — DETERMINISTIC**
- My battery's been draining fast. Turn on battery saver in Settings when the battery drops below 20%, note today's usage, compare it against yesterday's noted in Notes, flag it if today's drain is unusually fast, and confirm the setting saved <!--hard__settings-notes__081-->

**82. [Settings+Notes] — DETERMINISTIC**
- Did I hit my step goal? Find yesterday's step total in Settings if available, note it, match it against the daily goal noted in Notes, write down only whether the goal was met, and check today's progress so far too <!--hard__settings-notes__082-->

**[Obsidian]**

**99. [Obsidian] — ASK USER**
- My notes have a messy one that needs tidying. Find the note I mean, rewrite it into a cleaner organized version with clear sections, and confirm it saved (deliberately no note title is specified, so the agent must ask the user which note) <!--hard__obsidian__099-->

### Day 9

**[Chrome]**
- Easy (1pt): In Chrome, check today's news headline for [topic] <!--easy__chrome__006-->
- Medium (3pt): In Chrome, compare two product pages, list the differences, and note which is the better deal <!--medium__chrome__005-->

**[Telegram]**
<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__004, absent-entity): data genuinely absent (No Telegram group named 'Old College Group' exists.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Telegram, leave the group 'Old College Group' <!--easy__telegram__004-->
- Medium (3pt) **[Telegram+Obsidian]**: In Telegram, rank chats by number of unread messages, open the top one, reply to the most recent message, and note in Obsidian what you replied <!--medium__telegram__003-->

**16. [Telegram+Calendar] — DETERMINISTIC**
- I think a date was mentioned in the group chat. Check the last 10 messages in the Telegram group for any mention of a date, record the most recent one, and compare it against Calendar. If there's no matching event within 2 days, create a 'Follow-up' event; confirm the check either way <!--hard__telegram-calendar__016-->

**[Calculator]**
- Easy (1pt): In Calculator, convert [amount] between two currencies <!--easy__calculator__002-->
- Medium (3pt) **[Calculator+Obsidian]**: In Calculator, sum 5 expense categories into a monthly budget, compare to income, and save in an Obsidian note whether it's over budget <!--medium__calculator__002-->

**[Calendar]**
- Medium (3pt): In Calendar, compare two calendars for overlapping events, flag the conflicts, and note which calendar has more conflicts <!--medium__calendar__005-->
- Medium (3pt) **[Calendar+Telegram]**: In Calendar, find and cancel just the next occurrence of a recurring event, notify attendees via Telegram, and note the reason in the event <!--medium__calendar-telegram__001-->

**[Files]**
- Easy (1pt): In Files, search for all PDF files on the device <!--easy__files__004-->
<!-- 🔮 HALLUCINATION CONTROL (medium__files__004, absent-entity): data genuinely absent (No folder named 'Temp' exists anywhere in storage.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Files+Obsidian]**: In Files, find folders named 'Temp' across storage, count them, delete them, and log in Obsidian how many were removed <!--medium__files__004-->

**[Gallery]**
- Easy (1pt): In Gallery, undo a recent edit made to a photo <!--easy__gallery__004-->
- Medium (3pt): In Gallery, rank recent albums by number of photos, open the largest, and note its cover photo <!--medium__gallery__005-->

**36. [Gallery+Telegram] — ASK USER**
- I want to share a photo with the person I want to share it with, without sending a duplicate. Find the photo in Gallery, check Telegram chat history for whether it's already been shared with them, share it now if not, star the photo either way, and confirm the chat history is up to date (deliberately no recipient or photo is named, so the agent must ask the user who to send it to and which photo they mean) <!--hard__gallery-telegram__036-->

**[Music]**
- Easy (1pt): In Music, check how long is left in the current song <!--easy__music__007-->

**37. [Music+Telegram] — ASK USER**
- I'm making a two-song playlist and want to compare notes with a friend. Create it in Music, name it, check Telegram for whether that friend has mentioned a similar playlist, message them only if a match exists, and verify the playlist saved (deliberately no recipient or songs are named, so the agent must ask the user who to compare notes with and which two songs to include) <!--hard__music-telegram__037-->

**[Messages]**
- Easy (1pt): In Messages, mark a conversation as unread for later <!--easy__messages__006-->

**[Phone]**
- Easy (1pt): In Phone, redial the last dialed number <!--easy__phone__004-->
- Medium (3pt): In Phone, list my 5 most recent missed calls, note which haven't been returned, and call back the most recent one <!--medium__phone__004-->

### Day 10

**[Chrome]**
- Easy (1pt): In Chrome, reopen the most recently closed tab <!--easy__chrome__007-->
- Medium (3pt) **[Chrome+Notes]**: In Chrome, search for reviews of [product], summarize the overall sentiment, and save the decision as a note <!--medium__chrome-notes__001-->

**31. [Chrome+Files+Obsidian] — DETERMINISTIC**
- I'm downloading a file and don't want to overwrite anything. Download it via Chrome, check Files for whether a same-named file already exists, and if so, rename the new one with a version number; otherwise move it in as-is. Record the final filename in a note and confirm it's in the right folder <!--hard__chrome-files-obsidian__031-->

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__007, absent-entity): data genuinely absent (No email from 'Rahul Mehta' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gmail, star the latest email from 'Rahul Mehta' <!--easy__gmail__007-->
- Medium (3pt) **[Gmail+Obsidian]**: In Gmail, find every email mentioning 'invoice' this month, total the amounts, and note the total in an Obsidian note <!--medium__gmail__007-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__005, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive to check sharing on.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, check if the file 'Q3 Budget.xlsx' has been shared with anyone <!--easy__google-drive__005-->
- Medium (3pt) **[Google Drive+Telegram]**: In Google Drive, filter shared files to show only ones I can edit, star the most recent, and message its name to [contact] on Telegram, with no other text <!--medium__google-drive__004-->
- Medium (3pt) **[Google Drive+Notes]**: In Google Drive, filter Drive search results to only PDFs from this year, download the most recent, and log the filename in a note <!--medium__google-drive-notes__001-->

**[Google Search]**
- Easy (1pt): In Google Search, search for the calories in [food item] <!--easy__google-search__005-->
- Medium (3pt): In Google Search, find a product's warranty terms from its official page, summarize them, and note the coverage period <!--medium__google-search__005-->

**[Notes]**
- Easy (1pt): In Notes, lock a note with a password <!--easy__notes__004-->
- Medium (3pt): In Notes, find and merge two related notes into one, delete the originals, and rename the merged note <!--medium__notes__002-->

**30. [Notes+Files] — DETERMINISTIC**
- Sync my shopping list with what I already bought. Check the Notes list titled 'To Buy' against a Files-stored receipt, write down the items on the receipt, match each item on the list, remove only the items confirmed present, and note the remaining count <!--hard__notes-files__030-->

**[Files]**
- Easy (1pt): In Files, find the largest file in my Downloads <!--easy__files__005-->
- Medium (3pt) **[Files+Obsidian]**: In Files, summarize how storage is split across folders, note the largest category, and check if it exceeds half of total storage <!--medium__files-obsidian__002-->

**[Music]**
- Medium (3pt) **[Music+Obsidian]**: In Music, find songs added to a playlist but never played, remove them, and note in Obsidian how many were removed <!--medium__music__006-->

**[Messages]**
- Medium (3pt): In Messages, filter messages to find ones containing a shared link, open the most recent, and star it <!--medium__messages__006-->

**[Settings]**
- Easy (1pt): In Settings, turn on auto-rotate <!--easy__settings__007-->
- Medium (3pt): In Settings, compare today's battery usage to yesterday's, note the difference, and check which app used the most today <!--medium__settings__005-->

**44. [Settings+Obsidian] — DETERMINISTIC**
- I think I've been on my phone too much. Check today's screen time in Settings, note the total, compare it against yesterday's noted in Obsidian, and set an app timer only if today exceeds yesterday by 30 minutes or more, recording the comparison <!--hard__settings-obsidian__044-->

### Day 11

**[Gmail]**
- Medium (3pt): In Gmail, filter unread emails to keep only 1:1 emails (hide mailing lists), reply 'Thanks!' to the oldest one, and star it <!--medium__gmail__008-->

**92. [Gmail+Messages] — ASK USER**
- An important email needs to get seen. Find the most recent important-looking unread email today in Gmail, forward it to the person who needs to see it, and message them on Messages that it's been forwarded (deliberately no recipient or specific email is named, so the agent must ask the user who to forward it to and which email to forward) <!--hard__gmail-messages__092-->

**[Google Maps]**
- Easy (1pt): In Google Maps, get walking directions to [place] <!--easy__google-maps__005-->
- Medium (3pt) **[Google Maps+Telegram]**: In Google Maps, summarize traffic conditions across three routes to work, pick the best one, start navigation on it, and message [contact] the ETA on Telegram <!--medium__google-maps__004-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__006, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive to preview.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, preview the file 'Q3 Budget.xlsx' without opening it fully <!--easy__google-drive__006-->

**[YouTube]**
<!-- 🔮 HALLUCINATION CONTROL (easy__youtube__004, absent-entity): data genuinely absent (No YouTube channel named 'TechDaily' exists (not searched/subscribed).). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In YouTube, check if the channel 'TechDaily' has posted today <!--easy__youtube__004-->
- Medium (3pt) **[YouTube+Obsidian]**: In YouTube, compare view counts across three videos on the same topic, note which is most popular, save that one, and write the pick in an Obsidian note <!--medium__youtube__005-->

**39. [YouTube+Music] — DETERMINISTIC**
- I heard a song in a video that I want to keep. Check the YouTube video's description for a song mention, record the song name, match it against my Music library, add it only if it isn't already there, and confirm the playlist count updated <!--hard__youtube-music__039-->

**52. [YouTube+Settings] — DETERMINISTIC**
- I want notifications from a channel but not at night. Turn on notifications for the YouTube channel, check its upload history for posting frequency, note how many uploads this week, and mute notifications during 10pm-8am in Settings if it posts more than twice a week, then confirm both settings saved <!--hard__youtube-settings__052-->

**[Chrome]**
- Easy (1pt): In Chrome, check available sizes/colors for a specific product <!--easy__shopping-delivery-browser__004-->
- Medium (3pt): In Chrome, summarize a store's return policy vs. a competitor's, note which is more lenient, and check the return window length for each <!--medium__shopping-delivery-browser__004-->

**[Contacts]**
- Easy (1pt): In Contacts, check recently added contacts <!--easy__contacts__009-->
- Medium (3pt) **[Contacts+Obsidian]**: In Contacts, filter contacts to show only ones added this month, star the most recent, check whether any are missing a phone number, and note in Obsidian how many are missing one <!--medium__contacts__008-->

**[Gallery]**
- Easy (1pt): In Gallery, crop the most recent photo <!--easy__gallery__005-->
- Medium (3pt): In Gallery, find and tag a group of untagged photos with a shared label, confirm the tag applied, and count how many were tagged <!--medium__gallery__006-->

**[Music]**
- Easy (1pt): In Music, search for '[song]' and play it <!--easy__music__009-->

**[Messages]**
- Easy (1pt): In Messages, reply to the most recent thread with a photo attached <!--easy__messages__008-->

**[Settings]**
- Easy (1pt): In Settings, turn on location services <!--easy__settings__008-->
- Medium (3pt): In Settings, compare Wi-Fi vs. mobile data usage this week, note which is higher, and check the total combined usage <!--medium__settings__006-->

### Day 12

**[Google Drive]**
- Easy (1pt): In Google Drive, rename the most recent upload to [X] <!--easy__google-drive__007-->
- Medium (3pt): In Google Drive, rank files in a folder by last-modified date, open the oldest, and note its last-edit date <!--medium__google-drive__006-->

**[Google Photos]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__005, absent-entity): data genuinely absent (No photo exists in Google Photos dated 2023-06-15.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Photos, find a photo from 2023-06-15 <!--easy__google-photos__005-->
- Medium (3pt): In Google Photos, find photos not yet backed up, note how much storage they'd use, and start the backup <!--medium__google-photos__004-->

**[Google Search]**
- Easy (1pt): In Google Search, search for the meaning of an acronym <!--easy__google-search__006-->
- Medium (3pt) **[Google Search+Calendar]**: In Google Search, filter local event results to this weekend only, pick one, and add it to the Calendar <!--medium__google-search__006-->

**[Calendar]**
- Easy (1pt): In Calendar, create an event titled '[X]' for tomorrow at [time] <!--easy__calendar__006-->
- Medium (3pt) **[Calendar+Obsidian]**: In Calendar, list this month's events missing a location field, add one to the nearest event, and note in Obsidian how many gaps remain <!--medium__calendar__006-->

**63. [Calendar+Notes] — DETERMINISTIC**
- Book my most urgent task tomorrow. Find a free 30-minute slot in Calendar, note it, check it against my Notes to-do list for the most urgent unstarted task, book the slot with that task's name, and verify the event saved <!--hard__calendar-notes__063-->

**[Chrome]**
- Easy (1pt): In Chrome, search a shopping site's FAQ for a shipping question <!--easy__shopping-delivery-browser__005-->

**[Contacts]**
- Easy (1pt): In Contacts, add a new contact named [X] with a phone number <!--easy__contacts__010-->
- Medium (3pt) **[Contacts+Obsidian]**: In Contacts, find all contacts missing a phone number, list them, delete the ones with no other info, and log in Obsidian how many remain <!--medium__contacts__009-->

**[Files]**
<!-- 🔮 HALLUCINATION CONTROL (easy__files__006, absent-entity): data genuinely absent (No file named 'report_final_v2.pdf' exists in Downloads.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Files, rename the downloaded file 'report_final_v2.pdf' <!--easy__files__006-->
- Medium (3pt): In Files, find and remove duplicate files in Downloads, note how much storage was freed, and check the folder's new total size <!--medium__files__006-->

**[Phone]**
- Easy (1pt): In Phone, check the total number of calls made today <!--easy__phone__005-->
- Medium (3pt): In Phone, rank missed calls by how recently they came in, return the most recent, and note the callback time <!--medium__phone__005-->

**40. [Phone+Contacts] — DETERMINISTIC**
- I missed a call and don't know who it was. Check Phone for the most recent missed call, write down the number, cross-reference it against Contacts, save it as a new contact only if it isn't already saved, and log the call time in the contact's note <!--hard__phone-contacts__040-->

**[Settings]**
- Easy (1pt): In Settings, turn on Do Not Disturb <!--easy__settings__009-->

**43. [Settings+Calendar] — DETERMINISTIC**
- I have a call coming up and don't want interruptions. Check Settings for whether a calendar event starts in the next hour, note its start time, and if so, schedule Do Not Disturb to match it; otherwise leave it off. Verify the DND window matches the event <!--hard__settings-calendar__043-->

### Day 13

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__009, absent-entity): data genuinely absent (No promotional email from 'Rahul Mehta' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gmail, delete the most recent promotional email from 'Rahul Mehta' <!--easy__gmail__009-->

**[Google Photos]**
- Easy (1pt): In Google Photos, search for videos from last month <!--easy__google-photos__006-->
- Medium (3pt) **[Google Photos+Obsidian]**: In Google Photos, list albums that haven't been viewed recently, delete the least-used one, and note in Obsidian which was removed <!--medium__google-photos__005-->

**[Telegram]**
<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__006, absent-entity): data genuinely absent (No Telegram group named 'Old College Group' exists.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Telegram, check the member list of the group 'Old College Group' <!--easy__telegram__006-->
- Medium (3pt) **[Telegram+Google Maps]**: In Telegram, filter a chat for messages containing an address, get directions to it in Google Maps, and share the ETA back in the chat <!--medium__telegram__004-->
- Medium (3pt) **[Telegram+Notes]**: In Telegram, summarize a group discussion into 3 bullet points, save the summary as a note, and pin the note <!--medium__telegram-notes__001-->

**[Calculator]**
- Easy (1pt): In Calculator, compute a percentage for a school grade <!--easy__calculator__003-->
- Medium (3pt) **[Calculator+Obsidian]**: In Calculator, compute the total cost of two financing plans for the same purchase, compare them, and note in Obsidian which is cheaper <!--medium__calculator__003-->

**20. [Calculator+Telegram+Notes] — DETERMINISTIC**
- Splitting a bill with the group. Compute the split on the Calculator, check each person's share, and if any share exceeds $50, message those people individually on Telegram; otherwise send one group message. Log the total in a note <!--hard__calculator-telegram-notes__020-->

**60. [Calculator+Obsidian+Telegram] — ASK USER**
- Would a loan payment fit my budget? Compute the monthly loan payment on the Calculator, write down the amount, compare it against the budget noted in Obsidian, message the person I handle money with on Telegram only if it doesn't fit, and log whether it fits either way (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__calculator-obsidian-telegram__060-->

**[Chrome]**
- Easy (1pt): In Chrome, search a shopping site for '[product]' and open the top result <!--easy__shopping-delivery-browser__007-->
- Medium (3pt): In Chrome, filter a wishlist/cart preview to only items currently on sale, note the total savings, and check which item has the biggest discount <!--medium__shopping-delivery-browser__006-->

**[Obsidian]**
- Easy (1pt): In Obsidian, rename an existing note <!--easy__obsidian__004-->

**[Notes]**
- Medium (3pt) **[Notes+Calendar]**: In Notes, filter notes to show only ones edited in the last week, open the most recent, check whether it's still unfinished, and set a Calendar reminder to finish it <!--medium__notes__003-->

**[Files]**
- Medium (3pt) **[Files+Telegram]**: In Files, summarize what's taking up the most space this month, free up the biggest offender, and message [contact] on Telegram that storage is freed up <!--medium__files-telegram__001-->

**[Camera]**
- Easy (1pt): In Camera, check how much storage is left for photos/videos <!--easy__camera__006-->
- Medium (3pt): In Camera, record a 5-second slow-motion clip of a moving object, check playback quality, and save it <!--medium__camera__006-->

**[Music]**
- Easy (1pt): In Music, pause the currently playing track <!--easy__music__011-->
- Medium (3pt): In Music, rank my most-played songs this week, rebuild a playlist from the top 10, and name it <!--medium__music__009-->
- Medium (3pt) **[Music+Telegram]**: In Music, compare listening stats between this week and last week, note the difference, and share the summary with [contact] on Telegram <!--medium__music-telegram__001-->

**38. [Music+Telegram+Notes] — ASK USER**
- See how my listening changed this week. Check Music for this week's most-played tracks, note them, compare against last week's most-played, message the person I share music with on Telegram only the tracks new to the list, and save the full comparison in a note (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__music-telegram-notes__038-->

**[Phone]**
- Easy (1pt): In Phone, set a reminder to call [contact] back later today <!--easy__phone__007-->
- Medium (3pt): In Phone, filter today's call log to show only calls over 5 minutes, note the longest, and check who it was with <!--medium__phone__006-->

### Day 14

**[Chrome]**
- Easy (1pt): In Chrome, look up a word's definition <!--easy__chrome__008-->
- Medium (3pt) **[Chrome+Obsidian]**: In Chrome, find yesterday's page about [topic] in my browsing history, summarize what it said, reopen it, and save the summary in an Obsidian note <!--medium__chrome__007-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__008, absent-entity): data genuinely absent (No PDF named 'Q3 Budget.pdf' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, open the PDF 'Q3 Budget.pdf' stored in Drive <!--easy__google-drive__008-->
- Medium (3pt): In Google Drive, find all files over 50MB, list them by size, and delete the largest if unneeded <!--medium__google-drive__007-->

**[Google Search]**
- Easy (1pt): In Google Search, search for a nearby holiday or public event <!--easy__google-search__007-->

**56. [Google Search+Clock] — DETERMINISTIC**
- I'm about to miss my bus. Look up the transit line's next departure via Google Search, write down the time remaining, and set an alarm now if it's within 10 minutes, otherwise set one 5 minutes before the following departure, then verify the alarm time <!--hard__google-search-clock__056-->

**[Clock]**
- Easy (1pt): In Clock, set a 10-minute timer <!--easy__clock__004-->
- Medium (3pt) **[Clock+Obsidian]**: In Clock, set three timers with different durations and labels for a cooking session, confirm all three are running, check which will finish first, and note the timings in Obsidian <!--medium__clock__004-->

**[Files]**
- Easy (1pt): In Files, check which folder is using the most storage <!--easy__files__009-->
- Medium (3pt): In Files, find all screenshots across folders, delete the oldest 10, and check the folder's new total size <!--medium__files__009-->

**69. [Files+Notes] — DETERMINISTIC**
- Free up space safely. Compress several Files into an archive, note its size, match it against the storage limit noted in Notes, delete the originals only if the archive is under the limit, and verify the originals' status <!--hard__files-notes__069-->

**[Camera]**
- Easy (1pt): In Camera, record a 5-second video of my surroundings with sound enabled <!--easy__camera__007-->
- Medium (3pt): In Camera, record a 5-second video and take a photo of the same stationary object, and decide which captures it better <!--medium__camera__007-->

**73. [Camera+Files] — DETERMINISTIC**
- Keep a slow-motion clip under a size limit. Record it with Camera, note its length, check its file size in Files, trim it only if it exceeds 50MB, and verify the final file size afterward <!--hard__camera-files__073-->

**[Gallery]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__006, absent-entity): data genuinely absent (No photos tagged/located at 'Bali' exist in Gallery.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gallery, search the gallery for photos from 'Bali' <!--easy__gallery__006-->
- Medium (3pt) **[Gallery+Obsidian]**: In Gallery, find the 10 photos taking up the most storage, review them, delete the 3 least useful ones, and note the space freed in Obsidian <!--medium__gallery__007-->

**[Phone]**
- Easy (1pt): In Phone, mute the microphone during an active call <!--easy__phone__008-->

**[Settings]**
- Easy (1pt): In Settings, check current battery percentage <!--easy__settings__010-->
- Medium (3pt): In Settings, rank notification-heavy apps by how often they alert today, mute the noisiest, and count remaining unmuted <!--medium__settings__008-->

### Day 15

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__011, absent-entity): data genuinely absent (No noisy email thread from 'Rahul Mehta' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gmail, mute the noisy email thread from 'Rahul Mehta' <!--easy__gmail__011-->
- Medium (3pt) **[Gmail+Telegram]**: In Gmail, filter the inbox to show only emails with attachments from this week, star the 3 most recent, and message [contact] on Telegram to check one of them <!--medium__gmail-telegram__001-->

**[Google Maps]**
- Easy (1pt): In Google Maps, check the weather along today's commute <!--easy__google-maps__007-->
- Medium (3pt) **[Google Maps+Obsidian]**: In Google Maps, find the cheapest parking option near [place], save it as an Obsidian note, and check its distance from [place] <!--medium__google-maps__005-->

**[Google Photos]**
- Easy (1pt): In Google Photos, find the oldest photo in the library <!--easy__google-photos__008-->
- Medium (3pt): In Google Photos, find photos taken with a specific mode (e.g. portrait), determine which one is sharpest, and star it <!--medium__google-photos__006-->

**[YouTube]**
- Easy (1pt): In YouTube, skip the ad on the current video <!--easy__youtube__006-->
- Medium (3pt): In YouTube, filter the Shorts feed for a specific topic, like the 3 best ones, and count how many were liked <!--medium__youtube__006-->

**15. [YouTube+Telegram] — ASK USER**
- Which of my favorite channel's latest videos is doing better? Check its two most recent uploads, note both view counts, compare them, and message the person who cares about this on Telegram only the title of whichever performed better, then confirm they replied (deliberately no recipient or channel is named, so the agent must ask the user who to message and which channel they mean) <!--hard__youtube-telegram__015-->

**[Telegram]**
- Easy (1pt): In Telegram, send my current location to [contact] <!--easy__telegram__007-->
- Medium (3pt) **[Telegram+Obsidian]**: In Telegram, find the 5 most active group chats this week, mute the least relevant one, and note in Obsidian which was muted <!--medium__telegram__005-->

**54. [Telegram+Calendar] — ASK USER**
- Schedule a message to the right person without it landing mid-meeting. Schedule the Telegram message, note the intended send time, check it against Calendar for a conflicting event, shift it by 30 minutes if one exists, and double-check the final scheduled time (deliberately no recipient or message content is specified, so the agent must ask the user who the message is for and what to say) <!--hard__telegram-calendar__054-->

**[Calculator]**
- Easy (1pt): In Calculator, work out an 18% tip on [amount] <!--easy__calculator__004-->
- Medium (3pt) **[Calculator+Telegram]**: In Calculator, compute each roommate's share of a shared bill with different usage levels, message each their share, and log the total bill in a note <!--medium__calculator__005-->

**[Calendar]**
<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__008, absent-entity): data genuinely absent (No calendar event titled 'Team Sync Weekly' exists.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Calendar, delete the calendar event 'Team Sync Weekly' <!--easy__calendar__008-->
- Medium (3pt): In Calendar, filter this week's events to show only ones with more than 2 attendees, check which has the most, and open that one <!--medium__calendar__007-->

**64. [Calendar+Contacts+Telegram] — DETERMINISTIC**
- Make sure every attendee gets the update. Check Calendar for the next occurrence of the recurring event, note the attendees, compare them against Contacts for whether any lack an email, notify only the ones missing an email via Telegram instead, and confirm all attendees were reached <!--hard__calendar-contacts-telegram__064-->

**[Contacts]**
- Easy (1pt): In Contacts, check the phone number saved for [contact] <!--easy__contacts__011-->

**[Messages]**
- Easy (1pt): In Messages, star an important message <!--easy__messages__009-->
- Medium (3pt): In Messages, find all messages from [contact] this week, note how many need replies, and reply to the most recent <!--medium__messages__008-->

### Day 16

**[Chrome]**
- Easy (1pt): In Chrome, check if a website is down <!--easy__chrome__009-->
- Medium (3pt) **[Chrome+Telegram]**: In Chrome, compare flight prices for [route] across two travel sites, note the cheaper option, bookmark it, and send the price to [contact] on Telegram <!--medium__chrome__008-->

**6. [Chrome+Clock+Notes] — DETERMINISTIC**
- I'm planning my morning around the weather. Check tomorrow's forecast via Chrome, record the expected conditions and temperature, and the chance of rain in particular. If rain's expected, set an alarm 15 minutes earlier; if not, leave it. Write down the reason for the decision in Notes <!--hard__chrome-clock-notes__006-->

**48. [Chrome+Obsidian] — DETERMINISTIC**
- Found a coupon and want to make sure I haven't used it. Find the coupon code on a Chrome page, note it, match it against the Obsidian list of already-used codes, save it only if it isn't a duplicate, and label the note with the store name <!--hard__chrome-obsidian__048-->

**[Google Maps]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__008, absent-entity): data genuinely absent (No saved place named 'Bali Cafe' exists in Google Maps.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Maps, check if the saved place 'Bali Cafe' is currently open <!--easy__google-maps__008-->
- Medium (3pt): In Google Maps, filter saved places to show only ones tagged 'restaurant', check which ones are open right now, and star the closest open one <!--medium__google-maps__006-->

**[YouTube]**
- Easy (1pt): In YouTube, add the currently playing video to a new playlist <!--easy__youtube__008-->

**[Clock]**
- Easy (1pt): In Clock, check sunrise/sunset time via the world clock <!--easy__clock__006-->
- Medium (3pt) **[Clock+Calendar]**: In Clock, filter alarms to show only the ones that repeat weekly, disable one, and check against Calendar whether any conflict remains among the rest <!--medium__clock__005-->
- Medium (3pt) **[Clock+Notes]**: In Clock, set a Wind Down schedule based on a target wake-up time, confirm it saved, and log the wake-up time in a note <!--medium__clock-notes__001-->

**[Contacts]**
- Medium (3pt): In Contacts, group several contacts into a new label like 'Family', confirm the count, and star one member <!--medium__contacts__011-->

**65. [Contacts+Google Maps+Notes] — DETERMINISTIC**
- I need to update a contact's address. Confirm the new address on Maps, update the contact, record the old address, match it against Notes for any pending mail noted there, flag it if pending mail exists, and confirm the contact saved <!--hard__contacts-google-maps-notes__065-->

**[Obsidian]**
- Easy (1pt): In Obsidian, add today's date as a heading in a new note <!--easy__obsidian__005-->

**[Notes]**
<!-- 🔮 HALLUCINATION CONTROL (medium__notes__004, absent-entity): data genuinely absent (No note titled 'Old Draft' exists in Notes.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt): In Notes, find the note 'Old Draft' not opened in over a month, delete it, and check whether other notes are still relevant <!--medium__notes__004-->

**[Gallery]**
- Easy (1pt): In Gallery, search for videos only, not photos <!--easy__gallery__007-->

**[Music]**
- Easy (1pt): In Music, skip to the next track <!--easy__music__012-->
- Medium (3pt) **[Music+Telegram]**: In Music, merge two playlists into one, remove duplicates, confirm the final count, and send the new playlist to [contact] on Telegram <!--medium__music__010-->

**[Settings]**
- Medium (3pt): In Settings, compare screen time this week to last week, note the change, and check which day had the most screen time <!--medium__settings__009-->

### Day 17

**[Chrome]**
- Easy (1pt): In Chrome, translate the current page to English <!--easy__chrome__010-->
- Medium (3pt): In Chrome, filter open tabs down to just the ones about [topic], close any duplicates among them, and keep only the most recent <!--medium__chrome__009-->

**87. [Chrome+Google Search+Notes] — ASK USER**
- Can you help me understand something I've been wondering about? Research it via Chrome or Search, summarize the findings in a new note, and pin that note (deliberately no topic or note title is specified, so the agent must ask the user what to research and what to title the note) <!--hard__chrome-google-search-notes__087-->

**[Gmail]**
<!-- 🔮 HALLUCINATION CONTROL (medium__gmail__011, absent-entity): data genuinely absent (No emails from 'Rahul Mehta' exist in the past week.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Gmail+Telegram]**: In Gmail, filter and count how many emails came from 'Rahul Mehta' in the past week, and if more than 10, add the sender to spam and tell 'Rahul Mehta' on Telegram <!--medium__gmail__011-->

**45. [Gmail+Notes] — DETERMINISTIC**
- I want to use a discount code before it expires. Find the email with the discount code in Gmail, check the expiration date, save the code in a note if not expired, otherwise archive the email, and confirm the action taken <!--hard__gmail-notes__045-->

**[Google Search]**
- Easy (1pt): In Google Search, look up a random fact about [topic] <!--easy__google-search__009-->
- Medium (3pt) **[Google Search+Obsidian]**: In Google Search, compare public transit options for a specific route, note the fastest, and save it as an Obsidian note <!--medium__google-search__008-->

**[Clock]**
- Easy (1pt): In Clock, set a timer for boiling eggs <!--easy__clock__007-->
- Medium (3pt): In Clock, set up a repeating interval timer for a workout routine, confirm it starts on the first interval, and label it <!--medium__clock__006-->

**[Calendar]**
- Easy (1pt): In Calendar, add a birthday reminder for [contact] <!--easy__calendar__009-->
- Medium (3pt) **[Calendar+Obsidian]**: In Calendar, list the 5 busiest days this month, note the busiest one, and save it as an Obsidian note <!--medium__calendar__008-->
- Medium (3pt) **[Calendar+Notes]**: In Calendar, summarize tomorrow's schedule into a short morning briefing, save it as a note, and set a reminder to check it in the morning <!--medium__calendar-notes__001-->

**[Notes]**
- Easy (1pt): In Notes, add a photo to an existing note <!--easy__notes__005-->

**[Obsidian]**
- Medium (3pt): In Obsidian, find all notes mentioning a specific person's name, star the most recent, and check whether the oldest one is still accurate <!--medium__obsidian__005-->

**[Gallery]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__009, absent-entity): data genuinely absent (No photo named 'IMG_20250101.jpg' exists in Gallery.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gallery, check the file size of the photo 'IMG_20250101.jpg' <!--easy__gallery__009-->

**[Messages]**
- Easy (1pt): In Messages, send a GIF in a conversation <!--easy__messages__010-->
- Medium (3pt): In Messages, compare message volume from two contacts this week, note who messaged more, and star that contact <!--medium__messages__009-->

### Day 18

**[Google Maps]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__009, absent-entity): data genuinely absent (No saved place named 'Bali Cafe' exists in Google Maps.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Maps, check the distance to the saved place 'Bali Cafe' <!--easy__google-maps__009-->
- Medium (3pt): In Google Maps, filter nearby coffee shops by rating above 4 stars, pick the closest one, and save it to favorites <!--medium__google-maps__008-->
- Medium (3pt) **[Google Maps+Telegram]**: In Google Maps, list the top 5 highest-rated restaurants within a mile, save the top one to favorites, and message [contact] on Telegram suggesting it <!--medium__google-maps-telegram__001-->

**47. [Google Maps+Telegram+Obsidian] — ASK USER**
- I keep going back to the same place and want it handy. Save the frequently visited place as a Maps favorite, rename it with a short label, check whether it's open now, message the person I usually go there with on Telegram only if it is, and note its hours either way (deliberately no recipient or place is named, so the agent must ask the user who to message and which place they keep going back to) <!--hard__google-maps-telegram-obsidian__047-->

**[YouTube]**
- Easy (1pt): In YouTube, resume a recently watched video from where it left off <!--easy__youtube__009-->
- Medium (3pt) **[YouTube+Obsidian]**: In YouTube, list the top 5 recommended videos on the home feed, save the most relevant one to Watch Later, and note in Obsidian why <!--medium__youtube__008-->
- Medium (3pt) **[YouTube+Obsidian]**: In YouTube, summarize a podcast episode's key points from its description, save the summary as a note, and like the video <!--medium__youtube-obsidian__003-->

**[Telegram]**
<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__008, absent-entity): data genuinely absent (No Telegram group named 'Old College Group' exists to mute.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Telegram, mute notifications for the group 'Old College Group' <!--easy__telegram__008-->
- Medium (3pt): In Telegram, summarize what was discussed in a group while I was away, note if action is needed, and reply if so <!--medium__telegram__006-->
- Medium (3pt) **[Telegram+Obsidian]**: In Telegram, summarize a long forwarded article shared in a chat, save the summary as a note, and reply confirming I've read it <!--medium__telegram-obsidian__003-->

**[Calculator]**
- Easy (1pt): In Calculator, convert a temperature between Celsius and Fahrenheit <!--easy__calculator__006-->
- Medium (3pt) **[Calculator+Obsidian]**: In Calculator, compute fuel cost for a trip given distance, mileage, and gas price, compare it to a stated budget, and note the difference in an Obsidian note <!--medium__calculator__006-->
- Medium (3pt) **[Calculator+Notes]**: In Calculator, convert a recipe's measurements from cups to grams across 6 ingredients, log them in a note, and double-check the largest quantity <!--medium__calculator-notes__001-->

**[Obsidian]**
- Easy (1pt): In Obsidian, check the most recently edited note <!--easy__obsidian__006-->

**[Notes]**
- Medium (3pt): In Notes, rank folders by number of notes inside, open the folder with the most, and note the count <!--medium__notes__005-->

**[Files]**
- Easy (1pt): In Files, check total storage used on the device <!--easy__files__010-->
- Medium (3pt) **[Files+Obsidian]**: In Files, filter files larger than 100MB across the whole device, note the largest one, star it, and log its size in an Obsidian note <!--medium__files__010-->

**[Camera]**
- Easy (1pt): In Camera, take a photo of any object with HDR mode on <!--easy__camera__008-->
- Medium (3pt): In Camera, record a 15-second video of my surroundings, trim the first 3 seconds, and save the trimmed version <!--medium__camera__008-->

**[Chrome]**

**88. [Chrome+YouTube+Notes] — ASK USER**
- I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note (deliberately no task is specified, so the agent must ask the user what they want to learn) <!--hard__chrome-youtube-notes__088-->

### Day 19

**[Google Photos]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__009, absent-entity): data genuinely absent (No photo named 'IMG_20250101.jpg' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Photos, rotate the sideways photo 'IMG_20250101.jpg' <!--easy__google-photos__009-->
- Medium (3pt): In Google Photos, group similar-looking photos, flag the extras, and delete them <!--medium__google-photos__007-->

**[Telegram]**
- Easy (1pt): In Telegram, send a voice message to [contact] <!--easy__telegram__009-->
- Medium (3pt) **[Telegram+Obsidian]**: In Telegram, summarize the last 10 messages in a busy group chat, save the summary in an Obsidian note, reply with a one-line update, and pin my reply <!--medium__telegram__007-->

**[Google Search]**
- Easy (1pt): In Google Search, check the current temperature outside <!--easy__google-search__010-->

**18. [Google Search+Telegram+Clock] — ASK USER**
- I'm going to grab something from the place I'm going to. Look up its hours via Google Search, note whether it's open now, and if it is, message the person I'm going with on Telegram suggesting we go now; otherwise message the reopening time and set an alarm for it (deliberately no place or recipient is specified, so the agent must ask the user where they are going and who to message) <!--hard__google-search-telegram-clock__018-->

**[Calculator]**
- Easy (1pt): In Calculator, split a bill evenly between 4 people <!--easy__calculator__007-->
- Medium (3pt): In Calculator, compute how many months to pay off a debt at a fixed monthly payment, note the payoff date, and check if it's before a stated target date <!--medium__calculator__007-->

**[Clock]**
- Easy (1pt): In Clock, check what time it is in [city] <!--easy__clock__008-->
- Medium (3pt) **[Clock+Calendar]**: In Clock, convert the '[meeting title]' time across two timezones, set a matching local alarm, and label it with the timezone <!--medium__clock__007-->
- Medium (3pt) **[Clock+Telegram]**: In Clock, compare the current time across three saved world-clock cities, note which is furthest ahead, and message [contact] on Telegram the best time to call <!--medium__clock-telegram__001-->

**[Calendar]**
<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__010, absent-entity): data genuinely absent (No calendar event titled 'Team Sync Weekly' exists to add a note to.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Calendar, add a note to the event 'Team Sync Weekly' <!--easy__calendar__010-->

**[Chrome]**
- Easy (1pt): In Chrome, check the return/refund policy for a recent purchase on a shopping site <!--easy__shopping-delivery-browser__010-->
- Medium (3pt) **[Chrome+Telegram]**: In Chrome, filter a product category by price range, check which item has the best rating within it, note it, and send it to [contact] on Telegram <!--medium__shopping-delivery-browser__008-->

**[Camera]**
- Easy (1pt): In Camera, switch to the front-facing lens and take a photo of myself <!--easy__camera__009-->
- Medium (3pt): In Camera, compare a photo taken in normal mode vs. night mode of the same dimly lit scene, keep the better one, and delete the other <!--medium__camera__009-->

**[Phone]**
- Medium (3pt): In Phone, summarize today's voicemails into a short list of who to call back, call the first one, and note the call outcome <!--medium__phone__008-->

**41. [Phone+Google Search+Telegram] — ASK USER**
- Got a call from an unknown number. Check the missed call in Phone, look up the number via Google Search, note what it matches, and message the person who usually handles this on Telegram only if it's a known business; otherwise flag it as possible spam and record the outcome (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__phone-google-search-telegram__041-->

### Day 20

**[Google Maps]**
- Easy (1pt): In Google Maps, search for the nearest [type of place] <!--easy__google-maps__010-->

**4. [Google Maps+Telegram+Clock] — ASK USER**
- Someone wants to know when I'll reach my destination. Check Maps for the live ETA, write down the exact minutes, and message the person who asked on Telegram with it. If it's over 30 minutes, set an alarm for that arrival time; if not, just send 'close by'. Then verify the message went through (deliberately no destination or recipient is specified, so the agent must ask the user where they are headed and who wants to know) <!--hard__google-maps-telegram-clock__004-->

**[Google Photos]**
- Easy (1pt): In Google Photos, find a screenshot from earlier today <!--easy__google-photos__010-->
- Medium (3pt) **[Google Photos+Obsidian]**: In Google Photos, filter the library to show only videos over 1 minute long, delete the longest if unneeded, count what's left, and note the count in Obsidian <!--medium__google-photos__008-->
- Medium (3pt) **[Google Photos+Telegram]**: In Google Photos, find the 5 most recent photos of [subject], add them to a new album, and share the album name with [contact] on Telegram <!--medium__google-photos-telegram__001-->

**[Telegram]**
- Easy (1pt): In Telegram, turn off read receipts for a specific chat <!--easy__telegram__010-->
- Medium (3pt) **[Telegram+Contacts]**: In Telegram, find contacts who haven't messaged in over a month (check Contacts), send one of them a check-in, and note who I messaged <!--medium__telegram__008-->

**[Clock]**
- Easy (1pt): In Clock, set a quick 5-minute timer <!--easy__clock__009-->

**[Calendar]**
- Easy (1pt): In Calendar, see how many events are scheduled tomorrow <!--easy__calendar__012-->
- Medium (3pt): In Calendar, summarize which days this week are meeting-heavy vs. open, block the open day for focus time, and note the meeting-heaviest day in a reminder <!--medium__calendar__010-->

**[Contacts]**
<!-- 🔮 HALLUCINATION CONTROL (easy__contacts__013, absent-entity): data genuinely absent (No contact named 'Rahul Mehta' exists in Contacts.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Contacts, add a birthday to the contact 'Rahul Mehta' <!--easy__contacts__013-->
- Medium (3pt) **[Contacts+Obsidian]**: In Contacts, merge duplicate contacts sharing the same phone number, confirm only one remains, check its info is complete, and log the merge in an Obsidian note <!--medium__contacts__012-->

**[Camera]**
- Easy (1pt): In Camera, take a photo of any nearby object in portrait mode <!--easy__camera__010-->
- Medium (3pt): In Camera, take a burst of 5 photos of the same object, keep only the best 2, and delete the rest <!--medium__camera__010-->

**71. [Camera+Gallery+Telegram] — DETERMINISTIC**
- Taking a panorama and don't want duplicates. Take it with Camera, check Gallery for whether a similar panorama from the same location already exists, compare the two for sharpness, share only the sharper one via Telegram, and confirm the recipient received it <!--hard__camera-gallery-telegram__071-->

**[Gallery]**
<!-- 🔮 HALLUCINATION CONTROL (medium__gallery__010, absent-entity): data genuinely absent (No photos from the 'Bali' trip exist in Gallery (album absent).). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt): In Gallery, filter the 'Bali' trip photos to find ones missing location metadata, note which album has the most, and star one from that album <!--medium__gallery__010-->

**[Phone]**
- Easy (1pt): In Phone, check my most recent missed call <!--easy__phone__010-->
- Medium (3pt): In Phone, compare this week's call volume to last week's, note the difference, and check which day had the most calls <!--medium__phone__009-->

### Day 21

**[Google Maps]**
- Easy (1pt): In Google Maps, find the nearest ATM <!--easy__google-maps__011-->
- Medium (3pt) **[Google Maps+Notes]**: In Google Maps, list all saved places visited this month, determine which category (restaurant, park, shop) was visited most, and log that category in a note <!--medium__google-maps-notes__001-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__010, absent-entity): data genuinely absent (No document named 'Q3 Budget.xlsx' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, open the document 'Q3 Budget.xlsx' <!--easy__google-drive__010-->
<!-- 🔮 HALLUCINATION CONTROL (medium__google-drive__009, absent-entity): data genuinely absent (No files shared by 'Rahul Mehta' exist in Google Drive.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Google Drive+Telegram]**: In Google Drive, find every file shared by 'Rahul Mehta', list them, count how many are documents vs. sheets, and message the breakdown to 'Rahul Mehta' on Telegram <!--medium__google-drive__009-->

**[YouTube]**
- Easy (1pt): In YouTube, check comments on the current video <!--easy__youtube__011-->
- Medium (3pt) **[YouTube+Obsidian]**: In YouTube, compare two videos on the same topic, note which is more thorough, save that one to Watch Later, and note the pick in Obsidian <!--medium__youtube__010-->

**[Google Search]**
- Medium (3pt): In Google Search, find conflicting information across two sources on [topic], summarize it, and note which seems more credible <!--medium__google-search__010-->

**[Calculator]**
- Easy (1pt): In Calculator, divide [amount] between [number] people <!--easy__calculator__008-->
- Medium (3pt) **[Calculator+Obsidian]**: In Calculator, compute compound interest on a savings amount over 3 years, note the final total in an Obsidian note, and compare it to the original principal <!--medium__calculator__008-->

**58. [Calculator+Obsidian] — DETERMINISTIC**
- Scaling a recipe up and need to know what to buy. Convert it from 4 to 6 servings on the Calculator, record the new quantities, check them against my Obsidian pantry list, add only the ingredients not already on hand, and confirm the shopping note updated <!--hard__calculator-obsidian__058-->

**[Chrome]**
- Easy (1pt): In Chrome, search for a specific product's warranty information <!--easy__shopping-delivery-browser__011-->
- Medium (3pt): In Chrome, compare loyalty/rewards programs across two shopping sites, note which offers more value, and check the sign-up requirements for each <!--medium__shopping-delivery-browser__009-->

**[Notes]**
- Easy (1pt): In Notes, duplicate an existing note <!--easy__notes__006-->

**[Obsidian]**
- Medium (3pt): In Obsidian, summarize a shopping-list note into categories, reorganize the note accordingly, and rename it <!--medium__obsidian__006-->

**[Camera]**
- Easy (1pt): In Camera, take a burst of 5 photos of the same object quickly <!--easy__camera__012-->

**[Settings]**
- Easy (1pt): In Settings, enable dark theme <!--easy__settings__013-->
- Medium (3pt): In Settings, filter apps to find ones not opened in over a month, uninstall one, and check whether the rest free enough storage <!--medium__settings__010-->

**[Google Photos]**

**51. [Photos+Obsidian] — DETERMINISTIC**
- I deleted a photo I actually wanted. Restore it from Photos trash, note its date, compare it against my Obsidian trip log, add it to the matching trip's note, and confirm it's no longer in the trash <!--hard__photos-obsidian__051-->

### Day 22

**[Google Photos]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__012, absent-entity): data genuinely absent (No photo named 'IMG_20250101.jpg' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Photos, crop the photo 'IMG_20250101.jpg' <!--easy__google-photos__012-->
- Medium (3pt) **[Google Photos+Obsidian]**: In Google Photos, filter screenshots older than a month, count them, delete them in bulk, and note the count in Obsidian <!--medium__google-photos__010-->

**[Telegram]**
- Easy (1pt): In Telegram, send a photo with a caption to [contact] <!--easy__telegram__011-->

**55. [Telegram+Obsidian] — ASK USER**
- Keep my notification sounds consistent per contact. Check the Telegram chat's notification sound setting, record the current sound, compare it against the preferred sound for that contact, update it only if it doesn't match, and confirm the change (deliberately no chat or preferred notification sound is specified, so the agent must ask the user which chat and what sound to use) <!--hard__telegram-obsidian__055-->

**[Calculator]**
- Easy (1pt): In Calculator, compute a percentage discount on [amount] <!--easy__calculator__009-->
- Medium (3pt): In Calculator, compute a currency-adjusted price for the same product in two countries, compare them, and note the cheaper one <!--medium__calculator__009-->

**[Clock]**
- Easy (1pt): In Clock, start the stopwatch <!--easy__clock__010-->
- Medium (3pt) **[Clock+Calendar]**: In Clock, set a recurring alarm, confirm it doesn't clash with an existing Calendar event, and label it accordingly <!--medium__clock__009-->

**[Chrome]**
- Easy (1pt): In Chrome, check if a store has a physical location nearby via its website <!--easy__shopping-delivery-browser__012-->
- Medium (3pt): In Chrome, rank menu items on a delivery site by rating for a specific restaurant, pick the top one, and check its price <!--medium__shopping-delivery-browser__010-->

**[Obsidian]**
- Easy (1pt): In Obsidian, move a note into a folder <!--easy__obsidian__007-->
- Medium (3pt): In Obsidian, find notes containing a specific date mentioned, list them, and open the most recent <!--medium__obsidian__007-->

**67. [Obsidian+Calendar] — DETERMINISTIC**
- I don't want to forget an important note. Pin it to the top of the Obsidian list, note its due date, check it against Calendar, create a matching calendar event only if one doesn't already exist, and double-check the note stays pinned <!--hard__obsidian-calendar__067-->

**[Camera]**
- Easy (1pt): In Camera, record a 10-second video of my surroundings <!--easy__camera__013-->

**[Music]**
- Easy (1pt): In Music, shuffle the current playlist <!--easy__music__014-->
<!-- 🔮 HALLUCINATION CONTROL (medium__music__012, absent-entity): data genuinely absent (No playlists named 'Chill' or 'Focus' exist in Music.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Music+Notes]**: In Music, find and remove duplicate songs across the 'Chill' and 'Focus' playlists, confirm the count after, rename one playlist to avoid future confusion, and note the result <!--medium__music__012-->
- Medium (3pt) **[Music+Telegram]**: In Music, summarize what a new album is about based on track titles, decide whether to add it, and message [contact] on Telegram my verdict <!--medium__music-telegram__002-->

**[Phone]**
- Easy (1pt): In Phone, merge two calls into a conference call <!--easy__phone__011-->
- Medium (3pt): In Phone, filter call history to find calls from unknown numbers, block the most frequent one, and note the count <!--medium__phone__010-->

### Day 23

**[Chrome]**
- Easy (1pt): In Chrome, clear browsing history from the last hour <!--easy__chrome__012-->
- Medium (3pt) **[Chrome+Notes]**: In Chrome, filter bookmarks to show only ones added this month, delete any duplicates, count what's left, and note the count <!--medium__chrome__011-->

**[Google Maps]**
- Medium (3pt): In Google Maps, find the nearest [type of place] with rating above 4.5 and wheelchair access, save it as a favorite, and check its hours <!--medium__google-maps__011-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__011, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive Trash.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, restore the file 'Q3 Budget.xlsx' from Trash <!--easy__google-drive__011-->
- Medium (3pt) **[Google Drive+Notes]**: In Google Drive, compare two versions of the same document, note what changed in a note, and keep the latest <!--medium__google-drive__010-->

**[Telegram]**
- Easy (1pt): In Telegram, check unread messages across all chats <!--easy__telegram__012-->
- Medium (3pt) **[Telegram+Notes]**: In Telegram, search across all chats for a keyword, list which chats mention it, reply to the most recent, and note the matches <!--medium__telegram__010-->

**[Calculator]**
- Easy (1pt): In Calculator, compute a running total from a list of numbers read aloud <!--easy__calculator__011-->

**[Obsidian]**
<!-- 🔮 HALLUCINATION CONTROL (easy__obsidian__009, absent-entity): data genuinely absent (No folder named 'Old Projects' exists in the Obsidian vault.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Obsidian, check how many notes are in the 'Old Projects' folder <!--easy__obsidian__009-->
- Medium (3pt): In Obsidian, summarize my 5 most recently edited notes into one overview note, star it, and pin it to the top <!--medium__obsidian__008-->

**[Notes]**
- Medium (3pt) **[Notes+Telegram]**: In Notes, summarize a long meeting note into 3 action items, save them as a checklist, and share them with [contact] on Telegram <!--medium__notes-telegram__002-->

**[Gallery]**
- Easy (1pt): In Gallery, set a specific photo as a contact's photo <!--easy__gallery__012-->
- Medium (3pt) **[Gallery+Notes]**: In Gallery, filter for blurry or near-duplicate photos, review them, clean them up, and note how many were removed <!--medium__gallery__011-->

**75. [Gallery+Settings+Obsidian] — DETERMINISTIC**
- I want a fresh wallpaper. Set a Gallery photo as wallpaper via Settings, check the Obsidian log for whether it was already used as wallpaper this month, star the photo, update the log only if it's a new choice, and confirm the wallpaper applied <!--hard__gallery-settings-obsidian__075-->

**83. [Gallery+Obsidian+Telegram] — ASK USER**
- Is my trip-place photo count a record? Check Gallery for photos taken on the trip, note the count, cross-reference it against my Obsidian travel log, message the person I share travel updates with on Telegram the total count only if it's a new personal best, and update the log (deliberately no place or recipient is specified, so the agent must ask the user which place they mean and who to message) <!--hard__gallery-obsidian-telegram__083-->

**[Messages]**
- Easy (1pt): In Messages, check the spam/blocked messages folder <!--easy__messages__012-->
- Medium (3pt): In Messages, rank threads by number of unread messages, open the top one, and reply to the most recent message <!--medium__messages__011-->
- Medium (3pt) **[Messages+Obsidian]**: In Messages, summarize a group thread's discussion while I was away, save the summary as a note, and reply if action is needed <!--medium__messages-obsidian__001-->

**[Settings]**
- Easy (1pt): In Settings, check the device's current software version <!--easy__settings__014-->
- Medium (3pt): In Settings, rank apps by notification count this week, turn off notifications for the noisiest, and note the change <!--medium__settings__011-->

### Day 24

**[Chrome]**
- Easy (1pt): In Chrome, open a new incognito tab <!--easy__chrome__013-->
- Medium (3pt) **[Chrome+Notes]**: In Chrome, search for step-by-step instructions for [task], summarize the steps, and save as a checklist note <!--medium__chrome__012-->

**[YouTube]**
- Easy (1pt): In YouTube, check how long a video is before playing it <!--easy__youtube__013-->
- Medium (3pt): In YouTube, rank saved playlists by number of videos, open the largest, and star its top video <!--medium__youtube__011-->

**96. [YouTube] — ASK USER**
- I need this explained simply. Find a video that explains what I'm trying to understand in simple terms on YouTube and save it to Watch Later (deliberately no topic is specified, so the agent must ask the user what to explain) <!--hard__youtube__096-->

**[Google Search]**
- Easy (1pt): In Google Search, check today's top news headline for [topic] <!--easy__google-search__012-->
- Medium (3pt) **[Google Search+Notes]**: In Google Search, search for step-by-step instructions, summarize into a checklist, and save it as a note <!--medium__google-search__011-->

**[Calculator]**
- Easy (1pt): In Calculator, compute the square root of a number <!--easy__calculator__013-->
- Medium (3pt) **[Calculator+Calendar]**: In Calculator, compute the break-even point for a side project's costs vs. earnings, note the month it breaks even, and check it against the deadline in Calendar <!--medium__calculator__011-->

**[Clock]**
- Easy (1pt): In Clock, set an alarm for a nap <!--easy__clock__011-->
- Medium (3pt): In Clock, set a bedtime schedule, check it doesn't conflict with an early alarm, and confirm the schedule saved <!--medium__clock__010-->

**[Files]**
<!-- 🔮 HALLUCINATION CONTROL (easy__files__012, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Files to move to Trash.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Files, move the file 'Q3 Budget.xlsx' to the Trash <!--easy__files__012-->
- Medium (3pt): In Files, rank folders by total size, open the largest, and note what's inside <!--medium__files__011-->

**[Gallery]**
<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__013, absent-entity): data genuinely absent (No album named 'Bali' exists in Gallery.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Gallery, check the total number of videos in the 'Bali' album <!--easy__gallery__013-->
- Medium (3pt): In Gallery, merge two albums covering the same event into one, delete the duplicate album, and rename the merged album <!--medium__gallery__012-->

**85. [Gallery] — ASK USER**
- I want the best shot of my friend for their profile. Choose the most flattering photo of the person from the Gallery album (deliberately no album or person is specified on the test device, so the agent must ask the user which album and which person they mean) <!--hard__gallery__085-->

### Day 25

**[Gmail]**
- Easy (1pt): In Gmail, check the subject line of the oldest unread email <!--easy__gmail__013-->
- Medium (3pt) **[Gmail+Notes]**: In Gmail, gather today's promotional emails, summarize into a note on what to unsubscribe from, and delete the oldest one <!--medium__gmail__012-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__012, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive to delete.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, delete the file 'Q3 Budget.xlsx' from Drive <!--easy__google-drive__012-->
- Medium (3pt) **[Google Drive+Notes]**: In Google Drive, filter Drive to show only files shared with me, check which ones I can edit versus view-only, star the most recent editable one, and note the edit access <!--medium__google-drive__011-->

**[YouTube]**
- Easy (1pt): In YouTube, subscribe to the channel of the video currently playing <!--easy__youtube__014-->

**[Telegram]**
- Easy (1pt): In Telegram, star an important message for later <!--easy__telegram__013-->

**[Google Search]**
- Easy (1pt): In Google Search, look up a unit conversion <!--easy__google-search__013-->
- Medium (3pt): In Google Search, find the pros and cons of [a decision], summarize them, and note a leaning <!--medium__google-search__012-->

**90. [Google Search+Calendar] — ASK USER**
- There was an event I read about that I don't want to lose track of. Search for the event via Google Search, find a date mentioned in the results, create a calendar event on that date titled with the topic, and set a reminder for it (deliberately no topic is specified, so the agent must ask the user what event they read about) <!--hard__google-search-calendar__090-->

**[Calendar]**
- Easy (1pt): In Calendar, check the time of the next event after lunch <!--easy__calendar__013-->
- Medium (3pt) **[Calendar+Notes]**: In Calendar, find a free 30-minute slot tomorrow, book it as 'Focus time', set a reminder for it, and log what you'll focus on in a note <!--medium__calendar__011-->

**[Chrome]**
- Easy (1pt): In Chrome, search for '[product]' on a shopping site and check its current price <!--easy__shopping-delivery-browser__013-->
- Medium (3pt): In Chrome, rank three similar restaurants on a delivery site by rating and delivery time, pick one, and check its current wait time <!--medium__shopping-delivery-browser__011-->

**[Files]**
<!-- 🔮 HALLUCINATION CONTROL (easy__files__013, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Files.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Files, search for a file named 'Q3 Budget.xlsx' <!--easy__files__013-->
- Medium (3pt): In Files, filter files by type to isolate video files over 500MB, delete the largest, and note the size freed <!--medium__files__012-->

**[Music]**
- Easy (1pt): In Music, check the lyrics of the current song <!--easy__music__015-->
- Medium (3pt): In Music, rank followed artists by how often they're played, unfollow the least-played, and note who was unfollowed <!--medium__music__013-->

**72. [Music] — ASK USER**
- I want a high-energy workout playlist. Curate a workout playlist in Music based on song energy, with no explicit song list given (deliberately no song list or energy preference exists on the test device, so the agent must ask the user how long it should be and what energy level they want) <!--hard__music__072-->

### Day 26

**[Chrome]**
- Easy (1pt): In Chrome, bookmark the current page <!--easy__chrome__014-->

**[Google Maps]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__014, absent-entity): data genuinely absent (No place named 'Bali Cafe' exists on Google Maps (not searched/saved).). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Maps, look up the opening hours for 'Bali Cafe' <!--easy__google-maps__014-->
- Medium (3pt) **[Google Maps+Notes]**: In Google Maps, summarize the reviews for [place] into pros and cons, note the overall rating, and save both as a note <!--medium__google-maps__013-->

**86. [Maps+Telegram] — ASK USER**
- I could use a coffee. Find the highest-rated coffee shop within a mile that's open now on Maps, save it to favorites, and message the person I usually meet for coffee on Telegram its name and location (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__maps-telegram__086-->

**[YouTube]**
- Easy (1pt): In YouTube, check the watch history for today <!--easy__youtube__015-->
- Medium (3pt): In YouTube, find the 3 most relevant tutorial videos for [topic], save them to a new playlist, and name the playlist <!--medium__youtube__013-->

**[Telegram]**
<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__014, absent-entity): data genuinely absent (No Telegram contact named 'Rahul Mehta' exists.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Telegram, check the last-seen time for 'Rahul Mehta' <!--easy__telegram__014-->
- Medium (3pt) **[Telegram+Notes]**: In Telegram, rank groups by message volume today, mute the noisiest one, count remaining unmuted groups, and note the count <!--medium__telegram__012-->

**[Calculator]**
- Easy (1pt): In Calculator, add [numberA] and [numberB] <!--easy__calculator__014-->
- Medium (3pt) **[Calculator+Notes]**: In Calculator, compute overtime pay given an hourly rate and extra hours across a week, note the total pay in a note, and compare it to the regular weekly pay <!--medium__calculator__012-->
- Medium (3pt) **[Calculator+Calendar]**: In Calculator, compute a monthly savings plan to hit a goal amount in 6 months, log the monthly figure in a note, and set a calendar reminder to check progress <!--medium__calculator-calendar__001-->

**[Calendar]**
- Easy (1pt): In Calendar, check today's schedule at a glance <!--easy__calendar__014-->

**[Camera]**
- Easy (1pt): In Camera, turn on grid lines and take a photo of a straight edge (like a door frame) using them for alignment <!--easy__camera__015-->
- Medium (3pt): In Camera, take 5 photos of the same stationary object, identify the sharpest one, and delete the rest <!--medium__camera__013-->
- Medium (3pt) **[Camera+Telegram]**: In Camera, take photos of the same distant object at 3 different zoom levels, pick the best framing, and share it via Telegram <!--medium__camera-telegram__001-->

**[Messages]**
- Easy (1pt): In Messages, check my unread messages <!--easy__messages__013-->
- Easy (1pt): In Messages, send an emoji reaction to a specific message <!--easy__messages__014-->
- Medium (3pt): In Messages, filter threads to find ones with no reply in over 2 weeks, reply to the oldest, and note the gap <!--medium__messages__012-->

**[Phone]**
- Easy (1pt): In Phone, check the contact name for an unknown incoming number <!--easy__phone__013-->
- Medium (3pt): In Phone, find repeat calls from the same unknown number, block it as possible spam, and note the block <!--medium__phone__012-->

**91. [Phone+Notes+Calendar] — DETERMINISTIC**
- I've got a voicemail I need to act on. Check the most recent voicemail, note the key detail in a note, and add a calendar follow-up for it <!--hard__phone-notes-calendar__091-->

### Day 27

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__014, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive to star.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, star the file 'Q3 Budget.xlsx' <!--easy__google-drive__014-->
- Medium (3pt) **[Google Drive+Telegram]**: In Google Drive, summarize comments left on a shared document, reply to the most recent one, star the document, and tell [contact] on Telegram you replied <!--medium__google-drive__012-->
- Medium (3pt) **[Google Drive+Telegram]**: In Google Drive, summarize the contents of a specific document in 2-3 sentences, save the summary as a note, and message [contact] on Telegram that it's ready <!--medium__google-drive-telegram__001-->

**89. [Google Drive] — ASK USER**
- Leave feedback on a document a colleague shared. Find it in Google Drive, read it, add a comment with feedback on its main point, and note which document I commented on (deliberately no person is named for the shared document, so the agent must ask the user who shared it) <!--hard__drive__089-->

**[Google Photos]**
- Easy (1pt): In Google Photos, mark the most recent photo as a favorite <!--easy__google-photos__014-->
- Medium (3pt) **[Google Photos+Notes]**: In Google Photos, find and remove duplicate photos, note how much storage was freed, and save that in a note <!--medium__google-photos__012-->

**[Clock]**
- Easy (1pt): In Clock, set a bedtime reminder <!--easy__clock__013-->
- Medium (3pt) **[Clock+Notes]**: In Clock, rank currently running timers by time remaining, cancel the longest if not needed, and note which one will finish first <!--medium__clock__012-->

**[Chrome]**
- Easy (1pt): In Chrome, check the estimated delivery date before adding to cart <!--easy__shopping-delivery-browser__015-->
- Medium (3pt): In Chrome, find the 3 highest-rated items in a product category, note the top choice, and check its current price <!--medium__shopping-delivery-browser__012-->

**[Files]**
- Easy (1pt): In Files, check available storage on an SD card if present <!--easy__files__014-->
- Medium (3pt): In Files, rank recently downloaded files by size, delete the largest if unneeded, and note the result <!--medium__files__013-->

**[Gallery]**
- Easy (1pt): In Gallery, check how many photos were taken today <!--easy__gallery__014-->
- Medium (3pt): In Gallery, rank videos by length, flag the longest ones for review, and delete one if unneeded <!--medium__gallery__013-->

**[Messages]**
<!-- 🔮 HALLUCINATION CONTROL (easy__messages__015, absent-entity): data genuinely absent (No conversation with 'Rahul Mehta' exists in Messages.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Messages, mute notifications for the thread with 'Rahul Mehta' <!--easy__messages__015-->
- Medium (3pt): In Messages, rank contacts by how recently they messaged, reply to the least recent, and note the reply time <!--medium__messages__013-->

**[Settings]**
- Easy (1pt): In Settings, turn on Bluetooth <!--easy__settings__015-->
- Medium (3pt): In Settings, check which apps used the most battery today, rank the top 3, and restrict the worst one <!--medium__settings__013-->

**[Telegram]**

**100. [Telegram] — ASK USER**
- Decline that invitation for me, politely. Open the Telegram chat with the person who invited me, find the recent invitation, draft a polite decline reply referencing it, and send it (deliberately no sender or tone is named for the invitation, so the agent must ask the user who invited them and how politely to decline) <!--hard__telegram__100-->

### Day 28

**[Gmail]**
- Easy (1pt): In Gmail, open the most recent email with an attachment <!--easy__gmail__015-->
- Medium (3pt) **[Gmail+Telegram]**: In Gmail, find the 3 most frequent promotional senders, unsubscribe from them, add those emails to spam, and message [contact] on Telegram that you cleaned up <!--medium__gmail__013-->

**93. [Gmail] — ASK USER**
- There's an urgent email I should deal with. Find the most recent unread email marked important today in Gmail, reply to it with an appropriate short response, and star it (deliberately no reply content is specified, so the agent must ask the user what to respond) <!--hard__gmail__093-->

**[Google Drive]**
<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__015, absent-entity): data genuinely absent (No file named 'Q3 Budget.xlsx' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Google Drive, check the last-modified date of the file 'Q3 Budget.xlsx' <!--easy__google-drive__015-->

**[Google Photos]**
- Easy (1pt): In Google Photos, delete the most recent screenshot <!--easy__google-photos__015-->
- Medium (3pt): In Google Photos, filter for photos with faces not yet tagged, tag the 3 most recent, and check whether any remain fully untagged <!--medium__google-photos__013-->

**[Google Search]**
- Easy (1pt): In Google Search, search for tomorrow's sunrise time <!--easy__google-search__014-->
- Medium (3pt) **[Google Search+Notes]**: In Google Search, filter results to only ones from official/government sites, open the most relevant, bookmark it, and save the link in a note <!--medium__google-search__013-->

**98. [Google Search+Obsidian] — ASK USER**
- Point me to a source I can trust. Find the most reputable-seeming source discussing what I asked about via Search (official or a major outlet), open it, and save the link in a note (deliberately no topic or note is specified, so the agent must ask the user what to look up and which note to save the link in) <!--hard__google-search-obsidian__098-->

**[Clock]**
- Easy (1pt): In Clock, delete an existing alarm <!--easy__clock__014-->
- Medium (3pt): In Clock, set an alarm that accounts for a timezone change on travel day, confirm the local time, and label it <!--medium__clock__013-->

**[Calendar]**
<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__015, absent-entity): data genuinely absent (No calendar event titled 'Team Sync Weekly' exists to reschedule.). Correct = honest failure; do NOT fabricate. -->
- Easy (1pt): In Calendar, move the 'Team Sync Weekly' meeting two hours later and notify attendees <!--easy__calendar__015-->
- Medium (3pt): In Calendar, find all events tagged 'work' this week, total the hours booked, and note the total <!--medium__calendar__013-->

**[Contacts]**
- Easy (1pt): In Contacts, add a nickname to an existing contact <!--easy__contacts__014-->
- Medium (3pt) **[Contacts+Notes]**: In Contacts, find contacts with an outdated area code, update the most recent one, and note how many remain <!--medium__contacts__013-->

**[Gallery]**
- Easy (1pt): In Gallery, delete the most recent photo <!--easy__gallery__015-->

**[Phone]**
- Easy (1pt): In Phone, check missed calls from today only <!--easy__phone__015-->
- Medium (3pt): In Phone, find calls from this week not yet logged with a note, add a note to the most recent, and count the rest <!--medium__phone__013-->
- Medium (3pt) **[Phone+Clock]**: In Phone, summarize a voicemail's key detail, decide whether to call back, and set a reminder if so <!--medium__phone-clock__001-->

