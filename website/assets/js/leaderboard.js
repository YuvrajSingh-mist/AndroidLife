// Leaderboard for DailyBench300. Real results, sourced from the run reports in
// reports/public/ (the "Official metrics" tables of each run). These numbers are
// hand-copied here (not fetched at build time) because the run folders are
// private / gitignored. Update these constants — and add another row — whenever
// a new model's results are published.
//
// Column definitions (also shown as the hover tooltips on each header):
//   success  = Success Rate: fully-successful tasks ÷ total (60), from the
//              report's official metrics table.
//   askUser  = Success Rate on the 7 ASK USER tasks (agent must ask the
//              simulated user for a load-bearing fact before acting).
//   guiOnly  = Success Rate on the 53 non-ASK-USER tasks (deterministic
//              end-state verified on device).
//   steps    = Average Completion Steps across the run.
//   queries  = Average User Queries per task.
//   uiq      = User Interaction Quality (fact-match) — how often the agent's
//              ask_user answer matched the ground-truth fact.
//   kbiq     = KB Interaction Quality (manual) — correct KB queries ÷ total.
//   elapsed  = Wall-clock run duration vs agent running time (cooldown removed).
//   hc       = Hallucination-control honesty — controls the agent honestly
//              reported as absent (vs falsely claiming success).
//   buckets  = Success rate by difficulty bucket: easy / medium / hard.
//
// Rows (from the reports in reports/public/):
//   2026-08-28 qwen3.8-27b TEXT      → SR 51.7%, steps 29.25, HC 7/7
//   2026-08-26 gemini-3.1-flash-lite → SR 63.3%, steps 8.32,  HC 6/7
//   2026-08-26 qwen3.8-27b VISION    → SR 38.3%, steps 39.83, HC 6/7

const COL_DEFS = {
  success: "Success Rate — fully-successful tasks ÷ total (60), from the run's official metrics table (verified, false-passes excluded).",
  askUser: "Success Rate on the 7 ASK USER tasks, where the agent must ask the simulated user (gpt-5.4-mini) for a load-bearing fact before acting.",
  guiOnly: "Success Rate on the 53 non-ASK-USER tasks, where the end state is verified directly on the device (deterministic).",
  steps: "Average Completion Steps — mean agent steps per task across the run.",
  queries: "Average User Queries — mean number of times the agent asked the simulated user per task.",
  uiq: "User Interaction Quality (UIQ, fact-match) — share of ask_user calls whose answer matched the ground-truth fact.",
  kbiq: "KB Interaction Quality (KBIQ, manual) — correct knowledge-base queries ÷ total KB queries asked.",
  elapsed: "Elapsed — wall-clock run duration (including resets) vs agent running time (cooldown between tasks subtracted).",
  hc: "Hallucination-control honesty — share of the 7 controls the agent honestly reported as absent, instead of falsely claiming success.",
  buckets: "Success rate by difficulty bucket: easy / medium / hard.",
};

const LEADERBOARD_ROWS = [
  {
    model: "qwen3.8-27b (TEXT)",
    params: "Public · 60 tasks · 2026-08-28",
    org: "Alibaba (OpenRouter)",
    runs: 60,
    success: { score: 51.7, margin: 0 },
    askUser: 14.3,
    guiOnly: 56.6,
    steps: 29.25,
    queries: 0.57,
    uiq: 0.033,
    kbiq: "N/A",
    elapsed: { wall: "23223 s (6.45 h)", agent: "22633 s" },
    hc: { score: 100, detail: "7/7 honest" },
    buckets: { easy: 73.1, medium: 52.9, hard: 17.6 },
  },
  {
    model: "gemini-3.1-flash-lite",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Google (OpenRouter)",
    runs: 60,
    success: { score: 63.3, margin: 0 },
    askUser: 42.9,
    guiOnly: 64.2,
    steps: 8.32,
    queries: 0.71,
    uiq: 0.125,
    kbiq: "0.000",
    elapsed: { wall: "5932 s (1.65 h)", agent: "5342 s (1.48 h)" },
    hc: { score: 85.7, detail: "6/7 honest" },
    buckets: { easy: 65.4, medium: 64.7, hard: 47.1 },
  },
  {
    model: "qwen3.8-27b (VISION)",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Alibaba (OpenRouter)",
    runs: 60,
    success: { score: 38.3, margin: 0 },
    askUser: 14.3,
    guiOnly: 41.5,
    steps: 39.83,
    queries: 0.43,
    uiq: 0.125,
    kbiq: "0.000",
    elapsed: { wall: "32452 s (9.01 h)", agent: "31862 s (8.85 h)" },
    hc: { score: 85.7, detail: "6/7 honest" },
    buckets: { easy: 57.7, medium: 23.5, hard: 23.5 },
  },
];

let currentSearchQuery = "";
let currentTableSort = { key: "success", direction: "desc" };

function ordinal(n) {
  const rem100 = n % 100;
  if (rem100 >= 11 && rem100 <= 13) return `${n}th`;
  switch (n % 10) {
    case 1:
      return `${n}st`;
    case 2:
      return `${n}nd`;
    case 3:
      return `${n}rd`;
    default:
      return `${n}th`;
  }
}

function formatSteps(steps) {
  return steps == null ? "—" : steps.toFixed(2);
}

const TABLE_SORTS = {
  rank: { label: "Score rank", defaultDirection: "asc", value: (row) => row.rankValue },
  success: { label: "Success rate", defaultDirection: "desc", value: (row) => row.success.score },
  askUser: { label: "ASK USER", defaultDirection: "desc", value: (row) => row.askUser },
  guiOnly: { label: "GUI-only", defaultDirection: "desc", value: (row) => row.guiOnly },
  steps: { label: "Avg steps", defaultDirection: "asc", value: (row) => row.steps },
  queries: { label: "Avg queries", defaultDirection: "desc", value: (row) => row.queries },
  uiq: { label: "UIQ", defaultDirection: "desc", value: (row) => row.uiq },
  kbiq: { label: "KBIQ", defaultDirection: "desc", value: (row) => (row.kbiq === "N/A" ? -1 : parseFloat(row.kbiq)) },
  elapsed: { label: "Elapsed", defaultDirection: "asc", value: (row) => parseFloat(row.elapsed.wall) },
  hc: { label: "HC honesty", defaultDirection: "desc", value: (row) => row.hc.score },
  buckets: { label: "Buckets", defaultDirection: "desc", value: (row) => row.buckets.easy },
  runs: { label: "Runs", defaultDirection: "desc", value: (row) => row.runs },
  org: { label: "Organization", defaultDirection: "asc", value: (row) => row.org.toLowerCase() },
};

function rankedRows(rows) {
  const rankByModel = new Map(
    [...rows]
      .sort((a, b) => b.success.score - a.success.score || a.model.localeCompare(b.model))
      .map((row, index) => [row.model + "|" + row.params, index + 1])
  );
  const sort = TABLE_SORTS[currentTableSort.key];
  const direction = currentTableSort.direction === "asc" ? 1 : -1;

  return rows
    .map((row) => {
      const rankValue = rankByModel.get(row.model + "|" + row.params);
      return { ...row, rankValue, rank: ordinal(rankValue) };
    })
    .sort((a, b) => {
      const aValue = sort.value(a);
      const bValue = sort.value(b);
      if (aValue == null && bValue != null) return 1;
      if (aValue != null && bValue == null) return -1;
      if (typeof aValue === "string" && typeof bValue === "string") {
        return direction * aValue.localeCompare(bValue) || a.model.localeCompare(b.model);
      }
      return direction * (aValue - bValue) || a.model.localeCompare(b.model);
    });
}

function getFilteredRows() {
  let rows = LEADERBOARD_ROWS;
  if (currentSearchQuery) {
    const q = currentSearchQuery.toLowerCase();
    rows = rows.filter((row) => row.model.toLowerCase().includes(q));
  }
  return rows;
}

function renderModeFilter() {
  const root = document.getElementById("lb-mode-filter");
  if (root) root.innerHTML = "";
}

function renderSearchBar() {
  const root = document.getElementById("lb-search-bar");
  if (!root) return;
  root.innerHTML = `
    <input
      type="search"
      class="lb-search-input"
      id="lb-search-input"
      placeholder="Search for any model"
      value="${currentSearchQuery.replace(/"/g, "&quot;")}"
      autocomplete="off"
    />
  `;
  const input = root.querySelector("#lb-search-input");
  let debounceTimer;
  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentSearchQuery = input.value.trim();
      renderLeaderboard();
    }, 200);
  });
}

const METRICS = {
  success: { label: "Success", statLabel: "success rate" },
  steps: { label: "Avg steps", statLabel: "average completion steps" },
};

// Header for a sortable column. `tip` (optional) renders a hover tooltip with
// the metric's definition, styled to match the site (same as info-tooltip).
function sortableHeader(key, label, tip = "", suffix = "") {
  const isActive = currentTableSort.key === key;
  const direction = isActive ? currentTableSort.direction : "none";
  const arrow = isActive ? (direction === "asc" ? "&#8593;" : "&#8595;") : "&#8597;";
  const ariaSort = direction === "asc" ? "ascending" : direction === "desc" ? "descending" : "none";
  const tooltip = tip
    ? `
      <span class="lb-col-info" tabindex="0" role="button" aria-label="Definition of ${label}">
        <span class="lb-col-info-ico" aria-hidden="true">&#9432;</span>
        <span class="lb-col-tip" role="tooltip">${tip}</span>
      </span>`
    : "";
  return `
    <th aria-sort="${ariaSort}">
      <button type="button" class="lb-sort-btn${isActive ? " active" : ""}" data-sort-key="${key}" aria-label="Sort by ${TABLE_SORTS[key].label}">
        <span>${label}${suffix}</span><span class="lb-sort-arrow" aria-hidden="true">${arrow}</span>
      </button>
      ${tooltip}
    </th>
  `;
}

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  if (rows.length === 0) {
    root.innerHTML = `<p class="lb-empty">No models benchmarked yet.</p>`;
    return;
  }
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr>
          ${sortableHeader("rank", "Score rank")}
          <th>Model</th>
          ${sortableHeader("success", "Success rate", COL_DEFS.success)}
          ${sortableHeader("askUser", "ASK USER", COL_DEFS.askUser)}
          ${sortableHeader("guiOnly", "GUI-only", COL_DEFS.guiOnly)}
          ${sortableHeader("steps", "Avg steps", COL_DEFS.steps)}
          ${sortableHeader("queries", "Avg queries", COL_DEFS.queries)}
          ${sortableHeader("uiq", "UIQ", COL_DEFS.uiq)}
          ${sortableHeader("kbiq", "KBIQ", COL_DEFS.kbiq)}
          ${sortableHeader("elapsed", "Elapsed", COL_DEFS.elapsed)}
          ${sortableHeader("hc", "HC honesty", COL_DEFS.hc)}
          ${sortableHeader("buckets", "Buckets E / M / H", COL_DEFS.buckets)}
          ${sortableHeader("runs", "Runs")}
          ${sortableHeader("org", "Organization")}
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr class="${row.rank === "1st" ? "lb-row-rank1" : ""}">
                <td class="lb-rank">${row.rank}</td>
                <td>${row.model}<span class="lb-sub">${row.params.replace("Public · ", "")}</span></td>
                <td class="lb-score">${row.success.score.toFixed(1)}%</td>
                <td class="lb-score">${formatPct(row.askUser)}</td>
                <td class="lb-score">${formatPct(row.guiOnly)}</td>
                <td class="lb-score">${formatSteps(row.steps)}</td>
                <td class="lb-score">${row.queries.toFixed(2)}</td>
                <td class="lb-score">${row.uiq.toFixed(3)}</td>
                <td class="lb-score">${escapeHtml(row.kbiq)}</td>
                <td class="lb-score"><span class="lb-elapsed">${row.elapsed.wall}</span><span class="lb-sub">agent ${row.elapsed.agent}</span></td>
                <td class="lb-score">${row.hc.score.toFixed(1)}%<span class="lb-sub">${row.hc.detail}</span></td>
                <td class="lb-score">${row.buckets.easy.toFixed(1)} / ${row.buckets.medium.toFixed(1)} / ${row.buckets.hard.toFixed(1)}</td>
                <td>${row.runs}</td>
                <td>${row.org}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;

  for (const button of root.querySelectorAll(".lb-sort-btn")) {
    button.addEventListener("click", () => {
      const key = button.dataset.sortKey;
      if (currentTableSort.key === key) {
        currentTableSort.direction = currentTableSort.direction === "asc" ? "desc" : "asc";
      } else {
        currentTableSort = { key, direction: TABLE_SORTS[key].defaultDirection };
      }
      renderTable(containerId, rankedRows(getFilteredRows()));
    });
  }
}

function formatPct(value) {
  return value == null ? "—" : `${value.toFixed(1)}%`;
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function makeTooltip(card) {
  const existing = card.querySelector(".lb-tooltip");
  if (existing) existing.remove();
  const tooltip = document.createElement("div");
  tooltip.className = "lb-tooltip";
  card.style.position = "relative";
  card.appendChild(tooltip);
  return tooltip;
}

function showTooltip(tooltip, x, y, html) {
  tooltip.innerHTML = html;
  tooltip.style.top = `${y}px`;
  tooltip.classList.add("active");

  const containerWidth = tooltip.parentElement.clientWidth;
  const halfWidth = tooltip.offsetWidth / 2;
  const edgePadding = 8;
  const minX = halfWidth + edgePadding;
  const maxX = containerWidth - halfWidth - edgePadding;
  const clampedX = minX > maxX ? containerWidth / 2 : Math.max(minX, Math.min(maxX, x));
  tooltip.style.left = `${clampedX}px`;
  tooltip.classList.toggle("below", y - tooltip.offsetHeight - 10 < edgePadding);
}

function hideTooltip(tooltip) {
  tooltip.classList.remove("active");
}

let currentChartMetric = "success";
let pinnedChartTooltip = null;

document.addEventListener("click", (event) => {
  if (!pinnedChartTooltip || event.target.closest(".lb-hit")) return;
  hideTooltip(pinnedChartTooltip.tooltip);
  pinnedChartTooltip = null;
});

function renderMetricToggle(card) {
  const root = card.querySelector(".lb-metric-toggle");
  if (!root) return;
  root.innerHTML = Object.entries(METRICS)
    .map(
      ([key, meta]) => `
        <button class="lb-metric-btn${key === currentChartMetric ? " active" : ""}" data-metric="${key}">${meta.label}</button>
      `
    )
    .join("");
  for (const btn of root.querySelectorAll(".lb-metric-btn")) {
    btn.addEventListener("click", () => {
      currentChartMetric = btn.dataset.metric;
      renderPerfDollarChart();
    });
  }
}

// Scatter of the chosen metric (success rate or avg steps) vs. average
// completion steps, so you can see the success-vs-efficiency tradeoff.
// Rows without an avg-steps value are placed in a categorical band on the left.
function renderPerfDollarChart() {
  const card = document.getElementById("perf-dollar-chart");
  if (!card) return;
  const width = 760;
  const height = 360;
  const margin = { top: 16, right: 24, bottom: 44, left: 68 };
  const plotH = height - margin.top - margin.bottom;
  const paidPlotStart = 250;
  const paidPlotWidth = width - margin.right - paidPlotStart;
  const localBandStart = margin.left + 18;
  const localBandEnd = paidPlotStart - 24;

  const xMin = 20;
  const xMax = 80;
  const yMin = 0;
  const yMax = 100;
  const visibleRows = getFilteredRows();

  const xScaleSteps = (steps) =>
    paidPlotStart + ((Math.min(Math.max(steps, xMin), xMax) - xMin) / (xMax - xMin)) * paidPlotWidth;
  const yScale = (score) => margin.top + plotH - ((score - yMin) / (yMax - yMin)) * plotH;

  // Rows with no avg-steps value get a categorical band on the left.
  const unknownRows = visibleRows
    .filter((row) => row.steps == null)
    .sort((a, b) => a.model.localeCompare(b.model));
  const unknownXByModel = new Map(
    unknownRows.map((row, index) => {
      const ratio = unknownRows.length === 1 ? 0.5 : index / (unknownRows.length - 1);
      return [row.model + "|" + row.params, localBandStart + ratio * (localBandEnd - localBandStart)];
    })
  );

  const pointLayouts = [];
  const offsetCandidates = [0, -28, 28, -56, 56, -84, 84, -112, 112];
  for (const row of [...visibleRows].sort((a, b) => (a.steps || 0) - (b.steps || 0) || a.model.localeCompare(b.model))) {
    const point = row[currentChartMetric];
    const cy = yScale(currentChartMetric === "success" ? point.score : point);
    const isUnknown = row.steps == null;
    const baseX = isUnknown ? unknownXByModel.get(row.model + "|" + row.params) : xScaleSteps(row.steps);
    let cx = baseX;

    if (!isUnknown) {
      for (const offset of offsetCandidates) {
        const candidateX = Math.max(paidPlotStart, Math.min(width - margin.right, baseX + offset));
        const overlaps = pointLayouts.some(
          (placed) => Math.hypot(candidateX - placed.cx, cy - placed.cy) < 28
        );
        if (!overlaps) {
          cx = candidateX;
          break;
        }
      }
    }

    pointLayouts.push({ row, point, cx, cy });
  }

  const xTicks = [20, 30, 40, 50, 60, 70, 80];
  const yTicks = [0, 25, 50, 75, 100];
  const metricMeta = METRICS[currentChartMetric];
  const localBandCenter = (localBandStart + localBandEnd) / 2;

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${metricMeta.label} (${metricMeta.statLabel}) versus average completion steps">`;

  for (const t of yTicks) {
    const y = yScale(t);
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${t}%</text>`;
  }
  if (unknownRows.length > 0) {
    svg += `<text class="lb-tick-label" x="${localBandCenter}" y="${height - margin.bottom + 16}" text-anchor="middle">no steps</text>`;
    svg += `<line class="lb-cost-band-divider" x1="${paidPlotStart - 12}" y1="${margin.top}" x2="${paidPlotStart - 12}" y2="${margin.top + plotH}" />`;
  }
  for (const t of xTicks) {
    const x = xScaleSteps(t);
    svg += `<text class="lb-tick-label" x="${x}" y="${height - margin.bottom + 16}" text-anchor="middle">${t}</text>`;
  }
  svg += `<text class="lb-axis-label" x="${margin.left + (width - margin.right - margin.left) / 2}" y="${height - 6}" text-anchor="middle">Average completion steps per run</text>`;
  svg += `<text class="lb-axis-label" transform="translate(14 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">${metricMeta.label} (%)</text>`;

  for (const { row, point, cx, cy } of pointLayouts) {
    const priceLabel = row.steps == null ? "no steps" : row.steps.toFixed(2) + " steps";
    svg += `<circle class="lb-dot" cx="${cx}" cy="${cy}" r="6" fill="var(--accent)" />`;
    svg += `<circle class="lb-hit" cx="${cx}" cy="${cy}" r="13" tabindex="0" role="button" aria-label="${row.model} (${row.params}): ${currentChartMetric === "success" ? point.score + "% success" : point + " avg steps"}, ${priceLabel}" data-model="${row.model}" data-price-label="${priceLabel}" data-score="${currentChartMetric === "success" ? point.score : point}" data-stat-label="${metricMeta.statLabel}" />`;
  }

  const inner = card.querySelector(".lb-chart-card-inner");
  const container = inner || card;
  const hits = container.querySelectorAll(".lb-hit");
  const tooltip = makeTooltip(container);
  for (const hit of hits) {
    const model = hit.dataset.model;
    const label = hit.dataset.priceLabel;
    const score = hit.dataset.score;
    const statLabel = hit.dataset.statLabel;
    const row = visibleRows.find((r) => r.model === model);
    const html = `<strong>${model}</strong><span>${row ? row.params : ""}</span><span>${score} · ${statLabel}</span><span>${label}</span>`;
    hit.addEventListener("mouseenter", (event) => showTooltip(tooltip, event.clientX - container.getBoundingClientRect().left, event.clientY - container.getBoundingClientRect().top, html));
    hit.addEventListener("mouseleave", () => hideTooltip(tooltip));
    hit.addEventListener("focus", (event) => showTooltip(tooltip, event.clientX - container.getBoundingClientRect().left, event.clientY - container.getBoundingClientRect().top, html));
    hit.addEventListener("blur", () => hideTooltip(tooltip));
    hit.addEventListener("click", (event) => {
      event.preventDefault();
      if (pinnedChartTooltip && pinnedChartTooltip.tooltip === tooltip && tooltip.classList.contains("active")) {
        hideTooltip(tooltip);
        pinnedChartTooltip = null;
      } else {
        showTooltip(tooltip, event.clientX - container.getBoundingClientRect().left, event.clientY - container.getBoundingClientRect().top, html);
        pinnedChartTooltip = { tooltip, model };
      }
    });
  }

  container.innerHTML += svg;
}

function renderLeaderboard() {
  renderModeFilter();
  renderSearchBar();
  renderTable("mcq-table", rankedRows(getFilteredRows()));
  const chartCard = document.getElementById("perf-dollar-chart");
  if (chartCard) {
    chartCard.innerHTML = `
      <div class="lb-metric-toggle" role="tablist" aria-label="Score dimension"></div>
      <div class="lb-chart-card-inner"></div>
    `;
    renderMetricToggle(chartCard);
    renderPerfDollarChart();
  }
}

// Tab switching
document.addEventListener("DOMContentLoaded", () => {
  renderLeaderboard();
  for (const tab of document.querySelectorAll(".lb-tab")) {
    tab.addEventListener("click", () => {
      for (const t of document.querySelectorAll(".lb-tab")) t.classList.remove("active");
      for (const p of document.querySelectorAll(".lb-panel")) p.classList.remove("active");
      tab.classList.add("active");
      document.getElementById(tab.dataset.panel).classList.add("active");
    });
  }
});
