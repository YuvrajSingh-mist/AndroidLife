# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 18  ·  model: all

| metric | value |
|---|---|
| Success Rate | 61.1% |
| Success Rate (interaction / ASK USER) | 50.0% (2 runs) |
| Success Rate (GUI-only) | 62.5% (16 runs) |
| Average Completion Steps | 37.83 |
| Average User Queries | 0.50 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.500 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.500 |

### Outcome split (true success / true failure / hallucination)

| outcome | count | rate |
|---|---|---|
| True success | 11 | 61.1% |
| True failure (incl. honest-fail controls) | 5 | 27.8% |
| **Hallucination** (control self-reported success) | 2 | 11.1% |

Hallucination-control honesty: **1/3** controls honest, **2** hallucinated (33.3%).

| Elapsed (wall-clock, incl. cooldowns) | 5374 s (1.49 h) |
| Elapsed (TRUE agent running time) | 5204 s (1.45 h) |
| Inter-task cooldown subtracted | 170 s (10 s × 17 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 100.0% |
| hard | 66.7% |
| medium | 25.0% |
