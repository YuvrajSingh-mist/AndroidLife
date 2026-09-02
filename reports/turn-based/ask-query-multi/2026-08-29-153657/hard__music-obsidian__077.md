# hard__music-obsidian__077  — ASK USER MULTI

**Run day:** day2 · **Run root:** `assets/runs/public/2026-08-29-153657/day2/hard-music-obsidian-077/`

**Difficulty:** hard · **Apps:** Music, Obsidian

**Task (what the user asked):**

> I have been maintaining a routine of listening to music to fall asleep and been keeping a record of it lately with time and what music helps me sleep which you look up to and I think I found something that works for me. I want you set it up so that once you start it yourself, it then stops by itself around my asleep time. Can you set that up for me in the music app I used the most lately to time my sleep and listen to music?

**Ground-truth fact:** multiturn_kb: youtube-music::sleep-timer-1030pm
**ask_user turns:** 0

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

> ⚠️ **No ask_user calls recorded** — the agent never asked the user (guesses a target instead → FAIL under the MobileWorld gate).
