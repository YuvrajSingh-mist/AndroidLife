# Redo queue — tasks to re-run

Local working note (gitignored). Tasks whose recorded results are **not trustworthy**,
why, and what to do before re-running. Not a changelog — only things we owe a re-run.

---

## Manual review — verification pass, 2026-09-23

Every re-run that exists on disk was re-reviewed from its own artifacts (`output.json`,
`delivery.json`, `ui_states`, trajectories) and reconciled with what the reports publish.

| § | task | re-runs on disk | reviewed | outcome |
| --- | --- | --- | --- | --- |
| 1 | `medium__google-maps__002` | 13 of 13 | ✅ | **10 PASS / 3 FAIL** across the batch. **Published: all 13 rows** — rows 1-8 by the arithmetic pass, **rows 9-13 by the hand pass** (§1b below). `verify_leaderboard.py`: 0 mismatches / 300 fields |
| 2 | `hard__google-meet-files__070` | 13 of 13 | ✅ | **9 PASS / 4 FAIL**; published to all 13 reports + metrics + leaderboard. FAILs: rows 7/8 (luna, non-termination), 11 (kimi VISION, attendee trap), 12 (gemma VISION, `[agenda file]` unresolved) |
| 3 | `hard__bookmyshow__005` | 13 | ✅ | **1 published verdict moved: row 5 FAIL → PASS**; applied to all 13 reports + metrics + leaderboard |
| 4 | `hard__drive-notes-telegram__010` | 13 | ✅ | **0 PASS** confirmed; rows 3/4 are delivery-gate false passes (composer never sent), row 12 FAILs the ASK-USER gate |
| 5 | `easy__google-slides__001` | 7 | ✅ | **6 PASS / 1 FAIL** confirmed (row 7, 60-step cap) — every PASS replied `8` |
| 6 | `easy__calendar__002` | 9 (8 roots + row 13 in place) | ✅ | **7 PASS / 1 FAIL** confirmed (row 12, malformed tool-call markup) |

Notes from the pass:
* **§1 now has artifacts, and all 13 rows are published.** Rows 1-7 ran on 2026-09-23 and
  were audited from their trajectories (all typed the query — see §1a). Rows 8-13 were lost to a
  false seed-gate abort and were re-run afterwards; those five are the hand pass in §1b, because
  their reports do not use the 60-task table shape. **§2 is now done too** — the seed was
  repaired on 2026-09-24 and all 13 rows re-run; see the §2 `RE-RUN COMPLETE` block (this note
  is the 2026-09-23 snapshot, when §2 was still the one section with no artifacts).
* **§4 rows 3/4/12 self-report `success: true`** — that is exactly the false pass the
  delivery gate exists to catch; recorded correctly as FAIL.
* **§6 row 13 (Bonsai)** has no separate *working* root: its calendar re-run was captured
  **in place** inside `20260920-044846/day1/easy-calendar-002/` (artifacts dated 2026-09-21),
  which is why a `LAUNCH.txt` scan finds only 8 roots for 9 rows. Publication is unaffected —
  see §8h.
* **Every re-run, in every section, is published the same way: in place.** The canonical roots
  keep their identity and only the re-run task's directory inside them is replaced. HF carries
  the 15 canonical roots and no re-run roots at all; 56 of the 65 redo-task directories are
  byte-identical to a local re-run root, and the 9 that are not are exactly the rows that were
  deliberately left alone (details in §8h).
* `reports/` is byte-identical on HuggingFace and `verify_leaderboard.py` reports
  **0 mismatches across 13 rows / 300 fields**.

---

## 1. `medium__google-maps__002` — Google Maps + Notes (medium, 3pt, day 1)

**Verdict: every recorded result is a vacuous PASS — the search was never performed.**

The task asks the agent to compare driving / transit / walking ETAs in Maps for
`[place]` (= `Bhubaneswar Airport`, which Maps resolves to *Biju Patnaik International
Airport*) and save the fastest one to Notes. **No run ever typed the query.** Maps'
recent history and/or a leftover open route already contained the airport, so the agent
taps what is already on screen and the grader sees the right end state.

| Run | Typed the airport query? | What it actually did | Recorded |
|---|---|---|---|
| qwen-28 | no | "I see 'Biju Patnaik International Airport' in recent history — I'll tap it." | ✅ vacuous PASS |
| qwen-0909v | no | "…in recent history" | ✅ vacuous PASS |
| seed-30 | no | "there's a pre-existing suggestion … I can click that directly instead of typing, which is faster" | ✅ vacuous PASS |
| gemini-26 | no | went straight to a Directions button on an already-open airport page | ✅ vacuous PASS |
| qwen35-0914 | no | "the driving mode is already selected showing 24 minutes" — live leftover route | ✅ vacuous PASS |
| mimo-0901 | no | "recent search history" → tapped it | ❌ FAIL (malformed) |
| gemma-0917v | **yes** | typed `Bhubaneswar Airport`, reached the airport page, then **tapped Start and began live turn-by-turn navigation** (32 min / 13 km) — never compared modes, never saved the note | 🚨 HALLUCINATION |

Established by tracing every run's tool calls for a `type` / `type_text` of the airport
query. The 17 Sep vision run is the first that *did* type it, and it still failed — so the
free-pass mechanism above is about the earlier runs only.

**Root cause:** Maps is not returned to a clean search state between runs, so a prior
run's query / route leaks forward and satisfies the task for free where no query is typed.

**Before re-running:**
- Clear Maps search history + recent destinations, and stop any leftover active route.
- **Specifically stop leftover live navigation.** On 17 Sep the agent tapped *Start* on the
  airport route and nothing cancelled it; a Maps element then sat on top of **26 of the 27
  tasks** (552 a11y states across 472 files), with the navigation bubble reading
  `Hostel Rd` in 21 of them — so every later task was observed through it. Only the first
  task, which ran before Maps, was clean. Stop navigation (or reboot) between Maps and the
  next task as well as before the run.
- Confirm the airport is **not** pre-suggested when you open the search box.
- Then re-run on that clean state.
- Consider tightening the grade so it also asserts the query was typed — otherwise a
  pre-existing suggestion can keep satisfying it.

> ### ↻ RE-RUN STARTED 2026-09-23 — all 13 rows
>
> Seed applied today (`2026-09-23`, profile `public_v2`) and the gate passed. **The "before
> re-running" step was load-bearing, and it is NOT automated.** On opening the Maps search
> box the **Recent** list still held **`Biju Patnaik International Airport`** — the exact
> free hint that produced the vacuous PASSes — plus `restaurants` and `AI4Bharat`. Cleared
> through the documented UI path (long-press → *Delete suggested search?* → Delete, never a
> plain tap, which would open the place page and re-add the row), re-confirmed empty, then
> Maps force-stopped. The airport is no longer pre-suggested.
>
> **Why this nearly bit again.** `scripts/seeding/SKILL.md` §8 documents the step and the
> task→check table marks it `manual (§7)`, but it is **absent from
> `public_v2.manual_ui_cleanup`** in `reset_phone.py`, so the reset never printed it and a
> run could have started on a dirty Maps and re-scored the same vacuous PASSes.
>
> ### ⚠️ ABORTED mid-batch — rows 8-13 lost to a *second* leak this section never named
>
> The run went out as a 13-row batch (against the one-row-at-a-time rule this file keeps
> restating). It cleared the leak named above, ran rows 1-7, then **aborted rows 8-13 at the
> seed gate**: `Budget Deadline` was reported missing.
>
> It was never missing. The Maps task **writes a note** ("Fastest Route to Bhubaneswar
> Airport", plus a model-specific variant per row). Nothing force-stops those out of
> existence, so they accumulated **one per row — 7 of them, all dated 9/23** — and pushed the
> `Budget Deadline` seed **below the fold**. Worse, the OnePlus Notes app **reopens on
> whichever bottom tab it was last left on**, and the *To-dos* tab lists no notes at all: a
> row that ended on To-dos made every note look gone. `_note_open` returned `[]`, the gate
> read that as "seed damaged", and stopped the batch. **The seed was intact the whole time.**
>
> So the section above undercounted the leak. It named the Maps *recents* free-pass but not
> the Maps *run-notes*, which are the same free-hint surface **and** the thing that buried
> the seed. Both are now automated; see §7.8.

---

## 1a. `medium__google-maps__002` — both leaks now automated (2026-09-23)

`reset_phone.py` grows two cleanups next to the existing Telegram / Budget-Deadline ones,
in the same place and with the same shape:

| function | what it clears | how |
| --- | --- | --- |
| `clear_maps_run_notes` | every note titled `*Bhubaneswar Airport*` or `parked here` | OnePlus Notes multi-select → Delete |
| `clear_maps_recents` | the Maps search box's **Recent** list | long-press row → *Delete suggested search?* → Delete |
| `verify_maps_run_notes_clear` | gate: 0 Maps run-notes left | re-reads the Notes list |

Both run in the `--apply` reset path **and** in `--leak-cleanup-only`, which
`rerun_task_rows.sh` already calls between rows (`LEAK_CLEANUP=1`) — so a batch now repairs
these before every row's gate instead of accumulating them.

Two measured traps, both fixed:

* **A plain tap on a Maps recent row re-adds it to history.** Always long-press → Delete.
* **Tapping an already-checked Notes checkbox *deselects* it.** The long-press enters
  multi-select *and* checks the pressed row, so the first version — which tapped every
  target — cleared the very row it had just selected and deleted nothing **while printing
  `[ok] deleted 12`**. Fixed by reading the checkbox's `checked` attribute and ticking only
  the unchecked ones, then asserting the `N selected` count before pressing Delete. Caught
  by a controlled test: create a real Maps-style note, run the cleanup, assert it is gone
  **and** the `Budget Deadline` seed survives (it did, `text_count 518`).

`_note_open` also stopped assuming the Notes tab is showing: `_note_find_title` now taps the
bottom-nav **Notes** item when the list looks empty and scrolls a bounded number of times,
because run artifacts push the seed down the list. It never touches the seed itself.

**State after the abort:** run-notes 7 → 0, Maps recents → empty, `Budget Deadline`
`text_count 518` intact, `--leak-cleanup-only` **RESULT PASS**.

**Rows 1-7 ARE valid — this was checked, not assumed.** The abort lost rows 8-13, so the
question was whether the 7 rows that did run are trustworthy. They are: tracing every row's
trajectory for a `type` of the airport query (the discriminator this section defines) shows
**all 7 typed it themselves** — `Bhubaneswar Airport`, into the Maps search box — and each
wrote its own distinct comparison note. None read an answer off a leftover suggestion or a
previous row's note. So the manual recents clear did its job and **only rows 8-13 are
missing**.

## 1b. Manual review per row — the pipeline, and why it now gates the runner

**Every re-run row gets reviewed before the next model starts.** Not the artifact-level
"did it type the query" check alone — that one was fooled on 2026-09-23 by row 9, which
typed the query *and* wrote a well-formed note and still got the question wrong.

The review is `scripts/tools/review_rerun_row.py`: it reads a row from its OWN artifacts
(`output.json`, `trajectory.json`) and writes `review.json` next to them. `rerun_task_rows.sh`
now **stops the batch** after any row that has no `review.json` (`REVIEW_GATE=1`, default),
so the one-row-at-a-time discipline is enforced by the runner instead of by memory:

```
bash scripts/run/rerun_task_rows.sh medium__google-maps__002 rerun-maps 10 11 12 13
# ... row 10 runs, then:
#   REVIEW REQUIRED before the next row - this batch is stopping here.
uv run python scripts/tools/review_rerun_row.py --run-root assets/runs/public/<ts> --write
bash scripts/run/rerun_task_rows.sh medium__google-maps__002 rerun-maps 11 12 13
```

What the reviewer catches that `success: true` does not:

| signal | why it matters |
| --- | --- |
| no `type` of the airport query | the redo.md §1 vacuous PASS — a leftover suggestion satisfies the task for free |
| note names an off-mode (`Two-wheeler`, `cab`, …) | a well-formed note answering a different question (**row 9**) |
| note names none of driving/transit/walking | the saved answer is not about the asked modes |
| 60-step cap | an honest FAIL, not a harness failure |
| no note at all | the deliverable is missing |

Care is needed in **both** directions, and both traps are pinned in
`tests/test_review_rerun_row.py`:

* The task says *save the ETA and distance for that fastest option*, so a note carrying
  **one** mode (`Driving: 26 minutes, 13 km`) is correct — the comparison happens on the Maps
  screen. The reviewer's first version demanded all three modes in the note and
  false-FAILed row 3.
* The note write is itself a `type` call containing the airport name, so it must be excluded
  from query detection or a row that only wrote a note looks like it searched. Caught by the
  test suite, not by inspection.

### Per-row status

| row | model | mode | where | run root | typed query | review |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | qwen3.8-27b | TEXT | API | `20260923-022050` | ✅ | ✅ PASS |
| 2 | kimi-k2.6 | TEXT | API | `20260923-023201` | ✅ | ✅ PASS |
| 3 | gemini-3.1-flash-lite | TEXT | API | `20260923-023915` | ✅ | ✅ PASS |
| 4 | seed-2.0-lite | TEXT | API | `20260923-024645` | ✅ | ✅ PASS |
| 5 | qwen3.8-27b | VISION | API | `20260923-025320` | ✅ | ✅ PASS |
| 6 | seed-2.0-lite | VISION | API | `20260923-025950` | ✅ | ✅ PASS |
| 7 | gpt-5.6-luna | TEXT | API | `20260923-030604` | ✅ | ✅ PASS |
| 8 | gpt-5.6-luna | VISION | API | `20260923-160008` | ✅ | ✅ PASS |
| 9 | Qwen3.5-4B | TEXT | **local** | `20260923-162648` | ✅ | ❌ **FAIL** |
| 10 | gemma-4-E2B-it | TEXT | **local** | `20260923-171300` | ✅ | ❌ **FAIL** |
| 11 | kimi-k2.6 | VISION | API | `20260923-174839` | ✅ | ✅ PASS |
| 12 | gemma-4-E2B-it | VISION | **local** | `20260923-180228` | ✅ | ❌ **FAIL** |
| 13 | Bonsai-2-27B | TEXT | **local** | `20260923-184553` | ✅ | ✅ PASS |

**Row 13 verdict — PASS.** Best local row: 15 steps, all three modes compared, note written.

### Row-by-row outcome — all 13 done

| outcome | rows | note |
| --- | --- | --- |
| ✅ PASS | 1-8, **11**, **13** | typed the query and wrote a note naming the fastest of the three modes |
| ❌ FAIL — off-mode answer | 9 | saved *Two-wheeler* as fastest |
| ❌ FAIL — click loop | 10 | never reached Notes |
| ❌ FAIL — no note, step cap | 12 | reached Maps, never saved anything |

**Final: 10 PASS / 3 FAIL across 13 rows.** Every row was reviewed from its own
`trajectory.json` + `output.json` via `review_rerun_row.py` before the next row was
allowed to start (§1b). Leak cleanup reported **PASS** after every row: no Maps
run-notes left, recents cleared, Telegram composer empty, `Budget Deadline` intact.

**Done.** All 13 verdicts are written back into the 13 model reports, the metrics JSONs are
recomputed and their `.md` rendered from them, `leaderboard.js` matches all 300 fields, and
`reports/` + `runs/` are uploaded byte-identical to `androidlife-public`.

### The published artifacts had to be replaced, not just the text

Writing the verdicts into the reports was only half the job. `runs/<root>/day1/
medium-google-maps-002/` on the Hub still held the **original** artifacts for all 13 rows,
while every report already said *"Artifacts and metrics are the 2026-09-23 re-run"*. So the
artifact viewer would have shown the vacuous tap-the-recent run under a FAIL verdict, and the
hallucinated run under a PASS — the text and the evidence said opposite things.

Replaced in place, one commit per row (the run roots keep their identity; only that one task's
files change):

| | delete | add | | | delete | add |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 43 | 57 | | 8 | 137 | 127 |
| 2 | 45 | 45 | | 9 | 45 | 139 |
| 3 | 33 | 37 | | 10 | 45 | 139 |
| 4 | 45 | 47 | | 11 | 137 | 51 |
| 5 | 49 | 49 | | 12 | 69 | 139 |
| 6 | 49 | 43 | | 13 | 45 | 49 |
| 7 | 136 | 99 | | **total** | **878** | **1021** (687.8 MB) |

Verified byte-identical afterwards on the two hashes that matter — git blob for text/JSON and
**LFS sha256** for the screenshots and `trajectory.gif`. The first check compared git blob ids
and reported all 13 rows as mismatched; that was the check being wrong, not the upload: binary
files are LFS pointers, so their blob id is the pointer's hash, not the content's.

**Rows 7, 8 and 11 lost ~40 files each** (136→99, 137→127, 137→51). Those originals carried
screenshot sets from the *pre-re-run* attempts that were still under the same task dir.

### One gap this exposed: the Maps gate did not run on the full reset

`clear_maps_run_notes` and `clear_maps_recents` both ran in `--apply`, but only
`--leak-cleanup-only` *asserted* the result — `verify_maps_run_notes_clear` was unreachable
from the full reset path, and the Recents list had no gate at all. `clear_maps_recents` also
printed `[ok] maps: recent list cleared` unconditionally after a bounded loop, the same
"reports success while achieving nothing" shape that already shipped twice in that function
(the plain-tap re-add and the checkbox-deselect). The full reset is what precedes a fresh
launch, so a silent cleanup failure there would have gone unseen — which is the class of
failure that cost rows 8-13 in §1.

Fixed: `verify_maps_recents_clear` added, both gates wired into the full path, the sweep now
asserts instead of announcing, and both fail **closed** — a Maps that never opened has no
`Recent` header either, so "no header" is no longer read as "no recents" (it now requires
positive evidence of the search screen: `Search here` or the Home/Work/Favourites chips).
10 new tests in `tests/test_reset_phone_run_leaks.py` cover the pure row-selection, the
fail-closed path, the surviving-entry failure, and that the full `--verify-only` path gates on
both Maps leaks. Live-verified on the device: both gates PASS, `--leak-cleanup-only` → `RESULT
PASS`, full `--verify-only` → `RESULT PASS`.

### 1b. The hand pass — rows 9-13 (2026-09-23)

Rows 9-13 are partial/interrupted runs (`Success Rate (N runs)`, orphaned tasks, different
denominators), so the delta cannot be applied by counting (see §7c). Each was re-derived from
its own re-run artifacts — `output.json` + `run_metrics.json` for the **before** half (pulled
from `androidlife-public`, since those run roots are not on disk), the local re-run root for the
**after** half, and `review.json` for the verdict:

| row | model | report | re-run root | before (steps / s) | after | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | Qwen3.5-4B (TEXT) | `20260914-061846` | `20260923-162648` | 14 / 386.3 | 60 / 1971.9 | ❌ FAIL → **❌ FAIL** (was recorded PASS) |
| 10 | gemma-4-E2B-it (TEXT) | `20260916-011341` | `20260923-171300` | 14 / 342.5 | 60 / 1552.4 | ❌ FAIL → ❌ FAIL |
| 11 | kimi-k2.6 (VISION) | `2026-08-30-021852` | `20260923-174839` | 60 / 569.2 | 16 / 269.9 | ❌ FAIL → **✅ PASS** |
| 12 | gemma-4-E2B-it (VISION) | `20260917-160018` | `20260923-180228` | 26 / 553.0 | 60 / 2052.8 | 🚨 HALLU → ❌ FAIL |
| 13 | Bonsai-2-27B (TEXT) | `20260920-044846` | `20260923-184553` | 14 / 1807.8 | 15 / 1695.7 | ✅ PASS → ✅ PASS |

Three things surfaced that the arithmetic pass could not have seen:

* **Row 9 was recorded as PASS on an off-mode answer.** Its report had already been merged in
  place from a **16 Sep** re-run, upgraded FAIL → PASS on a note that named **Two-wheeler** as the
  fastest option. Two-wheeler is not one of driving / transit / walking, so the note answers a
  different question; the 2026-09-23 re-run reproduced exactly that (plus a 60-step cap). The row
  is now ❌ FAIL — the 23 Sep reviewer was right and the 16 Sep upgrade was wrong.
* **Row 11's report carried three different totals for the same 35 tasks** (Day-1 header 3 PASS,
  Totals table 4 PASS, prose 4/35) while its verdict rows already said 4 — left behind when the
  2026-09-21 slides re-run flipped a Day-1 FAIL to PASS without moving the aggregates. Same for
  its official-vs-manual note, whose worked example used two *orphaned* tasks (`meet-004`,
  `google-maps-004`) that are not graded at all. Both are fixed against the verdict rows.
* **Row 10 had the same class of drift from the calendar re-run** (metrics table 6 PASS / Totals
  5 PASS / failure analysis 43 FAIL) — reconciled to 6 PASS / 42 FAIL.
* **Row 12's rows 1-8 siblings were not the pattern for the elapsed figure.** The report's
  wall-clock and the metrics JSON's are computed on slightly different bases (row 9 by 458 s,
  row 11 by 18 s, row 12 by 97 s). The maps delta was applied to **each on its own basis**, as
  §7d requires for steps, rather than re-basing either onto the other.

**A note on `steps(official)`.** §7d's warning list is unchanged apart from rows 9-12 dropping
off it (their two figures now agree). Re-audited 2026-09-26: the list is rows 3/4/7/13 on
`steps`, row 4 on `queries` and rows 3/6 on `uiq` — 7 fields, all explained in §7d, with row 13
resolved there as the timeout (`steps: 0`) artifact.

**Row 9 verdict — FAIL, and the reason is substantive.** It typed the query and saved
`Travel to Bhubaneswar Airport - Fastest Option: Two-wheeler (33 min, 12 km)`. The task asks
for the fastest of **driving / transit / walking**; the Maps UI also offers *Two-wheeler* and
*Public transport*, and the model compared a mode that was never asked about — it read
`Driving at 35 minutes` and then reported a 33-minute two-wheeler as the answer. It also
burned all 60 steps. The artifact-level check would have called this a pass.

**Row 10 verdict — FAIL.** Typed the query, then got stuck in a **click loop**: from step 7
onward it toggled between two UI elements (`index 24` / `20` / `26`) without ever reaching the
Notes app, ending on `Clicked on Text: 'Bicycling'`. No note was written. 60-step cap.

### The review gate stopped a batch for the first time (working as designed)

Rows 10-13 launched together; after row 10 the runner refused to continue:

```
REVIEW REQUIRED before the next row - this batch is stopping here.
BATCH FINISHED WITH PROBLEMS: 10(gemma-4-E2B-it) 10(unreviewed)
```

Rows 11-13 did **not** start. Previously they would have run and been reviewed — or not — long
afterwards. That is the difference between a rule in a document and a gate in the pipeline.

### Device-state note (verified, not assumed)

Rows 1-7 ran against a manually-cleared Maps recents list, and rows 2-7 **re-added** the
airport to that list. That is real, but it cost nothing: every row typed the query anyway.
An earlier version of this file called rows 2-7 suspect on the strength of the re-added
recents; **trajectory evidence beats inference about device state**, and the evidence says
they are fine.

---

## 2. `hard__google-meet-files__070` — Google Meet + Files (hard, 5pt, day 3)

**Verdict: failed in all 11 recorded runs (10 on the current leaderboard). The cause is
now fixed, so these need a re-run on the new seed.**

> The other Meet task, `easy__google-meet__004` (day 2, easy), is **not** on this list —
> its recorded mix of PASS/FAIL traces to ordinary model errors (3 AM vs 3 PM, garbled
> invitee field, step caps), not to a broken seed. It is however the source of the
> `Product Demo` contamination noted below.

The failure was **never the account** — one report (`public-20260826-105200.md`) claims
"account mismatch / Rani Singh", and that is wrong. The real causes were:

1. the seeded `Weekly Sync` carried **no Meet conference link**, and Meet's "Scheduled"
   list only ever shows conferenced meetings;
2. Meet's "Scheduled" list only covers **~48h**, and the seed was Monday-anchored — so
   it sat 3–6 days out whenever a run started midweek, and Meet showed nothing.

**Fixed 2026-09-17** (`d26932d` main, `b4a544a` website):
- Meet links added by hand to the two offset-anchored seeds (`wph-bgoe-eye`, `ruo-uxua-pfr`);
- `reset_phone.py` now **shifts seeds in place** so those links survive every reset;
- the agenda meeting is anchored at **today+1 / today+2** (always inside the 48h window);
- the prompt no longer hardcodes "Monday".

**Before re-running:**
- Run `reset_phone.py --apply` **on the run day** (anchors are date-relative). This is
  the only thing "re-seed on the run day" means — there is **no new time to pick**; the
  meetings stay at 10:00 and only the dates shift to today+1 / today+2.
- Then run `reset_phone.py --verify-only`, which now **gates on this task**: it fails
  loudly if the anchor is stale (outside Meet's ~48h window), if the Meet link is gone,
  or if Meet's "Scheduled" list does not actually show `Weekly Sync` (wrong account).
  A broken seed can no longer silently cost a FAIL.
- **Watch for `Product Demo` contamination.** The day-2 task `easy__google-meet__004`
  creates a *conferenced* "Product Demo" event, which then shows up in Meet's list on
  day 3. Several of the recorded failures cited exactly this — the agent reported
  "Product Demo" instead of the seeded `Weekly Sync`. Clear any leftover "Product Demo"
  events before the day-3 Meet task runs.
- The links persist through resets; they only need re-adding if the events get deleted.

> ### ⚠️ 2026-09-21 CORRECTION — the 2026-09-17 fix was NOT sufficient
>
> *(Historical. **Superseded 2026-09-24**: the seed was repaired with app-UI writes and all 13
> rows re-run — see the `RE-RUN COMPLETE` block at the end of this section. The diagnosis below
> still stands as the reason the adb-only path could never work, which is what forced the
> app-UI seed.)*
>
> **This task is still unsolvable as seeded, and cannot be made solvable by resetting.**
> The 17 Sep fix assumed the blocker was the link and the 48h window. Both were real, but
> neither was the whole cause. The real blocker is that **Meet is a cloud app and the seed
> is a local database**:
>
> - Meet lists what exists on **Google's servers**, not what is in the phone's
>   `com.android.calendar` provider. `content insert`/`update` writes only the local copy.
> - Measured on the live device: the seeded rows carry `_sync_id`s (so they reached Google
>   *once*, when the links were added **by hand in the app UI**), but every later adb
>   date-shift sits at `dirty=1` **forever** — it never uploads.
> - Both documented ways to force a sync are **no-ops on this build**. `content call
>   --method forceSync` prints `Result: null` and `am broadcast -a
>   android.content.SyncAdapter` returns `result=0`; logcat during both shows **zero sync
>   activity**. There is no public force-sync API for a third-party account.
> - So the in-place shift added on 17 Sep *does* preserve the link (good) — but it moves
>   the meeting to a date the **server never learns about**, and Meet keeps showing the
>   stale server-side date, which by then is in the past.
>
> **Net rule: adb calendar writes never reach the cloud. Only app-UI writes do.**
> Evidence that app writes upload: the leftover `Weekly_Standup` from the 17 Sep run was
> agent-created in the UI and synced fine (`dirty=0`).
>
> **The fix that will actually work** (one-time, ~2 min, do it on the run day):
> 1. Open **Google Calendar** signed in as `yuvraj.mist@gmail.com`.
> 2. Create a **recurring DAILY** event `Weekly Sync` 10:00–11:00 **with a Meet
>    conference + attendees** (Daily ⇒ there is *always* an occurrence inside Meet's 48h
>    window, so it never needs re-uploading and never goes stale).
> 3. Delete the adb-seeded `Weekly Sync` copies so the reset stops shifting them, and add
>    the recurring series to an exclusion so `--apply` leaves it alone.
>
> Until that is done, `reset_phone.py` reports this check as a **WARN** (not a FAIL) so the
> launch gate stays usable; `--meet-strict` re-arms it once the seed is fixed.

> ### ⚠️ 2026-09-24 — attendees added by hand; the *task prompt* is the remaining defect
>
> The guest list was added through the Calendar **app UI** (the adb path cannot write guest
> rows on a synced event — same limit as the conference link): `rajceo2031@gmail.com` and
> `ranirajesh786@gmail.com` on the linked 10:00 `Weekly Sync`. Measured after saving:
> `dirty=0`, same `_sync_id`, Meet link intact, Calendar sheet reads **"4 guests /
> 1 yes, 3 awaiting"**. `--apply` date-shifts this seed **in place**, so the guests survive
> resets — **a one-time seed**. `verify_meet_agenda()` now asserts them
> (`meet_expected_attendees`), so a dropped guest list FAILs the pre-run gate.
>
> Side effect worth knowing: the UI save **re-uploaded the whole event**, so the corrected
> date went to Google with it (`dirty=0`). That is why Meet's `Scheduled` list currently
> shows `Weekly Sync` at the right date.
>
> **But the hand-review of row 2 proved the requirement itself is unsatisfiable.** Across
> every Meet surface — home card, green room header, participant line, `Joining info`
> sheet, and `More options` — Meet **never displays a scheduled attendee count**.
> `No one is in the call yet` is *live call participants*, which is 0 before the call by
> definition. Only **Calendar** shows the count.
>
> The prompt nevertheless instructs the model to *"open Google Meet … and note its title,
> time, and number of attendees"*. There is no `answer_check` for this task and the graded
> reply is only title + file name, so the clause is ungraded — but it is a **trap**: row 2
> (`kimi-k2.6`) burned all 60 steps hunting it (56 identical swipes in the green room) and
> FAILed, while row 1 (`qwen3.8-27b`) gave up after ~10 steps and passed. Diligence is
> penalised; that is not a model signal.
>
> **Decision (2026-09-24): the clause is being KEPT and the task is re-run as worded.**
> Rather than amend the prompt or re-point it at Calendar, the owner chose to run rows 1–13
> against the prompt verbatim and grade a green-room loop as a **genuine model failure**.
> Rationale to keep in mind when reading the results: the requirement is not satisfiable
> from Meet and is not graded, so a FAIL here measures *how a model handles an unanswerable
> sub-goal* (does it recognise the information is unavailable and move on, or thrash?) —
> not whether it can read an attendee count. Row 1 (`qwen3.8-27b`) recognised it and passed
> in 16 steps; row 2 (`kimi-k2.6`) thrashed for 56 and hit the 60-step cap. Read §2 verdicts
> with that lens, and **do not compare them to other tasks' pass rates.**

**Expect the numbers to move** once it is fixed — but note the post-fix runs will not be
comparable to the 11 on record, and the earlier "this is now solvable" claim above was
wrong: every recorded run failed, and none of them failed for a reason a reset could fix.

### ✅ RE-RUN COMPLETE — 2026-09-24/25 (all 13 rows, hand-reviewed)

The seed was repaired (conference link **and** guest list re-added through the Calendar app
UI, so they upload to Google's servers) and every leaderboard row was re-taken on the
corrected seed. **Result: 9 PASS / 4 FAIL.**

| row | model | mode | run root | steps | verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | qwen3.8-27b | text | `20260924-102208` | 13 | ✅ PASS |
| 2 | kimi-k2.6 | text | `20260924-103804` | 17 | ✅ PASS |
| 3 | gemini-3.1-flash-lite | text | `20260924-105601` | 5 | ✅ PASS |
| 4 | seed-2.0-lite | text | `20260924-111349` | 12 | ✅ PASS |
| 5 | qwen3.8-27b | vision | `20260924-113115` | 9 | ✅ PASS |
| 6 | seed-2.0-lite | vision | `20260924-114614` | 7 | ✅ PASS |
| 7 | gpt-5.6-luna | text | `20260924-132821` | 60 (cap) | ❌ FAIL |
| 8 | gpt-5.6-luna | vision | `20260925-145242` | 60 (cap) | ❌ FAIL |
| 9 | Qwen3.5-4B | text (local) | `20260925-210711` | 8 | ✅ PASS |
| 10 | gemma-4-E2B-it | text (local) | `20260925-212621` | 6 | ✅ PASS |
| 11 | kimi-k2.6 | vision | `20260925-223649` | 60 (cap) | ❌ FAIL |
| 12 | gemma-4-E2B-it | vision (local) | `20260925-230840` | 12 | ❌ FAIL |
| 13 | Bonsai-2-27B | text (local) | `20260925-232447` | 13 | ✅ PASS |

**This is the largest single-task movement of any redo section: 9 of 13 published verdicts
move, all FAIL → PASS.** The task was previously FAIL in all 13 rows *because the seed was
unsolvable* (Meet listed no conferenced meeting), so the re-run is the first time the task
measured a model at all. Per-row evidence is the run root, step count and verdict in the table
above; each row's full reasoning is written into that row's public report
(`reports/public/public-<root>.md` → `hard__google-meet-files__070` re-run note) and metrics JSON
(`rerun_2026_09_25_meet`).

**Four failure modes, all model-side — no seeding defect:**

1. **Rows 7, 8 (gpt-5.6-luna, both modes) — failure to terminate.** Both had the deliverable
   correct (row 8 by step 47) and then repeated the answer string without ever emitting
   `complete`, burning to the 60-step cap. This is luna's documented corpus-wide signature.
2. **Row 11 (kimi-k2.6 VISION) — the attendee trap.** Repeated *"0 attendees … let me scroll
   down more in the bottom sheet to see if there's attendee information"* ×38 to the cap.
   Reproduced on a verified-clean device, so it is the prompt's unsatisfiable
   "number of attendees" clause, not device state — the failure the owner's 2026-09-24
   decision anticipated. Note kimi-k2.6 **TEXT** (row 2) passed the same task, so this is
   mode-specific, and it is the *first* row to actually fall into the trap (rows 1-6, 9, 10 all
   recognised the count was unavailable and moved on).
3. **Row 12 (gemma-4-E2B-it VISION) — placeholder not resolved.** It found the meeting but
   searched Files for the literal string `"agenda file"` instead of `Weekly Agenda`. The value
   is supplied in the system prompt as ground truth and every other row resolved it, including
   the same model in TEXT mode (row 10).
4. Row 13 (Bonsai-2-27B) is the only row that **routed around** the attendee clause — it fell
   back to the Calendar app and read *"3 guests (1 yes, 2 awaiting)"*.

**Note on the first row-11 attempt.** `20260925-214040` was re-run with the `Left at 21:37`
Meet-card subtitle present and also failed; a clean re-run (`20260925-223649`) reproduced the
failure with the card absent, which is what proved the card was incidental and the attendee
trap is the cause. The clean root supersedes it.

**Operational note.** The pre-run seed gate flaked ~4 times during this batch on its UI checks
(`maps` recents, Meet `Scheduled`), each passing on immediate retry while `reset_phone.py
--verify-only` printed `RESULT PASS`. The runner aborts the row on that, so the batch needed
manual/looped retries. Worth hardening before the next multi-row sweep.


---

## 3. `hard__bookmyshow__005` — BookMyShow + Telegram (hard, 5pt, day 2)
**Verdict: the `[cinema]` placeholder named a cinema that does not exist. Failed in every
recorded public run. Vars fixed 2026-09-18 — all models need a re-run.**

`public_vars.local.env` resolved the placeholder to `cinema=INOX Bhubaneswar`. BookMyShow
has no listing by that name. Its Bhubaneswar cinemas are:

- `INOX: Symphony Mall`
- `INOX: DN Regalia Mall`
- `INOX: BMC Bhawani Mall`
- (plus `Cinepolis: Nexus Esplanade, Bhubaneswar`, `PVR: Utkal Kanika Galleria, Bhubaneswar`)

BookMyShow's search is **literal**, so typing the placeholder verbatim returns
**"Sorry! No result found"** — reproduced in the 17 Sep vision run
(`hard-bookmyshow-005/.../ui_states/0003`), which tried it once and returned `success=false`
after 4 steps. The 16 Sep run only found the cinemas because it happened to browse the
`INOX` prefix instead.

**Fixed 2026-09-18:** `cinema` is now **`INOX: Symphony Mall`** (an exact live listing) in
`src/androidlife/user_config.py`, `config/user_config.example`, and the
`public_vars.local.env` / `tasks_vars.local.env` copies under `benchmarks/`.

> ### ⚠️ 2026-09-22 — the fix was NOT in effect; re-verified live before re-running
>
> **The fix missed the one file the runner actually reads.** `config/user.yaml` is
> **gitignored** (machine-local persona config), so a "fixed in all five places" commit could
> not touch it, and because `load_user_config()` merges it *over* the shipped defaults it
> **overrode** the corrected value:
>
> | Layer | `cinema` | Actually used? |
> |---|---|---|
> | `src/androidlife/user_config.py` (shipped default) | `INOX: Symphony Mall` ✅ | no — overridden |
> | `config/user_config.example` | `INOX: Symphony Mall` ✅ | no |
> | `benchmarks/.../public_vars.local.env`, `tasks_vars.local.env` | `INOX: Symphony Mall` ✅ | no — not passed by the launcher |
> | **`config/user.yaml`** (gitignored, the runner's `--config` default) | ~~`INOX Bhubaneswar`~~ ❌ | **YES** |
>
> Proof, through the runner's own resolution path: `var_map(load_user_config())` returned
> `cinema = 'INOX Bhubaneswar'`. A 13-row re-run staged against that value would have
> re-run the *defect*, not the fix. Corrected in `config/user.yaml` 2026-09-22, and
> `scripts/tools/verify_task_vars.py` now renders the resolved task vars and **fails the
> launch** on a known-bad value — the runner only guards a *missing* placeholder, never a
> wrong one, which is why this slipped through twice.
>
> **Live re-verification on the run day (2026-09-22, device `CPH2423`).** BookMyShow
> Bhubaneswar still lists `INOX: Symphony Mall` (first result), `INOX: DN Regalia Mall`,
> `INOX: BMC Bhawani Mall`. So the pinned value is current.
>
> **Correction to this section's own claim: the search is not strictly literal.** Typing
> `INOX` — or even a mangled `INOX Bhuneswar` — surfaces the real INOX venues, so the task is
> reachable by browsing the prefix. What returns `Sorry! No result found` is the **exact
> phrase** `INOX Bhubaneswar`, confirmed in row 12's own `ui_states/0003`. The defect is
> therefore *ambiguity*, not unreachability — but pinning a real listing is still the right
> fix for a `DETERMINISTIC` task.
>
> **The recorded history is more mixed than "every run failed this task"** (all live pulls
> from the Hub, `day2/hard-bookmyshow-005/output.json`):
>
> | row | run | outcome | reply / reason |
> |---|---|---|---|
> | 3 | `20260826-105200` | `success=true`, 7 steps | `INOX: Symphony Mall, Toxic…, 07:00 AM` — **correct cinema**, failed only at the harness Send step |
> | 6 | `20260905-051950` | `success=true`, 18 steps | replied `INOX Bhubaneswar` — the **placeholder**, not a listing |
> | 10 | `20260916-011341` | `success=true`, 18 steps | replied `INOX Bhubaneswar` — graded 🚨 **HALLUCINATION** ("wrong cinema label") |
> | 8 | `20260910-041531` | `success=false` | "`INOX Bhubaneswar` was not found in BookMyShow" |
> | 12 | `20260917-160018` | `success=false`, 4 steps | "Sorry! No result found" at `ui_states/0003` |
> | 1,1,2,5,11,+ | … | `success=false` | step-capped at 60 (or malformed tool-call ×3) |
>
> Two consequences for interpretation:
> 1. **Rows 6 and 10 "succeeded" by echoing the placeholder back** — `INOX Bhubaneswar` is
>    not a cinema BookMyShow lists. Row 10 was correctly graded a hallucination; **row 6 was
>    graded `❌ FAIL — ASK USER — 0 asks (gate FAIL)`, but this task is `DETERMINISTIC`
>    (`is_ask_user: false`)** — an ASK USER gate applied to a non-ASK-USER task. The verdict
>    (FAIL) may still be right, but that stated reason is not.
> 2. So the redo premise "**failed in every recorded public run**" is wrong: at least one run
>    (row 3) produced the correct cinema+showtime and failed on delivery, and two others
>    replied with the non-existent placeholder. Row 3's is the only genuine solve, and it was
>    a **harness** failure.
>
> **Still open, for a verdict pass after the re-run:** there is no `answer_check` for this
> task, so a reply naming a non-existent cinema (`INOX Bhubaneswar`) is not machine-checkable
> — every graded judgement here came from a human reading the reply.

**Before re-running:**
- ✅ **Re-verified live 2026-09-22** — `INOX: Symphony Mall` is still the first Bhubaneswar
  result. ✅ **`config/user.yaml` corrected 2026-09-22** (it was silently overriding the fix —
  see above), and `scripts/tools/verify_task_vars.py` now gates the launch.
- Keep `ticket price=₹240`.
- This task touches live data (showtimes for "this weekend"), so re-verify on the run day
  like the docs already require for the other live-data tasks.
- ⚠️ **Verdict pass needed afterwards:** rows 6 and 10 recorded "success" while replying the
  non-existent `INOX Bhubaneswar`, and row 6's stated FAIL reason (ASK USER gate) does not
  apply to a `DETERMINISTIC` task. See the table above.

> ### 2026-09-22 re-run — 9 of 13 rows done, and a delivery defect it exposed
>
> Rows 1–5 and 7–10 have run; **6, 11, 12 and 13 still need one** (the host rebooted mid-batch
> at ~15:02 and took the detached launcher with it — `start_new_session=True` survives the
> shell and Cursor dying, not a reboot — and the handset then dropped off the network, so the
> batch cannot resume until it is reachable again).
>
> | row | model | `success` | delivered? | verdict |
> |---|---|---|---|---|
> | 3 | gemini-3.1-flash-lite (text) | `true` | ❌ left in the composer | **FAIL** (demoted) |
> | 4 | seed-2.0-lite (text) | `true` | ❌ Telegram never launched | **FAIL** (demoted) |
> | 5 | qwen3.8-27b (vision) | `true` | ✅ real sent bubble | **PASS** — the first genuine solve |
> | 7 | gpt-5.6-luna (text) | `false` | — | FAIL (honest) |
> | 8 | gpt-5.6-luna (vision) | `false` | — | FAIL |
> | 10 | gemma-4-E2B-it (text) | `true` | ❌ typed into Telegram's search box | **FAIL** (demoted) |
> | 1, 2, 9 | qwen3.8-27b / kimi-k2.6 / Qwen3.5-4B | `false` | — | FAIL (step cap) |
>
> **The defect: `success` cannot tell a send from a near-miss.** Three rows scored a pass while
> delivering nothing, each in a different way — row 3 typed the plan and never tapped Send
> (the leak cleanup recovered it as a live draft, `draft='INOX: Symphony Mall, Avengers
> Endgame: Encore, 07:15 PM'`); row 4 could not launch Telegram at all (it used the
> non-existent package `org.telegram.messaging`, which every other row resolved correctly to
> `org.telegram.messenger`) and called `complete(success=true)` anyway; row 10 typed the whole
> message into Telegram's **search box** and never opened the chat. Row 10 is the instructive
> one: its final UI state is a chat *list* with the composer empty, so nothing inside the chat
> looks wrong — the tell is that the message text is sitting in the search field.
>
> **Fixed, in the same one-directional style as `answer_check`:** `reset_phone.py
> --delivery-probe` reads the device-side fact (a "Sent at" bubble under today's separator in
> the `Yuvraj Airtel` chat) and the launcher writes it to `delivery.json` before the leak
> cleanup deletes the bubble. `androidlife_report.py` then demotes a self-reported success when
> a required-delivery task has evidence that nothing was sent. It only demotes on *definite*
> evidence: an unreachable chat, or a run taken before the probe existed, keeps its own
> outcome. The sidecar `benchmarks/androidlife-530/delivery_checks_public.json` lists the task,
> and it must stay **opt-in** — `hard__drive-notes-telegram__010` ("message … if it hasn't been
> updated by the deadline"), `hard__chrome-telegram-notes__008` (only over $10) and
> `hard__google-search-obsidian-telegram__057` (only if it crossed the threshold) all have
> *conditional* sends, so gating them would fail a correct decision not to send.
>
> Today's rows predate the probe, so their evidence was recovered from the leak-cleanup logs —
> the same two functions (`_tg_run_window_bubbles` / `_tg_draft`), run at the same moment —
> by `scripts/tools/backfill_delivery_evidence.py`. Re-running the grader over the 7 rows
> demotes exactly 3, 4 and 10 and leaves row 5's pass intact.
>
> **Also fixed in the harness (all committed):** `--leak-cleanup-only` between rows (the gate
> is verify-only, so one row's leftover draft used to abort every row after it — the first
> 2026-09-22 attempt lost rows 3–13 to row 2's unsent plan); a retry on transient seed-gate
> UI-read failures; the Telegram bubble deletion, which had **never** worked because the
> selection bar's `Delete` carries its label in `content-desc` rather than `text`, so it
> always reported "long-press menu did not appear" while the menu was on screen; and a retry
> in `_tg_open_chat`.
>
> **Still open:** run rows 6, 11–13 with the probe active, then do the verdict pass below.

> ### 2026-09-22 (later) — row 6 hit a `400` on BookMyShow, and it was *state*, not network
>
> Row 6 died at step 2 on an app error page, so the batch was stopped to diagnose it:
>
> ```
> com.bt.bms:id/no_network_error_container
> Sorry! Request failed
> It seems like we are encountering some issues at our side. Please try again.
> (Error code: 400).
> ```
>
> **The tell is the container: `seat_quantity_container`.** That is the *seat-selection*
> page — reachable only after choosing a movie, cinema and showtime — and it appeared one
> step after the splash, before the agent had done anything. BookMyShow had been **resumed
> into a previous run's unfinished booking**: row 10 (`20260922-140420`, 14:04) drove the
> app into seat selection and left it there (its own narration: *"the screen has changed to
> a seat selection interface… I see a 'How many seats?'"*). Row 6 started at 16:57, its
> `open_app` brought that stale task to the foreground instead of cold-starting, and
> BookMyShow answered the dead session with `400`.
>
> **It is not a network fault.** Verified on the device during the diagnosis: `ping 8.8.8.8`
> 0% loss, Wi-Fi on, airplane mode off, and BookMyShow opens to a normal home page
> (Bhubaneswar, movies listed). `am force-stop com.bt.bms` → relaunch lands cleanly on
> `MainActivity`. Blast radius was **1 of 13 rows**: rows 1, 5 and 10 also reached seat
> selection without erroring, because each was cold-started.
>
> **Why the reset missed it.** The pre-run reset (`cli.py`, §7.4) force-stops only the app in
> the **foreground**. BookMyShow was *backgrounded* (the foreground was Telegram), so it was
> never touched, and a backgrounded app keeps its UI state. The fix force-stops **the task's
> own apps** as well:
>
> * `src/androidlife/app_packages.py` — the app-name → package map, moved out of
>   `scripts/tools/app_audit.py` so the audit and the runner share one source of truth.
> * `adb.stop_packages()` — best-effort force-stop of a package list, reusing
>   `should_force_stop` so a protected/system package can never be killed. Force-stop kills
>   the process **without clearing app data**, so a signed-in app stays signed in — it is
>   deliberately not `pm clear`.
> * `cli.py --pre-app-reset-packages` — stopped before the agent starts, and recorded in
>   `meta.json` as `pre_app_reset_stopped_packages` so each run says what it actually reset.
> * `task_batch.py` resolves the dataset's per-task `apps` field (all 60 tasks declare one;
>   `hard__bookmyshow__005` → `['BookMyShow', 'Telegram']`) and passes the packages through.
>
> Verified on the device: with BookMyShow in the foreground, `stop_packages(['com.bt.bms',
> 'org.telegram.messenger'])` returns both, the focus falls back to the launcher, and no
> `com.bt.bms` process remains.

### 2026-09-22 re-run — rows 6/11/12/13 (relaunch with the pre-app reset live)

Row 6 is the run that proves the §7.4 fix was load-bearing, and it fails for the reason the
task actually deserves:

| row | model | outcome | evidence |
| --- | --- | --- | --- |
| 6 | `bytedance-seed/seed-2.0-lite` | **FAIL** (not sent) | 30 steps, self-reported `success: true`, but the composer held the whole message unsent |
| 11 | `moonshotai/kimi-k2.6` | **VOID — never ran** | aborted at the seed gate on row 6's leaked draft (§7.5); queued for re-run |
| 12 | `gemma-4-E2B-it` | **FAIL** | hit the 60-step cap, `sent_bubbles: 0`, composer empty at the end |
| 13 | `Bonsai-2-27B` | in flight | `LAUNCH.txt` model matches the row; 8088 serving `Bonsai-2-27B` |

Queued as a detached chain (`LOCAL_AUTOSERVE=1`) so it runs as soon as row 13 exits, the
device being single-tenant: **BMS row 11**, then **`hard__drive-notes-telegram__010` row 13**
(the one run `audit_telegram_inheritance.py` voids — `20260921-194413` scored with the
bubble row 11 had sent at 19:29; it is the only inherited run among all 17 scanned).

Row 6's `meta.json` is the proof that the old reset could not have caught this:

```json
"pre_app_reset_stopped_package": null,
"pre_app_reset_stopped_packages": ["com.bt.bms", "org.telegram.messenger"]
```

`pre_app_reset_stopped_package: null` means the **foreground** app was not BookMyShow — so
the pre-§7.4 reset was a silent no-op and BookMyShow was free to resume the stale
seat-selection page that produced the previous row 6's `Error code: 400`. With the task-apps
stop in place the 400 **did not recur** (0 occurrences), and the run cold-started cleanly.

Row 6 then produced exactly the false pass the delivery gate exists to catch:

```
self-reported success : False   <- after the gate (was true before it)
delivery_check        : not_sent
sent_bubbles / draft  : 0 / true
draft_text: "INOX: Symphony Mall, Avengers Endgame: Encore, 07:15 PM, per-ticket price ₹240..."
```

It typed the entire message and never pressed send. This is a genuine task failure (the
deliverable is the message), but note it is *not* the `INOX Bhubaneswar` failure of the
original rows — the cinema is now correct, so this row is a clean, attributable miss.

### ✅ RE-RUN COMPLETE — 2026-09-22 (all 13 rows, manually reviewed)

All 13 model rows were re-run against the corrected `INOX: Symphony Mall` seed and each
run was then manually reviewed from its own artifacts — `output.json` (`success`, `steps`),
`delivery.json` (`sent_bubbles`, `draft_present`, `draft_text`) and the `ui_states` dumps
(which cinema the run actually reached). `androidlife_report.py`'s delivery gate is what
separates a real send from a self-reported one.

**The seed fix worked: every one of the 13 rows reached the real `INOX: Symphony Mall`.**
(BookMyShow still renders `Bhubaneswar` as its city chip — that is the app's city label,
not the cinema the agent picked.)

| row | model | verdict | evidence |
| --- | --- | --- | --- |
| 1 | `qwen/qwen3.8-27b` (TEXT) | ❌ FAIL | step cap (60), no send |
| 2 | `moonshotai/kimi-k2.6` (TEXT) | ❌ FAIL | step cap (60), no send |
| 3 | `google/gemini-3.1-flash-lite` | ❌ FAIL *(false pass)* | 13 steps, `sent_bubbles: 0`, draft left in the composer |
| 4 | `bytedance-seed/seed-2.0-lite` (TEXT) | ❌ FAIL *(false pass)* | 5 steps, nothing drafted, self-reported success |
| **5** | **`qwen/qwen3.8-27b` (VISION)** | **✅ PASS** | **`sent_bubbles: 1`** — plan delivered to `Yuvraj Airtel`, `Avengers Endgame: Encore 07:15 PM Sat 26 Sep`, 20 steps |
| 6 | `bytedance-seed/seed-2.0-lite` (VISION) | ❌ FAIL *(false pass)* | 30 steps, whole message left unsent in the composer |
| 7 | `openai/gpt-5.6-luna` (TEXT) | ❌ FAIL | 13 steps, no send |
| 8 | `openai/gpt-5.6-luna` (VISION) | ❌ FAIL | 23 steps, no send |
| 9 | `Qwen3.5-4B` (TEXT) | ❌ FAIL | step cap (60), no send |
| 10 | `gemma-4-E2B-it` (TEXT) | ❌ FAIL *(false pass)* | 14 steps, no send — **the wrong-cinema hallucination is retired** |
| 11 | `moonshotai/kimi-k2.6` (VISION) | ❌ FAIL | step cap (60), no send |
| 12 | `gemma-4-E2B-it` (VISION) | ❌ FAIL | step cap (60), no send |
| 13 | `Bonsai-2-27B` (TEXT) | ⏸️ VOID (timeout) | 2400 s cap after 19 steps; at ~2 min/step a 60-step hard task cannot fit |

**Exactly one published verdict moved: row 5, FAIL → PASS.** No run recorded the old
`INOX Bhubaneswar`. Rows 3/4/6/10 were already non-PASS, so their downgrade to a
**delivery-gate FAIL** does not change the headline count — but it does change *why* they
fail, and row 10's hallucination is retired.

**Applied in place:**
* the `hard__bookmyshow__005` row in all **13** reports (`reports/public/public-*.md`),
  each with a `↻ re-run 2026-09-22` note under its manual-audit heading, and the Day-2
  header recalculated where the class changed (row 9 interrupted → FAIL, row 10
  hallucination → FAIL);
* `reports/metrics/public/public-20260909-043419-report.{json,md}` — aggregates recomputed
  by exact arithmetic (+1 success, −40 steps over the 60-run corpus) and a
  `rerun_2026_09_22_bookmyshow` key added alongside the existing
  `rerun_2026_09_21_drive_notes_telegram` one;
* `androidlife-website/assets/js/leaderboard.js` — row 5 `success 60.0 → 61.7`,
  `guiOnly 58.5 → 60.4`, `steps 26.28 → 25.62`, `buckets.hard 23.5 → 29.4`.
  `verify_leaderboard.py` reports **0 mismatches across 13 rows / 300 fields**.

---

## 4. `hard__drive-notes-telegram__010` — Notes + Telegram (hard, 5pt, day 1)

**Verdict: two benchmark-level defects — a missing app-private seed and an oracle naming a
file that never existed. ✅ BOTH FIXED 2026-09-21; this needs a re-run, not a code fix.**

The prompt named "my 'Budget Deadline' note", and the task also sent the agent to a Drive
spreadsheet described **only** in the oracle. Both halves were broken:

- the note lives **only** in the OnePlus Notes app (`com.oneplus.note`), which has no file
  seed, so it kept disappearing and nothing could restore it;
- the oracle directed the agent to a Drive file that does not exist anywhere.

The fix drops the Drive half entirely and turns the note's text into a tracked file seed.

Two pre-run UI dumps bracket the note's original loss:

| Dump | Date | Notes listed |
|---|---|---|
| `notes_final.xml` | 2026-08-30 | **`Budget Deadline`** + 7 others |
| `notes_now.xml` | 2026-09-16 | 8 notes, **no `Budget Deadline`** |

The 17 Sep run opened OnePlus Notes, searched `Budget Deadline`, and correctly got
"No results" — the task was genuinely unsolvable that day.

**Why the note kept vanishing:** it is an **app-private `needs_ui` seed with no file seed**.
`build_day_seed_manifest.py` records it as `{"type": "notes", "location": "Notes app
(app-private)", "status": "needs_ui"}`. `reset_phone.py` only *deletes* run-created notes
from that app; it cannot create this one. `docs/fabricated-test-data.md` says it was enriched
through the app UI — that edit does not survive a wipe, exactly as the doc warns
("re-applied via UI if ever reset"). It is now re-typed before each batch, and its text is
version-controlled.

> ### ✅ 2026-09-21 RESOLVED — Drive dropped, oracle fixed, seed re-typed
>
> **Defect 1 — the oracle named a Drive file that never existed.** The public ground truth
> told the agent to chase `family_numbers.xlsx`, but the device only ever held `budget.xlsx`:
>
> | Source | Named |
> |---|---|
> | public `ask_user_facts_public.json` + dataset | `family_numbers.xlsx` ❌ |
> | 530 twin (`ask_user_facts_530.json`) | `shared budget.xlsx` |
> | seed manifest (`build_day_seed_manifest.py`) | *"operator ensures the shared **budget.xlsx** exists in Drive"* |
> | `reset_phone.py` `seed_files` | `/sdcard/Download/budget.xlsx` |
> | **the device, observed 2026-09-21** | **`budget.xlsx`** (Microsoft Excel, Modified Aug 14) |
>
> Drive search for `budget.xlsx` returned exactly that one file; a search for `family`
> returned only stray images and a PDF — **no `family_numbers.xlsx`, no spreadsheet**.
> `family_numbers` appears in **0** of the 55 `ui_states` across the two runs that actually
> reached Drive.
>
> This had already corrupted a published verdict. `public-2026-08-30-143554.md` records
> `hard__drive-notes-telegram__010` as a FAIL partly because the agent "used `budget.xlsx`
> (ground truth `family_numbers.xlsx`)" — that specific criticism is **backwards**: the agent
> used the only file that exists. (The FAIL stands on its other grounds — it never asked
> which spreadsheet, missed the 08-10 deadline, and never messaged.)
>
> **Fix:** the public oracle now reads *"Message Yuvraj Airtel. The note you want is
> 'Budget Deadline'."* — and **Drive is out of the task altogether**, so there is no filename
> left to disagree about.
>
> **Defect 2 — the note was self-mutating and unresettable.** The prompt instructed the agent
> to *"log today's check date in the note"* on the not-overdue branch, so a run can **write
> into the very seed it is graded against**. The OnePlus Notes copy is app-private:
> `reset_phone.py` can only *delete* run-created notes, so it cannot restore this one, and
> `--verify-only` reads the content provider only — it is blind to `com.oneplus.note`.
> Evidence it really happened: the 2026-08-30 run read a note carrying *"prior check dates
> 2026-08-24 and 2026-08-28"* that the file seed does not contain.
>
> **Fix:** the note was re-typed through the Notes UI on 2026-09-21 carrying real budget
> figures plus both dates, and that exact text is now the tracked file seed
> `assets/seeds/public/notes/Budget Deadline.md` (generated by `enrich_public_notes.py`,
> restored by `reset_phone.py`). `reset_phone.py` still **deletes run-created notes by title
> and never sweeps by date**, so the seed survives a batch.
>
> **What changed**
>
> | File | Change |
> |---|---|
> | `public.md` | prompt → "Open my budget note in the Notes app and compare the last-reviewed date recorded in it against the finalisation deadline recorded in the same note"; header `[Drive+Notes+Telegram]` → `[Notes+Telegram]` |
> | `ask_user_facts_public.json` | `family_numbers.xlsx` → `"The note you want is 'Budget Deadline'."` |
> | `assets/seeds/public/notes/Budget Deadline.md` | real budget data + `Deadline: 2026-08-10` + `Last reviewed: 2026-07-10.` |
> | `enrich_public_notes.py` / `reset_phone.py` / `build_day_seed_manifest.py` | same text as the seed source / restore entry / manifest |
> | on-device `com.oneplus.note` | note re-typed via the UI 2026-09-21 |
>
> The `task_id` comment is untouched, so the artifact path stays
> `hard-drive-notes-telegram-010` and history remains comparable by path.
>
> **This is a deliberate public-only divergence — but the 530 twin was NOT self-consistent.**
> `tasks_530.md` keeps its own copy of this task on **Drive + Notes + Telegram**
> (`hard__drive-obsidian-telegram__049` is its Obsidian twin) and keeps the Drive leg.
> It was originally left as-is on the belief that the 530 corpus was self-consistent because
> `ask_user_facts_530.json` named **`shared budget.xlsx`**, "which really does exist in Drive".
>
> **That was wrong, and it was corrected 2026-09-23.** Verified on the live device: the only
> budget spreadsheet that exists is **`budget.xlsx`** — `/sdcard/Download/budget.xlsx`,
> 57 bytes, mtime `2026-07-18 10:00` (exactly as the 530 fabrication spec creates it). There
> is **no `shared budget.xlsx`** anywhere, and the 530 corpus's own docs
> (`fabricated-test-data.md`) describe the file as **`budget.xlsx` in Drive**. The
> `shared budget.xlsx` string was a typo in the sidecar, so the 530 oracle named a phantom
> file — the same defect class as the public `family_numbers.xlsx`, just in the other slice.
>
> Fixed in `ask_user_facts_530.json` + `AndroidLife_530_v1.{json,jsonl}`
> (`shared budget.xlsx` → **`budget.xlsx`**) and `hf_release/` regenerated, which also
> swept up the **stale public copy** that still carried `family_numbers.xlsx`.
>
> **Residual risk — now automated (2026-09-22).** The note is *still* app-private, and with
> Drive gone it is the **only** graded state — but it is no longer true that "nothing but a
> human in the UI can recreate it". Its text is version-controlled at
> `assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, and `reset_phone.py --apply`
> runs `restore_budget_note()`, which re-types it from that seed whenever
> `com.oneplus.note:id/text_count` drifts (canonical **518**), then verifies the result.
> `--verify-only` gates on it, so drift now **fails the gate** instead of silently costing a
> task — and unlike the old manual step it also repairs the *in-place edit* case, where a run
> takes the note's own "log today's check date" branch and overwrites the very seed it is
> graded against. Two measured constraints are load-bearing: the retype uses **Ctrl+A**, never
> a DEL loop (the note's **title is its first line**, so a character-wise delete renames it and
> the next run cannot find it), and the note **must not** be swept by date — hence
> `reset_phone.py` still deletes run-created notes **by title only**.
>
> **Before re-running**
> - ✅ Note re-typed via the UI 2026-09-21 (title `Budget Deadline`; preview `FY26 family
>   budget - finalisation`; list holds 12 notes).
> - ✅ Seed gate PASSES 2026-09-21, including
>   `PASS seed file content ... Budget Deadline.md contains 'Last reviewed: 2026-07-10.'`
> - **Now gate-enforced (2026-09-22):** the app-private copy is verified via
>   `com.oneplus.note:id/text_count` (**518** non-whitespace chars) against the tracked seed
>   `assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, and `restore_budget_note()`
>   re-types it on drift. The old manual "confirm the note is in the list — nothing on disk
>   verifies the app-private copy" step is therefore obsolete: there *is* now something on
>   disk, and drift fails the gate rather than costing a task.
> - The app force-stops back to the **list** on relaunch (verified), so the seed does not trip
>   the "starts inside the last-edited note" trap.

### ✅ 2026-09-21 RESULT — all 13 rows re-run; **0 PASS, and no verdict flipped**

The task is finally graded against state that actually exists, and the honest answer is that
**no model completed it**. Every row now fails for a reason the task itself defines, not for a
missing seed or a phantom filename:

| row | model | re-run outcome (2026-09-21) | verdict |
|---|---|---|---|
| 1 | qwen3.8-27b (TEXT) | read the note, called it overdue, **0 asks**, no chase | ❌ FAIL |
| 2 | kimi-k2.6 (TEXT) | asked ✓ → overdue → **60-step cap**, chase never confirmed | ❌ FAIL |
| 3 | gemini-3.1-flash-lite | asked ✓ → overdue → chase **composed** for Yuvraj Airtel, **`Send` never registered** | ❌ FAIL |
| 4 | seed-2.0-lite | asked ✓ → overdue → chase **composed**, 3 × `Send` + Enter, **never delivered** | ❌ FAIL |
| 5 | qwen3.8-27b (VISION) | **0 asks** (gate), 60-step cap | ❌ FAIL |
| 6 | seed-2.0-lite (VISION) | **malformed tool-call markup ×3** at step 9 | ❌ FAIL |
| 7 | gpt-5.6-luna (TEXT) | overdue detected, but judged the note to name no owner → nothing sent, 0 asks | ❌ FAIL |
| 8 | gpt-5.6-luna (VISION) | same as row 7 | ❌ FAIL |
| 9 | Qwen3.5-4B (TEXT) | 1 ask → **60-step cap** | ❌ FAIL |
| 10 | gemma-4-E2B-it (TEXT) | overdue detected, **could not reach a Telegram send surface**, 0 asks | ❌ FAIL |
| 11 | kimi-k2.6 (VISION) | 1 ask → **60-step cap** | ❌ FAIL |
| 12 | gemma-4-E2B-it (VISION) | judged the note **overdue**, then took the note's own "log today's check date" branch instead of messaging (accepted by the grader), **0 asks** | ❌ FAIL |
| 13 | Bonsai-2-27B (TEXT) | **2400 s timeout, 0 steps** | ❌ FAIL |

**No published verdict changed.** The two PASSes that the first substitution recorded
(rows 3 and 4) were **self-reported only**: in both runs the chase text is still sitting in
Telegram's composer at the final UI state, with the `Send` button present and no sent bubble
— and row 4's own closing reason admits *"the send button did not register clicks to finalize
delivery"*. That is the **same harness Send-button failure** that made the original rows 3 and
6 FAIL, so both were re-graded to FAIL and the manual-audit headlines for rows 3, 4 and 6 are
back where they started. Only telemetry (steps / queries / elapsed / cost) moved.

> **⚠️ New infra finding — the Telegram `Send` tap is unreliable (see §7.2).** Of the 13
> re-runs, **2 composed the exact correct chase message and could not deliver it** (rows 3, 4),
> and 2 more of the original runs hit the identical failure (rows 3, 6). A tap on
> `Text: 'Send'` at its reported centre coordinates registers as "clicked" in the trajectory
> yet leaves the text in the compose box. Until that is characterised, **any chase-message task
> has a delivery step the harness cannot be trusted to perform** — grade such tasks from the
> post-send UI state, never from the model's claim.

**What was done with the result**

- all 13 reports (`reports/public/public-*.md`) carry a re-run note, and rows 1, 2, 5 and 7–13
  had their stale `family_numbers.xlsx` / Drive-loop verdict text replaced with the re-run's
  actual behaviour;
- `reports/metrics/public/*` and `androidlife-website/assets/js/leaderboard.js` were updated
  for the telemetry only — `verify_leaderboard.py` → **0 mismatches**;
- row 12's Limitations bullet now records that the app-private seed gap it depended on is fixed;
- the re-run artifacts replaced the superseded ones in place under
  `runs/<canonical>/day1/hard-drive-notes-telegram-010/` on
  `YuvrajSingh9886/androidlife-public`, and every uploaded file was verified byte-identical
  (sha256 for LFS objects, git-blob-sha1 for the rest).


---

## 5. `easy__google-slides__001` — Google Slides (easy, 1pt, day 1)

**Verdict: CLOSED 2026-09-21. Two presentations were both named "Q3 Review" and the runs
read the wrong one (1 slide, not 8). All 7 affected rows re-taken against the canonical
`Q3_Review.pptx`; 6 PASS / 1 genuine FAIL. The deck is now version-controlled + restored by
`reset_phone.py`, and the grader now checks the reply against ground truth — see the end of
this item.**

**↻ Re-reviewed 2026-09-23 under the review gate (backfill) — then withdrawn (2026-09-24).**
These verdicts were reached by hand on 2026-09-21, *before* `review_rerun_row.py` existed, so
none of the 7 re-run roots carried a `review.json` and the gate had no record to read. On
2026-09-23 all 7 were re-derived from their own artifacts by a purpose-built reviewer
(`review_slides`), which reproduced the hand verdicts exactly (**6 PASS / 1 FAIL**; row 7's
60-step cap is the FAIL). The reviewer is deliberately stricter than the hand pass in one way
— because two decks were both called "Q3 Review", it requires (a) the canonical
`Q3_Review.pptx` to be the deck actually opened and (b) the reply's **first integer** to be
the expected `8`, mirroring the grader's `answer_checks` semantics. That combination is what
the original grader could not see: replies of `1`, `3` and `8` all scored PASS because the
grader carried no ground truth at all.

**The resulting `review.json` files were deleted again on 2026-09-24, and the verdicts stand
on the hand review alone.** Writing them created an artifact dated 2026-09-23 for a review
performed on 2026-09-21, i.e. a gate record for a gate that did not exist at review time —
indistinguishable in the corpus from a genuine one. The task does not need the file: its
re-run artifacts replaced the superseded ones in place, and the 6/1 split is recorded here.
`review_rerun_row.py`'s `review_slides` reviewer remains in the tool and is what a *future*
re-run of this task will be gated by.

The task: *"open the `[presentation name]` presentation in Google Slides and tell me how
many slides it has"* → `presentation name=Q3 Review`.

**The canonical account map** (`.agents/skills/reset-phone/SKILL.md` → "Cloud account
map") puts **Gmail / Drive / Docs / Slides on `ranirajesh786@gmail.com`** — that account
owns the `Q3 Review` deck. Verified 2026-09-18:

| App | Canonical account | Found on device | |
|---|---|---|---|
| Calendar (`cal_id=16`) | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Google Meet | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Gmail | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Drive | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Docs | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| **Slides** | `ranirajesh786@gmail.com` | **`rajceo2031@gmail.com`** | ❌ → fixed |
| Google Photos | `rajeshceo2015@gmail.com` | `rajeshceo2015@gmail.com` | ✅ |
| Google Maps | *(not constrained)* | `rajceo2031@gmail.com` | ⚠️ benign |

**This was a genuine drift, not the original state.** An archived UI dump
(`assets/runs/logs/gui_checks/51_slides.xml`, **2026-09-04 21:42**) shows Slides signed in
as `ranirajesh786@gmail.com` with `Q3 Review` **visible**. On 2026-09-18 it was
`rajceo2031@gmail.com` and the deck list contained **no `Q3` token at all** — a completely
different set of decks. Any run made in that window could not see the seeded deck.

**Fixed 2026-09-18:** switched Slides to `ranirajesh786@gmail.com` via the in-app account
chooser (all six accounts are already on the device — no password needed).

**The deck itself is fine.** `Q3_Review.pptx` is present **both** as the device file
`/sdcard/Download/Q3_Review.pptx` and in **Drive** on `ranirajesh786@gmail.com` (an uploaded
`.pptx`, not a native cloud Slides deck — which is why a search for the literal string
`Q3 Review` misses it; the item is `Q3_Review.pptx`). Opening it in Slides shows
**`Slide N of 8`** and the indicator **is** exposed to the accessibility tree, so a
text-tree agent can read it. Confirmed live 2026-09-18.

**Root cause, corrected 2026-09-21.** The account drift was real but was *not* what
produced the wrong answers. Two different presentations were both called **"Q3 Review"**:

| | file | slides | role |
|---|---|---|---|
| stray | `Q3 Review` (old upload) | **1** | what every run in the 08-26 → 09-06 window opened |
| canonical | `Q3_Review.pptx` | **8** | rebuilt **2026-09-07 13:12**; the real target |

The task's `presentation name` var is `Q3 Review`, and a literal search matches the stray.
So the earlier answers were honest readings of the **wrong file** — `1`, `3` and `8` all
scored PASS because the grader carried no ground truth at all. **6 of the 7 affected rows
were self-reported passes** against the wrong deck.

**Re-taken 2026-09-21** for all 7 affected rows (`1, 2, 3, 4, 6, 7, 11`), each confirmed in
`ui_states` to have opened `Q3_Review.pptx` (`Slide N of 8` on screen):

| row | model | re-run verdict | steps / s |
|---|---|---|---|
| 1 | qwen3.8-27b (TEXT) | ✅ PASS — replied `8` | 4 / 78.47 |
| 2 | kimi-k2.6 (TEXT) | ✅ PASS — replied `8` | 8 / 113.28 |
| 3 | gemini-3.1-flash-lite | ✅ PASS — replied `8` | 3 / 43.54 |
| 4 | seed-2.0-lite | ✅ PASS — replied `8` | 3 / 54.57 |
| 6 | seed-2.0-lite (VISION) | ✅ PASS — replied `8` | 3 / 64.51 |
| 7 | gpt-5.6-luna (TEXT) | ❌ FAIL — 60-step cap, no count | 60 / — |
| 11 | kimi-k2.6 (VISION) | ✅ PASS — replied `8` | 21 / 319.55 |

*Row 6 and row 7 above previously carried **swapped mode labels** — the leaderboard's row 6
is `seed-2.0-lite (VISION)` = `20260905-051950`, and its row 7 is `gpt-5.6-luna (TEXT)` =
`20260906-063336` (the same mapping the calendar table further down already used). The
step/latency figures always pointed at the right runs; only the two model strings were
wrong. Corrected 2026-09-21.*

### Visual re-verification — was the deck actually *empty*?

Checked 2026-09-21 by reading every run's `ui_states` (the same evidence the screenshots and
`.gif`s render) for the deck on screen. **The stray deck really is effectively empty:**
`Slide 1 of 1` with no content. The single intact original trajectory that still shows it is
`20260901-002701` (mimo-0901), which recorded the reply `1`; it is **not a leaderboard row**,
so it was never in scope for a re-run. The canonical deck instead renders `Slide N of 8`
with the full Q3 content.

Every run whose *original* trajectory is still intact was checked for the same symptom —
**none of them shows it**:

| Row | Run | Deck actually opened | Counts seen | Reply |
|---|---|---|---|---|
| 5 | `20260909-043419` | first a **22-slide** `UFDS Mentoring Orientation 2022`, then `Q3_Review.pptx` | `of 8` (settled) | `8` ✅ |
| 8 | `20260910-041531` | `Q3_Review.pptx` | `of 8` | 60-step cap ❌ |
| 9 | `20260914-061846` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 10 | `20260916-011341` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 12 | `20260917-160018` | `Q3_Review.pptx` | `of 8` | `8` ✅ |
| 13 | `20260920-044846` | `Q3_Review.pptx` | `of 8` | `8` ✅ |

(Non-`8` counts do appear mid-trajectory on rows 10 and 12 — `of 7`, `of 5`, `of 6` — but
they are transient while the deck loads/settles; the settled count is always `8`.)

So the re-run set **is** exactly the runs that read the wrong, empty-looking deck. The four
local / mac-mini rows (9, 10, 12, 13) were never affected and were correctly left alone.

**Caveat, worth remembering:** the seven re-runs *replaced* their original trajectory
directories in `androidlife-public`, so the pre-fix screen state for exactly those seven rows
can no longer be re-verified from the hub — only from the report notes. Every other run's
original is intact.

Row 7's FAIL **stands**, but is now known to be a genuine model limit (the correct 8-slide
deck was on screen) rather than a seed artifact. Rows 1 and 11 gained a true success; the
reports, `leaderboard.js` and the `reports/metrics/public/*.json` aggregates were all
recomputed from the re-runs by exact arithmetic, and the artifacts + reports re-uploaded to
`androidlife-public` (byte-identical, 337 files, 0 stale). Row 11's re-run left an
`Untitled presentation` behind; it was trashed and the gate re-verified before the next
launch.

**Both systemic fixes are now in (2026-09-21), so this cannot recur:**

1. **The deck is version-controlled and self-repairing.** `assets/seeds/public/Q3_Review.pptx`
   is tracked (the single exception to the blanket `assets/` gitignore — see `.gitignore`;
   a `!` under an excluded *directory* is silently useless, so the tree is excluded
   entry-by-entry to make the negation reachable). `restore_slides_deck()` re-pushes it on
   `--apply` whenever the device copy is missing or the wrong length, and refuses to push a
   fixture that disagrees with the task's ground truth; `verify_slides_deck()` blocks the
   gate. Tests: `tests/test_reset_phone_slides_deck.py` (incl. one that asserts the fixture
   is *actually tracked*, so a gitignore regression fails loudly).
2. **The grader grades the reply, not the model's opinion.** A new
   `answer_checks_public.json` sidecar (mirroring the existing `ask_user_facts` plumbing:
   `answer_checks_path` / `merge_answer_checks`) marks tasks with objectively known answers.
   `easy__google-slides__001` → `numeric_reply: 8`. `androidlife_report.py` takes the first
   integer in the agent's reply and **demotes** a self-reported pass that does not state it.
   The check is **one-directional — it can never promote**, so enabling it can only make a
   score more honest. Verified end-to-end against the 7 real re-run artifacts: all 7 classify
   correctly and **none of the 7 was decided by the check** (so no published number moved
   because of it).

**Before re-running:**
- Confirm **Slides → account = `ranirajesh786@gmail.com`** (now part of the account gate).
- Confirm `Q3_Review.pptx` is present and still has **8** slides (now restored + gate-enforced).
- **Never repair the deck by hand on the device again** — update the git fixture, or the next
  reset will put the old one back.

---

## 6. `easy__calendar__002` — Google Calendar (easy, 1pt, day 1)

**Verdict: the seeded conflict pair has been sitting on the RUN DAY instead of "tomorrow"
in most runs, so the task is vacuous when it passes and unjust when it fails. Cause now
confirmed; all models need a re-run.**

> ### ✅ RE-RUN COMPLETE — 2026-09-21
>
> All **9 affected models** were re-run on 2026-09-21 against a corrected same-day seed
> (conflict pair verifiably on “tomorrow” = **Tue 22 Sep**, and confirmed to be *rendering
> in the Calendar app*, not merely present in the provider). Aggregate metrics, official
> metrics JSONs, reports and the leaderboard were all updated in place; HF is byte-identical;
> `verify_leaderboard.py` reports **0 mismatches across 13 rows / 300 fields**.
>
> | Row | Model (mode) | Was | Now | Score move |
> |---|---|---|---|---|
> | 1 | qwen3.8-27b (TEXT) | ❌ FAIL *(unjust)* | ✅ PASS | 25 → **26 / 60** |
> | 2 | kimi-k2.6 (TEXT) | ❌ FAIL *(timeout)* | ✅ PASS | 31 → **32 / 60** |
> | 3 | gemini-3.1-flash-lite (TEXT) | ❌ FAIL *(never looked)* | ✅ PASS | 25 → **26 / 60** |
> | 6 | seed-2.0-lite (VISION) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — |
> | 7 | gpt-5.6-luna (TEXT) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — (official 8 → **9**) |
> | 10 | gemma-4-E2B-it (TEXT) | ❌ FAIL *(unjust)* | ✅ PASS | 5 → **6 / 53** |
> | 11 | kimi-k2.6 (VISION) | ✅ PASS *(incl. artifact)* | ✅ PASS *(clean pair)* | — |
> | 12 | gemma-4-E2B-it (VISION) | 🚨 HALLUCINATION | ❌ FAIL *(protocol abort)* | halluc 4 → **3** |
> | 13 | Bonsai-2-27B (TEXT) | ✅ PASS *(vacuous)* | ✅ PASS *(earned)* | — |
>
> **Net: +4 true successes across the 9 rows**, 1 hallucination retired, and every remaining
> PASS on this task is now earned rather than vacuous.
>
> **↻ Re-reviewed 2026-09-23 under the review gate (backfill) — then withdrawn (2026-09-24).**
> As with section 5, these verdicts were reached by hand on 2026-09-21 before
> `review_rerun_row.py` existed, so no root carried a `review.json`. On 2026-09-23 the re-run
> roots were re-derived from their own artifacts by a purpose-built reviewer
> (`review_calendar`), reproducing the hand verdicts — **8 PASS / 1 FAIL across the 9 rows**,
> row 12 the FAIL (malformed tool-call markup). Two caveats on the count: row 12 was attempted
> **twice** (both malformed, both FAIL); and row 13's calendar re-run is the only one
> **captured** directly inside its canonical root `20260920-044846` instead of in a separate
> `2026092x` working root. That is a capture detail, not a publication one — every re-run,
> here and in §1/§3/§4/§5, is published the same way, by replacing the task directory inside
> the canonical root (see §8h). The two discarded first-pass runs for rows 1 and 2 sit in
> `assets/runs/_rerun_backups/thrownaway/` and are deliberately not reviewed — they were
> superseded, not published.
>
> **Those `review.json` files were deleted again on 2026-09-24**, for the same provenance
> reason as section 5: a gate record dated after the review it describes, for a gate that did
> not exist when the review was done, is indistinguishable in the corpus from a genuine one.
> The 8/1 split stands on the hand review and on this section. `review_calendar` remains the
> reviewer a future re-run of this task will be gated by.
>
> The reviewer requires the reply to name **both** seeded events *and* say they
> conflict/overlap, and it special-cases the malformed-tool-call abort. A self-reported
> success is not sufficient, which is the point: the entire section-6 defect was a PASS that
> was vacuous once the seed drifted onto the run day.
>
> **Row 12 is the one judgement call.** gemma-4-E2B-it VISION *twice* named the correct pair
> in its reasoning, then emitted `<complete success="true" message="…"/>` instead of the
> harness's `<invoke name="complete"><parameter …></invoke>` form, and the runner aborted
> with `malformed tool-call markup 3/3`. It is recorded as ❌ FAIL, not PASS: an answer that
> never reaches a valid tool call is not a deliverable, and this failure mode is scored FAIL
> everywhere else in the benchmark (that same report lists 3 other tasks killed by it).
> T=0.0 makes it deterministic, so a third attempt reproduces it byte-for-byte.
>
> **No longer needed:** the `Weekly_Standup` sweep is now automatic, and `--apply` on a
> previous day can no longer start a run (the launch gate is enforced and fail-closed).
> See `.agents/skills/reset-phone/SKILL.md`.
>
> ---
>
> #### ↻ Second pass — 2026-09-21 (Schedule-view correction), rows 1 and 2
>
> Auditing the re-runs above for polluted starting conditions found one class the gate
> **cannot** see: the **Calendar app's view mode**. Google Calendar's agenda row reads
> `"<weekday> <D> <Month> <Y>, Open Day View"` when it is in **Schedule** view and
> `"... Open Schedule View"` when it is in **Day** view — so the mode is recoverable from
> the `ui_states` artifacts. Checked across all nine re-runs:
>
> | Row | Re-run traj | t0 view | Fixed? |
> |---|---|---|---|
> | 13 | `20260921_020121` | Schedule | — |
> | 1 | `20260921_021331` | **Day** ✗ | re-run as `20260921_035827` |
> | 2 | `20260921_023010` | **Day** ✗ | re-run as `20260921_040820` |
> | 3, 6, 7, 10, 11, 12 | `20260921_0245..0319` | Schedule | — |
>
> Cause: the agent of each run left the app wherever it finished, so row 13's agent left
> **Day** and rows 1–2 inherited it. From row 3 onward the view was forced back to
> Schedule before launch. Both affected rows were taken again from a verified Schedule
> start (`ui_states/0002`), verdicts unchanged (**PASS**), and their task figures,
> aggregates, metrics JSONs, the leaderboard and HF were all updated. **All nine re-runs
> now start from Schedule — 0 exceptions.**
>
> The re-take also repaired three lines the *first* pass had left stale on row 2 — its
> Date-line elapsed, its **Grand total run cost** (which contradicted the leaderboard:
> `$9.84` vs `$8.37`) and its **Top-token tasks** list (the calendar task, now ~21K tokens,
> was still listed first at 1972K) — plus the `easy-calendar__002` reference in the
> failure-analysis header count. The corrected top-token ranking was re-derived from all 60
> `run_metrics.json` on the hub, not guessed.


The task asks about **conflicts tomorrow afternoon**. `reset_phone.py` seeds
`Team Sync` 14:00–15:00 and `Mentor 1 on 1` 14:30–15:30 at `offset_days: 1`. When the
anchors are day-relative and `--apply` ran **on a previous day**, both land on what is by
run time *today*, leaving tomorrow with only the recurring `Weekly_Standup` 14:30–15:30 —
so "no conflicts" is the *correct* answer for that device, and the task tests nothing.

Established by parsing **every** `easy-calendar-002` `ui_states/*.json` on HF and reading
the day header each event sits under:

| Row | Run | Model | Conflict pair sat on | Recorded | Reality |
|---|---|---|---|---|---|
| 1 | `2026-08-28-002424` | qwen3.8-27b (TEXT) | **run day** (Fri 28 Aug) | ❌ FAIL *(“false pass”)* | **the FAIL is wrong** — the model said “tomorrow has only `Weekly_Standup`”, which was *true*; the audit’s ground truth came from ADB **after** the drift |
| 2 | `2026-08-29-153657` | kimi-k2.6 (TEXT) | not on screen | ❌ FAIL (timeout) | inconclusive |
| 3 | `20260826-105200` | gemini-3.1-flash-lite | not on screen | ❌ FAIL | inconclusive |
| 4 | `2026-08-30-143554` | seed-2.0-lite | **D+1 ✅** | ✅ PASS | correct |
| 5 | `20260909-043419` | qwen3.8-27b (VISION) | **D+1 ✅** | ✅ PASS | correct |
| 6 | `20260905-051950` | seed-2.0-lite (VISION) | **run day** (Sat 5 Sep) | ✅ PASS | **vacuous** |
| 7 | `20260906-063336` | gpt-5.6-luna (TEXT) | **run day** (Sun 6 Sep) | ✅ PASS | **vacuous** ← *this is the golden-format report* |
| 8 | `20260910-041531` | gpt-5.6-luna (VISION) | **D+1 ✅** | ✅ PASS | correct |
| 9 | `20260914-061846` | Qwen3.5-4B (TEXT) | **D+1 ✅** | ✅ PASS | correct |
| 10 | `20260916-011341` | gemma-4-E2B-it (TEXT) | **run day** (Wed 16 Sep) | ❌ FAIL | seed issue (already documented) |
| 11 | `2026-08-30-021852` | kimi-k2.6 (VISION) | not on screen | ✅ PASS | inconclusive |
| 12 | `20260917-160018` | gemma-4-E2B-it (VISION) | not on screen | 🚨 HALLUCINATION | inconclusive |
| 13 | `20260920-044846` | Bonsai-2-27B (TEXT) | **run day** (Sun 20 Sep) | ✅ PASS *(vacuous)* | **vacuous** |

**5 of 13 rows are demonstrably wrong or meaningless** on this task: 3 unearned PASSes
(rows 6, 7, 13 — including the report held up as the format standard) and 1 unjust FAIL
(row 1). It is the *same* failure class as #4 and #5: a benchmark-level seed defect, not a
model signal. Note the split is not random — every run with a **same-day** `--apply` is
correct (rows 4, 5, 8, 9); every run where the reset happened a day earlier is broken.

**Root cause (CONFIRMED 2026-09-20, from the 20 Sep run's own week view):**

```
Sun 20 Sep (run day)   Weekly Sync 10:00, Team Sync 14:00, Mentor 1 on 1 14:30, Weekly_Standup 14:30
Mon 21 Sep (tomorrow)  Weekly Sync 07:00, Weekly Sync 10:00, Weekly_Standup 14:30
```

Every `offset_days` seed is **exactly one day early** — `19 Sep + 1 = 20 Sep` — while every
`weekday` anchor is correct, because on consecutive days "next Monday" resolves to the same
date. **`--apply` ran on 19 Sep, not on the run day.** This is the recorded 2026-09-16
failure (seeded 15 Sep, batch started 16 Sep 01:13) and it keeps recurring.

**Disproven along the way** (do not re-apply these "fixes"):
- **Not** a Google-sync revert. A plain `content update` survives, and binding
  `dirty:i:1` is *rejected* by the CalendarProvider (`Only sync adapters may write to
  dirty`) — silently, since `content insert/update` still exit 0. That bind **broke every
  calendar write** and has been removed.
- **Not** a gate failure. `verify_calendar_anchors` was committed ~11 h *after* the 20 Sep
  run began, so it never ran that morning; the "gate saw the right dates" line in
  `public-20260920-044846.md` was a reconstruction artefact.

**Also found: a recurring run artifact pollutes the window.** `Weekly_Standup`
(`_id=4378`) is `rrule=FREQ=DAILY;COUNT=14` from Thu **17 Sep** 14:30 — created by the
2026-09-17 gemma run's agent, uploaded, never cleaned. It therefore appears on *every* day
including "tomorrow", and would add a spurious third afternoon event even with correct
seeds. Reset only sweeps exact-date rows today.

**Before re-running:**
- Run `reset_phone.py --apply` **on the run day** (same calendar day as launch). This is
  the whole fix; there is no other setting to change.
- Confirm the anchor gate shows `Team Sync` / `Mentor 1 on 1` on **D+1**; the script now
  re-reads every write it makes, so a rejected write fails loudly instead of silently.
- **Sweep recurring run artifacts** (`Weekly_Standup` FREQ=DAILY) across the window —
  query the `rrule` column, delete the series, not just today's instance.
- The two 14:30 events (`Mentor 1 on 1` + `Weekly_Standup`) overlap by design in the
  "triple-booking" reading; keep the recurring artifact out or the conflict set changes.

**Do not trust any recorded `easy__calendar__002` cell** from a run where the reset did not
happen on the same day — including the golden-format report.

---

## Re-run list (by model)

When the fixes below are in place, these tasks need a fresh run **for every model on the
board**. Scores for them are not comparable across the fix boundary.

### Count: **6 tasks × 13 model rows = 78 task-runs** to redo

`13` = the current leaderboard rows in `androidlife-website/assets/js/leaderboard.js`
(`LEADERBOARD_ROWS`), including the interrupted battery-death rows. Each of the 6 tasks
below must be re-run for every one of them, because all 6 were broken **at the benchmark
level**, not by any individual model — so the recorded cells are not a model signal.

| # | Task | Why | Blocked on |
|---|---|---|---|
| 1 | `medium__google-maps__002` | vacuous PASS from Maps' leaked recent/route state; the 17 Sep run also left live navigation running over 26/27 tasks | clear Maps history + stop nav |
| 2 | `hard__google-meet-files__070` | unsolvable seed — the 2026-09-17 "no conference link + 48h window" fix was **not sufficient**: Meet lists Google's *cloud* state, and an adb calendar write never uploads (see the §2 correction) | ✅ **DONE 2026-09-24** — one-time seed applied in the Calendar **app UI** (recurring DAILY `Weekly Sync` 10:00–11:00 with a Meet link + guest list; adb-seeded copies deleted) and the pre-run gate extended to assert both, so a silently dropped seed can no longer reach run day. All 13 rows re-run on the repaired seed: **9 PASS / 4 FAIL** (row 11's ATTENDEE clause and rows 7/8's non-termination are model-side). Verified by the gate: `reset_phone.py --verify-only` now covers `ATTENDEES_URI` |
| 3 | `hard__bookmyshow__005` | `[cinema]` placeholder named a non-existent cinema — **fixed (`INOX: Symphony Mall`); the 2026-09-18 fix had NOT taken effect** — `config/user.yaml` is gitignored and was overriding it, so the runner still resolved `INOX Bhubaneswar`. Corrected + launch now gated by `verify_task_vars.py` | ✅ **DONE 2026-09-22** — all 13 rows re-run on the corrected seed and **manually reviewed** (0.5 → 1 PASS: **only row 5 moved, FAIL → PASS**, its plan genuinely delivered; rows 3/4/6/10 became delivery-gate false passes; row 10's hallucination retired; row 13 VOID on timeout). Rows + `↻` notes written into all 13 reports, metrics JSONs substituted, leaderboard updated (`verify_leaderboard.py`: 0 mismatches) |
| 4 | `hard__drive-notes-telegram__010` | app-private `Budget Deadline` note kept vanishing, and the oracle named a Drive file (`family_numbers.xlsx`) that never existed — **fixed 2026-09-21: Drive dropped from the task, oracle fixed, note text version-controlled + re-typed via UI** | ✅ **DONE 2026-09-21** — all 13 rows re-run against the corrected seed (**0 PASS**, no verdict flipped); every run verified to start on the launcher; reports/leaderboard/metrics substituted, artifacts + reports byte-identical on HF |
| 5 | `easy__google-slides__001` | Two decks both named **"Q3 Review"** (stray **1**-slide vs canonical `Q3_Review.pptx` **8**-slide, rebuilt 2026-09-07) → runs read the wrong file; the grader had no ground truth, so `1`/`3`/`8` all recorded PASS — **deck now version-controlled + restored on reset, grader now checks the reply** | ✅ **DONE 2026-09-21** — all 7 affected rows re-run against the real deck (6 PASS / 1 genuine FAIL); reports, leaderboard + metrics JSONs substituted; artifacts byte-identical on HF |
| 6 | `easy__calendar__002` | conflict pair seeded on the **run day** instead of tomorrow in 5 of 13 rows → 3 vacuous PASSes (incl. the golden report) + 1 unjust FAIL — **cause confirmed, fix is same-day `--apply`** | ✅ **DONE 2026-09-21** — all 9 affected rows re-run; `--apply` gate is now enforced at launch and the recurring-artifact sweep is automatic |

---

## Device account state (verified 2026-09-18)

The device carries **6 Google accounts** and the apps are **not auto-consistent** — each
app remembers its own selected account, and nothing resets it between runs. Per-app
account selection is therefore **unmanaged drift**, and it is the same failure class as
#5: an app on the wrong account cannot see its seeded cloud data.

Canonical map (from `.agents/skills/reset-phone/SKILL.md` → "Cloud account map") vs what
was actually on the device:

| App | Canonical | Found | |
|---|---|---|---|
| Calendar (`cal_id=16`) | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Google Meet | `yuvraj.mist@gmail.com` | `yuvraj.mist@gmail.com` | ✅ |
| Gmail | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Drive | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| Docs | `ranirajesh786@gmail.com` | `ranirajesh786@gmail.com` | ✅ |
| **Slides** | `ranirajesh786@gmail.com` | ~~`rajceo2031@gmail.com`~~ | ❌ **fixed** |
| Google Photos | `rajeshceo2015@gmail.com` | `rajeshceo2015@gmail.com` | ✅ |
| Google Maps | *(not constrained by any task)* | `rajceo2031@gmail.com` | ⚠️ benign |
| Amazon / Swiggy / Zomato / BookMyShow / Prime Video / YT Music | personal accounts | all signed in | ✅ |

**Maps is on `rajceo2031@gmail.com`, not `yuvraj.mist@gmail.com`** — and that is fine. Maps
is deliberately **not** in the canonical map: neither Maps task
(`medium__google-maps__002` = compare ETAs + Notes, `easy__google-maps__004` = save parking
location) touches account-bound data, so the Maps account gates nothing. `rajceo2031` is
the documented *"device owner's own primary Gmail"*. Only Slides was actually wrong.

**Maps WAS on `yuvraj.mist` at some point and moved** — the same drift, just harmless here.
The lesson is the general one: never assume an app is on the account you last left it on.

**Recommended gate:** extend `reset_phone.py --verify-only` to assert the cloud account per
app (the identity disc's `content-desc` reads `Signed in as <Name> <email>`), so a drifted
app fails the pre-run gate instead of silently costing a task — the same treatment the Meet
seed now gets.

---

## Standing note

The items above are **benchmark-validity** issues, not model failures: the recorded
scores overstate ability for #1 (free pass) and #5 (unverified count) and understate it
for #2 (unsolvable seed). Worth keeping in mind when comparing against any run made
before 2026-09-17.

One more, **not** a re-run item — it caps what any of these numbers can mean:

- **The Google Sheets editor exposes no cell data to the accessibility tree.** Verified on
  the 17 Sep run: **0 of 15** a11y states for `hard__google-sheets-amazon-shopping__074`
  contain any cell text (`IPL 2025 Final Over`, `12500000` appear 0 times in the whole
  run). The tree carries only the sheet tab name and the toolbar; the grid draws on
  `id/spreadsheet_view`. So every Sheets task (and the Sheets half of
  `hard__google-sheets-amazon-shopping__074`) is **effectively vision-only** — a text-tree
  agent cannot read the spreadsheet at all. Keep this in mind when reading Sheets results
  as a capability signal; fix would be a UI-automator path that reads the grid, or
  accepting it as a vision-only task.

---

## 7. Latent infra defects found while auditing the seed path (2026-09-21)

Not task re-runs, but they can silently corrupt a run — which is the same hazard class as
items 1–6.

### 7.1 Stale tests hide real regressions (fix before trusting the suite)

`tests/test_reset_phone_calendar_gate.py` has **3 failing tests**. They are pre-existing,
not new: verified by stashing all local edits, and bisected to **`4be381d`** ("seeding: make
calendar seeds survive the Google sync, and re-verify after a settle") — green at
`b2d09a1`, red from `4be381d` onward. The suite has been red ever since.

There are **two mechanisms**, and they stack in a way that matters for the fix:

- **(a) The exact-date fast path — the cause today.** `ensure_calendar_events` computes
  each anchor from `date.today()`; the shared `QUERY_ROWS` fixture builds its copies from
  the **same** anchor helpers (`MONDAY`, `D1`, `D2`). So every fixture copy already sits
  exactly on its anchor, the seeder logs `already on ... (no write needed)`, and it issues
  **zero** writes of any kind. Measured: three `no write needed` lines and a call list
  containing only `getprop` + two `content query`s — no update, no insert, no delete.
  This fires **every day**, not just on Mondays (both sides derive from the same helpers).
- **(b) A latent second trap, revealed the moment you fix (a).** If you "fix" these tests
  by dating the fixture rows in the past, the seeder sees a same-time miss and — because
  the fixture rows are **unlinked** — resolves it by **INSERT**, not UPDATE (only
  `meet: True` seeds are UPDATE'd on a same-time miss, since delete+insert would silently
  destroy the conference link, which the non-rooted `content` CLI cannot rewrite). So
  re-dating the fixture alone will **not** green them.

Therefore the fix needs **both**: a stale-dated fixture (so (a) doesn't skip) *and*
`meet: True` seeds (so (b) resolves to an in-place UPDATE). The invariant actually worth
pinning is **link preservation**, which is why the update-in-place path exists.

One assertion in test 1 is **dead code** regardless: `assert ["_id=4341" in updates[0],
"_id=4342" in updates[1], "_id=4343" in updates[2]]` builds a non-empty list, and a
non-empty list is always truthy — it asserts nothing.

Why it matters more than it looks: a permanently red suite means a **real** regression is
indistinguishable from the known noise, which is exactly how the calendar drift survived
five runs. Note (a) itself is **not** unprotected — the new
`test_already_correct_seed_is_not_rewritten` pins the skip deliberately. Only these three
stale tests are broken.


### 7.2 Other pollution classes with no gate coverage

Everything below is ADB-invisible, so `--verify-only` **cannot** see it and only the manual
checklist in `docs/pre-run-checklist.md` covers it.

> **Promoted out of this table 2026-09-22 — the two content leaks that survived `force-stop`.**
> Both of the first two rows below were *app content*, not app screen, so the new pre-run app
> reset (`cli.py`, §7.4) cannot touch them and they stayed manual. Both are now **blocking
> gates with `--apply` repairs**:
>
> * **Telegram `Yuvraj Airtel` chat** — `clear_telegram_run_leaks()`. Deletes the draft and
>   any bubble under **today's** date separator (seeded history is dated 2026-08-20/23
>   precisely so run artifacts are distinguishable). Two measured facts drive the
>   implementation: **`force-stop` does NOT clear a Telegram draft** (typed → HOME →
>   force-stop → relaunch showed the identical draft, so the clearing has to happen in the
>   UI before the process is killed), and the chat-list **search box is also an EditText**,
>   so the composer lookup is y-guarded or `Search Chats` reads as a leak.
> * **OnePlus Notes `Budget Deadline`** — `restore_budget_note()`. The note text is now a
>   tracked fixture (`assets/seeds/public/Budget Deadline (OnePlus Notes).txt`, canonical
>   `text_count` **518**); a drifted note is re-typed from it via Ctrl+A and verified. It
>   must **not** be repaired by character-wise deletion: the note's **title is its first
>   line**, so a DEL-loop renames the note (a trial turned it into `- Utilities: Rs 9400`)
>   and the next run cannot find it.
>
> Opt out with `--no-leak-cleanup`. Both run in the same pre-first-task window as
> `verify_calendar_view_mode`, so they always hand back a stopped app on the launcher.

> **A second, nastier version of the Telegram leak: the run *after* the send (2026-09-22).**
> The cleanup above only deletes bubbles under **today's** separator, and it did not exist
> before 2026-09-22. So the 2026-09-21 `hard__drive-notes-telegram__010` re-runs had **no
> coverage at all**, and the chat carried each row's delivered message into the next row.
> The consequence is a genuinely false pass, not just a dirty device:
>
> | row | run | started | what the chat showed |
> |---|---|---|---|
> | 11 | `20260921-192331` (kimi-k2.6) | 19:25 | typed the chase from step 8, **sent it at 19:29** |
> | 13 | `20260921-194413` (Bonsai-2-27B) | 19:46 | at **step 6** already showed the same `Sent at 19:29` bubble |
>
> Row 13's `success=true` over 9 steps was **inherited state**: row 11 had already sent the
> exact message the task asks for, so there was nothing left to do and Bonsai reported
> success having sent nothing. The PASS was an artifact of the previous row, which is why it
> was already recorded FAIL — but the *reason* matters, because the same shape will recur
> wherever a task's deliverable is a message.
>
> **The rule this generalises to:** a run must not start while a message it is required to
> send is already sitting in the target chat. Any run that did start in that state is void
> and has to be re-taken, however it scored — a leftover message turns "did the agent do the
> work" into "was the work already done for it".
>
> Re-measured across both batches on 2026-09-22 with
> `scripts/tools/audit_telegram_inheritance.py` (a sent bubble whose stamp predates the
> run's own start is an inheritance, not an action): the `010` batch has exactly one
> inheritance (**row 13**), and the `bookmyshow` batch has **none** — row 5 is the only row
> that sent, at 12:06 against an 11:58 start, and the between-row cleanup deleted it before
> row 7 began. So the fix holds going forward, and the contamination is confined to the
> batch that ran before the cleanup existed.

> **Promoted out of this table 2026-09-21 — App UI mode drift.** A previous run leaving the
> **Calendar app in Day view** used to be undetectable here: `--verify-only` reads the
> *provider*, and the view mode lives in app state. It bit **rows 1 and 2** of the
> 2026-09-21 calendar re-runs, both of which had to be taken a second time from Schedule
> view. It is now a **blocking gate**, `verify_calendar_view_mode()`. Two details worth
> keeping:
>
> * The marker is **inverted** — the day-row content-desc names the mode you would switch
>   *into*, so `"... , Open Day View"` means the app is currently in **Schedule** view. Do
>   not "fix" `_OPEN_DAY` / `_OPEN_SCHEDULE`; pinned by the first test in
>   `tests/test_reset_phone_calendar_view.py`.
> * It **repairs** (taps "Open Schedule View") instead of warning, because "a human will
>   notice and fix it" is the exact assumption that failed. Opt out with
>   `--no-calendar-view-check`. Like `verify_meet_agenda`, it always hands back a stopped app
>   on the launcher — it runs immediately before the first task, so whatever it leaves on
>   screen *becomes* the agent's start state.

| Class | Example | Blast radius |
|---|---|---|
| Leftover app state lets the agent skip the work | Maps recents + leftover route: 7 of 13 runs never typed the query | `medium__google-maps__002`, `easy__google-maps__004` |
| ~~**Messaging leftovers inherited across runs**~~ ✅ **gated 2026-09-22** | **Telegram draft/sent bubble in the `Yuvraj Airtel` chat: ONE draft survived 7 rows and ~90 min** — row 4 composed the chase message, its Send never registered, and rows 5/6/9/11 then opened the chat to find it pre-typed ("*The message is already composed*") or already sent ("*I can see the message has been sent!*"). Now a **blocking gate** (`clear_telegram_run_leaks` / `verify_telegram_chat_clean`); the chat list is still unreadable by uiautomator, so the check opens the chat by name rather than scanning the list. | `hard__drive-notes-telegram__010`; any "message X" deliverable |
| Leftover *conferenced* event hijacks the Meet task | day-2 `easy__google-meet__004` creates "Product Demo", which day-3 Meet reports instead | `hard__google-meet-files__070` |
| **The Telegram `Send` tap does not reliably deliver** | A tap on `Text: 'Send'` at its reported centre coordinates is logged as "clicked" but the text stays in the compose box — hit by **4 runs across 2 models** (rows 3 & 6 originally, rows 3 & 4 on the 2026-09-21 re-run). Row 4 even pressed Enter and retried the button 3×. Post-send `ui_states` and the model's own closing reason are the only reliable evidence; the trajectory's "clicked" line is not. | every "message X" deliverable |
| ~~App-private seeds with no file backup~~ ✅ **fixed 2026-09-22** | OnePlus Notes `Budget Deadline` — adb cannot recreate it, but the text is now version-controlled (`assets/seeds/public/Budget Deadline (OnePlus Notes).txt`) and `restore_budget_note()` re-types + verifies it (`text_count` 518) | `hard__drive-notes-telegram__010` |
| Cloud account drift | Slides drifted to `rajceo2031`; caught only by the account gate | 25 of 60 tasks touch a cloud app |
| Live external data | BookMyShow listings, Maps ETAs, Swiggy/Amazon/Prime state | 10 of 60 tasks |
| Grader blind spots | Slides has no ground truth (1/3/8 all passed); Sheets exposes no cell data to the a11y tree | `*google-slides*`, `*google-sheets*` |

### 7.3 Scope note on the new recurring-artifact sweep

`calendar_recurring_artifacts_to_remove` is **public_v2-only, deliberately**:
`Weekly_Standup` is a legitimate *seed* for the 530 `day_N` profiles
(`scripts/seeding/verify_day1_seeds.py` asserts it). The sweep must never run there.

### 7.4 Pre-run vs post-run reset: the harness now closes the start-state hole (2026-09-22)

The distinction that matters, since "we reset between runs" was being read as covering more
than it did:

| | **Post-run reset** (`reset_phone.py --apply`, before a *batch*) | **Pre-run reset** (`cli.py`, before *every task*) |
|---|---|---|
| Scope | whole device → canonical seeds | the **focused app** only |
| Resets | files, calendar, provider DBs, now two leak repairs | the app's **screen** (force-stop + HOME) |
| Resets app **data**? | only for the two named leaks | ❌ no — a draft/edit still survives it |

So both holes were real and neither was redundant: the post-run reset cannot run between
tasks in a batch (it would wipe seeds a previous task legitimately consumed), and the
pre-run reset cannot see app content. Concretely, this is why `5–11 (vision/text) FAIL` is
**not** a start-state artifact — every one of the 13 re-runs began on the launcher
(`🏠 LAUNCHER` in its first `ui_states`), so those failures are model behaviour, not
inherited screens. The pre-run package is recorded per run as
`pre_app_reset_stopped_package` in `meta.json`, so a run that starts inside an app is now
visible in the artifacts instead of having to be inferred from `ui_states/0001`.
`get_foreground_package()` was hardened at the same time: it previously read only
`mCurrentFocus`, which is `null` whenever nothing holds input focus (transient dialog,
notification shade, mid-animation) and made the force-stop a silent no-op — three of the
2026-09-21 re-runs recorded `None` while parked inside `com.oneplus.note`. It now falls
back to `mFocusedApp`, then the resumed-activity line.

### 7.5 The Telegram draft clear gave up two ways and burned a row (fixed 2026-09-22)

The between-row leak cleanup is the **only** thing standing between a composed-but-unsent
message and the next row reading it as already handled (§7.2). It failed on row 6's draft,
and the cost was not a wrong verdict but a **wasted row**: row 11 aborted at the seed gate
without ever running, then the identical draft cleared fine on the very next attempt.

The 27-character residue is the tell. A ~127-char draft came back as
`'INOX: Symphony Mall, Avenge'`, which identifies both defects at once:

* **A single `input keyevent 67 x N` drops presses.** The flood is not a reliable delete, so
  a long draft survives it in part. Deletes are now issued in chunks of 25 with a read
  between chunks, so a partial clear is *seen* and deleted again instead of accepted.
* **`box is None` broke the whole loop.** One dump that transiently lacked the composer
  ended the cleanup — which then printed `still holds a draft after 3 attempts` having
  really tried *once*. A missing composer is now a retry (6 rounds), never a reason to bail,
  and the message no longer claims attempts that never happened.

Regression cover: `tests/test_reset_phone_run_leaks.py` gains three tests, and the first two
**fail against the previous code** — the second reproduces the misleading
`after 3 attempts` line verbatim.

Worth keeping the safety net in mind: the abort was loud and correct. The seed gate caught
the surviving draft and refused to run the row, so no contaminated result was recorded. The
defect cost a row, not a verdict.

### 7.6 A local row could silently run against the wrong model (fixed 2026-09-22)

The launcher's readiness probe asked only whether *something* answered on the shared local
port, never **which** model was behind it. A `llama-server` left on 8088 by one row would
therefore serve the next row the wrong weights — and the run would be published under the
intended row's name.

Concretely: row 13 needs `Bonsai-2-27B`, row 12 needs `gemma-4-E2B-it`. A leftover Bonsai on
8088 would have had row 12 recorded as a `gemma` result while actually running Bonsai.

`server_model()` now reads the alias the port advertises and `preset_alias()` maps each
preset to the alias `serve_gguf.sh` publishes (an unknown preset yields empty and disables
the guard rather than failing a row that may be fine). With `LOCAL_AUTOSERVE=1` the stale
server is restarted; otherwise the row is skipped and named `local-wrong-model` in the
failure list. `stop_existing_server()` targets the listener on that port only — verified to
kill 8088 while leaving an unrelated listener on 8090 untouched.

This is the same shape as the §3 `cinema` placeholder: a value that resolves perfectly and
is simply wrong, with nothing downstream positioned to notice.

### 7.7 Failed runs stayed in the run root and could be counted as results (fixed 2026-09-22)

**Scored results — one run per model, per task.** A model gets exactly one recorded run.
Harness failures are not attempts: they are void and must not be counted, and they must not
be left looking like results.

Two kinds of debris had accumulated in `assets/runs/public/`, and **18 roots were removed**:

- **15 dead roots** that produced no `output.json` — the batch killed mid-flight by the
  2026-09-22 restart (12 roots), seed-gate aborts (`20260922-121017`, `20260922-121707`,
  `20260922-203844`), and one earlier abort (`20260921-182317.aborted-step43`).
- **3 superseded runs that DID write `output.json`** — and this is the dangerous class:
  - `20260921-194413` (row 13) held `success: true` from the §4 inherited message. A voided
    pass sitting in the run root under a plain timestamped name is indistinguishable from a
    real result to anything that globs the roots.
  - `20260921-193702` (row 12) and `20260922-223255` (row 13, this session's redundant spot
    re-run) were superseded by the audited `20260921-212306` / `20260921-213754`, which are
    the roots that carry turn-based reports under `reports/turn-based/`.

After pruning, both `hard__bookmyshow__005` and `hard__drive-notes-telegram__010` have
**13 valid runs — one per model — with zero duplicates and zero dead roots**.

**Why it stayed hidden.** `androidlife_report.py:is_backup()` only skips `.bak`/`.old`-style
names, and `.aborted-<reason>` was created by *nothing in the repo* — the two that existed
were renamed by hand. So the convention was real but unenforced, and the root that most
needed it (a false pass) never got it.

**The fix.** `rerun_task_rows.sh` now calls `flag_aborted_root()` as the last step of each
row: a root that produced no `output.json` is renamed to `<ts>.aborted-seedgate` (seed gate
refused it) or `<ts>.aborted-incomplete` (the harness died), keeping `batch.log` and
`SEED_GATE_FAILED` as the explanation for why the row vanished.

A **timeout is deliberately not flagged**: it writes `output.json` and is an honest, if
void, result (Bonsai row 13), whereas no `output.json` at all means nothing was measured.
`tests/test_rerun_task_rows.py` pins both the flagging and the acceptance case, including an
abort that happens before the task directory is known.

### 7.8 The run-note sweep only covered the tasks someone remembered (fixed 2026-09-23)

§7.2's Telegram and Budget-Deadline cleanups were written because those tasks got caught
leaking. This one is the generalisation: **a task that writes an app-private note leaks on
every single row**, and nothing about force-stopping prevents it.

`medium__google-maps__002` writes "Fastest Route to Bhubaneswar Airport". Seven rows left
seven of them. Two consequences, both measured on 2026-09-23:

1. They are the *same* free-hint surface as the Maps recents — a later agent can read the
   previous row's answer off the Notes list without doing the comparison.
2. They **bury the protected seed**. `Budget Deadline` was pushed below the fold, and the
   OnePlus Notes app reopens on the last-used bottom tab (the *To-dos* tab lists no notes at
   all), so `_note_open` saw nothing. The seed gate then reported the seed as damaged and
   **aborted six good rows on a false alarm**. The seed was never touched.

**The fix.** `clear_maps_run_notes` deletes notes by title substring
(`Bhubaneswar Airport`, `parked here`) and `clear_maps_recents` clears the Maps recent
list; both are wired into `--apply` and `--leak-cleanup-only`, so `rerun_task_rows.sh`
repairs them between rows. `_note_find_title` additionally repairs the wrong-tab and
below-the-fold cases before concluding a note is missing. The seed is protected by an
explicit `NOTE_PROTECTED_TITLES` list, and the sweep never uses *Select all*.

**The lesson, stated generally:** any future "delete the run artifacts" step must be
triggered by the reset, not by a human remembering it. The two cleanups in §7.2 were
correct and still let this through because they only knew about the tasks that had already
bitten. Task→artifact knowledge belongs in the profile (`manual_ui_cleanup`) *and* in an
automated sweep; a note in `SKILL.md` alone is not a gate.

---

## 7. Two conventions to get right when publishing (found while publishing Maps row 1)

**7a. `reports/metrics/...-report.{json,md}` carry the OFFICIAL number; `reports/public/*.md`
carries the MANUAL one.** They are *supposed* to differ. Established from the generator, not
inferred: `androidlife_report.py` builds one `report` dict, dumps it to `.json`, then renders
the SAME dict to `.md` via `render_markdown()` — so the two are one artefact in two formats.
Row 8 proves which number they carry: its report states *"official 3 true success / 5.0%;
manual headline 10/60 (16.7%)"* while its metrics file says **5.0%**.

*Do not "reconcile" metrics against the run report* — that is the official/manual split. Apply
the task delta to the OFFICIAL values (row 1: 32 -> 33, 53.3% -> 55.0%), leaving the manual
report to carry its own reconciled number (37/60, 61.7%).

**7b. But `.md` and `.json` must never disagree with each other**, and in 6 of 13 rows they do.
That IS a bug — one dict, two files. Rebuild the `.md` instead of hand-editing it:

```bash
uv run python -c "
import json, sys; sys.path.insert(0,'scripts/eval'); import androidlife_report as ar
p='reports/metrics/public/<root>-report'
open(p+'.md','w').write(ar.render_markdown(json.load(open(p+'.json'))))"
```

Regenerating row 1's surfaced a second drift the hand-edit had preserved: KBIQ read
`0/4 KB tasks with a correct KB answer` where the JSON has `0/3 queries`.

Known-current drift (regenerate each when touched): rows **11** (14.3 vs 17.1), **12** (33.3 vs
29.6), **13** (42.9 vs 40.0) — all three belong to the rows 9-13 hand pass. Rows 2, 3, 5 and 6
were fixed while publishing the Maps batch (row 2 48.3 -> 50.0, row 3 61.7 -> 63.3, row 5 BMS
`hard` 35.3 -> 41.2, row 6 65.0 -> 63.3); rows 1, 4, 7, 8, 9, 10 now agree exactly.

**7d. A third divergence axis: the report's manual average vs the metrics JSON's
average.** These are *different metrics on different bases* and the verifier already
treats the gap as a **warning**, not a mismatch (`steps(official): metrics JSON X vs
published Y`, and likewise for `queries` and `uiq`).

**Re-audited 2026-09-26 (all 7 warnings, all three axes).** The verifier's warning list is
not steps-only — `queries` and `uiq` are cross-checked on the same official/manual split.
The full current list:

| row | model | axis | official (metrics JSON) | published (report table) | cause |
|---|---|---|---|---|---|
| 3 | gemini-3.1-flash-lite | steps | 8.4 | 8.12 | audit basis, unexplained residual |
| 3 | gemini-3.1-flash-lite | uiq | 0.1111 | 0.125 | **denominator**: generator = 1 ÷ (7 interaction + 2 triggered) = 1/9; audit = 1/8 |
| 4 | seed-2.0-lite | steps | 12.8833 | 13.59 | audit basis, unexplained residual |
| 4 | seed-2.0-lite | queries | 0.5714 | 0.67 | **denominator**: generator = 4 asks ÷ 7 interaction tasks = 4/7; audit = 4/6 |
| 6 | seed-2.0-lite (VISION) | uiq | 0.1 | 0.2 | **stale JSON** — fresh artifact recompute gives 0.2, i.e. the published figure |
| 7 | gpt-5.6-luna (TEXT) | steps | 41.2833 | 42.22 | audit basis, unexplained residual |
| 13 | Bonsai-2-27B (TEXT) | steps | 4.1875 | 12.73 | **resolved → §7e** |

Rows 1, 2, 5, 8, 9, 10, 11 and 12 agree on all three axes.

*Do not force them equal.* Row 7 briefly did, on the theory that the 0.93 gap was exactly the
2026-09-21 `calendar_002` re-run's -56/60; it was reverted because rows 3/4/13 show the same
kind of gap with no such tidy explanation, i.e. the two numbers are genuinely computed
differently. Apply the task delta to **each** on its own basis and leave the residual alone.

**Evidence that both series are being maintained (not one going stale).** Every re-run's delta
lands on *both* bases by the same amount, within the report's 2-dp rounding — measured across
the 2026-09-24/25 meet batch: row 3 +0.03 (report) vs +0.0333 (JSON), row 4 −0.08 vs −0.0834,
row 6 −0.02 vs −0.0167, row 7 +0.70 vs +0.70. A stale series would drift by zero. The residual
is what stays behind, and it does not move.

**Reproduction notes (2026-09-26).** The official figures are reproducible from the Hub
artifacts via `load_run_record()` + `benchmark_metrics`: row 3 `uiq` = 1/9 and
`queries` = 5/7, row 4 `queries` = 4/7 all match their JSONs exactly, which is what pins the
cause to the `triggered` term in `user_interaction_quality_factmatch` and to the audit's own
interaction denominator. Note the JSONs are hand-adjusted per re-run, **not** regenerated, so a
fresh aggregate over today's (in-place-merged) artifacts does not equal them — expected, not a
defect. And §7b holds: every `metrics/*-report.md` is a pure `render_markdown()` of its `.json`
(15/15 verified 2026-09-26).

**7e. Row 13's steps gap (4.19 vs 12.73) — RESOLVED, it is a timeout artifact.** Every task
that times out writes `steps: 0` to its `output.json` (the step counter is lost on the timeout
path), so the official mean covers only the terminating tasks: **67 steps ÷ 16 records =
4.1875**. The report's **12.73** is the true effort counted from the trajectories
(**191 tool calls ÷ 15 tasks**). The published figure is the right one and the report says so in
its own note at `reports/public/public-20260920-044846.md`; the official one must not be quoted
as a speed figure. Nothing left to hand-pass here — this is the *explanation* of why the two
bases differ, and it is the cleanest single example of the class.

**7c. Every report has a third, pre-existing class of drift: its own three totals disagree.**
Row 1 carried 36 (outcome + metrics tables), 35 (prose), 34 (totals + day headers) for the same
60 tasks; the per-task verdict rows were 36. Row 2 carries 32 (metrics table + prose) vs 31
(totals + day headers). Reconcile against the **per-task verdict rows**, which are ground truth.

*Caveat:* that counting works cleanly only for rows 1-8. Rows 9-13 use a different table shape
(`Success Rate (N runs)`, partial runs, orphaned tasks) where the verdict rows do not sum to the
headers by simple counting — row 2 already needs a manual read (its day tables parse as
19/16/20 rows and a hallucination row is not machine-findable). Each of those rows needs a hand
pass, not arithmetic.

---

## 8. Re-run battery telemetry — N/A (no proxy), not a median fill (2026-09-25)

### 8a. The problem

All charge-night re-runs recorded `battery_level_delta_pct = 0`. Leaving that 0 next to
neighbours with real drains makes a re-run look free; **inventing** a same-category median
to stand in for the missing reading was tried on 2026-09-24 and is **withdrawn**. A proxy
is not a measurement.

Thermals were never touched and stay as measured.

### 8b. The rule (current)

For every re-run task taken on charge:

* `battery_level_delta_pct` is **N/A** in the reports (not a median, not a guessed drain).
* Artifacts keep the honest on-charge reading of **0** (any median that was written into
  `run_metrics.json` is being restored to 0).
* The run's published **Battery drain (Δ sum)** is the sum over **untouched tasks only** —
  re-run cells are excluded. That sum equals the pre-fill "published" column below.

### 8c. Aggregates (untouched tasks only)

| row | root | batteryDrain (excl. re-runs) | re-runs excluded |
|---|---|---|---|
| 1 | 2026-08-28-002424 | **−69 %** | calendar, slides, 010, maps, bookmyshow |
| 2 | 2026-08-29-153657 | **−90 %** | calendar, slides, 010, maps, bookmyshow |
| 3 | 20260826-105200 | **−21 %** | calendar, slides, 010, maps, bookmyshow |
| 4 | 2026-08-30-143554 | **−29 %** | slides, 010, maps, bookmyshow |
| 5 | 20260909-043419 | **−79 %** | 010, maps, bookmyshow |
| 6 | 20260905-051950 | **−51 %** | calendar, slides, 010, maps, bookmyshow |
| 7 | 20260906-063336 | **−85 %** | calendar, slides, 010, maps, bookmyshow |
| 8 | 20260910-041531 | **−87 %** | 010, maps, bookmyshow, meet |
| 9 | 20260914-061846 | **−96 %** | 010, maps *(bookmyshow orphan — already excluded)* |
| 10 | 20260916-011341 | **−81 %** | calendar, 010, maps, bookmyshow |
| 11 | 2026-08-30-021852 | **−94 %** | calendar, slides, 010, maps, bookmyshow |
| 12 | 20260917-160018 | **−93 %** | calendar, 010, maps, bookmyshow |
| 13 | 20260920-044846 | **−92 %** | calendar, 010, maps *(bookmyshow orphan — already excluded)*; phone still 100%→0% overall |

The 2026-09-24 median-fill figures (−70 / −80 / −16 / … / −100) and the six-row
bookmyshow-fold correction are historical only — they must not be re-applied.

### 8d. Where the numbers live

1. **Artifacts** — re-run `run_metrics.json` carry `battery_level_delta_pct = 0` (on charge).
   Median fills written into them are restored to 0; reports label those cells **N/A**.
2. **Reports** — each battery row uses the excl.-re-runs sum above, with a
   `> **Battery Δ note:**` stating N/A / no proxy.
3. **Leaderboard** — `batteryDrain` matches the table (`verify_leaderboard.py`).

### 8e. BookMyShow publication (all 13 rows)

The 2026-09-22 BookMyShow re-runs had verdicts written into every report but their artifacts were
never uploaded, so HF still served the *originals*. Replaced in place for all 13:
**1102 file ops, ~435 MB** (row 13's dir created fresh; rows 9/12's partial dirs completed).

### 8f. `review.json` is not backfilled anywhere (decided 2026-09-24)

Only `medium__google-maps__002` carries a `review.json`, in all 13 roots, and those are genuine
outputs of the live batch — `rerun_task_rows.sh` ran with `REVIEW_GATE=1` and stopped after each
row until the file existed, which is why they could be published at the time.

The other four redo tasks have **none**, and a backfill attempt was reverted:

| task | re-run | how it was really reviewed | `review.json` |
|---|---|---|---|
| `medium__google-maps__002` | 2026-09-23 | live, through the gate | **13/13** |
| `easy__google-slides__001` | 2026-09-21 | by hand (gate didn't exist) | 0 |
| `easy__calendar__002` | 2026-09-21 | by hand (gate didn't exist) | 0 |
| `hard__bookmyshow__005` | 2026-09-22 | by hand (gate didn't exist) | 0 |
| `hard__drive-notes-telegram__010` | 2026-09-21 | by hand (gate didn't exist) | 0 |

A backfill for the four was written on 2026-09-23 and **deleted on 2026-09-24**, having been
verified byte-for-byte back to the pre-commit state on the Hub. The file's whole value is that
its presence means "a batch was gated here"; fabricating one *post hoc* for a review performed
before the gate existed produces something indistinguishable in the corpus from a genuine gate
record, and it re-dates the review. Their reviews live where they were actually done: the
per-row verdict tables in sections 3–6 and the `↻ re-run` notes in the 13 reports.

`review_slides` and `review_calendar` remain in `review_rerun_row.py`, so a *future* re-run of
either task is gated and writes a `review.json` with true provenance. There is **no** reviewer
for `hard__bookmyshow__005` or `hard__drive-notes-telegram__010` — a matching one was written
and then reverted with the backfill, since it existed only to manufacture the files.

### 8h. How re-runs are published: in place, for every task

There is **one** publication rule and it applies to all five redo tasks: the re-run replaces the
task directory **inside the canonical run root**, and the root keeps its identity. No re-run is
ever published as a root of its own.

| | |
|---|---|
| run roots on HF | **15** — the canonical rows, plus `2026-08-26-184934` and `20260901-002701`. **Zero** re-run roots |
| redo-task dirs in those roots | **65** (13 rows × 5 tasks) |
| byte-identical to a local re-run root | **56** |
| not identical | **9** — exactly the rows deliberately left alone |

The 9 are `easy__calendar__002` rows 4, 5, 8, 9 and `easy__google-slides__001` rows 5, 8, 9, 10,
12 — precisely the rows those two sections record as unaffected and correctly not re-run. Row 13
on all five tasks is a self-match against the canonical root (which is local for that row), so
its "match" is uninformative; its calendar re-run is evidenced instead by
`assets/runs/_rerun_backups/20260920-044846/easy-calendar-002/`, which holds the displaced
original (`started_at_utc` 2026-09-20T04:00:09).

**Why the backup exists for that one directory and no other.** Merging in place overwrites the
local original. For rows 1–12 that costs nothing, because the canonical roots are not on this
machine — only the published copy is touched. Row 13's canonical root *is* local
(`20260920-044846`), so its in-place merge would have destroyed the pre-fix run, and the original
was moved to `_rerun_backups/` first. Same for the three superseded first-pass runs in
`_rerun_backups/thrownaway/`.

So "merged in place" is not a property of `easy__calendar__002` — it is the mechanism for every
re-run. The only thing unique to row 13 is that its calendar re-run was *captured* in the
canonical root rather than in a separate `2026092x` working root, which is what forced the
backup. Earlier wording in §6 implied the former; §6 and the header table now say the latter.

### 8i. Still open

* **§2's meet re-runs were published in the reports/metrics/leaderboard before the Hub had the
  artifacts — now fixed, but this is the check to repeat for any future section.** Verified
  2026-09-26 against `runs/` on `YuvrajSingh9886/androidlife-public` (15 canonical roots, zero
  re-run roots): rows 1-8 still carried the **pre-fix** meet directory (row 3:
  `"The Weekly Sync meeting was not found"` / `steps: 3` / `success: false`, where the published
  re-run is `"Weekly Sync, Weekly Agenda.txt"` / `5` / `true`), row 10 carried a meet directory
  with **no `output.json`**, and rows 9, 11, 12, 13 had no meet directory at all; HF's
  `reports/` was also the pre-meet snapshot (last commit `bfb56a07`, 2026-09-25 07:17 UTC,
  while the meet rows were written 19:05-20:20 UTC). **Merged in place on 2026-09-26** — the 13
  local re-run roots replaced `runs/<canonical>/day3/hard-google-meet-files-070/` (524 MB
  added, 359 pre-fix trajectory files deleted, `30926a1e`), all 13 file sets now match their
  re-run root exactly with a single trajectory dir, and the reports were pushed (`39` files).
  The lesson: a section is not published until the **artifacts** are, and the only proof is a
  file-set comparison against the local re-run root — the reports alone will look right.
* ~~`hard__google-meet-files__070` — blocked on a manually seeded recurring DAILY `Weekly Sync`
  calendar event.~~ **Resolved 2026-09-24:** the event was seeded through the Calendar app UI
  (conference link + guest list), the pre-run gate now asserts both, and all 13 rows were
  re-run — 9 PASS / 4 FAIL (§2).
* The 010 and BookMyShow re-runs have no `review.json` (see 8f). The sidecar mechanism cannot
  cover 010 at all: `delivery_checks_public.json` lists only BookMyShow, and 010 must stay out
  of it because its send is conditional — gating it would fail a correct decision *not* to send.
  The discriminator for 010 is the final screen (a bubble ending `Sent at` vs. text left in an
  `EditText`), which is what the hand review used.
