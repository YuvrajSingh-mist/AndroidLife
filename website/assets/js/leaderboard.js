// Leaderboard for DailyBench500. Real results, sourced from the run reports in
// reports/public/ (the MANUAL AUDIT sections of each run). The reports state
// explicitly that the manual audit is the ground truth — the "Official metrics"
// tables are self-reported and inflated (e.g. gemini's official 63.3% hides 12
// false passes; its manual headline is 41.7%). These numbers are hand-copied
// here (not fetched at build time) because the run folders are private /
// gitignored. Update these constants — and add another row — whenever a new
// model's results are published.
//
// Column definitions (also shown in the "How the metrics are computed" tooltip):
//   success  = Manual-audit Success Rate: fully-successful tasks ÷ total (60),
//              from the report's manual audit (honest-fail controls count as
//              success; false passes downgraded to FAIL).
//   askUser  = Manual interaction pass rate on the 10 ASK USER tasks (6 SINGLE
//              + 4 MULTI) — agent must ask the simulated user for a
//              load-bearing fact before acting.
//   guiOnly  = Manual genuine pass rate on the 53 non-control tasks (honest-fail
//              controls excluded).
//   steps    = Average Completion Steps across the run.
//   queries  = Average User Queries per task.
//   uiq      = User Interaction Quality (fact-match) — how often the agent's
//              ask_user answer matched the ground-truth fact.
//   kbiq     = KB Interaction Quality (manual) — correct KB queries ÷ total.
//   elapsed  = Wall-clock run duration vs agent running time (cooldown removed).
//   hc       = Hallucination-control honesty — controls the agent honestly
//              reported as absent (vs falsely claiming success).
//   buckets  = Manual success rate by difficulty bucket: easy / medium / hard.
//   cost      = Agent LLM cost (prompt + completion) + request count.
//   askUserCost = Cost of the simulated-user (gpt-5.4-mini) ask_user calls.
//   totalCost = Grand total run cost, with the ≈$/task figure.
//   cpuTemp   = Max CPU/GPU/NPU temp (°C) sampled per second during the run.
//   powerSkinTemp = Max power-amp / skin temp (°C).
//   batteryTemp = Max battery temp (°C).
//   batteryDrain = Total battery drain across the run (per-task Δ sum, %).
//
// Rows (manual audit, from the reports in reports/public/):
//   2026-08-28 qwen3.8-27b TEXT      → SR 61.7%, steps 29.25, HC 7/7
//   2026-08-26 gemini-3.1-flash-lite → SR 41.7%, steps 8.32,  HC 6/7
//   2026-08-26 qwen3.8-27b VISION    → SR 36.7%, steps 39.83, HC 6/7

const COL_DEFS = {
  success: "manual-audit success rate: fully-successful tasks ÷ 60, from the run report's manual audit (honest-fail controls count as success; false passes downgraded to FAIL). The manual audit is the ground truth — the official self-reported metric was inflated.",
  askUser: "manual interaction pass rate on the 10 ASK USER tasks (6 SINGLE + 4 MULTI), where the agent must ask the simulated user (gpt-5.4-mini) for a load-bearing fact before acting.",
  guiOnly: "manual genuine pass rate on the 53 non-control tasks (honest-fail hallucination controls excluded), where the end state is verified directly on the device.",
  steps: "mean agent steps per task across the run.",
  queries: "mean number of times the agent asked the simulated user per task.",
  uiq: "User Interaction Quality (UIQ, fact-match) — share of ask_user calls whose answer matched the ground-truth fact.",
  kbiq: "KB Interaction Quality (KBIQ, manual) — correct knowledge-base queries ÷ total KB queries asked.",
  elapsed: "wall-clock run duration (including resets) vs agent running time (cooldown between tasks subtracted).",
  hc: "share of the 7 controls the agent honestly reported as absent, instead of falsely claiming success.",
  buckets: "manual success rate by difficulty bucket: easy / medium / hard.",
  cost: "agent LLM cost (prompt + completion) for the run, from llm_proxy_metrics.jsonl (per-request tokens & price), plus the request count.",
  askUserCost: "cost of the simulated-user model (gpt-5.4-mini) ask_user calls, from ask_user_metrics.jsonl.",
  totalCost: "grand total run cost (agent LLM + ask_user), with the ≈ per-task figure.",
  cpuTemp: "max on-device CPU / GPU / NPU temperature (°C), sampled per second per task (samples.ndjson).",
  powerSkinTemp: "max power-amp / skin temperature (°C), sampled per second per task.",
  batteryTemp: "max battery temperature (°C), sampled per second per task.",
  batteryDrain: "total battery drain across the run — sum of per-task battery deltas (%). A battery-death gap (task died at 0%) shows as a large negative.",
};

const LEADERBOARD_ROWS = [
  {
    model: "qwen3.8-27b (TEXT)",
    params: "Public · 60 tasks · 2026-08-28",
    org: "Alibaba (OpenRouter)",
    mode: "text",
    runs: 60,
    success: { score: 61.7, margin: 0 },
    askUser: 20.0,
    guiOnly: 56.6,
    steps: 29.25,
    queries: 0.57,
    uiq: 0.033,
    kbiq: "N/A",
    elapsed: { wall: "23223 s (6.45 h)", agent: "22633 s" },
    hc: { score: 100, detail: "7/7 honest" },
    buckets: { easy: 88.5, medium: 52.9, hard: 29.4 },
    cost: { total: 7.133, detail: "1,844 requests" },
    askUserCost: { total: 0.0022, detail: "7 requests" },
    totalCost: { total: 7.14, perTask: 0.119 },
    cpuTemp: { max: 98.2, detail: "CPU / GPU — hot (many step-capped tasks burned heavy context)" },
    powerSkinTemp: null,
    batteryTemp: 37.9,
    batteryDrain: -71,
  },
  {
    model: "gemini-3.1-flash-lite",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Google (OpenRouter)",
    mode: "text",
    runs: 60,
    success: { score: 41.7, margin: 0 },
    askUser: 10.0,
    guiOnly: 37.7,
    steps: 8.32,
    queries: 0.71,
    uiq: 0.125,
    kbiq: "0.000",
    elapsed: { wall: "5932 s (1.65 h)", agent: "5342 s (1.48 h)" },
    hc: { score: 85.7, detail: "6/7 honest" },
    buckets: { easy: 69.2, medium: 29.4, hard: 11.8 },
    cost: { total: 1.086, detail: "626 requests" },
    askUserCost: { total: 0.0024, detail: "7 requests" },
    totalCost: { total: 1.09, perTask: 0.018 },
    cpuTemp: { max: 86.5, detail: "CPU 86.4 · GPU 86.4 · NPU 86.5 — no throttling" },
    powerSkinTemp: { max: 47.4, detail: "power-amp 47.4 · skin 47.2" },
    batteryTemp: 37.8,
    batteryDrain: -21,
  },
  {
    model: "qwen3.8-27b (VISION)",
    params: "Public · 60 tasks · 2026-08-26",
    org: "Alibaba (OpenRouter)",
    mode: "vision",
    runs: 60,
    success: { score: 36.7, margin: 0 },
    askUser: 20.0,
    guiOnly: 39.6,
    steps: 39.83,
    queries: 0.43,
    uiq: 0.125,
    kbiq: "0.000",
    elapsed: { wall: "32452 s (9.01 h)", agent: "31862 s (8.85 h)" },
    hc: { score: 85.7, detail: "6/7 honest" },
    buckets: { easy: 57.7, medium: 23.5, hard: 17.6 },
    cost: { total: 8.369, detail: "2,530 requests" },
    askUserCost: { total: 0.0036, detail: "4 requests" },
    totalCost: { total: 8.37, perTask: 0.140 },
    cpuTemp: { max: 85.6, detail: "CPU 85.6 · GPU 85.6 · NPU 85.6" },
    powerSkinTemp: { max: 45.8, detail: "power-amp 45.8 · skin 45.4" },
    batteryTemp: 37.7,
    batteryDrain: -99,
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
  cost: { label: "Agent LLM cost", defaultDirection: "asc", value: (row) => row.cost.total },
  askUserCost: { label: "ask_user cost", defaultDirection: "asc", value: (row) => row.askUserCost.total },
  totalCost: { label: "Total cost", defaultDirection: "asc", value: (row) => row.totalCost.total },
  cpuTemp: { label: "CPU/GPU/NPU temp", defaultDirection: "desc", value: (row) => row.cpuTemp.max },
  powerSkinTemp: { label: "Power-amp/skin temp", defaultDirection: "desc", value: (row) => (row.powerSkinTemp ? row.powerSkinTemp.max : -Infinity) },
  batteryTemp: { label: "Battery temp", defaultDirection: "desc", value: (row) => row.batteryTemp },
  batteryDrain: { label: "Battery drain", defaultDirection: "asc", value: (row) => row.batteryDrain },
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

// Ordered column definitions for the leaderboard table. `rank` + `model` are
// always shown; the rest can be toggled on/off via the "Columns" dropdown.
const COLUMNS = [
  { key: "rank", label: "Score rank", always: true, header: (label) => sortableHeader("rank", label), cell: (r) => `<td class="lb-rank">${r.rank}</td>` },
  { key: "model", label: "Model", always: true, header: () => `<th>Model</th>`, cell: (r) => `<td>${r.model}</td>` },
  { key: "success", label: "Success rate", def: COL_DEFS.success, cell: (r) => `<td class="lb-score">${r.success.score.toFixed(1)}%</td>` },
  { key: "askUser", label: "ASK USER", def: COL_DEFS.askUser, cell: (r) => `<td class="lb-score">${formatPct(r.askUser)}</td>` },
  { key: "guiOnly", label: "GUI-only", def: COL_DEFS.guiOnly, cell: (r) => `<td class="lb-score">${formatPct(r.guiOnly)}</td>` },
  { key: "steps", label: "Avg steps", def: COL_DEFS.steps, cell: (r) => `<td class="lb-score">${formatSteps(r.steps)}</td>` },
  { key: "queries", label: "Avg queries", def: COL_DEFS.queries, cell: (r) => `<td class="lb-score">${r.queries.toFixed(2)}</td>` },
  { key: "uiq", label: "UIQ", def: COL_DEFS.uiq, cell: (r) => `<td class="lb-score">${r.uiq.toFixed(3)}</td>` },
  { key: "kbiq", label: "KBIQ", def: COL_DEFS.kbiq, cell: (r) => `<td class="lb-score">${escapeHtml(r.kbiq)}</td>` },
  { key: "elapsed", label: "Elapsed", def: COL_DEFS.elapsed, cell: (r) => `<td class="lb-score"><span class="lb-elapsed">${r.elapsed.wall}</span><span class="lb-sub">agent ${r.elapsed.agent}</span></td>` },
  { key: "hc", label: "HC honesty", def: COL_DEFS.hc, cell: (r) => `<td class="lb-score">${r.hc.score.toFixed(1)}%<span class="lb-sub">${r.hc.detail}</span></td>` },
  { key: "buckets", label: "Buckets E / M / H", def: COL_DEFS.buckets, cell: (r) => `<td class="lb-score">${r.buckets.easy.toFixed(1)} / ${r.buckets.medium.toFixed(1)} / ${r.buckets.hard.toFixed(1)}</td>` },
  { key: "cost", label: "Agent LLM cost", def: COL_DEFS.cost, cell: (r) => `<td class="lb-score">$${r.cost.total.toFixed(2)}<span class="lb-sub">${r.cost.detail}</span></td>` },
  { key: "askUserCost", label: "ask_user cost", def: COL_DEFS.askUserCost, cell: (r) => `<td class="lb-score">$${r.askUserCost.total.toFixed(4)}<span class="lb-sub">${r.askUserCost.detail}</span></td>` },
  { key: "totalCost", label: "Total cost", def: COL_DEFS.totalCost, cell: (r) => `<td class="lb-score">$${r.totalCost.total.toFixed(2)}<span class="lb-sub">≈ $${r.totalCost.perTask.toFixed(3)} / task</span></td>` },
  { key: "cpuTemp", label: "CPU/GPU/NPU temp", def: COL_DEFS.cpuTemp, cell: (r) => `<td class="lb-score">${r.cpuTemp.max.toFixed(1)} °C<span class="lb-sub">${r.cpuTemp.detail}</span></td>` },
  { key: "powerSkinTemp", label: "Power-amp/skin temp", def: COL_DEFS.powerSkinTemp, cell: (r) => `<td class="lb-score">${r.powerSkinTemp ? r.powerSkinTemp.max.toFixed(1) + " °C" : "—"}<span class="lb-sub">${r.powerSkinTemp ? r.powerSkinTemp.detail : "not sampled"}</span></td>` },
  { key: "batteryTemp", label: "Battery temp", def: COL_DEFS.batteryTemp, cell: (r) => `<td class="lb-score">${r.batteryTemp.toFixed(1)} °C</td>` },
  { key: "batteryDrain", label: "Battery drain", def: COL_DEFS.batteryDrain, cell: (r) => `<td class="lb-score">${r.batteryDrain}%</td>` },
  { key: "runs", label: "Runs", cell: (r) => `<td>${r.runs}</td>` },
  { key: "org", label: "Organization", cell: (r) => `<td>${r.org}</td>` },
];

// Which metric columns are visible in the table (toggled via the Columns
// dropdown). rank + model are always shown. The original metric set stays on by
// default; the cost / thermal / battery columns added later default to OFF so
// the table doesn't get crowded (they're one checkbox away in the dropdown).
const columnVisibility = Object.fromEntries(
  COLUMNS.filter((c) => !c.always).map((c) => [c.key, true])
);
for (const off of ["cost", "askUserCost", "totalCost", "cpuTemp", "powerSkinTemp", "batteryTemp", "batteryDrain"]) {
  columnVisibility[off] = false;
}

// Renders the "Columns" dropdown with a checkbox per metric column. Toggling a
// checkbox immediately shows/hides that column in the table.
function renderMetricsToggle() {
  const root = document.getElementById("lb-metrics-toggle");
  if (!root) return;
  const toggleables = COLUMNS.filter((c) => !c.always);
  root.innerHTML = `
    <div class="lb-metrics">
      <button type="button" class="lb-metrics-btn" id="lb-metrics-btn" aria-haspopup="true" aria-expanded="false">
        <span>Columns</span><span class="lb-metrics-arrow" aria-hidden="true">&#9662;</span>
      </button>
      <div class="lb-metrics-panel" id="lb-metrics-panel" hidden>
        ${toggleables
          .map(
            (c) => `
              <label class="lb-metrics-option">
                <input type="checkbox" data-col="${c.key}" ${columnVisibility[c.key] ? "checked" : ""} />
                <span>${c.label}</span>
              </label>`
          )
          .join("")}
      </div>
    </div>
  `;

  const btn = root.querySelector("#lb-metrics-btn");
  const panel = root.querySelector("#lb-metrics-panel");
  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    const open = panel.hidden;
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  });
  for (const box of root.querySelectorAll('input[data-col]')) {
    box.addEventListener("change", () => {
      columnVisibility[box.dataset.col] = box.checked;
      renderTable("mcq-table", rankedRows(getFilteredRows()));
    });
  }
}

// Header for a sortable column. Metric definitions live in the "How the
// metrics are computed" tooltip (rendered by renderMetricsInfo), not on the
// column headers themselves.
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

function visibleColumns() {
  return COLUMNS.filter((c) => c.always || columnVisibility[c.key]);
}

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  if (rows.length === 0) {
    root.innerHTML = `<p class="lb-empty">No models benchmarked yet.</p>`;
    return;
  }
  const cols = visibleColumns();

  const headerCells = cols
    .map((c) => (c.always ? c.header(c.label) : sortableHeader(c.key, c.label)))
    .join("");

  const bodyRows = rows
    .map(
      (row) =>
        `<tr class="${row.rank === "1st" ? "lb-row-rank1" : ""}">${cols.map((c) => c.cell(row)).join("")}</tr>`
    )
    .join("");

  root.innerHTML = `
    <table class="lb-table">
      <thead><tr>${headerCells}</tr></thead>
      <tbody>${bodyRows}</tbody>
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

// Fills the "How the metrics are computed" tooltip (the info button under the
// leaderboard) with one definition per metric column. Scrollable via CSS so it
// never covers the whole page.
function renderMetricsInfo() {
  const list = document.getElementById("stats-tooltip-list");
  if (!list) return;
  const items = COLUMNS
    .filter((c) => c.def)
    .map((c) => `<li><strong>${escapeHtml(c.label)}</strong> — ${c.def}</li>`)
    .join("");
  list.innerHTML = items;
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

let pinnedChartTooltip = null;
let chartX = "success";
let chartY = "steps";
let chartMode = "all"; // "all" | "text" | "vision"

document.addEventListener("click", (event) => {
  if (pinnedChartTooltip && !event.target.closest(".lb-hit")) {
    hideTooltip(pinnedChartTooltip.tooltip);
    pinnedChartTooltip = null;
  }
  // Close the Columns dropdown when clicking outside it.
  const panel = document.getElementById("lb-metrics-panel");
  const btn = document.getElementById("lb-metrics-btn");
  if (panel && btn && !panel.hidden && !event.target.closest(".lb-metrics")) {
    panel.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  }
});

// Chartable metrics — every leaderboard column that has a numeric value, so the
// user can pick any X and Y axis freely. Default: X = success, Y = avg steps.
// Each difficulty bucket is its own metric so you can chart easy vs medium vs
// hard directly; cost / thermal / battery figures come from the run telemetry.
const CHART_METRICS = {
  success: { label: "Success rate", unit: "%", value: (r) => r.success.score },
  askUser: { label: "ASK USER", unit: "%", value: (r) => r.askUser },
  guiOnly: { label: "GUI-only", unit: "%", value: (r) => r.guiOnly },
  steps: { label: "Avg steps", unit: "", value: (r) => r.steps },
  queries: { label: "Avg queries", unit: "", value: (r) => r.queries },
  uiq: { label: "UIQ", unit: "", value: (r) => r.uiq },
  kbiq: { label: "KBIQ", unit: "", value: (r) => (r.kbiq === "N/A" ? null : parseFloat(r.kbiq)) },
  elapsed: { label: "Elapsed", unit: "s", value: (r) => parseFloat(r.elapsed.wall) },
  hc: { label: "HC honesty", unit: "%", value: (r) => r.hc.score },
  bucketEasy: { label: "Easy bucket", unit: "%", value: (r) => r.buckets.easy },
  bucketMedium: { label: "Medium bucket", unit: "%", value: (r) => r.buckets.medium },
  bucketHard: { label: "Hard bucket", unit: "%", value: (r) => r.buckets.hard },
  cost: { label: "Agent LLM cost", unit: "$", value: (r) => r.cost.total },
  askUserCost: { label: "ask_user cost", unit: "$", value: (r) => r.askUserCost.total },
  totalCost: { label: "Total cost", unit: "$", value: (r) => r.totalCost.total },
  cpuTemp: { label: "CPU/GPU/NPU temp", unit: "°C", value: (r) => r.cpuTemp.max },
  powerSkinTemp: { label: "Power-amp/skin temp", unit: "°C", value: (r) => (r.powerSkinTemp ? r.powerSkinTemp.max : null) },
  batteryTemp: { label: "Battery temp", unit: "°C", value: (r) => r.batteryTemp },
  batteryDrain: { label: "Battery drain", unit: "%", value: (r) => r.batteryDrain },
};

// Distinct bubble colours (one per model), so each model reads clearly.
const CHART_COLORS = ["#2a6f8f", "#7f8f3a", "#c9a227", "#c9732a", "#c94a2a", "#9c3a3a", "#6b4a8f"];

// Rough pixel width of a model-name label at the chart's font size, so labels
// can be placed without overflowing the plot area.
function labelWidth(text) {
  return String(text).length * 6.6 + 16;
}

function niceTicks(min, max, count = 5) {
  const span = Math.max(max - min, 1e-9);
  const step0 = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const norm = step0 / mag;
  const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10) * mag;
  const start = Math.floor(min / step) * step;
  const ticks = [];
  for (let v = start; v <= max + step * 0.001; v += step) ticks.push(Number(v.toPrecision(12)));
  return ticks;
}

function renderChartControls() {
  const xSel = document.getElementById("chart-x");
  const ySel = document.getElementById("chart-y");
  const modeSel = document.getElementById("chart-mode");
  if (!xSel || !ySel) return;
  const opts = (sel, current) => {
    sel.innerHTML = Object.entries(CHART_METRICS)
      .map(([key, m]) => `<option value="${key}"${key === current ? " selected" : ""}>${m.label}</option>`)
      .join("");
  };
  opts(xSel, chartX);
  opts(ySel, chartY);
  xSel.addEventListener("change", () => { chartX = xSel.value; renderScatterChart(); });
  ySel.addEventListener("change", () => { chartY = ySel.value; renderScatterChart(); });

  // Text vs vision filter — only chart runs of the chosen mode.
  if (modeSel) {
    const counts = { text: 0, vision: 0 };
    for (const r of LEADERBOARD_ROWS) if (r.mode) counts[r.mode] = (counts[r.mode] || 0) + 1;
    modeSel.innerHTML = [
      `<option value="all">All models</option>`,
      `<option value="text">Text (${counts.text})</option>`,
      `<option value="vision">Vision (${counts.vision})</option>`,
    ].join("");
    modeSel.value = chartMode;
    modeSel.addEventListener("change", () => {
      chartMode = modeSel.value;
      renderScatterChart();
    });
  }
}

// Free-axis scatter chart: X and Y can each be any chartable metric. Every
// model is a coloured bubble; hovering shows the model name + its x/y values.
// Overlapping dots and labels are nudged apart so nothing collides.
function renderScatterChart() {
  const card = document.getElementById("perf-dollar-chart");
  if (!card) return;
  const inner = card.querySelector(".lb-chart-card-inner");
  if (!inner) return;
  inner.innerHTML = "";

  const rows = getFilteredRows().filter((r) => chartMode === "all" || r.mode === chartMode);
  if (!rows.length) {
    inner.innerHTML = `<p class="lb-empty">No models match this mode filter.</p>`;
    return;
  }

  const xMeta = CHART_METRICS[chartX];
  const yMeta = CHART_METRICS[chartY];
  const points = rows
    .map((r) => ({ row: r, x: xMeta.value(r), y: yMeta.value(r) }))
    .filter((p) => p.x != null && p.y != null);

  if (!points.length) {
    inner.innerHTML = `<p class="lb-empty">No plottable values for this axis pair.</p>`;
    return;
  }

  const width = 760;
  const height = 400;
  const margin = { top: 30, right: 30, bottom: 54, left: 64 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const xVals = points.map((p) => p.x);
  const yVals = points.map((p) => p.y);
  const xMin = Math.min(...xVals);
  const xMax = Math.max(...xVals);
  const yMin = Math.min(...yVals);
  const yMax = Math.max(...yVals);
  const xPad = (xMax - xMin) * 0.12 || 1;
  const yPad = (yMax - yMin) * 0.12 || 1;

  const xTicks = niceTicks(xMin - xPad, xMax + xPad, 5);
  const yTicks = niceTicks(yMin - yPad, yMax + yPad, 5);
  const xScale = (v) => margin.left + ((v - (xMin - xPad)) / (xMax + xPad - (xMin - xPad))) * plotW;
  const yScale = (v) => margin.top + plotH - ((v - (yMin - yPad)) / (yMax + yPad - (yMin - yPad))) * plotH;

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${xMeta.label} vs ${yMeta.label} scatter">`;

  for (const t of yTicks) {
    const y = yScale(t);
    if (y < margin.top - 0.5 || y > height - margin.bottom + 0.5) continue; // skip stray lines outside plot
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${fmtTick(t, yMeta)}</text>`;
  }
  for (const t of xTicks) {
    const x = xScale(t);
    if (x < margin.left - 0.5 || x > width - margin.right + 0.5) continue; // skip stray lines outside plot
    svg += `<line class="lb-grid-line-v" x1="${x}" y1="${margin.top}" x2="${x}" y2="${height - margin.bottom}" />`;
    svg += `<text class="lb-tick-label" x="${x}" y="${height - margin.bottom + 18}" text-anchor="middle">${fmtTick(t, xMeta)}</text>`;
  }

  svg += `<text class="lb-axis-label" x="${margin.left + plotW / 2}" y="${height - 6}" text-anchor="middle">${xMeta.label}${xMeta.unit ? ` (${xMeta.unit})` : ""}</text>`;
  svg += `<text class="lb-axis-label" transform="translate(14 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">${yMeta.label}${yMeta.unit ? ` (${yMeta.unit})` : ""}</text>`;

  // --- Layout with collision avoidance ---
  // Reserve right margin for labels so they never clip.
  const reservedRight = margin.right + 130;
  const plotW2 = width - margin.left - reservedRight;
  const xScale2 = (v) => margin.left + ((v - (xMin - xPad)) / (xMax + xPad - (xMin - xPad))) * plotW2;

  // 1) Position dots, nudging apart any that overlap.
  const dotPos = [];
  const nudgeOffsets = [
    [0, 0], [16, 0], [-16, 0], [0, 16], [0, -16], [32, 0], [-32, 0],
    [0, 32], [0, -32], [32, 32], [-32, -32], [32, -32], [-32, 32],
  ];
  for (let i = 0; i < points.length; i++) {
    const baseX = xScale2(points[i].x);
    const baseY = yScale(points[i].y);
    let cx = baseX;
    let cy = baseY;
    for (const [dx, dy] of nudgeOffsets) {
      const candX = baseX + dx;
      const candY = baseY + dy;
      if (candX < margin.left + 10 || candX > width - reservedRight - 10) continue;
      if (candY < margin.top + 10 || candY > height - margin.bottom - 10) continue;
      const clash = dotPos.some((p) => Math.hypot(candX - p.cx, candY - p.cy) < 26);
      if (!clash) {
        cx = candX;
        cy = candY;
        break;
      }
    }
    dotPos.push({ cx, cy });
  }

  // 2) Lay out labels, nudging vertically apart when they overlap.
  const placedLabels = [];
  const layout = points.map((p, i) => {
    const { cx, cy } = dotPos[i];
    const color = CHART_COLORS[i % CHART_COLORS.length];
    const name = p.row.model;
    const lw = labelWidth(name);
    let labelX = cx + 14;
    let anchor = "start";
    if (cx + 14 + lw > width - margin.right) {
      if (cx - 14 - lw >= margin.left) {
        labelX = cx - 14;
        anchor = "end";
      } else {
        labelX = Math.min(cx - 14, width - margin.right);
        anchor = "end";
      }
    }
    let labelY = cy + 4;
    // Avoid overlapping another label that is horizontally adjacent.
    const x0 = anchor === "start" ? labelX : labelX - lw;
    const x1 = anchor === "start" ? labelX + lw : labelX;
    for (const dy of [0, 15, -15, 30, -30, 45]) {
      const y = cy + 4 + dy;
      const clash = placedLabels.some((L) => Math.abs(L.y - y) < 14 && !(x1 < L.x0 || x0 > L.x1));
      if (!clash) {
        labelY = y;
        break;
      }
    }
    placedLabels.push({ x0, x1, y: labelY });
    return { p, cx, cy, color, name, labelX, labelY, anchor, lw };
  });

  for (const L of layout) {
    const escName = escapeHtml(L.name);
    svg += `<circle class="lb-dot" cx="${L.cx}" cy="${L.cy}" r="8" fill="${L.color}" />`;
    svg += `<text class="lb-dot-label" x="${L.labelX}" y="${L.labelY}" text-anchor="${L.anchor}" fill="${L.color}">${escName}</text>`;
    svg += `<circle class="lb-hit" cx="${L.cx}" cy="${L.cy}" r="15" tabindex="0" role="button" aria-label="${L.name}: ${xMeta.label} ${fmtVal(L.p.x, xMeta)}, ${yMeta.label} ${fmtVal(L.p.y, yMeta)}" data-model="${L.name}" data-x="${fmtVal(L.p.x, xMeta)}" data-y="${fmtVal(L.p.y, yMeta)}" data-xlabel="${xMeta.label}" data-ylabel="${yMeta.label}" />`;
  }

  svg += `</svg>`;
  inner.innerHTML = svg;

  const tooltip = makeTooltip(card);
  const hits = inner.querySelectorAll(".lb-hit");
  for (const hit of hits) {
    const html = `<strong>${hit.dataset.model}</strong><span>${hit.dataset.xlabel}: ${hit.dataset.x}</span><span>${hit.dataset.ylabel}: ${hit.dataset.y}</span>`;
    hit.addEventListener("mouseenter", (event) => showTooltip(tooltip, event.clientX - card.getBoundingClientRect().left, event.clientY - card.getBoundingClientRect().top, html));
    hit.addEventListener("mouseleave", () => hideTooltip(tooltip));
    hit.addEventListener("focus", (event) => showTooltip(tooltip, event.clientX - card.getBoundingClientRect().left, event.clientY - card.getBoundingClientRect().top, html));
    hit.addEventListener("blur", () => hideTooltip(tooltip));
    hit.addEventListener("click", (event) => {
      event.preventDefault();
      if (pinnedChartTooltip && pinnedChartTooltip.tooltip === tooltip && tooltip.classList.contains("active")) {
        hideTooltip(tooltip);
        pinnedChartTooltip = null;
      } else {
        showTooltip(tooltip, event.clientX - card.getBoundingClientRect().left, event.clientY - card.getBoundingClientRect().top, html);
        pinnedChartTooltip = { tooltip, model: hit.dataset.model };
      }
    });
  }
}

function fmtTick(v, meta) {
  if (meta.unit === "%") return `${Math.round(v)}%`;
  if (meta.unit === "°C") return `${Math.round(v)}°`;
  if (meta.unit === "$") return v >= 1 ? `$${v.toFixed(1)}` : `$${v.toFixed(2)}`;
  if (v >= 1000) return `${Math.round(v / 100) / 10}k`;
  if (Number.isInteger(v)) return String(v);
  if (Math.abs(v) >= 1) return v.toFixed(1).replace(/\.0$/, "");
  return v.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

function fmtVal(v, meta) {
  if (meta.unit === "%") return `${Math.round(v * 10) / 10}%`;
  if (meta.unit === "°C") return `${Math.round(v * 10) / 10} °C`;
  if (meta.unit === "$") return `$${v.toFixed(2)}`;
  if (meta.unit === "s") return `${Math.round(v)} s`;
  if (v >= 1) return String(Math.round(v * 100) / 100);
  return String(Math.round(v * 1000) / 1000);
}

function renderLeaderboard() {
  renderModeFilter();
  renderSearchBar();
  renderMetricsToggle();
  renderMetricsInfo();
  renderTable("mcq-table", rankedRows(getFilteredRows()));
  const chartCard = document.getElementById("perf-dollar-chart");
  if (chartCard) {
    chartCard.innerHTML = `
      <div class="lb-chart-controls">
        <div class="select-wrap">
          <span class="filter-label">X axis</span>
          <select id="chart-x" class="site-select" aria-label="X axis metric"></select>
        </div>
        <div class="select-wrap">
          <span class="filter-label">Y axis</span>
          <select id="chart-y" class="site-select" aria-label="Y axis metric"></select>
        </div>
        <div class="select-wrap">
          <span class="filter-label">Mode</span>
          <select id="chart-mode" class="site-select" aria-label="Filter chart by text or vision"></select>
        </div>
      </div>
      <div class="lb-chart-card-inner"></div>
    `;
    renderChartControls();
    renderScatterChart();
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
