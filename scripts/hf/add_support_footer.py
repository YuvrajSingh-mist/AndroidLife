#!/usr/bin/env python3
"""Append a support footer (project blurb + website + Ko-fi + GitHub Sponsors)
to every Hugging Face repo README under the account.

Two variants:
  * AndroidLife repos  -> full project blurb + leaderboard/code/dataset links
  * everything else    -> short "support the work" footer

Idempotent: a repo whose README already carries the `ad-footer` marker is
skipped, so re-running never stacks footers.

Usage (from the repo root):
    python3 scripts/hf/add_support_footer.py            # dry run: plan only
    python3 scripts/hf/add_support_footer.py --push     # write the READMEs
    python3 scripts/hf/add_support_footer.py --push --only androidlife-530
"""
from __future__ import annotations

import argparse
import os
import sys

from huggingface_hub import CommitOperationAdd, HfApi
from huggingface_hub.utils import EntryNotFoundError

AUTHOR = "YuvrajSingh9886"
MARKER = "<!-- ad-footer -->"
SITE = "https://androidlife-website.vercel.app/"
CODE = "https://github.com/YuvrajSingh-mist/AndroidLife"
KOFI = "https://ko-fi.com/O7W120DR8R"
SPONSORS = "https://github.com/sponsors/YuvrajSingh-mist"
KOFI_BADGE = "https://storage.ko-fi.com/cdn/kofi2.png?v=3"
SPONSOR_BADGE = ("https://img.shields.io/badge/Sponsor-GitHub-ea4aaa"
                 "?logo=githubsponsors&logoColor=white")

# Repos that are part of AndroidLife and get the full blurb.
ANDROIDLIFE = {
    "dataset:androidlife-530",
    "dataset:androidlife-public",
    "dataset:androidlife-public-sample",
    "dataset:androidlife-trajectories",
    "model:DailyBench300-trajectories",
}

SUPPORT_LINKS = (
    f"[![Support me on Ko-fi]({KOFI_BADGE})]({KOFI})\n"
    f"[![GitHub Sponsors]({SPONSOR_BADGE})]({SPONSORS})"
)

FOOTER_ANDROIDLIFE = f"""
{MARKER}
---

## About AndroidLife

**AndroidLife** is a real-phone Android agent benchmark. **530 tasks** (Easy 1pt /
Medium 3pt / Hard 5pt) run against an actual handset over ADB + MobileRun and are
graded on a verifiable **on-device end state** — not a simulator, not a mock API.
Tasks span Gmail, Calendar, Meet, Maps, Drive, Files, Contacts, Photos, YouTube,
Telegram, Swiggy, Amazon and more, and the corpus deliberately separates:

- **deterministic** tasks, where everything needed is seeded on the device;
- **ASK USER** tasks, where one load-bearing fact is withheld and the agent must ask a simulated user;
- **hallucination controls**, where the honest answer is "this does not exist", so a confident false success is caught.

Every run is manual-audited against the device end state, and reports disclose cost,
tokens, per-app battery drain and CPU/GPU/NPU thermals for each row.

- 🌐 **Leaderboard + live step-by-step trajectories:** <{SITE}>
- 💻 **Code:** <{CODE}>
- 📚 **All datasets & models:** <https://huggingface.co/{AUTHOR}>

## Fuel the bench

A full 60-task suite is ~6.5 h of wall-clock on a phone that runs hot enough to
throttle, plus real API spend. If these numbers helped you pick a model or a board,
fuel the next run:

{SUPPORT_LINKS}
"""

FOOTER_GENERIC = f"""
{MARKER}
---

## Support the work

Released freely — if it saved you some time, you can support more experiments like it:

{SUPPORT_LINKS}

More of my work: <https://huggingface.co/{AUTHOR}>
"""


def build_footer(repo_type: str, name: str) -> str:
    return (FOOTER_ANDROIDLIFE if f"{repo_type}:{name}" in ANDROIDLIFE
            else FOOTER_GENERIC)


def fetch_readme(api: HfApi, repo_id: str, repo_type: str) -> str | None:
    from pathlib import Path
    try:
        p = api.hf_hub_download(repo_id=repo_id, filename="README.md",
                                repo_type=repo_type, force_download=True)
    except EntryNotFoundError:
        return None
    except Exception:
        return None
    return Path(p).read_text(encoding="utf-8")


def title_for(name: str, is_al: bool) -> str:
    if is_al:
        return f"# {name}\n\nPart of the AndroidLife real-phone Android agent benchmark.\n"
    return f"# {name}\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--push", action="store_true", help="Write the READMEs (default: dry run).")
    ap.add_argument("--only", nargs="*", help="Limit to these repo names.")
    args = ap.parse_args()

    api = HfApi(token=os.environ.get("HF_TOKEN") or None)
    targets: list[tuple[str, str, str]] = []   # (repo_type, repo_id, name)
    for d in api.list_datasets(author=AUTHOR):
        targets.append(("dataset", d.id, d.id.split("/")[-1]))
    for m in api.list_models(author=AUTHOR):
        targets.append(("model", m.id, m.id.split("/")[-1]))

    if args.only:
        want = set(args.only)
        targets = [t for t in targets if t[2] in want]

    print(f"repos: {len(targets)}  (push={args.push})\n")
    todo, skipped, fresh = [], [], []
    for repo_type, repo_id, name in sorted(targets, key=lambda t: t[1]):
        is_al = f"{repo_type}:{name}" in ANDROIDLIFE
        body = fetch_readme(api, repo_id, repo_type)
        if body is None:
            fresh.append((repo_type, repo_id, is_al))
            continue
        if MARKER in body:
            skipped.append(name)
            continue
        todo.append((repo_type, repo_id, body.rstrip() + "\n", is_al))

    print(f"to update : {len(todo)}")
    print(f"new README: {len(fresh)}")
    print(f"already has footer (skipped): {len(skipped)}")
    for _, repo_id, _, is_al in todo:
        print(f"   {'[AL]' if is_al else '    '} {repo_id}")
    for repo_type, repo_id, is_al in fresh:
        print(f"   {'[AL]' if is_al else '    '} {repo_id}  (no README -> create)")

    if not args.push:
        print("\n(dry run — pass --push to write)")
        return 0

    for repo_type, repo_id, body, is_al in todo:
        new = body + build_footer(repo_type, repo_id.split("/")[-1])
        api.create_commit(
            repo_id=repo_id, repo_type=repo_type,
            operations=[CommitOperationAdd(path_in_repo="README.md",
                                           path_or_fileobj=new.encode("utf-8"))],
            commit_message="docs: add support footer (project info + Ko-fi + sponsors)",
        )
        print(f"   updated  {repo_id}")

    for repo_type, repo_id, is_al in fresh:
        new = title_for(repo_id.split("/")[-1], is_al) + build_footer(repo_type, repo_id.split("/")[-1])
        api.create_commit(
            repo_id=repo_id, repo_type=repo_type,
            operations=[CommitOperationAdd(path_in_repo="README.md",
                                           path_or_fileobj=new.encode("utf-8"))],
            commit_message="docs: add README with support footer",
        )
        print(f"   created  {repo_id}")

    print(f"\ndone: {len(todo) + len(fresh)} repo(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
