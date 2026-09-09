/**
 * Interactive doughnut / bar charts for AndroidLife pages (Chart.js).
 * Markup: <canvas class="al-chart" data-chart='{"type":"doughnut",...}'></canvas>
 */
(function () {
  const PALETTE = {
    easy: "#8a7355",
    medium: "#6b8a94",
    hard: "#c4b09a",
    askSingle: "#6b8a94",
    askMulti: "#8a7355",
    nonAsk: "#b7a48c",
    bar: "#8a7355",
  };

  function baseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: 4 },
      plugins: {
        legend: { display: false },
        title: { display: false },
        tooltip: {
          enabled: true,
          backgroundColor: "rgba(40, 36, 32, 0.94)",
          titleFont: { family: "Crimson Pro, Georgia, serif", size: 13 },
          bodyFont: { family: "Crimson Pro, Georgia, serif", size: 12 },
          padding: 8,
          cornerRadius: 4,
          displayColors: false,
          caretPadding: 8,
          callbacks: {
            title(items) {
              return items[0] ? items[0].label : "";
            },
            label(ctx) {
              const v = ctx.raw;
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total ? ((v / total) * 100).toFixed(1) : "0";
              return `${v}  (${pct}%)`;
            },
          },
        },
      },
      animation: { duration: 550, easing: "easeOutQuart" },
    };
  }

  function renderDoughnut(canvas, cfg) {
    const labels = cfg.labels || [];
    const data = cfg.data || [];
    const colors = cfg.colors || labels.map((_, i) => Object.values(PALETTE)[i % 6]);
    const center = cfg.center || null;
    const opts = baseOptions();
    opts.cutout = "62%";
    opts.interaction = { mode: "nearest", intersect: true };
    opts.onHover = (evt, els) => {
      evt.native.target.style.cursor = els.length ? "pointer" : "default";
    };
    opts.elements = {
      arc: { hoverOffset: 4, borderWidth: 2, borderColor: "rgba(255,255,255,0.9)" },
    };

    // HTML center label (avoids canvas text stacking / overlap)
    const host = canvas.closest(".pie-canvas-wrap");
    if (host && center) {
      let badge = host.querySelector(".pie-center");
      if (!badge) {
        badge = document.createElement("div");
        badge.className = "pie-center";
        badge.setAttribute("aria-hidden", "true");
        host.appendChild(badge);
      }
      badge.innerHTML =
        `<span class="pie-center-value">${center.value}</span>` +
        (center.label ? `<span class="pie-center-label">${center.label}</span>` : "");
    }

    return new Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, hoverOffset: 4 }],
      },
      options: opts,
    });
  }

  function renderBar(canvas, cfg) {
    const labels = cfg.labels || [];
    const data = cfg.data || [];
    const opts = baseOptions();
    opts.indexAxis = cfg.horizontal === false ? "x" : "y";
    opts.scales = {
      x: {
        beginAtZero: true,
        max: cfg.max ?? 100,
        grid: { color: "rgba(0,0,0,0.04)" },
        ticks: {
          callback: (v) => (cfg.unit === "%" ? `${v}%` : v),
          font: { family: "Crimson Pro, Georgia, serif", size: 11 },
        },
      },
      y: {
        grid: { display: false },
        ticks: { font: { family: "Crimson Pro, Georgia, serif", size: 12 } },
      },
    };
    opts.plugins.tooltip.callbacks = {
      title(items) {
        return items[0] ? items[0].label : "";
      },
      label(ctx) {
        const u = cfg.unit === "%" ? "%" : "";
        return `${ctx.raw}${u}`;
      },
    };
    return new Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: cfg.colors || labels.map(() => PALETTE.bar),
            borderRadius: 3,
            maxBarThickness: 28,
          },
        ],
      },
      options: opts,
    });
  }

  /** Grid legend: swatch | label | count | pct - columns stay aligned. */
  function fillLegend(el, cfg) {
    if (!el || !cfg.labels) return;
    const colors = cfg.colors || [];
    const total = cfg.data.reduce((a, b) => a + b, 0);
    el.classList.add("pie-legend--grid");
    el.innerHTML = cfg.labels
      .map((label, i) => {
        const v = cfg.data[i];
        const pct =
          cfg.showPct !== false && total ? `${((v / total) * 100).toFixed(1)}%` : "";
        const href = (cfg.hrefs && cfg.hrefs[i]) || null;
        const name = href
          ? `<a class="pie-legend-name" href="${href}">${label}</a>`
          : `<span class="pie-legend-name">${label}</span>`;
        return (
          `<li>` +
          `<span class="swatch" style="background:${colors[i]}"></span>` +
          name +
          `<span class="pie-legend-count">${v}</span>` +
          `<span class="pie-legend-pct">${pct}</span>` +
          `</li>`
        );
      })
      .join("");
  }

  function boot() {
    if (typeof Chart === "undefined") return;
    document.querySelectorAll("canvas.al-chart").forEach((canvas) => {
      let cfg;
      try {
        cfg = JSON.parse(canvas.getAttribute("data-chart") || "{}");
      } catch {
        return;
      }
      const wrap = canvas.closest(".pie-wrap, .viz-chart-wrap");
      const legend = wrap && wrap.querySelector(".pie-legend");
      if (cfg.type === "bar") {
        renderBar(canvas, cfg);
      } else {
        renderDoughnut(canvas, cfg);
        fillLegend(legend, cfg);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
