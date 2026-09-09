# Device reset + seed (public 60-task)

Return the OnePlus CPH2423 to a known baseline, then push fabricated seeds before a public run.
Canonical serial (Tailscale): `100.108.15.119:5555`. Never use the Xiaomi Pad.

Operator skill with edge cases / UI-only checks:
[`.agents/skills/reset-phone/SKILL.md`](../.agents/skills/reset-phone/SKILL.md) ·
GUI checklist: [pre-run-checklist.md](pre-run-checklist.md).

## 1. Connect

```bash
S=100.108.15.119:5555
adb connect "$S"
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
uv run python - <<'PY'
import datetime, subprocess
from zoneinfo import ZoneInfo
S = "100.108.15.119:5555"
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
print("seeded", tomorrow)
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
pkill -f 'androidlife_tasks.py|dailybench_tasks.py'; pkill -f 'androidlife_runner.py|dailybench_runner.py'; pkill -f 'phoenix serve'
rm -rf "assets/runs/public/<RUN_TS>" "assets/db/public/<RUN_TS>"
rm -f "assets/runs/public/batch-<RUN_TS>.log" "assets/runs/public/phoenix-<RUN_TS>.log"
# then repeat §2–§4 before the next launch
```
