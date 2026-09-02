#!/usr/bin/env python3
"""Start `phoenix serve` for a specific benchmark day (or the shared project)."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_ROOT = REPO_ROOT / "assets" / "db"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Start phoenix serve for a day's run.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--day", type=int, metavar="N", help="Day 1-28: DB assets/db/dayN/phoenix.db, project dailybench-dayN")
    g.add_argument("--public", action="store_true", help="Public-sample run: DB assets/db/public/phoenix.db, project dailybench-public")
    g.add_argument("--project", default=None, help="Shared project name -> assets/db/misc/phoenix.db")
    ap.add_argument("--run-ts", default=None, metavar="YYYYMMDD-HHMMSS", help="With --public: use assets/db/public/<run-ts>/phoenix.db (dedicated per-run DB folder)")
    ap.add_argument("--port", type=int, default=6006, help="Phoenix dashboard/HTTP port (default 6006)")
    ap.add_argument("--host", default="localhost", help="Bind host (default localhost)")
    ap.add_argument("--no-open", action="store_true", help="Do not print the dashboard URL (informational only; we never auto-open a browser).")
    return ap


def _already_running(host: str, port: int) -> bool:
    try:
        with urlopen(f"http://{host}:{port}", timeout=1.5) as resp:  # noqa: S310
            return resp.status < 500
    except Exception:  # noqa: BLE001
        pass
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def main() -> int:
    args = build_parser().parse_args()
    if args.day is not None:
        project = f"dailybench-day{args.day}"
        db_path = DB_ROOT / f"day{args.day}" / "phoenix.db"
    elif args.public:
        project = "dailybench-public"
        db_path = DB_ROOT / "public" / (args.run_ts or "") / "phoenix.db" if args.run_ts else DB_ROOT / "public" / "phoenix.db"
    else:
        project = args.project
        db_path = DB_ROOT / "misc" / "phoenix.db"

    if _already_running(args.host, args.port):
        print(f"Phoenix already running on {args.host}:{args.port} — nothing to do.")
        return 0

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    cmd = ["uv", "run", "phoenix", "serve", "--port", str(args.port)]
    env = dict(os.environ)
    env["PHOENIX_SQL_DATABASE_URL"] = url
    env["PHOENIX_PROJECT_NAME"] = project
    print(f"Starting phoenix serve -> {url} (project {project})")
    print(f"  command: {' '.join(cmd)}")
    print("  (runs in the foreground; Ctrl-C to stop. Dashboard: http://localhost:%d)" % args.port)
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
