document.querySelectorAll("nav").forEach((nav) => {
  const toggle = nav.querySelector(".nav-toggle");
  const links = nav.querySelector(".nav-links");
  if (!toggle || !links) return;

  function setOpen(open) {
    nav.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
  }

  toggle.addEventListener("click", () => {
    setOpen(!nav.classList.contains("nav-open"));
  });

  links.addEventListener("click", (event) => {
    if (event.target.closest("a")) setOpen(false);
  });

  document.addEventListener("click", (event) => {
    if (nav.classList.contains("nav-open") && !nav.contains(event.target)) setOpen(false);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && nav.classList.contains("nav-open")) {
      setOpen(false);
      toggle.focus();
    }
  });

  const desktop = window.matchMedia("(min-width: 741px)");
  const resetAtDesktop = (event) => {
    if (event.matches) setOpen(false);
  };
  desktop.addEventListener("change", resetAtDesktop);
});

// Theme-matched custom menus for <select class="site-select"> / .lb-filter-select.
// Native option popups stay OS-grey on macOS; this wraps each select once.
(function enhanceSiteSelects() {
  const SELECTOR = "select.site-select, select.lb-filter-select";

  function closeAll(except) {
    document.querySelectorAll(".select-wrap.is-open, .lb-select-wrap.is-open").forEach((wrap) => {
      if (except && wrap === except) return;
      wrap.classList.remove("is-open");
      const menu = wrap.querySelector(".site-select-menu");
      if (menu) menu.hidden = true;
      const trigger = wrap.querySelector(".site-select-trigger");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
    });
  }

  function optionLabel(opt) {
    return (opt.textContent || opt.label || opt.value || "").trim();
  }

  function enhance(select) {
    if (!select || select.dataset.enhanced === "1") return;
    let wrap = select.closest(".select-wrap, .lb-select-wrap");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "select-wrap";
      select.parentNode.insertBefore(wrap, select);
      wrap.appendChild(select);
    }
    wrap.classList.add("select-wrap-enhanced");
    select.classList.add("site-select-enhanced");
    select.dataset.enhanced = "1";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "site-select-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.innerHTML = `<span class="site-select-trigger-label"></span><span class="site-select-caret" aria-hidden="true"></span>`;

    const menu = document.createElement("ul");
    menu.className = "site-select-menu";
    menu.setAttribute("role", "listbox");
    menu.hidden = true;

    wrap.appendChild(trigger);
    wrap.appendChild(menu);

    const labelEl = trigger.querySelector(".site-select-trigger-label");

    function syncFromSelect() {
      const selected = select.options[select.selectedIndex];
      labelEl.textContent = selected ? optionLabel(selected) : "";
      menu.innerHTML = "";
      Array.from(select.options).forEach((opt, idx) => {
        if (opt.hidden) return;
        const li = document.createElement("li");
        li.className = "site-select-option";
        li.setAttribute("role", "option");
        li.dataset.index = String(idx);
        if (opt.disabled) {
          li.setAttribute("aria-disabled", "true");
          li.style.opacity = "0.45";
          li.style.pointerEvents = "none";
        }
        if (idx === select.selectedIndex) {
          li.classList.add("is-selected");
          li.setAttribute("aria-selected", "true");
        }
        li.innerHTML = `<span class="site-select-option-check" aria-hidden="true">✓</span>`;
        const text = document.createElement("span");
        text.textContent = optionLabel(opt);
        li.appendChild(text);
        li.addEventListener("click", (event) => {
          event.preventDefault();
          if (opt.disabled) return;
          select.selectedIndex = idx;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          syncFromSelect();
          closeAll();
          trigger.focus();
        });
        menu.appendChild(li);
      });
    }

    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const open = !wrap.classList.contains("is-open");
      closeAll();
      if (open) {
        wrap.classList.add("is-open");
        menu.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
      }
    });

    select.addEventListener("change", syncFromSelect);

    const mo = new MutationObserver(syncFromSelect);
    mo.observe(select, { childList: true, subtree: true, characterData: true, attributes: true });

    syncFromSelect();
  }

  function scan(root) {
    (root || document).querySelectorAll(SELECTOR).forEach(enhance);
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".select-wrap-enhanced")) closeAll();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => scan());
  } else {
    scan();
  }

  // Leaderboard / public-run options are filled after fetch — re-scan periodically briefly.
  let passes = 0;
  const timer = setInterval(() => {
    scan();
    passes += 1;
    if (passes > 40) clearInterval(timer);
  }, 250);

  window.enhanceSiteSelects = scan;
})();
