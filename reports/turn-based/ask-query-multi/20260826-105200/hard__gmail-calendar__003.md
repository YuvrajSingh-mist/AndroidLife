# hard__gmail-calendar__003  — ASK USER MULTI

**Run day:** day2 · **Run root:** `assets/runs/public/20260826-105200/day2/hard-gmail-calendar-003/`

**Difficulty:** hard · **Apps:** Gmail, Calendar

**Task (what the user asked):**

> I'm need details about my next trip quickly. Find my flight confirmation email for that trip, extract the details like flight name, departure time and terminal for me and yea could you forward it to my friend's email id too? And also for my end, add it to the Calendar as a reminder 3 hours before departure so I get a heads-up?

**Ground-truth fact:** multiturn_kb: gmail-calendar::bbi-del-reminder
**ask_user turns:** 0

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

> ⚠️ **No ask_user calls recorded** — the agent never asked the user (guesses a target instead → FAIL under the MobileWorld gate).
