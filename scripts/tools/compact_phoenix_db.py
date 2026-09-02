#!/usr/bin/env python3
"""Shrink an Arize Phoenix SQLite DB by stripping embedded screenshot blobs."""

from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path

_IMAGE_PAT = re.compile(r"data:image/(?:png|jpe?g|webp|gif|avif);base64,[A-Za-z0-9+/=]+")
# mobilerun embeds screenshots a second way: as bytes literals inside an
# ImageBlock repr, e.g. `ImageBlock(block_type='image', image=b'iVBOR...', ...)`.
_IMAGE_BLOCK_PAT = re.compile(r"image=b'[A-Za-z0-9+/=]+'")
_ALL_PATS = (_IMAGE_PAT, _IMAGE_BLOCK_PAT)


def _strip(value: str | None) -> str | None:
    if not value:
        return value
    for pat, repl in ((_IMAGE_PAT, "data:image/[omitted]"), (_IMAGE_BLOCK_PAT, "image=b'[omitted]'")):
        value = pat.sub(repl, value)
    return value


def compact(db_path: str) -> tuple[int, int]:
    """Strip image blobs from spans. Returns (spans_changed, old_bytes, new_bytes)."""
    path = Path(db_path)
    old_bytes = path.stat().st_size
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA busy_timeout=30000")
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id FROM spans WHERE attributes LIKE '%data:image%' OR events LIKE '%data:image%'"
        " OR attributes LIKE '%image=b''%' OR events LIKE '%image=b''%'"
    ).fetchall()
    changed = 0
    for (sid,) in rows:
        attrs, ev = cur.execute("SELECT attributes, events FROM spans WHERE id=?", (sid,)).fetchone()
        na = _strip(attrs)
        ne = _strip(ev)
        if na != attrs or ne != ev:
            cur.execute("UPDATE spans SET attributes=?, events=? WHERE id=?", (na, ne, sid))
            changed += 1
    conn.commit()
    print(f"stripped image blobs in {changed} spans; vacuuming...", flush=True)
    conn.execute("VACUUM")
    conn.commit()
    conn.close()
    new_bytes = path.stat().st_size
    return changed, old_bytes, new_bytes


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    db = sys.argv[1]
    if not Path(db).exists():
        print(f"no such db: {db}", file=sys.stderr)
        sys.exit(1)
    t0 = time.time()
    changed, old, new = compact(db)
    print(f"done in {time.time() - t0:.1f}s: {old/1e9:.2f} GB -> {new/1e9:.2f} GB "
          f"({(1 - new / old) * 100:.1f}% smaller, {changed} spans touched)")
