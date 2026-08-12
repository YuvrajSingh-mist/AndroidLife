// Builds website/assets/data/trajectories/* and copies per-task trajectory GIFs
// into website/assets/trajectories/* from the canonical day-1/2/3 run folders.
//
// Usage (from the repo root):
//   node website/tools/export_trajectories.mjs
//
// Reads (canonical runs — the same events that were traced into Phoenix):
//   day1 -> assets/runs/full-bench/2026-08-09-153930/day1
//   day2 -> assets/runs/full-bench/2026-08-10-234158/day2
//   day3 -> assets/runs/2026-08-11-040846/day3            (reruns merged)
// For each task dir it reads meta.json (model, task_id, timestamps), output.json
// (success/reason) and the newest trajectories/<ts>/trajectory.json (the agent
// step stream that Phoenix traced) + screenshots/trajectory.gif.
//
// Writes:
//   website/assets/data/trajectories/<day>/<task_id>.json  (condensed steps)
//   website/assets/data/trajectories/index.json            (availability index)
//   website/assets/trajectories/<day>/<task_id>/trajectory.gif (copied)

import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync, statSync, readdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");

const DAY_RUN_ROOTS = {
  1: "assets/runs/full-bench/2026-08-09-153930/day1",
  2: "assets/runs/full-bench/2026-08-10-234158/day2",
  3: "assets/runs/2026-08-11-040846/day3",
};

const OUT_DATA = "website/assets/data/trajectories";
const OUT_GIFS = "website/assets/trajectories";

// Task renames between the run and the current dataset: the run was filed under
// the OLD id. Map old -> current so the site can show the trajectory under the
// renamed task_id. (From the task authoring history.)
const TASK_ID_ALIASES = {
  "medium__obsidian__001": "medium__google-docs__001",
};

function joinPath(rel) {
  return resolve(ROOT, rel);
}

function readJson(rel) {
  try {
    return JSON.parse(readFileSync(joinPath(rel), "utf-8"));
  } catch {
    return null;
  }
}

function isDir(p) {
  try {
    return statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function readDirNames(p) {
  try {
    return readdirSync(p);
  } catch {
    return [];
  }
}

// Condense the raw FastAgent event stream into human-readable steps.
// Each FastAgentResponseEvent opens a step (thought + code + token usage) and the
// ToolExecutionEvent(s) + output that follow it are attached to that step.
function condenseTrajectory(events) {
  const steps = [];
  let current = null;

  for (const ev of events) {
    switch (ev.type) {
      case "FastAgentResponseEvent": {
        current = {
          index: steps.length,
          thought: ev.thought || "",
          code: ev.code || "",
          usage: ev.usage || null,
          tools: [],
          output: "",
        };
        steps.push(current);
        break;
      }
      case "ToolExecutionEvent": {
        if (!current) break;
        current.tools.push({
          tool_name: ev.tool_name || "",
          tool_args: ev.tool_args ?? null,
          success: Boolean(ev.success),
          summary: ev.summary || "",
        });
        break;
      }
      case "FastAgentOutputEvent": {
        if (!current) break;
        current.output = (current.output ? current.output + "\n" : "") + (ev.output || "");
        break;
      }
      default:
        break;
    }
  }
  return steps;
}

function newestTrajectoryDir(taskDir) {
  const trajRoot = `${taskDir}/trajectories`;
  if (!isDir(trajRoot)) return null;
  const dirs = readDirNames(trajRoot).filter((n) => isDir(`${trajRoot}/${n}`));
  if (!dirs.length) return null;
  dirs.sort().reverse(); // timestamps sort lexically (YYYYMMDD_HHMMSS_hex)
  return `${trajRoot}/${dirs[0]}`;
}

// Downscale a full-res screenshot PNG into a small JPEG for the website
// (full-res would be ~470KB each → ~1GB for all steps). Prefers `sips` (macOS)
// then `ffmpeg`; returns false if neither is available.
function downscaleToJpg(srcPng, destJpg) {
  try {
    execFileSync("sips", ["-s", "format", "jpeg", "-s", "formatOptions", "72", "--resampleHeight", "560", srcPng, "--out", destJpg], { stdio: "ignore" });
    return true;
  } catch {
    try {
      execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", srcPng, "-vf", "scale=-2:560", "-q:v", "4", destJpg], { stdio: "ignore" });
      return true;
    } catch {
      return false;
    }
  }
}

// Copy downscaled per-step screenshots into the site assets. Screenshots are
// named 0000.png..NNNN.png and align 1:1 with condensed steps. Returns count.
function exportScreenshots(trajDir, outGifAbsDir) {
  const shotsDir = `${trajDir}/screenshots`;
  if (!isDir(shotsDir)) return 0;
  const names = readDirNames(shotsDir).filter((n) => /^\d{4}\.png$/.test(n)).sort();
  if (!names.length) return 0;
  const outShots = `${outGifAbsDir}/screenshots`;
  mkdirSync(outShots, { recursive: true });
  let ok = 0;
  for (const n of names) {
    const jpg = `${outShots}/${n.replace(/\.png$/, ".jpg")}`;
    if (downscaleToJpg(`${shotsDir}/${n}`, jpg)) ok++;
  }
  return ok;
}

function main() {
  const index = { tasks: {} };
  const daySummaries = {};

  for (const [dayStr, relRoot] of Object.entries(DAY_RUN_ROOTS)) {
    const day = Number(dayStr);
    const root = joinPath(relRoot);
    if (!isDir(root)) {
      console.warn(`  (skip) day ${day}: missing run root ${relRoot}`);
      continue;
    }

    const taskDirs = readDirNames(root).filter((n) => isDir(`${root}/${n}`)).sort();

    let ok = 0;
    let noGif = 0;
    let realRuns = 0;
    for (const name of taskDirs) {
      const taskDir = `${root}/${name}`;
      const meta = readJson(`${relRoot}/${name}/meta.json`);
      if (!meta) continue; // not a real run folder (e.g. stray dirs with no meta.json)
      realRuns++;
      const output = readJson(`${relRoot}/${name}/output.json`);
      const trajDir = newestTrajectoryDir(taskDir);

      const taskId = (meta && meta.task_id) || name;
      const model = (meta && meta.model) || "";
      const success = output ? Boolean(output.success) : null;
      const reason = (output && output.reason) || "";
      const stepsCount = (output && output.steps) || 0;
      const startedAt = (meta && meta.started_at_utc) || "";
      const endedAt = (meta && meta.ended_at_utc) || "";

      const entry = {
        task_id: taskId,
        day,
        dir: name,
        model,
        success,
        reason,
        steps: stepsCount,
        started_at_utc: startedAt,
        ended_at_utc: endedAt,
        has_trajectory: false,
        gif: null,
        data: null,
      };

      if (trajDir) {
        const events = readJson(`${trajDir.replace(ROOT + "/", "")}/trajectory.json`);
        if (events && Array.isArray(events)) {
          const steps = condenseTrajectory(events);
          const gifRel = `day${day}/${taskId}`;
          const gifAbsDir = joinPath(`${OUT_GIFS}/${gifRel}`);
          const screenshotCount = exportScreenshots(trajDir, gifAbsDir);
          // Tag each step with its screenshot filename (0000.jpg..NNNN.jpg).
          for (let i = 0; i < steps.length; i++) {
            if (i < screenshotCount) steps[i].screenshot = `${String(i).padStart(4, "0")}.jpg`;
          }
          const dataRel = `day${day}/${taskId}.json`;
          const dataAbs = joinPath(`${OUT_DATA}/${dataRel}`);
          mkdirSync(dirname(dataAbs), { recursive: true });
          writeFileSync(
            dataAbs,
            JSON.stringify(
              {
                task_id: taskId,
                day,
                dir: name,
                model,
                success,
                reason,
                steps_count: steps.length,
                tool_call_count: steps.reduce((n, s) => n + s.tools.length, 0),
                screenshot_count: screenshotCount,
                screenshot_base: `assets/trajectories/day${day}/${taskId}/screenshots`,
                started_at_utc: startedAt,
                ended_at_utc: endedAt,
                steps,
              },
              null,
              2
            ) + "\n",
            "utf-8"
          );
          entry.has_trajectory = true;
          // Site-root-relative path (pages under website/pages/ prefix with ../)
          entry.data = `assets/data/trajectories/${dataRel}`;
          entry.step_count = steps.length;
          entry.screenshot_count = screenshotCount;
          ok++;
        }

        const gif = `${trajDir}/screenshots/trajectory.gif`;
        if (existsSync(gif)) {
          const gifRel = `day${day}/${taskId}/trajectory.gif`;
          const gifAbs = joinPath(`${OUT_GIFS}/${gifRel}`);
          mkdirSync(dirname(gifAbs), { recursive: true });
          copyFileSync(gif, gifAbs);
          entry.gif = `assets/trajectories/${gifRel}`;
        } else {
          noGif++;
        }
      } else {
        noGif++;
      }

      index.tasks[taskId] = entry;
      // Register the same trajectory under the current (renamed) task id too.
      const alias = TASK_ID_ALIASES[taskId];
      if (alias && alias !== taskId) {
        index.tasks[alias] = { ...entry, task_id: alias, is_alias: true, aliased_from: taskId };
      }
    }

    daySummaries[day] = { total: realRuns, with_trajectory: ok, without_gif: noGif };
    console.log(`  day ${day}: ${ok}/${realRuns} tasks with trajectory (${noGif} without gif)`);
  }

  mkdirSync(joinPath(OUT_DATA), { recursive: true });
  const indexRel = "website/assets/data/trajectories/index.json";
  writeFileSync(
    joinPath(indexRel),
    JSON.stringify(
      {
        generated: new Date().toISOString(),
        note: "Per-task agent trajectories (the FastAgent step stream traced into Phoenix) + trajectory.gif replays, exported from the canonical day-1/2/3 run folders.",
        days: daySummaries,
        tasks: index.tasks,
      },
      null,
      2
    ) + "\n",
    "utf-8"
  );
  console.log(`Wrote ${joinPath(indexRel)}`);
}

main();
