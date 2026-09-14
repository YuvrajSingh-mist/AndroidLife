# Naming: AndroidLife

**Product name:** AndroidLife

## Canonical names

| Kind | Canonical |
|------|-----------|
| Python package | `androidlife` |
| Batch CLI | `androidlife_tasks.py` / `uv run androidlife-tasks` |
| Single-task CLI | `androidlife_runner.py` / `uv run androidlife-runner` |
| Report script | `scripts/eval/androidlife_report.py` |
| Serial env | `ANDROIDLIFE_SERIAL` |
| Dataset dir | `benchmarks/androidlife-600/` |
| Corpus JSON | `AndroidLife_530_v1.json` / `AndroidLife_public_v2.json` |
| Phoenix projects | `androidlife` / `androidlife-dayN` / `androidlife-public` |
| HF 530 corpus | [`YuvrajSingh9886/androidlife-530`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-530) |
| HF public runs | [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public) |
| HF trajectories | [`YuvrajSingh9886/androidlife-trajectories`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-trajectories) |

## Local workspace folder

The checkout directory may still be named `DrainBench300` on disk. That folder name is local only and is not the product name.

## Process watchers

```bash
pgrep -fl 'androidlife_tasks|androidlife_runner'
pkill -f 'androidlife_tasks.py'
pkill -f 'androidlife_runner.py'
```
