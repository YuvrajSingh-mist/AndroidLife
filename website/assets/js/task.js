// Task detail page logic: loads task metadata from site_data.json, the per-task
// trajectory from data/trajectories/index.json + dayN/<task_id>.json, then renders
// the task state, prompt, the trajectory replay GIF and a step-by-step viewer for
// the actual model trajectory (the FastAgent step stream that was traced to Phoenix).

const SITE_DATA = document.body.dataset.siteData || "../assets/data/site_data.json";
const TRAJ_INDEX = document.body.dataset.trajectoryIndex || "../assets/data/trajectories/index.json";

// index.json stores site-root-relative paths; pages live under website/pages/,
// so any task-relative asset path needs a leading ../ to resolve from the page.
function pagePath(rootRel) {
  if (!rootRel) return rootRel;
  return rootRel.startsWith("../") || rootRel.startsWith("http") ? rootRel : `../${rootRel}`;
}

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

// --- Lightweight syntax highlighting (muted colors, no external lib) ---

// Pretty-print + colorize a JSON value: keys, strings, numbers, booleans/null.
function highlightJson(value) {
  if (value == null) return "";
  let text;
  try {
    text = JSON.stringify(value, null, 2);
  } catch {
    text = String(value);
  }
  return escapeHtml(text).replace(
    /("(?:[^"\\]|\\.)*")(\s*:)?|\b(true|false|null)\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
    (match, str, colon, kw, num) => {
      if (str !== undefined) {
        return colon
          ? `<span class="tok-key">${str}</span>${colon}`
          : `<span class="tok-str">${str}</span>`;
      }
      if (kw !== undefined) return `<span class="tok-kw">${kw}</span>`;
      if (num !== undefined) return `<span class="tok-num">${num}</span>`;
      return match;
    }
  );
}

// Colorize the XML-ish function-call blocks the agent emits (e.g.
// <function_calls><invoke name="click">…): tag names + attribute names/values.
function highlightCode(text) {
  if (!text) return "";
  const esc = escapeHtml(text);
  return esc.replace(
    /&lt;(\/?)([\w.-]+)((?:\s+[\w.-]+(?:="[^"]*")?)*)(\/?)&gt;/g,
    (m, openSlash, tagName, attrs, closeSlash) => {
      const attrHl = attrs.replace(
        /([\w.-]+)="([^"]*)"/g,
        (am, an, av) => `<span class="tok-attr">${an}</span>="<span class="tok-str">${av}</span>"`
      );
      return `&lt;${openSlash}<span class="tok-tag">${tagName}</span>${attrHl}${closeSlash}&gt;`;
    }
  );
}

// Lightbox for the trajectory replay GIF (mirrors app.js attachLightbox).
function attachLightbox() {
  const overlay = document.getElementById("lightbox-overlay");
  const overlayImg = document.getElementById("lightbox-image");
  const closeBtn = overlay ? overlay.querySelector(".lightbox-close") : null;
  if (!overlay || !overlayImg) return;

  function open(img) {
    overlayImg.src = img.src;
    overlayImg.alt = img.alt;
    overlay.classList.add("active");
    overlay.setAttribute("aria-hidden", "false");
  }

  function close() {
    overlay.classList.remove("active");
    overlay.setAttribute("aria-hidden", "true");
    overlayImg.src = "";
  }

  for (const img of document.querySelectorAll("img.lightbox-trigger")) {
    img.addEventListener("click", () => open(img));
  }

  if (closeBtn) closeBtn.addEventListener("click", close);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) close();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && overlay.classList.contains("active")) close();
  });
}

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function fmtUtc(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function fmtDuration(startIso, endIso) {
  if (!startIso || !endIso) return "—";
  try {
    const ms = new Date(endIso) - new Date(startIso);
    if (Number.isNaN(ms) || ms < 0) return "—";
    const m = Math.floor(ms / 60000);
    const s = Math.round((ms % 60000) / 1000);
    return `${m}m ${s}s`;
  } catch {
    return "—";
  }
}

// ---------------------------------------------------------------------------
// State badges
// ---------------------------------------------------------------------------

function taskTagsMarkup(task, traj) {
  const tags = [];
  if (task.is_ask_user) tags.push(`<span class="tag tag-ask">ASK USER</span>`);
  else if (task.bucket === "hard") tags.push(`<span class="tag tag-det">Deterministic</span>`);
  if (task.cross_app) tags.push(`<span class="tag tag-cross">cross-app</span>`);
  if (task.placeholder_count) {
    tags.push(`<span class="tag">${task.placeholder_count} placeholder${task.placeholder_count === 1 ? "" : "s"}</span>`);
  }
  tags.push(`<span class="tag">${task.points} pt</span>`);
  if (traj && traj.has_trajectory) tags.push(`<span class="tag tag-has-traj">trajectory</span>`);
  return tags.join("");
}

function stateRow(label, value) {
  return `
    <div class="task-state-item">
      <span class="task-state-label">${escapeHtml(label)}</span>
      <span class="task-state-value">${value}</span>
    </div>
  `;
}

function renderTaskState(task, traj) {
  const root = document.getElementById("task-state-body");
  if (!root) return;

  const diff = capitalize(task.bucket || task.difficulty || "—");
  const apps = (task.apps && task.apps.length ? task.apps : [task.app]).map((a) => escapeHtml(a)).join(" · ");
  const type = task.is_ask_user ? "ASK USER" : task.bucket === "hard" ? "Deterministic" : "GUI-only";

  let runModel = "No run recorded";
  let runResult = "—";
  let runDuration = "—";
  if (traj) {
    runModel = traj.model ? escapeHtml(traj.model) : "—";
    runResult = traj.success === true ? '<span class="run-ok">Success</span>' : traj.success === false ? '<span class="run-fail">Failure</span>' : "—";
    runDuration = fmtDuration(traj.started_at_utc, traj.ended_at_utc);
  }

  root.innerHTML =
    stateRow("Difficulty", `<span class="tag tag-${escapeHtml(task.bucket || "easy")}">${escapeHtml(diff)}</span>`) +
    stateRow("Type", escapeHtml(type)) +
    stateRow("App(s)", apps) +
    stateRow("Day", task.day ? `Day ${task.day}` : "—") +
    stateRow("Points", String(task.points ?? "—")) +
    stateRow("Cross-app", task.cross_app ? "Yes" : "No") +
    stateRow("Model", runModel) +
    stateRow("Run result", runResult) +
    stateRow("Run duration", runDuration);
}

// ---------------------------------------------------------------------------
// Trajectory viewer (step-through)
// ---------------------------------------------------------------------------

const VIEWER = {
  steps: [],
  index: 0,
  timer: null,
  playing: false,
  screenshotBase: null,
  screenshotCount: 0,
};

function usageText(usage) {
  if (!usage) return "";
  const parts = [];
  if (usage.total_tokens != null) parts.push(`${usage.total_tokens} tokens`);
  if (usage.request_tokens != null && usage.response_tokens != null) {
    parts.push(`${usage.request_tokens} in / ${usage.response_tokens} out`);
  }
  return parts.length ? parts.join(" · ") : "";
}

// Pretty-print tool args as JSON with syntax highlighting (full, not truncated).
function toolArgsMarkup(args) {
  if (args == null) return "";
  if (typeof args === "string") {
    // Sometimes args arrive as a JSON string; try to parse for pretty display.
    try {
      args = JSON.parse(args);
    } catch {
      return `<pre class="step-tool-args"><code>${escapeHtml(args)}</code></pre>`;
    }
  }
  return `<pre class="step-tool-args"><code>${highlightJson(args)}</code></pre>`;
}

function stepToolsMarkup(tools) {
  if (!tools || !tools.length) return "";
  return tools
    .map((t) => {
      const ok = t.success ? '<span class="tool-ok">ok</span>' : '<span class="tool-fail">error</span>';
      const args = toolArgsMarkup(t.tool_args);
      return `
        <div class="step-tool ${t.success ? "step-tool-ok" : "step-tool-fail"}">
          <div class="step-tool-head">
            <code class="step-tool-name">${escapeHtml(t.tool_name || "tool")}</code>
            ${ok}
          </div>
          ${args}
          ${t.summary ? `<div class="step-tool-summary">${escapeHtml(t.summary)}</div>` : ""}
        </div>
      `;
    })
    .join("");
}

function renderStep() {
  const s = VIEWER.steps[VIEWER.index];
  const numEl = document.getElementById("step-number");
  const thoughtEl = document.getElementById("step-thought");
  const codeEl = document.getElementById("step-code");
  const toolsEl = document.getElementById("step-tools");
  const outputEl = document.getElementById("step-output");
  const counterEl = document.getElementById("step-counter");
  const shotEl = document.getElementById("step-screenshot");
  if (!s) return;

  if (numEl) numEl.textContent = String(VIEWER.index + 1);
  if (counterEl) counterEl.textContent = `Step ${VIEWER.index + 1} / ${VIEWER.steps.length}`;

  if (shotEl) {
    const shotFile = s.screenshot;
    if (shotFile && VIEWER.screenshotBase) {
      shotEl.src = pagePath(`${VIEWER.screenshotBase}/${shotFile}`);
      shotEl.alt = `Phone screen at step ${VIEWER.index + 1}`;
      shotEl.hidden = false;
    } else {
      shotEl.hidden = true;
    }
  }

  if (thoughtEl) {
    const usage = usageText(s.usage);
    thoughtEl.innerHTML = `
      ${s.thought ? `<div class="step-thought-text">${escapeHtml(s.thought)}</div>` : '<div class="step-thought-empty">(no explicit reasoning recorded for this step)</div>'}
      ${usage ? `<div class="step-usage">${escapeHtml(usage)}</div>` : ""}
    `;
  }

  if (codeEl) {
    codeEl.innerHTML = s.code
      ? `<div class="step-block-label">function calls</div><pre class="step-code-block"><code>${highlightCode(s.code)}</code></pre>`
      : "";
  }

  if (toolsEl) toolsEl.innerHTML = stepToolsMarkup(s.tools);
  if (outputEl) {
    outputEl.innerHTML = s.output
      ? `<div class="step-block-label">function results</div><pre class="step-output-text"><code>${highlightCode(s.output)}</code></pre>`
      : "";
  }

  // Disable prev/next at bounds.
  const prev = document.getElementById("step-prev");
  const next = document.getElementById("step-next");
  const first = document.getElementById("step-first");
  const last = document.getElementById("step-last");
  if (prev) prev.disabled = VIEWER.index === 0;
  if (first) first.disabled = VIEWER.index === 0;
  if (next) next.disabled = VIEWER.index >= VIEWER.steps.length - 1;
  if (last) last.disabled = VIEWER.index >= VIEWER.steps.length - 1;
}

function stepTo(i) {
  if (!VIEWER.steps.length) return;
  VIEWER.index = Math.max(0, Math.min(VIEWER.steps.length - 1, i));
  renderStep();
}

function stopPlay() {
  VIEWER.playing = false;
  if (VIEWER.timer) {
    clearTimeout(VIEWER.timer);
    VIEWER.timer = null;
  }
  const btn = document.getElementById("step-play");
  if (btn) btn.textContent = "Play";
}

function play() {
  if (!VIEWER.steps.length) return;
  if (VIEWER.playing) {
    stopPlay();
    return;
  }
  VIEWER.playing = true;
  const btn = document.getElementById("step-play");
  if (btn) btn.textContent = "Pause";
  if (VIEWER.index >= VIEWER.steps.length - 1) stepTo(0);
  scheduleNext();
}

// Advance one step, then schedule the next one — keeps playing until the end or
// until stopPlay() is called. (Must NOT go through play(), which toggles state.)
function scheduleNext() {
  if (!VIEWER.playing) return;
  const speed = Number(document.getElementById("step-speed")?.value || 900);
  VIEWER.timer = setTimeout(() => {
    if (VIEWER.index < VIEWER.steps.length - 1) {
      stepTo(VIEWER.index + 1);
      scheduleNext();
    } else {
      stopPlay();
    }
  }, speed);
}

function initStepControls() {
  const bind = (id, fn) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", fn);
  };
  bind("step-first", () => { stopPlay(); stepTo(0); });
  bind("step-prev", () => { stopPlay(); stepTo(VIEWER.index - 1); });
  bind("step-next", () => { stopPlay(); stepTo(VIEWER.index + 1); });
  bind("step-last", () => { stopPlay(); stepTo(VIEWER.steps.length - 1); });
  bind("step-play", play);
  const speed = document.getElementById("step-speed");
  if (speed) {
    speed.addEventListener("change", () => {
      if (!VIEWER.playing) return;
      // Restart the current timer at the new speed without toggling state.
      if (VIEWER.timer) {
        clearTimeout(VIEWER.timer);
        VIEWER.timer = null;
      }
      scheduleNext();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (!VIEWER.steps.length) return;
    if (e.key === "ArrowRight") { stopPlay(); stepTo(VIEWER.index + 1); }
    if (e.key === "ArrowLeft") { stopPlay(); stepTo(VIEWER.index - 1); }
    if (e.key === " ") { e.preventDefault(); play(); }
  });
}

// ---------------------------------------------------------------------------
// Render trajectory section (GIF + meta) and step viewer
// ---------------------------------------------------------------------------

// Resolve the full list of runs for a task: the index entry carries a `runs`
// array (multi-run support: e.g. two 26-Aug models + today's 28-Aug); when
// absent, fall back to the single run represented by the entry itself.
function runsForTask(traj) {
  if (traj && Array.isArray(traj.runs) && traj.runs.length) return traj.runs;
  return traj ? [traj] : [];
}

// Re-render the whole trajectory section for a single run entry.
async function renderRun(task, run, stepsSection) {
  if (!run || !run.has_trajectory) return;

  const gif = document.getElementById("trajectory-gif");
  if (gif && run.gif) {
    gif.src = pagePath(run.gif);
    gif.alt = `Agent trajectory replay for ${task.task_id}`;
  }

  // Per-run trajectory data (may 404 if has_trajectory is false).
  let trajData = null;
  if (run.data) {
    try {
      trajData = await loadJson(pagePath(run.data));
    } catch {
      trajData = null;
    }
  }

  const cap = document.getElementById("trajectory-gif-caption");
  if (cap) cap.textContent = `${task.task_id} — replay of ${run.step_count ?? trajData?.steps_count ?? "—"} agent steps`;

  const metaList = document.getElementById("trajectory-meta-list");
  if (metaList) {
    const items = [
      ["Run", run.run_label ? escapeHtml(run.run_label) : "—"],
      ["Model", run.model ? escapeHtml(run.model) : "—"],
      ["Result", run.success === true ? '<span class="run-ok">Success</span>' : run.success === false ? '<span class="run-fail">Failure</span>' : "—"],
      ["Steps (output)", String(run.steps ?? "—")],
      ["Steps (trajectory)", String(trajData?.steps_count ?? "—")],
      ["Tool calls", String(trajData?.tool_call_count ?? "—")],
      ["Started", fmtUtc(run.started_at_utc)],
      ["Ended", fmtUtc(run.ended_at_utc)],
      ["Duration", fmtDuration(run.started_at_utc, run.ended_at_utc)],
    ];
    metaList.innerHTML = items.map(([k, v]) => `<li><span class="tm-key">${k}</span><span class="tm-val">${v}</span></li>`).join("");
  }

  // "Open in Phoenix" — deep-links to a local Phoenix instance's project page.
  // A Phoenix backend only exists on the author's machine (localhost preview);
  // on the public GitHub Pages site there is no Phoenix, so the button stays
  // hidden. The step viewer below already IS the Phoenix-traced trajectory.
  const phoenixBtn = document.getElementById("trajectory-open-phoenix");
  if (phoenixBtn) {
    phoenixBtn.onclick = () => {
      const base = localStorage.getItem("drainbench.phoenixBase") || "http://localhost:6006";
      window.open(`${base}/projects/dailybench-day${run.day}`, "_blank", "noopener");
    };
    phoenixBtn.hidden = !(["localhost", "127.0.0.1"].includes(window.location.hostname) && /^https?:$/.test(window.location.protocol));
  }

  // Steps viewer
  if (trajData && trajData.steps && trajData.steps.length) {
    VIEWER.steps = trajData.steps;
    VIEWER.index = 0;
    VIEWER.screenshotBase = trajData.screenshot_base || null;
    VIEWER.screenshotCount = trajData.screenshot_count || 0;
    if (stepsSection) stepsSection.hidden = false;
    initStepControls();
    renderStep();
  }
}

function renderTrajectory(task, traj) {
  const section = document.getElementById("task-trajectory");
  const stepsSection = document.getElementById("task-trajectory-steps");
  const runs = runsForTask(traj);
  const hasAny = runs.some((r) => r.has_trajectory);

  if (!hasAny) {
    const btn = document.getElementById("trajectory-btn");
    if (btn) btn.hidden = true;
    const noTraj = document.getElementById("task-desc");
    if (noTraj) {
      noTraj.textContent = "No recorded run / trajectory exists for this task yet on days 1-3.";
    }
    return;
  }

  const btn = document.getElementById("trajectory-btn");
  if (btn) {
    btn.hidden = false;
    btn.addEventListener("click", () => {
      if (section) section.scrollIntoView({ behavior: "smooth" });
      if (stepsSection) stepsSection.scrollIntoView({ behavior: "smooth" });
    });
  }

  if (section) section.hidden = false;

  // Multi-run selector — when several runs exist (e.g. two 26-Aug models +
  // today's 28-Aug), let the viewer pick which trajectory to replay.
  const runSelect = document.getElementById("trajectory-run-select");
  const runWrap = document.getElementById("run-select-wrap");
  const runnable = runs.filter((r) => r.has_trajectory);
  if (runSelect && runWrap && runnable.length > 1) {
    runSelect.innerHTML = runnable
      .map((r, i) => `<option value="${i}">${escapeHtml(r.run_label || `Run ${i + 1} (${r.model || "?"})`)}</option>`)
      .join("");
    runWrap.hidden = false;
    const primaryIdx = Math.max(0, runnable.findIndex((r) => r.is_primary));
    runSelect.value = String(primaryIdx);
    runSelect.onchange = () => {
      const run = runnable[Number(runSelect.value)];
      if (run) renderRun(task, run, stepsSection);
    };
    renderRun(task, runnable[primaryIdx], stepsSection);
  } else {
    if (runWrap) runWrap.hidden = true;
    renderRun(task, runnable[0], stepsSection);
  }
}

// ---------------------------------------------------------------------------
// Page init
// ---------------------------------------------------------------------------

async function loadJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load ${url}`);
  return resp.json();
}

async function init() {
  const taskId = getParam("task_id");
  const title = document.getElementById("task-title");
  const subtitle = document.getElementById("task-subtitle");
  const promptEl = document.getElementById("task-prompt-body");
  const descEl = document.getElementById("task-desc");

  if (!taskId) {
    if (title) title.textContent = "Task";
    if (subtitle) subtitle.textContent = "No task selected — open one from the task browser.";
    return;
  }

  try {
    const [site, idx] = await Promise.all([loadJson(SITE_DATA), loadJson(TRAJ_INDEX)]);
    // set=public → resolve from the public bench sample (homepage examples);
    // otherwise default to the 530 corpus (Tasks page). Public task_ids can
    // also exist in the 530 corpus, so the set is explicit.
    const isPublic = getParam("set") === "public";
    const task = isPublic
      ? (site.public_examples || []).find((t) => t.task_id === taskId)
      : (site.tasks || []).find((t) => t.task_id === taskId);

    if (!task) {
      if (title) title.textContent = "Unknown task";
      if (subtitle) subtitle.textContent = `No task with id "${taskId}" found.`;
      return;
    }

    if (title) title.textContent = task.task_id;
    const appLabel = task.app || task.category_name || "Task";
    if (subtitle) subtitle.textContent = `${capitalize(task.bucket || task.difficulty || "")} · ${appLabel}${task.day ? ` · Day ${task.day}` : ""}${isPublic ? " · public sample" : ""}`;
    if (descEl) descEl.textContent = "";
    if (promptEl) {
      promptEl.innerHTML = `<code>${escapeHtml(task.prompt)}</code>`;
    }
    document.title = `DailyBench300  -  ${task.task_id}`;

    const traj = (isPublic ? idx.public : idx.tasks) && (isPublic ? idx.public : idx.tasks)[taskId];
    renderTaskState(task, traj);

    renderTrajectory(task, traj);
    attachLightbox();
  } catch (error) {
    if (subtitle) subtitle.textContent = "Failed to load task data.";
    if (title) title.textContent = "Task";
    console.error(error);
  }
}

init();
