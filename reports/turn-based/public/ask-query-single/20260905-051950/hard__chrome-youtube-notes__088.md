# hard__chrome-youtube-notes__088  — ASK USER SINGLE

**Run day:** day3 · **Run root:** `assets/runs/public/20260905-051950/day3/hard-chrome-youtube-notes-088/`

**Difficulty:** hard · **Apps:** Chrome, YouTube, Notes

**Task (what the user asked):**

> I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note in Notes. Ask me about the title though!

**Ground-truth fact:** The task is changing a bike tyre. Save the steps as 'How to change a bike tyre'.
**ask_user turns:** 1

**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**

```text
Ask the human user a clarifying question when the task needs a specific fact that is NOT available anywhere on the device (for example a particular contact's name, a date or time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact you think is missing to complete the task. Never ask about things you can look up yourself. Ask one specific question at a time. You may ask multiple questions over multiple turns to disambiguate a vague request.
```

## Turn 1  (2026-09-05T09:08:08Z)

**What the simulated user was told (actual system prompt from the run):**

```text
You are acting as a mobile phone user. A mobile GUI agent is executing a task on your phone. The task goal is: I'm trying to learn a new skill. Find a how-to guide or tutorial for it, extract the key steps, and save them as a note in Notes. Ask me about the title though!

The relevant information for the task is: The task is changing a bike tyre. Save the steps as 'How to change a bike tyre'.

You need to answer questions from the mobile GUI agent about the task above. You can ONLY answer using the relevant information given and the task goal - do not make up any information under any circumstances. If the question is not related to the task, or no relevant information is available to answer it, refuse to answer in a polite manner and say so plainly.

The current real date and time is: Sat Sep  5 14:38:07 IST 2026. If the question is about the date or time, answer using this real value rather than any date you might otherwise assume.
```

**Agent asked:**

> What skill are you wanting to learn, so I can find a how-to guide or tutorial for it?

**User answered:**

> The skill is changing a bike tyre.
