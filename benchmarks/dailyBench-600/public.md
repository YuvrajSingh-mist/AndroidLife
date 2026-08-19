# DrainBench — Public Sample (3-Day Preview)

### Not the eval set. A structural preview only — a TRUE sample drawn from the
530-task corpus (same task_ids, exact prompt text, placeholder slots) plus a few public-sample-specific additions. **61 tasks total.**

**Grading model**: no separate rubric/LLM-judge "open-ended" bucket — a task either has everything
it needs (**DETERMINISTIC**, ADB-verified end state) or needs the agent to ask the user for a fact
(**ASK USER SINGLE** — one deliberately omitted fact, answered just-what's-asked) or to run a
multi-turn dialogue (**ASK USER - MULTI** — a knowledge-base profile in `multiturn_kb_public.json`
holds what the simulated user knows, with rolling memory; graded on acting on the correct target,
turn count as an efficiency signal).

Easy: 1 app, Medium: 1-2 apps; Hard battery: 2-3 apps, genuine reasoning, natural first-person
requests, **distributed across the days and mixed so ask-user, deterministic and multi-turn tasks
aren't grouped or predictable by position.**

---

### Day 1

**2. [Drive+Notes+Telegram] — ASK USER SINGLE**
- I'm worried our shared budget spreadsheet is slipping. Open the shared budget spreadsheet in Drive, check when it was last edited, and compare that against the committed finalisation deadline noted in my 'Budget Deadline' note. If it hasn't been updated by the deadline (it's overdue), message the person who owns the budget on Telegram to chase it; otherwise just log today's check date in the note. Confirm what you did either way <!--hard__drive-notes-telegram__010-->

- Medium (3pt) **[Google Maps + Notes]**: I need to get to [place] and can't decide how to travel. Can you open Google Maps and just compare the driving ETA? Wait no, hold on. Compare the ETA by driving, transit, and walking, all three modes, not just driving. Then pick whichever is fastest. Hmm, and I almost forgot, save the ETA and distance for that fastest option as a note in Notes with a sensible title. Thanks! <!--medium__google-maps__002-->

**[Google Photos]**
- Easy (1pt): I want to make sure my screenshots are all saved. Can you open Google Photos, go to my Screenshots album, and tell me how many photos are in it? Reply with only the number, no other text. <!--easy__gallery__012-->

- Medium (3pt) **[Contacts + Phone]**: Could you find all contacts missing a phone number, list them, and delete the ones with no other info in Contacts? Also, call [contact] to confirm their number. <!--medium__contacts__009-->

**[Google Drive]**
- Medium (3pt): Could you check my Google Drive for files that were shared with me, list the ones I can edit, and tell me how many there are? Reply with only the count, no other text. <!--medium__google-drive__007-->

**6. [YouTube+Settings] — DETERMINISTIC**
- Notifications from [notifying channel] keep pinging me at night and waking me up. Can you open YouTube, turn off its notifications so I stop getting alerts from that channel? Also, set Do Not Disturb so all notifications are silenced between 10 PM and 8 AM. Reply with only the channel name you muted for confirmation, no other text. <!--hard__youtube-settings__052-->

**5. [Telegram+Calendar] — ASK USER - MULTI**
- I think someone dropped a date in one of my Telegram chats for something coming up, and I don't want to forget it. Can you make sure it's on my calendar with a reminder? <!--hard__telegram-calendar__016-->

**[Chrome]**
- Easy (1pt): I'm about to order food but worried about surcharges — open the [food delivery site] in Chrome and check if there's any weather-related surcharge notice <!--easy__shopping-delivery-browser__001-->

**[Camera]**
- Easy (1pt): I'm about to record something and want to be ready. Can you open Camera and switch to video mode? <!--easy__camera__006-->

**[Phone]**
- Easy (1pt): Can you open the Phone app and call [contact] for me pls? <!--easy__phone__002-->

**[Google Slides]**
- Easy (1pt): I've lost track of how long this deck is. Can you open the '[presentation name]' presentation in Google Slides and tell me how many slides it has? Reply with only the number of slides, no other text. <!--easy__google-slides__001-->

**[Calendar]**
- Easy (1pt): I've got a packed day tomorrow and want to make sure nothing overlaps. Could you check my Calendar for any scheduling conflicts tomorrow afternoon? <!--easy__calendar__002-->

- Medium (3pt) **[Google Photos + Obsidian]**: I'm putting together a food favourites note in Obsidian. I've created a 'Food Favourites' note with headings for Pancakes, Pizza, and Veggie Bowl. Could you open Google Photos Favourites, find the appropriate photo for each heading by looking at each photo's description, and copy each one into the note under the matching heading, one by one? Reply with only the number of photos added, no other text. <!--medium__gallery__007-->

**[Files]**
- Medium (3pt): Could you find duplicate files in my Downloads folder, delete the extra copies, and count how many you removed in Files? Reply with only the count, no other text. <!--medium__files__013-->

- Medium (3pt) **[Files + PDF]**: I need to know if I still owe on that hosting plan. Open the file 'Invoice INV-2026-071.pdf' in Files, read out the amount due, and check whether the due date has already passed. Reply with only the amount, no other text. <!--medium__files-pdf__001-->

- Medium (3pt) **[Files + PDF]**: I'm sorting out my rent. Open the file 'Rent Receipt.pdf' in Files, read the rent amount, and tell me whether the receipt shows it as paid in full. <!--medium__files-pdf__002-->

- Medium (3pt) **[Google Maps + Telegram]**: Could you filter EV charging stations near the route by connector type and check the nearest one's availability in Google Maps? Also, message [contact] on Telegram the address of the nearest station. <!--medium__google-maps__003-->

**[Google Drive]**
- Medium (3pt): I'm running out of space in my Drive and can't figure out where it all went. Check my current storage usage in Drive's settings, then open the details of the files in the main Drive folder, find the largest file, and note its name, type, size, and last modified date. <!--medium__google-drive__001-->

**4. [Swiggy+Telegram] — ASK USER - MULTI**
- Ugh, I'm craving the food I ate in the past week — can you get me that again? Also, message him on Telegram the order total so I can confirm before paying. <!--hard__swiggy__005-->

**3. [Google Sheets+Amazon Shopping] — DETERMINISTIC**
- I've got all my video stats in the [spreadsheet name] spreadsheet and I want to treat myself. Can you open it in Google Sheets, find the video with the most views, and read out its name and view count? Then open Amazon Shopping, search for '[related product]', and open the top result to check its price. Reply with only the video name and the product name, no other text. <!--hard__google-sheets-amazon-shopping__074-->

**1. [Contacts+Gmail] — DETERMINISTIC**
- I want to clean up my contacts. Find all Contacts missing a phone number, list them, check each against Gmail for a saved email, delete only the ones with neither, and star one of the remaining contacts as a reminder to verify it later <!--hard__contacts-gmail__026-->

**[Calculator]**
- Easy (1pt): A recipe uses a temperature I'm not used to. Convert [temperature] between Celsius and Fahrenheit in Calculator? <!--easy__calculator__006-->


### Day 2

**2. [Chrome+Telegram+Notes] — ASK USER SINGLE**
- I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing <!--hard__chrome-telegram-notes__008-->

**6. [Google Photos+Gmail+Obsidian] — ASK USER SINGLE**
- I'd like to send [contact] a photo from the event. Find the event photo in Google Photos, for which the caption has the [contact] mentioned, and email it to them if so, recording the send in a note in Obsidian; otherwise save it to a general album. Star it either way <!--hard__photos-gmail-obsidian__012-->

- Medium (3pt) **[Chrome + Messages]**: Can you send my buddy, [contact], links to the shopping websites about some earbuds I was looking at today from my Chrome history please? He's bene looking for cheap earbuds recently. <!--medium__chrome__003-->

- Medium (3pt) **[Calculator + Messages]**: Could you open the '[budget note title]' note in Obsidian, add up the 5 expense categories into a monthly budget, and compare it to my income in Calculator? Reply with only the final total, no other text, then message [contact] that I'll be late for dinner tonight. <!--medium__calculator__002-->

**[Files]**
- Medium (3pt): Could you find all my screenshots across folders, delete the oldest 10, and check the folder's new total size in Files? <!--medium__files__009-->

- Medium (3pt) **[Files]**: I'm trying to free up space on my phone. Can you check what's in my Downloads, sort them by size, and tell me the biggest file's name and size? Oh, and don't delete anything — I just want to know. <!--medium__files__015-->

**1. [BookMyShow+Telegram] — DETERMINISTIC**
- We're doing a movie night this weekend — me and 3 friends. Can you open BookMyShow, check what's showing at [cinema] this weekend, pick the earliest showtime that fits our group of 4, and note the movie, showtime, and per-ticket price ([ticket price])? Then message [contact] on Telegram with the plan so they can book — but don't book anything yourself. Reply with only the cinema name, movie, and showtime, no other text. <!--hard__bookmyshow__005-->

**[Settings]**
- Easy (1pt): I want to know if my phone's up to date. Can you check the device's current software version in Settings? Reply with only yes or no, no other text. <!--easy__settings__014-->

**[Phone]**
- Easy (1pt): I want to see how much I've been on the phone today. Can you tell me how many calls I've made today in Phone? Reply with only the total call time, no other text. <!--easy__phone__005-->

**[Amazon Shopping]**
- Easy (1pt): I thought I added something earlier and want to confirm. Can you open Amazon Shopping and check whether '[product]' is currently in my cart? <!--easy__amazon-shopping__002-->

**[Prime Video]**
- Medium (3pt): I want to pick up where I left off. Open Prime Video, find what's in my "Continue Watching", and give me a quick summary of the most recent one. <!--medium__prime-video__003-->

**3. [Gmail+Calendar] — ASK USER - MULTI**
- I'm flying out soon and don't wanna miss it. Find my flight confirmation email for the next trip and add it to the Calendar as a reminder 3 hours before departure so I get a heads-up? <!--hard__gmail-calendar__003-->

**[Google Maps]**
- Easy (1pt): I just parked and I'm worried I'll forget where. Could you save my current location in Google Maps as 'parked here'? <!--easy__google-maps__004-->

**4. [Google Search+Telegram+Clock] — ASK USER SINGLE**
- I'm going to grab something from the place I'm going to. Look up its hours via Google Search, note whether it's open now, and if it is, message the person I'm going with on Telegram suggesting we go now; otherwise message the reopening time and set an alarm for it <!--hard__google-search-telegram-clock__018-->

**[Swiggy]**
- Easy (1pt): I'm starving and my food's been a while. Can you open Swiggy and check the delivery status of my most recent order? Reply with only the delivery status, no other text. <!--easy__swiggy__001-->

- Medium (3pt) **[Clock + Calendar]**: Could you set a recurring alarm, confirm it doesn't clash with an existing Calendar event, and label it accordingly in Clock? <!--medium__clock__009-->

- Medium (3pt) **[Clock]**: Could you set a timer for me? Make it 25 minutes, label it 'Workout', and start it once it's set. Thanks! <!--medium__clock__011-->

**[Google Meet]**
- Easy (1pt): I want to know which meeting I need to be ready for first. Can you check today's list of scheduled meetings in Google Meet and tell me the earliest one? <!--easy__google-meet__004-->

- Medium (3pt) **[Google Photos + Messages]**: Could you open Google Photos, put my 3 most recent photos into a new album called '[album name]', and message [contact] the album name so they can find it? Reply with only the album name, no other text. <!--medium__google-photos__012-->

**[YouTube]**
- Easy (1pt): I want to see what people are saying about this video. Can you check the comments on the current video in YouTube? <!--easy__youtube__011-->

- Medium (3pt) **[Chrome + Messages]**: Could you filter my bookmarks to only ones added this month, delete any duplicates, and count what's left in Chrome? Also, message [contact] the count. <!--medium__chrome__011-->

**5. [Music+Obsidian] — ASK USER - MULTI**
- I listen to music to fall asleep and want it to stop by itself around my bedtime. Can you set that up for me in YouTube Music? <!--hard__music-obsidian__077-->


### Day 3

- Medium (3pt) **[Google Photos + Phone]**: Could you filter the library to only videos over 1 minute long, delete the longest if it's unneeded, and count what's left in Google Photos? Also, call [contact] to confirm the plan for tonight. <!--medium__google-photos__008-->

**4. [Google Search+Obsidian+Telegram] — ASK USER SINGLE**
- I'm tracking [stock name] and only want to hear about it when it matters. Check its current value via Google Search against the threshold in my '[stock note title]' Obsidian note, note today's value, compare it to the last recorded value in that Obsidian note, message the person I follow this stock with on Telegram only if it has crossed the threshold since then, and update the Obsidian note with today's value <!--hard__google-search-obsidian-telegram__057-->

- Medium (3pt) **[Google Photos + Calendar]**: I want to see my photo habits this year. Can you summarize how many photos I took each month this year? Note down the busiest month for me, and set a calendar reminder to review that month's album in Google Photos sometime tomorrow noon?. Reply with only the number of photos, no other text. <!--medium__google-photos-calendar__001-->

**[BookMyShow]**
- Easy (1pt): I'm free tonight and want to catch a movie nearby. Open BookMyShow and tell me which movies are playing at the nearest cinema. <!--easy__bookmyshow__004-->

**[YouTube]**
- Easy (1pt): I paused mid-video and want to pick up where I stopped. Can you resume a recently watched video in YouTube from where it left off? <!--easy__youtube__009-->

- Medium (3pt) **[Google Search + Telegram]**: Could you compare public transit options for a specific route and tell me the fastest in Google Search? Also, message [contact] on Telegram the fastest route for tomorrow. Reply with only the fastest option, no other text. <!--medium__google-search__008-->

**1. [Chrome+YouTube+Notes] — ASK USER SINGLE**
- I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note <!--hard__chrome-youtube-notes__088-->

- Medium (3pt) **[Contacts + Phone]**: Could you merge duplicate contacts sharing the same phone number, confirm only one remains, and check its info is complete in Contacts? Also, call [contact] to confirm their address. <!--medium__contacts__012-->

- Medium (3pt) **[Calculator + Obsidian + Notes]**: I'm stressing about my grades. Can you open the '[exam scores note title]' note in Obsidian, read my exam scores and how much each one is weighted, then compute the weighted average in Calculator? Write the final grade in a note. Oh and check whether it meets the passing threshold of [passing threshold]. That's the real ask. Reply with only the final grade, no other text. <!--medium__calculator__001-->

**[Google Docs]**
- Easy (1pt): I've got a document I need a fresh copy of to edit — could you open Google Docs and rename one of my existing documents for me to an apt name based on the contents of the document? <!--easy__google-docs__004-->

**[MSN News]**
- Easy (1pt): I want to know what's big in [topic] right now. Can you open MSN News and read me the headline of the top story in the '[topic]' section? Reply with only the top story, no other text. <!--easy__msn-news__002-->

**2. [Clock+Calendar] — DETERMINISTIC**
- I need to start a new habit with a weekday alarm, but I've got some early meetings to dodge. Can you open Calendar and check whether I have any events at 7 AM on weekdays (I think there's a [weekly meeting] on Monday and [gym event] on Tuesday)? Then open Clock, create a repeating weekday alarm at 7:00 AM, and if any event clashes, shift it 30 minutes later so it doesn't overlap. Confirm the final alarm time. Reply with only the final alarm time, no other text. <!--hard__clock-calendar__023-->

**[Messages]**
- Easy (1pt): Words aren't enough for this reply. Can you send a GIF in a conversation in Messages? <!--easy__messages__010-->

**3. [Google Meet+Files] — DETERMINISTIC**
- Got my next meeting coming up and the agenda needs prepping. Can you open Google Meet, find my next scheduled meeting — I think it's the Monday [weekly meeting] at 10 AM — and note its title, time, and number of attendees? Then open Files, find the agenda document called '[agenda file]', and open it so it's ready. Reply with only the meeting title and the agenda file name, no other text. <!--hard__google-meet-files__070-->

**[Prime Video]**
- Easy (1pt): I've been saving shows and lost track of how many. Can you open Prime Video and tell me how many titles are in my Watchlist sorted by TV Shows? Reply with only the number, no other text. <!--easy__prime-video__002-->

**[Google Photos]**
- Easy (1pt): That screenshot was a mistake and I want it gone. Can you delete my most recent screenshot in Google Photos? <!--easy__google-photos__015-->

- Medium (3pt) **[Music + Telegram]**: Could you compare my listening stats between this week and last week, note the difference, and share the summary with [contact] on Telegram in Music? <!--medium__music-telegram__001-->
