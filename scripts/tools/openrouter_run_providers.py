#!/usr/bin/env python3
"""Resolve which upstream providers actually served an OpenRouter run.

Why this exists
---------------
The public leaderboard labels OpenRouter rows with the *model author*
("Alibaba (OpenRouter)"), which is not the same thing as the *provider that
served the inference*. OpenRouter routes a request across every endpoint it has
capacity on unless the caller pins one with `provider.order` / `provider.only`,
and the harness does not pin. So a single run is spread over many providers,
each of which may serve a differently quantized copy of the same model. That is
why an OpenRouter row cannot honestly carry one quantization string.

The run's `llm_proxy_metrics.jsonl` logs each response's OpenRouter generation id
(`gen-...`). `GET /api/v1/generation?id=<gen-id>` resolves that id to the
`provider_name` that served it. This script samples generation ids from a run and
reports the provider distribution.

Caveats
-------
- OpenRouter expires generation records (roughly a month), so old runs return
  404 and cannot be back-filled.
- The endpoint carries no quantization field, so quant is joined separately from
  `GET /api/v1/models/<author>/<slug>/endpoints`, which reflects the provider
  registry *now*, not at run time.

Usage
-----
    uv run python scripts/tools/openrouter_run_providers.py --run 2026-08-28-002424
    uv run python scripts/tools/openrouter_run_providers.py --all --sample 12
    uv run python scripts/tools/openrouter_run_providers.py --run ... --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEADERBOARD_JS = REPO / "androidlife-website" / "assets" / "js" / "leaderboard.js"
CACHE = REPO / ".cache" / "openrouter_providers.json"

HF_DATASET = "YuvrajSingh9886/androidlife-public"
HF_TREE = f"https://huggingface.co/api/datasets/{HF_DATASET}/tree/main/runs"
HF_FILE = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/runs"
GEN_API = "https://openrouter.ai/api/v1/generation"
MODELS_API = "https://openrouter.ai/api/v1/models"
USER_AGENT = "androidlife-leaderboard/1.0"


def _key() -> str | None:
    """OpenRouter key from the environment, else the repo's .env (never printed)."""
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def _get(url: str, key: str | None = None, timeout: int = 45) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def load_rows() -> list[dict]:
    """Evaluate LEADERBOARD_ROWS in node — the array is a JS literal."""
    script = (
        "const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');"
        "const s=src.indexOf('const LEADERBOARD_ROWS = [');"
        "const e=src.indexOf('\\n];', s);"
        "process.stdout.write(JSON.stringify(eval(src.slice(s+25,e+2))));"
    )
    out = subprocess.run(
        ["node", "-e", script, str(LEADERBOARD_JS)], capture_output=True, text=True, check=True
    ).stdout
    return json.loads(out)


def gen_ids_for_run(run_ts: str, sample: int) -> list[str]:
    """Sample `gen-` ids from the run's proxy metrics on the HF dataset."""
    try:
        days = _get(f"{HF_TREE}/{run_ts}")
    except urllib.error.HTTPError:
        return []
    ids: list[str] = []
    day_dirs = [d["path"] for d in days if d.get("type") == "directory"]
    for day in day_dirs:
        try:
            tasks = _get(f"https://huggingface.co/api/datasets/{HF_DATASET}/tree/main/{day}")
        except urllib.error.HTTPError:
            continue
        for t in tasks:
            if t.get("type") != "directory":
                continue
            url = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/{t['path']}/llm_proxy_metrics.jsonl"
            try:
                raw = urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=45
                ).read().decode(errors="replace")
            except Exception:
                continue
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                gid = rec.get("id") or ""
                if gid.startswith("gen-"):
                    ids.append(gid)
            if len(ids) >= sample * 4:
                break
        if len(ids) >= sample * 4:
            break
    # even stride across the run so we don't sample one task's provider mix only
    if len(ids) > sample:
        step = len(ids) / sample
        ids = [ids[int(i * step)] for i in range(sample)]
    return ids


def resolve(gid: str, key: str) -> str | None:
    try:
        return (_get(f"{GEN_API}?id={gid}", key) or {}).get("data", {}).get("provider_name")
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None


def provider_quants(slug: str) -> dict[str, str]:
    """provider_name -> quantization, from the current endpoint registry."""
    try:
        data = _get(f"{MODELS_API}/{slug}/endpoints").get("data", {})
    except Exception:
        return {}
    out: dict[str, str] = {}
    for e in data.get("endpoints", []):
        name = e.get("provider_name")
        if name and name not in out:
            out[name] = e.get("quantization") or "unknown"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", help="run timestamp (the runRoot basename); repeatable")
    ap.add_argument("--all", action="store_true", help="every non-local leaderboard row")
    ap.add_argument("--sample", type=int, default=12, help="generation ids to resolve per run (default 12)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    rows = load_rows()
    targets: list[dict] = []
    for r in rows:
        if "(local" in (r.get("org") or ""):
            continue
        ts = (r.get("runRoot") or "").rstrip("/").split("/")[-1]
        if not ts:
            continue
        if args.run and ts not in args.run:
            continue
        targets.append({"ts": ts, "model": r["model"], "slug": r.get("openrouterSlug") or ""})
    if not args.all and not args.run:
        ap.error("pass --run <ts> (repeatable) or --all")

    key = _key()
    if not key:
        print("OPENROUTER_API_KEY missing (env or repo .env)", file=sys.stderr)
        return 2

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    report = {}
    for t in targets:
        ts = t["ts"]
        entry = cache.setdefault(ts, {"model": t["model"], "gen_ids": {}, "sample": args.sample})
        ids = entry.get("gen_ids") or {}
        if not ids:
            gids = gen_ids_for_run(ts, args.sample)
            if not gids:
                report[ts] = {"model": t["model"], "error": "no proxy metrics on HF"}
                if not args.json:
                    print(f"{ts}  {t['model']}: no proxy metrics on HF")
                continue
            for gid in gids:
                ids[gid] = None
                time.sleep(0.25)
            entry["gen_ids"] = ids
            CACHE.write_text(json.dumps(cache, indent=1))
        # resolve any still-unknown
        for gid in list(ids):
            if ids[gid] is None:
                ids[gid] = resolve(gid, key) or "unknown"
                time.sleep(0.25)
        CACHE.write_text(json.dumps(cache, indent=1))

        dist = Counter(ids.values())
        quants = provider_quants(t["slug"]) if t["slug"] else {}
        report[ts] = {
            "model": t["model"],
            "resolved": sum(1 for v in ids.values() if v != "unknown"),
            "providers": dict(dist.most_common()),
            "quants": {p: quants.get(p, "?") for p in dist},
        }
        if not args.json:
            print(f"\n{ts}  {t['model']}  ({len(ids)} generations sampled)")
            for p, n in dist.most_common():
                print(f"   {p:<16} {n:>3}x   quant={quants.get(p, '?')}")

    if args.json:
        print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
