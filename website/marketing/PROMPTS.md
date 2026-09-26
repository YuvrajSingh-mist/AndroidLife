# AndroidLife - video-generator prompts (fact-checked)

Use these if you want polished motion from Kling / Runway / Luma / etc.  
Prefer **three separate clips**. Numbers below match the published manual-audit leaderboard - do **not** invent 84% success.

---

## MASTER VISUAL PROMPT (prepend to every clip)

Create a premium 9:16 vertical product-marketing sequence for "AndroidLife".
Look like a human-made Apple/editorial product still - NOT a generic AI research video.

Visual identity:
- Soft light-gray studio background (#e8e8ea), gentle falloff, no glow orbs
- Realistic black Android phone with soft physical shadow
- Editorial typography: high-contrast serif headlines + quiet system sans labels
- Eyebrow labels like " -  A DAY IN THE LIFE"
- Floating white callout cards with soft drop shadows (magnified UI / metrics)
- Micro captions: "No speed-up · 1×" / "CONTROL · 0:00"
- Color is almost monochrome; functional color only when needed (green check, red fail)

Avoid completely:
- Dark neon "AI lab" backgrounds
- Electric-blue glass UI kits
- Robot / brain / circuit / particle effects
- Cyberpunk gradients
- Generic Inter+purple SaaS look
- Fake futuristic dashboards

The phone screen must show believable Android app UI (Messages, Calendar, Gmail, Swiggy, MakeMyTrip) - not abstract bars.

---

## CLIP 1 - THE HOOK (10-12s)

Open on black.
Text:
"Can an AI agent survive
a day in the life of a real user?"

A realistic Android phone emerges.
Agent interacts: open apps, read, type, scroll, switch apps.

Morning 8:00 AM - Messages, Calendar, Maps, Gmail  
Afternoon 12:30 PM - Search, Docs, Amazon, YouTube  
Evening 7:00 PM - Swiggy, MakeMyTrip, BookMyShow, Amazon  

Camera pulls far back. Huge type:
31 APPS
530 TASKS
28 DAYS
168 CROSS-APP

Then:
ANDROIDLIFE
"Real-phone benchmark for everyday AI agents"

Black out. Subtle UI sounds only. No jargon (no SR/UIQ/ADB/MobileRun).

---

## CLIP 2 - LEADERBOARD (8-10s)

ANDROIDLIFE
60-TASK PUBLIC BENCHMARK
REAL PHONE · REAL TASKS · REAL MODELS

Live race leaderboard (manual-audit success rates):

qwen3.8-27b TEXT …… 61.7%  
qwen3.8-27b VISION … 60.0%  
kimi-k2.6 TEXT ……… 58.3%  
seed-2.0-lite VISION … 53.3%  
gemini-3.1-flash-lite … 41.7%  
gpt-5.6-luna TEXT …… 30.0%

Zoom into top row. Morph dimensions:

SUCCESS …… 61.7%  
STEPS ……… 29.3  
COST ……… $0.12 / task  
BATTERY …… −71% / run  
THERMAL …… 98.2°C CPU

Then:
"Success isn't the whole story."
"Can it actually live on your phone?"
ANDROIDLIFE

Optional micro-beat: flash gemini side-card - 41.7% · 8.3 steps · $0.02/task · −21% battery - to sell the tradeoff.

---

## CLIP 3 - VERIFY / HALLUCINATION (6-8s)

Phone: agent works a MakeMyTrip-style booking task.
Agent UI: "Task completed ✓" (brief celebrate).
Freeze.
"VERIFYING DEVICE STATE…"
Expected: Flight reservation saved ✓  
Actual: No reservation found ✗  
FAIL
"AndroidLife doesn't trust the agent's claim."
"Success is verified on-device."
ANDROIDLIFE
"Real phone. Real state. Real evaluation."

Tone: slightly dramatic, still research-serious.

---

## Local alternative

Already implemented as screen-recordable HTML:

- `website/marketing/clips/clip1-hook.html`
- `website/marketing/clips/clip2-leaderboard.html`
- `website/marketing/clips/clip3-verify.html`

Open hub: `website/marketing/clips/index.html`
