# Naming: AndroidLife

**Product name:** AndroidLife  
**Former names:** DailyBench / DrainBench / dailybench300

## Canonical names

| Kind | Canonical | Thin compat (still works) |
|------|-----------|---------------------------|
| Python package | `androidlife` | `DailyBench` (shim re-exports) |
| Batch CLI | `androidlife_tasks.py` / `uv run androidlife-tasks` | `dailybench_tasks.py` |
| Single-task CLI | `androidlife_runner.py` / `uv run androidlife-runner` | `dailybench_runner.py` |
| Report script | `scripts/eval/androidlife_report.py` | `scripts/eval/dailybench_report.py` |
| Serial env | `ANDROIDLIFE_SERIAL` | `DAILYBENCH_SERIAL` (fallback) |
| Dataset dir | `benchmarks/androidlife-600/` | symlink `benchmarks/dailyBench-600` → same |
| Corpus JSON | `AndroidLife_530_v1.json` / `AndroidLife_public_v2.json` | — |
| Phoenix projects | `androidlife` / `androidlife-dayN` / `androidlife-public` | old `dailybench-*` still accepted for DB derive |
| HF 530 corpus | [`YuvrajSingh9886/androidlife-530`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-530) | legacy [`drainbench-530`](https://huggingface.co/datasets/YuvrajSingh9886/drainbench-530) redirect |
| HF public runs | [`YuvrajSingh9886/androidlife-public`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-public) | — |
| HF trajectories | [`YuvrajSingh9886/androidlife-trajectories`](https://huggingface.co/datasets/YuvrajSingh9886/androidlife-trajectories) | — |

## Left alone on purpose

- Local workspace folder `DrainBench300` — orthogonal to product name
- Historical `reports/**` narrative text (not rewritten)
- Existing Phoenix SQLite DBs under `assets/db/**` that were stamped with `dailybench-*` — reopen with matching `--phoenix-project` or rely on dual accept

## Process watchers

```bash
pgrep -fl 'androidlife_tasks|dailybench_tasks|androidlife_runner|dailybench_runner'
pkill -f 'androidlife_tasks.py|dailybench_tasks.py'
pkill -f 'androidlife_runner.py|dailybench_runner.py'
```
