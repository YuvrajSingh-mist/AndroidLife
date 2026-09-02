# hard__chrome-telegram-notes__008  — ASK USER SINGLE

**Run day:** day2 · **Run root:** `assets/runs/public/20260826-105200/day2/hard-chrome-telegram-notes-008/`

**Difficulty:** hard · **Apps:** Chrome, Telegram, Notes

**Task (what the user asked):**

> I'm shopping for something specific and want the best price. Compare prices across two sites: [shopping_website_1] and [shopping_website_2], check the difference, and message [contact] on Telegram the cheaper link if it's over $10; otherwise note both prices and star the cheaper listing

**Ground-truth fact:** The item is wireless earbuds.
**ask_user turns:** 1

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

## Turn 1  (2026-08-26T05:58:42Z)

**Agent asked:**

> What specific item are you looking to buy so I can compare prices for you?

**User answered:**

> Wireless earbuds.
