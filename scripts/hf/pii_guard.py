#!/usr/bin/env python3
"""PII / secret scanner for run artifacts bound for the public HF dataset.

**This tool is report-only.** It never deletes, moves or rewrites an artifact
unless you explicitly pass `--i-understand-this-modifies-artifacts` together with
`--redact` or `--quarantine`. Repo policy is that a human reviews the findings
and decides what to do; the scanner's job is to make the leak visible, not to act
on it.

Why this exists
---------------
Public runs are captured from a *real* phone, so their trajectories legitimately
contain whatever was on the device at capture time: the notification shade, SMS
inboxes, Drive listings, Telegram chat lists. On 2026-08-26 that captured a live
MF OTP, an HDFC card-spend alert, a CIBIL notice, real account balances, and the
filenames of third-party resumes/CVs shared from the owner's Drive.

The device is *supposed* to be seeded with a fictional persona. The scanner's
whole job is therefore: **allow the seeded values, flag anything else.** Anything
not traceable to a seed file is, by construction, either real device data or an
unreviewed fabrication, and needs a human look before publishing.

Usage
-----
    # Scan a run directory (text + screenshots + trajectory gifs)
    python3 scripts/hf/pii_guard.py assets/runs/public/20260826-105200

    # Machine-readable report
    python3 scripts/hf/pii_guard.py assets/runs/public/<run> --json /tmp/pii.json

    # Skip OCR (fast, text only)
    python3 scripts/hf/pii_guard.py assets/runs/public/<run> --no-images

Exit status
-----------
    0  report produced (default - findings do NOT fail the run)
    2  only with --strict, when HIGH-severity findings exist

Image scanning needs macOS (Apple Vision via JXA). Elsewhere the image pass is
skipped with a warning, and `--require-images` turns that into a failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TEXT_SUFFIXES = {".json", ".jsonl", ".ndjson", ".txt", ".log", ".md", ".yaml", ".yml", ".csv", ".xml", ".html"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
ANIM_SUFFIXES = {".gif"}

# Seed files that describe the *intended* fictional persona / device state.
# Values found here are expected in trajectories and must not be flagged.
ALLOWLIST_SOURCES = [
    ".fabricated_test_data.json",
    "benchmarks/androidlife-530/public_vars.local.env",
    "benchmarks/androidlife-530/public_vars.example.env",
    "benchmarks/androidlife-530/tasks_vars.local.env",
    "benchmarks/androidlife-530/tasks_vars.local.json",
    "benchmarks/androidlife-530/tasks_vars_usage.json",
    "benchmarks/androidlife-530/ask_user_facts_public.json",
    "benchmarks/androidlife-530/ask_user_facts_530.json",
    "benchmarks/androidlife-530/multiturn_kb_public.json",
    "benchmarks/androidlife-530/multiturn_kb_530.json",
    "config/user.yaml",
    "config/user_config.example",
]

# Domains/addresses that are defined as non-personal by convention.
PLACEHOLDER_DOMAINS = ("example.com", "example.org", "email.com", "test.com", "localhost")

EMAIL_RX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RX = re.compile(r"(?:\+91[\s\-]?)?\b[6-9]\d{4}[\s\-]?\d{5}\b")
AADHAAR_RX = re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b")
PAN_RX = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
CARD_RX = re.compile(r"\b(?:\d[ \-]?){13,19}\b")
DIGITS_RX = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")

OTP_CONTEXT_RX = re.compile(
    r"(?i)(otp|one[\s\-]?time\s?(?:password|code|pin)|verification\s+code|"
    r"authorisation\s+code|authorization\s+code|do\s+not\s+share|valid\s+for\s+\d+\s*min)"
)
BANK_RX = re.compile(
    r"(?i)(spent\s+rs\.?|debited|credited|available\s+balance|avl\s+bal|a/?c\s+balance|"
    r"card\s+x?\d{4}|statement\s+due|minimum\s+due|emi\s+of|"
    r"hdfc|icici|sbi|axis\s+bank|kotak|yes\s+bank|paytm|phonepe|gpay)"
)
BUREAU_RX = re.compile(r"(?i)(cibil|experian|equifax|crif|dispute\s+id|credit\s+score)")
RESUME_RX = re.compile(
    r"(?i)\b((?:resume|cv|curriculum\s+vitae)[^\n\"']{0,40}\.pdf|[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:resume|cv)\b|"
    r"[A-Za-z_]+\s*[_\-]\s*(?:CV|Resume)\b[^\n\"']{0,30})"
)
# A person-name-looking token immediately followed by a role suffix, as it shows
# up in a Drive / contacts listing. Deliberately narrow to keep precision.
NAME_ROLE_RX = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+(?:SE|SDE|AIML|AI|ML|HR|QA|PM)\b")


@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    match: str
    context: str = ""
    location: str = ""

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "match": self.match,
            "context": self.context,
            "location": self.location,
        }


@dataclass
class Allowlist:
    """Values the benchmark intends to be on the device."""

    values: set[str] = field(default_factory=set)
    digits: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, root: Path = REPO_ROOT) -> "Allowlist":
        al = cls()
        for rel in ALLOWLIST_SOURCES:
            p = root / rel
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            al.values.add(rel)
            for m in EMAIL_RX.findall(text):
                al.values.add(m.lower())
            for m in PHONE_RX.findall(text):
                al.digits.add(re.sub(r"\D", "", m))
            for m in DIGITS_RX.findall(text):
                al.digits.add(m)
            # env-style KEY=value lines: the value is intentional seeded content
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                _, _, val = line.partition("=")
                val = val.strip().strip("'\"")
                if val:
                    al.values.add(val)
                    for m in DIGITS_RX.findall(val):
                        al.digits.add(m)
        return al

    def email_ok(self, addr: str) -> bool:
        a = addr.lower()
        if a in self.values:
            return True
        return any(a.endswith("@" + d) for d in PLACEHOLDER_DOMAINS)

    def phone_ok(self, raw: str) -> bool:
        return re.sub(r"\D", "", raw) in self.digits

    def digits_ok(self, raw: str) -> bool:
        return raw in self.digits


def _clip(text: str, idx: int, width: int = 60) -> str:
    lo = max(0, idx - width)
    return text[lo : idx + width].replace("\n", " ")


def scan_text(text: str, path: str, allow: Allowlist, source: str = "") -> list[Finding]:
    """Apply every text rule to one blob of text."""
    out: list[Finding] = []

    for m in EMAIL_RX.finditer(text):
        if not allow.email_ok(m.group(0)):
            out.append(Finding("email_unseeded", "HIGH", path, m.group(0), _clip(text, m.start()), source))

    for m in PHONE_RX.finditer(text):
        if not allow.phone_ok(m.group(0)):
            out.append(Finding("phone_unseeded", "HIGH", path, m.group(0), _clip(text, m.start()), source))

    for m in OTP_CONTEXT_RX.finditer(text):
        # The code can sit either side of the trigger word ("371789 is OTP for
        # authorising your..." and "OTP: 371789" are both common in SMS layout).
        lo = max(0, m.start() - 120)
        window = text[lo : m.start() + 160]
        for d in DIGITS_RX.finditer(window):
            if not allow.digits_ok(d.group(1)):
                at = lo + d.start()
                out.append(Finding("otp_like_code", "HIGH", path, d.group(1), _clip(text, at), source))

    for rx, rule, sev in (
        (BANK_RX, "bank_alert", "HIGH"),
        (BUREAU_RX, "credit_bureau", "HIGH"),
        (PAN_RX, "pan_number", "HIGH"),
        (AADHAAR_RX, "aadhaar_like", "HIGH"),
    ):
        for m in rx.finditer(text):
            hit = m.group(0)
            if rule == "bank_alert" and any(t in allow.values for t in (hit,)):
                continue
            out.append(Finding(rule, sev, path, hit, _clip(text, m.start()), source))

    for m in RESUME_RX.finditer(text):
        out.append(Finding("resume_or_cv_filename", "HIGH", path, m.group(0), _clip(text, m.start()), source))

    for m in NAME_ROLE_RX.finditer(text):
        if m.group(0).lower() not in {v.lower() for v in allow.values if v}:
            out.append(Finding("person_name_with_role", "LOW", path, m.group(0), _clip(text, m.start()), source))

    for m in CARD_RX.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and not allow.digits_ok(digits):
            out.append(Finding("card_like_number", "HIGH", path, m.group(0), _clip(text, m.start()), source))

    return out


# --- image OCR (macOS Apple Vision, via JavaScript for Automation) -----------
# The list of paths is interpolated per batch so concurrent batches never share
# a scratch file.
_OCR_HELPER = r"""
ObjC.import('Foundation'); ObjC.import('Vision');
function ocr(path) {
  var url = $.NSURL.fileURLWithPath(path);
  var req = $.VNRecognizeTextRequest.alloc.init;
  req.recognitionLevel = 1; req.usesLanguageCorrection = false;
  var h = $.VNImageRequestHandler.alloc.initWithURLOptions(url, $());
  h.performRequestsError($.NSArray.arrayWithObject(req), $());
  var out = [], obs = req.results;
  for (var i = 0; i < obs.count; i++)
    out.push(ObjC.unwrap(obs.objectAtIndex(i).topCandidates(1).objectAtIndex(0).string));
  return out.join(' | ');
}
var s = $.NSString.stringWithContentsOfFileEncodingError(LISTFILE, $.NSUTF8StringEncoding, $());
var files = ObjC.unwrap(s).trim().split('\n');
var res = {};
for (var i = 0; i < files.length; i++) {
  try { res[files[i]] = ocr(files[i]); } catch (e) { res[files[i]] = ''; }
}
console.log(JSON.stringify(res));
"""


def ocr_available() -> bool:
    if sys.platform != "darwin" or not shutil.which("osascript"):
        return False
    return True


def _ocr_batch(paths: list[Path], timeout: int) -> dict[str, str]:
    """OCR one batch in a private scratch dir (safe under a thread pool)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        listfile = tmp / "paths.txt"
        listfile.write_text("\n".join(str(p) for p in paths), encoding="utf-8")
        helper = tmp / "ocr.js"
        helper.write_text(_OCR_HELPER.replace("LISTFILE", json.dumps(str(listfile))), encoding="utf-8")
        try:
            proc = subprocess.run(
                ["osascript", "-l", "JavaScript", str(helper)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {}
    # osascript sends console.log to stderr on some builds and stdout on others.
    raw = (proc.stdout + proc.stderr).strip()
    for line in reversed(raw.splitlines()):
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {}


def _gif_frames(path: Path, tmpdir: Path) -> list[Path]:
    """Gifs embed the whole session, so OCR a spread of frames, not just the last."""
    try:
        from PIL import Image  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return []
    out: list[Path] = []
    try:
        im = Image.open(path)
        n = getattr(im, "n_frames", 1)
        picks = sorted({0, n - 1, *range(0, n, max(1, n // 6))})
        for i in picks:
            if i >= n:
                continue
            im.seek(i)
            q = tmpdir / f"{path.stem}_f{i:03d}.png"
            im.convert("RGB").save(q)
            out.append(q)
    except Exception:  # noqa: BLE001
        return out
    return out


def scan_images(
    images: list[Path],
    allow: Allowlist,
    root: Path,
    batch: int = 8,
    workers: int = 4,
    timeout: int = 180,
) -> list[Finding]:
    if not images:
        return []
    if not ocr_available():
        print("WARNING: image OCR needs macOS (Apple Vision) - images NOT scanned", file=sys.stderr)
        return []

    findings: list[Finding] = []
    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)

        # OCR needs whole frames; gifs are expanded to a frame spread first.
        frames: dict[Path, Path] = {}
        work: list[Path] = list(images)
        for gif in [p for p in images if p.suffix.lower() in ANIM_SUFFIXES]:
            for fr in _gif_frames(gif, tmpdir):
                frames[fr] = gif
                work.append(fr)

        batches = [work[i : i + batch] for i in range(0, len(work), batch)]
        with ThreadPoolExecutor(workers) as pool:
            per_batch = list(pool.map(lambda b: _ocr_batch(b, timeout), batches))

        for b, got in zip(batches, per_batch):
            for p in b:
                text = got.get(str(p), "")
                if not text:
                    continue
                origin = frames.get(p, p)
                rel = str(origin.relative_to(root)) if origin.is_relative_to(root) else str(origin)
                src = "gif-frame" if p in frames else "image-ocr"
                findings.extend(scan_text(text, rel, allow, source=src))
    return findings


def iter_files(targets: list[Path]) -> tuple[list[Path], list[Path]]:
    texts: list[Path] = []
    images: list[Path] = []
    for t in targets:
        if t.is_file():
            (texts if t.suffix.lower() in TEXT_SUFFIXES else images).append(t)
            continue
        for p in t.rglob("*"):
            if not p.is_file():
                continue
            suf = p.suffix.lower()
            if suf in TEXT_SUFFIXES:
                texts.append(p)
            elif suf in IMAGE_SUFFIXES or suf in ANIM_SUFFIXES:
                images.append(p)
    return texts, images


def redact_text(paths: list[Path], findings: list[Finding]) -> int:
    """Scrub the flagged text files in place. Images can't be scrubbed - quarantine them."""
    by_path: dict[str, list[Finding]] = {}
    for f in findings:
        if f.match and f.severity == "HIGH" and f.location != "image-ocr" and f.location != "gif-frame":
            by_path.setdefault(f.path, []).append(f)

    repl = {
        "otp_like_code": "[otp-redacted]",
        "bank_alert": "[bank-detail-redacted]",
        "credit_bureau": "[bureau-detail-redacted]",
        "pan_number": "[pan-redacted]",
        "aadhaar_like": "[id-redacted]",
        "card_like_number": "[card-redacted]",
        "email_unseeded": "[email-redacted]",
        "phone_unseeded": "[phone-redacted]",
        "resume_or_cv_filename": "[document-name-redacted]",
    }
    touched = 0
    for rel, fs in by_path.items():
        p = Path(rel)
        if not p.is_file():
            continue
        before = p.read_text(encoding="utf-8", errors="surrogateescape")
        after = before
        for f in fs:
            after = after.replace(f.match, repl.get(f.rule, "[redacted]"))
        if after != before:
            p.write_text(after, encoding="utf-8", errors="surrogateescape")
            touched += 1
    return touched


def quarantine_images(findings: list[Finding], root: Path, dest: Path, targets: list[Path]) -> int:
    """Move flagged images out of the run so they cannot be uploaded.

    DISABLED BY DEFAULT. Repo policy: this scanner reports, it never removes or
    moves artifacts. Review findings by hand, then decide what to do with them.
    Only reachable with --i-understand-this-moves-files.
    """
    flagged = {f.path for f in findings if f.location in ("image-ocr", "gif-frame")}
    moved = 0
    for rel in sorted(flagged):
        src = root / rel
        if not src.is_file():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        out = dest / rel.replace("/", "__")
        shutil.move(str(src), str(out))
        moved += 1
    return moved


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PII/secret scanner for public run artifacts.",
        epilog=(
            "This tool is REPORT-ONLY. It never deletes, moves or rewrites artifacts unless "
            "you explicitly pass --redact --i-understand-this-modifies-artifacts."
        ),
    )
    ap.add_argument("targets", nargs="+", help="Run directory (or individual files) to scan.")
    ap.add_argument("--json", dest="json_out", help="Write the full report as JSON here.")
    ap.add_argument("--no-images", action="store_true", help="Skip the screenshot/gif OCR pass.")
    ap.add_argument("--require-images", action="store_true", help="Return non-zero if OCR is unavailable.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Return exit 2 when HIGH-severity findings exist (for CI / gating).",
    )
    # --- deliberately opt-in, double-gated destructive path -------------------
    ap.add_argument("--redact", action="store_true", help="Scrub HIGH text findings in place (needs the guard flag).")
    ap.add_argument("--quarantine", metavar="DIR", help="Move PII-carrying images to DIR (needs the guard flag).")
    ap.add_argument(
        "--i-understand-this-modifies-artifacts",
        dest="confirm_modify",
        action="store_true",
        help="Required to enable --redact / --quarantine.",
    )
    ap.add_argument("--root", default=str(REPO_ROOT), help="Repo root (for reporting + allowlist).")
    ap.add_argument("--batch", type=int, default=8, help="Images per OCR invocation.")
    ap.add_argument("--workers", type=int, default=4, help="Parallel OCR invocations.")
    args = ap.parse_args()

    destructive = bool(args.redact or args.quarantine)
    if destructive and not args.confirm_modify:
        print(
            "REFUSED: --redact / --quarantine modify artifacts, which this repo does not do "
            "automatically.\n"
            "  Findings are a report for a human to act on. If you really intend to modify\n"
            "  artifacts, re-run with --i-understand-this-modifies-artifacts.",
            file=sys.stderr,
        )
        return 1

    root = Path(args.root).resolve()
    targets = [Path(t).resolve() for t in args.targets]
    texts, images = iter_files(targets)
    if args.no_images:
        images = []
    if args.require_images and not ocr_available():
        print("FAIL: --require-images but OCR is unavailable (needs macOS + osascript)", file=sys.stderr)
        return 2

    allow = Allowlist.load(root)
    print(f"scanning {len(texts)} text files + {len(images)} images", flush=True)
    print(f"allowlist: {len(allow.values)} seeded values, {len(allow.digits)} seeded numeric tokens", flush=True)

    findings: list[Finding] = []
    for p in texts:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(root)) if p.is_relative_to(root) else str(p)
        findings.extend(scan_text(text, rel, allow))
    findings.extend(scan_images(images, allow, root, batch=args.batch, workers=args.workers))

    by_rule: dict[str, int] = {}
    by_file: dict[str, list[str]] = {}
    for f in findings:
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
        by_file.setdefault(f.path, []).append(f"{f.rule}:{f.match}")

    high = [f for f in findings if f.severity == "HIGH"]
    print()
    if not findings:
        print("CLEAN - no candidate PII found")
    else:
        print(f"{len(high)} HIGH / {len(findings) - len(high)} LOW findings across {len(by_file)} files")
        print("(report only - nothing has been changed; review by hand)")
        for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1]):
            print(f"  {rule:26s} {n}")
        print()
        for path, hits in sorted(by_file.items())[:40]:
            print(f"  {path}")
            for h in hits[:6]:
                print(f"      {h}")
            if len(hits) > 6:
                print(f"      ... +{len(hits) - 6} more")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps([f.as_dict() for f in findings], indent=1, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nreport -> {args.json_out}")

    if args.confirm_modify and args.redact:
        n = redact_text(texts, findings)
        print(f"redacted {n} text files in place")
    if args.confirm_modify and args.quarantine:
        n = quarantine_images(findings, root, Path(args.quarantine), targets)
        print(f"quarantined {n} images -> {args.quarantine}")

    if high and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
