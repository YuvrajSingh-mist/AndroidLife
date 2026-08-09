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

function renderBenchmarkSummary(categories) {
  const root = document.getElementById("benchmark-summary-body");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .map((category) => {
      const counts = category.difficulty || { easy: 0, medium: 0, hard: 0 };
      return `
        <tr>
          <td>${category.name}</td>
          <td>${category.count}</td>
          <td>Easy ${counts.easy}  -  Medium ${counts.medium}  -  Hard ${counts.hard}</td>
        </tr>
      `;
    })
    .join("");
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
// example card shows the app, difficulty, tags, and the goal prompt.
function publicExampleMarkup(example) {
  const tags = [
    example.is_ask_user ? `<span class="tag tag-ask">ASK USER</span>` : "",
    example.cross_app ? `<span class="tag tag-cross">cross-app</span>` : "",
    example.placeholder_count ? `<span class="tag">${example.placeholder_count} placeholder${example.placeholder_count === 1 ? "" : "s"}</span>` : "",
    `<span class="tag">${example.points} pt</span>`,
  ]
    .filter(Boolean)
    .join("");
  return `
    <article class="public-example">
      <div class="public-example-meta">
        <span class="public-example-cat">${example.category_name} <span class="public-example-id">${example.task_id}</span></span>
        <span class="public-example-diff">${capitalize(example.difficulty)}</span>
      </div>
      ${tags ? `<div class="public-example-tags">${tags}</div>` : ""}
      <pre class="public-example-prompt"><code>${escapeHtml(example.prompt)}</code></pre>
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

// ---------------------------------------------------------------------------
// Task browser (all 533 tasks + filters) — used by pages/tasks.html
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

function taskCardMarkup(task) {
  return `
    <article class="public-example task-card">
      <div class="public-example-meta">
        <span class="public-example-cat">${escapeHtml(task.app)} <span class="public-example-id">${escapeHtml(task.task_id)}</span></span>
        <span class="public-example-diff">${capitalize(task.bucket)}${task.day ? ` &middot; Day ${task.day}` : ""}</span>
      </div>
      <div class="public-example-tags">${taskTagsMarkup(task)}</div>
      <pre class="public-example-prompt"><code>${escapeHtml(task.prompt)}</code></pre>
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

  renderTaskList(tasks);
}

loadData()
  .then((data) => {
    renderStatsInline(data.stats);
    renderCategoryTable(data.categories);
    renderBenchmarkSummary(data.categories);
    renderDayTable(data.days);
    renderPublicExampleList(
      "featured-examples-list",
      (data.public_examples || []).filter((example) => example.difficulty === "hard")
    );
    renderPublicExampleList("public-examples-list", data.public_examples);
    initTaskBrowser(data.tasks || []);
    attachLightbox();
  })
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
