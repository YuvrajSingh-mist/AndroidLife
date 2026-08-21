# DrainBench: The 28-Day Survival Schedule — runnable 530-task set

This is the **canonical runnable schedule**: the deterministic 530-task corpus
(216 easy / 242 medium / 72 hard = 36 ASK USER / 36 DETERMINISTIC), landing each
day at the real-world ~9-10 distinct-app density (see
docs/app-usage-grounding.md).

This file is the **source of truth for the runnable set**: edit it, then run
`scripts/export_530_dataset.py` to regenerate `DailyBench_530_v1.json` / `.jsonl`.
Each task line carries its `task_id` in an HTML comment, so ids survive edits.
Resync from the JSON with `scripts/export_530_markdown.py`.

---

## The 28-Day Schedule

### Day 1

**[Google Search]**
- Medium (3pt): I'm curious about [topic]. Google it, skim the two best results, and give me a one-line takeaway from each <!--medium__google-search__001-->

**[Google Photos]**
- Easy (1pt): Hide the specific photo taken about an hour back from the main view in Google Photos <!--easy__gallery__001-->

**[Messages]**
- Medium (3pt): Find all unread Messages from this week that contain an unanswered question, answer the most recent with "Will get back to you fr in some time!", and tell me the question you answered <!--medium__messages__001-->

**[Camera]**
- Medium (3pt): I'm taking a portrait this evening, so set up the Camera: turn on AI enhancement mode and portrait mode. <!--medium__camera__001-->

**[Calendar]**
- Easy (1pt): Add my current location to my 'Lunch with Maa' event in Calendar today <!--easy__calendar__001-->

**[Chrome]**
- Easy (1pt): Save the page I'm on right now in Chrome so I can read it offline later <!--easy__chrome__001-->

**[Camera]**
- Easy (1pt): Take a photo of any object on my desk with the Camera and save it with an appropriate name for the object captured <!--easy__camera__001-->

**[Phone]**
- Easy (1pt): In Phone, message the most recent unknown number with "who's this?" <!--easy__phone__001-->

**[Messages]**
- Easy (1pt): Search my Messages for the word '[search word]' <!--easy__messages__001-->

**1. [Google Search+Obsidian+Telegram] — ASK USER SINGLE**
- I'm tracking [stock name] and only want to hear about it when it matters. Check its current value via Google Search against the threshold in my '[stock note title]' Obsidian note, note today's value, compare it to the last recorded value in that Obsidian note, message the person I follow this stock with on Telegram only if it has crossed the threshold since then, and update the Obsidian note with today's value (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__google-search-obsidian-telegram__057-->

- Medium (3pt) **[Google Photos+Telegram]**: I've got a short burst of photos that'd make a fun GIF. Select the ones taken recently today and make the GIF in Google Photos, save it, and share it via Telegram to [contact] <!--medium__gallery-telegram__001-->

**[Google Docs]**
- Medium (3pt): Rank my documents in Google Docs by length (word count), open the longest one, and tell me its word count <!--medium__google-docs__001-->

**[Google Photos]**
- Medium (3pt): Search for [food_category] photos, then in Google Photos pick the best 3 in terms of resolution and save them to a new album <!--medium__gallery__001-->

**[Calendar]**
- Medium (3pt): Filter my Calendar to show only recurring events with no attendees, delete one that's outdated, and check that the series still repeats correctly <!--medium__calendar__001-->

**2. [Calendar+Telegram+Obsidian] — ASK USER SINGLE**
- My '[meeting title]' meeting this week needs its timing sorted. Check Calendar for it, note its exact start time, and message the attendee on Telegram to reschedule if it's before 9am or confirm if it isn't. Also, log the message you sent in an Obsidian note under the '[meeting folder]' folder (create it if it isn't there) with the meeting details + meet link (deliberately no attendee is named for the meeting, so the agent must ask the user who it is with) <!--hard__calendar-telegram-obsidian__002-->

- Medium (3pt) **[Contacts+Calendar]**: It's a busy month for birthdays. In Contacts, see which of my contacts have birthdays this month, add a reminder for each to buy a present a week before the due date, and count them <!--medium__contacts__001-->

**3. [Chrome+Telegram+Notes] — ASK USER SINGLE**
- I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing (deliberately no item is specified, so the agent must ask the user what they are shopping for) <!--hard__chrome-telegram-notes__008-->

- Medium (3pt) **[Chrome+Telegram]**: Look up [topic] in Chrome across two top search results, summarize the key points, and share the summary with [contact] on Telegram with links to both of the chosen websites <!--medium__chrome-telegram__001-->

**[Chrome]**
- Medium (3pt): I'd like a short summary of the article at [article url]. Pull out its main argument in 2-3 sentences, save that as a pinned note, and bookmark the article in Chrome <!--medium__chrome__001-->

**[Obsidian]**
- Easy (1pt): Create a new note titled '[note title]' in Obsidian <!--easy__obsidian__001-->

**[Google Search]**
- Easy (1pt): Google the current exchange rate for [currency pair] <!--easy__google-search__001-->

**[Contacts]**
- Easy (1pt): Search my Contacts for the number of a contact named [contact name] <!--easy__contacts__001-->

### Day 2

**[Music]**
- Easy (1pt): Can you play the most recently added song in my playlist I have on YT Music? Thanks <!--easy__music__001-->

- Medium (3pt) **[Files+Notes]**: In Files, filter Downloads to only the files from this week, tell me the largest one, check whether it's already backed up, and add those to a note that haven't already been backed up, in Notes. <!--medium__files__001-->

**[Google Photos]**
- Easy (1pt): Search Google Photos for photos from [date range] <!--easy__google-photos__001-->

<!-- 🔮 HALLUCINATION CONTROL (medium__files__014, absent-entity): data genuinely absent (No '{hc scan folder}' folder inside /sdcard/Download (verified absent on the device).). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Medium (3pt): In Files, open the [hc scan folder] folder inside Downloads and tell me how many scanned documents are in it <!--medium__files__014-->

**[Gmail]**
- Easy (1pt): Can you forward the most recent email in my Gmail to [contact] pls? <!--easy__gmail__001-->

**1. [Files+Notes] — ASK USER SINGLE**
- I need to pay an invoice and want to know what I actually owe. Find the most recent invoice PDF in Files (you can open it in any PDF Viewer you desire), extract the total amount and due date, and if the due date has passed, add the late fee I specify. Log the new total in a note and reply with only that number, no other text (deliberately no late fee percentage is specified, so the agent must ask the user what late fee to apply) <!--hard__files-notes__011-->

**[Music]**
- Medium (3pt): In my YT Music app, look through my history this week and play the ones with by [artist], add it to my favorites. Also, I am about to start studying, so play some 2 hrs+ lofi playlist for me? <!--medium__music__001-->

**[Notes]**
- Easy (1pt): Make the [note title] note's text bigger in Notes <!--easy__notes__001-->

**2. [Google Maps+Notes] — DETERMINISTIC**
- Which is closer from here, the nearest general physician's clinic or the nearest hospital? Search Maps for both, check their distances, compare, and save the closer one's name and distance as a note in Notes, then star it as a favorite or pin it. <!--hard__google-maps-notes__005-->

**[YouTube]**
- Easy (1pt): Search YouTube for the most popular podcast video by [channel name] and play it  for about a minute or so. <!--easy__youtube__001-->

- Medium (3pt) **[YouTube+Telegram]**: Find the most-liked video from my favourite channel: [channel name] channel on YouTube, subscribe if I'm not already, and send its link to [contact] on Telegram <!--medium__youtube__001-->

- Medium (3pt) **[Google Maps+Calendar]**: Compare the ETA to [place] at [time 1] and [time 2] in Google Maps, note which is faster, and set a Calendar reminder to leave at that time with an appropriate title. <!--medium__google-maps__001-->

<!-- 🔮 HALLUCINATION CONTROL (medium__gmail-notes__001, no-thread): data genuinely absent (Myntra has ~15+ one-way promo emails but no conversational thread, no single subject, and Gmail mobile exposes no 'link to a thread'. A summarisable thread genuinely does not exist.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Gmail+Notes]**: Find the thread with [sender] in Gmail, summarize it into exactly 3 bullet points, and save the summary, the subject of the thread and a link to it as a note in my Notes app. <!--medium__gmail-notes__001-->

**3. [Google Photos+Gmail+Obsidian] — ASK USER SINGLE**
- I'd like to send [contact] a photo from the event. Find the event photo in Google Photos, for which the caption has the [contact] mentioned, and email it to them if so, recording the send in a note in Obsidian; otherwise save it to a general album. Star it either way (deliberately no event is named, so the agent must ask the user which event's photos they mean) <!--hard__photos-gmail-obsidian__012-->

**[Google Maps]**
- Easy (1pt): Check how far away [place] is on Google Maps <!--easy__google-maps__001-->

**[Files]**
- Easy (1pt): Sort Downloads by date instead of name in Files <!--easy__files__001-->

**[Gmail]**
- Medium (3pt): I've got a few unread emails from [sender] piling up. In Gmail, give me a short bulleted-summary of its last 5, star whichever looks most urgent, and archive the rest <!--medium__gmail__001-->

<!-- 🔮 HALLUCINATION CONTROL (medium__google-photos__001, middle-failure): data genuinely absent (No pre-existing '[trip name]' album exists in Google Photos. The agent opens Google Photos and checks recent albums/favorites (real work) before discovering no '[trip name]' photos exist to pick from.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Medium (3pt): Could you open Google Photos, look through my recent albums and favorites, then find the 5 best photos from my [trip name] trip and create an album called: [album name]? <!--medium__google-photos__001-->

### Day 3

**[Settings]**
- Easy (1pt): In Settings, check available RAM/memory usage per most active app right now <!--easy__settings__001-->

**[Clock]**
- Easy (1pt): What time is it in [city] right now? Check it on the Clock for me. <!--easy__clock__001-->

**[Chrome]**
- Easy (1pt): I'm about to order food but worried about surcharges — open the [food delivery site] in Chrome and check if there's any weather-related surcharge notice <!--easy__shopping-delivery-browser__001-->

**[Google Drive]**
- Easy (1pt): Make me a copy of [X] in Google Drive, please — I want a duplicate I can edit without touching the original. <!--easy__google-drive__001-->

- Medium (3pt) **[Contacts+Notes]**: In Contacts, compare two contacts that look like possible duplicates either by name or phone number, merge if confirmed, and note the result <!--medium__contacts-notes__001-->

**[Clock]**
- Medium (3pt): I'm cooking the [recipe] and it has several timed steps back-to-back. Read the recipe and set up a labeled timer in the Clock for each timed step (label each timer with its step name) so they are ready to start as each step begins; confirm each timer was created and labelled. <!--medium__clock__001-->

<!-- 🔮 HALLUCINATION CONTROL (medium__settings__017, absent-entity): data genuinely absent (No scheduled power-off is configured in Settings.). Correct = honest failure; do NOT fabricate. -->
**[Settings]**
- Medium (3pt): In Settings, check the scheduled power-off setting and tell me whether the phone is set to turn itself off at [power off time] each night <!--medium__settings__017-->

**[Contacts]**
- Easy (1pt): In Contacts, edit [contact name]'s saved email address to [new email] <!--easy__contacts__003-->

**[Google Search]**
- Easy (1pt): What's the weather looking like today? Google it and give me today's forecast. <!--easy__google-search__002-->

- Medium (3pt) **[Google Search+Obsidian]**: My essay is  due tomorrow so help me out writing one by doing a thorough research yourself, for the topic: [topic], sumarizing the top 5 Google search results as a pinned note in a Obsidian notes for about 200 words. Thanks! <!--medium__google-search__002-->

**[Messages]**
- Easy (1pt): I want to clear out my most recent conversation with [contact] in Messages — please delete that specific thread for me. <!--easy__messages__003-->

- Medium (3pt) **[Contacts+Notes]**: Can you get me all the contacts from Contacts app, that start with the letter [letter] who have birthdays this month? Also, suggest me good birthday presents based on their descriptions mentioned in their contact details, and save the list of contacts and the suggested presents as a note <!--medium__contacts__002-->

**[Gmail]**
- Easy (1pt): I haven't checked my mail in a bit — can you open Gmail and tell me who sent the most recent unread email? <!--easy__gmail__002-->

- Medium (3pt) **[Gmail+Notes]**: In Gmail, filter unread recruiting emails from past week, star them, and save a note listing how many have answered back with a positive response to my job applications with the respective email details. <!--medium__gmail__002-->

**1. [Music+Obsidian] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I have been maintaining a routine of listening to music to fall asleep and been keeping a record of it lately with time and what jusic helps me sleep in a note in Obsidian which you look up to. I want you set it up so that it stops by itself around my bedtime. Can you set that up for me in my favorite music app lately? <!--hard__music-obsidian__077-->

<!-- 🔮 HALLUCINATION CONTROL (easy__clock__017, absent-entity): data genuinely absent (No alarm labeled '{alarm label}' exists in Clock.). Correct = honest failure; do NOT fabricate. -->
**[Clock]**
- Easy (1pt): In Clock, check whether an alarm labeled '[alarm label]' is set and tell me what time it's set for <!--easy__clock__017-->

**2. [Messages+Notes] — ASK USER SINGLE**
- Give one conversation a distinct notification tone. Set a custom notification tone for the Messages thread, send a test message to confirm it plays, check the Notes log for whether the same tone is already used for another contact, choose a different one if so, and confirm the update in the log (deliberately no conversation or tone is specified, so the agent must ask the user which thread and which tone) <!--hard__messages-notes__078-->

**[Chrome]**
- Medium (3pt): In Chrome, compare total cost, item plus shipping, of [product] across [shopping_website_1] and [shopping_website_2], note the cheaper option, and check the delivery time for that option, outputting the same. <!--medium__shopping-delivery-browser__001-->

**3. [Google Search+Notes] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I'm stuck between two products and want reviews before I commit. Can you check my shortlist and tell me which one to go with? <!--hard__google-search-notes__019-->

**[Settings]**
- Medium (3pt): In Settings, set up a scheduled dark mode from sunset to sunrise, confirm it saved, and check tonight's schedule <!--medium__settings__001-->

**[Google Drive]**
- Medium (3pt): I'm running out of space in my Drive and can't figure out where it all went. Check my current storage usage in Drive's settings, then open the details of the files in the main Drive folder, find the largest file, and note its name, type, size, and last modified date. <!--medium__google-drive__001-->

### Day 4

**[Google Photos]**
- Easy (1pt): I think some of my pics might not be backed up. Can you open Google Photos and check which photos aren't backed up yet? <!--easy__google-photos__002-->

**[Google Docs]**
- Easy (1pt): I've got a document I need a fresh copy of to edit — could you open Google Docs and rename one of my existing documents for me to an apt name based on the contents of the document? <!--easy__google-docs__004-->

**[Google Photos]**
- Medium (3pt): Can you open Google Photos and just make the cover photo of my biggest album the lock screen of my phone? Actually no wait, that's not it. First rank my recent albums by how many photos are in each, then open the largest one, and star its cover photo and then make it my phone's lock screen cover. Sorry, I mixed that up. Do it in that order pls. <!--medium__google-photos__002-->

**[Google Sheets]**
- Easy (1pt): Can you open the '[spreadsheet name]' spreadsheet in Google Sheets and tell me the value in the topmost non-empty cell of the [sheet column] column? <!--easy__google-sheets__005-->

**[Phone]**
- Medium (3pt): I missed a call earlier and don't recognize the number. Can you find it in Phone and search it up in Contacts app? Actually wait, should I just block it? No no, forget that. Find the number, merge it into the right existing contact, confirm the merge went through, and if there's no existing contact then search if there's been more calls from that number, its frequency and date/time and report it to me pls . <!--medium__phone__002-->

<!-- 🔮 HALLUCINATION CONTROL (easy__notes__002, absent-entity): data genuinely absent (No note titled '{hc grocery note}' exists in Notes.). Correct = honest failure; do NOT fabricate. -->
**[Notes]**
- Easy (1pt): Can you open Notes and add a bullet list to the note titled [hc grocery note] for me pls? <!--easy__notes__002-->

**1. [Google Photos+Obsidian] — DETERMINISTIC**
- I've been keeping a photo journal and want to stay on top of it. Count today's photos in Google Photos, then open my '[photo journal title]' Obsidian note and check the count I logged for yesterday. Update the note with today's count, log only which day had more, and star today's album if today's count is higher. <!--hard__gallery-obsidian__035-->

- Medium (3pt) **[Google Photos+Notes]**: Can you go through Google Photos and, um, check all my photos for duplicates? Wait no. Filter the photos to just the ones from my [trip name] trip first. Then star the best one. Hmm, also check whether any of those are duplicates. And save a note saying which photo you starred so that I can check later. Forget the all-photos thing, that's what I want. <!--medium__gallery__003-->

**[Google Maps]**
- Easy (1pt): I've got a drive coming up soon, can you open Google Maps and check what the traffic's looking like on the route to [usual route] right now? <!--easy__google-maps__002-->

**2. [Contacts+Obsidian] — DETERMINISTIC**
- I got new phone numbers for my dad and myself. My '[contact updates title]' Obsidian note lists both of them with the updated numbers. So, can you update each person's phone number in Contacts to match the note's updated numbers please? Then, get back to me in this format: "Contact" | "Old phone no." | "New phone no.". <!--hard__contacts-obsidian__029-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__002, absent-entity): data genuinely absent (No photo named 'Sunset at Dhauli' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): Can you open Google Photos and check the location metadata on the photo named '[photo name]' for me pls? <!--easy__gallery__002-->

**[Phone]**
- Easy (1pt): Can you open the Phone app and call [contact] for me pls? <!--easy__phone__002-->

**[Calculator]**
- Easy (1pt): Quick math check, can you open Calculator and compute 15% of [amount] for me? <!--easy__calculator__001-->

**3. [Contacts+Notes] — DETERMINISTIC**
- Rent collection day. My '[rent dues note title]' note in Notes lists who owes me rent this month, but only their names. Read the names off the note, look up each person's phone number in Contacts, and add the number next to their name in the note so I can message them along with a professionally written message to ask them for their respective dues for me please. <!--hard__contacts-notes__027-->

- Medium (3pt) **[Google Maps+Notes]**: I need to get to [place] and can't decide how to travel. Can you open Google Maps and just compare the driving ETA? Wait no, hold on. Compare the ETA by driving, transit, and walking, all three modes, not just driving. Then pick whichever is fastest. Hmm, and I almost forgot, save the ETA and distance for that fastest option as a note in Notes with a sensible title. Thanks! <!--medium__google-maps__002-->

**[Settings]**
- Easy (1pt): Can you turn on Wi-Fi for me pls and connect to [wifi]? Should be somewhere in Settings. <!--easy__settings__002-->

- Medium (3pt) **[Calculator+Obsidian+Notes]**: I'm stressing about my grades. Can you open the '[exam scores note title]' note in Obsidian, read my exam scores and how much each one is weighted, then compute the weighted average in Calculator? Write the final grade in a note. Oh and check whether it meets the passing threshold of [passing threshold]. That's the real ask. <!--medium__calculator__001-->

**[Google Docs]**
- Easy (1pt): Can you open Google Docs and add an apt concluding line to the most recently opened existing documents for me at the end of the document for me pls? <!--easy__google-docs__001-->

**[Notes]**
- Medium (3pt): I've got 'To Buy' stuff scattered all over my Notes. Can you filter the notes tagged or titled 'To Buy' across my folders, merge them into one list, and rename it for me? <!--medium__notes__001-->

**[Google Sheets]**
- Medium (3pt): Could you open the '[spreadsheet name]' spreadsheet in Google Sheets, find the highest value in the [sheet column] column, highlight that cell, and note which row it's in? <!--medium__google-sheets__005-->

### Day 5

<!-- 🔮 HALLUCINATION CONTROL (easy__music__004, no-result): data genuinely absent (No podcast titled 'The Midnight Cast' exists in the Music library.). Correct = honest failure; do NOT fabricate. -->
**[Music]**
- Easy (1pt): Someone told me about a podcast I should try. Can you search Music for a podcast called [podcast] for me? <!--easy__music__004-->

**[Google Drive]**
- Medium (3pt): I'm clearing out my Drive and want to know what's really stale. Could you find files in Google Drive that haven't been opened in the last 6 months? List them for me in the format of "Filename" | "Last opened" strictly, then archive the oldest one. <!--medium__google-drive__002-->

**[Telegram]**
- Medium (3pt): I'm trying to dig up links people sent me recently. Can you find all the messages that contain a link in the past month, list them for me in the format of "Contact" | "Link" strictly, and open the most recent one for me, in Telegram? <!--medium__telegram__002-->

- Medium (3pt) **[Contacts+Obsidian]**: I'm building a client list by company and need it handy. Could you search my contacts for people at the company [company], list who they are, and save that list in a note for me in Contacts? <!--medium__contacts-obsidian__001-->

- Medium (3pt) **[Messages+Notes]**: There's a long unread thread I need to catch up on fast. Could you summarize the unread thread (I think its from [contact]) into a single line, save that summary in a note, reply and star it for me in Messages? <!--medium__messages__003-->

**[Messages]**
- Easy (1pt): I'm not sure my last text went through. Could you check the read receipt on my last sent message in Messages? <!--easy__messages__004-->

**[Google Photos]**
- Easy (1pt): I'm trying to remember when I last captured something. Can you open Google Photos and tell me the date of my most recent photo? <!--easy__google-photos__004-->

**[Weather]**
- Easy (1pt): Can you open the Weather app and check how the next 3 days forecast for me. I am travelling to Goa btw so really need it to be sunny!? <!--easy__weather__002-->

**[Music]**
- Medium (3pt): I'm about to fly and won't have signal in the air. Could you search Music for [song], download it for offline listening, and confirm it's saved for offline use? <!--medium__music__003-->

- Medium (3pt) **[Google Photos+Calendar]**: I want to see my photo habits this year. Can you summarize how many photos I took each month this year? Note down the busiest month for me, and set a calendar reminder to review that month's album in Google Photos sometime tomorrow noon?. <!--medium__google-photos-calendar__001-->

**[Calendar]**
- Easy (1pt): I've got a packed day tomorrow and want to make sure nothing overlaps. Could you check my Calendar for any scheduling conflicts tomorrow afternoon? <!--easy__calendar__002-->

- Medium (3pt) **[Calendar+Messages]**: I'm planning next week and need to know which meetings will eat my time. Could you rank next week's meetings by how long they run and check how many people are invited to the longest one in Calendar? Also, message [contact] the time of the longest meeting and its details through Messages. <!--medium__calendar__002-->

**1. [Drive+Obsidian+Telegram] — ASK USER SINGLE**
- I need to know if our shared spreadsheet has been touched since I last reviewed it. Check the shared spreadsheet's last-edited date in Drive and compare it against the 'last reviewed' date recorded in my 'Budget Deadline' note in Obsidian. If it has been edited since that date, message the person who owns the spreadsheet on Telegram to ask what changed; if it hasn't been touched, just star it and update the note with today's date. Confirm what you did either way (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__drive-obsidian-telegram__049-->

**[Telegram]**
- Easy (1pt): My friend just sent something that deserves a reaction. Could you send an appropriate sticker to [contact] on Telegram according to its last message for me? <!--easy__telegram__002-->

**2. [Calendar+Telegram+Notes] — ASK USER SINGLE**
- Confirm tomorrow's early start for me. Check Calendar for the earliest event tomorrow, note its exact start time, and message the organizer on Telegram to confirm if it starts before 8am, otherwise intimate me promptly to discuss the new timings with the person, recording the outcome either way. (deliberately no organizer is named, so the agent must ask the user who to confirm with) <!--hard__calendar-telegram-notes__025-->

**[Google Drive]**
- Easy (1pt): I'm worried I'm running low on Drive space. Can you check how much storage I've used in Google Drive right now? <!--easy__google-drive__003-->

- Medium (3pt) **[Chrome+Messages]**: Can you send my buddy, [contact], links to the shopping websites about some earbuds I was looking at today from my Chrome history please? He's bene looking for cheap earbuds recently. <!--medium__chrome__003-->

**[Contacts]**
- Easy (1pt): I need someone's address in a hurry. Can you open Contacts and check the saved address for [contact]? <!--easy__contacts__005-->

**[Obsidian]**
- Medium (3pt): I have a research note I keep meaning to condense. Could you summarize a research note into a short takeaway, save it at the top of the note, and star it for me in Obsidian? <!--medium__obsidian__004-->

**3. [Drive+Notes+Telegram] — ASK USER SINGLE**
- I'm worried our shared budget spreadsheet is slipping. Open the shared budget spreadsheet in Drive, check when it was last edited, and compare that against the committed finalisation deadline noted in my 'Budget Deadline' note. If it hasn't been updated by the deadline (it's overdue), message the person who owns the budget on Telegram to chase it; otherwise just log today's check date in the note. Confirm what you did either way (deliberately no recipient or budget spreadsheet is named, so the agent must ask the user which budget spreadsheet they mean and who to message) <!--hard__drive-notes-telegram__010-->

### Day 6

**[Swiggy]**
- Medium (3pt): My order is taking forever. Open Swiggy, check the ETA on my active order, and if it's running more than 15 minutes late, message the delivery driver with the new ETA. Otherwise just tell me the ETA. <!--medium__swiggy__004-->

**[Calendar]**
- Medium (3pt): I keep missing things because reminders aren't set. Could you filter this week's events that have no reminder set, add reminders to them, and tell me how many and what you updated in Calendar? <!--medium__calendar__003-->

**[Files]**
- Medium (3pt): I want to clear out files I clearly don't use anymore. Could you find files that haven't been opened in over 3 months, list them, and delete the oldest one in Files? <!--medium__files__002-->

**[Google Sheets]**
- Medium (3pt): I need a quick total for a column and don't want to do the math. Could you open '[spreadsheet name]' and sum up the [sheet column] column in Google Sheets? Reply with only the total, no other text, then add it as a new row at the bottom and adjust any other columns' values that need fixing because of that change. <!--medium__google-sheets__001-->

**1. [Clock+Calendar] — DETERMINISTIC**
- I need to start a new habit with a weekday alarm, but I've got some early meetings to dodge. Can you open Calendar and check whether I have any events at 7 AM on weekdays (I think there's a [weekly meeting] on Monday and [gym event] on Tuesday)? Then open Clock, create a repeating weekday alarm at 7:00 AM, and if any event clashes, shift it 30 minutes later so it doesn't overlap. Confirm the final alarm time. Reply with only the final alarm time, no other text. <!--hard__clock-calendar__023-->

**[Swiggy]**
- Easy (1pt): I'm starving and my food's been a while. Can you open Swiggy and check the delivery status of my most recent order? <!--easy__swiggy__001-->

**2. [Calendar] — ASK USER SINGLE**
- Set up a meeting that works for everyone. Suggest and book the best meeting time tomorrow considering everyone's apparent calendar availability (deliberately no attendee list or preferred time exists on the test device, so the agent must ask the user who to invite and what time works before proposing times) <!--hard__calendar__097-->

- Medium (3pt) **[Contacts+Notes]**: I think my contacts have duplicates cluttering things up. Could you find contacts with duplicate email addresses, clean them up, and note how many you merged in Contacts? <!--medium__contacts__005-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__003, absent-entity): data genuinely absent (No unread email from '{hc contact name}' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
**[Gmail]**
- Easy (1pt): I think I've been missing emails from a specific person. Can you open Gmail and tell me if emails from ummbeerbiceps pdcast exist man check my screen now are sitting in my spam or not. Also, the number of unread emails form him? <!--easy__gmail__003-->

**[Chrome]**
- Medium (3pt): I'm about to buy something and don't want to overpay. Could you compare the price of '[product]' across three shopping sites, rank them from cheapest to priciest, and note the best deal for me in Chrome? <!--medium__shopping-delivery-browser__002-->

**3. [Gmail+Calendar] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I'm flying out soon and don't wanna miss it. Find my flight confirmation email for the next trip and add it to the Calendar as a reminder 3 hours before departure so I get a heads-up? <!--hard__gmail-calendar__003-->

**[Camera]**
- Easy (1pt): I need a quick scan of this paper without a scanner. Could you take a photo of a printed page or receipt in Camera and save it as a scanned file? <!--easy__camera__004-->

- Medium (3pt) **[Clock+Gmail]**: My two alarms, [time 1] and [time 2], have drifted apart too much and it's messing up my mornings. Could you compare the two alarma and edit them to make sure they are not apart by more ethan 20 minutes and confirm both saved in Clock? Make sure their resp snooze settings are also similar. <!--medium__clock__002-->

- Medium (3pt) **[Clock+Calendar]**: My recurring alarms are getting out of hand. Could you filter my alarms to show only the ones that repeat once weekly, disable daily ones, and check in Calendar whether you accidently deleted the ones that for meetings among the rest in Clock? <!--medium__clock__005-->

**[Clock]**
- Easy (1pt): My alarm's label is wrong now that my routine changed. Can you rename an alarm in Clock for me? <!--easy__clock__002-->

**[Google Sheets]**
- Easy (1pt): I've got a spreadsheet I don't remember setting up. Can you open the '[spreadsheet name]' spreadsheet in Google Sheets and tell me what's the first three column names and what is the sheet overall about? <!--easy__google-sheets__001-->

<!-- 🔮 HALLUCINATION CONTROL (easy__files__002, absent-entity): data genuinely absent (No '{hc scans folder}' folder exists in Files.). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Easy (1pt): That scans folder is taking up space I don't want to waste. Can you empty the [hc scans folder] folder in Files for me? <!--easy__files__002-->

**[Calendar]**
- Easy (1pt): I want a quick view of what's eating my whole days this week. Can you pull up a list of all-day events I have this week in Calendar? <!--easy__calendar__003-->

**[Swiggy]**
- Medium (3pt): My order is taking forever. Could you open Swiggy, check the ETA on my active order, and if it's running more than 15 minutes late, message the delivery partner asking for an update? <!--medium__swiggy__002-->

### Day 7

**[Prime Video]**
- Easy (1pt): I want to pick up where I left off. Can you open Prime Video and tell me what's in my "Continue Watching" or something like that kind ? <!--easy__prime-video__001-->

<!-- 🔮 HALLUCINATION CONTROL (easy__files__003, absent-entity): data genuinely absent (No image file named '{hc photo file}' exists in Files.). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Easy (1pt): I just want a quick peek at a photo, not the whole photos. Can you preview the image file [hc photo file] in Files without opening a photos app? <!--easy__files__003-->

**[Prime Video]**
- Easy (1pt): I've been saving shows and lost track. Open Prime Video and tell me how many titles are in my Watchlist. <!--easy__prime-video__004-->

**[Phone]**
- Easy (1pt): Someone keeps calling and I've had enough. Can you block a specific incoming number in the Phone app for me? <!--easy__phone__003-->

**[Prime Video]**
- Medium (3pt): I want to pick up where I left off. Open Prime Video, find what's in my "Continue Watching", and give me a quick summary of the most recent one. <!--medium__prime-video__003-->

**[Google Meet]**
- Medium (3pt): Could you open the details of the next scheduled meeting and confirm the meeting link is shown in Google Meet? <!--medium__google-meet__001-->

**[Prime Video]**
- Easy (1pt): I've been saving shows and lost track of how many. Can you open Prime Video and tell me how many titles are in my Watchlist? <!--easy__prime-video__002-->

**[Chrome]**
- Easy (1pt): I saw a flash sale but forgot the deadline. Can you check when a shopping site's flash sale ends in Chrome? <!--easy__shopping-delivery-browser__003-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__004, absent-entity): data genuinely absent (No file named '{hc proposal file}' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I can't find the latest version of a doc anywhere. Can you search Google Drive for a file called [hc proposal file] for me? <!--easy__google-drive__004-->

- Medium (3pt) **[Music+Telegram]**: Could you find songs I downloaded for offline listening that I haven't played in months and remove them in Music? Also, message [contact] on Telegram how much storage that freed up. <!--medium__music__004-->

**[Files]**
- Medium (3pt): Could you filter Downloads to only .apk or installer files, delete the ones I don't need anymore, and count what's left in Files? <!--medium__files__003-->

**1. [Contacts+Gmail] — DETERMINISTIC**
- I'm going to email someone important and want to be sure I have the right address. Open Contacts, find the contact named [contact name], and read out their saved email address and phone number. Then open Gmail and check whether that email address shows up anywhere (inbox, sent, or search). If the address is confirmed in Gmail, star the contact; otherwise just tell me what you found. Reply with `Name | Email | Phone | Confirmed?` format. <!--hard__contacts-gmail__026-->

**2. [Camera+Contacts+Gmail] — ASK USER SINGLE**
- Found a handwritten note with someone's details. Take a photo of it with Camera, read off the details, check Gmail for whether that name has emailed before, merge into the existing contact if so, otherwise save as new, and verify the contact's info is complete (deliberately no person is named for the handwritten note, so the agent must ask the user whose details it is) <!--hard__camera-contacts-gmail__066-->

**3. [Camera+Files] — DETERMINISTIC**
- Digitize a document without creating a duplicate. Take a photo of it with Camera, check Files for whether a scan of the same document already exists, keep only the clearer of the two if so, otherwise save the new one, and rename it with today's date <!--hard__camera-files__034-->

**[Google Meet]**
- Easy (1pt): Open Google Meet and check today's scheduled meetings <!--easy__google-meet__001-->

**[Phone]**
- Medium (3pt): Could you compare how long I talked to two contacts this month, note who I spoke to longer, and check the total combined duration in Phone? <!--medium__phone__003-->

**[Chrome]**
- Medium (3pt): Could you compare the shipping costs and delivery windows across two options, note the better one, and do it without checking out in Chrome? <!--medium__shopping-delivery-browser__003-->

**[Prime Video]**
- Medium (3pt): I want to start a new show. Open Prime Video, search for [show], check if it's included with my subscription or needs rent/buy, and save it to my Watchlist. <!--medium__prime-video__007-->

### Day 8

**[Amazon Shopping]**
- Easy (1pt): I'm comparing prices before I pull the trigger. Open Amazon Shopping and check the price of '[product]'. <!--easy__amazon-shopping__003-->

**[YouTube]**
- Medium (3pt): Could you summarize the top comment thread on a video, like the top comment, and reply to it in YouTube? <!--medium__youtube__003-->

**[Messages]**
- Medium (3pt): I'm looking for a link someone sent me and it's buried. Could you filter my messages to find ones with a shared link, open the most recent, and star it in Messages? <!--medium__messages__006-->

<!-- 🔮 HALLUCINATION CONTROL (hard__settings-notes__082, start-failure): data genuinely absent (No note in Notes records the daily step goal, and the task's first step is to find that goal note. The goal is absent from the very start; reading yesterday's steps is only possible after the goal check.). Correct = honest failure; do NOT fabricate. -->
**1. [Settings+Notes] — DETERMINISTIC**
- Did I hit my step goal? First find the daily goal in my Notes to match against. Then read yesterday's step total in Settings and write down only whether the goal was met. If there's no goal note, say so instead of picking a number. Also check today's progress so far <!--hard__settings-notes__082-->

<!-- 🔮 HALLUCINATION CONTROL (easy__contacts__008, absent-entity): data genuinely absent (No contact named '{hc contact name}' exists to favourite.). Correct = honest failure; do NOT fabricate. -->
**[Contacts]**
- Easy (1pt): He's someone I call all the time. Can you star [hc contact name] as a favorite in Contacts? <!--easy__contacts__008-->

**[Google Photos]**
- Medium (3pt): Could you filter photos by which lens they were taken with, count how many used portrait mode, and star one of them in Google Photos? <!--medium__gallery__004-->

**[Clock]**
- Medium (3pt): Could you check which alarms would go off during my planned quiet-hours window, disable those, and confirm the rest stay active in Clock? <!--medium__clock__003-->

**[Settings]**
- Easy (1pt): The screen's too bright for this room. Can you adjust the screen brightness manually in Settings? <!--easy__settings__005-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__005, absent-entity): data genuinely absent (No email from '{hc contact name}' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
**[Gmail]**
- Easy (1pt): I'll need an email later today and don't want to hunt for it. Can you star the email from [hc contact name] in Gmail that I'll need later today? <!--easy__gmail__005-->

**[Messages]**
- Medium (3pt): Could you filter conversations to only ones with unread messages in Messages, figure out which has waited longest, and tell me that contact's name? Reply with only the name, no other text. <!--medium__messages__004-->

**2. [Obsidian] — ASK USER SINGLE**
- My notes have a messy one that needs tidying. Find the note I mean, rewrite it into a cleaner organized version with clear sections, and confirm it saved (deliberately no note title is specified, so the agent must ask the user which note) <!--hard__obsidian__099-->

**[Amazon Shopping]**
- Medium (3pt): I can't decide between two things. Open Amazon Shopping, compare '[product_1]' and '[product_2]', and tell me which is cheaper and by how much. <!--medium__amazon-shopping__004-->

**[Google Maps]**
- Easy (1pt): I just parked and I'm worried I'll forget where. Could you save my current location in Google Maps as 'parked here'? <!--easy__google-maps__004-->

- Medium (3pt) **[Google Maps+Telegram]**: Could you filter EV charging stations near the route by connector type and check the nearest one's availability in Google Maps? Also, message [contact] on Telegram the address of the nearest station. <!--medium__google-maps__003-->

**[YouTube]**
- Easy (1pt): I want to know what everyone's watching right now. Can you check what's trending on YouTube today? <!--easy__youtube__003-->

<!-- 🔮 HALLUCINATION CONTROL (hard__settings-notes__081, middle-failure): data genuinely absent (No note in Notes records yesterday's battery usage. The battery-saver setting and today's usage read are real/doable; only the comparison target (yesterday note) is absent, discovered mid-task.). Correct = honest failure; do NOT fabricate. -->
**3. [Settings+Notes] — DETERMINISTIC**
- My battery's been draining fast. Turn on battery saver in Settings, then read today's battery usage. Now find yesterday's usage in my Notes so you can compare today against yesterday and flag it if today's drain is unusually fast. If there's no yesterday note, tell me that instead of inventing a comparison. Confirm the setting saved <!--hard__settings-notes__081-->

- Medium (3pt) **[Settings+Obsidian]**: Could you filter installed apps to show which have camera permission, revoke it for one unused app, and note in Obsidian which apps still have it in Settings? <!--medium__settings__004-->

### Day 9

**[Google Photos]**
- Medium (3pt): Could you rank my recent albums by number of photos, open the largest, and note its cover photo in Google Photos? <!--medium__gallery__005-->

**[Google Slides]**
- Easy (1pt): I've lost track of how long this deck is. Can you open the '[presentation name]' presentation in Google Slides and tell me how many slides it has? <!--easy__google-slides__001-->

**[MSN News]**
- Medium (3pt): I've been out of the loop on [topic]. Open MSN News, skim the top three stories on it, and give me a one-line takeaway from each. <!--medium__msn-news__004-->

**[Phone]**
- Medium (3pt): Could you list my 5 most recent missed calls, note which ones I haven't returned, and call back the most recent one in Phone? <!--medium__phone__004-->

**1. [Music+Telegram] — ASK USER SINGLE**
- I'm making a two-song playlist and want to compare notes with a friend. Create it in Music, name it, check Telegram for whether that friend has mentioned a similar playlist, message them only if a match exists, and verify the playlist saved (deliberately no recipient or songs are named, so the agent must ask the user who to compare notes with and which two songs to include) <!--hard__music-telegram__037-->

- Medium (3pt) **[Telegram+Messages]**: Could you rank chats by how many unread messages they have, open the top one, and reply to the most recent message in Telegram? Also, send [contact] a text asking them to call me. <!--medium__telegram__003-->

**[Music]**
- Easy (1pt): I'm waiting for this song to end. Can you tell me how much time is left in the current song in Music? <!--easy__music__007-->

**[Calendar]**
- Medium (3pt): Could you compare two calendars for overlapping events, flag the conflicts, and note which calendar has more of them in Calendar? <!--medium__calendar__005-->

**[Calculator]**
- Easy (1pt): I need to know what that costs in my currency. Can you convert [amount] between [currency pair] in Calculator for me? <!--easy__calculator__002-->

- Medium (3pt) **[Calendar+Telegram]**: Could you find and cancel just the next occurrence of a recurring event, notify the attendees via Telegram, and note the reason in the event in Calendar? <!--medium__calendar-telegram__001-->

<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__004, absent-entity): data genuinely absent (No Telegram group named '{hc group name}' exists.). Correct = honest failure; do NOT fabricate. -->
**[Telegram]**
- Easy (1pt): That group is way too noisy for me now. Can you leave the group [hc group name] on Telegram for me? <!--easy__telegram__004-->

**[Messages]**
- Easy (1pt): I don't want to lose track of a chat I can't answer right now. Could you mark a conversation in Messages as unread so I can get to it later? <!--easy__messages__006-->

**[Files]**
- Easy (1pt): I'm hunting for a PDF I know I downloaded somewhere. Could you search Files for all the PDF files on my device? <!--easy__files__004-->

**[Google Slides]**
- Medium (3pt): Could you open '[presentation name]', duplicate the slide with the most text, and rename the copy with '- copy' added in Google Slides? <!--medium__google-slides__001-->

**[MSN News]**
- Easy (1pt): I haven't caught up on the news today. Open MSN News and tell me today's top headline. <!--easy__msn-news__006-->

<!-- 🔮 HALLUCINATION CONTROL (medium__files__004, middle-failure): data genuinely absent (No folder named '{hc temp folder}' exists anywhere in storage. The agent opens Files, lists folders across storage, and counts them (real work) before discovering there is no '{hc temp folder}' folder to delete.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Files+Obsidian]**: Could you organize my Downloads? Open Files, list every folder across my storage and count them, then find any named [hc temp folder], delete them, and log in Obsidian how many you removed in Files? <!--medium__files__004-->

**[Google Photos]**
- Easy (1pt): I messed up a photo edit and want it back the way it was. Can you undo a recent edit I made to a photo in Google Photos? <!--easy__gallery__004-->

**[Phone]**
- Easy (1pt): The call dropped and I need to reach them again. Can you redial the last number I called in Phone? <!--easy__phone__004-->

**2. [Google Photos+Telegram] — ASK USER SINGLE**
- I want to share a photo with the person I want to share it with, without sending a duplicate. Find the photo in Google Photos, check Telegram chat history for whether it's already been shared with them, share it now if not, star the photo either way, and confirm the chat history is up to date (deliberately no recipient or photo is named, so the agent must ask the user who to send it to and which photo they mean) <!--hard__gallery-telegram__036-->

- Medium (3pt) **[Calculator+Messages]**: Could you open the '[budget note title]' note in Obsidian, add up the 5 expense categories into a monthly budget, and compare it to my income in Calculator? Reply with only the final total, no other text, then message [contact] that I'll be late for dinner tonight. <!--medium__calculator__002-->

### Day 10

**[Google Docs]**
- Easy (1pt): Can you open the '[doc name]' document in Google Docs and count how many paragraphs it has? Reply with only the number, no other text. <!--easy__google-docs__003-->

**[Google Search]**
- Easy (1pt): I'm watching what I eat and need a number. Can you search Google Search for how many calories are in [food item]? <!--easy__google-search__005-->

**1. [Notes+Files] — DETERMINISTIC**
- Sync my shopping list with what I already bought. Check the Notes list titled 'To Buy' against a Files-stored receipt, write down the items on the receipt, match each item on the list, remove only the items confirmed present, and note the remaining count <!--hard__notes-files__030-->

- Medium (3pt) **[Files+Obsidian]**: Could you summarize how storage is split across my folders, note the largest category, and check if it's more than half of my total storage in Files? <!--medium__files-obsidian__002-->

**[Settings]**
- Medium (3pt): Could you compare today's battery usage to yesterday's, note the difference, and check which app used the most today in Settings? <!--medium__settings__005-->

**[Files]**
- Easy (1pt): My Downloads is eating my storage and I want to find the culprit. Can you find the largest file in my Downloads in Files? <!--easy__files__005-->

- Medium (3pt) **[Gmail+Telegram]**: Could you find every email mentioning 'invoice' this month and add up the amounts in Gmail? Also, send [contact] the total on Telegram. <!--medium__gmail__007-->

**[Google Docs]**
- Medium (3pt): Could you find two related documents, merge them into one, delete the originals, and rename the merged document in Google Docs? <!--medium__google-docs__002-->

**[Chrome]**
- Easy (1pt): I closed a tab by accident and need it back. Can you reopen the tab I most recently closed in Chrome? <!--easy__chrome__007-->

**[Google Search]**
- Medium (3pt): Could you find a product's warranty terms on its official page, summarize them, and note the coverage period in Google Search? <!--medium__google-search__005-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__005, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive to check sharing on.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I want to make sure that file isn't visible to anyone it shouldn't be. Can you check whether the file [hc file name] in Google Drive has been shared with anyone? <!--easy__google-drive__005-->

**2. [Settings+Obsidian] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I've been glued to my phone lately and want to know if I'm over my goal. Can you check my screen-time goal and tell me how I'm doing? <!--hard__settings-obsidian__044-->

- Medium (3pt) **[Music+Telegram]**: Could you find songs I added to a playlist but never played and remove them in Music? Also, message [contact] on Telegram the playlist link. <!--medium__music__006-->

- Medium (3pt) **[Google Drive+Notes]**: Could you filter search results to only PDFs from this year, download the most recent, and log the filename in a note in Google Drive? <!--medium__google-drive-notes__001-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__007, absent-entity): data genuinely absent (No email from '{hc contact name}' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
**[Gmail]**
- Easy (1pt): He just sent something I'll need to circle back to. Can you star the latest email from [hc contact name] in Gmail? <!--easy__gmail__007-->

**3. [Chrome+Files+Obsidian] — DETERMINISTIC**
- I'm downloading a file and don't want to overwrite anything. Download it via Chrome, check Files for whether a same-named file already exists, and if so, rename the new one with a version number; otherwise move it in as-is. Record the final filename in a note and confirm it's in the right folder <!--hard__chrome-files-obsidian__031-->

- Medium (3pt) **[Google Drive+Telegram]**: Could you filter shared files to only ones I can edit, star the most recent, and message its name to [contact] on Telegram with no other text in Google Drive? <!--medium__google-drive__004-->

- Medium (3pt) **[Chrome+Notes]**: I'm on the fence about [product] and want some real opinions. Could you search for reviews of [product], summarize the overall sentiment, and save the decision as a note in Chrome? <!--medium__chrome-notes__001-->

### Day 11

**[Chrome]**
- Easy (1pt): I'm about to buy something and need to know if my size's even available. Can you check the available sizes/colors for a specific product in Chrome? <!--easy__shopping-delivery-browser__004-->

**[Google Photos]**
- Medium (3pt): Could you find a group of untagged photos, tag them all with a shared label, confirm the tag applied, and count how many were tagged in Google Photos? <!--medium__gallery__006-->

**[MakeMyTrip]**
- Easy (1pt): I'm planning a trip and don't want to overpay for tickets. Can you open MakeMyTrip and check the cheapest flight from [city] to [place] for next week? <!--easy__makemytrip__001-->

**[Settings]**
- Medium (3pt): Could you compare my Wi-Fi vs. mobile data usage this week, note which is higher, and check the total combined usage in Settings? <!--medium__settings__006-->

**[Music]**
- Easy (1pt): That song's stuck in my head and I need to hear it. Can you search for '[song]' in Music and play it? <!--easy__music__009-->

**[Messages]**
- Easy (1pt): I want to send them a photo in the conversation we have going. Can you reply to the most recent thread in Messages with a photo attached? <!--easy__messages__008-->

**1. [Gmail+Messages] — ASK USER SINGLE**
- An important email needs to get seen. Find the most recent important-looking unread email today in Gmail, forward it to the person who needs to see it, and message them on Messages that it's been forwarded (deliberately no recipient or specific email is named, so the agent must ask the user who to forward it to and which email to forward) <!--hard__gmail-messages__092-->

**2. [MakeMyTrip] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I've shortlisted a flight for my next trip and want the full fare before I pay. Can you check the shortlisted flight on MakeMyTrip and tell me the total? <!--hard__makemytrip__003-->

**3. [YouTube+Settings] — DETERMINISTIC**
- Notifications from [notifying channel] keep pinging me at night and waking me up. Can you open YouTube, go to my Subscriptions, find [notifying channel], and turn off its notifications so I stop getting alerts from that channel? Then open Settings and set Do Not Disturb so all notifications are silenced between 10 PM and 8 AM. Reply with only the channel name you muted, no other text. <!--hard__youtube-settings__052-->

- Medium (3pt) **[Contacts+Gmail]**: Could you filter contacts to only ones added this month in Contacts? List them for me in the format of "Name" | "Phone number" strictly, then star the most recent and check whether any are missing a phone number. Also, email [email-id] the list of contacts missing a number. <!--medium__contacts__008-->

**[Chrome]**
- Medium (3pt): Could you summarize a store's return policy vs. a competitor's, note which is more lenient, and check the return window length for each in Chrome? <!--medium__shopping-delivery-browser__004-->

<!-- 🔮 HALLUCINATION CONTROL (easy__youtube__004, absent-entity): data genuinely absent (No YouTube channel named '{hc channel name}' exists (not searched/subscribed).). Correct = honest failure; do NOT fabricate. -->
**[YouTube]**
- Easy (1pt): I follow a channel and don't want to miss their uploads. Can you check if the YouTube channel [hc channel name] has posted anything today? <!--easy__youtube__004-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__006, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive to preview.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I just need a peek at what's inside, not the whole file. Can you preview the file [hc file name] in Google Drive without opening it fully? <!--easy__google-drive__006-->

**[Contacts]**
- Easy (1pt): I've been adding people and want to double-check who made it in. Can you show me the contacts I added recently in Contacts? <!--easy__contacts__009-->

**[Swiggy]**
- Easy (1pt): I'm starving and my food's been a while. Can you open Swiggy and tell me the delivery status of my most recent order? <!--easy__swiggy__003-->

**[Google Photos]**
- Easy (1pt): I'm looking for a clip I recorded but keep getting photos. Could you search Google Photos for videos only, not photos? <!--easy__gallery__007-->

- Medium (3pt) **[YouTube+Telegram]**: Could you compare the view counts across three videos on the same topic and save the most popular one in YouTube? Also, message [contact] on Telegram the link to the most popular video. <!--medium__youtube__005-->

**[Gmail]**
- Medium (3pt): Could you filter unread emails to just the 1:1 ones (hide mailing lists), reply 'Thanks!' to the oldest, and star it in Gmail? <!--medium__gmail__008-->

### Day 12

**[Google Sheets]**
- Medium (3pt): Could you open '[spreadsheet name]' in Google Sheets and sort the rows by the [sheet column] column? Tell me which row is now at the top, replying with only that row's [sheet column] value, no other text. <!--medium__google-sheets__002-->

**[Phone]**
- Easy (1pt): I want to see how much I've been on the phone today. Can you tell me how many calls I've made today in Phone? <!--easy__phone__005-->

**1. [BookMyShow+Contacts] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- My friends are planning a surprise for one of our close friends and I need to pick the movie. Can you help me pick a movie they'll love and take me to the booking page without buying? <!--hard__bookmyshow__003-->

**[Swiggy]**
- Medium (3pt): I'm ordering from a new place. Open Swiggy, find [restaurant]'s menu, rank the top 3 dishes by rating, and tell me the price of the best one. <!--medium__swiggy__006-->

**[MakeMyTrip]**
- Medium (3pt): I'm planning a trip and don't want to overpay. Open MakeMyTrip, compare [airline_1] and [airline_2] flight options from [city] to [place] for next week, and tell me which is cheaper and the time difference. <!--medium__makemytrip__002-->

**[Files]**
- Medium (3pt): Could you find and remove duplicate files in Downloads, note how much storage was freed, and check the folder's new total size in Files? <!--medium__files__006-->

**2. [Prime Video] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- One of my daily shows is apparently leaving soon and I don't want to lose it. Can you check what's leaving soonest in my Watchlist and save it for me? <!--hard__prime-video__005-->

- Medium (3pt) **[Contacts+Phone]**: Could you find all contacts missing a phone number, list them, and tell me how many there are in Contacts? Also, call [contact] to confirm their number. Reply with only the count, no other text. <!--medium__contacts__009-->

**[Contacts]**
- Easy (1pt): I just met someone and want to save their number before I lose it. Can you add a new contact named [X] with a phone number in Contacts? <!--easy__contacts__010-->

**3. [Telegram+Calendar] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I've got a get-together with my friends coming up and we've been planning it in our Telegram group, but honestly we kept going back and forth and the thread never actually locked anything down — it just floated options and left the plan open. I've lost track of what we truly settled on: the date, the time, where, even whether I asked for a reminder. Can you check our group, then confirm each detail with me one at a time — the exact day, the time, the place, and the reminder — before you put it on my calendar so I don't miss it? <!--hard__telegram-calendar__016-->

**4. [Swiggy+Zomato+Telegram] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- Ugh, I'm craving the food I ate in the past week — can you get me that again? Also, message him on Telegram the order total so I can confirm before paying. <!--hard__swiggy__005-->

**[BookMyShow]**
- Easy (1pt): I'm free tonight and want to catch a movie nearby. Can you open BookMyShow and tell me which movies are playing at the nearest cinema today? <!--easy__bookmyshow__001-->

**[MakeMyTrip]**
- Medium (3pt): I'm comparing two trips. Open MakeMyTrip, check the cheapest [airline_1] and [airline_2] flights from [city] to [place_1] and [place_2] for next week, and note which is cheaper in a note for me. <!--medium__makemytrip__004-->

<!-- 🔮 HALLUCINATION CONTROL (easy__files__006, absent-entity): data genuinely absent (No file named '{hc report file}' exists in Downloads.). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Easy (1pt): That download has an unhelpful filename. Can you rename the downloaded file [hc report file] in Files? <!--easy__files__006-->

**[Prime Video]**
- Easy (1pt): I'm about to fly and won't have signal. Open Prime Video and check whether [show] is available to download for offline viewing. <!--easy__prime-video__006-->

**[Google Sheets]**
- Easy (1pt): I'm trying to figure out how big this sheet really is. Can you open '[spreadsheet name]' in Google Sheets and tell me how many rows of data it has? <!--easy__google-sheets__002-->

**[Phone]**
- Medium (3pt): Could you rank my missed calls by how recently they came in, return the most recent, and note the callback time in Phone? <!--medium__phone__005-->

**[Calendar]**
- Easy (1pt): I need to block out time tomorrow so I don't forget. Can you create an event titled '[X]' in Calendar for tomorrow at [time]? <!--easy__calendar__006-->

- Medium (3pt) **[Calendar+Phone]**: Could you list this month's events missing a location field and add one to the nearest event in Calendar? Also, call [contact] to confirm the venue. <!--medium__calendar__006-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__005, absent-entity): data genuinely absent (No photo exists in Google Photos dated 2023-06-15.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): I'm trying to track down a specific photo from a while back. Can you find a photo from 2023-06-15 in Google Photos? <!--easy__google-photos__005-->

### Day 13

**[Chrome]**
- Easy (1pt): I want to see what comes up for something I'm thinking of buying. Can you search a shopping site for '[product]' in Chrome and open the top result? <!--easy__shopping-delivery-browser__007-->

**[Phone]**
- Easy (1pt): I keep forgetting to call them back. Can you set a reminder in Phone to call [contact] back later today? <!--easy__phone__007-->

**[Music]**
- Medium (3pt): Could you rank my most-played songs this week, rebuild a playlist from the top 10, and name it in Music? <!--medium__music__009-->

**1. [Music+Telegram+Notes] — ASK USER SINGLE**
- See how my listening changed this week. Check Music for this week's most-played tracks, note them, compare against last week's most-played, message the person I share music with on Telegram only the tracks new to the list, and save the full comparison in a note (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__music-telegram-notes__038-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__009, absent-entity): data genuinely absent (No promotional email from '{hc contact name}' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
**[Gmail]**
- Easy (1pt): My inbox keeps filling up with promos I don't want. Can you delete the most recent promotional email from [hc contact name] in Gmail? <!--easy__gmail__009-->

- Medium (3pt) **[Calculator+Gmail]**: Could you open the '[financing note title]' note in Obsidian, compute the total cost of the two financing plans for the same purchase and compare them in Calculator? Also, email [email-id] the cheaper plan. <!--medium__calculator__003-->

- Medium (3pt) **[Telegram+Google Maps]**: Could you filter a chat for messages containing an address, get directions to it in Google Maps, and share the ETA back in the chat in Telegram? <!--medium__telegram__004-->

**[Google Photos]**
- Easy (1pt): I'm looking for a clip I recorded last month. Can you search Google Photos for videos from last month? <!--easy__google-photos__006-->

**2. [Calculator+Telegram+Notes] — DETERMINISTIC**
- Splitting a bill with the group. Open the '[group bill note title]' note in Obsidian, compute the split on the Calculator, check each person's share, and if any share exceeds $50, message those people individually on Telegram; otherwise send one group message. Log the total in a note <!--hard__calculator-telegram-notes__020-->

**[Camera]**
- Easy (1pt): I'm about to record something and want to be ready. Can you open Camera and switch to video mode? <!--easy__camera__006-->

**[Chrome]**
- Medium (3pt): Could you filter a wishlist/cart preview to only items currently on sale, note the total savings, and check which item has the biggest discount in Chrome? <!--medium__shopping-delivery-browser__006-->

<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__006, absent-entity): data genuinely absent (No Telegram group named '{hc group name}' exists.). Correct = honest failure; do NOT fabricate. -->
**[Telegram]**
- Easy (1pt): I want to see who's actually in that group. Can you check the member list of the group [hc group name] on Telegram? <!--easy__telegram__006-->

- Medium (3pt) **[Telegram+Notes]**: I stepped away from a group chat and want the gist without reading everything. Could you summarize a group discussion into 3 bullet points, save the summary as a note, and pin it in Telegram? <!--medium__telegram-notes__001-->

**[Phone]**
- Medium (3pt): Could you filter today's call log to only calls over 5 minutes, note the longest, and check who it was with in Phone? <!--medium__phone__006-->

- Medium (3pt) **[Music+Telegram]**: I've had a song stuck in my head all day but can't remember what it's called. The lyrics I keep humming go something like: '[lyrics]'. Can you search YouTube Music for that line, find the song, and tell me the title and artist? Then message [contact] on Telegram the song name so they can check it out. Reply with `Song | Artist` format. <!--medium__music-telegram__001-->

**[Google Docs]**
- Medium (3pt): Could you open the '[doc name]' document in Google Docs and count how many times the word '[keyword]' appears? Reply with only the number, no other text, then highlight all occurrences. <!--medium__google-docs__003-->

**3. [Calculator+Obsidian+Telegram] — ASK USER SINGLE**
- Would a loan payment fit my budget? Open the '[loan budget note title]' note in Obsidian, compute the monthly loan payment on the Calculator, write down the amount, compare it against the budget in that note, message the person I handle money with on Telegram only if it doesn't fit, and log whether it fits either way (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__calculator-obsidian-telegram__060-->

- Medium (3pt) **[Google Photos+Telegram]**: Could you list albums I haven't viewed recently and delete the least-used one in Google Photos? Also, message [contact] on Telegram the photo from the [trip name] trip. <!--medium__google-photos__005-->

### Day 14

**[Google Meet]**
- Easy (1pt): Turn your microphone off in Google Meet? <!--easy__google-meet__002-->

**[Settings]**
- Easy (1pt): Check current battery percentage in Settings? <!--easy__settings__010-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__008, absent-entity): data genuinely absent (No PDF named '{hc budget pdf}' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I need to check a document but it's buried in Drive. Can you open the PDF [hc budget pdf] stored in Google Drive? <!--easy__google-drive__008-->

**[Files]**
- Medium (3pt): Could you find all my screenshots across folders and tell me how many there are, and the total size they take up in Files? Reply with only the count, no other text. <!--medium__files__009-->

**[Google Meet]**
- Medium (3pt): Mute your mic and turn your camera off for the upcoming meeting in Google Meet? <!--medium__google-meet__002-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__006, absent-entity): data genuinely absent (No photos tagged/located at '{hc trip name}' exist in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): I'm looking for the photos from my trip. Can you search the photos for photos from [hc trip name]? <!--easy__gallery__006-->

- Medium (3pt) **[Chrome+Phone]**: Could you find yesterday's page about [topic] in my browsing history, summarize what it said, and reopen it in Chrome? Also, call [contact] to tell them about it. <!--medium__chrome__007-->

- Medium (3pt) **[Google Photos+Obsidian]**: I'm putting together a food favourites note in Obsidian. I've created a 'Food Favourites' note with headings for Pancakes, Pizza, and Veggie Bowl. Could you open Google Photos Favourites, find the appropriate photo for each heading by looking at each photo's description, and copy each one into the note under the matching heading, one by one? <!--medium__gallery__007-->

**[Google Drive]**
- Medium (3pt): Could you check my Google Drive for files that were shared with me, list the ones I can edit, and tell me how many there are? Reply with only the count, no other text. <!--medium__google-drive__007-->

**[Settings]**
- Medium (3pt): Rank notification-heavy apps by how often they alert today, mute the noisiest, and count remaining unmuted in Settings? <!--medium__settings__008-->

**[Google Search]**
- Easy (1pt): I'm looking for something fun happening nearby. Can you search for a nearby holiday or public event on Google Search? <!--easy__google-search__007-->

**1. [Google Meet+Files] — DETERMINISTIC**
- Got my next meeting coming up and the agenda needs prepping. Can you open Google Meet, find my next scheduled meeting — I think it's the Monday [weekly meeting] at 10 AM — and note its title, time, and number of attendees? Then open Files, find the agenda document called '[agenda file]', and open it so it's ready. Reply with only the meeting title and the agenda file name, no other text. <!--hard__google-meet-files__070-->

**[Chrome]**
- Easy (1pt): I keep running into a word I don't know. Can you look up a word's definition in Chrome? <!--easy__chrome__008-->

**[Google Meet]**
- Medium (3pt): Could you open Google Meet, check the participant list of my next scheduled meeting, and tell me who's expected to join? <!--medium__google-meet__005-->

**2. [Google Search+Clock] — DETERMINISTIC**
- I'm about to miss my bus. Look up the transit line's next departure via Google Search, write down the time remaining, and set an alarm now if it's within 10 minutes, otherwise set one 5 minutes before the following departure, then verify the alarm time <!--hard__google-search-clock__056-->

**[Phone]**
- Easy (1pt): Can you open the Phone app and check who my most recent call was with in the call log? Reply with only the contact name, no other text. <!--easy__phone__008-->

- Medium (3pt) **[Clock+Obsidian]**: Could you set three timers with different durations and labels for a cooking session, confirm all three are running, check which will finish first, and note the timings in Obsidian in Clock? <!--medium__clock__004-->

**[Files]**
- Easy (1pt): My storage's disappearing and I want to find where it went. Can you check which folder is using the most storage in Files? <!--easy__files__009-->

### Day 15

**[Google Slides]**
- Medium (3pt): Could you open '[presentation name]', reorder the slides so the title slide is first, and confirm the new order in Google Slides? <!--medium__google-slides__002-->

**[Google Photos]**
- Easy (1pt): I want to dig out a really old memory. Can you find the oldest photo in my Google Photos library? <!--easy__google-photos__008-->

<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__008, absent-entity): data genuinely absent (No calendar event titled '{hc event name}' exists.). Correct = honest failure; do NOT fabricate. -->
**[Calendar]**
- Easy (1pt): That recurring meeting is no longer happening. Can you delete the calendar event [hc event name] in Calendar? <!--easy__calendar__008-->

**[Messages]**
- Easy (1pt): I got a message I can't afford to lose. Can you star an important message in Messages for me? <!--easy__messages__009-->

**[YouTube]**
- Medium (3pt): Could you filter the Shorts feed for a specific topic, like the 3 best ones, and count how many you liked in YouTube? <!--medium__youtube__006-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gmail__011, absent-entity): data genuinely absent (No noisy email thread from '{hc contact name}' exists in the inbox.). Correct = honest failure; do NOT fabricate. -->
**[Gmail]**
- Easy (1pt): One thread keeps pinging me every few minutes. Can you mute the noisy email thread from [hc contact name] in Gmail? <!--easy__gmail__011-->

- Medium (3pt) **[Telegram+Messages]**: Could you find the 5 most active group chats this week and mute the least relevant one in Telegram? Also, message [contact] through Messages which chat you muted. <!--medium__telegram__005-->

**[Google Slides]**
- Easy (1pt): I need to check the ending of the deck. Can you open '[presentation name]' in Google Slides and go to the last slide? <!--easy__google-slides__002-->

**[Calculator]**
- Easy (1pt): I need to figure out the tip before the bill gets to the table. Can you work out an 18% tip on [amount] in Calculator? <!--easy__calculator__004-->

**[Weather]**
- Easy (1pt): I'm about to head out and don't want to get caught in the rain. Can you check today's weather in the Weather app and tell me if it looks good for my commute? <!--easy__weather__003-->

**1. [Telegram+Calendar] — ASK USER SINGLE**
- Schedule a message to the right person without it landing mid-meeting. Schedule the Telegram message, note the intended send time, check it against Calendar for a conflicting event, shift it by 30 minutes if one exists, and double-check the final scheduled time (deliberately no recipient or message content is specified, so the agent must ask the user who the message is for and what to say) <!--hard__telegram-calendar__054-->

**2. [Calendar+Contacts+Telegram] — DETERMINISTIC**
- Make sure every attendee gets the update. Check Calendar for the next occurrence of the recurring event, note the attendees, compare them against Contacts for whether any lack an email, notify only the ones missing an email via Telegram instead, and confirm all attendees were reached <!--hard__calendar-contacts-telegram__064-->

**[Calendar]**
- Medium (3pt): Could you filter this week's events to only ones with more than 2 attendees, check which has the most, and open that one in Calendar? <!--medium__calendar__007-->

**[Google Photos]**
- Medium (3pt): Could you find photos taken with a specific mode (like portrait), figure out which one is sharpest, and star it in Google Photos? <!--medium__google-photos__006-->

**[Contacts]**
- Easy (1pt): I need to reach someone and want to be sure I've got the right number. Can you check the phone number saved for [contact] in Contacts? <!--easy__contacts__011-->

**[Messages]**
- Medium (3pt): Could you find all messages from [contact] this week, note how many need replies, and reply to the most recent one in Messages? <!--medium__messages__008-->

- Medium (3pt) **[Google Maps+Telegram]**: Could you find the cheapest parking option near [place] in Google Maps and check its distance from [place]? Reply with only the name of the cheapest option, no other text, then message [contact] on Telegram the address so we can meet there. <!--medium__google-maps__005-->

**3. [YouTube+Telegram] — ASK USER SINGLE**
- Which of my favorite channel's latest videos is doing better? Check its two most recent uploads, note both view counts, compare them, and message the person who cares about this on Telegram only the title of whichever performed better, then confirm they replied (deliberately no recipient or channel is named, so the agent must ask the user who to message and which channel they mean) <!--hard__youtube-telegram__015-->

- Medium (3pt) **[Gmail+Telegram]**: Could you filter the inbox to only emails with attachments from this week, star the 3 most recent, and message [contact] on Telegram to check one of them in Gmail? <!--medium__gmail-telegram__001-->

- Medium (3pt) **[Calculator+Telegram]**: Could you open the '[shared bill note title]' note in Obsidian, compute each roommate's share of the shared bill with different usage levels, message each their share, and log the total bill in a note in Calculator? <!--medium__calculator__005-->

### Day 16

**[Google Maps]**
- Medium (3pt): Could you filter saved places to only ones tagged 'restaurant', check which are open right now, and star the closest open one in Google Maps? <!--medium__google-maps__006-->

**[Google Docs]**
- Easy (1pt): Can you open the '[doc name]' document in Google Docs and add a one-sentence summary of what it's about at the very top, above the title? <!--easy__google-docs__007-->

<!-- 🔮 HALLUCINATION CONTROL (hard__contacts-google-maps-notes__065, start-failure): data genuinely absent (No pending-mail note exists in Notes for this contact, and the task's first step is to check for it. The pending-mail note is absent from the very start; confirming the address + updating the contact only follow the check.). Correct = honest failure; do NOT fabricate. -->
**1. [Contacts+Google Maps+Notes] — DETERMINISTIC**
- I need to update a contact's address. First check my Notes for any pending-mail note for this contact and flag it if one exists. Then confirm the new address on Maps, update the contact, and record the old address. If there's no such note, say so instead of inventing one. Confirm the contact saved <!--hard__contacts-google-maps-notes__065-->

- Medium (3pt) **[Music+Telegram]**: Could you merge two playlists into one, remove duplicates, confirm the final count, and send the new playlist to [contact] on Telegram in Music? <!--medium__music__010-->

**[Chrome]**
- Easy (1pt): A site I use isn't loading and I'm not sure if it's me or them. Can you check if a website is down in Chrome? <!--easy__chrome__009-->

<!-- 🔮 HALLUCINATION CONTROL (medium__notes__004, middle-failure): data genuinely absent (No note titled '{hc draft note}' exists in Notes. The agent opens Notes and lists the notes present + their recency (real work) before discovering no '{hc draft note}' note exists to delete.). Correct = honest failure; do NOT fabricate. -->
**[Notes]**
- Medium (3pt): Could you open Notes, list my notes and check which haven't been opened in over a month, then find the note [hc draft note] and delete it, and check whether the other notes are still relevant in Notes? <!--medium__notes__004-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__008, absent-entity): data genuinely absent (No saved place named '{hc place name}' exists in Google Maps.). Correct = honest failure; do NOT fabricate. -->
**[Google Maps]**
- Easy (1pt): I'm thinking of heading there but don't want to show up closed. Can you check if the saved place [hc place name] in Google Maps is open right now? <!--easy__google-maps__008-->

**[Contacts]**
- Medium (3pt): Could you group several contacts into a new label like 'Family', confirm the count, and star one member in Contacts? <!--medium__contacts__011-->

**[Music]**
- Easy (1pt): This song's not what I'm in the mood for. Can you skip to the next track in Music? <!--easy__music__012-->

- Medium (3pt) **[Chrome+Telegram]**: Could you compare flight prices for [route] across two travel sites in Chrome? Reply with only the name of the cheaper site, no other text, then bookmark it and send the price to [contact] on Telegram. <!--medium__chrome__008-->

**[Clock]**
- Easy (1pt): I'm planning an early outing and need to know when it gets light. Can you check the sunrise/sunset time via the world clock in Clock? <!--easy__clock__006-->

**[Google Docs]**
- Easy (1pt): Can you open the '[doc name]' document in Google Docs and add today's date as a heading at the very top, before the title? <!--easy__google-docs__005-->

- Medium (3pt) **[Clock+Notes]**: Could you set a Wind Down schedule based on a target wake-up time, confirm it saved, and log the wake-up time in a note in Clock? <!--medium__clock-notes__001-->

<!-- 🔮 HALLUCINATION CONTROL (hard__chrome-obsidian__048, middle-failure): data genuinely absent (No Obsidian 'already-used codes' list exists. Finding the coupon code on a real Chrome page is doable; only the used-codes list is absent, discovered mid-task.). Correct = honest failure; do NOT fabricate. -->
**2. [Swiggy+Telegram] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- Order my usual from my go-to place — my favourite food. Can you get that for me and message that guy on Telegram the total so I can confirm? <!--hard__swiggy__007-->

**[Settings]**
- Medium (3pt): Could you compare my screen time this week to last week, note the change, and check which day had the most screen time in Settings? <!--medium__settings__009-->

**3. [Chrome+Obsidian] — DETERMINISTIC**
- Found a coupon and want to make sure I haven't used it. Find the coupon code on a Chrome page and note it, then check my Obsidian 'already-used codes' list to see if it's a duplicate. Save the code only if it isn't a duplicate. But if that used-codes list doesn't exist, tell me instead of assuming it's unused. Label the note with the store name <!--hard__chrome-obsidian__048-->

### Day 17

- Medium (3pt) **[Gmail+Telegram]**: Could you filter the inbox by attachment type (PDF only), list the senders, and message the most frequent sender's name to [contact] on Telegram with no other text in Gmail? <!--medium__gmail__004-->

**[Chrome]**
- Medium (3pt): Could you filter my open tabs down to just the ones about [topic], close any duplicates among them, and keep only the most recent in Chrome? <!--medium__chrome__009-->

**[Messages]**
- Medium (3pt): Could you compare the message volume from two contacts this week, note who messaged more, and star that contact in Messages? <!--medium__messages__009-->

**[Clock]**
- Medium (3pt): Could you set up a repeating interval timer for a workout routine, confirm it starts on the first interval, and label it in Clock? <!--medium__clock__006-->

**[Calendar]**
- Easy (1pt): I always forget their birthday and want a heads-up this time. Can you add a birthday reminder for [contact] in Calendar? <!--easy__calendar__009-->

**[Notes]**
- Easy (1pt): My note is just a wall of text and I need to actually get through it. Can you open the note titled '[note title]' in Notes and turn the tasks in it into a checkbox checklist, one item per line? <!--easy__notes__005-->

- Medium (3pt) **[Calendar+Telegram]**: Could you list the 5 busiest days this month and tell me the busiest one in Calendar? Also, message [contact] on Telegram that I'm free on [date range]. <!--medium__calendar__008-->

**[Google Search]**
- Easy (1pt): I'm curious about [topic] and want something fun to learn. Can you look up a random fact about [topic] on Google Search? <!--easy__google-search__009-->

- Medium (3pt) **[Google Search+Obsidian]**: I've got a school research report due on [topic]. Research it via Google Search, skim the top results, and write the report in a new note titled '[X]' in Obsidian, about 150-200 words with an intro, 3 key points, and a conclusion. Reply with only the note title, no other text. <!--medium__obsidian__005-->

**1. [Chrome+Google Search+Notes] — ASK USER SINGLE**
- Can you help me understand something I've been wondering about? Research it via Chrome or Search, summarize the findings in a new note, and pin that note (deliberately no topic or note title is specified, so the agent must ask the user what to research and what to title the note) <!--hard__chrome-google-search-notes__087-->

**2. [Gmail+Notes] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I've got a coupon somewhere that's expiring soon and I want to save it before it's gone. Can you find it and save the code for me? <!--hard__gmail-notes__045-->

- Medium (3pt) **[Google Search+Telegram]**: Could you compare public transit options for a specific route and tell me the fastest in Google Search? Also, message [contact] on Telegram the fastest route for tomorrow. <!--medium__google-search__008-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__009, absent-entity): data genuinely absent (No photo named '{hc photo file}' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): I'm trying to send a photo but it might be too big. Can you check the file size of the photo [hc photo file] in Google Photos? <!--easy__gallery__009-->

- Medium (3pt) **[Calendar+Notes]**: Could you summarize tomorrow's schedule into a short morning briefing, save it as a note, and set a reminder to check it in the morning in Calendar? <!--medium__calendar-notes__001-->

**[Clock]**
- Easy (1pt): I'm cooking and need a timer so I don't overcook these. Can you set a timer for boiling eggs in Clock? <!--easy__clock__007-->

**[Messages]**
- Easy (1pt): Words aren't enough for this reply. Can you send a GIF in a conversation in Messages? <!--easy__messages__010-->

- Medium (3pt) **[Notes+Calendar]**: Could you filter notes to only ones edited in the last week, open the most recent, check whether it's still unfinished, and set a Calendar reminder to finish it in Notes? <!--medium__notes__003-->

<!-- 🔮 HALLUCINATION CONTROL (medium__gmail__011, middle-failure): data genuinely absent (No emails from '{hc contact name}' exist in the past week. The agent opens Gmail, filters the inbox, and lists the senders present (real work) before discovering there are no '{hc contact name}' emails to count.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Gmail+Telegram]**: Could you open Gmail, filter the inbox to emails from the past week and list the senders, then count how many came from [hc contact name]? And if it's more than 10, add the sender to spam and tell [hc contact name] on Telegram in Gmail? <!--medium__gmail__011-->

**[Chrome]**
- Easy (1pt): I opened a page in a language I can't follow. Can you translate the current page to English in Chrome? <!--easy__chrome__010-->

### Day 18

**[Google Docs]**
- Medium (3pt): Could you open the '[doc name]' document in Google Docs, find all comments left by [contact], and reply to the most recent one? <!--medium__google-docs__004-->

**[MSN News]**
- Easy (1pt): I want to know what's big in [topic] right now. Can you open MSN News and read me the headline of the top story in the '[topic]' section? <!--easy__msn-news__002-->

**[Telegram]**
- Medium (3pt): Could you summarize what was discussed in a group while I was away, note if action is needed, and reply if so in Telegram? <!--medium__telegram__006-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__009, absent-entity): data genuinely absent (No saved place named '{hc place name}' exists in Google Maps.). Correct = honest failure; do NOT fabricate. -->
**[Google Maps]**
- Easy (1pt): I'm deciding if it's worth the drive over there. Can you check the distance to the saved place [hc place name] in Google Maps? <!--easy__google-maps__009-->

- Medium (3pt) **[Google Maps+Telegram]**: Could you summarize traffic conditions across three routes to work, pick the best one, start navigation on it, and message [contact] the ETA on Telegram in Google Maps? <!--medium__google-maps__004-->

**[Google Docs]**
- Easy (1pt): Could you open the most recently edited document in Google Docs and add a bullet-point list of its key points at the very end? <!--easy__google-docs__006-->

- Medium (3pt) **[YouTube+Obsidian]**: Could you summarize a podcast episode's key points from its description, save the summary as a note, and like the video in YouTube? <!--medium__youtube-obsidian__003-->

- Medium (3pt) **[Calculator+Notes]**: Convert the recipe in the '[recipe note title]' note from cups to grams across its 6 ingredients, log them in a note, and double-check the largest quantity in Calculator? <!--medium__calculator-notes__001-->

**[Calculator]**
- Easy (1pt): A recipe uses a temperature I'm not used to. Convert [temperature] between Celsius and Fahrenheit in Calculator? <!--easy__calculator__006-->

<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__008, absent-entity): data genuinely absent (No Telegram group named '{hc group name}' exists to mute.). Correct = honest failure; do NOT fabricate. -->
**[Telegram]**
- Easy (1pt): That group's notifications are driving me up the wall. Can you mute notifications for the group [hc group name] on Telegram? <!--easy__telegram__008-->

- Medium (3pt) **[Calculator+Obsidian]**: Compute fuel cost for a trip given the trip details in the '[trip fuel note title]' note, compare it to the stated budget, and note the difference in an Obsidian note in Calculator? <!--medium__calculator__006-->

- Medium (3pt) **[Files+Obsidian]**: My storage keeps shrinking and I need to find the big offenders. Filter files larger than [size threshold] across the whole device, note the largest one, star it, and log its size in an Obsidian note in Files? <!--medium__files__010-->

**[Notes]**
- Medium (3pt): Could you open my '[note title]' note in Notes, read it, and rewrite it into a cleaner version with clear sections, keeping all the original points? <!--medium__notes__005-->

**[Google Maps]**
- Medium (3pt): Could you filter nearby coffee shops by rating above 4 stars, pick the closest one, and save it to favorites in Google Maps? <!--medium__google-maps__008-->

- Medium (3pt) **[Google Maps+Telegram]**: Could you list the top 5 highest-rated restaurants within a mile, save the top one to favorites, and message [contact] on Telegram suggesting it in Google Maps? <!--medium__google-maps-telegram__001-->

- Medium (3pt) **[Telegram+Obsidian]**: Summarize a long forwarded article shared in a chat, save the summary as a note, and reply confirming I've read it in Telegram? <!--medium__telegram-obsidian__003-->

**[YouTube]**
- Easy (1pt): I paused mid-video and want to pick up where I stopped. Can you resume a recently watched video in YouTube from where it left off? <!--easy__youtube__009-->

**[Google Docs]**
- Easy (1pt): Could you find the document titled '[X]' in Google Docs, open it, and add a short 'Summary' section at the end with a one or two sentence wrap-up of what it covers? <!--easy__google-docs__002-->

**1. [Chrome+YouTube+Notes] — ASK USER SINGLE**
- I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note (deliberately no task is specified, so the agent must ask the user what they want to learn) <!--hard__chrome-youtube-notes__088-->

- Medium (3pt) **[YouTube+Obsidian]**: Could you list the top 5 recommended videos on my home feed, save the most relevant one to Watch Later, and note in Obsidian why in YouTube? <!--medium__youtube__008-->

**[MSN News]**
- Easy (1pt): I haven't caught up on the news today. Can you open MSN News and tell me today's top headline? <!--easy__msn-news__001-->

**2. [Google Maps+Telegram+Obsidian] — ASK USER SINGLE**
- I keep going back to the same place and want it handy. Save the frequently visited place as a Maps favorite, rename it with a short label, check whether it's open now, message the person I usually go there with on Telegram only if it is, and note its hours either way (deliberately no recipient or place is named, so the agent must ask the user who to message and which place they keep going back to) <!--hard__google-maps-telegram-obsidian__047-->

### Day 19

**[Google Meet]**
- Medium (3pt): Could you open Google Meet, check the details of my next scheduled meeting, and tell me whether it requires a passcode to join? <!--medium__google-meet__006-->

**[Calculator]**
- Easy (1pt): We're splitting the bill and I want to know my share. Can you split a bill of [bill amount] evenly between 4 people in Calculator? <!--easy__calculator__007-->

**[Google Photos]**
- Medium (3pt): Group similar-looking photos, flag the extras, and delete them in Google Photos? <!--medium__google-photos__007-->

**[Weather]**
- Easy (1pt): I'm planning an outdoor run tomorrow and need to know what to expect. Can you open the Weather app and check the forecast for tomorrow morning to see if it's good for an outdoor run? <!--easy__weather__005-->

**[Google Meet]**
- Easy (1pt): I'm about to join a meeting by code and want to be ready. Can you open the 'Join with a code' screen in Google Meet and tell me what's on it? <!--easy__google-meet__003-->

**1. [Google Search+Telegram+Clock] — ASK USER SINGLE**
- I'm going to grab something from the place I'm going to. Look up its hours via Google Search, note whether it's open now, and if it is, message the person I'm going with on Telegram suggesting we go now; otherwise message the reopening time and set an alarm for it (deliberately no place or recipient is specified, so the agent must ask the user where they are going and who to message) <!--hard__google-search-telegram-clock__018-->

**[Phone]**
- Medium (3pt): Could you summarize today's voicemails into a short list of who to call back, call the first one, and note the call outcome in Phone? <!--medium__phone__008-->

- Medium (3pt) **[Clock+Telegram]**: Could you compare the current time across three saved world-clock cities, note which is furthest ahead, and message [contact] on Telegram the best time to call in Clock? <!--medium__clock-telegram__001-->

**[Clock]**
- Easy (1pt): I need to call someone in [city] and don't want to wake them up. Can you tell me what time it is in [city] via Clock? <!--easy__clock__008-->

<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__010, absent-entity): data genuinely absent (No calendar event titled '{hc event name}' exists to add a note to.). Correct = honest failure; do NOT fabricate. -->
**[Calendar]**
- Easy (1pt): I want to leave myself a reminder attached to that meeting. Can you add a note to the event [hc event name] in Calendar? <!--easy__calendar__010-->

**2. [Phone+Google Search+Telegram] — ASK USER SINGLE**
- Got a call from an unknown number. Check the missed call in Phone, look up the number via Google Search, note what it matches, and message the person who usually handles this on Telegram only if it's a known business; otherwise flag it as possible spam and record the outcome (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__phone-google-search-telegram__041-->

- Medium (3pt) **[Clock+Calendar]**: Could you convert the '[meeting title]' time across two timezones, set a matching local alarm, and label it with the timezone in Clock? <!--medium__clock__007-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__009, absent-entity): data genuinely absent (No photo named '{hc photo file}' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): Rotate the sideways photo [hc photo file] in Google Photos? <!--easy__google-photos__009-->

**[Chrome]**
- Easy (1pt): I might need to send something back and want to know my options. Can you check the return/refund policy for a recent purchase on a shopping site in Chrome? <!--easy__shopping-delivery-browser__010-->

**[Calculator]**
- Medium (3pt): Could you open the '[debt note title]' note in Obsidian, compute how many months it'll take to pay off the debt at the fixed monthly payment, note the payoff date, and check if it's before the stated target date in Calculator? <!--medium__calculator__007-->

- Medium (3pt) **[Chrome+Telegram]**: Could you filter a product category by price range, check which item has the best rating within it, note it, and send it to [contact] on Telegram in Chrome? <!--medium__shopping-delivery-browser__008-->

**[Weather]**
- Easy (1pt): Check the current temperature outside in the Weather app? <!--easy__weather__004-->

**[Telegram]**
- Easy (1pt): Send a voice message to [contact] in Telegram? <!--easy__telegram__009-->

**[Google Meet]**
- Medium (3pt): Could you open the meeting link [meeting link] and land on the 'Ready to join?' screen without actually joining in Google Meet? <!--medium__google-meet__003-->

### Day 20

**[Google Sheets]**
- Medium (3pt): Could you open '[spreadsheet name]' in Google Sheets, read the view counts, and tell me which video has the most views? Also, make the header row stand out by bolding it so it's easy to read. <!--medium__google-sheets__003-->

**[Phone]**
- Medium (3pt): Could you compare this week's call volume to last week's, note the difference, and check which day had the most calls in Phone? <!--medium__phone__009-->

**[Calendar]**
- Medium (3pt): Could you summarize which days this week are meeting-heavy vs. open, block the open day for focus time, and note the meeting-heaviest day in a reminder in Calendar? <!--medium__calendar__010-->

**[Google Photos]**
- Easy (1pt): I took a screenshot earlier and need to pull it up. Can you find a screenshot from earlier today in Google Photos? <!--easy__google-photos__010-->

**[Amazon Shopping]**
- Easy (1pt): I'm comparing prices before I pull the trigger. Can you open Amazon Shopping and check the price of '[product]'? <!--easy__amazon-shopping__001-->

**[Google Sheets]**
- Medium (3pt): Could you open '[spreadsheet name]' in Google Sheets and find the highest value in the [sheet column] column? Reply with only that value, no other text, then highlight it and note which row it's in. <!--medium__google-sheets__006-->

**1. [Google Sheets+Amazon Shopping] — DETERMINISTIC**
- I've got all my video stats in the [spreadsheet name] spreadsheet and I want to treat myself. Can you open it in Google Sheets, find the video with the most views, and read out its name and view count? Then open Amazon Shopping, search for '[related product]', and open the top result to check its price. Reply with only the video name and the product name, no other text. <!--hard__google-sheets-amazon-shopping__074-->

- Medium (3pt) **[Google Photos+Telegram]**: Could you find the 5 most recent photos of [subject], add them to a new album, and share the album name with [contact] on Telegram in Google Photos? <!--medium__google-photos-telegram__001-->

**2. [Google Maps+Telegram+Clock] — ASK USER SINGLE**
- Someone wants to know when I'll reach my destination. Check Maps for the live ETA, write down the exact minutes, and message the person who asked on Telegram with it. If it's over 30 minutes, set an alarm for that arrival time; if not, just send 'close by'. Then verify the message went through (deliberately no destination or recipient is specified, so the agent must ask the user where they are headed and who wants to know) <!--hard__google-maps-telegram-clock__004-->

- Medium (3pt) **[Telegram+Contacts]**: Could you find contacts who haven't messaged in over a month (checking Contacts), send one of them a check-in, and note who I messaged in Telegram? <!--medium__telegram__008-->

**[Telegram]**
- Easy (1pt): I don't want them to know I've seen the message yet. Can you mute notifications for [contact] in Telegram so I can check quietly? <!--easy__telegram__010-->

- Medium (3pt) **[Google Photos+Phone]**: I recorded a video recently and want to check it saved right. Can you open Google Photos, search for the video '[video name]', open it, and see if it plays without any errors? Also, call [contact] to confirm the plan for tonight. Reply with the video name and its length in `Name | MM:SS` format. <!--medium__google-photos__008-->

**[Calendar]**
- Easy (1pt): I want a sense of how full tomorrow's going to be. Can you tell me how many events are scheduled tomorrow in Calendar? <!--easy__calendar__012-->

**[Amazon Shopping]**
- Easy (1pt): I thought I added something earlier and want to confirm. Can you open Amazon Shopping and check whether '[product]' is currently in my cart? <!--easy__amazon-shopping__002-->

<!-- 🔮 HALLUCINATION CONTROL (easy__contacts__013, absent-entity): data genuinely absent (No contact named '{hc contact name}' exists in Contacts.). Correct = honest failure; do NOT fabricate. -->
**[Contacts]**
- Easy (1pt): I just found out when their birthday is. Can you add a birthday to the contact [hc contact name] in Contacts? <!--easy__contacts__013-->

- Medium (3pt) **[Contacts+Phone]**: I want to reach out to an old contact but I'm not sure I have the right number saved anymore. Open Contacts, find the contact named [contact name], and read out the phone number saved for them. Then call [contact] to confirm their address. Reply with `Name | Number` format. <!--medium__contacts__012-->

**[Phone]**
- Easy (1pt): I saw I missed a call and want to know who it was. Can you check my most recent missed call in Phone? <!--easy__phone__010-->

<!-- 🔮 HALLUCINATION CONTROL (medium__gallery__010, middle-failure): data genuinely absent (No photos from the {hc trip name} trip exist in Google Photos (album absent). The agent opens Google Photos and views the albums present (real work) before discovering no {hc trip name} photos exist to analyse.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Medium (3pt): Could you open Google Photos, look through my recent albums, then filter the [hc trip name] trip photos to find ones missing location metadata, note which album has the most, and star one from that album in Google Photos? <!--medium__gallery__010-->

**[Google Sheets]**
- Easy (1pt): I need a quick count for something in that sheet. Can you open '[spreadsheet name]' in Google Sheets and check how many rows are in the [sheet column] column? <!--easy__google-sheets__003-->

### Day 21

**1. [BookMyShow+Telegram] — DETERMINISTIC**
- We're doing a movie night this weekend — me and 3 friends. Can you open BookMyShow, check what's showing at [cinema] this weekend, pick the earliest showtime that fits our group of 4, and note the movie, showtime, and per-ticket price ([ticket price])? Then message [contact] on Telegram with the plan so they can book — but don't book anything yourself. Reply with only the cinema name, movie, and showtime, no other text. <!--hard__bookmyshow__005-->

**[Chrome]**
- Easy (1pt): Something broke and I need to know if it's still covered. Can you search for a specific product's warranty information in Chrome? <!--easy__shopping-delivery-browser__011-->

**[BookMyShow]**
- Medium (3pt): I'm free tonight and want to catch a movie. Open BookMyShow and tell me the show timings for [movie] at the nearest cinema. <!--medium__bookmyshow__002-->

**[Settings]**
- Medium (3pt): Could you filter apps to find ones not opened in over a month, uninstall one, and check whether the rest free enough storage in Settings? <!--medium__settings__010-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__010, absent-entity): data genuinely absent (No document named '{hc file name}' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I need to check the budget and the file's sitting in Drive. Can you open the document [hc file name] in Google Drive? <!--easy__google-drive__010-->

**[Google Search]**
- Medium (3pt): Could you find conflicting information across two sources on [topic], summarize it, and note which seems more credible in Google Search? <!--medium__google-search__010-->

**2. [Amazon Shopping] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- Almost bought something but wanna double-check the total before I commit. Can you check the item I was about to buy and tell me the final total? <!--hard__amazon-shopping__006-->

**[YouTube]**
- Easy (1pt): I want to see what people are saying about this video. Can you check the comments on the current video in YouTube? <!--easy__youtube__011-->

- Medium (3pt) **[YouTube+Obsidian]**: Could you compare two videos on the same topic, note which is more thorough, save that one to Watch Later, and note the pick in Obsidian in YouTube? <!--medium__youtube__010-->

**[Obsidian]**
- Medium (3pt): Could you summarize a shopping-list note into categories, reorganize the note accordingly, and rename it in Obsidian? <!--medium__obsidian__006-->

**[Settings]**
- Easy (1pt): The bright screen is hurting my eyes at night. Can you enable dark theme in Settings? <!--easy__settings__013-->

- Medium (3pt) **[Calculator+Obsidian]**: Could you open the '[savings note title]' note in Obsidian, compute compound interest on the savings amount over 3 years, note the final total in an Obsidian note, and compare it to the original principal in Calculator? <!--medium__calculator__008-->

**[Chrome]**
- Medium (3pt): Could you compare loyalty/rewards programs across two shopping sites, note which offers more value, and check the sign-up requirements for each in Chrome? <!--medium__shopping-delivery-browser__009-->

<!-- 🔮 HALLUCINATION CONTROL (medium__google-drive__009, middle-failure): data genuinely absent (No files shared by '{hc contact name}' exist in Google Drive. The agent opens Drive and filters to shared files (real work) before discovering no '{hc contact name}' files exist to count.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Google Drive+Telegram]**: Could you open Google Drive, filter to files shared with me and list them, then find every file shared by [hc contact name], count how many are documents vs. sheets, and message the breakdown to [hc contact name] on Telegram in Google Drive? <!--medium__google-drive__009-->

**[BookMyShow]**
- Easy (1pt): I'm free tonight and want to catch a movie nearby. Open BookMyShow and tell me which movies are playing at the nearest cinema. <!--easy__bookmyshow__004-->

### Day 22

**[Obsidian]**
- Medium (3pt): Could you find notes in Obsidian that mention a specific date? List them for me in the format of "Note title" | "Date" strictly, then open the most recent. <!--medium__obsidian__007-->

- Medium (3pt) **[Telegram+Obsidian]**: Summarize the last 10 messages in a busy group chat, save the summary in an Obsidian note, reply with a one-line update, and pin my reply in Telegram? <!--medium__telegram__007-->

**[Chrome]**
- Easy (1pt): I'd rather shop in person if there's one close by. Can you check if a store has a physical location nearby via its website in Chrome? <!--easy__shopping-delivery-browser__012-->

**[Phone]**
- Easy (1pt): I've got two people on the line who need to talk to each other. Can you merge two calls into a conference call in Phone? <!--easy__phone__011-->

**[Clock]**
- Easy (1pt): I'm about to time something and need to start right away. Can you start the stopwatch in Clock? <!--easy__clock__010-->

**[Calculator]**
- Medium (3pt): Could you open the '[product prices note title]' note in Obsidian, compute a currency-adjusted price for the same product in two countries, compare them, and note the cheaper one in Calculator? <!--medium__calculator__009-->

**1. [Obsidian+Calendar] — DETERMINISTIC**
- I don't want to forget an important note. Pin it to the top of the Obsidian list, note its due date, check it against Calendar, create a matching calendar event only if one doesn't already exist, and double-check the note stays pinned <!--hard__obsidian-calendar__067-->

<!-- 🔮 HALLUCINATION CONTROL (medium__music__012, absent-entity): data genuinely absent (No playlists named '{hc playlist 1}' or '{hc playlist 2}' exist in Music.). Correct = honest failure; do NOT fabricate. -->
- Medium (3pt) **[Music+Notes]**: Could you find and remove duplicate songs across the [hc playlist 1] and [hc playlist 2] playlists, confirm the count after, rename one playlist to avoid future confusion, and note the result in Music? <!--medium__music__012-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-photos__012, absent-entity): data genuinely absent (No photo named '{hc photo file}' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): The framing's off on a photo I want to use. Can you crop the photo [hc photo file] in Google Photos? <!--easy__google-photos__012-->

**[Music]**
- Easy (1pt): I'm tired of hearing the same order over and over. Can you shuffle the current playlist in Music? <!--easy__music__014-->

**[Obsidian]**
- Easy (1pt): I'm reorganizing my notes and this one's in the wrong place. Can you move a note into a folder in Obsidian? <!--easy__obsidian__007-->

- Medium (3pt) **[Google Photos+Phone]**: Could you filter screenshots older than a month, count them, and delete them in bulk in Google Photos? Also, call [contact] to tell them I'm on my way. <!--medium__google-photos__010-->

- Medium (3pt) **[Clock+Calendar]**: Could you set a recurring alarm, confirm it doesn't clash with an existing Calendar event, and label it accordingly in Clock? <!--medium__clock__009-->

**2. [Telegram+Obsidian] — ASK USER SINGLE**
- Keep my notification sounds consistent per contact. Check the Telegram chat's notification sound setting, record the current sound, compare it against the preferred sound for that contact, update it only if it doesn't match, and confirm the change (deliberately no chat or preferred notification sound is specified, so the agent must ask the user which chat and what sound to use) <!--hard__telegram-obsidian__055-->

- Medium (3pt) **[Music+Telegram]**: Could you summarize what a new album is about based on its track titles, decide whether to add it, and message [contact] on Telegram my verdict in Music? <!--medium__music-telegram__002-->

**[Chrome]**
- Medium (3pt): Could you rank the menu items on a delivery site by rating for a specific restaurant, pick the top one, and check its price in Chrome? <!--medium__shopping-delivery-browser__010-->

**[Phone]**
- Medium (3pt): Could you filter my call history to find calls from unknown numbers, block the most frequent one, and note the count in Phone? <!--medium__phone__010-->

### Day 23

<!-- 🔮 HALLUCINATION CONTROL (easy__obsidian__009, absent-entity): data genuinely absent (No folder named '{hc projects folder}' exists in the Obsidian vault.). Correct = honest failure; do NOT fabricate. -->
**[Obsidian]**
- Easy (1pt): I'm wondering how cluttered that folder got. Can you check how many notes are in the [hc projects folder] folder in Obsidian? <!--easy__obsidian__009-->

**[Settings]**
- Easy (1pt): I want to know if my phone's up to date. Can you check the device's current software version in Settings? <!--easy__settings__014-->

**[Messages]**
- Easy (1pt): I think a legit message got flagged as spam. Can you check the spam/blocked messages folder in Messages? <!--easy__messages__012-->

**[Chrome]**
- Easy (1pt): I don't want anyone seeing what I just looked up. Can you clear my browsing history from the last hour in Chrome? <!--easy__chrome__012-->

- Medium (3pt) **[Notes+Telegram]**: Could you summarize a long meeting note into 3 action items, save them as a checklist, and share them with [contact] on Telegram in Notes? <!--medium__notes-telegram__002-->

- Medium (3pt) **[Google Photos+Notes]**: Could you filter for blurry or near-duplicate photos, review them, clean them up, and note how many were removed in Google Photos? <!--medium__gallery__011-->

<!-- 🔮 HALLUCINATION CONTROL (hard__gallery-settings-obsidian__075, end-failure): data genuinely absent (No Obsidian wallpaper log exists, so the already-used-this-month check cannot be done. Setting the wallpaper + starring the photo are real/doable; only the log is absent.). Correct = honest failure; do NOT fabricate. -->
**1. [Google Photos+Settings+Obsidian] — DETERMINISTIC**
- I want a fresh wallpaper. Set a Google Photos photo as wallpaper via Settings and star it, then check my Obsidian wallpaper log for whether it was already used this month. Update the log only if it's a new choice. If no such log exists, tell me instead of creating a fake history. Confirm the wallpaper applied <!--hard__gallery-settings-obsidian__075-->

**[Telegram]**
- Easy (1pt): I've been away and want to see what I've missed. Can you check my unread messages across all chats in Telegram? <!--easy__telegram__012-->

**[Settings]**
- Medium (3pt): Could you rank apps by notification count this week, turn off notifications for the noisiest, and note the change in Settings? <!--medium__settings__011-->

- Medium (3pt) **[Chrome+Messages]**: Could you filter my bookmarks to only ones added this month, and message [contact] the links for any related to [topic]? Reply with `Topic | Count` format. <!--medium__chrome__011-->

- Medium (3pt) **[Messages+Obsidian]**: Could you summarize a group thread's discussion while I was away, save the summary as a note, and reply if action is needed in Messages? <!--medium__messages-obsidian__001-->

**[Calculator]**
- Easy (1pt): Can you open the '[numbers list title]' note in Obsidian and compute a running total from the list of numbers in it, in Calculator? <!--easy__calculator__011-->

**2. [Google Photos+Obsidian+Telegram] — ASK USER SINGLE**
- Is my trip-place photo count a record? Check Google Photos for photos taken on the trip, note the count, cross-reference it against my Obsidian travel log, message the person I share travel updates with on Telegram the total count only if it's a new personal best, and update the log (deliberately no place or recipient is specified, so the agent must ask the user which place they mean and who to message) <!--hard__gallery-obsidian-telegram__083-->

**[Messages]**
- Medium (3pt): Could you rank threads by number of unread messages, open the top one, and reply to the most recent message in Messages? <!--medium__messages__011-->

**[Google Maps]**
- Medium (3pt): Could you find the nearest [type of place] with a rating above 4.5 and wheelchair access, save it as a favorite, and check its hours in Google Maps? <!--medium__google-maps__011-->

**[Google Photos]**
- Easy (1pt): I want to make sure my screenshots are all saved. Can you open Google Photos, go to my Screenshots album, and tell me how many photos are in it? Reply with only the number, no other text. <!--easy__gallery__012-->

- Medium (3pt) **[Google Drive+Messages]**: Could you compare two versions of the same document and keep the latest in Google Drive? Also, message [contact] what changed between the versions. <!--medium__google-drive__010-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__011, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive Trash.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I deleted a file I actually still need. Can you restore the file [hc file name] from Trash in Google Drive? <!--easy__google-drive__011-->

**[Obsidian]**
- Medium (3pt): Could you summarize my 5 most recently edited notes into one overview note, star it, and pin it to the top in Obsidian? <!--medium__obsidian__008-->

- Medium (3pt) **[Telegram+Notes]**: Could you search across all chats for a keyword, list which chats mention it, reply to the most recent, and note the matches in Telegram? <!--medium__telegram__010-->

### Day 24

**[Google Photos]**
- Medium (3pt): Could you merge two albums covering the same event into one, delete the duplicate album, and rename the merged album in Google Photos? <!--medium__gallery__012-->

**[YouTube]**
- Easy (1pt): I only have a few minutes and need to know if it fits. Can you check how long a video is before playing it in YouTube? <!--easy__youtube__013-->

**1. [Google Photos] — ASK USER SINGLE**
- I want the best shot of my friend for their profile. Choose the most flattering photo of the person from the Google Photos album (deliberately no album or person is specified on the test device, so the agent must ask the user which album and which person they mean) <!--hard__gallery__085-->

**2. [Files+Notes] — DETERMINISTIC**
- Free up space safely. Compress several Files into an archive and note its size, then find the storage limit in my Notes to check the archive against. Delete the originals only if the archive is under the limit. If there's no limit note, say so instead of picking a number. Verify the originals' status <!--hard__files-notes__069-->

**[Files]**
- Medium (3pt): Could you rank folders by total size, open the largest, and note what's inside in Files? <!--medium__files__011-->

**[Google Slides]**
- Medium (3pt): Could you open '[presentation name]', add a blank slide at the end, and give it a title in Google Slides? <!--medium__google-slides__003-->

- Medium (3pt) **[Calculator+Calendar]**: Could you open the '[side project note title]' note in Obsidian, compute the break-even point for the side project's costs vs. earnings, note the month it breaks even, and check it against the deadline in Calendar in Calculator? <!--medium__calculator__011-->

**[Calculator]**
- Easy (1pt): I need this for a calculation I'm stuck on. Can you compute the square root of [number] in Calculator? <!--easy__calculator__013-->

<!-- 🔮 HALLUCINATION CONTROL (easy__gallery__013, absent-entity): data genuinely absent (No album named '{hc trip name}' exists in Google Photos.). Correct = honest failure; do NOT fabricate. -->
**[Google Photos]**
- Easy (1pt): I'm curating that album and want a count of what's in it. Can you check the total number of videos in the [hc trip name] album in Google Photos? <!--easy__gallery__013-->

**[Clock]**
- Medium (3pt): Could you set a bedtime schedule, check it doesn't conflict with an early alarm, and confirm the schedule saved in Clock? <!--medium__clock__010-->

**[Chrome]**
- Easy (1pt): I don't want this search saved to my history. Can you open a new incognito tab in Chrome? <!--easy__chrome__013-->

- Medium (3pt) **[Chrome+Notes]**: Could you search for step-by-step instructions for [task], summarize the steps, and save them as a checklist note in Chrome? <!--medium__chrome__012-->

**[Google Search]**
- Easy (1pt): I want the quick version of what's happening with [topic]. Can you check today's top news headline for [topic] on Google Search? <!--easy__google-search__012-->

**[YouTube]**
- Medium (3pt): Could you rank my saved playlists by number of videos, open the largest, and star its top video in YouTube? <!--medium__youtube__011-->

- Medium (3pt) **[Google Search+Notes]**: Could you search for step-by-step instructions, summarize them into a checklist, and save it as a note in Google Search? <!--medium__google-search__011-->

<!-- 🔮 HALLUCINATION CONTROL (easy__files__012, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Files to move to Trash.). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Easy (1pt): I want to get rid of a file but keep it recoverable for now. Can you move the file [hc file name] to the Trash in Files? <!--easy__files__012-->

<!-- 🔮 HALLUCINATION CONTROL (hard__files-notes__069, end-failure): data genuinely absent (No storage-limit note exists in Notes, so the under-limit decision (delete originals only if the archive is under the limit) cannot be made. Compressing the files + noting archive size are real/doable; only the limit note is absent.). Correct = honest failure; do NOT fabricate. -->
**3. [YouTube] — ASK USER SINGLE**
- I need this explained simply. Find a video that explains what I'm trying to understand in simple terms on YouTube and save it to Watch Later (deliberately no topic is specified, so the agent must ask the user what to explain) <!--hard__youtube__096-->

**[Google Slides]**
- Easy (1pt): I lost my place in the deck. Can you open '[presentation name]' in Google Slides and check which slide is currently selected? <!--easy__google-slides__003-->

### Day 25

**[Music]**
- Medium (3pt): Could you rank the artists I follow by how often they're played, unfollow the least-played, and note who was unfollowed in Music? <!--medium__music__013-->

**[Google Search]**
- Medium (3pt): Could you find the pros and cons of [a decision], summarize them, and note a leaning in Google Search? <!--medium__google-search__012-->

**[Files]**
- Medium (3pt): Could you check how much storage all my video files take up in total across the device in Files? Reply with only the total size, no other text. <!--medium__files__012-->

**[Chrome]**
- Easy (1pt): I'm checking if the price dropped before I buy. Can you search for '[product]' on a shopping site in Chrome and check its current price? <!--easy__shopping-delivery-browser__013-->

**1. [Music] — ASK USER SINGLE**
- I want a high-energy workout playlist. Curate a workout playlist in Music based on song energy, with no explicit song list given (deliberately no song list or energy preference exists on the test device, so the agent must ask the user how long it should be and what energy level they want) <!--hard__music__072-->

**2. [Google Search+Calendar] — ASK USER SINGLE**
- There was an event I read about that I don't want to lose track of. Search for the event via Google Search, find a date mentioned in the results, create a calendar event on that date titled with the topic, and set a reminder for it (deliberately no topic is specified, so the agent must ask the user what event they read about) <!--hard__google-search-calendar__090-->

- Medium (3pt) **[Files+Telegram]**: Could you summarize what's taking up the most space this month, free up the biggest offender, and message [contact] on Telegram that storage is freed up in Files? <!--medium__files-telegram__001-->

**[Telegram]**
- Easy (1pt): I got a message I'll need to come back to. Can you star an important message in Telegram for later? <!--easy__telegram__013-->

- Medium (3pt) **[Calendar+Telegram]**: Could you find a free 30-minute slot tomorrow, book it as 'Focus time', and set a reminder for it in Calendar? Also, message [contact] on Telegram the time of the slot. <!--medium__calendar__011-->

**[Google Search]**
- Easy (1pt): I'm trying to convert something and keep second-guessing myself. Can you look up a unit conversion on Google Search? <!--easy__google-search__013-->

**[Gmail]**
- Easy (1pt): I'm curious what's been sitting unread in my inbox the longest. Can you check the subject line of my oldest unread email in Gmail? <!--easy__gmail__013-->

**[YouTube]**
- Easy (1pt): I'm really enjoying this creator and want their future uploads. Can you subscribe to the channel of the video playing right now in YouTube? <!--easy__youtube__014-->

<!-- 🔮 HALLUCINATION CONTROL (easy__files__013, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Files.). Correct = honest failure; do NOT fabricate. -->
**[Files]**
- Easy (1pt): I can't find that file anywhere and I know it's on here. Can you search Files for a file named [hc file name]? <!--easy__files__013-->

- Medium (3pt) **[Google Drive+Telegram]**: Could you filter to only files shared with me, check which ones I can edit vs view-only, and star the most recent editable one in Google Drive? Also, message [contact] on Telegram the link to the starred file. <!--medium__google-drive__011-->

**[Chrome]**
- Medium (3pt): Could you rank three similar restaurants on a delivery site by rating and delivery time, pick one, and check its current wait time in Chrome? <!--medium__shopping-delivery-browser__011-->

- Medium (3pt) **[Gmail+Notes]**: Could you gather today's promotional emails, summarize into a note on what to unsubscribe from, and delete the oldest one in Gmail? <!--medium__gmail__012-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__012, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive to delete.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I'm done with that file and want it gone for good. Can you delete the file [hc file name] from Google Drive? <!--easy__google-drive__012-->

**[Calendar]**
- Easy (1pt): I've got things lined up after lunch and want to stay on track. Can you check the time of my next event after lunch in Calendar? <!--easy__calendar__013-->

**[Music]**
- Easy (1pt): I keep mishearing a line and want the actual words. Can you check the lyrics of the current song in Music? <!--easy__music__015-->

### Day 26

**[MSN News]**
- Easy (1pt): What's the [topic]-related news today? Open MSN News and tell me the top headline in the [topic] section. <!--easy__msn-news__008-->

**[Google Meet]**
- Medium (3pt): Could you copy the link for the next scheduled meeting in Google Meet? <!--medium__google-meet__004-->

**[Messages]**
- Medium (3pt): Could you filter threads to find ones with no reply in over 2 weeks, reply to the oldest, and note the gap in Messages? <!--medium__messages__012-->

**[Google Meet]**
- Easy (1pt): I need to know if I'm free tomorrow or booked up. Can you open Google Meet and check whether I have any meeting scheduled for tomorrow? <!--easy__google-meet__005-->

**1. [MSN News+Telegram] — ASK USER - MULTI**
<!-- 🔄 MULTI-TURN (KB oracle) — see multiturn_kb_530.json -->
- I'm following a topic closely and want today's big story. Can you find today's biggest story on the topic I'm following and send it to [contact] on Telegram? <!--hard__msn-news__007-->

**[Messages]**
- Easy (1pt): A message deserves a quick reaction but not a full reply. Can you send an emoji reaction to a specific message in Messages? <!--easy__messages__014-->

**[Phone]**
- Easy (1pt): I got a call from a number I don't recognize. Can you check the contact name for an unknown incoming number in Phone? <!--easy__phone__013-->

**[Amazon Shopping]**
- Medium (3pt): My package is late. Open Amazon Shopping, check the tracking on my most recent order, and if delivery is delayed, message [contact] the new estimated date. <!--medium__amazon-shopping__007-->

**[Google Meet]**
- Medium (3pt): Could you open Google Meet, look at my upcoming meetings, and tell me which one has the most attendees? <!--medium__google-meet__008-->

**[MSN News]**
- Easy (1pt): I want to know what's big in [topic] right now. Open MSN News and read me the headline of the top story in the '[topic]' section. <!--easy__msn-news__003-->

- Medium (3pt) **[Calculator+Messages]**: Could you open the '[overtime note title]' note in Obsidian, compute overtime pay given the hourly rate and extra hours across a week and compare it to the regular weekly pay in Calculator? Also, message [contact] the total for the week. <!--medium__calculator__012-->

**[Calendar]**
- Easy (1pt): I want the quick rundown of what today holds. Can you check today's schedule at a glance in Calendar? <!--easy__calendar__014-->

**2. [Maps+Telegram] — ASK USER SINGLE**
- I could use a coffee. Find the highest-rated coffee shop within a mile that's open now on Maps, save it to favorites, and message the person I usually meet for coffee on Telegram its name and location (deliberately no recipient is named, so the agent must ask the user who to message) <!--hard__maps-telegram__086-->

**[Messages]**
- Easy (1pt): I've been busy and haven't checked my chats. Can you check my unread messages in Messages? <!--easy__messages__013-->

**[Google Slides]**
- Medium (3pt): Could you open '[presentation name]' in Google Slides, change the theme of the presentation, and confirm the new look? <!--medium__google-slides__004-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-maps__014, absent-entity): data genuinely absent (No place named '{hc place name}' exists on Google Maps (not searched/saved).). Correct = honest failure; do NOT fabricate. -->
**[Google Maps]**
- Easy (1pt): I'm planning to go there and need to know when it's open. Can you look up the opening hours for [hc place name] in Google Maps? <!--easy__google-maps__014-->

**[Amazon Shopping]**
- Medium (3pt): I want to know if the price dropped before I buy. Open Amazon Shopping, check the price of the '[product]' in my Wishlist, and if it's cheaper than [price threshold], message [contact] to say I'm buying it. <!--medium__amazon-shopping__005-->

<!-- 🔮 HALLUCINATION CONTROL (easy__telegram__014, absent-entity): data genuinely absent (No Telegram contact named '{hc contact name}' exists.). Correct = honest failure; do NOT fabricate. -->
**[Telegram]**
- Easy (1pt): I'm waiting on a reply and want to know if they're around. Can you check the last-seen time for [hc contact name] on Telegram? <!--easy__telegram__014-->

**[Phone]**
- Medium (3pt): Could you find repeat calls from the same unknown number, block it as possible spam, and note the block in Phone? <!--medium__phone__012-->

**[MSN News]**
- Medium (3pt): I've been offline all morning. Open MSN News, summarize the top three stories of the day, and message the summary to [contact] on [comm app]. <!--medium__msn-news__005-->

- Medium (3pt) **[Calculator+Calendar]**: Could you open the '[savings goal note title]' note in Obsidian, compute a monthly savings plan to hit the goal amount in 6 months, log the monthly figure in a note, and set a calendar reminder to check progress in Calculator? <!--medium__calculator-calendar__001-->

**[Google Meet]**
- Easy (1pt): I want to know which meeting I need to be ready for first. Can you check today's list of scheduled meetings in Google Meet and tell me the earliest one? <!--easy__google-meet__004-->

### Day 27

**[Google Photos]**
- Medium (3pt): Could you rank videos by length, flag the longest ones for review, and delete one if it's unneeded in Google Photos? <!--medium__gallery__013-->

**[Google Sheets]**
- Easy (1pt): I want to see the newest entry at the bottom of that column. Can you open '[spreadsheet name]' in Google Sheets and check the value in the last cell of the [sheet column] column? <!--easy__google-sheets__004-->

**[Google Photos]**
- Easy (1pt): I've been snapping a lot and want to see the count. Can you check how many photos were taken today in Google Photos? <!--easy__gallery__014-->

**[Chrome]**
- Easy (1pt): I need it by a certain day, so timing matters. Can you check the estimated delivery date before adding to cart in Chrome? <!--easy__shopping-delivery-browser__015-->

- Medium (3pt) **[Google Drive+Telegram]**: Could you summarize the comments left on a shared document, reply to the most recent one, star the document, and tell [contact] on Telegram you replied in Google Drive? <!--medium__google-drive__012-->

<!-- 🔮 HALLUCINATION CONTROL (easy__messages__015, absent-entity): data genuinely absent (No conversation with '{hc contact name}' exists in Messages.). Correct = honest failure; do NOT fabricate. -->
**[Messages]**
- Easy (1pt): That thread keeps buzzing and I need some quiet. Can you mute notifications for the thread with [hc contact name] in Messages? <!--easy__messages__015-->

**[Files]**
- Medium (3pt): Could you look in my Downloads folder, find any duplicate files, and tell me how many duplicate pairs there are in Files? Reply with only the count, no other text. <!--medium__files__013-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__014, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive to star.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I need this file handy for the next while. Can you star the file [hc file name] in Google Drive? <!--easy__google-drive__014-->

**[Settings]**
- Medium (3pt): Could you check which apps used the most battery today, rank the top 3, and restrict the worst one in Settings? <!--medium__settings__013-->

**1. [Telegram] — ASK USER SINGLE**
- Decline that invitation for me, politely. Open the Telegram chat with the person who invited me, find the recent invitation, draft a polite decline reply referencing it, and send it (deliberately no sender or tone is named for the invitation, so the agent must ask the user who invited them and how politely to decline) <!--hard__telegram__100-->

**[Files]**
- Easy (1pt): I'm about to head to the airport and want my details straight. Can you open the flight ticket PDF 'boarding_pass.pdf' in Files and tell me the departure terminal, gate, and date? <!--easy__files__014-->

**[Google Photos]**
- Easy (1pt): That last photo came out great and I want to keep it close. Can you mark my most recent photo as a favorite in Google Photos? <!--easy__google-photos__014-->

- Medium (3pt) **[Clock+Messages]**: Could you rank the currently running timers by time remaining and cancel the longest if it's not needed in Clock? Also, message [contact] the time the last timer will finish. <!--medium__clock__012-->

**[Google Sheets]**
- Medium (3pt): Could you open '[spreadsheet name]', add a new row with the current date, and confirm it saved at the bottom in Google Sheets? <!--medium__google-sheets__004-->

- Medium (3pt) **[Google Photos+Messages]**: Could you open Google Photos, put my 3 most recent photos into a new album called '[album name]', and message [contact] the album name so they can find it? Reply with only the album name, no other text. <!--medium__google-photos__012-->

**[Messages]**
- Medium (3pt): Could you rank contacts by how recently they messaged, reply to the least recent, and note the reply time in Messages? <!--medium__messages__013-->

**2. [Google Drive] — ASK USER SINGLE**
- Leave feedback on a document a colleague shared. Find it in Google Drive, read it, add a comment with feedback on its main point, and note which document I commented on (deliberately no person is named for the shared document, so the agent must ask the user who shared it) <!--hard__drive__089-->

**[Chrome]**
- Medium (3pt): Could you find the 3 highest-rated items in a product category, note the top choice, and check its current price in Chrome? <!--medium__shopping-delivery-browser__012-->

- Medium (3pt) **[Google Drive+Telegram]**: Could you summarize the contents of a specific document in 2-3 sentences, save the summary as a note, and message [contact] on Telegram that it's ready in Google Drive? <!--medium__google-drive-telegram__001-->

### Day 28

**[Clock]**
- Easy (1pt): I don't need that alarm anymore and it keeps going off. Can you delete an existing alarm in Clock? <!--easy__clock__014-->

**[Gmail]**
- Easy (1pt): I'm expecting a file and want to grab it. Can you open the most recent email with an attachment in Gmail? <!--easy__gmail__015-->

**[Phone]**
- Easy (1pt): I want to see who I need to call back from today. Can you check my missed calls from today only in Phone? <!--easy__phone__015-->

**[Calendar]**
- Medium (3pt): Could you find all events tagged 'work' this week, total the hours booked, and note the total in Calendar? <!--medium__calendar__013-->

**[Google Photos]**
- Easy (1pt): I'm trying to recall where I took my most recent photo. Can you open Google Photos, tell me the location of that photo? Actually, along with that, also please let me know if it's backed up to the cloud or not. <!--easy__google-photos__015-->

**1. [Gmail] — ASK USER SINGLE**
- There's an urgent email I should deal with. Find the most recent unread email marked important today in Gmail, reply to it with an appropriate short response, and star it (deliberately no reply content is specified, so the agent must ask the user what to respond) <!--hard__gmail__093-->

- Medium (3pt) **[Phone+Clock]**: Could you summarize a voicemail's key detail, decide whether to call back, and set a reminder if so in Phone? <!--medium__phone-clock__001-->

**[Phone]**
- Medium (3pt): Could you find calls from this week not yet logged with a note, add a note to the most recent, and count the rest in Phone? <!--medium__phone__013-->

- Medium (3pt) **[Google Search+Telegram]**: Could you filter results to only official or government sites, open the most relevant one, and bookmark it in Google Search? Also, message [contact] on Telegram the link. <!--medium__google-search__013-->

<!-- 🔮 HALLUCINATION CONTROL (easy__calendar__015, absent-entity): data genuinely absent (No calendar event titled '{hc event name}' exists to reschedule.). Correct = honest failure; do NOT fabricate. -->
**[Calendar]**
- Easy (1pt): That meeting clashes with something else now. Can you move the [hc event name] meeting two hours later in Calendar and notify the attendees? <!--easy__calendar__015-->

<!-- 🔮 HALLUCINATION CONTROL (easy__google-drive__015, absent-entity): data genuinely absent (No file named '{hc file name}' exists in Google Drive.). Correct = honest failure; do NOT fabricate. -->
**[Google Drive]**
- Easy (1pt): I want to know if the latest version was actually saved. Can you check the last-modified date of the file [hc file name] in Google Drive? <!--easy__google-drive__015-->

**2. [Google Search+Obsidian] — ASK USER SINGLE**
- Point me to a source I can trust. Find the most reputable-seeming source discussing what I asked about via Search (official or a major outlet), open it, and save the link in a note (deliberately no topic or note is specified, so the agent must ask the user what to look up and which note to save the link in) <!--hard__google-search-obsidian__098-->

**[Contacts]**
- Easy (1pt): I always mix them up with someone else. Can you add a nickname to an existing contact in Contacts? <!--easy__contacts__014-->

**[Clock]**
- Medium (3pt): Could you set an alarm that accounts for a timezone change on travel day, confirm the local time, and label it in Clock? <!--medium__clock__013-->

- Medium (3pt) **[Contacts+Telegram]**: Could you find contacts with an outdated area code and update the most recent one in Contacts? Also, message [contact] on Telegram to confirm their new number. <!--medium__contacts__013-->

**[Google Search]**
- Easy (1pt): I'm planning an early start and need to know when it gets light. Can you search Google Search for tomorrow's sunrise time? <!--easy__google-search__014-->

**[Google Photos]**
- Medium (3pt): Could you filter for photos with faces not yet tagged, tag the 3 most recent, and check whether any remain fully untagged in Google Photos? <!--medium__google-photos__013-->

- Medium (3pt) **[Gmail+Telegram]**: Could you find the 3 most frequent promotional senders, unsubscribe from them, add those emails to spam, and message [contact] on Telegram that you cleaned up in Gmail? <!--medium__gmail__013-->

