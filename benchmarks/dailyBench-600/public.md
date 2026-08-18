# DrainBench — Public Sample (3-Day Preview)

### Not the eval set. A structural preview only — a TRUE sample drawn from the
530-task corpus (same task_ids, exact prompt text, placeholder slots). **57 tasks total.**

**Grading model**: no separate rubric/LLM-judge "open-ended" bucket — a task either has everything
it needs (deterministic, ADB-verified end state) or is missing one load-bearing fact the agent
must actively ask for (agent-user interaction, resolved by an LLM playing the user, holding only
the omitted fact, answering just what's asked). Multi-turn (KB) tasks are DETERMINISTIC with a
knowledge-base profile in `multiturn_kb_public.json`.

Easy: 1 app, Medium: 1-2 apps; Hard battery: 2-3 apps, genuine reasoning, natural first-person
requests, **distributed across the days and mixed so ask-user, deterministic and multi-turn tasks
aren't grouped or predictable by position.**

---

### Day 1

**2. [Drive+Notes+Telegram] — ASK USER**
- I'm worried our shared budget spreadsheet is slipping. Open the shared budget spreadsheet in Drive, check when it was last edited, and compare that against the committed finalisation deadline noted in my 'Budget Deadline' note. If it hasn't been updated by the deadline (it's overdue), message the person who owns the budget on Telegram to chase it; otherwise just log today's check date in the note. Confirm what you did either way <!--hard__drive-notes-telegram__010-->

- Medium (3pt) **[Google Maps + Notes]**: I need to get to [place] and can't decide how to travel. Can you open Google Maps and just compare the driving ETA? Wait no, hold on. Compare the ETA by driving, transit, and walking, all three modes, not just driving. Then pick whichever is fastest. Hmm, and I almost forgot, save the ETA and distance for that fastest option as a note in Notes with a sensible title. Thanks! <!--medium__google-maps__002-->

**[Google Photos]**
- Easy (1pt): I want them to show up with a proper picture. Can you set a specific photo as a contact's photo in Google Photos? <!--easy__gallery__012-->

- Medium (3pt) **[Contacts + Phone]**: Could you find all contacts missing a phone number, list them, and delete the ones with no other info in Contacts? Also, call [contact] to confirm their number. <!--medium__contacts__009-->

**[Google Drive]**
- Medium (3pt): Could you find all files over [file size threshold], list them by size, and delete the largest if it's unneeded in Google Drive? <!--medium__google-drive__007-->

**6. [YouTube+Settings] — DETERMINISTIC**
- Notifications from one of my channels keep coming at night and it's annoying. Can you fix that so they only show up during the day? <!--hard__youtube-settings__052-->

**5. [Telegram+Calendar] — DETERMINISTIC**
- Pretty sure someone dropped a date in one of the group chats. Can you check and set a reminder if there's one? <!--hard__telegram-calendar__016-->

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
- Medium (3pt): Could you rank recently downloaded files by size, delete the largest if it's unneeded, and note the result in Files? <!--medium__files__013-->

- Medium (3pt) **[Google Maps + Telegram]**: Could you filter EV charging stations near the route by connector type and check the nearest one's availability in Google Maps? Also, message [contact] on Telegram the address of the nearest station. <!--medium__google-maps__003-->

**[Google Drive]**
- Medium (3pt): I'm running out of space in my Drive and can't figure out where it all went. Check my current storage usage in Drive's settings, then open the details of the files in the main Drive folder, find the largest file, and note its name, type, size, and last modified date. <!--medium__google-drive__001-->

**4. [Swiggy] — DETERMINISTIC**
- Ugh, I'm craving what I ordered last Friday — can you get me that again? Just take me to the payment page, don't place the order. <!--hard__swiggy__005-->

**3. [Google Sheets+Amazon Shopping] — DETERMINISTIC**
- I've got all my video stats in a sheet. Can you find my best performer and show me something related to grab? <!--hard__google-sheets-amazon-shopping__074-->

**1. [Contacts+Gmail] — DETERMINISTIC**
- I want to clean up my contacts. Find all Contacts missing a phone number, list them, check each against Gmail for a saved email, delete only the ones with neither, and star one of the remaining contacts as a reminder to verify it later <!--hard__contacts-gmail__026-->

**[Calculator]**
- Easy (1pt): A recipe uses a temperature I'm not used to. Convert [temperature] between Celsius and Fahrenheit in Calculator? <!--easy__calculator__006-->


### Day 2

**2. [Chrome+Telegram+Notes] — ASK USER**
- I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing <!--hard__chrome-telegram-notes__008-->

**6. [Google Photos+Gmail+Obsidian] — ASK USER**
- I'd like to send [contact] a photo from the event. Find the event photo in Google Photos, for which the caption has the [contact] mentioned, and email it to them if so, recording the send in a note in Obsidian; otherwise save it to a general album. Star it either way <!--hard__photos-gmail-obsidian__012-->

- Medium (3pt) **[Chrome + Messages]**: Can you send my buddy, [contact], links to the shopping websites about some earbuds I was looking at today from my Chrome history please? He's bene looking for cheap earbuds recently. <!--medium__chrome__003-->

- Medium (3pt) **[Calculator + Messages]**: Could you open the '[budget note title]' note in Obsidian, add up the 5 expense categories into a monthly budget, and compare it to my income in Calculator? Reply with only the final total, no other text, then message [contact] that I'll be late for dinner tonight. <!--medium__calculator__002-->

**[Files]**
- Medium (3pt): Could you find all my screenshots across folders, delete the oldest 10, and check the folder's new total size in Files? <!--medium__files__009-->

**1. [BookMyShow] — DETERMINISTIC**
- We're doing a movie night this weekend. Could you check showtimes and seat prices and save the best one? <!--hard__bookmyshow__005-->

**[Settings]**
- Easy (1pt): I want to know if my phone's up to date. Can you check the device's current software version in Settings? Reply with only yes or no, no other text. <!--easy__settings__014-->

**[Phone]**
- Easy (1pt): I want to see how much I've been on the phone today. Can you tell me how many calls I've made today in Phone? Reply with only the total call time, no other text. <!--easy__phone__005-->

**[Amazon Shopping]**
- Easy (1pt): I thought I added something earlier and want to confirm. Can you open Amazon Shopping and check whether '[product]' is currently in my cart? <!--easy__amazon-shopping__002-->

**[Prime Video]**
- Medium (3pt): I want to pick up where I left off. Open Prime Video, find what's in my "Continue Watching", and give me a quick summary of the most recent one. <!--medium__prime-video__003-->

**3. [Gmail+Calendar] — DETERMINISTIC**
- I'm flying out soon and don't wanna miss it. Can you make sure I get a heads-up before departure? <!--hard__gmail-calendar__003-->

**5. [Music+Obsidian] — DETERMINISTIC**
- I listen to music to fall asleep and want it to stop by itself around my bedtime. Can you set that up with my kind of music? <!--hard__music-obsidian__077-->

**[Google Maps]**
- Easy (1pt): I just parked and I'm worried I'll forget where. Could you save my current location in Google Maps as 'parked here'? <!--easy__google-maps__004-->

**4. [Google Search+Telegram+Clock] — ASK USER**
- I'm going to grab something from the place I'm going to. Look up its hours via Google Search, note whether it's open now, and if it is, message the person I'm going with on Telegram suggesting we go now; otherwise message the reopening time and set an alarm for it <!--hard__google-search-telegram-clock__018-->

**[Swiggy]**
- Easy (1pt): I'm starving and my food's been a while. Can you open Swiggy and check the delivery status of my most recent order? Reply with only the delivery status, no other text. <!--easy__swiggy__001-->

- Medium (3pt) **[Clock + Calendar]**: Could you set a recurring alarm, confirm it doesn't clash with an existing Calendar event, and label it accordingly in Clock? <!--medium__clock__009-->

**[Google Meet]**
- Easy (1pt): I want to know which meeting I need to be ready for first. Can you check today's list of scheduled meetings in Google Meet and tell me the earliest one? <!--easy__google-meet__004-->

- Medium (3pt) **[Google Photos + Messages]**: Could you find and remove duplicate photos in Google Photos? Also, message [contact] how much storage was freed. <!--medium__google-photos__012-->

**[YouTube]**
- Easy (1pt): I want to see what people are saying about this video. Can you check the comments on the current video in YouTube? <!--easy__youtube__011-->

- Medium (3pt) **[Chrome + Messages]**: Could you filter my bookmarks to only ones added this month, delete any duplicates, and count what's left in Chrome? Also, message [contact] the count. <!--medium__chrome__011-->


### Day 3

- Medium (3pt) **[Google Photos + Phone]**: Could you filter the library to only videos over 1 minute long, delete the longest if it's unneeded, and count what's left in Google Photos? Also, call [contact] to confirm the plan for tonight. <!--medium__google-photos__008-->

**4. [Google Search+Obsidian+Telegram] — ASK USER**
- I'm tracking [stock name] and only want to hear about it when it matters. Check its current value via Google Search against the threshold in my '[stock note title]' Obsidian note, note today's value, compare it to the last recorded value in that Obsidian note, message the person I follow this stock with on Telegram only if it has crossed the threshold since then, and update the Obsidian note with today's value <!--hard__google-search-obsidian-telegram__057-->

- Medium (3pt) **[Google Photos + Calendar]**: I want to see my photo habits this year. Can you summarize how many photos I took each month this year? Note down the busiest month for me, and set a calendar reminder to review that month's album in Google Photos sometime tomorrow noon?. Reply with only the number of photos, no other text. <!--medium__google-photos-calendar__001-->

**[BookMyShow]**
- Easy (1pt): I'm free tonight and want to catch a movie nearby. Open BookMyShow and tell me which movies are playing at the nearest cinema. <!--easy__bookmyshow__004-->

**[YouTube]**
- Easy (1pt): I paused mid-video and want to pick up where I stopped. Can you resume a recently watched video in YouTube from where it left off? <!--easy__youtube__009-->

- Medium (3pt) **[Google Search + Telegram]**: Could you compare public transit options for a specific route and tell me the fastest in Google Search? Also, message [contact] on Telegram the fastest route for tomorrow. Reply with only the fastest option, no other text. <!--medium__google-search__008-->

**1. [Chrome+YouTube+Notes] — ASK USER**
- I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note <!--hard__chrome-youtube-notes__088-->

- Medium (3pt) **[Contacts + Phone]**: Could you merge duplicate contacts sharing the same phone number, confirm only one remains, and check its info is complete in Contacts? Also, call [contact] to confirm their address. <!--medium__contacts__012-->

- Medium (3pt) **[Calculator + Obsidian + Notes]**: I'm stressing about my grades. Can you open the '[exam scores note title]' note in Obsidian, read my exam scores and how much each one is weighted, then compute the weighted average in Calculator? Write the final grade in a note. Oh and check whether it meets the passing threshold of [passing threshold]. That's the real ask. Reply with only the final grade, no other text. <!--medium__calculator__001-->

**[Google Docs]**
- Easy (1pt): I've got a document I need a fresh copy of to edit — could you open Google Docs and rename one of my existing documents for me to an apt name based on the contents of the document? <!--easy__google-docs__004-->

- Medium (3pt) **[Music + Telegram]**: Could you compare my listening stats between this week and last week, note the difference, and share the summary with [contact] on Telegram in Music? <!--medium__music-telegram__001-->

**[MSN News]**
- Easy (1pt): I want to know what's big in [topic] right now. Can you open MSN News and read me the headline of the top story in the '[topic]' section? Reply with only the top story, no other text. <!--easy__msn-news__002-->

**2. [Clock+Calendar] — DETERMINISTIC**
- I need an alarm that repeats, but make sure it doesn't clash with anything I've got going on. <!--hard__clock-calendar__023-->

**[Messages]**
- Easy (1pt): Words aren't enough for this reply. Can you send a GIF in a conversation in Messages? <!--easy__messages__010-->

**3. [Google Meet+Files] — DETERMINISTIC**
- Got a meeting coming up and the agenda needs prepping. Can you pull up the next one and get the doc ready? <!--hard__google-meet-files__070-->

**[Prime Video]**
- Easy (1pt): I've been saving shows and lost track of how many. Can you open Prime Video and tell me how many titles are in my Watchlist sorted by TV Shows? Reply with only the number, no other text. <!--easy__prime-video__002-->

**[Google Photos]**
- Easy (1pt): That screenshot was a mistake and I want it gone. Can you delete my most recent screenshot in Google Photos? <!--easy__google-photos__015-->
