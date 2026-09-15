"""One-shot upload of 20260909 + 20260910 to androidlife-public."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2]
REPO_ID = "YuvrajSingh9886/androidlife-public"
RUNS = ["20260909-043419", "20260910-041531"]
os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")


def load_token() -> str:
    tok = os.environ.get("HF_TOKEN")
    if tok:
        return tok
    env = ROOT / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("HF_TOKEN not set")


def main() -> int:
    token = load_token()
    try:
        import hf_xet  # noqa: F401

        print("hf_xet OK", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"hf_xet missing: {exc!r}", flush=True)
    api = HfApi(token=token)
    for run_id in RUNS:
        src = ROOT / "assets" / "runs" / "public" / run_id
        if not src.is_dir():
            print(f"SKIP missing {src}", flush=True)
            continue
        print(f"== uploading {run_id} ({src}) ==", flush=True)
        api.upload_folder(
            folder_path=str(src),
            path_in_repo=f"runs/{run_id}",
            repo_id=REPO_ID,
            repo_type="dataset",
            ignore_patterns=[".DS_Store", "*.log", "*.pid"],
        )
        print(f"   DONE {run_id}", flush=True)
    print("ALL DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
