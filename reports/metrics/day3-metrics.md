# DailyBench batch report (MobileWorld metrics, no MCP)

- runs: 21  ·  model: all

| metric | value |
|---|---|
| Success Rate | 90.5% |
| Success Rate (interaction / ASK USER) | 0.0% (1 runs) |
| Success Rate (GUI-only) | 95.0% (20 runs) |
| Average Completion Steps | 69.57 |
| Average User Queries | 0.00 |
| User Interaction Quality (QIS, fact-match, success-free) | 0.000 |
| — QIS success-gated variant (MobileWorld, deprecated) | 0.000 |

### Outcome split (true success / true failure / hallucination)

| outcome | count | rate |
|---|---|---|
| True success | 17 | 81.0% |
| True failure (incl. honest-fail controls) | 4 | 19.0% |
| **Hallucination** (control self-reported success) | 0 | 0.0% |

Hallucination-control honesty: **2/2** controls behaved honestly (100.0%).

| Elapsed (wall-clock, incl. cooldowns) | 16821 s (4.67 h) |
| Elapsed (TRUE agent running time) | 16621 s (4.62 h) |
| Inter-task cooldown subtracted | 200 s (10 s × 20 gaps) |

### Success rate by bucket

| bucket | success rate |
|---|---|
| easy | 100.0% |
| hard | 66.7% |
| medium | 88.9% |
