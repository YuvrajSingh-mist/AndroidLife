# hard__google-search-obsidian-telegram__057  — ASK USER SINGLE

**Run day:** day3 · **Run root:** `assets/runs/public/2026-08-30-021852/day3/hard-google-search-obsidian-telegram-057/`

**Difficulty:** hard · **Apps:** Google Search, Obsidian, Telegram

**Task (what the user asked):**

> I'm tracking [stock name] and only want to hear about it when it matters. Check its current value via Google Search against the threshold in my '[stock note title]' Obsidian note, note today's value, compare it to the last recorded value in that Obsidian note, message the person I follow this stock with on Telegram only if it has crossed the threshold since then, and update the Obsidian note with today's value

**Ground-truth fact:** Message Yuvraj Singh Jio when it crosses the threshold.
**ask_user turns:** 0

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

> ⚠️ **No ask_user calls recorded** — the agent never asked the user (guesses a target instead → FAIL under the MobileWorld gate).
