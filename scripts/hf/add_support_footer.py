#!/usr/bin/env python3
"""Append a support footer (project blurb + website + Ko-fi + GitHub Sponsors)
to every Hugging Face repo README under the account.

Two variants:
  * AndroidLife repos  -> short project blurb + leaderboard / collection / code links
  * everything else    -> short "support the work" footer

Idempotent: a repo whose README already carries the `ad-footer` marker is
skipped, so re-running never stacks footers. Pass --force to *replace* an
existing footer (e.g. after the wording was tightened) instead of skipping it.

Usage (from the repo root):
    python3 scripts/hf/add_support_footer.py                # dry run: plan only
    python3 scripts/hf/add_support_footer.py --push         # write new footers
    python3 scripts/hf/add_support_footer.py --push --force # rewrite existing ones
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
COLLECTION = ("https://huggingface.co/collections/YuvrajSingh9886/"
              "androidlife-can-llm-agents-survive-a-day-in-your-life")
KOFI = "https://ko-fi.com/O7W120DR8R"
SPONSORS = "https://github.com/sponsors/YuvrajSingh-mist"
KOFI_BADGE = "https://storage.ko-fi.com/cdn/kofi2.png?v=3"
SPONSOR_BADGE = ("https://img.shields.io/badge/Sponsor-GitHub-ea4aaa"
                 "?logo=githubsponsors&logoColor=white")

# Repos that are part of AndroidLife and get the project blurb.
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

# Kept deliberately short: link out for detail, don't paste an essay.
FOOTER_ANDROIDLIFE = f"""
{MARKER}
---

**AndroidLife** — a real-phone Android agent benchmark. 530 tasks, graded on the
on-device end state: not a simulator, not a mock API.

[Leaderboard + step-by-step replays]({SITE}) · [All models & datasets]({COLLECTION}) · [Code]({CODE})

*Fuel the next run — a full 60-task suite is ~6.5 h of phone time plus real API spend:*

{SUPPORT_LINKS}
"""

FOOTER_GENERIC = f"""
{MARKER}
---

*Released freely — support more experiments like it:*

{SUPPORT_LINKS}

More: <https://huggingface.co/{AUTHOR}>
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


def strip_footer(body: str) -> str:
    """Drop everything from the marker on, so a new footer can replace it."""
    return body[:body.index(MARKER)].rstrip() + "\n"


def title_for(name: str, is_al: bool) -> str:
    if is_al:
        return f"# {name}\n\nPart of the AndroidLife real-phone Android agent benchmark.\n"
    return f"# {name}\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--push", action="store_true", help="Write the READMEs (default: dry run).")
    ap.add_argument("--force", action="store_true",
                    help="Replace an existing footer instead of skipping the repo.")
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

    print(f"repos: {len(targets)}  (push={args.push}, force={args.force})\n")
    todo, skipped, fresh = [], [], []
    for repo_type, repo_id, name in sorted(targets, key=lambda t: t[1]):
        is_al = f"{repo_type}:{name}" in ANDROIDLIFE
        body = fetch_readme(api, repo_id, repo_type)
        if body is None:
            fresh.append((repo_type, repo_id, is_al))
            continue
        if MARKER in body:
            if not args.force:
                skipped.append(name)
                continue
            body = strip_footer(body)
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
            commit_message="docs: tighten the support footer (project info + Ko-fi + sponsors)",
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
