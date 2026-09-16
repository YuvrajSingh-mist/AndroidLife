#!/usr/bin/env python3
"""Backfill ui_states/ for the 530 corpus on Hugging Face.

The viewer draws the implicit tap that `type` / `type_secret` performs on a field
before typing, and resolves its coordinate from the run's per-step accessibility
tree (ui_states/NNNN.json). The public dataset ships that directory, but the 530
corpus (YuvrajSingh9886/androidlife-trajectories) only ever got screenshots/ and
trajectory.gif, so 530 task pages cannot draw those markers.

Mapping a local run onto a Hub task dir is the delicate part: a task can have
several local runs, and frame numbers cannot tell them apart because every run
numbers from 0000. Choosing by file-name overlap is not enough either - two runs
of the same task overlap almost completely. So a couple of real frames are
compared pixel-for-pixel against the frames already on the Hub, and only a run
whose frames are the same screens is used. A run that cannot be confirmed is
skipped, because another run's trees would put markers in the wrong place.

Usage (from the repo root):
    python3 scripts/hf/upload_530_ui_states.py            # dry run: plan + checks
    python3 scripts/hf/upload_530_ui_states.py --push     # upload
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests
from huggingface_hub import HfApi
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS = REPO_ROOT / "assets" / "runs" / "full-bench"
REPO_ID = "YuvrajSingh9886/androidlife-trajectories"
# Verification downloads two frames per candidate run, so it dominates the
# runtime. Caching which run won for each task makes the job resumable: an
# interrupted upload can be re-run without paying for the frames again.
PLAN_CACHE = REPO_ROOT / ".cache" / "530_ui_states_runs.json"

# Two probes must both come in under this, so the choice never rests on a single
# coincidence. Same screen scores in the low tens; a different run scores in the
# hundreds.
SAME_RUN_MAE = 60


def norm(name: str) -> str:
    """easy-google-search-001 and easy__google-search__001 are the same task."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def frame_no(filename: str) -> str | None:
    """Frame number from a screenshot name.

    macOS/iCloud re-uploads land as '0000 2.jpg' beside '0000.jpg', and a local
    run keeps its trajectory.gif inside screenshots/. Both are noise here.
    """
    base = re.sub(r"\s+\d+$", "", Path(filename).stem)
    return base if re.fullmatch(r"\d{3,5}", base) else None


def local_runs() -> dict[tuple[int, str], list[Path]]:
    """(day, normalized_task) -> run dirs that have a ui_states/ directory."""
    out: dict[tuple[int, str], list[Path]] = defaultdict(list)
    for ui in RUNS.glob("*/day*/**/ui_states"):
        run = ui.parent
        # .../<run-id>/day<N>/<task-dir>/trajectories/<ts>/
        parts = run.relative_to(RUNS).parts
        if len(parts) < 5 or parts[1] not in {"day1", "day2", "day3", "day4", "day5"}:
            continue
        out[(int(parts[1].removeprefix("day")), norm(parts[2]))].append(run)
    return out


def hf_tasks(api: HfApi) -> dict[tuple[int, str], dict]:
    """(day, normalized_task) -> {day, task, shots: {frame: filename}} from the Hub."""
    out: dict[tuple[int, str], dict] = {}
    paths = [
        e.path
        for e in api.list_repo_tree(REPO_ID, path_in_repo="trajectories", repo_type="dataset", recursive=True)
        if getattr(e, "path", None)
    ]
    for p in paths:
        m = re.match(r"trajectories/day(\d)/([^/]+)/screenshots/([^/]+)$", p)
        if not m:
            continue
        day, task, name = int(m.group(1)), m.group(2), m.group(3)
        frame = frame_no(name)
        if not frame:
            continue
        entry = out.setdefault((day, norm(task)), {"day": day, "task": task, "shots": {}})
        entry["shots"].setdefault(frame, name)  # prefer the un-suffixed copy
    return out


def frame_mae(hub_dir: str, hub_name: str, local_png: Path) -> tuple[float | None, str | None]:
    """Mean absolute pixel difference between a Hub frame and a local frame."""
    try:
        raw = requests.get(
            f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/{hub_dir}/{hub_name}", timeout=120
        ).content
        img_hub = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller, not swallowed
        return None, f"{type(exc).__name__}: {str(exc)[:60]}"
    img_loc = Image.open(local_png).convert("RGB")
    if img_hub.size != img_loc.size:
        img_hub = img_hub.resize(img_loc.size)
    a, b = img_hub.load(), img_loc.load()
    w, h = img_loc.size
    total = n = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            pa, pb = a[x, y], b[x, y]
            total += abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2])
            n += 1
    return total / n, None


def match_run(day: int, hub: dict, runs: list[Path]) -> tuple[tuple | None, str | None]:
    """Pick the local run that is the one the Hub copy came from, or explain why not."""
    # The Hub directory name is the canonical task id; the dict key is only a
    # normalized comparison form, so the URL must use the former.
    hub_dir = f"trajectories/day{day}/{hub['task']}/screenshots"
    scored = []
    errors: list[str] = []
    for run in runs:
        local = {p.stem: p for p in (run / "screenshots").glob("*.png")}
        shared = sorted(set(local) & set(hub["shots"]))
        if not shared:
            errors.append(f"{run.name}: no shared frame numbers")
            continue
        probes = [shared[len(shared) // 2], shared[len(shared) * 3 // 4]]
        maes = []
        for f in probes:
            mae, err = frame_mae(hub_dir, hub["shots"][f], local[f])
            if err:
                errors.append(f"{run.name} frame {f}: {err}")
                mae = None
            maes.append(mae)
        if any(m is None for m in maes):
            continue
        scored.append((max(maes), run, maes))
    if not scored:
        return None, "no frame could be compared" + (f" ({errors[0]})" if errors else "")
    scored.sort(key=lambda s: s[0])
    best_mae, run, maes = scored[0]
    if best_mae >= SAME_RUN_MAE:
        detail = "; ".join(f"{r.name} MAE {m:.0f}" for m, r, _ in scored[:3])
        return None, f"no local run matches the Hub copy ({detail})"
    return (run, maes), None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="actually upload (default: dry run)")
    ap.add_argument("--only-day", type=int, help="limit to a single day")
    ap.add_argument("--reuse-plan", action="store_true",
                    help="reuse the cached run choice instead of re-verifying frames")
    args = ap.parse_args()

    api = HfApi()
    local = local_runs()
    remote = hf_tasks(api)
    cache: dict[str, str] = {}
    if PLAN_CACHE.exists():
        try:
            cache = json.loads(PLAN_CACHE.read_text())
        except Exception:  # noqa: BLE001 - a corrupt cache just means re-verifying
            cache = {}
    print(f"local 530 runs with ui_states : {sum(len(v) for v in local.values())} across {len(local)} tasks")
    print(f"530 task dirs on the Hub       : {len(remote)}")
    if args.reuse_plan:
        print(f"reusing {len(cache)} verified run(s) from {PLAN_CACHE.relative_to(REPO_ROOT)}")
    print("verifying each run against the Hub copy (two frame pairs per candidate)...\n")

    plan: list[tuple[int, str, Path, int, list]] = []
    problems: list[str] = []
    for (day, task), runs in sorted(local.items()):
        if args.only_day and day != args.only_day:
            continue
        hub = remote.get((day, task))
        if not hub:
            problems.append(f"day{day} {task}: no matching task dir on the Hub")
            continue
        key = f"day{day}/{hub['task']}"
        cached = cache.get(key) if args.reuse_plan else None
        run = next((r for r in runs if r.name == cached), None)
        if run is not None:
            maes = ["cached"] * 2
        else:
            matched, why = match_run(day, hub, runs)
            if not matched:
                problems.append(f"day{day} {task}: {why}")
                continue
            run, maes = matched
            cache[key] = run.name
        trees = sorted((run / "ui_states").glob("*.json"))
        plan.append((day, hub["task"], run, len(trees), maes))
        shown = "/".join(str(m) if isinstance(m, str) else f"{m:.0f}" for m in maes)
        print(f"  ok  day{day} {hub['task']:46s} {len(trees):3d} trees  MAE {shown:9s}  {run.name}")

    PLAN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PLAN_CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=1) + "\n")

    total_files = sum(p[3] for p in plan)
    print(f"\nverified runs                 : {len(plan)}")
    print(f"ui_states files to upload      : {total_files}")
    if problems:
        print(f"\nskipped ({len(problems)}):")
        for p in problems:
            print("  -", p)

    by_day: dict[int, list] = defaultdict(list)
    for entry in plan:
        by_day[entry[0]].append(entry)
    print("\nper day:")
    for day in sorted(by_day):
        print(f"  day{day}: {len(by_day[day])} tasks, {sum(e[3] for e in by_day[day])} files")

    if not args.push:
        print("\ndry run - nothing uploaded. Re-run with --push")
        return 0

    # Uploads are retried with backoff and failures are collected rather than
    # raised: one flaky request should not abandon the other hundred tasks, and a
    # re-run is cheap with --reuse-plan.
    failed: list[str] = []
    for day in sorted(by_day):
        for _d, task, run, count, _maes in by_day[day]:
            for attempt in range(1, 4):
                try:
                    api.upload_folder(
                        repo_id=REPO_ID,
                        repo_type="dataset",
                        folder_path=str(run / "ui_states"),
                        path_in_repo=f"trajectories/day{day}/{task}/ui_states",
                        commit_message=f"Add per-step ui_states for day{day} {task} (530 corpus)",
                    )
                except Exception as exc:  # noqa: BLE001 - retried, then reported
                    if attempt == 3:
                        failed.append(f"day{day} {task}: {type(exc).__name__}: {str(exc)[:90]}")
                        print(f"  FAILED day{day} {task} after {attempt} attempts: {str(exc)[:80]}")
                    else:
                        wait = 5 * attempt
                        print(f"  retry day{day} {task} in {wait}s ({type(exc).__name__})")
                        time.sleep(wait)
                    continue
                print(f"  uploaded day{day} {task}: {count} files from {run.name}")
                break

    print(f"\nuploaded: {len(plan) - len(failed)}/{len(plan)} tasks")
    if failed:
        print("failed:")
        for f in failed:
            print("  -", f)
        print("re-run with --reuse-plan to retry only the missing ones")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
