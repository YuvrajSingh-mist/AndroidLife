#!/usr/bin/env python3
"""Harvest real-world Android user queries to source benchmark tasks."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SE_API = "https://api.stackexchange.com/2.3"
UA = {"User-Agent": "DrainBench-task-sourcing/0.1 (benchmark authoring)"}

# DrainBench's 32 apps -> Stack Exchange tag(s) + a subreddit-like search hint.
# Tags are the authoritative source on the android SE site; fall back to free
# text search when a tag doesn't exist.
APP_TAGS = {
    "Amazon Shopping": ["amazon"],
    "BookMyShow": ["bookmyshow"],
    "Calculator": ["calculator"],
    "Calendar": ["calendar", "google-calendar"],
    "Camera": ["camera"],
    "Chrome": ["chrome", "google-chrome"],
    "Clock": ["clock", "alarm"],
    "Contacts": ["contacts"],
    "Files": ["file-management", "file-manager"],
    "Gmail": ["gmail"],
    "Google Docs": ["google-docs"],
    "Google Drive": ["google-drive"],
    "Google Maps": ["google-maps", "navigation"],
    "Google Meet": ["google-meet"],
    "Google Photos": ["google-photos", "gallery"],
    "Google Search": ["google-search", "google-now"],
    "Google Sheets": ["google-sheets"],
    "Google Slides": ["google-slides"],
    "MSN News": ["news"],
    "MakeMyTrip": ["makemytrip"],
    "Messages": ["sms", "messages"],
    "Music": ["music", "google-play-music"],
    "Notes": ["notes"],
    "Obsidian": ["obsidian"],
    "Phone": ["phone", "calls"],
    "Prime Video": ["prime-video"],
    "Settings": ["settings"],
    "Swiggy": ["swiggy"],
    "Telegram": ["telegram"],
    "Weather": ["weather"],
    "YouTube": ["youtube"],
}

# Generic Android tags that yield high-value "how do I" queries not tied to one app.
GENERIC_TAGS = ["notifications", "background-processes", "battery-life",
                "permissions", "sync", "backup", "widgets", "dark-mode",
                "share", "screen-recording", "default-app"]


def se_get(path: str, params: dict) -> dict:
    url = f"{SE_API}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


def fetch_for_tag(tag: str, limit: int) -> list[dict]:
    """Fetch recent questions for a StackExchange tag (or free-text search)."""
    # tags must be URL-encoded; 'how do I' style questions are the task material.
    q = f'[{tag}] how do I'  # search syntax: tagged + phrase
    data = se_get("search/advanced", {
        "site": "android", "pagesize": limit, "q": f"how do I",
        "tagged": tag, "order": "desc", "sort": "activity", "filter": "withbody",
    })
    return data.get("items", [])


def fetch_search(q: str, limit: int) -> list[dict]:
    data = se_get("search/advanced", {
        "site": "android", "pagesize": limit, "q": q,
        "order": "desc", "sort": "activity", "filter": "withbody",
    })
    return data.get("items", [])


def clean_html(s: str) -> str:
    import html as _html
    import re
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = _html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def harvest(app: str, limit: int) -> list[dict]:
    out: list[dict] = []
    for tag in APP_TAGS.get(app, [app.lower()]):
        try:
            items = fetch_for_tag(tag, limit)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] tag '{tag}' failed: {e}", file=sys.stderr)
            items = []
        for it in items:
            out.append({
                "app": app, "tag": tag,
                "title": it.get("title", ""),
                "body": clean_html(it.get("body", ""))[:500],
                "link": it.get("link", ""),
                "score": it.get("score", 0),
                "answers": it.get("answer_count", 0),
            })
        if out:
            break  # first tag that returned results is enough
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest real Android user queries for task authoring.")
    ap.add_argument("--out", default=str(REPO_ROOT / "reports" / "real-user-queries.md"),
                    help="Output markdown path (default reports/real-user-queries.md)")
    ap.add_argument("--app", default=None, help="Comma-separated apps (default: all 32)")
    ap.add_argument("--limit", type=int, default=5, help="Queries per app (default 5)")
    ap.add_argument("--include-generic", action="store_true", help="Also pull generic Android tags (notifications, battery, etc.)")
    args = ap.parse_args()

    apps = [a.strip() for a in args.app.split(",")] if args.app else list(APP_TAGS.keys())
    from datetime import date
    lines: list[str] = ["# Real-world Android user queries (task-sourcing material)",
                        "",
                        f"> Harvested {args.limit} question(s) per app from the Android Enthusiasts Stack "
                        f"Exchange API on {date.today().isoformat()}. Each entry is a REAL user query — "
                        "paraphrase it into a task using the benchmark's fabricated persona + device vars.",
                        "",
                        "---", ""]

    grand_total = 0
    for app in apps:
        items = harvest(app, args.limit)
        if not items:
            lines.append(f"## {app}\n\n_(no Stack Exchange results — use app-specific subreddit or forum)_\n")
            continue
        grand_total += len(items)
        lines.append(f"## {app}\n")
        for it in items:
            title = it["title"].replace("&quot;", '"').replace("&#39;", "'")
            lines.append(f"- **{title}**  \n  {it['body'][:220]}…  \n  _{it['link']}_")
        lines.append("")

    if args.include_generic:
        lines.append("---\n\n# Generic Android queries (cross-app)\n")
        for tag in GENERIC_TAGS:
            try:
                items = fetch_for_tag(tag, args.limit)
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] generic tag '{tag}' failed: {e}", file=sys.stderr)
                continue
            lines.append(f"### {tag}\n")
            for it in items:
                lines.append(f"- **{it.get('title','')}**  \n  {clean_html(it.get('body',''))[:220]}…  \n  _{it.get('link','')}_")
            lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({grand_total} app-mapped queries, {args.include_generic and 'incl generic' or 'no generic'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
