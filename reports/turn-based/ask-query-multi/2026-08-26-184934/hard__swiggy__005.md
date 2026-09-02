# hard__swiggy__005  — ASK USER MULTI

**Run day:** day1 · **Run root:** `assets/runs/public/2026-08-26-184934/day1/hard-swiggy-005/`

**Difficulty:** hard · **Apps:** Swiggy, Telegram

**Task (what the user asked):**

> Ugh, I'm craving the food I ate on [date] — can you get me that again? Also, message him on Telegram the order total so I can confirm before paying.

**Ground-truth fact:** multiturn_kb: swiggy::reorder-downtown-delight-murgh-mughlai
**ask_user turns:** 1

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

## Turn 1  (2026-08-28T15:08:41Z)

**Agent asked:**

> 
I've re-ordered the 14-Aug food (Downtown Delight: Kushka Rice + Murgh Mughlai) and the current order total is ₹616. But "him" isn't clear — which contact on Telegram should I send the total to? (e.g. Kumar, tilak, Aamir aos, or someone else?)

**User answered:**

> Send it to **Yuvraj Airtel** on Telegram.
