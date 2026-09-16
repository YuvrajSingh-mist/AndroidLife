#!/usr/bin/env python3
"""Retry HF upload for Gemma run 20260916-011341 until commits succeed."""
from __future__ import annotations

import os
import time
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2] if False else Path.cwd()
REPO = "YuvrajSingh9886/androidlife-public"
RUN_ID = "20260916-011341"


def token() -> str:
    t = os.environ.get("HF_TOKEN")
    if t:
        return t
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("HF_TOKEN missing")


def main() -> int:
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
    api = HfApi(token=token())
    jobs = [
        ("file", "reports/public/public-20260916-011341.md", "reports/public/public-20260916-011341.md"),
        ("file", "reports/metrics/public/public-20260916-011341-report.json", "reports/metrics/public/public-20260916-011341-report.json"),
        ("file", "reports/metrics/public/public-20260916-011341-report.md", "reports/metrics/public/public-20260916-011341-report.md"),
        ("file", "reports/metrics/hallucination/public-20260916-011341.json", "reports/metrics/hallucination/public-20260916-011341.json"),
        ("file", "reports/metrics/hallucination/public-20260916-011341.md", "reports/metrics/hallucination/public-20260916-011341.md"),
        ("folder", "reports/public/audit-20260916-011341", "reports/public/audit-20260916-011341"),
        ("folder", f"assets/runs/public/{RUN_ID}/day1", f"runs/{RUN_ID}/day1"),
        ("folder", f"assets/runs/public/{RUN_ID}/day2", f"runs/{RUN_ID}/day2"),
        ("folder", f"assets/runs/public/{RUN_ID}/day3", f"runs/{RUN_ID}/day3"),
    ]
    for kind, src, dest in jobs:
        attempt = 0
        while True:
            attempt += 1
            try:
                print(f"== {dest} attempt {attempt} ==", flush=True)
                if kind == "file":
                    api.upload_file(path_or_fileobj=src, path_in_repo=dest, repo_id=REPO, repo_type="dataset")
                else:
                    api.upload_folder(
                        folder_path=src,
                        path_in_repo=dest,
                        repo_id=REPO,
                        repo_type="dataset",
                        ignore_patterns=[".DS_Store", "*.log"],
                    )
                print(f"OK {dest}", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {dest}: {e}", flush=True)
                time.sleep(min(180, 15 * attempt))
    print("ALL UPLOADS DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
