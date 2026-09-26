#!/usr/bin/env python3
"""Independent re-derivation of each public report's headline from its day verdicts.

`verify_leaderboard.py` checks that the *surfaces agree* (board <-> report <->
metrics JSON). This script checks something the agreement checks structurally
cannot: that each report's headline is what its own **day-verdict tables** say.

The day tables (`| Task | Verdict | Notes |`, one per day) are the manual ground
truth: every one of the 60 tasks carries a verdict, decided by a human looking at
the trajectory. The headline is a *summary* of them. So the headline can be
audited by re-summing the table and comparing:

    total passes  = ✅ + 🔮           must equal the headline's "true success"
    GUI-only      = passes not in the ASK USER set (7 tasks)
                                     must equal the headline's GUI-only numerator

This is the check that caught row 1 `2026-08-28`'s GUI-only drift. The reports had
been publishing **non-control** (every genuine ✅ over the non-control tasks) while
the column claims **non-interaction** (the run set with no ASK USER task), and row
1's value was additionally a re-run stale (33 = the pre-meet count). Re-summed from
the tables it is 32/53 = 60.4%. The whole public set was moved onto the declared
non-interaction basis in the same pass; see `redo.md` §7e(4).

Verdict vocabulary, as printed in the reports:

    ✅ PASS              a genuine pass
    ❌ FAIL              a genuine failure
    🔮 PASS (HC)         a hallucination control that honestly reported absence
                         (counted as a pass in the manual convention)
    🚨 HALLUCINATION     a control that fabricated data (never a pass)

The ASK USER tables further down a report also carry a `Verdict` column, but its
verdict cell is a bare word (`FAIL`) with no emoji -- an emoji-only scan silently
falls through to the ✅ in the neighbouring "Agent behavior" column and invents a
PASS. That trap is handled here (bare-word fallback) and is why this script
reports conflicts: any task with two different verdicts in one report is a bug in
the report, not something to average.

Usage
-----
    uv run python scripts/tools/audit_day_verdicts.py           # table + findings
    uv run python scripts/tools/audit_day_verdicts.py -v        # per-report detail
    uv run python scripts/tools/audit_day_verdicts.py --json    # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO / "reports" / "public"
SIDECARS = REPO / "benchmarks" / "androidlife-530"
INTERACTION_SIDECAR = SIDECARS / "ask_user_facts_public.json"
CONTROLS_SIDECAR = SIDECARS / "hallucination_controls.json"

TASK_RE = re.compile(r"^(easy|medium|hard)__[a-z0-9_-]+__[0-9]+$")
ROW_RE = re.compile(r"^\|(.+)\|\s*$")

PASS, FAIL, HC, HALL = "\u2705", "\u274c", "\U0001F52E", "\U0001F6A8"
BARE = {"PASS": "PASS", "FAIL": "FAIL", "HC": "HC", "HALL": "HALL",
        "HALLUCINATION": "HALL", "HONEST-FAIL": "HC", "PASS (HC)": "HC"}

# headline extractors
TRUE_SUCCESS_RE = re.compile(r"(\d+)\s+true\s+success", re.IGNORECASE)
FRAC_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def split_row(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def clean(cell: str) -> str:
    return cell.replace("**", "").replace("`", "").strip()


def verdict_of(cell: str) -> str | None:
    """Verdict for one table cell: emoji first, then the bare word.

    Reports use more than the four canonical emoji. Alongside PASS/FAIL there are
    `⚠️ PASS (caveat)` (still a pass), `🟡 FAIL (honest)`, `🔧 FAIL (harness)` (both
    plain FAILs) and `🚫 BLOCKED` (a storefront/environment outage -- neither a
    model success nor a model failure, so it is its own category and never lands in
    a success numerator). A bare-word scan that only understands PASS/FAIL silently
    drops those rows, which makes a report look like it tabulates fewer tasks than
    it really does.
    """
    if HC in cell:
        return "HC"
    if HALL in cell:
        return "HALL"
    if PASS in cell:
        return "PASS"
    if FAIL in cell:
        return "FAIL"
    token = re.sub(r"[^\w\s()-]", "", cell).strip().upper()
    if token in BARE:
        return BARE[token]
    if token.startswith("PASS (HC)"):
        return "HC"
    if token.startswith("HC") or token.startswith("HALL"):
        return "HC" if token.startswith("HC") else "HALL"
    if token.startswith("BLOCKED"):
        return "BLOCKED"
    if token.startswith("PASS"):
        return "PASS"
    if token.startswith("FAIL"):
        return "FAIL"
    return None


@dataclass
class Report:
    path: Path
    run_root: str = ""
    verdicts: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    headline_total: int | None = None
    headline_gui: tuple[int, int] | None = None

    @property
    def counted(self) -> dict[str, str]:
        """First verdict per task (reports repeat a task across tables)."""
        return {t: vs[0] for t, vs in self.verdicts.items()}

    @property
    def conflicts(self) -> dict[str, list[str]]:
        return {t: vs for t, vs in self.verdicts.items() if len(set(vs)) > 1}


def parse(path: Path) -> Report:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"run root:\*\*\s*`?(assets/runs/public/[^/`]+)/?", text, re.IGNORECASE)
    rep = Report(path=path, run_root=m.group(1) if m else "")

    header: list[str] = []
    for line in text.splitlines():
        if not ROW_RE.match(line):
            header = []
            continue
        cells = [clean(c) for c in split_row(line)]
        if len(cells) < 2 or set("".join(cells)) <= set("-: "):
            continue
        label = cells[0]
        if label.lower() == "task" and any("verdict" in c.lower() for c in cells):
            header = cells
            continue
        if label.lower() in {"metric", "bucket"}:
            header = cells
            continue
        if TASK_RE.match(label):
            if not any("verdict" in c.lower() for c in header):
                continue
            idx = next(i for i, c in enumerate(header) if "verdict" in c.lower())
            v = verdict_of(cells[idx]) if idx < len(cells) else None
            if v is None:
                for c in cells[1:]:
                    v = verdict_of(c)
                    if v:
                        break
            if v:
                rep.verdicts[label].append(v)
            continue
        # headline rows
        low = label.lower()
        if "gui-only" in low:
            fm = FRAC_RE.search(" ".join(cells[1:]))
            if fm:
                rep.headline_gui = (int(fm.group(1)), int(fm.group(2)))
            continue
        if low.startswith("success rate"):
            if "interaction" in low or "ask user" in low or "comparable" in low:
                continue
            joined = " ".join(cells[1:])
            tm = TRUE_SUCCESS_RE.search(joined)
            if tm is None:
                tm = re.search(r"(\d+)\s*/\s*\d+\s*—", joined)
            if tm:
                val = int(tm.group(1))
                rep.headline_total = val if rep.headline_total is None else max(rep.headline_total, val)
    return rep


def audit(path: Path, interaction: set[str], controls: set[str], run_count: int | None = None) -> dict:
    rep = parse(path)
    counted = rep.counted
    c = Counter(counted.values())
    on_report = set(counted)
    # A control reports a *success* for its task (the data does not exist), so a
    # control that self-reports success is a hallucination and one that honestly
    # reports absence is a "pass" in the headline convention but never a genuine
    # task completion. Net them out before measuring any genuine pass rate.
    ctrl_passes = {t for t, v in counted.items() if v == "PASS" and t in controls}
    genuine = {t for t, v in counted.items() if v == "PASS" and t not in controls}
    total_passes = c["PASS"] + c["HC"]
    nonint = {t for t in genuine if t not in interaction}
    inter = {t for t in genuine if t in interaction}
    # Denominator = every task the run *finalised*, minus its interaction tasks.
    # Tasks the sweep never started carry no verdict row but are still scored (the
    # reports count them as FAIL), so the denominator has to come from run_count,
    # not from the number of rows parsed -- otherwise a partial run looks like it
    # has a smaller denominator than it publishes.
    base = run_count if run_count else len(on_report)
    denom = base - len(on_report & interaction)

    findings = []
    if counted:
        if rep.headline_total is not None and total_passes != rep.headline_total:
            findings.append(
                f"total passes {total_passes} (tables) != {rep.headline_total} (headline true-success)"
            )
        if rep.headline_gui is not None:
            gn, gd = rep.headline_gui
            if gn != len(nonint):
                findings.append(
                    f"GUI-only numerator {gn} (headline) != {len(nonint)} (recounted "
                    f"non-interaction passes; {len(inter)} interaction task(s) passed)"
                )
            if gd != denom and denom:
                findings.append(f"GUI-only denominator {gd} (headline) != {denom} (recounted)")
        for t, vs in rep.conflicts.items():
            findings.append(f"conflicting verdicts for {t}: {vs}")

    return {
        "report": path.name,
        "run_root": rep.run_root,
        "tasks": len(on_report),
        "pass": c["PASS"],
        "hc": c["HC"],
        "hall": c["HALL"],
        "fail": c["FAIL"],
        "blocked": c["BLOCKED"],
        "total_passes": total_passes,
        "headline_total": rep.headline_total,
        "nonint": len(nonint),
        "inter": len(inter),
        "ctrl_passes": len(ctrl_passes),
        "denom": denom,
        "headline_gui": rep.headline_gui,
        "findings": findings,
    }


def run_count_for(run_root: str) -> int | None:
    """Finalised task count for a run, from its sibling metrics JSON."""
    ts = run_root.rstrip("/").split("/")[-1]
    path = REPO / "reports" / "metrics" / "public" / f"public-{ts}-report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("run_count")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-v", "--verbose", action="store_true", help="print a line per report")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    interaction = set(json.loads(INTERACTION_SIDECAR.read_text()))
    controls = set(json.loads(CONTROLS_SIDECAR.read_text()))
    rows = []
    for p in sorted(REPORTS_DIR.glob("public-*.md")):
        if p.name.endswith("-report.md"):
            continue
        rc = run_count_for(parse(p).run_root)
        rows.append(audit(p, interaction, controls, rc))

    if args.json:
        print(json.dumps(rows, indent=1, default=str))
        return 1 if any(r["findings"] for r in rows) else 0

    print(f"{'report':34} {'n':>3} {'PASS':>4} {'HC':>3} {'HAL':>3} {'FAIL':>4} "
          f"{'total':>5} {'hdr':>4} {'GUI rec':>9} {'GUI hdr':>9}  status")
    bad = 0
    for r in rows:
        if not r["tasks"]:
            print(f"{r['report']:34} {'-':>3}  (no day-verdict table)")
            continue
        rec = f"{r['nonint']}/{r['denom']}"
        hdr = f"{r['headline_gui'][0]}/{r['headline_gui'][1]}" if r["headline_gui"] else "-"
        status = "ok" if not r["findings"] else f"{len(r['findings'])} FINDING(S)"
        if r["findings"]:
            bad += 1
        print(f"{r['report']:34} {r['tasks']:>3} {r['pass']:>4} {r['hc']:>3} {r['hall']:>3} "
              f"{r['fail']:>4} {r['total_passes']:>5} {str(r['headline_total']):>4} "
              f"{rec:>9} {hdr:>9}  {status}")
    if args.verbose:
        for r in rows:
            for f in r["findings"]:
                print(f"  ! {r['report']}: {f}")
    print()
    print(f"audited {len(rows)} report(s) -> {bad} with findings")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
