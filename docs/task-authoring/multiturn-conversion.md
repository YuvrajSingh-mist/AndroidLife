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

## 3. The 18 tasks (DET → multi-turn), with complete KBs

> **Live-data flag 🔴:** entries that reflect real-time app state and MUST be
> re-confirmed on-device immediately before the run (orders, delivery status,
> today's news). Everything else (notes, contacts, calendar) is seeded/static.

### 1. `hard__swiggy__005` — reorder my last order (day 12)
**Prompt (vague):** "I want the same thing I ordered last Friday. Get it again for me."
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
**Prompt (vague):** "Order my usual from my go-to place — the same items as last time. Don't place it, just show me the payment page."
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
**Prompt (vague):** "I've picked a flight but want to see the fare before paying. Pull it up and show me the payment page with the breakdown."
Agent must ask: *which route? which airline?* → BBI→DEL, the cheaper of the two.
```json
{
  "correct_target": "makemytrip::bbi-del-indigo",
  "profile": {
    "trips": {
      "bbi_del": [
        {"airline":"IndiGo","flight":"6E 2031","depart":"BBI 07:10","arrive":"DEL 09:20","fare":"₹4,850"},
        {"airline":"Air India","flight":"AI 723","depart":"BBI 16:40","arrive":"DEL 19:05","fare":"₹5,390"}
      ],
      "bbi_bom": [
        {"airline":"IndiGo","flight":"6E 501","depart":"BBI 09:00","arrive":"BOM 11:15","fare":"₹5,100"}
      ]
    },
    "preferences": {"next_trip":"BBI to DEL next week"}
  }
}
```
🔴 Re-verify live fares/routes; keep both airlines on the route.

### 4. `hard__prime-video__005` — [show] leaving soon (day 12)
**Prompt (vague):** "I heard something I watch is leaving soon. Check if it's still there and save it to my Watchlist."
Agent must ask: *which show?* → the one leaving (Reacher).
```json
{
  "correct_target": "prime-video::reacher",
  "profile": {
    "watchlist": [
      {"title":"Reacher","leaving":"2026-08-31","available":true,"downloadable":true},
      {"title":"The Boys","leaving":null,"available":true,"downloadable":true},
      {"title":"The Office","leaving":null,"available":true,"downloadable":false}
    ]
  }
}
```
🔴 Re-verify which title shows a "leaving soon" badge in the app.

### 5. `hard__bookmyshow__003` — surprise-party movie booking (day 12)
**Prompt (vague):** "My friends are throwing a surprise party for a close friend. Book movie tickets he'd like — get his details from my contacts, find a fitting movie, and take me to booking. Don't buy."
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
**Prompt (vague):** "I'm planning a movie night for a few people. Check showtimes and seat prices, and save the best option."
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
**Prompt (vague):** "I'm about to buy something but want to confirm the total first. Add it and take me to the payment page showing the final amount. Don't complete it."
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
**Prompt (vague):** "I follow a topic closely. Find today's biggest story on it, summarize it, and send it to my contact."
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

### 9. `hard__settings-notes__081` — battery saver on (day 8)
**Prompt (vague):** "My battery's draining fast. Turn on the setting that helps, and check the note to confirm which mode I should use."
Agent must ask: *which note? which mode?* → Battery note → Battery Saver.
```json
{
  "correct_target": "settings::battery-saver-on",
  "profile": {
    "notes": {
      "Battery": {"suggested_mode":"Battery Saver","target_charge":"below 30%"},
      "Screen Time": {"goal_hours":2}
    }
  }
}
```
*(Note: existing `hard__settings-notes__081`/`082` — check current seed for the actual note title; if only one note exists, fold into a single target.)*

### 10. `hard__telegram-calendar__016` — date mentioned in group chat (day 9)
**Prompt (vague):** "I think a date was mentioned in a group chat. Check recent messages, and if there's a date, set a reminder for it."
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

### 11. `hard__contacts-gmail__026` — contacts missing a phone (day 7)
**Prompt (vague):** "I want to clean up my contacts. Find the ones missing a number and let me know."
Agent must ask: *which ones?* → the two contacts with no phone.
```json
{
  "correct_target": "contacts::missing-phone",
  "profile": {
    "contacts": [
      {"name":"Aaditya","phone":null,"has_email":true},
      {"name":"Mousi Maa","phone":"+918541806133","has_email":false},
      {"name":"Nanimaa","phone":"+917781089901","has_email":false},
      {"name":"Anannya Mishra","phone":null,"has_email":true}
    ]
  }
}
```
🔴 Verify current contact list on device.

### 12. `hard__contacts-notes__027` — rent collection day (day 4)
**Prompt (vague):** "Rent collection day. My notes list who owes what — check and tell me who's paid."
Agent must ask: *which note? which tenant?* → Rent Dues note → the tenant who hasn't paid.
```json
{
  "correct_target": "contacts-notes::rent-dues",
  "profile": {
    "notes": {
      "Rent Dues": [
        {"tenant":"Rahul Verma","amount":"₹15,000","paid":true},
        {"tenant":"Sneha Kapoor","amount":"₹12,000","paid":false}
      ]
    }
  }
}
```

### 13. `hard__google-meet-files__070` — meeting agenda ready (day 14)
**Prompt (vague):** "I'm hosting a meeting soon and want the agenda ready. Pull up the next one and prep the doc."
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

### 14. `hard__notes-files__030` — sync shopping list with receipts (day 10)
**Prompt (vague):** "Sync my shopping list with what I already bought. Check the list against the receipt and note what's left."
Agent must ask: *which list? which receipt?* → the To-Buy list + the grocery receipt.
```json
{
  "correct_target": "notes-files::shopping-sync",
  "profile": {
    "notes": {"To Buy":["Rice 5kg","Milk","Eggs","Detergent"]},
    "files": {
      "receipt_grocery_2026_08_15.pdf": {"items":["Milk","Eggs"],"total":"₹320"}
    }
  }
}
```

### 15. `hard__chrome-files-obsidian__031` — download without overwriting (day 10)
**Prompt (vague):** "I'm downloading a file and don't want to overwrite anything. Download it and make sure the old one is safe."
Agent must ask: *which file? which destination?* → the report PDF → Obsidian/Downloads.
```json
{
  "correct_target": "chrome-files::download-report",
  "profile": {
    "downloads": [
      {"name":"Q3_Report.pdf","existing":true,"note_in":"Obsidian","folder":"Downloads"},
      {"name":"Budget.xlsx","existing":true,"note_in":null,"folder":"Drive"}
    ],
    "preferences": {"download_file":"Q3_Report.pdf"}
  }
}
```

### 16. `hard__settings-obsidian__044` — today's screen time (day 10)
**Prompt (vague):** "I think I've been on my phone too much. Check today's usage and compare it to my goal."
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

### 17. `hard__obsidian-calendar__067` — pin an important note (day 22)
**Prompt (vague):** "I don't want to forget an important note. Pin it so it stays on top, and set a reminder too."
Agent must ask: *which note?* → the one with the upcoming deadline.
```json
{
  "correct_target": "obsidian-calendar::pin-deadline-note",
  "profile": {
    "notes": [
      {"title":"Budget Deadline","deadline":"2026-08-10","pinned":false,"important":true},
      {"title":"Research Notes","deadline":null,"pinned":false,"important":false},
      {"title":"Internship Application","deadline":"2026-08-25","pinned":false,"important":true}
    ]
  }
}
```

### 18. `hard__google-search-notes__019` — product comparison (day 3)
**Prompt (vague):** "I'm torn between two things. Search for an overall review and note which is better for me."
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

## 4. Which 18 of the 36 DET are converted

From the 36 DETERMINISTIC hard tasks, these 18 become multi-turn (the rest stay
as plain DET):
`hard__swiggy__005`, `hard__swiggy__007`, `hard__makemytrip__003`,
`hard__prime-video__005`, `hard__bookmyshow__003`, `hard__bookmyshow__005`,
`hard__amazon-shopping__006`, `hard__msn-news__007`, `hard__settings-notes__081`,
`hard__telegram-calendar__016`, `hard__contacts-gmail__026`,
`hard__contacts-notes__027`, `hard__google-meet-files__070`, `hard__notes-files__030`,
`hard__chrome-files-obsidian__031`, `hard__settings-obsidian__044`,
`hard__obsidian-calendar__067`, `hard__google-search-notes__019`.

(Day-1/2-only DET tasks like `hard__google-maps-notes__005`,
`hard__music-obsidian__077` stay as DET — they're already specific enough or
fall in the locked days 1–4.)

## 5. Vars / seeds needed

- New placeholders: `[product]`, `[product_1]`, `[product_2]`, `[restaurant]`,
  `[movie]`, `[cinema]`, `[show]`, `[topic]`, `[airline_1]`, `[airline_2]`,
  `[city]`, `[place]`, `[contact]` — pinned in `day_N.env`/`user.yaml` with the
  **current** on-device value (see `docs/task-authoring/occasional-apps.md` §6).
- Seeds: the Obsidian notes above already exist (Stock Watch, Budget Deadline,
  Exam Scores, Contact Updates, Photo Log, Bedtime). Add the new notes referenced
  in tasks 9/12/14/15/16/17/18 to `seed_data.py` where missing.

## 6. Rollout (after review)

1. Confirm the 18 tasks + KB profiles in this doc.
2. Write the two KB files (`multiturn_kb_public.json`, `multiturn_kb_530.json`).
3. Reword the 18 prompts in `tasks_530.md`/`public.md` to the vague versions
   above; tag them as multi-turn (ahi = MULTI_TURN or keep DETERMINISTIC + a
   `multiturn_kb` pointer).
4. `uv run python scripts/export_530_dataset.py --verify`.
5. Wire `--ask-user-kb` into the batch runner for these tasks.
6. On-device solvability pass + live-data refresh (🔴 items) per task.
7. Run, G-Eval, metrics (turn count), commit.
