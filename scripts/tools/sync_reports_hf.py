#!/usr/bin/env python3
"""Sync the local reports/ tree up to YuvrajSingh9886/androidlife-public.

Uploads only files that are missing or content-different on the Hub, so it is
safe to re-run. Reports are small text files; images inside them (if any) are
already covered by the run-artifact uploader.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

REPO = "YuvrajSingh9886/androidlife-public"
ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "reports"

os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")


def hf_hashes(api: HfApi) -> dict[str, str]:
    """path_in_repo -> git blob sha for everything under reports/."""
    out: dict[str, str] = {}
    for e in api.list_repo_tree(REPO, "reports", repo_type="dataset", recursive=True):
        if e.__class__.__name__ == "RepoFile" and getattr(e, "blob_id", None):
            out[e.path] = e.blob_id
    return out


def git_blob_sha(path: Path) -> str:
    """Local file -> the same git blob sha HF reports (sha1 of 'blob <n>\\0' + data)."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main() -> int:
    dry = "--push" not in sys.argv
    api = HfApi(token=os.environ.get("HF_TOKEN") or None)

    remote = hf_hashes(api)
    print(f"HF reports/ files: {len(remote)}")

    local = [p for p in LOCAL.rglob("*") if p.is_file()]
    todo: list[tuple[Path, str]] = []
    ops: list[CommitOperationAdd] = []
    for p in local:
        rel = p.relative_to(ROOT).as_posix()
        if remote.get(rel) != git_blob_sha(p):
            todo.append((p, rel))

    print(f"local reports/ files: {len(local)}")
    print(f"to upload: {len(todo)}")
    for _, rel in sorted(todo):
        print(f"   {rel}")

    if dry:
        print("\n(dry run — pass --push to upload)")
        return 0

    for p, rel in sorted(todo):
        ops.append(CommitOperationAdd(path_in_repo=rel, path_or_fileobj=str(p)))

    if ops:
        api.create_commit(
            repo_id=REPO, repo_type="dataset", operations=ops,
            commit_message=f"reports: sync local reports/ to the repo ({len(ops)} file(s))",
        )
    print(f"\ndone: {len(ops)} file(s) uploaded to {REPO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
