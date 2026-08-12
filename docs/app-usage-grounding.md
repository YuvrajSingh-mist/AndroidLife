# Grounding the schedule in real app-usage data

Every DrainBench day is meant to look like an **ordinary person's real phone use**. So the number of apps a benchmark day asks the agent to touch should be anchored to how many apps a real person actually touches in a day. This document records that baseline, with citable sources, and explains the design choice it drives. Verified 2026-08-03.

## The real-world baseline

> The average smartphone user has **~80 apps installed but uses only ~9-10 per day and ~30 per month**, according to data.ai's (formerly App Annie) annual *State of Mobile* report.

That headline figure is consistent across the independent sources below:

| Figure | Source | Link |
|---|---|---|
| ~80 installed; **9-10 used/day**, ~30/month | data.ai (App Annie), *State of Mobile* (primary) | https://www.data.ai/en/insights/market-data/state-of-mobile-2023/ |
| "80 apps installed but uses only 9-10 per day and 30 per month" (cites data.ai State of Mobile) | getfaithlock, *App Addiction Statistics* (2026) | https://www.getfaithlock.com/resources/app-addiction-statistics |
| "average smartphone owner uses **10 apps per day and 30 per month**" | BuildFire, *Mobile App Download & Usage Statistics* (Jul 2026) | https://buildfire.com/app-statistics/ |
| "Users open mobile apps **9.5 times per day** on average" (2024); 4h39m/day in apps | GitNux, *App Usage Statistics* (2026, fact-checked) | https://gitnux.org/app-usage-statistics/ |
| "opens roughly **10 apps daily**, out of about **34 apps used per month**" | getpanto.ai, *Mobile App Usage Statistics* (2026) | https://www.getpanto.ai/blog/mobile-app-usage-statistics |

**Supporting context:**
- Roughly **90% of mobile time is spent inside apps** rather than mobile browsers (eMarketer, cited at https://www.getfaithlock.com/resources/app-addiction-statistics).
- A small handful of apps (roughly 5-6) captures most of a user's daily attention (https://www.getfaithlock.com/resources/app-addiction-statistics).
- People check their phones ~58 times/day and spend ~4h37m/day on them (Exploding Topics, *Time Spent Using Smartphones*, 2026: https://explodingtopics.com/blog/smartphone-usage-stats).

### Precision caveat
The published figures are **averages across users, not strict medians**. Because heavy users skew averages upward, the true **median is likely at or below ~9 apps/day**. Citing "**~9-10 apps/day**" as the *typical* value is therefore a safe, conservative claim.

## What this drives in the benchmark

The schedule should not make a simulated day denser than reality. Three candidate designs, measured by **distinct apps present per day**:

| Design | Apps/day | vs. real ~9-10 |
|---|---|---|
| Original 21-day draft (30 tasks/day) | 17-18 | ~80-100% above |
| First 28-day draft (630 tasks, decoupled) | 12-15 | ~35-50% above |
| 630-task superset, co-located | 11-12 | ~15-25% above |
| **Final runnable design (530-task corpus)** | **~10.8 (10-12)** | **~10% above** |

### Why the superset floor is 11-12 at 630 tasks, and how 530 lands at reality

DrainBench's full corpus is **530 runnable tasks over 28 days across 32 apps** (216 easy + 242 medium + 72 hard). Realistically an app contributes **at most 2 tasks on any day** (one easy + one medium). Therefore each app must be active on at least 15 of 28 days, giving:

- total app-days ≥ 32 × 15 = 480
- apps/day ≥ 480 / 28 ≈ **17.1** (before the cross-app/notes-sharing relaxation)

So 11-12 apps/day is the mathematical minimum for the 630-task superset. The **runnable schedule lands at ~10.8 distinct apps/day (min 10, max 12) and ~18.9 tasks/day (15-22)** — close to the real ~9-10 baseline, while preserving the easy/medium/hard split (216/242/72), the 50/50 ASK USER / DETERMINISTIC hard split (36/36), the cross-app share (178 of 530), and all 32 apps. (The note-taking load is shared between Notes, Obsidian and Google Docs, so the three together occupy the app-days a single note app would; the 6 apps added on 2026-08-12 — Swiggy, Prime Video, MakeMyTrip, BookMyShow, MSN News, Amazon Shopping — appear as occasional 1-2 task guests rather than daily fixtures, which is why density barely moved.)

### Design consequence
To land at the target density, each app's tasks are selected **round-robin across its active days** (fewest-kept-so-far wins, deterministic tie-breaks), so every app keeps a spread of active days across the month rather than clustering early, and is **entirely absent the rest**. That keeps per-day density realistic (~19-20 tasks across ~11 apps) while still preventing an agent from camping on any one app's screen across the whole run.

## Two different numbers: penetration ≠ time-share (2026-08-12)

People often conflate two distinct published statistics; they drive *different* parts of the benchmark, so it matters to keep them apart:

| Stat | What it measures | Example | What it drives in the benchmark |
|---|---|---|---|
| **Category penetration** | Share of users who have **at least one app in the category installed** | Communication **99.39%**, Tools **99.81%**, Social Media **95.02%**, Shopping **35.79%** (Statista 200855, 2019 vintage) | **App *selection*** — which apps are plausible on an ordinary everyday device |
| **Time-share** | Share of **time spent in apps** that goes to the category | Social media **35.1%** of app time (Statista 1465726, 2024) | **NOT task weighting** — deliberately not mirrored (see below) |
| **Daily-active-app count** | How many distinct apps a person actually opens in a day | **~9-10 apps/day**, ~30/month (data.ai *State of Mobile*) | **Per-day density** — how many distinct apps appear on a benchmark day |

**Penetration is an install/availability stat, not a usage-time stat.** "Communication 99.39%" means ~99.4% of Android users have at least one communication app installed — *not* that people spend 99.4% of their phone time communicating. "Social media 35.1%" is time-share: on average, ~a third of every hour in apps is spent in social apps. They answer different questions and are never directly comparable.

## What actually fills a person's daily ~9-10 apps — sector composition (research, 2026-08-12)

The density figure (~9-10 apps/day) tells us **how many** apps a person touches, but
not **which sectors** those daily apps belong to. That matters for the benchmark
because it is the closest published proxy we have for "what does an ordinary day
of phone use actually consist of?" The honest answer: **no single public dataset
breaks down the daily-active-app *mix* by sector** (data.ai publishes total app
*time* by category, not "the 9 apps I opened today, by category"). But three
independent, citable signals converge on the same shape:

**1. Time-share by category — what people spend their app time on (dominated by a few sectors).**
Statista's "Share of time spent using mobile apps worldwide 2024, by category"
(stat 1465726, Android only, released Feb 2025) is the canonical category-level
time figure. Its headline: **social media ≈ 35.1%** of all app time — the single
largest category — followed by the **video/entertainment** and **messaging/
communication** cluster. Supporting, independent figures:
- Social media apps ≈ **2 h 31 m/day** globally — the largest single category
  (DataReportal *Digital 2024* / GWI, cited at getfaithlock.com/resources/app-addiction-statistics).
- TikTok ≈ **95 min/day** and YouTube ≈ **74 min/day** per user — the two
  most time-consuming apps (data.ai *State of Mobile 2023*).
- **~4 h 37 m/day** total in apps (data.ai), of which **~90%** of mobile time is
  in apps vs. mobile web (eMarketer).

**2. "Essential / can't-live-without" daily apps — the concrete daily handful.**
Statista's US "apps people can't do without" and the BuildFire roundup both name
the same short list as the *daily* core: **social (Facebook/Instagram), instant
messaging (WhatsApp/Messenger), email (Gmail), video (YouTube), navigation
(Maps), browsing (Chrome), and shopping (Amazon)**. These are overwhelmingly
**Communication + Media/Entertainment + a couple of utility/tool apps** — exactly
the sectors that appear every day, while office/weather/books/finance apps are
the "open occasionally" tail.

**3. Category penetration — what's installed on nearly every phone (near-daily by default).**
Statista 200855 (2019, the newest public release of this series): Communication
**99.39%**, Tools **99.81%**, Business **99.33%**, Video Players **96.63%**,
Travel & Local **95.70%**, Social Media **95.02%**, Productivity **91.67%**,
Music & Audio **88.38%**, Entertainment **83.85%**, News **81.11%**, Photography
**75.77%**, Books **70.74%**, Shopping **35.79%**, Weather **32.46%**. Categories
with ~90-100% penetration (communication, tools, video, social, productivity)
are the ones present on essentially every phone and thus in most daily mixes;
low-penetration ones (shopping, weather) are genuinely *occasional*.

**What this means for the benchmark's per-day composition (and our honest caveat):**
- ⚠️ **This next claim is an inference, not a measured statistic.** No source has
  published the *sector breakdown of the actual ~9-10 apps a person opens in a
  day*. What we *infer* from time-share + penetration + essential-app lists:
  real daily app time is dominated by **social + video/entertainment + messaging**
  (passive-consumption categories, per time-share), with **communication and
  tools** as the ever-present structural core (per ~99-100% penetration) and
  **productivity/docs/weather/shopping** as the occasional tail (lower
  penetration / infrequent use). In short: "communication + media/entertainment
  dominate; tools are the always-on core; productivity/docs/weather/shopping are
  occasional" is a **reasonable synthesis of three proxies — not a directly
  measured "daily mix by sector"**.
- DrainBench cannot mirror that time-share (social/video/gaming are excluded for
  ToS + ungradeable-passive-consumption reasons — see the next section). What it
  **does** preserve is the *shape*: a small ever-present communication/tool core
  (Chrome 22/28 days, Telegram 19/28, Notes 19/28), a rotating set of
  productivity/media apps that appear roughly every other day, and the new
  occasional real-world guests (Swiggy/Prime/MakeMyTrip/BookMyShow/MSN News/
  Amazon Shopping 1/28) — matching the "small daily handful + long occasional
  tail" structure the sources describe.
- **Data-availability caveat (2026-08-12):** no public source breaks down the
  *daily-active mix* (the ~9-10 apps opened today) by sector; the closest
  published numbers are category time-share (stat 1465726) and penetration
  (stat 200855). The benchmark therefore grounds **density** on the daily-active
  count and grounds **app selection** on penetration + time-share, and is
  transparent that the *daily sector mix itself* is approximated from these two
  proxies rather than measured directly.

## Why the task mix is NOT proportional to real time-share (design, not accident)

If the corpus were weighted by real time-share, ~35% of tasks would be social media and much of the rest would be gaming/OTT. That is deliberately **not** the case, for four reasons:

1. **ToS / publishability**: social + high-automation-risk apps (Instagram, WhatsApp, TikTok, Zoom) are excluded so runs publish openly (see `benchmark-spec.md` §Scope). A time-share-weighted corpus would be 35% un-automatable.
2. **It is a task-difficulty benchmark, not a usage-simulator.** Tasks are authored around apps with **verifiable, deterministic end-states** (documents, notes, settings, timers, contacts, sheets) so a model's "success" can be checked against real device state. Real top-time categories (gaming, video) are mostly *passive consumption* — there is no crisp "did the agent do it" end-state, so they would produce ungradeable tasks.
3. **Verifiability skews the mix toward productivity/documents** — which is why the corpus over-represents those sectors relative to real time-share (a documented, intentional trade-off, not a flaw).
4. **The hard requirement the corpus *does* preserve is density**: the *number* of distinct apps per day (10-12, avg ~10.8) tracks the real ~9-10 apps/day baseline, because that is the property that makes a day look like a real person's phone.

**What the distribution actually does (measured 2026-08-12 from `DailyBench_530_v1.json`):**

- **Per-day distinct apps**: 10-12, mean **~10.8** (real baseline ~9-10 → ~10% above, the closest the 28-day/32-app corpus can land without dropping density constraints).
- **Every-day apps** (present ≥75% of days): Chrome 22/28 — the one always-on "hub" app (Telegram 19/28 and Notes 19/28 just miss the ≥75% bar; Obsidian 17/28). After the 2026-08-12 rebalance the always-on core is slimmer because 36 note-anchored cross tasks became unrelated multi-intent chains that touch Telegram/Gmail/Phone instead of Notes/Obsidian.
- **Rotating apps** (present ~36-54% of days): Calendar (15/28), Contacts (13), Google Search, Phone, Gmail, Google Maps, Google Photos, Google Drive, Clock (12 each), Gallery, Messages, Files, Music, Settings, Calculator (11 each), Camera, YouTube (10 each) — each appears roughly every other day, round-robin, never every day.
- **Occasional apps** (the newer sets): Google Docs 5/28, Weather 5/28, Sheets 4/28, Meet 4/28, Slides 3/28 — present on a few dedicated days, matching how real people use office + weather apps sporadically rather than daily. The 2026-08-12 diversification pass added single-task guests for the biggest real-world gaps: Swiggy / Prime Video / MakeMyTrip / BookMyShow / MSN News / Amazon Shopping 1/28 each — occasional, like real food/OTT/travel/news apps.
- **Sector touch-share** (app-touches, 733 total): Communication & Messaging 29.2% (214), Media & Entertainment 26.2% (192), Documents & Notes 22.9% (168), Productivity & Tools 20.5% (150), Weather 0.7% (5), Food & Delivery / OTT / Travel / Tickets / News / Shopping 0.1-0.3% each (1), PDF (open+read, in Files/Drive/Gmail) ~0.5% (4+). Compare real **time-share** (social ~35% + video/games): the corpus shifts weight *away from* passive-consumption categories into verifiable productivity ones, exactly as a difficulty benchmark should.
- **Single vs cross-app** (178 of 530 tasks touch >1 app = 33.6%): cross-app rises with difficulty — **0% of easy, 47% of medium, 89% of hard** (100% of DET hard, 78% of ASK USER hard). Cross-app tasks are how the corpus forces multi-app reasoning. **Since 2026-08-12 the mix is ~46% note-anchored / ~34% info→comm action chains / ~20% unrelated multi-intent** (a compound request like "rank my meetings in Calendar and message [contact] the longest one's time" bundles two independent, each-verifiable actions). The cross-app transfer points are now Telegram (58 cross tasks), Notes (47), Obsidian (35), Gmail (33).

**Bottom line:** the *app set* is justified by penetration (apps people actually have), the *per-day density* is justified by daily-active-app count (~9-10/day), and the *task mix* is deliberately *not* time-share-proportional — it's skewed to verifiable end-states for gradeability, with the density constraint as the honest tie to reality.
