// Leaderboard for DailyBench300. Real results, sourced from the run reports
// in reports/ (day1-run.md, day2-run.md, day3-run.md, dailybench_report.py
// outputs in reports/metrics/, and the public-dataset run analyses). These
// numbers are hand-copied here (not fetched at build time) because the run
// folders are private / gitignored. Update these constants — and add another
// row — whenever a new model's results are published.
//
// Column definitions:
//   success  = verified success rate (fully-successful tasks / total), %
//   steps    = average completion steps across the run (NULL when not computed)
//   halluc   = hallucination rate (control self-reported success), %
//   transport = "wired" (USB ADB) or "wireless" (Tailscale / TCP ADB)
//
// Rows (from the reports in reports/public/):
//   2026-08-28 (qwen3.8-27b TEXT, wireless):  manual audit 37/60 = 61.7% SR, avg steps 29.25, halluc 0/60
//   2026-08-26 (gemini-3.1-flash-lite, wireless): manual audit 25/60 = 41.7% SR, avg steps 8.32, halluc 1/60
//   2026-08-26 (qwen3.8-27b VISION, wired):  manual audit 22/60 = 36.7% SR, avg steps 39.83, halluc 1/60
// Success = manual-audit ground truth (reports mark it authoritative over the
// self-reported official number).

const LEADERBOARD_ROWS = [
  {
    model: "qwen3.8-27b (TEXT)",
    params: "Public · 60 tasks · 2026-08-28",
    org: "Alibaba (OpenRouter)",
    mode: "wireless",
    runs: 60,
    success: { score: 61.7, margin: 0 },
    steps: 29.25,
    halluc: 0.0,
  },
  {
    model: "gemini-3.1-flash-lite",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Google (OpenRouter)",
    mode: "wireless",
    runs: 60,
    success: { score: 41.7, margin: 0 },
    steps: 8.32,
    halluc: 1.7,
  },
  {
    model: "qwen3.8-27b (VISION)",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Alibaba (OpenRouter)",
    mode: "wired",
    runs: 60,
    success: { score: 36.7, margin: 0 },
    steps: 39.83,
    halluc: 1.7,
  },
];

const MODE_FILTERS = [
  { value: "all", label: "All" },
  { value: "wired", label: "Wired" },
  { value: "wireless", label: "Wireless" },
];

let currentModeFilter = "all";
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

function formatHalluc(halluc) {
  return halluc == null ? "—" : `${halluc.toFixed(1)}%`;
}

const TABLE_SORTS = {
  rank: { label: "Score rank", defaultDirection: "asc", value: (row) => row.rankValue },
  success: { label: "Success rate", defaultDirection: "desc", value: (row) => row.success.score },
  steps: { label: "Avg steps", defaultDirection: "asc", value: (row) => row.steps },
  halluc: { label: "Hallucination", defaultDirection: "asc", value: (row) => row.halluc },
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
  if (currentModeFilter !== "all") {
    rows = rows.filter((row) => row.mode === currentModeFilter);
  }
  if (currentSearchQuery) {
    const q = currentSearchQuery.toLowerCase();
    rows = rows.filter((row) => row.model.toLowerCase().includes(q));
  }
  return rows;
}

function renderModeFilter() {
  const root = document.getElementById("lb-mode-filter");
  if (!root) return;
  root.innerHTML = `
    <label class="lb-filter-label" for="lb-mode-select">Transport</label>
    <div class="lb-select-wrap">
      <select id="lb-mode-select" class="lb-filter-select">
        ${MODE_FILTERS
          .map((opt) => {
            const count = opt.value === "all" ? LEADERBOARD_ROWS.length : LEADERBOARD_ROWS.filter((r) => r.mode === opt.value).length;
            return `<option value="${opt.value}"${opt.value === currentModeFilter ? " selected" : ""}>${opt.label} (${count})</option>`;
          })
          .join("")}
      </select>
    </div>
  `;
  const select = root.querySelector("#lb-mode-select");
  select.addEventListener("change", () => {
    currentModeFilter = select.value;
    renderLeaderboard();
  });
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
  success: { label: "Success", statLabel: "verified success rate" },
  steps: { label: "Avg steps", statLabel: "average completion steps" },
};

function sortableHeader(key, label, suffix = "") {
  const isActive = currentTableSort.key === key;
  const direction = isActive ? currentTableSort.direction : "none";
  const arrow = isActive ? (direction === "asc" ? "&#8593;" : "&#8595;") : "&#8597;";
  const ariaSort = direction === "asc" ? "ascending" : direction === "desc" ? "descending" : "none";
  return `
    <th aria-sort="${ariaSort}">
      <button type="button" class="lb-sort-btn${isActive ? " active" : ""}" data-sort-key="${key}" aria-label="Sort by ${TABLE_SORTS[key].label}">
        <span>${label}${suffix}</span><span class="lb-sort-arrow" aria-hidden="true">${arrow}</span>
      </button>
    </th>
  `;
}

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  if (rows.length === 0) {
    root.innerHTML = `<p class="lb-empty">No models benchmarked yet for this transport mode.</p>`;
    return;
  }
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr>
          ${sortableHeader("rank", "Score rank")}
          <th>Model</th>
          <th>Task set</th>
          ${sortableHeader("success", "Success rate")}
          ${sortableHeader("steps", "Avg steps")}
          ${sortableHeader("halluc", "Hallucination")}
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
                <td>${row.model}</td>
                <td class="lb-params">${row.params}</td>
                <td>${row.success.score.toFixed(1)}%</td>
                <td class="lb-score">${formatSteps(row.steps)}</td>
                <td class="lb-score">${formatHalluc(row.halluc)}</td>
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
