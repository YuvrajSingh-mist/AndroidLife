#!/usr/bin/env python3
"""Render the public run reports as a blog on the AndroidLife website.

Reads `reports/public/*.md` and writes:
  * one post per report -> androidlife-website/pages/blog/<slug>.html
  * an index           -> androidlife-website/pages/blog.html

The reports are the single source of truth: edit a report, re-run this, and the
post updates. A run id listed in UNPUBLISHED is skipped, so its report stays in
the repo without appearing on the site.
Relative links into the repo (e.g. ../../docs/manual-audit-protocol.md)
are rewritten to GitHub blob URLs so nothing 404s on the deployed site.

Usage (from the repo root):
    python3 scripts/tools/build_blog.py            # write the pages
    python3 scripts/tools/build_blog.py --check    # report drift only, no writes
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "public"
SITE = ROOT / "androidlife-website"
OUT_INDEX = SITE / "pages" / "blog.html"
OUT_DIR = SITE / "pages" / "blog"

GITHUB_BLOB = "https://github.com/YuvrajSingh-mist/AndroidLife/blob/master"

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "attr_list"]

# Reports that stay in the repo (and keep their normal format) but are not
# published as posts. Add a run id here to take its post down; remove it to
# put the post back. Kept in code rather than in the report so the report
# stays a clean data artifact.
UNPUBLISHED: frozenset[str] = frozenset({
    "20260917-160018",  # interrupted run (battery/ADB death at 3%) - not for the blog yet
})


@dataclass
class Post:
    slug: str
    title: str
    date: str
    model: str
    blob: str
    summary: str
    source: Path


def parse(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    title = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)
    run = next((re.search(r"`([^`]+)`", l).group(1)
                for l in lines if l.startswith("**Run root:**") and re.search(r"`([^`]+)`", l)), "")
    date = next((l.split("**Date:**", 1)[1].strip()
                 for l in lines if l.startswith("**Date:**")), "")
    model = next((l.split("**Model under test:**", 1)[1].strip()
                  for l in lines if l.startswith("**Model under test:**")), "")

    # The blockquote right under the header reads as the post's standfirst.
    quote: list[str] = []
    started = False
    for l in lines:
        if l.startswith("> ") or l == ">":
            started = True
            quote.append(l.lstrip("> ").rstrip())
        elif started and l.strip() == "":
            break
        elif started:
            break
    summary = " ".join(q for q in quote if q)

    slug = path.stem.replace("public-", "").replace("public", "").strip("-") or path.stem
    return Post(slug=slug, title=title, date=date, model=model,
                blob=run, summary=summary, source=path)


def body_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    # Drop the leading H1: the page hero already renders the title.
    text = re.sub(r"^# .*\n", "", text, count=1)
    # Repo-relative links would 404 once deployed.
    text = re.sub(r"\]\(\.\./\.\./([^)]+)\)", rf"]({GITHUB_BLOB}/\1)", text)
    return text


def render_body(path: Path) -> str:
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    return md.convert(body_markdown(path))


NAV = """<nav aria-label="Main navigation">
  <a href="{p}index.html" class="nav-title">AndroidLife</a>
  <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation" aria-label="Open navigation menu">
    <span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>
  </button>
  <div class="nav-links" id="primary-navigation">
    <a href="{blog}"{blog_active}>Blog</a>
    <a href="{p}pages/tasks.html">Tasks</a>
    <a href="{p}pages/browse-apps.html">Browse Apps</a>
    <a href="{p}pages/how-it-was-formed.html">How it was formed</a>
    <a href="{p}pages/arena.html">Arena</a>
  </div>
</nav>"""

FOOTER = """<footer>
  <div class="container">
    <div class="footer-links">
      <a href="{blog}">Blog</a>
      <a href="{p}pages/how-it-was-formed.html">How it was formed</a>
      <a href="{p}pages/tasks.html">Tasks</a>
      <a href="{p}pages/arena.html">Arena</a>
    </div>
    <p><strong>AndroidLife</strong> &nbsp;&middot;&nbsp; real-phone Android agent benchmark &nbsp;&middot;&nbsp; GitHub Pages ready</p>
    <p><em>Built by Yuvraj Singh.</em></p>
    <p class="footnote">For business inquiries, contact <a href="mailto:yuvraj.mist@gmail.com">yuvraj.mist@gmail.com</a>.</p>
  </div>
</footer>"""

SCRIPTS = """<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"></script>
<script src="{p}assets/js/nav.js?v=13"></script>
<script src="{p}assets/js/app.js?v=13"></script>"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="{canonical}">
  <title>{title_html} - AndroidLife</title>
  <meta name="description" content="{desc}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css">
  <link rel="stylesheet" href="{p}assets/css/style.css?v=40">
  <script src="{p}assets/js/posthog.js"></script>
</head>"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def render_post(post: Post, body: str) -> str:
    p = "../../"
    nav = NAV.format(p=p, blog="../blog.html", blog_active=' class="nav-active"')
    desc = esc((post.summary or post.title)[:180])
    meta_bits = [b for b in (post.date, post.blob and f"run `{post.blob}`") if b]
    return f"""{HEAD.format(canonical=f"https://androidlife-website.vercel.app/pages/blog/{post.slug}.html", title_html=esc(post.title), desc=desc, p=p)}
<body data-site-data="../assets/data/site_data.json">

{nav}

<main>
  <div class="hero">
    <div class="container">
      <p class="blog-kicker">Run report</p>
      <h1>{esc(post.title)}</h1>
      <p class="hero-subtitle">{esc(post.model)}</p>
      <p class="hero-desc">{esc(" · ".join(meta_bits))}</p>
      <div class="hero-btns">
        <a href="../blog.html" class="btn btn-outline">&larr; All posts</a>
        <a href="{p}index.html#leaderboard" class="btn btn-outline">Leaderboard</a>
      </div>
    </div>
  </div>

  <section>
    <div class="container">
      <article class="prose blog-prose">
{body}
      </article>
    </div>
  </section>
</main>

{FOOTER.format(p=p, blog="../blog.html")}

{SCRIPTS.format(p=p)}
</body>
</html>
"""


def render_index(posts: list[Post]) -> str:
    p = "../"
    nav = NAV.format(p=p, blog="./blog.html", blog_active=' class="nav-active"')
    cards = []
    for post in posts:
        cards.append(f"""        <li class="blog-card">
          <a class="blog-card-link" href="./blog/{post.slug}.html">
            <p class="blog-card-date">{esc(post.date)}</p>
            <h3 class="blog-card-title">{esc(post.title)}</h3>
            <p class="blog-card-model">{esc(post.model)}</p>
            <p class="blog-card-sum">{esc(post.summary[:240])}{"…" if len(post.summary) > 240 else ""}</p>
            <span class="blog-card-more">Read the report &rarr;</span>
          </a>
        </li>""")
    desc = "Every AndroidLife public run report, in full: manual-audit verdicts, cost, battery, thermals, and honesty controls."
    return f"""{HEAD.format(canonical="https://androidlife-website.vercel.app/pages/blog.html", title_html="Blog", desc=desc, p=p)}
<body data-site-data="../assets/data/site_data.json">

{nav}

<main>
  <div class="hero">
    <div class="container">
      <h1>Blog</h1>
      <p class="hero-subtitle">Every public run, reported in full</p>
      <p class="hero-desc">
        One post per public benchmark run. These are the same reports the leaderboard is built
        from &mdash; manual-audit verdicts for all 60 tasks, cost and token breakdowns, per-app
        battery drain, device thermals, and the hallucination-control results. Published
        unedited, including the runs that went badly.
      </p>
    </div>
  </div>

  <section>
    <div class="container">
      <ul class="blog-list">
{chr(10).join(cards)}
      </ul>
    </div>
  </section>
</main>

{FOOTER.format(p=p, blog="./blog.html")}

{SCRIPTS.format(p=p)}
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Report drift without writing.")
    args = ap.parse_args()

    sources = sorted(REPORTS.glob("*.md"))
    if not sources:
        print(f"error: no reports found in {REPORTS}")
        return 1

    posts = []
    for source in sources:
        post = parse(source)
        if post.slug in UNPUBLISHED:
            print(f"   skip   {source.relative_to(ROOT)} (unpublished)")
            continue
        posts.append(post)
    # Newest run id first (run ids sort lexicographically by date).
    posts.sort(key=lambda x: x.slug, reverse=True)

    drift = 0
    plan: list[tuple[Path, str]] = []
    for post in posts:
        plan.append((OUT_DIR / f"{post.slug}.html", render_post(post, render_body(post.source))))
    plan.append((OUT_INDEX, render_index(posts)))

    for path, content in plan:
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        drift += 1
        state = "update" if path.exists() else "create"
        print(f"   {state:6} {path.relative_to(ROOT)}")

    print(f"\n   {len(posts)} post(s), {drift} file(s) to write")
    if args.check:
        return 1 if drift else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in plan:
        path.write_text(content, encoding="utf-8")
    print("   written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
