# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 18  ·  model: all

| metric | value |
|---|---|
| Success Rate | 77.8% |
| Success Rate (interaction / ASK USER) | 50.0% (2 runs) |
| Success Rate (GUI-only) | 81.2% (16 runs) |
| Average Completion Steps | 38.94 |
| Average User Queries | 0.50 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.500 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.500 |

### Outcome split (true success / true failure / hallucination)

| outcome | count | rate |
|---|---|---|
| True success | 14 | 77.8% |
| True failure (incl. honest-fail controls) | 2 | 11.1% |
| **Hallucination** (control self-reported success) | 2 | 11.1% |

Hallucination-control honesty: **1/3** controls honest, **2** hallucinated (33.3%).

| Elapsed (wall-clock, incl. cooldowns) | 6429 s (1.79 h) |
| Elapsed (TRUE agent running time) | 6259 s (1.74 h) |
| Inter-task cooldown subtracted | 170 s (10 s × 17 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 100.0% |
| hard | 66.7% |
| medium | 62.5% |
