#!/usr/bin/env python3
"""Auto-organize public-run artifacts into their per-run (date-time) folders."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from DailyBench.jsonutils import read_json  # noqa: E402

RUNS = REPO / "assets" / "runs" / "public"
DB = REPO / "assets" / "db" / "public"
REPORTS = REPO / "reports"
PUB = REPORTS / "public"
MET = REPORTS / "metrics" / "public"
HALL = REPORTS / "metrics" / "hallucination"
TB = REPORTS / "turn-based" / "public"
SINGLE = TB / "ask-query-single"
MULTI = TB / "ask-query-multi"
BENCH = REPO / "benchmarks" / "dailyBench-600"
FACTS = BENCH / "ask_user_facts.json"
KB = BENCH / "multiturn_kb_public.json"
DATASET = BENCH / "DailyBench_public_v2.json"

# The mobile GUI agent's `ask_user` tool description — exactly what the RUN AGENT
# sees registered for its ask_user tool (both single-fact and multi-turn/KB modes
# register the same tool). Source of truth: src/DailyBench/custom_tools.py
# build_ask_user_tool() "description". Included in the turn-based audits so the
# reader can see the prompt the mobile agent was given for its ask_user tool.
ASK_USER_TOOL_DESCRIPTION = (
    "Ask the human user a clarifying question when the task needs a specific fact that is "
    "NOT available anywhere on the device (for example a particular contact's name, a date or "
    "time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely "
    "cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact "
    "you think is missing to complete the task. Never ask about things you can look up yourself. Ask "
    "one specific question at a time. You may ask multiple questions over multiple turns to "
    "disambiguate a vague request."
)

# Run-timestamp matcher. Accepts the conventional dashed form (2026-08-22-195244)
# AND the compact form (20260826-105200, produced by `date +%Y%m%d-%H%M%S`) so runs
# launched with either naming convention get filed by --sweep.
_TS_RE = re.compile(r"\d{4}(?:-\d{2}-\d{2}|\d{4})-\d{6}")


def _ts_from_run_root(root: Path) -> str:
    return root.name


def _load_json(p: Path) -> dict:
    return read_json(p) or {}


def _fact_maps():
    """task_id -> fact (SINGLE) and task_id -> kb label (MULTI)."""
    single = _load_json(FACTS)
    kb = _load_json(KB)
    multi = {}
    for tid, meta in kb.items():
        ct = meta.get("correct_target") or ""
        multi[tid] = f"multiturn_kb: {ct}" if ct else tid
    return single, multi


def _dataset_map():
    return {t["task_id"]: t for t in _load_json(DATASET).get("tasks", [])}


def _phoenix_ask_user_prompts(run_ts: str, goal: str) -> dict[str, str]:
    """Return {question: system_prompt} — the ACTUAL prompts the simulated user
    was given each turn, read straight from the run's Phoenix DB (ask_user spans).
    This is the ground truth of what the oracle knew (fact/KB + history), which the
    JSONL log does not record. Empty dict if the DB is unavailable.
    """
    db = DB / run_ts / "phoenix.db"
    if not db.exists() or not goal:
        return {}
    out: dict[str, str] = {}
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        # Single-fact template has 'relevant information for the task is'; the
        # multi-turn KB template has 'Here is everything about you that is relevant'.
        rows = cur.execute(
            "SELECT start_time, attributes FROM spans "
            "WHERE attributes LIKE '%relevant information for the task is%' "
            "   OR attributes LIKE '%Here is everything about you that is relevant%'"
        ).fetchall()
        con.close()
    except Exception:
        return {}
    for _start, attrs in rows:
        try:
            a = json.loads(attrs)
            llm = a.get("llm", {})
            msgs = llm.get("input_messages")
            if isinstance(msgs, str):
                msgs = json.loads(msgs)
            sysc = next((m.get("content", "") for m in (msgs or [])
                        if isinstance(m, dict) and m.get("role") == "system"), "")
            userc = next((m.get("content", "") for m in (msgs or [])
                         if isinstance(m, dict) and m.get("role") == "user"), "")
        except Exception:
            continue
        if not userc or not sysc:
            continue
        if goal[:50] and goal[:50] not in sysc:
            continue  # not this task's ask_user span
        out[userc] = sysc
    return out


def _audit_text(tid: str, kind: str, day: str, fact: str, rows: list, meta: dict, rendered: str | None = None, run_ts: str | None = None, oracle: dict | None = None) -> str:
    bucket = meta.get("bucket") or meta.get("difficulty") or ""
    apps = ", ".join(meta.get("apps") or [meta.get("app", "")])
    prompt = (rendered or meta.get("prompt_text") or meta.get("prompt_template") or "").strip()
    root = f"assets/runs/public/{run_ts}/{day}/" if run_ts else f"assets/runs/public/{day}/"
    L = [f"# {tid}  — {kind}", "",
         f"**Run day:** {day} · **Run root:** `{root}{tid.replace('__','-')}/`", "",
         f"**Difficulty:** {bucket} · **Apps:** {apps}", "",
         "**Task (what the user asked):**", "", f"> {prompt}", "",
         f"**Ground-truth fact:** {fact}", f"**ask_user turns:** {len(rows)}", "",
         "**The mobile GUI agent's `ask_user` tool (as the run agent sees it):**", "",
         "```text", ASK_USER_TOOL_DESCRIPTION, "```", ""]
    if not rows:
        L.append("> ⚠️ **No ask_user calls recorded** — the agent never asked the user "
                 "(guesses a target instead → FAIL under the MobileWorld gate).")
        L.append("")
    for i, r in enumerate(rows, 1):
        req = r.get("request", {}) or {}
        q = req.get("framework_prompt", "(no question captured)")
        a = r.get("response", "")
        ts = r.get("timestamp_utc", "")
        sysp = (oracle or {}).get(q) if oracle else None
        L += [f"## Turn {i}  ({ts})", ""]
        if sysp:
            L += ["**What the simulated user was told (actual system prompt from the run):**", "",
                  "```text", sysp, "```", ""]
        L += ["**Agent asked:**", "", f"> {q}", "", "**User answered:**", "", f"> {a}", ""]
    return "\n".join(L)


def generate_turn_audits(run_ts: str, root: Path) -> None:
    """Generate per-task ASK USER audits under SINGLE/<ts>/ and MULTI/<ts>/.

    Iterates the dataset's ask-user tasks (authoritative `__`-delimited IDs) and
    resolves the run folder via `tid.replace('__','-')` (e.g. hard__gmail-calendar__003
    -> hard-gmail-calendar-003). Falls back to the rendered `meta.json` goal so the
    audit shows exactly what the agent saw.
    """
    single, multi = _fact_maps()
    meta_by_id = _dataset_map()
    # Prune stale audits whose filename isn't a canonical dataset task_id
    # (older runs used the hyphenated dir form, e.g. hard__gmail-calendar-003).
    valid = set(meta_by_id.keys())
    for base in (SINGLE, MULTI):
        d = base / run_ts
        if d.is_dir():
            for f in d.glob("*.md"):
                if f.stem not in valid:
                    f.unlink()
    for tid, meta in meta_by_id.items():
        if tid not in single and tid not in multi:
            continue
        day = meta.get("day")
        if not day:
            continue
        taskdir = root / f"day{day}" / tid.replace("__", "-")
        if not taskdir.is_dir():
            continue
        rows = []
        metrics = taskdir / "ask_user_metrics.jsonl"
        if metrics.exists():
            for line in metrics.read_text(encoding="utf-8").splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        rendered = None
        mj = _load_json(taskdir / "meta.json")
        if mj.get("goal"):
            rendered = mj["goal"]
        oracle = _phoenix_ask_user_prompts(run_ts, rendered or meta.get("prompt_text") or "")
        if tid in single:
            (SINGLE / run_ts).mkdir(parents=True, exist_ok=True)
            (SINGLE / run_ts / f"{tid}.md").write_text(
                _audit_text(tid, "ASK USER SINGLE", f"day{day}", single[tid], rows, meta, rendered, run_ts, oracle), encoding="utf-8")
        elif tid in multi:
            (MULTI / run_ts).mkdir(parents=True, exist_ok=True)
            (MULTI / run_ts / f"{tid}.md").write_text(
                _audit_text(tid, "ASK USER MULTI", f"day{day}", multi[tid], rows, meta, rendered, run_ts, oracle), encoding="utf-8")


def _move_if(src: Path, dst: Path) -> bool:
    if src.exists() and src.is_file() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return True
    return False


def organize(run_ts: str, root: Path) -> None:
    """Create folders + file all artifacts for one run."""
    # 1. folders
    for d in (PUB, MET, HALL, SINGLE / run_ts, MULTI / run_ts, DB / run_ts):
        d.mkdir(parents=True, exist_ok=True)
    # 2. report -> reports/public/public-<ts>.md
    for cand in (REPORTS / f"{run_ts}.md", REPORTS / f"public-{run_ts}.md",
                 REPORTS / "public" / f"public-{run_ts}.md", REPORTS / f"public-{run_ts}.md"):
        _move_if(cand, PUB / f"public-{run_ts}.md")
    # 3. metrics -> reports/metrics/public/ (accept dashed + compact ts forms; keep filename)
    compact = run_ts.replace("-", "", 2)  # 2026-08-22-195244 -> 20260822-195244
    for ext in ("json", "md"):
        for cts in (run_ts, compact):
            for cand in (REPORTS / "metrics" / f"public-{cts}-report.{ext}",):
                if cand.exists() and cand.is_file():
                    shutil.move(str(cand), str(MET / cand.name))
    # 4. hallucination eval -> reports/metrics/hallucination/ (accept both forms; keep filename)
    for ext in ("json", "md"):
        for cts in (run_ts, compact):
            cand = HALL / f"public-{cts}.{ext}"
            if cand.exists() and cand.is_file():
                pass  # already in the right folder; nothing to move
    # 5. DB -> assets/db/public/<ts>/phoenix.db
    live = DB / "phoenix.db"
    if live.exists() and not (DB / run_ts / "phoenix.db").exists():
        shutil.move(str(live), str(DB / run_ts / "phoenix.db"))
        for suffix in ("-shm", "-wal"):
            s = DB / f"phoenix.db{suffix}"
            if s.exists():
                shutil.move(str(s), str(DB / run_ts / f"phoenix.db{suffix}"))
    # 6. regenerate turn-based audits (idempotent)
    generate_turn_audits(run_ts, root)


def _verdict_table(kind_dir: Path, label: str) -> str:
    rows = []
    for run_dir in sorted(kind_dir.glob("*")):
        if not run_dir.is_dir() or not _TS_RE.fullmatch(run_dir.name):
            continue
        for f in sorted(run_dir.glob("*.md")):
            txt = f.read_text(encoding="utf-8")
            fact = re.search(r"\*\*Ground-truth fact:\*\* (.+)", txt)
            turns = re.search(r"\*\*ask_user turns:\*\* (\d+)", txt)
            day = re.search(r"\*\*Run day:\*\* (\w+)", txt)
            n = int(turns.group(1)) if turns else 0
            asked = "✅ asked" if n > 0 else "❌ never asked"
            rows.append((run_dir.name, f.stem, day.group(1) if day else "-",
                         str(n), asked, (fact.group(1) if fact else "-")[:60]))
    if not rows:
        return f"_(no {label} audits yet)_\n"
    out = [f"| Run | Task | Day | # asks | Asked? | Fact |", "|---|---|---|---|---|---|"]
    for run, tid, day, n, asked, fact in rows:
        rel = f"{kind_dir.name}/{run}/{tid}.md"
        out.append(f"| {run} | [{tid}]({rel}) | {day} | {n} | {asked} | {fact} |")
    return "\n".join(out) + "\n"


def write_readme() -> None:
    TB.mkdir(parents=True, exist_ok=True)
    single_tbl = _verdict_table(SINGLE, "ASK USER SINGLE")
    multi_tbl = _verdict_table(MULTI, "ASK USER MULTI")
    runs = sorted(r.name for r in SINGLE.glob("*") if r.is_dir() and _TS_RE.fullmatch(r.name))
    readme = f"""# Turn-based ASK USER audits (public)

Full per-turn audits of every ASK USER interaction (question → answer), one
date-time folder per run — same convention as `assets/db/public/<run-ts>/`:

```
reports/turn-based/public/
├── README.md
├── ask-query-single/<run-ts>/<task>.md
└── ask-query-multi/<run-ts>/<task>.md
```

Runs present: {', '.join('`'+r+'`' for r in runs) if runs else '_(none)_'}

## ask-query-single/
{single_tbl}
## ask-query-multi/
{multi_tbl}
"""
    (TB / "README.md").write_text(readme, encoding="utf-8")


def sweep() -> None:
    """Organize every public run + file any loose artifacts."""
    # organize each run under assets/runs/public/
    for root in sorted(RUNS.glob("*")):
        if root.is_dir() and _TS_RE.fullmatch(root.name):
            organize(root.name, root)
    # loose reports at reports/ root that look like run reports
    for f in sorted(REPORTS.glob("*.md")):
        m = _TS_RE.search(f.name)
        if m and f.name.startswith(("public-", "")) and not f.name.startswith("day"):
            run_ts = m.group(0)
            _move_if(f, PUB / f"public-{run_ts}.md")
    # loose turn-based audit files not under a <ts>/ subfolder -> drop (regenerated)
    for kind in (SINGLE, MULTI):
        for f in sorted(kind.glob("*.md")):
            try:
                f.unlink()
            except OSError:
                pass
    write_readme()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--run-root", help="Public run root (e.g. assets/runs/public/2026-08-22-195244)")
    g.add_argument("--run-ts", help="Run timestamp (e.g. 2026-08-22-195244)")
    g.add_argument("--sweep", action="store_true", help="Organize every public run + file loose artifacts")
    args = ap.parse_args()

    if args.sweep:
        sweep()
        print("sweep done: organized all public runs + filed loose artifacts + rebuilt README")
        return 0
    if args.run_root:
        root = Path(args.run_root)
        run_ts = _ts_from_run_root(root)
    elif args.run_ts:
        run_ts = args.run_ts
        root = RUNS / run_ts
    else:
        ap.error("provide --run-root, --run-ts, or --sweep")
    if not root.is_dir():
        print(f"run root not found: {root}", file=sys.stderr)
        return 1
    organize(run_ts, root)
    write_readme()
    print(f"organized run {run_ts}: folders created, artifacts filed, audits + README regenerated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
