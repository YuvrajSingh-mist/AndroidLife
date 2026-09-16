# Device reset + seed

Return the benchmark phone (reference: OnePlus CPH2423) to a known baseline, then push fabricated seeds before a scored run.

**Run every command from the repo root** (`cd` into your `AndroidLife` clone). Paths are relative; the only host-specific value is your ADB serial.

## Which protocol?

| Tier | When | Profile / seeds | Launch |
|---|---|---|---|
| **Public benchmark (60)** | Before every scored public batch | `public_v2` + days **1–3** + enrich notes + public PDFs + verify (§2–§4 below) | [README · Run the public 60](../README.md#run-the-public-60-operator-path) |
| **Full dataset (530)** | Before each day / campaign slice on the 28-day schedule | Reset to undo agent side-effects, then `seed_data.py --day N` + day verify — **not** the public enrich/PDF path | [README · 530-day schedule](../README.md#530-day-schedule-optional) |

`public_v2` is for the **public benchmark only**. Do not treat public enrich/PDF steps as a stand-in for the full 530 corpus.

---

## Public benchmark (60-task) — full sequence

The sections below are the public-60 operator path.

```bash
# pick the connected phone (USB or wireless) — works on any machine
export S="$(adb devices | awk '/\tdevice$/{print $1; exit}')"
test -n "$S" || { echo "No adb device in 'device' state — connect/pair first"; exit 1; }
echo "Using serial: $S"
```

Maintainer note: wireless debugging ports change after re-pair; Tailscale / LAN IPs are **not** portable — always resolve `$S` from `adb devices` on your machine.

Operator skill with edge cases / UI-only checks:
[`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md) ·
GUI checklist: [pre-run-checklist.md](pre-run-checklist.md).

## 1. Connect

```bash
adb devices -l
adb -s "$S" shell echo OK
```

## 2. Reset (undo agent side-effects)

```bash
# dry-run first (optional)
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2

# apply
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --apply
```

Soft-delete common run-created calendar titles the profile can miss:

```bash
for t in "Get-together with friends" "IndiGo 6E-6737 Flight - BBI to DEL" "Review July Photos"; do
  adb -s "$S" shell content delete --uri content://com.android.calendar/events --where "'title=\"$t\"'"
done
```

## 3. Seed (ADB-pushable data)

```bash
uv run python scripts/seeding/seed_data.py --serial "$S" --day 1
uv run python scripts/seeding/seed_data.py --serial "$S" --day 2
uv run python scripts/seeding/seed_data.py --serial "$S" --day 3
uv run python scripts/seeding/enrich_public_notes.py --serial "$S"   # public Obsidian baselines
uv run python scripts/seeding/fabricate_public_pdfs.py --serial "$S" # Invoice + Rent Receipt
```

Re-seed **tomorrow afternoon** conflicts (`easy__calendar__002`):

```bash
uv run python - <<PY
import datetime, os, subprocess
from zoneinfo import ZoneInfo
S = os.environ["S"]
tz = ZoneInfo("Asia/Kolkata")
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
CAL = "content://com.android.calendar/events"
def sh(*a):
    return subprocess.run(["adb", "-s", S, "shell", *a], capture_output=True, text=True)
def ms(d, h, m):
    return int(datetime.datetime(d.year, d.month, d.day, h, m, tzinfo=tz).timestamp() * 1000)
for t in ("Team Sync", "Mentor 1 on 1", "Team_Conflict_A", "Team_Conflict_B"):
    for _ in range(6):
        sh("content", "delete", "--uri", CAL, "--where", f"'title=\"{t}\"'")
def ins(t, h0, m0, h1, m1):
    sh("content", "insert", "--uri", CAL, "--bind", "calendar_id:i:16",
       "--bind", f"title:s:'{t}'", "--bind", f"dtstart:l:{ms(tomorrow, h0, m0)}",
       "--bind", f"dtend:l:{ms(tomorrow, h1, m1)}", "--bind", "allDay:i:0",
       "--bind", "hasAlarm:i:0", "--bind", "eventTimezone:s:Asia/Kolkata")
ins("Team Sync", 14, 0, 15, 0)
ins("Mentor 1 on 1", 14, 30, 15, 30)
print("seeded", tomorrow, "on", S)
PY
```

## 4. Verify (gate — do not launch on FAIL)

```bash
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --verify-only
for d in 1 2 3; do
  uv run python scripts/seeding/verify_day1_seeds.py --serial "$S" --day "$d"
done
```

Expect **RESULT PASS** on baseline and each day. Operator WARNs (Photos caption, Drive doc, etc.) are UI/cloud — see pre-run checklist.

## 5. After cancel / wipe a run

```bash
pkill -f 'androidlife_tasks.py|androidlife_tasks.py'; pkill -f 'androidlife_runner.py|androidlife_runner.py'; pkill -f 'phoenix serve'
rm -rf "assets/runs/public/<RUN_TS>" "assets/db/public/<RUN_TS>"
rm -f "assets/runs/public/batch-<RUN_TS>.log" "assets/runs/public/phoenix-<RUN_TS>.log"
# then repeat §2–§4 before the next launch
```

---

## Full dataset (530) — per-day outline

For a day `N` on the 28-day schedule (details / edge cases: [`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md)):

```bash
export S="$(adb devices | awk '/\tdevice$/{print $1; exit}')"

# undo prior agent side-effects (same script; avoid public-only enrich/PDF unless that day needs them)
uv run python scripts/seeding/reset_phone.py --serial "$S" --profile public_v2 --apply

uv run python scripts/seeding/seed_data.py --serial "$S" --day "$N"
uv run python scripts/seeding/verify_day1_seeds.py --serial "$S" --day "$N"
# finish any UI/cloud seeds for that day’s tasks (pre-run-checklist.md), then launch:
#   README → “530-day schedule (optional)”
```

Date-relative calendar events and app-private seeds still need the same operator care as public runs; only the **scope of days** and **launch flags** change.
