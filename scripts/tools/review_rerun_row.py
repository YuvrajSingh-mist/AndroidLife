"""Manual-review gate for a re-run row: read the row from its OWN artifacts and record a verdict.

Why this exists
---------------
A redo row's `output.json` is not enough to publish. Three failures this project has
already paid for, all invisible to `success: true`:

  * **vacuous PASS** -- Maps' leaked recent list let the agent reach the right end state
    without typing the query (redo.md section 1; 7 of 13 runs on 2026-09-16).
  * **wrong-answer PASS** -- 2026-09-23 row 9 (Qwen3.5-4B) typed the query and wrote a
    note, so the artifact-level check looked clean, but the note names **Two-wheeler** as
    the fastest mode when the task asks for the fastest of driving / transit / walking.
  * **false pass on delivery** -- hard__drive-notes-telegram__010 rows 3/4 self-report
    success having sent nothing (the delivery gate catches that one).

So the pipeline is: run ONE row -> run this -> only then start the next. `review.json`
is written next to the row's own artifacts, and `rerun_task_rows.sh` refuses to continue
past a row until it exists (REVIEW_GATE=1).

Usage
-----
    review_rerun_row.py --run-root assets/runs/public/<ts>
    review_rerun_row.py --run-root ... --write     # persist review.json
    review_rerun_row.py --task-id medium__google-maps__002 --newest 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PUBLIC = REPO / "assets" / "runs" / "public"

INVOKE_RE = re.compile(r'<invoke name="([^"]+)">(.*?)</invoke>', re.DOTALL)
PARAM_RE = re.compile(r'<parameter name="([^"]+)">(.*?)</parameter>', re.DOTALL)

# The task's own wording: compare these three modes and save the fastest.
MAPS_MODES = ("driving", "transit", "walking")
# Modes the Maps UI offers that are NOT part of the question. Picking one of these as
# "fastest" answers a different question, however well-formed the note looks.
MAPS_OFF_MODE = ("two-wheeler", "two wheeler", "bike", "motorcycle", "cycling", "cab")




def tool_calls(traj: list) -> list[tuple[str, dict[str, str]]]:
    out = []
    for ev in traj:
        if ev.get("type") != "FastAgentResponseEvent":
            continue
        for m in INVOKE_RE.finditer(ev.get("code") or ""):
            out.append((m.group(1), {k: v.strip() for k, v in PARAM_RE.findall(m.group(2))}))
    return out


def review_maps(task_dir: Path, max_steps: int = 60) -> dict:
    """medium__google-maps__002: compare driving/transit/walking and note the fastest."""
    r: dict = {"reasons": [], "evidence": {}}
    out_path = task_dir / "output.json"
    if not out_path.is_file():
        return {"verdict": "VOID", "reasons": ["no output.json (aborted before any result)"],
                "evidence": {}}
    out = json.loads(out_path.read_text())
    steps, success = out.get("steps"), out.get("success")
    r["evidence"]["steps"] = steps
    r["evidence"]["output_success"] = success

    trajs = sorted(task_dir.glob("trajectories/*/trajectory.json"))
    if not trajs:
        return {"verdict": "VOID", "reasons": ["no trajectory.json - nothing to review"],
                "evidence": r["evidence"]}
    traj = json.loads(trajs[0].read_text())
    calls = tool_calls(traj)

    typed = [a.get("text", "") for n, a in calls
             if n in ("type", "input_text")
             and "bhubaneswar" in a.get("text", "").lower()
             # The note write is ALSO a `type` and also names the airport, so it must be
             # excluded or a row that only wrote a note looks like it searched. The note is
             # identified by its own content ("Fastest ..."), which the query never has.
             and "fastest" not in a.get("text", "").lower()]
    r["evidence"]["typed_query"] = bool(typed)

    note = next((a.get("text", "") for n, a in calls
                 if n in ("type", "input_text") and "Fastest" in a.get("text", "")), None)
    r["evidence"]["note"] = note

    # 1) The discriminator redo.md section 1 defines: no typed query = free pass.
    if not typed:
        r["reasons"].append("never typed the airport query - the result is a vacuously "
                            "reachable end state, not an answer (redo.md section 1)")
    # 2) The deliverable.
    if not note:
        r["reasons"].append("no comparison note was written")
    else:
        low = note.lower()
        off = [m for m in MAPS_OFF_MODE if m in low]
        named = [m for m in MAPS_MODES if m in low]
        r["evidence"]["modes_in_note"] = named
        r["evidence"]["off_mode_in_note"] = off
        # The task says "save the ETA and distance for THAT FASTEST OPTION", so the note
        # legitimately carries one mode only -- the comparison itself happens on the Maps
        # screen. Requiring all three in the note false-FAILed row 3, whose note was
        # `Driving: 26 minutes, 13 km` and which is a correct answer.
        #
        # What must hold is (a) the note names one of the three modes the task asked about,
        # so the saved answer is about the question, and (b) it does not name one of the
        # UI's other modes as the winner -- that answers a different question (row 9,
        # 2026-09-23: "Fastest Option: Two-wheeler (33 min, 12 km)").
        if off:
            r["reasons"].append(
                f"note reports '{off[0]}' as the fastest option, but the task asks for the "
                f"fastest of {'/'.join(MAPS_MODES)} - this answers a different question")
        elif not named:
            r["reasons"].append("note names none of driving/transit/walking as the fastest option")
        # Evidence only (never a FAIL): did it actually compare all three on screen?
        r["evidence"]["compared_all_three"] = len(named) >= 3 and not off
    # 4) A step-cap exit is an honest FAIL, not a harness failure.
    if steps is not None and steps >= max_steps:
        r["reasons"].append(f"hit the {max_steps}-step cap without completing")
    if success is not True:
        r["reasons"].append(f"harness recorded success={success!r}")

    r["verdict"] = "PASS" if not r["reasons"] else "FAIL"
    return r


REVIEWERS = {"medium__google-maps__002": review_maps}


def review_root(root: Path, task_id: str | None, max_steps: int) -> dict:
    if task_id is None:
        launch = root / "LAUNCH.txt"
        task_id = ""
        if launch.is_file():
            m = re.search(r"^redo_task=(.+)$", launch.read_text(), re.MULTILINE)
            task_id = m.group(1).strip() if m else ""
    if task_id not in REVIEWERS:
        return {"task_id": task_id, "verdict": "VOID",
                "reasons": [f"no reviewer implemented for task {task_id!r}"], "evidence": {}}
    slug = task_id.replace("__", "-")
    day_dirs = sorted(root.glob(f"day*/{slug}"))
    if not day_dirs:
        return {"task_id": task_id, "verdict": "VOID",
                "reasons": ["no task directory in this run root"], "evidence": {}}
    res = REVIEWERS[task_id](day_dirs[0], max_steps)
    res["task_id"] = task_id
    res["run_root"] = root.name
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-root")
    ap.add_argument("--task-id")
    ap.add_argument("--newest", type=int, help="review the N newest roots for --task-id")
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--write", action="store_true", help="persist review.json in the row")
    a = ap.parse_args()

    roots: list[Path] = []
    if a.newest:
        if not a.task_id:
            ap.error("--newest needs --task-id")
        for d in sorted((p for p in PUBLIC.iterdir() if p.is_dir()), reverse=True):
            if ".aborted" in d.name:
                continue
            launch = d / "LAUNCH.txt"
            if launch.is_file() and f"redo_task={a.task_id}" in launch.read_text():
                roots.append(d)
            if len(roots) >= a.newest:
                break
    elif a.run_root:
        roots = [Path(a.run_root)]
    else:
        ap.error("pass --run-root or --newest")

    rc = 0
    for root in roots:
        res = review_root(root, a.task_id, a.max_steps)
        print(f"=== {res.get('run_root', root.name)}  [{res.get('task_id', '?')}] ===")
        ev = res.get("evidence", {})
        if "steps" in ev:
            print(f"   steps={ev['steps']}  output_success={ev['output_success']}  "
                  f"typed_query={ev.get('typed_query')}")
            if ev.get("modes_in_note") is not None:
                print(f"   modes in note: {ev.get('modes_in_note')}"
                      + (f"   OFF-MODE: {ev['off_mode_in_note']}" if ev.get("off_mode_in_note") else ""))
            if ev.get("note"):
                print(f"   note: {ev['note'][:120]!r}")
        print(f"   VERDICT: {res['verdict']}")
        for why in res.get("reasons", []):
            print(f"     - {why}")
        if a.write:
            if res["verdict"] == "VOID":
                print("   (not written: VOID means there is nothing to review)")
            else:
                slug = (res.get("task_id") or "").replace("__", "-")
                target = next(iter(root.glob(f"day*/{slug}")), None)
                if target is not None:
                    (target / "review.json").write_text(json.dumps(res, indent=2) + "\n")
                    print(f"   wrote {target / 'review.json'}")
        if res["verdict"] != "PASS":
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
