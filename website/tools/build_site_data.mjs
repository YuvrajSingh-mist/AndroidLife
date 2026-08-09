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

  // Public examples.
  const public_examples = publicTasks
    .slice()
    .sort((a, b) => {
      const order = { easy: 0, medium: 1, hard: 2 };
      return order[a.bucket] - order[b.bucket] || a.task_id.localeCompare(b.task_id);
    })
    .map((t) => ({
      task_id: t.task_id,
      difficulty: t.bucket,
      category_name: primaryApp(t),
      prompt: t.prompt_text,
      points: t.points || 1,
      cross_app: Boolean(t.is_cross_app || t.cross_app_required),
      is_ask_user: Boolean(t.is_ask_user),
      placeholder_count: t.placeholder_count || 0,
    }));

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
    public_examples,
    tasks: task_list,
  };

  writeFileSync(OUT, JSON.stringify(data, null, 2) + "\n", "utf-8");
  console.log(`Wrote ${OUT}`);
  console.log(`  categories: ${categories.length} apps · days: ${days.length} · public examples: ${public_examples.length} · tasks: ${task_list.length}`);
  console.log(`  stats: ${JSON.stringify(stats)}`);
}

main();
