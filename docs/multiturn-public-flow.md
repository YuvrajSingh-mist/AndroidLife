# Public multi-turn (KB) flow — annotated transcripts & how the KB is used

This doc walks through exactly what happened in the **4 public multi-turn KB tasks**
run in `assets/runs/public/2026-08-20-003030` (qwen3.6-plus), turn by turn: the
prompt, the clarifying question the ask-user oracle asked (if the agent asked
anything), what the oracle answered, what the agent actually did, and how the
public knowledge base (`benchmarks/dailyBench-600/multiturn_kb_public.json`) is
consumed by the simulated-user LLM.

It is the companion to the summary table in `reports/public/public-2026-08-20-003030.md`
("Multi-turn KB tasks" section). Here we go deeper into the actual dialogue and
the mechanics.

---

## 1. How the public KB is used (the mechanism)

There is **no RAG, no retrieval, no vector search**. The KB is used in exactly
one way:

- At run start, the harness loads the task's profile from
  `multiturn_kb_public.json` (keyed by `task_id`) into the **ask_user tool** as a
  JSON blob (`kb`).
- The agent (qwen3.6-plus) is a plain GUI agent with a tool called `ask_user`.
  The tool description tells it: *"Ask the human user a clarifying question when
  the task needs a specific fact that is NOT available anywhere on the device…
  First search the device thoroughly for it — only if you genuinely cannot find
  or infer it should you ask."*
- When (and **only** when) the agent calls `ask_user("…question…")`, the call is
  forwarded to the **simulated user** = `gpt-5.4-mini` (DeepEval/OpenAI-backed,
  `DEFAULT_ASK_USER_MODEL` in `src/DailyBench/custom_tools.py`).
- The oracle's system prompt (`ASK_USER_KB_SYSTEM_PROMPT_TEMPLATE`) injects:
  - the task goal,
  - the **entire KB profile** as JSON (`knowledge_base`),
  - the device's real current date,
  - a **rolling conversation history** (every prior Q&A), so follow-ups are
    consistent across turns.
- The oracle rules: answer **only** from the KB + goal, never invent, keep
  answers short, and if the KB doesn't contain the asked-for fact, say so plainly.

So **what "gets out of the KB" is exactly the answer to whatever the agent
asked.** The KB is passive: it never volunteers anything, never pushes a fact
the agent didn't request. If the agent asks nothing, the KB contributes nothing
— and that is precisely the failure mode we observed in 3 of 4 tasks.

Each `ask_user` call is logged to `<run>/ask_user_metrics.jsonl` with the
question, the answer, model, turn number, tokens, and cost.

---

## 2. The four tasks at a glance

| task_id | goal (abridged) | correct target (KB) | ask_user calls | self-report | verdict |
|---|---|---|---|---|---|
| `hard__swiggy__005` | "craving the food I ate in the past week — get me that again; also message him on Telegram the order total" | `swiggy::reorder-downtown-delight-murgh-mughlai` | **1** | success=True | ⚠️ **wrong target** (wrong contact, no reorder) |
| `hard__telegram-calendar__016` | "date dropped in a Telegram chat → calendar event + reminder" | `telegram::forever-21-date` | **0** | success=True | ✅ pass (GUI-only shortcut) |
| `hard__gmail-calendar__003` | "find my flight confirmation for the next trip → calendar reminder 3h before" | `gmail-calendar::bbi-del-reminder` | **0** | success=False | ❌ fail (wrong flight, never asked) |
| `hard__music-obsidian__077` | "make music stop by itself at my bedtime in YT Music" | `youtube-music::sleep-timer-1030pm` | **0** | success=False | ❌ fail (step-cap) |

Only **1 of 4** ever called `ask_user`.

---

## 3. `hard__swiggy__005` — the one task that DID use the oracle

**Goal:** "Ugh, I'm craving the food I ate in the past week — can you get me that
again? Also, message him on Telegram the order total so I can confirm before
paying."

**KB profile highlights** (`multiturn_kb_public.json`):
- `account.name` = Yuvraj Singh, address Work = K 504 IIIT Bhubaneswar.
- `orders[0]` = **Downtown Delight · Khandagiri · Murgh Mughlai + Kushka Rice ·
  ₹523** (status delivered, `recent: true`, `this_week: true`, `favourite: true`).
- `contacts` / `selected_contacts` include **Yuvraj Singh Jio** and **Yuvraj Airtel**.

**Actual dialogue (1 ask_user turn), from `ask_user_metrics.jsonl`:**

| # | question (from agent) | oracle answer (from KB) | when |
|---|---|---|---|
| 1 | `"Who is "him" that you want to message on Telegram? Please provide the contact name."` | **`Yuvraj Singh Jio`** | step ~18 (01:53:59 IST) |

Model `gpt-5.4-mini-2026-03-17`, turn 1, ~2.5 s, 1786 tokens, **$0.00137**.

**What the agent did around that (from `agent.log.txt`):**
1. Opened Swiggy, tapped **Reorder** — but the Reorder screen lists restaurants,
   not per-order totals, so it couldn't find a clean "total".
2. Left Swiggy; opened **Messages**, found a Swiggy promo SMS + a **bank SMS for
   ₹160 to Maharani Restaurant**.
3. Opened Telegram, saw a chat with **Yuvraj Airtel**, decided "him" was
   ambiguous, and **called `ask_user`** with the question above.
4. Oracle answered **"Yuvraj Singh Jio"**.
5. Agent searched Telegram for **"Yuvraj Singh Jio"** → **no exact match**.
6. It fell back to the existing **Yuvraj Airtel** chat and sent:
   *"The order total for the food I ate last week was Rs. 160."*
7. `complete(success=true)`.

**What went wrong vs. the KB target:**
- It messaged the **wrong contact** (Yuvraj Airtel, not the oracle's Yuvraj Singh Jio).
- It never **reordered** anything (the KB target is reorder Downtown Delight /
  Murgh Mughlai — "the food I ate in the past week").
- The "total" (₹160 Maharani) is **not** the KB's recent order (₹523 Downtown Delight).
- Self-report success=True → the report counts it a pass, but the strict
  KB-target check is **FAIL (wrong target)**.

---

## 4. `hard__telegram-calendar__016` — GUI-only shortcut (pass, but no interaction)

**Goal:** "I think someone dropped a date in one of my Telegram group chats for
something coming up, and I don't want to forget it. Can you make sure it's on my
calendar with a reminder?"

> Note: this run used the **pre-edit** prompt ("Telegram chats"). The dataset was
> later re-generated with "group chats" (see §7).

**KB profile:** `chats` include the group **Forever 21** (2 members, topic "plans /
get-together"), `preferences.reminder_chat` = Forever 21. Correct target =
`telegram::forever-21-date`.

**Actual flow (0 ask_user calls):**
1. Opened Telegram, read a thread: *"Wait I think she is busy at that day so
   maybe 22nd of this month?"* / *"Umm ok 22nd seems cool let's set that date
   then!"* and *"It a meetup!"*.
2. Checked the device date (`adb shell date` → **August 20, 2026**), resolved
   "22nd of this month" → **August 22, 2026**.
3. Opened Calendar, created **"Meetup"** on **Sat, Aug 22, 2026**, saved it.
4. `complete(success=true)`.

**Outcome:** the date the agent found happened to be the right one, so it passes
— but it exercised **zero** interaction with the KB oracle. It never confirmed
*which* group/date with the user. With the new "group chats" wording the agent
should (ideally) ask which group before assuming.

---

## 5. `hard__gmail-calendar__003` — the "why did it never ask?" case (FAIL)

**Goal:** "I'm flying out soon and don't wanna miss it. Find my flight
confirmation email for that trip and add it to the Calendar as a reminder 3
hours before departure so I get a heads-up?"

**KB profile** (`multiturn_kb_public.json` → `hard__gmail-calendar__003`):
- `flights[0]` = **IndiGo 6E 6893 · BBI→DEL · 2026-08-24 · 07:10** (confirmation email: true).
- `flights[1]` = IndiGo 6E 6737 · BBI→DEL · 2026-05-08 (past-trip distractor).
- `preferences.next_trip` = **BBI→DEL**, `reminder_hours_before` = 3.

**Actual flow (0 ask_user calls, from `agent.log.txt`):**
1. Opened Gmail. The search bar showed **persisted recent searches**:
   **"IndiGo"** and **"6E 6821"** — i.e. Gmail's own search history on the
   device, **not** the KB.
2. Searched "flight confirmation" → only an old 2015 Saudi Arabian flight.
3. Searched "IndiGo" → only **Google Flights price alerts / tracked-route**
   emails (DEL→IAD), not a booking confirmation.
4. Searched **"6E 6821"** → **"No matches"**.
5. Tried "booking confirmation", "itinerary", "e-ticket", "flight" — nothing
   recent.
6. `complete(success=false)`: *"Could not find a recent flight confirmation email
   in the Gmail inbox… Without the flight details (date, time, airline), I cannot
   create a calendar reminder."*

**Why did it never ask? (root cause analysis)**
- **It thought it had a concrete lead.** Gmail surfaced "6E 6821" in its recent
  searches, so the agent treated that as "a very specific search term that likely
  leads to the actual booking confirmation" — it believed it already had the
  flight number.
- **The ask_user tool is agent-initiated.** Nothing pulls from the KB unless the
  agent calls `ask_user`. The tool description says to search the device first
  and ask only if it "genuinely cannot find or infer" the fact. The agent
  interpreted the failed search as "the email doesn't exist" rather than "I'm
  missing which flight — I should ask."
- **No ambiguity signal.** The task never forces an ask; a well-behaved
  multi-turn agent should notice it has no trip date/airline/flight# and
  disambiguate *which* flight via the oracle — but this agent never reached that
  decision point. 0 `ask_user` calls, 0 oracle answers, so the KB (which would
  have answered "6E 6893") was never consulted.

**⚠️ Found inconsistency worth fixing:** the seed manifest
(`scripts/seeding/build_day_seed_manifest.py`, `hard__gmail-calendar__003`) and
the agent's device context reference flight **6E 6821**, while the **KB says the
next trip is 6E 6893**. Even if the agent *had* asked the oracle, the on-device
email (if any) and the KB must agree on the flight number for this task to be
solved. These two sources of truth are out of sync and should be reconciled
before a re-run.

---

## 6. `hard__music-obsidian__077` — step-cap thrash, never asked (FAIL)

**Goal:** "I listen to music to fall asleep and want it to stop by itself around
my bedtime. Can you set that up for me in YouTube Music?"

**KB profile:**
- `preferences.sleep_timer` = **10:30 PM**, `wake_up_time` = 6:30 AM,
  `wind_down_routine` = lo-fi beats, `volume` = low (~20%),
  `repeat_mode` = off, `fall_asleep_habit` = "starts a Chillhop lo-fi track then
  lets the timer stop it".
- `notes.Bedtime.time` = 10:30 PM (Obsidian `Bedtime.md`, real on-device).
- Correct target = `youtube-music::sleep-timer-1030pm`.

**Actual flow (0 ask_user calls, from `agent.log.txt`):**
1. Opened YouTube Music, started/selected a track, then hunted for a **sleep
   timer** in the UI.
2. Repeatedly tapped the three-dot menu (`index 16`) and `Close` (`index 11`) in
   loops, never finding a "Sleep timer" option.
3. Hit the **60-step cap** at 03:58 with the timer never set.
4. No `complete()`; the run is scored as step-cap failure.

**What went wrong:** pure GUI navigation thrash in YT Music. The oracle was never
consulted — it would have confirmed bedtime 10:30 PM and the lo-fi/Chillhop
habit, giving the agent a concrete target (a sleep timer ending at 10:30 PM on a
Chillhop track). With 0 `ask_user` calls, the KB contributed nothing.

---

## 7. Summary & next-run implications

- **The KB only speaks when asked.** Its entire "output" is the oracle's short
  answers to the agent's `ask_user` calls — nothing more. This makes the agent's
  willingness to ask the *only* thing that determines whether the KB is used.
- **3 of 4 tasks never asked**, so the public multi-turn mechanism was barely
  exercised: only `hard__swiggy__005` produced an actual Q&A (and then ignored
  the answer's contact).
- **`hard__swiggy__005` is a silent wrong-target success** — the report's
  self-reported pass masks a FAIL under a strict KB-target check.
- **`hard__gmail-calendar__003` has a seed-vs-KB flight-number mismatch**
  (6E 6821 vs 6E 6893) that should be fixed before re-running.
- The dataset was re-generated after this run (`scripts/data/export_public_dataset.py`,
  68 tasks) with the telegram-calendar prompt now reading "group chats" — a
  future run will exercise the "which group?" disambiguation path that this run
  skipped.

**Where to look for the raw evidence:**
- Dialogue + cost: `<run>/ask_user_metrics.jsonl`
- Full step-by-step reasoning: `<run>/agent.log.txt`
- Profile the oracle answers from: `benchmarks/dailyBench-600/multiturn_kb_public.json`
- Simulated-user prompt & rules: `src/DailyBench/custom_tools.py`
  (`ASK_USER_KB_SYSTEM_PROMPT_TEMPLATE`, `ask_user`)
