#!/usr/bin/env python3
"""Publish website trajectory assets to a public HuggingFace repo.

Moves all trajectory media (GIFs + per-step screenshots + per-task condensed
step JSON) out of the git repo and onto HF, so the git tree stays small while
the published site keeps full trajectory replay by loading from HF resolve URLs.

What it does:
  1. Rewrites website/assets/data/trajectories/index.json so every `gif` and
     `data` path becomes an absolute HF resolve URL.
  2. Rewrites each per-task data JSON's `screenshot_base` to the HF resolve URL.
  3. Uploads to the HF repo:
       index.json
       data/trajectories/<set>/<day>/<task>.json      (rewritten)
       trajectories/<set>/<day>/<task>/trajectory.gif  (media, LFS)
       trajectories/<set>/<day>/<task>/screenshots/*   (media, LFS)
  4. Writes the rewritten index.json back to the local tree (it's the small
     metadata manifest the site + build_site_data.mjs read; the heavy media is
     no longer tracked).

Usage (from the repo root):
    uv run python scripts/tools/publish_trajectories.py
    uv run python scripts/tools/publish_trajectories.py --repo Other/Name

Requires huggingface_hub (dev extra) + a logged-in HF token.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "website" / "assets" / "data" / "trajectories" / "index.json"
DATA_DIR = ROOT / "website" / "assets" / "data" / "trajectories"
MEDIA_DIR = ROOT / "website" / "assets" / "trajectories"

DEFAULT_REPO = "YuvrajSingh9886/DailyBench300-trajectories"
LFS_THRESHOLD = 5 * 1024 * 1024  # upload_folder handles LFS automatically


def resolve_base(repo: str) -> str:
    return f"https://huggingface.co/datasets/{repo}/resolve/main"


def rewrite_index(index: dict, base: str) -> dict:
    """Rewrite every gif/data path to an absolute HF resolve URL.

    Local paths are site-root-relative (e.g. assets/trajectories/...) but the
    HF repo stores media under trajectories/... and data under
    data/trajectories/... (the assets/ prefix is dropped on upload), so the
    prefix is stripped here.
    """
    out = json.loads(json.dumps(index))  # deep copy
    for section in ("tasks", "public"):
        for entry in out.get(section, {}).values():
            gif = entry.get("gif")
            data = entry.get("data")
            if gif and gif.startswith("assets/"):
                entry["gif"] = f"{base}/{gif[len('assets/'):]}"
            if data and data.startswith("assets/"):
                entry["data"] = f"{base}/{data[len('assets/'):]}"
    return out


def rewrite_screenshot_base(data: dict, base: str) -> dict:
    out = json.loads(json.dumps(data))
    sb = out.get("screenshot_base")
    if sb and sb.startswith("assets/"):
        out["screenshot_base"] = f"{base}/{sb[len('assets/'):]}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=DEFAULT_REPO, help="HF repo id (dataset).")
    ap.add_argument("--dry-run", action="store_true", help="Rewrite locally only, no upload.")
    ap.add_argument("--skip-media", action="store_true",
                    help="Skip the trajectories/ media upload (re-upload JSONs only).")
    args = ap.parse_args()

    if not INDEX.exists():
        print(f"index not found: {INDEX}")
        return 1

    base = resolve_base(args.repo)
    api = HfApi()
    if not args.dry_run:
        print(f"repo: {api.whoami()['name']} -> {args.repo}")
        api.create_repo(repo_id=args.repo, repo_type="dataset", private=False, exist_ok=True)

    # 1) Rewrite the index manifest (kept in git: it's small metadata).
    index = json.loads(INDEX.read_text())
    rewritten = rewrite_index(index, base)
    INDEX.write_text(json.dumps(rewritten, indent=1) + "\n")
    n = sum(len(rewritten.get(s, {})) for s in ("tasks", "public"))
    print(f"index rewritten: {n} entries -> absolute HF URLs")

    # 2) Stage rewritten per-task data JSONs (screenshot_base -> HF).
    staged = Path(tempfile.mkdtemp(prefix="traj-stage-"))
    staged_data = staged / "data" / "trajectories"
    n_data = 0
    for p in DATA_DIR.rglob("*.json"):
        if p.name == "index.json":
            continue
        rel = p.relative_to(DATA_DIR)
        dst = staged_data / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(p.read_text())
        dst.write_text(json.dumps(rewrite_screenshot_base(data, base), indent=1) + "\n")
        n_data += 1
    print(f"staged {n_data} per-task data JSONs (screenshot_base -> HF)")

    if args.dry_run:
        print("dry-run: not uploading.")
        shutil.rmtree(staged, ignore_errors=True)
        return 0

    # 3) Upload index.json + data JSONs.
    api.upload_file(
        path_or_fileobj=str(INDEX),
        path_in_repo="index.json",
        repo_id=args.repo,
        repo_type="dataset",
    )
    api.upload_folder(
        folder_path=str(staged_data),
        path_in_repo="data/trajectories",
        repo_id=args.repo,
        repo_type="dataset",
    )
    print("uploaded index.json + data/trajectories/*")

    # 4) Upload media (gifs + screenshots) — the big LFS transfer.
    if not args.skip_media:
        print("uploading media (gifs + screenshots) to trajectories/ ...")
        api.upload_folder(
            folder_path=str(MEDIA_DIR),
            path_in_repo="trajectories",
            repo_id=args.repo,
            repo_type="dataset",
        )
        print("uploaded trajectories/ media")
    else:
        print("skipped trajectories/ media upload (--skip-media)")

    # 5) README for the repo.
    readme = (
        "# DailyBench300 — trajectory replays\n\n"
        "Public trajectory assets for the [DrainBench300](https://github.com/"
        "YuvrajSingh-mist/DrainBench300) Android-agent benchmark, served to the "
        "published site via `resolve/main` URLs.\n\n"
        f"- `index.json` — per-task availability manifest (model, success, steps, gif/data URLs)\n"
        f"- `data/trajectories/<set>/<day>/<task>.json` — condensed step streams (thoughts, tool calls, screenshots)\n"
        f"- `trajectories/<set>/<day>/<task>/trajectory.gif` + `screenshots/` — screen replay + per-step frames\n\n"
        "Regenerate/republish with `uv run python scripts/tools/publish_trajectories.py`.\n"
    )
    api.upload_file(
        path_or_fileobj=readme.encode(),
        path_in_repo="README.md",
        repo_id=args.repo,
        repo_type="dataset",
    )

    shutil.rmtree(staged, ignore_errors=True)
    print(f"done -> https://huggingface.co/datasets/{args.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
