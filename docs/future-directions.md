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

### Summary

| # | Direction | Core change | Keeps UI-honest? |
|---|---|---|---|
| 1 | MCP / GUI / MCP+GUI | Add programmatic read/act paths alongside UI | Hybrid yes, MCP-only no |
| 2 | Multi-turn user agent | Conversational user, follow-ups, pushback | Yes |
| 3 | Web lookup for app steps | Agent may search how-tos before acting | Yes |
