"""CLI entrypoint for one DailyBench run: drives the mobilerun MobileAgent SDK directly."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import socket
import sqlite3
import time
from pathlib import Path
from urllib.request import urlopen

from dotenv import load_dotenv
from llama_index.llms.openai_like import OpenAILike
from mobilerun import AgentConfig, DeviceConfig, FastAgentConfig, LoggingConfig, MobileAgent, MobileConfig, TracingConfig

from .adb import capture_app_battery, capture_sample, read_jsonl, reset_app_state, utc_now
from .custom_tools import CUSTOM_TOOLS, DEFAULT_ASK_USER_MODEL, build_ask_user_tool
from .files import default_batch_run_dir, run_dir_for_label, write_json, write_text
from .processes import ProxyStartupError, start_llm_proxy, start_scrcpy, stop_process, wait_for_proxy_ready
from .sampler import Sampler
from .summary import TaskOutcome, summarize, summarize_app_battery

load_dotenv()  # picks up .env from the repo root (or any parent dir) - see README's Setup section

FAST_AGENT_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "fast_agent_system.jinja2").read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the DailyBench CLI parser."""
    parser = argparse.ArgumentParser(description="Run one benchmarked mobilerun task with device and LLM metrics.")
    parser.add_argument("--serial", default=os.environ.get("DAILYBENCH_SERIAL"))
    parser.add_argument("--label", required=True)
    parser.add_argument("--task-id", default=None, help="Dataset task_id this run corresponds to (recorded in meta.json for batch reporting).")
    parser.add_argument("--sample-interval", type=float, default=1.0, help="Seconds between battery/thermal samples (1.0 = every second; 0.1 = every 100ms, heavier).")
    parser.add_argument("--screen-bit-rate", default="8M")
    parser.add_argument("--screen-size", default=None)
    parser.add_argument("--screen-record", action="store_true", help="Record screen.mp4 via scrcpy (OFF by default — saves significant disk/CPU; a single task can produce 10-70MB of mp4).")
    parser.add_argument("--llm-upstream-base", default=None)
    parser.add_argument("--llm-proxy-port", type=int, default=8090)
    parser.add_argument("--goal", required=True, help="The task prompt/instruction for the agent.")
    parser.add_argument("--var", action="append", default=[], help="Resolved task variable as key=value; passed to mobilerun's native custom_variables (rendered in the system prompt + readable by custom tools via ctx.shared_state.custom_variables).")
    parser.add_argument("--model", default=os.environ.get("MODEL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--task-timeout", type=int, default=0, help="Wall-clock seconds before mobilerun's own MobileAgent(timeout=...) aborts the task. 0 = no wall-clock limit (default): the --steps step budget is the real bound.")
    parser.add_argument("--vision", action="store_true", help="Enable vision (screenshots) for the agent; off by default for this harness.")
    parser.add_argument("--reasoning", action="store_true", help="Use mobilerun's manager/executor planning workflow instead of the fast-agent loop.")
    parser.add_argument("--thinking", action="store_true", help="Leave the model's reasoning/thinking mode ON. OFF by default (the fast-agent loop needs immediate text content, and hidden reasoning burns tokens + breaks determinism): when off, the harness sends reasoning-off switches (OpenRouter `reasoning.enabled=false` + Qwen `chat_template_kwargs.enable_thinking=false`) for whichever the model/host honors.")
    parser.add_argument("--no-debug", action="store_true", help="Disable mobilerun's verbose debug logging (on by default).")
    parser.add_argument("--no-tracing", action="store_true", help="Disable Arize Phoenix tracing (ON by default; needs `phoenix serve` running locally, see docs.mobilerun.ai/framework/features/tracing).")
    parser.add_argument("--phoenix-url", default="http://localhost:6006", help="Phoenix collector endpoint (sets the `phoenix_url` env var mobilerun reads; default local Phoenix on :6006).")
    parser.add_argument("--phoenix-project", default="dailybench", help="Phoenix project name to group traces under (sets the `phoenix_project_name` env var).")
    parser.add_argument("--phoenix-db", default=None, help="Path to the Phoenix SQLite DB file to stamp this run's model onto the matching trace (e.g. assets/db/day3/phoenix.db). When omitted but --phoenix-project is `dailybench-dayN`, the DB is auto-derived as assets/db/dayN/phoenix.db. Stamping is best-effort and never fails the run.")
    parser.add_argument("--save-trajectory", choices=["none", "step", "action"], default="action", help="Local trajectory recording level: none, step (per agent step), or action (per atomic action); default action.")
    parser.add_argument("--no-app-reset", action="store_true", help="Skip force-stopping the foreground app and returning home after the run (on by default, for fairness so the next task doesn't inherit this task's UI/navigation state).")
    parser.add_argument("--ask-user-context", default="", help="The hidden ground-truth fact for this task's ask_user tool (Hard/ASK USER tasks only - see the dataset's 'note'/'ask_user_fact' fields). Empty means the simulated user has nothing to reveal.")
    parser.add_argument("--ask-user-kb", default="", help="Path to a JSON knowledge-base profile for the simulated user (multi-turn mode): the user answers whatever the agent asks, from the profile, with rolling memory across turns. When set, takes precedence over --ask-user-context.")
    parser.add_argument("--ask-user-model", default=DEFAULT_ASK_USER_MODEL, help="OpenAI model used to play the simulated user for the ask_user tool.")
    parser.add_argument("--run-root", default=None, help="Optional shared run directory created by the batch; the task's run folder is created inside it (instead of assets/runs/full-bench/<timestamp>/<label>).")
    return parser


def parse_vars(items: list[str]) -> dict[str, str]:
    """Parse repeated `key=value` CLI items into a dictionary (mobilerun custom variables)."""
    values: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--var expects key=value, got: {item}")
        key, value = item.split("=", 1)
        values[key.strip()] = value
    return values


def build_mobile_config(args: argparse.Namespace, run_dir: Path) -> MobileConfig:
    """Translate DailyBench CLI flags into one MobileConfig, with trajectories pinned inside run_dir."""
    return MobileConfig(
        device=DeviceConfig(serial=args.serial),
        agent=AgentConfig(max_steps=args.steps, reasoning=args.reasoning, fast_agent=FastAgentConfig(vision=args.vision)),
        logging=LoggingConfig(debug=not args.no_debug, save_trajectory=args.save_trajectory, trajectory_path=str(run_dir / "trajectories")),
        tracing=TracingConfig(enabled=not args.no_tracing),
    )


class _StreamAwareFileHandler(logging.FileHandler):
    """Collapses mobilerun's token-by-token stream log records (extra={"stream": True}) into one
    line per LLM response, instead of one timestamped log line per token (the default FileHandler
    behavior, which turned a handful of agent responses into thousands of near-empty lines).
    """

    def __init__(self, path: Path, encoding: str = "utf-8") -> None:
        super().__init__(path, encoding=encoding)
        self._streaming = False

    def emit(self, record: logging.LogRecord) -> None:
        if getattr(record, "stream", False):
            if not self._streaming:
                self.stream.write(self._prefix(record))
                self._streaming = True
            self.stream.write(str(record.msg))
            self.flush()
            return
        if getattr(record, "stream_end", False):
            if self._streaming:
                self.stream.write("\n")
                self.flush()
                self._streaming = False
            return
        if self._streaming:
            self.stream.write("\n")
            self._streaming = False
        super().emit(record)

    @staticmethod
    def _prefix(record: logging.LogRecord) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        return f"{timestamp},{int(record.msecs):03d} {record.levelname} {record.name}: "


def attach_agent_log_file(path: Path) -> logging.Handler:
    """Attach a per-run file handler to mobilerun's logger, capturing this run's agent log to disk."""
    handler = _StreamAwareFileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger("mobilerun").addHandler(handler)
    return handler


async def run_agent(args: argparse.Namespace, run_dir: Path, api_base: str) -> TaskOutcome:
    """Build one MobileAgent against the local logging proxy and run it to completion."""
    if args.phoenix_url:
        os.environ["phoenix_url"] = args.phoenix_url
    if args.phoenix_project:
        os.environ["phoenix_project_name"] = args.phoenix_project
    llm = OpenAILike(
        model=args.model,
        api_base=api_base,
        # The local proxy forwards this to --llm-upstream-base. A local llama-server
        # ignores auth, so "sk-DailyBench-local" is a safe fallback; a real authenticated
        # upstream (OpenRouter) needs OPENROUTER_API_KEY set in .env. OPENAI_API_KEY is
        # NOT a fallback here — it belongs to the ask_user tool, a completely separate service.
        api_key=os.environ.get("OPENROUTER_API_KEY", "sk-DailyBench-local"),
        temperature=args.temperature,
        is_chat_model=True,
        additional_kwargs={
            "top_p": args.top_p,
            "seed": args.seed,
            # ONE reasoning-off mechanism for model swap: the `--thinking` flag
            # (off by default). When off, extra_body carries both switches so it
            # works on any host the model runs through:
            #  (1) "reasoning": {"enabled": false} — OpenRouter's NATIVE param
            #      (confirmed live on qwen/qwen3.7-flash: clean content, no
            #      reasoning tokens). Self-hosted servers ignore it.
            #  (2) "chat_template_kwargs.enable_thinking" — the model's OWN
            #      chat-template switch for self-hosted Qwen3-family thinking
            #      models (e.g. mini2's local Qwen3-4B), where OpenRouter's
            #      `reasoning` param isn't in play. Confirmed live: 226 reasoning
            #      tokens dropped to 0, output reproducible with a fixed seed.
            # Both are sent together because the OpenAI SDK only forwards unknown
            # params via extra_body (a top-level `reasoning` kwarg raises
            # "got an unexpected keyword argument"). Non-reasoning models ignore
            # both fields. Pass --thinking to leave reasoning ON (no switches).
            "extra_body": (
                {} if args.thinking else {
                    "reasoning": {"enabled": False},
                    "chat_template_kwargs": {"enable_thinking": False},
                }
            ),
        },
    )
    # The ask_user tool is registered ONLY for ASK USER tasks (--ask-user-context non-empty).
    # Its simulated user holds only that task's hidden fact; on every other task it would have
    # nothing to reveal, so exposing it there only tempts the agent to "ask" instead of either
    # finding the data on-device or honestly reporting it absent (the correct outcome for a
    # hallucination control). The model decides on its own when to call ask_user from the tool's
    # own description (which instructs it to search the device first and ask only when the fact is
    # genuinely absent) — the system prompt does not announce that a task is an ASK USER task.
    custom_tools = dict(CUSTOM_TOOLS)
    # Multi-turn KB mode takes precedence: if --ask-user-kb points to a JSON profile,
    # the simulated user becomes an honest oracle over it with rolling memory.
    kb: dict | None = None
    if args.ask_user_kb:
        import json as _json
        kb = _json.loads(open(args.ask_user_kb).read())
        # Multi-turn KB mode: hand the simulated user ONLY this task's profile
        # (the file may hold many tasks' data), so the oracle knows just what it
        # needs for this run - never the grader's correct_target.
        if args.task_id and isinstance(kb, dict):
            entry = kb.get(args.task_id)
            kb = entry.get("profile", entry) if isinstance(entry, dict) else None
    if args.ask_user_context or kb is not None:
        # Truncate the ask_user log at run start so a merge-drill rerun into an existing
        # run root doesn't carry stale ask_user entries from a previous run (the tool appends
        # per call; run_metrics counts lines in this file, so stale lines would corrupt the
        # latest run's ask_user_call_count).
        (run_dir / "ask_user_metrics.jsonl").write_text("")
        custom_tools.update(
            build_ask_user_tool(
                args.ask_user_context,
                kb=kb,
                model=args.ask_user_model,
                log_path=run_dir / "ask_user_metrics.jsonl",
                temperature=args.temperature,
                top_p=args.top_p,
                seed=args.seed,
            )
        )
    # 0 means "no wall-clock cap". The FastAgent loop's MobileAgentInitEvent requires an int
    # timeout (None fails pydantic validation: "Input should be a valid integer"), so we pass
    # a 100-year deadline instead of None — effectively no wall-clock limit. The step budget
    # (--steps) is the real bound. Every bucket comes through as --task-timeout 0 from the
    # batch runner.
    NO_WALL_CLOCK_TIMEOUT_SECONDS = 60 * 60 * 24 * 365 * 100  # 100 years ≈ no cap
    timeout = NO_WALL_CLOCK_TIMEOUT_SECONDS if args.task_timeout == 0 else args.task_timeout
    agent = MobileAgent(
        goal=args.goal,
        config=build_mobile_config(args, run_dir),
        llms=llm,
        variables=parse_vars(args.var),  # mobilerun-native custom_variables
        prompts={"fast_agent_system": FAST_AGENT_SYSTEM_PROMPT},
        custom_tools=custom_tools,
        timeout=timeout,
    )
    handler = attach_agent_log_file(run_dir / "agent.log.txt")
    try:
        result = await agent.run()
        return TaskOutcome(success=result.success, reason=result.reason, steps=result.steps)
    except Exception as exc:  # noqa: BLE001 - a failed task run must still produce a run folder, not crash the batch
        return TaskOutcome(success=False, reason=f"mobilerun agent raised: {exc}", steps=0)
    finally:
        logging.getLogger("mobilerun").removeHandler(handler)
        handler.close()


def _phoenix_db_from_project(project: str | None) -> Path | None:
    """Derive the Phoenix SQLite DB path from a `dailybench-dayN` project name.

    Returns ``assets/db/dayN/phoenix.db`` for ``dailybench-dayN``, else None (no
    deterministic mapping). Used to stamp this run's model onto its trace when the
    user didn't pass an explicit ``--phoenix-db``.
    """
    if not project:
        return None
    m = re.fullmatch(r"dailybench-day(\d+)", project)
    if not m:
        return None
    return Path(__file__).resolve().parents[2] / "assets" / "db" / f"day{m.group(1)}" / "phoenix.db"


def check_phoenix_ready(url: str, warn_only: bool = False) -> bool:
    """Pre-run guard: confirm the Phoenix collector is actually reachable.

    The mobilerun SDK silently drops traces when ``phoenix serve`` is not running
    (traces are sent on port 4317, dashboard on :6006). This guard fails fast so a
    run never silently loses its trace data. ``url`` is the ``--phoenix-url`` (e.g.
    ``http://localhost:6006``); when warn_only we log a loud warning instead of
    returning failure (used by paths that intentionally pass a remote collector).
    Returns True when the collector looks reachable.
    """
    if not url:
        return True
    try:
        host = re.sub(r"^https?://", "", url).split(":")[0]
        port = int(re.sub(r"^https?://", "", url).split(":")[1]) if ":" in re.sub(r"^https?://", "", url) else 6006
    except (ValueError, IndexError):
        host, port = "localhost", 6006
    # Phoenix serves both the dashboard (HTTP :6006) and the OTLP/gRPC collector
    # (:4317 by default). Reaching the dashboard is a good proxy for "server up".
    reachable = False
    try:
        with urlopen(f"http://{host}:{port}", timeout=2.0) as resp:  # noqa: S310 - local collector health check
            reachable = resp.status < 500
    except Exception:  # noqa: BLE001
        reachable = False
    if not reachable:
        try:
            with socket.create_connection((host, 4317), timeout=2.0):
                reachable = True
        except OSError:
            reachable = False
    if reachable:
        logging.getLogger("mobilerun").info("phoenix collector reachable at %s (traces will be captured)", url)
        return True
    msg = f"Phoenix collector NOT reachable at {url} — run will silently lose trace data. Start `phoenix serve` first (see README)."
    if warn_only:
        logging.getLogger("mobilerun").warning("WARNING: %s", msg)
        return False
    logging.getLogger("mobilerun").error("ABORTING run: %s", msg)
    return False


def stamp_model_on_phoenix_trace(db_path: Path, model: str, start_utc: str, end_utc: str) -> None:
    """Best-effort: set ``traces.model`` for the trace(s) overlapping this run's time window.

    The Phoenix collector (mobilerun) writes the trace with a ``start_time`` inside
    [run start, run end]; update any matching row whose model is NULL. Never raises:
    a stamping failure must not lose an otherwise-successful run. ``start_utc`` /
    ``end_utc`` are ISO-8601 UTC strings from the run's meta.json.
    """
    if db_path is None or not db_path.exists() or not model:
        return
    try:
        from datetime import datetime, timezone

        start = datetime.fromisoformat(start_utc.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        end = datetime.fromisoformat(end_utc.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(str(db_path))
        try:
            # Ensure the model column exists (older DBs), then stamp the matching trace.
            cols = [r[1] for r in conn.execute("PRAGMA table_info(traces)")]
            if "model" not in cols:
                conn.execute("ALTER TABLE traces ADD COLUMN model TEXT")
            conn.execute(
                "UPDATE traces SET model=? WHERE start_time BETWEEN ? AND ? AND model IS NULL",
                (model, start, end),
            )
            conn.commit()
        finally:
            conn.close()
        logging.getLogger("mobilerun").debug("stamped model %r on phoenix trace(s) in %s", model, db_path)
    except Exception:  # noqa: BLE001 - best-effort stamping must never break the run
        logging.getLogger("mobilerun").debug("phoenix model stamping skipped for %s", db_path)


def main() -> int:
    """Run one fully instrumented benchmark task and write one run folder."""
    args = build_parser().parse_args()
    if not args.serial:
        raise SystemExit("ADB serial required via --serial or DAILYBENCH_SERIAL")
    if not args.model:
        raise SystemExit("Model required via --model or MODEL")
    # Fail early when API keys are missing, so the user doesn't waste 30 min on a task
    # that will fail on the first LLM call with an auth error.
    if args.llm_upstream_base and "openrouter" in args.llm_upstream_base.lower():
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise SystemExit(
                "OPENROUTER_API_KEY required in .env when using OpenRouter. "
                "Set it or point --llm-upstream-base at a local model server that doesn't require auth."
            )
    if args.ask_user_context and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY required in .env for Hard/ASK USER tasks "
            "(the ask_user tool calls OpenAI's GPT). Set it or omit --ask-user-context."
        )
    if args.run_root:
        run_dir = run_dir_for_label(args.run_root, args.label)
        run_dir.mkdir(parents=True, exist_ok=True)
        run_dir = run_dir.resolve()
    else:
        run_dir = run_dir_for_label(default_batch_run_dir(), args.label)
        run_dir.mkdir(parents=True, exist_ok=True)
        run_dir = run_dir.resolve()
    meta = {
        "run_id": run_dir.name, "label": args.label, "task_id": args.task_id, "serial": args.serial, "started_at_utc": utc_now(),
        "goal": args.goal, "variables": parse_vars(args.var), "model": args.model, "steps": args.steps, "task_timeout_seconds": args.task_timeout, "sample_interval_seconds": args.sample_interval,
        "temperature": args.temperature, "top_p": args.top_p, "seed": args.seed,
    }
    write_json(run_dir / "meta.json", meta)
    preflight = capture_sample(args.serial)
    preflight["app_battery_mah"] = capture_app_battery(args.serial)
    write_json(run_dir / "preflight.json", preflight)
    llm_entries: list[dict] = []
    llm_proxy = None
    api_base = f"http://127.0.0.1:{args.llm_proxy_port}/v1"
    if args.llm_upstream_base:
        try:
            llm_proxy, port, llm_log = start_llm_proxy(run_dir, args.llm_upstream_base, args.llm_proxy_port)
            wait_for_proxy_ready(port)
        except (ProxyStartupError, TimeoutError) as exc:
            write_text(run_dir / "PROXY_STARTUP_FAILED", str(exc))
            logging.error("ABORTING run: LLM proxy did not become ready. %s", exc)
            return 2
        api_base = f"http://127.0.0.1:{port}/v1"
        meta.update({"llm_proxy_port": port, "llm_proxy_base": api_base, "llm_proxy_upstream_base": args.llm_upstream_base, "llm_log_jsonl": str(llm_log)})
        write_json(run_dir / "meta.json", meta)
    recording = start_scrcpy(args.serial, run_dir, args.screen_bit_rate, args.screen_size) if args.screen_record else None
    sampler = Sampler(args.serial, args.sample_interval, run_dir / "samples.ndjson")
    sampler.start()
    # Phoenix pre-run guard: if tracing is on but the collector is down, fail fast
    # instead of silently dropping all trace data (day-4 2026-08-13 lost its traces
    # because `phoenix serve` was never started for the day).
    if not args.no_tracing and not check_phoenix_ready(args.phoenix_url):
        write_text(run_dir / "PHOENIX_NOT_READY", f"phoenix not reachable at {args.phoenix_url}")
        logging.error("ABORTING run: Phoenix collector down at %s — start `phoenix serve` for this day first.", args.phoenix_url)
        return 3
    start_monotonic = time.monotonic()
    outcome = asyncio.run(run_agent(args, run_dir, api_base))
    elapsed = time.monotonic() - start_monotonic
    return_code = 0 if outcome.success else 1
    sampler.stop()
    if recording is not None:
        meta["screenrecord_exit_code"] = stop_process(recording, sigint=True)
    if llm_proxy is not None:
        meta["llm_proxy_exit_code"] = stop_process(llm_proxy)
        llm_entries = read_jsonl(meta["llm_log_jsonl"], 0)
        write_json(run_dir / "llm_metrics.json", llm_entries)
    postflight = capture_sample(args.serial)
    postflight["app_battery_mah"] = capture_app_battery(args.serial)
    write_json(run_dir / "postflight.json", postflight)
    app_reset_stopped_package = None
    if not args.no_app_reset:
        try:
            app_reset_stopped_package = reset_app_state(args.serial)
        except Exception:  # noqa: BLE001 - the fairness reset is best-effort; a failure here must not lose an otherwise-successful run
            pass
    meta.update({
        "ended_at_utc": utc_now(), "elapsed_seconds": elapsed, "command_exit_code": return_code,
        "sampler_errors": sampler.errors, "app_reset_stopped_package": app_reset_stopped_package,
    })
    write_json(run_dir / "meta.json", meta)
    write_text(run_dir / "output.txt", outcome.reason)
    write_json(run_dir / "output.json", outcome.model_dump())
    summary = summarize(sampler.samples, meta, llm_entries)
    summary["ask_user_call_count"] = len(read_jsonl(run_dir / "ask_user_metrics.jsonl", 0))
    summary["app_battery"] = summarize_app_battery(preflight, postflight)
    write_json(run_dir / "run_metrics.json", summary)
    # Future-proofing: stamp this run's model onto its Phoenix trace (best-effort).
    # `--phoenix-db` wins; otherwise auto-derive from `--phoenix-project` (dailybench-dayN).
    if not args.no_tracing and args.phoenix_url:
        phoenix_db = Path(args.phoenix_db) if args.phoenix_db else _phoenix_db_from_project(args.phoenix_project)
        stamp_model_on_phoenix_trace(
            phoenix_db, args.model,
            meta.get("started_at_utc", ""), meta.get("ended_at_utc", ""),
        )
    print(f"Run directory: {run_dir}")
    print((run_dir / "run_metrics.json").read_text())
    return return_code
