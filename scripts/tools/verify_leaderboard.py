#!/usr/bin/env python3
"""Deterministic leaderboard <-> run-report reconciliation.

The public leaderboard (`androidlife-website/assets/js/leaderboard.js`) quotes a
number for every run. Each of those numbers must be traceable to the run's own
report, which is the manually-audited source of truth. This script re-reads both
sides and fails loudly when they disagree, so a report revision can never again
silently drift away from what the site publishes.

Where the numbers come from
---------------------------
The reports print a metric table plus a telemetry table. Two columns can appear:

    | Metric | Value (manual audit) | Official (…) |

The leaderboard deliberately mixes the two, per field, so the mapping below is
explicit rather than inferred:

  manual column  (first value on the row) -> success, askUser, guiOnly, hc, buckets
  official/derived column (last value)    -> steps, queries, uiq, kbiq, elapsed
  telemetry table                          -> cost, askUserCost, cpuTemp,
                                              powerSkinTemp, batteryTemp,
                                              batteryDrain

`steps`/`queries`/`uiq`/`kbiq` are also cross-checked against the official
metrics JSON (`reports/metrics/public/public-<run>-report.json`) and the cost
group against the raw `llm_proxy_metrics.jsonl` / `ask_user_metrics.jsonl` when
the run root is present locally, because those are machine-generated and cannot
be mistyped by hand.

Interrupted rows
----------------
Rows 9-11 are interrupted runs. They carry two denominators: the relaxed
incomplete-counts-as-fail figure against the full 60 (what the site ranks on,
`success.score`) and the reached-task figure. For those rows:

  success.score  must equal `interrupted.passed / interrupted.total` (relaxed),
                 and the report's reached-denominator Success Rate must equal
                 `passed / finished`.
  hc / askUser / guiOnly compare against the report's manual value directly,
                 which the reports already express over the reached tasks.

Usage
-----
    uv run python scripts/tools/verify_leaderboard.py            # check, exit 1 on mismatch
    uv run python scripts/tools/verify_leaderboard.py -v         # print every parsed value
    uv run python scripts/tools/verify_leaderboard.py --row 10   # one row
    uv run python scripts/tools/verify_leaderboard.py --json     # machine-readable result
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEADERBOARD_JS = REPO / "androidlife-website" / "assets" / "js" / "leaderboard.js"
REPORTS_DIR = REPO / "reports" / "public"
METRICS_DIR = REPO / "reports" / "metrics" / "public"
RUNS_DIR = REPO / "assets" / "runs" / "public"

# Per-field tolerance. Percent-like fields are 0-100, the rest are ratios/counts.
# The reports round for presentation (cost to 2-3 dp, steps to 1-2 dp), so the
# tolerances are set to the report's own printing precision, not to float noise.
TOL = {
    "success": 0.06,
    "askUser": 0.06,
    "guiOnly": 0.06,
    "hc": 0.06,
    "steps": 0.06,
    "queries": 0.011,
    "uiq": 0.0011,
    "kbiq": 0.0011,
    "buckets": 0.06,
    "cost": 0.0051,
    "askUserCost": 0.00051,
    "cpuTemp": 0.06,
    "powerSkinTemp": 0.06,
    "batteryTemp": 0.06,
    "batteryDrain": 0.6,
    "elapsedWall": 1.0,
    "elapsedAgent": 1.0,
}


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #
def load_leaderboard_rows() -> list[dict]:
    """Evaluate LEADERBOARD_ROWS in node and return it as JSON.

    The array is a JS object literal (unquoted keys, comments, trailing commas),
    so evaluating it in its native runtime is the only faithful read. Node is
    already a repo dependency (`node website/tools/build_site_data.mjs`).
    """
    if not LEADERBOARD_JS.exists():
        raise SystemExit(f"leaderboard not found: {LEADERBOARD_JS}")
    script = (
        "const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');"
        "const s=src.indexOf('const LEADERBOARD_ROWS = [');"
        "if(s<0)throw new Error('LEADERBOARD_ROWS not found');"
        "const e=src.indexOf('\\n];', s);"
        "const arr=eval(src.slice(s+25,e+2));"
        "process.stdout.write(JSON.stringify(arr));"
    )
    try:
        out = subprocess.run(
            ["node", "-e", script, str(LEADERBOARD_JS)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except FileNotFoundError as exc:  # pragma: no cover - environment guard
        raise SystemExit("node is required to read leaderboard.js") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"could not evaluate leaderboard.js: {exc.stderr.strip()}") from exc
    return json.loads(out)


@dataclass
class Report:
    """One run report, reduced to the values the leaderboard publishes."""

    path: Path
    run_root: str
    metric: dict[str, list[str]] = field(default_factory=dict)
    bucket: dict[str, list[str]] = field(default_factory=dict)
    telemetry: dict[str, list[str]] = field(default_factory=dict)

    def m(self, *needles: str, exclude: tuple[str, ...] = ()) -> list[str] | None:
        """First metric row whose label contains every needle and no exclude."""
        for label, cells in self.metric.items():
            low = label.lower()
            if all(n.lower() in low for n in needles) and not any(
                x.lower() in low for x in exclude
            ):
                return cells
        return None

    def t(self, *needles: str) -> list[str] | None:
        for label, cells in self.telemetry.items():
            low = label.lower()
            if all(n.lower() in low for n in needles):
                return cells
        return None


ROW_RE = re.compile(r"^\|(.+)\|\s*$")


def _split_row(line: str) -> list[str]:
    """Split a markdown table row, honouring escaped pipes."""
    body = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def _clean(cell: str) -> str:
    return cell.replace("**", "").replace("`", "").strip()


def parse_report(path: Path) -> Report:
    """Split a report into its metric / bucket / telemetry tables."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"run root:\*\*\s*`?(assets/runs/public/[^/`]+)/?", text, re.IGNORECASE)
    report = Report(path=path, run_root=m.group(1) if m else "")

    # Walk tables; remember the most recent header so bucket tables are separable.
    header: list[str] = []
    for line in text.splitlines():
        if not ROW_RE.match(line):
            header = []
            continue
        cells = [_clean(c) for c in _split_row(line)]
        if len(cells) < 2:
            continue
        if set("".join(cells)) <= set("-: "):  # separator row
            continue
        label = cells[0]
        if label.lower() == "metric":
            header = cells
            continue
        if label.lower() == "bucket":
            header = cells
            continue
        joined_header = " ".join(header).lower()
        if "bucket" in joined_header:
            # bucket table: rows are easy/medium/hard
            if label.lower() in {"easy", "medium", "hard"}:
                report.bucket[label.lower()] = cells[1:]
            continue
        # metric tables: first row is "| Metric | ... |"; classify by header
        if not header:
            continue
        if "value" in joined_header and "agent llm cost" not in joined_header:
            # one "Metric | Value" table can hold both manual+official columns,
            # and the telemetry table reuses the same header, so keep both maps.
            report.metric.setdefault(label, cells[1:])
            report.telemetry.setdefault(label, cells[1:])
    return report


# --------------------------------------------------------------------------- #
# value extraction
# --------------------------------------------------------------------------- #
NUM_RE = re.compile(r"[-\u2212\u2013]?\d[\d,]*\.?\d*")
PCT_RE = re.compile(r"([-\u2212\u2013]?\d[\d,]*\.?\d*)\s*%")
FRAC_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def _norm(s: str) -> str:
    """Reports use a typographic minus (U+2212) for temperature/drain deltas."""
    return s.replace("\u2212", "-").replace("\u2013", "-")


def _to_num(s: str) -> float | None:
    s = _norm(_clean(s))
    m = NUM_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def first_num(cells: list[str] | None) -> float | None:
    if not cells:
        return None
    return _to_num(cells[0])


def max_num(cells: list[str] | None) -> float | None:
    """Largest number in a cell.

    The board reports the *peak* for the thermal columns: 'Max CPU / GPU / NPU
    temp' stores max(CPU, GPU, NPU) and 'Max power-amp / skin temp' stores
    max(power-amp, skin).
    """
    if not cells:
        return None
    nums = [float(n.replace(",", "")) for n in NUM_RE.findall(_norm(_clean(cells[0])))]
    if not nums and len(cells) > 1:
        for cell in cells[1:]:
            nums = [float(n.replace(",", "")) for n in NUM_RE.findall(_norm(_clean(cell)))]
            if nums:
                break
    return max(nums) if nums else None


def last_num(cells: list[str] | None) -> float | None:
    """Last cell that carries a number (skips an em-dash manual placeholder)."""
    for cell in reversed(cells or []):
        if _clean(cell) in {"—", "-", ""}:
            continue
        if re.search(r"\bN/?A\b", _clean(cell), re.IGNORECASE):
            return None
        v = _to_num(cell)
        if v is not None:
            return v
    return None


def first_pct(cells: list[str] | None) -> float | None:
    """Percent from the first cell, or a fraction X/Y expressed as a percent."""
    if not cells:
        return None
    cell = _norm(cells[0])
    m = PCT_RE.search(cell)
    if m:
        return float(m.group(1).replace(",", ""))
    f = FRAC_RE.search(cell)
    if f:
        tot = float(f.group(2))
        return float(f.group(1)) / tot * 100 if tot else None
    return None


def _pct_or_frac_at(text: str) -> tuple[float | None, int]:
    """Value + position of the last percentage or fraction in `text`."""
    text = _norm(text)
    hits: list[tuple[int, float]] = []
    for m in PCT_RE.finditer(text):
        hits.append((m.start(), float(m.group(1).replace(",", ""))))
    for m in FRAC_RE.finditer(text):
        tot = float(m.group(2))
        if tot:
            hits.append((m.start(), float(m.group(1)) / tot * 100))
    if not hits:
        return None, -1
    pos, val = max(hits)
    return val, pos


def askuser_pct(cells: list[str] | None) -> float | None:
    """ASK USER pass rate on the *11* ASK USER tasks (7 SINGLE + 4 MULTI).

    The reports print two figures, e.g.
        **28.6%** (2/7 single-turn) · **18.2% (2/11)** all ASK USER
    and the board publishes the all-ASK-USER one (see COL_DEFS.askUser).
    """
    if not cells:
        return None
    text = cells[0]
    low = text.lower()
    if "all ask user" in low:
        val, _ = _pct_or_frac_at(text[: low.index("all ask user")])
        return val
    val, _ = _pct_or_frac_at(text)
    return val


def manual_fraction_pct(cells: list[str] | None) -> float | None:
    """Percent implied by the *manually graded* X/Y in an HC row.

    Rows mix the manual and DeepEval counts in either order
    ('**5/7 (71.4%)** — manual (official/DeepEval 6/7 …)' but also
    'DeepEval **7/7** · Manual **5/7**'), so each fraction is classified by the
    text that *introduces* it (the span since the previous fraction) rather than
    by a fixed-size window, which would bleed one fraction's label onto the next.
    """
    if not cells:
        return None
    text = _norm(cells[0])
    matches = list(FRAC_RE.finditer(text))
    if not matches:
        return first_pct(cells)

    def value(m: re.Match[str]) -> float | None:
        tot = float(m.group(2))
        return float(m.group(1)) / tot * 100 if tot else None

    neutral: tuple[float | None] | None = None
    cursor = 0
    for m in matches:
        introducer = text[cursor : m.start()].lower()
        cursor = m.end()
        if "deepeval" in introducer or "official" in introducer:
            continue
        if "manual" in introducer:
            return value(m)
        if neutral is None:
            neutral = (value(m),)
    if neutral is not None:
        return neutral[0]
    return value(matches[0])


def kbiq_nothing_to_grade(cells: list[str] | None) -> bool:
    """True when a KBIQ row says the metric is ungraded (no asks reached)."""
    if not cells:
        return False
    text = _norm(" ".join(cells)).lower()
    return ("n/a" in text) or bool(re.search(r"\b0\s+asks?\b", text)) or bool(
        re.search(r"\b0\s*/\s*0\b", text)
    )


def dollars(cells: list[str] | None) -> float | None:
    if not cells:
        return None
    m = re.search(r"\$\s*([\d,]+\.?\d*)", cells[0])
    return float(m.group(1).replace(",", "")) if m else None


# --------------------------------------------------------------------------- #
# reconciliation
# --------------------------------------------------------------------------- #
@dataclass
class FieldResult:
    name: str
    expected: float | str | None
    actual: float | str | None
    source: str
    ok: bool
    note: str = ""
    warn: bool = False
    """`warn` marks a cross-check against a third source (the official metrics
    JSON) that the board does not publish from. A disagreement there is report
    drift, not a leaderboard bug, so it does not fail the gate."""


def compare(
    name: str,
    lb_value: float | str | None,
    report_value: float | str | None,
    source: str,
    *,
    tol: float | None = None,
) -> FieldResult:
    tol = TOL.get(name, 0.01) if tol is None else tol
    if report_value is None:
        return FieldResult(name, None, lb_value, source, True, "not in report")
    if isinstance(lb_value, str) or isinstance(report_value, str):
        # "N/A" / "0.000"-style: normalise both to a token
        a = re.sub(r"[\s`]+", "", str(lb_value)).upper()
        b = re.sub(r"[\s`]+", "", str(report_value)).upper()
        if a == b:
            return FieldResult(name, b, a, source, True, "")
        # a report that says 0.000 where the board says N/A is a real disagreement
        ok = _numishes_equal(a, b, tol)
        return FieldResult(name, b, a, source, ok, "" if ok else "string mismatch")
    ok = abs(float(lb_value) - float(report_value)) <= tol
    return FieldResult(name, report_value, lb_value, source, ok, "" if ok else "out of tolerance")


def _numishes_equal(a: str, b: str, tol: float) -> bool:
    na, nb = _to_num(a), _to_num(b)
    if na is None or nb is None:
        return False
    return abs(na - nb) <= tol


def derive_cost(run_root: Path) -> tuple[int, float, int, float] | None:
    """(llm_requests, agent_cost, ask_requests, ask_cost) from the run's proxies."""
    if not run_root.is_dir():
        return None
    n = 0
    cost = 0.0
    an = 0
    acost = 0.0
    found = False
    for root, _dirs, files in os.walk(run_root):
        for fname in files:
            if fname not in {"llm_proxy_metrics.jsonl", "ask_user_metrics.jsonl"}:
                continue
            found = True
            for line in (Path(root) / fname).open(encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if fname == "llm_proxy_metrics.jsonl":
                    n += 1
                    cost += float((rec.get("usage") or {}).get("cost") or 0.0)
                else:
                    an += 1
                    acost += float(rec.get("cost") or 0.0)
    return (n, cost, an, acost) if found else None


def requests_in(cells: list[str] | None) -> int | None:
    if not cells:
        return None
    m = re.search(r"\(([\d,]+)\s+(?:requests|calls)", cells[0])
    return int(m.group(1).replace(",", "")) if m else None


def check_row(idx: int, row: dict, report: Report, official: dict | None, verbose: bool) -> list[FieldResult]:
    out: list[FieldResult] = []
    inter = row.get("interrupted")

    # ---- success -------------------------------------------------------- #
    if inter:
        relaxed = round(inter["passed"] / inter["total"] * 100, 1)
        out.append(
            FieldResult(
                "success",
                relaxed,
                row["success"]["score"],
                f"interrupted.passed/{inter['total']} (relaxed)",
                abs(relaxed - row["success"]["score"]) <= TOL["success"],
            )
        )
        reached = round(inter["passed"] / inter["finished"] * 100, 1)
        rep_reached = first_pct(
            report.m("success rate", exclude=("ask user", "gui-only", "comparable", "interaction"))
        )
        out.append(
            FieldResult(
                "success(reached)",
                reached,
                rep_reached,
                "report Success Rate (reached denom)",
                rep_reached is not None and abs(reached - rep_reached) <= TOL["success"],
            )
        )
        comparable = report.m("success rate", "comparable")
        if comparable:
            out.append(
                compare("success", row["success"]["score"], first_pct(comparable), "report comparable-60")
            )
    else:
        out.append(
            compare(
                "success",
                row["success"]["score"],
                first_pct(report.m("success rate", exclude=("ask user", "gui-only", "interaction"))),
                "report Success Rate (manual)",
            )
        )

    # ---- ask user / gui only / hc ---------------------------------------- #
    out.append(compare("askUser", row["askUser"], askuser_pct(report.m("ask user")), "report ASK USER (manual)"))
    out.append(compare("guiOnly", row["guiOnly"], first_pct(report.m("gui-only")), "report GUI-only (manual)"))
    out.append(
        compare(
            "hc",
            row["hc"]["score"],
            manual_fraction_pct(report.m("hallucination-control honesty")),
            "report HC honesty (manual)",
        )
    )

    # ---- derived: steps / queries / uiq / kbiq ---------------------------- #
    out.append(compare("steps", row["steps"], last_num(report.m("average completion steps")), "report steps (official)"))
    out.append(compare("queries", row["queries"], last_num(report.m("average user queries")), "report queries (official)"))
    out.append(compare("uiq", row["uiq"], last_num(report.m("uiq")), "report UIQ (official)"))
    kbiq_cells = report.m("kbiq")
    kbiq_val = last_num(kbiq_cells)
    lb_kbiq = row["kbiq"]
    if isinstance(lb_kbiq, str) and kbiq_nothing_to_grade(kbiq_cells):
        # "0 correct / 0 asks" is rendered as N/A on the board (see COL_DEFS.kbiq)
        out.append(
            FieldResult("kbiq", "N/A (ungraded)", lb_kbiq, "report KBIQ (ungraded)", True, "nothing to grade")
        )
    else:
        out.append(compare("kbiq", lb_kbiq, kbiq_val, "report KBIQ (manual)"))

    # official metrics JSON is an independent machine-generated cross-check. The
    # board does not publish from it (it publishes the manually-audited report),
    # so a disagreement is *report* drift — surface it, don't fail the gate.
    if official:
        for field_name, key in (("steps", "average_steps"), ("queries", "average_user_queries")):
            off = official.get(key)
            if off is not None:
                out.append(
                    FieldResult(
                        f"{field_name}(official)",
                        round(float(off), 4),
                        row[field_name],
                        "metrics/public/*-report.json",
                        abs(row[field_name] - float(off)) <= TOL[field_name],
                        warn=True,
                    )
                )
        off_uiq = official.get("user_interaction_quality_factmatch")
        if off_uiq is not None and isinstance(row["uiq"], (int, float)):
            out.append(
                FieldResult(
                    "uiq(metrics-json)",
                    round(float(off_uiq), 4),
                    row["uiq"],
                    "metrics/public/*-report.json",
                    abs(row["uiq"] - float(off_uiq)) <= 0.006,
                    warn=True,
                )
            )

    # ---- buckets --------------------------------------------------------- #
    for bucket in ("easy", "medium", "hard"):
        cells = report.bucket.get(bucket)
        if cells:
            out.append(
                compare(f"buckets.{bucket}", row["buckets"][bucket], first_pct(cells), f"report bucket {bucket}")
            )

    # ---- telemetry ------------------------------------------------------- #
    cost_cells = report.t("agent llm cost")
    out.append(compare("cost", row["cost"]["total"], dollars(cost_cells), "report agent LLM cost"))
    rep_req = requests_in(cost_cells)
    if rep_req is not None:
        lb_req = _to_num(row["cost"]["detail"])
        out.append(
            FieldResult(
                "cost.requests",
                rep_req,
                int(lb_req) if lb_req is not None else None,
                "report agent LLM cost (requests)",
                lb_req is not None and int(lb_req) == rep_req,
            )
        )
    ask_cells = report.t("ask_user cost")
    out.append(compare("askUserCost", row["askUserCost"]["total"], dollars(ask_cells), "report ask_user cost"))

    for field_name, needles, lb, extractor in (
        ("cpuTemp", ("max cpu", "npu temp"), row["cpuTemp"]["max"], max_num),
        ("powerSkinTemp", ("power-amp", "skin temp"), (row.get("powerSkinTemp") or {}).get("max"), max_num),
        ("batteryTemp", ("max battery",), row["batteryTemp"], first_num),
    ):
        if lb is None:
            continue
        val = extractor(report.t(*needles))
        out.append(compare(field_name, lb, val, f"report {needles[0]}"))

    drain_cells = report.t("battery", "drain") or report.t("battery level", "\u0394")
    if drain_cells:
        val = first_num(drain_cells)
        out.append(
            compare(
                "batteryDrain",
                abs(row["batteryDrain"]),
                abs(val) if val is not None else None,
                "report battery drain",
            )
        )

    # ---- elapsed --------------------------------------------------------- #
    el_cells = report.t("elapsed")
    lb_wall = _to_num((row.get("elapsed") or {}).get("wall"))
    rep_wall = first_num(el_cells)
    out.append(compare("elapsedWall", lb_wall, rep_wall, "report elapsed (wall)"))
    lb_agent = _to_num((row.get("elapsed") or {}).get("agent"))
    rep_agent = None
    if el_cells:
        nums = [float(x.replace(",", "")) for x in re.findall(r"([\d,]+)\s*s", el_cells[0])]
        if len(nums) >= 2:
            rep_agent = nums[1]
    if lb_agent is not None and rep_agent is not None:
        out.append(compare("elapsedAgent", lb_agent, rep_agent, "report elapsed (agent)"))

    if verbose:
        for r in out:
            mark = "ok " if r.ok else "BAD"
            print(f"      [{mark}] {r.name:22} lb={r.actual!s:>12}  report={r.expected!s:>12}  {r.source}")
    return out


def find_report(run_root: str) -> Path | None:
    """Locate the report whose `Run root:` matches this leaderboard row."""
    ts = run_root.rstrip("/").split("/")[-1]
    for path in sorted(REPORTS_DIR.glob("public-*.md")):
        if path.name.endswith("-report.md"):
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
        if f"assets/runs/public/{ts}/" in head:
            return path
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--row", type=int, action="append", help="check only this row by position in LEADERBOARD_ROWS (rank order, 1-based, repeatable)")
    ap.add_argument("--model", action="append", help="check only rows whose model name contains this substring (repeatable)")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every parsed value per row")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--no-artifacts", action="store_true", help="skip the local run-root cost check")
    args = ap.parse_args()

    rows = load_leaderboard_rows()
    results: dict[str, list[FieldResult]] = {}
    report_errors: list[str] = []
    cost_drift: list[str] = []

    for i, row in enumerate(rows, start=1):
        if args.row and i not in args.row:
            continue
        if args.model and not any(m.lower() in row["model"].lower() for m in args.model):
            continue
        run_root = row.get("runRoot")
        if not run_root:
            report_errors.append(f"row {i} ({row['model']}): no `runRoot` field on the leaderboard row")
            continue
        path = find_report(run_root)
        if path is None:
            report_errors.append(f"row {i} ({row['model']}): no report matches run root {run_root}")
            continue
        report = parse_report(path)
        ts = run_root.rstrip("/").split("/")[-1]
        mpath = METRICS_DIR / f"public-{ts}-report.json"
        official = json.loads(mpath.read_text()) if mpath.exists() else None

        if not args.json:
            print(f"row {i:>2}  {row['model']}")
            print(f"        lb: {LEADERBOARD_JS.relative_to(REPO)}")
            print(f"        rp: {path.relative_to(REPO)}")
        res = check_row(i, row, report, official, args.verbose)
        results[f"{i} {row['model']}"] = res

        # independent artifact check of the cost group
        if not args.no_artifacts:
            derived = derive_cost(REPO / run_root)
            if derived:
                n, cost, an, acost = derived
                lbc = row["cost"]["total"]
                lbn = _to_num(row["cost"]["detail"])
                lba = row["askUserCost"]["total"]
                problems = []
                if abs(cost - lbc) > TOL["cost"]:
                    problems.append(f"cost {lbc} vs {round(cost, 4)}")
                if lbn is None or int(lbn) != n:
                    problems.append(f"requests {int(lbn) if lbn else None} vs {n}")
                if abs(acost - lba) > TOL["askUserCost"]:
                    problems.append(f"ask_user {lba} vs {round(acost, 4)}")
                if problems:
                    cost_drift.append(f"row {i} ({row['model']}): " + "; ".join(problems))
                    res.append(
                        FieldResult("cost(artifacts)", f"{n} req / ${round(cost, 4)}", f"{lbn} req / ${lbc}", "llm_proxy_metrics.jsonl", False)
                    )
                elif not args.json:
                    print(f"        artifacts: {n} req / ${cost:.4f} / ask {an} / ${acost:.4f}  ok")

    if args.json:
        payload = {
            "rows": {
                key: [
                    {
                        "field": r.name,
                        "expected": r.expected,
                        "actual": r.actual,
                        "source": r.source,
                        "ok": r.ok,
                        "warn": r.warn,
                    }
                    for r in rs
                ]
                for key, rs in results.items()
            },
            "errors": report_errors,
            "costDrift": cost_drift,
        }
        print(json.dumps(payload, indent=1, default=str))
        bad = [r for rs in results.values() for r in rs if not r.ok and not r.warn] or report_errors
        return 1 if bad else 0

    failures = [(key, r) for key, rs in results.items() for r in rs if not r.ok and not r.warn]
    warnings = [(key, r) for key, rs in results.items() for r in rs if not r.ok and r.warn]
    print()
    if report_errors:
        print("STRUCTURE ERRORS")
        for e in report_errors:
            print(f"  ! {e}")
        print()
    if failures:
        print(f"MISMATCHES ({len(failures)}) — leaderboard does not match the run report")
        for key, r in failures:
            print(f"  ✗ {key}  ·  {r.name}: leaderboard {r.actual!r} vs {r.source} {r.expected!r}")
        print()
    else:
        print("All checked leaderboard values agree with their run reports.")
    if cost_drift:
        print("COST DRIFT vs local run artifacts")
        for c in cost_drift:
            print(f"  ✗ {c}")
        print()
    if warnings:
        print(f"REPORT vs OFFICIAL METRICS JSON ({len(warnings)}) — not a leaderboard bug")
        for key, r in warnings:
            print(f"  ~ {key}  ·  {r.name}: metrics JSON {r.expected!r} vs published {r.actual!r}")
        print()
    total = sum(len(rs) for rs in results.values())
    print(f"checked {len(results)} row(s), {total} field(s) -> {len(failures)} mismatch(es), {len(warnings)} warning(s)")
    return 1 if failures or report_errors else 0


if __name__ == "__main__":
    sys.exit(main())
