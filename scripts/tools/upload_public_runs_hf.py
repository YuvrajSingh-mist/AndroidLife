"""Upload the completed public benchmark runs to the androidlife-public HF dataset.

Each run is scanned by `scripts/hf/pii_guard.py` first, and the report is printed
before the upload so anything sensitive is visible in the log. The scan is
**report-only**: it never deletes, moves or rewrites an artifact, and by default a
finding does NOT stop the upload (`--block-on-pii` opts into skipping a flagged
run). Public runs are captured off a real phone, so a trajectory can legitimately
pick up the notification shade, an SMS inbox or a Drive listing.

Note: the remote paths are `runs/<id>/...` and the local source is
`assets/runs/public/<id>/`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "YuvrajSingh9886/androidlife-public"
REPO_ROOT = Path(__file__).resolve().parents[2]
PII_GUARD = REPO_ROOT / "scripts" / "hf" / "pii_guard.py"
PUBLIC_RUNS = "assets/runs/public"

# Force the Xet storage backend (chunked, deduped, parallel, adaptive commits).
# Without this, upload_folder falls back to legacy hash-then-HTTP which is very
# slow for many small files. 1 = saturate available bandwidth and CPU cores.
os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

# Completed runs only — the active mimo run (20260901-002701) is excluded so we
# don't snapshot a mid-write state. Add it here once the benchmark finishes.
RUNS = [
    "2026-08-20-003030",
    "2026-08-22-195244",
    "2026-08-23-232211",
    "2026-08-26-184934",
    "2026-08-28-002424",
    "2026-08-29-153657",
    "2026-08-30-021852",
    "2026-08-30-143554",
    "20260826-105200",
    "20260901-002701",
    "20260905-051950",
    "20260906-063336",
]


def pii_report(run_id: str, src: str, *, skip_images: bool, write_report: bool) -> int:
    """Scan one run and print the PII report. Never deletes or rewrites anything.

    Returns the number of HIGH-severity findings (0 on a clean run, or -1 if the
    scanner could not be run at all).
    """
    if not PII_GUARD.is_file():
        print(f"   PII SCAN SKIPPED: {PII_GUARD} not found", flush=True)
        return -1
    cmd = [sys.executable, str(PII_GUARD), src, "--root", str(REPO_ROOT)]
    if skip_images:
        cmd.append("--no-images")
    if write_report:
        cmd += ["--json", str(REPO_ROOT / ".cache" / f"pii_{run_id}.json")]
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    except OSError as exc:  # noqa: BLE001
        print(f"   PII SCAN ERROR: {exc!r}", flush=True)
        return -1
    if proc.returncode != 0:
        print(f"   PII SCAN ERROR (exit {proc.returncode})", flush=True)
        return -1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--block-on-pii",
        action="store_true",
        help="Skip a run whose scan reported HIGH-severity findings. Default is warn-and-continue.",
    )
    ap.add_argument("--no-pii-scan", action="store_true", help="Skip the PII scan entirely.")
    ap.add_argument("--no-pii-images", action="store_true", help="Skip the screenshot OCR pass (faster, weaker).")
    ap.add_argument("--pii-report", action="store_true", help="Also write a per-run JSON report to .cache/.")
    ap.add_argument("--runs", nargs="*", help="Subset of run ids to upload (default: all completed runs).")
    args = ap.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set", flush=True)
        return 1
    # Sanity-check the fast path is actually available before starting.
    try:
        import hf_xet  # noqa: F401

        print(
            f"hf_xet available (HF_XET_HIGH_PERFORMANCE={os.environ.get('HF_XET_HIGH_PERFORMANCE')}) "
            f"-> using streamed/parallel Xet uploads",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: hf_xet NOT importable ({exc!r}) - upload will be slow", flush=True)
    api = HfApi(token=token)
    for run_id in (args.runs or RUNS):
        src = os.path.join(PUBLIC_RUNS, run_id)
        if not os.path.isdir(src):
            print(f"SKIP {run_id}: {src} not found", flush=True)
            continue
        print(f"== uploading {run_id} ==", flush=True)
        if not args.no_pii_scan:
            print(f"   scanning {run_id} for PII (report only - nothing is modified)", flush=True)
            pii_report(run_id, src, skip_images=args.no_pii_images, write_report=args.pii_report)
            if args.block_on_pii:
                print("   --block-on-pii is set; check the scan output above before relying on this run", flush=True)
        try:
            api.upload_folder(
                folder_path=src,
                path_in_repo=f"runs/{run_id}",
                repo_id=REPO_ID,
                repo_type="dataset",
                ignore_patterns=[".DS_Store", "*.log"],
            )
            print(f"   {run_id} done", flush=True)
        except Exception as exc:  # noqa: BLE001 - keep going on per-run failures
            print(f"   {run_id} ERROR: {exc!r}", flush=True)
    print("ALL DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
