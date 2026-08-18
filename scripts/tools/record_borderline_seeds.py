#!/usr/bin/env python3
"""Record the 2026-08-18 borderline-solvability seeds (files__012, clock__001,
gmail-notes__045) in the disclosure files:

* .fabricated_test_data.json  (gitignored, authoritative device-side record)
* assets/seeds/manifests/day_XX/<task>/manifest.json
* assets/seeds/manifests/day_XX/day_XX_fabricated_data.jsonl
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEVICE_SERIAL = "RS7XKZDI8HTOJNYL"
VAULT = "/sdcard/Obsidian/Papers vault oneplus "

# --- 1) .fabricated_test_data.json -----------------------------------------
fdt_path = os.path.join(ROOT, ".fabricated_test_data.json")
with open(fdt_path) as f:
    fdt = json.load(f)

new_items = [
    {
        "placeholder": "public sample seeding - >500MB video (medium__files__012)",
        "created": True,
        "what": (
            "520 MB zeros video 'seed_lecture_video.mp4' in /sdcard/Download/ "
            "so medium__files__012 (filter files by type to isolate video files "
            "over 500MB, delete the largest, note size freed) is solvable. "
            "545,259,520 bytes, created 2026-08-18 14:32."
        ),
        "created_at_utc": "2026-08-18T09:02:00Z",
        "identifiers": {
            "path": "/sdcard/Download/seed_lecture_video.mp4"
        },
        "delete_command": (
            f"adb -s {DEVICE_SERIAL} shell rm /sdcard/Download/seed_lecture_video.mp4"
        ),
    },
    {
        "placeholder": "public sample seeding - Recipe note (medium__clock__001)",
        "created": True,
        "what": (
            "Obsidian 'Recipe.md' with timed steps for World's Best Lasagna "
            "(Oven 375 F, Bake 50 min, Rest 10 min, Prep 20 min) so "
            "medium__clock__001 (recipe with timed steps) is solvable on-device "
            "in addition to the real recipe URL in config/user.yaml."
        ),
        "created_at_utc": "2026-08-18T09:00:00Z",
        "identifiers": {
            "path": f"{VAULT}Recipe.md"
        },
        "delete_command": (
            f"adb -s {DEVICE_SERIAL} shell rm '{VAULT}Recipe.md'"
        ),
    },
    {
        "placeholder": "public sample seeding - Myntra coupon email (hard__gmail-notes__045)",
        "created": True,
        "what": (
            "Self-sent Gmail coupon email so hard__gmail-notes__045 (find the "
            "discount-code email before it expires) is solvable on-device. "
            "To: rajceo2031@gmail.com, Subject: 'Your 15 Coupon', Body: 'Use "
            "code FLIP15 expires 2026-08-20'. Sent 2026-08-18 ~14:36 from the "
            "primary Gmail account; verified present in Gmail (All mail, from "
            "'me'). Gmail is app-private: no adb delete - remove via the Gmail "
            "UI (search 'coupon' -> open -> trash), or leave; the task itself "
            "deletes/marks it."
        ),
        "created_at_utc": "2026-08-18T09:06:00Z",
        "identifiers": {
            "subject": "Your 15 Coupon",
            "body": "Use code FLIP15 expires 2026-08-20",
            "to": "rajceo2031@gmail.com",
        },
        "delete_command": (
            "Delete in Gmail UI (search 'coupon' -> open 'Your 15 Coupon' -> trash). "
            "No adb command - Gmail mail is app-private."
        ),
    },
]

existing_placeholders = {i.get("placeholder") for i in fdt["items"]}
added = 0
for item in new_items:
    if item["placeholder"] not in existing_placeholders:
        fdt["items"].append(item)
        added += 1

with open(fdt_path, "w") as f:
    json.dump(fdt, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"[.fabricated_test_data.json] added {added} new item(s) -> total {len(fdt['items'])}")

# --- 2/3) per-task manifest.json updates -----------------------------------
def load_json(p):
    with open(p) as f:
        return json.load(f)

def save_json(p, obj):
    with open(p, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

# day_25/medium__files__012
m25 = os.path.join(ROOT, "assets/seeds/manifests/day_25/medium__files__012/manifest.json")
d25 = load_json(m25)
d25["fabricated_seed_data"] = [{
    "type": "files",
    "location": "/sdcard/Download (real)",
    "value": (
        "seed_lecture_video.mp4 (545,259,520 bytes = 520 MB zeros) so the agent "
        "can filter video files over 500MB, identify the largest, delete it, and "
        "note the size freed. (120 MB seed_large_video.mp4 also present for "
        "medium__files__010.)"
    ),
    "status": "seeded",
}]
d25["seed_device_paths"] = {"/sdcard/Download/seed_lecture_video.mp4": "520 MB video"}
d25["delete_command"] = "adb -s RS7XKZDI8HTOJNYL shell rm /sdcard/Download/seed_lecture_video.mp4"
save_json(m25, d25)
print("[day_25/medium__files__012] marked seeded")

# day_3/medium__clock__001
m3 = os.path.join(ROOT, "assets/seeds/manifests/day_3/medium__clock__001/manifest.json")
d3 = load_json(m3)
d3["fabricated_seed_data"] = [
    {
        "type": "web",
        "location": "real web via Chrome",
        "value": (
            "The 'World's Best Lasagna https://www.allrecipes.com/recipe/23600/"
            "worlds-best-lasagna/' page has 5 explicit timed steps (simmer 1.5h, "
            "boil noodles 8-10m, bake 25m+25m, rest 15m)."
        ),
        "status": "web",
    },
    {
        "type": "obsidian",
        "location": "/sdcard/Obsidian/Papers vault oneplus /Recipe.md",
        "value": (
            "Recipe.md: 'Worlds Best Lasagna - Oven: 375 F / Bake: 50 minutes / "
            "Rest: 10 minutes before serving / Prep: 20 minutes' so the recipe's "
            "timed steps are findable on-device without opening the URL."
        ),
        "status": "seeded",
    },
]
d3["seed_device_paths"] = {f"{VAULT}Recipe.md": "recipe timed steps"}
d3["delete_command"] = "adb -s RS7XKZDI8HTOJNYL shell rm '" + VAULT + "Recipe.md'"
save_json(m3, d3)
print("[day_3/medium__clock__001] Recipe.md seed recorded")

# day_17/hard__gmail-notes__045
m17 = os.path.join(ROOT, "assets/seeds/manifests/day_17/hard__gmail-notes__045/manifest.json")
d17 = load_json(m17)
d17["fabricated_seed_data"] = [{
    "type": "gmail",
    "location": "Gmail (primary account, app-private)",
    "value": (
        "Self-sent coupon email: To rajceo2031@gmail.com, Subject 'Your 15 "
        "Coupon', Body 'Use code FLIP15 expires 2026-08-20' (sent 2026-08-18 "
        "~14:36, verified present). Agent searches Gmail for the discount-code "
        "email, reads FLIP15 + expiry 2026-08-20."
    ),
    "status": "seeded",
}]
d17["seed_device_paths"] = {}
d17["delete_command"] = (
    "Delete in Gmail UI (search 'coupon' -> open 'Your 15 Coupon' -> trash). "
    "Gmail is app-private - no adb delete."
)
save_json(m17, d17)
print("[day_17/hard__gmail-notes__045] marked seeded")

# --- 4) per-day jsonl: refresh the 3 task records ---------------------------
def refresh_jsonl(jsonl_path, task_id, new_manifest):
    with open(jsonl_path) as f:
        lines = f.readlines()
    out = []
    changed = False
    for ln in lines:
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        rec = json.loads(ln)
        if rec.get("task_id") == task_id:
            rec["fabricated_seed_data"] = new_manifest["fabricated_seed_data"]
            rec["seed_device_paths"] = new_manifest.get("seed_device_paths", {})
            rec["delete_command"] = new_manifest.get("delete_command")
            changed = True
        out.append(json.dumps(rec, ensure_ascii=False))
    if changed:
        with open(jsonl_path, "w") as f:
            f.write("\n".join(out) + "\n")
        print(f"[{os.path.basename(jsonl_path)}] refreshed {task_id}")
    else:
        print(f"[{os.path.basename(jsonl_path)}] WARNING: {task_id} not found")

refresh_jsonl(os.path.join(ROOT, "assets/seeds/manifests/day_25/day_25_fabricated_data.jsonl"), "medium__files__012", d25)
refresh_jsonl(os.path.join(ROOT, "assets/seeds/manifests/day_3/day_3_fabricated_data.jsonl"), "medium__clock__001", d3)
refresh_jsonl(os.path.join(ROOT, "assets/seeds/manifests/day_17/day_17_fabricated_data.jsonl"), "hard__gmail-notes__045", d17)

print("DONE")
