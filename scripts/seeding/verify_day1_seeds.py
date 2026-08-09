#!/usr/bin/env python3
"""Verify the Day-1 runnable seeds are good to go on the real phone.

Two halves, printed as shared CHECK lines (parsed like device_health_check.py):

  (1) CONFIG: every Day-1 prompt placeholder, ASK USER fact, and seed-spec
      {key} on the runnable 530 Day-1 set resolves from config/user.yaml
      (the same REQUIRED set verify_config.py checks).
  (2) DEVICE: every fabricated Day-1 seed that should be on-device is actually
      there, via ADB:
        - calendar events (Lunch with Maa / Weekly_Standup / Old_Gym_Class / meeting)
        - Obsidian 'stock note title' note in the vault
        - Camera seed photos (pizza1-5, today_1-5, hide_me)
        - Screenshot seeds (old_shot_1-4)
        - persona contacts (Maa / Airtel / Jio) + birthday contacts
        - the seeded SMS ticket message
        - Day 2 additionally: the invoice PDF, the fabricated {contact} email (so
          the photo-email branch can trigger), and the operator caption check

Run:  uv run python scripts/verify_day1_seeds.py [--serial SERIAL]
Exit: 0 if all PASS/WARN, 1 if any FAIL.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from DailyBench.user_config import load_user_config, parse_flat_config, template_keys  # noqa: E402

DATASET_530 = REPO_ROOT / "benchmarks" / "dailyBench-600" / "DailyBench_530_v1.json"
FACTS = REPO_ROOT / "benchmarks" / "dailyBench-600" / "ask_user_facts_730.json"
MANIFEST_SCRIPT = REPO_ROOT / "scripts" / "seeding" / "build_day_seed_manifest.py"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seeding" / "seed_data.py"
CONFIG_PATH = REPO_ROOT / "config" / "user.yaml"
VARS_LOCAL = REPO_ROOT / "benchmarks" / "dailyBench-600" / "tasks_vars.local.env"
NON_CONFIG_TEMPLATES = {"today's date"}

sys.path.insert(0, str(REPO_ROOT / "scripts" / "seeding"))
import device_paths  # noqa: E402  (auto-detect vault/camera per device)

CAMERA = device_paths.CAMERA
SCREENSHOTS = device_paths.SCREENSHOTS

CAMERA_SEEDS = [f"pizza{i}.jpg" for i in range(1, 6)] + \
               [f"today_{i}.jpg" for i in range(1, 6)] + ["hide_me.jpg"]
SCREENSHOT_SEEDS = [f"old_shot_{i}.png" for i in range(1, 5)]
PERSONA_CONTACTS = ["Maa", "Airtel", "Jio"]
BIRTHDAY_CONTACTS = ["Harshit", "Hariom", "Hemant"]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def collect_keys(obj) -> set[str]:
    if isinstance(obj, str):
        return set(template_keys(obj))
    if isinstance(obj, dict):
        keys: set[str] = set()
        for v in obj.values():
            keys |= collect_keys(v)
        return keys
    if isinstance(obj, list):
        keys = set()
        for v in obj:
            keys |= collect_keys(v)
        return keys
    return set()


def adb(serial: str, *args: str) -> tuple[int, str]:
    res = subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True)
    return res.returncode, (res.stdout + res.stderr).strip()


def shell(serial: str, cmd: str) -> tuple[int, str]:
    return adb(serial, "shell", cmd)


FAILS: list[str] = []
CHECKS: list[str] = []

# ANSI colors for terminal output (auto-disabled when not a TTY)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _use_color() -> bool:
    return sys.stdout.isatty()


def _col(status: str, text: str) -> str:
    if not _use_color():
        return text
    color = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED}.get(status, "")
    return f"{color}{text}{RESET}"


def report(name: str, status: str, message: str) -> None:
    CHECKS.append(name)
    if status == "FAIL":
        FAILS.append(name)
    print(f"CHECK {name} {_col(status, status)} {message}")


def config_checks(cfg: dict[str, str], day: int = 1) -> None:
    """REQUIRED: placeholders + ASK USER facts + seed spec keys for the day resolve."""
    corpus = json.loads(DATASET_530.read_text(encoding="utf-8"))["tasks"]
    runnable_ids = {t["task_id"] for t in corpus if t.get("day") == day}
    gaps = []
    for t in corpus:
        if t["task_id"] not in runnable_ids:
            continue
        for ph in t.get("placeholders") or []:
            if ph not in cfg:
                gaps.append(f"{t['task_id']}: [{ph}]")
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    for tid, fact in facts.items():
        if tid not in runnable_ids:
            continue
        for key in template_keys(fact):
            if key not in NON_CONFIG_TEMPLATES and key not in cfg:
                gaps.append(f"fact {tid}: {key!r}")
    man = load_module("build_day_seed_manifest", MANIFEST_SCRIPT)
    spec_map = {
        1: man.DAY1_TASKS, 2: man.DAY2_TASKS, 3: man.DAY3_TASKS, 4: man.DAY4_TASKS,
        5: man.DAY5_TASKS, 6: man.DAY6_TASKS,
    }.get(day, {})
    for task_id, spec in spec_map.items():
        for key in sorted(collect_keys(spec)):
            if key not in NON_CONFIG_TEMPLATES and key not in cfg:
                gaps.append(f"seed {task_id}: {key!r}")
    for task_id, files in man.SEED_FILE_TEMPLATES.items():
        for key in sorted(collect_keys(files)):
            if key not in cfg:
                gaps.append(f"seed-file {task_id}: {key!r}")
    if gaps:
        report("config_placeholders", "FAIL", "; ".join(sorted(set(gaps))))
    else:
        report("config_placeholders", "PASS", f"all Day-{day} placeholders, facts, seed keys resolve")


def device_checks(serial: str, cfg: dict[str, str]) -> None:
    # online
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    # date (device-local, so calendar date checks below are host-tz independent)
    rc, out = shell(serial, "date")
    report("device_date", "PASS", out)
    device_date_out = out

    # calendar: presence + date sanity. The "today" events (Lunch / Standup /
    # meeting) must be dated TODAY; Old_Gym_Class is intentionally an outdated
    # series (its UNTIL is in the past). This catches stale-date seed regressions.
    rc, out = shell(serial, "content query --uri content://com.android.calendar/events")
    expected_cal = ["Lunch with Maa", "Weekly_Standup", "Old_Gym_Class", cfg.get("meeting title", "")]
    missing_cal = [t for t in expected_cal if t and t not in out]
    dparts = device_date_out.split()  # e.g. ['Sat','Aug','8','06:48:53','IST','2026']
    _MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    today_local = _dt.date(int(dparts[5]), _MONTHS.index(dparts[1]) + 1, int(dparts[2]))
    stale = []
    for ln in out.splitlines():
        if not ln.startswith("Row:"):
            continue
        m = re.search(r"title=(.*?)(?: dtstart=(\d+)|$)", ln)
        if not m or not m.group(2):
            continue
        title = m.group(1).strip()
        if title not in expected_cal or title == "Old_Gym_Class":
            continue
        ev = _dt.datetime.fromtimestamp(int(m.group(2)) / 1000).date()
        if ev != today_local:
            stale.append(f"{title}@{ev.isoformat()}")
    cal_ok = not missing_cal and not stale
    cal_msg = f"{len(expected_cal) - len(missing_cal)}/{len(expected_cal)} seeded events present"
    if missing_cal:
        cal_msg += f"; missing: {missing_cal}"
    if stale:
        cal_msg += f"; STALE-DATED: {stale}"
    report("calendar_events", "PASS" if cal_ok else "FAIL", cal_msg)

    # obsidian stock note
    note = cfg.get("stock note title", "")
    vault = device_paths.vault_path(serial, cfg)
    rc, out = shell(serial, f"ls '{vault}'")
    md_files = [ln for ln in out.splitlines() if ln.strip().endswith(".md")]
    ok = any(ln.strip() == f"{note}.md" for ln in md_files)
    report("obsidian_note", "PASS" if ok else "FAIL",
           f"'{note}.md' in vault ({len(md_files)} .md files)")

    # camera seeds
    rc, out = shell(serial, f"ls {CAMERA}")
    missing_cam = [f for f in CAMERA_SEEDS if f not in out]
    report("camera_seeds", "PASS" if not missing_cam else "FAIL",
           f"{len(CAMERA_SEEDS) - len(missing_cam)}/{len(CAMERA_SEEDS)} photos present"
           + (f"; missing: {missing_cam}" if missing_cam else ""))

    # screenshot seeds
    rc, out = shell(serial, f"ls {SCREENSHOTS}")
    missing_ss = [f for f in SCREENSHOT_SEEDS if f not in out]
    report("screenshot_seeds", "PASS" if not missing_ss else "FAIL",
           f"{len(SCREENSHOT_SEEDS) - len(missing_ss)}/{len(SCREENSHOT_SEEDS)} screenshots present"
           + (f"; missing: {missing_ss}" if missing_ss else ""))

    # contacts (persona + birthdays)
    rc, out = shell(serial, "content query --uri content://com.android.contacts/data --projection display_name")
    names = [ln.split("display_name=", 1)[-1].split(",")[0].strip().lower()
             for ln in out.splitlines() if "display_name=" in ln]
    missing_contacts = [n for n in PERSONA_CONTACTS + BIRTHDAY_CONTACTS
                        if not any(n.lower() in name for name in names)]
    report("contacts", "PASS" if not missing_contacts else "FAIL",
           f"persona+birthday contacts present"
           + (f"; missing: {missing_contacts}" if missing_contacts else ""))

    # SMS seeded ticket
    rc, out = shell(serial, "content query --uri content://sms --projection body")
    ticket_ok = "confirmed" in out.lower() and "gate" in out.lower()
    report("sms_ticket", "PASS" if ticket_ok else "FAIL",
           "seeded SMS ticket found" if ticket_ok else "no seeded ticket SMS")


def device_checks_day2(serial: str, cfg: dict[str, str]) -> None:
    """Day-2 on-device checks: invoice seed present, hallucination control STILL absent,
    this-week files present, and the {contact} email so the photo-email branch can trigger."""
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    rc, dl = shell(serial, "ls /sdcard/Download")
    report("invoice_pdf", "PASS" if "invoice_seed.pdf" in dl else "FAIL",
           "invoice_seed.pdf in /sdcard/Download" if "invoice_seed.pdf" in dl else "missing invoice_seed.pdf")

    # HALLUCINATION CONTROL guarantee: 'Scan Backup' must NOT exist.
    rc, out = shell(serial, "ls -d /sdcard/Download/'Scan Backup'")
    absent = rc != 0 or "no such" in out.lower() or "not found" in out.lower()
    report("halluc_scan_backup_absent", "PASS" if absent else "FAIL",
           "'Scan Backup' absent (control intact)" if absent else "'Scan Backup' unexpectedly EXISTS!")

    # this-week files (Aug 3-9) so medium__files__001 is satisfiable. Check for ANY
    # file modified within the current week (not a hardcoded name — the old marker
    # 'Google (1)' was a Day-1 Chrome run artifact that reset_phone.py correctly
    # removes, so it can't be relied on after a clean reset).
    import datetime as _dt
    _now = _dt.date.today()
    _week_start = (_now - _dt.timedelta(days=_now.weekday())).isoformat()  # Monday
    _rc, _week_files = shell(
        serial,
        f"find /sdcard/Download -maxdepth 1 -type f -newermt {_week_start} 2>/dev/null | head -1",
    )
    week_ok = bool((_week_files or "").strip())
    report("files_this_week", "PASS" if week_ok else "FAIL",
           f"this-week (>= {_week_start}) files present in Downloads" if week_ok else "no this-week file found")

    # photos-gmail-obsidian__012: {contact} has a fabricated saved email so the
    # "email it to them if so" branch can trigger.
    contact = cfg["contact"]
    seed_mod = load_module("seed_data", SEED_SCRIPT)
    contact_email = seed_mod.CONTACT_EMAIL
    rc, out = shell(serial, "content query --uri content://com.android.contacts/data --projection data1")
    email_ok = contact_email in out
    report("contact_email", "PASS" if email_ok else "FAIL",
           f"'{contact_email}' saved on the '{contact}' contact (email branch reachable)"
           if email_ok else f"no fabricated email on the '{contact}' contact")

    # photos-gmail-obsidian__012: one event photo's caption must mention {contact}.
    # Google Photos captions are app-private, so this is operator-ensured, not ADB-checkable.
    report("event_caption_photo", "WARN",
           f"operator-ensured: a Bhubaneswar-trip event photo caption mentions '{contact}'")


def device_checks_day3(serial: str, cfg: dict[str, str]) -> None:
    """Day-3 on-device checks: Obsidian 'Bedtime' note (the sleep-timer target for
    hard__music-obsidian__077) plus the operator-ensured day-3 seeds."""
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    vault = device_paths.vault_path(serial, cfg)
    rc, out = shell(serial, f"ls '{vault}'")
    ok = "Bedtime.md" in out
    report("obsidian_bedtime", "PASS" if ok else "FAIL",
           "'Bedtime.md' in vault (hard__music-obsidian__077 sleep-timer target)"
           if ok else "missing Bedtime.md")

    rc, content = shell(serial, f"cat '{vault}/Bedtime.md'")
    bedtime = cfg.get("bedtime", "10:30 PM")
    cok = bedtime.lower() in content.lower()
    report("bedtime_content", "PASS" if cok else "FAIL",
           f"Bedtime.md carries '{bedtime}'" if cok
           else f"Bedtime.md missing '{bedtime}' (got {content[:60]!r})")

    # Operator-ensured / app-private day-3 seeds (WARN, not ADB-checkable).
    report("drive_weekly_review", "WARN",
           "operator-ensured: 'Weekly Review' doc to duplicate in Drive (easy__google-drive__001)")
    report("tone_log_note", "WARN",
           "operator-ensured: per-contact tone log in Notes (hard__messages-notes__078)")


def device_checks_day4(serial: str, cfg: dict[str, str]) -> None:
    """Day-4 on-device checks: obsidian add-a-line note, trip + today photos, and
    the duplicate-contact pair for hard__contacts-obsidian__029."""
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    vault = device_paths.vault_path(serial, cfg)
    rc, out = shell(serial, f"ls '{vault}'")
    ok = "Daily Log.md" in out
    report("obsidian_daily_log", "PASS" if ok else "FAIL",
           "'Daily Log.md' in vault (easy__obsidian__003 target)" if ok else "missing Daily Log.md")
    ok = "Photo Log.md" in out
    report("obsidian_photo_log", "PASS" if ok else "FAIL",
           "'Photo Log.md' in vault (hard__gallery-obsidian__035 yesterday count)" if ok else "missing Photo Log.md")

    rc, out = shell(serial, f"ls {CAMERA}")
    missing = [f for f in ("trip_1.jpg", "trip_2.jpg", "trip_3.jpg", "trip_4.jpg") if f not in out]
    report("trip_photos", "PASS" if not missing else "FAIL",
           "trip_1-4.jpg present (medium__gallery__003)" if not missing else f"missing: {missing}")
    missing = [f"today_photo_{i}.jpg" for i in range(1, 6) if f"today_photo_{i}.jpg" not in out]
    report("today_photos", "PASS" if not missing else "FAIL",
           "today_photo_1-5.jpg present (hard__gallery-obsidian__035)" if not missing else f"missing: {missing}")

    # hard__contacts-obsidian__029: duplicate contact pair sharing one number.
    rc, out = shell(serial, "content query --uri content://com.android.contacts/contacts --projection display_name")
    names = out.lower()
    dup_ok = "maa home" in names
    report("duplicate_contact", "WARN" if not dup_ok else "PASS",
           "'Maa Home' duplicate present (merge task)" if dup_ok
           else "operator-ensured: create 'Maa Home' sharing {contact name}'s number in Contacts")


def device_checks_day5(serial: str, cfg: dict[str, str]) -> None:
    """Day-5 on-device checks: obsidian deadline + research notes, tomorrow
    conflict events, and the contact address/company fields."""
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    vault = device_paths.vault_path(serial, cfg)
    rc, out = shell(serial, f"ls '{vault}'")
    ok = "Budget Deadline.md" in out
    report("obsidian_budget_deadline", "PASS" if ok else "FAIL",
           "'Budget Deadline.md' in vault (hard__drive-obsidian-telegram__049)" if ok else "missing Budget Deadline.md")
    ok = "Research Notes.md" in out
    report("obsidian_research_notes", "PASS" if ok else "FAIL",
           "'Research Notes.md' in vault (medium__obsidian__004)" if ok else "missing Research Notes.md")

    rc, out = shell(serial, "content query --uri content://com.android.calendar/events --projection title")
    missing = [t for t in ("Team_Conflict_A", "Team_Conflict_B", "Early_Bird_Standup") if t not in out]
    report("day5_calendar", "PASS" if not missing else "FAIL",
           "tomorrow conflict + early-bird events present" if not missing else f"missing: {missing}")
    missing = [t for t in ("Next_Week_30m", "Next_Week_1h", "Next_Week_90m") if t not in out]
    report("day5_nextweek", "PASS" if not missing else "FAIL",
           "next-week meetings present (medium__calendar__002)" if not missing else f"missing: {missing}")

    rc, out = shell(serial, "content query --uri content://com.android.contacts/data --projection data1:data3")
    addr_ok = "751003" in out
    report("contact_address", "PASS" if addr_ok else "FAIL",
           "persona contact has a saved address (easy__contacts__005)" if addr_ok else "no postal address on persona contact")
    comp_ok = "Airtel" in out
    report("contact_company", "PASS" if comp_ok else "FAIL",
           "persona contact has a company field (medium__contacts-obsidian__001)" if comp_ok else "no company field on persona contact")


def device_checks_day6(serial: str, cfg: dict[str, str]) -> None:
    """Day-6 on-device checks: all-day + no-reminder + clash events, old files in
    Downloads, and the duplicate-email pair."""
    rc, out = adb(serial, "get-state")
    report("device_online", "PASS" if rc == 0 else "FAIL", out or serial)

    rc, out = shell(serial, "content query --uri content://com.android.calendar/events --projection title")
    missing = [t for t in ("AllDay_Planning_Retreat", "AllDay_Team_Offsite") if t not in out]
    report("allday_events", "PASS" if not missing else "FAIL",
           "all-day events present (easy__calendar__003)" if not missing else f"missing: {missing}")
    missing = [t for t in ("No_Reminder_Sync", "No_Reminder_Review", "No_Reminder_1o1") if t not in out]
    report("no_reminder_events", "PASS" if not missing else "FAIL",
           "no-reminder events present (medium__calendar__003)" if not missing else f"missing: {missing}")
    missing = [t for t in ("Alarm_Clash_Event", "Availability_AM", "Availability_PM") if t not in out]
    report("day6_calendar", "PASS" if not missing else "FAIL",
           "clash + availability events present" if not missing else f"missing: {missing}")

    rc, dl = shell(serial, "ls /sdcard/Download")
    missing = [f"old_doc_{i}.txt" for i in range(1, 4) if f"old_doc_{i}.txt" not in dl]
    report("old_files", "PASS" if not missing else "FAIL",
           "old_doc_1-3.txt present (medium__files__002)" if not missing else f"missing: {missing}")

    rc, out = shell(serial, "content query --uri content://com.android.contacts/data --projection data1")
    email_ok = seed_contact_email_value() in out
    report("duplicate_email", "PASS" if email_ok else "FAIL",
           f"'{seed_contact_email_value()}' on persona contact (medium__contacts__005)" if email_ok else "no fabricated email to duplicate")


def seed_contact_email_value() -> str:
    """The fabricated persona email used across seeds (imported lazily to avoid
    a hard dependency on seed_data internals at import time)."""
    seed_mod = load_module("seed_data", SEED_SCRIPT)
    return seed_mod.CONTACT_EMAIL


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", default=None)
    ap.add_argument("--day", type=int, default=1, help="Day to verify (1/2/3/4/5/6 = that day's seeds).")
    args = ap.parse_args()
    serial = args.serial
    if not serial:
        rc, out = adb("", "devices")
        lines = [l.split("\t") for l in out.splitlines() if "\tdevice" in l]
        serial = lines[0][0] if lines else None
    if not serial:
        print("CHECK serial FAIL no device connected")
        return 1

    cfg = load_user_config(CONFIG_PATH)
    vars_local = parse_flat_config(VARS_LOCAL.read_text(encoding="utf-8")) if VARS_LOCAL.exists() else {}
    cfg = {**cfg, **vars_local}  # tasks_vars.local.env wins, matching run-time var resolution
    if args.day == 2:
        config_checks(cfg, day=2)
        device_checks_day2(serial, cfg)
    elif args.day == 3:
        config_checks(cfg, day=3)
        device_checks_day3(serial, cfg)
    elif args.day == 4:
        config_checks(cfg, day=4)
        device_checks_day4(serial, cfg)
    elif args.day == 5:
        config_checks(cfg, day=5)
        device_checks_day5(serial, cfg)
    elif args.day == 6:
        config_checks(cfg, day=6)
        device_checks_day6(serial, cfg)
    else:
        config_checks(cfg, day=1)
        device_checks(serial, cfg)

    verdict = "FAIL" if FAILS else "PASS"
    if _use_color():
        print(f"{BOLD}RESULT {_col(verdict, verdict)}{RESET}")
    else:
        print(f"RESULT {verdict}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
