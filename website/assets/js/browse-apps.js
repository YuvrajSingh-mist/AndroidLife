// Browse Apps: grid of public-benchmark apps + per-app trajectory browser

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

async function loadJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`Failed to load ${url}`);
  return resp.json();
}

function appMatchesQuery(app, query) {
  const q = (query || "").trim().toLowerCase();
  if (!q) return true;
  const name = (app.name || "").toLowerCase();
  const slug = (app.slug || "").toLowerCase();
  const publisher = (app.publisher || "").toLowerCase();
  // Prefix / token match on app name — "note" hits Notes only, not Swiggy.
  if (name === q || slug === q) return true;
  if (name.startsWith(q) || slug.startsWith(q)) return true;
  const tokens = name.split(/[\s/-]+/);
  if (tokens.some((t) => t.startsWith(q))) return true;
  if (q.length >= 3 && publisher.includes(q)) return true;
  return false;
}

function appIconMarkup(app, extraClass) {
  const cls = `app-icon ${extraClass || ""}`.trim();
  const letter = escapeHtml(app.initial || (app.name || "?")[0]);
  const color = escapeHtml(app.color || "#8a7355");
  const primary = app.icon || "";
  const fallback = app.icon_fallback || "";
  return `<span class="${cls}" style="--app-color:${color}" aria-hidden="true">
    <span class="app-icon-letter">${letter}</span>
    ${
      primary
        ? `<img class="app-icon-img" src="${escapeHtml(primary)}" alt="" loading="lazy" decoding="async"
            data-fallback="${escapeHtml(fallback)}"
            onload="this.classList.add('is-loaded')"
            onerror="if(this.dataset.fallback&&this.src!==this.dataset.fallback){this.src=this.dataset.fallback;this.dataset.fallback='';}else{this.remove()}">`
        : ""
    }
  </span>`;
}

function renderAppsGrid(apps, query) {
  const root = document.getElementById("apps-grid");
  const countEl = document.getElementById("apps-count");
  if (!root) return;
  const filtered = apps.filter((a) => appMatchesQuery(a, query));
  if (countEl) {
    const q = (query || "").trim();
    countEl.textContent = q
      ? `${filtered.length} match${filtered.length === 1 ? "" : "es"} for “${q}”`
      : `${filtered.length} app${filtered.length === 1 ? "" : "s"} in the public sample`;
  }
  if (!filtered.length) {
    root.innerHTML = `<p class="hero-desc apps-empty">No apps match that search.</p>`;
    return;
  }
  root.innerHTML = filtered
    .map(
      (app) => `
    <a class="app-card" href="./browse-app.html?app=${encodeURIComponent(app.slug)}">
      ${appIconMarkup(app)}
      <span class="app-card-text">
        <span class="app-card-name">${escapeHtml(app.name)}</span>
        <span class="app-card-publisher">${escapeHtml(app.publisher || "")}</span>
        <span class="app-card-meta">${app.task_count} task${app.task_count === 1 ? "" : "s"}</span>
      </span>
    </a>`
    )
    .join("");
}

async function initBrowseAppsPage() {
  const grid = document.getElementById("apps-grid");
  if (!grid) return;
  const appsUrl = document.body.dataset.apps || "../assets/data/apps.json";
  try {
    const data = await loadJson(appsUrl);
    const apps = data.apps || [];
    renderAppsGrid(apps, "");
    const search = document.getElementById("apps-search");
    if (search) {
      search.setAttribute("autocomplete", "off");
      search.setAttribute("autocapitalize", "off");
      search.setAttribute("autocorrect", "off");
      search.setAttribute("spellcheck", "false");
      search.name = "db500-apps-filter";
      let timer = null;
      const paint = () => renderAppsGrid(apps, search.value);
      search.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(paint, 60);
      });
      search.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          search.value = "";
          paint();
        }
      });
    }
  } catch (err) {
    grid.innerHTML = `<p class="hero-desc">Failed to load apps catalog.</p>`;
    console.error(err);
  }
}

function publicRunByKey(trajEntry, key) {
  if (!key || !trajEntry || !Array.isArray(trajEntry.runs)) return null;
  return trajEntry.runs.find((r) => r.run_key === key) || null;
}

function collectRunOrder(trajIndex) {
  const seen = new Map();
  if (Array.isArray(trajIndex?.public_run_order)) {
    for (const r of trajIndex.public_run_order) {
      if (r?.key) seen.set(r.key, r.label || r.key);
    }
    return seen;
  }
  for (const entry of Object.values(trajIndex?.public || {})) {
    for (const run of entry.runs || []) {
      if (run?.run_key && !seen.has(run.run_key)) {
        seen.set(run.run_key, run.run_label || run.run_key);
      }
    }
  }
  return seen;
}

function appTaskCard(task, run) {
  const tags = [
    task.is_ask_user ? `<span class="tag tag-ask">ASK USER</span>` : "",
    task.cross_app ? `<span class="tag tag-cross">cross-app</span>` : "",
    task.points != null ? `<span class="tag">${task.points} pt</span>` : "",
    task.difficulty ? `<span class="tag">${escapeHtml(String(task.difficulty))}</span>` : "",
  ]
    .filter(Boolean)
    .join("");
  let runBadge = "";
  if (run) {
    runBadge = `
      <div class="public-example-run">
        <span class="tag ${run.success === true ? "tag-run-ok" : run.success === false ? "tag-run-fail" : ""}">${
          run.success === true ? "&#10003; pass" : run.success === false ? "&#10007; fail" : "not run"
        }</span>
        ${run.steps != null ? `<span class="public-example-steps">${run.steps} steps</span>` : ""}
      </div>`;
  }
  const href = `./task.html?set=public&task_id=${encodeURIComponent(task.task_id)}${
    run?.run_key ? `&run=${encodeURIComponent(run.run_key)}` : ""
  }`;
  return `
    <article class="public-example" data-task-id="${escapeHtml(task.task_id)}">
      <div class="public-example-meta">
        <span class="public-example-cat">Day ${escapeHtml(String(task.day ?? "-"))}
          <span class="public-example-id">${escapeHtml(task.task_id)}</span></span>
      </div>
      ${tags ? `<div class="public-example-tags">${tags}</div>` : ""}
      ${runBadge}
      <pre class="public-example-prompt"><code>${escapeHtml(task.prompt || "")}</code></pre>
      <div class="card-footer">
        <a class="card-trajectory-link" href="${href}">&#9654; View trajectory</a>
      </div>
    </article>`;
}

async function initBrowseAppPage() {
  const list = document.getElementById("app-task-list");
  if (!list) return;
  const slug = getParam("app");
  const appsUrl = document.body.dataset.apps || "../assets/data/apps.json";
  const trajUrl = document.body.dataset.trajectoryIndex || "../assets/data/trajectories/index.json";
  try {
    const [appsData, trajIndex] = await Promise.all([loadJson(appsUrl), loadJson(trajUrl)]);
    const app = (appsData.apps || []).find((a) => a.slug === slug);
    if (!app) {
      document.getElementById("app-title").textContent = "App not found";
      document.getElementById("app-meta").textContent = "Unknown app slug.";
      return;
    }
    document.title = `${app.name} - DailyBench500`;
    document.getElementById("app-title").textContent = `${app.name}`;
    const platform = document.getElementById("app-platform");
    if (platform) platform.textContent = "Android";
    document.getElementById("app-meta").textContent = `${app.publisher} · ${app.task_count} public task${
      app.task_count === 1 ? "" : "s"
    }`;
    const iconHost = document.getElementById("app-icon");
    if (iconHost) {
      iconHost.outerHTML = appIconMarkup(app, "app-icon-lg");
    }

    const select = document.getElementById("app-run-select");
    const runs = collectRunOrder(trajIndex);
    if (select) {
      const opts = [`<option value="">All runs</option>`];
      for (const [key, label] of runs) {
        opts.push(`<option value="${escapeHtml(key)}">${escapeHtml(label)}</option>`);
      }
      select.innerHTML = opts.join("");
      if (typeof window.enhanceSiteSelects === "function") window.enhanceSiteSelects();
    }

    const paint = () => {
      const key = select ? select.value || "" : "";
      const cards = (app.tasks || []).map((task) => {
        const entry = trajIndex.public?.[task.task_id];
        let run = null;
        if (key) {
          run = publicRunByKey(entry, key) || {
            run_key: key,
            success: null,
            steps: null,
          };
        } else if (entry?.runs?.length) {
          run = entry.runs.find((r) => r.is_primary) || entry.runs[0];
        }
        return appTaskCard(task, run);
      });
      list.innerHTML = cards.join("") || `<p class="hero-desc">No public tasks for this app.</p>`;
      const countEl = document.getElementById("app-task-count");
      if (countEl) {
        countEl.textContent = key
          ? `${app.tasks.length} tasks · ${runs.get(key) || key}`
          : `${app.tasks.length} tasks · showing primary run when available`;
      }
    };
    if (select) select.addEventListener("change", paint);
    paint();
  } catch (err) {
    list.innerHTML = `<p class="hero-desc">Failed to load app trajectories.</p>`;
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initBrowseAppsPage();
  initBrowseAppPage();
});
