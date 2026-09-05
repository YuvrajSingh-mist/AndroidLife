"""Upload the completed public benchmark runs to the dailybench500-public HF dataset"""

from __future__ import annotations

import os
import sys

from huggingface_hub import HfApi

REPO_ID = "YuvrajSingh9886/dailybench500-public"
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
]


def main() -> int:
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
    for run_id in RUNS:
        src = os.path.join(PUBLIC_RUNS, run_id)
        if not os.path.isdir(src):
            print(f"SKIP {run_id}: {src} not found", flush=True)
            continue
        print(f"== uploading {run_id} ==", flush=True)
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
