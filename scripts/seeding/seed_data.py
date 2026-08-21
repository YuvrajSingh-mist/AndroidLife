#!/usr/bin/env python3
"""Seed the Day-1 fabricated data onto the device (sanity-check run, 2026-08-05).

For every seedable-by-ADB task the script:
  1. materialises the literal fabricated files into
     seeds/day_<N>/  (flat folder of real artifacts: photos/pdf/notes),
     and
  2. pushes them to the device with the correct mtime (so Gallery/Messages sort them
     as "today", "~1h ago", ">1 month old" respectively).

Things that cannot be seeded via ADB (app-private / blocked content-insert) are
attempted and their result reported honestly:
  - SMS insert (content://sms)  - usually blocked on non-rooted
  - call-log insert (content://call_log/calls) - usually allowed

Generalized with `--day` (default 1). Day 2 seeds the ADB-seedable invoice PDF for
hard__files-notes__011 and the fabricated {contact} email address for
hard__photos-gmail-obsidian__012 (everything else on Day 2 is web / real state /
app-private / operator-ensured).

Run:  uv run python scripts/seed_data.py --serial RS7XKZDI8HTOJNYL --day 2
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "seeding"))
from DailyBench.user_config import load_user_config  # noqa: E402
import device_paths  # noqa: E402  (auto-detect vault/calendar/email per device)

DAY_DIR = REPO_ROOT / "assets" / "seeds" / "day_1"
CAMERA = device_paths.CAMERA
SCREENSHOTS = device_paths.SCREENSHOTS
CONFIG_PATH = REPO_ROOT / "config" / "user.yaml"

NOW = time.time()
TODAY = time.strftime("%Y-%m-%d", time.localtime(NOW))
ONE_HOUR_AGO = NOW - 3600
OLD_MONTH = "2026-05-20"  # well over a month before 2026-08-05


# ---------------------------------------------------------------------------
# minimal pure-Python PNG writer (solid color, no deps)
# ---------------------------------------------------------------------------
def write_png(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    idat = zlib.compress(raw)
    path.write_bytes(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def mtime_seconds(stamp: str) -> int:
    """Parse an ISO local timestamp into epoch seconds (matches the shell date)."""
    return int(time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M:%S")))


def write_invoice_pdf(path: Path) -> None:
    """Minimal valid one-page PDF (pure python, no deps) - a fabricated invoice.

    hard__files-notes__011 (ASK USER) needs "the most recent invoice PDF" in Files
    with a total amount + a past due date, so the agent extracts them and applies the
    user-specified late fee. The due date (2026-07-25) is in the past relative to
    Aug 2026 so the late-fee branch is exercised.
    """
    content = (
        "BT /F1 16 Tf 72 730 Td (INVOICE) Tj ET\n"
        "BT /F1 10 Tf 72 700 Td (Invoice #: INV-2026-071) Tj ET\n"
        "BT /F1 10 Tf 72 682 Td (Bill To: Yuvraj Singh) Tj ET\n"
        "BT /F1 10 Tf 72 664 Td (Item: Web Hosting - Annual Plan) Tj ET\n"
        "BT /F1 10 Tf 72 646 Td (Amount Due: Rs. 1,240.00) Tj ET\n"
        "BT /F1 10 Tf 72 628 Td (Due Date: 2026-07-25) Tj ET\n"
        "BT /F1 9 Tf 72 598 Td (Please pay the total by the due date to avoid a late fee.) Tj ET\n"
    ).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode() + b"0000000000 65535 f \n"
    out += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


def write_boarding_pass_pdf(path: Path) -> None:
    """Minimal valid one-page PDF (pure python, no deps) - a fabricated flight ticket.

    easy__files__014 (day 27) needs a flight ticket PDF in Downloads with a flight
    number, date, departure terminal, gate, and boarding time so the agent opens it
    in Files and reads back the terminal + gate + date (a realistic "people interact
    with PDFs a lot" task - no editing, just open + read).
    """
    content = (
        "BT /F1 16 Tf 72 730 Td (BOARDING PASS) Tj ET\n"
        "BT /F1 10 Tf 72 700 Td (Passenger: Yuvraj Singh) Tj ET\n"
        "BT /F1 10 Tf 72 682 Td (Flight: 6E 2042) Tj ET\n"
        "BT /F1 10 Tf 72 664 Td (Route: BBI - DEL) Tj ET\n"
        "BT /F1 10 Tf 72 646 Td (Date: 2026-08-20) Tj ET\n"
        "BT /F1 10 Tf 72 628 Td (Departure Terminal: T3) Tj ET\n"
        "BT /F1 10 Tf 72 610 Td (Gate: B4) Tj ET\n"
        "BT /F1 10 Tf 72 592 Td (Boarding Time: 07:45 AM) Tj ET\n"
        "BT /F1 9 Tf 72 562 Td (Please arrive at the gate 30 minutes before boarding.) Tj ET\n"
    ).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode() + b"0000000000 65535 f \n"
    out += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))


# ---------------------------------------------------------------------------
# seed definitions: task_id -> list of (filename, [w,h], rgb, mtime_iso, dest_dir)
# ---------------------------------------------------------------------------
def make_seed_images() -> None:
    def img(task: str, fname: str, rgb: tuple[int, int, int], mtime: str, dest: str, size=(64, 64)):
        if not (REPO_ROOT / "assets" / "seeds" / "manifests" / "day_1" / "manifest_index.json").exists():
            print(f"  [skip] {task}: no day-1 manifest (not built) - not materialising {fname}")
            return None, mtime, dest
        DAY_DIR.mkdir(parents=True, exist_ok=True)
        p = DAY_DIR / fname
        if not p.exists():
            write_png(p, size[0], size[1], rgb)
        return p, mtime, dest

    import datetime as _dt
    today = _dt.date.today().strftime("%Y-%m-%d")

    # pizza search (medium__gallery__001) - 5 pizza shots, taken today
    pizza_colors = [(180, 40, 30), (200, 90, 40), (160, 30, 20), (220, 120, 60), (190, 70, 35)]
    for i, c in enumerate(pizza_colors, 1):
        img("medium__gallery__001", f"pizza{i}.jpg", c, f"{today} 00:30:00", CAMERA, (96 + i * 8, 64))

    # today's burst for the GIF task (medium__gallery-telegram__001) - 5 photos today
    burst_colors = [(30, 90, 180), (60, 160, 90), (200, 160, 30), (120, 70, 180), (220, 90, 140)]
    for i, c in enumerate(burst_colors, 1):
        img("medium__gallery-telegram__001", f"today_{i}.jpg", c, f"{today} 00:{20+i:02d}:00", CAMERA, (80, 80))

    # ~1h-ago photo to hide (easy__gallery__001)
    img("easy__gallery__001", "hide_me.jpg", (140, 140, 140),
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW - 3600)), CAMERA, (96, 64))

    print("materialised seed images into assets/seeds/day_1/")


def adb(serial: str, *args: str) -> tuple[int, str]:
    res = subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True)
    return res.returncode, (res.stdout + res.stderr).strip()


def _seed_path_for_ls(path: str) -> str | None:
    """Return the real filesystem path to `ls`, or None when the entry is NOT a
    filesystem path (e.g. "Calendar (cal_id=16): event titled X") and therefore
    must be verified by hand / verify_day1_seeds.py instead.

    Manifest entries sometimes annotate a range, e.g. "pizza1.jpg (and pizza2-5.jpg)" - the
    parenthetical is documentation, not part of the path, so it is stripped before `ls`.
    """
    path = (path or "").strip()
    if not path.startswith("/"):
        return None
    m = re.search(r"^(/.*?)\s*\(and .*\)\s*$", path)
    return m.group(1) if m else path


def verify_day_seeds(serial: str, day: int) -> int:
    """Verify (device-state, not just config) that every seed a day's tasks
    declare is actually present on the phone.

    Reads seeds/manifests/day_N/manifest_index.json, then for each task's
    manifest:
      - checks every entry in `seed_device_paths` with `adb shell ls` (these
        are the ADB-pushable files, so they can be confirmed on the device), and
      - flags every `fabricated_seed_data` entry with status `needs_ui` as
        UNVERIFIED: those are server-side / operator-action seeds (e.g. a real
        Google Drive doc) that cannot be confirmed via adb — the operator must
        create them manually, and a silent skip is exactly how a missing Drive
        file slipped through before.

    Returns 0 (all present / warnings only) or 1 (missing device paths). This is
    the check that catches "the manifest says /path exists but it was never pushed".
    """
    index = day_seed_dir(day) / "manifest_index.json"
    if not index.exists():
        print(f"  [warn] no assets/seeds/manifests/day_{day}/manifest_index.json - build the day first")
        return 0
    idx = json.loads(index.read_text(encoding="utf-8"))
    task_ids = idx.get("tasks") or []
    missing: list[tuple[str, str]] = []
    unverified: list[tuple[str, str, str]] = []  # (task_id, seed_type, value)
    non_fs: list[tuple[str, str]] = []  # (task_id, seed description) - not a filesystem path
    checked = 0
    for task_id in sorted(task_ids):
        mf = day_seed_dir(day) / task_id / "manifest.json"
        if not mf.exists():
            continue
        man = json.loads(mf.read_text(encoding="utf-8"))
        # 1) ADB-verifiable on-device paths.
        paths = man.get("seed_device_paths") or {}
        for _, raw in sorted(paths.items()):
            ls_path = _seed_path_for_ls(raw)
            if ls_path is None:
                # Not a filesystem path (e.g. "Calendar (cal_id=16): event titled X")
                # - cannot be checked with `ls`; hand it to verify_day1_seeds.py / operator.
                non_fs.append((task_id, raw))
                continue
            checked += 1
            rc, out = adb(serial, "shell", "ls", f"'{ls_path}'")
            if rc != 0 or "No such file" in out or not out.strip():
                missing.append((task_id, raw))
            else:
                print(f"  [ok] {task_id}: {raw}")
        # 2) needs_ui seeds: cannot be confirmed on-device -> warn, don't silently skip.
        for seed in man.get("fabricated_seed_data") or []:
            if seed.get("status") == "needs_ui":
                unverified.append((task_id, seed.get("type", "?"), seed.get("value", "")))
    if missing:
        print(f"\nDEVICE VERIFY FAIL: {len(missing)} declared seed path(s) missing on device:")
        for task_id, path in missing:
            print(f"  - {task_id}: {path}")
        print("Fix: uv run python scripts/seed_data.py --serial <serial> --day "
              f"{day}   (real push, no --no-push)")
        return 1
    if non_fs:
        print(f"\nNOT FILESYSTEM (check via verify_day1_seeds.py / operator):")
        for task_id, raw in sorted(non_fs):
            print(f"  - {task_id}: {raw}")
    if unverified:
        print(f"\nUNVERIFIED: {len(unverified)} needs_ui seed(s) require manual/operator action"
              f" (cannot be confirmed via adb):")
        for task_id, seed_type, value in sorted(unverified):
            print(f"  - {task_id} [{seed_type}]: {value}")
        print("  These are server-side / app-private (e.g. a real Google Drive doc)."
              " Confirm they exist on the account/device before the run.")
    # Only flag UNVERIFIED when there is actually something unverified (needs_ui
    # and/or non-filesystem seeds). With both empty the device is fully verified.
    suffix: list[str] = []
    if non_fs:
        suffix.append(f"{len(non_fs)} non-filesystem seed(s) UNVERIFIED")
    if unverified:
        suffix.append(f"{len(unverified)} needs_ui seed(s) UNVERIFIED (see above)")
    summary = f"\nDEVICE VERIFY PASS: all {checked} declared seed path(s) present on device (day {day})"
    if suffix:
        summary += "; " + " + ".join(suffix)
    print(summary)
    return 0


def seed_auto_day(serial: str, day: int) -> None:
    """Push every ADB-verifiable seed file an auto-generated day declares.

    Reads assets/seeds/manifests/day_N/*/manifest.json, collects every
    `seed_device_paths` entry (all filesystem paths), and pushes the matching
    materialised artifact from assets/seeds/day_N/ to that exact device path.
    Skips non-filesystem seeds (calendar events, contact rows, needs_ui) - those
    are handled by their day-specific functions / the operator.
    """
    d = day_seed_dir(day)
    vault = device_paths.vault_path(serial)
    pushed = 0
    for task_dir in sorted(x for x in d.iterdir() if x.is_dir()):
        mf = task_dir / "manifest.json"
        if not mf.exists():
            continue
        man = json.loads(mf.read_text(encoding="utf-8"))
        for _, raw in sorted((man.get("seed_device_paths") or {}).items()):
            path = _seed_path_for_ls(raw)
            if path is None:
                continue  # non-filesystem (calendar/contact/etc.) - handled elsewhere
            local = _find_materialised_file(day, path)
            if local is None:
                print(f"  [warn] {man.get('task_id')}: no materialised file for {path}")
                continue
            # ensure parent dir exists, then push (vault may not exist yet)
            remote_parent = path.rsplit("/", 1)[0] if "/" in path else ""
            if remote_parent:
                adb(serial, "shell", "mkdir", "-p", remote_parent)
            adb(serial, "push", str(local), path)
            print(f"  pushed {man.get('task_id')}: {local.name} -> {path}")
            pushed += 1
    print(f"seed_auto_day day {day}: pushed {pushed} file(s)")


def _find_materialised_file(day: int, device_path: str) -> Path | None:
    """Match a declared device path back to the materialised seed file on disk.

    SEED_FILE_TEMPLATES write artifacts flat into assets/seeds/day_N/ with the
    template's own filename (e.g. monthly_budget.md), and the device path points
    at `.../{budget note title}.md` (the resolved title). The manifest doesn't
    record the local filename, so we infer it: if a day dir has exactly ONE .md
    file whose content was just built, prefer it; else fall back to a direct
    basename match against the device path.
    """
    art = day_artifacts_dir(day)
    if not art.is_dir():
        return None
    base = device_path.rsplit("/", 1)[-1]
    direct = art / base
    if direct.exists():
        return direct
    # Obsidian notes: vault title on device often differs from the template
    # filename (e.g. 'Monthly Budget.md' vs 'monthly_budget.md'). When a day has
    # a single .md artifact that isn't already claimed, reuse it.
    mds = sorted(p for p in art.glob("*.md") if p.name != "DEVICE_PATHS.md")
    if len(mds) == 1:
        return mds[0]
    # multi-file day: try a slugified basename match (spaces -> underscores)
    for p in art.glob("*.md"):
        if _slugify(p.stem) == _slugify(base):
            return p
    return None


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def push_with_mtime(serial: str, local: Path, remote_dir: str, mtime_iso: str) -> None:
    remote = f"{remote_dir}/{local.name}"
    adb(serial, "push", str(local), remote)
    ts = time.strftime("%Y%m%d%H%M.%S", time.localtime(mtime_seconds(mtime_iso)))
    adb(serial, "shell", "touch", "-t", ts, remote)
    print(f"  pushed {local.name} -> {remote}  (mtime {mtime_iso})")


def mtime_for(fname: str) -> str:
    """Deterministic mtime per filename so Gallery sorts the seeds as intended.
    Relative to the actual run date (not a hardcoded snapshot)."""
    import datetime as _dt
    today = _dt.date.today()
    if fname.startswith("old_shot_"):
        n = int(fname[len("old_shot_"):].split(".")[0])
        old = today - _dt.timedelta(days=40 + n)   # 41-44 days -> >1 month old
        return f"{old} 10:00:00"
    if fname == "hide_me.jpg":
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW - 3600))  # ~1h ago
    return f"{today} 00:30:00"                     # today (pizza / burst)


def push_seed_images(serial: str) -> None:
    print("pushing images...")
    if not DAY_DIR.is_dir():
        print("  (missing assets/seeds/day_1/ - materialise first)")
        return
    for f in sorted(DAY_DIR.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            dest = SCREENSHOTS if f.name.startswith("old_shot") else CAMERA
            adb(serial, "shell", "mkdir", "-p", dest)
            push_with_mtime(serial, f, dest, mtime_for(f.name))
    # rescan media so Gallery picks them up
    adb(serial, "shell", "content", "call", "--uri", "content://media/none", "--method", "scan_volume", "--arg", "external_primary")
    print("  media rescan triggered")


def push_obsidian_seed(serial: str, cfg: dict[str, str]) -> None:
    note_title = cfg["stock note title"]
    print(f"pushing Obsidian '{note_title}' note...")
    sf = DAY_DIR
    note = next((sf / f for f in sorted(sf.iterdir())
                 if f.suffix == ".md" and f.name != "DEVICE_PATHS.md"), None) if sf.is_dir() else None
    if note is None or not note.exists():
        print("  (missing assets/seeds/day_1/ - materialise first)")
        return
    vault = device_paths.vault_path(serial, cfg)
    remote = f"{vault}/{note_title}.md"  # slash AFTER the trailing space -> inside the vault dir
    adb(serial, "shell", "mkdir", "-p", vault)
    adb(serial, "push", str(note), remote)
    print(f"  pushed -> {remote}")
    print("  note contents:")
    print(note.read_text(encoding="utf-8"))


def seed_calendar_events(serial: str, meeting_title: str, cfg: dict[str, str] | None = None) -> None:
    """Seed the Day-1 calendar tasks into the Google-synced calendar (cal_id auto-detected).

    Coverts the three calendar tasks:
      easy__calendar__001        -> the 'Lunch with Maa' event today the agent can add a location to
      medium__calendar__001      -> a recurring NO-attendee event that recurs today,
                                    plus an OUTDATED recurring series (ended last month)
      hard__calendar-telegram-obsidian__002 -> a meeting this week at 08:30 (before 9am,
                                    so the reschedule branch is exercised), titled {meeting title}
    """
    import datetime as _dt

    cal_id = device_paths.calendar_id(serial, cfg)
    today = _dt.date.today()  # run/device date (NOT a hardcoded snapshot)
    wd = today.strftime("%a").upper()[:2]  # e.g. 'SA' for Saturday
    ms = int(_dt.datetime.combine(today, _dt.time.min, tzinfo=_dt.timezone.utc).timestamp() * 1000)
    until = (today - _dt.timedelta(days=40)).strftime("%Y%m%dT000000Z")  # series ended ~6 weeks ago

    def ins(title: str, dtstart_ms: int, dtend_ms: int, rrule: str | None = None) -> None:
        # single-quote wrap on the title too: a title with spaces (e.g.
        # "1:1 with Yuvraj Airtel") must survive the device shell's word-split.
        cmd = ["content", "insert", "--uri", "content://com.android.calendar/events",
               "--bind", f"calendar_id:i:{cal_id}",
               "--bind", f"title:s:'{title}'",
               "--bind", f"dtstart:l:{dtstart_ms}",
               "--bind", f"dtend:l:{dtend_ms}",
               "--bind", "allDay:i:0", "--bind", "hasAlarm:i:0",
               "--bind", "eventTimezone:s:Asia/Kolkata"]
        if rrule:
            # single-quote wrap: the DEVICE shell strips the quotes, so the ';' in
            # the rrule reaches `content` intact instead of being split into commands.
            cmd += ["--bind", f"rrule:s:'{rrule}'"]
        adb(serial, "shell", *cmd)

    h = 3600_000
    day0 = ms - (ms % 86_400_000)  # midnight today UTC (close enough for sanity)
    # idempotent: drop any previously-seeded rows first (title-delete removes ONE
    # matching row per call, so repeat until none remain)
    for t in ("Add_Location_Demo", "Lunch with Maa", "Weekly_Standup", "Old_Gym_Class", "Project_Review", meeting_title, "TeamSync", "ProbeEvent"):
        for _ in range(6):
            adb(serial, "shell", "content", "delete", "--uri", "content://com.android.calendar/events",
                "--where", f"'title=\"{t}\"'")
    # 1. existing event today (easy__calendar__001)
    ins("Lunch with Maa", day0 + 11 * h, day0 + 12 * h)
    # 2a. recurring NO-attendee daily event that recurs on the run day (medium__calendar__001).
    #     A DAILY series starting today guarantees the agent sees a recurring
    #     no-attendee event no matter which weekday the run happens on (a WEEKLY
    #     BYDAY series seeded on a different weekday than the run day caused the
    #     Day-1 false-negative: the event only recurs on the seed day's weekday).
    ins("Weekly_Standup", day0 + 9 * h, day0 + 10 * h,
        rrule="FREQ=DAILY;COUNT=14")
    # 2b. OUTDATED recurring series (ended ~6 weeks ago) -> agent should delete it
    ins("Old_Gym_Class", day0 - 90 * 24 * h + 7 * h, day0 - 90 * 24 * h + 8 * h,
        rrule=f"FREQ=WEEKLY;BYDAY={wd};UNTIL={until}")
    # 3. meeting this week 08:30 (before 9am) for the hard reschedule task
    ins(meeting_title, day0 + 8 * h + 30 * 60_000, day0 + 9 * h + 30 * 60_000)
    print("seeded calendar events into cal_id=16 (Google-synced)")


def cleanup_test_events(serial: str) -> None:
    """Remove the throwaway test events created while probing (local-account TeamSync)."""
    adb(serial, "shell", "content", "delete", "--uri", "content://com.android.calendar/events",
        "--where", "title='TeamSync'")


def seed_contact_email(serial: str, contact_name: str, email: str) -> None:
    """ADB-seed a fabricated email onto the persona {contact} (idempotent).

    hard__photos-gmail-obsidian__012 emails the event photo to {contact} only when
    the caption mentions them; Gmail can only address that if the contact has a
    saved email. This fabricates it on-device (skips if already present).

    NB: the device shell strips single quotes, so string literals in --where must
    be double-quoted inside a single-quoted arg (same pattern as the calendar seed).
    Also, Android 15's `content` command rejects comma-separated projections, so
    single-column projections are used here.
    """
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data",
                  "--projection", "raw_contact_id",
                  "--where", f"'display_name=\"{contact_name}\"'")
    m = re.search(r"raw_contact_id=(\d+)", out)
    if m is None:
        print(f"  [skip] contact '{contact_name}' not found - cannot seed email")
        return
    raw_id = m.group(1)
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data", "--projection", "data1")
    if email in out:
        print(f"  contact email already present (raw_contact_id={raw_id}) - nothing to do")
        return
    rc, out = adb(serial, "shell", "content", "insert", "--uri",
                  "content://com.android.contacts/data",
                  "--bind", f"raw_contact_id:i:{raw_id}",
                  "--bind", "mimetype:s:vnd.android.cursor.item/email_v2",
                  "--bind", f"data1:s:{email}",
                  "--bind", "data2:i:1")
    print(f"  contact-email insert rc={rc}: {out[:120] or 'OK'}")


def seed_day2(serial: str) -> None:
    """Seed the Day-2 ADB-seedable artifacts.

    - hard__files-notes__011: invoice PDF in Downloads (late-fee branch).
    - hard__photos-gmail-obsidian__012: fabricated {contact} email so the
      'email it to them if so' branch can trigger (the caption mention is an
      operator step - see the manifest; not ADB-seedable).

    Everything else on Day 2 depends on the real web / real Gmail/Photos/YouTube/
    Music state / app-private data.
    """
    task_dir = REPO_ROOT / "assets" / "seeds" / "day_2"
    sf = task_dir
    sf.mkdir(parents=True, exist_ok=True)
    pdf = sf / "invoice_seed.pdf"
    if not pdf.exists():
        write_invoice_pdf(pdf)
    adb(serial, "shell", "mkdir", "-p", "/sdcard/Download")
    push_with_mtime(serial, pdf, "/sdcard/Download",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW)))
    adb(serial, "shell", "content", "call", "--uri", "content://media/none",
        "--method", "scan_volume", "--arg", "external_primary")
    print("seeded Day-2 invoice PDF -> /sdcard/Download/invoice_seed.pdf")

    # photos-gmail-obsidian__012: fabricated {contact} email so the 'email it to
    # them if so' branch can trigger (the caption is an operator step - manifest).
    cfg = load_user_config(CONFIG_PATH)
    seed_contact_email(serial, cfg["contact"], device_paths.contact_email(cfg))


def seed_day27(serial: str) -> None:
    """Seed the Day-27 ADB-seedable artifacts.

    - easy__files__014: flight ticket PDF (boarding_pass.pdf) in Downloads so the
      agent opens it in Files and reads back the terminal, gate, and date.

    Everything else on Day 27 depends on the real web / real app state.
    """
    task_dir = REPO_ROOT / "assets" / "seeds" / "day_27"
    sf = task_dir
    sf.mkdir(parents=True, exist_ok=True)
    pdf = sf / "boarding_pass.pdf"
    if not pdf.exists():
        write_boarding_pass_pdf(pdf)
    adb(serial, "shell", "mkdir", "-p", "/sdcard/Download")
    push_with_mtime(serial, pdf, "/sdcard/Download",
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW)))
    adb(serial, "shell", "content", "call", "--uri", "content://media/none",
        "--method", "scan_volume", "--arg", "external_primary")
    print("seeded Day-27 flight ticket PDF -> /sdcard/Download/boarding_pass.pdf")


def attempt_content_seeds(serial: str, cfg: dict[str, str]) -> None:
    """Try SMS + call-log inserts; report honestly if the non-rooted device blocks them."""
    print("attempting SMS insert (usually blocked on non-rooted)...")
    import datetime as _dt
    day_name = _dt.date.today().strftime("%A")
    body = (f"Your {cfg['search word']} for {day_name} is confirmed. "
            "Show this at the gate.")
    rc, out = adb(serial, "shell", "content", "insert", "--uri", "content://sms",
                  "--bind", "address:s:+919876501234",
                  "--bind", f"body:s:{body}",
                  "--bind", "date:l:" + str(int(NOW) * 1000), "--bind", "read:i:1")
    print(f"  SMS insert rc={rc}: {out[:120] or 'OK'}")

    print("attempting call-log insert (usually allowed)...")
    rc2, out2 = adb(serial, "shell", "content", "insert", "--uri", "content://call_log/calls",
                    "--bind", f"number:s:{cfg['digits']}000001", "--bind", "type:i:1",
                    "--bind", "date:l:" + str(int(NOW) * 1000), "--bind", "duration:i:45")
    print(f"  call-log insert rc={rc2}: {out2[:120] or 'OK'}")


# ---------------------------------------------------------------------------
# Day 4-6 seeding (fabricated ADB-seedable data for the runnable 530 subset).
# Mirrors the Day-1/2 pattern: materialise the literal seed files into
# seeds/day_N/ (flat real artifacts) + manifests/day_N/, then push them + calendar/contact
# content-provider rows to the device. Anything app-private is reported honestly
# as a manual/operator step instead (see docs/fabricated-test-data.md).
# ---------------------------------------------------------------------------

def day_seed_dir(day: int) -> Path:
    return REPO_ROOT / "assets" / "seeds" / "manifests" / f"day_{day}"


def day_artifacts_dir(day: int) -> Path:
    return REPO_ROOT / "assets" / "seeds" / f"day_{day}"


def push_obsidian_note(serial: str, day: int, task_id: str, fname: str, vault_title: str) -> None:
    """Push a materialised Obsidian .md seed file into the vault (idempotent).

    The vault dir is resolved per-device (see device_paths.vault_path); its
    historical name has a trailing space, so the remote path joins with a slash
    AFTER it (`{vault}/{title}`) - joining without it would create a stray file
    at the Obsidian root instead.
    """
    sf = day_artifacts_dir(day)
    note = sf / fname
    if not note.exists():
        print(f"  [skip] {task_id}: no assets/seeds/day_{day}/{fname}")
        return
    vault = device_paths.vault_path(serial)
    adb(serial, "shell", "mkdir", "-p", vault)
    remote = f"{vault}/{vault_title}"
    adb(serial, "push", str(note), remote)
    print(f"  pushed {fname} -> {remote}")


def make_day4_seed_images() -> None:
    """Materialise Day-4 fabricated photos into assets/seeds/day_4/ (trip + today)."""
    def img(day: int, task: str, fname: str, rgb: tuple[int, int, int], size=(64, 64)):
        d = day_artifacts_dir(day)
        d.mkdir(parents=True, exist_ok=True)
        p = d / fname
        if not p.exists():
            write_png(p, size[0], size[1], rgb)

    # medium__gallery__003: a set of trip photos (filter-by-trip + star-best).
    trip_colors = [(160, 120, 40), (40, 140, 170), (190, 80, 60), (90, 130, 90)]
    for i, c in enumerate(trip_colors, 1):
        img(4, "medium__gallery__003", f"trip_{i}.jpg", c, (72 + i * 8, 64))
    # hard__gallery-obsidian__035: today's photos for the daily count curation.
    today_colors = [(30, 90, 180), (60, 160, 90), (200, 160, 30), (120, 70, 180), (220, 90, 140)]
    for i, c in enumerate(today_colors, 1):
        img(4, "hard__gallery-obsidian__035", f"today_photo_{i}.jpg", c, (80, 80))
    print("materialised Day-4 seed images into assets/seeds/day_4/")


def push_day4_obsidian(serial: str) -> None:
    """Day-4 Obsidian notes: Photo Log (hard__gallery-obsidian__035), the
    Exam Scores note (medium__calculator__001) the weighted-average task reads,
    and the Contact Updates note (hard__contacts-obsidian__029) the number-sync
    task reads. The add-a-line target (was easy__obsidian__003) is now
    easy__google-docs__001, a real cloud Google Docs document (needs_ui) — no
    on-device vault note is seeded for it."""
    cfg = load_user_config(CONFIG_PATH)
    push_obsidian_note(serial, 4, "hard__gallery-obsidian__035", "photo_log.md",
                       f"{cfg.get('photo journal title', 'Photo Log')}.md")
    push_obsidian_note(serial, 4, "medium__calculator__001", "exam_scores.md",
                       f"{cfg.get('exam scores note title', 'Exam Scores')}.md")
    push_obsidian_note(serial, 4, "hard__contacts-obsidian__029", "contact_updates.md",
                       f"{cfg.get('contact updates title', 'Contact Updates')}.md")


def push_day4_images(serial: str) -> None:
    """Push Day-4 photo seeds to /sdcard/DCIM/Camera with today's mtime."""
    adb(serial, "shell", "mkdir", "-p", CAMERA)
    d = day_artifacts_dir(4)
    if d.is_dir():
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            push_with_mtime(serial, f, CAMERA,
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW)))
    adb(serial, "shell", "content", "call", "--uri", "content://media/none",
        "--method", "scan_volume", "--arg", "external_primary")
    print("  pushed Day-4 photos -> Camera (media rescan triggered)")


def seed_day4(serial: str) -> None:
    """Seed Day-4 ADB-seedable artifacts.

    - easy__google-docs__001: real cloud Google Docs document (needs_ui; operator
      ensures an existing doc to add a line to — no ADB seed).
    - hard__gallery-obsidian__035: today's photos + 'Photo Log' note with
      yesterday's count (so the daily-count comparison is satisfiable).
    - medium__gallery__003: trip photos.
    - hard__contacts-obsidian__029: the Obsidian 'Contact Updates' note listing
      names + updated numbers (the number-sync task reads it and updates
      Contacts).
    - medium__phone__002: a missed call from a number matching an existing
      contact (call-log insert usually allowed on this device).
    """
    make_day4_seed_images()
    push_day4_images(serial)
    push_day4_obsidian(serial)
    # medium__phone__002: a missed call from the persona {contact} number.
    cfg = load_user_config(CONFIG_PATH)
    seed_missed_call(serial, cfg["digits"])


def _bedtime_note_template(bedtime: str) -> str:
    """Render the 7-day Obsidian 'Bedtime' sleep-routine record (day-3 seed).

    A proper human sleep log: varied bedtimes + artists/genres across 7 nights
    (lo-fi most frequent - that is the answer the agent must read out). The
    bedtime line comes from the config var so it stays consistent with the
    sleep-timer target.
    """
    return f"""# Bedtime

## Sleep routine record
What I listen to wind down and my sleep timings — kept as a log so I can see
what's working and when I'm actually getting to bed. Last 7 nights.

## 2026-08-15 (Sat)
- Bedtime: {bedtime}, asleep by ~11:15 PM
- Wind-down: Chillhop Lofi Beats - Sleep Mix (YouTube Music) — lo-fi beats
- Note: easy night, sleep timer stopped it right on time

## 2026-08-16 (Sun)
- Bedtime: 10:45 PM, asleep by ~11:30 PM
- Wind-down: Kind of Blue - Miles Davis (Amazon Music) — jazz
- Note: tried jazz, took a little longer to drift off

## 2026-08-17 (Mon)
- Bedtime: 10:20 PM, asleep by ~11:05 PM
- Wind-down: Hotel California - Eagles (YouTube Music) — classic rock
- Note: rock was too upbeat, had to skip to something calmer

## 2026-08-18 (Tue)
- Bedtime: {bedtime}, asleep by ~11:10 PM
- Wind-down: Chillhop Lofi Beats - Sleep Mix (YouTube Music) — lo-fi beats
- Note: back to lo-fi, felt properly sleepy

## 2026-08-19 (Wed)
- Bedtime: 10:25 PM, asleep by ~11:00 PM
- Wind-down: Lo-Fi Sleep Beats (Amazon Music) — lo-fi beats
- Note: lo-fi again, worked just as well on Amazon

## 2026-08-20 (Thu)
- Bedtime: {bedtime}, asleep by ~11:05 PM
- Wind-down: Chillhop Lofi Beats - Sleep Mix (YouTube Music) — lo-fi beats
- Note: usual routine, timer stopped at bedtime

## 2026-08-21 (Fri)
- Bedtime: {bedtime}, asleep by ~11:00 PM
- Wind-down: Chillhop Lofi Beats - Sleep Mix (YouTube Music) — lo-fi beats
- Note: consistent — lo-fi beats help me sleep most nights

## What's been working
- Lo-fi beats get me to sleep fastest (used most of the last 7 nights)
- Bedtime settled at {bedtime}
- Favorite app for this lately: YouTube Music

## Habit
- Start a Chillhop lo-fi track, set a sleep timer so it stops by itself at bedtime
"""


def seed_day3_music(serial: str) -> None:
    """Seed Day-3 Music sleep-timer artifacts (hard__music-obsidian__077).

    The task asks the agent to set a sleep timer so music stops by itself around
    the user's bedtime, and the source of truth is the Obsidian 'Bedtime' note
    (a 7-day sleep-routine record: what music helps sleep + the sleep timings).
    The only ADB-seedable artifact here is that note; the music playback itself
    is real app + web state (no fabricated audio).
    """
    cfg = load_user_config(CONFIG_PATH)

    # Obsidian Bedtime note: a 7-day sleep-journey record with varied artists /
    # genres (lo-fi most frequent) + varied sleep timings (bedtime from config).
    # The agent must READ this note to find the bedtime + the music that helps.
    bedtime = cfg.get("bedtime", "10:30 PM")
    push_obsidian_note(
        serial, 3, "hard__music-obsidian__077", "bedtime.md", "Bedtime.md")
    # The template file may not exist under assets/seeds/day_3 yet; ensure it.
    d3 = day_artifacts_dir(3)
    if not (d3 / "bedtime.md").exists():
        d3.mkdir(parents=True, exist_ok=True)
        (d3 / "bedtime.md").write_text(
            _bedtime_note_template(bedtime), encoding="utf-8")
        print(f"  materialised assets/seeds/day_3/bedtime.md (Bedtime={bedtime})")
        # (re)push now that the file exists
        vault = device_paths.vault_path(serial)
        adb(serial, "shell", "mkdir", "-p", vault)
        adb(serial, "push", str(d3 / "bedtime.md"), f"{vault}/Bedtime.md")
        print(f"  pushed Bedtime.md -> {vault}/Bedtime.md")
    else:
        print(f"  Bedtime.md already seeded (Bedtime={bedtime})")


def seed_day5_obsidian(serial: str) -> None:
    """Day-5 Obsidian notes: Budget Deadline (drive-obsidian-telegram) + the
    research note to summarise (medium__obsidian__004)."""
    push_obsidian_note(serial, 5, "hard__drive-obsidian-telegram__049",
                       "budget_deadline.md", "Budget Deadline.md")
    push_obsidian_note(serial, 5, "medium__obsidian__004",
                       "research_notes.md", "Research Notes.md")


def seed_day5_calendar(serial: str) -> None:
    """Day-5 calendar seeds (relative to the run date):

    - easy__calendar__002: two overlapping events TOMORROW afternoon -> conflict.
    - medium__calendar__002: three next-week meetings with distinct durations.
    - hard__calendar-telegram-notes__025: the earliest event TOMORROW starts
      before 8am so the message branch triggers.
    """
    import datetime as _dt

    cal_id = device_paths.calendar_id(serial)
    today = _dt.date.today()  # the run day (device date == run date when seeding)
    tomorrow = today + _dt.timedelta(days=1)
    next_monday = tomorrow + _dt.timedelta(days=(7 - tomorrow.weekday()) % 7)

    def ms(d: _dt.date, hh: int, mm: int = 0) -> int:
        return int(_dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=_dt.timezone.utc).timestamp() * 1000)

    def ins(title: str, start: int, end: int, all_day: bool = False) -> None:
        cmd = ["content", "insert", "--uri", "content://com.android.calendar/events",
               "--bind", f"calendar_id:i:{cal_id}",
               "--bind", f"title:s:'{title}'",
               "--bind", f"dtstart:l:{start}", "--bind", f"dtend:l:{end}",
               "--bind", "allDay:i:" + ("1" if all_day else "0"), "--bind", "hasAlarm:i:0",
               "--bind", "eventTimezone:s:Asia/Kolkata"]
        adb(serial, "shell", *cmd)

    # idempotent: drop previously-seeded rows by title first.
    for t in ("Team_Conflict_A", "Team_Conflict_B", "Next_Week_1h", "Next_Week_30m",
              "Next_Week_90m", "Early_Bird_Standup", "AllDay_Planning_Retreat",
              "AllDay_Team_Offsite", "No_Reminder_Sync", "No_Reminder_Review",
              "No_Reminder_1o1", "Alarm_Clash_Event", "Availability_AM", "Availability_PM"):
        for _ in range(6):
            adb(serial, "shell", "content", "delete", "--uri", "content://com.android.calendar/events",
                "--where", f"'title=\"{t}\"'")

    h = 3600_000
    # easy__calendar__002: tomorrow afternoon conflict.
    ins("Team_Conflict_A", ms(tomorrow, 14, 0), ms(tomorrow, 15, 0))
    ins("Team_Conflict_B", ms(tomorrow, 14, 30), ms(tomorrow, 15, 30))
    # medium__calendar__002: next-week meetings by duration.
    ins("Next_Week_30m", ms(next_monday, 10, 0), ms(next_monday, 10, 30))
    ins("Next_Week_1h", ms(next_monday, 11, 0), ms(next_monday, 12, 0))
    ins("Next_Week_90m", ms(next_monday, 14, 0), ms(next_monday, 15, 30))
    # hard__calendar-telegram-notes__025: earliest tomorrow event before 8am.
    ins("Early_Bird_Standup", ms(tomorrow, 7, 0), ms(tomorrow, 8, 0))
    print("seeded Day-5 calendar events into cal_id=16 (Google-synced)")


def seed_day5(serial: str) -> None:
    """Seed Day-5 ADB-seedable artifacts (Obsidian notes + calendar + contact
    address/company so the contact tasks resolve; Drive/Telegram stay real)."""
    seed_day5_obsidian(serial)
    seed_day5_calendar(serial)
    cfg = load_user_config(CONFIG_PATH)
    seed_contact_address(serial, cfg["contact"], "A-42, Kalinga Nagar, Bhubaneswar 751003")
    seed_contact_company(serial, cfg["contact"], "Airtel")


def seed_day6_calendar(serial: str) -> None:
    """Day-6 calendar seeds (relative to the run date):

    - easy__calendar__003: two ALL-DAY events this week.
    - medium__calendar__003: several no-reminder events this week.
    - hard__clock-calendar__023: a same-week event so the alarm clash check has
      something to find.
    - hard__calendar__097: tomorrow availability for the three invitees, each
      busy except the 1-3 PM window.
    """
    import datetime as _dt

    cal_id = device_paths.calendar_id(serial)
    today = _dt.date.today()
    tomorrow = today + _dt.timedelta(days=1)

    def ms(d: _dt.date, hh: int, mm: int = 0) -> int:
        return int(_dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=_dt.timezone.utc).timestamp() * 1000)

    def ins(title: str, start: int, end: int, all_day: bool = False) -> None:
        cmd = ["content", "insert", "--uri", "content://com.android.calendar/events",
               "--bind", f"calendar_id:i:{cal_id}",
               "--bind", f"title:s:'{title}'",
               "--bind", f"dtstart:l:{start}", "--bind", f"dtend:l:{end}",
               "--bind", "allDay:i:" + ("1" if all_day else "0"), "--bind", "hasAlarm:i:0",
               "--bind", "eventTimezone:s:Asia/Kolkata"]
        adb(serial, "shell", *cmd)

    for t in ("AllDay_Planning_Retreat", "AllDay_Team_Offsite", "No_Reminder_Sync",
              "No_Reminder_Review", "No_Reminder_1o1", "Alarm_Clash_Event",
              "Availability_AM", "Availability_PM"):
        for _ in range(6):
            adb(serial, "shell", "content", "delete", "--uri", "content://com.android.calendar/events",
                "--where", f"'title=\"{t}\"'")

    # easy__calendar__003: all-day events this week.
    ins("AllDay_Planning_Retreat", ms(today, 0, 0), ms(today, 23, 59), all_day=True)
    ins("AllDay_Team_Offsite", ms(today + _dt.timedelta(days=2), 0, 0), ms(today + _dt.timedelta(days=2), 23, 59), all_day=True)
    # medium__calendar__003: no-reminder events this week (hasAlarm=0 seeded).
    ins("No_Reminder_Sync", ms(tomorrow, 9, 0), ms(tomorrow, 10, 0))
    ins("No_Reminder_Review", ms(tomorrow, 11, 0), ms(tomorrow, 11, 30))
    ins("No_Reminder_1o1", ms(tomorrow + _dt.timedelta(days=1), 15, 0), ms(tomorrow + _dt.timedelta(days=1), 15, 45))
    # hard__clock-calendar__023: same-week event for the alarm clash check.
    ins("Alarm_Clash_Event", ms(tomorrow, 7, 0), ms(tomorrow, 8, 0))
    # hard__calendar__097: tomorrow availability for invitees, busy except 1-3 PM.
    ins("Availability_AM", ms(tomorrow, 9, 0), ms(tomorrow, 12, 0))
    ins("Availability_PM", ms(tomorrow, 15, 0), ms(tomorrow, 18, 0))
    print("seeded Day-6 calendar events into cal_id=16 (Google-synced)")


def seed_day6_files(serial: str) -> None:
    """medium__files__002: push files with mtimes > 3 months old to Downloads so
    the 'not opened in over 3 months' filter has real targets."""
    d6 = day_artifacts_dir(6)
    d6.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        f = d6 / f"old_doc_{i}.txt"
        if not f.exists():
            f.write_text(f"Old archived document {i}\n", encoding="utf-8")
    adb(serial, "shell", "mkdir", "-p", "/sdcard/Download")
    for i in range(1, 4):
        push_with_mtime(serial, d6 / f"old_doc_{i}.txt", "/sdcard/Download",
                        f"2026-04-{10 + i:02d} 10:00:00")  # >3 months before Aug
    print("  pushed old_doc_1..3.txt -> Download (2026-04 mtimes)")


def seed_day6(serial: str) -> None:
    """Seed Day-6 ADB-seedable artifacts (calendar + old files + duplicate-email
    contacts for medium__contacts__005)."""
    seed_day6_calendar(serial)
    seed_day6_files(serial)
    cfg = load_user_config(CONFIG_PATH)
    seed_duplicate_contact_email(serial, cfg["contact"], cfg)


def _contact_raw_id(serial: str, display_name: str) -> str | None:
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data",
                  "--projection", "raw_contact_id",
                  "--where", f"'display_name=\"{display_name}\"'")
    m = re.search(r"raw_contact_id=(\d+)", out)
    return m.group(1) if m else None


def seed_contact_address(serial: str, contact_name: str, address: str) -> None:
    """ADB-seed a postal address onto an existing contact (idempotent)."""
    raw_id = _contact_raw_id(serial, contact_name)
    if raw_id is None:
        print(f"  [skip] contact '{contact_name}' not found - cannot seed address")
        return
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data", "--projection", "data1")
    if address in out:
        print(f"  contact address already present - nothing to do")
        return
    rc, out = adb(serial, "shell", "content", "insert", "--uri",
                  "content://com.android.contacts/data",
                  "--bind", f"raw_contact_id:i:{raw_id}",
                  "--bind", "mimetype:s:vnd.android.cursor.item/postal_v2",
                  # single-quote wrap: the address has spaces/commas and the
                  # device shell would split it into multiple args otherwise.
                  "--bind", f"data1:s:'{address}'", "--bind", "data2:i:1")
    print(f"  contact-address insert rc={rc}: {out[:120] or 'OK'}")


def seed_contact_company(serial: str, contact_name: str, company: str) -> None:
    """ADB-seed an organization/company field onto a contact (idempotent)."""
    raw_id = _contact_raw_id(serial, contact_name)
    if raw_id is None:
        print(f"  [skip] contact '{contact_name}' not found - cannot seed company")
        return
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data", "--projection", "data1")
    if company in out:
        print(f"  contact company already present - nothing to do")
        return
    rc, out = adb(serial, "shell", "content", "insert", "--uri",
                  "content://com.android.contacts/data",
                  "--bind", f"raw_contact_id:i:{raw_id}",
                  "--bind", "mimetype:s:vnd.android.cursor.item/organization",
                  "--bind", f"data1:s:{company}", "--bind", "data2:i:1")
    print(f"  contact-company insert rc={rc}: {out[:120] or 'OK'}")


def seed_duplicate_contact(serial: str, source_name: str, new_name: str) -> None:
    """Create a duplicate contact sharing the same phone number as an existing
    one (hard__contacts-obsidian__029 needs a real duplicate pair to merge).
    Idempotent: skips if a contact named {new_name} already exists."""
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/contacts", "--projection", "display_name")
    if new_name.lower() in out.lower():
        print(f"  duplicate contact '{new_name}' already exists - nothing to do")
        return
    # find the source contact's phone number
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data", "--projection", "data1:data2:data3:data4")
    # NOTE: contact creation with a matching phone number on a non-rooted device
    # usually requires the Contacts app UI (content raw_contacts insert is often
    # blocked). Reported honestly here; operator can add 'Maa Home' manually.
    print(f"  [operator] create duplicate contact '{new_name}' with {source_name}'s number in the Contacts app")


def seed_missed_call(serial: str, digits: str) -> None:
    """medium__phone__002: insert a missed call (type=3) from the persona's number
    so the agent can merge it into the matching existing contact. Call-log insert
    is usually allowed on this device."""
    rc, out = adb(serial, "shell", "content", "insert", "--uri", "content://call_log/calls",
                  "--bind", f"number:s:+91{digits}000001", "--bind", "type:i:3",
                  "--bind", "date:l:" + str(int(NOW - 3600) * 1000), "--bind", "duration:i:0",
                  "--bind", "presentation:i:1")
    print(f"  missed-call insert rc={rc}: {out[:120] or 'OK'}")


def seed_unknown_number_call(serial: str) -> None:
    """easy__phone__001: insert a recent incoming call (type=1) from an UNKNOWN
    (not-in-contacts) number so the agent can message it \"who's this?\". Uses a
    number not present in the contact book; call-log insert is usually allowed.

    Idempotent-ish: deletes any prior seed row first, then inserts one fresh row.
    """
    # remove any previously-seeded probe rows (number ends in 555001)
    adb(serial, "shell", "content", "delete", "--uri", "content://call_log/calls",
        "--where", "'number LIKE \"%555001\"'")
    rc, out = adb(serial, "shell", "content", "insert", "--uri", "content://call_log/calls",
                  "--bind", "number:s:+919555555001", "--bind", "type:i:1",
                  "--bind", "date:l:" + str(int(NOW - 1800) * 1000), "--bind", "duration:i:0",
                  "--bind", "presentation:i:1", "--bind", "name:s:")
    print(f"  unknown-number call insert rc={rc}: {out[:120] or 'OK'}")


def seed_duplicate_contact_email(serial: str, source_name: str, cfg: dict[str, str] | None = None) -> None:
    """medium__contacts__005: ensure at least two contacts share one email
    address (idempotent; reports the operator step if not creatable)."""
    email = device_paths.contact_email(cfg)
    rc, out = adb(serial, "shell", "content", "query", "--uri",
                  "content://com.android.contacts/data", "--projection", "data1")
    if email in out:
        print(f"  duplicate-email pair already present ({email}) - nothing to do")
        return
    raw_id = _contact_raw_id(serial, source_name)
    if raw_id is None:
        print(f"  [skip] contact '{source_name}' not found - cannot seed email")
        return
    rc, out = adb(serial, "shell", "content", "insert", "--uri",
                  "content://com.android.contacts/data",
                  "--bind", f"raw_contact_id:i:{raw_id}",
                  "--bind", "mimetype:s:vnd.android.cursor.item/email_v2",
                  "--bind", f"data1:s:{email}", "--bind", "data2:i:1")
    print(f"  duplicate-email insert rc={rc}: {out[:120] or 'OK'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--day", type=int, default=1, help="Day to seed (1 = Day-1 images/calendar/obsidian, 2 = invoice PDF, 3 = Music sleep-timer Obsidian note, 4/5/6 = those days' fabricated data).")
    parser.add_argument("--no-push", action="store_true", help="Only materialise seed files, don't touch the device.")
    parser.add_argument("--verify", action="store_true", help="Device-state check: confirm every declared seed_device_path exists on the phone (does not push).")
    args = parser.parse_args()

    if args.verify:
        return verify_day_seeds(args.serial, args.day)

    if args.day in (4, 5, 6):
        d = day_seed_dir(args.day)
        if not (d / "manifest_index.json").exists():
            raise SystemExit(f"No assets/seeds/manifests/day_{args.day}/manifest_index.json - run scripts/build_day_seed_manifest.py --day {args.day} first")
        if args.day == 4:
            make_day4_seed_images()
        if args.no_push:
            return 0
        if args.day == 4:
            seed_day4(args.serial)
        elif args.day == 5:
            seed_day5(args.serial)
        else:
            seed_day6(args.serial)
        return 0

    if 7 <= args.day <= 28 and args.day != 27:
        # Auto-generated days: push every ADB-verifiable seed file (obsidian_note
        # and other filesystem `device_path` seeds) the manifest declares. The
        # materialised files live in assets/seeds/day_N/ (written by the manifest
        # builder's SEED_FILE_TEMPLATES); this mirrors the days-4-6 pattern for
        # the whole corpus so a task never references a doc that wasn't pushed.
        # Day 27 keeps its dedicated branch (flight-ticket PDF) below.
        d = day_seed_dir(args.day)
        if not (d / "manifest_index.json").exists():
            raise SystemExit(f"No assets/seeds/manifests/day_{args.day}/manifest_index.json - run scripts/build_day_seed_manifest.py --day {args.day} first")
        if args.no_push:
            return 0
        seed_auto_day(args.serial, args.day)
        return 0

    if args.day == 3:
        # Day 3 currently has no build_day_seed_manifest entry (its tasks are
        # mostly web / real-state / app-private); only the Music sleep-timer
        # artifacts are ADB-seedable. --no-push materialises the seed_files and
        # still exits cleanly without a manifest_index.json.
        if not args.no_push:
            seed_day3_music(args.serial)
        return 0

    if args.day == 27:
        day_dir = day_seed_dir(27)
        if not (day_dir / "manifest_index.json").exists():
            raise SystemExit("No assets/seeds/manifests/day_27/manifest_index.json - run scripts/build_day_seed_manifest.py --day 27 first")
        if args.no_push:
            return 0
        seed_day27(args.serial)
        return 0

    if args.day == 2:
        day_dir = day_seed_dir(2)
        if not (day_dir / "manifest_index.json").exists():
            raise SystemExit("No assets/seeds/manifests/day_2/manifest_index.json - run scripts/build_day_seed_manifest.py --day 2 first")
        if args.no_push:
            return 0
        seed_day2(args.serial)
        return 0

    if not (day_seed_dir(1) / "manifest_index.json").exists():
        raise SystemExit("No assets/seeds/manifests/day_1/manifest_index.json - run scripts/build_day_seed_manifest.py --day 1 first")

    make_seed_images()
    if args.no_push:
        return 0
    cfg = load_user_config(CONFIG_PATH)
    push_seed_images(args.serial)
    push_obsidian_seed(args.serial, cfg)
    cleanup_test_events(args.serial)
    seed_calendar_events(args.serial, cfg["meeting title"], cfg)
    seed_unknown_number_call(args.serial)
    attempt_content_seeds(args.serial, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
