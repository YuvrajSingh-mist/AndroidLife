# Occasional-App Task Expansion — Design + Authoring Draft (days 6–28)

> **Status: DRAFT for review.** Not yet applied to `tasks_530.md`. After review,
> tasks land in `benchmarks/dailyBench-600/tasks_530.md` (day 6+ only; days 1–4
> locked, day 5 in-flight), then `scripts/export_530_dataset.py` regenerates the
> JSON/.jsonl, per-app vars get pinned in `tasks_vars/day_N.env`, seeds get added
> to `scripts/seeding/seed_data.py`, and each task passes an **on-device
> solvability pass** before it counts.

## 1. Design principles

1. **Daily-user realism is the priority.** The benchmark runs tasks live on a
   real phone; success = *getting it done*, not matching a fixed ground truth.
   Live data (news, flights, movies, order status) is fine — grade on "did the
   agent report/complete a valid real option", not exact-match.
2. **Difficulty spread across every app** (E/M/H) — daily users do quick lookups
   most days and multi-step workflows occasionally.
3. **Non-negotiable:** on-device solvability verification before a task counts
   (the day-5 lesson). This is *not* the same as deterministic grading — it only
   ensures the task is actually doable in the app UI on this phone.
4. **Cross-app composites** force multi-app reasoning (agent must switch apps).
   Two flavors, both already in the corpus:
   - **Info→comm chains** (research → summarize → send/save).
   - **Unrelated multi-intent composites** (~20% of cross-app): two *independent*
     actions bundled in one real-user request, each with its own verifiable
     end-state (e.g. "rank next week's meetings **and** message [contact] the
     longest one's time").

## 2. Safety rules (payment / purchase)

- ✅ Tasks **may** navigate to the checkout/payment page, confirm it's
  reachable, and report the total / options shown.
- ❌ Tasks **never** complete a purchase, place an order, or require buying
  anything.
- ❌ No task wording asks the agent to actually pay, confirm payment, or enter
  card details.
- Every "payment page" task ends at: *"…take me to the payment page, but don't
  buy anything"* — the verifiable end-state is reaching the page (or the last
  step before confirmation), not completing a transaction.

## 3. Target distribution (current → target, incl. existing tasks)

| App | E | M | H | Total | Notes |
|---|---|---|---|---|---|
| MSN News ⬆️ | 5 | 2 | 1 | **8** | most-increased; headline, topic, summary, composite news→message |
| Swiggy | 2 | 3 | 2 | **7** | order tracking / live ETA / reorder (user really orders), menu rank, payment page |
| Amazon Shopping | 3 | 3 | 1 | **7** | price, wishlist, compare, track package, checkout page |
| Prime Video | 4 | 2 | 1 | **7** | watchlist count, is-X-downloadable, continue-watching, search+summary |
| BookMyShow | 2 | 1 | 2 | **5** | movies at [cinema], showtimes, **surprise-party composite**, booking page |
| MakeMyTrip | 1 | 2 | 1 | **4** | cheapest flight, compare 2, flight payment page |
| **Total** | **17** | **13** | **8** | **38** | 10 existing + 28 new (was 10 total) |

Replacement source pools (days 6–28 only): the most repetitive single-app slots —
Calendar (22), Google Drive (22), Photos (21), Chrome (19), Files
(21), Settings (16), Clock (19) — swap ~1–2 per day, keeping every day at ≤11
distinct apps and the corpus exactly 530 tasks.

## 4. New tasks, day-by-day

> Task-id numbering continues each app's existing sequence. `[bracket]` = var
> pinned in `tasks_vars/day_N.env`. **● live** = live data, loose grading.
> **✓ seeded** = seedable on-device state, tight grading. **◆ composite**.

### Day 6
- **`easy__swiggy__003`** (E, ●) — I'm starving and my food's been a while. Can
  you open Swiggy and tell me the delivery status of my most recent order?
- **`medium__swiggy__004`** (M, ●) — My order is taking forever. Open Swiggy,
  check the ETA on my active order, and if it's running more than 15 minutes
  late, message the delivery driver with the new ETA. Otherwise just tell me the ETA.

### Day 7
- **`medium__prime-video__003`** (M, ✓) — I want to pick up where I left off.
  Open Prime Video, find what's in my "Continue Watching", and give me a quick
  summary of the most recent one.
- **`easy__prime-video__004`** (E, ✓) — I've been saving shows and lost track.
  Open Prime Video and tell me how many titles are in my Watchlist.

### Day 8
- **`easy__amazon-shopping__003`** (E, ✓) — I'm comparing prices before I pull
  the trigger. Open Amazon Shopping and check the price of '[product]'.
- **`medium__amazon-shopping__004`** (M, ✓) — I can't decide between two things.
  Open Amazon Shopping, compare '[product_1]' and '[product_2]', and tell me
  which is cheaper and by how much.

### Day 9
- **`easy__msn-news__003`** (E, ●) — I want to know what's big in [topic] right
  now. Open MSN News and read me the headline of the top story in the '[topic]'
  section.
- **`medium__msn-news__004`** (M, ●) — I've been out of the loop on [topic].
  Open MSN News, skim the top three stories on it, and give me a one-line
  takeaway from each.

### Day 10
- **`hard__swiggy__005`** (H, ●, ◆) — I want the same thing I ordered last
  Friday. Open Swiggy, find my most recent order from that day, reorder it, then
  message [contact] to say it's on the way. (Don't complete payment — stop at
  the payment page.)

### Day 11
- **`medium__makemytrip__002`** (M, ●) — I'm planning a trip and don't want to
  overpay. Open MakeMyTrip, compare [airline_1] and [airline_2] flight options
  from [city] to [place] for next week, and tell me which is cheaper and the time
  difference.

### Day 12
- **`medium__bookmyshow__002`** (M, ●) — I'm free tonight and want to catch a
  movie. Open BookMyShow and tell me the show timings for [movie] at the nearest
  cinema.

### Day 13
- **`hard__prime-video__005`** (H, ✓, ◆) — I heard [show] is leaving soon. Open
  Prime Video, search for it, check whether it's still available and can be
  downloaded, and add it to my Watchlist so I don't lose it.

### Day 14
- **`medium__amazon-shopping__005`** (M, ✓) — I want to know if the price
  dropped before I buy. Open Amazon Shopping, check the price of the '[product]'
  in my Wishlist, and if it's cheaper than [price threshold], message [contact]
  to say I'm buying it.

### Day 15
- **`medium__msn-news__005`** (M, ●, ◆) — I've been offline all morning. Open
  MSN News, summarize the top three stories of the day, and message the summary
  to [contact] on [comm app].

### Day 16
- **`medium__swiggy__006`** (M, ●) — I'm ordering from a new place. Open Swiggy,
  find [restaurant]'s menu, rank the top 3 dishes by rating, and tell me the
  price of the best one.

### Day 17
- **`hard__bookmyshow__003`** (H, ●, ◆) — **Surprise-party composite.** My
  friends are throwing a surprise party for a close friend. Can you book movie
  tickets he'd like? Get his details and what he's into from his contact info,
  then search for a movie that fits and take me to the booking page (don't buy
  anything).

### Day 18
- **`easy__msn-news__006`** (E, ●) — I haven't caught up on the news today. Open
  MSN News and tell me today's top headline.
- **`hard__msn-news__007`** (H, ●, ◆) — I follow [topic] closely. Open MSN News,
  find today's biggest story on it, summarize it, and send the summary to
  [contact] on Telegram.

### Day 19
- **`easy__prime-video__006`** (E, ✓) — I'm about to fly and won't have signal.
  Open Prime Video and check whether [show] is available to download for offline
  viewing.

### Day 20
- **`hard__amazon-shopping__006`** (H, ✓, ◆) — I'm ready to buy '[product]' but
  want to confirm the total before I commit. Open Amazon Shopping, add it to
  cart, and take me to the payment page showing the final total — don't complete
  the purchase.

### Day 21
- **`hard__swiggy__007`** (H, ●, ◆) — I want to reorder my usual from
  [restaurant] with the same items as my last order. Open Swiggy, rebuild that
  order, and take me to the payment page to confirm — don't place the order.

### Day 22
- **`easy__msn-news__008`** (E, ●) — What's the [topic]-related news today? Open
  MSN News and tell me the top headline in the [topic] section.

### Day 23
- **`medium__amazon-shopping__007`** (M, ✓) — My package is late. Open Amazon
  Shopping, check the tracking on my most recent order, and if delivery is
  delayed, message [contact] the new estimated date.

### Day 24
- **`hard__makemytrip__003`** (H, ●, ◆) — I've picked my flight but want to see
  the breakdown before paying. Open MakeMyTrip, pull up the cheapest [airline_1]
  or [airline_2] flight from [city] to [place] next week, and take me to the
  payment page showing the fare breakdown — don't book.

### Day 25
- **`medium__prime-video__007`** (M, ✓, ◆) — I want to start a new show. Open
  Prime Video, search for [show], check if it's included with my subscription or
  needs rent/buy, and save it to my Watchlist.

### Day 26
- **`easy__bookmyshow__004`** (E, ●) — I'm free tonight and want to catch a
  movie nearby. Open BookMyShow and tell me which movies are playing at the
  nearest cinema.

### Day 27
- **`medium__makemytrip__004`** (M, ●, ◆) — I'm comparing two trips. Open
  MakeMyTrip, check the cheapest [airline_1] and [airline_2] flights from [city]
  to [place_1] and [place_2] for next week, and note which is cheaper in a note
  for me.

### Day 28
- **`hard__bookmyshow__005`** (H, ●, ◆) — I'm planning a movie night for a
  group. Open BookMyShow, find [movie]'s showtimes at [cinema], check the
  seat prices for a group of [group size], and save the best option to a note.

## 5. Cross-app composites (unrelated multi-intent) in this set

The "polar-opposite / unrelated subtask" flavor the spec already documents
(~20% of cross-app). Examples in this expansion:

- **Day 17 `hard__bookmyshow__003`** — subtask A: pull friend's deets + interests
  from Contacts; subtask B: search + reach movie booking page. Independent
  end-states (contact info retrieved **and** booking page reached).
- **Day 18 `hard__msn-news__007`** — subtask A: find + summarize today's story;
  subtask B: message [contact]. Independent.
- **Day 10 `hard__swiggy__005`** — subtask A: reorder; subtask B: notify
  [contact]. Independent.

## 6. Vars / seeds needed (per new task)

> **Nothing is hardcoded.** Every entity that could be absent or change
> on-device (products, shows, movies, restaurants, news topics, airlines,
> airports, cinemas, thresholds) is a **placeholder** pinned in
> `tasks_vars/day_N.env` + `config/user.yaml`. The pinned value is always the
> **latest confirmed on-device state at seed time** — so a task can never
> false-fail as a hallucination just because a stale hardcoded name no longer
> exists. If the current device state changes, the placeholder value is updated,
> never the task text.

Placeholders to pin in `tasks_vars/day_N.env` + `config/user.yaml` (value = the
**current** on-device entity, verified before each run):

| var | value (example — always resync to current device state) | used by |
|---|---|---|
| `[product]` | a seeded Amazon Wishlist item (e.g. Noise wireless earbuds) | amazon 003, 005, 006 |
| `[product_1]`, `[product_2]` | two seeded Wishlist items | amazon 004 |
| `[restaurant]` | a real, active Swiggy restaurant | swiggy 006, 007 |
| `[movie]` | a movie currently showing | bookmyshow 002, 005 |
| `[show]` | a real Prime Video title | prime-video 005, 006, 007 |
| `[topic]` | a live MSN News section (cricket, economy, weather…) | msn 003, 004, 007, 008 |
| `[airline_1]`, `[airline_2]` | two airlines that fly the route | makemytrip 002, 003, 004 |
| `[city]`, `[place]`, `[place_1]`, `[place_2]` | real nearby airports | makemytrip 002–004 |
| `[cinema]` | a real cinema near the device | bookmyshow 005 |
| `[price threshold]` | fixed number | amazon 005 |
| `[group size]` | fixed number | bookmyshow 005 |
| `[comm app]` | Telegram (primary comm app) | msn 005, 007 |

Seed additions to `scripts/seeding/seed_data.py`:
- Amazon Wishlist with the current `[product]` items (for amazon 003–006).
- Swiggy: no seed (user's real order history is the live state) — solvability
  pass must confirm a recent order exists and the named `[restaurant]` is active.
- Prime Video Watchlist with the current `[show]` titles.
- Contacts: friend card with an interests/notes field (for the surprise-party
  composite).

## 7. Per-task solvability verification checklist

Before any new task counts in a run (day-5 lesson), verify on-device that:
0. **Placeholder values are the CURRENT device state.** Each `[var]` in the task
   text is resolved from `day_N.env`/`user.yaml`, and that resolved value is
   confirmed to exist on-device right now (restaurant is active, movie is
   showing, product is in the Wishlist, show is on Prime Video, airline flies
   the route, news section exists). If it doesn't exist, update the **placeholder
   value** — never the task text — so the task stays solvable and never becomes
   an accidental hallucination task.
1. The app is installed and logged in.
2. The target screen (order, wishlist, watchlist, menu, showtimes, payment page)
   is reachable in the UI and exposes the asked value/state via accessibility.
3. Live-data tasks report *a valid real option* at run time (loose grading), and
   the grader knows the exact phrasing to look for.
4. No task depends on a permission/account the benchmark setup doesn't provide.

## 8. Rollout order (after review)

1. Confirm scope/count in this doc.
2. Land tasks in `tasks_530.md` (days 6–28), keeping corpus at exactly 530.
3. `uv run python scripts/export_530_dataset.py --verify` (expect 530 / 216 / 242
   / 72, 36/36 AU, HC count unchanged for these apps — no new HC).
4. Pin new vars in `tasks_vars/day_N.env` + `config/user.yaml`.
5. Add seeds to `seed_data.py`; run the day seed.
6. On-device solvability pass per task (checklist §7).
7. Rerun affected days on qwen3.6-plus; G-Eval + metrics; update reports.
8. Commit + push.
