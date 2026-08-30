async function loadData() {
  const dataPath = document.body.dataset.siteData || "./assets/data/site_data.json";
  const response = await fetch(dataPath);
  if (!response.ok) {
    throw new Error("Failed to load site data");
  }
  return response.json();
}

function renderStatsInline(stats) {
  const root = document.getElementById("stats-inline");
  if (!root) {
    return;
  }
  root.textContent =
    `${stats.task_count} tasks across ${stats.app_count} apps and ${stats.day_count} days, ` +
    `${stats.cross_app_count} cross-app, ` +
    `${stats.hard_ask_user} ASK USER / ${stats.hard_deterministic} deterministic hard tasks, ` +
    `${stats.placeholder_count} placeholder instances.`;
}

function renderCategoryTable(categories) {
  const root = document.getElementById("category-table-body");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .map(
      (category) => `
        <tr>
          <td>${category.name} (${category.count})</td>
          <td>${category.description}${category.cross_app ? ` · ${category.cross_app} cross-app` : ""}</td>
        </tr>
      `
    )
    .join("");
}

// Renders the homepage "Benchmark Summary" from the public dataset stats
// (computed in build_site_data.mjs, cross-checked against
// docs/benchmark-spec-public.md). At-a-glance stat cards + per-day composition.
function renderPublicBenchmarkSummary(stats) {
  const root = document.getElementById("benchmark-summary-body");
  if (!root || !stats) {
    return;
  }
  const b = stats.buckets || { easy: 0, medium: 0, hard: 0 };
  const hs = stats.hard_split || { single: 0, multi: 0, det: 0 };
  const crossShare = stats.task_count ? Math.round((stats.cross_app / stats.task_count) * 1000) / 10 : 0;

  const cards = [
    { value: stats.task_count, label: "runnable tasks", sub: `${stats.day_count} days · ${stats.success_graded + stats.hc_count} graded (${stats.success_graded} runnable + ${stats.hc_count} hallucination-control)` },
    { value: `${b.easy} / ${b.medium} / ${b.hard}`, label: "easy / medium / hard", sub: "difficulty buckets" },
    { value: `${hs.single} / ${hs.multi} / ${hs.det}`, label: "hard: SINGLE / MULTI / DET", sub: "17 hard tasks split by grading mode" },
    { value: stats.ask_user_total, label: "ASK USER tasks", sub: `${stats.ask_user_single} single-turn · ${stats.ask_user_multi} multi-turn (KB oracle)` },
    { value: stats.hc_count, label: "hallucination controls", sub: "data genuinely absent — honest failure is correct" },
    { value: `${stats.single_app} / ${stats.cross_app}`, label: "single-app / cross-app", sub: `${crossShare}% cross-app (${stats.two_app} two-app · ${stats.three_app} three-app)` },
    { value: stats.app_count, label: "distinct apps", sub: "of 31 in the full corpus" },
    { value: stats.placeholder_uses, label: "placeholder uses", sub: `${stats.placeholder_keys} distinct keys${stats.top_placeholder ? ` · top: [${stats.top_placeholder.key}] ×${stats.top_placeholder.uses}` : ""}` },
  ];

  root.innerHTML =
    `<div class="bench-summary-cards">` +
    cards
      .map(
        (c) => `
          <div class="bench-card">
            <div class="bench-card-value">${escapeHtml(c.value)}</div>
            <div class="bench-card-label">${escapeHtml(c.label)}</div>
            <div class="bench-card-sub">${c.sub}</div>
          </div>`
      )
      .join("") +
    `</div>` +
    `<div class="bench-day-table-wrap">
      <h3 class="subsection-title">Per-day composition</h3>
      <table class="bench-day-table">
        <thead>
          <tr>
            <th>Day</th>
            <th>Easy</th>
            <th>Medium</th>
            <th>Hard</th>
            <th>Hard SINGLE</th>
            <th>Hard MULTI</th>
            <th>Hard DET</th>
            <th>HC</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          ${(stats.per_day || [])
            .map(
              (d) => `
                <tr>
                  <td>${d.day}</td>
                  <td>${d.easy}</td>
                  <td>${d.medium}</td>
                  <td>${d.hard}</td>
                  <td>${d.single}</td>
                  <td>${d.multi}</td>
                  <td>${d.det}</td>
                  <td>${d.hc}</td>
                  <td><strong>${d.total}</strong></td>
                </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>`;
}

function renderDayTable(days) {
  const root = document.getElementById("day-table-body");
  if (!root) {
    return;
  }
  root.innerHTML = days
    .map(
      (day) => `
        <tr>
          <td>Day ${day.day}</td>
          <td>${day.count}</td>
          <td>${day.easy} / ${day.medium} / ${day.hard}</td>
          <td>${day.ask_user} / ${day.deterministic}</td>
          <td>${day.apps}</td>
        </tr>
      `
    )
    .join("");
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

// Render a task prompt, turning placeholder tokens ('[product]', [contact]) into
// italic <em> without the surrounding quotes. Applied to both the 530 corpus and
// the public sample. Placeholder tokens always look like [something] (with or
// without single-quote decoration), so we wrap those in a styled <em>.
function formatPrompt(text) {
  return escapeHtml(text).replace(/'\[([^\]]+)\]'|\[([^\]]+)\]/g, (m, quoted, bare) => {
    const name = quoted || bare;
    return `<em class="placeholder">[${name}]</em>`;
  });
}

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function attachLightbox() {
  const overlay = document.getElementById("lightbox-overlay");
  const overlayImg = document.getElementById("lightbox-image");
  const closeBtn = overlay ? overlay.querySelector(".lightbox-close") : null;
  if (!overlay || !overlayImg) {
    return;
  }

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

  if (closeBtn) {
    closeBtn.addEventListener("click", close);
  }
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      close();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && overlay.classList.contains("active")) {
      close();
    }
  });
}

// DailyBench tasks are text-prompt mobile tasks (no reference images), so an
// example card shows the app, difficulty, tags, and the goal prompt. Public
// example cards link to the per-task detail page (set=public) with the same
// trajectory functionality as the 530 tasks.
function detailPageHref(query) {
  // Homepage lives at repo root (site data at ./assets/...); the tasks/task
  // pages live under pages/ (site data at ../assets/...). Build the detail URL
  // from the same base so links work from either location.
  const siteData = document.body.dataset.siteData || "./assets/data/site_data.json";
  const base = siteData.startsWith("../") ? "./task.html" : "./pages/task.html";
  return `${base}?${query}`;
}

function publicExampleMarkup(example, run) {
  const tags = [
    example.is_ask_user ? `<span class="tag tag-ask">ASK USER</span>` : "",
    example.cross_app ? `<span class="tag tag-cross">cross-app</span>` : "",
    example.placeholder_count ? `<span class="tag">${example.placeholder_count} placeholder${example.placeholder_count === 1 ? "" : "s"}</span>` : "",
    `<span class="tag">${example.points} pt</span>`,
  ]
    .filter(Boolean)
    .join("");
  let runBadge = "";
  if (run) {
    // Per-model run outcome: pass/fail + steps when a specific run is selected.
    runBadge = `
      <div class="public-example-run">
        <span class="tag ${run.success === true ? "tag-run-ok" : run.success === false ? "tag-run-fail" : ""}">${run.success === true ? "&#10003; pass" : run.success === false ? "&#10007; fail" : "not run"}</span>
        ${run.steps != null ? `<span class="public-example-steps">${run.steps} steps</span>` : ""}
      </div>
    `;
  }
  const detailHref = detailPageHref(`set=public&task_id=${encodeURIComponent(example.task_id)}${run && run.run_key ? `&run=${encodeURIComponent(run.run_key)}` : ""}`);
  return `
    <article class="public-example" data-task-id="${escapeHtml(example.task_id)}">
      <div class="public-example-meta">
        <span class="public-example-cat">${escapeHtml(example.category_name)} <span class="public-example-id">${escapeHtml(example.task_id)}</span></span>
        <span class="public-example-diff">${capitalize(example.difficulty)}</span>
      </div>
      ${tags ? `<div class="public-example-tags">${tags}</div>` : ""}
      ${runBadge}
      <pre class="public-example-prompt"><code>${formatPrompt(example.prompt)}</code></pre>
      <div class="card-footer">
        <a class="card-trajectory-link" href="${detailHref}" title="View task detail + trajectory replay">&#9654; View task</a>
      </div>
    </article>
  `;
}

function renderPublicExampleList(containerId, examples) {
  const root = document.getElementById(containerId);
  if (!root || !examples) {
    return;
  }
  root.innerHTML = examples.map((example) => publicExampleMarkup(example)).join("");
}

// --- Public-tasks model-run selector (homepage "Public Tasks" section) ---
//
// Each public task has runs recorded under several models (e.g. qwen-28 text,
// gemini-26, qwen-26 vision). This is now a *typed box with autosuggestion*:
// the datalist is built from the models actually recorded in the trajectory
// index (dates stripped), and typing/choosing one re-renders the list with
// that run's pass/fail + steps per task (runBadge). Clearing the box → all.
let PUBLIC_RUN_FILTER = "";

function publicRunByKey(example, key) {
  if (!key || !TRAJECTORY_INDEX || !TRAJECTORY_INDEX.public) return null;
  const entry = TRAJECTORY_INDEX.public[example.task_id];
  if (!entry || !Array.isArray(entry.runs)) return null;
  return entry.runs.find((r) => r.run_key === key) || null;
}

// Strip the "· 28 Aug" date segment out of a run label so the suggestions show
// clean model names ("qwen3.8-27b (text)", "gemini-3.1-flash-lite", ...).
function cleanRunLabel(label) {
  if (!label) return label;
  return String(label).replace(/\s*·\s*\d{1,2}\s+\w+\s*/g, " ").replace(/\s+/g, " ").trim();
}

function renderPublicExampleListFiltered(containerId, examples) {
  const root = document.getElementById(containerId);
  if (!root || !examples) {
    return;
  }
  root.innerHTML = examples
    .map((example) => publicExampleMarkup(example, PUBLIC_RUN_FILTER ? publicRunByKey(example, PUBLIC_RUN_FILTER) : null))
    .join("");
}

function initPublicRunSelect() {
  const input = document.getElementById("public-run-select");
  const dl = document.getElementById("public-run-datalist");
  if (!input || !dl) return;
  if (!TRAJECTORY_INDEX || !TRAJECTORY_INDEX.public) return;

  // Collect the distinct runs across public tasks, in a stable order. Build the
  // autosuggest datalist from the models actually recorded (dates removed).
  const seen = new Map();
  for (const entry of Object.values(TRAJECTORY_INDEX.public)) {
    for (const run of entry.runs || []) {
      if (run && run.run_key && !seen.has(run.run_key)) {
        seen.set(run.run_key, cleanRunLabel(run.run_label) || run.run_key);
      }
    }
  }
  dl.innerHTML = [...seen.values()]
    .map((label) => `<option value="${escapeHtml(label)}"></option>`)
    .join("");

  // Match typed text against the cleaned model labels (case-insensitive).
  const matchRun = (text) => {
    const t = text.trim().toLowerCase();
    if (!t) return "";
    for (const [key, label] of seen) {
      if (label.toLowerCase() === t || label.toLowerCase().includes(t)) return key;
    }
    return "";
  };

  input.addEventListener("input", () => {
    PUBLIC_RUN_FILTER = matchRun(input.value);
    renderPublicExampleListFiltered("featured-examples-list", window.__publicExamples || []);
  });
}

// ---------------------------------------------------------------------------
// Task browser (all 530 tasks + filters) — used by pages/tasks.html
// ---------------------------------------------------------------------------

const FILTER_STATE = { difficulty: "", type: "", day: "", app: "", search: "" };

function taskType(task) {
  if (task.is_ask_user) return "ask";
  if (task.bucket === "hard") return "det";
  return "gui";
}

function taskTagsMarkup(task) {
  const tags = [];
  if (task.is_ask_user) tags.push(`<span class="tag tag-ask">ASK USER</span>`);
  else if (task.bucket === "hard") tags.push(`<span class="tag tag-det">Deterministic</span>`);
  if (task.cross_app) tags.push(`<span class="tag tag-cross">cross-app</span>`);
  if (task.placeholder_count) {
    tags.push(`<span class="tag">${task.placeholder_count} placeholder${task.placeholder_count === 1 ? "" : "s"}</span>`);
  }
  tags.push(`<span class="tag">${task.points} pt</span>`);
  return tags.join("");
}

// task_id -> trajectory availability, loaded from data/trajectories/index.json
let TRAJECTORY_INDEX = null;

function taskHasTrajectory(taskId) {
  return Boolean(TRAJECTORY_INDEX && TRAJECTORY_INDEX.tasks && TRAJECTORY_INDEX.tasks[taskId] && TRAJECTORY_INDEX.tasks[taskId].has_trajectory);
}

function taskCardMarkup(task) {
  const hasTraj = taskHasTrajectory(task.task_id);
  const trajTag = hasTraj
    ? `<a class="card-trajectory-link" href="./task.html?task_id=${encodeURIComponent(task.task_id)}" title="View trajectory replay + model trace">&#9654; View trajectory</a>`
    : "";
  return `
    <article class="public-example task-card" data-task-id="${escapeHtml(task.task_id)}">
      <div class="public-example-meta">
        <span class="public-example-cat">${escapeHtml(task.app)} <span class="public-example-id">${escapeHtml(task.task_id)}</span></span>
        <span class="public-example-diff">${capitalize(task.bucket)}${task.day ? ` &middot; Day ${task.day}` : ""}</span>
      </div>
      <div class="public-example-tags">${taskTagsMarkup(task)}</div>
      <pre class="public-example-prompt"><code>${formatPrompt(task.prompt)}</code></pre>
      <div class="card-footer">${trajTag}</div>
    </article>
  `;
}

function filteredTasks(tasks) {
  const q = FILTER_STATE.search.trim().toLowerCase();
  return tasks.filter((task) => {
    if (FILTER_STATE.difficulty && task.bucket !== FILTER_STATE.difficulty) return false;
    if (FILTER_STATE.type && taskType(task) !== FILTER_STATE.type) return false;
    if (FILTER_STATE.day && String(task.day) !== FILTER_STATE.day) return false;
    if (FILTER_STATE.app && task.app !== FILTER_STATE.app) return false;
    if (q && !(task.prompt + " " + task.task_id + " " + (task.note || "")).toLowerCase().includes(q)) return false;
    return true;
  });
}

function renderTaskList(tasks) {
  const root = document.getElementById("task-list");
  const count = document.getElementById("task-count");
  if (!root) return;
  const visible = filteredTasks(tasks);
  if (count) count.textContent = `Showing ${visible.length} of ${tasks.length} tasks`;
  root.innerHTML = visible.map(taskCardMarkup).join("");
}

function initTaskBrowser(tasks) {
  const root = document.getElementById("task-browser");
  if (!root) return;

  // Populate day + app selects.
  const daySel = document.getElementById("filter-day");
  const appSel = document.getElementById("filter-app");
  const days = [...new Set(tasks.map((t) => t.day).filter(Boolean))].sort((a, b) => a - b);
  for (const d of days) {
    const opt = document.createElement("option");
    opt.value = String(d);
    opt.textContent = `Day ${d}`;
    daySel.appendChild(opt);
  }
  const apps = [...new Set(tasks.map((t) => t.app))].sort((a, b) => a.localeCompare(b));
  for (const a of apps) {
    const opt = document.createElement("option");
    opt.value = a;
    opt.textContent = a;
    appSel.appendChild(opt);
  }

  // Difficulty + type buttons.
  for (const btn of document.querySelectorAll(".filter-btn")) {
    btn.addEventListener("click", () => {
      const group = btn.closest(".filter-options");
      for (const b of group.querySelectorAll(".filter-btn")) b.classList.remove("active");
      btn.classList.add("active");
      FILTER_STATE[group.dataset.filter] = btn.dataset.value;
      renderTaskList(tasks);
    });
  }

  daySel.addEventListener("change", () => {
    FILTER_STATE.day = daySel.value;
    renderTaskList(tasks);
  });
  appSel.addEventListener("change", () => {
    FILTER_STATE.app = appSel.value;
    renderTaskList(tasks);
  });
  const search = document.getElementById("filter-search");
  search.addEventListener("input", () => {
    FILTER_STATE.search = search.value;
    renderTaskList(tasks);
  });

  // Click a task card (not the trajectory link itself) -> open the detail page.
  const list = document.getElementById("task-list");
  if (list) {
    list.addEventListener("click", (event) => {
      const link = event.target.closest("a");
      if (link) return; // let the anchor handle it
      const card = event.target.closest(".task-card");
      if (card && card.dataset.taskId) {
        window.location.href = `./task.html?task_id=${encodeURIComponent(card.dataset.taskId)}`;
      }
    });
  }

  renderTaskList(tasks);
}

function loadTrajectoryIndex() {
  const dataPath = document.body.dataset.trajectoryIndex;
  if (!dataPath) return Promise.resolve(null);
  return fetch(dataPath)
    .then((resp) => (resp.ok ? resp.json() : null))
    .catch(() => null);
}

loadData()
  .then((data) =>
    loadTrajectoryIndex().then((trajIndex) => {
      TRAJECTORY_INDEX = trajIndex;
      renderStatsInline(data.stats);
      renderPublicBenchmarkSummary(data.public_stats);
      renderDayTable(data.days);
      // Homepage: show the FULL public bench we have runs for, in a 2-col grid.
      window.__publicExamples = data.public_examples || [];
      renderPublicExampleListFiltered("featured-examples-list", window.__publicExamples);
      renderPublicExampleList("public-examples-list", data.public_examples || []);
      initPublicRunSelect();
      initTaskBrowser(data.tasks || []);
      attachLightbox();
    })
  )
  .catch((error) => {
    const statsRoot = document.getElementById("stats-inline");
    const summaryRoot = document.getElementById("benchmark-summary-body");
    if (statsRoot) {
      statsRoot.textContent = error.message;
    }
    if (summaryRoot) {
      summaryRoot.innerHTML = `<tr><td colspan="3">${error.message}</td></tr>`;
    }
  });
