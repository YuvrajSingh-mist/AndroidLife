# hard__telegram-calendar__016  — ASK USER MULTI

**Run day:** day1 · **Run root:** `assets/runs/public/2026-08-28-002424/day1/hard-telegram-calendar-016/`

**Difficulty:** hard · **Apps:** Telegram, Calendar

**Task (what the user asked):**

> I've got a get-together with my friends coming up and we've been planning it in our chat group, but honestly we kept going back and forth and the thread never actually locked anything down — it just floated options and left the plan open. I've lost track of what the last thing we settled on: the date, the time, where, even whether I asked for a reminder. Can you check our group, then confirm each detail with me one at a time — the exact day, the time, the place, and the reminder — before you put it on my calendar so I don't miss it?

**Ground-truth fact:** multiturn_kb: telegram::forever-21-meetup-tue-8pm
**ask_user turns:** 0

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

> ⚠️ **No ask_user calls recorded** — the agent never asked the user (guesses a target instead → FAIL under the MobileWorld gate).
