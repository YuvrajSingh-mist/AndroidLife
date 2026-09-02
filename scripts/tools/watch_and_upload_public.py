"""Watch iCloud materialization of the 9 completed public runs, then launch the HF upload"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PUBLIC_RUNS = Path("assets/runs/public")

# The 9 completed runs (exclude the active mimo run 20260901-002701).
COMPLETED_RUNS = [
    "2026-08-20-003030",
    "2026-08-22-195244",
    "2026-08-23-232211",
    "2026-08-26-184934",
    "2026-08-28-002424",
    "2026-08-29-153657",
    "2026-08-30-021852",
    "2026-08-30-143554",
    "20260826-105200",
]

UPLOAD_CMD = [
    sys.executable,
    "scripts/tools/upload_public_runs_hf.py",
]

POLL_SECONDS = 20
ZERO_BEFORE_LAUNCH = 3  # require dataless==0 on 3 consecutive polls before launching


def count_dataless() -> int:
    """Return number of iCloud-evicted (dataless) files across the completed runs."""
    total = 0
    for run in COMPLETED_RUNS:
        d = PUBLIC_RUNS / run
        if not d.is_dir():
            continue
        proc = subprocess.run(
            [
                "bash", "-c",
                f'find "{d}" -type f -print0 2>/dev/null | '
                'while IFS= read -r -d "" f; do '
                '[ -n "$(stat -f \'%Sf\' "$f" 2>/dev/null | grep dataless)" ] && echo x; '
                "done | wc -l | tr -d ' '",
            ],
            capture_output=True,
            text=True,
        )
        try:
            total += int(proc.stdout.strip() or 0)
        except ValueError:
            pass
    return total


def main() -> int:
    print(f"watch: monitoring {len(COMPLETED_RUNS)} completed runs @ {PUBLIC_RUNS}", flush=True)
    zeros = 0
    while True:
        n = count_dataless()
        print(f"[{time.strftime('%H:%M:%S')}] dataless (completed runs) = {n}", flush=True)
        if n == 0:
            zeros += 1
            if zeros >= ZERO_BEFORE_LAUNCH:
                print("dataless == 0 consistently - launching upload", flush=True)
                env = dict(os.environ)
                env["HF_XET_HIGH_PERFORMANCE"] = "1"
                with open("/tmp/hf-upload-20260901.log", "ab") as logf:
                    subprocess.Popen(
                        UPLOAD_CMD,
                        stdin=subprocess.DEVNULL,
                        stdout=logf,
                        stderr=logf,
                        env=env,
                        start_new_session=True,
                    )
                print("uploader launched (detached); watcher exiting", flush=True)
                return 0
        else:
            zeros = 0
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
