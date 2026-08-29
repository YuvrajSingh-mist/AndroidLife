// Builds website/assets/data/site_data.json from the real benchmark datasets.
//
// Usage (from the repo root):
//   node website/tools/build_site_data.mjs
//
// Reads:
//   benchmarks/dailyBench-600/DailyBench_530_v1.json  (the 533-task private set)
//   benchmarks/dailyBench-600/DailyBench_public_v2.json (the 50-task public preview)
//
// Writes:
//   website/assets/data/site_data.json  (consumed by the static website)
//
// Run `npm i` or use `npx --yes` if node:fs/json are unavailable via global node.

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const OUT = joinPath("website/assets/data/site_data.json");

function joinPath(rel) {
  return resolve(ROOT, rel);
}

function readJson(rel) {
  return JSON.parse(readFileSync(joinPath(rel), "utf-8"));
}

function primaryApp(task) {
  const apps = task.apps && task.apps.length ? task.apps : [task.app];
  return apps[0];
}

function main() {
  const full = readJson("benchmarks/dailyBench-600/DailyBench_530_v1.json");
  const pub = readJson("benchmarks/dailyBench-600/DailyBench_public_v2.json");
  const tasks = full.tasks;
  const publicTasks = pub.tasks;

  const stats = {
    task_count: tasks.length,
    day_count: 28,
    app_count: new Set(tasks.map(primaryApp)).size,
    cross_app_count: tasks.filter((t) => t.is_cross_app || t.cross_app_required).length,
    max_points: tasks.reduce((sum, t) => sum + (t.points || 0), 0),
    easy: tasks.filter((t) => t.bucket === "easy").length,
    medium: tasks.filter((t) => t.bucket === "medium").length,
    hard: tasks.filter((t) => t.bucket === "hard").length,
    hard_ask_user: tasks.filter((t) => t.bucket === "hard" && t.is_ask_user).length,
    hard_deterministic: tasks.filter((t) => t.bucket === "hard" && !t.is_ask_user).length,
    placeholder_count: tasks.reduce((sum, t) => sum + (t.placeholder_count || 0), 0),
  };

  // Per-app coverage, grouped by primary app, ordered by total count desc.
  const byApp = new Map();
  for (const t of tasks) {
    const app = primaryApp(t);
    if (!byApp.has(app)) byApp.set(app, []);
    byApp.get(app).push(t);
  }
  const categories = [...byApp.entries()]
    .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))
    .map(([app, ts]) => {
      const diff = { easy: 0, medium: 0, hard: 0 };
      for (const t of ts) diff[t.bucket] = (diff[t.bucket] || 0) + 1;
      const cross = ts.filter((t) => t.is_cross_app || t.cross_app_required).length;
      return {
        id: app.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        slug: app.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        name: app,
        description: `${ts.length} task${ts.length === 1 ? "" : "s"} in ${app}`,
        count: ts.length,
        difficulty: diff,
        cross_app: cross,
      };
    });

  // Per-day distribution.
  const byDay = new Map();
  for (const t of tasks) {
    const d = t.day || 0;
    if (!byDay.has(d)) byDay.set(d, []);
    byDay.get(d).push(t);
  }
  const days = [];
  for (let d = 1; d <= 28; d++) {
    const ts = byDay.get(d) || [];
    const diff = { easy: 0, medium: 0, hard: 0 };
    let ask = 0;
    for (const t of ts) {
      diff[t.bucket] = (diff[t.bucket] || 0) + 1;
      if (t.is_ask_user) ask++;
    }
    days.push({
      day: d,
      count: ts.length,
      easy: diff.easy,
      medium: diff.medium,
      hard: diff.hard,
      ask_user: ask,
      deterministic: diff.hard - ask,
      apps: new Set(ts.map(primaryApp)).size,
    });
  }

  // Public benchmark stats — the homepage "Benchmark Summary". Computed from the
  // actual public dataset + sidecars so the numbers always match the 60 tasks
  // shown on the site (cross-checked against docs/benchmark-spec-public.md).
  let hcSidecar = {};
  let kbSidecar = {};
  try {
    hcSidecar = readJson("benchmarks/dailyBench-600/hallucination_controls.json");
  } catch {}
  try {
    kbSidecar = readJson("benchmarks/dailyBench-600/multiturn_kb_public.json");
  } catch {}

  const publicIdSet = new Set(publicTasks.map((t) => t.task_id));
  const publicHc = Object.keys(hcSidecar).filter((id) => publicIdSet.has(id));
  const publicMulti = Object.keys(kbSidecar).filter((id) => publicIdSet.has(id));
  const publicMultiSet = new Set(publicMulti);

  const pubBuckets = { easy: 0, medium: 0, hard: 0 };
  const pubHardSplit = { single: 0, multi: 0, det: 0 };
  const pubPerDay = new Map();
  const pubApps = new Set();
  const pubPlaceholders = [];
  let pubSingle = 0;
  let pubCross = 0;
  let pubTwoApp = 0;
  let pubThreeApp = 0;

  for (const t of publicTasks) {
    pubBuckets[t.bucket] = (pubBuckets[t.bucket] || 0) + 1;
    const apps = t.apps && t.apps.length ? t.apps : [t.app];
    for (const a of apps) pubApps.add(a);
    if (apps.length > 1) {
      pubCross++;
      if (apps.length === 2) pubTwoApp++;
      else pubThreeApp++;
    } else {
      pubSingle++;
    }
    for (const p of t.placeholders || []) pubPlaceholders.push(p);
    if (t.bucket === "hard") {
      if (t.is_ask_user) {
        if (publicMultiSet.has(t.task_id)) pubHardSplit.multi++;
        else pubHardSplit.single++;
      } else {
        pubHardSplit.det++;
      }
    }
    const d = t.day || 0;
    if (!pubPerDay.has(d)) {
      pubPerDay.set(d, { day: d, easy: 0, medium: 0, hard: 0, single: 0, multi: 0, det: 0, hc: 0, total: 0 });
    }
    const row = pubPerDay.get(d);
    row[t.bucket]++;
    row.total++;
    if (t.bucket === "hard") {
      if (t.is_ask_user) {
        if (publicMultiSet.has(t.task_id)) row.multi++;
        else row.single++;
      } else {
        row.det++;
      }
    }
    if (publicHc.includes(t.task_id)) row.hc++;
  }

  const phCounts = new Map();
  for (const p of pubPlaceholders) phCounts.set(p, (phCounts.get(p) || 0) + 1);
  const topPlaceholder = [...phCounts.entries()].sort((a, b) => b[1] - a[1])[0] || null;

  const pubAskSingle = publicTasks.filter((t) => t.is_ask_user && !publicMultiSet.has(t.task_id)).length;

  const public_stats = {
    task_count: publicTasks.length,
    day_count: 3,
    success_graded: publicTasks.length - publicHc.length,
    hc_count: publicHc.length,
    buckets: pubBuckets,
    hard_split: pubHardSplit,
    ask_user_single: pubAskSingle,
    ask_user_multi: pubHardSplit.multi,
    ask_user_total: pubAskSingle + pubHardSplit.multi,
    single_app: pubSingle,
    cross_app: pubCross,
    two_app: pubTwoApp,
    three_app: pubThreeApp,
    app_count: pubApps.size,
    placeholder_uses: pubPlaceholders.length,
    placeholder_keys: phCounts.size,
    top_placeholder: topPlaceholder ? { key: topPlaceholder[0], uses: topPlaceholder[1] } : null,
    per_day: [...pubPerDay.values()].sort((a, b) => a.day - b.day),
  };

  // Public examples — the full public bench we have runs for. Cross-reference
  // the trajectory index (if already exported) so each example carries its
  // run + trajectory availability, and only tasks with a recorded run are shown
  // on the homepage (matching the "we have these" public set).
  let trajIndex = null;
  try {
    trajIndex = readJson("website/assets/data/trajectories/index.json");
  } catch {
    trajIndex = null;
  }
  const publicRuns = (trajIndex && trajIndex.public) || {};
  const hasPublicRun = (id) => Boolean(publicRuns[id]);

  const public_examples = publicTasks
    .filter((t) => hasPublicRun(t.task_id))
    .slice()
    .sort((a, b) => {
      const order = { easy: 0, medium: 1, hard: 2 };
      return order[a.bucket] - order[b.bucket] || a.task_id.localeCompare(b.task_id);
    })
    .map((t) => {
      const run = publicRuns[t.task_id] || {};
      const runs = Array.isArray(run.runs) ? run.runs : [];
      return {
        task_id: t.task_id,
        difficulty: t.bucket,
        category_name: primaryApp(t),
        prompt: t.prompt_text,
        points: t.points || 1,
        cross_app: Boolean(t.is_cross_app || t.cross_app_required),
        is_ask_user: Boolean(t.is_ask_user),
        placeholder_count: t.placeholder_count || 0,
        day: run.day || t.day || 0,
        model: run.model || "",
        success: run.success ?? null,
        has_trajectory: Boolean(run.has_trajectory),
        run_count: runs.length ? runs.length : (run.has_trajectory ? 1 : 0),
        set: "public",
      };
    });

  // Every task in the full 530 set, with the fields the site filters/renders on.
  // The full task list IS the benchmark (a fixed 28-day schedule); the prompts are
  // the task text. ask_user_fact / hidden answers are NOT exported here.
  const task_list = tasks
    .slice()
    .sort((a, b) => a.day - b.day || a.task_id.localeCompare(b.task_id))
    .map((t) => ({
      task_id: t.task_id,
      bucket: t.bucket,
      difficulty: t.bucket,
      day: t.day,
      app: primaryApp(t),
      apps: t.apps && t.apps.length ? t.apps : [t.app],
      is_ask_user: Boolean(t.is_ask_user),
      is_deterministic: t.bucket === "hard" && !t.is_ask_user,
      cross_app: Boolean(t.is_cross_app || t.cross_app_required),
      points: t.points || 1,
      placeholder_count: t.placeholder_count || 0,
      prompt: t.prompt_text,
      note: t.note || "",
    }));

  const data = {
    title: "DailyBench300",
    summary: "28-day Android agent benchmark across 533 real-phone tasks, measuring success, cost, battery, and heat.",
    stats,
    categories,
    days,
    public_stats,
    public_examples,
    tasks: task_list,
  };

  writeFileSync(OUT, JSON.stringify(data, null, 2) + "\n", "utf-8");
  console.log(`Wrote ${OUT}`);
  console.log(`  categories: ${categories.length} apps · days: ${days.length} · public examples: ${public_examples.length} · tasks: ${task_list.length}`);
  console.log(`  stats: ${JSON.stringify(stats)}`);
  console.log(`  public_stats: ${JSON.stringify(public_stats)}`);
}

main();
