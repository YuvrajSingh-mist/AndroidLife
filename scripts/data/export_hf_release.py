"""Assemble Hugging Face release packages for DrainBench (two repos).

Two separate HF repos are produced (the public 530 eval corpus, and the private
public-sample package that carries personal/device-specific data):

1. 530-PUBLIC  (public visibility)
   - DailyBench_530_v1.json/.jsonl (the 530-task corpus)
   - tasks_530.md / tasks.md (source markdown)
   - multiturn_kb_530.json, ask_user_facts.json, hallucination_controls.json
   - vars: tasks_vars.local.env / tasks_vars.local.json / tasks_vars/
   - config/user_config.example (documented defaults, NOT the personal user.yaml)
   - fabrication disclosure (fabricated_test_data.json + fabricated-test-data.md)

2. PUBLIC-SAMPLE  (PRIVATE visibility — contains personal/device data)
   - DailyBench_public_v2.json/.jsonl (the 68-task public 3-day sample: 61 runnable + 7 hallucination-control)
   - public.md (source), multiturn_kb_public.json
   - vars: public_vars.local.env + config/user.yaml (personal values)
   - fabrication/seeds (the fabricated PDFs + enriched Obsidian notes)
   - fabrication disclosure

Usage:
    python scripts/data/export_hf_release.py [--out <dir>] [--force]

Then push each staged dir to its HF repo:
    hf auth login                              # one-time
    huggingface-cli upload <public-repo>  hf_release/530-public
    huggingface-cli upload <private-repo> hf_release/public-sample
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH = REPO_ROOT / "benchmarks" / "dailyBench-600"
DOCS = REPO_ROOT / "docs"
CONFIG = REPO_ROOT / "config"
SEEDS_PUBLIC = REPO_ROOT / "assets" / "seeds" / "public"
DEFAULT_OUT = REPO_ROOT / "hf_release"


def _copy(out: Path, src: Path, rel: str) -> None:
    if not src.exists():
        print(f"  [skip] {rel} (missing)")
        return
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
    print(f"  copied {rel}")


README_530 = """---
license: mit
pretty_name: DrainBench-530 (Android agent benchmark)
task_categories:
  - text-generation
  - other
tags:
  - android
  - mobile-agent
  - agent-benchmark
  - gui-agents
  - tool-use
language:
  - en
size_categories:
  - 1K<n<10K
---

# DrainBench-530 — Android agent benchmark (real phone, real LLM)

DrainBench runs Android agent tasks against a **real phone** (via ADB/mobilerun)
and a real LLM, and grades the agent on reaching a verifiable device end-state.
This repo ships the **530-task corpus** plus everything needed to reproduce runs.

> The 68-task **public 3-day sample** (61 runnable + 7 hallucination-control;
> its personal/device-specific vars + seeds) is kept in a separate private repo;
> this public repo carries only the 530 corpus + its run-time variables +
> fabrication disclosure.

## Files

| File | Content |
|---|---|
| `data/DailyBench_530_v1.json` / `.jsonl` | The 530-task corpus (Easy 1pt / Medium 3pt / Hard 5pt). |
| `data/tasks_530.md` | Human-readable source (canonical prompt text). |
| `data/tasks.md` | Wider task list (superset). |
| `data/multiturn_kb_530.json` | Knowledge-base profiles for **ASK USER - MULTI** tasks. |
| `data/ask_user_facts.json` | Facts for **ASK USER SINGLE** tasks. |
| `data/hallucination_controls.json` | Hallucination-control tasks. |
| `vars/` | 530-corpus run-time variable values (resolve every `[placeholder]`). |
| `config/user_config.example` | Documented default persona/device config. |
| `fabrication/` | Full disclosure of every fabricated test entity. |

## Task model

- **DETERMINISTIC** — everything needed is seeded on-device; end state is
  ADB-verified.
- **ASK USER SINGLE** — one fact deliberately omitted; agent must ask.
- **ASK USER - MULTI** — multi-turn dialogue against the KB profile.

Each record carries `task_id`, exact `prompt_text`/`prompt_template`,
placeholder slots, difficulty, and grading type. Prompts use `[placeholder]`
slots resolved through the run-time variables in `vars/`.

## Fabricated test data — disclosure

To make deterministic tasks solvable, a controlled **fictional persona** and
fabricated data are seeded on the device. Everything is disclosed honestly in
`fabrication/` (machine-readable JSON + full human-readable doc). No real phone
numbers, personal emails, or real identities appear; all personas are fictional.
"""

README_SAMPLE = """---
license: mit
pretty_name: DrainBench public sample (68 tasks, private companion)
task_categories:
  - text-generation
  - other
tags:
  - android
  - mobile-agent
  - agent-benchmark
language:
  - en
size_categories:
  - n<1K
---

# DrainBench public sample (PRIVATE companion repo)

The **68-task public 3-day sample** (61 runnable + 7 hallucination-control) for DrainBench-530, kept in a **private**
repo because it carries personal/device-specific data (run-time vars, the
personal user config, and the fabricated on-device seed documents).

## Files

| File | Content |
|---|---|
| `data/DailyBench_public_v2.json` / `.jsonl` | The 68-task public sample (61 runnable + 7 hallucination-control; drawn from the 530 corpus + public-specific additions). |
| `data/public.md` | Human-readable source. |
| `data/multiturn_kb_public.json` | Knowledge-base profiles for public multi-turn tasks. |
| `vars/public_vars.local.env` | Public-sample placeholder values (personal). |
| `config/user.yaml` | Personal persona/device config (gitignored upstream). |
| `fabrication/seeds/` | Fabricated seed documents: the 2 realistic PDFs + 8 enriched Obsidian notes. |
| `fabrication/` | Full fabrication disclosure. |

The 530 corpus itself is published separately (public repo); this package is the
companion with the sample-specific, personal data. See the main `DrainBench-530`
dataset card for the task model and schema.
"""


def build_530_public(out: Path) -> None:
    print(f"[1/2] 530-public -> {out}")
    for f in ["DailyBench_530_v1.json", "DailyBench_530_v1.jsonl"]:
        _copy(out, BENCH / f, f"data/{f}")
    for f in ["tasks_530.md", "tasks.md"]:
        _copy(out, BENCH / f, f"data/{f}")
    for f in ["multiturn_kb_530.json", "ask_user_facts.json", "hallucination_controls.json"]:
        _copy(out, BENCH / f, f"data/{f}")
    for f in ["tasks_vars.local.env", "tasks_vars.local.json"]:
        _copy(out, BENCH / f, f"vars/{f}")
    _copy(out, BENCH / "tasks_vars", "vars/tasks_vars")
    _copy(out, CONFIG / "user_config.example", "config/user_config.example")
    _copy(out, REPO_ROOT / ".fabricated_test_data.json", "fabrication/fabricated_test_data.json")
    _copy(out, DOCS / "fabricated-test-data.md", "fabrication/fabricated-test-data.md")
    (out / "README.md").write_text(README_530, encoding="utf-8")


def build_public_sample(out: Path) -> None:
    print(f"[2/2] public-sample (private) -> {out}")
    for f in ["DailyBench_public_v2.json", "DailyBench_public_v2.jsonl"]:
        _copy(out, BENCH / f, f"data/{f}")
    for f in ["public.md", "multiturn_kb_public.json"]:
        _copy(out, BENCH / f, f"data/{f}")
    for f in ["public_vars.local.env", "public_vars.example.env"]:
        _copy(out, BENCH / f, f"vars/{f}")
    _copy(out, CONFIG / "user.yaml", "config/user.yaml")
    _copy(out, SEEDS_PUBLIC, "fabrication/seeds")
    _copy(out, REPO_ROOT / ".fabricated_test_data.json", "fabrication/fabricated_test_data.json")
    _copy(out, DOCS / "fabricated-test-data.md", "fabrication/fabricated-test-data.md")
    (out / "README.md").write_text(README_SAMPLE, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage two HF release packages (530-public + private public-sample).")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output staging root.")
    ap.add_argument("--force", action="store_true", help="Replace an existing staging dir.")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out} already exists (use --force to replace)")
        return 1
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    build_530_public(out / "530-public")
    print()
    build_public_sample(out / "public-sample")

    n530 = sum(1 for _ in (out / "530-public").rglob("*") if _.is_file())
    nps = sum(1 for _ in (out / "public-sample").rglob("*") if _.is_file())
    print(f"\nstaged 530-public ({n530} files) + public-sample ({nps} files) under {out}")
    print("next: hf auth login && huggingface-cli upload <repo> <dir>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
