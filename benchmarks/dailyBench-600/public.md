# DrainBench — Public Sample (3-Day Preview)

### Not the eval set. A structural preview only — a TRUE sample drawn from the
530-task corpus (same task_ids, placeholder slots; prompts identical except
note/tell tasks carry the 530-style output format "Reply with only X, no other
text"). **57 tasks total.**

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

**[Calendar]**
- Easy (1pt): I've got a packed day tomorrow and want to make sure nothing overlaps. Could you check my Calendar for any scheduling conflicts tomorrow afternoon? <!--easy__calendar__002-->

**[Chrome]**
- Easy (1pt): I'd rather shop in person if there's one close by. Can you check if [store] has a physical location nearby via Chrome? <!--easy__shopping-delivery-browser__012-->

**[Clock]**
- Easy (1pt): I'm about to time something and need to start right away. Can you start the stopwatch in Clock? <!--easy__clock__010-->

**[Files+Obsidian]**
- Medium (3pt) **[Files + Obsidian]**: My storage keeps shrinking and I need to find the big offenders. Filter files larger than 100MB across the whole device, note the largest one, star it, and log its size in an Obsidian note in Files? List it for me in the format of "Filename" | "Size" strictly. <!--medium__files__010-->

**[Gallery+Obsidian]**
- Medium (3pt) **[Gallery + Obsidian]**: Could you find the 10 photos taking up the most storage, review them, delete the 3 least useful ones, and note the space freed in Obsidian in Gallery? Reply with only the space freed, no other text. <!--medium__gallery__007-->

**[Gmail]**
- Easy (1pt): Can you forward the most recent email in my Gmail to [contact] pls? <!--easy__gmail__001-->

**[Google Photos]**
- Easy (1pt): I'm trying to remember when I last captured something. Can you open Google Photos and tell me the date of my most recent photo? Reply with only the date, no other text. <!--easy__google-photos__004-->

**[Google Sheets]**
- Medium (3pt): Could you open '[spreadsheet name]', freeze the header row, and confirm it stays visible when scrolling in Google Sheets? <!--medium__google-sheets__003-->

**[Music]**
- Easy (1pt): That song's stuck in my head and I need to hear it. Can you search for '[song]' in Music and play it? <!--easy__music__009-->

**[Music+Gmail]**
- Medium (3pt) **[Music + Gmail]**: Could you find songs I downloaded for offline listening that I haven't played in months and remove them in Music? Also, email [contact] how much storage that freed up. <!--medium__music__004-->

**[Notes]**
- Medium (3pt): Could you open my '[note title]' note in Notes, read it, and rewrite it into a cleaner version with clear sections, keeping all the original points? <!--medium__notes__005-->

**[Settings]**
- Medium (3pt): Could you compare today's battery usage to yesterday's, note the difference, and check which app used the most today in Settings? Tell me in the format of "Difference" | "Top app" strictly. <!--medium__settings__005-->

**[Swiggy]**
- Easy (1pt): I'm starving and my food's been a while. Can you open Swiggy and tell me the delivery status of my most recent order? Reply with only the delivery status, no other text. <!--easy__swiggy__003-->

**[YouTube+Gmail]**
- Medium (3pt) **[YouTube + Gmail]**: Could you compare the view counts across three videos on the same topic and save the most popular one in YouTube? Also, email [contact] the link to the most popular video. <!--medium__youtube__005-->

Hard tasks — Day 1:
**1. [Drive+Notes+Telegram] — ASK USER**
- I'm worried our shared budget spreadsheet is slipping. Open the shared budget spreadsheet in Drive, check when it was last edited, and compare that against the committed finalisation deadline noted in my 'Budget Deadline' note. If it hasn't been updated by the deadline (it's overdue), message the person who owns the budget on Telegram to chase it; otherwise just log today's check date in the note. Confirm what you did either way <!--hard__drive-notes-telegram__010-->
**2. [Swiggy] — DETERMINISTIC**
- Ugh, I'm craving what I ordered last Friday — can you get me that again? Just take me to the payment page, don't place the order. <!--hard__swiggy__005-->
**3. [Music+Obsidian] — DETERMINISTIC**
- I listen to music to fall asleep and want it to stop by itself around my bedtime. Can you set that up with my kind of music? <!--hard__music-obsidian__077-->
**4. [Files+Notes] — ASK USER**
- I need to pay an invoice and want to know what I actually owe. Find the most recent invoice PDF in Files (you can open it in any PDF Viewer you desire), extract the total amount and due date, and if the due date has passed, add the late fee I specify. Log the new total in a note and reply with only that number, no other text <!--hard__files-notes__011-->
**5. [Contacts+Obsidian] — DETERMINISTIC**
- I got new phone numbers for my dad and myself. My '[contact updates title]' Obsidian note lists both of them with the updated numbers. So, can you update each person's phone number in Contacts to match the note's updated numbers please? Then, get back to me in this format: "Contact" | "Old phone no." | "New phone no.". <!--hard__contacts-obsidian__029-->
**6. [Telegram+Calendar] — DETERMINISTIC**
- Pretty sure someone dropped a date in one of the group chats. Can you check and set a reminder if there's one? <!--hard__telegram-calendar__016-->

### Day 2

**[Calculator+Obsidian+Notes]**
- Medium (3pt) **[Calculator + Obsidian + Notes]**: I'm stressing about my grades. Can you open the '[exam scores note title]' note in Obsidian, read my exam scores and how much each one is weighted, then compute the weighted average in Calculator? Write the final grade in a note. Oh and check whether it meets the passing threshold of [passing threshold]. That's the real ask. Reply with only the final grade, no other text. <!--medium__calculator__001-->

**[Calculator+Telegram]**
- Medium (3pt) **[Calculator + Telegram]**: Could you open the '[shared bill note title]' note in Obsidian, compute each roommate's share of the shared bill with different usage levels, message each their share, and log the total bill in a note in Calculator? List each share for me in the format of "Name" | "Share" strictly, and reply with only the total bill, no other text. <!--medium__calculator__005-->

**[Calendar]**
- Medium (3pt): Could you find all events tagged 'work' this week, total the hours booked, and note the total in Calendar? Reply with only the total hours, no other text. <!--medium__calendar__013-->

**[Chrome]**
- Easy (1pt): I'm about to order food but worried about surcharges — open the [food delivery site] in Chrome and check if there's any weather-related surcharge notice <!--easy__shopping-delivery-browser__001-->

**[Google Maps+Gmail]**
- Medium (3pt) **[Google Maps + Gmail]**: Could you filter EV charging stations near the route by connector type and check the nearest one's availability in Google Maps? Also, email [contact] the address of the nearest station. <!--medium__google-maps__003-->

**[Google Sheets]**
- Medium (3pt): I need a quick total for a column and don't want to do the math. Could you open '[spreadsheet name]' and sum up the [sheet column] column in Google Sheets? Reply with only the total, no other text, then add it as a new row at the bottom and adjust any other columns' values that need fixing because of that change. <!--medium__google-sheets__001-->

**[Google Slides]**
- Easy (1pt): I need to check the ending of the deck. Can you open '[presentation name]' in Google Slides and go to the last slide? <!--easy__google-slides__002-->
- Medium (3pt): Could you open '[presentation name]', reorder the slides so the title slide is first, and confirm the new order in Google Slides? <!--medium__google-slides__002-->

**[Messages]**
- Easy (1pt): I've been busy and haven't checked my chats. Can you check my unread messages in Messages? Reply with only the number of unread messages, no other text. <!--easy__messages__013-->

**[Phone]**
- Easy (1pt): I want to see who I need to call back from today. Can you check my missed calls from today only in Phone? Reply with only the number of missed calls, no other text. <!--easy__phone__015-->

**[Prime Video]**
- Easy (1pt): I've been saving shows and lost track of how many. Can you open Prime Video and tell me how many titles are in my Watchlist? Reply with only the number, no other text. <!--easy__prime-video__002-->

**[Telegram]**
- Easy (1pt): I don't want them to know I've seen the message yet. Can you turn off read receipts for [contact] in Telegram? <!--easy__telegram__010-->

**[Weather]**
- Easy (1pt): I'm about to head out and don't want to get caught in the rain. Can you check today's weather in the Weather app and tell me if it looks good for my commute? Reply with only yes or no, no other text. <!--easy__weather__003-->

**[YouTube]**
- Medium (3pt): Could you filter the Shorts feed for [topic], like the 3 best ones, and count how many you liked in YouTube? Reply with only the number, no other text. <!--medium__youtube__006-->

Hard tasks — Day 2:
**1. [Chrome+YouTube+Notes] — ASK USER**
- I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note <!--hard__chrome-youtube-notes__088-->
**2. [Clock+Calendar] — DETERMINISTIC**
- I need an alarm that repeats, but make sure it doesn't clash with anything I've got going on. <!--hard__clock-calendar__023-->
**3. [Gmail+Calendar] — DETERMINISTIC**
- I'm flying out soon and don't wanna miss it. Can you make sure I get a heads-up before departure? <!--hard__gmail-calendar__003-->
**4. [Chrome+Telegram+Notes] — ASK USER**
- I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing <!--hard__chrome-telegram-notes__008-->
**5. [Google Search+Clock] — DETERMINISTIC**
- I'm about to miss my bus. Look up [transit line]'s next departure via Google Search, write down the time remaining, and set an alarm now if it's within 10 minutes, otherwise set one 5 minutes before the following departure, then verify the alarm time. Reply in the format of "Time remaining" | "Alarm time" strictly. <!--hard__google-search-clock__056-->
**6. [Gmail+Notes] — DETERMINISTIC**
- I've got a coupon somewhere that's expiring soon. Can you find it and save it before it's gone? <!--hard__gmail-notes__045-->

### Day 3

**[Calculator]**
- Easy (1pt): We're splitting the bill and I want to know my share. Can you split a bill of [bill amount] evenly between 4 people in Calculator? <!--easy__calculator__007-->

**[Camera]**
- Easy (1pt): I'm about to shoot a lot and don't want to run out of space. Can you check how much storage is left for photos/videos in Camera? <!--easy__camera__006-->

**[Chrome]**
- Easy (1pt): I don't want anyone seeing what I just looked up. Can you clear my browsing history from the last hour in Chrome? <!--easy__chrome__012-->
- Medium (3pt): Could you rank the menu items on [food delivery site] by rating for [restaurant], pick the top one, and check its price in Chrome? <!--medium__shopping-delivery-browser__010-->

**[Clock]**
- Easy (1pt): I'm cooking and need a timer so I don't overcook these. Can you set a timer for boiling eggs in Clock? <!--easy__clock__007-->
- Medium (3pt): I'm cooking the [recipe] and it has several timed steps back-to-back. Read the recipe and set up a labeled timer in the Clock for each timed step (label each timer with its step name) so they are ready to start as each step begins; confirm each timer was created and labelled. <!--medium__clock__001-->

**[Files]**
- Medium (3pt): Could you filter files by type to isolate video files over 500MB, delete the largest, and note the size freed in Files? Reply with only the size freed, no other text. <!--medium__files__012-->

**[Google Meet]**
- Easy (1pt): I'm about to join a meeting by code and want to be ready. Can you open the 'Join with a code' screen in Google Meet and tell me what's on it? Reply with only what's on the screen, no other text. <!--easy__google-meet__003-->
- Easy (1pt): I want to know which meeting I need to be ready for first. Can you check today's list of scheduled meetings in Google Meet and tell me the earliest one? Reply with only the earliest meeting, no other text. <!--easy__google-meet__004-->
- Medium (3pt): Could you open the meeting link [meeting link] and land on the 'Ready to join?' screen without actually joining in Google Meet? <!--medium__google-meet__003-->
- Medium (3pt): Could you open Google Meet, check the participant list of my next scheduled meeting, and tell me who's expected to join? List them for me in the format of "Name" strictly. <!--medium__google-meet__005-->

**[Music+Telegram]**
- Medium (3pt) **[Music + Telegram]**: Could you summarize what a new album is about based on its track titles, decide whether to add it, and message [contact] on Telegram my verdict in Music? Reply with only your verdict, no other text. <!--medium__music-telegram__002-->

**[Phone]**
- Easy (1pt): I'm on a call and need to mute myself for a second. Can you mute the microphone during an active call in Phone? <!--easy__phone__008-->

Hard tasks — Day 3:
**1. [Music] — ASK USER**
- I want a high-energy workout playlist. Curate a workout playlist in Music based on song energy, with no explicit song list given <!--hard__music__072-->
**2. [Google Meet+Files] — DETERMINISTIC**
- Got a meeting coming up and the agenda needs prepping. Can you pull up the next one and get the doc ready? <!--hard__google-meet-files__070-->
**3. [Drive+Obsidian+Telegram] — ASK USER**
- I need to know if our shared spreadsheet has been touched since I last reviewed it. Check the shared spreadsheet's last-edited date in Drive and compare it against the 'last reviewed' date recorded in my 'Budget Deadline' note in Obsidian. If it has been edited since that date, message the person who owns the spreadsheet on Telegram to ask what changed; if it hasn't been touched, just star it and update the note with today's date. Confirm what you did either way <!--hard__drive-obsidian-telegram__049-->
**4. [Google Search+Notes] — DETERMINISTIC**
- I'm stuck between [product 1] and [product 2]. Can you look up reviews and tell me which one's better for me? Reply with only the better product, no other text. <!--hard__google-search-notes__019-->

