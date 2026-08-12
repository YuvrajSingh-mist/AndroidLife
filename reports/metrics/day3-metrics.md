# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 21  ·  model: all

| metric | value |
|---|---|
| Success Rate | 85.7% |
| Success Rate (interaction / ASK USER) | 0.0% (1 runs) |
| Success Rate (GUI-only) | 90.0% (20 runs) |
| Average Completion Steps | 22.67 |
| Average User Queries | 0.00 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.000 |

### Outcome split (true success / true failure / hallucination)

| outcome | count | rate |
|---|---|---|
| True success | 18 | 85.7% |
| True failure (incl. honest-fail controls) | 1 | 4.8% |
| **Hallucination** (control self-reported success) | 2 | 9.5% |

Hallucination-control honesty: **0/2** controls honest, **2** hallucinated (0.0%).

| Elapsed (wall-clock, incl. cooldowns) | 4116 s (1.14 h) |
| Elapsed (TRUE agent running time) | 3916 s (1.09 h) |
| Inter-task cooldown subtracted | 200 s (10 s × 20 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 88.9% |
| hard | 66.7% |
| medium | 88.9% |
