# DrainBench300 self-audit: improvement tasks (2026-08-14)

This doc is a **self-audit of our own 530-task corpus** (`benchmarks/dailyBench-600/tasks_530.md`),
**inspired by patterns in `Tongyi-MAI/MobileWorld`** (Apache-2.0, sparse-cloned for
inspection; 202 tasks across calendar/chrome/gmail/map/messages/native/settings/work). We
do NOT copy MobileWorld code or exact task text; we mined it to spot *categories of
capability* our corpus is missing, then wrote fresh tasks in our own format to close each
gap.

For each gap this doc: states the gap (with current-coverage evidence from our corpus) and
writes **only our-format tasks** (first-person, Easy/Medium/Hard buckets, deterministic +
ASK USER, data-present-on-device, ≥1 page real content for content-dependent apps, no em
dashes in prose). These are proposals for future days; none have been added to
`tasks_530.md` yet. IDs use the `<difficulty>__<app-slug>__<NNN>` convention but `NNN` is
a placeholder.

Corpus facts at time of audit: 530 tasks (216E/242M/72H, 36 ASK / 36 DET, 61 hallucination
controls, 0 dupes), 353 single-app / 177 cross-app. Days 1-4 are locked (already run);
new tasks go in day 5+ only, keeping 9-10 apps/day and the 216/242/72 bucket split.

---

## Gap 1: Files has no PDF-invoice read + recompute task

Coverage today: `hard__files-notes__011` reads an invoice + applies a late fee, but there
is no easy/medium "read the invoice and give me the total" tier, and no
"invoice vs receipt naming" categorization.

**Easy (new):**
```
- Easy (1pt): Open the invoice PDF in my Downloads and tell me the total amount on it.
<!--easy__files__015-->
```
Seed: `invoice.pdf` with a total line (real PDF). End-state: correct total reported.

**Medium (new):**
```
- Medium (3pt): Open the invoice PDF in my Downloads. The customer pays 45 days after the
due date, so recalculate the total amount payable with the late fee applied, and reply with
only the number. <!--medium__files__015-->
```
Seed: `invoice.pdf` with line items + a stated late-fee % (real PDF). End-state: correct
recalculated total.

**Medium (new, invoice vs receipt categorization):**
```
- Medium (3pt): Find the PDFs in my Downloads whose filenames contain 'invoice' or 'receipt'
from this month, and copy them into my 'Finance/invoice' folder. <!--medium__files__016-->
```
Seed: a mix of invoice/receipt/other PDFs (real content). End-state: correct copies moved.

---

## Gap 2: Files has no zip extraction / line-count task

Coverage today: zero tasks that open a zip and count lines, and no "compress files" task.
This is a genuinely useful long-horizon Files capability.

**Medium (new):**
```
- Medium (3pt): Open the earliest zip file from July in my Downloads, and count the total
number of lines across all the text files inside it. Reply with only the integer total.
<!--medium__files__017-->
```
Seed: a July zip containing 3-4 text files with known line counts (real content).
End-state: correct total line count.

**Hard (new, compress + record):**
```
**NN. [Files+Notes] — DETERMINISTIC**
Compress the files I downloaded in the past three months into a single 'old_files.zip' in
my Downloads, note its size in a note, and confirm which files went in.
<!--hard__files-notes__NNN-->
```
Seed: several downloaded files with recent timestamps (real content). End-state: zip exists,
note has size + file list.

---

## Gap 3: Settings lacks brightness/font/flight-mode tiers

Coverage today: `easy__settings__005` (manual brightness), no font-size task, no
flight-mode task, and wallpaper only exists as an HC end-failure
(`hard__gallery-settings-obsidian__075`). These are cheap, deterministic Settings checks
MobileWorld covers well.

**Easy (new):**
```
- Easy (1pt): Set my screen brightness to the maximum level in Settings.
<!--easy__settings__018-->
```
End-state: brightness == max (read via dumpsys).

**Easy (new):**
```
- Easy (1pt): Turn flight mode on in Settings. <!--easy__settings__019-->
```
End-state: flight mode enabled (read via adb).

**Easy (new):**
```
- Easy (1pt): Turn flight mode off in Settings. <!--easy__settings__020-->
```
End-state: flight mode disabled.

**Medium (new):**
```
- Medium (3pt): Increase my font size and icon size to the maximum setting in Settings.
<!--medium__settings__015-->
```
End-state: font scale + display density at max.

**Easy (new, wallpaper):**
```
- Easy (1pt) **[Gallery+Settings]**: Change my wallpaper to the photo of [flower type] from
my gallery. <!--easy__gallery-settings__001-->
```
Seed: a [flower type] photo in Gallery. End-state: wallpaper is that image.

---

## Gap 4: Clock lacks ringtone/vibration detail on alarms

Coverage today: many Clock alarm tasks, but none set an alarm with a specific ringtone or
vibration toggle. MobileWorld's `SetAlarmTask` (ringtone "beebeep", vibration off) is a
nice deterministic check we don't have.

**Medium (new):**
```
- Medium (3pt): Set a weekend alarm for [time] with the ringtone '[ringtone]' and vibration
turned off. <!--medium__clock__015-->
```
End-state: alarm at [time], weekend repeat, vibration off (read via adb).

**Medium (new, ASK USER variant):**
```
- Medium (3pt): Set a wake-up alarm for my weekend and pick my favorite ringtone
(deliberately no ringtone is named, so the agent must ask the user which one they want)
<!--medium__clock__016-->
```
Ask-user fact: the ringtone. End-state: alarm set with the chosen ringtone.

---

## Gap 5: Calendar lacks duplicate-event detection

Coverage today: no task asks for finding/counting duplicate calendar events.

**Medium (new):**
```
- Medium (3pt): Could you check my calendar from [start date] to [end date], find any
duplicate events, and tell me how many unique events remain? <!--medium__calendar__015-->
```
Seed: a week with a few duplicate events. End-state: unique count reported.

---

## Gap 6: Gmail lacks email->calendar bulk extraction

Coverage today: `hard__gmail-calendar__003` (flight reminder) exists, but no task reads a
batch of emails and creates several calendar events from them.

**Medium (new):**
```
- Medium (3pt) **[Gmail+Calendar]**: Check my email for any job interviews I have this
month, and add each one to my calendar using the company name as the title and the
interview time as the event window. <!--medium__gmail-calendar__002-->
```
Seed: 2-3 seeded interview emails (real content). End-state: calendar events created.

---

## Gap 7: Gmail+Messages conditional-response bridges

Coverage today: `medium__gmail-messages__001` style variants exist but there's no
"if found do X else text Y" conditional off an email's content.

**Medium (new):**
```
- Medium (3pt) **[Gmail+Messages]**: Check whether I've received an email with the
departure time for [event]. If not, text [contact] 'Do you know what time we're leaving
tomorrow?'. <!--medium__gmail-messages__002-->
```
Seed: no departure email (absent) + [contact] exists. End-state: the SMS is sent.

---

## Gap 8: Google Maps has no drive-time -> SMS task

Coverage today: Maps distance tasks exist (`easy__google-maps__001` etc.), but no
"look up drive time then text it to someone" combo.

**Medium (new):**
```
- Medium (3pt) **[Google Maps+Messages]**: Look up how long it takes to drive from
[origin] to [destination], then text [contact] the approximate arrival time if I leave at
[time]. <!--medium__google-maps-messages__001-->
```
Seed: real web maps; [contact] exists. End-state: SMS with arrival time.

---

## Gap 9: Google Maps+Contacts phone lookup

Coverage today: `hard__phone-contacts__040` (missed-call -> contact) exists, but no
"look up a company's phone on Maps then create a contact" task.

**Medium (new):**
```
- Medium (3pt) **[Google Maps+Contacts]**: Find the phone number of [company]'s [city]
office on Google Maps, then create a contact named '[contact]' with that number and the
company name. <!--medium__google-maps-contacts__001-->
```
Seed: real maps lookup. End-state: contact created with right number/company.

---

## Gap 10: Low-density apps need medium tiers

Coverage today (all easy-only or nearly): MakeMyTrip 1, BookMyShow 1, Prime Video 2,
Swiggy 2, MSN News 2, Amazon Shopping 2, Weather 4. These apps need a Medium (3pt) tier to
be properly benchmarked.

**Medium (new, Weather):**
```
- Medium (3pt): Compare the hourly forecast for tomorrow morning against this evening in
the Weather app, note which will be cooler, and check whether rain is expected in either
window. <!--medium__weather__001-->
```
End-state: comparison reported.

**Medium (new, Amazon Shopping):**
```
- Medium (3pt) **[Amazon Shopping+Messages]**: Check the price of '[product]' on Amazon
Shopping, then text [contact] the price plus whether it's cheaper than [price].
<!--medium__amazon-shopping-messages__001-->
```
Seed: real catalog + [contact]. End-state: SMS with price + comparison.

**Medium (new, MSN News):**
```
- Medium (3pt): Open MSN News, read the top 3 headlines in the '[topic]' section, and rank
them by how important they seem. <!--medium__msn-news__001-->
```
End-state: 3 headlines + ranking.

**Medium (new, MakeMyTrip):**
```
- Medium (3pt): Compare the cheapest flights from [city] to [place] next week on MakeMyTrip
across two airlines, note the cheaper one, and check its departure time.
<!--medium__makemytrip__001-->
```
End-state: cheaper airline + departure time reported.

**Medium (new, BookMyShow):**
```
- Medium (3pt): Find the highest-rated movie playing at the nearest cinema on BookMyShow,
note its showtimes, and tell me the earliest one today. <!--medium__bookmyshow__001-->
```
End-state: movie + earliest showtime reported.

---

## Gap 11: Contacts+Messages bulk "say hello" tier

Coverage today: no task adds several contacts and texts each of them.

**Medium (new, ASK USER):**
```
- Medium (3pt) **[Contacts+Messages]**: Add my new roommates to Contacts, favorite them,
and text 'hello' to each of them (deliberately no roommate names or numbers are given, so
the agent must ask the user for them) <!--medium__contacts-messages__001-->
```
Ask-user fact: roommate names + numbers. End-state: contacts + SMS sent.

---

## Gap 12: Calendar -> SMS bridge (dates out to a contact)

Coverage today: `hard__gmail-calendar__003` reads a flight email then sets a reminder, but
there is no "read my calendar and text the dates to someone" bridge. MobileWorld's
`CheckConferenceAndSendSmsTask` does exactly this.

**Medium (new):**
```
- Medium (3pt) **[Calendar+Messages]**: Check my calendar for the arrival and departure
dates of my trip to [place], and text [contact] those two dates in MM/DD/YYYY format
separated by a comma. Find [contact]'s number in Contacts. <!--medium__calendar-messages__002-->
```
Seed: trip events in Calendar; [contact] in Contacts. End-state: SMS contains the dates.

**Hard (new, ASK USER):**
```
**NN. [Calendar+Messages] — ASK USER**
I have a trip coming up and want to keep someone in the loop. Check my calendar for the
arrival and departure dates, and text the dates to the person I want to notify
(deliberately no trip or recipient is named, so the agent must ask the user which trip
and who to notify) <!--hard__calendar-messages__NNN-->
```
Ask-user fact: trip + recipient. End-state: SMS with the dates.

---

## Gap 13: SMS invite -> calendar reply/schedule

Coverage today: no task reads an incoming SMS invitation, checks calendar availability,
then replies + creates an event. MobileWorld's `ScheduleCoffeeTimeViaSms` /
`ScheduleLunchViaSms` family is a strong, deterministic pattern we lack.

**Hard (new, DETERMINISTIC):**
```
**NN. [Messages+Calendar] — DETERMINISTIC**
I got a coffee invitation over text asking if [date] at [time] works. Check my calendar:
if I'm free then, reply 'OK' and add a matching calendar event; if not, reply 'Not
available in this time slot.' <!--hard__messages-calendar__NNN-->
```
Seed: injected SMS invite + a calendar that may or may not conflict. End-state: reply text
+ event (or honest "not available").

**Medium (new, ASK USER):**
```
- Medium (3pt) **[Messages+Calendar]**: I've received a lunch invitation via text. Reply
'OK' and schedule a matching event on my calendar (deliberately no time is stated, so the
agent must ask the user what time works) <!--medium__messages-calendar__001-->
```
Ask-user fact: the lunch time. End-state: reply + calendar event.

---

## Gap 14: Calendar -> "cancel a meal/meeting" email

Coverage today: no task reads next week's schedule and emails a person to cancel a
specific meeting/meal. MobileWorld's `CheckMealEventAskUser` / `CheckMeetingEventAskUser`.

**Medium (new, ASK USER):**
```
- Medium (3pt) **[Calendar+Gmail]**: Check next week's schedule. If there's a meal with
someone, email them to ask if it can be canceled (deliberately no person or meal is named,
so the agent must ask the user who the meal is with) <!--medium__calendar-gmail__001-->
```
Seed: a meal event next week + contact's email in Contacts. Ask-user fact: who.
End-state: cancel-request email sent.

**Hard (new, ASK USER):**
```
**NN. [Calendar+Gmail] — ASK USER**
Check next week's schedule. If there's a meeting with someone, email them to ask if it can
be canceled (deliberately no meeting or person is named, so the agent must ask the user
which meeting and who it's with) <!--hard__calendar-gmail__NNN-->
```
Ask-user fact: meeting + person. End-state: cancel-request email sent.

---

## Gap 15: Resume -> conditional SMS to HR

Coverage today: no task reads a resume and makes a pass/reject decision. MobileWorld's
`CheckCandidateAskUserTask` (skill/GPA check -> kickoff/reject SMS) is a nice deterministic
decision task.

**Medium (new, DETERMINISTIC):**
```
- Medium (3pt) **[Files+Messages]**: Find [candidate]'s resume in Downloads and check
whether their skills match the job requirement in my note. If yes, text [contact] 'please
kickoff the interview for [candidate].'; if no, text 'please reject the application.'
<!--medium__messages-files__001-->
```
Seed: resume PDF with real skills + a note stating the requirement. End-state: correct SMS.

**Hard (new, ASK USER):**
```
**NN. [Files+Messages] — ASK USER**
Read [candidate]'s resume in Downloads and check their GPA against the job requirement. If
it passes, text HR to move them forward; if not, text HR to reject (deliberately no GPA
threshold is given, so the agent must ask the user what the requirement is)
<!--hard__messages-files__NNN-->
```
Ask-user fact: the GPA cutoff. End-state: pass/reject SMS to HR.

---

## Gap 16: Files batch rename by date (bid_ prefix)

Coverage today: `easy__files__006` renames a single file; no task renames a group by
creation date. MobileWorld's `BidFileRenameTask` renames `bid_*` files in date order.

**Medium (new):**
```
- Medium (3pt): Rename the files in my Downloads that start with 'bid_' in creation-date
order to 'bid_1.ext', 'bid_2.ext', and so on, keeping each original extension.
<!--medium__files__018-->
```
Seed: several bid_ files with real content + distinct dates. End-state: renamed in order.

---

## Gap 17: Invoice -> SMS (line-item comparison)

Coverage today: `easy__files__014` reads a boarding pass; no task reads an invoice and
texts a computed delta between line items. MobileWorld's `CheckInvoiceTask3` does this.

**Medium (new):**
```
- Medium (3pt) **[Files+Messages]**: Open the invoice PDF in my Downloads and text
[contact] how many more hours Consulting Services has than Software Development, as a
single number. <!--medium__files-messages__001-->
```
Seed: invoice.pdf with both line items (real PDF). End-state: SMS with the delta.

---

## Gap 18: Weather -> SMS

Coverage today: Weather tasks are all read-only; no task texts tomorrow's forecast to
someone. MobileWorld's `SendWeatherSmsTask`.

**Medium (new):**
```
- Medium (3pt) **[Weather+Messages]**: Check tomorrow's daytime forecast in the Weather
app and text [contact] the condition and temperature. <!--medium__weather-messages__001-->
```
Seed: real weather + [contact]. End-state: SMS with forecast.

---

## Gap 19: Count a keyword on a page -> SMS

Coverage today: Chrome tasks read/summarize pages, but no task counts an exact keyword
occurrence and texts the result. MobileWorld's `SendWebpageAudioCountSmsTask`.

**Medium (new):**
```
- Medium (3pt) **[Chrome+Messages]**: Open [article url] in Chrome, count how many times
the word '[keyword]' appears on it, and text [contact] that count.
<!--medium__chrome-messages__001-->
```
Seed: real web page. End-state: SMS with the count.

---

## Gap 20: Settings min-tiers + more toggles

Coverage today: gap 3 added max brightness + flight mode + max font; MobileWorld also has
*minimum* brightness/font and a wallpaper-with-photo task. Add the min counterparts so the
Settings tier is symmetric.

**Easy (new):**
```
- Easy (1pt): Set my screen brightness to the minimum level in Settings.
<!--easy__settings__021-->
```
End-state: brightness == min (read via dumpsys).

**Medium (new):**
```
- Medium (3pt): Decrease my font size and icon size to the minimum setting in Settings.
<!--medium__settings__016-->
```
End-state: font scale + display density at min.

**Easy (new, wallpaper with a named photo):**
```
- Easy (1pt) **[Gallery+Settings]**: Change my wallpaper to the photo 'sunset.jpg' from my
gallery. <!--easy__gallery-settings__002-->
```
Seed: sunset.jpg in Gallery. End-state: wallpaper is that image.

---

## Notes on adopting these

- Every content-dependent seed (invoice PDFs, zips, calendar events, emails, gallery
  photos, settings values) must be REAL on-device (>=1 page / populated), per the
  2026-08-13 content audit. Hallucination-control variants (where the email / event / file
  is genuinely absent) must say "MUST NOT create" with status `absent`.
- Bucket/difficulty above is a suggestion; fit to the 216E/242M/72H target and keep the
  ASK USER / DETERMINISTIC balance (36/36 on the 530 set).
- Emails / texts reference [contact]/[sender] placeholders resolved from
  `tasks_vars.local.env`; the persona world (Yuvraj Airtel / Yuvraj Singh Jio / Maa /
  Harshit Singh / Akash Kumar, Bhubaneswar) stays consistent.
- Verify app coverage stays 9-10 apps/day and keep days 1-4 untouched; new tasks go in
  day 5+ only.
- These are raw *ideas* for future days; nothing here has been added to `tasks_530.md`
  yet. Each needs a manifest + seed before it can run.
