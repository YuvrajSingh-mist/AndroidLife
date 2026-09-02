# CLI reference

Full flag tables for the two harness entry points. See [README.md](../README.md) for the common quick-start commands.

## `dailybench_runner.py` — single-run harness

| Flag | Default | Meaning |
|---|---|---|
| `--serial` | `$DAILYBENCH_SERIAL` | ADB serial (USB device ID or `ip:port` for wireless) |
| `--label` | *(required)* | Run label; used directly as the run folder name (e.g. `easy-gmail-001`) |
| `--sample-interval` | `1.0` | Seconds between battery/thermal samples (1.0s = every second; 0.1s = every 100ms, heavier) |
| `--screen-bit-rate` | `8M` | `scrcpy` recording bit rate |
| `--screen-size` | *(none)* | `scrcpy` `--max-size` cap, if set |
| `--screen-record` | off | Record `screen.mp4` via `scrcpy` — **off by default** (a single task can produce 10–70MB of mp4, which adds real disk/CPU load); opt in when you need video evidence |
| `--llm-upstream-base` | *(none)* | Real model server base URL; when set, the harness starts a local logging proxy in front of it |
| `--llm-proxy-port` | `8090` | Preferred local proxy port (falls back to a free port if taken) |
| `--goal` | *(required)* | The task prompt/instruction for the agent |
| `--model` | `$MODEL` | Model name passed to the `MobileAgent`'s LLM |
| `--temperature` | `0.0` | Sampling temperature |
| `--top-p` | `0.95` | Nucleus sampling top-p, forwarded to the LLM request |
| `--seed` | `42` | Fixed sampling seed, forwarded to the LLM request, for run-to-run reproducibility |
| `--steps` | `50` | Step budget (`AgentConfig.max_steps`) |
| `--vision` | off | Enable vision: the agent sees the accessibility UI tree **plus** a screenshot on every step (mutually exclusive with `--vision-only`) |
| `--vision-only` | off | **Screenshots only**: drop the accessibility tree and drive from screenshots alone (mobilerun `vision_only`); the framework auto-enables the coordinate tools this mode requires. Implies `--vision` but without the UI tree (mutually exclusive with `--vision`) |
| `--reasoning` | off | Use mobilerun's manager/executor planning workflow instead of the fast-agent loop |
| `--thinking` | off | Leave the model's reasoning/thinking mode ON. Off by default: the harness sends reasoning-off switches (OpenRouter `reasoning.enabled=false` + Qwen `chat_template_kwargs.enable_thinking=false`) so reasoning models return text content; non-reasoning models ignore them |
| `--no-debug` | off | Disable mobilerun's verbose debug logging (on by default) |
| `--tracing` | off | Enable Arize Phoenix tracing (see [cli-reference.md](#tracing--phoenix)) |
| `--phoenix-url` | *(none)* | Phoenix collector endpoint; sets the `phoenix_url` env var mobilerun reads |
| `--phoenix-project` | *(none)* | Phoenix project name; sets the `phoenix_project_name` env var |
| `--save-trajectory` | `none` | Local trajectory recording level: `none`, `step`, or `action` |
| `--no-app-reset` | off | Skip the post-run fairness reset — leaves the app in whatever state the task ended in |
| `--task-timeout` | `0` | Wall-clock seconds before mobilerun's own `MobileAgent(timeout=...)` aborts the task. `0` = no wall-clock limit (the `--steps` step budget is the real bound) |
| `--ask-user-context` | *(empty)* | The hidden ground-truth fact for this task's `ask_user` tool (Hard/`ASK USER` tasks only — the dataset's `note` field); empty means the simulated user has nothing to reveal |
| `--ask-user-model` | `gpt-5.4-mini` | OpenAI model used to play the simulated user for `ask_user` — **OpenAI-hosted models only** (see note below) |
| `--ask-user-base-url` | *(OpenAI's default)* | Override the OpenAI API base URL for `ask_user` (e.g. to point at a local stand-in) |

> `ask_user` inherits the run's `--temperature`, `--top-p`, and `--seed` (it now sends them in the OpenAI call), so the simulated user is as reproducible as the main agent.

> **Note:** The `ask_user` simulated user (`--ask-user-model`, default `gpt-5.4-mini`) only supports **OpenAI-hosted models** — the `ask_user` tool calls the OpenAI API directly, and its per-1M-token cost table covers OpenAI models. It is a separate service from the agent's LLM (`--model`), which can be any model your LLM host (e.g. OpenRouter) serves.

## `dailybench_tasks.py` — dataset-backed batch runner

| Flag | Default | Meaning |
|---|---|---|
| `--dataset` | `benchmarks/dailyBench-600/DailyBench_530_v1.json` | Which exported task dataset to read |
| `--day` | *(none)* | Run every task whose schedule `day` equals `N` (any day 1..28 on the 530-task set). A selector on its own; combines with `--bucket`/`--app`/`--task-id` |
| `--bucket` | *(none)* | Filter to `easy`/`medium`/`hard`/`hard-deterministic`/`open-ended` (`hard` is the current dialect's shuffled DETERMINISTIC+ASK USER battery; `hard-deterministic`/`open-ended` are the older dialect's split buckets) |
| `--app` | *(none)* | Filter to one app slug (e.g. `gmail`) |
| `--task-id` | `[]` | Repeatable; run only these specific task IDs |
| `--var` | `[]` | Repeatable `key=value`; fills in `[placeholder]` values in task prompts |
| `--limit` | *(none)* | Cap the number of selected tasks |
| `--all` | off | Select every task in the dataset (required if no other selector is given) |
| `--list` | off | Print the selected tasks and exit, without running anything |
| `--dry-run` | off | Print the exact commands that would run, without executing them |
| `--skip-unresolved` | off | Skip (rather than error on) tasks whose placeholders have no `--var` value |
| `--serial` | `$DAILYBENCH_SERIAL` | ADB serial, forwarded to every task run |
| `--sample-interval` | `1.0` | Forwarded to each task run |
| `--llm-upstream-base` | `$LLM_UPSTREAM` | Forwarded to each task run |
| `--llm-proxy-port-base` | `8090` | First proxy port; each task/repeat invocation gets `base + running index` |
| `--model` | `$MODEL` | Model name, forwarded as `dailybench_runner.py --model` |
| `--temperature` | `0.0` | Sampling temperature |
| `--top-p` | `0.95` | Nucleus sampling top-p, forwarded to each task run (agent + `ask_user`) |
| `--seed` | `42` | Fixed sampling seed, forwarded to each task run (agent + `ask_user`), for run-to-run reproducibility |
| `--steps` | `50` | Fixed step budget for every task, regardless of bucket (see [Step-budget policy](#step-budget-policy)) |
| `--repeats` | `1` | Run each selected task this many times; opt-in since runs are already deterministic at temperature 0 (see caveat below) |
| `--screen-record` | off | Record `screen.mp4` for every task in the batch — **off by default** (see single-run flag for why); opt in when you need video evidence |
| `--vision` | off | Enable vision: the agent sees the accessibility UI tree **plus** a screenshot on every step (mutually exclusive with `--vision-only`) |
| `--vision-only` | off | **Screenshots only**: drop the accessibility tree and drive from screenshots alone (mobilerun `vision_only`); the framework auto-enables the coordinate tools this mode requires. Implies `--vision` but without the UI tree (mutually exclusive with `--vision`) |
| `--reasoning` | off | Use mobilerun's manager/executor planning workflow instead of the fast-agent loop |
| `--thinking` | off | Leave the model's reasoning/thinking mode ON (default off: reasoning-off switches sent via `extra_body`) |
| `--no-debug` | off | Disable mobilerun's verbose debug logging (on by default) |
| `--tracing` | off | Enable Arize Phoenix tracing (needs `phoenix serve` running first) |
| `--phoenix-url` | *(none)* | Phoenix collector endpoint; sets the `phoenix_url` env var |
| `--phoenix-project` | *(none)* | Phoenix project name; sets the `phoenix_project_name` env var |
| `--save-trajectory` | `none` | Local trajectory recording level: `none`, `step`, or `action` |
| `--no-app-reset` | off | Skip the post-run fairness reset for every task in the batch (see below) |
| `--cooldown-seconds` | `10.0` | Fixed pause between tasks so the device doesn't run continuously into thermal/load territory; `0` disables it |
| `--source` | `tasks.md` | Task source markdown the dataset was exported from; selects the ask_user_facts sidecar with fallback per-`task_id` facts for Hard/`ASK USER` tasks (`tasks.md` -> `ask_user_facts_730.json`, `public.md` -> `ask_user_facts.json`); used only when a task's own dataset row has no `ask_user_fact`; a missing file means no facts configured (fine for DETERMINISTIC-only selections) |
| `--ask-user-model` | `gpt-5.4-mini` | Forwarded to every task run's `ask_user` tool — **OpenAI-hosted models only** (see note above) |
| `--ask-user-base-url` | *(OpenAI's default)* | Forwarded to every task run's `ask_user` tool |
| `--run-root` | *(none)* | Continue into an existing run folder root (e.g. `assets/runs/public/20260901-002701`) instead of creating a fresh dated folder. **Pair with `--resume-from` to continue an interrupted batch in place.** |
| `--resume-from` | `TASK_ID` | Skip every selected task whose `task_id` sorts before `TASK_ID` and start at `TASK_ID` (inclusive) — resumes an interrupted batch without re-running earlier tasks. Prints "Resuming batch at <id>". |

### Long-running batches (detached) & resume

For full multi-hour runs, launch the batch **detached** so it survives terminal cleanup —
a plain `nohup ... &` dies with `Fatal Python error: init_sys_streams ... Bad file descriptor`
when the launching terminal closes (stdin becomes invalid). **Always redirect stdin from
`/dev/null`:**

```bash
nohup uv run dailybench_tasks.py --dataset ... --all --serial ... \
  --model <model> --save-trajectory action \
  --run-root "assets/runs/public/<TS>" \
  < /dev/null > "assets/runs/public/batch-<TS>.log" 2>&1 &
```

If a detached batch dies mid-run, **resume in place** (same run-root, no re-runs):

```bash
uv run dailybench_tasks.py --dataset ... --all --serial ... \
  --model <model> --save-trajectory action \
  --run-root "assets/runs/public/<TS>" --resume-from "<next-task-id>" \
  < /dev/null > "assets/runs/public/resume-<TS>.log" 2>&1 &
```

Find the next task id from the dead batch's log: it echoes every `label dayN--...`
command in run order; the first label with no `output.json` in its folder is the resume point
(the batch died while spawning it). Aliveness checks: `pgrep -af dailybench`,
`lsof -nP -iTCP:<task proxy port>`, and the active `agent.log.txt` mtime advancing.

### Model compatibility notes (2026-09-01)

The harness sends **reasoning-off** by default (`extra_body` with OpenRouter
`reasoning.enabled=false` + Qwen `enable_thinking=false`). Known behaviors:

| Model (OpenRouter) | reasoning | Works? | Notes |
|---|---|---|---|
| `bytedance-seed/seed-2.0-lite` | optional | ✅ | Proven good XML; last full run 51.7%. |
| `qwen/qwen3.8-27b` | optional | ✅ | Text + vision modes both work. |
| `moonshotai/kimi-k2.6` | optional | ✅ | Historically tested. |
| `stepfun/step-3.7-flash` | **mandatory** | ⚠️ | `reasoning.mandatory: True` → reasoning-off **400s** every call. Must launch with `--thinking` (verified HTTP 200). |
| `xiaomi/mimo-v2.5-pro` | optional | ⚠️ | Drives the device well but emits **malformed `<parameter=message>`** on the final `complete` call → strict XML parser rejects it → every task grades `success: False` at the last step (diagnostic only; do not use for a scoring run unless the parser is made tolerant). |

To leave reasoning ON for a mandatory-reasoning model, pass `--thinking` (forwarded through
the batch wrapper since 2026-09-01). Manual audit remains ground truth over self-reported
success. `--run-root`/`--resume-from` are the in-place resume pair for interrupted batches.

### App-reset fairness

After each task finishes, the harness force-stops whatever app ended up in the foreground (`am force-stop`) and returns to the home screen, before writing the run's final artifacts. Without this, a task can silently inherit UI/navigation state left behind by the previous task's agent (mid-scroll in Gmail, a half-typed compose draft, a different app entirely) instead of starting clean. It's on by default; the launcher, systemui, and mobilerun's own Portal app are never touched. The stopped package (or `null` if nothing eligible was in the foreground) is recorded in `meta.json` as `app_reset_stopped_package`. A reset failure is logged but never fails the run.

### Repeats caveat

`--repeats` re-runs the identical task back-to-back against a live, stateful mailbox/app. It's fully valid for hardware metrics (thermals, battery), but for destructive or state-toggling tasks (delete, archive, mark read/unread, send/reply), reps after the first face a different starting state than rep 1 — treat repeat-based success rates on those tasks with caution.

### Step-budget policy

- Default action budget: `50` steps for every task.
- This is intentionally fixed across easy, medium, hard-deterministic, and open-ended buckets.
- The benchmark uses one global action budget to avoid bucket-specific budget advantages.
