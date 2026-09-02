#!/usr/bin/env python3
"""One-command setup / onboarding for DrainBench on a new machine + phone."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

ENV_EXAMPLE = REPO_ROOT / ".env.example"
ENV_PATH = REPO_ROOT / ".env"
CONFIG_EXAMPLE = REPO_ROOT / "config" / "user_config.example"
CONFIG_PATH = REPO_ROOT / "config" / "user.yaml"

STAGES = ["prerequisites", "deps", "env", "config", "device", "manifests", "day-vars", "seed", "verify"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def sh(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("  $ " + " ".join(cmd))
    return subprocess.run(cmd, check=check, text=True)


def stage(name: str) -> None:
    print(f"\n=== [{name}] ===")


def run_uv(args: list[str]) -> subprocess.CompletedProcess[str]:
    return sh(["uv", "run", *args])


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------
def s_prerequisites(opts) -> int:
    stage("prerequisites")
    ok = True
    for tool in ("adb", "scrcpy", "uv", "python3"):
        path = shutil.which(tool)
        print(f"  {tool}: {path or 'MISSING'}")
        ok = ok and path is not None
    # python version
    res = subprocess.run(["python3", "--version"], capture_output=True, text=True)
    print("  python3 --version:", (res.stdout or res.stderr).strip())
    return 0 if ok else 1


def s_deps(opts) -> int:
    stage("deps")
    run_uv(["sync", "--extra", "dev", "--extra", "tracing", "--extra", "hf"])
    return 0


def s_env(opts) -> int:
    stage("env")
    if ENV_PATH.exists():
        print(f"  .env already exists ({ENV_PATH}) - leaving it alone. Edit it to add API keys.")
        return 0
    shutil.copy(ENV_EXAMPLE, ENV_PATH)
    print(f"  scaffolded {ENV_PATH} from .env.example - add your API keys (OPENAI_API_KEY for the "
          "ask_user tool, OPENROUTER_API_KEY if using OpenRouter).")
    return 0


def s_config(opts) -> int:
    stage("config")
    if CONFIG_PATH.exists():
        print(f"  config/user.yaml already exists - leaving it alone.")
    else:
        shutil.copy(CONFIG_EXAMPLE, CONFIG_PATH)
        print(f"  scaffolded {CONFIG_PATH} from the committed example persona.")
    # verify it resolves
    run_uv(["run", "python", "scripts/seeding/verify_config.py"])  # uses REPO_ROOT cwd
    return 0


def _pick_serial(opts) -> str | None:
    if opts.serial:
        return opts.serial
    res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    devs = [ln.split("\t")[0] for ln in res.stdout.splitlines()
            if "\tdevice" in ln]
    if not devs:
        return None
    if len(devs) == 1:
        return devs[0]
    print("  multiple devices:", ", ".join(devs))
    return None


def s_device(opts) -> int:
    stage("device")
    serial = _pick_serial(opts)
    if serial is None:
        print("  no (single) ADB device found - plug the phone in (USB) or pair wireless, then retry.")
        print("  You can pass --serial <id> to pick one explicitly.")
        return 1
    print(f"  serial: {serial}")
    # quick connectivity
    res = subprocess.run(["adb", "-s", serial, "shell", "echo", "OK"], capture_output=True, text=True)
    if "OK" not in res.stdout:
        print(f"  device not reachable: {res.stdout}{res.stderr}")
        return 1
    print("  adb reachable.")
    # app audit
    app_audit = REPO_ROOT / "scripts" / "tools" / "app_audit.py"
    subprocess.run(["uv", "run", "python", str(app_audit), "--serial", serial])
    return 0


def s_manifests(opts) -> int:
    stage("manifests")
    days = opts.days if opts.days else [1, 2, 3, 4, 5, 6]
    for d in days:
        run_uv(["run", "python", "scripts/seeding/build_day_seed_manifest.py", "--day", str(d)])
    return 0


def s_day_vars(opts) -> int:
    stage("day-vars")
    run_uv(["run", "python", "scripts/seeding/generate_day_vars.py", "--all"])
    return 0


def s_seed(opts) -> int:
    stage("seed")
    serial = opts.serial or _pick_serial(opts)
    if not serial:
        print("  no ADB device found - pass --serial or plug in the phone.")
        return 1
    days = opts.days if opts.days else [opts.day]
    for d in days:
        run_uv(["run", "python", "scripts/seeding/seed_data.py", "--serial", serial, "--day", str(d)])
    return 0


def s_verify(opts) -> int:
    stage("verify")
    serial = opts.serial or _pick_serial(opts)
    if not serial:
        print("  no ADB device found - pass --serial or plug in the phone.")
        return 1
    days = opts.days if opts.days else [opts.day]
    for d in days:
        run_uv(["run", "python", "scripts/seeding/seed_data.py", "--serial", serial, "--day", str(d), "--verify"])
    return 0


STAGE_FNS = {
    "prerequisites": s_prerequisites,
    "deps": s_deps,
    "env": s_env,
    "config": s_config,
    "device": s_device,
    "manifests": s_manifests,
    "day-vars": s_day_vars,
    "seed": s_seed,
    "verify": s_verify,
}

# The full guided flow, in order. `seed`/`verify` use the default day unless
# overridden (they need a device; the rest don't).
FULL_FLOW = ["prerequisites", "deps", "env", "config", "device", "manifests", "day-vars"]


def main() -> int:
    ap = argparse.ArgumentParser(description="One-command DrainBench setup / onboarding.")
    ap.add_argument("stages", nargs="*", choices=STAGES + ["all"],
                    help="Stages to run (default: full guided flow = " + " ".join(FULL_FLOW) + " + seed/verify for --day).")
    ap.add_argument("--day", type=int, default=1, help="Day for seed/verify stages (default 1).")
    ap.add_argument("--days", type=int, nargs="*", help="Explicit day list for manifests/seed/verify (overrides --day).")
    ap.add_argument("--serial", default=None, help="ADB serial (default: auto-detect).")
    ap.add_argument("--yes", action="store_true", help="Run the full flow non-interactively (no device prompts).")
    args = ap.parse_args()

    if args.stages:
        wanted: list[str] = []
        for s in args.stages:
            wanted.extend(STAGES if s == "all" else [s])
    else:
        # full flow: everything except seed/verify unless a device-focused run
        # is requested via --day. Keep it safe: seed/verify are opt-in even in
        # the full flow (they mutate the device), but if the user passed --days
        # explicitly we assume they want seeding too.
        wanted = list(FULL_FLOW)
        if args.days is not None:
            wanted += ["seed", "verify"]

    rc = 0
    for s in wanted:
        if s in ("seed", "verify") and not args.yes and not args.days:
            print(f"\n=== [{s}] skipped (mutates the device; run explicitly: "
                  f"uv run python scripts/setup.py {s} --day {args.day} --serial <id> ===")
            continue
        rc = rc or STAGE_FNS[s](args)
    print("\nSetup complete.")
    print("Next: start Phoenix (see README Tracing), then:")
    print("  uv run python scripts/run/run_day.py --day 1 --dry-run   # preview")
    print("  uv run python scripts/run/run_day.py --day 1             # run Day 1")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
