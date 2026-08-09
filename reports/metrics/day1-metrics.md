# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 22  ·  model: all

| metric | value |
|---|---|
| Success Rate | 68.2% |
| Success Rate (interaction / ASK USER) | 33.3% (3 runs) |
| Success Rate (GUI-only) | 73.7% (19 runs) |
| Average Completion Steps | 74.41 |
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

| Elapsed (wall-clock, incl. cooldowns) | 22143 s (6.15 h) |
| Elapsed (TRUE agent running time) | 21933 s (6.09 h) |
| Inter-task cooldown subtracted | 210 s (10 s × 21 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 88.9% |
| hard | 33.3% |
| medium | 60.0% |
