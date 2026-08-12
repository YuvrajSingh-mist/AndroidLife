# Future Directions

Ideas for evolving DrainBench / the agent beyond the current UI-automation-only
setup. These are **proposals** — not committed work. Each entry states the idea,
why it matters, and the open questions / risks.

---

## 1) MCP vs GUI-only vs MCP+GUI hybrid

**Today:** the agent drives the phone purely through UI automation (ADB taps /
uiautomator on Android, accessibility/coordinates), which is exactly what makes
tasks hard and realistic — it has to *see* the screen and act like a person.

**Proposal — three modes to compare:**

- **GUI-only (baseline):** everything via on-screen interaction, no app-specific
  programmatic access. This is the current behaviour and the fairest measure of
  "can the agent actually use the app like a human".
- **MCP-only:** expose each app through a Model Context Protocol server (structured
  tools: `list_contacts`, `create_event`, `send_message`, etc.). Fast, precise,
  deterministic — but it no longer tests real UI skill; it tests tool-calling.
- **MCP+GUI hybrid (the interesting one):** the agent gets MCP tools for the
  *read* side (query state, verify end state reliably) but must still perform the
  *act* side through GUI (make the change on screen). This keeps tasks honest
  (real UI manipulation still required) while removing the flaky "did the UI
  actually change?" verification problem.

**Why it matters:** lets us isolate *where* agents fail — reading/understanding
the UI vs. manipulating it. Also enables graded comparisons: "same task, GUI-only
vs hybrid" gives a ceiling on how much of the difficulty is pure UI friction.

**Open questions:** Does MCP tooling need to run on-device (a local MCP server on
the phone) or can it talk to app backends/accounts directly? If MCP can do
everything, does the benchmark stop being a *UI* benchmark? Where do we draw the
line on which apps get MCP servers?

---

## 2) Multi-turn user agent

**Today:** tasks are mostly one-shot — the agent gets a prompt, acts, and (for
ASK USER) asks a single clarifying question. There is a simulated user
(`ask_user_facts.json`) that answers facts only when asked.

**Proposal:** make the agent genuinely **multi-turn** with a conversational user:

- The agent can ask follow-up questions mid-task, not just once (e.g. "the
  notification tone is already used by another contact — should I pick a
  different one?").
- The simulated user can *push back* or *clarify* ("no, the other conversation")
  so the agent must reconcile conflicting/ambiguous instructions.
- Long tasks can involve a back-and-forth: confirm → act → report → adjust → act
  again, with the final answer graded on the end state *and* on whether the agent
  asked the right questions at the right time.
- Optionally: a memory/context thread so the agent remembers user preferences
  across turns (tones, naming conventions, tone of voice) and applies them.

**Why it matters:** real users don't hand over a phone and walk away — they
collaborate. Multi-turn is closer to reality and stresses the agent's ability to
ask *good* questions (which current ASK USER tasks already hint at) rather than
just execute.

**Open questions:** How to grade the *quality* of questions, not just the final
end state? Should every task become multi-turn or keep a fixed 1-turn subset for
backward comparison? Who drives the user persona (LLM-simulated vs scripted)?

---

## 3) Agent-driven web lookup of "how to do X in app Y"

**Today:** the agent must figure out each app's UI from first principles (or from
trained knowledge). If it doesn't know where "sleep timer" lives in YouTube Music,
it has to stumble around the UI.

**Proposal:** let the agent **query the web to find step-by-step instructions for
the specific task on the specific app**, then follow them on-device:

- Before acting, the agent may search e.g. *"how to set a sleep timer in YouTube
  Music"* / *"Google Calendar create event steps"* and read a how-to (docs,
  support page, Reddit, app guide).
- It then maps those instructions onto the live UI (which may have moved since the
  article was written — so it still needs real visual grounding).
- This could be an *available tool* (agent chooses when to use it) or a *scored
  behaviour* (we reward consulting authoritative sources before acting, and check
  it doesn't blindly trust stale instructions).

**Why it matters:** this is exactly what a capable human assistant would do —
look up the current steps rather than guessing. It also differentiates agents by
*resourcefulness*, and makes the benchmark robust to app UI changes (the
instruction source updates with the app, so the task stays solvable).

**Open questions:** Should web lookup be a *right* (optional tool) or a
*requirement* (deduct points for not researching)? How do we prevent the agent
from "cheating" by looking up the exact benchmark task text (vs. generic app
how-tos)? Need an allow-list of instruction sources? Network on the test device
is already live, so this is technically straightforward — the design question is
purely about grading and anti-gaming.

---

## 4) Close the Google Sheets gap — DONE (2026-08-12)

**Today:** the benchmark has **no `sheets` app_slug**, yet at least one task in
`benchmarks/dailyBench-600/public.md` explicitly says *"open it in the google
sheets app"* (the Files → SPORTS_VIDEO_DATA task), and Google Sheets **is installed
on the device** (`com.google.android.apps.docs.editors.sheets`). So the app exists on
the phone but is missing from the benchmark's app inventory / app list.

**Proposal:** add `sheets` as a first-class app in the dataset (app_slug, vars,
seeds) and write a real Sheets task set: open a sheet, read/format a cell range,
sum a column, sort rows, add a note/freeze a header, share a sheet link, etc.
Make sure the seed ships a `SPORTS_VIDEO_DATA`-style workbook so the Files→Sheets
handoff is actually testable.

**Done (2026-08-12):** the `google-sheets` app_slug, `SPORTS_VIDEO_DATA` seed vars
(`spreadsheet name`, `sheet column`), and an 8-task Sheets set (days 6/12/20/27:
read first row, sum a column, count rows, sort, freeze header, append date row)
were added to `tasks_530.md`, `task_dataset.py` aliases, `app_audit.py`,
`build_day_seed_manifest.py`, and `config/user.yaml`.

**Remaining open questions:** verify the exact launcher label / package for the
agent's `open_app` step; confirm Sheets needs a Google account sign-in on a fresh
device; define the read-back verification (cells → text dump) for grading.

## 5) Add Google Meet tasks — DONE (2026-08-12)

**Today:** no `meet` app_slug, and Google Meet is **not installed** on the current
device (no `com.google.android.apps.meetings` package — confirmed via `pm list`).
The existing "meeting" tasks (e.g. hard__calendar-telegram-obsidian__002) only
*reference* a meet link text; they never open Meet.

**Proposal:** add Meet as an app + task set. Realistic, testable tasks that don't
need a live call: open Meet, view today's/upcoming scheduled meetings, join a
meeting by link (landing screen), toggle camera/mic off, check the meeting roster
(participant list), copy the meeting link, mute/unmute, leave the meeting, or
schedule a Meet via Calendar. Keep it to UI-reachable states — no real call
needed.

**Done (2026-08-12):** the `google-meet` app_slug, `meeting link` var, and an
8-task UI-only Meet set (days 7/14/19/26: view schedule, open next meeting
details, mute/unmute + camera off, open join-by-code / landing screen, copy
link) were added to `tasks_530.md`, `task_dataset.py` aliases, `app_audit.py`
(Mark as OPTIONAL — app not yet installed on the device), `build_day_seed_manifest.py`,
and `config/user.yaml`. All tasks stay on the join/landing + controls surface — no
live calls.

**Remaining open questions:** Meet must be installed first (device provisioning /
seed step for the app itself); sign-in requirements; whether joining a real
meeting is in scope (probably keep to the join/landing + controls surface to stay
deterministic).

## 6) Real-world end-to-end "booking / checkout" tasks

**Today:** tasks are mostly single-app or short cross-app. The closest thing to a
real-world transaction is the public Notes task *"add the first checklist's
unchecked items to my shopping cart on Amazon, and get it to the payments page"* —
which is exactly the right shape, but it's one task, not a family.

**Proposal:** add a family of **day-to-day end-to-end flow tasks** (user's words:
"flight booking, ticket booking for movie, and shopping end-to-end from product
picking to the payment page"):

- **Flight booking:** pick a route + date, choose a flight, select a fare, and
  reach the passenger/payment step (stop before paying).
- **Movie ticket booking:** pick a movie + showtime, select seats, choose snacks if
  offered, and reach the payment/checkout step.
- **Shopping checkout:** pick a product, choose variant/qty, add to cart, and
  navigate to the payment page (existing public task is the template).

All three stop **at the payment page** — no real purchase, no credentials. This is
"more like usual day-to-day" usage (user's phrasing) and stresses multi-step
navigation, persistence across screens, and end-state verification.

**Why it matters:** these are the flows real people do daily; they exercise long
action chains, form-filling, and app-specific checkout UIs — much harder and more
representative than single-step tasks.

**Open questions:** which app to use (Amazon vs Flipkart vs a dedicated app) —
`shopping-delivery-browser` already exists; booking sites need a browser or an
app; how to seed state (logged-in cart, a movie listing) deterministically; and
how to verify "reached payment page" as the end state without making a purchase.

---

### Summary

| # | Direction | Core change | Keeps UI-honest? |
|---|---|---|---|
| 1 | MCP / GUI / MCP+GUI | Add programmatic read/act paths alongside UI | Hybrid yes, MCP-only no |
| 2 | Multi-turn user agent | Conversational user, follow-ups, pushback | Yes |
| 3 | Web lookup for app steps | Agent may search how-tos before acting | Yes |
| 4 | Close Google Sheets gap | Add `sheets` app_slug + task set (device has it) | Yes |
| 5 | Add Google Meet tasks | Add `meet` app + install + UI-reachable tasks | Yes |

**Implemented 2026-08-12:** roadmap items 4 (Google Sheets) and 5 (Google Meet)
were shipped along with a Google Docs rotation and a Google Slides task set — see
`benchmark-spec.md` → "App coverage & sector distribution".
| 6 | Real-world booking/checkout | Flight / movie / shopping → payment-page flows | Yes |
