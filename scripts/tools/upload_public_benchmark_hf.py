#!/usr/bin/env python3
"""Refresh `benchmark/` + README on YuvrajSingh9886/androidlife-public.

Uploads the current public-sample sidecars from benchmarks/androidlife-530/
(JSON/JSONL, ask_user_facts_public, multiturn KB, public.md, vars, HC) and a
compact tasks_preview.jsonl so the HF Dataset Viewer can table-browse the 60
tasks. Removes legacy filenames left from earlier uploads.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "YuvrajSingh9886/androidlife-public"
ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmarks" / "androidlife-530"
README_SRC = ROOT / "hf_release" / "androidlife-public-README.md"

UPLOAD_FILES = [
    "AndroidLife_public_v2.json",
    "AndroidLife_public_v2.jsonl",
    "ask_user_facts_public.json",
    "multiturn_kb_public.json",
    "public.md",
    "hallucination_controls.json",
    "public_vars.example.env",
    "public_vars.local.env",
]

# Stale paths from earlier uploads (DailyBench / 730 / wrong corpus files).
DELETE_PATHS = [
    "benchmark/ask_user_facts.json",
    "benchmark/ask_user_facts_730.json",
    "benchmark/multiturn_kb_530.json",
    "benchmark/tasks.md",
    "benchmark/tasks_vars_usage.json",
]

PREVIEW_COLS = [
    "task_id",
    "day",
    "bucket",
    "difficulty",
    "points",
    "app",
    "ahi",
    "interaction",
    "is_ask_user",
    "cross_app_required",
    "prompt_text",
]


def _write_preview(dst: Path) -> None:
    tasks = json.loads((BENCH / "AndroidLife_public_v2.json").read_text(encoding="utf-8"))["tasks"]
    with dst.open("w", encoding="utf-8") as f:
        for t in tasks:
            row = {k: t.get(k) for k in PREVIEW_COLS}
            row["apps"] = ", ".join(t.get("apps") or [])
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stage(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name in UPLOAD_FILES:
        src = BENCH / name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, out / name)
        print(f"  staged {name}")
    _write_preview(out / "tasks_preview.jsonl")
    print(f"  staged tasks_preview.jsonl ({sum(1 for _ in (out / 'tasks_preview.jsonl').open())} rows)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Stage only; do not upload.")
    args = ap.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token and not args.dry_run:
        # Fall back to huggingface_hub cached login.
        from huggingface_hub.utils import get_token

        token = get_token()
    if not token and not args.dry_run:
        print("HF_TOKEN not set and no cached login", flush=True)
        return 1

    with tempfile.TemporaryDirectory(prefix="androidlife-public-benchmark-") as tmp:
        staged = Path(tmp) / "benchmark"
        print(f"staging -> {staged}", flush=True)
        stage(staged)
        if args.dry_run:
            print("dry-run: skip upload")
            return 0

        api = HfApi(token=token)
        print(f"uploading folder -> {REPO_ID}:benchmark/", flush=True)
        api.upload_folder(
            folder_path=str(staged),
            path_in_repo="benchmark",
            repo_id=REPO_ID,
            repo_type="dataset",
            commit_message="Refresh public benchmark sample (json/jsonl, facts, KB, preview)",
        )
        if README_SRC.exists():
            print("uploading README.md", flush=True)
            api.upload_file(
                path_or_fileobj=str(README_SRC),
                path_in_repo="README.md",
                repo_id=REPO_ID,
                repo_type="dataset",
                commit_message="Document public task sample + Dataset Viewer configs",
            )
        existing = set(api.list_repo_files(REPO_ID, repo_type="dataset"))
        to_delete = [p for p in DELETE_PATHS if p in existing]
        if to_delete:
            print(f"deleting legacy paths: {to_delete}", flush=True)
            api.delete_files(
                delete_patterns=to_delete,
                repo_id=REPO_ID,
                repo_type="dataset",
                commit_message="Remove legacy benchmark/ filenames (730 / wrong corpus)",
            )
        else:
            print("no legacy paths to delete", flush=True)

    print("DONE", flush=True)
    print(f"viewer: https://huggingface.co/datasets/{REPO_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
