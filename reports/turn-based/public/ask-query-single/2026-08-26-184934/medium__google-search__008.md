# medium__google-search__008  — ASK USER SINGLE

**Run day:** day3 · **Run root:** `assets/runs/public/2026-08-26-184934/day3/medium-google-search-008/`

**Difficulty:** medium · **Apps:** Google Search, Telegram

**Task (what the user asked):**

> Could you compare public transit options for a specific route and tell me the fastest in Google Search? Also, message [contact] on Telegram the fastest route for tomorrow. Reply with only the fastest option, no other text.

**Ground-truth fact:** The route is from IIIT Bhubaneswar to Bhubaneswar Airport.
**ask_user turns:** 1

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

## Turn 1  (2026-08-26T20:54:40Z)

**Agent asked:**

> Which specific route (origin and destination) should I compare public transit options for in Google Search? Please provide the starting point and the destination.

**User answered:**

> IIIT Bhubaneswar to Bhubaneswar Airport
