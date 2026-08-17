# Multi-Turn (KB) Task Authoring — 18 DET → Multi-Turn Conversion

> **Status: DRAFT for review.** Not yet applied to `tasks_530.md`/`public.md`.
> These are the 18 DETERMINISTIC hard tasks being converted to **multi-turn**
> (KB-oracle) mode. Each task has a deliberately **vague** prompt + a
> **knowledge-base profile** (JSON) the simulated user holds. The agent's job:
> ask the right clarifying questions, converge on the correct target, get it done.
>
> **Device data source:** real on-device state pulled 2026-08-17 from the
> OnePlus CPH2423 (serial RS7XKZDI8HTOJNYL): Obsidian notes, contacts, calendar.
> **Live-app data (Swiggy/Amazon orders) must be re-verified at run time** — the
> benchmark runs live, so order state changes; each KB's order entries below are
> the values to confirm/refresh just before running (see §"live data").

---

## 1. How the conversion works

- **Before:** a DETERMINISTIC hard task had a fixed prompt, and the simulated
  user held **one** hidden fact (`--ask-user-context`).
- **After:** the task keeps its hard difficulty but becomes **multi-turn**: it
  ships with a **KB profile** (`--ask-user-kb profile.json`). The simulated user
  is an **honest oracle** over the profile with **rolling memory** (v2 ask_user).
- The task prompt is **reworded to be genuinely ambiguous** — multiple plausible
  targets, only one correct per the on-device state — so the agent *must* ask to
  disambiguate (e.g. "check my order status" → *which* service, *which* order).
- Grading: **outcome** (acted on the correct target, verifiable on-device) as the
  hard gate + **turn count** as the efficiency signal (reference 1–2 turns).
- **"Agent must ask:"** lines in this doc are **human-review annotations only** —
  they show a reviewer what info is missing. They are **NOT** part of the agent's
  input. The agent gets only the natural prompt + the KB oracle and decides on its
  own how many / how good its clarifying questions are.

## 2. Two KB files (multi-turn convos only)

| File | Used by | Contents |
|---|---|---|
| `benchmarks/dailyBench-600/multiturn_kb_public.json` | public.md (3-day public preview) tasks | KB profiles for public-set multi-turn tasks |
| `benchmarks/dailyBench-600/multiturn_kb_530.json` | tasks_530.md (full 530) tasks | KB profiles for 530-set multi-turn tasks |

Format (per task_id):
```json
{
  "hard__some-task__NNN": {
    "correct_target": "swiggy::order_4821",
    "profile": {
      "orders": [ {"service":"Swiggy","order_id":"4821","status":"out for delivery","item":"Chicken Biryani","restaurant":"Biryani Blues","eta":"18:40","recent":true},
                  {"service":"Amazon","order_id":"9032","status":"shipped","item":"Noise earbuds","eta":"Aug 19"} ],
      "contacts": {...},
      "notes": {...},
      "preferences": {...}
    }
  }
}
```
`correct_target` is the single right answer the grader checks the agent acted on.

---

## 3. Selection audit — which 18 to convert (and why)

**Rule:** convert only tasks whose success depends on a **fact only the user
knows** (which order/restaurant/show/product/topic/channel/spreadsheet/files/
photo/code/group/meeting/bedtime). A vague prompt then *forces* the agent to ask.
**Keep as DET** the self-contained execution chains — the prompt fully specifies
the rule and the agent resolves it from on-device state + one hidden fact.

| Convert to multi-turn (user-KB-dependent) | Keep as DET (self-contained) |
|---|---|
| `swiggy__005`, `swiggy__007`, `makemytrip__003`, `prime-video__005` | `google-maps-notes__005`, `gallery-obsidian__035` |
| `bookmyshow__003`, `bookmyshow__005`, `amazon-shopping__006`, `msn-news__007` | `contacts-notes__027`, `contacts-obsidian__029` |
| `music-obsidian__077`, `youtube-settings__052`, `gmail-calendar__003` | `contacts-gmail__026`, `camera-files__034` |
| `google-sheets-amazon-shopping__074`, `telegram-calendar__016` | `settings-notes__081`, `settings-notes__082` |
| `google-meet-files__070`, `settings-obsidian__044`, `clock-calendar__023` | `chrome-files-obsidian__031`, `notes-files__030` |
| `gmail-notes__045`, `google-search-notes__019` | `calculator-telegram-notes__020`, `google-search-clock__056` |
| | `calendar-contacts-telegram__064`, `chrome-obsidian__048` |
| | `contacts-google-maps-notes__065`, `obsidian-calendar__067` |
| | `gallery-settings-obsidian__075`, `files-notes__069` |

> **v2 (this revision):** 6 tasks were pulled back out of the convert set after
> audit — `settings-notes__081`, `contacts-gmail__026`, `contacts-notes__027`,
> `notes-files__030`, `chrome-files-obsidian__031`, `obsidian-calendar__067` —
> because they are strong **single-shot** DET tasks (fully-specified rules the
> agent resolves from device state; a forced Q&A would be artificial). Replaced
> with 6 genuinely user-knowledge tasks: `music-obsidian__077`,
> `youtube-settings__052`, `google-sheets-amazon-shopping__074`, `gmail-notes__045`,
> `gallery-settings-obsidian__075`, `files-notes__069`.
>
> **v3 (wiring):** `gallery-settings-obsidian__075` and `files-notes__069` were
> pulled back out again — both are **hallucination-control** tasks (the wallpaper
> log / storage-limit note are deliberately ABSENT on the device; correct =
> honest failure). A KB oracle claiming that data exists would contradict the
> device and break the HC design, so they stay plain DET+HC. Replaced with two
> more genuine multi-turn tasks: `gmail-calendar__003` (which trip/flight) and
> `clock-calendar__023` (which alarm schedule).

## 4. The 18 tasks (DET → multi-turn), with complete KBs

> **Live-data flag 🔴:** entries that reflect real-time app state and MUST be
> re-confirmed on-device immediately before the run (orders, delivery status,
> today's news). Everything else (notes, contacts, calendar) is seeded/static.
>
> **ℹ️ "Agent must ask" lines under each task are author annotations for human
> review only — never sent to the agent.** The agent decides the number and
> quality of its own questions against the KB oracle.

### 1. `hard__swiggy__005` — reorder my last order (day 12)
**Prompt (vague):** "Ugh, I'm craving what I ordered last Friday — can you get me that again?"
Agent must ask: *which service? which order?* → converge on the Swiggy order.
```json
{
  "correct_target": "swiggy::order_4821",
  "profile": {
    "orders": [
      {"service":"Swiggy","order_id":"4821","date":"2026-08-14 (Fri)","item":"Chicken Biryani + Gulab Jamun","restaurant":"Biryani Blues","status":"delivered","recent":true},
      {"service":"Amazon","order_id":"9032","date":"2026-08-11","item":"Noise earbuds","status":"shipped","recent":false},
      {"service":"Swiggy","order_id":"4790","date":"2026-08-12","item":"Paneer Roll","restaurant":"Rolls King","status":"delivered","recent":false}
    ]
  }
}
```
🔴 Re-verify the actual most-recent-order state in Swiggy before running.

### 2. `hard__swiggy__007` — reorder my usual from [restaurant] (day 16)
**Prompt (vague):** "Order my usual from my go-to place - my favourite food. Don't place it, just show me the payment page."
Agent must ask: *which restaurant? which items?* → Biryani Blues + the biryani set.
```json
{
  "correct_target": "swiggy::biryani-blues-usual",
  "profile": {
    "orders": [
      {"service":"Swiggy","restaurant":"Biryani Blues","usual_items":["Chicken Biryani","Gulab Jamun","Coke"],"last_total":"₹412","recent":true},
      {"service":"Swiggy","restaurant":"Rolls King","usual_items":["Paneer Roll","Cold Coffee"],"last_total":"₹230","recent":false}
    ],
    "preferences": {"usual_restaurant":"Biryani Blues"}
  }
}
```
🔴 Re-verify restaurant still active + last-order items.

### 3. `hard__makemytrip__003` — cheapest flight fare breakdown (day 11)
**Prompt (vague):** "I've shortlisted a flight for my trip but wanna see the full fare before I pay. Can you open it and show me the breakdown on the payment page?"
Agent must ask: *which route? which airline? which day/date?* → BBI→DEL next week (Mon 2026-08-24), IndiGo, the cheaper of the two.
```json
{
  "correct_target": "makemytrip::bbi-del-indigo",
  "profile": {
    "trips": {
      "bbi_del": [
        {"airline":"IndiGo","flight":"6E 2031","date":"2026-08-24 (Mon)","depart":"BBI 07:10","arrive":"DEL 09:20","fare":"₹4,850"},
        {"airline":"Air India","flight":"AI 723","date":"2026-08-24 (Mon)","depart":"BBI 16:40","arrive":"DEL 19:05","fare":"₹5,390"}
      ],
      "bbi_bom": [
        {"airline":"IndiGo","flight":"6E 501","date":"2026-08-25 (Tue)","depart":"BBI 09:00","arrive":"BOM 11:15","fare":"₹5,100"}
      ]
    },
    "preferences": {"next_trip":"BBI to DEL next week"}
  }
}
```
🔴 Re-verify live fares/routes; keep both airlines on the route.

### 4. `hard__prime-video__005` — [show] leaving soon (day 12)
**Prompt (vague):** "One of my daily shows is apparently leaving soon. Can you check if it's still up and save it so I don't lose it?"
Agent must ask: *which show? which platform?* → Reacher on Prime Video (leaving 2026-08-31).
```json
{
  "correct_target": "prime-video::reacher",
  "profile": {
    "watchlist": [
      {"title":"Reacher","platform":"Prime Video","leaving":"2026-08-31","available":true,"downloadable":true},
      {"title":"The Boys","platform":"Prime Video","leaving":null,"available":true,"downloadable":true},
      {"title":"Dark","platform":"Netflix","leaving":null,"available":true,"downloadable":true}
    ]
  }
}
```
🔴 Re-verify which title shows a "leaving soon" badge in the app.

### 5. `hard__bookmyshow__003` — surprise-party movie booking (day 12)
**Prompt (vague):** "My friends are planning a surprise for one of our close friends. Can you book tickets to a movie he'd actually like? Pull his info from my contacts — don't buy, just get me to booking."
Agent must ask: *which friend? what does he like?* → Priyanshu (likes action) → an action movie → booking page.
```json
{
  "correct_target": "bookmyshow::priyanshu-action-movie",
  "profile": {
    "contacts": {
      "Priyanshu Kumar": {"likes":["action movies","sci-fi"],"birthday":"2026-08-20"},
      "Anannya Mishra": {"likes":["rom-coms"],"birthday":"2026-09-02"}
    },
    "preferences": {"surprise_party_for":"Priyanshu Kumar"}
  }
}
```
🔴 Re-verify friend's interests in the contact card + which movies are showing.

### 6. `hard__bookmyshow__005` — movie night for a group (day 21)
**Prompt (vague):** "We're doing a movie night this weekend. Could you check showtimes and seat prices and save the best one?"
Agent must ask: *which movie? which cinema? group size?* → [movie] at [cinema], group of 4.
```json
{
  "correct_target": "bookmyshow::group4-movie",
  "profile": {
    "cinemas": [
      {"name":"INOX Bhubaneswar","showing":["Kalki 2898 AD","Pushpa 2"],"seats_per_ticket":"₹240"},
      {"name":"PVR Esplanade","showing":["Kalki 2898 AD"],"seats_per_ticket":"₹280"}
    ],
    "preferences": {"group_size":4,"preferred_cinema":"INOX Bhubaneswar"}
  }
}
```
🔴 Re-verify movies currently showing + live prices.

### 7. `hard__amazon-shopping__006` — confirm cart total (day 21)
**Prompt (vague):** "Almost bought something but wanna double-check the total before I commit. Add it and show me the final price on the payment page — don't finish the order."
Agent must ask: *which product?* → Noise earbuds.
```json
{
  "correct_target": "amazon::noise-earbuds-cart",
  "profile": {
    "cart": [
      {"item":"Noise wireless earbuds","price":"₹1,299","prime_saved":"₹200"},
      {"item":"boAt Airdopes 131","price":"₹1,499","prime_saved":"₹250"}
    ],
    "preferences": {"intending_to_buy":"Noise wireless earbuds"}
  }
}
```
🔴 Re-verify the item is in cart + current price.

### 8. `hard__msn-news__007` — today's biggest story on [topic] (day 26)
**Prompt (vague):** "I am following the topic closely. Find today's biggest story on it, summarize it, and send it to my friend the summary."
Agent must ask: *which topic? which contact?* → cricket → [contact] on Telegram.
```json
{
  "correct_target": "msn-news::cricket-today",
  "profile": {
    "topics": {"cricket":true,"economy":false,"technology":true},
    "contacts": {"primary_share":"Yuvraj Airtel","telegram_handle":"@yuvraj_airtel"},
    "preferences": {"followed_topic":"cricket"}
  }
}
```
🔴 Live: today's top story must be looked up at run time (loose grading).

### 9. `hard__music-obsidian__077` — sleep timer to match bedtime (day 3)
**Prompt (vague):** "I listen to music to fall asleep and want it to stop by itself around my bedtime. Can you set that up with my kind of music?"
Agent must ask: *which music type? what's your bedtime?* → lo-fi → 10:30 PM (Bedtime note).
```json
{
  "correct_target": "youtube-music::sleep-timer-1030pm",
  "profile": {
    "music": {"favorite_genre":"lo-fi beats","sleep_artist":"Chillhop"},
    "notes": {"Bedtime":{"time":"10:30 PM","source":"real on-device note"}},
    "preferences": {"sleep_timer":"10:30 PM"}
  }
}
```
🔴 Re-verify favorite genre from YouTube Music history + the Bedtime note on device.

### 10. `hard__telegram-calendar__016` — date mentioned in group chat (day 9)
**Prompt (vague):** "Pretty sure someone dropped a date in one of the group chats. Can you check and set a reminder if there's one?"
Agent must ask: *which group?* → the study group.
```json
{
  "correct_target": "telegram::study-group-date",
  "profile": {
    "chats": [
      {"name":"Study Group","recent_date_mentioned":"2026-08-20","topic":"exam prep"},
      {"name":"Family","recent_date_mentioned":null,"topic":"general"},
      {"name":"Hostel","recent_date_mentioned":"2026-08-18","topic":"weekend plan"}
    ],
    "preferences": {"reminder_chat":"Study Group"}
  }
}
```
🔴 Live: verify which chat actually mentions a date at run time.

### 11. `hard__youtube-settings__052` — channel notifications muted at night (day 11)
**Prompt (vague):** "Notifications from one of my channels keep coming at night and it's annoying. Can you fix that so they only show up during the day?"
Agent must ask: *which channel?* → the one that posts most (Tech Burner).
```json
{
  "correct_target": "youtube-settings::channel-night-mute",
  "profile": {
    "channels": [
      {"name":"Tech Burner","posts_per_week":3,"notify":true},
      {"name":"Dhruv Rathee","posts_per_week":1,"notify":false}
    ],
    "preferences": {"notify_channel":"Tech Burner","quiet_hours":"22:00-08:00"}
  }
}
```
🔴 Re-verify the channel actually subscribed/followed on the device.

### 12. `hard__google-sheets-amazon-shopping__074` — top video + related buy (day 20)
**Prompt (vague):** "I've got all my video stats in a sheet. Can you find my best performer and show me something related to grab?"
Agent must ask: *which spreadsheet? which column?* → SPORTS_VIDEO_DATA → [views] → the top video.
```json
{
  "correct_target": "sheets-amazon::sports-video-data-top",
  "profile": {
    "spreadsheet": {
      "name":"SPORTS_VIDEO_DATA",
      "columns":["video_title","views","likes"],
      "top_video":{"title":"Final Match Highlights","views":"1.2M","column":"views"}
    },
    "preferences": {"related_product":"smartphone gimbal"}
  }
}
```
🔴 Re-verify the actual spreadsheet name + top row on device (user.yaml: SPORTS_VIDEO_DATA).

### 13. `hard__google-meet-files__070` — meeting agenda ready (day 14)
**Prompt (vague):** "Got a meeting coming up and the agenda needs prepping. Can you pull up the next one and get the doc ready?"
Agent must ask: *which meeting? which doc?* → the next meeting + its agenda doc.
```json
{
  "correct_target": "meet-files::next-meeting-agenda",
  "profile": {
    "meetings": [
      {"title":"Team Standup","time":"2026-08-18 10:00","agenda_doc":"Standup Agenda","attendees":5},
      {"title":"Project Review","time":"2026-08-18 14:00","agenda_doc":"Review Agenda","attendees":8}
    ],
    "preferences": {"next_meeting":"Team Standup"}
  }
}
```
🔴 Verify calendar actually has these events.

### 14. `hard__gmail-notes__045` — discount code before it expires (day 17)
**Prompt (vague):** "I've got a coupon for an online shopping website somewhere that's expiring soon. Can you find it and save it before it's gone?"
Agent must ask: *which account? which email? which code?* → the Flipkart coupon in the primary Gmail → save FLIP15.
```json
{
  "correct_target": "gmail-notes::discount-code-saved",
  "profile": {
    "accounts": [
      {
        "email": "yuvraj.singh@gmail.com",
        "primary": true,
        "emails": [
          {"from":"Flipkart","subject":"Your 15% coupon","code":"FLIP15","expires":"2026-08-20"},
          {"from":"Amazon","subject":"Deal of the day","code":null,"expires":null}
        ]
      },
      {
        "email": "yuvraj@college.edu",
        "primary": false,
        "emails": [
          {"from":"Student Offers","subject":"Exam-prep coupon","code":"PREP10","expires":"2026-08-25"}
        ]
      }
    ],
    "preferences": {"code_to_use":"FLIP15"}
  }
}
```
🔴 Re-verify a real coupon email exists + which Gmail account holds it at run time.

### 15. `hard__gmail-calendar__003` — flight departure heads-up (day 6)
**Prompt (vague):** "I'm flying out soon and don't wanna miss it. Can you make sure I get a heads-up before departure?"
Agent must ask: *which trip/flight?* → the BBI→DEL IndiGo 6E 2031 (2026-08-24, 07:10) → reminder 3h before.
```json
{
  "correct_target": "gmail-calendar::bbi-del-reminder",
  "profile": {
    "flights": [
      {"airline":"IndiGo","flight":"6E 2031","route":"BBI→DEL","date":"2026-08-24","depart":"07:10","confirmation_email":true},
      {"airline":"IndiGo","flight":"6E 501","route":"BBI→BOM","date":"2026-09-02","depart":"09:00","confirmation_email":false}
    ],
    "preferences": {"reminder_hours_before":3,"next_trip":"BBI→DEL"}
  }
}
```
🔴 Re-verify the flight-confirmation email + departure time on device.

### 16. `hard__settings-obsidian__044` — today's screen time (day 10)
**Prompt (vague):** "I've been glued to my phone lately. Can you check today's usage and see if I'm over my goal?"
Agent must ask: *which metric? which goal note?* → Screen Time vs the goal in the note.
```json
{
  "correct_target": "settings-obsidian::screen-time-goal",
  "profile": {
    "notes": {"Screen Time Goal":{"daily_limit_hours":2}},
    "preferences": {"check":"today's screen time"}
  }
}
```

### 17. `hard__clock-calendar__023` — recurring alarm that doesn't clash (day 6)
**Prompt (vague):** "I need an alarm that repeats, but make sure it doesn't clash with anything I've got going on."
Agent must ask: *what time? which days?* → 7:00 AM weekdays → Calendar shows a clash Mon 07:00–08:00 → shift to 07:30.
```json
{
  "correct_target": "clock-calendar::alarm-0730-shifted",
  "profile": {
    "alarm": {"requested_time":"07:00","days":["Mon","Tue","Wed","Thu","Fri"]},
    "calendar": [
      {"event":"Team Sync","date":"2026-08-17","start":"07:00","end":"08:00"},
      {"event":"Gym","date":"2026-08-18","start":"06:30","end":"07:30"}
    ],
    "preferences": {"shift_if_clash_min":30}
  }
}
```
🔴 Re-verify the recurring-event/weekly calendar on device.

### 18. `hard__google-search-notes__019` — product comparison (day 3)
**Prompt (vague):** "I'm stuck between two products. Can you look up reviews and tell me which one's better for me?"
Agent must ask: *which two products?* → the two in my notes.
```json
{
  "correct_target": "search-notes::product-comparison",
  "profile": {
    "notes": {"Products I'm Considering":[
      {"name":"Noise wireless earbuds","price":"₹1,299"},
      {"name":"boAt Airdopes 131","price":"₹1,499"}
    ]},
    "preferences": {"compare":"headphones"}
  }
}
```

---

## 5. Which 18 of the 36 DET are converted

From the 36 DETERMINISTIC hard tasks, these 18 become multi-turn (the rest stay
as plain DET):
`hard__swiggy__005`, `hard__swiggy__007`, `hard__makemytrip__003`,
`hard__prime-video__005`, `hard__bookmyshow__003`, `hard__bookmyshow__005`,
`hard__amazon-shopping__006`, `hard__msn-news__007`, `hard__music-obsidian__077`,
`hard__youtube-settings__052`, `hard__google-sheets-amazon-shopping__074`,
`hard__telegram-calendar__016`, `hard__google-meet-files__070`,
`hard__settings-obsidian__044`, `hard__gmail-notes__045`,
`hard__gmail-calendar__003`, `hard__clock-calendar__023`,
`hard__google-search-notes__019`.

## 6. Vars / seeds needed

- New placeholders: `[product]`, `[product_1]`, `[product_2]`, `[restaurant]`,
  `[movie]`, `[cinema]`, `[show]`, `[topic]`, `[channel]`, `[music_type]`,
  `[spreadsheet_name]`, `[sheet_column]`, `[airline_1]`, `[airline_2]`,
  `[city]`, `[place]`, `[contact]` — pinned in `day_N.env`/`user.yaml` with the
  **current** on-device value (see `docs/task-authoring/occasional-apps.md` §6).
- Seeds: Obsidian notes already exist (Stock Watch, Budget Deadline, Exam
  Scores, Contact Updates, Photo Log, Bedtime). New notes to add where missing:
  **Screen Time Goal** (task 16), **Products I'm Considering** (task 18).
  Spreadsheet **SPORTS_VIDEO_DATA** (task 12) already pinned in `user.yaml`.
  `gmail-calendar__003` (task 15) needs a flight-confirmation email in Gmail;
  `clock-calendar__023` (task 17) needs the weekly calendar populated.

## 7. Rollout (after review)

1. Confirm the 18 tasks + KB profiles in this doc.
2. Write the two KB files (`multiturn_kb_public.json`, `multiturn_kb_530.json`).
3. Reword the 18 prompts in `tasks_530.md`/`public.md` to the vague versions
   above; tag them as multi-turn (ahi = MULTI_TURN or keep DETERMINISTIC + a
   `multiturn_kb` pointer).
4. `uv run python scripts/export_530_dataset.py --verify`.
5. Wire `--ask-user-kb` into the batch runner for these tasks.
6. On-device solvability pass + live-data refresh (🔴 items) per task.
7. Run, G-Eval, metrics (turn count), commit.
