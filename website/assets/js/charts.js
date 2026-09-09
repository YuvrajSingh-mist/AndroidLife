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

  function baseOptions(title) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: { display: false },
        tooltip: {
          backgroundColor: "rgba(40, 36, 32, 0.92)",
          titleFont: { family: "Crimson Pro, Georgia, serif", size: 14 },
          bodyFont: { family: "Crimson Pro, Georgia, serif", size: 13 },
          padding: 10,
          cornerRadius: 4,
          callbacks: {
            label(ctx) {
              const v = ctx.raw;
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total ? ((v / total) * 100).toFixed(1) : "0";
              return ` ${ctx.label}: ${v} (${pct}%)`;
            },
          },
        },
      },
      animation: { duration: 700, easing: "easeOutQuart" },
    };
  }

  function renderDoughnut(canvas, cfg) {
    const labels = cfg.labels || [];
    const data = cfg.data || [];
    const colors = cfg.colors || labels.map((_, i) => Object.values(PALETTE)[i % 6]);
    const center = cfg.center || null;

    const chart = new Chart(canvas.getContext("2d"), {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data,
            backgroundColor: colors,
            borderColor: "rgba(255,255,255,0.85)",
            borderWidth: 2,
            hoverOffset: 8,
          },
        ],
      },
      options: {
        ...baseOptions(cfg.title),
        cutout: "58%",
        onHover(evt, els) {
          evt.native.target.style.cursor = els.length ? "pointer" : "default";
        },
      },
      plugins: center
        ? [
            {
              id: "centerText",
              afterDraw(c) {
                const { ctx, chartArea } = c;
                if (!chartArea) return;
                const x = (chartArea.left + chartArea.right) / 2;
                const y = (chartArea.top + chartArea.bottom) / 2;
                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#5c5348";
                ctx.font = "600 1.35rem Cormorant Garamond, Georgia, serif";
                ctx.fillText(String(center.value), x, y - 8);
                ctx.fillStyle = "#8a8074";
                ctx.font = "0.72rem Crimson Pro, Georgia, serif";
                ctx.fillText(center.label || "", x, y + 14);
                ctx.restore();
              },
            },
          ]
        : [],
    });
    return chart;
  }

  function renderBar(canvas, cfg) {
    const labels = cfg.labels || [];
    const data = cfg.data || [];
    const opts = baseOptions(cfg.title);
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
      label(ctx) {
        const u = cfg.unit === "%" ? "%" : "";
        return ` ${ctx.label}: ${ctx.raw}${u}`;
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

  function fillLegend(el, cfg) {
    if (!el || !cfg.labels) return;
    const colors = cfg.colors || [];
    el.innerHTML = cfg.labels
      .map((label, i) => {
        const v = cfg.data[i];
        const total = cfg.data.reduce((a, b) => a + b, 0);
        const pct = cfg.showPct !== false && total ? ` · ${((v / total) * 100).toFixed(1)}%` : "";
        const href = (cfg.hrefs && cfg.hrefs[i]) || null;
        const text = href
          ? `<a href="${href}">${label}</a> <strong>${v}</strong>${pct}`
          : `<strong>${label}</strong> ${v}${pct}`;
        return `<li><span class="swatch" style="background:${colors[i]}"></span>${text}</li>`;
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
