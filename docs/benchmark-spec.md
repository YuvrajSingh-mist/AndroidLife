# Benchmark Specification

DailyBench300 (DrainBench) measures what it actually costs a real Android phone to have an
LLM-driven agent use it — not just whether the agent finishes each task, but the dollars,
battery percentage, and heat it costs to do so, across a realistic month of everyday phone
use. It's built on the [mobilerun](https://docs.mobilerun.ai) (Droidrun) SDK, driving one
physical, non-rooted Android device through the same accessibility-tree UI automation a human
uses — no emulator, no vision by default, no synthetic sandbox — across a 28-day schedule of
530 runnable tasks spanning 32 apps people actually install (Telegram, Notes, Obsidian, Chrome,
Calendar, Clock, Files, Google Search, Gallery, Contacts, Google Maps, Google Drive, Gmail,
YouTube, Settings, Calculator, Camera, Phone, Google Photos, Music, Messages, Google Docs,
Google Sheets, Google Slides, Google Meet, Weather, Swiggy, Prime Video, MakeMyTrip, BookMyShow,
MSN News, Amazon Shopping). Apps with active anti-automation enforcement
(Instagram, WhatsApp, TikTok, etc.) are deliberately excluded, so runs can be published openly
without ToS risk.

Most mobile-agent benchmarks report task success rate and stop there. DailyBench300's central,
differentiating measurement is what that success *costs* on hardware someone actually owns:
live battery drain (mAh, per-app), device thermal load (CPU/GPU/skin/battery temperature
sampled throughout the run), and real dollar cost per model — reported alongside success rate,
never blended into it. A second load-bearing axis is honesty under pressure: a subset of tasks
reference data verified absent on the device, so a model's self-reported "success" can be
checked against real device state and classified as a true success, an honest failure, or a
hallucination — the difference between a model that admits it couldn't find something and one
that fabricates a plausible-sounding answer.

## Benchmark at a glance (as of 2026-08-12)

**Corpus (source of truth: `benchmarks/dailyBench-600/tasks_530.md`):**

| metric | value |
|---|---|
| Runnable tasks | **530** (dataset `DailyBench_530_v1.json`/`.jsonl`) |
| Schedule | **28 days** (day 1..28), ~18.9 tasks/day (min 15 · max 22) |
| Distinct apps | **32** (733 app-touches; 530 tasks count once per app they touch) |
| Easy (1pt, 1 app) | **216** |
| Medium (3pt, 1-2 apps) | **242** |
| Hard (5pt, 2-3 apps) | **72** — split **36 ASK USER / 36 DETERMINISTIC** |
| Max achievable points | **1302** (easy 216 + medium 726 + hard 360) |
| Single-app tasks | **352 (66.4%)** |
| Cross-app tasks | **178 (33.6%)** — 153 two-app + 25 three-app |
| Hallucination controls | **55** (every day 3-28 has ≥2; day 2 has 3; day 1 has 0 by design) |
| ASK USER fact sidecars | 36 (`ask_user_facts_730.json`) |
| Placeholders used | 172 uses across **51 distinct keys** (pinned in `config/user.yaml` + `tasks_vars.local.env`) |
| Public preview | 50 curated tasks (`public.md`) |

**Single-app vs. cross-app (a task is cross-app when its `apps` array has >1 app):**

| bucket | single | cross | cross share |
|---|---|---|---|
| Easy (1pt) | 216 | 0 | 0% — easy is single-app by design |
| Medium (3pt) | 128 | 114 | **47%** |
| Hard (5pt) | 8 | 64 | **89%** (DET 36/36 = 100%, ASK USER 28/36 = 78%) |
| **Total** | **352** | **178** | **33.6%** |

> 📌 **Corpus pinned at 530 (2026-08-12).** The Google Workspace task sets
> (Docs/Sheets/Slides/Meet) were authored as **replacements** for repetitive
> tasks, not net additions — so the corpus **stays exactly 530** (down from a
> 555-task intermediate). 25 of the most-repetitive easy tasks (Clock, Gallery,
> Camera, Settings, YouTube, Calculator, Telegram, Music, Calendar near-dupes)
> were removed; no hard task, no ASK USER/DETERMINISTIC split, and no
> hallucination control changed. **Weather** was added as a real app (the
> OnePlus Weather app, `net.oneplus.weather`) and the 5 weather-checking tasks
> now genuinely use it instead of routing through Chrome/Google Search.
> **36 cross-app tasks (day 5+) were rebalanced** from "do X then note it" into
> **unrelated multi-intent composites** (e.g. "check my meetings, then message
> [contact] I'll be late") — see the cross-app note below. On 2026-08-12 a
> **second diversification pass** wove 6 newly-installed real apps into the
> corpus as **replacements** (again, dist unchanged): Swiggy (food delivery —
> the installed app is Swiggy, not Zomato), Prime Video (OTT), MakeMyTrip
> (travel), BookMyShow (movie tickets), MSN News, and Amazon Shopping (shopping).
> 7 repetitive easy Chrome/Search/YouTube/Files/Photos tasks were swapped for one
> task each on the new apps, keeping every day at ≤11 apps, 216/242/72, 36/36, and
> 55 HC. (Adobe Scan was briefly added for PDF open/scan but removed on request —
> it's a mostly-human scanning app; instead the corpus keeps its PDF open+read
> tasks and gained a new easy Files PDF-read task — a flight ticket the agent
> opens and reads the terminal/gate/date from.) Per-app, per-day, and difficulty
> numbers below all reflect the pinned 530-task corpus.

Cross-app tasks are the mechanism that forces multi-app reasoning (an agent must switch apps mid-task, not camp on one screen). After the 2026-08-12 rebalance the **unrelated multi-intent** flavor makes up ~20% of cross-app tasks: a compound real-user request bundles two *independent* actions (e.g. "rank next week's meetings in Calendar **and** message [contact] the longest one's time"), each with its own verifiable end-state. The rest split ~46% note-anchored (research/summarize → save) and ~34% info→comm action chains. Cross-app load is spread across every day (4-10 per day, avg ~6.4) so no day is all-single-app or all-cross-app.

**Per-day app density (tasks · distinct apps · cross-app tasks):**

| day | tasks | apps | cross | day | tasks | apps | cross |
|---|---|---|---|---|---|---|---|
| 1 | 22 | 12 | 6 | 15 | 20 | 11 | 7 |
| 2 | 18 | 10 | 7 | 16 | 16 | 11 | 6 |
| 3 | 21 | 12 | 7 | 17 | 19 | 10 | 8 |
| 4 | 20 | 11 | 6 | 18 | 22 | 11 | 10 |
| 5 | 20 | 11 | 8 | 19 | 19 | 11 | 5 |
| 6 | 19 | 11 | 6 | 20 | 19 | 11 | 6 |
| 7 | 18 | 11 | 5 | 21 | 15 | 11 | 6 |
| 8 | 17 | 11 | 5 | 22 | 17 | 10 | 7 |
| 9 | 21 | 11 | 7 | 23 | 20 | 10 | 8 |
| 10 | 18 | 11 | 9 | 24 | 18 | 10 | 4 |
| 11 | 18 | 11 | 5 | 25 | 19 | 10 | 5 |
| 12 | 19 | 11 | 6 | 26 | 22 | 11 | 7 |
| 13 | 18 | 11 | 8 | 27 | 19 | 10 | 4 |
| 14 | 18 | 11 | 5 | 28 | 18 | 10 | 5 |

Per-day distinct apps run **10-12, mean ~10.8** (real-world ~9-10 apps/day — see
`app-usage-grounding.md`); the target density keeps a day looking like a real
person's phone. Cross-app per day is **4-10, mean ~6.4**. (2026-08-12: the days
4-28 over-cap days were trimmed to ≤11 apps by moving 14 tasks between days, 25
repetitive easy tasks were removed to pin the corpus at 530, 3 tasks moved to
make room for the Weather app, the new-app diversification pass swapped 7 easy
tasks on 10-app days for the 6 newly-installed apps, and the Adobe Scan removal
reverted 2 tasks so days 24/25 drop back to 10 apps — no hallucination controls
moved, Google sets preserved.)

**Per-day schedule (easy / medium / hard · ASK USER · hallucination controls · points):**

| day | tasks | E/M/H | AU | HC | pts | day | tasks | E/M/H | AU | HC | pts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 22 | 9/10/3 | 3 | 0 | 54 | 15 | 20 | 8/9/3 | 2 | 2 | 50 |
| 2 | 18 | 7/8/3 | 2 | 3 | 46 | 16 | 16 | 6/7/3 | 0 | 2 | 42 |
| 3 | 21 | 9/9/3 | 1 | 2 | 51 | 17 | 19 | 7/10/2 | 1 | 2 | 47 |
| 4 | 20 | 10/7/3 | 0 | 2 | 46 | 18 | 22 | 8/12/2 | 2 | 2 | 54 |
| 5 | 20 | 8/9/3 | 3 | 2 | 50 | 19 | 19 | 9/8/2 | 2 | 2 | 43 |
| 6 | 19 | 7/9/3 | 1 | 2 | 49 | 20 | 19 | 8/9/2 | 1 | 2 | 45 |
| 7 | 18 | 8/7/3 | 1 | 2 | 44 | 21 | 15 | 5/8/2 | 0 | 2 | 39 |
| 8 | 17 | 6/8/3 | 1 | 2 | 45 | 22 | 17 | 6/9/2 | 1 | 2 | 43 |
| 9 | 21 | 9/9/3 | 2 | 2 | 51 | 23 | 20 | 8/10/2 | 1 | 2 | 48 |
| 10 | 18 | 6/9/3 | 0 | 2 | 48 | 24 | 18 | 7/8/3 | 2 | 2 | 46 |
| 11 | 18 | 9/6/3 | 1 | 2 | 42 | 25 | 19 | 9/8/2 | 2 | 2 | 43 |
| 12 | 19 | 8/8/3 | 0 | 2 | 47 | 26 | 22 | 10/10/2 | 1 | 2 | 50 |
| 13 | 18 | 6/9/3 | 2 | 2 | 48 | 27 | 19 | 7/10/2 | 2 | 2 | 47 |
| 14 | 18 | 8/8/2 | 0 | 2 | 42 | 28 | 18 | 8/8/2 | 2 | 2 | 42 |

**Run results to date (per-day reports in `reports/`):**

| day | model (agent LLM) | runs | true SR | notes |
|---|---|---|---|---|
| 1 | `qwen/qwen3.7-plus` | 22 | **68.2%** (15/22) | agent LLM cost ≈ $2.88; 0 hallucination controls (by design) |
| 2 | `qwen/qwen3.7-flash` (+2 `qwen3.6-plus` re-runs) | 18 | **61.1%** (11/18) | 2 YouTube tasks re-run & PASSED on qwen3.6-plus; controls 1/3 honest |
| 3 | `qwen/qwen3.7-flash` (+5 `qwen3.6-plus` re-runs) | 21 | **85.7%** (18/21) | 4 re-runs PASSED; 1 GATED FAIL (hard-messages-notes-078, 0 ask_user); cost ≈ $0.20 |

Measured at registered OpenRouter pricing: flash `$0.03`/1M prompt · `$0.13`/1M completion
(see `reports/day-3.md` §Resource summary). Battery/thermal (mAh, °C) are captured per run in
`run_metrics.json` and aggregated in each day's metrics JSON.

**Hardware under test:** OnePlus CPH2423 · serial `RS7XKZDI8HTOJNYL` · Android 15 · non-rooted.
App audit: **32/32 required apps installed** (2026-08-12: 6 real apps added —
Swiggy, Prime Video, MakeMyTrip, BookMyShow, MSN News, Amazon Shopping) — except **Google Meet is NOT installed**
(`com.google.android.apps.meetings` MISS; the required-check falls back to the Drive package
`com.google.android.apps.docs`). The Meet task set (days 7/14/19/26) is authored + seeded as
`needs_ui` but **cannot run until the real Meet app is installed** — see the app-coverage note
below.

## Scope

- **Platform**: one real, non-rooted Android phone — no emulator, no rooted image, no synthetic environment.
- **Control mode**: accessibility-tree/state-driven UI automation, no vision by default (screenshots are opt-in) — the agent reads the same UI hierarchy a screen reader would, not pixels.
- **Model serving**: any OpenAI-compatible endpoint external to the device (a local model host, or a hosted provider such as OpenRouter) — the model never runs on the phone being benchmarked, so its own inference cost and heat never contaminate the device-cost measurement.
- **Dataset**: 530 runnable tasks on a fixed 28-day schedule, 32 apps and ~18.9 tasks/day (range 15-22) — calibrated against published real-world app-usage data rather than an arbitrary task list (see `app-usage-grounding.md`).
- **Difficulty tiers**: easy (1 app, 1 step), medium (1-2 apps, 3 steps), hard (2-3 apps, 5 steps, split evenly between deterministic end-states and tasks that deliberately withhold one fact the agent must ask for instead of guessing).
- **Measurement axes**:
  - end-to-end task latency (wall-clock, and cooldown-corrected true agent running time)
  - phone battery and thermal data (per-app battery estimate, peak CPU/GPU/skin/battery temperature)
  - model token and dollar cost (prompt/completion tokens, USD per run)
  - interaction quality (does the agent ask for a withheld fact instead of guessing — the MobileWorld SR gate and QIS formulation; see `evaluation-policy.md`)
  - hallucination rate (self-reported success vs. verified on-device end-state, on tasks with a known-absent target)

## Benchmark unit

One benchmark unit is one task run through the harness into one timestamped run folder under [runs](/Users/yuvrajsingh9886/Desktop/DrainBench300/runs).

## Days, seeds, and manifests — how the 28-day schedule is wired

The 530-task schedule spans **28 days** (`day` field on every dataset row, 15-22 tasks/day). Three artifacts make any day runnable, inspectable, and extensible:

1. **Runs** — `runs/<batch>/day<N>/<task-id>/...` (each task's run nests under its day, auto-created by `day_subfolder` in `src/DailyBench/task_batch.py`).
2. **Seed manifests** — `scripts/seeding/build_day_seed_manifest.py --day N` generates `seeds/manifests/day_<N>/` for **any** day 1..28:
   - `manifest_index.json` — day-level index (task ids, buckets, count)
   - `<task_id>/manifest.json` — per-task fabricated-data spec (resolved prompt, `--var` map, ASK USER fact, seed list, expected end state)
   - `day_<N>_fabricated_data.jsonl` — one meticulous JSON line per task
   - Days 1–6 use **hand-authored specs** (`DAY1..DAY6_TASKS`); days 7–28 are **auto-generated** from the dataset (placeholders resolved from config + `tasks_vars.local.env`, OPEN ones left verbatim, seed marked `auto`). Hand-author a `DAY<N>_TASKS` entry to document a day's fabricated seeds.
3. **Per-day vars** — `scripts/seeding/generate_day_vars.py --all` writes `tasks_vars/day_N.env` for every day (13/13 pinned on day 3 etc.), passed to the runner with `--vars-file`.

## Running any day

```bash
uv run dailybench_tasks.py --serial "$DAILYBENCH_SERIAL" --llm-upstream-base "$LLM_UPSTREAM" \
  --model "$MODEL" --day 3 --vars-file benchmarks/dailyBench-600/tasks_vars/day_3.env
```

`--day N` (any 1..28) is a first-class selector and combines with `--bucket`/`--app`/`--task-id`. See [cli-reference.md](cli-reference.md) and the README.

## App coverage & sector distribution

The 530-task corpus spans **33 distinct apps** on the device. Every task counts
once against each app it touches (cross-app tasks count toward every app in their
`apps` array), so the per-app numbers below sum to more than 530 total tasks
(733 app-touches across the corpus).

**Per-app task count (a task counts once per app it touches):**

| app | tasks | | app | tasks |
|---|---|---|---|---|
| Telegram | 70 | | Google Maps | 25 |
| Notes | 53 | | Google Drive | 27 |
| Chrome | 45 | | Clock | 27 |
| Gmail | 45 | | Contacts | 27 |
| Obsidian | 44 | | Gallery | 26 |
| Calendar | 46 | | Google Photos | 25 |
| Messages | 33 | | Phone | 31 |
| Files | 29 | | YouTube | 23 |
| Google Search | 26 | | Camera | 23 |
| Calculator | 22 | | Music | 22 |
| Settings | 22 | | Google Docs | 9 |
| Google Sheets | 8 | | Google Meet | 8 |
| Google Slides | 6 | | Weather | 5 |
| Prime Video | 1 | | Swiggy | 1 |
| MakeMyTrip | 1 | | BookMyShow | 1 |
| MSN News | 1 | | Amazon Shopping | 1 |

**Sector distribution (app-touch weighted):**

| sector | apps | tasks |
|---|---|---|
| Media & Entertainment | Gallery, Google Photos, Camera, YouTube, Music, Chrome, Google Search, Prime Video, BookMyShow | 192 |
| Documents & Notes | Notes, Obsidian, Google Docs, Google Slides, Google Drive, Files | 168 |
| Communication & Messaging | Messages, Phone, Gmail, Telegram, Contacts, Google Meet | 214 |
| Productivity & Tools | Calculator, Calendar, Clock, Settings, Google Maps, Google Sheets | 150 |
| Weather | Weather | 5 |
| Food & Delivery | Swiggy | 1 |
| Travel & Booking | MakeMyTrip | 1 |
| News | MSN News | 1 |
| Shopping | Amazon Shopping | 1 |

Sectors are a convenience grouping (see `app_usage_grounding.md` for the
per-day app-density rationale); the authoritative per-app counts above are what
`dailybench_report.py` uses for bucket/`--app` selection. The Google Workspace
task sets (Docs rotation ~1/3 of note-app slots; Sheets; Slides; Meet) were added
from day 4 onward — see `future-directions.md`. The 2026-08-12 diversification
pass added real apps for the biggest real-world gaps (food, OTT, travel, tickets,
news, shopping). PDF handling stays in Files/Drive/Gmail (open + read only — no
editing, which is a premium feature); a dedicated easy Files PDF-read task now
lives on day 27 — the agent opens a flight ticket (`boarding_pass.pdf`) and reads
back the departure terminal, gate, and date, mirroring how people really use
PDFs (tickets, boarding passes) rather than just file management.

## Sector coverage vs. real-world daily app usage (grounded)

To check whether the benchmark reflects how people actually spend time on their
phones, the corpus's sector mix is compared against published usage data
(Statista / eMarketer / Business of Apps, 2024–2025; collected 2026-08-11):

**Ground-truth anchors:**

- **Social media is the single largest time category** — **35.1%** of time spent
  in mobile apps worldwide (2024, Android-only, Statista stat 1465726, released
  Feb 2025).
- Google Play **category penetration** (share of Android users with the category
  installed; Statista stat 200855, **data as of September 2019** — the most
  recent public release of this series): Communication **99.39%**, Tools
  **99.81%**, Business **99.33%**, Video Players & Editors **96.63%**, Travel &
  Local **95.70%**, Social Media **95.02%**, Productivity **91.67%**, Music &
  Audio **88.38%**, Entertainment **83.85%**, News & Magazines **81.11%**,
  Photography **75.77%**, Books & Reference **70.74%**, Shopping **35.79%**,
  Weather **32.46%**.
- The average smartphone user spends **~2 h 51 m/day in apps** (≈90% of
  smartphone time) and uses **~9 apps/day, ~30/month** (eMarketer / Techjury).

> ⚠️ **Source-accuracy note (2026-08-11):** the penetration figures were
> cross-checked against the **primary Statista page (200855)**. A widely-copied
> secondary roundup (BuildFire) mislabels Communication as **99.93%**; the
> primary source value is **99.39%**. This spec uses the primary-source values.
> Penetration data is **2019** vintage (the newest Statista release of this
> series); it is used only to rank categories relatively, not as a 2024 claim.

**Our corpus vs. reality — what's covered:**

| sector | our tasks | real-world prominence |
|---|---|---|
| Media & Entertainment | 192 | high (video/audio top time-sink) |
| Documents & Notes | 168 | productivity-heavy, over-represented vs real time-share |
| Communication & Messaging | 214 | high (comm penetration ~100%) |
| Productivity & Tools | 150 | medium (tools ~91–100% penetration) |
| Weather | 5 | niche (dedicated weather app checks) |
| Food & Delivery | 1 | high-usage in India (Swiggy native app added 2026-08-12) |
| OTT / streaming | 1 | high (Prime Video added) |
| Travel & booking | 1 | high (MakeMyTrip added) |
| Tickets & entertainment | 1 | medium (BookMyShow added) |
| News | 1 | high (MSN News added) |
| Shopping | 1 | medium (Amazon Shopping added) |
| PDF (open + read) | 4+ | high — opened/read in Files, Drive, Gmail (no editing: premium) |

**Missing sectors (not represented as apps in the corpus):**

1. **Social media apps** (Facebook, Instagram, TikTok, X, Snapchat, Reddit) —
   the **#1 real-world time category (35.1%)** yet entirely absent as apps
   (Telegram is messaging; Chrome/Search are browser). The single biggest gap.
2. **Gaming** — a top global time-spend category; zero games in the corpus.
3. **Finance / banking / UPI** (Paytm, PhonePe, GPay, banking apps) — a very
   high-usage category in India (the benchmark's home market) and absent.
4. **Food delivery / ride-hailing breadth** — Swiggy now covers food; ride
   (Uber/Ola) still absent.
5. **Health & fitness** — absent.

**Why this matters / caveats:** the corpus is a *task-difficulty* benchmark, not
a usage-simulator — it intentionally skews to apps that support verifiable,
deterministic end states (documents, notes, settings, timers, contacts), which is
why Productivity/Documents are over-represented relative to real time-share and
social/gaming are absent. **Google Meet** (added day 4+) addresses part of the
Communication gap, but the **Meet app is not yet installed on the device**
(`com.google.android.apps.meetings` MISS — see the at-a-glance device note), so
those tasks are authored + seeded but not runnable until provisioning installs
it. The 2026-08-12 diversification pass closed the food/OTT/travel/tickets/news/
shopping gaps with real native apps (Swiggy, Prime Video, MakeMyTrip,
BookMyShow, MSN News, Amazon Shopping). PDF handling remains in Files/Drive/Gmail
as **open + read** tasks (Adobe Scan was briefly added for scan but removed on
request — it's a mostly-human scanning app; editing/annotating PDFs is excluded as
it's a premium feature). Adding a **social app** and a
**finance/UPI app** would most improve real-world representativeness. ToS
constraints (see the grounded assessment in §"Why the missing apps are absent"
below, and `future-directions.md` §5) rule out the highest-risk automation
targets (WhatsApp, Zoom) in favour of Google ecosystem apps (Docs, Sheets,
Slides, Meet).

> ⚠️ **Penetration ≠ time-share (2026-08-12):** a common misreading is that a
> category's Google Play **penetration** (e.g. Communication **99.39%**, Social
> Media **95.02%**) is a share of *usage time*. It is not — it is the share of
> users with **at least one app in the category installed**. The **35.1%** figure
> is *time-share* (share of app time spent in social media), a different stat.
> The benchmark uses penetration to justify **which apps are on an everyday
> device**, uses daily-active-app count (~9-10/day) to justify **per-day
> density**, and deliberately does **not** weight the task mix by time-share (a
> time-share mix would be ~35% social + much of the rest gaming/OTT — all
> excluded/ungradeable). Full reasoning + the measured distribution in
> `app-usage-grounding.md` §"Two different numbers" and §"Why the task mix is NOT
> proportional to real time-share".

## Honest answer on the research claim — what's real vs. inferred (2026-08-12)

The claim that "**real daily use is dominated by communication +
media/entertainment, with a tools core and an occasional
productivity/docs/weather/shopping tail**" is **not a single published
finding — it is a synthesis**. No public dataset breaks down the
"~9-10 apps a person opens today" by sector; the closest published numbers are
category **time-share** and category **penetration**, which are different stats
(see the ⚠️ callout above). Here is exactly what is grounded vs. what is inferred:

| Claim | Status |
|---|---|
| Social media ≈ **35.1%** of app *time* (largest category) | **Real data** — Statista 1465726 (2024, Android only) |
| TikTok **95 min** / YouTube **74 min** per day (most time-consuming apps) | **Real data** — data.ai *State of Mobile 2023* |
| Communication **99.39%** / Tools **99.81%** / Video Players **96.63%** penetration | **Real data** — Statista 200855 (2019, newest public release) |
| "Essential daily apps" = social, IM, email, video, maps, browser, shopping | **Real but qualitative** — BuildFire / Statista "can't live without" lists |
| "**Communication + media/entertainment dominate the daily mix**" | **Inference** from the above — not measured directly |

**Bottom line:** the *parts* are real and citable (time-share says media/social
dominate time; penetration says comm/tools are on ~every phone); the *daily
sector mix* itself is an **inference** assembled from those two proxies plus
qualitative essential-apps lists — there is no directly-measured "daily active
apps by sector" statistic in the public record. The benchmark therefore grounds
**density** on the daily-active-app count and **app selection** on
penetration + time-share, and is transparent that the daily sector mix is
approximated rather than measured. (The full, cited breakdown lives in
`app-usage-grounding.md` §"What actually fills a person's daily ~9-10 apps".)

## Why the missing apps are absent: a grounded ToS assessment (2026-08-12)

The categories still without apps (social, gaming, finance/UPI, health, ride) are
excluded for a mix of **automation ToS** and **verifiability**, not oversight —
the food/OTT/travel/tickets/news/shopping gaps were closed on 2026-08-12 by
adding real native apps (Swiggy, Prime Video, MakeMyTrip, BookMyShow, MSN News,
Amazon Shopping), which have permissive-enough terms and verifiable
end-states; PDF handling stays in Files/Drive/Gmail as open+read tasks. The key
published terms for the still-absent categories:

- **WhatsApp (Meta)** — Acceptable Use explicitly bans "bulk messaging,
  auto-messaging, auto-dialing" (item *e*), "any non-personal use of our
  Services unless otherwise authorized by us" (item *f*), and — under
  "Harm To WhatsApp" — any access "through automated or other means" used in
  "impermissible or unauthorized manners" (including reverse engineering and
  collecting user info in unauthorized ways). Its "Excluded Disputes" carve-out
  even names "engage with our Services in unauthorized ways (for example,
  automated ways)".
- **Instagram (Meta)** — Terms ban "access or collect information in automated
  way (including by engaging in Automated Data Collection ...) without our
  express permission", and the platform blocks/detects scripted UI drivers
  aggressively (login challenges, rate limits, account locks).
- **TikTok / X / Snapchat / Reddit** — each has a comparable no-bot/no-scraping
  automation clause and active anti-automation (e.g. TikTok's CAPTCHA + device
  fingerprinting on programmatic access).
- **Gaming & passive OTT** — no ToS barrier per se, but no crisp verifiable
  end-state (passive consumption; nothing to "complete" that is checkable against
  device state), so they are ungradeable under the deterministic/honesty
  framework. (Prime Video's tasks were scoped to catalog lookups, not passive
  playback.)
- **PDF editing/annotating** — excluded as a premium feature; PDF tasks open +
  read only (page count, totals, attachments), never edit.
- **Finance / UPI / banking** — the highest-risk category: payment UIs involve
  credentials and real money; automated control risks account locks and is
  excluded on safety grounds (see `future-directions.md` §7 for a sandboxed
  mock-pay proposal).

**What that means for the corpus:** the benchmark favours **Google-ecosystem
apps** (Docs, Sheets, Slides, Meet, Drive, Photos, Maps, Search) because their
terms permit normal human-equivalent UI use and their end-states are verifiable;
Telegram is the one messaging app with a permissive-enough stance (open bot API,
no per-device automation ban) that it can stand in for the messaging category;
and Chrome/Search exercise social-adjacent *browsing* without touching the
social apps themselves. Adding a real social app is the single biggest
representativeness win available **if** a ToS-clean path is found (see
`future-directions.md`).

## Canonical task families

- easy
- medium
- hard-deterministic
- open-ended

The canonical runnable task list lives in [benchmarks/dailyBench-600/tasks_530.md](../benchmarks/dailyBench-600/tasks_530.md) — the runnable corpus (530 dataset rows: 216 easy / 242 medium / 72 hard = 36 ASK USER / 36 DETERMINISTIC), laid out as a 28-day schedule. The public preview is `benchmarks/dailyBench-600/public.md` (50 curated tasks). `tasks_530.md` is the source of truth: edit it and regenerate `DailyBench_530_v1.json`/`.jsonl` with `scripts/data/export_530_dataset.py`.

## Days, seeds, and manifests

The benchmark is organised day-by-day so it is fully inspectable and extensible:

- **Run any day** with the batch runner: `uv run dailybench_tasks.py --day 3 ...` (a `--day N` selector for any day 1..28, see [README](../README.md#run-a-day-530)). Runs land under `runs/<batch>/day<N>/...`.
- **Seed manifests** are generated per day under `seeds/manifests/day_<N>/`:
  - `manifest_index.json` — day-level index (task ids in schedule order, bucket counts)
  - `<task_id>/manifest.json` — per-task fabricated-data manifest (resolved prompt, `--var` map, ASK USER fact, required seed data + status, expected end state, config keys used)
  - `day_<N>_fabricated_data.jsonl` — one meticulous JSON line per task
  - real seed files (photos/pdf/notes) live flat in `assets/seeds/day_<N>/`; `DEVICE_PATHS.md` per task sits in the manifest dir
- **Days 1–6** have hand-authored specs (`DAY1..6_TASKS` in `scripts/seeding/build_day_seed_manifest.py`) that document each task's exact fabricated data.
- **Days 7–28** are auto-generated per-task from the dataset (same manifest shape): each task gets an app-appropriate seed entry (web / needs_ui / needs_seed / present / sanity / creation) and a resolved-vars map. To document a specific day's fabricated seeds by hand, add a `DAY<N>_TASKS` block to `scripts/seeding/build_day_seed_manifest.py` and wire it into `build_day()` — the generator then uses your spec instead of the auto one.
- Rebuild all days at once: `for d in $(seq 1 28); do uv run python scripts/seeding/build_day_seed_manifest.py --day $d; done`.

This keeps the fabricated data, the run schedule, and the per-day vars (`tasks_vars/day_N.env`) all derived from `tasks_530.md` + `config/user.yaml`, so nothing is hidden in ad-hoc files.

## Required run artifacts

Each valid run should contain:

- `meta.json`
- `preflight.json`
- `postflight.json`
- `samples.ndjson`
- `run_metrics.json`
- `agent.log.txt`
- `output.txt`
- `output.json`

Optional artifacts:

- `screen.mp4`
- `llm_proxy_metrics.jsonl`
- `llm_metrics.json`

## Required summary metrics

- `elapsed_seconds`
- `command_exit_code`
- `llm_prompt_tokens_sum`
- `llm_completion_tokens_sum`
- `llm_total_tokens_sum`

## Action-budget policy

- all benchmark tasks use the same default `50`-step action budget
- this fixed cap is part of the benchmark definition and is meant to preserve fairness across buckets

## Evaluation philosophy

- deterministic tasks should be scored by explicit success/failure evidence
- open-ended tasks should be scored separately with rubric-based evaluation
- benchmark maintenance must preserve comparability across runs and dates
