# Leaderboard Format

Recommended columns for published results:

- model
- server/runtime
- vision on/off
- reasoning on/off
- deterministic success rate
- open-ended rubric score
- average elapsed seconds
- average total tokens

## MobileWorld-style metrics

The batch report script (`scripts/eval/dailybench_report.py`) additionally computes the
metrics defined in [MobileWorld](https://arxiv.org/abs/2512.19432) (arXiv:2512.19432,
Section 4.2) — excluding the MCP metric:

- **Success Rate** — overall and per bucket, plus a GUI-only vs interaction
  (ASK USER) split
- **Average Completion Steps** — mean action steps per trajectory
- **Average User Queries** — mean `ask_user` invocations on interaction tasks
- **User Interaction Quality (UIQ)** — success-free fact-match: each ASK USER
  task scores its own `c_i / q_i` (fraction of its `ask_user` answers that
  matched the ground-truth fact), so every interaction task counts equally
  regardless of how many times it asked; rewards right questions regardless of
  whole-task success, and penalizes never-asking or asking unnecessarily on
  GUI-only tasks

```
uv run scripts/eval/dailybench_report.py --runs runs/<date-time>            # default scans runs/*/*
uv run scripts/eval/dailybench_report.py --model qwen/qwen3.7-flash      # filter by model
uv run scripts/eval/dailybench_report.py --runs 'runs/<date-time>/day3/*' --cooldown-seconds 10
```

`--cooldown-seconds` (default `10.0`) subtracts the batch's fixed inter-task pause
(`cooldown_seconds × (n_tasks − 1)`) from summed wall-clock, so reported elapsed is the
**TRUE agent running time** — pass `0` to report raw per-run elapsed instead. Only set it
when the batch was actually run with a non-default `--cooldown-seconds`.

This writes `report.json` and `report.md`. Interaction tasks are identified by
task_id membership in the ask_user_facts sidecar for the runs' source: `--source
tasks.md` -> `benchmarks/dailyBench-600/ask_user_facts_730.json`, `--source
public.md` -> `benchmarks/dailyBench-600/ask_user_facts.json` (overridable with
`--ask-user-facts`). Run folders are joined to the dataset via the `task_id`
recorded in `meta.json` (falls back to parsing the run `--label` for older runs).

## Notes

- deterministic and open-ended scores should remain separate
- publish benchmark date and task subset
- publish run settings used for every reported row

