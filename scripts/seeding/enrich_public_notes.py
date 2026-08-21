"""Enrich the public sample's Obsidian notes into realistic, text-heavy docs.

The public sample's file-reading tasks read terse 3-6 line notes where the
answer value is the only content on the page. Real Obsidian notes carry far
more context, so each note is regenerated as a fuller, realistic document with
the key answer value preserved but no longer the only text visible.

Notes enriched (answer value kept EXACTLY):
- Budget Deadline.md   -> finalised by 2026-08-10, Last reviewed 2026-07-10
                          (hard__drive-notes-telegram__010 / -obsidian-telegram__049)
- Exam Scores.md       -> Midterm 82/100@30%, Final 91/100@50%, Quiz 74/100@20%,
                          passing threshold 60 (medium__calculator__001)
- Monthly Budget.md    -> income 25,000; Rent 8,000/Food 6,000/Transport 2,500/
                          Shopping 2,000/Bills 1,500; total 20,000 (medium__calculator__002)
- Shared Bill.md       -> bill 9,000 INR; units 120/80/60/40 (medium__calculator__005)
- Stock Watch.md       -> Reliance Industries, threshold 1,400 INR, last 1,320.50
                          on 2026-08-13 (hard__google-search-obsidian-telegram__057)
- Recipe.md            -> Oven 375 F, Prep 20 / Bake 50 / Rest 10 min
                          (medium__clock__001)
- Food Favourites.md   -> keeps ## Pancakes / ## Pizza / ## Veggie Bowl headings
                          (medium__gallery__007)
- Contact Updates.md   -> Dad Evalueserve +91 00030 30301, Yuvraj Singh Jio
                          +91 00030 30302 (hard__contacts-obsidian__029)
- Bedtime.md           -> sleep-routine record: bedtime 10:30 PM, wake 6:30 AM,
                          lo-fi beats by Chillhop (Chillhop Lofi Beats - Sleep
                          Mix on YouTube Music / Lo-Fi Sleep Beats on Amazon),
                          recent nights logged (hard__music-obsidian__077)

Pure-python; pushes to the device vault and media-scans. Writes templates to
assets/seeds/public/notes/ so the enrichment is reproducible.

Usage:
    python scripts/seeding/enrich_public_notes.py [--serial 100.108.15.119:5555] [--no-push]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = REPO_ROOT / "assets" / "seeds" / "public" / "notes"
DEFAULT_SERIAL = "100.108.15.119:5555"
VAULT = "/sdcard/Obsidian/Papers vault oneplus /"

NOTES: dict[str, str] = {
    "Budget Deadline.md": """# Budget Deadline

## Shared budget spreadsheet - FY26 finalisation

The family shared budget spreadsheet (the one we all add our monthly spends
to) must be **finalised by 2026-08-10** so the numbers are locked before the
new financial-year planning round starts.

Last reviewed: 2026-07-10.

## To do before finalising
- Make sure everyone has added their spends for June and July.
- Categorise the ~7 uncategorised rows in the misc column.
- Cross-check the rent + utilities split against last month.
- Export a PDF copy to Drive for the family group once locked.
""",
    "Exam Scores.md": """# Exam Scores

## Data Structures & Algorithms - Spring 2026

Term grades for the DSA course. The weighted average is what counts for the
final letter grade.

- Midterm: 82/100 (weight 30%)
- Final: 91/100 (weight 50%)
- Quiz: 74/100 (weight 20%)

Passing threshold: 60

## Notes
- Final exam had a small curve (+4 marks).
- Quiz 3 was dropped (lowest quiz score of the term).
- Assignment scores live on the course portal, not in this note.
""",
    "Monthly Budget.md": """# Monthly Budget

Budget for this month, tracked manually before I move everything into the
shared spreadsheet at month end.

Monthly income: ₹25,000

Expenses:
- Rent: ₹8,000
- Food: ₹6,000
- Transport: ₹2,500
- Shopping: ₹2,000
- Bills: ₹1,500

Total expenses: ₹20,000

## Leftover
- Surplus this month: ₹5,000 (income minus total expenses).
- Plan: move ₹3,000 to savings, keep ₹2,000 as a buffer.

## Notes
- Food is over by ~₹600 vs last month (ordered out a lot).
- Transport is down because I've been taking the metro.
""",
    "Shared Bill.md": """# Shared Bill

## Electricity bill - August 2026

Total bill for the flat this month: 9,000 INR (BESCOM, bill ref BES-2026-0812).

Units consumed this billing cycle:
- Yuvraj Airtel: 120 units
- Yuvraj Singh Jio: 80 units
- Maa: 60 units
- Dad: 40 units

## Notes
- Meter reading was taken on the 1st of the month.
- The split is proportional to units consumed; pay the account holder
  (Yuvraj Airtel) by the 10th.
- Water and internet are billed separately.
""",
    "Stock Watch.md": """# Stock Watch

Watchlist for the stocks I follow. I only act when a ticker crosses its
threshold since the last recorded value.

- Stock: Reliance Industries
- Threshold: 1,400 INR
- Last recorded value: 1,320.50 INR
- Date: 2026-08-13

## Watchlist rules
- If the price crosses the threshold, message the group and update this note
  with today's value.
- Re-check on the day I'm tracking; don't chase intraday noise.
- NSE ticker: RELIANCE.

## Other tickers I follow
- TCS: threshold 4,000 (currently ~3,950).
- HDFC Bank: threshold 1,700 (currently ~1,680).
""",
    "Recipe.md": """# Recipe

## World's Best Lasagna

My go-to weekend lasagna. Feeds 6-8. It took years to get right - save this one.

### Timing
- Prep: 20 minutes
- Bake: 50 minutes
- Rest: 10 minutes before serving

### Oven
- Oven: 375 F (190 C), middle rack.

### Ingredients
- 12 lasagna noodles
- 450g ground beef
- 1 onion, diced
- 3 cloves garlic, minced
- 700g tomato passata
- 2 tbsp tomato paste
- 1 tsp dried oregano
- 1 tsp dried basil
- 250g ricotta
- 300g shredded mozzarella
- 100g grated parmesan
- 1 egg
- Salt and pepper to taste

### Method
1. Brown the beef with onion and garlic; add passata, paste, and herbs; simmer.
2. Mix the ricotta with the egg and half the parmesan.
3. Layer noodles, meat sauce, and ricotta mix; top with mozzarella and parmesan.
4. Cover and bake at 375 F for 35 min, then uncover and bake 15 more (50 min total).
5. Rest 10 minutes before slicing.
""",
    "Food Favourites.md": """# Food Favourites

Quick reference of my favourite food photos pulled from Google Photos. Keep
these in sync with the album - one photo per dish, added from Google Photos
Favourites by matching the photo description to the heading.

## Pancakes

## Pizza

## Veggie Bowl
""",
    "Contact Updates.md": """# Contact Updates

Numbers that changed recently - update Contacts when you see these.

- Dad Evalueserve: +91 00030 30301
- Yuvraj Singh Jio: +91 00030 30302

## Notes
- Dad's office line; reachable only in the evening.
- Jio is the second SIM; WhatsApp is on the same number.
""",
    "Bedtime.md": """# Bedtime

## Sleep routine record
What I listen to wind down and my sleep timings - kept as a log so I can see
what's working and when I'm actually getting to bed.

## Wind-down music
- Genre: lo-fi beats (go-to artist: Chillhop)
- Sleep playlist (YouTube Music): Chillhop Lofi Beats - Sleep Mix
- Back-up sleep playlist (Amazon Music): Lo-Fi Sleep Beats
- Volume low (~20%), repeat off (single track)

## Sleep timings
- Bedtime: 10:30 PM
- Wake-up: 6:30 AM
- Sleep goal: ~8 hours

## Recent log
- 2026-08-18 (Mon): 10:30 PM - Chillhop Lofi Beats - Sleep Mix, asleep by ~11:15 PM
- 2026-08-19 (Tue): 10:30 PM - Lo-Fi Sleep Beats (Amazon Music), asleep by ~11:00 PM
- 2026-08-20 (Wed): 10:30 PM - Chillhop Lofi Beats - Sleep Mix, asleep by ~10:55 PM
- 2026-08-21 (Thu): 10:30 PM - Chillhop lo-fi track with sleep timer, stopped on time

## Habit
- Start a Chillhop lo-fi track before bed, let the sleep timer stop it at bedtime.
""",
}


def adb(serial: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich public-sample Obsidian notes to realistic text-heavy docs.")
    ap.add_argument("--serial", default=DEFAULT_SERIAL, help="ADB device serial (default: wireless).")
    ap.add_argument("--no-push", action="store_true", help="Only write templates to assets/seeds/public/notes, do not push.")
    args = ap.parse_args()

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    for fname, content in NOTES.items():
        (NOTES_DIR / fname).write_text(content, encoding="utf-8")
        print(f"wrote {NOTES_DIR / fname} ({len(content)} bytes)")

    if not args.no_push:
        adb(args.serial, "shell", "mkdir", "-p", VAULT)
        for fname, content in NOTES.items():
            tmp = NOTES_DIR / fname
            r = adb(args.serial, "push", str(tmp), VAULT + fname)
            print(f"  push {fname}: {r.stdout.strip() or r.returncode}")
        adb(args.serial, "shell", "content", "call", "--uri", "content://media/none",
            "--method", "scan_volume", "--arg", "external_primary")
        print("pushed all notes to the Obsidian vault and media-scanned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
