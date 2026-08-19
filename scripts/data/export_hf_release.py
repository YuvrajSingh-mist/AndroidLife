"""Assemble a Hugging Face release package for DrainBench (530 corpus + public sample).

Stages everything needed to actually USE the benchmark into a single folder:
- the two datasets (DailyBench_530_v1, DailyBench_public_v2) in .json/.jsonl
- the source markdown (tasks_530.md / tasks.md / public.md)
- the knowledge bases (multiturn_kb_530 / multiturn_kb_public) + ask-user facts
  + hallucination controls
- the run-time vars (all .env / .local / tasks_vars / config/user.yaml) so every
  placeholder resolves out of the box
- the full fabrication disclosure (.fabricated_test_data.json + the disclosure
  doc) and the public seed artifacts (assets/seeds/public: the fabricated PDFs
  and enriched Obsidian notes)

The staged folder can then be pushed to a Hugging Face dataset repo:

    hf auth login                 # one-time
    python scripts/data/export_hf_release.py --out /tmp/drainbench-hf
    huggingface-cli upload <repo> /tmp/drainbench-hf

Usage:
    python scripts/data/export_hf_release.py [--out <dir>] [--force]
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

DATASET_FILES = [
    "DailyBench_530_v1.json",
    "DailyBench_530_v1.jsonl",
    "DailyBench_public_v2.json",
    "DailyBench_public_v2.jsonl",
]
SOURCE_MD = ["tasks_530.md", "tasks.md", "public.md"]
KB_FILES = [
    "multiturn_kb_530.json",
    "multiturn_kb_public.json",
    "ask_user_facts.json",
    "hallucination_controls.json",
]
VARS_FILES = [
    "public_vars.example.env",
    "public_vars.local.env",
    "tasks_vars.local.env",
    "tasks_vars.local.json",
]
TASKS_VARS_DIR = BENCH / "tasks_vars"
RECORD_FILES = [
    "fabricated-test-data.md",
    "public-task-feasibility.md",
]

README_TEMPLATE = """---
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

DrainBench is a benchmark harness that runs Android agent tasks against a **real
phone** (via ADB/mobilerun) and a real LLM, and grades the agent on reaching a
verifiable device end-state. This release ships the two task corpora plus
everything needed to reproduce a run: the source prompts, the knowledge bases,
the run-time variables, and a full disclosure of every piece of fabricated
test data.

## Datasets in this repo

| File | Content |
|---|---|
| `data/DailyBench_530_v1.json` / `.jsonl` | The **530-task** corpus (all tasks, 3-day-schedulable, by difficulty: Easy 1pt / Medium 3pt / Hard 5pt). |
| `data/DailyBench_public_v2.json` / `.jsonl` | The **61-task public 3-day sample** drawn from the 530 corpus plus public-sample-specific additions. |
| `data/tasks_530.md` | Human-readable source of the 530 corpus (canonical prompt text). |
| `data/tasks.md` | The wider task list (superset). |
| `data/public.md` | Human-readable source of the public sample. |
| `data/multiturn_kb_*.json` | Knowledge-base profiles for the **ASK USER - MULTI** tasks (what the simulated user knows, with rolling memory). |
| `data/ask_user_facts.json` | Facts for the **ASK USER SINGLE** tasks (one deliberately omitted fact). |
| `data/hallucination_controls.json` | Hallucination-control tasks (must not be fabricated). |

## Task model

A task is graded on a **verifiable device end-state**, not on an open-ended
LLM-judge rubric:

- **DETERMINISTIC** — everything the task needs is seeded on-device; the end
  state is ADB-verified.
- **ASK USER SINGLE** — one load-bearing fact is deliberately omitted; the agent
  must ask the simulated user and answer just what's asked.
- **ASK USER - MULTI** — a multi-turn dialogue against the KB profile; graded on
  acting on the correct target, with turn count as an efficiency signal.

Each task record carries `task_id` (e.g. `medium__google-maps__002`), the exact
`prompt_text`/`prompt_template`, placeholder slots, difficulty, and grading type.
Prompt text uses `[placeholder]` slots that resolve through the run-time
variables.

## Run-time variables (`.env` / `.local` / `config`)

All prompts use `[placeholder]` slots (e.g. `[contact]`, `[invoice file]`,
`[timer minutes]`). The values live in:

- `config/user.yaml` — persona/device values (auto-detected + overridable).
- `vars/public_vars.local.env` — public-sample variable values.
- `vars/tasks_vars.local.env` / `vars/tasks_vars.local.json` + `vars/tasks_vars/`
  — 530-corpus variable values (per task).

These are the **personal, device-specific values** used by the owner; clone them
and edit to match your own device/persona before running. The
`public_vars.example.env` file ships the documented defaults.

## Fabricated test data — full disclosure

To make deterministic tasks solvable, a controlled **fictional persona**
("Yuvraj Singh") and fabricated data were seeded on the device. Everything is
disclosed honestly:

- `fabrication/fabricated_test_data.json` — machine-readable inventory of every
  fabricated entity (what, where, task, how to remove).
- `fabrication/fabricated-test-data.md` — the full human-readable disclosure
  (design principles, per-app inventory, known gaps, revision history).
- `fabrication/public-task-feasibility.md` — per-task solvability audit.
- `fabrication/seeds/` — the regenerable public seed artifacts (the two
  realistic PDFs + the 8 enriched Obsidian notes).

No real phone numbers, personal emails, or real identities appear in the data;
all personas are fictional (see the disclosure's Privacy & Redaction section).

## Running the benchmark

The full harness (ADB driving, LLM proxy, Phoenix tracing, metrics) lives in the
companion code repo (DrainBench300). Reproducing a public run:

```bash
uv run python dailybench_tasks.py \\
  --dataset benchmarks/dailyBench-600/DailyBench_public_v2.json \\
  --source public.md --all --serial <device> \\
  --llm-upstream-base https://openrouter.ai/api --model <model> \\
  --temperature 0.0 --steps 200 --save-trajectory action \\
  --vars-file benchmarks/dailyBench-600/public_vars.local.env \\
  --ask-user-kb benchmarks/dailyBench-600/multiturn_kb_public.json \\
  --run-root public/<timestamp>
```

## Dataset record schema

Each JSON record includes (among others):

| Field | Description |
|---|---|
| `task_id` | Unique id, `<difficulty>__<app(s)>__<n>` |
| `prompt_text` | Rendered prompt (placeholders resolved). |
| `prompt_template` | Template with `{{ placeholder }}` slots. |
| `difficulty` | `easy` (1pt) / `medium` (3pt) / `hard` (5pt). |
| `is_ask_user` / grading fields | Deterministic vs ask-user (single/multi). |
| `app` / `day` | Target app(s) and schedule day. |
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage a Hugging Face release package for DrainBench.")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output staging directory.")
    ap.add_argument("--force", action="store_true", help="Replace an existing staging dir.")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"error: {out} already exists (use --force to replace)")
        return 1

    def copy(src: Path, rel: str) -> None:
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

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    print(f"staging to {out}")
    for f in DATASET_FILES:
        copy(BENCH / f, f"data/{f}")
    for f in SOURCE_MD:
        copy(BENCH / f, f"data/{f}")
    for f in KB_FILES:
        copy(BENCH / f, f"data/{f}")

    for f in VARS_FILES:
        copy(BENCH / f, f"vars/{f}")
    copy(TASKS_VARS_DIR, "vars/tasks_vars")
    copy(CONFIG / "user.yaml", "config/user.yaml")
    copy(CONFIG / "user_config.example", "config/user_config.example")

    copy(REPO_ROOT / ".fabricated_test_data.json", "fabrication/fabricated_test_data.json")
    for f in RECORD_FILES:
        copy(DOCS / f, f"fabrication/{f}")
    copy(SEEDS_PUBLIC, "fabrication/seeds")

    (out / "README.md").write_text(README_TEMPLATE, encoding="utf-8")
    print(f"  wrote README.md ({len(README_TEMPLATE)} bytes)")

    print(f"\nstaged {sum(1 for _ in out.rglob('*') if _.is_file())} files in {out}")
    print("next: hf auth login && huggingface-cli upload <repo> <out>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
