#!/usr/bin/env python3
"""Build website public-trajectory index from HF raw runs (no local media copy).

For each public benchmark run on YuvrajSingh9886/dailybench500-public this script:
  1. Lists day*/task folders on HF (or uses a local assets/runs/public/<id> mirror)
  2. Downloads only meta.json / output.json / trajectory.json (tiny)
  3. Writes condensed step JSON under website/assets/data/trajectories/public/<key>/
  4. Points gif + screenshot_base at HF resolve URLs for the raw run media
  5. Merges all runs into website/assets/data/trajectories/index.json

Usage (repo root):
  uv run python website/tools/build_public_traj_from_hf.py
  uv run python website/tools/build_public_traj_from_hf.py --runs mimo-0901   # one run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "website" / "assets" / "data" / "trajectories" / "index.json"
OUT_DATA = ROOT / "website" / "assets" / "data" / "trajectories"

HF_RUNS_REPO = "YuvrajSingh9886/dailybench500-public"
HF_RUNS_BASE = f"https://huggingface.co/datasets/{HF_RUNS_REPO}/resolve/main"

# Oldest → newest (last becomes primary on the site).
PUBLIC_RUNS = [
    {"key": "gemini-26", "label": "gemini-3.1-flash-lite · 26 Aug", "hf_id": "20260826-105200"},
    {"key": "qwen-26", "label": "qwen3.8-27b · 26 Aug (vision)", "hf_id": "2026-08-26-184934"},
    {"key": "qwen-28", "label": "qwen3.8-27b · 28 Aug (text)", "hf_id": "2026-08-28-002424"},
    {"key": "kimi-29", "label": "kimi-k2.6 · 29 Aug (text)", "hf_id": "2026-08-29-153657"},
    {"key": "kimi-30v", "label": "kimi-k2.6 · 30 Aug (vision)", "hf_id": "2026-08-30-021852"},
    {"key": "seed-30", "label": "seed-2.0-lite · 30 Aug", "hf_id": "2026-08-30-143554"},
    {"key": "mimo-0901", "label": "mimo-v2.5-pro · 1 Sep (text)", "hf_id": "20260901-002701"},
    {"key": "seed-05v", "label": "seed-2.0-lite · 5 Sep (vision)", "hf_id": "20260905-051950"},
]

TASK_ID_ALIASES = {
    "medium__obsidian__001": "medium__google-docs__001",
    "easy__google-search__002": "easy__weather__001",
}


def token() -> str | None:
    t = os.environ.get("HF_TOKEN")
    if t:
        return t
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def hf_get_json(path: str):
    url = f"https://huggingface.co/api/datasets/{HF_RUNS_REPO}/tree/main/{path}?recursive=false"
    req = urllib.request.Request(url)
    tok = token()
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def hf_get_json_recursive(path: str) -> list[dict]:
    """Paginated recursive tree listing."""
    items: list[dict] = []
    url = f"https://huggingface.co/api/datasets/{HF_RUNS_REPO}/tree/main/{path}?recursive=true&limit=1000"
    tok = token()
    while url:
        req = urllib.request.Request(url)
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
        with urllib.request.urlopen(req, timeout=180) as r:
            chunk = json.load(r)
            link = r.headers.get("Link") or r.headers.get("link") or ""
        if not isinstance(chunk, list):
            raise RuntimeError(f"bad tree for {path}: {chunk}")
        items.extend(chunk)
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                next_url = part.split(";")[0].strip().strip("<>")
                break
        url = next_url
    return items


def hf_download(path: str) -> bytes:
    url = f"{HF_RUNS_BASE}/{path}"
    req = urllib.request.Request(url)
    tok = token()
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def load_json_bytes(data: bytes):
    return json.loads(data.decode("utf-8"))


def folder_to_task_id(name: str) -> str:
    m = re.match(r"^(easy|medium|hard)-(.+)-(\d+)$", name)
    if not m:
        return name
    return f"{m.group(1)}__{m.group(2)}__{m.group(3)}"


def condense_trajectory(events: list) -> list[dict]:
    """Match website/tools/export_trajectories.mjs condenseTrajectory.

    The task viewer expects tools as {tool_name, tool_args, success, summary}.
    Older HF-builder drafts used FastAgentToolCallEvent + {name, preview}, which
    made every tool render as a red \"error\" badge.
    """
    steps: list[dict] = []
    current = None
    for ev in events:
        et = ev.get("type") or ev.get("event_type") or ""
        if et == "FastAgentResponseEvent":
            current = {
                "index": len(steps),
                "thought": ev.get("thought") or "",
                "code": ev.get("code") or "",
                "usage": ev.get("usage") or None,
                "tools": [],
                "output": "",
            }
            steps.append(current)
        elif et == "ToolExecutionEvent" and current is not None:
            current["tools"].append(
                {
                    "tool_name": ev.get("tool_name") or "",
                    "tool_args": ev.get("tool_args") if "tool_args" in ev else None,
                    "success": bool(ev.get("success")),
                    "summary": ev.get("summary") or "",
                }
            )
        elif et == "FastAgentOutputEvent" and current is not None:
            out = ev.get("output") or ""
            current["output"] = (current["output"] + "\n" + out).strip() if current["output"] else out
    return steps


def no_em_dash(value):
    if isinstance(value, str):
        return re.sub(r"[ \t]*\u2014[ \t]*", " - ", value)
    if isinstance(value, list):
        return [no_em_dash(v) for v in value]
    if isinstance(value, dict):
        return {k: no_em_dash(v) for k, v in value.items()}
    return value


def newest_traj_ts(files: list[str]) -> str | None:
    dirs = set()
    for p in files:
        m = re.search(r"/trajectories/(\d{8}_\d{6}_[0-9a-f]+)/", p)
        if m:
            dirs.add(m.group(1))
    if not dirs:
        return None
    return sorted(dirs)[-1]


def process_task(run: dict, day: int, folder: str, file_index: dict[str, list[str]]) -> dict | None:
    """Build one condensed entry; returns index entry or None."""
    # Prefer local mirror when present (e.g. mimo already cloned); media still
    # points at HF so the site never needs local png/gif copies.
    local_root = ROOT / "assets" / "runs" / "public" / run["hf_id"] / f"day{day}" / folder
    meta = output = events = None
    traj_ts = None
    screenshot_count = 0
    has_gif = False

    if local_root.is_dir():
        meta_p = local_root / "meta.json"
        out_p = local_root / "output.json"
        if not meta_p.exists():
            return None
        meta = json.loads(meta_p.read_text())
        output = json.loads(out_p.read_text()) if out_p.exists() else {}
        traj_root = local_root / "trajectories"
        if traj_root.is_dir():
            dirs = sorted(
                d.name for d in traj_root.iterdir() if d.is_dir() and re.match(r"^\d{8}_\d{6}_", d.name)
            )
            if dirs:
                traj_ts = dirs[-1]
                td = traj_root / traj_ts
                tj = td / "trajectory.json"
                if tj.exists():
                    events = json.loads(tj.read_text())
                shots = td / "screenshots"
                if shots.is_dir():
                    screenshot_count = len(list(shots.glob("*.png")))
                    has_gif = (shots / "trajectory.gif").exists()
    else:
        all_files = file_index.get(f"{run['hf_id']}/day{day}/{folder}", [])
        if not all_files:
            return None
        meta_path = next((p for p in all_files if p.endswith("/meta.json")), None)
        out_path = next((p for p in all_files if p.endswith("/output.json")), None)
        if not meta_path:
            return None
        meta = load_json_bytes(hf_download(meta_path))
        output = load_json_bytes(hf_download(out_path)) if out_path else {}
        traj_ts = newest_traj_ts(all_files)
        if traj_ts:
            tj = next(
                (p for p in all_files if p.endswith(f"/trajectories/{traj_ts}/trajectory.json")),
                None,
            )
            if tj:
                events = load_json_bytes(hf_download(tj))
            shot_files = [
                p
                for p in all_files
                if f"/trajectories/{traj_ts}/screenshots/" in p and p.endswith(".png")
            ]
            screenshot_count = len(shot_files)
            has_gif = any(
                p.endswith(f"/trajectories/{traj_ts}/screenshots/trajectory.gif") for p in all_files
            )

    if not meta:
        return None

    task_id = meta.get("task_id") or folder_to_task_id(folder)
    success = bool(output.get("success")) if output else None
    reason = (output or {}).get("reason") or ""
    steps_count = (output or {}).get("steps") or 0
    started = meta.get("started_at_utc") or ""
    ended = meta.get("ended_at_utc") or ""

    entry = {
        "task_id": task_id,
        "set": "public",
        "day": day,
        "dir": folder,
        "model": meta.get("model") or "",
        "success": success,
        "reason": reason,
        "steps": steps_count,
        "started_at_utc": started,
        "ended_at_utc": ended,
        "has_trajectory": False,
        "gif": None,
        "data": None,
        "hf_run_id": run["hf_id"],
    }

    if events and isinstance(events, list) and traj_ts:
        steps = condense_trajectory(events)
        for i, step in enumerate(steps):
            if i < screenshot_count:
                step["screenshot"] = f"{i:04d}.png"
        data_rel = f"public/{run['key']}/day{day}/{task_id}.json"
        data_abs = OUT_DATA / data_rel
        data_abs.parent.mkdir(parents=True, exist_ok=True)
        shot_base = (
            f"{HF_RUNS_BASE}/runs/{run['hf_id']}/day{day}/{folder}/trajectories/{traj_ts}/screenshots"
        )
        payload = no_em_dash(
            {
                "task_id": task_id,
                "set": "public",
                "day": day,
                "dir": folder,
                "model": entry["model"],
                "success": success,
                "reason": reason,
                "steps_count": len(steps),
                "tool_call_count": sum(len(s.get("tools") or []) for s in steps),
                "screenshot_count": screenshot_count,
                "screenshot_base": shot_base,
                "started_at_utc": started,
                "ended_at_utc": ended,
                "hf_run_id": run["hf_id"],
                "traj_ts": traj_ts,
                "steps": steps,
            }
        )
        data_abs.write_text(json.dumps(payload, indent=2) + "\n")
        entry["has_trajectory"] = True
        # Keep data local-relative for the site; media is remote on HF.
        entry["data"] = f"assets/data/trajectories/{data_rel}"
        entry["step_count"] = len(steps)
        entry["screenshot_count"] = screenshot_count
        if has_gif:
            entry["gif"] = f"{shot_base}/trajectory.gif"

    return entry


def build_file_index(hf_id: str) -> dict[str, list[str]]:
    """Map '{hf_id}/dayN/folder' -> list of file paths under that task."""
    print(f"  listing HF tree for {hf_id}...", flush=True)
    tree = hf_get_json_recursive(f"runs/{hf_id}")
    out: dict[str, list[str]] = {}
    for e in tree:
        if e.get("type") != "file":
            continue
        p = e["path"]
        # runs/<id>/dayN/<folder>/...
        parts = p.split("/")
        if len(parts) < 5:
            continue
        key = f"{parts[1]}/{parts[2]}/{parts[3]}"  # id/dayN/folder
        out.setdefault(key, []).append(p)
    print(f"  {hf_id}: {len(out)} task folders", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="*", help="Optional subset of run keys to rebuild")
    args = ap.parse_args()

    runs = PUBLIC_RUNS
    if args.runs:
        want = set(args.runs)
        runs = [r for r in PUBLIC_RUNS if r["key"] in want]
        if not runs:
            print("no matching --runs")
            return 1

    existing = json.loads(INDEX_PATH.read_text()) if INDEX_PATH.exists() else {}
    public_by_task: dict[str, list[dict]] = {}

    for run in runs:
        print(f"== {run['key']} ({run['hf_id']}) ==", flush=True)
        local_root = ROOT / "assets" / "runs" / "public" / run["hf_id"]
        file_index: dict[str, list[str]] = {}
        if not local_root.is_dir():
            file_index = build_file_index(run["hf_id"])
        else:
            print(f"  using local mirror {local_root}", flush=True)

        run_index: dict[str, dict] = {}
        for day in (1, 2, 3):
            day_dir = local_root / f"day{day}"
            folders: list[str] = []
            if day_dir.is_dir():
                folders = sorted(d.name for d in day_dir.iterdir() if d.is_dir())
            else:
                folders = sorted(
                    {
                        k.split("/")[2]
                        for k in file_index
                        if k.startswith(f"{run['hf_id']}/day{day}/")
                    }
                )
            print(f"  day{day}: {len(folders)} tasks", flush=True)

            def work(folder: str, day: int = day):
                return folder, process_task(run, day, folder, file_index)

            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = [ex.submit(work, f) for f in folders]
                for fut in as_completed(futs):
                    folder, entry = fut.result()
                    if entry:
                        run_index[entry["task_id"]] = entry
                        alias = TASK_ID_ALIASES.get(entry["task_id"])
                        if alias:
                            run_index[alias] = {**entry, "task_id": alias, "is_alias": True}

        for task_id, entry in run_index.items():
            public_by_task.setdefault(task_id, []).append(
                {"run_key": run["key"], "run_label": run["label"], "entry": entry}
            )
        print(f"  indexed {len(run_index)} task ids", flush=True)

    # If only a subset was rebuilt, keep other runs from the existing index.
    if args.runs and existing.get("public"):
        rebuilt_keys = {r["key"] for r in runs}
        for task_id, entry in existing["public"].items():
            for r in entry.get("runs") or []:
                if r.get("run_key") in rebuilt_keys:
                    continue
                public_by_task.setdefault(task_id, []).append(
                    {
                        "run_key": r["run_key"],
                        "run_label": r.get("run_label") or r["run_key"],
                        "entry": {k: v for k, v in r.items() if k not in ("run_key", "run_label", "is_primary")},
                    }
                )

    # Order runs by PUBLIC_RUNS priority (all known keys).
    priority = {r["key"]: i for i, r in enumerate(PUBLIC_RUNS)}
    public_out: dict[str, dict] = {}
    for task_id, items in public_by_task.items():
        # Dedupe by run_key (prefer newly built)
        by_key: dict[str, dict] = {}
        for it in items:
            by_key[it["run_key"]] = it
        sorted_items = sorted(by_key.values(), key=lambda it: priority.get(it["run_key"], -1), reverse=True)
        primary = sorted_items[0]
        public_out[task_id] = {
            **primary["entry"],
            "run_key": primary["run_key"],
            "run_label": primary["run_label"],
            "runs": [
                {
                    "run_key": it["run_key"],
                    "run_label": it["run_label"],
                    "is_primary": i == 0,
                    **it["entry"],
                }
                for i, it in enumerate(sorted_items)
            ],
        }

    index = {
        "generated": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "note": (
            "Public trajectories: condensed step JSON is local; gif + screenshots load "
            f"from HF `{HF_RUNS_REPO}` raw runs (no local media copy). "
            "530 corpus section preserved from prior export."
        ),
        "public_run_order": [{"key": r["key"], "label": r["label"]} for r in PUBLIC_RUNS],
        "days": existing.get("days") or {},
        "tasks": existing.get("tasks") or {},
        "public": public_out,
    }
    # day summaries for public
    day_pub = {1: 0, 2: 0, 3: 0}
    for e in public_out.values():
        if e.get("has_trajectory") and e.get("day") in day_pub:
            day_pub[e["day"]] += 1
    index.setdefault("days", {})["public"] = {
        str(d): {"total": n, "with_trajectory": n, "without_gif": 0} for d, n in day_pub.items()
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(no_em_dash(index), indent=2) + "\n")
    print(f"wrote {INDEX_PATH} public_tasks={len(public_out)} runs={len(runs)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
