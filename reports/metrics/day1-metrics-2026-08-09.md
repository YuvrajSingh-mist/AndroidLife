# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 22  ·  model: all
- Source: `dailybench_report.py --runs assets/runs/full-bench/2026-08-09-153930/day1`
- ⚠️ **Manual audit correction:** this is the raw script output (counts
  `medium__gallery__001` as success). The on-device/trajectory audit in
  `reports/day1-run-2026-08-09.md` reclassifies `medium__gallery__001` as a
  **false pass** and `hard__chrome-telegram-notes__008` as **partial**, giving an
  audited success rate of **14/22 (63.6%)**.

| metric | value |
|---|---|
| Success Rate | 68.2% |
| Success Rate (interaction / ASK USER) | 33.3% (3 runs) |
| Success Rate (GUI-only) | 73.7% (19 runs) |
| Average Completion Steps | 34.14 |
| Average User Queries | 0.33 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.333 |

### Outcome split (true success / true failure / hallucination)

| outcome | count | rate |
|---|---|---|
| True success | 15 | 68.2% |
| True failure (incl. honest-fail controls) | 7 | 31.8% |
| **Hallucination** (control self-reported success) | 0 | 0.0% |

Hallucination-control honesty: **0/0** controls honest, **0** hallucinated (0.0%).

| Elapsed (wall-clock, incl. cooldowns) | 7763 s (2.16 h) |
| Elapsed (TRUE agent running time) | 7553 s (2.10 h) |
| Inter-task cooldown subtracted | 210 s (10 s × 21 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 77.8% |
| hard | 33.3% |
| medium | 70.0% |
