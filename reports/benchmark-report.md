# DailyBench300 — Benchmark Report

**What it is:** a 28-day, 530-task mobile-agent benchmark that measures not just *can the agent do the task?* but *what does doing it cost a real phone* — dollars, battery, and heat — across cloud and local models, on everyday tasks in apps people actually use.

**Source of truth:** `benchmarks/dailyBench-600/tasks_530.md` → `DailyBench_530_v1.json` (exported by `scripts/export_530_dataset.py`). All figures below are computed from that JSON.

---

## Part A — Stats & Distribution

### A1. Snapshot

| Metric | Value |
|---|---|
| Dataset rows | **533** |
| Schedule | 28 days (fixed, one-time-shuffled, reused for every model) |
| Tasks/day | 16–23 (~19 avg) |
| Difficulty split | 230 easy / 231 medium / 72 hard |
| Hard split | 36 ASK USER / 36 DETERMINISTIC |
| Max points | 1,283 (230×1 + 231×3 + 72×5) |
| Apps covered | 21 |
| Cross-app required | 178 / 533 (33.4%) |
| Uniqueness | 533 unique ids · 0 duplicate prompts · 0 empty prompts |

### A2. Distribution by difficulty

| bucket | count | share | points | subgoal (clause) range |
|---|---|---|---|---|
| easy | 230 | 43.1% | 230 | 1–3 (dominant 2) |
| medium | 231 | 43.3% | 693 | 3–8 (dominant 4) |
| hard | 72 | 13.5% | 360 | 1–11 (dominant 5) |

### A3. Hard split — ASK USER vs DETERMINISTIC

- **36 ASK USER** — each hides one load-bearing fact the agent must actively request (all 36 carry an `ask_user_fact`; a single skipped `ask_user` fails the task). 32 have 0 placeholders, 4 have 1–3.
- **36 DETERMINISTIC** — all data on-device, ADB-verifiable end state.
- Interleaved across days: **19/28 days mix both**, 4 days are all-ASK-USER, 5 days are all-DETERMINISTIC.

### A4. Subgoal (clause) distribution

Rough subgoal count = prompt clauses (split on commas/em-dashes/`and`, ignoring app prefixes and parentheticals).

| bucket | clause-count distribution |
|---|---|
| easy | 1×16, 2×197, 3×17 |
| medium | 3×13, 4×157, 5×53, 6×5, 7×1, 8×2 |
| hard | 1×1, 2×3, 3×7, 4×9, 5×35, 6×13, 7×2, 8×1, 11×1 |

### A5. Cross-app requirement

| bucket | cross-app | total | share |
|---|---|---|---|
| medium | 114 | 231 | 49.4% |
| hard | 64 | 72 | 88.9% |
| easy | 0 | 230 | 0% |
| **all** | **178** | **533** | **33.4%** |

### A6. Per-day distribution

| Day | tasks | easy/med/hard | ASK/DET | distinct apps |
|---|---|---|---|---|
| D01 | 22 | 9/10/3 | 3/0 | 11 |
| D02 | 18 | 7/8/3 | 2/1 | 10 |
| D03 | 21 | 9/9/3 | 1/2 | 11 |
| D04 | 19 | 9/7/3 | 0/3 | 10 |
| D05 | 21 | 9/9/3 | 3/0 | 10 |
| D06 | 17 | 7/7/3 | 1/2 | 9 |
| D07 | 17 | 7/7/3 | 1/2 | 12 |
| D08 | 18 | 8/7/3 | 1/2 | 11 |
| D09 | 19 | 8/8/3 | 2/1 | 10 |
| D10 | 20 | 7/10/3 | 0/3 | 11 |
| D11 | 19 | 9/7/3 | 1/2 | 12 |
| D12 | 19 | 9/7/3 | 0/3 | 11 |
| D13 | 23 | 9/11/3 | 2/1 | 13 |
| D14 | 19 | 9/7/3 | 0/3 | 11 |
| D15 | 20 | 9/8/3 | 2/1 | 10 |
| D16 | 18 | 7/8/3 | 0/3 | 12 |
| D17 | 17 | 7/8/2 | 1/1 | 10 |
| D18 | 20 | 7/11/2 | 2/0 | 9 |
| D19 | 18 | 8/8/2 | 2/0 | 10 |
| D20 | 18 | 8/8/2 | 1/1 | 10 |
| D21 | 18 | 8/8/2 | 0/2 | 12 |
| D22 | 19 | 9/8/2 | 1/1 | 11 |
| D23 | 20 | 8/10/2 | 1/1 | 10 |
| D24 | 16 | 7/7/2 | 2/0 | 9 |
| D25 | 18 | 9/7/2 | 2/0 | 10 |
| D26 | 21 | 10/9/2 | 1/1 | 10 |
| D27 | 19 | 8/9/2 | 2/0 | 10 |
| D28 | 19 | 9/8/2 | 2/0 | 12 |

**Schedule notes:** days 1–16 carry 3 hard tasks; days 17–28 carry 2. Every day spans 9–13 distinct apps (min 7, max 11 in the original design; observed 9–13) — no app is on screen every day.

### A7. Per-app coverage

| App | total | easy/med/hard |
|---|---|---|
| Telegram | 71 | 11/36/24 |
| Notes | 71 | 6/44/21 |
| Obsidian | 71 | 7/44/20 |
| Chrome | 49 | 22/21/6 |
| Calendar | 47 | 12/22/13 |
| Clock | 32 | 13/14/5 |
| Files | 30 | 11/13/6 |
| Google Search | 29 | 11/10/8 |
| Gallery | 29 | 12/11/6 |
| Contacts | 27 | 9/11/7 |
| Google Maps | 27 | 10/12/5 |
| Google Drive | 27 | 12/12/3 |
| Gmail | 26 | 9/10/7 |
| YouTube | 26 | 11/10/5 |
| Settings | 26 | 10/10/6 |
| Calculator | 26 | 11/12/3 |
| Camera | 25 | 11/10/4 |
| Phone | 25 | 11/11/3 |
| Google Photos | 25 | 11/12/2 |
| Music | 24 | 9/10/5 |
| Messages | 23 | 11/10/2 |

### A8. Placeholders

44 unique `[placeholders]` in prompts (contact, topic, time, amount, note title, product, song, route, city, sender, meeting title, etc.), resolved from `tasks_vars.local.env` / per-day `tasks_vars/day_N.env` at run time.

### A9. Model / measurement contract

- **Models:** agent = `~deepseek/deepseek-v4-flash-latest` (OpenRouter) · ask_user/judge = `gpt-5.4-mini` · temp 0.0 · top-p 0.95.
- **Core metrics:** success rate, cost (USD), latency, battery/energy drain, thermal drift — captured per step on-device (`dumpsys battery`, `dumpsys thermalservice`), independent of the model under test.
- **Action budget:** 50 steps default (fixed cap, part of the benchmark definition; fairness across buckets).
- **Reference device:** OnePlus CPH2423 (Android 15, non-rooted), wired or wireless ADB; host-side `scrcpy --record` for video artifacts.

---

## Part B — Failures Summary

Date: 2026-07-27

This section summarizes the main failed or abandoned paths from the Droidrun / on-device model work so far.

### B1. Mini2 as the actual inference host was the wrong target

What happened:

- We successfully brought up model-serving flows on `mini2`.
- That included testing LiteRT-LM Python CLI server mode on the Mac mini.

Why it failed for the real goal:

- The actual goal was phone-local model execution, not Mac-mini-local execution.
- Using `mini2` as the inference host solved the wrong problem.

Takeaway:

- `mini2` is useful as a build/staging machine.
- It should not be confused with the phone-local inference target.

### B2. LiteRT-LM macOS binary on mini2 failed due to missing dylibs

What happened:

- We downloaded the LiteRT-LM macOS arm64 binary release on `mini2`.

Why it failed:

- The raw binary did not run because required dynamic libraries were missing.

Takeaway:

- The standalone release binary path was not reliable on that machine.
- The Python CLI route was the workable fallback on `mini2`.

### B3. LiteRT-LM Python on mini2 initially failed on system Python

What happened:

- We tried installing/running `litert-lm` with the system Python on `mini2`.

Why it failed:

- The system Python version was too old for the package behavior we hit.
- The CLI crashed around unsupported Python features.

Takeaway:

- We needed an isolated newer Python runtime.
- `uv` + Python 3.13 was the successful workaround.

### B4. Homebrew Python 3.14 on mini2 was broken

What happened:

- We tried using Homebrew Python 3.14 on `mini2`.

Why it failed:

- It had a broken `pyexpat` / `libexpat` issue and could not reliably run the CLI.

Takeaway:

- Homebrew Python on that box was not trustworthy for this workflow.
- `uv`-managed Python was safer.

### B5. Initial LiteRT-LM Android build on mini2 failed with `macosx10.11`

What happened:

- We attempted the official Android source build for LiteRT-LM on `mini2`.

Why it failed:

- Bazel Apple support defaulted to `macosx10.11`.
- mini2 only had newer Command Line Tools SDKs.
- `xcrun` could not find the old SDK.

Takeaway:

- The build needed an explicit modern SDK override.
- The successful fix was `--macos_sdk_version=26.2`.

### B6. Full Xcode was not installed on mini2

What happened:

- We checked the Apple toolchain state on `mini2`.

Why it mattered:

- Only Command Line Tools were installed.
- That made the host toolchain behavior more fragile during Bazel’s Apple helper steps.

Takeaway:

- We were lucky that the SDK-version override was enough.
- This host is still somewhat brittle for Apple/Bazel work.

### B7. ADB availability was inconsistent during the phone handoff

What happened:

- After the Android bundle was built and copied back, the phone was not immediately reachable.

Why it failed:

- USB visibility and old wireless ADB state were inconsistent.
- The old Wi-Fi serial did not reconnect when retried.

Takeaway:

- The build pipeline succeeded before the device pipeline did.
- Phone-local work depended on reattaching the device later.

### B8. LiteRT phone-local path was not a ready-made OpenAI-compatible server

What happened:

- We built and pushed `litert_lm_main` to the phone.
- We successfully ran the model locally on-device.

Why it failed for Droidrun integration:

- `litert_lm_main` is a native runner binary, not a documented Android REST server.
- Droidrun/Mobilerun expects a provider/API layer.

Takeaway:

- Phone-local LiteRT execution worked.
- Direct drop-in Droidrun backend compatibility did not.

### B9. LiteRT GPU path on phone was not good for agent-style decode

What happened:

- We benchmarked the same LiteRT model on CPU and GPU on the phone.

What failed:

- GPU init was extremely slow.
- GPU decode speed was worse than CPU decode speed.

Observed result:

- CPU was more attractive for short interactive requests.
- GPU only looked better on prefill-heavy parts.

Takeaway:

- This GPU path was not good enough for the intended agent workflow.
- The result did not justify pushing harder on LiteRT GPU for Droidrun.

### B10. LiteRT GPU teardown was messy

What happened:

- The GPU run completed, but logged an EGL cleanup warning.

Why it matters:

- It suggests the path works, but is not especially polished/stable.

Takeaway:

- Even when successful, the GPU path looked rough around lifecycle cleanup.

### B11. Local phone model + Droidrun architecture mismatch

What happened:

- We wanted users to select a model and run it easily on-phone via Droidrun.

Why it failed in practice:

- Droidrun is strongest when talking to an external provider/server.
- Phone-local runtimes on Android are fragmented and not packaged in a user-friendly way.

Takeaway:

- The most practical architecture right now is:
  - Droidrun on phone
  - model hosted locally elsewhere
  - phone treated as the controlled client device

### B12. MLC looked promising, but not turnkey for Android localhost serving

What happened:

- We researched MLC because it has better odds of using the Mali GPU well.

Why it did not immediately solve the problem:

- Official Android support is real.
- Official REST/OpenAI-compatible support is real.
- But the Android path is SDK/app oriented, not a ready-made “install and run local server APK” path.

---

## Part C — Task Execution Trace

Trace date: July 27, 2026

Shared run settings:

- wireless ADB
- `--no-vision`
- `--no-reasoning`
- model: `bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF:Q4_K_M`
- path: Mobilerun -> per-run proxy -> mini2 `llama.cpp`
- serial: `172.24.2.66:5555`

### C1) Check current battery percentage

- run: [runs/20260728-042609-easy-settings-battery-qwen4b-wireless](/Users/yuvrajsingh9886/Desktop/DrainBench300/runs/20260728-042609-easy-settings-battery-qwen4b-wireless)
- outcome: failed
- exit code: `1`
- final output: `Battery percentage is not visible in the current UI. No accessible element shows battery status. Cannot determine current battery level.`

Trace:

1. Agent fetched the current launcher / Clock state.
2. It looked for battery-related accessible UI.
3. No battery field was visible.
4. It failed rather than guessing.

Metrics:

- total tokens: `3933`
- elapsed: `44.69476554193153 s`

### C2) Search "weather tomorrow" and open the first result

- run: [runs/20260728-042700-easy-chrome-weather-qwen4b-wireless](/Users/yuvrajsingh9886/Desktop/DrainBench300/runs/20260728-042700-easy-chrome-weather-qwen4b-wireless)
- outcome: succeeded
- exit code: `0`
- final output: `Successfully searched for "weather tomorrow" and opened the first result, which displays a detailed weather forecast.`

Trace:

1. Agent found the Chrome search surface.
2. It typed `weather tomorrow`.
3. It submitted the query.
4. It opened the first visible result.
5. It confirmed success.

Metrics:

- request count: `3`
- total tokens: `20472`
- elapsed: `112.75527962506749 s`

### C3) Compare the top 3 results for benefits of walking daily

- run: [runs/20260728-042859-medium-search-compare-walking-qwen4b-wireless](/Users/yuvrajsingh9886/Desktop/DrainBench300/runs/20260728-042859-medium-search-compare-walking-qwen4b-wireless)
- outcome: succeeded
- exit code: `0`
- final output: `The top three search results for benefits of walking daily were compared. The first result is concise but general, the second is comprehensive but unstructured, and the third offers a clear, actionable recommendation: walking 30 minutes daily to improve heart health, maintain weight, and reduce stress. The third result is selected as the best due to its clarity, practicality, and focus on a sustainable daily habit.`

Trace:

1. Agent searched for `benefits of walking daily`.
2. It opened the first result and summarized it.
3. It opened the second result and summarized it.
4. One third-result click target was noisy, but the agent recovered.
5. It produced a three-result comparison and chose the third result as best.

Metrics:

- request count: `5`
- total tokens: `41091`
- elapsed: `217.32312454108614 s`

### Whole-run metric aggregation

The harness logs one completion entry per agent turn, then aggregates across the run:

- `llm_total_tokens_sum`: sum of all `usage.total_tokens`
- `llm_prompt_tokens_sum`: sum of all prompt tokens
- `llm_completion_tokens_sum`: sum of all completion tokens
- `elapsed_seconds`: full wall-clock task time, including device-control overhead

So the summary is whole-task aggregate data, not just the last model call.

---

## Related reports

- Run reports: `reports/day1-run.md`, `reports/day2-run.md`, `reports/day3-run.md`
- Metric JSON/MD: `reports/metrics/day2-metrics.md`, `reports/metrics/day3-metrics.md`, `hallucination-eval-day2.md`
- Full pipeline spec: `docs/benchmark-spec.md`, `docs/leaderboard-format.md`, `docs/evaluation-policy.md`
- Dataset layout: `benchmarks/dailyBench-600/tasks_530.md` (canonical) + `public.md` (50-task preview)
