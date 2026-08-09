# Evaluation Policy

## Reproducibility

- benchmarked runs should use a fixed model, fixed flags, and fixed task text
- benchmarked runs should use the same 50-step action budget unless a separate experiment explicitly studies budget sensitivity
- wireless ADB is preferred for measured runs
- environment drift must be documented when it affects comparability

## Deterministic tasks

- score by observable success or failure
- use final outputs, run artifacts, and state evidence

## Open-ended tasks

- report separately from deterministic tasks
- use explicit rubric items
- do not collapse rubric-based and deterministic scores into one opaque number

## Success Rate (MobileWorld SR gate) — ASK USER / interaction tasks

An ASK USER (interaction) task only counts as a **success** if the agent actually
called `ask_user` to obtain the hidden fact. An agent that guesses instead gets 0
— mirroring MobileWorld's \(q_i = s_i / c_i\), where \(c_i = 0 \Rightarrow q_i = 0\).
This gate applies ONLY to Success Rate / outcome classification, NOT to QIS.

Implemented in `scripts/eval/dailybench_report.py` (`load_run_record`, the
"MobileWorld SR gate (restored 2026-08-08)" block).

Example (Day 1, 2026-08-09): `hard__google-search-obsidian-telegram__057` did
the work and updated the Stock Watch note, but `ask_user_call_count = 0` → it is
correctly counted as a FAIL under the SR gate. This is the intended behavior.

## User Interaction Quality (QIS) — success-free fact-match

QIS uses the **success-free fact-match formula** (`user_interaction_quality_factmatch`
in `DailyBench/benchmark_metrics.py`): it grades the quality of each `ask_user`
answer by whether the LLM-user's answer matched the task's ground-truth fact,
regardless of whether the task succeeded. The paper's success-gated variant is
also computed and reported as deprecated. QIS is independent of the SR gate.

Example (Day 1, 2026-08-09): QIS fact-match = 0.000 because the only real
`ask_user` call (wireless-earbuds price compare) returned an answer that did not
match the hidden fact, even though the task partially succeeded.

## Benchmark maintenance

- prefer evaluator fixes over retroactively changing old results
- document task volatility and environment changes
- keep regression tests for parsers and scorers
