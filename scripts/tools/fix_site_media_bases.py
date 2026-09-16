#!/usr/bin/env python3
"""Point any local media reference in the site data at its Hugging Face copy.

The site ships condensed step JSON from its own directory but loads media
(screenshots, and the replay GIF) from the Hub, because the frames are far too
large to keep in git. An export that predates that split can leave a
`screenshot_base` pointing at `assets/...`, which 404s once deployed: nothing
copies `androidlife-website/assets/trajectories/` into the build.

`data` fields are deliberately left alone - the condensed JSON really is served
from the site, so a local `assets/data/...` path there is correct.

Edits are made on the file text, not on parsed JSON, because the exporters left
these files with different indentation (some 1-space, some 2-space); reparsing
and re-dumping one value would rewrite every line of the file.

Safe to re-run: already-absolute URLs do not match.

Usage (from the repo root):
    python3 scripts/tools/fix_site_media_bases.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_DATA = ROOT / "androidlife-website" / "assets" / "data" / "trajectories"
REPO_ID = "YuvrajSingh9886/androidlife-trajectories"
BASE = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"

# Media keys that must resolve to the Hub. `data` is not here on purpose.
MEDIA = re.compile(r'("(?:screenshot_base|gif)"\s*:\s*")(assets/[^"]*)(")')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    files = sorted(SITE_DATA.rglob("*.json"))
    changed = 0
    hits = 0
    for path in files:
        text = path.read_text()
        rewrites = []

        def repl(m: re.Match) -> str:
            local = m.group(2)
            # The Hub mirrors assets/trajectories/... as trajectories/...
            new = f"{BASE}/{local[len('assets/'):]}"
            rewrites.append((m.group(1).strip().rstrip(":").strip('"'), local, new))
            return f"{m.group(1)}{new}{m.group(3)}"

        updated = MEDIA.sub(repl, text)
        if not rewrites:
            continue
        changed += 1
        hits += len(rewrites)
        print(f"  {path.relative_to(SITE_DATA)}")
        for key, old, new in rewrites:
            print(f"    {key}: {old}")
            print(f"      -> {new}")
        if not args.dry_run:
            path.write_text(updated)

    print(f"\nscanned : {len(files)} files under {SITE_DATA.relative_to(ROOT)}")
    print(f"changed : {changed} files, {hits} reference(s)")
    if args.dry_run and hits:
        print("dry run - nothing written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
