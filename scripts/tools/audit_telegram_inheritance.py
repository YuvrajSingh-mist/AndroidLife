#!/usr/bin/env python
"""Find runs that scored with a message the PREVIOUS run had already sent.

Why this exists
---------------
The leak cleanup did not exist before 2026-09-22, so the 2026-09-21
`hard__drive-notes-telegram__010` re-runs had no coverage between rows: each delivered
message stayed in the `Yuvraj Airtel` chat for the next row to find. The damage is not a
dirty device, it is a false pass.

Measured: row 11 (`20260921-192331`) sent the budget chase at 19:29. Row 13
(`20260921-194413`) started at 19:46 and its step-6 UI tree already contained the same
`Sent at 19:29` bubble. Bonsai then reported `success=true` in 9 steps having sent nothing
-- the work had been done for it. That root has since been DELETED: a `success=true` run
holding a voided pass is exactly the debris that a run-root glob cannot tell from a result
(see redo.md 7.7), so it was removed rather than left to be re-counted.

The test is a timestamp comparison, not a heuristic: a sent bubble carrying a stamp
EARLIER than the run's own start cannot have been produced by that run. Such a run is
void regardless of how it scored, and has to be re-taken on a cleared chat.

Seeded chat history is deliberately excluded. The seed uses fixed old stamps ("Seems nice
ain't it? Sent at 16:46"), so only bubbles that match the task's own keywords are
considered -- a seeded bubble is shared by every run and would otherwise flag all of them.

Usage
-----
    uv run python scripts/tools/audit_telegram_inheritance.py                    # whole corpus
    uv run python scripts/tools/audit_telegram_inheritance.py --task hard__drive-notes-telegram__010
    uv run python scripts/tools/audit_telegram_inheritance.py --run-root assets/runs/public/<TS>

Exit 1 if any run inherited a message (so it can gate a verdict pass), else 0.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# Bubbles that carry a delivery stamp. A composer has no stamp, which is what makes this
# a clean signal for "this message was actually sent".
STAMPED = re.compile(r'"text":\s*"([^"]{0,600}?(?:Sent|Received) at \d{1,2}:\d{2}[^"]{0,80})"')
SENT_AT = re.compile(r"Sent at (\d{1,2}):(\d{2})")

# The seeded history, dated so it can never be mistaken for run output. If a bubble looks
# like one of these it is shared by every run and says nothing about any of them.
SEED_MARKERS = ("GOBOULT", "Seems nice ain't it?", "That’s true man", "That's true man",
                "But need more suggestions pls")

# task_id -> keywords identifying the message that task asks the agent to send.
TASK_MESSAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hard__drive-notes-telegram__010": ("FY26 family budget", "just checked the", "overdue"),
    "hard__bookmyshow__005": ("movie night plan", "Avengers", "book for us"),
}


def run_started_at(task_dir: Path) -> datetime.datetime | None:
    """The run's own start, in IST, from meta.json."""
    meta = task_dir / "meta.json"
    if not meta.exists():
        return None
    try:
        raw = json.loads(meta.read_text()).get("started_at_utc")
    except Exception:  # noqa: BLE001 - a malformed meta must not abort a whole-corpus scan
        return None
    if not raw:
        return None
    # fromisoformat handles the trailing "Z" on Python 3.11+.
    dt = datetime.datetime.fromisoformat(raw)
    return dt.astimezone(IST)


def stamped_bubbles(task_dir: Path) -> dict[str, list[str]]:
    """{ui_state filename: [bubble text, ...]} for every state that shows a stamped bubble."""
    found: dict[str, list[str]] = {}
    for state in sorted(task_dir.glob("trajectories/*/ui_states/*.json")):
        try:
            text = state.read_text(errors="ignore")
        except OSError:
            continue
        hits = [m for m in STAMPED.findall(text) if not any(s in m for s in SEED_MARKERS)]
        if hits:
            found[state.name] = [" ".join(h.split()) for h in hits]
    return found


def inherited_sends(task_dir: Path, keywords: tuple[str, ...]) -> list[dict]:
    """Sent bubbles whose stamp predates the run's start -> that run did not send them."""
    start = run_started_at(task_dir)
    if start is None:
        return []
    out: list[dict] = []
    for state, bubbles in stamped_bubbles(task_dir).items():
        for bubble in bubbles:
            if keywords and not any(k.lower() in bubble.lower() for k in keywords):
                continue
            stamp = SENT_AT.search(bubble)
            if not stamp:
                continue  # received, not sent by us
            when = start.replace(hour=int(stamp.group(1)), minute=int(stamp.group(2)),
                                 second=0, microsecond=0)
            if when < start:
                out.append({"state": state, "sent_at": when.strftime("%H:%M"),
                            "started": start.strftime("%H:%M"), "bubble": bubble[:160]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=None, help="Repo root (default: derived from this file).")
    ap.add_argument("--task", default=None, help="Only this task_id (default: all known-message tasks).")
    ap.add_argument("--run-root", action="append", default=None,
                    help="Only this run root (repeatable); needs --task to pick the keywords.")
    args = ap.parse_args()

    repo = Path(args.repo) if args.repo else Path(__file__).resolve().parents[2]
    public = repo / "assets" / "runs" / "public"

    tasks = {args.task: TASK_MESSAGE_KEYWORDS.get(args.task, ())} if args.task else TASK_MESSAGE_KEYWORDS
    roots = [Path(r) if Path(r).is_absolute() else repo / r for r in (args.run_root or [])]
    if not roots:
        roots = sorted(p for p in public.glob("2026*") if p.is_dir())

    contaminated: list[tuple[str, Path, list[dict]]] = []
    scanned = 0
    for task_id, keywords in tasks.items():
        slug = task_id.replace("__", "-")
        for root in roots:
            task_dir = next(iter(root.glob(f"day*/{slug}")), None)
            if task_dir is None or not (task_dir / "meta.json").exists():
                continue
            scanned += 1
            hits = inherited_sends(task_dir, keywords)
            if hits:
                contaminated.append((task_id, root, hits))

    print(f"scanned {scanned} run(s) for {len(tasks)} task(s)")
    if not contaminated:
        print("OK: no run inherited a message it was supposed to send")
        return 0

    print(f"\n{len(contaminated)} run(s) inherited a message -> VOID, must be re-taken:\n")
    for task_id, root, hits in contaminated:
        print(f"  {task_id}  {root.name}")
        for h in hits:
            print(f"      {h['state']}: bubble 'Sent at {h['sent_at']}' but run started {h['started']}")
            print(f"          {h['bubble'][:120]!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
