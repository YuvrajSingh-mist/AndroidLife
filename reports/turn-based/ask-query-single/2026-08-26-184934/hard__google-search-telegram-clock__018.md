# hard__google-search-telegram-clock__018  — ASK USER SINGLE

**Run day:** day2 · **Run root:** `assets/runs/public/2026-08-26-184934/day2/hard-google-search-telegram-clock-018/`

**Difficulty:** hard · **Apps:** Google Search, Telegram, Clock

**Task (what the user asked):**

> I'm going to grab something from the place I'm going to. Look up its hours via Google Search, note whether it's open now, and if it is, message the person I'm going with on Telegram suggesting we go now; otherwise message the reopening time and set an alarm for it

**Ground-truth fact:** The place is the SBI ATM. The person to message is Yuvraj Singh Jio.
**ask_user turns:** 0

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

> ⚠️ **No ask_user calls recorded** — the agent never asked the user (guesses a target instead → FAIL under the MobileWorld gate).
